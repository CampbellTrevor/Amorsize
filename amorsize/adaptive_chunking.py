"""
Adaptive chunk size adjustment during execution for heterogeneous workloads.

This module provides runtime adaptation of chunk sizes based on observed task
completion times, improving load balancing for workloads with variable execution
times.
"""

import threading
import time
from collections import deque
from multiprocessing.pool import Pool, ThreadPool
from typing import Any, Callable, Deque, Iterable, List, Optional, Union


class AdaptiveChunkingPool:
    """
    Wrapper around multiprocessing.Pool that dynamically adjusts chunk sizes
    during execution based on runtime performance feedback.

    This class is designed for heterogeneous workloads where task execution
    times vary significantly. It monitors task completion times and adjusts
    chunk sizes to maintain optimal load balancing.

    Algorithm:
        1. Start with initial chunk size from optimize()
        2. Monitor completion times for each chunk
        3. Calculate moving average of chunk durations
        4. If duration deviates from target, adjust chunk size
        5. Enforce min/max bounds to prevent extreme values

    Benefits:
        - Better load balancing for heterogeneous workloads
        - Self-tuning performance without manual intervention
        - Reduces stragglers (workers waiting for slow tasks)
        - Maintains throughput stability

    Usage:
        >>> from amorsize import optimize
        >>> from amorsize.adaptive_chunking import AdaptiveChunkingPool
        >>>
        >>> result = optimize(func, data)
        >>>
        >>> with AdaptiveChunkingPool(result.n_jobs, result.chunksize) as pool:
        ...     results = pool.map(func, result.data)

    Thread Safety:
        This class is thread-safe. Multiple threads can submit work concurrently.
        Internal state is protected by locks.
    """

    def __init__(
        self,
        n_jobs: int,
        initial_chunksize: int,
        target_chunk_duration: float = 0.2,
        adaptation_rate: float = 0.3,
        min_chunksize: int = 1,
        max_chunksize: Optional[int] = None,
        enable_adaptation: bool = True,
        use_threads: bool = False,
        window_size: int = 10
    ):
        """
        Initialize adaptive chunking pool.

        Args:
            n_jobs: Number of worker processes/threads
            initial_chunksize: Starting chunk size (from optimize())
            target_chunk_duration: Target duration per chunk in seconds (default: 0.2s)
            adaptation_rate: How aggressively to adapt (0.0-1.0, default: 0.3)
                           Higher = faster adaptation, lower = more stable
            min_chunksize: Minimum chunk size (default: 1)
            max_chunksize: Maximum chunk size (default: None = no limit)
            enable_adaptation: If False, disables adaptation (acts like normal Pool)
            use_threads: If True, use ThreadPool instead of Pool (default: False)
            window_size: Number of recent chunks to consider for adaptation (default: 10)

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if n_jobs < 1:
            raise ValueError(f"n_jobs must be >= 1, got {n_jobs}")
        if initial_chunksize < 1:
            raise ValueError(f"initial_chunksize must be >= 1, got {initial_chunksize}")
        if target_chunk_duration <= 0:
            raise ValueError(f"target_chunk_duration must be > 0, got {target_chunk_duration}")
        if not (0.0 <= adaptation_rate <= 1.0):
            raise ValueError(f"adaptation_rate must be 0.0-1.0, got {adaptation_rate}")
        if min_chunksize < 1:
            raise ValueError(f"min_chunksize must be >= 1, got {min_chunksize}")
        if max_chunksize is not None and max_chunksize < min_chunksize:
            raise ValueError(f"max_chunksize ({max_chunksize}) must be >= min_chunksize ({min_chunksize})")
        if window_size < 1:
            raise ValueError(f"window_size must be >= 1, got {window_size}")

        self.n_jobs = n_jobs
        self.current_chunksize = initial_chunksize
        self.target_chunk_duration = target_chunk_duration
        self.adaptation_rate = adaptation_rate
        self.min_chunksize = min_chunksize
        self.max_chunksize = max_chunksize if max_chunksize is not None else float('inf')
        self.enable_adaptation = enable_adaptation
        self.use_threads = use_threads
        self.window_size = window_size

        # Performance tracking
        self._chunk_durations: Deque[float] = deque(maxlen=window_size)
        self._total_tasks_processed = 0
        self._adaptation_count = 0
        self._lock = threading.Lock()

        # Create underlying pool
        self._pool: Union[Pool, ThreadPool]
        if use_threads:
            self._pool = ThreadPool(processes=n_jobs)
        else:
            self._pool = Pool(processes=n_jobs)

        self._closed = False

    def _record_chunk_duration(self, duration: float, num_items: int) -> None:
        """
        Record chunk completion time and potentially adjust chunk size.

        Args:
            duration: Time taken to process chunk in seconds
            num_items: Number of items in the chunk

        Thread-safe: Uses lock to protect internal state.
        """
        with self._lock:
            self._chunk_durations.append(duration)
            self._total_tasks_processed += num_items

            # Only adapt if enabled and we have enough history
            if not self.enable_adaptation or len(self._chunk_durations) < 3:
                return

            # Calculate moving average duration
            avg_duration = sum(self._chunk_durations) / len(self._chunk_durations)

            # Check if we need to adjust
            # Allow 20% tolerance band around target to avoid oscillation
            lower_bound = self.target_chunk_duration * 0.8
            upper_bound = self.target_chunk_duration * 1.2

            if avg_duration < lower_bound or avg_duration > upper_bound:
                # Calculate adjustment factor
                # ratio > 1.0 means chunks are taking too long (need smaller chunks)
                # ratio < 1.0 means chunks are too fast (can use larger chunks)
                ratio = avg_duration / self.target_chunk_duration

                # Apply adaptation rate to smooth out changes
                adjustment = 1.0 + (1.0 / ratio - 1.0) * self.adaptation_rate

                # Calculate new chunk size
                new_chunksize = int(self.current_chunksize * adjustment)

                # Enforce bounds (handle infinity case for max_chunksize)
                if self.max_chunksize == float('inf'):
                    new_chunksize = max(self.min_chunksize, new_chunksize)
                else:
                    new_chunksize = max(self.min_chunksize, min(new_chunksize, int(self.max_chunksize)))

                # Only update if it's a significant change (>10% difference)
                if abs(new_chunksize - self.current_chunksize) > max(1, self.current_chunksize * 0.1):
                    self.current_chunksize = new_chunksize
                    self._adaptation_count += 1

                    # Reset history to adapt to new regime
                    self._chunk_durations.clear()

    def map(
        self,
        func: Callable[[Any], Any],
        iterable: Iterable[Any],
        chunksize: Optional[int] = None
    ) -> List[Any]:
        """
        Apply func to each element in iterable with adaptive chunking.

        This method monitors chunk completion times and adjusts chunk size
        dynamically for optimal load balancing.

        Args:
            func: Function to apply to each element
            iterable: Iterable of input items
            chunksize: Override chunk size (disables adaptation if provided)

        Returns:
            List of results in the same order as input

        Note:
            If chunksize is explicitly provided, adaptation is disabled for
            this call and the provided chunksize is used throughout.
        """
        if self._closed:
            raise ValueError("Pool is closed")

        # Convert to list to get length and enable chunking
        items = list(iterable)

        if not items:
            return []

        # Use explicit chunksize if provided (disables adaptation)
        if chunksize is not None:
            return self._pool.map(func, items, chunksize=chunksize)

        # For small workloads, don't bother with adaptation
        if len(items) <= self.current_chunksize * 2:
            return self._pool.map(func, items, chunksize=self.current_chunksize)

        # Process in adaptive chunks
        results = []
        idx = 0

        while idx < len(items):
            # Get current chunk size (may change during iteration)
            with self._lock:
                current_chunk = self.current_chunksize

            # Extract chunk
            chunk_end = min(idx + current_chunk, len(items))
            chunk_items = items[idx:chunk_end]

            # Process chunk and measure time
            start_time = time.perf_counter()
            chunk_results = self._pool.map(func, chunk_items, chunksize=len(chunk_items))
            end_time = time.perf_counter()

            # Record performance
            duration = end_time - start_time
            self._record_chunk_duration(duration, len(chunk_items))

            # Accumulate results
            results.extend(chunk_results)
            idx = chunk_end

        return results

    def imap(
        self,
        func: Callable[[Any], Any],
        iterable: Iterable[Any],
        chunksize: Optional[int] = None
    ):
        """
        Apply func to each element in iterable, yielding results as they complete.

        Note: Adaptation is limited for imap since we can't control chunk boundaries
        after submission. Consider using map() for full adaptive benefits.

        Args:
            func: Function to apply to each element
            iterable: Iterable of input items
            chunksize: Chunk size (uses current_chunksize if None)

        Returns:
            Iterator yielding results as they complete
        """
        if self._closed:
            raise ValueError("Pool is closed")

        chunk = chunksize if chunksize is not None else self.current_chunksize
        return self._pool.imap(func, iterable, chunksize=chunk)

    def imap_unordered(
        self,
        func: Callable[[Any], Any],
        iterable: Iterable[Any],
        chunksize: Optional[int] = None
    ):
        """
        Apply func to each element in iterable, yielding results in completion order.

        Note: Adaptation is limited for imap_unordered since we can't control chunk
        boundaries after submission. Consider using map() for full adaptive benefits.

        Args:
            func: Function to apply to each element
            iterable: Iterable of input items
            chunksize: Chunk size (uses current_chunksize if None)

        Returns:
            Iterator yielding results as they complete (unordered)
        """
        if self._closed:
            raise ValueError("Pool is closed")

        chunk = chunksize if chunksize is not None else self.current_chunksize
        return self._pool.imap_unordered(func, iterable, chunksize=chunk)

    def close(self) -> None:
        """
        Prevent any more tasks from being submitted to the pool.

        Once closed, the pool cannot accept new work. Call join() to wait
        for all tasks to complete.
        """
        if not self._closed:
            self._pool.close()
            self._closed = True

    def terminate(self) -> None:
        """
        Stop all worker processes immediately without completing pending work.

        This is a forceful shutdown. Pending work will be lost.
        """
        self._pool.terminate()
        self._closed = True

    def join(self) -> None:
        """
        Wait for all worker processes to exit.

        Must call close() or terminate() before calling join().
        """
        self._pool.join()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures proper cleanup."""
        self.close()
        self.join()
        return False

    def get_stats(self) -> dict:
        """
        Get statistics about adaptation performance.

        Returns:
            Dictionary with adaptation statistics:
            - current_chunksize: Current chunk size
            - total_tasks_processed: Total items processed
            - adaptation_count: Number of times chunk size was adjusted
            - average_chunk_duration: Average chunk processing time
            - adaptation_enabled: Whether adaptation is enabled
        """
        with self._lock:
            return {
                'current_chunksize': self.current_chunksize,
                'total_tasks_processed': self._total_tasks_processed,
                'adaptation_count': self._adaptation_count,
                'average_chunk_duration': (
                    sum(self._chunk_durations) / len(self._chunk_durations)
                    if self._chunk_durations else 0.0
                ),
                'adaptation_enabled': self.enable_adaptation,
                'window_size': self.window_size,
                'num_chunks_in_window': len(self._chunk_durations)
            }


def create_adaptive_pool(
    n_jobs: int,
    initial_chunksize: int,
    enable_adaptation: bool = True,
    use_threads: bool = False,
    **kwargs
) -> AdaptiveChunkingPool:
    """
    Factory function to create an adaptive chunking pool.

    This is a convenience function that creates an AdaptiveChunkingPool
    with sensible defaults.

    Args:
        n_jobs: Number of worker processes/threads
        initial_chunksize: Starting chunk size
        enable_adaptation: Enable runtime adaptation (default: True)
        use_threads: Use threading instead of multiprocessing (default: False)
        **kwargs: Additional arguments passed to AdaptiveChunkingPool

    Returns:
        AdaptiveChunkingPool instance

    Example:
        >>> from amorsize import optimize
        >>> from amorsize.adaptive_chunking import create_adaptive_pool
        >>>
        >>> result = optimize(func, data)
        >>>
        >>> with create_adaptive_pool(result.n_jobs, result.chunksize) as pool:
        ...     results = pool.map(func, result.data)
    """
    return AdaptiveChunkingPool(
        n_jobs=n_jobs,
        initial_chunksize=initial_chunksize,
        enable_adaptation=enable_adaptation,
        use_threads=use_threads,
        **kwargs
    )
