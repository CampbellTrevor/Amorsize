"""
Diagnostic Profiling Mode Example

This example demonstrates the comprehensive diagnostic profiling feature
that helps users understand exactly why the optimizer made its recommendations.
"""

from amorsize import optimize
import time


def expensive_computation(n):
    """
    A CPU-bound function that takes meaningful time.
    Simulates scientific computation or data processing.
    """
    result = 0
    for i in range(10000):
        result += n ** 2 + i ** 0.5
    return result


def fast_function(x):
    """
    A very fast function - too fast to benefit from parallelization.
    """
    return x * 2


def memory_intensive_function(x):
    """
    Function that returns a large object.
    Demonstrates memory constraint warnings.
    """
    # Return a large list (simulating large data structures)
    return [x] * 50000


def main():
    print("=" * 80)
    print("AMORSIZE DIAGNOSTIC PROFILING DEMO")
    print("=" * 80)
    
    # Example 1: Successful parallelization
    print("\n" + "=" * 80)
    print("Example 1: Expensive Computation (Parallelization Beneficial)")
    print("=" * 80)
    
    data = range(500)
    result = optimize(
        expensive_computation,
        data,
        sample_size=5,
        profile=True,  # Enable diagnostic profiling
        verbose=False   # Disable verbose to focus on diagnostic output
    )
    
    print(f"\nRecommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Expected speedup: {result.estimated_speedup:.2f}x")
    
    print("\n" + "-" * 80)
    print("DETAILED DIAGNOSTIC REPORT:")
    print("-" * 80)
    print(result.explain())
    
    # Example 2: Function too fast for parallelization
    print("\n\n" + "=" * 80)
    print("Example 2: Fast Function (Parallelization Rejected)")
    print("=" * 80)
    
    data = range(1000)
    result = optimize(
        fast_function,
        data,
        sample_size=5,
        profile=True
    )
    
    print(f"\nRecommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Reason: {result.reason}")
    
    print("\n" + "-" * 80)
    print("DETAILED DIAGNOSTIC REPORT:")
    print("-" * 80)
    print(result.explain())
    
    # Example 3: Memory constraints
    print("\n\n" + "=" * 80)
    print("Example 3: Memory-Intensive Function (Memory Warnings)")
    print("=" * 80)
    
    data = range(500)
    result = optimize(
        memory_intensive_function,
        data,
        sample_size=3,
        profile=True
    )
    
    print(f"\nRecommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
    
    print("\n" + "-" * 80)
    print("DETAILED DIAGNOSTIC REPORT:")
    print("-" * 80)
    print(result.explain())
    
    # Example 4: Using diagnostic info programmatically
    print("\n\n" + "=" * 80)
    print("Example 4: Programmatic Access to Diagnostic Data")
    print("=" * 80)
    
    data = range(200)
    result = optimize(expensive_computation, data, sample_size=5, profile=True)
    
    if result.profile:
        print("\nDiagnostic data available for programmatic use:")
        print(f"  • Execution time per item: {result.profile.format_time(result.profile.avg_execution_time)}")
        print(f"  • IPC overhead per item:   {result.profile.format_time(result.profile.avg_pickle_time)}")
        print(f"  • Physical cores:          {result.profile.physical_cores}")
        print(f"  • Spawn cost per worker:   {result.profile.format_time(result.profile.spawn_cost)}")
        print(f"  • Theoretical max speedup: {result.profile.theoretical_max_speedup:.2f}x")
        print(f"  • Estimated actual speedup:{result.profile.estimated_speedup:.2f}x")
        print(f"  • Parallel efficiency:     {result.profile.speedup_efficiency * 100:.1f}%")
        
        if result.profile.overhead_spawn > 0:
            print("\n  Overhead breakdown:")
            breakdown = result.profile.get_overhead_breakdown()
            print(f"    - Process spawn:     {breakdown['spawn']:.1f}%")
            print(f"    - IPC/Serialization: {breakdown['ipc']:.1f}%")
            print(f"    - Task distribution: {breakdown['chunking']:.1f}%")
        
        if result.profile.recommendations:
            print("\n  Recommendations:")
            for rec in result.profile.recommendations:
                print(f"    • {rec}")
    
    # Example 5: Comparison with and without profiling
    print("\n\n" + "=" * 80)
    print("Example 5: Performance Impact of Profiling")
    print("=" * 80)
    
    data = range(100)
    
    # Without profiling
    start = time.perf_counter()
    result_no_profile = optimize(expensive_computation, data, sample_size=3, profile=False)
    time_no_profile = time.perf_counter() - start
    
    # With profiling
    start = time.perf_counter()
    result_with_profile = optimize(expensive_computation, data, sample_size=3, profile=True)
    time_with_profile = time.perf_counter() - start
    
    print(f"\nOptimization time without profiling: {time_no_profile * 1000:.2f}ms")
    print(f"Optimization time with profiling:    {time_with_profile * 1000:.2f}ms")
    print(f"Overhead from profiling:             {(time_with_profile - time_no_profile) * 1000:.2f}ms")
    print(f"Relative overhead:                   {((time_with_profile / time_no_profile - 1) * 100):.1f}%")
    
    print("\nNote: Profiling adds minimal overhead (just data collection),")
    print("      making it safe to use even in production scenarios.")


if __name__ == "__main__":
    main()
