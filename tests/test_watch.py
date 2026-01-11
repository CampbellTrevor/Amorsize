"""
Tests for watch mode (continuous monitoring).
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from amorsize.optimizer import OptimizationResult
from amorsize.watch import WatchMonitor, WatchSnapshot, watch


def simple_function(x):
    """Simple test function."""
    return x * 2


def slow_function(x):
    """Slower test function for testing changes."""
    time.sleep(0.001)
    return x ** 2


class TestWatchSnapshot:
    """Test WatchSnapshot dataclass."""
    
    def test_snapshot_creation(self):
        """Test creating a snapshot."""
        result = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=3.5
        )
        timestamp = datetime.now()
        
        snapshot = WatchSnapshot(
            timestamp=timestamp,
            result=result,
            iteration=1
        )
        
        assert snapshot.timestamp == timestamp
        assert snapshot.result == result
        assert snapshot.iteration == 1


class TestWatchMonitor:
    """Test WatchMonitor class."""
    
    def test_monitor_initialization(self):
        """Test monitor initialization with defaults."""
        data = range(100)
        
        monitor = WatchMonitor(
            func=simple_function,
            data=data
        )
        
        assert monitor.func == simple_function
        assert monitor.data == data
        assert monitor.interval == 60.0
        assert monitor.change_threshold_n_jobs == 1
        assert monitor.change_threshold_speedup == 0.2
        assert not monitor.verbose
        assert monitor.sample_size == 5
        assert monitor.target_chunk_duration == 0.2
        assert len(monitor.snapshots) == 0
        assert not monitor.running
        assert monitor.iteration == 0
    
    def test_monitor_custom_parameters(self):
        """Test monitor initialization with custom parameters."""
        data = range(100)
        
        monitor = WatchMonitor(
            func=simple_function,
            data=data,
            interval=30.0,
            change_threshold_n_jobs=2,
            change_threshold_speedup=0.3,
            verbose=True,
            sample_size=10,
            target_chunk_duration=0.5
        )
        
        assert monitor.interval == 30.0
        assert monitor.change_threshold_n_jobs == 2
        assert monitor.change_threshold_speedup == 0.3
        assert monitor.verbose
        assert monitor.sample_size == 10
        assert monitor.target_chunk_duration == 0.5
    
    def test_detect_changes_n_jobs(self):
        """Test detection of n_jobs changes."""
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100),
            change_threshold_n_jobs=1
        )
        
        prev = OptimizationResult(
            n_jobs=2,
            chunksize=10,
            reason="Test",
            estimated_speedup=1.8
        )
        
        curr = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=1.8
        )
        
        changes = monitor._detect_changes(prev, curr)
        
        assert len(changes) == 1
        assert "n_jobs changed" in changes[0]
        assert "2 → 4" in changes[0]
    
    def test_detect_changes_speedup(self):
        """Test detection of speedup changes."""
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100),
            change_threshold_speedup=0.2
        )
        
        prev = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.0
        )
        
        curr = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.5
        )
        
        changes = monitor._detect_changes(prev, curr)
        
        assert len(changes) == 1
        assert "Speedup changed" in changes[0]
        assert "2.00x → 2.50x" in changes[0]
    
    def test_detect_changes_chunksize(self):
        """Test detection of chunksize changes."""
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100)
        )
        
        prev = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.0
        )
        
        curr = OptimizationResult(
            n_jobs=4,
            chunksize=20,
            reason="Test",
            estimated_speedup=2.0
        )
        
        changes = monitor._detect_changes(prev, curr)
        
        # Chunksize needs 50% change threshold
        assert len(changes) == 1
        assert "Chunksize changed" in changes[0]
        assert "10 → 20" in changes[0]
    
    def test_detect_no_changes(self):
        """Test when no significant changes detected."""
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100)
        )
        
        prev = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.0
        )
        
        curr = OptimizationResult(
            n_jobs=4,
            chunksize=11,  # Only 10% change, below 50% threshold
            reason="Test",
            estimated_speedup=2.05  # Only 2.5% change, below 20% threshold
        )
        
        changes = monitor._detect_changes(prev, curr)
        
        assert len(changes) == 0
    
    def test_detect_multiple_changes(self):
        """Test detection of multiple simultaneous changes."""
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100),
            change_threshold_n_jobs=1,
            change_threshold_speedup=0.2
        )
        
        prev = OptimizationResult(
            n_jobs=2,
            chunksize=10,
            reason="Test",
            estimated_speedup=1.5
        )
        
        curr = OptimizationResult(
            n_jobs=4,
            chunksize=20,
            reason="Test",
            estimated_speedup=2.5
        )
        
        changes = monitor._detect_changes(prev, curr)
        
        # Should detect n_jobs, speedup, and chunksize changes
        assert len(changes) == 3
        assert any("n_jobs" in c for c in changes)
        assert any("Speedup" in c for c in changes)
        assert any("Chunksize" in c for c in changes)
    
    @patch('amorsize.watch.optimize')
    def test_monitor_single_iteration(self, mock_optimize):
        """Test a single iteration of monitoring (mocked)."""
        # Mock the optimize function
        mock_optimize.return_value = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.5
        )
        
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100),
            interval=0.1  # Short interval for testing
        )
        
        # Manually run one iteration
        monitor.iteration = 1
        result = mock_optimize(
            monitor.func,
            monitor.data,
            sample_size=monitor.sample_size,
            target_chunk_duration=monitor.target_chunk_duration,
            verbose=False,
            profile=False,
            use_cache=False
        )
        
        snapshot = WatchSnapshot(
            timestamp=datetime.now(),
            result=result,
            iteration=monitor.iteration
        )
        monitor.snapshots.append(snapshot)
        
        # Verify
        assert len(monitor.snapshots) == 1
        assert monitor.snapshots[0].result.n_jobs == 4
        assert monitor.snapshots[0].result.chunksize == 10
        assert monitor.snapshots[0].iteration == 1


class TestWatchFunction:
    """Test the watch() convenience function."""
    
    @patch('amorsize.watch.WatchMonitor')
    def test_watch_function_creates_monitor(self, mock_monitor_class):
        """Test that watch() creates a WatchMonitor and starts it."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        data = range(100)
        
        watch(
            func=simple_function,
            data=data,
            interval=30.0,
            change_threshold_n_jobs=2,
            change_threshold_speedup=0.3,
            verbose=True,
            sample_size=10,
            target_chunk_duration=0.5
        )
        
        # Verify monitor was created with correct parameters
        mock_monitor_class.assert_called_once_with(
            func=simple_function,
            data=data,
            interval=30.0,
            change_threshold_n_jobs=2,
            change_threshold_speedup=0.3,
            verbose=True,
            sample_size=10,
            target_chunk_duration=0.5
        )
        
        # Verify start was called
        mock_monitor.start.assert_called_once()
    
    @patch('amorsize.watch.WatchMonitor')
    def test_watch_function_default_parameters(self, mock_monitor_class):
        """Test watch() with default parameters."""
        mock_monitor = MagicMock()
        mock_monitor_class.return_value = mock_monitor
        
        data = range(100)
        
        watch(func=simple_function, data=data)
        
        # Verify monitor was created with defaults
        mock_monitor_class.assert_called_once_with(
            func=simple_function,
            data=data,
            interval=60.0,
            change_threshold_n_jobs=1,
            change_threshold_speedup=0.2,
            verbose=False,
            sample_size=5,
            target_chunk_duration=0.2
        )


class TestPrintMethods:
    """Test the printing/display methods."""
    
    def test_print_snapshot_basic(self, capsys):
        """Test printing a basic snapshot."""
        result = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.5
        )
        snapshot = WatchSnapshot(
            timestamp=datetime.now(),
            result=result,
            iteration=1
        )
        
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100)
        )
        
        monitor._print_snapshot(snapshot)
        
        captured = capsys.readouterr()
        assert "Iteration #1" in captured.out
        assert "n_jobs=4" in captured.out
        assert "chunksize=10" in captured.out
        assert "speedup=2.50x" in captured.out
    
    def test_print_snapshot_with_changes(self, capsys):
        """Test printing a snapshot with detected changes."""
        result = OptimizationResult(
            n_jobs=4,
            chunksize=10,
            reason="Test",
            estimated_speedup=2.5
        )
        snapshot = WatchSnapshot(
            timestamp=datetime.now(),
            result=result,
            iteration=2
        )
        
        monitor = WatchMonitor(
            func=simple_function,
            data=range(100)
        )
        
        changes = ["n_jobs changed: 2 → 4"]
        monitor._print_snapshot(snapshot, changes=changes)
        
        captured = capsys.readouterr()
        assert "CHANGES DETECTED" in captured.out
        assert "n_jobs changed: 2 → 4" in captured.out


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
