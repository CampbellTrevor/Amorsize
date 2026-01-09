"""
Sampling module for performing dry runs and measuring function performance.
"""

import sys
import time
import pickle
import tracemalloc
from typing import Any, Callable, Iterator, List, Tuple, Union
import itertools


class SamplingResult:
    """Container for sampling results."""
    
    def __init__(
        self,
        avg_time: float,
        return_size: int,
        peak_memory: int,
        sample_count: int,
        is_picklable: bool,
        error: Exception = None
    ):
        self.avg_time = avg_time
        self.return_size = return_size
        self.peak_memory = peak_memory
        self.sample_count = sample_count
        self.is_picklable = is_picklable
        self.error = error


def check_picklability(func: Callable) -> bool:
    """
    Check if a function can be pickled.
    
    Args:
        func: Function to check
    
    Returns:
        True if the function is picklable, False otherwise
    """
    try:
        pickle.dumps(func)
        return True
    except (pickle.PicklingError, AttributeError, TypeError):
        return False


def safe_slice_data(data: Union[List, Iterator], sample_size: int) -> Tuple[List, bool]:
    """
    Safely extract a sample from data without consuming generators.
    
    Args:
        data: Input data (list, iterator, or generator)
        sample_size: Number of items to sample
    
    Returns:
        Tuple of (sample_list, is_generator)
    """
    # Check if data is a generator or iterator
    is_generator = hasattr(data, '__iter__') and not hasattr(data, '__len__')
    
    if is_generator:
        # Use itertools.islice for generators
        sample = list(itertools.islice(data, sample_size))
        return sample, True
    else:
        # For lists or sequences with __len__
        sample = list(itertools.islice(iter(data), sample_size))
        return sample, False


def perform_dry_run(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 5
) -> SamplingResult:
    """
    Perform a dry run of the function on a small sample of data.
    
    Args:
        func: The function to test
        data: The input data
        sample_size: Number of items to sample (default: 5)
    
    Returns:
        SamplingResult with timing and memory information
    """
    # Check if function is picklable
    is_picklable = check_picklability(func)
    
    # Get sample data
    try:
        sample, is_gen = safe_slice_data(data, sample_size)
    except Exception as e:
        return SamplingResult(
            avg_time=0.0,
            return_size=0,
            peak_memory=0,
            sample_count=0,
            is_picklable=is_picklable,
            error=e
        )
    
    if not sample:
        return SamplingResult(
            avg_time=0.0,
            return_size=0,
            peak_memory=0,
            sample_count=0,
            is_picklable=is_picklable,
            error=ValueError("Empty data sample")
        )
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        times = []
        return_sizes = []
        
        for item in sample:
            # Measure execution time
            start_time = time.perf_counter()
            result = func(item)
            end_time = time.perf_counter()
            
            times.append(end_time - start_time)
            
            # Measure return object size
            try:
                # Try to pickle the result to get realistic size
                pickled = pickle.dumps(result)
                return_sizes.append(len(pickled))
            except:
                # Fallback to sys.getsizeof
                return_sizes.append(sys.getsizeof(result))
        
        # Get peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Calculate averages
        avg_time = sum(times) / len(times) if times else 0.0
        avg_return_size = sum(return_sizes) // len(return_sizes) if return_sizes else 0
        
        return SamplingResult(
            avg_time=avg_time,
            return_size=avg_return_size,
            peak_memory=peak,
            sample_count=len(sample),
            is_picklable=is_picklable,
            error=None
        )
    
    except Exception as e:
        tracemalloc.stop()
        return SamplingResult(
            avg_time=0.0,
            return_size=0,
            peak_memory=0,
            sample_count=len(sample),
            is_picklable=is_picklable,
            error=e
        )


def estimate_total_items(data: Union[List, Iterator], sample_consumed: bool) -> int:
    """
    Estimate the total number of items in the data.
    
    Args:
        data: Input data
        sample_consumed: Whether the sample was consumed from a generator
    
    Returns:
        Estimated total items, or -1 if unknown
    """
    if hasattr(data, '__len__'):
        return len(data)
    else:
        # Can't determine length of consumed generator
        return -1
