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
        avg_pickle_time: float = 0.0,
        error: Exception = None,
        sample: List = None,
        remaining_data: Union[List, Iterator, None] = None,
        is_generator: bool = False
    ):
        self.avg_time = avg_time
        self.return_size = return_size
        self.peak_memory = peak_memory
        self.sample_count = sample_count
        self.is_picklable = is_picklable
        self.avg_pickle_time = avg_pickle_time
        self.error = error
        self.sample = sample or []
        self.remaining_data = remaining_data
        self.is_generator = is_generator


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


def safe_slice_data(data: Union[List, Iterator], sample_size: int) -> Tuple[List, Union[List, Iterator], bool]:
    """
    Safely extract a sample from data, preserving iterators when possible.
    
    Args:
        data: Input data (list, iterator, or generator)
        sample_size: Number of items to sample
    
    Returns:
        Tuple of (sample_list, reconstructed_data, is_generator) where:
        - sample_list: List of sampled items
        - reconstructed_data: Original data (List) or remaining iterator (Iterator)
        - is_generator: True if data was a generator/iterator, False otherwise
        
    Note on Return Type:
        The second element type depends on input:
        - If data is a list: returns the original list (unmodified)
        - If data is an iterator: returns the remaining unconsumed iterator
        
        For iterators, use reconstruct_iterator(sample, remaining) to rebuild
        the full sequence.
        
    Generator Handling:
        For generators/iterators, we consume items for sampling but return
        them along with the sample. The caller must use itertools.chain
        to reconstruct the full iterator: chain(sample, remaining_data).
        
        This prevents the "Iterator Consumption" problem where dry runs
        would destroy user data.
    """
    # Check if data is a generator or iterator
    is_generator = hasattr(data, '__iter__') and not hasattr(data, '__len__')
    
    if is_generator:
        # Consume sample from generator
        sample = list(itertools.islice(data, sample_size))
        # Return sample and the rest of the generator
        # Caller should use itertools.chain(sample, data) to reconstruct
        return sample, data, True
    else:
        # For lists or sequences with __len__, don't consume original
        sample = list(itertools.islice(iter(data), sample_size))
        return sample, data, False


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
        SamplingResult with timing and memory information, plus sample and
        remaining data for generator reconstruction
        
    Important:
        For generators, this function stores the consumed sample and the
        remaining iterator, allowing callers to reconstruct the full dataset
        using itertools.chain(sample, remaining_data).
    """
    # Check if function is picklable
    is_picklable = check_picklability(func)
    
    # Get sample data
    try:
        sample, remaining_data, is_gen = safe_slice_data(data, sample_size)
    except Exception as e:
        return SamplingResult(
            avg_time=0.0,
            return_size=0,
            peak_memory=0,
            sample_count=0,
            is_picklable=is_picklable,
            avg_pickle_time=0.0,
            error=e,
            sample=[],
            remaining_data=None,
            is_generator=False
        )
    
    if not sample:
        return SamplingResult(
            avg_time=0.0,
            return_size=0,
            peak_memory=0,
            sample_count=0,
            is_picklable=is_picklable,
            avg_pickle_time=0.0,
            error=ValueError("Empty data sample"),
            sample=[],
            remaining_data=remaining_data,
            is_generator=is_gen
        )
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        times = []
        return_sizes = []
        pickle_times = []
        
        for item in sample:
            # Measure execution time
            start_time = time.perf_counter()
            result = func(item)
            end_time = time.perf_counter()
            
            times.append(end_time - start_time)
            
            # Measure return object size and pickle time
            try:
                # Measure pickle serialization time (IPC overhead)
                pickle_start = time.perf_counter()
                pickled = pickle.dumps(result)
                pickle_end = time.perf_counter()
                
                pickle_times.append(pickle_end - pickle_start)
                return_sizes.append(len(pickled))
            except:
                # Fallback to sys.getsizeof if pickling fails
                return_sizes.append(sys.getsizeof(result))
                pickle_times.append(0.0)
        
        # Get peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Calculate averages
        avg_time = sum(times) / len(times) if times else 0.0
        avg_return_size = sum(return_sizes) // len(return_sizes) if return_sizes else 0
        avg_pickle_time = sum(pickle_times) / len(pickle_times) if pickle_times else 0.0
        
        return SamplingResult(
            avg_time=avg_time,
            return_size=avg_return_size,
            peak_memory=peak,
            sample_count=len(sample),
            is_picklable=is_picklable,
            avg_pickle_time=avg_pickle_time,
            error=None,
            sample=sample,
            remaining_data=remaining_data,
            is_generator=is_gen
        )
    
    except Exception as e:
        tracemalloc.stop()
        return SamplingResult(
            avg_time=0.0,
            return_size=0,
            peak_memory=0,
            sample_count=len(sample),
            is_picklable=is_picklable,
            avg_pickle_time=0.0,
            error=e,
            sample=sample,
            remaining_data=remaining_data,
            is_generator=is_gen
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


def reconstruct_iterator(sample: List, remaining_data: Iterator) -> Iterator:
    """
    Reconstruct an iterator by chaining the sample back with remaining data.
    
    This is critical for generators: after sampling, we must restore the
    consumed items so the user gets their full dataset back.
    
    Args:
        sample: Items that were consumed during sampling
        remaining_data: The rest of the iterator
    
    Returns:
        Iterator that yields sample items first, then remaining items
        
    Example:
        >>> def gen():
        ...     for i in range(10):
        ...         yield i
        >>> data = gen()
        >>> sample, rest, is_gen = safe_slice_data(data, 3)
        >>> # sample = [0, 1, 2], rest continues from 3
        >>> reconstructed = reconstruct_iterator(sample, rest)
        >>> list(reconstructed)  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    """
    return itertools.chain(sample, remaining_data)
