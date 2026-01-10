"""
Optimization cache module for fast retrieval of previously computed results.

This module provides intelligent caching of optimization results to avoid
redundant dry-run sampling and benchmarking for workloads that have been
analyzed before. The cache uses a composite key based on function signature
and workload characteristics to determine cache hits.
"""

import hashlib
import json
import os
import pickle
import platform
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method


# Cache version - increment when cache format changes
CACHE_VERSION = 1

# Cache entry time-to-live (default: 7 days)
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


class CacheEntry:
    """
    Container for a cached optimization result.
    
    Attributes:
        n_jobs: Recommended number of workers
        chunksize: Recommended chunk size
        executor_type: "process" or "thread"
        estimated_speedup: Expected speedup
        reason: Explanation of recommendation
        warnings: List of warning messages
        timestamp: When this entry was created
        system_info: System configuration at cache time
        cache_version: Version of cache format
    """
    
    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        executor_type: str,
        estimated_speedup: float,
        reason: str,
        warnings: list,
        timestamp: float,
        system_info: Dict[str, Any],
        cache_version: int = CACHE_VERSION
    ):
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.executor_type = executor_type
        self.estimated_speedup = estimated_speedup
        self.reason = reason
        self.warnings = warnings
        self.timestamp = timestamp
        self.system_info = system_info
        self.cache_version = cache_version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "n_jobs": self.n_jobs,
            "chunksize": self.chunksize,
            "executor_type": self.executor_type,
            "estimated_speedup": self.estimated_speedup,
            "reason": self.reason,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
            "system_info": self.system_info,
            "cache_version": self.cache_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create CacheEntry from dictionary."""
        return cls(
            n_jobs=data["n_jobs"],
            chunksize=data["chunksize"],
            executor_type=data["executor_type"],
            estimated_speedup=data["estimated_speedup"],
            reason=data["reason"],
            warnings=data["warnings"],
            timestamp=data["timestamp"],
            system_info=data["system_info"],
            cache_version=data.get("cache_version", 1)
        )
    
    def is_expired(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
        """Check if this cache entry has expired."""
        age = time.time() - self.timestamp
        return age > ttl_seconds
    
    def is_system_compatible(self) -> bool:
        """
        Check if cached result is compatible with current system.
        
        Returns False if key system parameters have changed:
        - Physical core count
        - Multiprocessing start method
        - Available memory (within 20% tolerance)
        """
        current_cores = get_physical_cores()
        current_memory = get_available_memory()
        current_start_method = get_multiprocessing_start_method()
        
        cached_cores = self.system_info.get("physical_cores", 0)
        cached_memory = self.system_info.get("available_memory", 0)
        cached_start_method = self.system_info.get("start_method", "")
        
        # Check core count match
        if cached_cores != current_cores:
            return False
        
        # Check start method match
        if cached_start_method != current_start_method:
            return False
        
        # Check memory within 20% tolerance
        if cached_memory > 0:
            memory_ratio = current_memory / cached_memory
            if not (0.8 <= memory_ratio <= 1.2):
                return False
        
        return True


def get_cache_dir() -> Path:
    """
    Get the cache directory path.
    
    Returns:
        Path to cache directory (creates if doesn't exist)
    """
    # Use platform-appropriate cache directory
    if platform.system() == "Windows":
        cache_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif platform.system() == "Darwin":  # macOS
        cache_base = Path.home() / "Library" / "Caches"
    else:  # Linux and others
        cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    
    cache_dir = cache_base / "amorsize" / "optimization_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def compute_cache_key(func: Callable, data_size: int, avg_time_per_item: float) -> str:
    """
    Compute a cache key for a function and workload characteristics.
    
    The key is based on:
    1. Function bytecode hash (detects function changes)
    2. Data size (affects optimal chunksize)
    3. Average execution time per item (affects parallelization benefit)
    
    Args:
        func: Function to cache results for
        data_size: Number of items in the workload
        avg_time_per_item: Average execution time per item (seconds)
    
    Returns:
        SHA256 hash as hexadecimal string
    """
    # Hash function bytecode to detect changes
    try:
        func_code = func.__code__.co_code
        func_hash = hashlib.sha256(func_code).hexdigest()[:16]
    except AttributeError:
        # For built-in functions or methods without __code__
        func_hash = hashlib.sha256(str(func).encode()).hexdigest()[:16]
    
    # Create workload signature (bucketed to avoid over-specific keys)
    # Bucket data size into ranges (powers of 10)
    if data_size < 10:
        size_bucket = "tiny"
    elif data_size < 100:
        size_bucket = "small"
    elif data_size < 1000:
        size_bucket = "medium"
    elif data_size < 10000:
        size_bucket = "large"
    else:
        size_bucket = "xlarge"
    
    # Bucket execution time into ranges (log scale)
    if avg_time_per_item < 0.0001:  # < 0.1ms
        time_bucket = "instant"
    elif avg_time_per_item < 0.001:  # < 1ms
        time_bucket = "fast"
    elif avg_time_per_item < 0.01:  # < 10ms
        time_bucket = "moderate"
    elif avg_time_per_item < 0.1:  # < 100ms
        time_bucket = "slow"
    else:  # >= 100ms
        time_bucket = "very_slow"
    
    # Combine into cache key
    key_components = [
        f"func:{func_hash}",
        f"size:{size_bucket}",
        f"time:{time_bucket}",
        f"v:{CACHE_VERSION}"
    ]
    
    cache_key = "_".join(key_components)
    return cache_key


def save_cache_entry(
    cache_key: str,
    n_jobs: int,
    chunksize: int,
    executor_type: str,
    estimated_speedup: float,
    reason: str,
    warnings: list
) -> None:
    """
    Save an optimization result to the cache.
    
    Args:
        cache_key: Unique key for this optimization
        n_jobs: Recommended number of workers
        chunksize: Recommended chunk size
        executor_type: "process" or "thread"
        estimated_speedup: Expected speedup
        reason: Explanation of recommendation
        warnings: List of warning messages
    """
    try:
        cache_dir = get_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        # Gather current system info
        system_info = {
            "physical_cores": get_physical_cores(),
            "available_memory": get_available_memory(),
            "start_method": get_multiprocessing_start_method(),
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"
        }
        
        # Create cache entry
        entry = CacheEntry(
            n_jobs=n_jobs,
            chunksize=chunksize,
            executor_type=executor_type,
            estimated_speedup=estimated_speedup,
            reason=reason,
            warnings=warnings,
            timestamp=time.time(),
            system_info=system_info
        )
        
        # Write to file atomically
        temp_file = cache_file.with_suffix(".tmp")
        with open(temp_file, 'w') as f:
            json.dump(entry.to_dict(), f, indent=2)
        temp_file.replace(cache_file)
        
    except (OSError, IOError, PermissionError):
        # Silently fail if cache cannot be written
        # This ensures caching never breaks the main functionality
        pass


def load_cache_entry(cache_key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Optional[CacheEntry]:
    """
    Load a cached optimization result.
    
    Args:
        cache_key: Unique key for the optimization
        ttl_seconds: Maximum age in seconds (default: 7 days)
    
    Returns:
        CacheEntry if found and valid, None otherwise
    """
    try:
        cache_dir = get_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        # Load cache entry
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        entry = CacheEntry.from_dict(data)
        
        # Validate cache entry
        if entry.cache_version != CACHE_VERSION:
            # Cache format changed, invalidate
            return None
        
        if entry.is_expired(ttl_seconds):
            # Cache entry too old, invalidate
            return None
        
        if not entry.is_system_compatible():
            # System configuration changed, invalidate
            return None
        
        return entry
        
    except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError):
        # Invalid or corrupted cache entry
        return None


def clear_cache() -> int:
    """
    Clear all cached optimization results.
    
    Returns:
        Number of cache entries deleted
    """
    try:
        cache_dir = get_cache_dir()
        count = 0
        
        for cache_file in cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass
        
        return count
        
    except (OSError, IOError):
        return 0


def prune_expired_cache(ttl_seconds: int = DEFAULT_TTL_SECONDS) -> int:
    """
    Remove expired cache entries.
    
    Args:
        ttl_seconds: Maximum age in seconds (default: 7 days)
    
    Returns:
        Number of cache entries deleted
    """
    try:
        cache_dir = get_cache_dir()
        count = 0
        
        for cache_file in cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                entry = CacheEntry.from_dict(data)
                
                if entry.is_expired(ttl_seconds) or not entry.is_system_compatible():
                    cache_file.unlink()
                    count += 1
                    
            except (OSError, IOError, json.JSONDecodeError, KeyError):
                # Invalid cache file, delete it
                try:
                    cache_file.unlink()
                    count += 1
                except OSError:
                    pass
        
        return count
        
    except (OSError, IOError):
        return 0
