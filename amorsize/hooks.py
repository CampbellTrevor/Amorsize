"""
Execution hooks for custom callbacks during parallel execution.

This module provides a flexible callback system that allows users to:
- Monitor execution progress in real-time
- Collect custom metrics during parallel processing
- Integrate with external monitoring systems (Prometheus, Datadog, etc.)
- Handle execution events (worker start/end, chunk completion, errors)
- Report progress to users or logging systems

Design principles:
- Error isolation: Hook failures don't crash execution
- Thread-safe: Hooks can be called from multiple workers
- Non-invasive: Hooks add minimal overhead
- Composable: Multiple hooks can be registered for same event
"""

import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HookEvent(Enum):
    """Events that can trigger execution hooks."""
    
    PRE_EXECUTE = "pre_execute"           # Before parallel execution starts
    POST_EXECUTE = "post_execute"         # After parallel execution completes
    ON_WORKER_START = "on_worker_start"   # When a worker process starts
    ON_WORKER_END = "on_worker_end"       # When a worker process ends
    ON_CHUNK_COMPLETE = "on_chunk_complete"  # When a chunk finishes processing
    ON_ERROR = "on_error"                 # When an error occurs
    ON_PROGRESS = "on_progress"           # Periodic progress updates


@dataclass
class HookContext:
    """
    Context information passed to hooks.
    
    Contains all relevant information about the execution state at the
    time the hook is triggered. Not all fields are populated for all events.
    """
    
    # Event identification
    event: HookEvent
    timestamp: float = field(default_factory=time.time)
    
    # Execution parameters
    n_jobs: Optional[int] = None
    chunksize: Optional[int] = None
    total_items: Optional[int] = None
    
    # Progress tracking
    items_completed: int = 0
    items_remaining: int = 0
    percent_complete: float = 0.0
    elapsed_time: float = 0.0
    estimated_time_remaining: float = 0.0
    
    # Performance metrics
    throughput_items_per_sec: float = 0.0
    avg_item_time: float = 0.0
    
    # Worker information (for worker-specific events)
    worker_id: Optional[int] = None
    worker_count: int = 0
    
    # Chunk information (for chunk events)
    chunk_id: Optional[int] = None
    chunk_size: Optional[int] = None
    chunk_time: float = 0.0
    
    # Error information (for error events)
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Results information
    results_count: int = 0
    results_size_bytes: int = 0
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


# Type alias for hook callback functions
HookCallback = Callable[[HookContext], None]


class HookManager:
    """
    Manager for execution hooks.
    
    Provides a centralized system for registering, managing, and executing
    hooks at various points during parallel execution. Designed to be
    thread-safe and handle hook failures gracefully.
    
    Thread Safety:
        Uses a lock to protect hook registration and execution. Multiple
        threads can safely trigger hooks simultaneously.
    
    Error Isolation:
        If a hook raises an exception, it's caught and logged without
        interrupting execution. This prevents user hooks from breaking
        the optimization/execution pipeline.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the hook manager.
        
        Args:
            verbose: If True, log hook execution and errors to stderr
        """
        self._hooks: Dict[HookEvent, List[HookCallback]] = {
            event: [] for event in HookEvent
        }
        self._lock = threading.Lock()
        self._verbose = verbose
        self._hook_call_counts: Dict[HookEvent, int] = {
            event: 0 for event in HookEvent
        }
        self._hook_error_counts: Dict[HookEvent, int] = {
            event: 0 for event in HookEvent
        }
    
    def register(self, event: HookEvent, callback: HookCallback) -> None:
        """
        Register a callback for a specific event.
        
        Args:
            event: The event to hook into
            callback: Function to call when event occurs. Should accept
                     a HookContext parameter and return None.
        
        Example:
            >>> def on_progress(ctx: HookContext):
            ...     print(f"Progress: {ctx.percent_complete:.1f}%")
            >>> manager = HookManager()
            >>> manager.register(HookEvent.ON_PROGRESS, on_progress)
        """
        with self._lock:
            if callback not in self._hooks[event]:
                self._hooks[event].append(callback)
    
    def unregister(self, event: HookEvent, callback: HookCallback) -> bool:
        """
        Unregister a callback for a specific event.
        
        Args:
            event: The event to unhook from
            callback: The callback function to remove
        
        Returns:
            True if callback was found and removed, False otherwise
        """
        with self._lock:
            if callback in self._hooks[event]:
                self._hooks[event].remove(callback)
                return True
        return False
    
    def unregister_all(self, event: Optional[HookEvent] = None) -> int:
        """
        Unregister all callbacks for an event, or all events.
        
        Args:
            event: Specific event to clear, or None to clear all events
        
        Returns:
            Number of callbacks removed
        """
        count = 0
        with self._lock:
            if event is not None:
                count = len(self._hooks[event])
                self._hooks[event].clear()
            else:
                for event_type in HookEvent:
                    count += len(self._hooks[event_type])
                    self._hooks[event_type].clear()
        return count
    
    def trigger(self, context: HookContext) -> None:
        """
        Trigger all hooks registered for an event.
        
        Executes all callbacks registered for the event in context.event.
        If a callback raises an exception, it's caught and logged without
        interrupting other callbacks or the main execution.
        
        Args:
            context: Context information for the event
        """
        event = context.event
        
        # Get callbacks while holding lock (quick operation)
        with self._lock:
            callbacks = self._hooks[event].copy()
            self._hook_call_counts[event] += 1
        
        # Execute callbacks without holding lock (allows concurrent triggers)
        for callback in callbacks:
            try:
                callback(context)
            except Exception as e:
                # Isolate hook errors to prevent cascade failures
                with self._lock:
                    self._hook_error_counts[event] += 1
                
                if self._verbose:
                    error_info = f"Hook error in {event.value}: {type(e).__name__}: {e}"
                    tb = traceback.format_exc()
                    print(f"WARNING: {error_info}\n{tb}", file=sys.stderr)
    
    def has_hooks(self, event: HookEvent) -> bool:
        """
        Check if any hooks are registered for an event.
        
        Args:
            event: Event to check
        
        Returns:
            True if at least one hook is registered for the event
        """
        with self._lock:
            return len(self._hooks[event]) > 0
    
    def get_hook_count(self, event: HookEvent) -> int:
        """
        Get the number of hooks registered for an event.
        
        Args:
            event: Event to check
        
        Returns:
            Number of hooks registered for the event
        """
        with self._lock:
            return len(self._hooks[event])
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about hook usage.
        
        Returns:
            Dictionary with hook counts, call counts, and error counts
        """
        with self._lock:
            return {
                "hook_counts": {
                    event.value: len(callbacks)
                    for event, callbacks in self._hooks.items()
                },
                "call_counts": {
                    event.value: count
                    for event, count in self._hook_call_counts.items()
                },
                "error_counts": {
                    event.value: count
                    for event, count in self._hook_error_counts.items()
                    if count > 0
                }
            }


# Convenience functions for common hook patterns

def create_progress_hook(
    callback: Callable[[float, int, int], None],
    min_interval: float = 1.0
) -> HookCallback:
    """
    Create a progress reporting hook.
    
    Args:
        callback: Function(percent, completed, total) to call with progress
        min_interval: Minimum seconds between progress updates (throttling)
    
    Returns:
        Hook callback function
    
    Example:
        >>> def report_progress(percent, completed, total):
        ...     print(f"{percent:.1f}% ({completed}/{total})")
        >>> hook = create_progress_hook(report_progress, min_interval=0.5)
        >>> manager.register(HookEvent.ON_PROGRESS, hook)
    """
    last_call_time = [0.0]  # Mutable to allow closure modification
    
    def progress_hook(ctx: HookContext) -> None:
        current_time = ctx.timestamp
        if current_time - last_call_time[0] >= min_interval:
            total = ctx.total_items if ctx.total_items is not None else 0
            callback(ctx.percent_complete, ctx.items_completed, total)
            last_call_time[0] = current_time
    
    return progress_hook


def create_timing_hook(
    callback: Callable[[str, float], None]
) -> HookCallback:
    """
    Create a timing metrics hook.
    
    Args:
        callback: Function(event_name, elapsed_time) to call with timing
    
    Returns:
        Hook callback function
    
    Example:
        >>> def log_timing(event, elapsed):
        ...     print(f"{event}: {elapsed:.3f}s")
        >>> hook = create_timing_hook(log_timing)
        >>> manager.register(HookEvent.POST_EXECUTE, hook)
    """
    def timing_hook(ctx: HookContext) -> None:
        callback(ctx.event.value, ctx.elapsed_time)
    
    return timing_hook


def create_throughput_hook(
    callback: Callable[[float], None],
    min_interval: float = 5.0
) -> HookCallback:
    """
    Create a throughput monitoring hook.
    
    Args:
        callback: Function(items_per_second) to call with throughput
        min_interval: Minimum seconds between throughput reports
    
    Returns:
        Hook callback function
    
    Example:
        >>> def report_throughput(rate):
        ...     print(f"Processing rate: {rate:.1f} items/sec")
        >>> hook = create_throughput_hook(report_throughput, min_interval=10.0)
        >>> manager.register(HookEvent.ON_PROGRESS, hook)
    """
    last_call_time = [0.0]
    
    def throughput_hook(ctx: HookContext) -> None:
        current_time = ctx.timestamp
        if current_time - last_call_time[0] >= min_interval:
            callback(ctx.throughput_items_per_sec)
            last_call_time[0] = current_time
    
    return throughput_hook


def create_error_hook(
    callback: Callable[[Exception, str], None]
) -> HookCallback:
    """
    Create an error handling hook.
    
    Args:
        callback: Function(error, traceback_str) to call on errors
    
    Returns:
        Hook callback function
    
    Example:
        >>> def log_error(error, tb):
        ...     print(f"Error: {error}")
        ...     print(tb)
        >>> hook = create_error_hook(log_error)
        >>> manager.register(HookEvent.ON_ERROR, hook)
    """
    def error_hook(ctx: HookContext) -> None:
        if ctx.error is not None:
            callback(ctx.error, ctx.error_traceback or "")
    
    return error_hook
