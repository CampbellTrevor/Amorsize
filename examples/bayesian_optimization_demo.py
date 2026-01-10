"""
Example: Bayesian Optimization for Parameter Tuning

This example demonstrates how to use Bayesian optimization to find optimal
parallelization parameters more efficiently than grid search.

Bayesian optimization is especially useful when:
- Benchmarking is expensive (slow function or large dataset)
- Search space is large (many possible configurations)
- You want to find near-optimal parameters with fewer trials
"""

from amorsize import bayesian_tune_parameters, tune_parameters
import time


def expensive_cpu_function(x):
    """
    Example CPU-intensive function.
    
    This simulates a real computation that takes time and benefits
    from parallelization.
    """
    result = 0
    for i in range(x * 100):
        result += i ** 2 + i ** 0.5
    return result


def main():
    print("=" * 70)
    print("BAYESIAN OPTIMIZATION FOR PARAMETER TUNING")
    print("=" * 70)
    print()
    
    # Generate data
    data = range(100, 500)
    print(f"Data size: {len(list(data))} items")
    print(f"Function: {expensive_cpu_function.__name__}")
    print()
    
    # Example 1: Basic Bayesian Optimization
    print("=" * 70)
    print("Example 1: Basic Bayesian Optimization")
    print("=" * 70)
    print()
    print("Using Bayesian optimization to find optimal parameters with 20 trials...")
    print()
    
    result_bayesian = bayesian_tune_parameters(
        expensive_cpu_function,
        data,
        n_iterations=20,
        verbose=True
    )
    
    print()
    print(result_bayesian)
    
    # Example 2: Comparison with Grid Search
    print("\n" + "=" * 70)
    print("Example 2: Comparison - Bayesian vs Grid Search")
    print("=" * 70)
    print()
    
    # Bayesian optimization (20 trials)
    print("Running Bayesian optimization (20 trials)...")
    start_bayesian = time.time()
    result_bayesian = bayesian_tune_parameters(
        expensive_cpu_function,
        data,
        n_iterations=20,
        verbose=False
    )
    time_bayesian = time.time() - start_bayesian
    
    print(f"  Best speedup: {result_bayesian.best_speedup:.2f}x")
    print(f"  Configurations tested: {result_bayesian.configurations_tested}")
    print(f"  Time taken: {time_bayesian:.2f}s")
    print()
    
    # Grid search (comparable number of tests)
    print("Running grid search with comparable configuration count...")
    start_grid = time.time()
    result_grid = tune_parameters(
        expensive_cpu_function,
        data,
        n_jobs_range=[1, 2, 4],
        chunksize_range=[1, 10, 20, 50],
        verbose=False
    )
    time_grid = time.time() - start_grid
    
    print(f"  Best speedup: {result_grid.best_speedup:.2f}x")
    print(f"  Configurations tested: {result_grid.configurations_tested}")
    print(f"  Time taken: {time_grid:.2f}s")
    print()
    
    print("Comparison:")
    print(f"  Bayesian speedup: {result_bayesian.best_speedup:.2f}x vs Grid speedup: {result_grid.best_speedup:.2f}x")
    print(f"  Bayesian faster by: {(time_grid - time_bayesian) / time_grid * 100:.1f}%")
    
    # Example 3: Custom Search Bounds
    print("\n" + "=" * 70)
    print("Example 3: Custom Search Bounds")
    print("=" * 70)
    print()
    print("You can specify custom bounds for the search space...")
    print()
    
    result_custom = bayesian_tune_parameters(
        expensive_cpu_function,
        data,
        n_iterations=15,
        n_jobs_min=2,      # Only consider 2-8 workers
        n_jobs_max=8,
        chunksize_min=5,   # Only consider chunks of 5-50
        chunksize_max=50,
        verbose=True
    )
    
    print()
    print(f"Found optimal within constrained bounds:")
    print(f"  n_jobs={result_custom.best_n_jobs}, chunksize={result_custom.best_chunksize}")
    print(f"  Speedup: {result_custom.best_speedup:.2f}x")
    
    # Example 4: With Optimizer Hint
    print("\n" + "=" * 70)
    print("Example 4: Starting Near Optimizer Recommendation")
    print("=" * 70)
    print()
    print("Bayesian optimization can start near the optimizer's recommendation")
    print("for faster convergence to optimal parameters...")
    print()
    
    result_hint = bayesian_tune_parameters(
        expensive_cpu_function,
        data,
        n_iterations=15,
        use_optimizer_hint=True,  # Start search near optimizer recommendation
        verbose=True
    )
    
    if result_hint.optimization_hint:
        print()
        print(f"Optimizer suggested: n_jobs={result_hint.optimization_hint.n_jobs}, "
              f"chunksize={result_hint.optimization_hint.chunksize}")
        print(f"Bayesian found: n_jobs={result_hint.best_n_jobs}, "
              f"chunksize={result_hint.best_chunksize}")
        print(f"Speedup: {result_hint.best_speedup:.2f}x")
    
    # Example 5: Reproducible Results
    print("\n" + "=" * 70)
    print("Example 5: Reproducible Results with Random Seed")
    print("=" * 70)
    print()
    print("Use random_state for reproducible results...")
    print()
    
    result1 = bayesian_tune_parameters(
        expensive_cpu_function,
        data,
        n_iterations=10,
        random_state=42,
        verbose=False
    )
    
    result2 = bayesian_tune_parameters(
        expensive_cpu_function,
        data,
        n_iterations=10,
        random_state=42,
        verbose=False
    )
    
    print(f"Run 1: n_jobs={result1.best_n_jobs}, chunksize={result1.best_chunksize}")
    print(f"Run 2: n_jobs={result2.best_n_jobs}, chunksize={result2.best_chunksize}")
    
    if result1.best_n_jobs == result2.best_n_jobs and result1.best_chunksize == result2.best_chunksize:
        print("✅ Results are reproducible with same random_state!")
    
    # Example 6: Save Configuration
    print("\n" + "=" * 70)
    print("Example 6: Save Optimal Configuration for Reuse")
    print("=" * 70)
    print()
    
    # Save the best configuration found by Bayesian optimization
    result_bayesian.save_config(
        '/tmp/bayesian_optimal_config.json',
        function_name='expensive_cpu_function',
        notes='Found via Bayesian optimization with 20 iterations'
    )
    print(f"Saved optimal configuration to /tmp/bayesian_optimal_config.json")
    print(f"  n_jobs: {result_bayesian.best_n_jobs}")
    print(f"  chunksize: {result_bayesian.best_chunksize}")
    print(f"  Expected speedup: {result_bayesian.best_speedup:.2f}x")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Key Benefits of Bayesian Optimization:")
    print("  ✅ Fewer trials needed than grid search")
    print("  ✅ Intelligently explores parameter space")
    print("  ✅ Finds near-optimal configurations efficiently")
    print("  ✅ Especially useful for expensive benchmarks")
    print()
    print("When to use:")
    print("  • Benchmarking is slow (large datasets or expensive functions)")
    print("  • Search space is large (many possible configurations)")
    print("  • You need near-optimal results with limited time/resources")
    print()
    print("When to use grid search instead:")
    print("  • Search space is small (few configurations to test)")
    print("  • Benchmarking is fast")
    print("  • You want exhaustive search of all possibilities")
    print()


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        if "skopt" in str(e):
            print("Error: scikit-optimize not installed.")
            print()
            print("Bayesian optimization requires scikit-optimize.")
            print("Install with:")
            print("  pip install scikit-optimize")
            print()
            print("Or install with amorsize:")
            print("  pip install amorsize[bayesian]")
        else:
            raise
