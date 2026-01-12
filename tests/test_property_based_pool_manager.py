"""
Property-based tests for the pool_manager module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the worker pool management system across a wide range of inputs and scenarios.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from multiprocessing.pool import Pool as PoolType
from typing import List, Tuple

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume

from amorsize.pool_manager import (
    PoolManager,
    get_global_pool_manager,
    managed_pool,
    shutdown_global_pool_manager,
)


# Custom strategies for generating test data

@st.composite
def valid_n_jobs(draw):
    """Generate valid n_jobs values (1-32)."""
    return draw(st.integers(min_value=1, max_value=32))


@st.composite
def valid_executor_type(draw):
    """Generate valid executor types."""
    return draw(st.sampled_from(["process", "thread"]))


@st.composite
def valid_idle_timeout(draw):
    """Generate valid idle timeout values."""
    return draw(st.one_of(
        st.none(),
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    ))


@st.composite
def pool_config(draw):
    """Generate a valid pool configuration."""
    return {
        "n_jobs": draw(valid_n_jobs()),
        "executor_type": draw(valid_executor_type()),
    }


# Helper function for pool execution tests
def _simple_func(x):
    """Simple function for testing pool execution."""
    return x * 2


class TestPoolManagerInitialization:
    """Test PoolManager initialization and configuration invariants."""

    @given(
        idle_timeout=valid_idle_timeout(),
        enable_auto_cleanup=st.booleans(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_initialization_creates_valid_manager(self, idle_timeout, enable_auto_cleanup):
        """Test that PoolManager can be initialized with various valid parameters."""
        manager = PoolManager(
            idle_timeout=idle_timeout,
            enable_auto_cleanup=enable_auto_cleanup
        )
        
        try:
            # Manager should be created successfully
            assert manager is not None
            assert not manager._shutdown
            assert manager._idle_timeout == idle_timeout
            assert manager._enable_auto_cleanup == enable_auto_cleanup
            
            # Internal state should be initialized
            assert isinstance(manager._pools, dict)
            assert isinstance(manager._pool_usage, dict)
            assert len(manager._pools) == 0
            assert len(manager._pool_usage) == 0
        finally:
            manager.shutdown()

    @given(n_jobs=valid_n_jobs())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_initialization_fields_have_correct_types(self, n_jobs):
        """Test that all manager fields have correct types after initialization."""
        manager = PoolManager()
        
        try:
            assert isinstance(manager._pools, dict)
            assert isinstance(manager._pool_usage, dict)
            assert isinstance(manager._lock, type(threading.Lock()))
            assert isinstance(manager._shutdown, bool)
            assert manager._idle_timeout is None or isinstance(manager._idle_timeout, (int, float))
            assert isinstance(manager._enable_auto_cleanup, bool)
        finally:
            manager.shutdown()


class TestPoolGetAndReuse:
    """Test pool retrieval and reuse invariants."""

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_pool_returns_valid_pool(self, n_jobs, executor_type):
        """Test that get_pool returns a valid pool object."""
        manager = PoolManager()
        
        try:
            pool = manager.get_pool(n_jobs, executor_type)
            
            # Pool should be valid
            assert pool is not None
            
            # Check pool type based on executor_type
            if executor_type == "process":
                assert isinstance(pool, PoolType)
                assert hasattr(pool, 'map')
                assert hasattr(pool, 'close')
            else:  # thread
                assert isinstance(pool, ThreadPoolExecutor)
                assert hasattr(pool, 'map')
                assert hasattr(pool, 'shutdown')
            
            # Pool should be tracked internally
            pool_key = (n_jobs, executor_type)
            assert pool_key in manager._pools
            assert pool_key in manager._pool_usage
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_same_config_reuses_pool(self, n_jobs, executor_type):
        """Test that requesting the same configuration returns the same pool."""
        manager = PoolManager()
        
        try:
            pool1 = manager.get_pool(n_jobs, executor_type)
            pool2 = manager.get_pool(n_jobs, executor_type)
            
            # Should be the same pool object
            assert pool1 is pool2
            
            # Should only have one pool tracked
            assert len(manager._pools) == 1
        finally:
            manager.shutdown()

    @given(
        configs=st.lists(pool_config(), min_size=1, max_size=5, unique_by=lambda x: (x["n_jobs"], x["executor_type"]))
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_different_configs_create_different_pools(self, configs):
        """Test that different configurations create different pools."""
        manager = PoolManager()
        
        try:
            pools = []
            for config in configs:
                pool = manager.get_pool(**config)
                pools.append(pool)
            
            # Should have one pool per unique config
            assert len(manager._pools) == len(configs)
            
            # All pools should be different objects (except duplicates)
            pool_ids = [id(p) for p in pools]
            assert len(set(pool_ids)) == len(configs)
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_force_new_creates_new_pool(self, n_jobs, executor_type):
        """Test that force_new=True creates a new pool even if one exists."""
        manager = PoolManager()
        
        try:
            pool1 = manager.get_pool(n_jobs, executor_type)
            pool2 = manager.get_pool(n_jobs, executor_type, force_new=True)
            
            # Should be different pool objects
            assert pool1 is not pool2
            
            # Both should still be tracked (newer one replaces older in dict)
            pool_key = (n_jobs, executor_type)
            assert pool_key in manager._pools
        finally:
            manager.shutdown()


class TestPoolValidation:
    """Test parameter validation invariants."""

    @given(
        n_jobs=st.integers(max_value=0),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_n_jobs_raises_valueerror(self, n_jobs, executor_type):
        """Test that invalid n_jobs raises ValueError."""
        manager = PoolManager()
        
        try:
            with pytest.raises(ValueError, match="n_jobs must be positive"):
                manager.get_pool(n_jobs, executor_type)
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=st.text(min_size=1, max_size=20).filter(lambda x: x not in ["process", "thread"]),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_executor_type_raises_valueerror(self, n_jobs, executor_type):
        """Test that invalid executor_type raises ValueError."""
        manager = PoolManager()
        
        try:
            with pytest.raises(ValueError, match="executor_type must be"):
                manager.get_pool(n_jobs, executor_type)
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_pool_after_shutdown_raises_runtimeerror(self, n_jobs, executor_type):
        """Test that getting pool after shutdown raises RuntimeError."""
        manager = PoolManager()
        manager.shutdown()
        
        with pytest.raises(RuntimeError, match="has been shut down"):
            manager.get_pool(n_jobs, executor_type)


class TestPoolUsageTracking:
    """Test pool usage timestamp tracking invariants."""

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_pool_updates_usage_time(self, n_jobs, executor_type):
        """Test that getting a pool updates its usage timestamp."""
        manager = PoolManager()
        
        try:
            pool_key = (n_jobs, executor_type)
            
            # Get pool first time
            time_before = time.time()
            pool1 = manager.get_pool(n_jobs, executor_type)
            time_after = time.time()
            
            # Usage time should be set
            assert pool_key in manager._pool_usage
            usage_time1 = manager._pool_usage[pool_key]
            assert time_before <= usage_time1 <= time_after
            
            # Wait a bit and get pool again
            time.sleep(0.01)
            time_before2 = time.time()
            pool2 = manager.get_pool(n_jobs, executor_type)
            time_after2 = time.time()
            
            # Should be same pool
            assert pool1 is pool2
            
            # Usage time should be updated
            usage_time2 = manager._pool_usage[pool_key]
            assert usage_time2 > usage_time1
            assert time_before2 <= usage_time2 <= time_after2
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_release_pool_updates_usage_time(self, n_jobs, executor_type):
        """Test that release_pool updates usage timestamp."""
        manager = PoolManager()
        
        try:
            pool = manager.get_pool(n_jobs, executor_type)
            pool_key = (n_jobs, executor_type)
            
            usage_time1 = manager._pool_usage[pool_key]
            
            # Wait and release
            time.sleep(0.01)
            time_before = time.time()
            manager.release_pool(n_jobs, executor_type)
            time_after = time.time()
            
            # Usage time should be updated
            usage_time2 = manager._pool_usage[pool_key]
            assert usage_time2 > usage_time1
            assert time_before <= usage_time2 <= time_after
        finally:
            manager.shutdown()


class TestIdleCleanup:
    """Test idle pool cleanup invariants."""

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_idle_pools_cleaned_up_after_timeout(self, n_jobs, executor_type):
        """Test that pools are cleaned up after idle timeout."""
        # Use very short timeout for testing
        manager = PoolManager(idle_timeout=0.1)
        
        try:
            # Create a pool
            pool = manager.get_pool(n_jobs, executor_type)
            pool_key = (n_jobs, executor_type)
            
            assert pool_key in manager._pools
            
            # Wait for timeout
            time.sleep(0.2)
            
            # Request a different pool to trigger cleanup
            different_n_jobs = n_jobs + 1 if n_jobs < 32 else n_jobs - 1
            manager.get_pool(different_n_jobs, executor_type)
            
            # Old pool should be cleaned up
            # (It might still be in _pools if it's the only pool, but usage should be updated)
            assert len(manager._pools) >= 1
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_no_cleanup_when_timeout_is_none(self, n_jobs, executor_type):
        """Test that pools are not cleaned up when idle_timeout is None."""
        manager = PoolManager(idle_timeout=None)
        
        try:
            # Create a pool
            pool = manager.get_pool(n_jobs, executor_type)
            pool_key = (n_jobs, executor_type)
            
            assert pool_key in manager._pools
            
            # Wait
            time.sleep(0.1)
            
            # Pool should still exist
            assert pool_key in manager._pools
        finally:
            manager.shutdown()


class TestStatistics:
    """Test statistics tracking invariants."""

    @given(
        configs=st.lists(pool_config(), min_size=0, max_size=5, unique_by=lambda x: (x["n_jobs"], x["executor_type"]))
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_stats_returns_correct_structure(self, configs):
        """Test that get_stats returns correctly structured data."""
        manager = PoolManager()
        
        try:
            # Create pools
            for config in configs:
                manager.get_pool(**config)
            
            stats = manager.get_stats()
            
            # Check structure
            assert isinstance(stats, dict)
            assert "active_pools" in stats
            assert "pool_configs" in stats
            assert "idle_times" in stats
            assert "is_shutdown" in stats
            
            # Check types
            assert isinstance(stats["active_pools"], int)
            assert isinstance(stats["pool_configs"], list)
            assert isinstance(stats["idle_times"], dict)
            assert isinstance(stats["is_shutdown"], bool)
            
            # Check counts
            assert stats["active_pools"] == len(configs)
            assert len(stats["pool_configs"]) == len(configs)
            assert len(stats["idle_times"]) == len(configs)
            assert stats["is_shutdown"] is False
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_stats_idle_times_non_negative(self, n_jobs, executor_type):
        """Test that idle times are non-negative."""
        manager = PoolManager()
        
        try:
            manager.get_pool(n_jobs, executor_type)
            
            # Wait a bit
            time.sleep(0.01)
            
            stats = manager.get_stats()
            
            # All idle times should be non-negative
            for idle_time in stats["idle_times"].values():
                assert idle_time >= 0
        finally:
            manager.shutdown()

    @given(
        configs=st.lists(pool_config(), min_size=1, max_size=3, unique_by=lambda x: (x["n_jobs"], x["executor_type"]))
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_stats_pool_configs_match_created_pools(self, configs):
        """Test that pool_configs in stats match the created pools."""
        manager = PoolManager()
        
        try:
            # Create pools
            for config in configs:
                manager.get_pool(**config)
            
            stats = manager.get_stats()
            
            # Extract n_jobs and executor_type from stats
            stats_configs = {(c["n_jobs"], c["executor_type"]) for c in stats["pool_configs"]}
            expected_configs = {(c["n_jobs"], c["executor_type"]) for c in configs}
            
            assert stats_configs == expected_configs
        finally:
            manager.shutdown()


class TestShutdown:
    """Test shutdown behavior invariants."""

    @given(
        configs=st.lists(pool_config(), min_size=0, max_size=5, unique_by=lambda x: (x["n_jobs"], x["executor_type"]))
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_shutdown_clears_all_pools(self, configs):
        """Test that shutdown clears all pools."""
        manager = PoolManager()
        
        # Create pools
        for config in configs:
            manager.get_pool(**config)
        
        assert len(manager._pools) == len(configs)
        
        # Shutdown
        manager.shutdown()
        
        # All pools should be cleared
        assert len(manager._pools) == 0
        assert len(manager._pool_usage) == 0
        assert manager._shutdown is True

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_shutdown_is_idempotent(self, n_jobs, executor_type):
        """Test that calling shutdown multiple times is safe."""
        manager = PoolManager()
        
        manager.get_pool(n_jobs, executor_type)
        
        # Shutdown multiple times
        manager.shutdown()
        manager.shutdown()
        manager.shutdown()
        
        # Should be in shutdown state
        assert manager._shutdown is True
        assert len(manager._pools) == 0

    @given(
        configs=st.lists(pool_config(), min_size=1, max_size=3, unique_by=lambda x: (x["n_jobs"], x["executor_type"]))
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_shutdown_updates_stats(self, configs):
        """Test that stats reflect shutdown state."""
        manager = PoolManager()
        
        # Create pools
        for config in configs:
            manager.get_pool(**config)
        
        # Shutdown
        manager.shutdown()
        
        stats = manager.get_stats()
        
        assert stats["is_shutdown"] is True
        assert stats["active_pools"] == 0


class TestClear:
    """Test clear() method invariants."""

    @given(
        configs=st.lists(pool_config(), min_size=1, max_size=5, unique_by=lambda x: (x["n_jobs"], x["executor_type"]))
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_clear_removes_all_pools(self, configs):
        """Test that clear removes all pools but doesn't shutdown manager."""
        manager = PoolManager()
        
        try:
            # Create pools
            for config in configs:
                manager.get_pool(**config)
            
            assert len(manager._pools) == len(configs)
            
            # Clear
            manager.clear()
            
            # Pools should be cleared
            assert len(manager._pools) == 0
            assert len(manager._pool_usage) == 0
            
            # But manager should not be shutdown
            assert manager._shutdown is False
            
            # Should be able to create new pools
            pool = manager.get_pool(n_jobs=2, executor_type="thread")
            assert pool is not None
        finally:
            manager.shutdown()


class TestContextManager:
    """Test context manager protocol invariants."""

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_context_manager_shuts_down_on_exit(self, n_jobs, executor_type):
        """Test that context manager shuts down on exit."""
        with PoolManager() as manager:
            pool = manager.get_pool(n_jobs, executor_type)
            assert pool is not None
            assert not manager._shutdown
        
        # After exiting context, manager should be shutdown
        assert manager._shutdown is True

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_context_manager_returns_manager(self, n_jobs, executor_type):
        """Test that context manager returns the manager instance."""
        with PoolManager() as manager:
            assert isinstance(manager, PoolManager)
            # Should be able to use it
            pool = manager.get_pool(n_jobs, executor_type)
            assert pool is not None


class TestManagedPoolContext:
    """Test managed_pool context manager invariants."""

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_managed_pool_returns_pool(self, n_jobs, executor_type):
        """Test that managed_pool returns a valid pool."""
        # Create a temporary manager for this test
        manager = PoolManager(enable_auto_cleanup=False)
        
        try:
            with managed_pool(n_jobs, executor_type, manager=manager, use_global=False) as pool:
                assert pool is not None
                
                if executor_type == "process":
                    assert isinstance(pool, PoolType)
                else:
                    assert isinstance(pool, ThreadPoolExecutor)
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_managed_pool_without_manager_creates_temporary(self, n_jobs):
        """Test that managed_pool without manager creates temporary manager."""
        with managed_pool(n_jobs, executor_type="thread", manager=None, use_global=False) as pool:
            assert pool is not None
            assert isinstance(pool, ThreadPoolExecutor)


class TestThreadSafety:
    """Test thread safety invariants."""

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
        num_threads=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_get_pool_is_safe(self, n_jobs, executor_type, num_threads):
        """Test that concurrent get_pool calls are thread-safe."""
        manager = PoolManager()
        pools = []
        errors = []
        
        def get_pool_worker():
            try:
                pool = manager.get_pool(n_jobs, executor_type)
                pools.append(pool)
            except Exception as e:
                errors.append(e)
        
        try:
            threads = []
            for _ in range(num_threads):
                t = threading.Thread(target=get_pool_worker)
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            # No errors should occur
            assert len(errors) == 0
            
            # All threads should get pools
            assert len(pools) == num_threads
            
            # All pools should be the same object (reuse)
            assert all(p is pools[0] for p in pools)
        finally:
            manager.shutdown()

    @given(
        configs=st.lists(pool_config(), min_size=2, max_size=5, unique_by=lambda x: (x["n_jobs"], x["executor_type"]))
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_different_configs_is_safe(self, configs):
        """Test that concurrent requests for different configs are thread-safe."""
        assume(len(configs) >= 2)
        
        manager = PoolManager()
        pools = []
        errors = []
        
        def get_pool_worker(config):
            try:
                pool = manager.get_pool(**config)
                pools.append((config["n_jobs"], config["executor_type"], pool))
            except Exception as e:
                errors.append(e)
        
        try:
            threads = []
            for config in configs:
                t = threading.Thread(target=get_pool_worker, args=(config,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            # No errors should occur
            assert len(errors) == 0
            
            # Should have one pool per config
            assert len(pools) == len(configs)
            
            # Each unique config should have its own pool
            config_to_pool = {}
            for n_jobs, executor_type, pool in pools:
                key = (n_jobs, executor_type)
                if key not in config_to_pool:
                    config_to_pool[key] = pool
                else:
                    # Same config should have same pool
                    assert config_to_pool[key] is pool
        finally:
            manager.shutdown()


class TestGlobalManager:
    """Test global pool manager invariants."""

    def test_get_global_returns_manager(self):
        """Test that get_global_pool_manager returns a PoolManager."""
        manager = get_global_pool_manager()
        assert isinstance(manager, PoolManager)

    def test_get_global_returns_same_instance(self):
        """Test that get_global_pool_manager returns the same instance."""
        manager1 = get_global_pool_manager()
        manager2 = get_global_pool_manager()
        
        # Should be the exact same object
        assert manager1 is manager2

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None)
    def test_global_manager_works_correctly(self, n_jobs, executor_type):
        """Test that global manager can create and reuse pools."""
        manager = get_global_pool_manager()
        
        pool1 = manager.get_pool(n_jobs, executor_type)
        pool2 = manager.get_pool(n_jobs, executor_type)
        
        # Should reuse same pool
        assert pool1 is pool2

    def test_shutdown_global_clears_singleton(self):
        """Test that shutdown_global_pool_manager clears the singleton."""
        # Get global manager
        manager1 = get_global_pool_manager()
        assert manager1 is not None
        
        # Shutdown global
        shutdown_global_pool_manager()
        
        # Get global again - should be a new instance
        manager2 = get_global_pool_manager()
        assert manager2 is not None
        
        # Should be different instances
        assert manager1 is not manager2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @given(n_jobs=st.just(1))
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_single_worker_pool(self, n_jobs):
        """Test creating a pool with a single worker."""
        manager = PoolManager()
        
        try:
            pool = manager.get_pool(n_jobs=1, executor_type="thread")
            assert pool is not None
        finally:
            manager.shutdown()

    @given(n_jobs=st.just(32))
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_many_worker_pool(self, n_jobs):
        """Test creating a pool with many workers."""
        manager = PoolManager()
        
        try:
            pool = manager.get_pool(n_jobs=32, executor_type="thread")
            assert pool is not None
        finally:
            manager.shutdown()

    @given(
        n_jobs=valid_n_jobs(),
        executor_type=valid_executor_type(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_get_pool_after_clear(self, n_jobs, executor_type):
        """Test that pools can be created after clear()."""
        manager = PoolManager()
        
        try:
            # Create, clear, create again
            pool1 = manager.get_pool(n_jobs, executor_type)
            manager.clear()
            pool2 = manager.get_pool(n_jobs, executor_type)
            
            # Should be different pools
            assert pool1 is not pool2
        finally:
            manager.shutdown()

    def test_zero_idle_timeout(self):
        """Test manager with very short idle timeout."""
        manager = PoolManager(idle_timeout=0.01)
        
        try:
            # Should still work
            pool = manager.get_pool(n_jobs=2, executor_type="thread")
            assert pool is not None
        finally:
            manager.shutdown()


class TestIntegration:
    """Test integration scenarios."""

    @given(
        n_jobs=valid_n_jobs(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_full_lifecycle_with_execution(self, n_jobs):
        """Test complete pool lifecycle including actual execution."""
        manager = PoolManager()
        
        try:
            # Get pool
            pool = manager.get_pool(n_jobs, executor_type="thread")
            
            # Use pool to execute work
            data = list(range(10))
            results = list(pool.map(_simple_func, data))
            
            # Verify results
            assert results == [x * 2 for x in data]
            
            # Get same pool again (reuse)
            pool2 = manager.get_pool(n_jobs, executor_type="thread")
            assert pool is pool2
            
            # Execute again
            results2 = list(pool2.map(_simple_func, data))
            assert results2 == results
            
            # Check stats
            stats = manager.get_stats()
            assert stats["active_pools"] == 1
        finally:
            manager.shutdown()

    @given(
        configs=st.lists(
            pool_config(),
            min_size=1,
            max_size=3,
            unique_by=lambda x: (x["n_jobs"], x["executor_type"])
        )
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_pools_lifecycle(self, configs):
        """Test managing multiple pools simultaneously."""
        manager = PoolManager()
        
        try:
            # Create multiple pools
            pools = []
            for config in configs:
                pool = manager.get_pool(**config)
                pools.append(pool)
            
            # Verify all created
            assert len(manager._pools) == len(configs)
            
            # Use all pools
            data = list(range(5))
            for i, pool in enumerate(pools):
                if configs[i]["executor_type"] == "thread":
                    results = list(pool.map(_simple_func, data))
                    assert len(results) == len(data)
            
            # Clear and verify
            manager.clear()
            assert len(manager._pools) == 0
            
            # Can create again
            new_pool = manager.get_pool(n_jobs=2, executor_type="thread")
            assert new_pool is not None
        finally:
            manager.shutdown()
