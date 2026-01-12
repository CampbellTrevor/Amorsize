"""
Worker Pool Manager for reusing multiprocessing pools across optimize() calls.

This module provides a pool management system that pre-spawns and reuses
worker pools to amortize the spawn cost across multiple optimization calls.
This is particularly beneficial for:
- Web services that repeatedly optimize workloads
- Batch processing systems
- Repeated analysis on similar datasets
"""

import atexit
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from multiprocessing import Pool
from typing import Any, Dict, Optional, Tuple
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


class PoolManager:
    """
    Manages a pool of reusable multiprocessing/threading workers.

    This class maintains worker pools and reuses them across multiple
    optimize() calls, amortizing the expensive process spawn cost.

    Features:
    - Automatic pool lifecycle management
    - Thread-safe pool access
    - Configurable pool sizes
    - Support for both multiprocessing and threading
    - Automatic cleanup on program exit
    - Idle timeout for resource conservation

    Usage:
        >>> manager = PoolManager()
        >>> pool = manager.get_pool(n_jobs=4, executor_type="process")
        >>> results = pool.map(func, data, chunksize=10)
        >>> # Pool is automatically returned to manager when done
        >>> # Reuse the same pool for next call
        >>> pool = manager.get_pool(n_jobs=4, executor_type="process")
        >>> # ...
        >>> manager.shutdown()  # Clean up when done
    """

    def xǁPoolManagerǁ__init____mutmut_orig(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_1(self, idle_timeout: float = 301.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_2(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = False):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_3(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = None  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_4(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = None  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_5(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = None
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_6(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = None
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_7(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = None
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_8(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = None

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_9(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = True

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(self.shutdown)

    def xǁPoolManagerǁ__init____mutmut_10(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
        """
        Initialize the pool manager.

        Args:
            idle_timeout: Seconds of inactivity before automatically closing
                         idle pools to free resources (default: 300s = 5 minutes).
                         Set to None to disable auto-cleanup.
            enable_auto_cleanup: If True, register atexit handler to clean up
                                pools on program exit (default: True).
        """
        self._pools: Dict[Tuple[int, str], Any] = {}  # (n_jobs, type) -> pool
        self._pool_usage: Dict[Tuple[int, str], float] = {}  # (n_jobs, type) -> last_used_time
        self._lock = threading.Lock()
        self._idle_timeout = idle_timeout
        self._enable_auto_cleanup = enable_auto_cleanup
        self._shutdown = False

        # Register cleanup on program exit
        if enable_auto_cleanup:
            atexit.register(None)
    
    xǁPoolManagerǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁ__init____mutmut_1': xǁPoolManagerǁ__init____mutmut_1, 
        'xǁPoolManagerǁ__init____mutmut_2': xǁPoolManagerǁ__init____mutmut_2, 
        'xǁPoolManagerǁ__init____mutmut_3': xǁPoolManagerǁ__init____mutmut_3, 
        'xǁPoolManagerǁ__init____mutmut_4': xǁPoolManagerǁ__init____mutmut_4, 
        'xǁPoolManagerǁ__init____mutmut_5': xǁPoolManagerǁ__init____mutmut_5, 
        'xǁPoolManagerǁ__init____mutmut_6': xǁPoolManagerǁ__init____mutmut_6, 
        'xǁPoolManagerǁ__init____mutmut_7': xǁPoolManagerǁ__init____mutmut_7, 
        'xǁPoolManagerǁ__init____mutmut_8': xǁPoolManagerǁ__init____mutmut_8, 
        'xǁPoolManagerǁ__init____mutmut_9': xǁPoolManagerǁ__init____mutmut_9, 
        'xǁPoolManagerǁ__init____mutmut_10': xǁPoolManagerǁ__init____mutmut_10
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁPoolManagerǁ__init____mutmut_orig)
    xǁPoolManagerǁ__init____mutmut_orig.__name__ = 'xǁPoolManagerǁ__init__'

    def xǁPoolManagerǁget_pool__mutmut_orig(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_1(
        self,
        n_jobs: int,
        executor_type: str = "XXprocessXX",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_2(
        self,
        n_jobs: int,
        executor_type: str = "PROCESS",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_3(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = True
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_4(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError(None)

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_5(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("XXPoolManager has been shut downXX")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_6(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("poolmanager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_7(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("POOLMANAGER HAS BEEN SHUT DOWN")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_8(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs < 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_9(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 1:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_10(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(None)

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_11(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_12(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("XXprocessXX", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_13(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("PROCESS", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_14(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "XXthreadXX"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_15(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "THREAD"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_16(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(None)

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_17(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = None

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_18(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new or pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_19(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_20(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key not in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_21(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = None
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_22(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(None, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_23(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, None):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_24(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_25(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, ):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_26(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = None
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_27(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key not in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_28(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_29(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type != "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_30(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "XXprocessXX":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_31(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "PROCESS":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_32(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = None
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_33(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=None)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_34(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = None

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_35(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=None)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_36(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = None
            self._pool_usage[pool_key] = time.time()

            return pool

    def xǁPoolManagerǁget_pool__mutmut_37(
        self,
        n_jobs: int,
        executor_type: str = "process",
        force_new: bool = False
    ) -> Any:
        """
        Get or create a worker pool with the specified configuration.

        If a pool with the same configuration exists and is not in use,
        it will be reused. Otherwise, a new pool is created.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
            force_new: If True, always create a new pool instead of reusing

        Returns:
            A multiprocessing.Pool or ThreadPoolExecutor instance

        Raises:
            ValueError: If n_jobs <= 0 or executor_type is invalid
            RuntimeError: If manager has been shut down
        """
        if self._shutdown:
            raise RuntimeError("PoolManager has been shut down")

        if n_jobs <= 0:
            raise ValueError(f"n_jobs must be positive, got {n_jobs}")

        if executor_type not in ("process", "thread"):
            raise ValueError(f"executor_type must be 'process' or 'thread', got {executor_type}")

        pool_key = (n_jobs, executor_type)

        with self._lock:
            # Check if we can reuse an existing pool
            if not force_new and pool_key in self._pools:
                pool = self._pools[pool_key]
                # Verify pool is still alive
                if self._is_pool_alive(pool, executor_type):
                    # Update usage time
                    self._pool_usage[pool_key] = time.time()
                    return pool
                else:
                    # Pool died, remove it
                    del self._pools[pool_key]
                    if pool_key in self._pool_usage:
                        del self._pool_usage[pool_key]

            # Clean up idle pools before creating new one
            if self._idle_timeout is not None:
                self._cleanup_idle_pools()

            # Create new pool
            if executor_type == "process":
                pool = Pool(processes=n_jobs)
            else:  # thread
                pool = ThreadPoolExecutor(max_workers=n_jobs)

            # Store pool and track usage
            self._pools[pool_key] = pool
            self._pool_usage[pool_key] = None

            return pool
    
    xǁPoolManagerǁget_pool__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁget_pool__mutmut_1': xǁPoolManagerǁget_pool__mutmut_1, 
        'xǁPoolManagerǁget_pool__mutmut_2': xǁPoolManagerǁget_pool__mutmut_2, 
        'xǁPoolManagerǁget_pool__mutmut_3': xǁPoolManagerǁget_pool__mutmut_3, 
        'xǁPoolManagerǁget_pool__mutmut_4': xǁPoolManagerǁget_pool__mutmut_4, 
        'xǁPoolManagerǁget_pool__mutmut_5': xǁPoolManagerǁget_pool__mutmut_5, 
        'xǁPoolManagerǁget_pool__mutmut_6': xǁPoolManagerǁget_pool__mutmut_6, 
        'xǁPoolManagerǁget_pool__mutmut_7': xǁPoolManagerǁget_pool__mutmut_7, 
        'xǁPoolManagerǁget_pool__mutmut_8': xǁPoolManagerǁget_pool__mutmut_8, 
        'xǁPoolManagerǁget_pool__mutmut_9': xǁPoolManagerǁget_pool__mutmut_9, 
        'xǁPoolManagerǁget_pool__mutmut_10': xǁPoolManagerǁget_pool__mutmut_10, 
        'xǁPoolManagerǁget_pool__mutmut_11': xǁPoolManagerǁget_pool__mutmut_11, 
        'xǁPoolManagerǁget_pool__mutmut_12': xǁPoolManagerǁget_pool__mutmut_12, 
        'xǁPoolManagerǁget_pool__mutmut_13': xǁPoolManagerǁget_pool__mutmut_13, 
        'xǁPoolManagerǁget_pool__mutmut_14': xǁPoolManagerǁget_pool__mutmut_14, 
        'xǁPoolManagerǁget_pool__mutmut_15': xǁPoolManagerǁget_pool__mutmut_15, 
        'xǁPoolManagerǁget_pool__mutmut_16': xǁPoolManagerǁget_pool__mutmut_16, 
        'xǁPoolManagerǁget_pool__mutmut_17': xǁPoolManagerǁget_pool__mutmut_17, 
        'xǁPoolManagerǁget_pool__mutmut_18': xǁPoolManagerǁget_pool__mutmut_18, 
        'xǁPoolManagerǁget_pool__mutmut_19': xǁPoolManagerǁget_pool__mutmut_19, 
        'xǁPoolManagerǁget_pool__mutmut_20': xǁPoolManagerǁget_pool__mutmut_20, 
        'xǁPoolManagerǁget_pool__mutmut_21': xǁPoolManagerǁget_pool__mutmut_21, 
        'xǁPoolManagerǁget_pool__mutmut_22': xǁPoolManagerǁget_pool__mutmut_22, 
        'xǁPoolManagerǁget_pool__mutmut_23': xǁPoolManagerǁget_pool__mutmut_23, 
        'xǁPoolManagerǁget_pool__mutmut_24': xǁPoolManagerǁget_pool__mutmut_24, 
        'xǁPoolManagerǁget_pool__mutmut_25': xǁPoolManagerǁget_pool__mutmut_25, 
        'xǁPoolManagerǁget_pool__mutmut_26': xǁPoolManagerǁget_pool__mutmut_26, 
        'xǁPoolManagerǁget_pool__mutmut_27': xǁPoolManagerǁget_pool__mutmut_27, 
        'xǁPoolManagerǁget_pool__mutmut_28': xǁPoolManagerǁget_pool__mutmut_28, 
        'xǁPoolManagerǁget_pool__mutmut_29': xǁPoolManagerǁget_pool__mutmut_29, 
        'xǁPoolManagerǁget_pool__mutmut_30': xǁPoolManagerǁget_pool__mutmut_30, 
        'xǁPoolManagerǁget_pool__mutmut_31': xǁPoolManagerǁget_pool__mutmut_31, 
        'xǁPoolManagerǁget_pool__mutmut_32': xǁPoolManagerǁget_pool__mutmut_32, 
        'xǁPoolManagerǁget_pool__mutmut_33': xǁPoolManagerǁget_pool__mutmut_33, 
        'xǁPoolManagerǁget_pool__mutmut_34': xǁPoolManagerǁget_pool__mutmut_34, 
        'xǁPoolManagerǁget_pool__mutmut_35': xǁPoolManagerǁget_pool__mutmut_35, 
        'xǁPoolManagerǁget_pool__mutmut_36': xǁPoolManagerǁget_pool__mutmut_36, 
        'xǁPoolManagerǁget_pool__mutmut_37': xǁPoolManagerǁget_pool__mutmut_37
    }
    
    def get_pool(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁget_pool__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁget_pool__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_pool.__signature__ = _mutmut_signature(xǁPoolManagerǁget_pool__mutmut_orig)
    xǁPoolManagerǁget_pool__mutmut_orig.__name__ = 'xǁPoolManagerǁget_pool'

    def xǁPoolManagerǁ_is_pool_alive__mutmut_orig(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_1(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type != "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_2(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "XXprocessXX":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_3(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "PROCESS":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_4(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(None, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_5(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, None):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_6(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr('_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_7(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, ):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_8(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, 'XX_stateXX'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_9(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_STATE'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_10(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state != RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_11(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return False
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_12(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(None, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_13(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, None):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_14(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr('_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_15(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, ):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_16(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, 'XX_shutdownXX'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_17(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_SHUTDOWN'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_18(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_19(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return False
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return False

    def xǁPoolManagerǁ_is_pool_alive__mutmut_20(self, pool: Any, executor_type: str) -> bool:
        """
        Check if a pool is still alive and functional.

        Args:
            pool: The pool to check
            executor_type: Type of executor ("process" or "thread")

        Returns:
            True if pool is alive, False otherwise
        """
        try:
            if executor_type == "process":
                # For multiprocessing.Pool, check if it's closed/terminated
                # Pool._state is an integer: RUN=0, CLOSE=1, TERMINATE=2
                # However, the constants are defined in the module
                from multiprocessing.pool import RUN
                if hasattr(pool, '_state'):
                    return pool._state == RUN
                return True
            else:  # thread
                # For ThreadPoolExecutor, check if it's shutdown
                if hasattr(pool, '_shutdown'):
                    return not pool._shutdown
                return True
        except (AttributeError, ImportError, Exception):
            # If we can't determine, assume it's not alive
            return True
    
    xǁPoolManagerǁ_is_pool_alive__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁ_is_pool_alive__mutmut_1': xǁPoolManagerǁ_is_pool_alive__mutmut_1, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_2': xǁPoolManagerǁ_is_pool_alive__mutmut_2, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_3': xǁPoolManagerǁ_is_pool_alive__mutmut_3, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_4': xǁPoolManagerǁ_is_pool_alive__mutmut_4, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_5': xǁPoolManagerǁ_is_pool_alive__mutmut_5, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_6': xǁPoolManagerǁ_is_pool_alive__mutmut_6, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_7': xǁPoolManagerǁ_is_pool_alive__mutmut_7, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_8': xǁPoolManagerǁ_is_pool_alive__mutmut_8, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_9': xǁPoolManagerǁ_is_pool_alive__mutmut_9, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_10': xǁPoolManagerǁ_is_pool_alive__mutmut_10, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_11': xǁPoolManagerǁ_is_pool_alive__mutmut_11, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_12': xǁPoolManagerǁ_is_pool_alive__mutmut_12, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_13': xǁPoolManagerǁ_is_pool_alive__mutmut_13, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_14': xǁPoolManagerǁ_is_pool_alive__mutmut_14, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_15': xǁPoolManagerǁ_is_pool_alive__mutmut_15, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_16': xǁPoolManagerǁ_is_pool_alive__mutmut_16, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_17': xǁPoolManagerǁ_is_pool_alive__mutmut_17, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_18': xǁPoolManagerǁ_is_pool_alive__mutmut_18, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_19': xǁPoolManagerǁ_is_pool_alive__mutmut_19, 
        'xǁPoolManagerǁ_is_pool_alive__mutmut_20': xǁPoolManagerǁ_is_pool_alive__mutmut_20
    }
    
    def _is_pool_alive(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁ_is_pool_alive__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁ_is_pool_alive__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _is_pool_alive.__signature__ = _mutmut_signature(xǁPoolManagerǁ_is_pool_alive__mutmut_orig)
    xǁPoolManagerǁ_is_pool_alive__mutmut_orig.__name__ = 'xǁPoolManagerǁ_is_pool_alive'

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_orig(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_1(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is not None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_2(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = None
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_3(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = None

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_4(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time + last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_5(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used >= self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_6(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(None)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_7(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = None
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_8(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(None)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_9(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is None:
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_10(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = None
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_11(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[2]
                self._close_pool(pool, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_12(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(None, executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_13(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, None)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_14(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(executor_type)
                del self._pools[pool_key]
                del self._pool_usage[pool_key]

    def xǁPoolManagerǁ_cleanup_idle_pools__mutmut_15(self):
        """
        Clean up pools that have been idle for longer than idle_timeout.

        This is called internally before creating new pools to free resources.
        Must be called with _lock held.
        """
        if self._idle_timeout is None:
            return

        current_time = time.time()
        pools_to_remove = []

        for pool_key, last_used in self._pool_usage.items():
            if current_time - last_used > self._idle_timeout:
                pools_to_remove.append(pool_key)

        for pool_key in pools_to_remove:
            pool = self._pools.get(pool_key)
            if pool is not None:
                executor_type = pool_key[1]
                self._close_pool(pool, )
                del self._pools[pool_key]
                del self._pool_usage[pool_key]
    
    xǁPoolManagerǁ_cleanup_idle_pools__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_1': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_1, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_2': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_2, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_3': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_3, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_4': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_4, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_5': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_5, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_6': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_6, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_7': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_7, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_8': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_8, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_9': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_9, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_10': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_10, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_11': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_11, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_12': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_12, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_13': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_13, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_14': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_14, 
        'xǁPoolManagerǁ_cleanup_idle_pools__mutmut_15': xǁPoolManagerǁ_cleanup_idle_pools__mutmut_15
    }
    
    def _cleanup_idle_pools(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁ_cleanup_idle_pools__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁ_cleanup_idle_pools__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _cleanup_idle_pools.__signature__ = _mutmut_signature(xǁPoolManagerǁ_cleanup_idle_pools__mutmut_orig)
    xǁPoolManagerǁ_cleanup_idle_pools__mutmut_orig.__name__ = 'xǁPoolManagerǁ_cleanup_idle_pools'

    def xǁPoolManagerǁ_close_pool__mutmut_orig(self, pool: Any, executor_type: str):
        """
        Safely close a pool.

        Args:
            pool: The pool to close
            executor_type: Type of executor ("process" or "thread")
        """
        try:
            if executor_type == "process":
                pool.close()
                pool.join()
            else:  # thread
                pool.shutdown(wait=True)
        except Exception:
            # Silently ignore errors during cleanup
            pass

    def xǁPoolManagerǁ_close_pool__mutmut_1(self, pool: Any, executor_type: str):
        """
        Safely close a pool.

        Args:
            pool: The pool to close
            executor_type: Type of executor ("process" or "thread")
        """
        try:
            if executor_type != "process":
                pool.close()
                pool.join()
            else:  # thread
                pool.shutdown(wait=True)
        except Exception:
            # Silently ignore errors during cleanup
            pass

    def xǁPoolManagerǁ_close_pool__mutmut_2(self, pool: Any, executor_type: str):
        """
        Safely close a pool.

        Args:
            pool: The pool to close
            executor_type: Type of executor ("process" or "thread")
        """
        try:
            if executor_type == "XXprocessXX":
                pool.close()
                pool.join()
            else:  # thread
                pool.shutdown(wait=True)
        except Exception:
            # Silently ignore errors during cleanup
            pass

    def xǁPoolManagerǁ_close_pool__mutmut_3(self, pool: Any, executor_type: str):
        """
        Safely close a pool.

        Args:
            pool: The pool to close
            executor_type: Type of executor ("process" or "thread")
        """
        try:
            if executor_type == "PROCESS":
                pool.close()
                pool.join()
            else:  # thread
                pool.shutdown(wait=True)
        except Exception:
            # Silently ignore errors during cleanup
            pass

    def xǁPoolManagerǁ_close_pool__mutmut_4(self, pool: Any, executor_type: str):
        """
        Safely close a pool.

        Args:
            pool: The pool to close
            executor_type: Type of executor ("process" or "thread")
        """
        try:
            if executor_type == "process":
                pool.close()
                pool.join()
            else:  # thread
                pool.shutdown(wait=None)
        except Exception:
            # Silently ignore errors during cleanup
            pass

    def xǁPoolManagerǁ_close_pool__mutmut_5(self, pool: Any, executor_type: str):
        """
        Safely close a pool.

        Args:
            pool: The pool to close
            executor_type: Type of executor ("process" or "thread")
        """
        try:
            if executor_type == "process":
                pool.close()
                pool.join()
            else:  # thread
                pool.shutdown(wait=False)
        except Exception:
            # Silently ignore errors during cleanup
            pass
    
    xǁPoolManagerǁ_close_pool__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁ_close_pool__mutmut_1': xǁPoolManagerǁ_close_pool__mutmut_1, 
        'xǁPoolManagerǁ_close_pool__mutmut_2': xǁPoolManagerǁ_close_pool__mutmut_2, 
        'xǁPoolManagerǁ_close_pool__mutmut_3': xǁPoolManagerǁ_close_pool__mutmut_3, 
        'xǁPoolManagerǁ_close_pool__mutmut_4': xǁPoolManagerǁ_close_pool__mutmut_4, 
        'xǁPoolManagerǁ_close_pool__mutmut_5': xǁPoolManagerǁ_close_pool__mutmut_5
    }
    
    def _close_pool(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁ_close_pool__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁ_close_pool__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _close_pool.__signature__ = _mutmut_signature(xǁPoolManagerǁ_close_pool__mutmut_orig)
    xǁPoolManagerǁ_close_pool__mutmut_orig.__name__ = 'xǁPoolManagerǁ_close_pool'

    def xǁPoolManagerǁrelease_pool__mutmut_orig(self, n_jobs: int, executor_type: str = "process"):
        """
        Release a pool back to the manager (no-op, pools are managed automatically).

        This method exists for API completeness but does nothing since pools
        are automatically managed and reused.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
        """
        # No-op: pools are managed automatically
        # Just update usage time
        pool_key = (n_jobs, executor_type)
        with self._lock:
            if pool_key in self._pool_usage:
                self._pool_usage[pool_key] = time.time()

    def xǁPoolManagerǁrelease_pool__mutmut_1(self, n_jobs: int, executor_type: str = "XXprocessXX"):
        """
        Release a pool back to the manager (no-op, pools are managed automatically).

        This method exists for API completeness but does nothing since pools
        are automatically managed and reused.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
        """
        # No-op: pools are managed automatically
        # Just update usage time
        pool_key = (n_jobs, executor_type)
        with self._lock:
            if pool_key in self._pool_usage:
                self._pool_usage[pool_key] = time.time()

    def xǁPoolManagerǁrelease_pool__mutmut_2(self, n_jobs: int, executor_type: str = "PROCESS"):
        """
        Release a pool back to the manager (no-op, pools are managed automatically).

        This method exists for API completeness but does nothing since pools
        are automatically managed and reused.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
        """
        # No-op: pools are managed automatically
        # Just update usage time
        pool_key = (n_jobs, executor_type)
        with self._lock:
            if pool_key in self._pool_usage:
                self._pool_usage[pool_key] = time.time()

    def xǁPoolManagerǁrelease_pool__mutmut_3(self, n_jobs: int, executor_type: str = "process"):
        """
        Release a pool back to the manager (no-op, pools are managed automatically).

        This method exists for API completeness but does nothing since pools
        are automatically managed and reused.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
        """
        # No-op: pools are managed automatically
        # Just update usage time
        pool_key = None
        with self._lock:
            if pool_key in self._pool_usage:
                self._pool_usage[pool_key] = time.time()

    def xǁPoolManagerǁrelease_pool__mutmut_4(self, n_jobs: int, executor_type: str = "process"):
        """
        Release a pool back to the manager (no-op, pools are managed automatically).

        This method exists for API completeness but does nothing since pools
        are automatically managed and reused.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
        """
        # No-op: pools are managed automatically
        # Just update usage time
        pool_key = (n_jobs, executor_type)
        with self._lock:
            if pool_key not in self._pool_usage:
                self._pool_usage[pool_key] = time.time()

    def xǁPoolManagerǁrelease_pool__mutmut_5(self, n_jobs: int, executor_type: str = "process"):
        """
        Release a pool back to the manager (no-op, pools are managed automatically).

        This method exists for API completeness but does nothing since pools
        are automatically managed and reused.

        Args:
            n_jobs: Number of workers in the pool
            executor_type: Type of executor ("process" or "thread")
        """
        # No-op: pools are managed automatically
        # Just update usage time
        pool_key = (n_jobs, executor_type)
        with self._lock:
            if pool_key in self._pool_usage:
                self._pool_usage[pool_key] = None
    
    xǁPoolManagerǁrelease_pool__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁrelease_pool__mutmut_1': xǁPoolManagerǁrelease_pool__mutmut_1, 
        'xǁPoolManagerǁrelease_pool__mutmut_2': xǁPoolManagerǁrelease_pool__mutmut_2, 
        'xǁPoolManagerǁrelease_pool__mutmut_3': xǁPoolManagerǁrelease_pool__mutmut_3, 
        'xǁPoolManagerǁrelease_pool__mutmut_4': xǁPoolManagerǁrelease_pool__mutmut_4, 
        'xǁPoolManagerǁrelease_pool__mutmut_5': xǁPoolManagerǁrelease_pool__mutmut_5
    }
    
    def release_pool(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁrelease_pool__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁrelease_pool__mutmut_mutants"), args, kwargs, self)
        return result 
    
    release_pool.__signature__ = _mutmut_signature(xǁPoolManagerǁrelease_pool__mutmut_orig)
    xǁPoolManagerǁrelease_pool__mutmut_orig.__name__ = 'xǁPoolManagerǁrelease_pool'

    def xǁPoolManagerǁshutdown__mutmut_orig(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_1(self, force: bool = True):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_2(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = None

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_3(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = False

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_4(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(None):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_5(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = None
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_6(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[2]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_7(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force or executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_8(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type != "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_9(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "XXprocessXX":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_10(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "PROCESS":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_11(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(None, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_12(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, None)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_13(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁshutdown__mutmut_14(self, force: bool = False):
        """
        Shutdown the pool manager and close all managed pools.

        This should be called when the manager is no longer needed to ensure
        clean resource cleanup.

        Args:
            force: If True, terminate pools immediately without waiting for
                  tasks to complete (default: False).
        """
        with self._lock:
            if self._shutdown:
                return  # Already shut down

            self._shutdown = True

            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                if force and executor_type == "process":
                    # Forceful termination for multiprocessing
                    try:
                        pool.terminate()
                        pool.join()
                    except Exception:
                        pass
                else:
                    # Graceful shutdown
                    self._close_pool(pool, )

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()
    
    xǁPoolManagerǁshutdown__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁshutdown__mutmut_1': xǁPoolManagerǁshutdown__mutmut_1, 
        'xǁPoolManagerǁshutdown__mutmut_2': xǁPoolManagerǁshutdown__mutmut_2, 
        'xǁPoolManagerǁshutdown__mutmut_3': xǁPoolManagerǁshutdown__mutmut_3, 
        'xǁPoolManagerǁshutdown__mutmut_4': xǁPoolManagerǁshutdown__mutmut_4, 
        'xǁPoolManagerǁshutdown__mutmut_5': xǁPoolManagerǁshutdown__mutmut_5, 
        'xǁPoolManagerǁshutdown__mutmut_6': xǁPoolManagerǁshutdown__mutmut_6, 
        'xǁPoolManagerǁshutdown__mutmut_7': xǁPoolManagerǁshutdown__mutmut_7, 
        'xǁPoolManagerǁshutdown__mutmut_8': xǁPoolManagerǁshutdown__mutmut_8, 
        'xǁPoolManagerǁshutdown__mutmut_9': xǁPoolManagerǁshutdown__mutmut_9, 
        'xǁPoolManagerǁshutdown__mutmut_10': xǁPoolManagerǁshutdown__mutmut_10, 
        'xǁPoolManagerǁshutdown__mutmut_11': xǁPoolManagerǁshutdown__mutmut_11, 
        'xǁPoolManagerǁshutdown__mutmut_12': xǁPoolManagerǁshutdown__mutmut_12, 
        'xǁPoolManagerǁshutdown__mutmut_13': xǁPoolManagerǁshutdown__mutmut_13, 
        'xǁPoolManagerǁshutdown__mutmut_14': xǁPoolManagerǁshutdown__mutmut_14
    }
    
    def shutdown(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁshutdown__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁshutdown__mutmut_mutants"), args, kwargs, self)
        return result 
    
    shutdown.__signature__ = _mutmut_signature(xǁPoolManagerǁshutdown__mutmut_orig)
    xǁPoolManagerǁshutdown__mutmut_orig.__name__ = 'xǁPoolManagerǁshutdown'

    def xǁPoolManagerǁget_stats__mutmut_orig(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_1(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = None
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_2(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = None

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_3(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[1]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_4(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[2]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_5(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time + last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_6(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "XXactive_poolsXX": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_7(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "ACTIVE_POOLS": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_8(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "XXpool_configsXX": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_9(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "POOL_CONFIGS": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_10(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"XXn_jobsXX": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_11(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"N_JOBS": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_12(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[1], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_13(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "XXexecutor_typeXX": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_14(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "EXECUTOR_TYPE": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_15(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[2]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_16(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "XXidle_timesXX": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_17(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "IDLE_TIMES": idle_times,
                "is_shutdown": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_18(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "XXis_shutdownXX": self._shutdown
            }

    def xǁPoolManagerǁget_stats__mutmut_19(self) -> Dict[str, Any]:
        """
        Get statistics about managed pools.

        Returns:
            Dictionary with pool statistics:
            - active_pools: Number of pools currently managed
            - pool_configs: List of (n_jobs, executor_type) for each pool
            - idle_times: Dict of pool_key -> seconds since last use
        """
        with self._lock:
            current_time = time.time()
            idle_times = {
                f"{k[0]}_{k[1]}": current_time - last_used
                for k, last_used in self._pool_usage.items()
            }

            return {
                "active_pools": len(self._pools),
                "pool_configs": [
                    {"n_jobs": k[0], "executor_type": k[1]}
                    for k in self._pools.keys()
                ],
                "idle_times": idle_times,
                "IS_SHUTDOWN": self._shutdown
            }
    
    xǁPoolManagerǁget_stats__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁget_stats__mutmut_1': xǁPoolManagerǁget_stats__mutmut_1, 
        'xǁPoolManagerǁget_stats__mutmut_2': xǁPoolManagerǁget_stats__mutmut_2, 
        'xǁPoolManagerǁget_stats__mutmut_3': xǁPoolManagerǁget_stats__mutmut_3, 
        'xǁPoolManagerǁget_stats__mutmut_4': xǁPoolManagerǁget_stats__mutmut_4, 
        'xǁPoolManagerǁget_stats__mutmut_5': xǁPoolManagerǁget_stats__mutmut_5, 
        'xǁPoolManagerǁget_stats__mutmut_6': xǁPoolManagerǁget_stats__mutmut_6, 
        'xǁPoolManagerǁget_stats__mutmut_7': xǁPoolManagerǁget_stats__mutmut_7, 
        'xǁPoolManagerǁget_stats__mutmut_8': xǁPoolManagerǁget_stats__mutmut_8, 
        'xǁPoolManagerǁget_stats__mutmut_9': xǁPoolManagerǁget_stats__mutmut_9, 
        'xǁPoolManagerǁget_stats__mutmut_10': xǁPoolManagerǁget_stats__mutmut_10, 
        'xǁPoolManagerǁget_stats__mutmut_11': xǁPoolManagerǁget_stats__mutmut_11, 
        'xǁPoolManagerǁget_stats__mutmut_12': xǁPoolManagerǁget_stats__mutmut_12, 
        'xǁPoolManagerǁget_stats__mutmut_13': xǁPoolManagerǁget_stats__mutmut_13, 
        'xǁPoolManagerǁget_stats__mutmut_14': xǁPoolManagerǁget_stats__mutmut_14, 
        'xǁPoolManagerǁget_stats__mutmut_15': xǁPoolManagerǁget_stats__mutmut_15, 
        'xǁPoolManagerǁget_stats__mutmut_16': xǁPoolManagerǁget_stats__mutmut_16, 
        'xǁPoolManagerǁget_stats__mutmut_17': xǁPoolManagerǁget_stats__mutmut_17, 
        'xǁPoolManagerǁget_stats__mutmut_18': xǁPoolManagerǁget_stats__mutmut_18, 
        'xǁPoolManagerǁget_stats__mutmut_19': xǁPoolManagerǁget_stats__mutmut_19
    }
    
    def get_stats(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁget_stats__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁget_stats__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_stats.__signature__ = _mutmut_signature(xǁPoolManagerǁget_stats__mutmut_orig)
    xǁPoolManagerǁget_stats__mutmut_orig.__name__ = 'xǁPoolManagerǁget_stats'

    def xǁPoolManagerǁclear__mutmut_orig(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁclear__mutmut_1(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(None):
                executor_type = pool_key[1]
                self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁclear__mutmut_2(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = None
                self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁclear__mutmut_3(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[2]
                self._close_pool(pool, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁclear__mutmut_4(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                self._close_pool(None, executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁclear__mutmut_5(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                self._close_pool(pool, None)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁclear__mutmut_6(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                self._close_pool(executor_type)

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()

    def xǁPoolManagerǁclear__mutmut_7(self):
        """
        Clear all pools immediately, forcing recreation on next get_pool().

        This is useful for testing or when you want to ensure fresh pools.
        """
        with self._lock:
            # Close all pools
            for pool_key, pool in list(self._pools.items()):
                executor_type = pool_key[1]
                self._close_pool(pool, )

            # Clear all pools
            self._pools.clear()
            self._pool_usage.clear()
    
    xǁPoolManagerǁclear__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁclear__mutmut_1': xǁPoolManagerǁclear__mutmut_1, 
        'xǁPoolManagerǁclear__mutmut_2': xǁPoolManagerǁclear__mutmut_2, 
        'xǁPoolManagerǁclear__mutmut_3': xǁPoolManagerǁclear__mutmut_3, 
        'xǁPoolManagerǁclear__mutmut_4': xǁPoolManagerǁclear__mutmut_4, 
        'xǁPoolManagerǁclear__mutmut_5': xǁPoolManagerǁclear__mutmut_5, 
        'xǁPoolManagerǁclear__mutmut_6': xǁPoolManagerǁclear__mutmut_6, 
        'xǁPoolManagerǁclear__mutmut_7': xǁPoolManagerǁclear__mutmut_7
    }
    
    def clear(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁclear__mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁclear__mutmut_mutants"), args, kwargs, self)
        return result 
    
    clear.__signature__ = _mutmut_signature(xǁPoolManagerǁclear__mutmut_orig)
    xǁPoolManagerǁclear__mutmut_orig.__name__ = 'xǁPoolManagerǁclear'

    def __enter__(self):
        """Context manager entry."""
        return self

    def xǁPoolManagerǁ__exit____mutmut_orig(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown the manager."""
        self.shutdown()
        return False

    def xǁPoolManagerǁ__exit____mutmut_1(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown the manager."""
        self.shutdown()
        return True
    
    xǁPoolManagerǁ__exit____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁPoolManagerǁ__exit____mutmut_1': xǁPoolManagerǁ__exit____mutmut_1
    }
    
    def __exit__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁPoolManagerǁ__exit____mutmut_orig"), object.__getattribute__(self, "xǁPoolManagerǁ__exit____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __exit__.__signature__ = _mutmut_signature(xǁPoolManagerǁ__exit____mutmut_orig)
    xǁPoolManagerǁ__exit____mutmut_orig.__name__ = 'xǁPoolManagerǁ__exit__'


# Global pool manager instance for convenience
_global_manager: Optional[PoolManager] = None
_global_manager_lock = threading.Lock()


def x_get_global_pool_manager__mutmut_orig() -> PoolManager:
    """
    Get the global pool manager instance.

    This provides a singleton pool manager that can be used across the
    entire application for pool reuse.

    Returns:
        The global PoolManager instance

    Example:
        >>> from amorsize.pool_manager import get_global_pool_manager
        >>> manager = get_global_pool_manager()
        >>> pool = manager.get_pool(n_jobs=4)
        >>> # Use pool...
    """
    global _global_manager

    if _global_manager is None:
        with _global_manager_lock:
            # Double-check locking pattern to ensure thread-safe singleton creation
            if _global_manager is None:
                _global_manager = PoolManager()

    return _global_manager


def x_get_global_pool_manager__mutmut_1() -> PoolManager:
    """
    Get the global pool manager instance.

    This provides a singleton pool manager that can be used across the
    entire application for pool reuse.

    Returns:
        The global PoolManager instance

    Example:
        >>> from amorsize.pool_manager import get_global_pool_manager
        >>> manager = get_global_pool_manager()
        >>> pool = manager.get_pool(n_jobs=4)
        >>> # Use pool...
    """
    global _global_manager

    if _global_manager is not None:
        with _global_manager_lock:
            # Double-check locking pattern to ensure thread-safe singleton creation
            if _global_manager is None:
                _global_manager = PoolManager()

    return _global_manager


def x_get_global_pool_manager__mutmut_2() -> PoolManager:
    """
    Get the global pool manager instance.

    This provides a singleton pool manager that can be used across the
    entire application for pool reuse.

    Returns:
        The global PoolManager instance

    Example:
        >>> from amorsize.pool_manager import get_global_pool_manager
        >>> manager = get_global_pool_manager()
        >>> pool = manager.get_pool(n_jobs=4)
        >>> # Use pool...
    """
    global _global_manager

    if _global_manager is None:
        with _global_manager_lock:
            # Double-check locking pattern to ensure thread-safe singleton creation
            if _global_manager is not None:
                _global_manager = PoolManager()

    return _global_manager


def x_get_global_pool_manager__mutmut_3() -> PoolManager:
    """
    Get the global pool manager instance.

    This provides a singleton pool manager that can be used across the
    entire application for pool reuse.

    Returns:
        The global PoolManager instance

    Example:
        >>> from amorsize.pool_manager import get_global_pool_manager
        >>> manager = get_global_pool_manager()
        >>> pool = manager.get_pool(n_jobs=4)
        >>> # Use pool...
    """
    global _global_manager

    if _global_manager is None:
        with _global_manager_lock:
            # Double-check locking pattern to ensure thread-safe singleton creation
            if _global_manager is None:
                _global_manager = None

    return _global_manager

x_get_global_pool_manager__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_global_pool_manager__mutmut_1': x_get_global_pool_manager__mutmut_1, 
    'x_get_global_pool_manager__mutmut_2': x_get_global_pool_manager__mutmut_2, 
    'x_get_global_pool_manager__mutmut_3': x_get_global_pool_manager__mutmut_3
}

def get_global_pool_manager(*args, **kwargs):
    result = _mutmut_trampoline(x_get_global_pool_manager__mutmut_orig, x_get_global_pool_manager__mutmut_mutants, args, kwargs)
    return result 

get_global_pool_manager.__signature__ = _mutmut_signature(x_get_global_pool_manager__mutmut_orig)
x_get_global_pool_manager__mutmut_orig.__name__ = 'x_get_global_pool_manager'


@contextmanager
def managed_pool(
    n_jobs: int,
    executor_type: str = "process",
    manager: Optional[PoolManager] = None,
    use_global: bool = True
):
    """
    Context manager for managed pool usage.

    Automatically gets a pool from the manager and ensures it's returned
    (though pools are managed automatically, this provides clean API).

    Args:
        n_jobs: Number of workers
        executor_type: Type of executor ("process" or "thread")
        manager: Specific pool manager to use (default: None = use global)
        use_global: If True and manager is None, use global manager (default: True)

    Yields:
        A pool instance (Pool or ThreadPoolExecutor)

    Example:
        >>> with managed_pool(n_jobs=4) as pool:
        ...     results = pool.map(func, data, chunksize=10)
        >>> # Pool is automatically returned to manager
    """
    if manager is None and use_global:
        manager = get_global_pool_manager()
    elif manager is None:
        # Create temporary manager for this context
        manager = PoolManager(enable_auto_cleanup=False)
        try:
            pool = manager.get_pool(n_jobs, executor_type)
            yield pool
        finally:
            manager.shutdown()
        return

    # Use provided manager
    pool = manager.get_pool(n_jobs, executor_type)
    try:
        yield pool
    finally:
        # Release pool back to manager (no-op, but explicit)
        manager.release_pool(n_jobs, executor_type)


def x_shutdown_global_pool_manager__mutmut_orig():
    """
    Shutdown the global pool manager.

    This should be called when the application is shutting down to ensure
    clean resource cleanup. It's automatically registered with atexit, but
    can be called explicitly for more control.
    """
    global _global_manager

    with _global_manager_lock:
        if _global_manager is not None:
            _global_manager.shutdown()
            _global_manager = None


def x_shutdown_global_pool_manager__mutmut_1():
    """
    Shutdown the global pool manager.

    This should be called when the application is shutting down to ensure
    clean resource cleanup. It's automatically registered with atexit, but
    can be called explicitly for more control.
    """
    global _global_manager

    with _global_manager_lock:
        if _global_manager is None:
            _global_manager.shutdown()
            _global_manager = None


def x_shutdown_global_pool_manager__mutmut_2():
    """
    Shutdown the global pool manager.

    This should be called when the application is shutting down to ensure
    clean resource cleanup. It's automatically registered with atexit, but
    can be called explicitly for more control.
    """
    global _global_manager

    with _global_manager_lock:
        if _global_manager is not None:
            _global_manager.shutdown()
            _global_manager = ""

x_shutdown_global_pool_manager__mutmut_mutants : ClassVar[MutantDict] = {
'x_shutdown_global_pool_manager__mutmut_1': x_shutdown_global_pool_manager__mutmut_1, 
    'x_shutdown_global_pool_manager__mutmut_2': x_shutdown_global_pool_manager__mutmut_2
}

def shutdown_global_pool_manager(*args, **kwargs):
    result = _mutmut_trampoline(x_shutdown_global_pool_manager__mutmut_orig, x_shutdown_global_pool_manager__mutmut_mutants, args, kwargs)
    return result 

shutdown_global_pool_manager.__signature__ = _mutmut_signature(x_shutdown_global_pool_manager__mutmut_orig)
x_shutdown_global_pool_manager__mutmut_orig.__name__ = 'x_shutdown_global_pool_manager'
