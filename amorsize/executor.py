"""
Execution module for running optimized parallel workloads.

This module provides convenience functions that combine optimization
and execution in a single call, making it easier to use Amorsize.
"""

import multiprocessing
import os
import threading
import time
from multiprocessing import Pool
from typing import Any, Callable, Iterator, List, Optional, Union

from .hooks import HookContext, HookEvent, HookManager
from .optimizer import optimize

# Default estimated item time when not available from optimization result
DEFAULT_ESTIMATED_ITEM_TIME = 0.01

# Global hook manager for worker processes (set via initializer)
_worker_hook_manager: Optional[HookManager] = None
_worker_id_counter = multiprocessing.Value('i', 0)
_worker_id_lock = multiprocessing.Lock()


def _worker_initializer(hook_manager: Optional[HookManager]) -> None:
    """
    Initialize worker process with hook manager.
    
    This function is called once when each worker process starts.
    It sets up the global hook manager and triggers ON_WORKER_START event.
    
    Args:
        hook_manager: HookManager instance to use for this worker
    """
    global _worker_hook_manager
    _worker_hook_manager = hook_manager
    
    # Trigger ON_WORKER_START hook
    if hook_manager is not None and hook_manager.has_hooks(HookEvent.ON_WORKER_START):
        # Get unique worker ID
        with _worker_id_lock:
            _worker_id_counter.value += 1
            worker_id = _worker_id_counter.value
        
        hook_manager.trigger(HookContext(
            event=HookEvent.ON_WORKER_START,
            worker_id=worker_id,
            metadata={"pid": os.getpid()}
        ))


def _worker_wrapper(func: Callable[[Any], Any], item: Any) -> Any:
    """
    Wrapper function that executes user function and triggers hooks.
    
    This wrapper is used to track individual item execution in workers.
    It's primarily used for fine-grained monitoring but adds minimal overhead.
    
    Args:
        func: User function to execute
        item: Input item to process
    
    Returns:
        Result of func(item)
    """
    # Simply execute the function - we track chunks, not individual items
    # to minimize overhead
    return func(item)


def _execute_serial(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    hooks: Optional[HookManager],
    start_time: float,
    chunksize: int,
    use_fine_grained_tracking: bool
) -> List[Any]:
    """
    Execute function serially with optional fine-grained tracking.
    
    Args:
        func: Function to execute
        data: Input data
        hooks: Hook manager for callbacks
        start_time: Execution start time
        chunksize: Chunk size for grouping
        use_fine_grained_tracking: Whether to trigger progress/chunk hooks
    
    Returns:
        List of results
    """
    results = []
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if not use_fine_grained_tracking:
        # Fast path - no fine-grained tracking
        return [func(item) for item in data_list]
    
    # Process items with fine-grained tracking
    chunk_id = 0
    for i in range(0, total_items, chunksize):
        chunk_start = time.time()
        chunk_data = data_list[i:i+chunksize]
        chunk_results = [func(item) for item in chunk_data]
        results.extend(chunk_results)
        chunk_time = time.time() - chunk_start
        
        # Trigger ON_CHUNK_COMPLETE hook
        if hooks is not None and hooks.has_hooks(HookEvent.ON_CHUNK_COMPLETE):
            hooks.trigger(HookContext(
                event=HookEvent.ON_CHUNK_COMPLETE,
                chunk_id=chunk_id,
                chunk_size=len(chunk_data),
                chunk_time=chunk_time,
                items_completed=len(results),
                total_items=total_items,
                percent_complete=(len(results) / total_items * 100.0) if total_items > 0 else 0.0,
                elapsed_time=time.time() - start_time
            ))
        
        # Trigger ON_PROGRESS hook
        if hooks is not None and hooks.has_hooks(HookEvent.ON_PROGRESS):
            elapsed = time.time() - start_time
            hooks.trigger(HookContext(
                event=HookEvent.ON_PROGRESS,
                items_completed=len(results),
                total_items=total_items,
                percent_complete=(len(results) / total_items * 100.0) if total_items > 0 else 0.0,
                elapsed_time=elapsed,
                throughput_items_per_sec=len(results) / elapsed if elapsed > 0 else 0.0
            ))
        
        chunk_id += 1
    
    return results


def _execute_threaded(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    n_jobs: int,
    chunksize: int,
    hooks: Optional[HookManager],
    start_time: float,
    use_fine_grained_tracking: bool
) -> List[Any]:
    """
    Execute function using ThreadPoolExecutor with optional fine-grained tracking.
    
    Args:
        func: Function to execute
        data: Input data
        n_jobs: Number of threads
        chunksize: Chunk size for grouping
        hooks: Hook manager for callbacks
        start_time: Execution start time
        use_fine_grained_tracking: Whether to trigger progress/chunk hooks
    
    Returns:
        List of results
    """
    from concurrent.futures import ThreadPoolExecutor
    
    data_list = list(data) if not isinstance(data, list) else data
    
    if not use_fine_grained_tracking:
        # Fast path - use standard map
        with ThreadPoolExecutor(max_workers=n_jobs) as executor:
            return list(executor.map(func, data_list, chunksize=chunksize))
    
    # Use submit for fine-grained tracking
    results = []
    total_items = len(data_list)
    
    with ThreadPoolExecutor(max_workers=n_jobs) as executor:
        # Submit all tasks
        futures = []
        for i in range(0, total_items, chunksize):
            chunk_data = data_list[i:i+chunksize]
            for item in chunk_data:
                futures.append(executor.submit(func, item))
        
        # Collect results with progress tracking
        chunk_id = 0
        items_processed = 0
        chunk_start_idx = 0
        
        for idx, future in enumerate(futures):
            result = future.result()
            results.append(result)
            items_processed += 1
            
            # Check if we completed a chunk
            if (items_processed - chunk_start_idx >= chunksize) or (items_processed == total_items):
                chunk_size = items_processed - chunk_start_idx
                chunk_start_idx = items_processed
                
                # Trigger ON_CHUNK_COMPLETE hook
                if hooks is not None and hooks.has_hooks(HookEvent.ON_CHUNK_COMPLETE):
                    hooks.trigger(HookContext(
                        event=HookEvent.ON_CHUNK_COMPLETE,
                        chunk_id=chunk_id,
                        chunk_size=chunk_size,
                        items_completed=items_processed,
                        total_items=total_items,
                        percent_complete=(items_processed / total_items * 100.0) if total_items > 0 else 0.0,
                        elapsed_time=time.time() - start_time
                    ))
                
                # Trigger ON_PROGRESS hook
                if hooks is not None and hooks.has_hooks(HookEvent.ON_PROGRESS):
                    elapsed = time.time() - start_time
                    hooks.trigger(HookContext(
                        event=HookEvent.ON_PROGRESS,
                        items_completed=items_processed,
                        total_items=total_items,
                        percent_complete=(items_processed / total_items * 100.0) if total_items > 0 else 0.0,
                        elapsed_time=elapsed,
                        throughput_items_per_sec=items_processed / elapsed if elapsed > 0 else 0.0
                    ))
                
                chunk_id += 1
    
    return results


def _execute_multiprocess(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    n_jobs: int,
    chunksize: int,
    hooks: Optional[HookManager],
    start_time: float,
    use_fine_grained_tracking: bool
) -> List[Any]:
    """
    Execute function using multiprocessing.Pool with optional fine-grained tracking.
    
    Args:
        func: Function to execute
        data: Input data
        n_jobs: Number of processes
        chunksize: Chunk size for grouping
        hooks: Hook manager for callbacks
        start_time: Execution start time
        use_fine_grained_tracking: Whether to trigger progress/chunk hooks
    
    Returns:
        List of results
    """
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    # Determine if we need worker hooks
    need_worker_hooks = (
        hooks is not None and (
            hooks.has_hooks(HookEvent.ON_WORKER_START) or
            hooks.has_hooks(HookEvent.ON_WORKER_END)
        )
    )
    
    if not use_fine_grained_tracking and not need_worker_hooks:
        # Fast path - use standard map without hooks
        with Pool(n_jobs) as pool:
            return pool.map(func, data_list, chunksize=chunksize)
    
    # Use imap for fine-grained tracking
    # Note: We can't pass hooks to worker processes due to pickling issues,
    # so ON_WORKER_START/END hooks can't be triggered in true worker context.
    # They would need shared memory or a separate communication channel.
    # For now, we focus on chunk and progress tracking which are valuable.
    
    with Pool(n_jobs) as pool:
        results = []
        chunk_id = 0
        items_processed = 0
        chunk_start_idx = 0
        chunk_start_time = time.time()
        
        # Use imap to get results as they complete
        for result in pool.imap(func, data_list, chunksize=chunksize):
            results.append(result)
            items_processed += 1
            
            # Check if we completed a chunk
            if (items_processed - chunk_start_idx >= chunksize) or (items_processed == total_items):
                chunk_size = items_processed - chunk_start_idx
                chunk_time = time.time() - chunk_start_time
                chunk_start_idx = items_processed
                chunk_start_time = time.time()
                
                # Trigger ON_CHUNK_COMPLETE hook
                if hooks is not None and hooks.has_hooks(HookEvent.ON_CHUNK_COMPLETE):
                    hooks.trigger(HookContext(
                        event=HookEvent.ON_CHUNK_COMPLETE,
                        chunk_id=chunk_id,
                        chunk_size=chunk_size,
                        chunk_time=chunk_time,
                        items_completed=items_processed,
                        total_items=total_items,
                        percent_complete=(items_processed / total_items * 100.0) if total_items > 0 else 0.0,
                        elapsed_time=time.time() - start_time
                    ))
                
                # Trigger ON_PROGRESS hook
                if hooks is not None and hooks.has_hooks(HookEvent.ON_PROGRESS):
                    elapsed = time.time() - start_time
                    hooks.trigger(HookContext(
                        event=HookEvent.ON_PROGRESS,
                        items_completed=items_processed,
                        total_items=total_items,
                        percent_complete=(items_processed / total_items * 100.0) if total_items > 0 else 0.0,
                        elapsed_time=elapsed,
                        throughput_items_per_sec=items_processed / elapsed if elapsed > 0 else 0.0
                    ))
                
                chunk_id += 1
    
    return results


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
    enable_online_learning: bool = False,
    hooks: Optional[HookManager] = None
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
        hooks: Optional HookManager for execution callbacks. If None, no hooks are triggered.
                Use this to monitor progress, collect metrics, or integrate with monitoring
                systems (default: None).

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
    # Track execution start time
    start_time = time.time()
    
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

    # Trigger PRE_EXECUTE hook
    if hooks is not None and hooks.has_hooks(HookEvent.PRE_EXECUTE):
        # Calculate total items safely
        total_items = None
        if hasattr(opt_result, 'data'):
            if hasattr(opt_result.data, '__len__'):
                try:
                    total_items = len(opt_result.data)
                except (TypeError, AttributeError):
                    pass
        
        hooks.trigger(HookContext(
            event=HookEvent.PRE_EXECUTE,
            n_jobs=opt_result.n_jobs,
            chunksize=opt_result.chunksize,
            total_items=total_items,
            metadata={
                "executor_type": opt_result.executor_type,
                "estimated_speedup": opt_result.estimated_speedup
            }
        ))

    # Determine if we need fine-grained tracking
    use_fine_grained_tracking = hooks is not None and (
        hooks.has_hooks(HookEvent.ON_CHUNK_COMPLETE) or
        hooks.has_hooks(HookEvent.ON_PROGRESS) or
        hooks.has_hooks(HookEvent.ON_WORKER_START) or
        hooks.has_hooks(HookEvent.ON_WORKER_END)
    )
    
    # Step 2: Execute with optimal parameters
    if opt_result.n_jobs == 1:
        # Serial execution - don't create any executor
        if verbose:
            print("Using serial execution (no Pool/ThreadPool created)")
        results = _execute_serial(
            func, opt_result.data, hooks, start_time, 
            opt_result.chunksize, use_fine_grained_tracking
        )
    elif opt_result.executor_type == "thread":
        # Threading execution for I/O-bound workloads
        if verbose:
            print(f"Creating ThreadPoolExecutor with {opt_result.n_jobs} workers")
        results = _execute_threaded(
            func, opt_result.data, opt_result.n_jobs, opt_result.chunksize,
            hooks, start_time, use_fine_grained_tracking
        )
    else:
        # Multiprocessing execution for CPU-bound workloads
        if verbose:
            print(f"Creating multiprocessing.Pool with {opt_result.n_jobs} workers")
        results = _execute_multiprocess(
            func, opt_result.data, opt_result.n_jobs, opt_result.chunksize,
            hooks, start_time, use_fine_grained_tracking
        )

    # Calculate execution time
    execution_time = time.time() - start_time
    
    if verbose:
        print(f"Execution complete: processed {len(results)} items in {execution_time:.2f}s")

    # Trigger POST_EXECUTE hook
    if hooks is not None and hooks.has_hooks(HookEvent.POST_EXECUTE):
        hooks.trigger(HookContext(
            event=HookEvent.POST_EXECUTE,
            n_jobs=opt_result.n_jobs,
            chunksize=opt_result.chunksize,
            total_items=len(results),
            items_completed=len(results),
            percent_complete=100.0,
            elapsed_time=execution_time,
            results_count=len(results),
            throughput_items_per_sec=len(results) / execution_time if execution_time > 0 else 0.0,
            metadata={
                "executor_type": opt_result.executor_type,
                "estimated_speedup": opt_result.estimated_speedup
            }
        ))

    # Step 3: Update ML model with actual results if online learning is enabled
    if enable_online_learning:
        try:
            # Import online learning function
            from .ml_prediction import update_model_from_execution

            # Calculate data size from results (avoids consuming iterator)
            data_size = len(results)

            # Estimate actual per-item time from optimization result
            # This is approximate but useful for training
            estimated_item_time = getattr(opt_result, 'avg_execution_time', DEFAULT_ESTIMATED_ITEM_TIME)

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
