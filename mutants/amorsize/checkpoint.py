"""
Checkpoint/Resume functionality for long-running parallel workloads.

This module provides the ability to save progress during execution and resume
from the last checkpoint on failure. This is particularly useful for:
- Long-running computations that may be interrupted
- Expensive workloads where re-computation should be avoided
- Production systems requiring fault tolerance beyond retry/circuit breaker
"""

import json
import os
import pickle
import time
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
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
class CheckpointPolicy:
    """
    Configuration for checkpoint behavior.
    
    Attributes:
        checkpoint_dir: Directory to store checkpoint files (default: "./checkpoints")
        checkpoint_interval: Number of items to process between checkpoints
                           (default: 100). Set to 0 to disable automatic checkpointing.
        checkpoint_name: Base name for checkpoint files (default: auto-generated from function)
        save_format: Format for checkpoint data ("json" or "pickle"). JSON is
                    human-readable but may not support all Python objects. Pickle
                    supports all objects but is binary (default: "pickle").
        keep_history: Number of checkpoint versions to keep (default: 2). Older
                     checkpoints are automatically cleaned up.
        auto_cleanup: Whether to automatically delete checkpoint on successful
                     completion (default: True).
    """
    checkpoint_dir: str = "./checkpoints"
    checkpoint_interval: int = 100
    checkpoint_name: Optional[str] = None
    save_format: str = "pickle"
    keep_history: int = 2
    auto_cleanup: bool = True
    
    def __post_init__(self):
        """Validate policy configuration."""
        if self.checkpoint_interval < 0:
            raise ValueError("checkpoint_interval must be >= 0")
        
        if self.save_format not in ("json", "pickle"):
            raise ValueError("save_format must be 'json' or 'pickle'")
        
        if self.keep_history < 1:
            raise ValueError("keep_history must be >= 1")


@dataclass
class CheckpointState:
    """
    State information stored in a checkpoint.
    
    Attributes:
        completed_indices: List of indices that have been processed
        results: List of results corresponding to completed indices
        total_items: Total number of items to process
        checkpoint_time: Timestamp when checkpoint was created
        n_jobs: Number of workers used
        chunksize: Chunk size used
        metadata: Additional metadata (executor type, etc.)
    """
    completed_indices: List[int]
    results: List[Any]
    total_items: int
    checkpoint_time: float
    n_jobs: int
    chunksize: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CheckpointState':
        """Create from dictionary after deserialization."""
        return cls(**data)


class CheckpointManager:
    """
    Manages checkpoint creation, loading, and cleanup.
    
    Thread-safe: Uses locks to prevent concurrent checkpoint operations.
    """
    
    def xǁCheckpointManagerǁ__init____mutmut_orig(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.policy.checkpoint_dir, exist_ok=True)
    
    def xǁCheckpointManagerǁ__init____mutmut_1(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = None
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.policy.checkpoint_dir, exist_ok=True)
    
    def xǁCheckpointManagerǁ__init____mutmut_2(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = None
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.policy.checkpoint_dir, exist_ok=True)
    
    def xǁCheckpointManagerǁ__init____mutmut_3(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(None, exist_ok=True)
    
    def xǁCheckpointManagerǁ__init____mutmut_4(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.policy.checkpoint_dir, exist_ok=None)
    
    def xǁCheckpointManagerǁ__init____mutmut_5(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(exist_ok=True)
    
    def xǁCheckpointManagerǁ__init____mutmut_6(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.policy.checkpoint_dir, )
    
    def xǁCheckpointManagerǁ__init____mutmut_7(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.policy.checkpoint_dir, exist_ok=False)
    
    xǁCheckpointManagerǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCheckpointManagerǁ__init____mutmut_1': xǁCheckpointManagerǁ__init____mutmut_1, 
        'xǁCheckpointManagerǁ__init____mutmut_2': xǁCheckpointManagerǁ__init____mutmut_2, 
        'xǁCheckpointManagerǁ__init____mutmut_3': xǁCheckpointManagerǁ__init____mutmut_3, 
        'xǁCheckpointManagerǁ__init____mutmut_4': xǁCheckpointManagerǁ__init____mutmut_4, 
        'xǁCheckpointManagerǁ__init____mutmut_5': xǁCheckpointManagerǁ__init____mutmut_5, 
        'xǁCheckpointManagerǁ__init____mutmut_6': xǁCheckpointManagerǁ__init____mutmut_6, 
        'xǁCheckpointManagerǁ__init____mutmut_7': xǁCheckpointManagerǁ__init____mutmut_7
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCheckpointManagerǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁCheckpointManagerǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁCheckpointManagerǁ__init____mutmut_orig)
    xǁCheckpointManagerǁ__init____mutmut_orig.__name__ = 'xǁCheckpointManagerǁ__init__'
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_orig(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_1(self, checkpoint_name: str, version: int = 1) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_2(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = None
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_3(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = "XX.pklXX" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_4(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".PKL" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_5(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format != "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_6(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "XXpickleXX" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_7(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "PICKLE" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_8(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else "XX.jsonXX"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_9(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".JSON"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_10(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version != 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_11(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version == 1:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_12(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = None
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_13(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = None
        
        return Path(self.policy.checkpoint_dir) / filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_14(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(self.policy.checkpoint_dir) * filename
    
    def xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_15(self, checkpoint_name: str, version: int = 0) -> Path:
        """
        Get path for checkpoint file.
        
        Args:
            checkpoint_name: Base name for checkpoint
            version: Version number (0 = latest, 1 = previous, etc.)
        
        Returns:
            Path to checkpoint file
        """
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        if version == 0:
            filename = f"{checkpoint_name}_checkpoint{ext}"
        else:
            filename = f"{checkpoint_name}_checkpoint_v{version}{ext}"
        
        return Path(None) / filename
    
    xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_1': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_1, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_2': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_2, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_3': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_3, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_4': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_4, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_5': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_5, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_6': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_6, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_7': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_7, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_8': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_8, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_9': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_9, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_10': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_10, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_11': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_11, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_12': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_12, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_13': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_13, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_14': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_14, 
        'xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_15': xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_15
    }
    
    def _get_checkpoint_path(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_orig"), object.__getattribute__(self, "xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _get_checkpoint_path.__signature__ = _mutmut_signature(xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_orig)
    xǁCheckpointManagerǁ_get_checkpoint_path__mutmut_orig.__name__ = 'xǁCheckpointManagerǁ_get_checkpoint_path'
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_orig(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__name__', 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_1(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = None
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_2(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(None, '__name__', 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_3(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, None, 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_4(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__name__', None)
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_5(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr('__name__', 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_6(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_7(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__name__', )
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_8(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, 'XX__name__XX', 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_9(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__NAME__', 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_10(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__name__', 'XXunknownXX')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_11(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__name__', 'UNKNOWN')
        
        # Add timestamp for uniqueness
        timestamp = int(time.time())
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_12(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__name__', 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = None
        
        return f"{func_name}_{timestamp}"
    
    def xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_13(self, func: Callable) -> str:
        """
        Generate checkpoint name from function.
        
        Args:
            func: Function being executed
        
        Returns:
            Checkpoint name
        """
        # Use function name if available
        func_name = getattr(func, '__name__', 'unknown')
        
        # Add timestamp for uniqueness
        timestamp = int(None)
        
        return f"{func_name}_{timestamp}"
    
    xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_1': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_1, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_2': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_2, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_3': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_3, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_4': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_4, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_5': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_5, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_6': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_6, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_7': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_7, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_8': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_8, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_9': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_9, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_10': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_10, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_11': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_11, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_12': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_12, 
        'xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_13': xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_13
    }
    
    def _generate_checkpoint_name(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_orig"), object.__getattribute__(self, "xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _generate_checkpoint_name.__signature__ = _mutmut_signature(xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_orig)
    xǁCheckpointManagerǁ_generate_checkpoint_name__mutmut_orig.__name__ = 'xǁCheckpointManagerǁ_generate_checkpoint_name'
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_orig(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_1(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = None
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_2(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(None)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_3(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(None, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_4(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, None):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_5(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_6(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, ):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_7(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 101):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_8(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = None
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_9(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(None, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_10(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, None)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_11(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_12(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, )
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_13(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        return  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_14(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(None, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_15(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, None, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_16(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, None):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_17(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_18(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_19(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, ):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_20(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history + 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_21(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 2, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_22(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 1, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_23(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, +1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_24(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -2):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_25(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = None
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_26(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(None, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_27(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, None)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_28(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_29(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, )
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_30(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = None
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_31(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(None, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_32(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, None)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_33(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_34(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, )
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_35(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i - 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_36(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 2)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_37(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(None)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_38(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = None
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_39(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(None, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_40(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, None)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_41(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_42(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, )
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_43(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 2)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_44(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(None)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_45(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format != "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_46(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "XXpickleXX":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_47(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "PICKLE":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_48(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(None, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_49(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, None) as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_50(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open('wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_51(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, ) as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_52(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'XXwbXX') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_53(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'WB') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_54(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(None, f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_55(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), None, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_56(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=None)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_57(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_58(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_59(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, )
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_60(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(None, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_61(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, None) as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_62(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open('w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_63(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, ) as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_64(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'XXwXX') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_65(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'W') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_66(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(None, f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_67(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), None, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_68(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=None)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_69(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_70(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_71(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, )
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_72(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=3)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(f"Failed to save checkpoint: {e}")
    
    def xǁCheckpointManagerǁsave_checkpoint__mutmut_73(
        self,
        checkpoint_name: str,
        state: CheckpointState
    ) -> Path:
        """
        Save checkpoint to disk.
        
        Thread-safe: Uses lock to prevent concurrent writes.
        
        Args:
            checkpoint_name: Name for checkpoint
            state: CheckpointState to save
        
        Returns:
            Path to saved checkpoint file
        
        Raises:
            IOError: If checkpoint cannot be saved
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            # Rotate existing checkpoints for history
            if checkpoint_path.exists():
                # First, delete versions beyond keep_history
                for i in range(self.policy.keep_history, 100):  # Check up to v100
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    if old_path.exists():
                        old_path.unlink()
                    else:
                        break  # No more versions to check
                
                # Rotate existing versions up by one
                for i in range(self.policy.keep_history - 1, 0, -1):
                    old_path = self._get_checkpoint_path(checkpoint_name, i)
                    new_path = self._get_checkpoint_path(checkpoint_name, i + 1)
                    if old_path.exists():
                        old_path.rename(new_path)
                
                # Move current checkpoint to v1
                v1_path = self._get_checkpoint_path(checkpoint_name, 1)
                checkpoint_path.rename(v1_path)
            
            # Save new checkpoint
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'wb') as f:
                        pickle.dump(state.to_dict(), f, protocol=pickle.HIGHEST_PROTOCOL)
                else:  # json
                    with open(checkpoint_path, 'w') as f:
                        json.dump(state.to_dict(), f, indent=2)
                
                return checkpoint_path
            
            except Exception as e:
                raise IOError(None)
    
    xǁCheckpointManagerǁsave_checkpoint__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCheckpointManagerǁsave_checkpoint__mutmut_1': xǁCheckpointManagerǁsave_checkpoint__mutmut_1, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_2': xǁCheckpointManagerǁsave_checkpoint__mutmut_2, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_3': xǁCheckpointManagerǁsave_checkpoint__mutmut_3, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_4': xǁCheckpointManagerǁsave_checkpoint__mutmut_4, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_5': xǁCheckpointManagerǁsave_checkpoint__mutmut_5, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_6': xǁCheckpointManagerǁsave_checkpoint__mutmut_6, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_7': xǁCheckpointManagerǁsave_checkpoint__mutmut_7, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_8': xǁCheckpointManagerǁsave_checkpoint__mutmut_8, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_9': xǁCheckpointManagerǁsave_checkpoint__mutmut_9, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_10': xǁCheckpointManagerǁsave_checkpoint__mutmut_10, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_11': xǁCheckpointManagerǁsave_checkpoint__mutmut_11, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_12': xǁCheckpointManagerǁsave_checkpoint__mutmut_12, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_13': xǁCheckpointManagerǁsave_checkpoint__mutmut_13, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_14': xǁCheckpointManagerǁsave_checkpoint__mutmut_14, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_15': xǁCheckpointManagerǁsave_checkpoint__mutmut_15, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_16': xǁCheckpointManagerǁsave_checkpoint__mutmut_16, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_17': xǁCheckpointManagerǁsave_checkpoint__mutmut_17, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_18': xǁCheckpointManagerǁsave_checkpoint__mutmut_18, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_19': xǁCheckpointManagerǁsave_checkpoint__mutmut_19, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_20': xǁCheckpointManagerǁsave_checkpoint__mutmut_20, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_21': xǁCheckpointManagerǁsave_checkpoint__mutmut_21, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_22': xǁCheckpointManagerǁsave_checkpoint__mutmut_22, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_23': xǁCheckpointManagerǁsave_checkpoint__mutmut_23, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_24': xǁCheckpointManagerǁsave_checkpoint__mutmut_24, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_25': xǁCheckpointManagerǁsave_checkpoint__mutmut_25, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_26': xǁCheckpointManagerǁsave_checkpoint__mutmut_26, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_27': xǁCheckpointManagerǁsave_checkpoint__mutmut_27, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_28': xǁCheckpointManagerǁsave_checkpoint__mutmut_28, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_29': xǁCheckpointManagerǁsave_checkpoint__mutmut_29, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_30': xǁCheckpointManagerǁsave_checkpoint__mutmut_30, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_31': xǁCheckpointManagerǁsave_checkpoint__mutmut_31, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_32': xǁCheckpointManagerǁsave_checkpoint__mutmut_32, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_33': xǁCheckpointManagerǁsave_checkpoint__mutmut_33, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_34': xǁCheckpointManagerǁsave_checkpoint__mutmut_34, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_35': xǁCheckpointManagerǁsave_checkpoint__mutmut_35, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_36': xǁCheckpointManagerǁsave_checkpoint__mutmut_36, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_37': xǁCheckpointManagerǁsave_checkpoint__mutmut_37, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_38': xǁCheckpointManagerǁsave_checkpoint__mutmut_38, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_39': xǁCheckpointManagerǁsave_checkpoint__mutmut_39, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_40': xǁCheckpointManagerǁsave_checkpoint__mutmut_40, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_41': xǁCheckpointManagerǁsave_checkpoint__mutmut_41, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_42': xǁCheckpointManagerǁsave_checkpoint__mutmut_42, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_43': xǁCheckpointManagerǁsave_checkpoint__mutmut_43, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_44': xǁCheckpointManagerǁsave_checkpoint__mutmut_44, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_45': xǁCheckpointManagerǁsave_checkpoint__mutmut_45, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_46': xǁCheckpointManagerǁsave_checkpoint__mutmut_46, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_47': xǁCheckpointManagerǁsave_checkpoint__mutmut_47, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_48': xǁCheckpointManagerǁsave_checkpoint__mutmut_48, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_49': xǁCheckpointManagerǁsave_checkpoint__mutmut_49, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_50': xǁCheckpointManagerǁsave_checkpoint__mutmut_50, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_51': xǁCheckpointManagerǁsave_checkpoint__mutmut_51, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_52': xǁCheckpointManagerǁsave_checkpoint__mutmut_52, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_53': xǁCheckpointManagerǁsave_checkpoint__mutmut_53, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_54': xǁCheckpointManagerǁsave_checkpoint__mutmut_54, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_55': xǁCheckpointManagerǁsave_checkpoint__mutmut_55, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_56': xǁCheckpointManagerǁsave_checkpoint__mutmut_56, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_57': xǁCheckpointManagerǁsave_checkpoint__mutmut_57, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_58': xǁCheckpointManagerǁsave_checkpoint__mutmut_58, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_59': xǁCheckpointManagerǁsave_checkpoint__mutmut_59, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_60': xǁCheckpointManagerǁsave_checkpoint__mutmut_60, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_61': xǁCheckpointManagerǁsave_checkpoint__mutmut_61, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_62': xǁCheckpointManagerǁsave_checkpoint__mutmut_62, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_63': xǁCheckpointManagerǁsave_checkpoint__mutmut_63, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_64': xǁCheckpointManagerǁsave_checkpoint__mutmut_64, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_65': xǁCheckpointManagerǁsave_checkpoint__mutmut_65, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_66': xǁCheckpointManagerǁsave_checkpoint__mutmut_66, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_67': xǁCheckpointManagerǁsave_checkpoint__mutmut_67, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_68': xǁCheckpointManagerǁsave_checkpoint__mutmut_68, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_69': xǁCheckpointManagerǁsave_checkpoint__mutmut_69, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_70': xǁCheckpointManagerǁsave_checkpoint__mutmut_70, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_71': xǁCheckpointManagerǁsave_checkpoint__mutmut_71, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_72': xǁCheckpointManagerǁsave_checkpoint__mutmut_72, 
        'xǁCheckpointManagerǁsave_checkpoint__mutmut_73': xǁCheckpointManagerǁsave_checkpoint__mutmut_73
    }
    
    def save_checkpoint(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCheckpointManagerǁsave_checkpoint__mutmut_orig"), object.__getattribute__(self, "xǁCheckpointManagerǁsave_checkpoint__mutmut_mutants"), args, kwargs, self)
        return result 
    
    save_checkpoint.__signature__ = _mutmut_signature(xǁCheckpointManagerǁsave_checkpoint__mutmut_orig)
    xǁCheckpointManagerǁsave_checkpoint__mutmut_orig.__name__ = 'xǁCheckpointManagerǁsave_checkpoint'
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_orig(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_1(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = None
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_2(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(None)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_3(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_4(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format != "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_5(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "XXpickleXX":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_6(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "PICKLE":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_7(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(None, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_8(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, None) as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_9(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open('rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_10(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, ) as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_11(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'XXrbXX') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_12(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'RB') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_13(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = None
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_14(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(None)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_15(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(None, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_16(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, None) as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_17(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open('r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_18(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, ) as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_19(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'XXrXX') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_20(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'R') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_21(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = None
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_22(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(None)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_23(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(None)
            
            except Exception as e:
                raise IOError(f"Failed to load checkpoint: {e}")
    
    def xǁCheckpointManagerǁload_checkpoint__mutmut_24(self, checkpoint_name: str) -> Optional[CheckpointState]:
        """
        Load checkpoint from disk.
        
        Thread-safe: Uses lock to prevent concurrent reads during cleanup.
        
        Args:
            checkpoint_name: Name of checkpoint to load
        
        Returns:
            CheckpointState if found, None otherwise
        
        Raises:
            IOError: If checkpoint exists but cannot be loaded
        """
        with self._lock:
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            
            if not checkpoint_path.exists():
                return None
            
            try:
                if self.policy.save_format == "pickle":
                    with open(checkpoint_path, 'rb') as f:
                        data = pickle.load(f)
                else:  # json
                    with open(checkpoint_path, 'r') as f:
                        data = json.load(f)
                
                return CheckpointState.from_dict(data)
            
            except Exception as e:
                raise IOError(None)
    
    xǁCheckpointManagerǁload_checkpoint__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCheckpointManagerǁload_checkpoint__mutmut_1': xǁCheckpointManagerǁload_checkpoint__mutmut_1, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_2': xǁCheckpointManagerǁload_checkpoint__mutmut_2, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_3': xǁCheckpointManagerǁload_checkpoint__mutmut_3, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_4': xǁCheckpointManagerǁload_checkpoint__mutmut_4, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_5': xǁCheckpointManagerǁload_checkpoint__mutmut_5, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_6': xǁCheckpointManagerǁload_checkpoint__mutmut_6, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_7': xǁCheckpointManagerǁload_checkpoint__mutmut_7, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_8': xǁCheckpointManagerǁload_checkpoint__mutmut_8, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_9': xǁCheckpointManagerǁload_checkpoint__mutmut_9, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_10': xǁCheckpointManagerǁload_checkpoint__mutmut_10, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_11': xǁCheckpointManagerǁload_checkpoint__mutmut_11, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_12': xǁCheckpointManagerǁload_checkpoint__mutmut_12, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_13': xǁCheckpointManagerǁload_checkpoint__mutmut_13, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_14': xǁCheckpointManagerǁload_checkpoint__mutmut_14, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_15': xǁCheckpointManagerǁload_checkpoint__mutmut_15, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_16': xǁCheckpointManagerǁload_checkpoint__mutmut_16, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_17': xǁCheckpointManagerǁload_checkpoint__mutmut_17, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_18': xǁCheckpointManagerǁload_checkpoint__mutmut_18, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_19': xǁCheckpointManagerǁload_checkpoint__mutmut_19, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_20': xǁCheckpointManagerǁload_checkpoint__mutmut_20, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_21': xǁCheckpointManagerǁload_checkpoint__mutmut_21, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_22': xǁCheckpointManagerǁload_checkpoint__mutmut_22, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_23': xǁCheckpointManagerǁload_checkpoint__mutmut_23, 
        'xǁCheckpointManagerǁload_checkpoint__mutmut_24': xǁCheckpointManagerǁload_checkpoint__mutmut_24
    }
    
    def load_checkpoint(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCheckpointManagerǁload_checkpoint__mutmut_orig"), object.__getattribute__(self, "xǁCheckpointManagerǁload_checkpoint__mutmut_mutants"), args, kwargs, self)
        return result 
    
    load_checkpoint.__signature__ = _mutmut_signature(xǁCheckpointManagerǁload_checkpoint__mutmut_orig)
    xǁCheckpointManagerǁload_checkpoint__mutmut_orig.__name__ = 'xǁCheckpointManagerǁload_checkpoint'
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_orig(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_1(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = None
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_2(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 1
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_3(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = None
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_4(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(None)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_5(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count = 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_6(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count -= 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_7(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 2
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_8(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(None, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_9(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, None):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_10(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_11(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, ):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_12(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(2, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_13(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history - 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_14(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 2):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_15(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = None
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_16(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(None, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_17(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, None)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_18(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_19(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, )
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_20(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count = 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_21(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count -= 1
            
            return deleted_count
    
    def xǁCheckpointManagerǁdelete_checkpoint__mutmut_22(self, checkpoint_name: str) -> int:
        """
        Delete checkpoint and all its versions.
        
        Thread-safe: Uses lock to prevent concurrent operations.
        
        Args:
            checkpoint_name: Name of checkpoint to delete
        
        Returns:
            Number of checkpoint files deleted
        """
        with self._lock:
            deleted_count = 0
            
            # Delete main checkpoint
            checkpoint_path = self._get_checkpoint_path(checkpoint_name)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                deleted_count += 1
            
            # Delete versioned checkpoints
            for version in range(1, self.policy.keep_history + 1):
                version_path = self._get_checkpoint_path(checkpoint_name, version)
                if version_path.exists():
                    version_path.unlink()
                    deleted_count += 2
            
            return deleted_count
    
    xǁCheckpointManagerǁdelete_checkpoint__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCheckpointManagerǁdelete_checkpoint__mutmut_1': xǁCheckpointManagerǁdelete_checkpoint__mutmut_1, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_2': xǁCheckpointManagerǁdelete_checkpoint__mutmut_2, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_3': xǁCheckpointManagerǁdelete_checkpoint__mutmut_3, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_4': xǁCheckpointManagerǁdelete_checkpoint__mutmut_4, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_5': xǁCheckpointManagerǁdelete_checkpoint__mutmut_5, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_6': xǁCheckpointManagerǁdelete_checkpoint__mutmut_6, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_7': xǁCheckpointManagerǁdelete_checkpoint__mutmut_7, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_8': xǁCheckpointManagerǁdelete_checkpoint__mutmut_8, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_9': xǁCheckpointManagerǁdelete_checkpoint__mutmut_9, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_10': xǁCheckpointManagerǁdelete_checkpoint__mutmut_10, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_11': xǁCheckpointManagerǁdelete_checkpoint__mutmut_11, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_12': xǁCheckpointManagerǁdelete_checkpoint__mutmut_12, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_13': xǁCheckpointManagerǁdelete_checkpoint__mutmut_13, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_14': xǁCheckpointManagerǁdelete_checkpoint__mutmut_14, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_15': xǁCheckpointManagerǁdelete_checkpoint__mutmut_15, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_16': xǁCheckpointManagerǁdelete_checkpoint__mutmut_16, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_17': xǁCheckpointManagerǁdelete_checkpoint__mutmut_17, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_18': xǁCheckpointManagerǁdelete_checkpoint__mutmut_18, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_19': xǁCheckpointManagerǁdelete_checkpoint__mutmut_19, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_20': xǁCheckpointManagerǁdelete_checkpoint__mutmut_20, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_21': xǁCheckpointManagerǁdelete_checkpoint__mutmut_21, 
        'xǁCheckpointManagerǁdelete_checkpoint__mutmut_22': xǁCheckpointManagerǁdelete_checkpoint__mutmut_22
    }
    
    def delete_checkpoint(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCheckpointManagerǁdelete_checkpoint__mutmut_orig"), object.__getattribute__(self, "xǁCheckpointManagerǁdelete_checkpoint__mutmut_mutants"), args, kwargs, self)
        return result 
    
    delete_checkpoint.__signature__ = _mutmut_signature(xǁCheckpointManagerǁdelete_checkpoint__mutmut_orig)
    xǁCheckpointManagerǁdelete_checkpoint__mutmut_orig.__name__ = 'xǁCheckpointManagerǁdelete_checkpoint'
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_orig(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_1(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = None
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_2(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(None)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_3(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_4(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = None
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_5(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = None
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_6(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = "XX.pklXX" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_7(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".PKL" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_8(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format != "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_9(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "XXpickleXX" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_10(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "PICKLE" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_11(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else "XX.jsonXX"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_12(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".JSON"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_13(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(None):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_14(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = None
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_15(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith(None):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_16(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("XX_checkpointXX"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_17(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_CHECKPOINT"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_18(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = None  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_19(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:+11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_20(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-12]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_21(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "XX_checkpoint_vXX" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_22(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_CHECKPOINT_V" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_23(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" not in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_24(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = None
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_25(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split(None)[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_26(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("XX_checkpoint_vXX")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_27(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_CHECKPOINT_V")[0]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_28(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[1]
            
            checkpoints.add(name)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_29(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(None)
        
        return sorted(checkpoints)
    
    def xǁCheckpointManagerǁlist_checkpoints__mutmut_30(self) -> List[str]:
        """
        List all available checkpoints in the checkpoint directory.
        
        Returns:
            List of checkpoint names (without extensions or version suffixes)
        """
        checkpoint_dir = Path(self.policy.checkpoint_dir)
        if not checkpoint_dir.exists():
            return []
        
        checkpoints = set()
        ext = ".pkl" if self.policy.save_format == "pickle" else ".json"
        
        for file in checkpoint_dir.glob(f"*{ext}"):
            # Remove extension and version suffix
            name = file.stem
            if name.endswith("_checkpoint"):
                name = name[:-11]  # Remove "_checkpoint"
            elif "_checkpoint_v" in name:
                name = name.split("_checkpoint_v")[0]
            
            checkpoints.add(name)
        
        return sorted(None)
    
    xǁCheckpointManagerǁlist_checkpoints__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁCheckpointManagerǁlist_checkpoints__mutmut_1': xǁCheckpointManagerǁlist_checkpoints__mutmut_1, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_2': xǁCheckpointManagerǁlist_checkpoints__mutmut_2, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_3': xǁCheckpointManagerǁlist_checkpoints__mutmut_3, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_4': xǁCheckpointManagerǁlist_checkpoints__mutmut_4, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_5': xǁCheckpointManagerǁlist_checkpoints__mutmut_5, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_6': xǁCheckpointManagerǁlist_checkpoints__mutmut_6, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_7': xǁCheckpointManagerǁlist_checkpoints__mutmut_7, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_8': xǁCheckpointManagerǁlist_checkpoints__mutmut_8, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_9': xǁCheckpointManagerǁlist_checkpoints__mutmut_9, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_10': xǁCheckpointManagerǁlist_checkpoints__mutmut_10, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_11': xǁCheckpointManagerǁlist_checkpoints__mutmut_11, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_12': xǁCheckpointManagerǁlist_checkpoints__mutmut_12, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_13': xǁCheckpointManagerǁlist_checkpoints__mutmut_13, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_14': xǁCheckpointManagerǁlist_checkpoints__mutmut_14, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_15': xǁCheckpointManagerǁlist_checkpoints__mutmut_15, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_16': xǁCheckpointManagerǁlist_checkpoints__mutmut_16, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_17': xǁCheckpointManagerǁlist_checkpoints__mutmut_17, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_18': xǁCheckpointManagerǁlist_checkpoints__mutmut_18, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_19': xǁCheckpointManagerǁlist_checkpoints__mutmut_19, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_20': xǁCheckpointManagerǁlist_checkpoints__mutmut_20, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_21': xǁCheckpointManagerǁlist_checkpoints__mutmut_21, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_22': xǁCheckpointManagerǁlist_checkpoints__mutmut_22, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_23': xǁCheckpointManagerǁlist_checkpoints__mutmut_23, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_24': xǁCheckpointManagerǁlist_checkpoints__mutmut_24, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_25': xǁCheckpointManagerǁlist_checkpoints__mutmut_25, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_26': xǁCheckpointManagerǁlist_checkpoints__mutmut_26, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_27': xǁCheckpointManagerǁlist_checkpoints__mutmut_27, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_28': xǁCheckpointManagerǁlist_checkpoints__mutmut_28, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_29': xǁCheckpointManagerǁlist_checkpoints__mutmut_29, 
        'xǁCheckpointManagerǁlist_checkpoints__mutmut_30': xǁCheckpointManagerǁlist_checkpoints__mutmut_30
    }
    
    def list_checkpoints(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁCheckpointManagerǁlist_checkpoints__mutmut_orig"), object.__getattribute__(self, "xǁCheckpointManagerǁlist_checkpoints__mutmut_mutants"), args, kwargs, self)
        return result 
    
    list_checkpoints.__signature__ = _mutmut_signature(xǁCheckpointManagerǁlist_checkpoints__mutmut_orig)
    xǁCheckpointManagerǁlist_checkpoints__mutmut_orig.__name__ = 'xǁCheckpointManagerǁlist_checkpoints'


def create_checkpoint_wrapper(
    func: Callable[[Any], Any],
    checkpoint_manager: CheckpointManager,
    checkpoint_name: str,
    state: CheckpointState,
    checkpoint_interval: int
) -> Callable[[Any], Any]:
    """
    Create a wrapper function that checkpoints progress periodically.
    
    Note: This is a helper for checkpoint integration. The actual checkpointing
    logic is handled in the executor to avoid pickling issues with closures.
    
    Args:
        func: Original function to wrap
        checkpoint_manager: Manager for checkpoint operations
        checkpoint_name: Name for checkpoint files
        state: Checkpoint state to update
        checkpoint_interval: Number of items between checkpoints
    
    Returns:
        Wrapped function (same signature as original)
    """
    # Note: In practice, checkpointing needs to be handled at the executor level
    # rather than wrapping individual function calls, because:
    # 1. Function wrappers with closures cannot be pickled for multiprocessing
    # 2. Checkpoint decisions need access to global state (completed count)
    # 3. Thread safety requires coordination at executor level
    #
    # This function is kept as a design reference but not used in practice.
    # The actual implementation is in the executor module.
    return func


def x_get_pending_items__mutmut_orig(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_1(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = None
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_2(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(None) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_3(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_4(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = None
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_5(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is not None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_6(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(None), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_7(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(None)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_8(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = None
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_9(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(None)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_10(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = None
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_11(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(None) if i not in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_12(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i in completed_set]
    pending_items = [data_list[i] for i in pending_indices]
    
    return pending_indices, pending_items


def x_get_pending_items__mutmut_13(
    data: Union[List, range],
    checkpoint_state: Optional[CheckpointState]
) -> Tuple[List[int], List[Any]]:
    """
    Get list of pending (not yet processed) items based on checkpoint state.
    
    Args:
        data: Original input data
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
    
    Returns:
        Tuple of (pending_indices, pending_items) where:
        - pending_indices: List of indices that still need processing
        - pending_items: List of data items at those indices
    """
    # Convert data to list for indexing
    data_list = list(data) if not isinstance(data, list) else data
    total_items = len(data_list)
    
    if checkpoint_state is None:
        # No checkpoint - process everything
        return list(range(total_items)), data_list
    
    # Filter out already completed indices
    completed_set = set(checkpoint_state.completed_indices)
    pending_indices = [i for i in range(total_items) if i not in completed_set]
    pending_items = None
    
    return pending_indices, pending_items

x_get_pending_items__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_pending_items__mutmut_1': x_get_pending_items__mutmut_1, 
    'x_get_pending_items__mutmut_2': x_get_pending_items__mutmut_2, 
    'x_get_pending_items__mutmut_3': x_get_pending_items__mutmut_3, 
    'x_get_pending_items__mutmut_4': x_get_pending_items__mutmut_4, 
    'x_get_pending_items__mutmut_5': x_get_pending_items__mutmut_5, 
    'x_get_pending_items__mutmut_6': x_get_pending_items__mutmut_6, 
    'x_get_pending_items__mutmut_7': x_get_pending_items__mutmut_7, 
    'x_get_pending_items__mutmut_8': x_get_pending_items__mutmut_8, 
    'x_get_pending_items__mutmut_9': x_get_pending_items__mutmut_9, 
    'x_get_pending_items__mutmut_10': x_get_pending_items__mutmut_10, 
    'x_get_pending_items__mutmut_11': x_get_pending_items__mutmut_11, 
    'x_get_pending_items__mutmut_12': x_get_pending_items__mutmut_12, 
    'x_get_pending_items__mutmut_13': x_get_pending_items__mutmut_13
}

def get_pending_items(*args, **kwargs):
    result = _mutmut_trampoline(x_get_pending_items__mutmut_orig, x_get_pending_items__mutmut_mutants, args, kwargs)
    return result 

get_pending_items.__signature__ = _mutmut_signature(x_get_pending_items__mutmut_orig)
x_get_pending_items__mutmut_orig.__name__ = 'x_get_pending_items'


def x_merge_results__mutmut_orig(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_1(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is not None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_2(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = None
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_3(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] / total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_4(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(None, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_5(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, None):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_6(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_7(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, ):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_8(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx <= total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_9(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = None
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_10(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(None, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_11(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, None):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_12(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_13(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, ):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_14(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx <= total_items:  # Safety check
            final_results[idx] = result
    
    return final_results


def x_merge_results__mutmut_15(
    new_results: List[Any],
    pending_indices: List[int],
    checkpoint_state: Optional[CheckpointState],
    total_items: int
) -> List[Any]:
    """
    Merge new results with checkpoint results to produce final output.
    
    Args:
        new_results: Results from processing pending items
        pending_indices: Indices of the pending items
        checkpoint_state: Loaded checkpoint state (None if starting fresh)
        total_items: Total number of items in original data
    
    Returns:
        Complete list of results in original order
    """
    # If no checkpoint, just return new results
    if checkpoint_state is None:
        return new_results
    
    # Create result array with None placeholders
    final_results = [None] * total_items
    
    # Fill in checkpointed results
    for idx, result in zip(checkpoint_state.completed_indices, checkpoint_state.results):
        if idx < total_items:  # Safety check
            final_results[idx] = result
    
    # Fill in new results
    for idx, result in zip(pending_indices, new_results):
        if idx < total_items:  # Safety check
            final_results[idx] = None
    
    return final_results

x_merge_results__mutmut_mutants : ClassVar[MutantDict] = {
'x_merge_results__mutmut_1': x_merge_results__mutmut_1, 
    'x_merge_results__mutmut_2': x_merge_results__mutmut_2, 
    'x_merge_results__mutmut_3': x_merge_results__mutmut_3, 
    'x_merge_results__mutmut_4': x_merge_results__mutmut_4, 
    'x_merge_results__mutmut_5': x_merge_results__mutmut_5, 
    'x_merge_results__mutmut_6': x_merge_results__mutmut_6, 
    'x_merge_results__mutmut_7': x_merge_results__mutmut_7, 
    'x_merge_results__mutmut_8': x_merge_results__mutmut_8, 
    'x_merge_results__mutmut_9': x_merge_results__mutmut_9, 
    'x_merge_results__mutmut_10': x_merge_results__mutmut_10, 
    'x_merge_results__mutmut_11': x_merge_results__mutmut_11, 
    'x_merge_results__mutmut_12': x_merge_results__mutmut_12, 
    'x_merge_results__mutmut_13': x_merge_results__mutmut_13, 
    'x_merge_results__mutmut_14': x_merge_results__mutmut_14, 
    'x_merge_results__mutmut_15': x_merge_results__mutmut_15
}

def merge_results(*args, **kwargs):
    result = _mutmut_trampoline(x_merge_results__mutmut_orig, x_merge_results__mutmut_mutants, args, kwargs)
    return result 

merge_results.__signature__ = _mutmut_signature(x_merge_results__mutmut_orig)
x_merge_results__mutmut_orig.__name__ = 'x_merge_results'
