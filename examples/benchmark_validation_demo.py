"""
Benchmark Validation Examples

This module demonstrates how to use the benchmark validation feature
to empirically verify optimizer recommendations.
"""

from amorsize import optimize, validate_optimization, quick_validate
import time


def example_1_basic_validation():
    """Example 1: Basic validation of optimizer recommendations."""
    print("=" * 60)
    print("Example 1: Basic Benchmark Validation")
    print("=" * 60)
    
    def expensive_computation(x):
        """Simulate expensive computation."""
        result = 0
        for i in range(x):
            result += i ** 2
        return result
    
    data = range(100, 200)  # 100 items
    
    print("\nStep 1: Optimize")
    opt = optimize(expensive_computation, data, verbose=True)
    
    print(f"\nStep 2: Validate (benchmarking {len(data)} items)")
    benchmark = validate_optimization(
        expensive_computation,
        data,
        optimization=opt,
        verbose=True
    )
    
    print(f"\nStep 3: Results")
    print(benchmark)
    
    if benchmark.is_accurate(threshold=75.0):
        print("\n✓ Optimizer predictions are accurate!")
    else:
        print("\n⚠️ Optimizer predictions deviate from actual performance")


def example_2_quick_validation():
    """Example 2: Quick validation using sampling."""
    print("\n" + "=" * 60)
    print("Example 2: Quick Validation (Fast)")
    print("=" * 60)
    
    def process_item(x):
        """Process a single item."""
        return sum(i**2 for i in range(x))
    
    # Large dataset
    data = range(100, 1000)  # 900 items
    
    print(f"\nDataset size: {len(data)} items")
    print("Using quick_validate() to sample 100 items...")
    
    start = time.perf_counter()
    result = quick_validate(
        process_item,
        data,
        sample_size=100,
        verbose=True
    )
    end = time.perf_counter()
    
    print(f"\nValidation completed in {end - start:.2f}s")
    print(f"Prediction accuracy: {result.accuracy_percent:.1f}%")
    
    if result.is_accurate():
        print("✓ Quick check passed - recommendations appear accurate")


def example_3_validation_without_precomputed():
    """Example 3: Validation without pre-computing optimization."""
    print("\n" + "=" * 60)
    print("Example 3: One-Step Validation")
    print("=" * 60)
    
    def compute(x):
        """Computational workload."""
        total = 0
        for i in range(x):
            total += i * (i + 1) // 2
        return total
    
    data = range(50, 150)
    
    print("\nValidating without pre-computing optimization...")
    print("(optimize() will be called automatically)")
    
    # validate_optimization() will call optimize() internally
    result = validate_optimization(
        compute,
        data,
        optimization=None,  # Will be computed
        verbose=True
    )
    
    print(f"\nRecommended: n_jobs={result.optimization.n_jobs}, "
          f"chunksize={result.optimization.chunksize}")
    print(f"Actual speedup: {result.actual_speedup:.2f}x")
    print(f"Predicted speedup: {result.predicted_speedup:.2f}x")
    print(f"Accuracy: {result.accuracy_percent:.1f}%")


def example_4_fast_function():
    """Example 4: Validation of fast function (serial recommended)."""
    print("\n" + "=" * 60)
    print("Example 4: Fast Function (Serial Execution)")
    print("=" * 60)
    
    def fast_function(x):
        """Very fast function - parallelization overhead dominates."""
        return x ** 2
    
    data = range(1000)
    
    print("\nFunction is very fast (< 1μs per item)")
    print("Expecting optimizer to recommend serial execution...")
    
    result = validate_optimization(
        fast_function,
        data,
        max_items=200,
        verbose=True
    )
    
    print(f"\nOptimizer decision: n_jobs={result.optimization.n_jobs}")
    print(f"Reason: {result.optimization.reason}")
    
    print("\nValidation results:")
    print(f"  Serial time: {result.serial_time:.4f}s")
    print(f"  Parallel time: {result.parallel_time:.4f}s")
    print(f"  Speedup: {result.actual_speedup:.2f}x")
    
    if result.optimization.n_jobs == 1:
        print("\n✓ Serial execution confirmed as optimal")


def example_5_large_dataset_with_limit():
    """Example 5: Validate large dataset with max_items limit."""
    print("\n" + "=" * 60)
    print("Example 5: Large Dataset with Item Limit")
    print("=" * 60)
    
    def process(x):
        """Process item."""
        result = 0
        for i in range(x):
            result += i ** 2
        return result
    
    # Very large dataset
    data = range(100, 10000)  # 9,900 items
    
    print(f"\nTotal dataset size: {len(data)} items")
    print("Using max_items=200 to limit benchmark runtime...")
    
    result = validate_optimization(
        process,
        data,
        max_items=200,  # Only benchmark first 200 items
        verbose=True
    )
    
    print(f"\nBenchmarked {200} items (2% of dataset)")
    print(f"Prediction accuracy: {result.accuracy_percent:.1f}%")
    print("\nNote: Results are representative for similar workloads")


def example_6_accuracy_thresholds():
    """Example 6: Using accuracy thresholds for decision making."""
    print("\n" + "=" * 60)
    print("Example 6: Accuracy Threshold Checking")
    print("=" * 60)
    
    def workload(x):
        """Computational workload."""
        return sum(i**2 for i in range(x))
    
    data = range(100, 300)
    
    print("\nRunning validation...")
    result = validate_optimization(
        workload,
        data,
        max_items=100,
        verbose=False
    )
    
    print(f"Prediction accuracy: {result.accuracy_percent:.1f}%")
    
    # Check against different thresholds
    thresholds = [90, 75, 60]
    for threshold in thresholds:
        if result.is_accurate(threshold=threshold):
            print(f"  ✓ Meets {threshold}% accuracy threshold")
        else:
            print(f"  ✗ Below {threshold}% accuracy threshold")
    
    # Decision making based on accuracy
    print("\nDecision:")
    if result.is_accurate(threshold=75):
        print("  → Recommendations are reliable for production use")
    elif result.is_accurate(threshold=60):
        print("  → Recommendations are acceptable, but validate in production")
    else:
        print("  → System-specific factors detected - investigate further")


def example_7_production_validation_workflow():
    """Example 7: Complete production validation workflow."""
    print("\n" + "=" * 60)
    print("Example 7: Production Validation Workflow")
    print("=" * 60)
    
    def critical_computation(x):
        """Production-critical computation."""
        result = 0
        for i in range(x):
            result += (i ** 2) % 1000
        return result
    
    data = range(100, 500)
    
    print("\nProduction Validation Workflow:")
    print("1. Optimize workload")
    print("2. Validate recommendations")
    print("3. Check accuracy")
    print("4. Make deployment decision")
    
    # Step 1: Optimize
    print("\nStep 1: Optimizing...")
    opt = optimize(critical_computation, data, verbose=False)
    print(f"  Recommendation: n_jobs={opt.n_jobs}, chunksize={opt.chunksize}")
    print(f"  Predicted speedup: {opt.estimated_speedup:.2f}x")
    
    # Step 2: Validate
    print("\nStep 2: Validating...")
    benchmark = validate_optimization(
        critical_computation,
        data,
        optimization=opt,
        max_items=200,
        verbose=False
    )
    
    # Step 3: Check accuracy
    print("\nStep 3: Checking accuracy...")
    print(f"  Actual speedup: {benchmark.actual_speedup:.2f}x")
    print(f"  Prediction error: {benchmark.error_percent:+.1f}%")
    print(f"  Accuracy: {benchmark.accuracy_percent:.1f}%")
    
    # Step 4: Make decision
    print("\nStep 4: Deployment decision...")
    if benchmark.is_accurate(threshold=75):
        print("  ✓ APPROVED: Recommendations validated for production")
        print(f"  → Deploy with n_jobs={opt.n_jobs}, chunksize={opt.chunksize}")
    elif benchmark.is_accurate(threshold=60):
        print("  ⚠️ CAUTION: Moderate accuracy - deploy with monitoring")
        print(f"  → Deploy with n_jobs={opt.n_jobs} but monitor actual performance")
    else:
        print("  ❌ REJECTED: Low accuracy - investigate system factors")
        print("  → Review system configuration and retry validation")
    
    # Show recommendations
    if benchmark.recommendations:
        print("\nRecommendations:")
        for rec in benchmark.recommendations:
            print(f"  • {rec}")


def main():
    """Run all examples."""
    examples = [
        ("Basic Validation", example_1_basic_validation),
        ("Quick Validation", example_2_quick_validation),
        ("One-Step Validation", example_3_validation_without_precomputed),
        ("Fast Function", example_4_fast_function),
        ("Large Dataset", example_5_large_dataset_with_limit),
        ("Accuracy Thresholds", example_6_accuracy_thresholds),
        ("Production Workflow", example_7_production_validation_workflow),
    ]
    
    print("\n" + "=" * 60)
    print("AMORSIZE BENCHMARK VALIDATION EXAMPLES")
    print("=" * 60)
    print("\nThese examples demonstrate how to validate optimizer")
    print("recommendations through empirical benchmarking.")
    print("\nPress Enter to continue through examples...")
    
    for i, (name, example_func) in enumerate(examples, 1):
        if i > 1:
            input(f"\nPress Enter for Example {i}: {name}...")
        try:
            example_func()
        except KeyboardInterrupt:
            print("\n\nExamples interrupted by user.")
            break
        except Exception as e:
            print(f"\nError in example: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
