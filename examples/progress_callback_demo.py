"""
Progress Callback Demo - Monitoring Long-Running Optimizations

This example demonstrates how to use progress callbacks to monitor
the optimization process in real-time.
"""

import time
from amorsize import optimize


def example_1_basic_progress():
    """Example 1: Basic progress callback."""
    print("=" * 70)
    print("Example 1: Basic Progress Callback")
    print("=" * 70)
    
    def progress_callback(phase: str, progress: float):
        """Simple progress callback that prints updates."""
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r{phase:30s} [{bar}] {progress*100:5.1f}%", end="", flush=True)
    
    def expensive_function(x):
        """Simulate expensive computation."""
        result = 0
        for i in range(10000):
            result += x ** 2
        return result
    
    data = list(range(200))
    result = optimize(expensive_function, data, progress_callback=progress_callback)
    print()  # New line after progress bar
    
    print(f"\nRecommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Expected speedup: {result.estimated_speedup:.2f}x")


def example_2_detailed_logging():
    """Example 2: Detailed logging with timestamps."""
    print("\n" + "=" * 70)
    print("Example 2: Detailed Logging with Timestamps")
    print("=" * 70)
    
    start_time = time.time()
    
    def detailed_callback(phase: str, progress: float):
        """Callback that logs detailed information."""
        elapsed = time.time() - start_time
        print(f"[{elapsed:6.3f}s] {progress*100:5.1f}% - {phase}")
    
    def computation_heavy(x):
        """CPU-intensive function."""
        result = sum(i ** 2 for i in range(5000))
        return result + x
    
    data = list(range(300))
    result = optimize(
        computation_heavy, 
        data, 
        sample_size=10,
        progress_callback=detailed_callback
    )
    
    print(f"\nOptimization took {time.time() - start_time:.3f}s")
    print(f"Result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")


def example_3_percentage_updates_only():
    """Example 3: Show only percentage updates."""
    print("\n" + "=" * 70)
    print("Example 3: Percentage-Only Progress")
    print("=" * 70)
    
    last_reported = -1
    
    def percentage_callback(phase: str, progress: float):
        """Report only when progress changes by 10%."""
        nonlocal last_reported
        percentage = int(progress * 10) * 10  # Round to nearest 10%
        if percentage > last_reported:
            last_reported = percentage
            print(f"{percentage}% complete...")
    
    def data_processing(x):
        """Simulate data processing."""
        return sum(x + i for i in range(1000))
    
    data = list(range(500))
    result = optimize(data_processing, data, progress_callback=percentage_callback)
    
    print(f"\nFinal: n_jobs={result.n_jobs}, chunksize={result.chunksize}")


def example_4_gui_style_callback():
    """Example 4: Callback suitable for GUI integration."""
    print("\n" + "=" * 70)
    print("Example 4: GUI-Style Callback (simulated)")
    print("=" * 70)
    
    class ProgressTracker:
        """Simulates a GUI progress tracker."""
        
        def __init__(self):
            self.current_phase = ""
            self.current_progress = 0.0
            self.phases = []
        
        def update(self, phase: str, progress: float):
            """Update progress (would update GUI in real app)."""
            self.current_phase = phase
            self.current_progress = progress
            self.phases.append((phase, progress))
            
            # Simulate GUI update
            if progress in [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]:
                print(f"[GUI] Phase: {phase:30s} Progress: {progress*100:5.1f}%")
        
        def get_summary(self):
            """Get summary of optimization process."""
            return f"Completed {len(self.phases)} phases"
    
    tracker = ProgressTracker()
    
    def scientific_computation(x):
        """Complex scientific computation."""
        import math
        result = 0
        for i in range(3000):
            result += math.sin(x + i) * math.cos(x - i)
        return result
    
    data = list(range(100))
    result = optimize(
        scientific_computation, 
        data,
        progress_callback=tracker.update
    )
    
    print(f"\n{tracker.get_summary()}")
    print(f"Optimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")


def example_5_error_handling():
    """Example 5: Robust error handling in callbacks."""
    print("\n" + "=" * 70)
    print("Example 5: Error Handling in Callbacks")
    print("=" * 70)
    
    class SafeProgressLogger:
        """Progress logger with built-in error handling."""
        
        def __init__(self, log_file=None):
            self.log_file = log_file
            self.errors = []
        
        def __call__(self, phase: str, progress: float):
            """Log progress with error handling."""
            try:
                message = f"Progress: {progress*100:5.1f}% - {phase}"
                print(message)
                
                # Attempt to write to file (may fail)
                if self.log_file:
                    with open(self.log_file, 'a') as f:
                        f.write(message + '\n')
            except Exception as e:
                self.errors.append(str(e))
                # Don't let callback errors break optimization
    
    logger = SafeProgressLogger()  # No file, won't cause errors
    
    def data_analysis(x):
        """Analyze data."""
        return sum(x + i for i in range(2000))
    
    data = list(range(150))
    result = optimize(data_analysis, data, progress_callback=logger)
    
    print(f"\nOptimization completed successfully")
    print(f"Callback errors encountered: {len(logger.errors)}")
    print(f"Result: n_jobs={result.n_jobs}")


def example_6_combined_with_profiling():
    """Example 6: Progress callback with diagnostic profiling."""
    print("\n" + "=" * 70)
    print("Example 6: Progress Callback + Diagnostic Profiling")
    print("=" * 70)
    
    phases_seen = []
    
    def tracking_callback(phase: str, progress: float):
        """Track phases for later analysis."""
        phases_seen.append(phase)
        if progress in [0.0, 0.5, 1.0]:
            print(f"✓ {phase}")
    
    def matrix_operation(x):
        """Simulate matrix operations."""
        result = 0
        for i in range(5000):
            result += (x + i) ** 2
        return result
    
    data = list(range(200))
    result = optimize(
        matrix_operation,
        data,
        profile=True,
        progress_callback=tracking_callback
    )
    
    print(f"\nPhases tracked: {len(phases_seen)}")
    print(f"\nOptimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Speedup: {result.estimated_speedup:.2f}x")
    
    # Show diagnostic profile
    if result.profile:
        print("\nDiagnostic Summary:")
        print(f"  Physical cores: {result.profile.physical_cores}")
        print(f"  Sampling time: {result.profile.avg_execution_time*1000:.2f}ms per item")
        print(f"  Total items: {result.profile.total_items}")


def main():
    """Run all examples."""
    examples = [
        example_1_basic_progress,
        example_2_detailed_logging,
        example_3_percentage_updates_only,
        example_4_gui_style_callback,
        example_5_error_handling,
        example_6_combined_with_profiling
    ]
    
    for example in examples:
        example()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
