"""
Demonstration of execution hooks for monitoring and integration.

This example shows various patterns for using execution hooks to:
1. Monitor execution progress
2. Collect performance metrics
3. Integrate with external monitoring systems
4. Handle errors gracefully
"""

import time
from typing import Any

from amorsize import (
    HookContext,
    HookEvent,
    HookManager,
    create_error_hook,
    create_progress_hook,
    create_throughput_hook,
    create_timing_hook,
    execute,
)


def expensive_function(x: int) -> int:
    """Example CPU-intensive function."""
    result = 0
    squared = x ** 2  # Calculate once outside loop
    for i in range(1000):
        result += squared
    return result


# ============================================================================
# Example 1: Basic Progress Monitoring
# ============================================================================

def demo_basic_progress():
    """Demonstrate basic progress monitoring."""
    print("=" * 70)
    print("Example 1: Basic Progress Monitoring")
    print("=" * 70)
    
    hooks = HookManager()
    
    # Simple progress callback
    def show_progress(percent: float, completed: int, total: int):
        print(f"Progress: {percent:.1f}% ({completed}/{total} items)")
    
    # Register progress hook
    hook = create_progress_hook(show_progress, min_interval=0.0)
    hooks.register(HookEvent.PRE_EXECUTE, lambda ctx: print(f"Starting execution with {ctx.n_jobs} workers..."))
    hooks.register(HookEvent.POST_EXECUTE, hook)
    
    # Execute with hooks
    data = range(100)
    results = execute(expensive_function, data, hooks=hooks, verbose=False)
    
    print(f"✓ Completed processing {len(results)} items\n")


# ============================================================================
# Example 2: Performance Metrics Collection
# ============================================================================

def demo_metrics_collection():
    """Demonstrate collecting performance metrics."""
    print("=" * 70)
    print("Example 2: Performance Metrics Collection")
    print("=" * 70)
    
    hooks = HookManager()
    metrics = {}
    
    def collect_pre_metrics(ctx: HookContext):
        metrics["start_time"] = ctx.timestamp
        metrics["n_jobs"] = ctx.n_jobs
        metrics["chunksize"] = ctx.chunksize
        metrics["total_items"] = ctx.total_items
        print(f"Starting: n_jobs={ctx.n_jobs}, chunksize={ctx.chunksize}")
    
    def collect_post_metrics(ctx: HookContext):
        metrics["end_time"] = ctx.timestamp
        metrics["elapsed_time"] = ctx.elapsed_time
        metrics["throughput"] = ctx.throughput_items_per_sec
        metrics["items_completed"] = ctx.items_completed
        print(f"Completed in {ctx.elapsed_time:.2f}s")
        print(f"Throughput: {ctx.throughput_items_per_sec:.1f} items/sec")
    
    hooks.register(HookEvent.PRE_EXECUTE, collect_pre_metrics)
    hooks.register(HookEvent.POST_EXECUTE, collect_post_metrics)
    
    # Execute
    data = range(200)
    results = execute(expensive_function, data, hooks=hooks, verbose=False)
    
    # Show collected metrics
    print("\nCollected Metrics:")
    for key, value in metrics.items():
        if "time" in key.lower():
            if isinstance(value, float) and value > 1000:  # Unix timestamp
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value:.2f}s")
        else:
            print(f"  {key}: {value}")
    print()


# ============================================================================
# Example 3: Timing Multiple Stages
# ============================================================================

def demo_timing_stages():
    """Demonstrate timing different execution stages."""
    print("=" * 70)
    print("Example 3: Timing Multiple Stages")
    print("=" * 70)
    
    hooks = HookManager()
    timings = {}
    
    def record_timing(event_name: str, elapsed: float):
        timings[event_name] = elapsed
        print(f"{event_name}: {elapsed:.3f}s")
    
    timing_hook = create_timing_hook(record_timing)
    hooks.register(HookEvent.PRE_EXECUTE, timing_hook)
    hooks.register(HookEvent.POST_EXECUTE, timing_hook)
    
    data = range(150)
    execute(expensive_function, data, hooks=hooks, verbose=False)
    
    print("\nTiming Summary:")
    print(f"  Total execution time: {timings.get('post_execute', 0):.3f}s")
    print()


# ============================================================================
# Example 4: Error Handling and Logging
# ============================================================================

def demo_error_handling():
    """Demonstrate error handling with hooks."""
    print("=" * 70)
    print("Example 4: Error Handling and Logging")
    print("=" * 70)
    
    hooks = HookManager(verbose=True)
    errors = []
    
    def log_error(error: Exception, traceback_str: str):
        errors.append({
            "error": str(error),
            "type": type(error).__name__
        })
        print(f"⚠ Error captured: {type(error).__name__}: {error}")
    
    error_hook = create_error_hook(log_error)
    hooks.register(HookEvent.ON_ERROR, error_hook)
    
    # Also add a hook that intentionally fails to show error isolation
    def failing_hook(ctx: HookContext):
        if ctx.event == HookEvent.PRE_EXECUTE:
            raise ValueError("Intentional hook error (should be isolated)")
    
    hooks.register(HookEvent.PRE_EXECUTE, failing_hook)
    
    # Execute (should complete despite hook error)
    data = range(50)
    results = execute(expensive_function, data, hooks=hooks, verbose=False)
    
    print(f"✓ Execution completed with {len(results)} results")
    print(f"  (Hook error was isolated and didn't break execution)\n")


# ============================================================================
# Example 5: Custom Monitoring System Integration
# ============================================================================

class MonitoringIntegration:
    """Example monitoring system integration (e.g., Prometheus, Datadog)."""
    
    def __init__(self):
        self.metrics = []
    
    def record_metric(self, name: str, value: Any, tags: dict = None):
        """Simulate sending metric to monitoring system."""
        self.metrics.append({
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time()
        })
    
    def get_metrics(self):
        """Get all recorded metrics."""
        return self.metrics


def demo_monitoring_integration():
    """Demonstrate integration with external monitoring system."""
    print("=" * 70)
    print("Example 5: Monitoring System Integration")
    print("=" * 70)
    
    # Create monitoring integration
    monitoring = MonitoringIntegration()
    hooks = HookManager()
    
    def send_pre_metrics(ctx: HookContext):
        monitoring.record_metric("parallel_execution.started", 1, {
            "n_jobs": ctx.n_jobs,
            "chunksize": ctx.chunksize
        })
        print("→ Sent 'execution.started' metric")
    
    def send_post_metrics(ctx: HookContext):
        monitoring.record_metric("parallel_execution.completed", 1, {
            "n_jobs": ctx.n_jobs,
            "items": ctx.items_completed
        })
        monitoring.record_metric("parallel_execution.duration_seconds", ctx.elapsed_time)
        monitoring.record_metric("parallel_execution.throughput", ctx.throughput_items_per_sec, {
            "unit": "items_per_second"
        })
        print("→ Sent 'execution.completed' metrics")
    
    hooks.register(HookEvent.PRE_EXECUTE, send_pre_metrics)
    hooks.register(HookEvent.POST_EXECUTE, send_post_metrics)
    
    # Execute
    data = range(100)
    results = execute(expensive_function, data, hooks=hooks, verbose=False)
    
    # Show captured metrics
    print(f"\nCaptured {len(monitoring.get_metrics())} metrics:")
    for metric in monitoring.get_metrics():
        print(f"  - {metric['name']}: {metric['value']}")
        if metric['tags']:
            print(f"    Tags: {metric['tags']}")
    print()


# ============================================================================
# Example 6: Throughput Monitoring
# ============================================================================

def demo_throughput_monitoring():
    """Demonstrate continuous throughput monitoring."""
    print("=" * 70)
    print("Example 6: Throughput Monitoring")
    print("=" * 70)
    
    hooks = HookManager()
    
    def report_throughput(rate: float):
        print(f"Throughput: {rate:.1f} items/second")
    
    throughput_hook = create_throughput_hook(report_throughput, min_interval=0.0)
    hooks.register(HookEvent.POST_EXECUTE, throughput_hook)
    
    # Also show pre-execution info
    hooks.register(HookEvent.PRE_EXECUTE, lambda ctx: print(
        f"Starting with {ctx.n_jobs} workers, chunksize={ctx.chunksize}"
    ))
    
    data = range(200)
    results = execute(expensive_function, data, hooks=hooks, verbose=False)
    
    print(f"✓ Processed {len(results)} items\n")


# ============================================================================
# Example 7: Complete Dashboard Pattern
# ============================================================================

def demo_complete_dashboard():
    """Demonstrate a complete monitoring dashboard pattern."""
    print("=" * 70)
    print("Example 7: Complete Monitoring Dashboard")
    print("=" * 70)
    
    hooks = HookManager()
    dashboard = {
        "execution_id": int(time.time()),
        "status": "pending",
        "metrics": {}
    }
    
    def update_dashboard_start(ctx: HookContext):
        dashboard["status"] = "running"
        dashboard["metrics"].update({
            "n_jobs": ctx.n_jobs,
            "chunksize": ctx.chunksize,
            "total_items": ctx.total_items,
            "start_time": ctx.timestamp,
            "executor_type": ctx.metadata.get("executor_type", "unknown"),
            "estimated_speedup": ctx.metadata.get("estimated_speedup", 0)
        })
        print(f"Dashboard: Execution #{dashboard['execution_id']} started")
        print(f"  Workers: {ctx.n_jobs}")
        print(f"  Chunksize: {ctx.chunksize}")
        print(f"  Executor: {ctx.metadata.get('executor_type', 'unknown')}")
        print(f"  Estimated speedup: {ctx.metadata.get('estimated_speedup', 0):.2f}x")
    
    def update_dashboard_complete(ctx: HookContext):
        dashboard["status"] = "completed"
        dashboard["metrics"].update({
            "end_time": ctx.timestamp,
            "duration": ctx.elapsed_time,
            "items_completed": ctx.items_completed,
            "throughput": ctx.throughput_items_per_sec,
            "completion_percent": ctx.percent_complete
        })
        print(f"\nDashboard: Execution #{dashboard['execution_id']} completed")
        print(f"  Duration: {ctx.elapsed_time:.2f}s")
        print(f"  Items: {ctx.items_completed}")
        print(f"  Throughput: {ctx.throughput_items_per_sec:.1f} items/s")
        print(f"  Status: {dashboard['status']}")
    
    hooks.register(HookEvent.PRE_EXECUTE, update_dashboard_start)
    hooks.register(HookEvent.POST_EXECUTE, update_dashboard_complete)
    
    # Execute
    data = range(150)
    results = execute(expensive_function, data, hooks=hooks, verbose=False)
    
    # Show final dashboard state
    print("\nFinal Dashboard State:")
    print(f"  Execution ID: {dashboard['execution_id']}")
    print(f"  Status: {dashboard['status']}")
    print(f"  Metrics: {len(dashboard['metrics'])} collected")
    print()


# ============================================================================
# Run All Demonstrations
# ============================================================================

def run_all_demos():
    """Run all demonstration examples."""
    demos = [
        demo_basic_progress,
        demo_metrics_collection,
        demo_timing_stages,
        demo_error_handling,
        demo_monitoring_integration,
        demo_throughput_monitoring,
        demo_complete_dashboard,
    ]
    
    for demo in demos:
        demo()
        time.sleep(0.5)  # Brief pause between demos


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AMORSIZE EXECUTION HOOKS - COMPREHENSIVE DEMONSTRATION")
    print("=" * 70 + "\n")
    
    run_all_demos()
    
    print("=" * 70)
    print("All demonstrations completed!")
    print("=" * 70)
