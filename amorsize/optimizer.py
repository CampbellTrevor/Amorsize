"""
Main optimizer module that coordinates the analysis and returns optimal parameters.
"""

from typing import Any, Callable, Iterator, List, Union, Tuple, Optional
import warnings

from .system_info import get_physical_cores, get_spawn_cost, calculate_max_workers
from .sampling import perform_dry_run, estimate_total_items


class OptimizationResult:
    """Container for optimization results."""
    
    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        reason: str,
        estimated_speedup: float = 1.0,
        warnings: List[str] = None
    ):
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.reason = reason
        self.estimated_speedup = estimated_speedup
        self.warnings = warnings or []
    
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


def optimize(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    verbose: bool = False
) -> OptimizationResult:
    """
    Analyze a function and data to determine optimal parallelization parameters.
    
    This function performs a heuristic analysis to prevent "Negative Scaling"
    where parallelism is slower than serial execution.
    
    Args:
        func: The function to parallelize. Must accept a single argument.
        data: Iterable of input data
        sample_size: Number of items to sample for timing (default: 5)
        target_chunk_duration: Target duration per chunk in seconds (default: 0.2)
        verbose: If True, print detailed information
    
    Returns:
        OptimizationResult with recommended n_jobs and chunksize
    
    Example:
        >>> def expensive_function(x):
        ...     return x ** 2
        >>> data = range(10000)
        >>> result = optimize(expensive_function, data)
        >>> print(f"Use n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    """
    result_warnings = []
    
    # Step 1: Perform dry run sampling
    if verbose:
        print("Performing dry run sampling...")
    
    sampling_result = perform_dry_run(func, data, sample_size)
    
    # Check for errors during sampling
    if sampling_result.error:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason=f"Error during sampling: {str(sampling_result.error)}",
            estimated_speedup=1.0,
            warnings=[f"Sampling failed: {str(sampling_result.error)}"]
        )
    
    # Check picklability
    if not sampling_result.is_picklable:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason="Function is not picklable - cannot use multiprocessing",
            estimated_speedup=1.0,
            warnings=["Function cannot be pickled. Use serial execution."]
        )
    
    avg_time = sampling_result.avg_time
    return_size = sampling_result.return_size
    peak_memory = sampling_result.peak_memory
    
    if verbose:
        print(f"Average execution time: {avg_time:.4f}s")
        print(f"Average return size: {return_size} bytes")
        print(f"Peak memory: {peak_memory} bytes")
    
    # Step 2: Fast Fail - very quick functions
    if avg_time < 0.001:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason="Function is too fast (< 1ms) - parallelization overhead would dominate",
            estimated_speedup=1.0
        )
    
    # Step 3: Estimate total workload
    total_items = estimate_total_items(data, False)
    
    if total_items > 0:
        estimated_total_time = avg_time * total_items
        
        if verbose:
            print(f"Estimated total items: {total_items}")
            print(f"Estimated serial execution time: {estimated_total_time:.2f}s")
    else:
        # Can't determine size for generators
        estimated_total_time = None
        result_warnings.append("Cannot determine data size - using heuristics")
    
    # Step 4: Get system information
    physical_cores = get_physical_cores()
    spawn_cost = get_spawn_cost()
    
    if verbose:
        print(f"Physical cores: {physical_cores}")
        print(f"Estimated spawn cost: {spawn_cost}s")
    
    # Step 5: Check if parallelization is worth it
    if estimated_total_time is not None and estimated_total_time < spawn_cost * 2:
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason=f"Total execution time ({estimated_total_time:.2f}s) too short for parallelization overhead",
            estimated_speedup=1.0
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
    
    # Step 8: Estimate speedup
    if estimated_total_time and optimal_n_jobs > 1:
        # Simplified Amdahl's law calculation
        parallel_fraction = 1.0  # Assume fully parallelizable
        serial_time = estimated_total_time
        parallel_time = (spawn_cost * optimal_n_jobs) + (serial_time / optimal_n_jobs)
        estimated_speedup = serial_time / parallel_time
    else:
        estimated_speedup = float(optimal_n_jobs)
    
    # Step 9: Final sanity check
    if optimal_n_jobs == 1:
        return OptimizationResult(
            n_jobs=1,
            chunksize=optimal_chunksize,
            reason="Serial execution recommended based on constraints",
            estimated_speedup=1.0,
            warnings=result_warnings
        )
    
    return OptimizationResult(
        n_jobs=optimal_n_jobs,
        chunksize=optimal_chunksize,
        reason=f"Parallelization beneficial: {optimal_n_jobs} workers with chunks of {optimal_chunksize}",
        estimated_speedup=estimated_speedup,
        warnings=result_warnings
    )
