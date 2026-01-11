"""
Enhanced Hooks Demo - Fine-Grained Monitoring

This demo showcases the enhanced hook system that provides real-time
monitoring of chunk completion and progress during parallel execution.

New hook events:
- ON_CHUNK_COMPLETE: Triggered when each chunk finishes processing
- ON_PROGRESS: Triggered periodically to report execution progress

These hooks enable:
- Real-time progress bars
- Fine-grained performance monitoring
- Per-chunk timing analysis
- Dynamic throughput tracking
- Integration with monitoring systems
"""

import time
from typing import List

from amorsize import execute
from amorsize.hooks import (
    HookManager,
    HookEvent,
    HookContext,
    create_progress_hook,
    create_throughput_hook,
)


# =============================================================================
# Test Functions
# =============================================================================

def cpu_intensive_task(x: int) -> int:
    """Simulated CPU-intensive task."""
    result = 0
    for i in range(100000):
        result += x ** 2
    return result


def io_intensive_task(x: int) -> int:
    """Simulated I/O-intensive task."""
    time.sleep(0.05)
    return x * 2


def variable_duration_task(x: int) -> int:
    """Task with variable duration (heterogeneous workload)."""
    sleep_time = 0.01 + (x % 5) * 0.01
    time.sleep(sleep_time)
    return x * 2


# =============================================================================
# Demo 1: Basic Progress Monitoring
# =============================================================================

def demo_basic_progress():
    """Demonstrate basic progress monitoring with ON_PROGRESS hook."""
    print("=" * 70)
    print("DEMO 1: Basic Progress Monitoring")
    print("=" * 70)
    print()
    
    hooks = HookManager()
    
    def on_progress(ctx: HookContext):
        bar_length = 40
        filled = int(bar_length * ctx.percent_complete / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(
            f"\rProgress: [{bar}] {ctx.percent_complete:5.1f}% "
            f"({ctx.items_completed}/{ctx.total_items}) "
            f"| {ctx.throughput_items_per_sec:.1f} items/sec",
            end='', flush=True
        )
    
    hooks.register(HookEvent.ON_PROGRESS, on_progress)
    
    print("Processing 100 I/O-intensive tasks...")
    data = range(100)
    results = execute(io_intensive_task, data, hooks=hooks, verbose=False)
    print("\n✓ Complete!")
    print()


# =============================================================================
# Demo 2: Chunk-Level Monitoring
# =============================================================================

def demo_chunk_monitoring():
    """Demonstrate chunk-level monitoring with ON_CHUNK_COMPLETE hook."""
    print("=" * 70)
    print("DEMO 2: Chunk-Level Monitoring")
    print("=" * 70)
    print()
    
    hooks = HookManager()
    chunk_times: List[float] = []
    
    def on_chunk_complete(ctx: HookContext):
        chunk_times.append(ctx.chunk_time)
        print(
            f"Chunk {ctx.chunk_id:2d}: "
            f"{ctx.chunk_size:3d} items in {ctx.chunk_time:.3f}s "
            f"({ctx.chunk_size / ctx.chunk_time:.1f} items/sec) "
            f"[{ctx.items_completed}/{ctx.total_items}]"
        )
    
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk_complete)
    
    print("Processing 50 CPU-intensive tasks...")
    print()
    data = range(50)
    results = execute(cpu_intensive_task, data, hooks=hooks, verbose=False)
    
    print()
    print(f"✓ Complete! Processed {len(chunk_times)} chunks")
    print(f"  Average chunk time: {sum(chunk_times) / len(chunk_times):.3f}s")
    print(f"  Min chunk time: {min(chunk_times):.3f}s")
    print(f"  Max chunk time: {max(chunk_times):.3f}s")
    print()


# =============================================================================
# Demo 3: Combined Progress and Chunk Monitoring
# =============================================================================

def demo_combined_monitoring():
    """Demonstrate combined progress and chunk monitoring."""
    print("=" * 70)
    print("DEMO 3: Combined Progress and Chunk Monitoring")
    print("=" * 70)
    print()
    
    hooks = HookManager()
    chunks_completed = [0]  # Mutable to update from closure
    
    def on_chunk_complete(ctx: HookContext):
        chunks_completed[0] += 1
        # Only print every few chunks to avoid spam
        if chunks_completed[0] % 5 == 0 or ctx.items_completed == ctx.total_items:
            print(
                f"  [{chunks_completed[0]:3d} chunks] "
                f"{ctx.items_completed:4d}/{ctx.total_items} items complete"
            )
    
    def on_progress(ctx: HookContext):
        # Print progress bar (updates in place)
        bar_length = 30
        filled = int(bar_length * ctx.percent_complete / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(
            f"\r[{bar}] {ctx.percent_complete:5.1f}%",
            end='', flush=True
        )
    
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk_complete)
    hooks.register(HookEvent.ON_PROGRESS, on_progress)
    
    print("Processing 200 I/O-intensive tasks...")
    print()
    data = range(200)
    results = execute(io_intensive_task, data, hooks=hooks, verbose=False)
    
    print("\n")
    print(f"✓ Complete! Processed {chunks_completed[0]} chunks")
    print()


# =============================================================================
# Demo 4: Performance Analysis with Timing Breakdown
# =============================================================================

def demo_performance_analysis():
    """Demonstrate detailed performance analysis using hooks."""
    print("=" * 70)
    print("DEMO 4: Performance Analysis with Timing Breakdown")
    print("=" * 70)
    print()
    
    hooks = HookManager()
    
    # Track metrics
    execution_start = None
    chunk_times: List[float] = []
    throughputs: List[float] = []
    
    def on_pre_execute(ctx: HookContext):
        nonlocal execution_start
        execution_start = time.time()
        print(f"Starting execution:")
        print(f"  n_jobs: {ctx.n_jobs}")
        print(f"  chunksize: {ctx.chunksize}")
        print(f"  total_items: {ctx.total_items}")
        print()
    
    def on_chunk_complete(ctx: HookContext):
        chunk_times.append(ctx.chunk_time)
    
    def on_progress(ctx: HookContext):
        if ctx.throughput_items_per_sec > 0:
            throughputs.append(ctx.throughput_items_per_sec)
    
    def on_post_execute(ctx: HookContext):
        print()
        print("Execution complete!")
        print()
        print("Performance Summary:")
        print(f"  Total time: {ctx.elapsed_time:.2f}s")
        print(f"  Items processed: {ctx.items_completed}")
        print(f"  Average throughput: {ctx.throughput_items_per_sec:.1f} items/sec")
        print()
        
        if chunk_times:
            print("Chunk Statistics:")
            print(f"  Total chunks: {len(chunk_times)}")
            print(f"  Average chunk time: {sum(chunk_times) / len(chunk_times):.3f}s")
            print(f"  Min chunk time: {min(chunk_times):.3f}s")
            print(f"  Max chunk time: {max(chunk_times):.3f}s")
            print(f"  Chunk time variance: {max(chunk_times) - min(chunk_times):.3f}s")
            print()
        
        if len(throughputs) > 1:
            print("Throughput Statistics:")
            avg_throughput = sum(throughputs) / len(throughputs)
            print(f"  Average: {avg_throughput:.1f} items/sec")
            print(f"  Min: {min(throughputs):.1f} items/sec")
            print(f"  Max: {max(throughputs):.1f} items/sec")
    
    hooks.register(HookEvent.PRE_EXECUTE, on_pre_execute)
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk_complete)
    hooks.register(HookEvent.ON_PROGRESS, on_progress)
    hooks.register(HookEvent.POST_EXECUTE, on_post_execute)
    
    print("Processing 100 CPU-intensive tasks...")
    data = range(100)
    results = execute(cpu_intensive_task, data, hooks=hooks, verbose=False)
    print()


# =============================================================================
# Demo 5: Heterogeneous Workload Monitoring
# =============================================================================

def demo_heterogeneous_workload():
    """Demonstrate monitoring of heterogeneous workloads."""
    print("=" * 70)
    print("DEMO 5: Heterogeneous Workload Monitoring")
    print("=" * 70)
    print()
    
    hooks = HookManager()
    
    chunk_durations: List[float] = []
    
    def on_chunk_complete(ctx: HookContext):
        chunk_durations.append(ctx.chunk_time)
        items_per_sec = ctx.chunk_size / ctx.chunk_time if ctx.chunk_time > 0 else 0
        
        # Color-code based on speed (simulated with text)
        if items_per_sec > 50:
            speed_indicator = "🚀 FAST "
        elif items_per_sec > 30:
            speed_indicator = "⚡ MEDIUM"
        else:
            speed_indicator = "🐌 SLOW "
        
        print(
            f"{speed_indicator} | Chunk {ctx.chunk_id:2d}: "
            f"{ctx.chunk_size:2d} items in {ctx.chunk_time:.3f}s "
            f"({items_per_sec:.0f} items/sec)"
        )
    
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk_complete)
    
    print("Processing variable-duration tasks (heterogeneous workload)...")
    print("Some chunks will be faster, some slower due to variable task duration.")
    print()
    
    data = range(100)
    results = execute(variable_duration_task, data, hooks=hooks, verbose=False)
    
    print()
    if chunk_durations:
        variance = max(chunk_durations) - min(chunk_durations)
        coefficient_of_variation = (
            (sum((t - sum(chunk_durations) / len(chunk_durations)) ** 2 
                 for t in chunk_durations) / len(chunk_durations)) ** 0.5
        ) / (sum(chunk_durations) / len(chunk_durations))
        
        print(f"Workload Heterogeneity Analysis:")
        print(f"  Chunk time variance: {variance:.3f}s")
        print(f"  Coefficient of variation: {coefficient_of_variation:.2f}")
        if coefficient_of_variation > 0.3:
            print("  ⚠ High variability detected - adaptive chunking may help!")
        else:
            print("  ✓ Low variability - workload is fairly homogeneous")
    print()


# =============================================================================
# Demo 6: Real-Time Dashboard Simulation
# =============================================================================

def demo_realtime_dashboard():
    """Demonstrate real-time dashboard-style monitoring."""
    print("=" * 70)
    print("DEMO 6: Real-Time Dashboard Simulation")
    print("=" * 70)
    print()
    
    hooks = HookManager()
    
    start_time = time.time()
    last_print_time = [start_time]  # Mutable for closure
    
    def on_progress(ctx: HookContext):
        current_time = time.time()
        # Throttle updates to once per 0.5 seconds
        if current_time - last_print_time[0] < 0.5 and ctx.percent_complete < 100:
            return
        
        last_print_time[0] = current_time
        
        # Clear previous lines (simple simulation)
        print("\033[2J\033[H", end='')  # Clear screen and move to top
        
        print("=" * 70)
        print(" " * 20 + "AMORSIZE EXECUTION DASHBOARD")
        print("=" * 70)
        print()
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * ctx.percent_complete / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"Progress: [{bar}] {ctx.percent_complete:.1f}%")
        print()
        
        # Metrics
        print(f"Items Processed:  {ctx.items_completed:,} / {ctx.total_items:,}")
        print(f"Elapsed Time:     {ctx.elapsed_time:.1f}s")
        
        if ctx.percent_complete > 0 and ctx.percent_complete < 100:
            eta = ctx.elapsed_time * (100 - ctx.percent_complete) / ctx.percent_complete
            print(f"Estimated ETA:    {eta:.1f}s")
        
        print(f"Throughput:       {ctx.throughput_items_per_sec:.1f} items/sec")
        print()
        print("=" * 70)
    
    hooks.register(HookEvent.ON_PROGRESS, on_progress)
    
    print("Starting real-time dashboard...")
    print("(Dashboard will update during execution)")
    time.sleep(1)
    
    data = range(100)
    results = execute(io_intensive_task, data, hooks=hooks, verbose=False)
    
    print("\n\n✓ Execution complete!")
    print()


# =============================================================================
# Demo 7: Integration with Monitoring Systems
# =============================================================================

def demo_monitoring_integration():
    """Demonstrate integration patterns for monitoring systems."""
    print("=" * 70)
    print("DEMO 7: Monitoring System Integration Patterns")
    print("=" * 70)
    print()
    
    print("This demo shows how to integrate with monitoring systems.")
    print()
    
    # Simulated metrics collector
    class MetricsCollector:
        def __init__(self):
            self.metrics = []
        
        def record_chunk_completion(self, chunk_id: int, duration: float, size: int):
            self.metrics.append({
                'type': 'chunk_complete',
                'chunk_id': chunk_id,
                'duration': duration,
                'size': size,
                'timestamp': time.time()
            })
        
        def record_progress(self, percent: float, throughput: float):
            self.metrics.append({
                'type': 'progress',
                'percent': percent,
                'throughput': throughput,
                'timestamp': time.time()
            })
        
        def get_summary(self):
            chunk_metrics = [m for m in self.metrics if m['type'] == 'chunk_complete']
            progress_metrics = [m for m in self.metrics if m['type'] == 'progress']
            return {
                'total_chunks': len(chunk_metrics),
                'total_progress_updates': len(progress_metrics),
                'avg_chunk_duration': sum(m['duration'] for m in chunk_metrics) / len(chunk_metrics) if chunk_metrics else 0
            }
    
    # Create collector and hooks
    collector = MetricsCollector()
    hooks = HookManager()
    
    def on_chunk_complete(ctx: HookContext):
        collector.record_chunk_completion(
            ctx.chunk_id,
            ctx.chunk_time,
            ctx.chunk_size
        )
        print(f"  → Sent chunk_{ctx.chunk_id} metrics to monitoring system")
    
    def on_progress(ctx: HookContext):
        collector.record_progress(
            ctx.percent_complete,
            ctx.throughput_items_per_sec
        )
    
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, on_chunk_complete)
    hooks.register(HookEvent.ON_PROGRESS, on_progress)
    
    print("Executing with monitoring integration...")
    print()
    
    data = range(50)
    results = execute(cpu_intensive_task, data, hooks=hooks, verbose=False)
    
    print()
    summary = collector.get_summary()
    print("Metrics Collection Summary:")
    print(f"  Total chunks tracked: {summary['total_chunks']}")
    print(f"  Progress updates: {summary['total_progress_updates']}")
    print(f"  Average chunk duration: {summary['avg_chunk_duration']:.3f}s")
    print()
    print("These metrics could be sent to:")
    print("  • Prometheus (via HTTP)")
    print("  • StatsD/Datadog (via UDP)")
    print("  • Custom webhooks (HTTP POST)")
    print("  • Time-series databases")
    print("  • Cloud monitoring services")
    print()


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " " * 15 + "ENHANCED HOOKS DEMONSTRATION" + " " * 25 + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    demos = [
        ("Basic Progress Monitoring", demo_basic_progress),
        ("Chunk-Level Monitoring", demo_chunk_monitoring),
        ("Combined Monitoring", demo_combined_monitoring),
        ("Performance Analysis", demo_performance_analysis),
        ("Heterogeneous Workload", demo_heterogeneous_workload),
        ("Real-Time Dashboard", demo_realtime_dashboard),
        ("Monitoring Integration", demo_monitoring_integration),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
            break
        except Exception as e:
            print(f"\n⚠ Demo {i} failed: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(demos):
            input("\nPress Enter to continue to next demo...")
            print("\n")
    
    print("=" * 70)
    print("ALL DEMOS COMPLETE")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  • ON_CHUNK_COMPLETE hooks provide fine-grained timing data")
    print("  • ON_PROGRESS hooks enable real-time progress tracking")
    print("  • Hooks add minimal overhead to execution")
    print("  • Easy integration with monitoring systems")
    print("  • Works with both CPU-bound and I/O-bound workloads")
    print()


if __name__ == '__main__':
    main()
