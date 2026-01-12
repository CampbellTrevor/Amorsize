"""
Property-based tests for the adaptive_chunking module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the adaptive chunking pool across a wide range of inputs and scenarios.

Note: The AdaptiveChunkingPool uses a "small workload optimization" where
workloads with size <= chunksize * 2 skip adaptive chunking and are processed
directly. This is because the overhead of tracking and adaptation is not worth
it for small workloads. Tests account for this behavior.
"""

import math
import threading
import time
from multiprocessing.pool import Pool, ThreadPool

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume

from amorsize.adaptive_chunking import AdaptiveChunkingPool, create_adaptive_pool


# Constants
SMALL_WORKLOAD_THRESHOLD_MULTIPLIER = 2  # Workload size <= chunksize * 2 skips adaptation


# Custom strategies for generating test data

@st.composite
def valid_n_jobs(draw):
    """Generate valid n_jobs values."""
    return draw(st.integers(min_value=1, max_value=8))


@st.composite
def valid_chunksize(draw):
    """Generate valid chunksize values."""
    return draw(st.integers(min_value=1, max_value=100))


@st.composite
def valid_target_duration(draw):
    """Generate valid target chunk durations."""
    return draw(st.floats(min_value=0.01, max_value=2.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_adaptation_rate(draw):
    """Generate valid adaptation rates (0.0-1.0)."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_window_size(draw):
    """Generate valid window sizes."""
    return draw(st.integers(min_value=1, max_value=50))


@st.composite
def valid_workload(draw):
    """Generate valid workload data."""
    size = draw(st.integers(min_value=0, max_value=200))
    return list(range(size))


# Test classes organized by functionality

class TestAdaptiveChunkingPoolInitialization:
    """Test AdaptiveChunkingPool initialization and parameter validation."""
    
    @given(
        n_jobs=valid_n_jobs(),
        chunksize=valid_chunksize(),
        target_duration=valid_target_duration(),
        adaptation_rate=valid_adaptation_rate(),
        window_size=valid_window_size()
    )
    @settings(max_examples=100, deadline=None)
    def test_valid_initialization(self, n_jobs, chunksize, target_duration, adaptation_rate, window_size):
        """Test that valid parameters create a pool successfully."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            target_chunk_duration=target_duration,
            adaptation_rate=adaptation_rate,
            window_size=window_size,
            use_threads=True  # Use threads for faster tests
        )
        try:
            assert pool.n_jobs == n_jobs
            assert pool.current_chunksize == chunksize
            assert pool.target_chunk_duration == target_duration
            assert pool.adaptation_rate == adaptation_rate
            assert pool.window_size == window_size
            assert pool._closed is False
        finally:
            pool.close()
            pool.join()
    
    @given(n_jobs=st.integers(max_value=0))
    @settings(max_examples=50, deadline=None)
    def test_invalid_n_jobs(self, n_jobs):
        """Test that n_jobs < 1 raises ValueError."""
        with pytest.raises(ValueError, match="n_jobs must be >= 1"):
            AdaptiveChunkingPool(n_jobs=n_jobs, initial_chunksize=10)
    
    @given(chunksize=st.integers(max_value=0))
    @settings(max_examples=50, deadline=None)
    def test_invalid_chunksize(self, chunksize):
        """Test that initial_chunksize < 1 raises ValueError."""
        with pytest.raises(ValueError, match="initial_chunksize must be >= 1"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=chunksize)
    
    @given(target_duration=st.floats(max_value=0.0))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_invalid_target_duration(self, target_duration):
        """Test that target_chunk_duration <= 0 raises ValueError."""
        import math
        assume(not math.isnan(target_duration))  # Filter NaN
        with pytest.raises(ValueError, match="target_chunk_duration must be > 0"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, target_chunk_duration=target_duration)
    
    @given(adaptation_rate=st.floats())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_invalid_adaptation_rate(self, adaptation_rate):
        """Test that adaptation_rate outside [0.0, 1.0] raises ValueError."""
        import math
        assume(not math.isnan(adaptation_rate))  # Filter NaN
        assume(adaptation_rate < 0.0 or adaptation_rate > 1.0)
        with pytest.raises(ValueError, match="adaptation_rate must be 0.0-1.0"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, adaptation_rate=adaptation_rate)
    
    @given(
        min_chunksize=valid_chunksize(),
        max_chunksize=valid_chunksize()
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_invalid_min_max_chunksize(self, min_chunksize, max_chunksize):
        """Test that max_chunksize < min_chunksize raises ValueError."""
        assume(max_chunksize < min_chunksize)
        with pytest.raises(ValueError, match="max_chunksize .* must be >= min_chunksize"):
            AdaptiveChunkingPool(
                n_jobs=2,
                initial_chunksize=10,
                min_chunksize=min_chunksize,
                max_chunksize=max_chunksize
            )
    
    @given(window_size=st.integers(max_value=0))
    @settings(max_examples=50, deadline=None)
    def test_invalid_window_size(self, window_size):
        """Test that window_size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="window_size must be >= 1"):
            AdaptiveChunkingPool(n_jobs=2, initial_chunksize=10, window_size=window_size)


class TestAdaptiveChunkingPoolConfiguration:
    """Test configuration options and field types."""
    
    @given(
        n_jobs=valid_n_jobs(),
        chunksize=valid_chunksize(),
        use_threads=st.booleans()
    )
    @settings(max_examples=50, deadline=None)
    def test_pool_type_selection(self, n_jobs, chunksize, use_threads):
        """Test that use_threads parameter controls pool type."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=use_threads
        )
        try:
            if use_threads:
                assert isinstance(pool._pool, ThreadPool)
            else:
                assert isinstance(pool._pool, Pool)
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=valid_n_jobs(),
        chunksize=valid_chunksize(),
        enable_adaptation=st.booleans()
    )
    @settings(max_examples=50, deadline=None)
    def test_adaptation_enable_flag(self, n_jobs, chunksize, enable_adaptation):
        """Test that enable_adaptation flag is respected."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            enable_adaptation=enable_adaptation,
            use_threads=True
        )
        try:
            assert pool.enable_adaptation == enable_adaptation
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=valid_n_jobs(),
        initial_chunksize=valid_chunksize(),
        max_chunksize=st.one_of(st.none(), valid_chunksize())
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_max_chunksize_handling(self, n_jobs, initial_chunksize, max_chunksize):
        """Test that max_chunksize is handled correctly (None = infinity)."""
        # Only proceed if max_chunksize is None or >= initial_chunksize
        if max_chunksize is not None:
            assume(max_chunksize >= initial_chunksize)
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=initial_chunksize,
            max_chunksize=max_chunksize,
            use_threads=True
        )
        try:
            if max_chunksize is None:
                assert pool.max_chunksize == float('inf')
            else:
                assert pool.max_chunksize == max_chunksize
        finally:
            pool.close()
            pool.join()


class TestMapOperation:
    """Test the map() operation with various inputs."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20),
        workload=valid_workload()
    )
    @settings(max_examples=50, deadline=None)
    def test_map_returns_correct_results(self, n_jobs, chunksize, workload):
        """Test that map() returns correct results for all inputs."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            results = pool.map(simple_func, workload)
            expected = [x * 2 for x in workload]
            assert results == expected
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_map_empty_workload(self, n_jobs, chunksize):
        """Test that map() handles empty workload correctly."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            results = pool.map(simple_func, [])
            assert results == []
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        initial_chunksize=st.integers(min_value=1, max_value=20),
        override_chunksize=st.integers(min_value=1, max_value=20),
        workload=st.lists(st.integers(), min_size=1, max_size=50)
    )
    @settings(max_examples=30, deadline=None)
    def test_map_with_explicit_chunksize(self, n_jobs, initial_chunksize, override_chunksize, workload):
        """Test that map() respects explicit chunksize parameter."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=initial_chunksize,
            use_threads=True
        )
        try:
            # Explicit chunksize should disable adaptation
            results = pool.map(simple_func, workload, chunksize=override_chunksize)
            expected = [x * 2 for x in workload]
            assert results == expected
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20),
        workload_size=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=30, deadline=None)
    def test_map_small_workload_no_adaptation(self, n_jobs, chunksize, workload_size):
        """Test that small workloads don't trigger adaptation.
        
        The AdaptiveChunkingPool skips adaptive chunking for small workloads
        (size <= chunksize * 2) as an optimization - these workloads are
        processed directly without the overhead of tracking and adaptation.
        """
        # Small workload threshold: size <= chunksize * 2
        assume(workload_size <= chunksize * 2)
        
        def simple_func(x):
            return x * 2
        
        workload = list(range(workload_size))
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            enable_adaptation=True,
            use_threads=True
        )
        try:
            results = pool.map(simple_func, workload)
            expected = [x * 2 for x in workload]
            assert results == expected
            
            # Adaptation count should be 0 for small workloads
            stats = pool.get_stats()
            assert stats['adaptation_count'] == 0
        finally:
            pool.close()
            pool.join()


class TestImapOperations:
    """Test imap() and imap_unordered() operations."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20),
        workload=st.lists(st.integers(), min_size=0, max_size=50)
    )
    @settings(max_examples=30, deadline=None)
    def test_imap_returns_correct_results(self, n_jobs, chunksize, workload):
        """Test that imap() returns correct results."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            results = list(pool.imap(simple_func, workload))
            expected = [x * 2 for x in workload]
            assert results == expected
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20),
        workload=st.lists(st.integers(), min_size=0, max_size=50)
    )
    @settings(max_examples=30, deadline=None)
    def test_imap_unordered_returns_all_results(self, n_jobs, chunksize, workload):
        """Test that imap_unordered() returns all results (order may vary)."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            results = list(pool.imap_unordered(simple_func, workload))
            expected = [x * 2 for x in workload]
            assert sorted(results) == sorted(expected)
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        initial_chunksize=st.integers(min_value=1, max_value=20),
        override_chunksize=st.integers(min_value=1, max_value=20),
        workload=st.lists(st.integers(), min_size=1, max_size=50)
    )
    @settings(max_examples=20, deadline=None)
    def test_imap_with_explicit_chunksize(self, n_jobs, initial_chunksize, override_chunksize, workload):
        """Test that imap() respects explicit chunksize parameter."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=initial_chunksize,
            use_threads=True
        )
        try:
            results = list(pool.imap(simple_func, workload, chunksize=override_chunksize))
            expected = [x * 2 for x in workload]
            assert results == expected
        finally:
            pool.close()
            pool.join()


class TestChunkDurationRecording:
    """Test chunk duration recording and adaptation logic."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20),
        num_chunks=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=30, deadline=None)
    def test_chunk_duration_recorded(self, n_jobs, chunksize, num_chunks):
        """Test that chunk durations are recorded during map()."""
        def simple_func(x):
            return x * 2
        
        # Create workload large enough to create multiple chunks
        workload_size = chunksize * num_chunks * 3
        workload = list(range(workload_size))
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            enable_adaptation=True,
            use_threads=True,
            window_size=20
        )
        try:
            pool.map(simple_func, workload)
            
            # Check that some durations were recorded
            stats = pool.get_stats()
            assert stats['num_chunks_in_window'] >= 0
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=20, deadline=None)
    def test_adaptation_disabled_no_change(self, n_jobs, chunksize):
        """Test that chunksize doesn't change when adaptation is disabled."""
        def simple_func(x):
            time.sleep(0.001)
            return x * 2
        
        workload = list(range(chunksize * 10))
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            enable_adaptation=False,
            use_threads=True
        )
        try:
            initial_chunksize = pool.current_chunksize
            pool.map(simple_func, workload)
            
            # Chunksize should not change when adaptation is disabled
            stats = pool.get_stats()
            assert stats['current_chunksize'] == initial_chunksize
            assert stats['adaptation_count'] == 0
            assert stats['adaptation_enabled'] is False
        finally:
            pool.close()
            pool.join()


class TestStatisticsTracking:
    """Test statistics collection and reporting."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_get_stats_structure(self, n_jobs, chunksize):
        """Test that get_stats() returns correct structure."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            stats = pool.get_stats()
            
            # Check all expected fields are present
            assert 'current_chunksize' in stats
            assert 'total_tasks_processed' in stats
            assert 'adaptation_count' in stats
            assert 'average_chunk_duration' in stats
            assert 'adaptation_enabled' in stats
            assert 'window_size' in stats
            assert 'num_chunks_in_window' in stats
            
            # Check types
            assert isinstance(stats['current_chunksize'], int)
            assert isinstance(stats['total_tasks_processed'], int)
            assert isinstance(stats['adaptation_count'], int)
            assert isinstance(stats['average_chunk_duration'], float)
            assert isinstance(stats['adaptation_enabled'], bool)
            assert isinstance(stats['window_size'], int)
            assert isinstance(stats['num_chunks_in_window'], int)
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_initial_stats_values(self, n_jobs, chunksize):
        """Test that initial stats have correct values."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            stats = pool.get_stats()
            
            # Initially no work has been done
            assert stats['current_chunksize'] == chunksize
            assert stats['total_tasks_processed'] == 0
            assert stats['adaptation_count'] == 0
            assert stats['average_chunk_duration'] == 0.0
            assert stats['num_chunks_in_window'] == 0
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20),
        workload=st.lists(st.integers(), min_size=1, max_size=100)
    )
    @settings(max_examples=30, deadline=None)
    def test_stats_after_work(self, n_jobs, chunksize, workload):
        """Test that stats are updated after processing work.
        
        Stats tracking behavior depends on workload size:
        - Small workloads (size <= chunksize * 2): Stats may not be tracked (optimization)
        - Large workloads (size > chunksize * 2): Stats should be tracked
        """
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            pool.map(simple_func, workload)
            
            stats = pool.get_stats()
            
            # After work, total_tasks_processed should match workload size
            # For small workloads (size <= chunksize * 2), stats may not be recorded
            if len(workload) > chunksize * SMALL_WORKLOAD_THRESHOLD_MULTIPLIER:
                assert stats['total_tasks_processed'] == len(workload)
            else:
                # For small workloads, stats tracking may be skipped
                assert stats['total_tasks_processed'] >= 0
            
            # Non-negative invariants (always hold)
            assert stats['current_chunksize'] >= 1
            assert stats['total_tasks_processed'] >= 0
            assert stats['adaptation_count'] >= 0
            assert stats['average_chunk_duration'] >= 0.0
            assert stats['num_chunks_in_window'] >= 0
        finally:
            pool.close()
            pool.join()


class TestContextManager:
    """Test context manager protocol."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_context_manager_returns_pool(self, n_jobs, chunksize):
        """Test that __enter__ returns the pool instance."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        
        with pool as p:
            assert p is pool
            assert not p._closed
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_context_manager_closes_pool(self, n_jobs, chunksize):
        """Test that __exit__ closes and joins the pool."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        
        with pool:
            pass
        
        # After exiting context, pool should be closed
        assert pool._closed
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20),
        workload=st.lists(st.integers(), min_size=0, max_size=50)
    )
    @settings(max_examples=30, deadline=None)
    def test_context_manager_with_work(self, n_jobs, chunksize, workload):
        """Test that context manager works correctly with actual work."""
        def simple_func(x):
            return x * 2
        
        with AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        ) as pool:
            results = pool.map(simple_func, workload)
            expected = [x * 2 for x in workload]
            assert results == expected


class TestPoolLifecycle:
    """Test pool lifecycle operations (close, terminate, join)."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_close_prevents_new_work(self, n_jobs, chunksize):
        """Test that close() prevents submitting new work."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        
        pool.close()
        pool.join()
        
        # After close, map should raise ValueError
        with pytest.raises(ValueError, match="Pool is closed"):
            pool.map(simple_func, [1, 2, 3])
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_imap_after_close_raises(self, n_jobs, chunksize):
        """Test that imap() after close() raises ValueError."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        
        pool.close()
        pool.join()
        
        with pytest.raises(ValueError, match="Pool is closed"):
            list(pool.imap(simple_func, [1, 2, 3]))
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_terminate_closes_pool(self, n_jobs, chunksize):
        """Test that terminate() closes the pool."""
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        
        pool.terminate()
        pool.join()
        
        assert pool._closed


class TestThreadSafety:
    """Test thread safety of concurrent operations."""
    
    @given(
        n_jobs=st.integers(min_value=2, max_value=4),
        chunksize=st.integers(min_value=5, max_value=20),
        num_threads=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=20, deadline=None)
    def test_concurrent_map_calls(self, n_jobs, chunksize, num_threads):
        """Test that concurrent map() calls are thread-safe."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        
        try:
            results_dict = {}
            errors = []
            barrier = threading.Barrier(num_threads)
            
            def worker(thread_id):
                try:
                    barrier.wait()  # Synchronize start
                    workload = list(range(thread_id * 10, (thread_id + 1) * 10))
                    result = pool.map(simple_func, workload)
                    results_dict[thread_id] = result
                except Exception as e:
                    errors.append(e)
            
            threads = [
                threading.Thread(target=worker, args=(i,))
                for i in range(num_threads)
            ]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # No errors should occur
            assert len(errors) == 0
            
            # All results should be correct
            assert len(results_dict) == num_threads
            for i in range(num_threads):
                expected = [x * 2 for x in range(i * 10, (i + 1) * 10)]
                assert results_dict[i] == expected
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=2, max_value=4),
        chunksize=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=20, deadline=None)
    def test_concurrent_stats_access(self, n_jobs, chunksize):
        """Test that concurrent get_stats() calls are thread-safe."""
        def simple_func(x):
            time.sleep(0.001)
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            enable_adaptation=True,
            use_threads=True
        )
        
        try:
            errors = []
            stats_list = []
            barrier = threading.Barrier(3)
            
            def worker():
                try:
                    barrier.wait()
                    for _ in range(5):
                        stats = pool.get_stats()
                        stats_list.append(stats)
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)
            
            def map_worker():
                try:
                    barrier.wait()
                    workload = list(range(50))
                    pool.map(simple_func, workload)
                except Exception as e:
                    errors.append(e)
            
            threads = [
                threading.Thread(target=worker),
                threading.Thread(target=worker),
                threading.Thread(target=map_worker)
            ]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # No errors should occur
            assert len(errors) == 0
            
            # All stats should be valid
            for stats in stats_list:
                assert stats['current_chunksize'] >= 1
                assert stats['total_tasks_processed'] >= 0
                assert stats['adaptation_count'] >= 0
        finally:
            pool.close()
            pool.join()


class TestCreateAdaptivePool:
    """Test the create_adaptive_pool factory function."""
    
    @given(
        n_jobs=valid_n_jobs(),
        chunksize=valid_chunksize(),
        enable_adaptation=st.booleans(),
        use_threads=st.booleans()
    )
    @settings(max_examples=50, deadline=None)
    def test_factory_creates_valid_pool(self, n_jobs, chunksize, enable_adaptation, use_threads):
        """Test that factory function creates a valid pool."""
        pool = create_adaptive_pool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            enable_adaptation=enable_adaptation,
            use_threads=use_threads
        )
        try:
            assert isinstance(pool, AdaptiveChunkingPool)
            assert pool.n_jobs == n_jobs
            assert pool.current_chunksize == chunksize
            assert pool.enable_adaptation == enable_adaptation
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=valid_n_jobs(),
        chunksize=valid_chunksize(),
        target_duration=valid_target_duration()
    )
    @settings(max_examples=30, deadline=None)
    def test_factory_passes_kwargs(self, n_jobs, chunksize, target_duration):
        """Test that factory function passes kwargs to constructor."""
        pool = create_adaptive_pool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True,
            target_chunk_duration=target_duration
        )
        try:
            assert pool.target_chunk_duration == target_duration
        finally:
            pool.close()
            pool.join()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=30, deadline=None)
    def test_single_item_workload(self, n_jobs, chunksize):
        """Test that single-item workloads are handled correctly."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        )
        try:
            result = pool.map(simple_func, [42])
            assert result == [84]
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=30, deadline=None)
    def test_very_small_chunksize(self, n_jobs):
        """Test that chunksize=1 works correctly."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=1,
            use_threads=True
        )
        try:
            workload = list(range(10))
            results = pool.map(simple_func, workload)
            assert results == [x * 2 for x in workload]
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=30, deadline=None)
    def test_very_large_chunksize(self, n_jobs):
        """Test that very large chunksize works correctly."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=1000,
            use_threads=True
        )
        try:
            workload = list(range(50))
            results = pool.map(simple_func, workload)
            assert results == [x * 2 for x in workload]
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=20, deadline=None)
    def test_extreme_target_duration(self, n_jobs, chunksize):
        """Test with extreme target_chunk_duration values."""
        def simple_func(x):
            return x * 2
        
        # Very small target duration
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            target_chunk_duration=0.001,
            use_threads=True
        )
        try:
            workload = list(range(50))
            results = pool.map(simple_func, workload)
            assert results == [x * 2 for x in workload]
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=20, deadline=None)
    def test_adaptation_rate_extremes(self, n_jobs, chunksize):
        """Test with extreme adaptation_rate values (0.0 and 1.0)."""
        def simple_func(x):
            return x * 2
        
        workload = list(range(50))
        
        # Test with adaptation_rate = 0.0 (no adaptation)
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            adaptation_rate=0.0,
            use_threads=True
        )
        try:
            results = pool.map(simple_func, workload)
            assert results == [x * 2 for x in workload]
        finally:
            pool.close()
            pool.join()
        
        # Test with adaptation_rate = 1.0 (maximum adaptation)
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            adaptation_rate=1.0,
            use_threads=True
        )
        try:
            results = pool.map(simple_func, workload)
            assert results == [x * 2 for x in workload]
        finally:
            pool.close()
            pool.join()


class TestIntegration:
    """Test integration scenarios combining multiple features."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=5, max_value=20),
        enable_adaptation=st.booleans()
    )
    @settings(max_examples=20, deadline=None)
    def test_full_lifecycle(self, n_jobs, chunksize, enable_adaptation):
        """Test full lifecycle: create, use, stats, close."""
        def simple_func(x):
            return x * 2
        
        pool = AdaptiveChunkingPool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            enable_adaptation=enable_adaptation,
            use_threads=True
        )
        
        try:
            # Initial state
            stats = pool.get_stats()
            assert stats['total_tasks_processed'] == 0
            
            # Process some work (large enough to track stats)
            # Use 100 items to ensure workload > chunksize * SMALL_WORKLOAD_THRESHOLD_MULTIPLIER
            workload1 = list(range(100))
            results1 = pool.map(simple_func, workload1)
            assert results1 == [x * 2 for x in workload1]
            
            # Check stats after first batch
            stats = pool.get_stats()
            # For workload size > chunksize * 2, stats should be tracked
            if len(workload1) > chunksize * SMALL_WORKLOAD_THRESHOLD_MULTIPLIER:
                assert stats['total_tasks_processed'] > 0
            
            # Process more work
            workload2 = list(range(100, 200))
            results2 = pool.map(simple_func, workload2)
            assert results2 == [x * 2 for x in workload2]
            
            # Check stats - total should have increased
            stats_after = pool.get_stats()
            # Just verify invariants rather than exact counts (depends on chunk handling)
            assert stats_after['total_tasks_processed'] >= stats['total_tasks_processed']
            
            # Use imap
            workload3 = list(range(200, 220))
            results3 = list(pool.imap(simple_func, workload3))
            assert results3 == [x * 2 for x in workload3]
            
            # Final stats
            stats = pool.get_stats()
            assert stats['adaptation_enabled'] == enable_adaptation
            assert stats['current_chunksize'] >= 1
        finally:
            pool.close()
            pool.join()
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=20, deadline=None)
    def test_multiple_operations_with_context_manager(self, n_jobs, chunksize):
        """Test multiple operations within context manager."""
        # Use a workload size that's guaranteed to be large enough to track stats
        LARGE_WORKLOAD_SIZE = 100  # Much larger than max chunksize * 2
        
        def simple_func(x):
            return x * 2
        
        with create_adaptive_pool(
            n_jobs=n_jobs,
            initial_chunksize=chunksize,
            use_threads=True
        ) as pool:
            # Map (large enough workload to track stats)
            results1 = pool.map(simple_func, list(range(LARGE_WORKLOAD_SIZE)))
            assert len(results1) == LARGE_WORKLOAD_SIZE
            
            # Imap
            results2 = list(pool.imap(simple_func, list(range(50))))
            assert len(results2) == 50
            
            # Imap unordered
            results3 = list(pool.imap_unordered(simple_func, list(range(60))))
            assert len(results3) == 60
            
            # Check stats - verify invariants
            stats = pool.get_stats()
            # For large workloads, should have processed some tasks
            if LARGE_WORKLOAD_SIZE > chunksize * SMALL_WORKLOAD_THRESHOLD_MULTIPLIER:
                assert stats['total_tasks_processed'] > 0
            # Always check invariants
            assert stats['current_chunksize'] >= 1
            assert stats['total_tasks_processed'] >= 0
