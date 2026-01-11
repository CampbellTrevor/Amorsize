"""
Example: Real-Time System Load Adjustment

This example demonstrates how to use the load-aware worker calculation feature
to dynamically adjust the number of parallel workers based on current system load.

This is particularly useful in:
- Multi-tenant environments (shared servers, cloud instances)
- Systems running multiple concurrent applications
- Production deployments where resource contention is possible
- Batch processing systems that need to be "good citizens"

When enabled, Amorsize will:
1. Monitor current CPU load (percentage of CPU in use)
2. Monitor current memory pressure (percentage of RAM in use)
3. Reduce worker count if CPU load > 70% or memory pressure > 75%
4. Ensure optimal resource utilization without overloading the system
"""

import time
import multiprocessing as mp
from amorsize import optimize


def cpu_intensive_task(n):
    """Simulate a CPU-intensive computation."""
    result = 0
    for i in range(n):
        result += i ** 2
    return result


def print_system_info():
    """Print current system load information."""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        print(f"Current System Load:")
        print(f"  CPU: {cpu_percent:.1f}%")
        print(f"  Memory: {memory_percent:.1f}%")
    except ImportError:
        print("Install psutil for detailed system monitoring: pip install psutil")


def example_basic_load_awareness():
    """Basic example showing load-aware optimization."""
    print("="*60)
    print("Example 1: Basic Load-Aware Optimization")
    print("="*60)
    
    data = [10000] * 100
    
    print("\n1. Standard optimization (hardware constraints only):")
    print_system_info()
    
    result_standard = optimize(
        cpu_intensive_task,
        data,
        adjust_for_system_load=False,
        verbose=True
    )
    
    print(f"\nResult: n_jobs={result_standard.n_jobs}, chunksize={result_standard.chunksize}")
    
    print("\n2. Load-aware optimization (considers current system load):")
    print_system_info()
    
    result_load_aware = optimize(
        cpu_intensive_task,
        data,
        adjust_for_system_load=True,
        verbose=True
    )
    
    print(f"\nResult: n_jobs={result_load_aware.n_jobs}, chunksize={result_load_aware.chunksize}")
    
    if result_load_aware.n_jobs < result_standard.n_jobs:
        print(f"\n✓ Load-aware optimization reduced workers to avoid overloading the system")
    else:
        print(f"\n✓ System load is low - using full worker capacity")


def example_simulated_high_load():
    """Demonstrate behavior under simulated high system load."""
    print("\n" + "="*60)
    print("Example 2: Behavior Under High System Load")
    print("="*60)
    
    print("\nSimulating a busy system by creating background CPU load...")
    print("(In production, this would be other applications using the system)")
    
    # Create some background CPU load
    def background_work():
        """Simulate background CPU load."""
        end_time = time.time() + 5
        while time.time() < end_time:
            _ = [i**2 for i in range(10000)]
    
    # Start background processes to simulate system load
    background_procs = []
    num_background = min(2, mp.cpu_count())
    for _ in range(num_background):
        p = mp.Process(target=background_work)
        p.start()
        background_procs.append(p)
    
    # Give background processes time to start
    time.sleep(0.5)
    
    data = [5000] * 50
    
    print("\nOptimizing with load awareness enabled:")
    print_system_info()
    
    result = optimize(
        cpu_intensive_task,
        data,
        adjust_for_system_load=True,
        verbose=True
    )
    
    print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print("\n✓ Worker count adjusted based on available system capacity")
    
    # Clean up background processes
    for p in background_procs:
        p.terminate()
        p.join()


def example_comparison():
    """Compare execution with and without load awareness."""
    print("\n" + "="*60)
    print("Example 3: Performance Comparison")
    print("="*60)
    
    data = [8000] * 80
    
    print("\nComparing both approaches:")
    print_system_info()
    
    # Without load awareness
    print("\n1. Standard optimization:")
    result_standard = optimize(
        cpu_intensive_task,
        data,
        adjust_for_system_load=False
    )
    print(f"   n_jobs={result_standard.n_jobs}, chunksize={result_standard.chunksize}")
    
    # With load awareness
    print("\n2. Load-aware optimization:")
    result_load_aware = optimize(
        cpu_intensive_task,
        data,
        adjust_for_system_load=True
    )
    print(f"   n_jobs={result_load_aware.n_jobs}, chunksize={result_load_aware.chunksize}")
    
    # Execute both and compare
    print("\nExecuting both approaches...")
    
    start = time.time()
    with mp.Pool(result_standard.n_jobs) as pool:
        _ = pool.map(cpu_intensive_task, data, chunksize=result_standard.chunksize)
    time_standard = time.time() - start
    
    start = time.time()
    with mp.Pool(result_load_aware.n_jobs) as pool:
        _ = pool.map(cpu_intensive_task, data, chunksize=result_load_aware.chunksize)
    time_load_aware = time.time() - start
    
    print(f"\nExecution times:")
    print(f"  Standard:   {time_standard:.2f}s")
    print(f"  Load-aware: {time_load_aware:.2f}s")
    
    if time_load_aware < time_standard:
        improvement = ((time_standard - time_load_aware) / time_standard) * 100
        print(f"\n✓ Load-aware was {improvement:.1f}% faster!")
    elif abs(time_standard - time_load_aware) < 0.1:
        print(f"\n✓ Both approaches performed similarly (system load was low)")
    else:
        print(f"\n✓ Results depend on current system conditions")


def example_use_cases():
    """Show practical use cases for load awareness."""
    print("\n" + "="*60)
    print("Example 4: Practical Use Cases")
    print("="*60)
    
    print("""
When to enable load-aware optimization:

✓ YES - Enable in these scenarios:
  - Multi-tenant cloud servers (AWS, GCP, Azure)
  - Shared development/CI servers
  - Production batch processing systems
  - Applications with unpredictable resource competition
  - Docker containers with resource limits
  - Systems running multiple concurrent applications

✗ NO - Not needed in these scenarios:
  - Dedicated single-application servers
  - Local development on laptop/workstation (unless testing)
  - Systems where you control all resource usage
  - When absolute maximum speed is required

Example usage in production:

    from amorsize import optimize
    
    # Production: Be a good citizen, respect other workloads
    result = optimize(
        my_function,
        data,
        adjust_for_system_load=True  # ← Enable load awareness
    )
    
    # Development: Use full resources for testing
    result = optimize(
        my_function,
        data,
        adjust_for_system_load=False  # ← Default, maximum speed
    )

The feature adds minimal overhead (<5ms) and provides significant benefits
in shared environments by preventing resource contention.
    """)


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Real-Time System Load Adjustment Examples")
    print("="*70)
    
    # Check if psutil is available
    try:
        import psutil
        print("✓ psutil is available - full load monitoring enabled")
    except ImportError:
        print("⚠ psutil not available - install for load monitoring: pip install psutil")
        print("  (Load awareness will be disabled without psutil)\n")
        return
    
    # Run examples
    example_basic_load_awareness()
    time.sleep(1)
    
    example_simulated_high_load()
    time.sleep(1)
    
    example_comparison()
    time.sleep(1)
    
    example_use_cases()
    
    print("\n" + "="*70)
    print("Examples complete!")
    print("="*70)


if __name__ == "__main__":
    main()
