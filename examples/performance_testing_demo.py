"""
Performance Regression Testing Demo

This example demonstrates how to use Amorsize's performance regression testing
framework to validate optimizer accuracy and detect performance degradations.
"""

from pathlib import Path
from amorsize import (
    run_performance_suite,
    run_performance_benchmark,
    compare_performance_results,
    get_standard_workloads,
    WorkloadSpec
)


def example_1_run_standard_suite():
    """Example 1: Run the standard benchmark suite."""
    print("=" * 70)
    print("Example 1: Running Standard Benchmark Suite")
    print("=" * 70)
    
    # Run all standard workloads with validation
    results = run_performance_suite(
        run_validation=True,
        validate_max_items=30,  # Smaller sample for demo
        verbose=True
    )
    
    # Summary
    passed = sum(1 for r in results.values() if r.passed)
    print(f"\nResults: {passed}/{len(results)} benchmarks passed")
    
    return results


def example_2_single_workload():
    """Example 2: Run a single benchmark workload."""
    print("\n" + "=" * 70)
    print("Example 2: Running Single Workload")
    print("=" * 70)
    
    # Get CPU-intensive workload
    workload = get_standard_workloads()[0]
    
    print(f"\nWorkload: {workload.name}")
    print(f"Description: {workload.description}")
    
    # Run benchmark
    result = run_performance_benchmark(
        workload,
        run_validation=True,
        validate_max_items=20,
        verbose=True
    )
    
    # Check results
    if result.passed:
        print("\n✅ Benchmark PASSED")
    else:
        print("\n❌ Benchmark FAILED")
        print("Issues:")
        for issue in result.issues:
            print(f"  - {issue}")
    
    return result


def example_3_custom_workload():
    """Example 3: Create and test a custom workload."""
    print("\n" + "=" * 70)
    print("Example 3: Custom Workload")
    print("=" * 70)
    
    # Define custom function
    def matrix_multiply(n):
        """Simple matrix multiplication."""
        import random
        # Create small matrices
        A = [[random.random() for _ in range(n)] for _ in range(n)]
        B = [[random.random() for _ in range(n)] for _ in range(n)]
        
        # Multiply
        C = [[0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    C[i][j] += A[i][k] * B[k][j]
        
        return C
    
    # Create workload spec
    custom_workload = WorkloadSpec(
        name="matrix_multiply",
        description="Matrix multiplication benchmark",
        func=matrix_multiply,
        data_generator=lambda n: list(range(10, 10 + n)),
        data_size=20,
        expected_workload_type="cpu_bound",
        min_speedup=1.2,
        max_execution_time=30.0
    )
    
    print(f"\nCustom workload: {custom_workload.name}")
    print(f"Description: {custom_workload.description}")
    
    # Run benchmark
    result = run_performance_benchmark(
        custom_workload,
        run_validation=True,
        validate_max_items=10,
        verbose=False
    )
    
    print(f"\nResult: {'PASSED' if result.passed else 'FAILED'}")
    if result.benchmark_result:
        print(f"Actual speedup: {result.benchmark_result['actual_speedup']:.2f}x")
        print(f"Accuracy: {result.benchmark_result['accuracy_percent']:.1f}%")
    
    return result


def example_4_save_and_compare():
    """Example 4: Save results and compare versions."""
    print("\n" + "=" * 70)
    print("Example 4: Save and Compare Results")
    print("=" * 70)
    
    # Create temp directory for demo
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        current_path = Path(tmpdir) / "current.json"
        
        # Run baseline benchmarks
        print("\nRunning baseline benchmarks...")
        run_performance_suite(
            run_validation=True,
            validate_max_items=20,
            verbose=False,
            save_results=True,
            results_path=baseline_path
        )
        print(f"Baseline saved to: {baseline_path}")
        
        # Simulate "current" version (same for demo purposes)
        print("\nRunning current benchmarks...")
        run_performance_suite(
            run_validation=True,
            validate_max_items=20,
            verbose=False,
            save_results=True,
            results_path=current_path
        )
        print(f"Current saved to: {current_path}")
        
        # Compare results
        print("\nComparing results...")
        comparison = compare_performance_results(
            baseline_path,
            current_path,
            regression_threshold=0.10  # 10%
        )
        
        # Display comparison
        print(f"\nComparison Results:")
        print(f"  Regressions: {len(comparison['regressions'])}")
        print(f"  Improvements: {len(comparison['improvements'])}")
        print(f"  Unchanged: {len(comparison['unchanged'])}")
        
        if comparison['regressions']:
            print("\n⚠️  Performance Regressions:")
            for reg in comparison['regressions']:
                print(f"    {reg['workload']}: "
                      f"{reg['baseline_speedup']:.2f}x → "
                      f"{reg['current_speedup']:.2f}x "
                      f"({reg['change_percent']:.1f}%)")
        else:
            print("\n✅ No regressions detected")
        
        if comparison['improvements']:
            print("\n🎉 Performance Improvements:")
            for imp in comparison['improvements']:
                print(f"    {imp['workload']}: "
                      f"{imp['baseline_speedup']:.2f}x → "
                      f"{imp['current_speedup']:.2f}x "
                      f"({imp['change_percent']:+.1f}%)")
        
        return comparison


def example_5_lightweight_testing():
    """Example 5: Lightweight testing without validation (faster)."""
    print("\n" + "=" * 70)
    print("Example 5: Lightweight Testing (No Validation)")
    print("=" * 70)
    
    print("\nRunning optimizer-only tests (fast)...")
    
    # Run without validation for speed
    results = run_performance_suite(
        run_validation=False,  # Skip empirical validation
        verbose=False
    )
    
    # Check optimizer recommendations
    print("\nOptimizer Recommendations:")
    for name, result in results.items():
        opt = result.optimizer_result
        print(f"  {name}:")
        print(f"    n_jobs={opt['n_jobs']}, "
              f"chunksize={opt['chunksize']}, "
              f"speedup={opt['estimated_speedup']:.2f}x")
    
    passed = sum(1 for r in results.values() if r.passed)
    print(f"\n{passed}/{len(results)} benchmarks passed (optimizer-only)")
    
    return results


def example_6_detect_anomalies():
    """Example 6: Detect anomalies in optimizer behavior."""
    print("\n" + "=" * 70)
    print("Example 6: Detecting Anomalies")
    print("=" * 70)
    
    # Run benchmarks
    results = run_performance_suite(
        run_validation=True,
        validate_max_items=20,
        verbose=False
    )
    
    # Analyze for anomalies
    print("\nAnomaly Detection:")
    
    for name, result in results.items():
        issues = []
        
        # Check for unrealistic recommendations
        opt = result.optimizer_result
        if opt['n_jobs'] > 64:
            issues.append(f"Unusually high n_jobs: {opt['n_jobs']}")
        
        if opt['chunksize'] < 1:
            issues.append(f"Invalid chunksize: {opt['chunksize']}")
        
        # Check prediction accuracy if validation was run
        if result.benchmark_result:
            bench = result.benchmark_result
            if bench['accuracy_percent'] < 50:
                issues.append(
                    f"Poor prediction accuracy: {bench['accuracy_percent']:.1f}%"
                )
            
            # Check for negative scaling
            if bench['actual_speedup'] < 0.8:
                issues.append(
                    f"Negative scaling: {bench['actual_speedup']:.2f}x speedup"
                )
        
        if issues:
            print(f"\n  ⚠️  {name}:")
            for issue in issues:
                print(f"      - {issue}")
    
    print("\nAnomaly detection complete")
    
    return results


def main():
    """Run all examples."""
    print("AMORSIZE PERFORMANCE REGRESSION TESTING DEMO")
    print("=" * 70)
    
    # Example 1: Run standard suite
    example_1_run_standard_suite()
    
    # Example 2: Single workload
    example_2_single_workload()
    
    # Example 3: Custom workload
    example_3_custom_workload()
    
    # Example 4: Save and compare
    example_4_save_and_compare()
    
    # Example 5: Lightweight testing
    example_5_lightweight_testing()
    
    # Example 6: Detect anomalies
    example_6_detect_anomalies()
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
