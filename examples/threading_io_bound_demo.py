"""
Demonstration of threading support for I/O-bound workloads in Amorsize.

This example shows how Amorsize automatically detects I/O-bound workloads
and uses ThreadPoolExecutor instead of multiprocessing.Pool for better
performance.

Note: The `requests` library is used in one example but is optional.
      All other examples work without external dependencies.
"""

import time
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    
from amorsize import optimize, execute


def io_bound_function_with_requests(url):
    """
    I/O-bound function that makes HTTP requests (requires requests library).
    
    This function spends most of its time waiting for I/O (network),
    not doing CPU computation. Such functions benefit more from threading
    than multiprocessing because:
    1. Threading has lower overhead (no process spawn cost)
    2. GIL is released during I/O operations
    3. Better resource utilization
    """
    if not HAS_REQUESTS:
        # Skip if requests not available
        time.sleep(0.01)
        return 100
    
    try:
        response = requests.get(url, timeout=5)
        return len(response.content)
    except requests.exceptions.RequestException as e:
        # Log specific request errors
        print(f"Request failed: {e}")
        return 0
    except Exception as e:
        # Catch other unexpected errors
        print(f"Unexpected error: {e}")
        return 0


def cpu_bound_function(n):
    """
    CPU-bound function for comparison.
    
    This function does heavy CPU computation and benefits from
    multiprocessing to utilize multiple CPU cores.
    """
    result = 0
    for i in range(1000000):
        result += i ** 2
    return result


def mixed_function(item):
    """
    Mixed CPU/I/O workload.
    
    Combines both CPU computation and I/O operations.
    """
    # Some CPU work
    result = sum(i ** 2 for i in range(10000))
    # Some I/O work
    time.sleep(0.01)
    return result


def example_1_io_bound_optimization():
    """Example 1: Automatic threading for I/O-bound workload."""
    print("=" * 70)
    print("Example 1: I/O-bound workload (automatic threading)")
    print("=" * 70)
    
    # Simulate I/O-bound workload with sleep
    def io_task(x):
        time.sleep(0.01)  # Simulate I/O wait
        return x * 2
    
    data = list(range(100))
    
    # Optimize with default settings (prefer_threads_for_io=True)
    result = optimize(io_task, data, verbose=True)
    
    print(f"\n✓ Executor type: {result.executor_type}")
    print(f"✓ Recommended n_jobs: {result.n_jobs}")
    print(f"✓ Estimated speedup: {result.estimated_speedup:.2f}x")
    
    if result.executor_type == "thread":
        print("\n✓ SUCCESS: Automatically selected ThreadPoolExecutor for I/O-bound workload!")
    
    print()


def example_2_cpu_bound_optimization():
    """Example 2: Multiprocessing for CPU-bound workload."""
    print("=" * 70)
    print("Example 2: CPU-bound workload (multiprocessing)")
    print("=" * 70)
    
    data = list(range(50))
    
    # Optimize CPU-bound function
    result = optimize(cpu_bound_function, data, sample_size=3, verbose=True)
    
    print(f"\n✓ Executor type: {result.executor_type}")
    print(f"✓ Recommended n_jobs: {result.n_jobs}")
    print(f"✓ Estimated speedup: {result.estimated_speedup:.2f}x")
    
    if result.executor_type == "process":
        print("\n✓ SUCCESS: Selected multiprocessing.Pool for CPU-bound workload!")
    
    print()


def example_3_execute_with_threading():
    """Example 3: Using execute() for I/O-bound workload."""
    print("=" * 70)
    print("Example 3: Execute I/O-bound workload with automatic threading")
    print("=" * 70)
    
    def io_task(x):
        time.sleep(0.01)  # Simulate I/O
        return x ** 2
    
    data = list(range(50))
    
    print("Executing with automatic optimization and threading...")
    
    # Execute automatically chooses the right executor
    results, opt_result = execute(
        io_task,
        data,
        verbose=True,
        return_optimization_result=True
    )
    
    print(f"\n✓ Processed {len(results)} items")
    print(f"✓ Used executor: {opt_result.executor_type}")
    print(f"✓ Results sample: {results[:5]}")
    
    print()


def example_4_force_multiprocessing():
    """Example 4: Force multiprocessing for I/O-bound workload (opt-out)."""
    print("=" * 70)
    print("Example 4: Force multiprocessing (prefer_threads_for_io=False)")
    print("=" * 70)
    
    def io_task(x):
        time.sleep(0.01)
        return x * 2
    
    data = list(range(50))
    
    # Explicitly disable threading preference
    result = optimize(
        io_task,
        data,
        prefer_threads_for_io=False,  # Force multiprocessing
        verbose=True
    )
    
    print(f"\n✓ Executor type: {result.executor_type}")
    print(f"✓ Forced to use: multiprocessing.Pool")
    
    print()


def example_5_comparison():
    """Example 5: Performance comparison (threading vs multiprocessing)."""
    print("=" * 70)
    print("Example 5: Performance comparison")
    print("=" * 70)
    
    def io_task(x):
        time.sleep(0.001)  # Simulate I/O
        return x * 2
    
    data = list(range(100))
    
    # Test with threading (default)
    print("\nTesting with ThreadPoolExecutor (prefer_threads_for_io=True):")
    start = time.perf_counter()
    results_thread, opt_thread = execute(
        io_task,
        data,
        prefer_threads_for_io=True,
        return_optimization_result=True
    )
    time_thread = time.perf_counter() - start
    
    print(f"  Executor: {opt_thread.executor_type}")
    print(f"  Workers: {opt_thread.n_jobs}")
    print(f"  Time: {time_thread:.3f}s")
    
    # Test with multiprocessing
    print("\nTesting with multiprocessing.Pool (prefer_threads_for_io=False):")
    start = time.perf_counter()
    results_proc, opt_proc = execute(
        io_task,
        data,
        prefer_threads_for_io=False,
        return_optimization_result=True
    )
    time_proc = time.perf_counter() - start
    
    print(f"  Executor: {opt_proc.executor_type}")
    print(f"  Workers: {opt_proc.n_jobs}")
    print(f"  Time: {time_proc:.3f}s")
    
    # Compare
    if time_thread < time_proc:
        speedup = time_proc / time_thread
        print(f"\n✓ Threading is {speedup:.2f}x FASTER for this I/O-bound workload!")
    
    print()


def example_6_workload_detection():
    """Example 6: Understanding workload detection."""
    print("=" * 70)
    print("Example 6: Workload type detection")
    print("=" * 70)
    
    # Pure I/O-bound (< 30% CPU)
    def pure_io(x):
        time.sleep(0.01)
        return x
    
    # Mixed workload (30-70% CPU)
    def mixed(x):
        time.sleep(0.005)
        return sum(i ** 2 for i in range(1000))
    
    # Pure CPU-bound (> 70% CPU)
    def pure_cpu(x):
        return sum(i ** 2 for i in range(10000))
    
    data = list(range(10))
    
    for func, name in [(pure_io, "Pure I/O"), (mixed, "Mixed"), (pure_cpu, "Pure CPU")]:
        result = optimize(func, data, sample_size=5, profile=True)
        
        workload_type = result.profile.workload_type if result.profile else "unknown"
        cpu_ratio = result.profile.cpu_time_ratio if result.profile else 0
        
        print(f"\n{name}:")
        print(f"  Workload type: {workload_type}")
        print(f"  CPU utilization: {cpu_ratio*100:.1f}%")
        print(f"  Executor chosen: {result.executor_type}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AMORSIZE: Threading Support for I/O-bound Workloads")
    print("=" * 70)
    print()
    print("This demo shows how Amorsize automatically detects I/O-bound")
    print("workloads and uses ThreadPoolExecutor for better performance.")
    print()
    
    # Run examples
    example_1_io_bound_optimization()
    example_2_cpu_bound_optimization()
    example_3_execute_with_threading()
    example_4_force_multiprocessing()
    example_5_comparison()
    example_6_workload_detection()
    
    print("=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print()
    print("1. Amorsize automatically detects I/O-bound workloads (< 30% CPU)")
    print("2. Threading is used automatically for I/O-bound tasks")
    print("3. Multiprocessing is used for CPU-bound tasks (> 70% CPU)")
    print("4. Mixed workloads (30-70% CPU) get recommendations")
    print("5. You can opt-out with prefer_threads_for_io=False")
    print("6. Threading has lower overhead and better I/O performance")
    print()
    print("=" * 70)
