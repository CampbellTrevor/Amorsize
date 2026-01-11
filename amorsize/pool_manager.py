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
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Tuple, Any, Callable
from contextlib import contextmanager


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
    
    def __init__(self, idle_timeout: float = 300.0, enable_auto_cleanup: bool = True):
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
    
    def get_pool(
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
    
    def _is_pool_alive(self, pool: Any, executor_type: str) -> bool:
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
    
    def _cleanup_idle_pools(self):
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
    
    def _close_pool(self, pool: Any, executor_type: str):
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
    
    def release_pool(self, n_jobs: int, executor_type: str = "process"):
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
    
    def shutdown(self, force: bool = False):
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
    
    def get_stats(self) -> Dict[str, Any]:
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
    
    def clear(self):
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
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown the manager."""
        self.shutdown()
        return False


# Global pool manager instance for convenience
_global_manager: Optional[PoolManager] = None
_global_manager_lock = threading.Lock()


def get_global_pool_manager() -> PoolManager:
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
            # Double-check after acquiring lock
            if _global_manager is None:
                _global_manager = PoolManager()
    
    return _global_manager


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


def shutdown_global_pool_manager():
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
