"""
Watch mode for continuous monitoring of workload optimization.

This module provides functionality to continuously monitor a function's performance
over time, detecting changes in optimal parallelization parameters and alerting
when performance characteristics shift.
"""

import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterator, List, Optional, Union

from .optimizer import OptimizationResult, optimize


# Constants for change detection thresholds
MIN_SPEEDUP_FOR_RATIO = 0.01  # Minimum speedup to avoid division by zero in ratio calculation
DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD = 0.5  # 50% change threshold for chunksize alerts

# Constants for output formatting
MAX_WARNINGS_TO_DISPLAY = 2  # Maximum number of warnings to show in verbose mode
WARNING_TRUNCATE_LENGTH = 100  # Character limit for truncating long warnings
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


@dataclass
class WatchSnapshot:
    """A snapshot of optimization results at a specific point in time."""
    timestamp: datetime
    result: OptimizationResult
    iteration: int


class WatchMonitor:
    """
    Continuous monitoring system for workload optimization.
    
    Periodically re-optimizes a function and alerts when recommendations change
    significantly, indicating workload drift or system changes.
    """
    
    def xǁWatchMonitorǁ__init____mutmut_orig(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_1(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 61.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_2(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 2,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_3(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 1.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_4(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = True,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_5(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 6,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_6(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 1.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_7(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = True,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_8(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = True
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_9(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = None
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_10(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = None
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_11(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = None
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_12(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = None
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_13(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = None
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_14(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = None
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_15(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = None
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_16(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = None
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_17(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = None
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_18(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = None
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_19(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = None
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_20(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = None
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_21(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = None
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_22(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = True
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_23(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = None
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_24(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 1
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_25(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = ""
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ__init____mutmut_26(
        self,
        func: Callable[[Any], Any],
        data: Union[List, Iterator],
        interval: float = 60.0,
        change_threshold_n_jobs: int = 1,
        change_threshold_speedup: float = 0.2,
        change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
        verbose: bool = False,
        sample_size: int = 5,
        target_chunk_duration: float = 0.2,
        enable_profiling: bool = False,
        use_cache: bool = False
    ):
        """
        Initialize the watch monitor.
        
        Args:
            func: Function to monitor
            data: Input data for the function
            interval: Time between optimization checks in seconds (default: 60s)
            change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
            change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2 = 20%)
            change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5 = 50%)
            verbose: Enable verbose output
            sample_size: Number of samples for dry run
            target_chunk_duration: Target chunk duration for optimization
            enable_profiling: Enable profiling during optimization (default: False)
            use_cache: Use optimization cache (default: False, recommended for watch mode)
        """
        self.func = func
        self.data = data
        self.interval = interval
        self.change_threshold_n_jobs = change_threshold_n_jobs
        self.change_threshold_speedup = change_threshold_speedup
        self.change_threshold_chunksize = change_threshold_chunksize
        self.verbose = verbose
        self.sample_size = sample_size
        self.target_chunk_duration = target_chunk_duration
        self.enable_profiling = enable_profiling
        self.use_cache = use_cache
        
        self.snapshots: List[WatchSnapshot] = []
        self.running = False
        self.iteration = 0
        
        # Store original signal handlers to restore later
        self._original_sigint_handler = None
        self._original_sigterm_handler = ""
    
    xǁWatchMonitorǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ__init____mutmut_1': xǁWatchMonitorǁ__init____mutmut_1, 
        'xǁWatchMonitorǁ__init____mutmut_2': xǁWatchMonitorǁ__init____mutmut_2, 
        'xǁWatchMonitorǁ__init____mutmut_3': xǁWatchMonitorǁ__init____mutmut_3, 
        'xǁWatchMonitorǁ__init____mutmut_4': xǁWatchMonitorǁ__init____mutmut_4, 
        'xǁWatchMonitorǁ__init____mutmut_5': xǁWatchMonitorǁ__init____mutmut_5, 
        'xǁWatchMonitorǁ__init____mutmut_6': xǁWatchMonitorǁ__init____mutmut_6, 
        'xǁWatchMonitorǁ__init____mutmut_7': xǁWatchMonitorǁ__init____mutmut_7, 
        'xǁWatchMonitorǁ__init____mutmut_8': xǁWatchMonitorǁ__init____mutmut_8, 
        'xǁWatchMonitorǁ__init____mutmut_9': xǁWatchMonitorǁ__init____mutmut_9, 
        'xǁWatchMonitorǁ__init____mutmut_10': xǁWatchMonitorǁ__init____mutmut_10, 
        'xǁWatchMonitorǁ__init____mutmut_11': xǁWatchMonitorǁ__init____mutmut_11, 
        'xǁWatchMonitorǁ__init____mutmut_12': xǁWatchMonitorǁ__init____mutmut_12, 
        'xǁWatchMonitorǁ__init____mutmut_13': xǁWatchMonitorǁ__init____mutmut_13, 
        'xǁWatchMonitorǁ__init____mutmut_14': xǁWatchMonitorǁ__init____mutmut_14, 
        'xǁWatchMonitorǁ__init____mutmut_15': xǁWatchMonitorǁ__init____mutmut_15, 
        'xǁWatchMonitorǁ__init____mutmut_16': xǁWatchMonitorǁ__init____mutmut_16, 
        'xǁWatchMonitorǁ__init____mutmut_17': xǁWatchMonitorǁ__init____mutmut_17, 
        'xǁWatchMonitorǁ__init____mutmut_18': xǁWatchMonitorǁ__init____mutmut_18, 
        'xǁWatchMonitorǁ__init____mutmut_19': xǁWatchMonitorǁ__init____mutmut_19, 
        'xǁWatchMonitorǁ__init____mutmut_20': xǁWatchMonitorǁ__init____mutmut_20, 
        'xǁWatchMonitorǁ__init____mutmut_21': xǁWatchMonitorǁ__init____mutmut_21, 
        'xǁWatchMonitorǁ__init____mutmut_22': xǁWatchMonitorǁ__init____mutmut_22, 
        'xǁWatchMonitorǁ__init____mutmut_23': xǁWatchMonitorǁ__init____mutmut_23, 
        'xǁWatchMonitorǁ__init____mutmut_24': xǁWatchMonitorǁ__init____mutmut_24, 
        'xǁWatchMonitorǁ__init____mutmut_25': xǁWatchMonitorǁ__init____mutmut_25, 
        'xǁWatchMonitorǁ__init____mutmut_26': xǁWatchMonitorǁ__init____mutmut_26
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁWatchMonitorǁ__init____mutmut_orig)
    xǁWatchMonitorǁ__init____mutmut_orig.__name__ = 'xǁWatchMonitorǁ__init__'
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_orig(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_1(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = None
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_2(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(None, self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_3(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, None)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_4(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_5(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, )
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_6(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm_handler = None
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_7(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(None, self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_8(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, None)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_9(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(self._handle_interrupt)
    
    def xǁWatchMonitorǁ_setup_signal_handlers__mutmut_10(self):
        """Set up signal handlers and store originals for later restoration."""
        self._original_sigint_handler = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm_handler = signal.signal(signal.SIGTERM, )
    
    xǁWatchMonitorǁ_setup_signal_handlers__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_1': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_1, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_2': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_2, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_3': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_3, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_4': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_4, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_5': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_5, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_6': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_6, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_7': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_7, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_8': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_8, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_9': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_9, 
        'xǁWatchMonitorǁ_setup_signal_handlers__mutmut_10': xǁWatchMonitorǁ_setup_signal_handlers__mutmut_10
    }
    
    def _setup_signal_handlers(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ_setup_signal_handlers__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ_setup_signal_handlers__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _setup_signal_handlers.__signature__ = _mutmut_signature(xǁWatchMonitorǁ_setup_signal_handlers__mutmut_orig)
    xǁWatchMonitorǁ_setup_signal_handlers__mutmut_orig.__name__ = 'xǁWatchMonitorǁ_setup_signal_handlers'
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_orig(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_1(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_2(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(None, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_3(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, None)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_4(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_5(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, )
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_6(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is None:
            signal.signal(signal.SIGTERM, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_7(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(None, self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_8(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, None)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_9(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(self._original_sigterm_handler)
    
    def xǁWatchMonitorǁ_restore_signal_handlers__mutmut_10(self):
        """Restore original signal handlers."""
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
        if self._original_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, )
    
    xǁWatchMonitorǁ_restore_signal_handlers__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_1': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_1, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_2': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_2, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_3': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_3, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_4': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_4, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_5': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_5, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_6': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_6, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_7': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_7, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_8': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_8, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_9': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_9, 
        'xǁWatchMonitorǁ_restore_signal_handlers__mutmut_10': xǁWatchMonitorǁ_restore_signal_handlers__mutmut_10
    }
    
    def _restore_signal_handlers(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ_restore_signal_handlers__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ_restore_signal_handlers__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _restore_signal_handlers.__signature__ = _mutmut_signature(xǁWatchMonitorǁ_restore_signal_handlers__mutmut_orig)
    xǁWatchMonitorǁ_restore_signal_handlers__mutmut_orig.__name__ = 'xǁWatchMonitorǁ_restore_signal_handlers'
    
    def xǁWatchMonitorǁ_handle_interrupt__mutmut_orig(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\n\nShutting down watch mode...")
        self.running = False
    
    def xǁWatchMonitorǁ_handle_interrupt__mutmut_1(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print(None)
        self.running = False
    
    def xǁWatchMonitorǁ_handle_interrupt__mutmut_2(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("XX\n\nShutting down watch mode...XX")
        self.running = False
    
    def xǁWatchMonitorǁ_handle_interrupt__mutmut_3(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\n\nshutting down watch mode...")
        self.running = False
    
    def xǁWatchMonitorǁ_handle_interrupt__mutmut_4(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\n\nSHUTTING DOWN WATCH MODE...")
        self.running = False
    
    def xǁWatchMonitorǁ_handle_interrupt__mutmut_5(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\n\nShutting down watch mode...")
        self.running = None
    
    def xǁWatchMonitorǁ_handle_interrupt__mutmut_6(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\n\nShutting down watch mode...")
        self.running = True
    
    xǁWatchMonitorǁ_handle_interrupt__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ_handle_interrupt__mutmut_1': xǁWatchMonitorǁ_handle_interrupt__mutmut_1, 
        'xǁWatchMonitorǁ_handle_interrupt__mutmut_2': xǁWatchMonitorǁ_handle_interrupt__mutmut_2, 
        'xǁWatchMonitorǁ_handle_interrupt__mutmut_3': xǁWatchMonitorǁ_handle_interrupt__mutmut_3, 
        'xǁWatchMonitorǁ_handle_interrupt__mutmut_4': xǁWatchMonitorǁ_handle_interrupt__mutmut_4, 
        'xǁWatchMonitorǁ_handle_interrupt__mutmut_5': xǁWatchMonitorǁ_handle_interrupt__mutmut_5, 
        'xǁWatchMonitorǁ_handle_interrupt__mutmut_6': xǁWatchMonitorǁ_handle_interrupt__mutmut_6
    }
    
    def _handle_interrupt(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ_handle_interrupt__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ_handle_interrupt__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _handle_interrupt.__signature__ = _mutmut_signature(xǁWatchMonitorǁ_handle_interrupt__mutmut_orig)
    xǁWatchMonitorǁ_handle_interrupt__mutmut_orig.__name__ = 'xǁWatchMonitorǁ_handle_interrupt'
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_orig(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_1(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = None
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_2(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(None) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_3(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs + prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_4(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) > self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_5(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                None
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_6(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs + prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_7(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = None
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_8(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) * max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_9(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(None) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_10(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup + prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_11(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(None, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_12(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, None)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_13(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_14(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, )
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_15(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio > self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_16(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                None
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_17(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio / 100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_18(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*101:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_19(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize >= 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_20(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 1:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_21(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = None
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_22(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) * prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_23(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(None) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_24(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize + prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_25(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio > self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_26(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    None
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_27(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio / 100:.0f}% change)"
                )
        
        return changes
    
    def xǁWatchMonitorǁ_detect_changes__mutmut_28(self, prev: OptimizationResult, curr: OptimizationResult) -> List[str]:
        """
        Detect significant changes between two optimization results.
        
        Args:
            prev: Previous optimization result
            curr: Current optimization result
            
        Returns:
            List of detected changes (empty if no significant changes)
        """
        changes = []
        
        # Check n_jobs change
        if abs(curr.n_jobs - prev.n_jobs) >= self.change_threshold_n_jobs:
            changes.append(
                f"n_jobs changed: {prev.n_jobs} → {curr.n_jobs} "
                f"(Δ{curr.n_jobs - prev.n_jobs:+d})"
            )
        
        # Check speedup change
        speedup_ratio = abs(curr.estimated_speedup - prev.estimated_speedup) / max(prev.estimated_speedup, MIN_SPEEDUP_FOR_RATIO)
        if speedup_ratio >= self.change_threshold_speedup:
            changes.append(
                f"Speedup changed: {prev.estimated_speedup:.2f}x → {curr.estimated_speedup:.2f}x "
                f"({speedup_ratio*100:.1f}% change)"
            )
        
        # Check chunksize change (only alert if significant relative change)
        if prev.chunksize > 0:
            chunksize_ratio = abs(curr.chunksize - prev.chunksize) / prev.chunksize
            if chunksize_ratio >= self.change_threshold_chunksize:
                changes.append(
                    f"Chunksize changed: {prev.chunksize} → {curr.chunksize} "
                    f"({chunksize_ratio*101:.0f}% change)"
                )
        
        return changes
    
    xǁWatchMonitorǁ_detect_changes__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ_detect_changes__mutmut_1': xǁWatchMonitorǁ_detect_changes__mutmut_1, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_2': xǁWatchMonitorǁ_detect_changes__mutmut_2, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_3': xǁWatchMonitorǁ_detect_changes__mutmut_3, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_4': xǁWatchMonitorǁ_detect_changes__mutmut_4, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_5': xǁWatchMonitorǁ_detect_changes__mutmut_5, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_6': xǁWatchMonitorǁ_detect_changes__mutmut_6, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_7': xǁWatchMonitorǁ_detect_changes__mutmut_7, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_8': xǁWatchMonitorǁ_detect_changes__mutmut_8, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_9': xǁWatchMonitorǁ_detect_changes__mutmut_9, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_10': xǁWatchMonitorǁ_detect_changes__mutmut_10, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_11': xǁWatchMonitorǁ_detect_changes__mutmut_11, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_12': xǁWatchMonitorǁ_detect_changes__mutmut_12, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_13': xǁWatchMonitorǁ_detect_changes__mutmut_13, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_14': xǁWatchMonitorǁ_detect_changes__mutmut_14, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_15': xǁWatchMonitorǁ_detect_changes__mutmut_15, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_16': xǁWatchMonitorǁ_detect_changes__mutmut_16, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_17': xǁWatchMonitorǁ_detect_changes__mutmut_17, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_18': xǁWatchMonitorǁ_detect_changes__mutmut_18, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_19': xǁWatchMonitorǁ_detect_changes__mutmut_19, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_20': xǁWatchMonitorǁ_detect_changes__mutmut_20, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_21': xǁWatchMonitorǁ_detect_changes__mutmut_21, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_22': xǁWatchMonitorǁ_detect_changes__mutmut_22, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_23': xǁWatchMonitorǁ_detect_changes__mutmut_23, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_24': xǁWatchMonitorǁ_detect_changes__mutmut_24, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_25': xǁWatchMonitorǁ_detect_changes__mutmut_25, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_26': xǁWatchMonitorǁ_detect_changes__mutmut_26, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_27': xǁWatchMonitorǁ_detect_changes__mutmut_27, 
        'xǁWatchMonitorǁ_detect_changes__mutmut_28': xǁWatchMonitorǁ_detect_changes__mutmut_28
    }
    
    def _detect_changes(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ_detect_changes__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ_detect_changes__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _detect_changes.__signature__ = _mutmut_signature(xǁWatchMonitorǁ_detect_changes__mutmut_orig)
    xǁWatchMonitorǁ_detect_changes__mutmut_orig.__name__ = 'xǁWatchMonitorǁ_detect_changes'
    
    def xǁWatchMonitorǁ_print_header__mutmut_orig(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_1(self):
        """Print the monitoring header."""
        print(None)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_2(self):
        """Print the monitoring header."""
        print("=" / 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_3(self):
        """Print the monitoring header."""
        print("XX=XX" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_4(self):
        """Print the monitoring header."""
        print("=" * 81)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_5(self):
        """Print the monitoring header."""
        print("=" * 80)
        print(None)
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_6(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("XX🔍 AMORSIZE WATCH MODE - Continuous Optimization MonitoringXX")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_7(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 amorsize watch mode - continuous optimization monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_8(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - CONTINUOUS OPTIMIZATION MONITORING")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_9(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print(None)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_10(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" / 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_11(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("XX=XX" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_12(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 81)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_13(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(None)
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_14(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(None)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_15(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(None)
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_16(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime(None)}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_17(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('XX%Y-%m-%d %H:%M:%SXX')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_18(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%y-%m-%d %h:%m:%s')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_19(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%M-%D %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_20(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(None)
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_21(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("XX\nPress Ctrl+C to stop monitoring\nXX")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_22(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\npress ctrl+c to stop monitoring\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_23(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPRESS CTRL+C TO STOP MONITORING\n")
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_24(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print(None)
    
    def xǁWatchMonitorǁ_print_header__mutmut_25(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" / 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_26(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("XX-XX" * 80)
    
    def xǁWatchMonitorǁ_print_header__mutmut_27(self):
        """Print the monitoring header."""
        print("=" * 80)
        print("🔍 AMORSIZE WATCH MODE - Continuous Optimization Monitoring")
        print("=" * 80)
        print(f"Function: {self.func.__module__}.{self.func.__name__}")
        print(f"Interval: {self.interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nPress Ctrl+C to stop monitoring\n")
        print("-" * 81)
    
    xǁWatchMonitorǁ_print_header__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ_print_header__mutmut_1': xǁWatchMonitorǁ_print_header__mutmut_1, 
        'xǁWatchMonitorǁ_print_header__mutmut_2': xǁWatchMonitorǁ_print_header__mutmut_2, 
        'xǁWatchMonitorǁ_print_header__mutmut_3': xǁWatchMonitorǁ_print_header__mutmut_3, 
        'xǁWatchMonitorǁ_print_header__mutmut_4': xǁWatchMonitorǁ_print_header__mutmut_4, 
        'xǁWatchMonitorǁ_print_header__mutmut_5': xǁWatchMonitorǁ_print_header__mutmut_5, 
        'xǁWatchMonitorǁ_print_header__mutmut_6': xǁWatchMonitorǁ_print_header__mutmut_6, 
        'xǁWatchMonitorǁ_print_header__mutmut_7': xǁWatchMonitorǁ_print_header__mutmut_7, 
        'xǁWatchMonitorǁ_print_header__mutmut_8': xǁWatchMonitorǁ_print_header__mutmut_8, 
        'xǁWatchMonitorǁ_print_header__mutmut_9': xǁWatchMonitorǁ_print_header__mutmut_9, 
        'xǁWatchMonitorǁ_print_header__mutmut_10': xǁWatchMonitorǁ_print_header__mutmut_10, 
        'xǁWatchMonitorǁ_print_header__mutmut_11': xǁWatchMonitorǁ_print_header__mutmut_11, 
        'xǁWatchMonitorǁ_print_header__mutmut_12': xǁWatchMonitorǁ_print_header__mutmut_12, 
        'xǁWatchMonitorǁ_print_header__mutmut_13': xǁWatchMonitorǁ_print_header__mutmut_13, 
        'xǁWatchMonitorǁ_print_header__mutmut_14': xǁWatchMonitorǁ_print_header__mutmut_14, 
        'xǁWatchMonitorǁ_print_header__mutmut_15': xǁWatchMonitorǁ_print_header__mutmut_15, 
        'xǁWatchMonitorǁ_print_header__mutmut_16': xǁWatchMonitorǁ_print_header__mutmut_16, 
        'xǁWatchMonitorǁ_print_header__mutmut_17': xǁWatchMonitorǁ_print_header__mutmut_17, 
        'xǁWatchMonitorǁ_print_header__mutmut_18': xǁWatchMonitorǁ_print_header__mutmut_18, 
        'xǁWatchMonitorǁ_print_header__mutmut_19': xǁWatchMonitorǁ_print_header__mutmut_19, 
        'xǁWatchMonitorǁ_print_header__mutmut_20': xǁWatchMonitorǁ_print_header__mutmut_20, 
        'xǁWatchMonitorǁ_print_header__mutmut_21': xǁWatchMonitorǁ_print_header__mutmut_21, 
        'xǁWatchMonitorǁ_print_header__mutmut_22': xǁWatchMonitorǁ_print_header__mutmut_22, 
        'xǁWatchMonitorǁ_print_header__mutmut_23': xǁWatchMonitorǁ_print_header__mutmut_23, 
        'xǁWatchMonitorǁ_print_header__mutmut_24': xǁWatchMonitorǁ_print_header__mutmut_24, 
        'xǁWatchMonitorǁ_print_header__mutmut_25': xǁWatchMonitorǁ_print_header__mutmut_25, 
        'xǁWatchMonitorǁ_print_header__mutmut_26': xǁWatchMonitorǁ_print_header__mutmut_26, 
        'xǁWatchMonitorǁ_print_header__mutmut_27': xǁWatchMonitorǁ_print_header__mutmut_27
    }
    
    def _print_header(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ_print_header__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ_print_header__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _print_header.__signature__ = _mutmut_signature(xǁWatchMonitorǁ_print_header__mutmut_orig)
    xǁWatchMonitorǁ_print_header__mutmut_orig.__name__ = 'xǁWatchMonitorǁ_print_header'
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_orig(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_1(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = None
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_2(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime(None)
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_3(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('XX%H:%M:%SXX')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_4(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%h:%m:%s')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_5(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = None
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_6(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(None)
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_7(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(None)
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_8(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print(None)
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_9(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("XX\n  ⚠️  CHANGES DETECTED:XX")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_10(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  changes detected:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_11(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(None)
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_12(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings or self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_13(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print(None)
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_14(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("XX\n  Warnings:XX")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_15(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_16(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  WARNINGS:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_17(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(None)
        
        print("-" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_18(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print(None)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_19(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" / 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_20(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("XX-XX" * 80)
    
    def xǁWatchMonitorǁ_print_snapshot__mutmut_21(self, snapshot: WatchSnapshot, changes: Optional[List[str]] = None):
        """
        Print a snapshot of optimization results.
        
        Args:
            snapshot: The snapshot to print
            changes: Optional list of detected changes to highlight
        """
        timestamp_str = snapshot.timestamp.strftime('%H:%M:%S')
        result = snapshot.result
        
        # Print timestamp and iteration
        print(f"\n[{timestamp_str}] Iteration #{snapshot.iteration}")
        
        # Print main results
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}, "
              f"speedup={result.estimated_speedup:.2f}x")
        
        # Print changes if any
        if changes:
            print("\n  ⚠️  CHANGES DETECTED:")
            for change in changes:
                print(f"    • {change}")
        
        # Print warnings if any
        if result.warnings and self.verbose:
            print("\n  Warnings:")
            for warning in result.warnings[:MAX_WARNINGS_TO_DISPLAY]:
                print(f"    - {warning[:WARNING_TRUNCATE_LENGTH]}")
        
        print("-" * 81)
    
    xǁWatchMonitorǁ_print_snapshot__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ_print_snapshot__mutmut_1': xǁWatchMonitorǁ_print_snapshot__mutmut_1, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_2': xǁWatchMonitorǁ_print_snapshot__mutmut_2, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_3': xǁWatchMonitorǁ_print_snapshot__mutmut_3, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_4': xǁWatchMonitorǁ_print_snapshot__mutmut_4, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_5': xǁWatchMonitorǁ_print_snapshot__mutmut_5, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_6': xǁWatchMonitorǁ_print_snapshot__mutmut_6, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_7': xǁWatchMonitorǁ_print_snapshot__mutmut_7, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_8': xǁWatchMonitorǁ_print_snapshot__mutmut_8, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_9': xǁWatchMonitorǁ_print_snapshot__mutmut_9, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_10': xǁWatchMonitorǁ_print_snapshot__mutmut_10, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_11': xǁWatchMonitorǁ_print_snapshot__mutmut_11, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_12': xǁWatchMonitorǁ_print_snapshot__mutmut_12, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_13': xǁWatchMonitorǁ_print_snapshot__mutmut_13, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_14': xǁWatchMonitorǁ_print_snapshot__mutmut_14, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_15': xǁWatchMonitorǁ_print_snapshot__mutmut_15, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_16': xǁWatchMonitorǁ_print_snapshot__mutmut_16, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_17': xǁWatchMonitorǁ_print_snapshot__mutmut_17, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_18': xǁWatchMonitorǁ_print_snapshot__mutmut_18, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_19': xǁWatchMonitorǁ_print_snapshot__mutmut_19, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_20': xǁWatchMonitorǁ_print_snapshot__mutmut_20, 
        'xǁWatchMonitorǁ_print_snapshot__mutmut_21': xǁWatchMonitorǁ_print_snapshot__mutmut_21
    }
    
    def _print_snapshot(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ_print_snapshot__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ_print_snapshot__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _print_snapshot.__signature__ = _mutmut_signature(xǁWatchMonitorǁ_print_snapshot__mutmut_orig)
    xǁWatchMonitorǁ_print_snapshot__mutmut_orig.__name__ = 'xǁWatchMonitorǁ_print_snapshot'
    
    def xǁWatchMonitorǁ_print_summary__mutmut_orig(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_1(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) <= 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_2(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 3:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_3(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print(None)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_4(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" - "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_5(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("XX\nXX" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_6(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" / 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_7(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "XX=XX" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_8(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 81)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_9(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print(None)
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_10(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("XX📊 WATCH MODE SUMMARYXX")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_11(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 watch mode summary")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_12(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print(None)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_13(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" / 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_14(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("XX=XX" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_15(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 81)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_16(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = None
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_17(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[1].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_18(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = None
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_19(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[+1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_20(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-2].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_21(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(None)
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_22(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp + self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_23(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[+1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_24(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-2].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_25(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[1].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_26(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(None)
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_27(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(None)
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_28(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = None
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_29(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = None
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_30(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = None
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_31(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) != 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_32(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 2
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_33(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = None
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_34(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) + min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_35(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(None) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_36(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(None)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_37(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(None)
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_38(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(None)
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_39(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'XX✓ StableXX' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_40(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_41(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ STABLE' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_42(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else 'XX⚠ VariableXX'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_43(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_44(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ VARIABLE'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_45(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(None)
        
        print("=" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_46(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print(None)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_47(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" / 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_48(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("XX=XX" * 80)
    
    def xǁWatchMonitorǁ_print_summary__mutmut_49(self):
        """Print summary statistics at the end of monitoring."""
        if len(self.snapshots) < 2:
            return
        
        print("\n" + "=" * 80)
        print("📊 WATCH MODE SUMMARY")
        print("=" * 80)
        
        first = self.snapshots[0].result
        last = self.snapshots[-1].result
        
        print(f"Duration: {len(self.snapshots)} iterations over "
              f"{(self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds():.0f}s")
        
        print(f"\nInitial:  n_jobs={first.n_jobs}, chunksize={first.chunksize}, "
              f"speedup={first.estimated_speedup:.2f}x")
        print(f"Final:    n_jobs={last.n_jobs}, chunksize={last.chunksize}, "
              f"speedup={last.estimated_speedup:.2f}x")
        
        # Calculate stability metrics
        n_jobs_values = [s.result.n_jobs for s in self.snapshots]
        speedup_values = [s.result.estimated_speedup for s in self.snapshots]
        
        n_jobs_stable = len(set(n_jobs_values)) == 1
        speedup_variance = max(speedup_values) - min(speedup_values)
        
        print(f"\nStability:")
        print(f"  n_jobs: {'✓ Stable' if n_jobs_stable else '⚠ Variable'}")
        print(f"  Speedup variance: {speedup_variance:.2f}x")
        
        print("=" * 81)
    
    xǁWatchMonitorǁ_print_summary__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁ_print_summary__mutmut_1': xǁWatchMonitorǁ_print_summary__mutmut_1, 
        'xǁWatchMonitorǁ_print_summary__mutmut_2': xǁWatchMonitorǁ_print_summary__mutmut_2, 
        'xǁWatchMonitorǁ_print_summary__mutmut_3': xǁWatchMonitorǁ_print_summary__mutmut_3, 
        'xǁWatchMonitorǁ_print_summary__mutmut_4': xǁWatchMonitorǁ_print_summary__mutmut_4, 
        'xǁWatchMonitorǁ_print_summary__mutmut_5': xǁWatchMonitorǁ_print_summary__mutmut_5, 
        'xǁWatchMonitorǁ_print_summary__mutmut_6': xǁWatchMonitorǁ_print_summary__mutmut_6, 
        'xǁWatchMonitorǁ_print_summary__mutmut_7': xǁWatchMonitorǁ_print_summary__mutmut_7, 
        'xǁWatchMonitorǁ_print_summary__mutmut_8': xǁWatchMonitorǁ_print_summary__mutmut_8, 
        'xǁWatchMonitorǁ_print_summary__mutmut_9': xǁWatchMonitorǁ_print_summary__mutmut_9, 
        'xǁWatchMonitorǁ_print_summary__mutmut_10': xǁWatchMonitorǁ_print_summary__mutmut_10, 
        'xǁWatchMonitorǁ_print_summary__mutmut_11': xǁWatchMonitorǁ_print_summary__mutmut_11, 
        'xǁWatchMonitorǁ_print_summary__mutmut_12': xǁWatchMonitorǁ_print_summary__mutmut_12, 
        'xǁWatchMonitorǁ_print_summary__mutmut_13': xǁWatchMonitorǁ_print_summary__mutmut_13, 
        'xǁWatchMonitorǁ_print_summary__mutmut_14': xǁWatchMonitorǁ_print_summary__mutmut_14, 
        'xǁWatchMonitorǁ_print_summary__mutmut_15': xǁWatchMonitorǁ_print_summary__mutmut_15, 
        'xǁWatchMonitorǁ_print_summary__mutmut_16': xǁWatchMonitorǁ_print_summary__mutmut_16, 
        'xǁWatchMonitorǁ_print_summary__mutmut_17': xǁWatchMonitorǁ_print_summary__mutmut_17, 
        'xǁWatchMonitorǁ_print_summary__mutmut_18': xǁWatchMonitorǁ_print_summary__mutmut_18, 
        'xǁWatchMonitorǁ_print_summary__mutmut_19': xǁWatchMonitorǁ_print_summary__mutmut_19, 
        'xǁWatchMonitorǁ_print_summary__mutmut_20': xǁWatchMonitorǁ_print_summary__mutmut_20, 
        'xǁWatchMonitorǁ_print_summary__mutmut_21': xǁWatchMonitorǁ_print_summary__mutmut_21, 
        'xǁWatchMonitorǁ_print_summary__mutmut_22': xǁWatchMonitorǁ_print_summary__mutmut_22, 
        'xǁWatchMonitorǁ_print_summary__mutmut_23': xǁWatchMonitorǁ_print_summary__mutmut_23, 
        'xǁWatchMonitorǁ_print_summary__mutmut_24': xǁWatchMonitorǁ_print_summary__mutmut_24, 
        'xǁWatchMonitorǁ_print_summary__mutmut_25': xǁWatchMonitorǁ_print_summary__mutmut_25, 
        'xǁWatchMonitorǁ_print_summary__mutmut_26': xǁWatchMonitorǁ_print_summary__mutmut_26, 
        'xǁWatchMonitorǁ_print_summary__mutmut_27': xǁWatchMonitorǁ_print_summary__mutmut_27, 
        'xǁWatchMonitorǁ_print_summary__mutmut_28': xǁWatchMonitorǁ_print_summary__mutmut_28, 
        'xǁWatchMonitorǁ_print_summary__mutmut_29': xǁWatchMonitorǁ_print_summary__mutmut_29, 
        'xǁWatchMonitorǁ_print_summary__mutmut_30': xǁWatchMonitorǁ_print_summary__mutmut_30, 
        'xǁWatchMonitorǁ_print_summary__mutmut_31': xǁWatchMonitorǁ_print_summary__mutmut_31, 
        'xǁWatchMonitorǁ_print_summary__mutmut_32': xǁWatchMonitorǁ_print_summary__mutmut_32, 
        'xǁWatchMonitorǁ_print_summary__mutmut_33': xǁWatchMonitorǁ_print_summary__mutmut_33, 
        'xǁWatchMonitorǁ_print_summary__mutmut_34': xǁWatchMonitorǁ_print_summary__mutmut_34, 
        'xǁWatchMonitorǁ_print_summary__mutmut_35': xǁWatchMonitorǁ_print_summary__mutmut_35, 
        'xǁWatchMonitorǁ_print_summary__mutmut_36': xǁWatchMonitorǁ_print_summary__mutmut_36, 
        'xǁWatchMonitorǁ_print_summary__mutmut_37': xǁWatchMonitorǁ_print_summary__mutmut_37, 
        'xǁWatchMonitorǁ_print_summary__mutmut_38': xǁWatchMonitorǁ_print_summary__mutmut_38, 
        'xǁWatchMonitorǁ_print_summary__mutmut_39': xǁWatchMonitorǁ_print_summary__mutmut_39, 
        'xǁWatchMonitorǁ_print_summary__mutmut_40': xǁWatchMonitorǁ_print_summary__mutmut_40, 
        'xǁWatchMonitorǁ_print_summary__mutmut_41': xǁWatchMonitorǁ_print_summary__mutmut_41, 
        'xǁWatchMonitorǁ_print_summary__mutmut_42': xǁWatchMonitorǁ_print_summary__mutmut_42, 
        'xǁWatchMonitorǁ_print_summary__mutmut_43': xǁWatchMonitorǁ_print_summary__mutmut_43, 
        'xǁWatchMonitorǁ_print_summary__mutmut_44': xǁWatchMonitorǁ_print_summary__mutmut_44, 
        'xǁWatchMonitorǁ_print_summary__mutmut_45': xǁWatchMonitorǁ_print_summary__mutmut_45, 
        'xǁWatchMonitorǁ_print_summary__mutmut_46': xǁWatchMonitorǁ_print_summary__mutmut_46, 
        'xǁWatchMonitorǁ_print_summary__mutmut_47': xǁWatchMonitorǁ_print_summary__mutmut_47, 
        'xǁWatchMonitorǁ_print_summary__mutmut_48': xǁWatchMonitorǁ_print_summary__mutmut_48, 
        'xǁWatchMonitorǁ_print_summary__mutmut_49': xǁWatchMonitorǁ_print_summary__mutmut_49
    }
    
    def _print_summary(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁ_print_summary__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁ_print_summary__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _print_summary.__signature__ = _mutmut_signature(xǁWatchMonitorǁ_print_summary__mutmut_orig)
    xǁWatchMonitorǁ_print_summary__mutmut_orig.__name__ = 'xǁWatchMonitorǁ_print_summary'
    
    def xǁWatchMonitorǁstart__mutmut_orig(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_1(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = None
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_2(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = False
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_3(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = ""
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_4(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration = 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_5(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration -= 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_6(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 2
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_7(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = None
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_8(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        None,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_9(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        None,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_10(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=None,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_11(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=None,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_12(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=None,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_13(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=None,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_14(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=None  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_15(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_16(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_17(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_18(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_19(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_20(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_21(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_22(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=True,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_23(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(None)
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_24(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(None)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_25(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    break
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_26(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = None
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_27(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=None,
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_28(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=None,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_29(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=None
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_30(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_31(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_32(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_33(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(None)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_34(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = ""
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_35(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_36(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = None
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_37(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(None, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_38(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, None)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_39(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_40(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, )
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_41(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(None, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_42(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, None)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_43(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_44(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, )
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_45(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = None
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_46(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(None)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = False
    
    def xǁWatchMonitorǁstart__mutmut_47(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = None
    
    def xǁWatchMonitorǁstart__mutmut_48(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs indefinitely until interrupted with Ctrl+C or SIGTERM.
        """
        self.running = True
        self._setup_signal_handlers()  # Set up signal handlers when starting
        self._print_header()
        
        prev_result: Optional[OptimizationResult] = None
        
        try:
            while self.running:
                self.iteration += 1
                
                # Perform optimization
                try:
                    result = optimize(
                        self.func,
                        self.data,
                        sample_size=self.sample_size,
                        target_chunk_duration=self.target_chunk_duration,
                        verbose=False,  # Suppress optimizer's verbose output
                        profile=self.enable_profiling,  # Configurable profiling
                        use_cache=self.use_cache  # Configurable caching
                    )
                except Exception as e:
                    print(f"\n❌ Optimization failed: {e}")
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                    # Wait before retry
                    time.sleep(self.interval)
                    continue
                
                # Create snapshot
                snapshot = WatchSnapshot(
                    timestamp=datetime.now(),
                    result=result,
                    iteration=self.iteration
                )
                self.snapshots.append(snapshot)
                
                # Detect changes if we have a previous result
                changes = None
                if prev_result is not None:
                    changes = self._detect_changes(prev_result, result)
                
                # Print snapshot
                self._print_snapshot(snapshot, changes)
                
                prev_result = result
                
                # Sleep until next iteration (unless interrupted)
                if self.running:
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass
        finally:
            self._print_summary()
            self._restore_signal_handlers()  # Restore original signal handlers
            self.running = True
    
    xǁWatchMonitorǁstart__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁWatchMonitorǁstart__mutmut_1': xǁWatchMonitorǁstart__mutmut_1, 
        'xǁWatchMonitorǁstart__mutmut_2': xǁWatchMonitorǁstart__mutmut_2, 
        'xǁWatchMonitorǁstart__mutmut_3': xǁWatchMonitorǁstart__mutmut_3, 
        'xǁWatchMonitorǁstart__mutmut_4': xǁWatchMonitorǁstart__mutmut_4, 
        'xǁWatchMonitorǁstart__mutmut_5': xǁWatchMonitorǁstart__mutmut_5, 
        'xǁWatchMonitorǁstart__mutmut_6': xǁWatchMonitorǁstart__mutmut_6, 
        'xǁWatchMonitorǁstart__mutmut_7': xǁWatchMonitorǁstart__mutmut_7, 
        'xǁWatchMonitorǁstart__mutmut_8': xǁWatchMonitorǁstart__mutmut_8, 
        'xǁWatchMonitorǁstart__mutmut_9': xǁWatchMonitorǁstart__mutmut_9, 
        'xǁWatchMonitorǁstart__mutmut_10': xǁWatchMonitorǁstart__mutmut_10, 
        'xǁWatchMonitorǁstart__mutmut_11': xǁWatchMonitorǁstart__mutmut_11, 
        'xǁWatchMonitorǁstart__mutmut_12': xǁWatchMonitorǁstart__mutmut_12, 
        'xǁWatchMonitorǁstart__mutmut_13': xǁWatchMonitorǁstart__mutmut_13, 
        'xǁWatchMonitorǁstart__mutmut_14': xǁWatchMonitorǁstart__mutmut_14, 
        'xǁWatchMonitorǁstart__mutmut_15': xǁWatchMonitorǁstart__mutmut_15, 
        'xǁWatchMonitorǁstart__mutmut_16': xǁWatchMonitorǁstart__mutmut_16, 
        'xǁWatchMonitorǁstart__mutmut_17': xǁWatchMonitorǁstart__mutmut_17, 
        'xǁWatchMonitorǁstart__mutmut_18': xǁWatchMonitorǁstart__mutmut_18, 
        'xǁWatchMonitorǁstart__mutmut_19': xǁWatchMonitorǁstart__mutmut_19, 
        'xǁWatchMonitorǁstart__mutmut_20': xǁWatchMonitorǁstart__mutmut_20, 
        'xǁWatchMonitorǁstart__mutmut_21': xǁWatchMonitorǁstart__mutmut_21, 
        'xǁWatchMonitorǁstart__mutmut_22': xǁWatchMonitorǁstart__mutmut_22, 
        'xǁWatchMonitorǁstart__mutmut_23': xǁWatchMonitorǁstart__mutmut_23, 
        'xǁWatchMonitorǁstart__mutmut_24': xǁWatchMonitorǁstart__mutmut_24, 
        'xǁWatchMonitorǁstart__mutmut_25': xǁWatchMonitorǁstart__mutmut_25, 
        'xǁWatchMonitorǁstart__mutmut_26': xǁWatchMonitorǁstart__mutmut_26, 
        'xǁWatchMonitorǁstart__mutmut_27': xǁWatchMonitorǁstart__mutmut_27, 
        'xǁWatchMonitorǁstart__mutmut_28': xǁWatchMonitorǁstart__mutmut_28, 
        'xǁWatchMonitorǁstart__mutmut_29': xǁWatchMonitorǁstart__mutmut_29, 
        'xǁWatchMonitorǁstart__mutmut_30': xǁWatchMonitorǁstart__mutmut_30, 
        'xǁWatchMonitorǁstart__mutmut_31': xǁWatchMonitorǁstart__mutmut_31, 
        'xǁWatchMonitorǁstart__mutmut_32': xǁWatchMonitorǁstart__mutmut_32, 
        'xǁWatchMonitorǁstart__mutmut_33': xǁWatchMonitorǁstart__mutmut_33, 
        'xǁWatchMonitorǁstart__mutmut_34': xǁWatchMonitorǁstart__mutmut_34, 
        'xǁWatchMonitorǁstart__mutmut_35': xǁWatchMonitorǁstart__mutmut_35, 
        'xǁWatchMonitorǁstart__mutmut_36': xǁWatchMonitorǁstart__mutmut_36, 
        'xǁWatchMonitorǁstart__mutmut_37': xǁWatchMonitorǁstart__mutmut_37, 
        'xǁWatchMonitorǁstart__mutmut_38': xǁWatchMonitorǁstart__mutmut_38, 
        'xǁWatchMonitorǁstart__mutmut_39': xǁWatchMonitorǁstart__mutmut_39, 
        'xǁWatchMonitorǁstart__mutmut_40': xǁWatchMonitorǁstart__mutmut_40, 
        'xǁWatchMonitorǁstart__mutmut_41': xǁWatchMonitorǁstart__mutmut_41, 
        'xǁWatchMonitorǁstart__mutmut_42': xǁWatchMonitorǁstart__mutmut_42, 
        'xǁWatchMonitorǁstart__mutmut_43': xǁWatchMonitorǁstart__mutmut_43, 
        'xǁWatchMonitorǁstart__mutmut_44': xǁWatchMonitorǁstart__mutmut_44, 
        'xǁWatchMonitorǁstart__mutmut_45': xǁWatchMonitorǁstart__mutmut_45, 
        'xǁWatchMonitorǁstart__mutmut_46': xǁWatchMonitorǁstart__mutmut_46, 
        'xǁWatchMonitorǁstart__mutmut_47': xǁWatchMonitorǁstart__mutmut_47, 
        'xǁWatchMonitorǁstart__mutmut_48': xǁWatchMonitorǁstart__mutmut_48
    }
    
    def start(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁWatchMonitorǁstart__mutmut_orig"), object.__getattribute__(self, "xǁWatchMonitorǁstart__mutmut_mutants"), args, kwargs, self)
        return result 
    
    start.__signature__ = _mutmut_signature(xǁWatchMonitorǁstart__mutmut_orig)
    xǁWatchMonitorǁstart__mutmut_orig.__name__ = 'xǁWatchMonitorǁstart'


def x_watch__mutmut_orig(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_1(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 61.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_2(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 2,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_3(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 1.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_4(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = True,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_5(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 6,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_6(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 1.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_7(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = True,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_8(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = True
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_9(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = None
    monitor.start()


def x_watch__mutmut_10(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=None,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_11(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=None,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_12(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=None,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_13(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=None,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_14(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=None,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_15(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=None,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_16(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=None,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_17(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=None,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_18(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=None,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_19(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=None,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_20(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=None
    )
    monitor.start()


def x_watch__mutmut_21(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_22(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_23(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_24(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_25(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_26(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_27(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_28(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_29(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        enable_profiling=enable_profiling,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_30(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        use_cache=use_cache
    )
    monitor.start()


def x_watch__mutmut_31(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    interval: float = 60.0,
    change_threshold_n_jobs: int = 1,
    change_threshold_speedup: float = 0.2,
    change_threshold_chunksize: float = DEFAULT_CHUNKSIZE_CHANGE_THRESHOLD,
    verbose: bool = False,
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    enable_profiling: bool = False,
    use_cache: bool = False
) -> None:
    """
    Watch a function's optimization parameters over time.
    
    This function continuously monitors optimal parallelization parameters,
    alerting when significant changes are detected. Useful for:
    - Monitoring production workloads
    - Detecting performance degradation
    - Observing workload pattern changes
    
    Args:
        func: Function to monitor
        data: Input data for the function
        interval: Time between checks in seconds (default: 60s)
        change_threshold_n_jobs: Alert if n_jobs changes by this amount (default: 1)
        change_threshold_speedup: Alert if speedup changes by this ratio (default: 0.2)
        change_threshold_chunksize: Alert if chunksize changes by this ratio (default: 0.5)
        verbose: Enable verbose output
        sample_size: Number of samples for dry run
        target_chunk_duration: Target chunk duration for optimization
        enable_profiling: Enable profiling during optimization (default: False)
        use_cache: Use optimization cache (default: False)
        
    Example:
        >>> from amorsize import watch
        >>> def process_item(x):
        ...     return x ** 2
        >>> 
        >>> # Monitor every 30 seconds
        >>> watch(process_item, range(1000), interval=30.0)
        
    Note:
        Press Ctrl+C to stop monitoring and see summary statistics.
    """
    monitor = WatchMonitor(
        func=func,
        data=data,
        interval=interval,
        change_threshold_n_jobs=change_threshold_n_jobs,
        change_threshold_speedup=change_threshold_speedup,
        change_threshold_chunksize=change_threshold_chunksize,
        verbose=verbose,
        sample_size=sample_size,
        target_chunk_duration=target_chunk_duration,
        enable_profiling=enable_profiling,
        )
    monitor.start()

x_watch__mutmut_mutants : ClassVar[MutantDict] = {
'x_watch__mutmut_1': x_watch__mutmut_1, 
    'x_watch__mutmut_2': x_watch__mutmut_2, 
    'x_watch__mutmut_3': x_watch__mutmut_3, 
    'x_watch__mutmut_4': x_watch__mutmut_4, 
    'x_watch__mutmut_5': x_watch__mutmut_5, 
    'x_watch__mutmut_6': x_watch__mutmut_6, 
    'x_watch__mutmut_7': x_watch__mutmut_7, 
    'x_watch__mutmut_8': x_watch__mutmut_8, 
    'x_watch__mutmut_9': x_watch__mutmut_9, 
    'x_watch__mutmut_10': x_watch__mutmut_10, 
    'x_watch__mutmut_11': x_watch__mutmut_11, 
    'x_watch__mutmut_12': x_watch__mutmut_12, 
    'x_watch__mutmut_13': x_watch__mutmut_13, 
    'x_watch__mutmut_14': x_watch__mutmut_14, 
    'x_watch__mutmut_15': x_watch__mutmut_15, 
    'x_watch__mutmut_16': x_watch__mutmut_16, 
    'x_watch__mutmut_17': x_watch__mutmut_17, 
    'x_watch__mutmut_18': x_watch__mutmut_18, 
    'x_watch__mutmut_19': x_watch__mutmut_19, 
    'x_watch__mutmut_20': x_watch__mutmut_20, 
    'x_watch__mutmut_21': x_watch__mutmut_21, 
    'x_watch__mutmut_22': x_watch__mutmut_22, 
    'x_watch__mutmut_23': x_watch__mutmut_23, 
    'x_watch__mutmut_24': x_watch__mutmut_24, 
    'x_watch__mutmut_25': x_watch__mutmut_25, 
    'x_watch__mutmut_26': x_watch__mutmut_26, 
    'x_watch__mutmut_27': x_watch__mutmut_27, 
    'x_watch__mutmut_28': x_watch__mutmut_28, 
    'x_watch__mutmut_29': x_watch__mutmut_29, 
    'x_watch__mutmut_30': x_watch__mutmut_30, 
    'x_watch__mutmut_31': x_watch__mutmut_31
}

def watch(*args, **kwargs):
    result = _mutmut_trampoline(x_watch__mutmut_orig, x_watch__mutmut_mutants, args, kwargs)
    return result 

watch.__signature__ = _mutmut_signature(x_watch__mutmut_orig)
x_watch__mutmut_orig.__name__ = 'x_watch'
