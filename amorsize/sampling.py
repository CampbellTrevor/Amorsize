"""
Sampling module for performing dry runs and measuring function performance.
"""

import sys
import time
import pickle
import tracemalloc
import threading
import os
import cProfile
import pstats
import io
from typing import Any, Callable, Iterator, List, Tuple, Union, Optional, Dict
import itertools

# Global caches for workload characteristic detection
# These values don't change during program execution, so we cache them
_CACHED_PARALLEL_LIBRARIES: Optional[List[str]] = None
_CACHED_ENVIRONMENT_VARS: Optional[Dict[str, str]] = None


def _clear_workload_caches():
    """
    Clear cached workload characteristic detection results.
    
    This is primarily for testing purposes to ensure tests don't
    interfere with each other's cached values.
    """
    global _CACHED_PARALLEL_LIBRARIES, _CACHED_ENVIRONMENT_VARS
    _CACHED_PARALLEL_LIBRARIES = None
    _CACHED_ENVIRONMENT_VARS = None



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
        sample: List[Any] = None,
        remaining_data: Union[List, Iterator, range, None] = None,
        is_generator: bool = False,
        data_items_picklable: bool = True,
        unpicklable_data_index: Optional[int] = None,
        data_pickle_error: Optional[Exception] = None,
        time_variance: float = 0.0,
        coefficient_of_variation: float = 0.0,
        nested_parallelism_detected: bool = False,
        parallel_libraries: List[str] = None,
        thread_activity: Dict[str, int] = None,
        workload_type: str = "cpu_bound",
        cpu_time_ratio: float = 1.0,
        function_profiler_stats: Optional[pstats.Stats] = None,
        avg_data_pickle_time: float = 0.0,
        data_size: int = 0
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
        self.data_items_picklable = data_items_picklable
        self.unpicklable_data_index = unpicklable_data_index
        self.data_pickle_error = data_pickle_error
        self.time_variance = time_variance
        self.coefficient_of_variation = coefficient_of_variation
        self.nested_parallelism_detected = nested_parallelism_detected
        self.parallel_libraries = parallel_libraries or []
        self.thread_activity = thread_activity or {}
        self.workload_type = workload_type
        self.cpu_time_ratio = cpu_time_ratio
        self.function_profiler_stats = function_profiler_stats
        self.avg_data_pickle_time = avg_data_pickle_time
        self.data_size = data_size


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


def check_data_picklability(data_items: List[Any]) -> Tuple[bool, Optional[int], Optional[Exception]]:
    """
    Check if data items can be pickled (required for multiprocessing).
    
    This function tests a sample of data items to ensure they can be serialized
    by pickle, which is necessary for multiprocessing.Pool.map() to work.
    Common unpicklable objects include: thread locks, file handles, database
    connections, lambdas, and objects with __getstate__ that raises errors.
    
    Args:
        data_items: List of data items to check
    
    Returns:
        Tuple of (all_picklable, first_unpicklable_index, exception)
        - all_picklable: True if all items can be pickled, False otherwise
        - first_unpicklable_index: Index of first unpicklable item, or None
        - exception: The exception raised during pickling, or None
        
    Examples:
        >>> data = [1, 2, 3, 4, 5]
        >>> check_data_picklability(data)
        (True, None, None)
        
        >>> import threading
        >>> data_with_lock = [1, threading.Lock(), 3]
        >>> picklable, idx, exc = check_data_picklability(data_with_lock)
        >>> picklable
        False
        >>> idx
        1
    """
    for idx, item in enumerate(data_items):
        try:
            pickle.dumps(item)
        except (pickle.PicklingError, AttributeError, TypeError) as e:
            return False, idx, e
    
    return True, None, None


def check_data_picklability_with_measurements(data_items: List[Any]) -> Tuple[bool, Optional[int], Optional[Exception], List[Tuple[float, int]]]:
    """
    Check if data items can be pickled AND measure pickle time/size for each item.
    
    This is an optimized version of check_data_picklability that also collects
    the pickle measurements, avoiding redundant pickle.dumps() calls in perform_dry_run().
    
    Memory Optimization:
        Only stores timing and size measurements, not the pickled bytes themselves.
        This significantly reduces memory usage for large objects (numpy arrays,
        dataframes, etc.) during the optimization phase.
    
    Args:
        data_items: List of data items to check
    
    Returns:
        Tuple of (all_picklable, first_unpicklable_index, exception, measurements)
        - all_picklable: True if all items can be pickled, False otherwise
        - first_unpicklable_index: Index of first unpicklable item, or None
        - exception: The exception raised during pickling, or None
        - measurements: List of (pickle_time, data_size) tuples for each item
    """
    measurements = []
    
    for idx, item in enumerate(data_items):
        try:
            data_pickle_start = time.perf_counter()
            pickled_data = pickle.dumps(item)
            data_pickle_end = time.perf_counter()
            
            pickle_time = data_pickle_end - data_pickle_start
            data_size = len(pickled_data)
            # Memory optimization: only store time and size, not the pickled bytes
            measurements.append((pickle_time, data_size))
        except (pickle.PicklingError, AttributeError, TypeError) as e:
            return False, idx, e, []
    
    return True, None, None, measurements


def detect_parallel_libraries() -> List[str]:
    """
    Detect commonly used parallel computing libraries that are currently loaded.
    
    This helps identify potential nested parallelism issues where the function
    being optimized may already use internal parallelism.
    
    Returns:
        List of detected parallel library names
        
    Libraries detected:
        - numpy (with MKL/OpenBLAS threading)
        - scipy (often uses numpy's BLAS)
        - numba (JIT compilation with threading)
        - joblib (parallel computing)
        - tensorflow (GPU/CPU parallelism)
        - torch/pytorch (GPU/CPU parallelism)
        - dask (distributed computing)
        
    Note:
        This function excludes concurrent.futures and multiprocessing.pool
        because they are loaded by Amorsize itself and don't indicate that
        the user's function uses internal parallelism.
        
    Performance:
        Results are cached after first call. Modules typically stay in
        sys.modules for the process lifetime, though they can be removed
        programmatically via module reloading. The cache should be cleared
        (via _clear_workload_caches) if modules are reloaded during testing.
    """
    global _CACHED_PARALLEL_LIBRARIES
    
    # Return cached result if available
    if _CACHED_PARALLEL_LIBRARIES is not None:
        return _CACHED_PARALLEL_LIBRARIES
    
    detected = []
    
    # Check for loaded modules
    # NOTE: We exclude concurrent.futures and multiprocessing.pool because
    # they're loaded by Amorsize itself and don't indicate user function parallelism
    parallel_libs = {
        'numpy': 'numpy',
        'scipy': 'scipy',
        'numba': 'numba',
        'joblib': 'joblib',
        'tensorflow': 'tensorflow',
        'torch': 'torch/pytorch',
        'dask': 'dask'
    }
    
    for module_name, display_name in parallel_libs.items():
        if module_name in sys.modules:
            detected.append(display_name)
    
    # Cache the result
    _CACHED_PARALLEL_LIBRARIES = detected
    return detected


def check_parallel_environment_vars() -> Dict[str, str]:
    """
    Check environment variables that control parallel library behavior.
    
    Returns:
        Dictionary of relevant environment variable names and their values
        
    Variables checked:
        - OMP_NUM_THREADS: OpenMP thread count
        - MKL_NUM_THREADS: Intel MKL thread count
        - OPENBLAS_NUM_THREADS: OpenBLAS thread count
        - NUMEXPR_NUM_THREADS: NumExpr thread count
        - VECLIB_MAXIMUM_THREADS: macOS Accelerate framework
        - NUMBA_NUM_THREADS: Numba JIT thread count
        
    Performance:
        Results are cached after first call. In typical usage, environment
        variables are set before program execution and remain constant.
        If env vars are modified programmatically during runtime via os.environ,
        call _clear_workload_caches() to force re-detection on next call.
    """
    global _CACHED_ENVIRONMENT_VARS
    
    # Return cached result if available
    if _CACHED_ENVIRONMENT_VARS is not None:
        return _CACHED_ENVIRONMENT_VARS
    
    env_vars = {
        'OMP_NUM_THREADS': os.getenv('OMP_NUM_THREADS'),
        'MKL_NUM_THREADS': os.getenv('MKL_NUM_THREADS'),
        'OPENBLAS_NUM_THREADS': os.getenv('OPENBLAS_NUM_THREADS'),
        'NUMEXPR_NUM_THREADS': os.getenv('NUMEXPR_NUM_THREADS'),
        'VECLIB_MAXIMUM_THREADS': os.getenv('VECLIB_MAXIMUM_THREADS'),
        'NUMBA_NUM_THREADS': os.getenv('NUMBA_NUM_THREADS')
    }
    
    # Return only variables that are set, and cache the result
    result = {k: v for k, v in env_vars.items() if v is not None}
    _CACHED_ENVIRONMENT_VARS = result
    return result


def estimate_internal_threads(parallel_libraries: List[str], thread_activity: Dict[str, int], env_vars: Dict[str, str]) -> int:
    """
    Estimate the number of internal threads used by the function.
    
    This function attempts to determine how many threads the function
    uses internally for parallel computation. This is important for
    avoiding thread oversubscription when combining multiprocessing
    with internally-threaded functions.
    
    Args:
        parallel_libraries: List of detected parallel libraries
        thread_activity: Dict with thread count before/during/after execution
        env_vars: Environment variables controlling thread counts
    
    Returns:
        Estimated number of internal threads per worker (minimum 1)
        
    Algorithm:
        1. Check explicit thread count from environment variables
        2. Use observed thread delta if available
        3. Use library-specific defaults:
           - NumPy/SciPy with MKL: 4 threads default
           - OpenBLAS: number of cores
           - Other libraries: 2-4 threads typical
        4. Conservative default: 4 threads if libraries detected
    """
    # Check for explicit thread limits in environment
    for var_name, var_value in env_vars.items():
        try:
            threads = int(var_value)
            if threads > 0:
                # User has explicitly set thread limit
                return threads
        except (ValueError, TypeError):
            pass
    
    # Check observed thread activity
    thread_delta = thread_activity.get('delta', 0)
    if thread_delta > 0:
        # Delta represents additional threads created beyond the baseline
        # We add 1 to estimate total threads used by the function
        # (the worker thread that runs the function + additional threads it creates)
        return thread_delta + 1
    
    # No explicit limits and no observed threads
    # Use library-specific heuristics
    if parallel_libraries:
        # Libraries detected but not explicitly limited
        # Most BLAS libraries default to 4-8 threads on modern systems
        # Conservative estimate: 4 threads
        return 4
    
    # No libraries detected - shouldn't happen but handle gracefully
    return 1


def detect_workload_type(func: Callable, sample_items: List[Any]) -> Tuple[str, float]:
    """
    Detect if a workload is CPU-bound, I/O-bound, or mixed.
    
    This function measures CPU time vs wall-clock time to determine workload characteristics.
    CPU-bound tasks use CPU constantly, while I/O-bound tasks wait for external resources.
    
    Args:
        func: Function to analyze
        sample_items: Sample data items to test with
    
    Returns:
        Tuple of (workload_type, cpu_time_ratio) where:
        - workload_type: 'cpu_bound', 'io_bound', or 'mixed'
        - cpu_time_ratio: Ratio of CPU time to wall-clock time (0.0 to 1.0+)
    
    Classification:
        - cpu_bound: cpu_time_ratio >= 0.7 (70%+ CPU utilization)
        - mixed: 0.3 <= cpu_time_ratio < 0.7 (30-70% CPU utilization)
        - io_bound: cpu_time_ratio < 0.3 (<30% CPU utilization)
    
    Rationale:
        - CPU-bound: Benefits from multiprocessing (parallel computation)
        - I/O-bound: Benefits from threading or asyncio (no GIL during I/O)
        - Mixed: May benefit from either, depends on workload balance
    """
    if not sample_items:
        # No data to analyze, assume CPU-bound (conservative)
        return "cpu_bound", 1.0
    
    try:
        import resource
        has_getrusage = True
    except ImportError:
        # Windows doesn't have resource module
        # Fall back to process_time measurement
        has_getrusage = False
    
    total_wall_time = 0.0
    total_cpu_time = 0.0
    
    for item in sample_items:
        try:
            # Measure wall-clock time
            wall_start = time.perf_counter()
            
            if has_getrusage:
                # Measure CPU time (user + system) on Unix systems
                rusage_start = resource.getrusage(resource.RUSAGE_SELF)
                cpu_start = rusage_start.ru_utime + rusage_start.ru_stime
            else:
                # Windows: use process_time (measures CPU time)
                cpu_start = time.process_time()
            
            # Execute function
            _ = func(item)
            
            # Measure end times
            wall_end = time.perf_counter()
            
            if has_getrusage:
                rusage_end = resource.getrusage(resource.RUSAGE_SELF)
                cpu_end = rusage_end.ru_utime + rusage_end.ru_stime
            else:
                cpu_end = time.process_time()
            
            # Accumulate times
            total_wall_time += (wall_end - wall_start)
            total_cpu_time += (cpu_end - cpu_start)
            
        except Exception:
            # If measurement fails for this item, skip it
            continue
    
    # Calculate CPU time ratio
    if total_wall_time > 0:
        cpu_time_ratio = total_cpu_time / total_wall_time
    else:
        # No successful measurements, assume CPU-bound
        cpu_time_ratio = 1.0
    
    # Classify workload based on CPU utilization
    # Note: cpu_time_ratio can exceed 1.0 for multi-threaded functions
    if cpu_time_ratio >= 0.7:
        workload_type = "cpu_bound"
    elif cpu_time_ratio >= 0.3:
        workload_type = "mixed"
    else:
        workload_type = "io_bound"
    
    return workload_type, cpu_time_ratio


def detect_thread_activity(func: Callable, sample_item: Any) -> Dict[str, int]:
    """
    Detect threading activity by monitoring thread count before/during/after function execution.
    
    Args:
        func: Function to test
        sample_item: Sample data item to execute function on
    
    Returns:
        Dictionary with thread count information:
        - 'before': Thread count before execution
        - 'during': Peak thread count during execution
        - 'after': Thread count after execution
        - 'delta': Maximum increase in thread count (during - before)
        
    If delta > 0, the function likely creates threads internally, indicating
    potential nested parallelism issues.
    """
    # Get baseline thread count
    threads_before = threading.active_count()
    
    try:
        # Execute function and monitor thread count
        # We sample multiple times during execution to catch transient threads
        threads_during = threads_before
        
        # For very fast functions, we may not catch thread creation
        # Execute and immediately check
        _ = func(sample_item)
        threads_peak = threading.active_count()
        threads_during = max(threads_during, threads_peak)
        
        # Check again after a brief pause to catch cleanup
        time.sleep(0.001)  # 1ms pause
        threads_after = threading.active_count()
        
    except Exception:
        # If execution fails, return baseline
        return {
            'before': threads_before,
            'during': threads_before,
            'after': threads_before,
            'delta': 0
        }
    
    return {
        'before': threads_before,
        'during': threads_during,
        'after': threads_after,
        'delta': threads_during - threads_before
    }


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
    sample_size: int = 5,
    enable_function_profiling: bool = False,
    enable_memory_tracking: bool = True
) -> SamplingResult:
    """
    Perform a dry run of the function on a small sample of data.
    
    Args:
        func: The function to test
        data: The input data
        sample_size: Number of items to sample (default: 5)
        enable_function_profiling: If True, use cProfile to profile the function
                                  execution to identify bottlenecks (default: False)
        enable_memory_tracking: If True, use tracemalloc to track peak memory
                               usage. Set to False to skip memory tracking overhead
                               for faster optimization (default: True)
    
    Returns:
        SamplingResult with timing and memory information, plus sample and
        remaining data for generator reconstruction. If enable_function_profiling
        is True, also includes function_profiler_stats with cProfile statistics.
        If enable_memory_tracking is False, peak_memory will be 0.
        
    Important:
        For generators, this function stores the consumed sample and the
        remaining iterator, allowing callers to reconstruct the full dataset
        using itertools.chain(sample, remaining_data).
        
    Performance:
        Setting enable_memory_tracking=False skips tracemalloc initialization
        and provides ~2-3% faster dry run performance. Memory-based worker
        calculation will use physical cores without memory constraints when
        tracking is disabled.
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
    
    # Check if data items are picklable AND measure pickle time/size (optimized: single pass)
    data_picklable, unpicklable_idx, pickle_err, data_measurements = check_data_picklability_with_measurements(sample)
    
    # Detect nested parallelism
    # Skip detection if AMORSIZE_TESTING environment variable is set
    # This prevents false positives in test environments where multiprocessing.pool
    # may be loaded by the test runner or other tests
    skip_nested_detection = os.environ.get('AMORSIZE_TESTING', '').lower() in ('1', 'true', 'yes')
    
    if skip_nested_detection:
        # In test mode, skip nested parallelism detection
        parallel_libs = []
        env_vars = {}
        thread_info = {'before': 0, 'during': 0, 'after': 0, 'delta': 0}
        nested_parallelism = False
    else:
        # 1. Check for parallel libraries loaded in memory
        parallel_libs = detect_parallel_libraries()
        
        # 2. Check environment variables controlling thread counts
        env_vars = check_parallel_environment_vars()
        
        # 3. Detect thread activity during function execution
        # Test with first sample item to detect threading behavior
        thread_info = detect_thread_activity(func, sample[0]) if sample else {
            'before': 0, 'during': 0, 'after': 0, 'delta': 0
        }
        
        # Determine if nested parallelism is detected
        # Criteria: 
        # - Thread count increases during execution (delta > 0)
        # - OR parallel libraries are loaded AND thread env vars not set to 1
        nested_parallelism = False
        if thread_info['delta'] > 0:
            nested_parallelism = True
        elif parallel_libs and not any(v == '1' for v in env_vars.values()):
            # Libraries present but no explicit thread limiting
            nested_parallelism = True
    
    # Detect workload type (CPU-bound vs I/O-bound)
    workload_type, cpu_time_ratio = detect_workload_type(func, sample)
    
    # Initialize cProfile if function profiling is enabled
    profiler = None
    if enable_function_profiling:
        profiler = cProfile.Profile()
    
    # Start memory tracking only if enabled
    # Lazy initialization: skip tracemalloc overhead when not needed
    # This provides ~2-3% faster dry run performance when memory tracking is disabled
    if enable_memory_tracking:
        tracemalloc.start()
    
    try:
        # Memory optimization: Pre-allocate lists with known size
        # This avoids dynamic resizing and reduces memory allocation overhead
        sample_count = len(sample)
        times = [0.0] * sample_count
        return_sizes = [0] * sample_count
        pickle_times = [0.0] * sample_count
        
        # Extract pre-measured data pickle times and sizes
        # This avoids redundant pickle.dumps() calls that were already done
        # during the picklability check
        # Memory optimization: Direct extraction instead of appending
        data_pickle_times = [pm[0] for pm in data_measurements]
        data_sizes = [pm[1] for pm in data_measurements]
        
        # Memory optimization: Use indexed assignment to pre-allocated lists
        # This eliminates append() method call overhead
        for idx, item in enumerate(sample):
            
            # Measure execution time
            start_time = time.perf_counter()
            
            # Profile function execution if enabled
            if profiler is not None:
                profiler.enable()
            
            result = func(item)
            
            if profiler is not None:
                profiler.disable()
            
            end_time = time.perf_counter()
            
            times[idx] = end_time - start_time
            
            # Measure OUTPUT result pickle time (The "Pickle Tax" - part 2: results → main)
            try:
                # Measure pickle serialization time (IPC overhead)
                pickle_start = time.perf_counter()
                pickled = pickle.dumps(result)
                pickle_end = time.perf_counter()
                
                pickle_times[idx] = pickle_end - pickle_start
                return_sizes[idx] = len(pickled)
            except:
                # Fallback to sys.getsizeof if pickling fails
                return_sizes[idx] = sys.getsizeof(result)
                pickle_times[idx] = 0.0
        
        # Get peak memory usage (only if tracking was enabled)
        if enable_memory_tracking:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        else:
            # Memory tracking disabled - return 0
            # Optimizer will fall back to using physical cores without memory constraints
            peak = 0
        
        # Calculate averages
        avg_time = sum(times) / len(times) if times else 0.0
        avg_return_size = sum(return_sizes) // len(return_sizes) if return_sizes else 0
        avg_pickle_time = sum(pickle_times) / len(pickle_times) if pickle_times else 0.0
        avg_data_pickle_time = sum(data_pickle_times) / len(data_pickle_times) if data_pickle_times else 0.0
        avg_data_size = sum(data_sizes) // len(data_sizes) if data_sizes else 0
        
        # Calculate variance and coefficient of variation for heterogeneous workload detection
        # Variance measures spread of execution times
        # Coefficient of variation (CV) = std_dev / mean, normalizes variance by mean
        time_variance = 0.0
        coefficient_of_variation = 0.0
        if len(times) > 1 and avg_time > 0:
            # Calculate variance: average of squared deviations from mean
            # Memory optimization: Use generator expression to avoid intermediate list
            time_variance = sum((t - avg_time) ** 2 for t in times) / len(times)
            
            # Calculate coefficient of variation (CV)
            # CV = (std_dev / mean) gives normalized measure of variability
            # CV < 0.3: homogeneous (consistent times)
            # CV 0.3-0.7: moderately heterogeneous
            # CV > 0.7: highly heterogeneous (varying times)
            std_dev = time_variance ** 0.5
            coefficient_of_variation = std_dev / avg_time
        
        # Process profiler stats if profiling was enabled
        profiler_stats = None
        if profiler is not None:
            # Create Stats object from profiler
            profiler_stats = pstats.Stats(profiler)
            # Strip directory paths for cleaner output
            profiler_stats.strip_dirs()
        
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
            is_generator=is_gen,
            data_items_picklable=data_picklable,
            unpicklable_data_index=unpicklable_idx,
            data_pickle_error=pickle_err,
            time_variance=time_variance,
            coefficient_of_variation=coefficient_of_variation,
            nested_parallelism_detected=nested_parallelism,
            parallel_libraries=parallel_libs,
            thread_activity=thread_info,
            workload_type=workload_type,
            cpu_time_ratio=cpu_time_ratio,
            function_profiler_stats=profiler_stats,
            avg_data_pickle_time=avg_data_pickle_time,
            data_size=avg_data_size
        )
    
    except Exception as e:
        # Cleanup: stop memory tracking if it was started
        if enable_memory_tracking:
            try:
                tracemalloc.stop()
            except:
                pass  # Already stopped or never started
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
            is_generator=is_gen,
            data_items_picklable=data_picklable,
            unpicklable_data_index=unpicklable_idx,
            data_pickle_error=pickle_err,
            workload_type="cpu_bound",
            cpu_time_ratio=1.0
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


def reconstruct_iterator(sample: List[Any], remaining_data: Union[Iterator, List, range]) -> Iterator:
    """
    Reconstruct an iterator by chaining the sample back with remaining data.
    
    This is critical for generators: after sampling, we must restore the
    consumed items so the user gets their full dataset back.
    
    Args:
        sample: Items that were consumed during sampling
        remaining_data: The rest of the iterator, or full list/range
    
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
