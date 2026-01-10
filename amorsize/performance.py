"""
Performance regression testing framework for Amorsize.

This module provides tools to run standardized benchmark workloads and detect
performance regressions across different versions or code changes. It's designed
to be used in CI/CD pipelines to ensure optimizer accuracy doesn't degrade.
"""

import time
import math
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

from .optimizer import optimize, OptimizationResult
from .benchmark import validate_optimization, BenchmarkResult


@dataclass
class WorkloadSpec:
    """
    Specification for a benchmark workload.
    
    Attributes:
        name: Human-readable name for the workload
        description: What this workload tests
        func: The function to benchmark
        data_generator: Function that generates test data
        data_size: Number of items to process
        expected_workload_type: Expected workload type (cpu_bound, io_bound, mixed)
        min_speedup: Minimum acceptable speedup (for regression detection)
        max_execution_time: Maximum acceptable execution time in seconds
    """
    name: str
    description: str
    func: Callable[[Any], Any]
    data_generator: Callable[[int], List[Any]]
    data_size: int
    expected_workload_type: str = "cpu_bound"
    min_speedup: float = 1.0
    max_execution_time: float = 60.0


@dataclass
class PerformanceResult:
    """
    Result from running a performance benchmark.
    
    Attributes:
        workload_name: Name of the workload that was tested
        optimizer_result: OptimizationResult from the optimizer
        benchmark_result: BenchmarkResult from validation (if run)
        passed: Whether the benchmark passed all checks
        regression_detected: Whether a performance regression was detected
        issues: List of issues found during benchmarking
        metadata: Additional metadata about the benchmark run
    """
    workload_name: str
    optimizer_result: Dict[str, Any]  # Serialized OptimizationResult
    benchmark_result: Optional[Dict[str, Any]]  # Serialized BenchmarkResult
    passed: bool
    regression_detected: bool
    issues: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'workload_name': self.workload_name,
            'optimizer_result': self.optimizer_result,
            'benchmark_result': self.benchmark_result,
            'passed': self.passed,
            'regression_detected': self.regression_detected,
            'issues': self.issues,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceResult':
        """Create from dictionary."""
        return cls(**data)


def _serialize_optimizer_result(result: OptimizationResult) -> Dict[str, Any]:
    """Serialize OptimizationResult to dictionary."""
    return {
        'n_jobs': result.n_jobs,
        'chunksize': result.chunksize,
        'reason': result.reason,
        'estimated_speedup': result.estimated_speedup,
        'warnings': result.warnings,
        'executor_type': result.executor_type
    }


def _serialize_benchmark_result(result: BenchmarkResult) -> Dict[str, Any]:
    """Serialize BenchmarkResult to dictionary."""
    return {
        'serial_time': result.serial_time,
        'parallel_time': result.parallel_time,
        'actual_speedup': result.actual_speedup,
        'predicted_speedup': result.predicted_speedup,
        'accuracy_percent': result.accuracy_percent,
        'error_percent': result.error_percent,
        'recommendations': result.recommendations
    }


# Standard benchmark workloads

def _cpu_intensive_func(n: int) -> int:
    """CPU-intensive workload: Prime checking and factorization."""
    def is_prime(num):
        if num < 2:
            return False
        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0:
                return False
        return True
    
    # Count primes and sum of squares
    prime_count = sum(1 for i in range(2, n) if is_prime(i))
    sum_squares = sum(i**2 for i in range(n))
    return prime_count + sum_squares


def _mixed_workload_func(n: int) -> Dict[str, int]:
    """Mixed workload: Computation + some I/O simulation."""
    # CPU-bound computation
    result = sum(i**2 for i in range(n))
    
    # Simulate light I/O with sleep
    time.sleep(0.0001)  # 0.1ms I/O simulation
    
    return {'sum': result, 'count': n}


def _memory_intensive_func(n: int) -> List[int]:
    """Memory-intensive workload: Large data structures."""
    # Create large list and perform operations
    data = list(range(n * 100))
    # Sort and filter
    filtered = [x for x in data if x % 3 == 0]
    filtered.sort(reverse=True)
    return filtered[:100]  # Return small result despite large intermediate


def get_standard_workloads() -> List[WorkloadSpec]:
    """
    Get the standard benchmark workloads for performance testing.
    
    Returns:
        List of WorkloadSpec objects for different workload patterns
        
    Standard Workloads:
        1. CPU-Intensive: Pure computation (prime checking)
        2. Mixed: Computation + light I/O
        3. Memory-Intensive: Large data structures
        4. Fast-Function: Very quick execution (may not benefit from parallelism)
        5. Variable-Time: Heterogeneous workload with varying execution times
    """
    workloads = [
        WorkloadSpec(
            name="cpu_intensive",
            description="Pure CPU-bound computation (prime checking)",
            func=_cpu_intensive_func,
            data_generator=lambda n: list(range(1000, 1000 + n)),
            data_size=100,
            expected_workload_type="cpu_bound",
            min_speedup=1.2,  # Realistic for small workloads with spawn overhead
            max_execution_time=30.0
        ),
        WorkloadSpec(
            name="mixed_workload",
            description="Mixed CPU and I/O workload",
            func=_mixed_workload_func,
            data_generator=lambda n: list(range(500, 500 + n)),
            data_size=100,
            expected_workload_type="mixed",
            min_speedup=1.2,
            max_execution_time=30.0
        ),
        WorkloadSpec(
            name="memory_intensive",
            description="Memory-intensive with large intermediate data",
            func=_memory_intensive_func,
            data_generator=lambda n: list(range(100, 100 + n)),
            data_size=50,
            expected_workload_type="cpu_bound",
            min_speedup=0.9,  # Memory overhead can prevent speedup
            max_execution_time=30.0
        ),
        WorkloadSpec(
            name="fast_function",
            description="Very fast function (may not benefit from parallelism)",
            func=lambda x: x ** 2,
            data_generator=lambda n: list(range(n)),
            data_size=1000,
            expected_workload_type="cpu_bound",
            min_speedup=0.8,  # May actually be slower with parallelism overhead
            max_execution_time=10.0
        ),
        WorkloadSpec(
            name="variable_time",
            description="Heterogeneous workload with varying execution times",
            func=lambda x: sum(i**2 for i in range(x)),
            data_generator=lambda n: list(range(100, 100 + n * 10, 10)),
            data_size=50,
            expected_workload_type="cpu_bound",
            min_speedup=0.9,  # Small heterogeneous workloads may not benefit
            max_execution_time=30.0
        ),
    ]
    
    return workloads


def run_performance_benchmark(
    workload: WorkloadSpec,
    run_validation: bool = True,
    validate_max_items: int = 50,
    verbose: bool = False
) -> PerformanceResult:
    """
    Run a performance benchmark on a specific workload.
    
    Args:
        workload: WorkloadSpec defining the benchmark
        run_validation: Whether to run empirical validation (default: True)
        validate_max_items: Max items for validation benchmark (default: 50)
        verbose: Print progress information (default: False)
    
    Returns:
        PerformanceResult with benchmark results and regression detection
        
    Example:
        >>> workload = get_standard_workloads()[0]  # CPU-intensive
        >>> result = run_performance_benchmark(workload, verbose=True)
        >>> print(f"Passed: {result.passed}")
        >>> print(f"Issues: {result.issues}")
    """
    if verbose:
        print(f"\n=== Running benchmark: {workload.name} ===")
        print(f"Description: {workload.description}")
        print(f"Data size: {workload.data_size}")
    
    issues = []
    regression_detected = False
    
    # Generate test data
    # CRITICAL FIX: When running validation, optimize on the SAME dataset size
    # that will be used for empirical testing. Otherwise, the optimizer optimizes
    # for a large dataset but gets validated on a small subset where overhead dominates.
    actual_data_size = min(workload.data_size, validate_max_items) if run_validation else workload.data_size
    data = workload.data_generator(actual_data_size)
    
    # Run optimizer
    if verbose:
        print("Running optimizer...")
    
    start_opt = time.perf_counter()
    try:
        opt_result = optimize(workload.func, data, verbose=False)
        opt_time = time.perf_counter() - start_opt
        
        if verbose:
            print(f"Optimizer completed in {opt_time:.4f}s")
            print(f"Recommendation: n_jobs={opt_result.n_jobs}, "
                  f"chunksize={opt_result.chunksize}, "
                  f"speedup={opt_result.estimated_speedup:.2f}x")
    except Exception as e:
        issues.append(f"Optimizer failed: {str(e)}")
        return PerformanceResult(
            workload_name=workload.name,
            optimizer_result={},
            benchmark_result=None,
            passed=False,
            regression_detected=False,
            issues=issues,
            metadata={'error': str(e)}
        )
    
    # Run empirical validation if requested
    benchmark_result = None
    if run_validation:
        if verbose:
            print("Running empirical validation...")
        
        try:
            bench = validate_optimization(
                workload.func,
                data,
                optimization=opt_result,
                max_items=validate_max_items,
                verbose=False
            )
            benchmark_result = bench
            
            if verbose:
                print(f"Validation completed")
                print(f"Actual speedup: {bench.actual_speedup:.2f}x")
                print(f"Predicted speedup: {bench.predicted_speedup:.2f}x")
                print(f"Accuracy: {bench.accuracy_percent:.1f}%")
            
            # Check for regression: actual speedup significantly below minimum
            if bench.actual_speedup < workload.min_speedup * 0.8:
                regression_detected = True
                issues.append(
                    f"Performance regression: Speedup {bench.actual_speedup:.2f}x "
                    f"is below minimum {workload.min_speedup:.2f}x"
                )
            
            # Check accuracy: predictions should be reasonably accurate
            if bench.accuracy_percent < 50.0:
                issues.append(
                    f"Low prediction accuracy: {bench.accuracy_percent:.1f}% "
                    f"(predictions may be unreliable)"
                )
            
            # Check execution time
            if bench.parallel_time > workload.max_execution_time:
                issues.append(
                    f"Execution time {bench.parallel_time:.2f}s exceeds "
                    f"maximum {workload.max_execution_time:.2f}s"
                )
        
        except Exception as e:
            issues.append(f"Validation failed: {str(e)}")
    
    # Determine if benchmark passed
    passed = len(issues) == 0
    
    if verbose:
        if passed:
            print("✅ Benchmark PASSED")
        else:
            print("❌ Benchmark FAILED")
            for issue in issues:
                print(f"  - {issue}")
    
    # Serialize results
    opt_serialized = _serialize_optimizer_result(opt_result)
    bench_serialized = (
        _serialize_benchmark_result(benchmark_result) 
        if benchmark_result else None
    )
    
    metadata = {
        'workload_size': workload.data_size,
        'workload_type': workload.expected_workload_type,
        'min_speedup_threshold': workload.min_speedup,
        'optimizer_time': opt_time
    }
    
    return PerformanceResult(
        workload_name=workload.name,
        optimizer_result=opt_serialized,
        benchmark_result=bench_serialized,
        passed=passed,
        regression_detected=regression_detected,
        issues=issues,
        metadata=metadata
    )


def run_performance_suite(
    workloads: Optional[List[WorkloadSpec]] = None,
    run_validation: bool = True,
    validate_max_items: int = 50,
    verbose: bool = False,
    save_results: bool = False,
    results_path: Optional[Path] = None
) -> Dict[str, PerformanceResult]:
    """
    Run the full performance benchmark suite.
    
    Args:
        workloads: List of workloads to run (default: all standard workloads)
        run_validation: Whether to run empirical validation (default: True)
        validate_max_items: Max items for validation (default: 50)
        verbose: Print progress information (default: False)
        save_results: Save results to JSON file (default: False)
        results_path: Path to save results (default: ./performance_results.json)
    
    Returns:
        Dictionary mapping workload names to PerformanceResult objects
        
    Example:
        >>> results = run_performance_suite(verbose=True, save_results=True)
        >>> passed = sum(1 for r in results.values() if r.passed)
        >>> print(f"Passed: {passed}/{len(results)} benchmarks")
    """
    if workloads is None:
        workloads = get_standard_workloads()
    
    if verbose:
        print("=" * 70)
        print("AMORSIZE PERFORMANCE BENCHMARK SUITE")
        print("=" * 70)
        print(f"Running {len(workloads)} workloads")
        print(f"Validation: {'enabled' if run_validation else 'disabled'}")
    
    results = {}
    
    for workload in workloads:
        result = run_performance_benchmark(
            workload,
            run_validation=run_validation,
            validate_max_items=validate_max_items,
            verbose=verbose
        )
        results[workload.name] = result
    
    # Summary
    if verbose:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        passed_count = sum(1 for r in results.values() if r.passed)
        failed_count = len(results) - passed_count
        regression_count = sum(1 for r in results.values() if r.regression_detected)
        
        print(f"Passed: {passed_count}/{len(results)}")
        print(f"Failed: {failed_count}/{len(results)}")
        print(f"Regressions detected: {regression_count}")
        
        if failed_count > 0:
            print("\nFailed benchmarks:")
            for name, result in results.items():
                if not result.passed:
                    print(f"  ❌ {name}")
                    for issue in result.issues:
                        print(f"      - {issue}")
    
    # Save results if requested
    if save_results:
        if results_path is None:
            results_path = Path("performance_results.json")
        
        # Convert results to dictionary format
        results_dict = {
            name: result.to_dict() 
            for name, result in results.items()
        }
        
        with open(results_path, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        if verbose:
            print(f"\nResults saved to: {results_path}")
    
    return results


def compare_performance_results(
    baseline_path: Path,
    current_path: Path,
    regression_threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Compare two performance benchmark results to detect regressions.
    
    Args:
        baseline_path: Path to baseline results JSON file
        current_path: Path to current results JSON file
        regression_threshold: Threshold for regression detection (default: 10%)
    
    Returns:
        Dictionary with comparison results and detected regressions
        
    Example:
        >>> comparison = compare_performance_results(
        ...     Path("baseline.json"),
        ...     Path("current.json")
        ... )
        >>> if comparison['regressions']:
        ...     print("Performance regressions detected!")
    """
    # Load results
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)
    
    with open(current_path, 'r') as f:
        current = json.load(f)
    
    comparison = {
        'regressions': [],
        'improvements': [],
        'unchanged': [],
        'missing_workloads': [],
        'new_workloads': []
    }
    
    # Compare workloads that exist in both
    for workload_name in baseline.keys():
        if workload_name not in current:
            comparison['missing_workloads'].append(workload_name)
            continue
        
        baseline_result = baseline[workload_name]
        current_result = current[workload_name]
        
        # Compare speedups if validation was run
        if (baseline_result['benchmark_result'] is not None and 
            current_result['benchmark_result'] is not None):
            
            baseline_speedup = baseline_result['benchmark_result']['actual_speedup']
            current_speedup = current_result['benchmark_result']['actual_speedup']
            
            speedup_change = (current_speedup - baseline_speedup) / baseline_speedup
            
            if speedup_change < -regression_threshold:
                # Performance regression
                comparison['regressions'].append({
                    'workload': workload_name,
                    'baseline_speedup': baseline_speedup,
                    'current_speedup': current_speedup,
                    'change_percent': speedup_change * 100
                })
            elif speedup_change > regression_threshold:
                # Performance improvement
                comparison['improvements'].append({
                    'workload': workload_name,
                    'baseline_speedup': baseline_speedup,
                    'current_speedup': current_speedup,
                    'change_percent': speedup_change * 100
                })
            else:
                # No significant change
                comparison['unchanged'].append(workload_name)
    
    # Find new workloads in current
    for workload_name in current.keys():
        if workload_name not in baseline:
            comparison['new_workloads'].append(workload_name)
    
    return comparison
