"""
Auto-tuning module for finding optimal parallelization parameters.

This module provides automated parameter search to find the best n_jobs and
chunksize configuration for a given function and dataset through empirical
benchmarking.
"""

import time
from typing import Any, Callable, List, Union, Iterator, Optional, Tuple, Dict
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
import itertools
import warnings

from .optimizer import optimize, OptimizationResult
from .system_info import get_physical_cores

# Check for scikit-optimize availability
try:
    from skopt import gp_minimize
    from skopt.space import Integer
    from skopt.utils import use_named_args
    HAS_SKOPT = True
except ImportError:
    HAS_SKOPT = False


class TuningResult:
    """
    Container for auto-tuning results.
    
    Attributes:
        best_n_jobs: Optimal number of workers found
        best_chunksize: Optimal chunk size found
        best_time: Execution time for best configuration (seconds)
        best_speedup: Speedup achieved by best configuration
        serial_time: Baseline serial execution time (seconds)
        configurations_tested: Number of configurations benchmarked
        all_results: Dict mapping (n_jobs, chunksize) -> execution_time
        optimization_hint: Initial optimizer recommendation
        search_strategy: Strategy used for search ("grid", "adaptive", etc.)
        executor_type: Type of executor used ("process" or "thread")
    """
    
    def __init__(
        self,
        best_n_jobs: int,
        best_chunksize: int,
        best_time: float,
        best_speedup: float,
        serial_time: float,
        configurations_tested: int,
        all_results: Dict[Tuple[int, int], float],
        optimization_hint: Optional[OptimizationResult] = None,
        search_strategy: str = "grid",
        executor_type: str = "process"
    ):
        self.best_n_jobs = best_n_jobs
        self.best_chunksize = best_chunksize
        self.best_time = best_time
        self.best_speedup = best_speedup
        self.serial_time = serial_time
        self.configurations_tested = configurations_tested
        self.all_results = all_results
        self.optimization_hint = optimization_hint
        self.search_strategy = search_strategy
        self.executor_type = executor_type
    
    def __repr__(self):
        return (f"TuningResult(best_n_jobs={self.best_n_jobs}, "
                f"best_chunksize={self.best_chunksize}, "
                f"best_speedup={self.best_speedup:.2f}x, "
                f"tested={self.configurations_tested})")
    
    def __str__(self):
        result = "=== Auto-Tuning Results ===\n\n"
        result += f"Search Strategy: {self.search_strategy}\n"
        result += f"Executor Type: {self.executor_type}\n"
        result += f"Configurations Tested: {self.configurations_tested}\n\n"
        
        result += "Performance:\n"
        result += f"  Serial execution time:   {self.serial_time:.4f}s\n"
        result += f"  Best parallel time:      {self.best_time:.4f}s\n"
        result += f"  Best speedup:            {self.best_speedup:.2f}x\n\n"
        
        result += "Optimal Configuration:\n"
        result += f"  n_jobs:     {self.best_n_jobs}\n"
        result += f"  chunksize:  {self.best_chunksize}\n\n"
        
        if self.optimization_hint:
            result += "Comparison with Optimizer Hint:\n"
            result += f"  Optimizer suggested: n_jobs={self.optimization_hint.n_jobs}, "
            result += f"chunksize={self.optimization_hint.chunksize}\n"
            
            hint_match = (self.best_n_jobs == self.optimization_hint.n_jobs and 
                         self.best_chunksize == self.optimization_hint.chunksize)
            if hint_match:
                result += "  ✅ Auto-tuning confirmed optimizer recommendation!\n"
            else:
                result += f"  ℹ️ Auto-tuning found different optimal configuration\n"
        
        # Show top 3 configurations
        if len(self.all_results) > 1:
            result += "\nTop Configurations:\n"
            sorted_results = sorted(self.all_results.items(), key=lambda x: x[1])
            for i, ((n_jobs, chunksize), exec_time) in enumerate(sorted_results[:3], 1):
                speedup = self.serial_time / exec_time if exec_time > 0 else 0
                result += f"  {i}. n_jobs={n_jobs:2d}, chunksize={chunksize:4d} -> "
                result += f"{exec_time:.4f}s ({speedup:.2f}x)\n"
        
        return result
    
    def get_top_configurations(self, n: int = 5) -> List[Tuple[int, int, float, float]]:
        """
        Get the top N configurations by execution time.
        
        Args:
            n: Number of top configurations to return
        
        Returns:
            List of (n_jobs, chunksize, time, speedup) tuples
        """
        sorted_results = sorted(self.all_results.items(), key=lambda x: x[1])
        return [
            (n_jobs, chunksize, exec_time, self.serial_time / exec_time if exec_time > 0 else 0)
            for (n_jobs, chunksize), exec_time in sorted_results[:n]
        ]
    
    def save_config(
        self,
        filepath: str,
        function_name: Optional[str] = None,
        notes: Optional[str] = None,
        overwrite: bool = False
    ) -> None:
        """
        Save the best tuning result as a reusable configuration file.
        
        Args:
            filepath: Path to save configuration file
            function_name: Optional name of the function
            notes: Optional notes about this configuration
            overwrite: If True, overwrite existing file
        
        Examples:
            >>> result = tune_parameters(my_func, data)
            >>> result.save_config('my_tuned_config.json', function_name='my_func')
        """
        from .config import save_config, ConfigData
        
        # Estimate data size from serial time and best time
        # This is approximate since we don't store the exact data size
        data_size = None  # Unknown from tuning alone
        
        # Calculate average execution time per item (approximate)
        avg_execution_time = None
        if data_size and data_size > 0:
            avg_execution_time = self.serial_time / data_size
        
        config = ConfigData(
            n_jobs=self.best_n_jobs,
            chunksize=self.best_chunksize,
            executor_type=self.executor_type,
            estimated_speedup=self.best_speedup,
            function_name=function_name,
            data_size=data_size,
            avg_execution_time=avg_execution_time,
            notes=notes,
            source="tune"
        )
        
        save_config(config, filepath, overwrite=overwrite)


def _benchmark_configuration(
    func: Callable,
    data: Union[List, range],
    n_jobs: int,
    chunksize: int,
    executor_type: str = "process",
    timeout: Optional[float] = None
) -> float:
    """
    Benchmark a specific configuration.
    
    Args:
        func: Function to benchmark
        data: Input data
        n_jobs: Number of workers
        chunksize: Chunk size
        executor_type: "process" or "thread"
        timeout: Maximum time to wait for execution
    
    Returns:
        Execution time in seconds, or float('inf') on error
    """
    try:
        start = time.perf_counter()
        
        if executor_type == "thread":
            with ThreadPoolExecutor(max_workers=n_jobs) as executor:
                # ThreadPoolExecutor.map doesn't have chunksize parameter
                # So we batch manually
                list(executor.map(func, data))
        else:
            with Pool(processes=n_jobs) as pool:
                list(pool.map(func, data, chunksize=chunksize))
        
        end = time.perf_counter()
        return end - start
    
    except (Exception, KeyboardInterrupt) as e:
        # Return infinity on error so this config is never selected
        return float('inf')


def tune_parameters(
    func: Callable,
    data: Union[List, range, Iterator],
    n_jobs_range: Optional[List[int]] = None,
    chunksize_range: Optional[List[int]] = None,
    use_optimizer_hint: bool = True,
    verbose: bool = False,
    timeout_per_config: Optional[float] = None,
    prefer_threads_for_io: bool = False
) -> TuningResult:
    """
    Automatically find optimal n_jobs and chunksize through grid search.
    
    This function benchmarks multiple parameter combinations to empirically
    determine the optimal configuration for your specific function and data.
    
    Args:
        func: Function to optimize (must accept single argument)
        data: Input data (list, range, or iterator)
        n_jobs_range: List of n_jobs values to test. If None, tests 1 to physical_cores
        chunksize_range: List of chunksize values to test. If None, uses smart defaults
        use_optimizer_hint: If True, includes optimizer recommendation in search space
        verbose: If True, prints progress during search
        timeout_per_config: Maximum seconds per configuration (None = no limit)
        prefer_threads_for_io: If True, uses ThreadPoolExecutor instead of multiprocessing.Pool
    
    Returns:
        TuningResult with optimal parameters and benchmark data
    
    Examples:
        >>> def expensive_func(x):
        ...     return sum(i**2 for i in range(x))
        >>> data = range(100, 500)
        >>> result = tune_parameters(expensive_func, data, verbose=True)
        >>> print(f"Optimal: n_jobs={result.best_n_jobs}, chunksize={result.best_chunksize}")
        
        >>> # Custom search space
        >>> result = tune_parameters(
        ...     expensive_func, data,
        ...     n_jobs_range=[2, 4, 8],
        ...     chunksize_range=[10, 50, 100]
        ... )
    """
    # Convert iterator to list if needed
    if hasattr(data, '__iter__') and not isinstance(data, (list, range)):
        data = list(data)
    
    data_list = list(data)
    n_items = len(data_list)
    
    if n_items == 0:
        raise ValueError("Cannot tune on empty dataset")
    
    # Determine executor type
    executor_type = "thread" if prefer_threads_for_io else "process"
    
    # Get optimizer hint if requested
    optimization_hint = None
    if use_optimizer_hint:
        try:
            optimization_hint = optimize(
                func, data_list,
                verbose=False,
                prefer_threads_for_io=prefer_threads_for_io
            )
            if verbose:
                print(f"Optimizer hint: n_jobs={optimization_hint.n_jobs}, "
                      f"chunksize={optimization_hint.chunksize}")
        except Exception as e:
            if verbose:
                print(f"Warning: Could not get optimizer hint: {e}")
    
    # Determine search space for n_jobs
    if n_jobs_range is None:
        physical_cores = get_physical_cores()
        # Test: 1 (serial), physical_cores/2, physical_cores, and optimizer hint
        n_jobs_range = [1, max(1, physical_cores // 2), physical_cores]
        if optimization_hint and optimization_hint.n_jobs not in n_jobs_range:
            n_jobs_range.append(optimization_hint.n_jobs)
        n_jobs_range = sorted(set(n_jobs_range))
    
    # Determine search space for chunksize
    if chunksize_range is None:
        # Smart defaults based on data size
        if n_items < 10:
            chunksize_range = [1]
        elif n_items < 100:
            chunksize_range = [1, max(1, n_items // 10), max(1, n_items // 4)]
        else:
            # Test various chunk sizes
            chunksize_range = [
                1,
                max(1, n_items // 100),
                max(1, n_items // 50),
                max(1, n_items // 20),
                max(1, n_items // 10)
            ]
        
        # Add optimizer hint
        if optimization_hint and optimization_hint.chunksize not in chunksize_range:
            chunksize_range.append(optimization_hint.chunksize)
        
        chunksize_range = sorted(set(chunksize_range))
    
    if verbose:
        print(f"\n=== Auto-Tuning Configuration ===")
        print(f"Function: {func.__name__}")
        print(f"Data items: {n_items}")
        print(f"Executor: {executor_type}")
        print(f"Testing n_jobs: {n_jobs_range}")
        print(f"Testing chunksizes: {chunksize_range}")
        print(f"Total configurations: {len(n_jobs_range) * len(chunksize_range) + 1}")
        print(f"\nStarting benchmark...\n")
    
    # Benchmark serial execution
    if verbose:
        print("Benchmarking serial execution...")
    
    serial_start = time.perf_counter()
    try:
        list(map(func, data_list))
    except Exception as e:
        raise RuntimeError(f"Serial execution failed: {e}")
    serial_end = time.perf_counter()
    serial_time = serial_end - serial_start
    
    if verbose:
        print(f"  Serial time: {serial_time:.4f}s\n")
    
    # Grid search over all configurations
    all_results: Dict[Tuple[int, int], float] = {}
    best_time = float('inf')
    best_n_jobs = n_jobs_range[0] if n_jobs_range else 1
    best_chunksize = chunksize_range[0] if chunksize_range else 1
    
    total_configs = len(n_jobs_range) * len(chunksize_range)
    current_config = 0
    
    for n_jobs in n_jobs_range:
        for chunksize in chunksize_range:
            current_config += 1
            
            if verbose:
                print(f"[{current_config}/{total_configs}] Testing n_jobs={n_jobs}, "
                      f"chunksize={chunksize}...", end=" ")
            
            exec_time = _benchmark_configuration(
                func, data_list, n_jobs, chunksize,
                executor_type=executor_type,
                timeout=timeout_per_config
            )
            
            all_results[(n_jobs, chunksize)] = exec_time
            
            if exec_time < best_time:
                best_time = exec_time
                best_n_jobs = n_jobs
                best_chunksize = chunksize
                if verbose:
                    speedup = serial_time / exec_time if exec_time > 0 else 0
                    print(f"{exec_time:.4f}s ({speedup:.2f}x) ⭐ NEW BEST")
            else:
                if verbose:
                    speedup = serial_time / exec_time if exec_time > 0 and exec_time != float('inf') else 0
                    print(f"{exec_time:.4f}s ({speedup:.2f}x)")
    
    # If serial is still faster than any parallel config, use serial
    if serial_time < best_time:
        best_time = serial_time
        best_n_jobs = 1
        best_chunksize = 1
    
    best_speedup = serial_time / best_time if best_time > 0 else 0
    
    if verbose:
        print(f"\n=== Tuning Complete ===")
        print(f"Best configuration: n_jobs={best_n_jobs}, chunksize={best_chunksize}")
        print(f"Best time: {best_time:.4f}s ({best_speedup:.2f}x speedup)\n")
    
    return TuningResult(
        best_n_jobs=best_n_jobs,
        best_chunksize=best_chunksize,
        best_time=best_time,
        best_speedup=best_speedup,
        serial_time=serial_time,
        configurations_tested=len(all_results) + 1,  # +1 for serial
        all_results=all_results,
        optimization_hint=optimization_hint,
        search_strategy="grid",
        executor_type=executor_type
    )


def quick_tune(
    func: Callable,
    data: Union[List, range, Iterator],
    verbose: bool = False,
    prefer_threads_for_io: bool = False
) -> TuningResult:
    """
    Quick auto-tuning using a minimal search space.
    
    This is a faster alternative to tune_parameters() that tests fewer
    configurations, focusing on the most likely optimal values.
    
    Args:
        func: Function to optimize
        data: Input data
        verbose: If True, prints progress
        prefer_threads_for_io: If True, uses ThreadPoolExecutor
    
    Returns:
        TuningResult with optimal parameters
    
    Examples:
        >>> result = quick_tune(expensive_func, data, verbose=True)
        >>> print(f"Optimal: n_jobs={result.best_n_jobs}")
    """
    # Convert to list if needed
    if hasattr(data, '__iter__') and not isinstance(data, (list, range)):
        data = list(data)
    
    data_list = list(data)
    n_items = len(data_list)
    
    physical_cores = get_physical_cores()
    
    # Minimal search space: serial, half cores, full cores
    n_jobs_range = [1, max(1, physical_cores // 2), physical_cores]
    
    # Minimal chunksize space
    if n_items < 20:
        chunksize_range = [1]
    else:
        chunksize_range = [1, max(1, n_items // 20), max(1, n_items // 10)]
    
    return tune_parameters(
        func, data_list,
        n_jobs_range=n_jobs_range,
        chunksize_range=chunksize_range,
        use_optimizer_hint=True,
        verbose=verbose,
        prefer_threads_for_io=prefer_threads_for_io
    )


def bayesian_tune_parameters(
    func: Callable,
    data: Union[List, range, Iterator],
    n_iterations: int = 20,
    n_jobs_min: int = 1,
    n_jobs_max: Optional[int] = None,
    chunksize_min: int = 1,
    chunksize_max: Optional[int] = None,
    use_optimizer_hint: bool = True,
    verbose: bool = False,
    timeout_per_config: Optional[float] = None,
    prefer_threads_for_io: bool = False,
    random_state: Optional[int] = None
) -> TuningResult:
    """
    Automatically find optimal n_jobs and chunksize using Bayesian Optimization.
    
    This function uses Gaussian Process-based Bayesian Optimization to intelligently
    explore the parameter space and find optimal configurations with fewer benchmarks
    than grid search. This is especially useful when benchmarking is expensive.
    
    Bayesian optimization builds a probabilistic model (surrogate) of the objective
    function and uses an acquisition function to decide which configuration to try
    next, balancing exploration and exploitation.
    
    Requires:
        scikit-optimize (skopt) - Install with: pip install scikit-optimize
    
    Args:
        func: Function to optimize (must accept single argument)
        data: Input data (list, range, or iterator)
        n_iterations: Number of configurations to benchmark (default: 20)
                     More iterations = better results but longer runtime
        n_jobs_min: Minimum number of workers to consider (default: 1)
        n_jobs_max: Maximum number of workers to consider (default: physical_cores)
        chunksize_min: Minimum chunk size to consider (default: 1)
        chunksize_max: Maximum chunk size to consider (default: data_size // 2)
        use_optimizer_hint: If True, starts search near optimizer recommendation
        verbose: If True, prints progress during search
        timeout_per_config: Maximum seconds per configuration (None = no limit)
        prefer_threads_for_io: If True, uses ThreadPoolExecutor instead of multiprocessing.Pool
        random_state: Random seed for reproducibility (default: None)
    
    Returns:
        TuningResult with optimal parameters and benchmark data
    
    Examples:
        >>> def expensive_func(x):
        ...     return sum(i**2 for i in range(x))
        >>> data = range(100, 500)
        >>> 
        >>> # Find optimal configuration with 30 intelligent trials
        >>> result = bayesian_tune_parameters(expensive_func, data, n_iterations=30, verbose=True)
        >>> print(f"Optimal: n_jobs={result.best_n_jobs}, chunksize={result.best_chunksize}")
        >>> print(f"Speedup: {result.best_speedup:.2f}x")
        
        >>> # Custom search bounds
        >>> result = bayesian_tune_parameters(
        ...     expensive_func, data,
        ...     n_jobs_min=2, n_jobs_max=8,
        ...     chunksize_min=5, chunksize_max=100,
        ...     n_iterations=25
        ... )
    
    Note:
        Falls back to grid search if scikit-optimize is not installed.
        For quick results, use n_iterations=15-20. For thorough search, use 30-50.
    """
    # Check for scikit-optimize
    if not HAS_SKOPT:
        warnings.warn(
            "scikit-optimize not available. Falling back to grid search. "
            "Install with: pip install scikit-optimize",
            RuntimeWarning
        )
        # Fall back to grid search with reasonable defaults
        physical_cores = get_physical_cores()
        n_jobs_range = [1, max(1, physical_cores // 2), physical_cores]
        
        data_list = list(data) if hasattr(data, '__iter__') and not isinstance(data, (list, range)) else data
        n_items = len(list(data_list))
        chunksize_range = [1, max(1, n_items // 20), max(1, n_items // 10)]
        
        return tune_parameters(
            func, data,
            n_jobs_range=n_jobs_range,
            chunksize_range=chunksize_range,
            use_optimizer_hint=use_optimizer_hint,
            verbose=verbose,
            timeout_per_config=timeout_per_config,
            prefer_threads_for_io=prefer_threads_for_io
        )
    
    # Convert iterator to list if needed
    if hasattr(data, '__iter__') and not isinstance(data, (list, range)):
        data = list(data)
    
    data_list = list(data)
    n_items = len(data_list)
    
    if n_items == 0:
        raise ValueError("Cannot tune on empty dataset")
    
    if n_iterations < 5:
        raise ValueError("n_iterations must be at least 5 for Bayesian optimization")
    
    # Determine executor type
    executor_type = "thread" if prefer_threads_for_io else "process"
    
    # Set default bounds
    if n_jobs_max is None:
        n_jobs_max = get_physical_cores()
    
    if chunksize_max is None:
        chunksize_max = max(1, n_items // 2)
    
    # Validate bounds
    if n_jobs_min < 1:
        raise ValueError("n_jobs_min must be at least 1")
    if n_jobs_max < n_jobs_min:
        raise ValueError("n_jobs_max must be >= n_jobs_min")
    if chunksize_min < 1:
        raise ValueError("chunksize_min must be at least 1")
    if chunksize_max < chunksize_min:
        raise ValueError("chunksize_max must be >= chunksize_min")
    
    # Get optimizer hint if requested
    optimization_hint = None
    initial_x = None
    if use_optimizer_hint:
        try:
            optimization_hint = optimize(
                func, data_list,
                verbose=False,
                prefer_threads_for_io=prefer_threads_for_io
            )
            if verbose:
                print(f"Optimizer hint: n_jobs={optimization_hint.n_jobs}, "
                      f"chunksize={optimization_hint.chunksize}")
            
            # Use optimizer hint as initial point (if within bounds)
            hint_n_jobs = max(n_jobs_min, min(n_jobs_max, optimization_hint.n_jobs))
            hint_chunksize = max(chunksize_min, min(chunksize_max, optimization_hint.chunksize))
            initial_x = [hint_n_jobs, hint_chunksize]
        except Exception as e:
            if verbose:
                print(f"Warning: Could not get optimizer hint: {e}")
    
    if verbose:
        print(f"\n=== Bayesian Optimization Configuration ===")
        print(f"Function: {func.__name__}")
        print(f"Data items: {n_items}")
        print(f"Executor: {executor_type}")
        print(f"Search space: n_jobs=[{n_jobs_min}, {n_jobs_max}], chunksize=[{chunksize_min}, {chunksize_max}]")
        print(f"Iterations: {n_iterations}")
        print(f"\nStarting optimization...\n")
    
    # Check if search space is too small for Bayesian optimization
    # If n_jobs range is 1 or chunksize range is 1, fall back to grid search
    if n_jobs_max == n_jobs_min or chunksize_max == chunksize_min:
        if verbose:
            print("Search space too small for Bayesian optimization. Using grid search...")
        
        # Fall back to grid search for tiny search spaces
        n_jobs_range = [n_jobs_min, n_jobs_max] if n_jobs_max != n_jobs_min else [n_jobs_min]
        chunksize_range = [chunksize_min, chunksize_max] if chunksize_max != chunksize_min else [chunksize_min]
        
        return tune_parameters(
            func, data_list,
            n_jobs_range=n_jobs_range,
            chunksize_range=chunksize_range,
            use_optimizer_hint=use_optimizer_hint,
            verbose=verbose,
            timeout_per_config=timeout_per_config,
            prefer_threads_for_io=prefer_threads_for_io
        )
    
    # Benchmark serial execution first
    if verbose:
        print("Benchmarking serial execution...")
    
    serial_start = time.perf_counter()
    try:
        list(map(func, data_list))
    except Exception as e:
        raise RuntimeError(f"Serial execution failed: {e}")
    serial_end = time.perf_counter()
    serial_time = serial_end - serial_start
    
    if verbose:
        print(f"  Serial time: {serial_time:.4f}s\n")
    
    # Define search space
    search_space = [
        Integer(n_jobs_min, n_jobs_max, name='n_jobs'),
        Integer(chunksize_min, chunksize_max, name='chunksize')
    ]
    
    # Track all results
    all_results: Dict[Tuple[int, int], float] = {}
    iteration_counter = [0]  # Use list to allow modification in nested function
    
    # Define objective function for optimization
    @use_named_args(search_space)
    def objective(n_jobs, chunksize):
        """Objective function to minimize: execution time."""
        iteration_counter[0] += 1
        
        if verbose:
            print(f"[{iteration_counter[0]}/{n_iterations}] Testing n_jobs={n_jobs}, "
                  f"chunksize={chunksize}...", end=" ")
        
        exec_time = _benchmark_configuration(
            func, data_list, n_jobs, chunksize,
            executor_type=executor_type,
            timeout=timeout_per_config
        )
        
        all_results[(n_jobs, chunksize)] = exec_time
        
        if verbose:
            if exec_time == float('inf'):
                print("FAILED")
            else:
                speedup = serial_time / exec_time if exec_time > 0 else 0
                print(f"{exec_time:.4f}s ({speedup:.2f}x)")
        
        return exec_time
    
    # Run Bayesian optimization
    try:
        result = gp_minimize(
            objective,
            search_space,
            n_calls=n_iterations,
            n_initial_points=max(3, n_iterations // 5),  # 20% initial random exploration
            initial_point_generator='random',
            x0=initial_x if initial_x else None,  # Start near optimizer hint if available
            random_state=random_state,
            verbose=False  # We handle our own verbosity
        )
        
        best_n_jobs = int(result.x[0])
        best_chunksize = int(result.x[1])
        best_time = result.fun
    except Exception as e:
        if verbose:
            print(f"\nWarning: Bayesian optimization failed: {e}")
            print("Using best result from completed iterations...")
        
        # If optimization fails, use best from what we have
        if all_results:
            best_config = min(all_results.items(), key=lambda x: x[1])
            best_n_jobs, best_chunksize = best_config[0]
            best_time = best_config[1]
        else:
            # Fallback to serial
            best_n_jobs = 1
            best_chunksize = 1
            best_time = serial_time
    
    # If serial is still faster, use serial
    if serial_time < best_time:
        best_time = serial_time
        best_n_jobs = 1
        best_chunksize = 1
    
    best_speedup = serial_time / best_time if best_time > 0 else 0
    
    if verbose:
        print(f"\n=== Optimization Complete ===")
        print(f"Best configuration: n_jobs={best_n_jobs}, chunksize={best_chunksize}")
        print(f"Best time: {best_time:.4f}s ({best_speedup:.2f}x speedup)")
        print(f"Configurations tested: {len(all_results) + 1}\n")
    
    return TuningResult(
        best_n_jobs=best_n_jobs,
        best_chunksize=best_chunksize,
        best_time=best_time,
        best_speedup=best_speedup,
        serial_time=serial_time,
        configurations_tested=len(all_results) + 1,  # +1 for serial
        all_results=all_results,
        optimization_hint=optimization_hint,
        search_strategy="bayesian",
        executor_type=executor_type
    )
