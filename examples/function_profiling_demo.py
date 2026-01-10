"""
Function Performance Profiling Demo

This example demonstrates the cProfile-based function profiling feature
that helps identify performance bottlenecks inside your functions.

This is different from diagnostic profiling (profile=True), which explains
why the optimizer made its decisions. Function profiling shows WHERE time
is spent inside YOUR function code.
"""

from amorsize import optimize
import time


def compute_fibonacci(n):
    """
    Compute Fibonacci number recursively (intentionally inefficient).
    This will show up clearly in the profiler.
    """
    if n <= 1:
        return n
    return compute_fibonacci(n - 1) + compute_fibonacci(n - 2)


def process_data_with_bottleneck(x):
    """
    A function with an obvious bottleneck for profiling demonstration.
    """
    # Fast operation
    result = x * 2
    
    # Bottleneck: expensive computation
    fib = compute_fibonacci(min(x, 20))
    
    # Another fast operation
    final = result + fib
    
    return final


def nested_helper_functions(x):
    """
    Function with nested helper calls to show call tree in profiler.
    """
    def level1_helper(val):
        """First level helper."""
        result = 0
        for i in range(50):
            result += val + i
        return result
    
    def level2_helper(val):
        """Second level helper that calls level1."""
        intermediate = level1_helper(val)
        return intermediate * 2
    
    def level3_helper(val):
        """Third level helper that calls level2."""
        intermediate = level2_helper(val)
        for i in range(10):
            intermediate += level1_helper(val + i)
        return intermediate
    
    return level3_helper(x)


def main():
    print("=" * 80)
    print("FUNCTION PERFORMANCE PROFILING DEMO")
    print("=" * 80)
    print("\nThis feature uses Python's cProfile to show where time is spent")
    print("INSIDE your function, helping you identify bottlenecks.")
    print()
    
    # Example 1: Profiling a function with obvious bottleneck
    print("=" * 80)
    print("Example 1: Identifying Bottlenecks")
    print("=" * 80)
    print("\nProfiling a function with expensive Fibonacci computation...")
    
    data = range(1, 30)
    result = optimize(
        process_data_with_bottleneck,
        data,
        sample_size=5,
        enable_function_profiling=True,  # Enable cProfile
        verbose=False
    )
    
    print(f"\nOptimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Estimated speedup: {result.estimated_speedup:.2f}x")
    print()
    
    # Show the profiling results
    result.show_function_profile(sort_by='cumulative', limit=15)
    
    print("\n" + "-" * 80)
    print("ANALYSIS:")
    print("-" * 80)
    print("The profiler shows that compute_fibonacci is the hotspot,")
    print("being called many times and consuming most of the execution time.")
    print("This insight tells us where to focus optimization efforts.")
    print()
    
    # Example 2: Profiling nested function calls
    print("\n" + "=" * 80)
    print("Example 2: Understanding Call Trees")
    print("=" * 80)
    print("\nProfiling a function with nested helper functions...")
    
    data = range(100)
    result = optimize(
        nested_helper_functions,
        data,
        sample_size=5,
        enable_function_profiling=True
    )
    
    print(f"\nOptimization result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print()
    
    # Show profiling sorted by cumulative time to see call tree
    result.show_function_profile(sort_by='cumulative', limit=20)
    
    print("\n" + "-" * 80)
    print("ANALYSIS:")
    print("-" * 80)
    print("The profiler shows the call hierarchy:")
    print("  - level3_helper calls level2_helper and level1_helper")
    print("  - level2_helper calls level1_helper")
    print("This helps understand function interaction patterns.")
    print()
    
    # Example 3: Saving profile to file
    print("\n" + "=" * 80)
    print("Example 3: Saving Profile Report")
    print("=" * 80)
    
    data = range(50)
    result = optimize(
        process_data_with_bottleneck,
        data,
        sample_size=5,
        enable_function_profiling=True
    )
    
    # Save to file for later analysis
    result.save_function_profile(
        '/tmp/function_profile.txt',
        sort_by='cumulative',
        limit=30
    )
    
    print("\nProfile saved! You can now:")
    print("  1. Review the file: cat /tmp/function_profile.txt")
    print("  2. Share with team members")
    print("  3. Compare profiles across different versions")
    print()
    
    # Example 4: Using both profiling modes together
    print("\n" + "=" * 80)
    print("Example 4: Combining Both Profiling Modes")
    print("=" * 80)
    print("\nYou can use both profiling types simultaneously:")
    print("  - enable_function_profiling=True  (shows WHERE time is spent)")
    print("  - profile=True                     (explains WHY optimizer decided)")
    print()
    
    data = range(200)
    result = optimize(
        nested_helper_functions,
        data,
        sample_size=5,
        enable_function_profiling=True,  # Function profiling (cProfile)
        profile=True  # Diagnostic profiling (optimizer decisions)
    )
    
    print("Function Performance Profile:")
    print("-" * 80)
    result.show_function_profile(sort_by='cumulative', limit=10)
    
    print("\n\nOptimizer Diagnostic Profile:")
    print("-" * 80)
    print(result.explain())
    
    # Example 5: Profiling sort options
    print("\n" + "=" * 80)
    print("Example 5: Different Sort Options")
    print("=" * 80)
    print("\nProfile can be sorted by different criteria:")
    print()
    
    data = range(50)
    result = optimize(
        nested_helper_functions,
        data,
        sample_size=5,
        enable_function_profiling=True
    )
    
    print("1. Sort by CUMULATIVE time (time in function + subcalls):")
    result.show_function_profile(sort_by='cumulative', limit=5)
    
    print("\n2. Sort by INTERNAL time (time in function itself, excluding subcalls):")
    result.show_function_profile(sort_by='time', limit=5)
    
    print("\n3. Sort by NUMBER OF CALLS:")
    result.show_function_profile(sort_by='calls', limit=5)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nFunction profiling is valuable when:")
    print("  ✓ You want to optimize your function's performance")
    print("  ✓ You need to identify bottlenecks and hotspots")
    print("  ✓ You're debugging unexpected slowness")
    print("  ✓ You want to understand function call patterns")
    print()
    print("Key differences from diagnostic profiling:")
    print("  • enable_function_profiling=True → Shows WHERE time is spent (cProfile)")
    print("  • profile=True → Shows WHY optimizer made decisions (Amorsize)")
    print()
    print("Use both together for complete insight!")
    print("=" * 80)


if __name__ == "__main__":
    main()
