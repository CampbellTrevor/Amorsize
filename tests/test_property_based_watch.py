"""
Property-based tests for watch mode (continuous monitoring) module.

These tests use the Hypothesis library to automatically generate and test thousands
of edge cases for the watch module, including WatchSnapshot creation, WatchMonitor
initialization, change detection, signal handling, and monitoring workflow.
"""

import time
from datetime import datetime, timedelta
from threading import Thread, Barrier
from unittest.mock import MagicMock, patch
import pytest
from hypothesis import given, strategies as st, settings, assume

from amorsize.optimizer import OptimizationResult
from amorsize.watch import (
    WatchSnapshot,
    WatchMonitor,
    watch,
    MIN_SPEEDUP_FOR_RATIO,
    DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
)


# ============================================================================
# Custom Strategies
# ============================================================================

@st.composite
def valid_n_jobs(draw):
    """Generate valid n_jobs values (positive integers)."""
    return draw(st.integers(min_value=1, max_value=128))


@st.composite
def valid_chunksize(draw):
    """Generate valid chunksize values (positive integers)."""
    return draw(st.integers(min_value=1, max_value=10000))


@st.composite
def valid_speedup(draw):
    """Generate valid speedup values (positive floats)."""
    return draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_interval(draw):
    """Generate valid interval values (positive floats)."""
    return draw(st.floats(min_value=0.1, max_value=300.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_threshold_n_jobs(draw):
    """Generate valid n_jobs change thresholds."""
    return draw(st.integers(min_value=0, max_value=10))


@st.composite
def valid_threshold_speedup(draw):
    """Generate valid speedup change thresholds."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_threshold_chunksize(draw):
    """Generate valid chunksize change thresholds."""
    return draw(st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_sample_size(draw):
    """Generate valid sample sizes."""
    return draw(st.integers(min_value=1, max_value=50))


@st.composite
def valid_target_chunk_duration(draw):
    """Generate valid target chunk durations."""
    return draw(st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False))


@st.composite
def optimization_result_strategy(draw):
    """Generate valid OptimizationResult instances."""
    return OptimizationResult(
        n_jobs=draw(valid_n_jobs()),
        chunksize=draw(valid_chunksize()),
        reason="Property-based test",
        estimated_speedup=draw(valid_speedup())
    )


@st.composite
def watch_snapshot_strategy(draw):
    """Generate valid WatchSnapshot instances."""
    result = draw(optimization_result_strategy())
    # Use recent timestamps (within last hour) for realistic test data
    timestamp = datetime.now() - timedelta(seconds=draw(st.integers(min_value=0, max_value=3600)))
    iteration = draw(st.integers(min_value=1, max_value=1000))
    return WatchSnapshot(
        timestamp=timestamp,
        result=result,
        iteration=iteration
    )


def simple_test_func(x):
    """Simple test function for monitoring."""
    return x * 2


def slow_test_func(x):
    """Slower test function for monitoring."""
    time.sleep(0.0001)
    return x ** 2


# ============================================================================
# Test Classes
# ============================================================================

class TestWatchSnapshotInvariants:
    """Test invariants of WatchSnapshot dataclass."""
    
    @given(watch_snapshot_strategy())
    def test_snapshot_stores_all_fields(self, snapshot):
        """Property: WatchSnapshot stores all provided fields correctly."""
        assert isinstance(snapshot.timestamp, datetime)
        assert isinstance(snapshot.result, OptimizationResult)
        assert isinstance(snapshot.iteration, int)
        assert snapshot.iteration >= 1
    
    @given(st.lists(watch_snapshot_strategy(), min_size=2, max_size=10))
    def test_snapshot_ordering_by_iteration(self, snapshots):
        """Property: Snapshots can be ordered by iteration number."""
        sorted_snapshots = sorted(snapshots, key=lambda s: s.iteration)
        for i in range(len(sorted_snapshots) - 1):
            assert sorted_snapshots[i].iteration <= sorted_snapshots[i + 1].iteration
    
    @given(watch_snapshot_strategy())
    def test_snapshot_result_integrity(self, snapshot):
        """Property: Snapshot preserves result data without modification."""
        # Access result fields - should not raise errors
        assert snapshot.result.n_jobs >= 1
        assert snapshot.result.chunksize >= 1
        assert snapshot.result.estimated_speedup >= 0.0
        assert isinstance(snapshot.result.reason, str)
    
    @given(watch_snapshot_strategy())
    def test_snapshot_timestamp_is_valid_datetime(self, snapshot):
        """Property: Snapshot timestamp is a valid datetime object."""
        assert isinstance(snapshot.timestamp, datetime)
        # Should be able to format without errors
        timestamp_str = snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        assert len(timestamp_str) > 0


class TestWatchMonitorInitialization:
    """Test WatchMonitor initialization properties."""
    
    @given(
        valid_interval(),
        valid_threshold_n_jobs(),
        valid_threshold_speedup(),
        valid_threshold_chunksize(),
        st.booleans(),
        valid_sample_size(),
        valid_target_chunk_duration(),
        st.booleans(),
        st.booleans()
    )
    def test_monitor_stores_all_parameters(
        self, interval, threshold_n_jobs, threshold_speedup, threshold_chunksize,
        verbose, sample_size, target_chunk_duration, enable_profiling, use_cache
    ):
        """Property: WatchMonitor stores all initialization parameters correctly."""
        data = range(100)
        monitor = WatchMonitor(
            func=simple_test_func,
            data=data,
            interval=interval,
            change_threshold_n_jobs=threshold_n_jobs,
            change_threshold_speedup=threshold_speedup,
            change_threshold_chunksize=threshold_chunksize,
            verbose=verbose,
            sample_size=sample_size,
            target_chunk_duration=target_chunk_duration,
            enable_profiling=enable_profiling,
            use_cache=use_cache
        )
        
        assert monitor.func == simple_test_func
        assert monitor.data == data
        assert monitor.interval == interval
        assert monitor.change_threshold_n_jobs == threshold_n_jobs
        assert monitor.change_threshold_speedup == threshold_speedup
        assert monitor.change_threshold_chunksize == threshold_chunksize
        assert monitor.verbose == verbose
        assert monitor.sample_size == sample_size
        assert monitor.target_chunk_duration == target_chunk_duration
        assert monitor.enable_profiling == enable_profiling
        assert monitor.use_cache == use_cache
    
    @given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=1000))
    def test_monitor_accepts_various_data_types(self, data):
        """Property: WatchMonitor accepts various list-like data types."""
        monitor = WatchMonitor(func=simple_test_func, data=data)
        assert monitor.data == data
    
    def test_monitor_initial_state(self):
        """Property: WatchMonitor starts with clean initial state."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        assert len(monitor.snapshots) == 0
        assert not monitor.running
        assert monitor.iteration == 0
        assert monitor._original_sigint_handler is None
        assert monitor._original_sigterm_handler is None
    
    @given(valid_interval())
    def test_monitor_accepts_positive_interval(self, interval):
        """Property: WatchMonitor accepts any positive interval value."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100), interval=interval)
        assert monitor.interval == interval
        assert monitor.interval > 0


class TestChangeDetectionProperties:
    """Test change detection logic properties."""
    
    @given(
        optimization_result_strategy(),
        optimization_result_strategy(),
        valid_threshold_n_jobs()
    )
    def test_n_jobs_change_detection(self, prev_result, curr_result, threshold):
        """Property: n_jobs changes are detected when exceeding threshold."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            change_threshold_n_jobs=threshold
        )
        
        changes = monitor._detect_changes(prev_result, curr_result)
        
        n_jobs_diff = abs(curr_result.n_jobs - prev_result.n_jobs)
        has_n_jobs_change = any("n_jobs" in c for c in changes)
        
        if n_jobs_diff >= threshold:
            assert has_n_jobs_change
        else:
            assert not has_n_jobs_change
    
    @given(
        optimization_result_strategy(),
        optimization_result_strategy(),
        valid_threshold_speedup()
    )
    def test_speedup_change_detection(self, prev_result, curr_result, threshold):
        """Property: Speedup changes are detected when exceeding threshold ratio."""
        # Ensure prev speedup is not too close to zero to avoid division issues
        assume(prev_result.estimated_speedup >= MIN_SPEEDUP_FOR_RATIO)
        
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            change_threshold_speedup=threshold
        )
        
        changes = monitor._detect_changes(prev_result, curr_result)
        
        speedup_ratio = abs(curr_result.estimated_speedup - prev_result.estimated_speedup) / max(
            prev_result.estimated_speedup, MIN_SPEEDUP_FOR_RATIO
        )
        has_speedup_change = any("Speedup" in c for c in changes)
        
        if speedup_ratio >= threshold:
            assert has_speedup_change
        else:
            assert not has_speedup_change
    
    @given(
        optimization_result_strategy(),
        optimization_result_strategy(),
        valid_threshold_chunksize()
    )
    def test_chunksize_change_detection(self, prev_result, curr_result, threshold):
        """Property: Chunksize changes are detected when exceeding threshold ratio."""
        # Ensure prev chunksize is positive to avoid division by zero
        assume(prev_result.chunksize > 0)
        
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            change_threshold_chunksize=threshold
        )
        
        changes = monitor._detect_changes(prev_result, curr_result)
        
        chunksize_ratio = abs(curr_result.chunksize - prev_result.chunksize) / prev_result.chunksize
        has_chunksize_change = any("Chunksize" in c for c in changes)
        
        if chunksize_ratio >= threshold:
            assert has_chunksize_change
        else:
            assert not has_chunksize_change
    
    @given(optimization_result_strategy())
    def test_no_changes_when_comparing_identical_results(self, result):
        """Property: Identical results produce no change detections."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        changes = monitor._detect_changes(result, result)
        
        assert len(changes) == 0
    
    @given(
        optimization_result_strategy(),
        optimization_result_strategy(),
        valid_threshold_n_jobs(),
        valid_threshold_speedup(),
        valid_threshold_chunksize()
    )
    def test_change_detection_returns_list_of_strings(
        self, prev_result, curr_result, threshold_n_jobs, threshold_speedup, threshold_chunksize
    ):
        """Property: Change detection always returns a list of strings."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            change_threshold_n_jobs=threshold_n_jobs,
            change_threshold_speedup=threshold_speedup,
            change_threshold_chunksize=threshold_chunksize
        )
        
        changes = monitor._detect_changes(prev_result, curr_result)
        
        assert isinstance(changes, list)
        for change in changes:
            assert isinstance(change, str)
            assert len(change) > 0
    
    @given(optimization_result_strategy(), optimization_result_strategy())
    def test_change_detection_is_deterministic(self, prev_result, curr_result):
        """Property: Change detection produces consistent results for same inputs."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        changes1 = monitor._detect_changes(prev_result, curr_result)
        changes2 = monitor._detect_changes(prev_result, curr_result)
        
        assert changes1 == changes2
    
    @given(
        valid_n_jobs(),
        valid_n_jobs(),
        valid_threshold_n_jobs()
    )
    def test_n_jobs_change_includes_delta(self, prev_n_jobs, curr_n_jobs, threshold):
        """Property: n_jobs change messages include delta information."""
        assume(abs(curr_n_jobs - prev_n_jobs) >= threshold)
        
        prev_result = OptimizationResult(
            n_jobs=prev_n_jobs,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.0
        )
        curr_result = OptimizationResult(
            n_jobs=curr_n_jobs,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.0
        )
        
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            change_threshold_n_jobs=threshold
        )
        
        changes = monitor._detect_changes(prev_result, curr_result)
        
        n_jobs_changes = [c for c in changes if "n_jobs" in c]
        if n_jobs_changes:
            change_msg = n_jobs_changes[0]
            assert "→" in change_msg  # Arrow indicating change
            assert str(prev_n_jobs) in change_msg
            assert str(curr_n_jobs) in change_msg
    
    @given(
        optimization_result_strategy(),
        optimization_result_strategy()
    )
    def test_multiple_changes_detected_independently(self, prev_result, curr_result):
        """Property: Multiple types of changes can be detected simultaneously."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            change_threshold_n_jobs=0,  # Detect any n_jobs change
            change_threshold_speedup=0.0,  # Detect any speedup change
            change_threshold_chunksize=0.0  # Detect any chunksize change
        )
        
        changes = monitor._detect_changes(prev_result, curr_result)
        
        # Should detect at most 3 types of changes (n_jobs, speedup, chunksize)
        assert len(changes) <= 3


class TestConfigurationOptions:
    """Test configuration option handling."""
    
    @given(valid_interval())
    def test_custom_interval_respected(self, interval):
        """Property: Custom interval values are stored correctly."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            interval=interval
        )
        assert monitor.interval == interval
    
    @given(st.booleans(), st.booleans(), st.booleans())
    def test_boolean_flags_respected(self, verbose, enable_profiling, use_cache):
        """Property: Boolean configuration flags are stored correctly."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            verbose=verbose,
            enable_profiling=enable_profiling,
            use_cache=use_cache
        )
        
        assert monitor.verbose == verbose
        assert monitor.enable_profiling == enable_profiling
        assert monitor.use_cache == use_cache
    
    @given(
        valid_sample_size(),
        valid_target_chunk_duration()
    )
    def test_optimization_parameters_stored(self, sample_size, target_chunk_duration):
        """Property: Optimization parameters are stored correctly."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            sample_size=sample_size,
            target_chunk_duration=target_chunk_duration
        )
        
        assert monitor.sample_size == sample_size
        assert monitor.target_chunk_duration == target_chunk_duration


class TestSnapshotHistory:
    """Test snapshot history accumulation properties."""
    
    @given(st.lists(watch_snapshot_strategy(), min_size=0, max_size=20))
    def test_snapshots_accumulate_in_list(self, snapshots):
        """Property: Snapshots accumulate in order as they are added."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        for snapshot in snapshots:
            monitor.snapshots.append(snapshot)
        
        assert len(monitor.snapshots) == len(snapshots)
        for i, snapshot in enumerate(snapshots):
            assert monitor.snapshots[i] == snapshot
    
    @given(st.lists(watch_snapshot_strategy(), min_size=1, max_size=20))
    def test_snapshots_preserve_order(self, snapshots):
        """Property: Snapshot order is preserved as added."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        monitor.snapshots = snapshots.copy()
        
        for i in range(len(snapshots)):
            assert monitor.snapshots[i] == snapshots[i]
    
    @given(st.integers(min_value=1, max_value=100))
    def test_iteration_counter_increments(self, iterations):
        """Property: Iteration counter can be incremented multiple times."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        for i in range(iterations):
            monitor.iteration += 1
        
        assert monitor.iteration == iterations
    
    @given(st.lists(watch_snapshot_strategy(), min_size=2, max_size=20))
    def test_first_and_last_snapshot_accessible(self, snapshots):
        """Property: First and last snapshots can be accessed reliably."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        monitor.snapshots = snapshots.copy()
        
        assert monitor.snapshots[0] == snapshots[0]
        assert monitor.snapshots[-1] == snapshots[-1]


class TestSignalHandlerSetup:
    """Test signal handler setup and restoration."""
    
    def test_signal_handlers_initially_none(self):
        """Property: Signal handlers are None before setup."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        assert monitor._original_sigint_handler is None
        assert monitor._original_sigterm_handler is None
    
    def test_signal_handlers_stored_on_setup(self):
        """Property: Original signal handlers are stored during setup."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        monitor._setup_signal_handlers()
        
        assert monitor._original_sigint_handler is not None
        assert monitor._original_sigterm_handler is not None
        
        # Cleanup
        monitor._restore_signal_handlers()
    
    def test_signal_handlers_restored_correctly(self):
        """Property: Signal handlers are restored to originals."""
        import signal
        
        # Save original handlers
        original_sigint = signal.signal(signal.SIGINT, signal.SIG_DFL)
        original_sigterm = signal.signal(signal.SIGTERM, signal.SIG_DFL)
        
        # Restore them for the test
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
        
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        # Setup and restore
        monitor._setup_signal_handlers()
        current_sigint = signal.getsignal(signal.SIGINT)
        current_sigterm = signal.getsignal(signal.SIGTERM)
        
        # Handlers should be changed
        assert current_sigint != original_sigint
        assert current_sigterm != original_sigterm
        
        # Restore
        monitor._restore_signal_handlers()
        restored_sigint = signal.getsignal(signal.SIGINT)
        restored_sigterm = signal.getsignal(signal.SIGTERM)
        
        # Should be back to original
        assert restored_sigint == original_sigint
        assert restored_sigterm == original_sigterm


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_small_interval(self):
        """Property: Monitor accepts very small intervals."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            interval=0.1
        )
        assert monitor.interval == 0.1
    
    def test_very_large_interval(self):
        """Property: Monitor accepts large intervals."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            interval=3600.0  # 1 hour
        )
        assert monitor.interval == 3600.0
    
    def test_zero_thresholds(self):
        """Property: Monitor accepts zero thresholds (detect all changes)."""
        monitor = WatchMonitor(
            func=simple_test_func,
            data=range(100),
            change_threshold_n_jobs=0,
            change_threshold_speedup=0.0,
            change_threshold_chunksize=0.0
        )
        
        assert monitor.change_threshold_n_jobs == 0
        assert monitor.change_threshold_speedup == 0.0
        assert monitor.change_threshold_chunksize == 0.0
    
    def test_empty_snapshot_list(self):
        """Property: Monitor handles empty snapshot list gracefully."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        assert len(monitor.snapshots) == 0
        # Should be able to access snapshots without error
        assert isinstance(monitor.snapshots, list)
    
    def test_single_snapshot(self):
        """Property: Monitor handles single snapshot correctly."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        result = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.0
        )
        snapshot = WatchSnapshot(
            timestamp=datetime.now(),
            result=result,
            iteration=1
        )
        monitor.snapshots.append(snapshot)
        
        assert len(monitor.snapshots) == 1
        assert monitor.snapshots[0] == snapshot
    
    @given(st.integers(min_value=1, max_value=10000))
    def test_large_iteration_count(self, iterations):
        """Property: Monitor handles large iteration counts."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        monitor.iteration = iterations
        
        assert monitor.iteration == iterations


class TestThreadSafety:
    """Test thread safety of watch components."""
    
    @given(st.lists(watch_snapshot_strategy(), min_size=2, max_size=10))
    def test_concurrent_snapshot_access(self, snapshots):
        """Property: Concurrent snapshot list access is safe."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        monitor.snapshots = snapshots.copy()
        
        results = []
        barrier = Barrier(3)
        
        def read_snapshots():
            barrier.wait()
            # Read snapshot list
            snapshot_count = len(monitor.snapshots)
            results.append(snapshot_count)
        
        threads = [Thread(target=read_snapshots) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should read same count
        assert all(r == len(snapshots) for r in results)
    
    @given(optimization_result_strategy(), optimization_result_strategy())
    def test_concurrent_change_detection(self, prev_result, curr_result):
        """Property: Concurrent change detection calls are safe."""
        monitor = WatchMonitor(func=simple_test_func, data=range(100))
        
        results = []
        barrier = Barrier(3)
        
        def detect_changes():
            barrier.wait()
            changes = monitor._detect_changes(prev_result, curr_result)
            results.append(changes)
        
        threads = [Thread(target=detect_changes) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should get same results
        first_result = results[0]
        assert all(r == first_result for r in results)


class TestIntegrationProperties:
    """Test integration of watch components."""
    
    @given(
        valid_interval(),
        valid_threshold_n_jobs(),
        valid_threshold_speedup()
    )
    def test_monitor_snapshot_creation_workflow(
        self, interval, threshold_n_jobs, threshold_speedup
    ):
        """Property: Monitor can create snapshots from optimization results."""
        with patch('amorsize.watch.optimize') as mock_optimize:
            # Mock optimize to return a result
            mock_optimize.return_value = OptimizationResult(
                n_jobs=4,
                chunksize=10,
                reason="Test",
                estimated_speedup=2.5
            )
            
            monitor = WatchMonitor(
                func=simple_test_func,
                data=range(100),
                interval=interval,
                change_threshold_n_jobs=threshold_n_jobs,
                change_threshold_speedup=threshold_speedup
            )
            
            # Simulate one iteration
            monitor.iteration = 1
            result = mock_optimize(
                monitor.func,
                monitor.data,
                sample_size=monitor.sample_size,
                target_chunk_duration=monitor.target_chunk_duration,
                verbose=False,
                profile=monitor.enable_profiling,
                use_cache=monitor.use_cache
            )
            
            snapshot = WatchSnapshot(
                timestamp=datetime.now(),
                result=result,
                iteration=monitor.iteration
            )
            monitor.snapshots.append(snapshot)
            
            # Verify workflow
            assert len(monitor.snapshots) == 1
            assert monitor.snapshots[0].result.n_jobs == 4
            assert monitor.snapshots[0].iteration == 1
    
    @patch('amorsize.watch.WatchMonitor')
    def test_watch_function_delegates_to_monitor(self, mock_monitor_class):
        """Property: watch() function creates monitor and starts it."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        data = range(100)
        
        watch(
            func=simple_test_func,
            data=data,
            interval=30.0,
            verbose=True
        )
        
        # Verify monitor was created
        mock_monitor_class.assert_called_once()
        
        # Verify start was called
        mock_monitor.start.assert_called_once()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
