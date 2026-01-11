"""
Tests for the Worker Pool Manager module.

This test suite validates the pool manager's functionality:
- Pool creation and reuse
- Thread safety
- Lifecycle management
- Idle timeout and cleanup
- Global manager
- Context manager
"""

import time
import pytest
import threading
from multiprocessing import cpu_count
from amorsize.pool_manager import (
    PoolManager,
    get_global_pool_manager,
    managed_pool,
    shutdown_global_pool_manager
)


# Helper function for testing pool execution
def _square(x):
    """Simple function for testing pool execution."""
    return x * x


class TestPoolManagerBasics:
    """Test basic pool manager functionality."""
    
    def test_create_pool_manager(self):
        """Test creating a pool manager instance."""
        manager = PoolManager()
        assert manager is not None
        assert not manager._shutdown
        manager.shutdown()
    
    def test_get_process_pool(self):
        """Test getting a multiprocessing pool."""
        manager = PoolManager()
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            assert pool is not None
            # Verify it's actually a Pool by checking attributes
            assert hasattr(pool, 'map')
            assert hasattr(pool, 'close')
            assert hasattr(pool, '_state')
        finally:
            manager.shutdown()
    
    def test_get_thread_pool(self):
        """Test getting a thread pool."""
        manager = PoolManager()
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="thread")
            assert pool is not None
            # Verify it's actually a ThreadPoolExecutor
            from concurrent.futures import ThreadPoolExecutor
            assert isinstance(pool, ThreadPoolExecutor)
        finally:
            manager.shutdown()
    
    def test_invalid_n_jobs(self):
        """Test that invalid n_jobs raises ValueError."""
        manager = PoolManager()
        try:
            with pytest.raises(ValueError, match="n_jobs must be positive"):
                manager.get_pool(n_jobs=0)
            
            with pytest.raises(ValueError, match="n_jobs must be positive"):
                manager.get_pool(n_jobs=-1)
        finally:
            manager.shutdown()
    
    def test_invalid_executor_type(self):
        """Test that invalid executor_type raises ValueError."""
        manager = PoolManager()
        try:
            with pytest.raises(ValueError, match="executor_type must be"):
                manager.get_pool(n_jobs=2, executor_type="invalid")
        finally:
            manager.shutdown()
    
    def test_after_shutdown_raises(self):
        """Test that getting pool after shutdown raises RuntimeError."""
        manager = PoolManager()
        manager.shutdown()
        
        with pytest.raises(RuntimeError, match="has been shut down"):
            manager.get_pool(n_jobs=2)


class TestPoolReuse:
    """Test pool reuse functionality."""
    
    def test_reuse_same_pool(self):
        """Test that the same pool is reused for identical configurations."""
        manager = PoolManager()
        try:
            pool1 = manager.get_pool(n_jobs=2, executor_type="process")
            pool2 = manager.get_pool(n_jobs=2, executor_type="process")
            
            # Should be the same pool instance (check by id since object is same)
            assert id(pool1) == id(pool2)
        finally:
            manager.shutdown()
    
    def test_different_pools_for_different_configs(self):
        """Test that different pools are created for different configurations."""
        manager = PoolManager()
        try:
            pool1 = manager.get_pool(n_jobs=2, executor_type="process")
            pool2 = manager.get_pool(n_jobs=4, executor_type="process")
            pool3 = manager.get_pool(n_jobs=2, executor_type="thread")
            
            # All should be different instances
            assert pool1 is not pool2
            assert pool1 is not pool3
            assert pool2 is not pool3
        finally:
            manager.shutdown()
    
    def test_force_new_pool(self):
        """Test forcing creation of a new pool."""
        manager = PoolManager()
        try:
            pool1 = manager.get_pool(n_jobs=2, executor_type="process")
            pool2 = manager.get_pool(n_jobs=2, executor_type="process", force_new=True)
            
            # Should be different instances
            assert pool1 is not pool2
        finally:
            manager.shutdown()
    
    def test_pool_execution(self):
        """Test that pools can actually execute tasks."""
        manager = PoolManager()
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            data = [1, 2, 3, 4, 5]
            results = pool.map(_square, data, chunksize=2)
            assert results == [1, 4, 9, 16, 25]
            
            # Reuse the pool
            pool2 = manager.get_pool(n_jobs=2, executor_type="process")
            assert id(pool) == id(pool2)
            results2 = pool2.map(_square, data, chunksize=2)
            assert results2 == [1, 4, 9, 16, 25]
        finally:
            manager.shutdown()


class TestLifecycleManagement:
    """Test pool lifecycle management."""
    
    def test_shutdown_closes_pools(self):
        """Test that shutdown closes all managed pools."""
        manager = PoolManager()
        pool1 = manager.get_pool(n_jobs=2, executor_type="process")
        pool2 = manager.get_pool(n_jobs=4, executor_type="process")
        
        stats_before = manager.get_stats()
        assert stats_before["active_pools"] == 2
        
        manager.shutdown()
        
        # After shutdown, manager should be empty
        assert manager._shutdown
        assert len(manager._pools) == 0
    
    def test_clear_removes_all_pools(self):
        """Test that clear removes all pools but doesn't shutdown manager."""
        manager = PoolManager()
        try:
            pool1 = manager.get_pool(n_jobs=2, executor_type="process")
            pool2 = manager.get_pool(n_jobs=4, executor_type="process")
            
            assert len(manager._pools) == 2
            
            manager.clear()
            
            # Pools should be gone but manager still usable
            assert len(manager._pools) == 0
            assert not manager._shutdown
            
            # Can create new pools
            pool3 = manager.get_pool(n_jobs=2, executor_type="process")
            assert pool3 is not None
        finally:
            manager.shutdown()
    
    def test_context_manager(self):
        """Test using pool manager as context manager."""
        with PoolManager() as manager:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            assert pool is not None
            assert not manager._shutdown
        
        # After context exit, manager should be shut down
        assert manager._shutdown
    
    def test_release_pool_updates_usage(self):
        """Test that release_pool updates usage time."""
        manager = PoolManager()
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            
            # Get initial usage time
            pool_key = (2, "process")
            time1 = manager._pool_usage[pool_key]
            
            # Wait a bit and release
            time.sleep(0.1)
            manager.release_pool(n_jobs=2, executor_type="process")
            
            # Usage time should be updated
            time2 = manager._pool_usage[pool_key]
            assert time2 > time1
        finally:
            manager.shutdown()


class TestIdleCleanup:
    """Test idle pool cleanup functionality."""
    
    def test_idle_cleanup(self):
        """Test that idle pools are cleaned up after timeout."""
        # Use very short timeout for testing
        manager = PoolManager(idle_timeout=0.2)
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            
            assert len(manager._pools) == 1
            
            # Wait for idle timeout
            time.sleep(0.3)
            
            # Create new pool (triggers cleanup)
            pool2 = manager.get_pool(n_jobs=4, executor_type="process")
            
            # Old pool should have been cleaned up
            pool_key_old = (2, "process")
            assert pool_key_old not in manager._pools
        finally:
            manager.shutdown()
    
    def test_no_idle_cleanup_when_disabled(self):
        """Test that idle cleanup doesn't occur when disabled."""
        manager = PoolManager(idle_timeout=None)
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            
            # Wait (would be long enough for cleanup if it were enabled)
            time.sleep(0.2)
            
            # Create new pool (would trigger cleanup if enabled)
            pool2 = manager.get_pool(n_jobs=4, executor_type="process")
            
            # Old pool should still be there
            assert len(manager._pools) == 2
        finally:
            manager.shutdown()
    
    def test_active_pool_not_cleaned(self):
        """Test that recently used pools are not cleaned up."""
        manager = PoolManager(idle_timeout=0.3)
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            
            # Keep pool active by getting it repeatedly
            for _ in range(5):
                time.sleep(0.1)
                pool = manager.get_pool(n_jobs=2, executor_type="process")
            
            # Pool should still be there
            pool_key = (2, "process")
            assert pool_key in manager._pools
        finally:
            manager.shutdown()


class TestStatistics:
    """Test pool statistics functionality."""
    
    def test_get_stats_empty(self):
        """Test getting stats from empty manager."""
        manager = PoolManager()
        try:
            stats = manager.get_stats()
            assert stats["active_pools"] == 0
            assert stats["pool_configs"] == []
            assert stats["idle_times"] == {}
            assert not stats["is_shutdown"]
        finally:
            manager.shutdown()
    
    def test_get_stats_with_pools(self):
        """Test getting stats with active pools."""
        manager = PoolManager()
        try:
            pool1 = manager.get_pool(n_jobs=2, executor_type="process")
            pool2 = manager.get_pool(n_jobs=4, executor_type="thread")
            
            stats = manager.get_stats()
            assert stats["active_pools"] == 2
            assert len(stats["pool_configs"]) == 2
            assert len(stats["idle_times"]) == 2
            
            # Check configs
            configs = stats["pool_configs"]
            assert {"n_jobs": 2, "executor_type": "process"} in configs
            assert {"n_jobs": 4, "executor_type": "thread"} in configs
        finally:
            manager.shutdown()
    
    def test_get_stats_after_shutdown(self):
        """Test getting stats after shutdown."""
        manager = PoolManager()
        pool = manager.get_pool(n_jobs=2, executor_type="process")
        manager.shutdown()
        
        stats = manager.get_stats()
        assert stats["active_pools"] == 0
        assert stats["is_shutdown"]


class TestThreadSafety:
    """Test thread safety of pool manager."""
    
    def test_concurrent_pool_creation(self):
        """Test that concurrent pool creation is thread-safe."""
        manager = PoolManager()
        pools = []
        errors = []
        lock = threading.Lock()
        
        def create_pool():
            try:
                pool = manager.get_pool(n_jobs=2, executor_type="process")
                with lock:
                    pools.append(pool)
            except Exception as e:
                with lock:
                    errors.append(e)
        
        try:
            # Create pools concurrently
            threads = [threading.Thread(target=create_pool) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # Should have no errors
            assert len(errors) == 0
            
            # All pools should be the same instance (reused) - check by id
            unique_ids = set(id(p) for p in pools)
            assert len(unique_ids) == 1, f"Expected 1 unique pool, got {len(unique_ids)}"
        finally:
            manager.shutdown()
    
    def test_concurrent_different_pools(self):
        """Test creating different pools concurrently."""
        manager = PoolManager()
        pools = {i: [] for i in range(1, 5)}  # Use 1-4 instead of 0-3
        errors = []
        lock = threading.Lock()
        
        def create_pool(n_jobs):
            try:
                pool = manager.get_pool(n_jobs=n_jobs, executor_type="process")
                with lock:
                    pools[n_jobs].append(pool)
            except Exception as e:
                with lock:
                    errors.append(e)
        
        try:
            # Create different pools concurrently
            threads = []
            for n_jobs in [1, 2, 3, 4]:
                for _ in range(3):  # 3 threads per config
                    t = threading.Thread(target=create_pool, args=(n_jobs,))
                    threads.append(t)
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # Should have no errors
            assert len(errors) == 0, f"Got errors: {errors}"
            
            # Each configuration should have same pool instance
            for n_jobs, pool_list in pools.items():
                if pool_list:  # Skip empty lists
                    unique_ids = set(id(p) for p in pool_list)
                    assert len(unique_ids) == 1, f"n_jobs={n_jobs} has {len(unique_ids)} unique pools"
        finally:
            manager.shutdown()


class TestGlobalManager:
    """Test global pool manager functionality."""
    
    def test_get_global_manager(self):
        """Test getting global manager instance."""
        manager1 = get_global_pool_manager()
        manager2 = get_global_pool_manager()
        
        # Should be the same instance (singleton)
        assert manager1 is manager2
    
    def test_global_manager_reuse(self):
        """Test that global manager reuses pools."""
        manager = get_global_pool_manager()
        
        pool1 = manager.get_pool(n_jobs=2, executor_type="process")
        pool2 = manager.get_pool(n_jobs=2, executor_type="process")
        
        # Should be the same pool (check by id)
        assert id(pool1) == id(pool2)
    
    def test_shutdown_global_manager(self):
        """Test shutting down global manager."""
        manager = get_global_pool_manager()
        pool = manager.get_pool(n_jobs=2, executor_type="process")
        
        shutdown_global_pool_manager()
        
        # After shutdown, getting global manager should create new instance
        manager2 = get_global_pool_manager()
        assert manager2 is not manager


class TestManagedPoolContext:
    """Test managed_pool context manager."""
    
    def test_managed_pool_basic(self):
        """Test basic managed_pool usage."""
        with managed_pool(n_jobs=2, executor_type="process") as pool:
            assert pool is not None
            results = pool.map(_square, [1, 2, 3])
            assert results == [1, 4, 9]
    
    def test_managed_pool_with_custom_manager(self):
        """Test managed_pool with custom manager."""
        manager = PoolManager()
        try:
            with managed_pool(n_jobs=2, manager=manager) as pool:
                assert pool is not None
                results = pool.map(_square, [1, 2, 3])
                assert results == [1, 4, 9]
            
            # Manager should still have the pool
            assert len(manager._pools) == 1
        finally:
            manager.shutdown()
    
    def test_managed_pool_thread_executor(self):
        """Test managed_pool with thread executor."""
        with managed_pool(n_jobs=2, executor_type="thread") as pool:
            assert pool is not None
            from concurrent.futures import ThreadPoolExecutor
            assert isinstance(pool, ThreadPoolExecutor)
    
    def test_managed_pool_without_global(self):
        """Test managed_pool without using global manager."""
        with managed_pool(n_jobs=2, use_global=False) as pool:
            assert pool is not None
            results = pool.map(_square, [1, 2, 3])
            assert results == [1, 4, 9]
        
        # Pool should be cleaned up after context exit
        # (No way to verify directly, but it should not leak)


class TestPoolAliveness:
    """Test pool aliveness checking."""
    
    def test_process_pool_alive(self):
        """Test checking if process pool is alive."""
        manager = PoolManager()
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            assert manager._is_pool_alive(pool, "process")
        finally:
            manager.shutdown()
    
    def test_thread_pool_alive(self):
        """Test checking if thread pool is alive."""
        manager = PoolManager()
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="thread")
            assert manager._is_pool_alive(pool, "thread")
        finally:
            manager.shutdown()
    
    def test_closed_pool_not_alive(self):
        """Test that closed pool is detected as not alive."""
        manager = PoolManager()
        try:
            pool = manager.get_pool(n_jobs=2, executor_type="process")
            
            # Close the pool directly
            pool.close()
            
            # Should be detected as not alive
            assert not manager._is_pool_alive(pool, "process")
            
            # Getting pool again should create new one
            pool2 = manager.get_pool(n_jobs=2, executor_type="process")
            assert pool2 is not pool
        finally:
            manager.shutdown()


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_multiple_shutdowns(self):
        """Test that multiple shutdowns don't cause errors."""
        manager = PoolManager()
        pool = manager.get_pool(n_jobs=2, executor_type="process")
        
        manager.shutdown()
        manager.shutdown()  # Second shutdown should be no-op
        
        assert manager._shutdown
    
    def test_clear_after_shutdown(self):
        """Test that clear after shutdown is a no-op."""
        manager = PoolManager()
        manager.shutdown()
        
        # Should not raise error
        manager.clear()
    
    def test_stats_concurrent_access(self):
        """Test that getting stats while pools are being created is safe."""
        manager = PoolManager()
        stats_list = []
        
        def get_stats_repeatedly():
            for _ in range(10):
                stats_list.append(manager.get_stats())
                time.sleep(0.01)
        
        def create_pools():
            for i in range(5):
                manager.get_pool(n_jobs=i+1, executor_type="process")
                time.sleep(0.01)
        
        try:
            t1 = threading.Thread(target=get_stats_repeatedly)
            t2 = threading.Thread(target=create_pools)
            
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
            # Should have collected stats without errors
            assert len(stats_list) > 0
        finally:
            manager.shutdown()
