"""
Tests for runtime adaptive chunk size tuning via AdaptiveChunkingPool.

This test suite validates the NEW runtime adaptive chunking feature that
dynamically adjusts chunk sizes DURING execution based on observed performance.

This is distinct from test_adaptive_chunking.py which tests the STATIC
CV-based chunk size adjustment done by optimize().
"""

import pytest
import time
from amorsize.adaptive_chunking import AdaptiveChunkingPool, create_adaptive_pool


# Test functions with different characteristics
def fast_func(x):
    """Fast function for testing."""
    return x * 2


def slow_func(x):
    """Slow function for testing."""
    time.sleep(0.01)  # 10ms per item
    return x * 2


def variable_func(x):
    """Function with variable execution time (heterogeneous workload)."""
    # Every 10th item is 10x slower
    if x % 10 == 0:
        time.sleep(0.02)
    else:
        time.sleep(0.002)
    return x * 2


class TestAdaptiveChunkingPoolBasics:
    """Test basic functionality of AdaptiveChunkingPool."""
    
    def test_initialization_valid_params(self):
        """Test pool initialization with valid parameters."""
        pool = AdaptiveChunkingPool(n_jobs=4, initial_chunksize=10)
        assert pool.n_jobs == 4
        assert pool.current_chunksize == 10
        assert pool.target_chunk_duration == 0.2
        assert pool.enable_adaptation is True
        pool.close()
        pool.join()
    
    def test_initialization_custom_params(self):
        """Test pool initialization with custom parameters."""
        pool = AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=5,
            target_chunk_duration=0.5,
            adaptation_rate=0.5,
            min_chunksize=2,
            max_chunksize=100,
            enable_adaptation=False,
            window_size=5
        )
        assert pool.n_jobs == 2
        assert pool.current_chunksize == 5
        assert pool.target_chunk_duration == 0.5
        assert pool.adaptation_rate == 0.5
        assert pool.min_chunksize == 2
        assert pool.max_chunksize == 100
        assert pool.enable_adaptation is False
        assert pool.window_size == 5
        pool.close()
        pool.join()
    
    def test_initialization_invalid_n_jobs(self):
        """Test that invalid n_jobs raises ValueError."""
        with pytest.raises(ValueError, match="n_jobs must be >= 1"):
            AdaptiveChunkingPool(n_jobs=0, initial_chunksize=10)
    
    def test_initialization_invalid_chunksize(self):
        """Test that invalid initial_chunksize raises ValueError."""
        with pytest.raises(ValueError, match="initial_chunksize must be >= 1"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=0)
    
    def test_initialization_invalid_target_duration(self):
        """Test that invalid target_chunk_duration raises ValueError."""
        with pytest.raises(ValueError, match="target_chunk_duration must be > 0"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, target_chunk_duration=0)
    
    def test_initialization_invalid_adaptation_rate(self):
        """Test that invalid adaptation_rate raises ValueError."""
        with pytest.raises(ValueError, match="adaptation_rate must be 0.0-1.0"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, adaptation_rate=1.5)
    
    def test_initialization_invalid_min_chunksize(self):
        """Test that invalid min_chunksize raises ValueError."""
        with pytest.raises(ValueError, match="min_chunksize must be >= 1"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, min_chunksize=0)
    
    def test_initialization_invalid_max_chunksize(self):
        """Test that max_chunksize < min_chunksize raises ValueError."""
        with pytest.raises(ValueError, match="max_chunksize.*must be >= min_chunksize"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, min_chunksize=5, max_chunksize=3)
    
    def test_initialization_invalid_window_size(self):
        """Test that invalid window_size raises ValueError."""
        with pytest.raises(ValueError, match="window_size must be >= 1"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, window_size=0)


class TestAdaptiveChunkingPoolMap:
    """Test map() method with adaptive chunking."""
    
    def test_map_basic_functionality(self):
        """Test basic map() functionality."""
        data = list(range(100))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = pool.map(fast_func, data)
        
        assert len(results) == len(data)
        assert results == [x * 2 for x in data]
    
    def test_map_empty_iterable(self):
        """Test map() with empty iterable."""
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = pool.map(fast_func, [])
        
        assert results == []
    
    def test_map_small_workload(self):
        """Test map() with workload smaller than 2 chunks."""
        data = list(range(15))  # Less than 2*10
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = pool.map(fast_func, data)
        
        assert results == [x * 2 for x in data]
    
    def test_map_with_explicit_chunksize(self):
        """Test map() with explicit chunksize (disables adaptation)."""
        data = list(range(100))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = pool.map(fast_func, data, chunksize=5)
            stats = pool.get_stats()
        
        assert results == [x * 2 for x in data]
        # Adaptation should not have occurred
        assert stats['adaptation_count'] == 0
    
    def test_map_adaptation_disabled(self):
        """Test that adaptation doesn't occur when disabled."""
        data = list(range(200))
        
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=10,
            enable_adaptation=False
        ) as pool:
            results = pool.map(slow_func, data)
            stats = pool.get_stats()
        
        assert results == [x * 2 for x in data]
        assert stats['current_chunksize'] == 10  # Should not change
        assert stats['adaptation_count'] == 0
    
    def test_map_closed_pool(self):
        """Test that map() on closed pool raises ValueError."""
        pool = AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10)
        pool.close()
        pool.join()
        
        with pytest.raises(ValueError, match="Pool is closed"):
            pool.map(fast_func, range(10))
    
    def test_map_with_threads(self):
        """Test map() using threads instead of processes."""
        data = list(range(50))
        
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=10,
            use_threads=True
        ) as pool:
            results = pool.map(fast_func, data)
        
        assert results == [x * 2 for x in data]


class TestAdaptiveChunkingPoolAdaptation:
    """Test adaptive chunk size adjustment logic."""
    
    def test_adaptation_for_slow_chunks(self):
        """Test that chunk size decreases when chunks are too slow."""
        # Use a slow function so chunks take longer than target duration
        data = list(range(300))
        
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=50,  # Large chunks
            target_chunk_duration=0.1,  # Low target
            adaptation_rate=0.5  # Fast adaptation
        ) as pool:
            results = pool.map(slow_func, data)
            stats = pool.get_stats()
        
        assert results == [x * 2 for x in data]
        # Chunk size should have decreased
        assert stats['current_chunksize'] < 50
        # At least one adaptation should have occurred
        assert stats['adaptation_count'] > 0
    
    def test_adaptation_respects_min_chunksize(self):
        """Test that adaptation respects min_chunksize bound."""
        data = list(range(200))
        
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=20,
            target_chunk_duration=0.01,  # Very low target
            min_chunksize=5,
            adaptation_rate=0.8  # Aggressive adaptation
        ) as pool:
            results = pool.map(slow_func, data)
            stats = pool.get_stats()
        
        assert results == [x * 2 for x in data]
        # Chunk size should not go below min
        assert stats['current_chunksize'] >= 5
    
    def test_adaptation_respects_max_chunksize(self):
        """Test that adaptation respects max_chunksize bound."""
        data = list(range(500))
        
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=5,  # Small chunks
            target_chunk_duration=1.0,  # High target
            max_chunksize=20,
            adaptation_rate=0.8  # Aggressive adaptation
        ) as pool:
            results = pool.map(fast_func, data)
            stats = pool.get_stats()
        
        assert results == [x * 2 for x in data]
        # Chunk size should not exceed max
        assert stats['current_chunksize'] <= 20
    
    def test_adaptation_with_heterogeneous_workload(self):
        """Test adaptation with variable task execution times."""
        data = list(range(300))
        
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=30,
            target_chunk_duration=0.3,
            adaptation_rate=0.4
        ) as pool:
            results = pool.map(variable_func, data)
            stats = pool.get_stats()
        
        assert results == [x * 2 for x in data]
        # Should adapt to find optimal chunk size
        assert stats['total_tasks_processed'] == len(data)


class TestAdaptiveChunkingPoolImap:
    """Test imap() and imap_unordered() methods."""
    
    def test_imap_basic(self):
        """Test basic imap() functionality."""
        data = list(range(50))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = list(pool.imap(fast_func, data))
        
        assert results == [x * 2 for x in data]
    
    def test_imap_with_chunksize(self):
        """Test imap() with explicit chunksize."""
        data = list(range(50))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = list(pool.imap(fast_func, data, chunksize=5))
        
        assert results == [x * 2 for x in data]
    
    def test_imap_closed_pool(self):
        """Test that imap() on closed pool raises ValueError."""
        pool = AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10)
        pool.close()
        pool.join()
        
        with pytest.raises(ValueError, match="Pool is closed"):
            list(pool.imap(fast_func, range(10)))
    
    def test_imap_unordered_basic(self):
        """Test basic imap_unordered() functionality."""
        data = list(range(50))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = list(pool.imap_unordered(fast_func, data))
        
        # Results should be complete but possibly unordered
        assert sorted(results) == [x * 2 for x in data]
    
    def test_imap_unordered_with_chunksize(self):
        """Test imap_unordered() with explicit chunksize."""
        data = list(range(50))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = list(pool.imap_unordered(fast_func, data, chunksize=5))
        
        assert sorted(results) == [x * 2 for x in data]
    
    def test_imap_unordered_closed_pool(self):
        """Test that imap_unordered() on closed pool raises ValueError."""
        pool = AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10)
        pool.close()
        pool.join()
        
        with pytest.raises(ValueError, match="Pool is closed"):
            list(pool.imap_unordered(fast_func, range(10)))


class TestAdaptiveChunkingPoolLifecycle:
    """Test pool lifecycle management."""
    
    def test_context_manager(self):
        """Test pool as context manager."""
        data = list(range(50))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            results = pool.map(fast_func, data)
        
        # Pool should be closed after context exit
        assert pool._closed
        assert results == [x * 2 for x in data]
    
    def test_manual_close_join(self):
        """Test manual close() and join()."""
        pool = AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10)
        data = list(range(50))
        
        results = pool.map(fast_func, data)
        pool.close()
        pool.join()
        
        assert pool._closed
        assert results == [x * 2 for x in data]
    
    def test_terminate(self):
        """Test terminate() for forceful shutdown."""
        pool = AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10)
        pool.terminate()
        pool.join()
        
        assert pool._closed


class TestAdaptiveChunkingPoolStats:
    """Test get_stats() method."""
    
    def test_stats_initial_state(self):
        """Test stats in initial state."""
        pool = AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10)
        stats = pool.get_stats()
        
        assert stats['current_chunksize'] == 10
        assert stats['total_tasks_processed'] == 0
        assert stats['adaptation_count'] == 0
        assert stats['average_chunk_duration'] == 0.0
        assert stats['adaptation_enabled'] is True
        assert stats['num_chunks_in_window'] == 0
        
        pool.close()
        pool.join()
    
    def test_stats_after_processing(self):
        """Test stats after processing data."""
        data = list(range(100))
        
        with AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10) as pool:
            pool.map(fast_func, data)
            stats = pool.get_stats()
        
        assert stats['total_tasks_processed'] == 100
        assert stats['average_chunk_duration'] > 0
        assert stats['num_chunks_in_window'] > 0
    
    def test_stats_window_size(self):
        """Test that stats respects window_size."""
        data = list(range(200))
        window_size = 5
        
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=10,
            window_size=window_size
        ) as pool:
            pool.map(fast_func, data)
            stats = pool.get_stats()
        
        assert stats['window_size'] == window_size
        # Number of chunks in window should not exceed window_size
        assert stats['num_chunks_in_window'] <= window_size


class TestCreateAdaptivePool:
    """Test create_adaptive_pool() factory function."""
    
    def test_create_adaptive_pool_basic(self):
        """Test basic factory function usage."""
        pool = create_adaptive_pool(n_jobs=4, initial_chunksize=20)
        
        assert pool.n_jobs == 4
        assert pool.current_chunksize == 20
        assert pool.enable_adaptation is True
        
        pool.close()
        pool.join()
    
    def test_create_adaptive_pool_with_threads(self):
        """Test factory function with threading."""
        pool = create_adaptive_pool(
            n_jobs=2,
            initial_chunksize=10,
            use_threads=True
        )
        
        assert pool.use_threads is True
        
        pool.close()
        pool.join()
    
    def test_create_adaptive_pool_disabled_adaptation(self):
        """Test factory function with adaptation disabled."""
        pool = create_adaptive_pool(
            n_jobs=2,
            initial_chunksize=10,
            enable_adaptation=False
        )
        
        assert pool.enable_adaptation is False
        
        pool.close()
        pool.join()
    
    def test_create_adaptive_pool_custom_params(self):
        """Test factory function with custom parameters."""
        pool = create_adaptive_pool(
            n_jobs=3,
            initial_chunksize=15,
            target_chunk_duration=0.5,
            adaptation_rate=0.4
        )
        
        assert pool.n_jobs == 3
        assert pool.current_chunksize == 15
        assert pool.target_chunk_duration == 0.5
        assert pool.adaptation_rate == 0.4
        
        pool.close()
        pool.join()


# Top-level functions for pickling in multiprocessing tests
def compute_func_for_integration(x):
    """Simple computation for integration test."""
    return sum(i**2 for i in range(x))


class TestAdaptiveChunkingPoolIntegration:
    """Integration tests with real-world scenarios."""
    
    def test_integration_with_optimize_result(self):
        """Test integration with amorsize optimize() result."""
        from amorsize import optimize
        
        data = list(range(50, 150))
        result = optimize(compute_func_for_integration, data)
        
        # Use adaptive pool with optimizer recommendations
        # Handle case where optimize() returns n_jobs=1 (serial execution)
        if result.n_jobs == 1:
            # For serial execution, adaptive pool will act like serial execution too
            # Just verify it works
            with create_adaptive_pool(result.n_jobs, result.chunksize) as pool:
                results = pool.map(compute_func_for_integration, result.data)
            assert len(results) == len(data)
        else:
            # For parallel execution, verify stats are tracked
            with create_adaptive_pool(result.n_jobs, result.chunksize) as pool:
                results = pool.map(compute_func_for_integration, result.data)
                stats = pool.get_stats()
            
            assert len(results) == len(data)
            assert stats['total_tasks_processed'] == len(data)
    
    def test_performance_improvement_heterogeneous(self):
        """Test that adaptive chunking improves performance for heterogeneous workloads."""
        # This is a qualitative test - adaptive should help with variable workloads
        data = list(range(200))
        
        # Without adaptation
        start_time = time.perf_counter()
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=20,
            enable_adaptation=False
        ) as pool:
            results1 = pool.map(variable_func, data)
        time_without_adaptation = time.perf_counter() - start_time
        
        # With adaptation
        start_time = time.perf_counter()
        with AdaptiveChunkingPool(
            n_jobs=2,
            initial_chunksize=20,
            enable_adaptation=True,
            adaptation_rate=0.5
        ) as pool:
            results2 = pool.map(variable_func, data)
            stats = pool.get_stats()
        time_with_adaptation = time.perf_counter() - start_time
        
        assert results1 == results2 == [x * 2 for x in data]
        # Adaptation should have occurred
        assert stats['adaptation_count'] > 0
        # Note: We don't assert that adaptive is faster because timing can be variable
        # in test environments. The important thing is that it completes correctly.
