"""
History module for tracking and comparing optimization results over time.

This module provides functionality to:
- Save comparison results to disk with metadata
- Load and filter historical results
- Compare results across different runs or systems
- Track performance trends and detect regressions
"""

import json
import os
import platform
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from .comparison import ComparisonResult, ComparisonConfig
from .system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method


class HistoryEntry:
    """
    Container for a single historical result entry.
    
    Attributes:
        id: Unique identifier for this entry
        name: User-provided name for this result
        timestamp: ISO 8601 timestamp when result was saved
        result: The ComparisonResult object
        function_name: Name of the function that was compared
        data_size: Size of the dataset
        system_info: System information at time of measurement
        metadata: Additional user-provided metadata
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        timestamp: str,
        result: ComparisonResult,
        function_name: str,
        data_size: int,
        system_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.name = name
        self.timestamp = timestamp
        self.result = result
        self.function_name = function_name
        self.data_size = data_size
        self.system_info = system_info
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "function_name": self.function_name,
            "data_size": self.data_size,
            "system_info": self.system_info,
            "metadata": self.metadata,
            "result": self._serialize_result()
        }
    
    def _serialize_result(self) -> Dict[str, Any]:
        """Serialize ComparisonResult to dictionary."""
        return {
            "configs": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type
                }
                for config in self.result.configs
            ],
            "execution_times": self.result.execution_times,
            "speedups": self.result.speedups,
            "best_config_index": self.result.best_config_index,
            "recommendations": self.result.recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Create HistoryEntry from dictionary."""
        # Reconstruct ComparisonResult
        result_data = data["result"]
        configs = [
            ComparisonConfig(
                name=c["name"],
                n_jobs=c["n_jobs"],
                chunksize=c["chunksize"],
                executor_type=c["executor_type"]
            )
            for c in result_data["configs"]
        ]
        
        result = ComparisonResult(
            configs=configs,
            execution_times=result_data["execution_times"],
            speedups=result_data["speedups"],
            best_config_index=result_data["best_config_index"],
            recommendations=result_data.get("recommendations", [])
        )
        
        return cls(
            id=data["id"],
            name=data["name"],
            timestamp=data["timestamp"],
            result=result,
            function_name=data["function_name"],
            data_size=data["data_size"],
            system_info=data["system_info"],
            metadata=data.get("metadata", {})
        )


def get_system_fingerprint() -> Dict[str, Any]:
    """
    Get a fingerprint of the current system for comparison purposes.
    
    Returns:
        Dictionary containing system information
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "physical_cores": get_physical_cores(),
        "available_memory_gb": get_available_memory() / (1024**3),
        "multiprocessing_start_method": get_multiprocessing_start_method()
    }


def _generate_id(name: str, timestamp: str) -> str:
    """Generate a unique ID for a history entry."""
    hash_input = f"{name}_{timestamp}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()[:12]


def get_history_dir() -> Path:
    """
    Get the directory where history files are stored.
    
    Returns:
        Path to history directory (creates if doesn't exist)
    """
    # Store in user's home directory under .amorsize/history
    home = Path.home()
    history_dir = home / ".amorsize" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def save_result(
    result: ComparisonResult,
    name: str,
    function_name: str = "unknown",
    data_size: int = 0,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a comparison result to history.
    
    Args:
        result: ComparisonResult to save
        name: User-provided name for this result (e.g., "baseline", "v2.0", "optimized")
        function_name: Name of the function that was tested
        data_size: Size of the dataset that was used
        metadata: Optional additional metadata to store
    
    Returns:
        ID of the saved entry
    
    Example:
        >>> result = compare_strategies(func, data, configs)
        >>> entry_id = save_result(result, "v1.0-baseline", "my_func", 1000)
        >>> print(f"Saved as {entry_id}")
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    entry_id = _generate_id(name, timestamp)
    system_info = get_system_fingerprint()
    
    entry = HistoryEntry(
        id=entry_id,
        name=name,
        timestamp=timestamp,
        result=result,
        function_name=function_name,
        data_size=data_size,
        system_info=system_info,
        metadata=metadata
    )
    
    # Save to file
    history_dir = get_history_dir()
    filename = f"{entry_id}.json"
    filepath = history_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(entry.to_dict(), f, indent=2)
    
    return entry_id


def load_result(entry_id: str) -> Optional[HistoryEntry]:
    """
    Load a specific result from history by ID.
    
    Args:
        entry_id: ID of the entry to load
    
    Returns:
        HistoryEntry object, or None if not found
    
    Example:
        >>> entry = load_result("a1b2c3d4e5f6")
        >>> if entry:
        ...     print(f"Result: {entry.name} from {entry.timestamp}")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"
    
    if not filepath.exists():
        return None
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return HistoryEntry.from_dict(data)


def list_results(
    name_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> List[HistoryEntry]:
    """
    List all saved results, optionally filtered by name.
    
    Args:
        name_filter: If provided, only return results with names containing this substring
        limit: If provided, limit the number of results returned
    
    Returns:
        List of HistoryEntry objects, sorted by timestamp (newest first)
    
    Example:
        >>> entries = list_results(name_filter="baseline", limit=10)
        >>> for entry in entries:
        ...     print(f"{entry.id}: {entry.name} ({entry.timestamp})")
    """
    history_dir = get_history_dir()
    entries = []
    
    # Load all JSON files in history directory
    for filepath in history_dir.glob("*.json"):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            entry = HistoryEntry.from_dict(data)
            
            # Apply name filter if provided
            if name_filter is None or name_filter.lower() in entry.name.lower():
                entries.append(entry)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Skip malformed files
            continue
    
    # Sort by timestamp (newest first)
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    
    # Apply limit if provided
    if limit is not None:
        entries = entries[:limit]
    
    return entries


def delete_result(entry_id: str) -> bool:
    """
    Delete a result from history.
    
    Args:
        entry_id: ID of the entry to delete
    
    Returns:
        True if deleted, False if not found
    
    Example:
        >>> if delete_result("a1b2c3d4e5f6"):
        ...     print("Deleted successfully")
    """
    history_dir = get_history_dir()
    filepath = history_dir / f"{entry_id}.json"
    
    if filepath.exists():
        filepath.unlink()
        return True
    
    return False


def compare_entries(
    entry_id1: str,
    entry_id2: str
) -> Optional[Dict[str, Any]]:
    """
    Compare two historical results.
    
    Args:
        entry_id1: ID of first entry
        entry_id2: ID of second entry
    
    Returns:
        Dictionary containing comparison data, or None if either entry not found
    
    Example:
        >>> comparison = compare_entries("abc123", "def456")
        >>> if comparison:
        ...     print(f"Speedup change: {comparison['speedup_delta']:.2f}x")
    """
    entry1 = load_result(entry_id1)
    entry2 = load_result(entry_id2)
    
    if entry1 is None or entry2 is None:
        return None
    
    # Get best configurations from each result
    best_time1 = entry1.result.best_time
    best_speedup1 = entry1.result.speedups[entry1.result.best_config_index]
    
    best_time2 = entry2.result.best_time
    best_speedup2 = entry2.result.speedups[entry2.result.best_config_index]
    
    # Calculate deltas
    speedup_delta = best_speedup2 - best_speedup1
    time_delta = best_time2 - best_time1
    time_delta_percent = ((best_time2 - best_time1) / best_time1) * 100 if best_time1 > 0 else 0.0
    
    # Check if systems are the same
    same_system = (
        entry1.system_info.get("platform") == entry2.system_info.get("platform") and
        entry1.system_info.get("physical_cores") == entry2.system_info.get("physical_cores")
    )
    
    return {
        "entry1": {
            "id": entry1.id,
            "name": entry1.name,
            "timestamp": entry1.timestamp,
            "best_strategy": entry1.result.best_config.name,
            "speedup": best_speedup1,
            "execution_time": best_time1,
            "system": entry1.system_info
        },
        "entry2": {
            "id": entry2.id,
            "name": entry2.name,
            "timestamp": entry2.timestamp,
            "best_strategy": entry2.result.best_config.name,
            "speedup": best_speedup2,
            "execution_time": best_time2,
            "system": entry2.system_info
        },
        "comparison": {
            "speedup_delta": speedup_delta,
            "time_delta_seconds": time_delta,
            "time_delta_percent": time_delta_percent,
            "same_system": same_system,
            "is_regression": time_delta > 0  # Slower is a regression
        }
    }


def clear_history() -> int:
    """
    Clear all history entries.
    
    Returns:
        Number of entries deleted
    
    Warning:
        This cannot be undone!
    
    Example:
        >>> count = clear_history()
        >>> print(f"Deleted {count} entries")
    """
    history_dir = get_history_dir()
    count = 0
    
    for filepath in history_dir.glob("*.json"):
        try:
            filepath.unlink()
            count += 1
        except OSError:
            # Skip files that can't be deleted
            continue
    
    return count
