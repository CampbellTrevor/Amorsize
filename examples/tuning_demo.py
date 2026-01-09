"""
Auto-Tuning Demo - Empirical Parameter Optimization

This script demonstrates how to use Amorsize's auto-tuning feature to find
optimal n_jobs and chunksize parameters through empirical benchmarking.
"""

import time
from amorsize import tune_parameters, quick_tune, optimize


def cpu_intensive_func(x):
    """
    CPU-intensive function for demonstration.
    
    Simulates expensive computation that benefits from parallelization.
    """
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def fast_func(x):
    """
    Very fast function for demonstration.
    
    This function is so fast that parallelization overhead dominates,
    making serial execution the best choice.
    """
    return x * 2


def io_bound_func(x):
    """
    I/O-bound function simulation.
    
    Simulates I/O-bound work where threads are more appropriate than processes.
    """
    time.sleep(0.01)  # Simulate I/O wait
    return x * 2


def demo_basic_tuning():
    """Demonstrate basic auto-tuning."""
    print("=" * 70)
    print("DEMO 1: Basic Auto-Tuning")
    print("=" * 70)
    
    data = range(100, 300)
    
    print("\nTuning CPU-intensive function...")
    result = tune_parameters(
        cpu_intensive_func,
        data,
        n_jobs_range=[1, 2, 4],
        chunksize_range=[20, 50],
        verbose=True
    )
    
    print("\n" + "=" * 70)
    print("RESULT:")
    print("=" * 70)
    print(result)
    
    # Show top configurations
    print("\nTop 3 configurations:")
    for i, (n_jobs, chunksize, time_taken, speedup) in enumerate(result.get_top_configurations(3), 1):
        print(f"  {i}. n_jobs={n_jobs:2d}, chunksize={chunksize:3d} -> "
              f"{time_taken:.4f}s ({speedup:.2f}x)")


def demo_quick_tune():
    """Demonstrate quick tuning for fast iteration."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Quick Tuning")
    print("=" * 70)
    
    data = range(100, 300)
    
    print("\nQuick tuning (minimal search space)...")
    result = quick_tune(cpu_intensive_func, data, verbose=True)
    
    print("\n" + "=" * 70)
    print("RESULT:")
    print("=" * 70)
    print(result)


def demo_comparison_with_optimizer():
    """Compare tuning results with optimizer recommendations."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Comparison with Optimizer")
    print("=" * 70)
    
    data = range(100, 300)
    
    # Get optimizer recommendation
    print("\nGetting optimizer recommendation...")
    opt_result = optimize(cpu_intensive_func, data, verbose=False)
    print(f"Optimizer: n_jobs={opt_result.n_jobs}, chunksize={opt_result.chunksize}, "
          f"estimated_speedup={opt_result.estimated_speedup:.2f}x")
    
    # Get tuning result
    print("\nRunning auto-tuning...")
    tune_result = tune_parameters(
        cpu_intensive_func,
        data,
        use_optimizer_hint=True,  # Include optimizer hint in search
        verbose=False
    )
    print(f"Tuning:    n_jobs={tune_result.best_n_jobs}, chunksize={tune_result.best_chunksize}, "
          f"actual_speedup={tune_result.best_speedup:.2f}x")
    
    # Compare
    print("\n" + "=" * 70)
    print("COMPARISON:")
    print("=" * 70)
    
    if (opt_result.n_jobs == tune_result.best_n_jobs and 
        opt_result.chunksize == tune_result.best_chunksize):
        print("✅ Optimizer recommendation confirmed by empirical tuning!")
    else:
        print("ℹ️  Tuning found different optimal configuration")
        print(f"   Optimizer suggested: {opt_result.n_jobs}x{opt_result.chunksize}")
        print(f"   Tuning found:        {tune_result.best_n_jobs}x{tune_result.best_chunksize}")
    
    # Compare speedups
    speedup_diff = tune_result.best_speedup - opt_result.estimated_speedup
    accuracy = (1 - abs(speedup_diff) / max(tune_result.best_speedup, 0.01)) * 100
    print(f"\nSpeedup prediction accuracy: {accuracy:.1f}%")


def demo_fast_function():
    """Demonstrate tuning on a fast function (serial is optimal)."""
    print("\n\n" + "=" * 70)
    print("DEMO 4: Fast Function (Serial Optimal)")
    print("=" * 70)
    
    data = range(1000)
    
    print("\nTuning very fast function...")
    print("(Expected: Serial execution should be fastest)")
    
    result = tune_parameters(
        fast_func,
        data,
        n_jobs_range=[1, 2, 4],
        chunksize_range=[50, 100],
        verbose=True
    )
    
    print("\n" + "=" * 70)
    print("ANALYSIS:")
    print("=" * 70)
    
    if result.best_n_jobs == 1:
        print("✅ Correctly identified that serial execution is optimal!")
        print("   For very fast functions, parallelization overhead dominates.")
    else:
        print(f"ℹ️  Parallel execution slightly better: {result.best_speedup:.2f}x")


def demo_custom_search_space():
    """Demonstrate custom search space specification."""
    print("\n\n" + "=" * 70)
    print("DEMO 5: Custom Search Space")
    print("=" * 70)
    
    data = range(100, 300)
    
    # Custom search space
    custom_n_jobs = [1, 2, 4, 8]
    custom_chunksize = [10, 25, 50, 100]
    
    print(f"\nCustom search space:")
    print(f"  n_jobs: {custom_n_jobs}")
    print(f"  chunksize: {custom_chunksize}")
    print(f"  Total configurations: {len(custom_n_jobs) * len(custom_chunksize)}")
    
    result = tune_parameters(
        cpu_intensive_func,
        data,
        n_jobs_range=custom_n_jobs,
        chunksize_range=custom_chunksize,
        use_optimizer_hint=False,  # Pure empirical search
        verbose=True
    )
    
    print("\n" + "=" * 70)
    print("RESULT:")
    print("=" * 70)
    print(f"Best configuration: n_jobs={result.best_n_jobs}, chunksize={result.best_chunksize}")
    print(f"Speedup: {result.best_speedup:.2f}x")
    print(f"Configurations tested: {result.configurations_tested}")


def demo_thread_executor():
    """Demonstrate tuning with ThreadPoolExecutor for I/O-bound work."""
    print("\n\n" + "=" * 70)
    print("DEMO 6: Thread Executor for I/O-Bound Work")
    print("=" * 70)
    
    data = range(20)  # Small dataset since each item sleeps 10ms
    
    print("\nTuning I/O-bound function with threads...")
    
    result = tune_parameters(
        io_bound_func,
        data,
        n_jobs_range=[1, 2, 4],
        chunksize_range=[5],
        prefer_threads_for_io=True,
        verbose=True
    )
    
    print("\n" + "=" * 70)
    print("RESULT:")
    print("=" * 70)
    print(result)
    print(f"\nNote: Using {result.executor_type} executor (threads for I/O-bound work)")


def demo_result_analysis():
    """Demonstrate analyzing tuning results."""
    print("\n\n" + "=" * 70)
    print("DEMO 7: Result Analysis")
    print("=" * 70)
    
    data = range(100, 300)
    
    result = tune_parameters(
        cpu_intensive_func,
        data,
        verbose=False
    )
    
    print("\nDetailed Result Analysis:")
    print("=" * 70)
    
    # Basic info
    print(f"\nBest Configuration:")
    print(f"  n_jobs:     {result.best_n_jobs}")
    print(f"  chunksize:  {result.best_chunksize}")
    print(f"  time:       {result.best_time:.4f}s")
    print(f"  speedup:    {result.best_speedup:.2f}x")
    
    # All results
    print(f"\nAll Configurations Tested ({len(result.all_results)}):")
    sorted_results = sorted(result.all_results.items(), key=lambda x: x[1])
    for (n_jobs, chunksize), exec_time in sorted_results[:5]:
        speedup = result.serial_time / exec_time if exec_time > 0 else 0
        indicator = "⭐" if (n_jobs == result.best_n_jobs and chunksize == result.best_chunksize) else "  "
        print(f"  {indicator} n_jobs={n_jobs:2d}, chunksize={chunksize:3d} -> "
              f"{exec_time:.4f}s ({speedup:.2f}x)")
    
    # Optimizer hint comparison
    if result.optimization_hint:
        print(f"\nOptimizer Hint:")
        print(f"  n_jobs:     {result.optimization_hint.n_jobs}")
        print(f"  chunksize:  {result.optimization_hint.chunksize}")
        print(f"  estimated:  {result.optimization_hint.estimated_speedup:.2f}x")
        
        # Check if optimizer was correct
        hint_config = (result.optimization_hint.n_jobs, result.optimization_hint.chunksize)
        if hint_config in result.all_results:
            hint_time = result.all_results[hint_config]
            hint_speedup = result.serial_time / hint_time
            print(f"  actual:     {hint_speedup:.2f}x")
            
            if hint_config == (result.best_n_jobs, result.best_chunksize):
                print("  ✅ Optimizer prediction was optimal!")
            else:
                diff = ((hint_time - result.best_time) / result.best_time) * 100
                print(f"  ℹ️  Optimizer was {diff:.1f}% slower than optimal")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("AMORSIZE AUTO-TUNING DEMONSTRATIONS")
    print("=" * 70)
    print("\nThese demos show how to use auto-tuning to empirically find")
    print("optimal parallelization parameters for your workloads.")
    
    try:
        demo_basic_tuning()
        demo_quick_tune()
        demo_comparison_with_optimizer()
        demo_fast_function()
        demo_custom_search_space()
        demo_thread_executor()
        demo_result_analysis()
        
        print("\n\n" + "=" * 70)
        print("ALL DEMOS COMPLETE")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  1. Use tune_parameters() for thorough empirical optimization")
        print("  2. Use quick_tune() for faster iteration")
        print("  3. Compare with optimizer to validate predictions")
        print("  4. Customize search space for large datasets")
        print("  5. Use threads for I/O-bound workloads")
        print("\nFor more information, see examples/README_tuning.md")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
