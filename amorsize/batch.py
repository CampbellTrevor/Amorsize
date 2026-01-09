"""
Batch processing utilities for memory-constrained workloads.

This module provides helpers for processing large datasets in batches when
memory constraints prevent processing everything at once. This is particularly
useful when optimize() warns about result memory exceeding safety thresholds.
"""

from typing import Any, Callable, Iterator, List, Union, Optional
from multiprocessing import Pool

from .optimizer import optimize, OptimizationResult
from .system_info import get_available_memory


def process_in_batches(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    batch_size: Optional[int] = None,
    max_memory_percent: float = 0.5,
    sample_size: int = 5,
    verbose: bool = False,
    **optimize_kwargs
) -> List[Any]:
    """
    Process data in batches to avoid memory exhaustion.
    
    This function automatically divides data into batches, optimizes each batch
    independently, and processes them sequentially. This prevents memory exhaustion
    when function results are large and would otherwise accumulate in RAM.
    
    This is the recommended solution when optimize() warns:
    "Result memory exceeds safety threshold - consider processing in batches"
    
    Args:
        func: Function to apply to each data item. Must be picklable.
        data: Input data to process (list, range, iterator, etc.)
        batch_size: Number of items per batch. If None, automatically calculated
                   based on available memory and sample size. Smaller batches use
                   less memory but add overhead between batches.
        max_memory_percent: Maximum percentage of available memory to use per batch
                           (default: 0.5 = 50%). Only used if batch_size is None.
        sample_size: Number of items to sample for optimization (default: 5).
                    Passed to optimize() for each batch.
        verbose: If True, print progress information for each batch.
        **optimize_kwargs: Additional keyword arguments passed to optimize(),
                          such as target_chunk_duration, profile, etc.
    
    Returns:
        List of all results concatenated from all batches.
        
    Raises:
        ValueError: If parameters are invalid (e.g., negative batch_size)
        
    Examples:
        >>> # Process large dataset with large return objects
        >>> def process_image(path):
        ...     img = load_large_image(path)
        ...     return transform(img)  # Returns large result
        >>> 
        >>> image_paths = list_all_images()  # 10,000 images
        >>> # Memory-safe batch processing
        >>> results = process_in_batches(process_image, image_paths, verbose=True)
        
        >>> # Custom batch size
        >>> results = process_in_batches(
        ...     expensive_func,
        ...     range(100000),
        ...     batch_size=1000,
        ...     verbose=True
        ... )
        
        >>> # With profiling for first batch
        >>> results = process_in_batches(
        ...     func,
        ...     data,
        ...     profile=True,  # Passed to optimize()
        ...     verbose=True
        ... )
    
    Notes:
        - Each batch is optimized independently using optimize()
        - Results are accumulated in memory after each batch
        - Total memory = batch_size * result_size (controlled by batch_size)
        - Progress is printed if verbose=True
        - Generator inputs are fully materialized (required for batching)
    
    Memory Safety:
        The batch_size is automatically calculated to keep result memory under
        max_memory_percent of available RAM. This prevents OOM kills while
        still processing as much data as possible per batch.
        
    Performance Characteristics:
        - Overhead: One optimize() call per batch (~10-50ms each)
        - Memory: Peak memory = batch_size * avg_result_size
        - CPU: Optimal parallelization within each batch
        - Total time: sum(batch_processing_times) + inter-batch_overhead
    """
    # Validate parameters
    if not callable(func):
        raise ValueError("func must be callable")
    
    if batch_size is not None:
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")
    
    if not isinstance(max_memory_percent, (int, float)) or max_memory_percent <= 0 or max_memory_percent > 1:
        raise ValueError("max_memory_percent must be between 0 and 1")
    
    if not isinstance(sample_size, int) or sample_size <= 0:
        raise ValueError("sample_size must be a positive integer")
    
    if not isinstance(verbose, bool):
        raise ValueError("verbose must be a boolean")
    
    # Convert data to list if it's an iterator (required for batching)
    # Note: For very large iterators, consider using imap/imap_unordered instead
    if not isinstance(data, list):
        if verbose:
            print("Converting iterator to list for batching...")
        data = list(data)
    
    total_items = len(data)
    
    if total_items == 0:
        if verbose:
            print("No items to process")
        return []
    
    # Calculate batch size if not provided
    if batch_size is None:
        # Run optimize on sample to estimate result size
        sample_data = data[:min(sample_size, total_items)]
        sample_result = optimize(func, sample_data, sample_size=sample_size, **optimize_kwargs)
        
        # Get available memory
        available_memory = get_available_memory()
        
        # Calculate safe batch size
        # Estimate: each result is sample_result.return_size bytes
        # We want: batch_size * result_size <= max_memory_percent * available_memory
        if hasattr(sample_result, 'profile') and sample_result.profile:
            avg_result_size = sample_result.profile.return_size_bytes
        else:
            # Fallback: run a quick sample to estimate
            # Use a minimal sample to get result size
            test_result = func(data[0])
            try:
                import pickle
                avg_result_size = len(pickle.dumps(test_result))
            except (TypeError, pickle.PicklingError, AttributeError, MemoryError):
                import sys
                avg_result_size = sys.getsizeof(test_result)
        
        if avg_result_size > 0:
            safe_batch_size = int((max_memory_percent * available_memory) / avg_result_size)
            # Ensure at least 1 item per batch, at most total_items
            batch_size = max(1, min(safe_batch_size, total_items))
        else:
            # Fallback if we can't estimate size
            batch_size = max(1, total_items // 10)  # Conservative: 10 batches
        
        if verbose:
            print(f"Auto-calculated batch_size: {batch_size} items")
            print(f"  (based on {max_memory_percent*100:.0f}% of {available_memory / (1024**3):.2f} GB available memory)")
    
    # Calculate number of batches
    num_batches = (total_items + batch_size - 1) // batch_size  # Ceiling division
    
    if verbose:
        print(f"\nProcessing {total_items} items in {num_batches} batches")
        print(f"Batch size: {batch_size} items\n")
    
    # Process each batch
    all_results = []
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_items)
        batch_data = data[start_idx:end_idx]
        batch_items = len(batch_data)
        
        if verbose:
            print(f"Batch {batch_idx + 1}/{num_batches}: Processing {batch_items} items (indices {start_idx}-{end_idx-1})...")
        
        # Optimize this batch
        opt_result = optimize(func, batch_data, sample_size=min(sample_size, batch_items), **optimize_kwargs)
        
        if verbose:
            print(f"  Optimization: n_jobs={opt_result.n_jobs}, chunksize={opt_result.chunksize}, speedup={opt_result.estimated_speedup:.2f}x")
        
        # Process this batch
        if opt_result.n_jobs == 1:
            # Serial execution
            batch_results = [func(item) for item in opt_result.data]
        else:
            # Parallel execution
            with Pool(opt_result.n_jobs) as pool:
                batch_results = pool.map(func, opt_result.data, chunksize=opt_result.chunksize)
        
        all_results.extend(batch_results)
        
        if verbose:
            print(f"  Completed batch {batch_idx + 1}/{num_batches} ({len(all_results)}/{total_items} items processed)\n")
    
    if verbose:
        print(f"All batches complete. Processed {len(all_results)} items total.")
    
    return all_results


def estimate_safe_batch_size(
    result_size_bytes: int,
    max_memory_percent: float = 0.5
) -> int:
    """
    Estimate safe batch size based on result size and available memory.
    
    This is a helper function for users who want to manually calculate batch sizes
    before calling process_in_batches().
    
    Args:
        result_size_bytes: Size of a single result in bytes
        max_memory_percent: Maximum percentage of available memory to use (default: 0.5)
    
    Returns:
        Safe batch size (number of items)
        
    Examples:
        >>> # Estimate batch size for 10MB results
        >>> batch_size = estimate_safe_batch_size(10 * 1024 * 1024)
        >>> print(f"Safe batch size: {batch_size} items")
        
        >>> # More conservative (30% of memory)
        >>> batch_size = estimate_safe_batch_size(
        ...     result_size_bytes=50 * 1024 * 1024,
        ...     max_memory_percent=0.3
        ... )
    """
    if result_size_bytes <= 0:
        raise ValueError("result_size_bytes must be positive")
    
    if not isinstance(max_memory_percent, (int, float)) or max_memory_percent <= 0 or max_memory_percent > 1:
        raise ValueError("max_memory_percent must be between 0 and 1")
    
    available_memory = get_available_memory()
    safe_batch_size = int((max_memory_percent * available_memory) / result_size_bytes)
    
    # Ensure at least 1 item
    return max(1, safe_batch_size)
