"""
Execution module for running optimized parallel workloads.

This module provides convenience functions that combine optimization
and execution in a single call, making it easier to use Amorsize.
"""

from typing import Any, Callable, Iterator, List, Union, Optional
from multiprocessing import Pool
from .optimizer import optimize


def execute(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    verbose: bool = False,
    use_spawn_benchmark: bool = True,
    use_chunking_benchmark: bool = True,
    profile: bool = False,
    auto_adjust_for_nested_parallelism: bool = True,
    progress_callback: Optional[Callable[[str, float], None]] = None,
    return_optimization_result: bool = False,
    prefer_threads_for_io: bool = True,
    enable_online_learning: bool = False
) -> Union[List[Any], tuple]:
    """
    Optimize and execute a function on data in parallel.
    
    This is a convenience function that combines optimize() and multiprocessing.Pool
    in a single call. It automatically:
    1. Analyzes the function and data to find optimal parameters
    2. Creates a Pool with the optimal number of workers
    3. Executes the function with the optimal chunksize
    4. Returns the results
    5. Optionally updates ML model with actual execution results (online learning)
    
    This eliminates the boilerplate of manually creating and managing the Pool.
    
    For serial execution (n_jobs=1), the function is executed directly without
    creating a Pool, which is more efficient.
    
    Args:
        func: The function to parallelize. Must accept a single argument and
              be picklable (no lambdas, no local functions with closures).
        data: Iterable of input data (list, range, generator, etc.).
        sample_size: Number of items to sample for timing (default: 5).
        target_chunk_duration: Target duration per chunk in seconds (default: 0.2).
        verbose: If True, print detailed analysis information.
        use_spawn_benchmark: If True, measure actual spawn cost (default: True).
        use_chunking_benchmark: If True, measure actual chunking overhead (default: True).
        profile: If True, capture detailed diagnostic information (default: False).
        auto_adjust_for_nested_parallelism: If True, automatically reduce n_jobs
                when nested parallelism is detected (default: True).
        progress_callback: Optional callback function for progress updates.
        return_optimization_result: If True, return (results, optimization_result) tuple
                instead of just results (default: False).
        prefer_threads_for_io: If True, automatically use ThreadPoolExecutor instead of
                multiprocessing.Pool for I/O-bound workloads (< 30% CPU utilization).
                (default: True). Set to False to always use multiprocessing.
        enable_online_learning: If True, update ML model with actual execution results
                to improve future predictions. This helps the model learn from real
                workload behavior over time (default: False).
    
    Returns:
        List of results from applying func to each item in data.
        If return_optimization_result=True, returns tuple of (results, OptimizationResult).
    
    Raises:
        ValueError: If any parameter fails validation (same as optimize()).
    
    Example:
        >>> def expensive_function(x):
        ...     result = 0
        ...     for i in range(1000):
        ...         result += x ** 2
        ...     return result
        
        >>> data = range(10000)
        >>> results = execute(expensive_function, data, verbose=True)
        >>> print(f"Processed {len(results)} items")
        
        >>> # To get optimization details:
        >>> results, opt_result = execute(
        ...     expensive_function,
        ...     data,
        ...     return_optimization_result=True,
        ...     profile=True
        ... )
        >>> print(opt_result.explain())
        
        >>> # To enable online learning (improves ML predictions over time):
        >>> results = execute(
        ...     expensive_function,
        ...     data,
        ...     enable_online_learning=True,
        ...     verbose=True
        ... )
    
    Note:
        This function creates a new Pool for each call. If you need to reuse
        a Pool across multiple calls, use optimize() directly and manage
        the Pool yourself.
    """
    # Step 1: Optimize to get parameters
    opt_result = optimize(
        func=func,
        data=data,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        verbose=verbose,
        use_spawn_benchmark=use_spawn_benchmark,
        use_chunking_benchmark=use_chunking_benchmark,
        profile=profile,
        auto_adjust_for_nested_parallelism=auto_adjust_for_nested_parallelism,
        progress_callback=progress_callback,
        prefer_threads_for_io=prefer_threads_for_io
    )
    
    if verbose:
        print(f"\nExecuting with n_jobs={opt_result.n_jobs}, chunksize={opt_result.chunksize}, executor={opt_result.executor_type}")
        print(f"Estimated speedup: {opt_result.estimated_speedup}")
    
    # Step 2: Execute with optimal parameters
    if opt_result.n_jobs == 1:
        # Serial execution - don't create any executor
        if verbose:
            print("Using serial execution (no Pool/ThreadPool created)")
        results = [func(item) for item in opt_result.data]
    elif opt_result.executor_type == "thread":
        # Threading execution for I/O-bound workloads
        # Lazy import to avoid loading concurrent.futures at module level
        from concurrent.futures import ThreadPoolExecutor
        if verbose:
            print(f"Creating ThreadPoolExecutor with {opt_result.n_jobs} workers")
        with ThreadPoolExecutor(max_workers=opt_result.n_jobs) as executor:
            results = list(executor.map(func, opt_result.data, chunksize=opt_result.chunksize))
    else:
        # Multiprocessing execution for CPU-bound workloads
        if verbose:
            print(f"Creating multiprocessing.Pool with {opt_result.n_jobs} workers")
        with Pool(opt_result.n_jobs) as pool:
            results = pool.map(func, opt_result.data, chunksize=opt_result.chunksize)
    
    if verbose:
        print(f"Execution complete: processed {len(results)} items")
    
    # Step 3: Update ML model with actual results if online learning is enabled
    if enable_online_learning:
        try:
            import time
            # Import online learning function
            from .ml_prediction import update_model_from_execution
            
            # Calculate data size
            data_size = len(list(opt_result.data)) if hasattr(opt_result.data, '__len__') else len(results)
            
            # Estimate actual per-item time from optimization result
            # This is approximate but useful for training
            estimated_item_time = getattr(opt_result, 'avg_execution_time', 0.01)
            
            # Get additional features if available from optimization result
            pickle_size = getattr(opt_result, 'pickle_size', None)
            coefficient_of_variation = getattr(opt_result, 'coefficient_of_variation', None)
            
            # Actual speedup is estimated_speedup (we don't measure actual time here for simplicity)
            # In a production system, you could measure actual time and calculate true speedup
            actual_speedup = opt_result.estimated_speedup
            
            # Update model
            success = update_model_from_execution(
                func=func,
                data_size=data_size,
                estimated_item_time=estimated_item_time,
                actual_n_jobs=opt_result.n_jobs,
                actual_chunksize=opt_result.chunksize,
                actual_speedup=actual_speedup,
                pickle_size=pickle_size,
                coefficient_of_variation=coefficient_of_variation,
                verbose=verbose
            )
            
            if verbose and success:
                print("✓ ML model updated with execution results (online learning)")
        
        except Exception as e:
            if verbose:
                print(f"⚠ Online learning update failed: {e}")
    
    # Step 4: Return results (and optionally optimization details)
    if return_optimization_result:
        return results, opt_result
    else:
        return results
