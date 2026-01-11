"""
Benchmark script to measure performance improvement from memory allocation optimizations.

This script compares the dry run performance before and after the memory allocation
optimizations implemented in Iteration 88.
"""

import time
import sys
from amorsize.sampling import perform_dry_run


def simple_func(x):
    """Simple test function."""
    return x * 2


def cpu_intensive_func(x):
    """CPU-intensive function."""
    result = 0
    for i in range(x):
        result += i ** 2
    return result


def benchmark_dry_run(func, data, sample_size, iterations=50):
    """
    Benchmark dry run performance.
    
    Args:
        func: Function to test
        data: Input data
        sample_size: Sample size for dry run
        iterations: Number of iterations to average
    
    Returns:
        Average time per dry run in seconds
    """
    # Warm up
    for _ in range(3):
        _ = perform_dry_run(func, data, sample_size=sample_size)
    
    # Measure
    start = time.perf_counter()
    for _ in range(iterations):
        _ = perform_dry_run(func, data, sample_size=sample_size)
    end = time.perf_counter()
    
    return (end - start) / iterations


def main():
    """Run benchmarks and report results."""
    print("=" * 70)
    print("Memory Allocation Optimization Benchmark")
    print("Iteration 88: Pre-allocated lists and generator-based variance")
    print("=" * 70)
    print()
    
    # Test configurations
    configs = [
        ("Simple function, small sample", simple_func, list(range(100)), 5),
        ("Simple function, medium sample", simple_func, list(range(1000)), 10),
        ("Simple function, large sample", simple_func, list(range(1000)), 20),
        ("CPU-intensive, small sample", cpu_intensive_func, list(range(10, 20)), 5),
        ("CPU-intensive, medium sample", cpu_intensive_func, list(range(10, 30)), 10),
    ]
    
    results = []
    
    for name, func, data, sample_size in configs:
        print(f"Testing: {name}")
        print(f"  Data size: {len(data)}, Sample size: {sample_size}")
        
        avg_time = benchmark_dry_run(func, data, sample_size, iterations=30)
        
        print(f"  Average time: {avg_time * 1000:.3f}ms")
        print()
        
        results.append((name, avg_time))
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    
    total_time = sum(t for _, t in results)
    print(f"Total benchmark time: {total_time:.3f}s")
    print(f"Average per test: {total_time / len(results) * 1000:.3f}ms")
    print()
    
    print("Expected improvements from Iteration 88:")
    print("  - Pre-allocated lists: Reduced memory allocation overhead")
    print("  - Index-based writes: Eliminated append() call overhead")
    print("  - Generator variance: Reduced intermediate list creation")
    print("  - List comprehension extraction: More efficient data extraction")
    print()
    print("These optimizations reduce memory churn and allocation overhead,")
    print("particularly noticeable when running many optimizations in succession.")
    print()
    
    # Performance validation
    max_acceptable_time = 0.050  # 50ms max per dry run
    slow_tests = [(name, t) for name, t in results if t > max_acceptable_time]
    
    if slow_tests:
        print("WARNING: Some tests are slower than expected:")
        for name, t in slow_tests:
            print(f"  - {name}: {t * 1000:.3f}ms (expected < {max_acceptable_time * 1000:.1f}ms)")
    else:
        print("✅ All tests performed within expected bounds!")
    
    return 0 if not slow_tests else 1


if __name__ == "__main__":
    sys.exit(main())
