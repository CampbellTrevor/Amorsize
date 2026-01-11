"""
Watch mode for continuous monitoring of workload optimization.

This module provides functionality to continuously monitor a function's performance
over time, detecting changes in optimal parallelization parameters and alerting
when performance characteristics shift.
"""

import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterator, List, Optional, Union

from .optimizer import OptimizationResult, optimize


@dataclass
class WatchSnapshot:
    """A snapshot of optimization results at a specific point in time."""
    timestamp: datetime
    result: OptimizationResult
    iteration: int


class WatchMonitor:
    """
    Continuous monitoring system for workload optimization.
    
    Periodically re-optimizes a function and alerts when recommendations change
    significantly, indicating workload drift or system changes.
    """
    
    def __init__(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\n\nShutting down watch mode...")
        self.running = False
    
    def _detect_changes(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, 0.01)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= 0.5:  # 50% change threshold
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def _print_header(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def _print_snapshot(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:2]:  # Limit to first 2 warnings
                print(f"    - {warning[:100]}")  # Truncate long warnings
        
        print("-" * 80)
    
    def _print_summary(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def start(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=False,  # Skip profiling for faster monitoring
                        use_cache=False  # Don't use cache in watch mode
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self.running = False


def watch(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration
    )
    monitor.start()
