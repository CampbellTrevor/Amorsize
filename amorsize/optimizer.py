"""
Main optimizer module that coordinates the analysis and returns optimal parameters.
"""

from typing import Any, Callable, Iterator, List, Union, Tuple, Optional
import warnings

from .system_info import (
    get_physical_cores,
    get_spawn_cost,
    get_chunking_overhead,
    calculate_max_workers,
    check_start_method_mismatch,
    get_multiprocessing_start_method,
    get_available_memory
)
from .sampling import perform_dry_run, estimate_total_items, reconstruct_iterator


class OptimizationResult:
    """Container for optimization results."""
    
    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        reason: str,
        estimated_speedup: float = 1.0,
        warnings: List[str] = None,
        data: Union[List, Iterator, None] = None
    ):
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.reason = reason
        self.estimated_speedup = estimated_speedup
        self.warnings = warnings or []
        self.data = data
    
    def __repr__(self):
        return (
            f"OptimizationResult(n_jobs={self.n_jobs}, "
            f"chunksize={self.chunksize}, "
            f"estimated_speedup={self.estimated_speedup:.2f}x)"
        )
    
    def __str__(self):
        result = f"Recommended: n_jobs={self.n_jobs}, chunksize={self.chunksize}\n"
        result += f"Reason: {self.reason}\n"
        result += f"Estimated speedup: {self.estimated_speedup:.2f}x"
        if self.warnings:
            result += "\nWarnings:\n" + "\n".join(f"  - {w}" for w in self.warnings)
        return result


def calculate_amdahl_speedup(
    total_compute_time: float,
    pickle_overhead_per_item: float,
    spawn_cost_per_worker: float,
    chunking_overhead_per_chunk: float,
    n_jobs: int,
    chunksize: int,
    total_items: int
) -> float:
    """
    Calculate realistic speedup using Amdahl's Law with overhead accounting.
    
    This implements a refined version of Amdahl's Law that accounts for:
    1. Process spawn overhead (one-time cost per worker)
    2. Pickle/IPC overhead (per-item serialization cost)
    3. Chunking overhead (per-chunk communication cost)
    
    The formula breaks execution into:
    - Serial portion: spawn costs + data distribution overhead
    - Parallel portion: actual computation time divided across workers
    - IPC overhead: pickle time for results (happens per item)
    
    Args:
        total_compute_time: Total serial computation time (seconds)
        pickle_overhead_per_item: Time to pickle one result (seconds)
        spawn_cost_per_worker: Time to spawn one worker process (seconds)
        chunking_overhead_per_chunk: Time per chunk for task distribution (seconds)
        n_jobs: Number of parallel workers
        chunksize: Items per chunk
        total_items: Total number of items to process
    
    Returns:
        Estimated speedup factor (>1.0 means parallelization helps)
        
    Mathematical Model:
        Serial Time = T_compute
        
        Parallel Time = T_spawn + T_parallel_compute + T_ipc + T_chunking
        where:
            T_spawn = spawn_cost * n_jobs (one-time startup)
            T_parallel_compute = T_compute / n_jobs (ideal parallelization)
            T_ipc = pickle_overhead * total_items (serialization overhead)
            T_chunking = chunking_overhead * num_chunks (task distribution)
        
        The IPC overhead is unavoidable and happens regardless of parallelization,
        but it represents the "serial fraction" in Amdahl's Law because results
        must be collected sequentially.
    """
    if n_jobs <= 0 or total_compute_time <= 0:
        return 1.0
    
    # Serial execution time (baseline)
    serial_time = total_compute_time
    
    # Parallel execution breakdown:
    # 1. Spawn overhead (one-time cost to start all workers)
    spawn_overhead = spawn_cost_per_worker * n_jobs
    
    # 2. Parallel computation (ideal speedup)
    parallel_compute_time = total_compute_time / n_jobs
    
    # 3. IPC overhead (pickle/unpickle for inter-process communication)
    # This is per-item and largely serial (results collected sequentially)
    ipc_overhead = pickle_overhead_per_item * total_items
    
    # 4. Chunking overhead (additional cost per chunk for task distribution)
    # Each chunk requires queue operations, context switches, etc.
    # This is now dynamically measured per-system
    num_chunks = max(1, (total_items + chunksize - 1) // chunksize)
    chunking_overhead = chunking_overhead_per_chunk * num_chunks
    
    # Total parallel execution time
    parallel_time = spawn_overhead + parallel_compute_time + ipc_overhead + chunking_overhead
    
    # Calculate speedup
    if parallel_time > 0:
        speedup = serial_time / parallel_time
        # Speedup cannot exceed n_jobs (theoretical maximum)
        return min(speedup, float(n_jobs))
    
    return 1.0


def optimize(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    verbose: bool = False,
    use_spawn_benchmark: bool = False,
    use_chunking_benchmark: bool = False
) -> OptimizationResult:
    """
    Analyze a function and data to determine optimal parallelization parameters.
    
    This function performs a heuristic analysis to prevent "Negative Scaling"
    where parallelism is slower than serial execution, following these steps:
    
    1. Dry Run Sampling: Execute func on sample_size items to measure timing
    2. Overhead Estimation: Calculate process spawn costs (OS-dependent)
    3. Optimization: Determine optimal chunksize and n_jobs based on:
       - Target chunk duration (default: 0.2s to amortize IPC overhead)
       - Physical cores (not hyperthreaded logical cores)
       - Memory constraints (prevents OOM)
    
    Fail-Safe Protocol:
        If ANY step fails (pickling error, sampling error, etc.), the function
        returns n_jobs=1 (serial execution) rather than crashing your program.
        Safety over speed is the priority.
    
    Generator Handling:
        When data is a generator, the sampling process consumes items from it.
        To preserve the full dataset, the consumed items are automatically
        reconstructed using itertools.chain. The reconstructed data is available
        in the result.data attribute. For list inputs, result.data will contain
        the original list unchanged.
        
        IMPORTANT: When using generators, always use result.data instead of
        the original generator to ensure no data is lost:
        
        >>> gen = (x for x in range(1000))
        >>> result = optimize(func, gen)
        >>> # Use result.data, NOT gen!
        >>> with Pool(result.n_jobs) as pool:
        ...     results = pool.map(func, result.data, chunksize=result.chunksize)
    
    Args:
        func: The function to parallelize. Must accept a single argument and
              be picklable (no lambdas, no local functions with closures).
        data: Iterable of input data (list, range, generator, etc.)
        sample_size: Number of items to sample for timing (default: 5)
                    Larger values = more accurate but slower analysis
        target_chunk_duration: Target duration per chunk in seconds (default: 0.2)
                              Higher values = fewer chunks, less overhead
        verbose: If True, print detailed analysis information
        use_spawn_benchmark: If True, measure actual spawn cost instead of
                            using OS-based estimate (slower but more accurate)
        use_chunking_benchmark: If True, measure actual chunking overhead instead of
                               using default estimate (slower but more accurate)
    
    Returns:
        OptimizationResult with:
            - n_jobs: Recommended number of workers
            - chunksize: Recommended chunk size
            - data: Reconstructed data (important for generators!)
            - reason: Explanation of recommendation
            - estimated_speedup: Expected performance improvement
            - warnings: List of constraints or issues
    
    Example:
        >>> def expensive_function(x):
        ...     result = 0
        ...     for i in range(1000):
        ...         result += x ** 2
        ...     return result
        >>> data = range(10000)
        >>> result = optimize(expensive_function, data, verbose=True)
        >>> print(f"Use n_jobs={result.n_jobs}, chunksize={result.chunksize}")
        >>> # Now use with multiprocessing.Pool:
        >>> from multiprocessing import Pool
        >>> with Pool(result.n_jobs) as pool:
        ...     # Use result.data to ensure generators are properly reconstructed
        ...     results = pool.map(expensive_function, result.data, chunksize=result.chunksize)
    """
    result_warnings = []
    
    # Step 1: Perform dry run sampling
    if verbose:
        print("Performing dry run sampling...")
    
    sampling_result = perform_dry_run(func, data, sample_size)
    
    # Reconstruct data for generators to preserve consumed items
    # For lists, use original data. For generators, chain sample with remaining.
    if sampling_result.is_generator and sampling_result.remaining_data is not None:
        reconstructed_data = reconstruct_iterator(sampling_result.sample, sampling_result.remaining_data)
    else:
        reconstructed_data = sampling_result.remaining_data if sampling_result.remaining_data is not None else data
    
    # Check for errors during sampling
    if sampling_result.error:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason=f"Error during sampling: {str(sampling_result.error)}",
            estimated_speedup=1.0,
            warnings=[f"Sampling failed: {str(sampling_result.error)}"],
            data=reconstructed_data
        )
    
    # Check picklability
    if not sampling_result.is_picklable:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason="Function is not picklable - cannot use multiprocessing",
            estimated_speedup=1.0,
            warnings=["Function cannot be pickled. Use serial execution."],
            data=reconstructed_data
        )
    
    avg_time = sampling_result.avg_time
    return_size = sampling_result.return_size
    peak_memory = sampling_result.peak_memory
    avg_pickle_time = sampling_result.avg_pickle_time
    
    if verbose:
        print(f"Average execution time: {avg_time:.4f}s")
        print(f"Average return size: {return_size} bytes")
        print(f"Peak memory: {peak_memory} bytes")
        print(f"Average pickle overhead: {avg_pickle_time:.6f}s")
    
    # Step 2: Estimate total workload and check for memory safety
    # This must happen BEFORE fast-fail checks because memory explosion
    # is a safety issue regardless of function speed
    total_items = estimate_total_items(data, False)
    available_memory = get_available_memory()
    memory_threshold = available_memory * 0.5
    
    if total_items > 0:
        estimated_total_time = avg_time * total_items
        
        # Estimate total memory for accumulated results
        # pool.map() keeps all results in memory until completion
        estimated_result_memory = return_size * total_items
        
        if verbose:
            print(f"Estimated total items: {total_items}")
            print(f"Estimated serial execution time: {estimated_total_time:.2f}s")
            print(f"Estimated result memory accumulation: {estimated_result_memory / (1024**2):.2f} MB")
        
        # Check if result accumulation might cause OOM
        if estimated_result_memory > memory_threshold:
            memory_gb = estimated_result_memory / (1024**3)
            available_gb = available_memory / (1024**3)
            warning_message = (
                f"Large return objects detected: Results will consume ~{memory_gb:.2f}GB "
                f"(available: {available_gb:.2f}GB). Consider using imap_unordered() or "
                f"processing in batches to avoid memory exhaustion."
            )
            result_warnings.append(warning_message)
            
            if verbose:
                print(f"WARNING: Result memory ({memory_gb:.2f}GB) exceeds safety threshold "
                      f"({available_gb * 0.5:.2f}GB). Risk of OOM!")
    else:
        # Can't determine size for generators
        estimated_total_time = None
        result_warnings.append("Cannot determine data size - using heuristics")
    
    # Step 3: Fast Fail - very quick functions
    if avg_time < 0.001:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason="Function is too fast (< 1ms) - parallelization overhead would dominate",
            estimated_speedup=1.0,
            warnings=result_warnings,
            data=reconstructed_data
        )
    
    # Step 4: Get system information
    physical_cores = get_physical_cores()
    spawn_cost = get_spawn_cost(use_benchmark=use_spawn_benchmark)
    chunking_overhead = get_chunking_overhead(use_benchmark=use_chunking_benchmark)
    
    # Check for non-default start method
    is_mismatch, mismatch_warning = check_start_method_mismatch()
    if is_mismatch:
        result_warnings.append(mismatch_warning)
    
    if verbose:
        print(f"Physical cores: {physical_cores}")
        print(f"Multiprocessing start method: {get_multiprocessing_start_method()}")
        print(f"Estimated spawn cost: {spawn_cost}s")
        print(f"Estimated chunking overhead: {chunking_overhead * 1000:.3f}ms per chunk")
        if is_mismatch:
            print(f"Warning: {mismatch_warning}")
    
    # Step 5: Check if parallelization is worth it
    if estimated_total_time is not None and estimated_total_time < spawn_cost * 2:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason=f"Total execution time ({estimated_total_time:.2f}s) too short for parallelization overhead",
            estimated_speedup=1.0,
            data=reconstructed_data
        )
    
    # Step 6: Calculate optimal chunksize
    # Target: each chunk should take at least target_chunk_duration seconds
    if avg_time > 0:
        optimal_chunksize = max(1, int(target_chunk_duration / avg_time))
    else:
        optimal_chunksize = 1
    
    # Cap chunksize at a reasonable value
    if total_items > 0:
        # Don't make chunks larger than 10% of total items
        max_reasonable_chunksize = max(1, total_items // 10)
        optimal_chunksize = min(optimal_chunksize, max_reasonable_chunksize)
    
    if verbose:
        print(f"Optimal chunksize: {optimal_chunksize}")
    
    # Step 7: Determine number of workers
    # Consider memory constraints
    estimated_job_ram = peak_memory if peak_memory > 0 else 0
    max_workers = calculate_max_workers(physical_cores, estimated_job_ram)
    
    if max_workers < physical_cores:
        result_warnings.append(
            f"Memory constraints limit workers to {max_workers} "
            f"(physical cores: {physical_cores})"
        )
    
    # For CPU-bound tasks, use physical cores (not logical/hyperthreaded)
    optimal_n_jobs = max_workers
    
    if verbose:
        print(f"Optimal n_jobs: {optimal_n_jobs}")
    
    # Step 8: Estimate speedup using proper Amdahl's Law
    if estimated_total_time and optimal_n_jobs > 1 and total_items > 0:
        # Use refined Amdahl's Law calculation with overhead accounting
        estimated_speedup = calculate_amdahl_speedup(
            total_compute_time=estimated_total_time,
            pickle_overhead_per_item=avg_pickle_time,
            spawn_cost_per_worker=spawn_cost,
            chunking_overhead_per_chunk=chunking_overhead,
            n_jobs=optimal_n_jobs,
            chunksize=optimal_chunksize,
            total_items=total_items
        )
        
        if verbose:
            print(f"Estimated speedup: {estimated_speedup:.2f}x")
        
        # If speedup is less than 1.2x, parallelization may not be worth it
        if estimated_speedup < 1.2:
            return OptimizationResult(
                n_jobs=1,
                chunksize=1,
                reason=f"Parallelization provides minimal benefit (estimated speedup: {estimated_speedup:.2f}x)",
                estimated_speedup=1.0,
                warnings=result_warnings + ["Overhead costs make parallelization inefficient for this workload"],
                data=reconstructed_data
            )
    else:
        # Fallback for cases where we don't have enough info
        estimated_speedup = float(optimal_n_jobs) * 0.7  # Conservative estimate
    
    # Step 9: Final sanity check
    if optimal_n_jobs == 1:
        return OptimizationResult(
            n_jobs=1,
            chunksize=optimal_chunksize,
            reason="Serial execution recommended based on constraints",
            estimated_speedup=1.0,
            warnings=result_warnings,
            data=reconstructed_data
        )
    
    return OptimizationResult(
        n_jobs=optimal_n_jobs,
        chunksize=optimal_chunksize,
        reason=f"Parallelization beneficial: {optimal_n_jobs} workers with chunks of {optimal_chunksize}",
        estimated_speedup=estimated_speedup,
        warnings=result_warnings,
        data=reconstructed_data
    )
