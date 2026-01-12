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
    
    def xǁDeadLetterQueueǁ__init____mutmut_orig(self, policy: Optional[DLQPolicy] = None):
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
    
    def xǁDeadLetterQueueǁ__init____mutmut_1(self, policy: Optional[DLQPolicy] = None):
        """
        Initialize the dead letter queue.
        
        Args:
            policy: DLQ configuration policy. If None, uses default policy.
        """
        self.policy = None
        self._entries: List[DLQEntry] = []
        self._lock = threading.Lock()
        
        # Create directory if auto_persist is enabled
        if self.policy.auto_persist:
            os.makedirs(self.policy.directory, exist_ok=True)
    
    def xǁDeadLetterQueueǁ__init____mutmut_2(self, policy: Optional[DLQPolicy] = None):
        """
        Initialize the dead letter queue.
        
        Args:
            policy: DLQ configuration policy. If None, uses default policy.
        """
        self.policy = policy and DLQPolicy()
        self._entries: List[DLQEntry] = []
        self._lock = threading.Lock()
        
        # Create directory if auto_persist is enabled
        if self.policy.auto_persist:
            os.makedirs(self.policy.directory, exist_ok=True)
    
    def xǁDeadLetterQueueǁ__init____mutmut_3(self, policy: Optional[DLQPolicy] = None):
        """
        Initialize the dead letter queue.
        
        Args:
            policy: DLQ configuration policy. If None, uses default policy.
        """
        self.policy = policy or DLQPolicy()
        self._entries: List[DLQEntry] = None
        self._lock = threading.Lock()
        
        # Create directory if auto_persist is enabled
        if self.policy.auto_persist:
            os.makedirs(self.policy.directory, exist_ok=True)
    
    def xǁDeadLetterQueueǁ__init____mutmut_4(self, policy: Optional[DLQPolicy] = None):
        """
        Initialize the dead letter queue.
        
        Args:
            policy: DLQ configuration policy. If None, uses default policy.
        """
        self.policy = policy or DLQPolicy()
        self._entries: List[DLQEntry] = []
        self._lock = None
        
        # Create directory if auto_persist is enabled
        if self.policy.auto_persist:
            os.makedirs(self.policy.directory, exist_ok=True)
    
    def xǁDeadLetterQueueǁ__init____mutmut_5(self, policy: Optional[DLQPolicy] = None):
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
            os.makedirs(None, exist_ok=True)
    
    def xǁDeadLetterQueueǁ__init____mutmut_6(self, policy: Optional[DLQPolicy] = None):
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
            os.makedirs(self.policy.directory, exist_ok=None)
    
    def xǁDeadLetterQueueǁ__init____mutmut_7(self, policy: Optional[DLQPolicy] = None):
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
            os.makedirs(exist_ok=True)
    
    def xǁDeadLetterQueueǁ__init____mutmut_8(self, policy: Optional[DLQPolicy] = None):
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
            os.makedirs(self.policy.directory, )
    
    def xǁDeadLetterQueueǁ__init____mutmut_9(self, policy: Optional[DLQPolicy] = None):
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
            os.makedirs(self.policy.directory, exist_ok=False)
    
    xǁDeadLetterQueueǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁ__init____mutmut_1': xǁDeadLetterQueueǁ__init____mutmut_1, 
        'xǁDeadLetterQueueǁ__init____mutmut_2': xǁDeadLetterQueueǁ__init____mutmut_2, 
        'xǁDeadLetterQueueǁ__init____mutmut_3': xǁDeadLetterQueueǁ__init____mutmut_3, 
        'xǁDeadLetterQueueǁ__init____mutmut_4': xǁDeadLetterQueueǁ__init____mutmut_4, 
        'xǁDeadLetterQueueǁ__init____mutmut_5': xǁDeadLetterQueueǁ__init____mutmut_5, 
        'xǁDeadLetterQueueǁ__init____mutmut_6': xǁDeadLetterQueueǁ__init____mutmut_6, 
        'xǁDeadLetterQueueǁ__init____mutmut_7': xǁDeadLetterQueueǁ__init____mutmut_7, 
        'xǁDeadLetterQueueǁ__init____mutmut_8': xǁDeadLetterQueueǁ__init____mutmut_8, 
        'xǁDeadLetterQueueǁ__init____mutmut_9': xǁDeadLetterQueueǁ__init____mutmut_9
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁ__init____mutmut_orig)
    xǁDeadLetterQueueǁ__init____mutmut_orig.__name__ = 'xǁDeadLetterQueueǁ__init__'
    
    def xǁDeadLetterQueueǁadd__mutmut_orig(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_1(
        self,
        item: Any,
        error: Exception,
        retry_count: int = 1,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_2(
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
        entry = None
        
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
    
    def xǁDeadLetterQueueǁadd__mutmut_3(
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
            item=None,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_4(
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
            error_type=None,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_5(
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
            error_message=None,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_6(
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
            timestamp=None,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_7(
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
            traceback=None,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_8(
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
            retry_count=None,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_9(
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
            metadata=None
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
    
    def xǁDeadLetterQueueǁadd__mutmut_10(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_11(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_12(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_13(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_14(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_15(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_16(
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
    
    def xǁDeadLetterQueueǁadd__mutmut_17(
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
            error_type=type(None).__name__,
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
    
    def xǁDeadLetterQueueǁadd__mutmut_18(
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
            error_message=str(None),
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
    
    def xǁDeadLetterQueueǁadd__mutmut_19(
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
            metadata=metadata and {}
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
    
    def xǁDeadLetterQueueǁadd__mutmut_20(
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
            self._entries.append(None)
            
            # Enforce size limit by removing oldest entries
            if self.policy.max_entries > 0 and len(self._entries) > self.policy.max_entries:
                # Remove oldest entries to stay within limit
                excess = len(self._entries) - self.policy.max_entries
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def xǁDeadLetterQueueǁadd__mutmut_21(
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
            if self.policy.max_entries > 0 or len(self._entries) > self.policy.max_entries:
                # Remove oldest entries to stay within limit
                excess = len(self._entries) - self.policy.max_entries
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def xǁDeadLetterQueueǁadd__mutmut_22(
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
            if self.policy.max_entries >= 0 and len(self._entries) > self.policy.max_entries:
                # Remove oldest entries to stay within limit
                excess = len(self._entries) - self.policy.max_entries
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def xǁDeadLetterQueueǁadd__mutmut_23(
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
            if self.policy.max_entries > 1 and len(self._entries) > self.policy.max_entries:
                # Remove oldest entries to stay within limit
                excess = len(self._entries) - self.policy.max_entries
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def xǁDeadLetterQueueǁadd__mutmut_24(
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
            if self.policy.max_entries > 0 and len(self._entries) >= self.policy.max_entries:
                # Remove oldest entries to stay within limit
                excess = len(self._entries) - self.policy.max_entries
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def xǁDeadLetterQueueǁadd__mutmut_25(
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
                excess = None
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def xǁDeadLetterQueueǁadd__mutmut_26(
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
                excess = len(self._entries) + self.policy.max_entries
                self._entries = self._entries[excess:]
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    def xǁDeadLetterQueueǁadd__mutmut_27(
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
                self._entries = None
            
            # Auto-persist if enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
    
    xǁDeadLetterQueueǁadd__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁadd__mutmut_1': xǁDeadLetterQueueǁadd__mutmut_1, 
        'xǁDeadLetterQueueǁadd__mutmut_2': xǁDeadLetterQueueǁadd__mutmut_2, 
        'xǁDeadLetterQueueǁadd__mutmut_3': xǁDeadLetterQueueǁadd__mutmut_3, 
        'xǁDeadLetterQueueǁadd__mutmut_4': xǁDeadLetterQueueǁadd__mutmut_4, 
        'xǁDeadLetterQueueǁadd__mutmut_5': xǁDeadLetterQueueǁadd__mutmut_5, 
        'xǁDeadLetterQueueǁadd__mutmut_6': xǁDeadLetterQueueǁadd__mutmut_6, 
        'xǁDeadLetterQueueǁadd__mutmut_7': xǁDeadLetterQueueǁadd__mutmut_7, 
        'xǁDeadLetterQueueǁadd__mutmut_8': xǁDeadLetterQueueǁadd__mutmut_8, 
        'xǁDeadLetterQueueǁadd__mutmut_9': xǁDeadLetterQueueǁadd__mutmut_9, 
        'xǁDeadLetterQueueǁadd__mutmut_10': xǁDeadLetterQueueǁadd__mutmut_10, 
        'xǁDeadLetterQueueǁadd__mutmut_11': xǁDeadLetterQueueǁadd__mutmut_11, 
        'xǁDeadLetterQueueǁadd__mutmut_12': xǁDeadLetterQueueǁadd__mutmut_12, 
        'xǁDeadLetterQueueǁadd__mutmut_13': xǁDeadLetterQueueǁadd__mutmut_13, 
        'xǁDeadLetterQueueǁadd__mutmut_14': xǁDeadLetterQueueǁadd__mutmut_14, 
        'xǁDeadLetterQueueǁadd__mutmut_15': xǁDeadLetterQueueǁadd__mutmut_15, 
        'xǁDeadLetterQueueǁadd__mutmut_16': xǁDeadLetterQueueǁadd__mutmut_16, 
        'xǁDeadLetterQueueǁadd__mutmut_17': xǁDeadLetterQueueǁadd__mutmut_17, 
        'xǁDeadLetterQueueǁadd__mutmut_18': xǁDeadLetterQueueǁadd__mutmut_18, 
        'xǁDeadLetterQueueǁadd__mutmut_19': xǁDeadLetterQueueǁadd__mutmut_19, 
        'xǁDeadLetterQueueǁadd__mutmut_20': xǁDeadLetterQueueǁadd__mutmut_20, 
        'xǁDeadLetterQueueǁadd__mutmut_21': xǁDeadLetterQueueǁadd__mutmut_21, 
        'xǁDeadLetterQueueǁadd__mutmut_22': xǁDeadLetterQueueǁadd__mutmut_22, 
        'xǁDeadLetterQueueǁadd__mutmut_23': xǁDeadLetterQueueǁadd__mutmut_23, 
        'xǁDeadLetterQueueǁadd__mutmut_24': xǁDeadLetterQueueǁadd__mutmut_24, 
        'xǁDeadLetterQueueǁadd__mutmut_25': xǁDeadLetterQueueǁadd__mutmut_25, 
        'xǁDeadLetterQueueǁadd__mutmut_26': xǁDeadLetterQueueǁadd__mutmut_26, 
        'xǁDeadLetterQueueǁadd__mutmut_27': xǁDeadLetterQueueǁadd__mutmut_27
    }
    
    def add(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁadd__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁadd__mutmut_mutants"), args, kwargs, self)
        return result 
    
    add.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁadd__mutmut_orig)
    xǁDeadLetterQueueǁadd__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁadd'
    
    def xǁDeadLetterQueueǁget_entries__mutmut_orig(self) -> List[DLQEntry]:
        """
        Get all entries in the queue.
        
        Returns:
            List of DLQEntry objects (copy, not reference to internal list)
        
        Thread Safety:
            Returns a copy to prevent external modification of internal state.
        """
        with self._lock:
            return list(self._entries)
    
    def xǁDeadLetterQueueǁget_entries__mutmut_1(self) -> List[DLQEntry]:
        """
        Get all entries in the queue.
        
        Returns:
            List of DLQEntry objects (copy, not reference to internal list)
        
        Thread Safety:
            Returns a copy to prevent external modification of internal state.
        """
        with self._lock:
            return list(None)
    
    xǁDeadLetterQueueǁget_entries__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁget_entries__mutmut_1': xǁDeadLetterQueueǁget_entries__mutmut_1
    }
    
    def get_entries(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁget_entries__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁget_entries__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_entries.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁget_entries__mutmut_orig)
    xǁDeadLetterQueueǁget_entries__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁget_entries'
    
    def size(self) -> int:
        """
        Get the number of entries in the queue.
        
        Returns:
            Number of failed items in the DLQ
        """
        with self._lock:
            return len(self._entries)
    
    def xǁDeadLetterQueueǁclear__mutmut_orig(self) -> int:
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
    
    def xǁDeadLetterQueueǁclear__mutmut_1(self) -> int:
        """
        Clear all entries from the queue.
        
        Returns:
            Number of entries that were cleared
        
        Thread Safety:
            Safe to call from multiple threads. Uses lock to prevent race conditions.
        """
        with self._lock:
            count = None
            self._entries.clear()
            
            # Persist empty state if auto-persist is enabled
            if self.policy.auto_persist:
                self._persist_unsafe()
            
            return count
    
    xǁDeadLetterQueueǁclear__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁclear__mutmut_1': xǁDeadLetterQueueǁclear__mutmut_1
    }
    
    def clear(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁclear__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁclear__mutmut_mutants"), args, kwargs, self)
        return result 
    
    clear.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁclear__mutmut_orig)
    xǁDeadLetterQueueǁclear__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁclear'
    
    def xǁDeadLetterQueueǁsave__mutmut_orig(self, filepath: Optional[str] = None) -> str:
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
    
    def xǁDeadLetterQueueǁsave__mutmut_1(self, filepath: Optional[str] = None) -> str:
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
            if filepath is not None:
                filepath = self._get_default_filepath()
            
            self._write_to_file_unsafe(filepath)
            return filepath
    
    def xǁDeadLetterQueueǁsave__mutmut_2(self, filepath: Optional[str] = None) -> str:
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
                filepath = None
            
            self._write_to_file_unsafe(filepath)
            return filepath
    
    def xǁDeadLetterQueueǁsave__mutmut_3(self, filepath: Optional[str] = None) -> str:
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
            
            self._write_to_file_unsafe(None)
            return filepath
    
    xǁDeadLetterQueueǁsave__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁsave__mutmut_1': xǁDeadLetterQueueǁsave__mutmut_1, 
        'xǁDeadLetterQueueǁsave__mutmut_2': xǁDeadLetterQueueǁsave__mutmut_2, 
        'xǁDeadLetterQueueǁsave__mutmut_3': xǁDeadLetterQueueǁsave__mutmut_3
    }
    
    def save(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁsave__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁsave__mutmut_mutants"), args, kwargs, self)
        return result 
    
    save.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁsave__mutmut_orig)
    xǁDeadLetterQueueǁsave__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁsave'
    
    def xǁDeadLetterQueueǁload__mutmut_orig(self, filepath: Optional[str] = None) -> int:
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
    
    def xǁDeadLetterQueueǁload__mutmut_1(self, filepath: Optional[str] = None) -> int:
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
            if filepath is not None:
                filepath = self._get_default_filepath()
            
            if not os.path.exists(filepath):
                raise IOError(f"DLQ file not found: {filepath}")
            
            loaded_entries = self._read_from_file_unsafe(filepath)
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def xǁDeadLetterQueueǁload__mutmut_2(self, filepath: Optional[str] = None) -> int:
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
                filepath = None
            
            if not os.path.exists(filepath):
                raise IOError(f"DLQ file not found: {filepath}")
            
            loaded_entries = self._read_from_file_unsafe(filepath)
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def xǁDeadLetterQueueǁload__mutmut_3(self, filepath: Optional[str] = None) -> int:
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
            
            if os.path.exists(filepath):
                raise IOError(f"DLQ file not found: {filepath}")
            
            loaded_entries = self._read_from_file_unsafe(filepath)
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def xǁDeadLetterQueueǁload__mutmut_4(self, filepath: Optional[str] = None) -> int:
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
            
            if not os.path.exists(None):
                raise IOError(f"DLQ file not found: {filepath}")
            
            loaded_entries = self._read_from_file_unsafe(filepath)
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def xǁDeadLetterQueueǁload__mutmut_5(self, filepath: Optional[str] = None) -> int:
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
                raise IOError(None)
            
            loaded_entries = self._read_from_file_unsafe(filepath)
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def xǁDeadLetterQueueǁload__mutmut_6(self, filepath: Optional[str] = None) -> int:
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
            
            loaded_entries = None
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def xǁDeadLetterQueueǁload__mutmut_7(self, filepath: Optional[str] = None) -> int:
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
            
            loaded_entries = self._read_from_file_unsafe(None)
            self._entries = loaded_entries
            return len(loaded_entries)
    
    def xǁDeadLetterQueueǁload__mutmut_8(self, filepath: Optional[str] = None) -> int:
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
            self._entries = None
            return len(loaded_entries)
    
    xǁDeadLetterQueueǁload__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁload__mutmut_1': xǁDeadLetterQueueǁload__mutmut_1, 
        'xǁDeadLetterQueueǁload__mutmut_2': xǁDeadLetterQueueǁload__mutmut_2, 
        'xǁDeadLetterQueueǁload__mutmut_3': xǁDeadLetterQueueǁload__mutmut_3, 
        'xǁDeadLetterQueueǁload__mutmut_4': xǁDeadLetterQueueǁload__mutmut_4, 
        'xǁDeadLetterQueueǁload__mutmut_5': xǁDeadLetterQueueǁload__mutmut_5, 
        'xǁDeadLetterQueueǁload__mutmut_6': xǁDeadLetterQueueǁload__mutmut_6, 
        'xǁDeadLetterQueueǁload__mutmut_7': xǁDeadLetterQueueǁload__mutmut_7, 
        'xǁDeadLetterQueueǁload__mutmut_8': xǁDeadLetterQueueǁload__mutmut_8
    }
    
    def load(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁload__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁload__mutmut_mutants"), args, kwargs, self)
        return result 
    
    load.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁload__mutmut_orig)
    xǁDeadLetterQueueǁload__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁload'
    
    def xǁDeadLetterQueueǁget_summary__mutmut_orig(self) -> Dict[str, Any]:
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_1(self) -> Dict[str, Any]:
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
            if self._entries:
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_2(self) -> Dict[str, Any]:
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
                    "XXtotal_entriesXX": 0,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_3(self) -> Dict[str, Any]:
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
                    "TOTAL_ENTRIES": 0,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_4(self) -> Dict[str, Any]:
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
                    "total_entries": 1,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_5(self) -> Dict[str, Any]:
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
                    "XXerror_typesXX": {},
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_6(self) -> Dict[str, Any]:
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
                    "ERROR_TYPES": {},
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_7(self) -> Dict[str, Any]:
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
                    "XXavg_retry_countXX": 0.0,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_8(self) -> Dict[str, Any]:
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
                    "AVG_RETRY_COUNT": 0.0,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_9(self) -> Dict[str, Any]:
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
                    "avg_retry_count": 1.0,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_10(self) -> Dict[str, Any]:
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
                    "XXoldest_timestampXX": None,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_11(self) -> Dict[str, Any]:
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
                    "OLDEST_TIMESTAMP": None,
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_12(self) -> Dict[str, Any]:
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
                    "XXnewest_timestampXX": None
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_13(self) -> Dict[str, Any]:
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
                    "NEWEST_TIMESTAMP": None
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_14(self) -> Dict[str, Any]:
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
            
            error_types: Dict[str, int] = None
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_15(self) -> Dict[str, Any]:
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
            total_retries = None
            
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_16(self) -> Dict[str, Any]:
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
            total_retries = 1
            
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
    
    def xǁDeadLetterQueueǁget_summary__mutmut_17(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = None
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_18(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = error_types.get(entry.error_type, 0) - 1
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_19(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = error_types.get(None, 0) + 1
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_20(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = error_types.get(entry.error_type, None) + 1
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_21(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = error_types.get(0) + 1
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_22(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = error_types.get(entry.error_type, ) + 1
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_23(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = error_types.get(entry.error_type, 1) + 1
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_24(self) -> Dict[str, Any]:
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
                error_types[entry.error_type] = error_types.get(entry.error_type, 0) + 2
                total_retries += entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_25(self) -> Dict[str, Any]:
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
                total_retries = entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_26(self) -> Dict[str, Any]:
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
                total_retries -= entry.retry_count
            
            return {
                "total_entries": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_27(self) -> Dict[str, Any]:
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
                "XXtotal_entriesXX": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_28(self) -> Dict[str, Any]:
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
                "TOTAL_ENTRIES": len(self._entries),
                "error_types": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_29(self) -> Dict[str, Any]:
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
                "XXerror_typesXX": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_30(self) -> Dict[str, Any]:
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
                "ERROR_TYPES": error_types,
                "avg_retry_count": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_31(self) -> Dict[str, Any]:
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
                "XXavg_retry_countXX": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_32(self) -> Dict[str, Any]:
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
                "AVG_RETRY_COUNT": total_retries / len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_33(self) -> Dict[str, Any]:
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
                "avg_retry_count": total_retries * len(self._entries),
                "oldest_timestamp": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_34(self) -> Dict[str, Any]:
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
                "XXoldest_timestampXX": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_35(self) -> Dict[str, Any]:
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
                "OLDEST_TIMESTAMP": min(e.timestamp for e in self._entries),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_36(self) -> Dict[str, Any]:
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
                "oldest_timestamp": min(None),
                "newest_timestamp": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_37(self) -> Dict[str, Any]:
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
                "XXnewest_timestampXX": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_38(self) -> Dict[str, Any]:
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
                "NEWEST_TIMESTAMP": max(e.timestamp for e in self._entries)
            }
    
    def xǁDeadLetterQueueǁget_summary__mutmut_39(self) -> Dict[str, Any]:
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
                "newest_timestamp": max(None)
            }
    
    xǁDeadLetterQueueǁget_summary__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁget_summary__mutmut_1': xǁDeadLetterQueueǁget_summary__mutmut_1, 
        'xǁDeadLetterQueueǁget_summary__mutmut_2': xǁDeadLetterQueueǁget_summary__mutmut_2, 
        'xǁDeadLetterQueueǁget_summary__mutmut_3': xǁDeadLetterQueueǁget_summary__mutmut_3, 
        'xǁDeadLetterQueueǁget_summary__mutmut_4': xǁDeadLetterQueueǁget_summary__mutmut_4, 
        'xǁDeadLetterQueueǁget_summary__mutmut_5': xǁDeadLetterQueueǁget_summary__mutmut_5, 
        'xǁDeadLetterQueueǁget_summary__mutmut_6': xǁDeadLetterQueueǁget_summary__mutmut_6, 
        'xǁDeadLetterQueueǁget_summary__mutmut_7': xǁDeadLetterQueueǁget_summary__mutmut_7, 
        'xǁDeadLetterQueueǁget_summary__mutmut_8': xǁDeadLetterQueueǁget_summary__mutmut_8, 
        'xǁDeadLetterQueueǁget_summary__mutmut_9': xǁDeadLetterQueueǁget_summary__mutmut_9, 
        'xǁDeadLetterQueueǁget_summary__mutmut_10': xǁDeadLetterQueueǁget_summary__mutmut_10, 
        'xǁDeadLetterQueueǁget_summary__mutmut_11': xǁDeadLetterQueueǁget_summary__mutmut_11, 
        'xǁDeadLetterQueueǁget_summary__mutmut_12': xǁDeadLetterQueueǁget_summary__mutmut_12, 
        'xǁDeadLetterQueueǁget_summary__mutmut_13': xǁDeadLetterQueueǁget_summary__mutmut_13, 
        'xǁDeadLetterQueueǁget_summary__mutmut_14': xǁDeadLetterQueueǁget_summary__mutmut_14, 
        'xǁDeadLetterQueueǁget_summary__mutmut_15': xǁDeadLetterQueueǁget_summary__mutmut_15, 
        'xǁDeadLetterQueueǁget_summary__mutmut_16': xǁDeadLetterQueueǁget_summary__mutmut_16, 
        'xǁDeadLetterQueueǁget_summary__mutmut_17': xǁDeadLetterQueueǁget_summary__mutmut_17, 
        'xǁDeadLetterQueueǁget_summary__mutmut_18': xǁDeadLetterQueueǁget_summary__mutmut_18, 
        'xǁDeadLetterQueueǁget_summary__mutmut_19': xǁDeadLetterQueueǁget_summary__mutmut_19, 
        'xǁDeadLetterQueueǁget_summary__mutmut_20': xǁDeadLetterQueueǁget_summary__mutmut_20, 
        'xǁDeadLetterQueueǁget_summary__mutmut_21': xǁDeadLetterQueueǁget_summary__mutmut_21, 
        'xǁDeadLetterQueueǁget_summary__mutmut_22': xǁDeadLetterQueueǁget_summary__mutmut_22, 
        'xǁDeadLetterQueueǁget_summary__mutmut_23': xǁDeadLetterQueueǁget_summary__mutmut_23, 
        'xǁDeadLetterQueueǁget_summary__mutmut_24': xǁDeadLetterQueueǁget_summary__mutmut_24, 
        'xǁDeadLetterQueueǁget_summary__mutmut_25': xǁDeadLetterQueueǁget_summary__mutmut_25, 
        'xǁDeadLetterQueueǁget_summary__mutmut_26': xǁDeadLetterQueueǁget_summary__mutmut_26, 
        'xǁDeadLetterQueueǁget_summary__mutmut_27': xǁDeadLetterQueueǁget_summary__mutmut_27, 
        'xǁDeadLetterQueueǁget_summary__mutmut_28': xǁDeadLetterQueueǁget_summary__mutmut_28, 
        'xǁDeadLetterQueueǁget_summary__mutmut_29': xǁDeadLetterQueueǁget_summary__mutmut_29, 
        'xǁDeadLetterQueueǁget_summary__mutmut_30': xǁDeadLetterQueueǁget_summary__mutmut_30, 
        'xǁDeadLetterQueueǁget_summary__mutmut_31': xǁDeadLetterQueueǁget_summary__mutmut_31, 
        'xǁDeadLetterQueueǁget_summary__mutmut_32': xǁDeadLetterQueueǁget_summary__mutmut_32, 
        'xǁDeadLetterQueueǁget_summary__mutmut_33': xǁDeadLetterQueueǁget_summary__mutmut_33, 
        'xǁDeadLetterQueueǁget_summary__mutmut_34': xǁDeadLetterQueueǁget_summary__mutmut_34, 
        'xǁDeadLetterQueueǁget_summary__mutmut_35': xǁDeadLetterQueueǁget_summary__mutmut_35, 
        'xǁDeadLetterQueueǁget_summary__mutmut_36': xǁDeadLetterQueueǁget_summary__mutmut_36, 
        'xǁDeadLetterQueueǁget_summary__mutmut_37': xǁDeadLetterQueueǁget_summary__mutmut_37, 
        'xǁDeadLetterQueueǁget_summary__mutmut_38': xǁDeadLetterQueueǁget_summary__mutmut_38, 
        'xǁDeadLetterQueueǁget_summary__mutmut_39': xǁDeadLetterQueueǁget_summary__mutmut_39
    }
    
    def get_summary(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁget_summary__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁget_summary__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_summary.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁget_summary__mutmut_orig)
    xǁDeadLetterQueueǁget_summary__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁget_summary'
    
    def xǁDeadLetterQueueǁ_persist_unsafe__mutmut_orig(self) -> None:
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
    
    def xǁDeadLetterQueueǁ_persist_unsafe__mutmut_1(self) -> None:
        """
        Internal method to persist to disk without acquiring lock.
        
        IMPORTANT: This method is NOT thread-safe. It must only be called
        from within a locked context (with self._lock held).
        """
        filepath = None
        try:
            self._write_to_file_unsafe(filepath)
        except Exception:
            # Silently ignore persistence errors to avoid disrupting the main workflow
            # The in-memory queue is still valid
            pass
    
    def xǁDeadLetterQueueǁ_persist_unsafe__mutmut_2(self) -> None:
        """
        Internal method to persist to disk without acquiring lock.
        
        IMPORTANT: This method is NOT thread-safe. It must only be called
        from within a locked context (with self._lock held).
        """
        filepath = self._get_default_filepath()
        try:
            self._write_to_file_unsafe(None)
        except Exception:
            # Silently ignore persistence errors to avoid disrupting the main workflow
            # The in-memory queue is still valid
            pass
    
    xǁDeadLetterQueueǁ_persist_unsafe__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁ_persist_unsafe__mutmut_1': xǁDeadLetterQueueǁ_persist_unsafe__mutmut_1, 
        'xǁDeadLetterQueueǁ_persist_unsafe__mutmut_2': xǁDeadLetterQueueǁ_persist_unsafe__mutmut_2
    }
    
    def _persist_unsafe(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁ_persist_unsafe__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁ_persist_unsafe__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _persist_unsafe.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁ_persist_unsafe__mutmut_orig)
    xǁDeadLetterQueueǁ_persist_unsafe__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁ_persist_unsafe'
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_orig(self, filepath: str) -> None:
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
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_1(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(None, exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_2(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=None)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_3(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_4(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), )
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_5(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(None), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_6(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(None)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_7(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=False)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_8(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format != DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_9(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = None
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_10(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(None, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_11(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, None) as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_12(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open('w') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_13(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, ) as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_14(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'XXwXX') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_15(self, filepath: str) -> None:
        """
        Write entries to file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        if self.policy.format == DLQFormat.JSON:
            # JSON format (human-readable)
            data = [entry.to_dict() for entry in self._entries]
            with open(filepath, 'W') as f:
                json.dump(data, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_16(self, filepath: str) -> None:
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
                json.dump(None, f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_17(self, filepath: str) -> None:
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
                json.dump(data, None, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_18(self, filepath: str) -> None:
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
                json.dump(data, f, indent=None)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_19(self, filepath: str) -> None:
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
                json.dump(f, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_20(self, filepath: str) -> None:
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
                json.dump(data, indent=2)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_21(self, filepath: str) -> None:
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
                json.dump(data, f, )
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_22(self, filepath: str) -> None:
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
                json.dump(data, f, indent=3)
        else:
            # Pickle format (binary, efficient)
            with open(filepath, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_23(self, filepath: str) -> None:
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
            with open(None, 'wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_24(self, filepath: str) -> None:
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
            with open(filepath, None) as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_25(self, filepath: str) -> None:
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
            with open('wb') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_26(self, filepath: str) -> None:
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
            with open(filepath, ) as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_27(self, filepath: str) -> None:
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
            with open(filepath, 'XXwbXX') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_28(self, filepath: str) -> None:
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
            with open(filepath, 'WB') as f:
                pickle.dump(self._entries, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_29(self, filepath: str) -> None:
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
                pickle.dump(None, f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_30(self, filepath: str) -> None:
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
                pickle.dump(self._entries, None)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_31(self, filepath: str) -> None:
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
                pickle.dump(f)
    
    def xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_32(self, filepath: str) -> None:
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
                pickle.dump(self._entries, )
    
    xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_1': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_1, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_2': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_2, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_3': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_3, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_4': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_4, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_5': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_5, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_6': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_6, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_7': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_7, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_8': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_8, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_9': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_9, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_10': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_10, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_11': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_11, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_12': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_12, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_13': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_13, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_14': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_14, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_15': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_15, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_16': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_16, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_17': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_17, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_18': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_18, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_19': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_19, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_20': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_20, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_21': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_21, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_22': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_22, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_23': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_23, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_24': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_24, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_25': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_25, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_26': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_26, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_27': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_27, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_28': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_28, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_29': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_29, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_30': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_30, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_31': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_31, 
        'xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_32': xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_32
    }
    
    def _write_to_file_unsafe(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _write_to_file_unsafe.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_orig)
    xǁDeadLetterQueueǁ_write_to_file_unsafe__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁ_write_to_file_unsafe'
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_orig(self, filepath: str) -> List[DLQEntry]:
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
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_1(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format != DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_2(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(None, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_3(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, None) as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_4(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open('r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_5(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, ) as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_6(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'XXrXX') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_7(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'R') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_8(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = None
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_9(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(None)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_10(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(None) for entry_dict in data]
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_11(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(None, 'rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_12(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, None) as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_13(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open('rb') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_14(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, ) as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_15(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'XXrbXX') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_16(self, filepath: str) -> List[DLQEntry]:
        """
        Read entries from file without acquiring lock.
        
        IMPORTANT: Not thread-safe. Must be called with lock held.
        """
        if self.policy.format == DLQFormat.JSON:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return [DLQEntry.from_dict(entry_dict) for entry_dict in data]
        else:
            with open(filepath, 'RB') as f:
                return pickle.load(f)
    
    def xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_17(self, filepath: str) -> List[DLQEntry]:
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
                return pickle.load(None)
    
    xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_1': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_1, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_2': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_2, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_3': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_3, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_4': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_4, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_5': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_5, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_6': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_6, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_7': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_7, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_8': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_8, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_9': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_9, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_10': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_10, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_11': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_11, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_12': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_12, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_13': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_13, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_14': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_14, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_15': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_15, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_16': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_16, 
        'xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_17': xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_17
    }
    
    def _read_from_file_unsafe(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _read_from_file_unsafe.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_orig)
    xǁDeadLetterQueueǁ_read_from_file_unsafe__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁ_read_from_file_unsafe'
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_orig(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(self.policy.directory, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_1(self) -> str:
        """Get default filepath based on policy."""
        extension = None
        return os.path.join(self.policy.directory, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_2(self) -> str:
        """Get default filepath based on policy."""
        extension = "XXjsonXX" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(self.policy.directory, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_3(self) -> str:
        """Get default filepath based on policy."""
        extension = "JSON" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(self.policy.directory, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_4(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format != DLQFormat.JSON else "pkl"
        return os.path.join(self.policy.directory, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_5(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "XXpklXX"
        return os.path.join(self.policy.directory, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_6(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "PKL"
        return os.path.join(self.policy.directory, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_7(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(None, f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_8(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(self.policy.directory, None)
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_9(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(f"dlq.{extension}")
    
    def xǁDeadLetterQueueǁ_get_default_filepath__mutmut_10(self) -> str:
        """Get default filepath based on policy."""
        extension = "json" if self.policy.format == DLQFormat.JSON else "pkl"
        return os.path.join(self.policy.directory, )
    
    xǁDeadLetterQueueǁ_get_default_filepath__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_1': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_1, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_2': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_2, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_3': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_3, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_4': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_4, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_5': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_5, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_6': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_6, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_7': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_7, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_8': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_8, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_9': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_9, 
        'xǁDeadLetterQueueǁ_get_default_filepath__mutmut_10': xǁDeadLetterQueueǁ_get_default_filepath__mutmut_10
    }
    
    def _get_default_filepath(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁDeadLetterQueueǁ_get_default_filepath__mutmut_orig"), object.__getattribute__(self, "xǁDeadLetterQueueǁ_get_default_filepath__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_default_filepath.__signature__ = _mutmut_signature(xǁDeadLetterQueueǁ_get_default_filepath__mutmut_orig)
    xǁDeadLetterQueueǁ_get_default_filepath__mutmut_orig.__name__ = 'xǁDeadLetterQueueǁ_get_default_filepath'


def x_replay_failed_items__mutmut_orig(
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


def x_replay_failed_items__mutmut_1(
    dlq: DeadLetterQueue,
    func: Callable[[Any], Any],
    clear_on_success: bool = False
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


def x_replay_failed_items__mutmut_2(
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
    entries = None
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


def x_replay_failed_items__mutmut_3(
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
    successful_results = None
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


def x_replay_failed_items__mutmut_4(
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
    still_failed = None
    
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


def x_replay_failed_items__mutmut_5(
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
            result = None
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


def x_replay_failed_items__mutmut_6(
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
            result = func(None)
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


def x_replay_failed_items__mutmut_7(
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
            successful_results.append(None)
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


def x_replay_failed_items__mutmut_8(
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
            entry.error_type = None
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


def x_replay_failed_items__mutmut_9(
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
            entry.error_type = type(None).__name__
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


def x_replay_failed_items__mutmut_10(
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
            entry.error_message = None
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


def x_replay_failed_items__mutmut_11(
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
            entry.error_message = str(None)
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


def x_replay_failed_items__mutmut_12(
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
            entry.timestamp = None
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


def x_replay_failed_items__mutmut_13(
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
            entry.retry_count = 1
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


def x_replay_failed_items__mutmut_14(
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
            entry.retry_count -= 1
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


def x_replay_failed_items__mutmut_15(
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
            entry.retry_count += 2
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


def x_replay_failed_items__mutmut_16(
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
            still_failed.append(None)
    
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


def x_replay_failed_items__mutmut_17(
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
            error_message = None
            error = Exception(error_message)
            
            dlq.add(
                entry.item,
                error,
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_18(
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
            error = None
            
            dlq.add(
                entry.item,
                error,
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_19(
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
            error = Exception(None)
            
            dlq.add(
                entry.item,
                error,
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_20(
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
                None,
                error,
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_21(
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
                None,
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_22(
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
                retry_count=None,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_23(
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
                metadata=None
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_24(
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
                error,
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_25(
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
                retry_count=entry.retry_count,
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_26(
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
                metadata=entry.metadata
            )
    
    return successful_results, still_failed


def x_replay_failed_items__mutmut_27(
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
                )
    
    return successful_results, still_failed

x_replay_failed_items__mutmut_mutants : ClassVar[MutantDict] = {
'x_replay_failed_items__mutmut_1': x_replay_failed_items__mutmut_1, 
    'x_replay_failed_items__mutmut_2': x_replay_failed_items__mutmut_2, 
    'x_replay_failed_items__mutmut_3': x_replay_failed_items__mutmut_3, 
    'x_replay_failed_items__mutmut_4': x_replay_failed_items__mutmut_4, 
    'x_replay_failed_items__mutmut_5': x_replay_failed_items__mutmut_5, 
    'x_replay_failed_items__mutmut_6': x_replay_failed_items__mutmut_6, 
    'x_replay_failed_items__mutmut_7': x_replay_failed_items__mutmut_7, 
    'x_replay_failed_items__mutmut_8': x_replay_failed_items__mutmut_8, 
    'x_replay_failed_items__mutmut_9': x_replay_failed_items__mutmut_9, 
    'x_replay_failed_items__mutmut_10': x_replay_failed_items__mutmut_10, 
    'x_replay_failed_items__mutmut_11': x_replay_failed_items__mutmut_11, 
    'x_replay_failed_items__mutmut_12': x_replay_failed_items__mutmut_12, 
    'x_replay_failed_items__mutmut_13': x_replay_failed_items__mutmut_13, 
    'x_replay_failed_items__mutmut_14': x_replay_failed_items__mutmut_14, 
    'x_replay_failed_items__mutmut_15': x_replay_failed_items__mutmut_15, 
    'x_replay_failed_items__mutmut_16': x_replay_failed_items__mutmut_16, 
    'x_replay_failed_items__mutmut_17': x_replay_failed_items__mutmut_17, 
    'x_replay_failed_items__mutmut_18': x_replay_failed_items__mutmut_18, 
    'x_replay_failed_items__mutmut_19': x_replay_failed_items__mutmut_19, 
    'x_replay_failed_items__mutmut_20': x_replay_failed_items__mutmut_20, 
    'x_replay_failed_items__mutmut_21': x_replay_failed_items__mutmut_21, 
    'x_replay_failed_items__mutmut_22': x_replay_failed_items__mutmut_22, 
    'x_replay_failed_items__mutmut_23': x_replay_failed_items__mutmut_23, 
    'x_replay_failed_items__mutmut_24': x_replay_failed_items__mutmut_24, 
    'x_replay_failed_items__mutmut_25': x_replay_failed_items__mutmut_25, 
    'x_replay_failed_items__mutmut_26': x_replay_failed_items__mutmut_26, 
    'x_replay_failed_items__mutmut_27': x_replay_failed_items__mutmut_27
}

def replay_failed_items(*args, **kwargs):
    result = _mutmut_trampoline(x_replay_failed_items__mutmut_orig, x_replay_failed_items__mutmut_mutants, args, kwargs)
    return result 

replay_failed_items.__signature__ = _mutmut_signature(x_replay_failed_items__mutmut_orig)
x_replay_failed_items__mutmut_orig.__name__ = 'x_replay_failed_items'
