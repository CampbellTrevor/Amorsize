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
    
    def __init__(self, policy: CheckpointPolicy):
        """
        Initialize checkpoint manager.
        
        Args:
            policy: CheckpointPolicy configuration
        """
        self.policy = policy
        self._lock = threading.Lock()
        
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.policy.checkpoint_dir, exist_ok=True)
    
    def _get_checkpoint_path(self, checkpoint_name: str, version: int = 0) -> Path:
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
    
    def _generate_checkpoint_name(self, func: Callable) -> str:
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
    
    def save_checkpoint(
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
    
    def load_checkpoint(self, checkpoint_name: str) -> Optional[CheckpointState]:
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
    
    def delete_checkpoint(self, checkpoint_name: str) -> int:
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
    
    def list_checkpoints(self) -> List[str]:
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


def get_pending_items(
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


def merge_results(
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
