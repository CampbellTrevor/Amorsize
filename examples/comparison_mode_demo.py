"""
Comparison Mode Demo - Comparing Different Parallelization Strategies

This example demonstrates how to use Amorsize's comparison mode to empirically
compare different parallelization strategies and choose the best one for your
workload.
"""

import time
from amorsize import (
    compare_strategies,
    compare_with_optimizer,
    ComparisonConfig,
    optimize
)


# Define a CPU-intensive function for testing
def expensive_computation(x):
    """Simulate a CPU-intensive task."""
    result = 0
    for i in range(2000):
        result += x ** 2
    return result


# Define an I/O-bound function for testing
def io_bound_task(x):
    """Simulate I/O-bound work with sleep."""
    time.sleep(0.001)  # Simulate I/O wait
    return x * 2


def example_1_basic_comparison():
    """Example 1: Basic comparison of different worker counts."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Comparison of Worker Counts")
    print("=" * 70)
    
    data = range(100)
    
    # Define strategies to compare
    configs = [
        ComparisonConfig("Serial", n_jobs=1),
        ComparisonConfig("2 Workers", n_jobs=2, chunksize=50),
        ComparisonConfig("4 Workers", n_jobs=4, chunksize=25),
        ComparisonConfig("8 Workers", n_jobs=8, chunksize=13)
    ]
    
    # Compare all strategies
    result = compare_strategies(expensive_computation, data, configs, verbose=True)
    
    # Print results
    print("\n" + str(result))
    
    # Access programmatic results
    print("\nProgrammatic access:")
    print(f"  Best configuration: {result.best_config.name}")
    print(f"  Best time: {result.best_time:.4f}s")
    print(f"  Best speedup: {result.speedups[result.best_config_index]:.2f}x")
    
    # Get sorted results (fastest first)
    sorted_results = result.get_sorted_configs()
    print("\n  Top 3 fastest strategies:")
    for i, (config, time_taken, speedup) in enumerate(sorted_results[:3], 1):
        print(f"    {i}. {config.name}: {time_taken:.4f}s ({speedup:.2f}x)")


def example_2_compare_chunksizes():
    """Example 2: Compare different chunksize strategies."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Comparing Different Chunksizes")
    print("=" * 70)
    
    data = range(200)
    
    # Fixed number of workers, vary chunksize
    configs = [
        ComparisonConfig("Serial", n_jobs=1),
        ComparisonConfig("Large Chunks (100)", n_jobs=4, chunksize=100),
        ComparisonConfig("Medium Chunks (50)", n_jobs=4, chunksize=50),
        ComparisonConfig("Small Chunks (25)", n_jobs=4, chunksize=25),
        ComparisonConfig("Tiny Chunks (10)", n_jobs=4, chunksize=10)
    ]
    
    result = compare_strategies(expensive_computation, data, configs, verbose=False)
    
    print(result)
    
    print("\nInsight: Chunksize affects load balancing vs overhead trade-off")
    print("  - Large chunks: Less overhead, but potential load imbalance")
    print("  - Small chunks: Better load balancing, but more overhead")


def example_3_compare_with_optimizer():
    """Example 3: Compare optimizer recommendation against alternatives."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Optimizer vs Manual Configurations")
    print("=" * 70)
    
    data = range(150)
    
    # Compare optimizer against manual configurations
    additional_configs = [
        ComparisonConfig("Conservative (2 workers)", n_jobs=2, chunksize=75),
        ComparisonConfig("Aggressive (8 workers)", n_jobs=8, chunksize=19),
        ComparisonConfig("Balanced (4 workers)", n_jobs=4, chunksize=38)
    ]
    
    result, optimization = compare_with_optimizer(
        expensive_computation,
        data,
        additional_configs=additional_configs,
        verbose=True
    )
    
    print("\n" + str(result))
    
    # Show how well optimizer performed
    optimizer_idx = 1  # Optimizer is always second (after Serial)
    optimizer_rank = sorted(enumerate(result.execution_times), key=lambda x: x[1])
    optimizer_position = [i for i, (idx, _) in enumerate(optimizer_rank) if idx == optimizer_idx][0] + 1
    
    print(f"\nOptimizer Performance:")
    print(f"  Recommended: n_jobs={optimization.n_jobs}, chunksize={optimization.chunksize}")
    print(f"  Predicted speedup: {optimization.estimated_speedup:.2f}x")
    print(f"  Actual speedup: {result.speedups[optimizer_idx]:.2f}x")
    print(f"  Rank: #{optimizer_position} out of {len(result.configs)}")


def example_4_threading_vs_multiprocessing():
    """Example 4: Compare threading vs multiprocessing for I/O-bound work."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Threading vs Multiprocessing (I/O-bound)")
    print("=" * 70)
    
    data = range(50)
    
    configs = [
        ComparisonConfig("Serial", n_jobs=1),
        ComparisonConfig("Multiprocessing (2)", n_jobs=2, chunksize=25, executor_type="process"),
        ComparisonConfig("Multiprocessing (4)", n_jobs=4, chunksize=13, executor_type="process"),
        ComparisonConfig("Threading (2)", n_jobs=2, executor_type="thread"),
        ComparisonConfig("Threading (4)", n_jobs=4, executor_type="thread")
    ]
    
    result = compare_strategies(io_bound_task, data, configs, verbose=False)
    
    print(result)
    
    # Analyze threading vs multiprocessing
    thread_configs = [(i, c, result.execution_times[i]) for i, c in enumerate(result.configs) if c.executor_type == "thread"]
    process_configs = [(i, c, result.execution_times[i]) for i, c in enumerate(result.configs) if c.executor_type == "process"]
    
    if thread_configs and process_configs:
        avg_thread = sum(t for _, _, t in thread_configs) / len(thread_configs)
        avg_process = sum(t for _, _, t in process_configs) / len(process_configs)
        
        print(f"\nExecutor Type Analysis:")
        print(f"  Average threading time: {avg_thread:.4f}s")
        print(f"  Average multiprocessing time: {avg_process:.4f}s")
        
        if avg_thread < avg_process * 0.9:
            print(f"  ✓ Threading is {avg_process/avg_thread:.1f}x faster for this workload")
            print("  → I/O-bound workloads benefit from threading (lower overhead)")
        elif avg_process < avg_thread * 0.9:
            print(f"  ✓ Multiprocessing is {avg_thread/avg_process:.1f}x faster for this workload")
            print("  → CPU-bound workloads benefit from multiprocessing (true parallelism)")
        else:
            print("  → Similar performance for both executor types")


def example_5_limited_dataset():
    """Example 5: Comparison with limited dataset (fast testing)."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Quick Comparison with Limited Dataset")
    print("=" * 70)
    
    # Large dataset, but limit comparison to first 100 items
    data = range(10000)
    
    configs = [
        ComparisonConfig("Serial", n_jobs=1),
        ComparisonConfig("2 Workers", n_jobs=2, chunksize=50),
        ComparisonConfig("4 Workers", n_jobs=4, chunksize=25)
    ]
    
    # Use max_items to limit benchmark runtime
    result = compare_strategies(
        expensive_computation,
        data,
        configs,
        max_items=100,  # Only benchmark first 100 items
        verbose=False
    )
    
    print(result)
    
    print("\nNote: Benchmarked only 100 items for speed")
    print("  → Results are indicative but may vary with full dataset")
    print("  → Use this for quick exploration before full benchmark")


def example_6_analyzing_recommendations():
    """Example 6: Understanding comparison recommendations."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Understanding Recommendations")
    print("=" * 70)
    
    data = range(100)
    
    configs = [
        ComparisonConfig("Serial", n_jobs=1),
        ComparisonConfig("Optimal (2 workers)", n_jobs=2, chunksize=50),
        ComparisonConfig("Oversubscribed (16 workers)", n_jobs=16, chunksize=7)
    ]
    
    result = compare_strategies(expensive_computation, data, configs, verbose=False)
    
    print(result)
    
    print("\nRecommendation Analysis:")
    for rec in result.recommendations:
        print(f"  • {rec}")
    
    # Check for inefficient configurations
    for i, (config, speedup) in enumerate(zip(result.configs, result.speedups)):
        if speedup < 1.0 and config.n_jobs > 1:
            print(f"\n⚠️  Warning: '{config.name}' is slower than serial!")
            print(f"     Speedup: {speedup:.2f}x (< 1.0)")
            print(f"     Cause: Overhead exceeds benefit for this workload")


def example_7_integration_with_optimize():
    """Example 7: Integration with optimize() function."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Validating Optimizer Predictions")
    print("=" * 70)
    
    data = range(120)
    
    # First, get optimizer recommendation
    print("Step 1: Get optimizer recommendation")
    opt = optimize(expensive_computation, data, verbose=True)
    
    print(f"\nOptimizer recommends: n_jobs={opt.n_jobs}, chunksize={opt.chunksize}")
    print(f"Predicted speedup: {opt.estimated_speedup:.2f}x")
    
    # Now, empirically validate with comparison
    print("\nStep 2: Empirically validate with comparison")
    
    # Create config from optimizer recommendation
    configs = [
        ComparisonConfig("Serial", n_jobs=1),
        ComparisonConfig(
            "Optimizer Recommendation",
            n_jobs=opt.n_jobs,
            chunksize=opt.chunksize,
            executor_type=opt.executor_type
        )
    ]
    
    result = compare_strategies(expensive_computation, data, configs, verbose=False)
    
    # Compare predicted vs actual
    actual_speedup = result.speedups[1]  # Optimizer is second config
    predicted_speedup = opt.estimated_speedup
    
    error = abs(actual_speedup - predicted_speedup) / predicted_speedup * 100
    
    print(f"\nValidation Results:")
    print(f"  Predicted speedup: {predicted_speedup:.2f}x")
    print(f"  Actual speedup: {actual_speedup:.2f}x")
    print(f"  Prediction error: {error:.1f}%")
    
    if error < 10:
        print("  ✅ Excellent prediction accuracy!")
    elif error < 25:
        print("  ✓ Good prediction accuracy")
    else:
        print("  ⚠️  Significant prediction error - investigate system-specific factors")


def main():
    """Run all examples."""
    print("\n")
    print("=" * 70)
    print("AMORSIZE COMPARISON MODE DEMONSTRATION")
    print("=" * 70)
    print()
    print("This demo shows how to compare different parallelization strategies")
    print("to find the best configuration for your specific workload.")
    print()
    
    example_1_basic_comparison()
    example_2_compare_chunksizes()
    example_3_compare_with_optimizer()
    example_4_threading_vs_multiprocessing()
    example_5_limited_dataset()
    example_6_analyzing_recommendations()
    example_7_integration_with_optimize()
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  1. compare_strategies() benchmarks multiple configurations")
    print("  2. compare_with_optimizer() validates optimizer recommendations")
    print("  3. Use max_items for quick exploration on large datasets")
    print("  4. Compare threading vs multiprocessing for I/O vs CPU-bound")
    print("  5. Recommendations provide insights for optimization decisions")
    print()


if __name__ == "__main__":
    main()
