"""
Benchmark validation module for empirically verifying optimizer predictions.

This module provides tools to validate that optimizer recommendations are
accurate for specific system and workload combinations by running actual
benchmarks and comparing against predictions.
"""

import time
from typing import Any, Callable, List, Union, Iterator, Optional, Dict
from multiprocessing import Pool

from .optimizer import optimize, OptimizationResult


class BenchmarkResult:
    """
    Container for benchmark validation results.
    
    Attributes:
        optimization: Original optimization result being validated
        serial_time: Measured serial execution time (seconds)
        parallel_time: Measured parallel execution time (seconds)
        actual_speedup: Measured speedup (serial_time / parallel_time)
        predicted_speedup: Optimizer's predicted speedup
        accuracy_percent: Accuracy of prediction ((1 - |error|) * 100)
        error_percent: Prediction error percentage
        recommendations: List of insights based on validation
    """
    
    def __init__(
        self,
        optimization: OptimizationResult,
        serial_time: float,
        parallel_time: float,
        actual_speedup: float,
        predicted_speedup: float,
        accuracy_percent: float,
        error_percent: float,
        recommendations: List[str] = None
    ):
        self.optimization = optimization
        self.serial_time = serial_time
        self.parallel_time = parallel_time
        self.actual_speedup = actual_speedup
        self.predicted_speedup = predicted_speedup
        self.accuracy_percent = accuracy_percent
        self.error_percent = error_percent
        self.recommendations = recommendations or []
    
    def __repr__(self):
        return (f"BenchmarkResult(actual_speedup={self.actual_speedup:.2f}x, "
                f"predicted={self.predicted_speedup:.2f}x, "
                f"accuracy={self.accuracy_percent:.1f}%)")
    
    def __str__(self):
        result = "=== Benchmark Validation Results ===\n\n"
        result += f"Optimizer Recommendation: n_jobs={self.optimization.n_jobs}, "
        result += f"chunksize={self.optimization.chunksize}\n\n"
        
        result += "Performance Measurements:\n"
        result += f"  Serial execution time:   {self.serial_time:.4f}s\n"
        result += f"  Parallel execution time: {self.parallel_time:.4f}s\n"
        result += f"  Actual speedup:          {self.actual_speedup:.2f}x\n"
        result += f"  Predicted speedup:       {self.predicted_speedup:.2f}x\n\n"
        
        result += "Prediction Accuracy:\n"
        result += f"  Accuracy:                {self.accuracy_percent:.1f}%\n"
        result += f"  Error:                   {self.error_percent:+.1f}%\n\n"
        
        # Interpretation
        if self.accuracy_percent >= 90:
            result += "✅ Excellent prediction accuracy!\n"
        elif self.accuracy_percent >= 75:
            result += "✓ Good prediction accuracy.\n"
        elif self.accuracy_percent >= 60:
            result += "⚠️ Moderate prediction accuracy - system-specific factors may apply.\n"
        else:
            result += "❌ Low prediction accuracy - investigate system-specific factors.\n"
        
        if self.recommendations:
            result += "\nRecommendations:\n"
            for rec in self.recommendations:
                result += f"  • {rec}\n"
        
        return result
    
    def is_accurate(self, threshold: float = 75.0) -> bool:
        """
        Check if prediction accuracy meets threshold.
        
        Args:
            threshold: Minimum accuracy percentage (default: 75%)
        
        Returns:
            True if accuracy >= threshold
        """
        return self.accuracy_percent >= threshold


def validate_optimization(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    optimization: Optional[OptimizationResult] = None,
    max_items: Optional[int] = None,
    timeout: float = 60.0,
    verbose: bool = False
) -> BenchmarkResult:
    """
    Validate optimizer recommendations by running empirical benchmarks.
    
    This function runs both serial and parallel execution on actual data
    and compares the measured performance against the optimizer's predictions.
    This helps users verify that recommendations are accurate for their
    specific system and workload.
    
    Args:
        func: Function to benchmark (must accept single argument)
        data: Input data (list, generator, or iterator)
        optimization: Pre-computed optimization result (if None, will compute)
        max_items: Maximum items to benchmark (limits runtime for large datasets)
        timeout: Maximum time for each benchmark in seconds (default: 60s)
        verbose: Print progress information (default: False)
    
    Returns:
        BenchmarkResult with actual vs predicted performance comparison
    
    Raises:
        ValueError: If parameters are invalid
        TimeoutError: If benchmark exceeds timeout
    
    Example:
        >>> def expensive_func(x):
        ...     return sum(i**2 for i in range(x))
        >>> 
        >>> data = range(100, 1000)
        >>> result = validate_optimization(expensive_func, data, verbose=True)
        >>> print(result)
        >>> print(f"Accuracy: {result.accuracy_percent:.1f}%")
    
    Notes:
        - For very large datasets, use max_items to limit benchmark runtime
        - Serial execution is skipped if n_jobs=1 (already optimal)
        - Results include recommendations for improving accuracy
    """
    # Validate inputs
    if not callable(func):
        raise ValueError("func must be callable")
    if data is None:
        raise ValueError("data cannot be None")
    if timeout <= 0:
        raise ValueError(f"timeout must be positive, got {timeout}")
    
    # Convert data to list for benchmarking (need to iterate multiple times)
    if not isinstance(data, list):
        data = list(data)
    
    # Limit dataset size if requested
    if max_items is not None and len(data) > max_items:
        if verbose:
            print(f"Limiting benchmark to first {max_items} of {len(data)} items")
        data = data[:max_items]
    
    if len(data) == 0:
        raise ValueError("data cannot be empty for benchmarking")
    
    # Get or compute optimization
    if optimization is None:
        if verbose:
            print("Computing optimization...")
        optimization = optimize(func, data, verbose=verbose)
    
    if verbose:
        print(f"\nValidating optimization: n_jobs={optimization.n_jobs}, "
              f"chunksize={optimization.chunksize}")
        print(f"Predicted speedup: {optimization.estimated_speedup:.2f}x\n")
    
    recommendations = []
    
    # Benchmark serial execution
    if optimization.n_jobs == 1:
        # Already optimal for serial - no parallel comparison needed
        if verbose:
            print("Optimizer recommended serial execution (n_jobs=1)")
            print("Running single benchmark to verify...")
        
        start = time.perf_counter()
        try:
            results = [func(item) for item in data]
        except Exception as e:
            raise RuntimeError(f"Function execution failed during benchmark: {e}")
        end = time.perf_counter()
        serial_time = end - start
        
        # For serial execution, parallel_time equals serial_time
        parallel_time = serial_time
        actual_speedup = 1.0
        
        if verbose:
            print(f"Serial execution: {serial_time:.4f}s")
            print("✓ Serial execution confirmed as optimal")
        
        recommendations.append("Serial execution is optimal for this workload")
        if "too fast" in optimization.reason.lower():
            recommendations.append("Function execution time is very short - overhead dominates")
    
    else:
        # Benchmark serial execution
        if verbose:
            print("Benchmarking serial execution...")
        
        start = time.perf_counter()
        try:
            results_serial = [func(item) for item in data]
        except Exception as e:
            raise RuntimeError(f"Serial execution failed during benchmark: {e}")
        end = time.perf_counter()
        serial_time = end - start
        
        if verbose:
            print(f"Serial execution: {serial_time:.4f}s")
        
        # Check timeout
        if serial_time > timeout:
            raise TimeoutError(f"Serial execution exceeded timeout ({timeout}s)")
        
        # Benchmark parallel execution
        if verbose:
            print(f"Benchmarking parallel execution (n_jobs={optimization.n_jobs}, "
                  f"chunksize={optimization.chunksize})...")
        
        start = time.perf_counter()
        try:
            with Pool(processes=optimization.n_jobs) as pool:
                results_parallel = pool.map(
                    func,
                    optimization.data,  # Use reconstructed data from optimization
                    chunksize=optimization.chunksize
                )
        except Exception as e:
            raise RuntimeError(f"Parallel execution failed during benchmark: {e}")
        end = time.perf_counter()
        parallel_time = end - start
        
        if verbose:
            print(f"Parallel execution: {parallel_time:.4f}s")
        
        # Check timeout
        if parallel_time > timeout:
            raise TimeoutError(f"Parallel execution exceeded timeout ({timeout}s)")
        
        # Calculate actual speedup
        actual_speedup = serial_time / parallel_time if parallel_time > 0 else 1.0
        
        if verbose:
            print(f"Actual speedup: {actual_speedup:.2f}x\n")
        
        # Analyze results and generate recommendations
        if actual_speedup < 1.0:
            recommendations.append(
                "Parallel execution is slower than serial - overhead dominates benefit"
            )
            recommendations.append(
                "Consider increasing workload size or function complexity"
            )
        elif actual_speedup < 1.2:
            recommendations.append(
                "Marginal speedup - overhead nearly equals benefit"
            )
    
    # Calculate prediction accuracy
    predicted_speedup = optimization.estimated_speedup
    
    # Error as percentage of predicted value
    error = actual_speedup - predicted_speedup
    error_percent = (error / predicted_speedup) * 100 if predicted_speedup > 0 else 0
    
    # Accuracy as (1 - |normalized_error|) * 100
    # Normalized error is |error| / max(predicted, actual) to handle both over and under-estimation
    max_speedup = max(predicted_speedup, actual_speedup)
    normalized_error = abs(error) / max_speedup if max_speedup > 0 else 0
    accuracy_percent = (1.0 - normalized_error) * 100
    
    # Additional recommendations based on accuracy
    if accuracy_percent < 75:
        recommendations.append(
            "Significant deviation from prediction - system-specific factors detected"
        )
        if actual_speedup > predicted_speedup * 1.3:
            recommendations.append(
                "Actual speedup exceeds prediction - your system is more efficient than estimated"
            )
        elif actual_speedup < predicted_speedup * 0.7:
            recommendations.append(
                "Actual speedup below prediction - check for system contention or thermal throttling"
            )
    
    return BenchmarkResult(
        optimization=optimization,
        serial_time=serial_time,
        parallel_time=parallel_time,
        actual_speedup=actual_speedup,
        predicted_speedup=predicted_speedup,
        accuracy_percent=accuracy_percent,
        error_percent=error_percent,
        recommendations=recommendations
    )


def quick_validate(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 100,
    verbose: bool = False
) -> BenchmarkResult:
    """
    Quick validation using a small sample of data.
    
    This is a convenience function for fast validation without running
    benchmarks on large datasets. It samples the data and runs validation
    on the sample only.
    
    Args:
        func: Function to benchmark
        data: Input data
        sample_size: Number of items to sample for validation (default: 100)
        verbose: Print progress information
    
    Returns:
        BenchmarkResult based on sampled data
    
    Example:
        >>> def process(x):
        ...     return x ** 2
        >>> 
        >>> data = range(10000)
        >>> result = quick_validate(process, data, sample_size=100)
        >>> print(f"Quick check: {result.accuracy_percent:.1f}% accurate")
    
    Notes:
        - Much faster than full validation
        - Less accurate for heterogeneous workloads
        - Good for quick confidence checks during development
    """
    # Convert to list and sample
    if not isinstance(data, list):
        data = list(data)
    
    if len(data) > sample_size:
        # Sample evenly distributed items
        step = len(data) // sample_size
        sampled_data = data[::step][:sample_size]
    else:
        sampled_data = data
    
    if verbose:
        print(f"Quick validation using {len(sampled_data)} sample items")
    
    return validate_optimization(
        func,
        sampled_data,
        optimization=None,
        verbose=verbose
    )
