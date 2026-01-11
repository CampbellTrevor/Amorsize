"""
Benchmark for reciprocal multiplication optimization (Iteration 98).

This benchmark measures the performance improvement from converting
division operations to multiplication by reciprocal in averaging calculations.

Theoretical expectation:
- Division: 10-40 CPU cycles (depends on architecture)
- Multiplication: 1-3 CPU cycles
- Optimization: 2 divisions → 2 multiplications per dry_run
- Expected savings: ~2-4ns per division → ~4-8ns total per dry_run
"""

import time
import math
from amorsize.sampling import perform_dry_run


def simple_func(x):
    """Simple function for benchmarking."""
    return x * 2


def benchmark_reciprocal_multiplication():
    """
    Benchmark the reciprocal multiplication optimization.
    
    Measures the time for averaging calculations with reciprocal multiplication
    vs. the theoretical cost of direct division.
    """
    print("=" * 70)
    print("Reciprocal Multiplication Optimization Benchmark (Iteration 98)")
    print("=" * 70)
    print()
    print("Optimization: Convert division to multiplication in averaging")
    print("  Before: avg = sum / sample_count  (division: ~10-40 cycles)")
    print("  After:  avg = sum * inv_sample_count  (multiplication: ~1-3 cycles)")
    print()
    
    # Warm up
    data = list(range(100))
    for _ in range(5):
        perform_dry_run(simple_func, data, sample_size=5)
    
    # Benchmark: Measure time for many dry runs
    iterations = 1000
    sample_sizes = [5, 10, 20]
    
    print(f"Running {iterations} dry runs for each sample size...")
    print()
    
    for sample_size in sample_sizes:
        data = list(range(sample_size * 2))
        
        # Time the dry runs
        start = time.perf_counter()
        for _ in range(iterations):
            result = perform_dry_run(simple_func, data, sample_size=sample_size)
        end = time.perf_counter()
        
        total_time = (end - start)
        time_per_run = total_time / iterations
        time_per_run_ns = time_per_run * 1e9
        
        print(f"Sample size: {sample_size}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Time per dry_run: {time_per_run * 1000:.3f}ms ({time_per_run_ns:.1f}ns)")
        print(f"  Dry runs per second: {iterations / total_time:.0f}")
        print()
    
    # Micro-benchmark: Isolate the division/multiplication operations
    print("-" * 70)
    print("Micro-benchmark: Isolated division vs multiplication")
    print("-" * 70)
    print()
    
    # Simulate the averaging calculations
    values = [1.234, 2.345, 3.456, 4.567, 5.678]
    sample_count = len(values)  # Dynamically computed to match values list
    iterations = 10_000_000
    
    # Benchmark division
    start = time.perf_counter()
    for _ in range(iterations):
        # Simulate 2 divisions (as in original code)
        avg1 = sum(values) / sample_count
        avg2 = sum(values) / sample_count
    end = time.perf_counter()
    div_time = end - start
    div_time_per_op = (div_time / iterations) * 1e9  # nanoseconds
    
    # Benchmark multiplication with reciprocal
    start = time.perf_counter()
    for _ in range(iterations):
        # Simulate 1 division + 2 multiplications (as in optimized code)
        inv_sample_count = 1.0 / sample_count
        avg1 = sum(values) * inv_sample_count
        avg2 = sum(values) * inv_sample_count
    end = time.perf_counter()
    mult_time = end - start
    mult_time_per_op = (mult_time / iterations) * 1e9  # nanoseconds
    
    savings = div_time - mult_time
    savings_per_op = div_time_per_op - mult_time_per_op
    speedup = div_time / mult_time if mult_time > 0 else float('inf')
    
    print(f"Iterations: {iterations:,}")
    print()
    print(f"Division approach (2 divisions):")
    print(f"  Total time: {div_time:.4f}s")
    print(f"  Time per operation: {div_time_per_op:.2f}ns")
    print()
    print(f"Multiplication approach (1 division + 2 multiplications):")
    print(f"  Total time: {mult_time:.4f}s")
    print(f"  Time per operation: {mult_time_per_op:.2f}ns")
    print()
    print(f"Performance improvement:")
    print(f"  Savings: {savings:.4f}s ({savings_per_op:.2f}ns per operation)")
    print(f"  Speedup: {speedup:.3f}x")
    print()
    
    # Analysis
    print("=" * 70)
    print("Analysis")
    print("=" * 70)
    print()
    print(f"Expected savings per dry_run: ~4-8ns (2 divisions → 2 multiplications)")
    print(f"Measured savings per operation: {savings_per_op:.2f}ns")
    print()
    
    if speedup > 1.01:
        print(f"✅ Optimization successful: {speedup:.3f}x faster")
        print(f"   This translates to ~{savings_per_op:.1f}ns saved per dry_run")
    elif speedup > 1.001:
        print(f"✅ Small but measurable improvement: {speedup:.3f}x faster")
        print(f"   Savings: ~{savings_per_op:.1f}ns per operation")
    else:
        print(f"ℹ️  Improvement within measurement noise: {speedup:.3f}x")
        print(f"   Note: Modern CPUs may optimize both approaches similarly")
    
    print()
    print("Notes:")
    print("- Division is typically 3-10x slower than multiplication on modern CPUs")
    print("- This optimization eliminates 1 division per dry_run (2 divs → 1 div + 2 mults)")
    print("- Every dry_run (called by optimize()) benefits from this optimization")
    print("- Zero complexity cost - mathematically identical results")
    print()


if __name__ == "__main__":
    benchmark_reciprocal_multiplication()
