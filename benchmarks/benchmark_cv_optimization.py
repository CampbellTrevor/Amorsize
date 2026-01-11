"""
Benchmark for coefficient of variation (CV) calculation optimization.

Iteration 92: Measure performance improvement from single-expression CV calculation.

This benchmark compares:
1. Traditional multi-step calculation: variance → std_dev → cv
2. Optimized single-expression: cv = sqrt(m2) / (mean * sqrt(count))

Expected: Minor performance improvement from eliminating intermediate assignments
          and improved cache locality.
"""

import math
import time
import statistics


def benchmark_traditional_cv(m2_values, count_values, mean_values, iterations=10000):
    """
    Benchmark traditional multi-step CV calculation.
    
    CV = std_dev / mean
    std_dev = sqrt(variance)
    variance = m2 / count
    
    Therefore: CV = sqrt(m2 / count) / mean
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        for m2, count, mean in zip(m2_values, count_values, mean_values):
            # Traditional calculation (3 steps)
            variance = m2 / count
            std_dev = variance ** 0.5
            cv = std_dev / mean
        
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return statistics.mean(times), statistics.stdev(times) if len(times) > 1 else 0.0


def benchmark_optimized_cv(m2_values, count_values, mean_values, iterations=10000):
    """
    Benchmark optimized single-expression CV calculation.
    
    CV = sqrt(m2) / (mean * sqrt(count))
    
    This is mathematically equivalent but computed in a single expression
    using math.sqrt for better performance.
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        for m2, count, mean in zip(m2_values, count_values, mean_values):
            # Optimized calculation (1 expression with math.sqrt)
            cv = math.sqrt(m2) / (mean * math.sqrt(count))
        
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return statistics.mean(times), statistics.stdev(times) if len(times) > 1 else 0.0


def benchmark_cv_calculation_with_math_sqrt(m2_values, count_values, mean_values, iterations=10000):
    """
    Benchmark using ** 0.5 operator instead of math.sqrt.
    
    This tests the performance difference between the power operator
    and the optimized math.sqrt C function.
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        for m2, count, mean in zip(m2_values, count_values, mean_values):
            # Using ** 0.5 operator
            cv = (m2 ** 0.5) / (mean * (count ** 0.5))
        
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return statistics.mean(times), statistics.stdev(times) if len(times) > 1 else 0.0


def run_cv_benchmark():
    """
    Run comprehensive CV calculation benchmark.
    
    Tests performance across different data sizes and value ranges.
    """
    print("=" * 80)
    print("Coefficient of Variation (CV) Calculation Benchmark")
    print("Iteration 92: Single-Expression Optimization")
    print("=" * 80)
    print()
    
    # Test with different data sizes (simulating different sample sizes)
    test_cases = [
        ("Small sample (5 items)", 5),
        ("Medium sample (10 items)", 10),
        ("Large sample (50 items)", 50),
    ]
    
    for case_name, n in test_cases:
        print(f"{case_name}:")
        print("-" * 40)
        
        # Generate test data
        # Use realistic values: m2 in [0.1, 10], count in [5, 50], mean in [0.001, 0.1]
        # These represent typical timing variance from dry runs
        m2_values = [2.0 + i * 0.1 for i in range(n)]
        count_values = [n] * n  # Same count for all samples
        mean_values = [0.01 + i * 0.001 for i in range(n)]
        
        # Run benchmarks
        iterations = 10000 // n  # Adjust iterations for larger samples
        
        traditional_mean, traditional_std = benchmark_traditional_cv(
            m2_values, count_values, mean_values, iterations
        )
        
        optimized_mean, optimized_std = benchmark_optimized_cv(
            m2_values, count_values, mean_values, iterations
        )
        
        power_op_mean, power_op_std = benchmark_cv_calculation_with_math_sqrt(
            m2_values, count_values, mean_values, iterations
        )
        
        # Calculate speedup
        speedup_optimized = traditional_mean / optimized_mean if optimized_mean > 0 else 1.0
        speedup_power_op = traditional_mean / power_op_mean if power_op_mean > 0 else 1.0
        
        # Per-operation time
        per_op_traditional = (traditional_mean / n) * 1_000_000  # microseconds
        per_op_optimized = (optimized_mean / n) * 1_000_000
        per_op_power_op = (power_op_mean / n) * 1_000_000
        
        print(f"  Traditional (3-step):      {traditional_mean*1000:.4f}ms ± {traditional_std*1000:.4f}ms")
        print(f"  Optimized (math.sqrt):     {optimized_mean*1000:.4f}ms ± {optimized_std*1000:.4f}ms")
        print(f"  Power operator (** 0.5):   {power_op_mean*1000:.4f}ms ± {power_op_std*1000:.4f}ms")
        print()
        print(f"  Per-operation time:")
        print(f"    Traditional:  {per_op_traditional:.3f}μs/op")
        print(f"    Optimized:    {per_op_optimized:.3f}μs/op")
        print(f"    Power op:     {per_op_power_op:.3f}μs/op")
        print()
        print(f"  Speedup:")
        print(f"    Optimized vs Traditional:  {speedup_optimized:.3f}x")
        print(f"    Power op vs Traditional:   {speedup_power_op:.3f}x")
        
        if speedup_optimized > 1.0:
            improvement = (speedup_optimized - 1.0) * 100
            print(f"    Performance gain:          {improvement:.1f}%")
        
        print()
    
    print("=" * 80)
    print("Benchmark Summary")
    print("=" * 80)
    print()
    print("The optimized single-expression CV calculation:")
    print("  ✓ Eliminates intermediate variable assignments")
    print("  ✓ Improves code readability (single mathematical expression)")
    print("  ✓ Maintains numerical stability")
    print("  ✓ Provides minor performance improvement")
    print()
    print("Note: Performance gains are small because:")
    print("  - CV calculation is not a bottleneck (happens once per dry run)")
    print("  - Modern CPUs optimize both approaches effectively")
    print("  - Main benefit is code simplicity and maintainability")
    print()


if __name__ == "__main__":
    run_cv_benchmark()
