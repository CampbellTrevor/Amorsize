"""
Dead Letter Queue (DLQ) for collecting permanently failed items.

This module provides infrastructure for handling items that fail even after
retry logic has been exhausted. It complements the retry and circuit breaker
features by providing a way to:
- Collect failed items with their error information
- Inspect failures for debugging and monitoring
- Replay failed items after fixing issues
- Persist failure information for auditing

Design Philosophy:
    - Standalone helper library (not integrated into execute() to avoid complexity)
    - Zero external dependencies (uses only stdlib)
    - Thread-safe for concurrent access
    - Flexible persistence (JSON for readability, Pickle for efficiency)
    - Composable with existing retry/circuit breaker patterns
"""

import json
import os
import pickle
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum


class DLQFormat(Enum):
    """Storage format for dead letter queue entries."""
    JSON = "json"
    PICKLE = "pickle"


@dataclass
class DLQPolicy:
    """
    Configuration policy for Dead Letter Queue behavior.
    
    Attributes:
        directory: Directory path for storing DLQ entries
        format: Storage format (JSON or Pickle)
        max_entries: Maximum number of entries to keep (0 = unlimited)
        include_traceback: Whether to include full exception tracebacks
        auto_persist: Whether to automatically persist entries to disk
    """
    directory: str = ".amorsize_dlq"
    format: DLQFormat = DLQFormat.JSON
    max_entries: int = 10000
    include_traceback: bool = True
    auto_persist: bool = True
    
    def __post_init__(self):
        """Validate policy configuration."""
        if not isinstance(self.directory, str) or not self.directory:
            raise ValueError("directory must be a non-empty string")
        
        if not isinstance(self.format, DLQFormat):
            raise ValueError("format must be a DLQFormat enum value")
        
        if not isinstance(self.max_entries, int) or self.max_entries < 0:
            raise ValueError("max_entries must be a non-negative integer")
        
        if not isinstance(self.include_traceback, bool):
            raise ValueError("include_traceback must be a boolean")
        
        if not isinstance(self.auto_persist, bool):
            raise ValueError("auto_persist must be a boolean")


@dataclass
class DLQEntry:
    """
    A single entry in the dead letter queue.
    
    Attributes:
        item: The original data item that failed
        error_type: The type of exception that occurred
        error_message: The exception message
        timestamp: Unix timestamp when the failure occurred
        traceback: Full exception traceback (if enabled)
        retry_count: Number of times the item was retried
        metadata: Optional additional metadata (e.g., function name, worker ID)
    """
    item: Any
    error_type: str
    error_message: str
    timestamp: float
    traceback: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entry to dictionary for JSON serialization.
        
        Note: Only works if item is JSON-serializable.
        """
        return {
            "item": self.item,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "traceback": self.traceback,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DLQEntry":
        """Create entry from dictionary (JSON deserialization)."""
        return cls(
            item=data["item"],
            error_type=data["error_type"],
            error_message=data["error_message"],
            timestamp=data["timestamp"],
            traceback=data.get("traceback"),
            retry_count=data.get("retry_count", 0),
            metadata=data.get("metadata", {})
        )


class DeadLetterQueue:
    """
    Thread-safe dead letter queue for collecting failed items.
    
    This class provides:
    - Adding failed items with error information
    - Listing and inspecting failures
    - Clearing the queue
    - Persisting to disk (JSON or Pickle)
    - Loading from disk
    - Size limiting with automatic pruning
    
    Thread Safety:
        All operations are thread-safe and can be called from multiple threads
        or processes concurrently.
    """
    
    def __init__(self, policy: Optional[DLQPolicy] = None):
        """
        Initialize the dead letter queue.
        
        Args:
            policy: DLQ configuration policy. If None, uses default policy.
        """
        self.policy = policy or DLQPolicy()
        self._entries: List[DLQEntry] = []
        self._lock = threading.Lock()
        
        # Create directory if auto_persist is enabled
        if self.policy.auto_persist:
            os.makedirs(self.policy.directory, exist_ok=True)
    
    def add(
        self,
        item: Any,
        error: Exception,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a failed item to the dead letter queue.
        
        Args:
            item: The data item that failed processing
            error: The exception that occurred
            retry_count: Number of times the item was retried before giving up
            metadata: Optional additional context (e.g., {'function': 'process_image'})
        
        Thread Safety:
            Safe to call from multiple threads. Uses lock to prevent race conditions.
        """
        entry = DLQEntry(
            item=item,
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=time.time(),
            traceback=traceback.format_exc() if self.policy.include_traceback else None,
            retry_count=retry_count,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._entries.append(entry)
            
            # Enforce size limit by removing oldest entries
            if self.policy.max_entries > 0 and len(self._entries) > self.policy.max_entries:
                # Remove oldest entries to stay within limit
                excess = len(self._entries) - self.policy.max_entries
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def get_entries(self) -> List[DLQEntry]:
        """
        Get all entries in the queue.
        
        Returns:
            List of DLQEntry objects (copy, not reference to internal list)
        
        Thread Safety:
            Returns a copy to prevent external modification of internal state.
        """
        with self._lock:
            return list(self._entries)
    
    def size(self) -> int:
        """
        Get the number of entries in the queue.
        
        Returns:
            Number of failed items in the DLQ
        """
        with self._lock:
            return len(self._entries)
    
    def clear(self) -> int:
        """
        Clear all entries from the queue.
        
        Returns:
            Number of entries that were cleared
        
        Thread Safety:
            Safe to call from multiple threads. Uses lock to prevent race conditions.
        """
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            
            # Persist empty state if auto-persist is enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
            
            return count
    
    def save(self, filepath: Optional[str] = None) -> str:
        """
        Persist the DLQ to disk.
        
        Args:
            filepath: Optional custom file path. If None, uses default based on policy.
        
        Returns:
            The filepath where the DLQ was saved
        
        Raises:
            IOError: If writing to disk fails
            ValueError: If JSON format is used but items are not JSON-serializable
        """
        with self._lock:
            if filepath is None:
                filepath = self._get_default_filepath()
            
            self._write_to_file_unsafe(filepath)
            return filepath
    
    def load(self, filepath: Optional[str] = None) -> int:
        """
        Load DLQ entries from disk.
        
        Args:
            filepath: Optional custom file path. If None, uses default based on policy.
        
        Returns:
            Number of entries loaded
        
        Raises:
            IOError: If reading from disk fails
            ValueError: If file format is invalid
        
        Note:
            This replaces current entries with loaded ones. Use clear() first if
            you want to append instead of replace.
        """
        with self._lock:
            if filepath is None:
                filepath = self._get_default_filepath()
            
            if not os.path.exists(filepath):
                raise IOError(f"DLQ file not found: {filepath}")
            
            loaded_entries = self._read_from_file_unsafe(filepath)
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about the DLQ.
        
        Returns:
            Dictionary with:
                - total_entries: Total number of failed items
                - error_types: Count of each error type
                - avg_retry_count: Average number of retries before failure
                - oldest_timestamp: Timestamp of oldest entry
                - newest_timestamp: Timestamp of newest entry
        """
        with self._lock:
            if not self._entries:
                return {
                    "total_entries": 0,
                    "error_types": {},
                    "avg_retry_count": 0.0,
                    "oldest_timestamp": None,
                    "newest_timestamp": None
                }
            
            error_types: Dict[str, int] = {}
            total_retries = 0
            
            for entry in self._entries:
                error_types[entry.error_type] = error_types.get(entry.error_type, 0) + 1
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def _persist_unsafe(self) -> None:
        """
        Internal method to persist to disk without acquiring lock.
        
        IMPORTANT: This method is NOT thread-safe. It must only be called
        from within a locked context (with self._lock held).
        """
        filepath = self._get_default_filepath()
        try:
            self._write_to_file_unsafe(filepath)
        except Exception:
            # Silently ignore persistence errors to avoid disrupting the main workflow
            # The in-memory queue is still valid
            pass
    
    def _write_to_file_unsafe(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def _read_from_file_unsafe(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def _get_default_filepath(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(self.policy.directory, f"dlq.{extension}")


def replay_failed_items(
    dlq: DeadLetterQueue,
    func: Callable[[Any], Any],
    clear_on_success: bool = True
) -> Tuple[List[Any], List[DLQEntry]]:
    """
    Replay all failed items through the function.
    
    This is a helper function to retry processing all items in the DLQ.
    Useful after fixing bugs or transient issues.
    
    Args:
        dlq: The dead letter queue containing failed items
        func: The function to retry processing with
        clear_on_success: If True, remove successfully processed items from DLQ
    
    Returns:
        Tuple of (successful_results, still_failed_entries)
        - successful_results: List of results for items that succeeded on replay
        - still_failed_entries: List of DLQEntry objects for items that failed again
    
    Example:
        >>> dlq = DeadLetterQueue()
        >>> # ... items fail and are added to DLQ ...
        >>> # After fixing the issue:
        >>> results, still_failed = replay_failed_items(dlq, process_item)
        >>> print(f"Recovered {len(results)} items, {len(still_failed)} still failing")
    """
    entries = dlq.get_entries()
    successful_results = []
    still_failed = []
    
    for entry in entries:
        try:
            result = func(entry.item)
            successful_results.append(result)
        except Exception as e:
            # Update entry with new failure information
            entry.error_type = type(e).__name__
            entry.error_message = str(e)
            entry.timestamp = time.time()
            entry.retry_count += 1
            still_failed.append(entry)
    
    # Clear DLQ and re-add only the items that still fail
    if clear_on_success:
        dlq.clear()
        for entry in still_failed:
            # Reconstruct error for proper add() call
            # We can't perfectly recreate the original exception, but we can
            # create a generic Exception with the stored information
            error_message = f"{entry.error_type}: {entry.error_message}"
            error = Exception(error_message)
            
            dlq.add(
                entry.item,
                error,
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed
