"""
Comparison mode for analyzing different parallelization strategies.

This module provides tools to compare multiple optimization strategies
(different n_jobs, chunksizes, or execution methods) side-by-side to help
users make informed decisions about parallelization parameters.
"""

import time
from typing import Any, Callable, List, Union, Iterator, Optional, Dict, Tuple
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor

from .optimizer import optimize, OptimizationResult
from .benchmark import BenchmarkResult, validate_optimization


class ComparisonConfig:
    """
    Configuration for a single strategy to compare.
    
    Attributes:
        name: Human-readable name for this configuration
        n_jobs: Number of workers (1 for serial)
        chunksize: Chunk size for batching
        executor_type: "process", "thread", or "serial"
    """
    
    def __init__(
        self,
        name: str,
        n_jobs: int = 1,
        chunksize: int = 1,
        executor_type: str = "process"
    ):
        if n_jobs < 1:
            raise ValueError(f"n_jobs must be >= 1, got {n_jobs}")
        if chunksize < 1:
            raise ValueError(f"chunksize must be >= 1, got {chunksize}")
        if executor_type not in ["process", "thread", "serial"]:
            raise ValueError(f"executor_type must be 'process', 'thread', or 'serial', got '{executor_type}'")
        
        self.name = name
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.executor_type = executor_type
    
    def __repr__(self):
        if self.n_jobs == 1 or self.executor_type == "serial":
            return f"ComparisonConfig('{self.name}', serial)"
        return f"ComparisonConfig('{self.name}', n_jobs={self.n_jobs}, chunksize={self.chunksize}, {self.executor_type})"
    
    def __str__(self):
        if self.n_jobs == 1 or self.executor_type == "serial":
            return f"{self.name}: Serial execution"
        return f"{self.name}: {self.n_jobs} {self.executor_type}s, chunksize={self.chunksize}"


class ComparisonResult:
    """
    Result of comparing multiple parallelization strategies.
    
    Attributes:
        configs: List of configurations that were compared
        execution_times: Execution times for each config (seconds)
        speedups: Speedup relative to serial (first config) for each config
        best_config_index: Index of fastest configuration
        best_config: Fastest configuration
        best_time: Execution time of best configuration
        recommendations: List of insights from comparison
    """
    
    def __init__(
        self,
        configs: List[ComparisonConfig],
        execution_times: List[float],
        speedups: List[float],
        best_config_index: int,
        recommendations: List[str] = None
    ):
        self.configs = configs
        self.execution_times = execution_times
        self.speedups = speedups
        self.best_config_index = best_config_index
        self.best_config = configs[best_config_index]
        self.best_time = execution_times[best_config_index]
        self.recommendations = recommendations or []
    
    def __repr__(self):
        return (f"ComparisonResult(best='{self.best_config.name}', "
                f"time={self.best_time:.4f}s, speedup={self.speedups[self.best_config_index]:.2f}x)")
    
    def __str__(self):
        result = "=== Strategy Comparison Results ===\n\n"
        
        # Find baseline (serial or first config)
        baseline_time = self.execution_times[0]
        
        # Table header
        result += f"{'Strategy':<30} {'Time (s)':<12} {'Speedup':<10} {'Status':<15}\n"
        result += "-" * 70 + "\n"
        
        # Add each configuration
        for i, (config, exec_time, speedup) in enumerate(zip(self.configs, self.execution_times, self.speedups)):
            # Status indicator
            if i == self.best_config_index:
                status = "⭐ FASTEST"
            elif speedup < 1.0:
                status = "⚠️  Slower"
            elif speedup < 1.1:
                status = "~ Similar"
            else:
                status = "✓ Faster"
            
            result += f"{config.name:<30} {exec_time:<12.4f} {speedup:<10.2f}x {status:<15}\n"
        
        result += "\n"
        result += f"Best Strategy: {self.best_config.name}\n"
        result += f"Best Time: {self.best_time:.4f}s\n"
        result += f"Best Speedup: {self.speedups[self.best_config_index]:.2f}x\n"
        
        if self.recommendations:
            result += "\nRecommendations:\n"
            for rec in self.recommendations:
                result += f"  • {rec}\n"
        
        return result
    
    def get_sorted_configs(self) -> List[Tuple[ComparisonConfig, float, float]]:
        """
        Get configurations sorted by execution time (fastest first).
        
        Returns:
            List of tuples: (config, time, speedup) sorted by time
        """
        combined = list(zip(self.configs, self.execution_times, self.speedups))
        return sorted(combined, key=lambda x: x[1])


def compare_strategies(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    configs: List[ComparisonConfig],
    max_items: Optional[int] = None,
    timeout: float = 120.0,
    verbose: bool = False
) -> ComparisonResult:
    """
    Compare multiple parallelization strategies by benchmarking each.
    
    This function runs actual benchmarks for each configuration and compares
    their performance. This helps users understand trade-offs between different
    parallelization approaches and choose the best one for their workload.
    
    Args:
        func: Function to benchmark (must accept single argument)
        data: Input data (list, generator, or iterator)
        configs: List of configurations to compare
        max_items: Maximum items to benchmark (limits runtime for large datasets)
        timeout: Maximum time for each benchmark in seconds (default: 120s)
        verbose: Print progress information (default: False)
    
    Returns:
        ComparisonResult with execution times and speedups for each config
    
    Raises:
        ValueError: If parameters are invalid
        TimeoutError: If any benchmark exceeds timeout
    
    Example:
        >>> from amorsize import compare_strategies, ComparisonConfig
        >>> 
        >>> def expensive_func(x):
        ...     return sum(i**2 for i in range(x))
        >>> 
        >>> data = range(100, 1000)
        >>> 
        >>> configs = [
        ...     ComparisonConfig("Serial", n_jobs=1),
        ...     ComparisonConfig("2 Workers", n_jobs=2, chunksize=50),
        ...     ComparisonConfig("4 Workers", n_jobs=4, chunksize=25),
        ...     ComparisonConfig("8 Workers", n_jobs=8, chunksize=13),
        ... ]
        >>> 
        >>> result = compare_strategies(expensive_func, data, configs, verbose=True)
        >>> print(result)
    
    Notes:
        - First config is used as baseline for speedup calculation
        - Configs are run in order provided
        - Use max_items to limit runtime for large datasets
        - Timeout applies to each individual benchmark
    """
    # Validate inputs
    if not callable(func):
        raise ValueError("func must be callable")
    if data is None:
        raise ValueError("data cannot be None")
    if not configs or len(configs) == 0:
        raise ValueError("configs cannot be empty")
    if timeout <= 0:
        raise ValueError(f"timeout must be positive, got {timeout}")
    
    # Convert data to list for benchmarking (need to iterate multiple times)
    if not isinstance(data, list):
        data = list(data)
    
    # Limit dataset size if requested
    if max_items is not None and len(data) > max_items:
        if verbose:
            print(f"Limiting benchmark to first {max_items} of {len(data)} items\n")
        data = data[:max_items]
    
    if len(data) == 0:
        raise ValueError("data cannot be empty for benchmarking")
    
    if verbose:
        print(f"Comparing {len(configs)} strategies on {len(data)} items\n")
    
    execution_times = []
    recommendations = []
    
    # Benchmark each configuration
    for i, config in enumerate(configs):
        if verbose:
            print(f"[{i+1}/{len(configs)}] Testing: {config}")
        
        start = time.perf_counter()
        
        try:
            if config.n_jobs == 1 or config.executor_type == "serial":
                # Serial execution
                for item in data:
                    _ = func(item)
            
            elif config.executor_type == "process":
                # Multiprocessing execution
                with Pool(processes=config.n_jobs) as pool:
                    _ = pool.map(func, data, chunksize=config.chunksize)
            
            elif config.executor_type == "thread":
                # Threading execution
                with ThreadPoolExecutor(max_workers=config.n_jobs) as executor:
                    # ThreadPoolExecutor.map doesn't have chunksize, but we can simulate
                    _ = list(executor.map(func, data))
            
            else:
                raise ValueError(f"Unknown executor_type: {config.executor_type}")
        
        except Exception as e:
            raise RuntimeError(f"Execution failed for config '{config.name}': {e}")
        
        end = time.perf_counter()
        exec_time = end - start
        execution_times.append(exec_time)
        
        if verbose:
            print(f"    Execution time: {exec_time:.4f}s")
        
        # Check timeout
        if exec_time > timeout:
            raise TimeoutError(f"Config '{config.name}' exceeded timeout ({timeout}s)")
    
    if verbose:
        print()
    
    # Calculate speedups relative to first (baseline) config
    baseline_time = execution_times[0]
    speedups = [baseline_time / t if t > 0 else 1.0 for t in execution_times]
    
    # Find best configuration
    best_idx = execution_times.index(min(execution_times))
    
    # Generate recommendations
    best_config = configs[best_idx]
    
    if best_idx == 0:
        recommendations.append("Serial execution is fastest - parallelization adds overhead without benefit")
        recommendations.append("Consider increasing workload size or function complexity")
    else:
        recommendations.append(f"Best strategy uses {best_config.n_jobs} workers with chunksize {best_config.chunksize}")
        
        # Check if speedup is close to linear
        if best_config.n_jobs > 1:
            efficiency = speedups[best_idx] / best_config.n_jobs
            if efficiency > 0.85:
                recommendations.append(f"Excellent parallel efficiency ({efficiency*100:.1f}%) - near-linear scaling")
            elif efficiency < 0.5:
                recommendations.append(f"Low parallel efficiency ({efficiency*100:.1f}%) - overhead is significant")
        
        # Check if any config is much worse
        for i, (config, speedup) in enumerate(zip(configs, speedups)):
            if i != best_idx and speedup < 0.8:
                recommendations.append(f"Config '{config.name}' is significantly slower - avoid this configuration")
    
    # Check for threading vs multiprocessing comparison
    has_thread = any(c.executor_type == "thread" for c in configs)
    has_process = any(c.executor_type == "process" for c in configs)
    
    if has_thread and has_process:
        thread_times = [t for c, t in zip(configs, execution_times) if c.executor_type == "thread"]
        process_times = [t for c, t in zip(configs, execution_times) if c.executor_type == "process"]
        
        if thread_times and process_times:
            avg_thread = sum(thread_times) / len(thread_times)
            avg_process = sum(process_times) / len(process_times)
            
            if avg_thread < avg_process * 0.9:
                recommendations.append("Threading is significantly faster - workload may be I/O-bound")
            elif avg_process < avg_thread * 0.9:
                recommendations.append("Multiprocessing is significantly faster - workload is CPU-bound")
    
    return ComparisonResult(
        configs=configs,
        execution_times=execution_times,
        speedups=speedups,
        best_config_index=best_idx,
        recommendations=recommendations
    )


def compare_with_optimizer(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    additional_configs: Optional[List[ComparisonConfig]] = None,
    max_items: Optional[int] = None,
    timeout: float = 120.0,
    verbose: bool = False
) -> Tuple[ComparisonResult, OptimizationResult]:
    """
    Compare optimizer recommendation against alternative strategies.
    
    This convenience function:
    1. Gets optimizer recommendation
    2. Benchmarks optimizer recommendation + additional configs
    3. Returns comparison results and original optimization
    
    Args:
        func: Function to benchmark
        data: Input data
        additional_configs: Additional configurations to compare (optional)
        max_items: Maximum items to benchmark
        timeout: Maximum time per benchmark
        verbose: Print progress information
    
    Returns:
        Tuple of (ComparisonResult, OptimizationResult)
    
    Example:
        >>> result, opt = compare_with_optimizer(func, data, verbose=True)
        >>> print(f"Optimizer recommended: {opt.n_jobs} workers")
        >>> print(f"Best strategy: {result.best_config.name}")
    """
    if verbose:
        print("Computing optimizer recommendation...\n")
    
    # Get optimizer recommendation
    optimization = optimize(func, data, verbose=verbose)
    
    if verbose:
        print(f"\nOptimizer recommends: n_jobs={optimization.n_jobs}, "
              f"chunksize={optimization.chunksize}, executor={optimization.executor_type}")
        print(f"Predicted speedup: {optimization.estimated_speedup:.2f}x\n")
    
    # Build list of configs to compare
    configs = []
    
    # Add serial baseline
    configs.append(ComparisonConfig("Serial", n_jobs=1))
    
    # Add optimizer recommendation
    configs.append(
        ComparisonConfig(
            "Optimizer",
            n_jobs=optimization.n_jobs,
            chunksize=optimization.chunksize,
            executor_type=optimization.executor_type
        )
    )
    
    # Add any additional configs
    if additional_configs:
        configs.extend(additional_configs)
    
    # Run comparison
    comparison = compare_strategies(
        func, data, configs,
        max_items=max_items,
        timeout=timeout,
        verbose=verbose
    )
    
    return comparison, optimization
