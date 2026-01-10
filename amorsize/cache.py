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
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .system_info import (
    get_physical_cores,
    get_available_memory,
    get_multiprocessing_start_method,
    get_spawn_cost_estimate
)


# Cache version - increment when cache format changes
CACHE_VERSION = 1

# Cache entry time-to-live (default: 7 days)
DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days

# Probability of triggering automatic cache pruning on load (5% chance)
# This provides gradual cleanup without impacting performance
AUTO_PRUNE_PROBABILITY = 0.05


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
    
    def is_system_compatible(self) -> Tuple[bool, str]:
        """
        Check if cached result is compatible with current system.
        
        Returns tuple of (is_compatible, reason):
        - is_compatible: False if key system parameters have changed
        - reason: Human-readable explanation of why cache is incompatible
        
        Checks:
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
            return False, f"Physical core count changed (cached: {cached_cores}, current: {current_cores})"
        
        # Check start method match
        if cached_start_method != current_start_method:
            return False, f"Multiprocessing start method changed (cached: {cached_start_method}, current: {current_start_method})"
        
        # Check memory within 20% tolerance
        if cached_memory > 0:
            memory_ratio = current_memory / cached_memory
            if not (0.8 <= memory_ratio <= 1.2):
                cached_gb = cached_memory / (1024**3)
                current_gb = current_memory / (1024**3)
                return False, f"Available memory changed significantly (cached: {cached_gb:.2f}GB, current: {current_gb:.2f}GB)"
        
        return True, ""


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


def load_cache_entry(cache_key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Tuple[Optional[CacheEntry], str]:
    """
    Load a cached optimization result.
    
    This function includes automatic cache pruning: with a small probability
    (default 5%), it will trigger cleanup of expired entries. This ensures
    cache directories don't grow unbounded over time without requiring
    explicit user action.
    
    Args:
        cache_key: Unique key for the optimization
        ttl_seconds: Maximum age in seconds (default: 7 days)
    
    Returns:
        Tuple of (CacheEntry, miss_reason):
        - CacheEntry if found and valid, None if invalid/missing
        - miss_reason: Empty string on success, or explanation why cache missed
    """
    # Probabilistically trigger automatic cache pruning
    # This distributes cleanup cost and prevents unbounded growth
    _maybe_auto_prune_cache(get_cache_dir, ttl_seconds=ttl_seconds)
    
    try:
        cache_dir = get_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None, "No cached entry found for this workload"
        
        # Load cache entry
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        entry = CacheEntry.from_dict(data)
        
        # Validate cache entry
        if entry.cache_version != CACHE_VERSION:
            # Cache format changed, invalidate
            return None, f"Cache format version mismatch (cached: v{entry.cache_version}, current: v{CACHE_VERSION})"
        
        if entry.is_expired(ttl_seconds):
            # Cache entry too old, invalidate
            age_days = (time.time() - entry.timestamp) / (24 * 60 * 60)
            ttl_days = ttl_seconds / (24 * 60 * 60)
            return None, f"Cache entry expired (age: {age_days:.1f} days, TTL: {ttl_days:.1f} days)"
        
        is_compatible, incompatibility_reason = entry.is_system_compatible()
        if not is_compatible:
            # System configuration changed, invalidate
            return None, incompatibility_reason
        
        return entry, ""
        
    except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
        # Silently fail - caching should never break functionality
        return None, f"Failed to load cache: {type(e).__name__}"
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


def _maybe_auto_prune_cache(cache_dir_func, probability: float = AUTO_PRUNE_PROBABILITY, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    """
    Probabilistically trigger automatic cache pruning.
    
    This function is called during cache load operations to gradually clean up
    expired entries without requiring explicit user action. The pruning happens
    with a low probability to minimize performance impact while ensuring that
    expired entries are eventually removed.
    
    Strategy:
        - Use probabilistic triggering (default 5% chance per load)
        - Distributes cleanup cost across many operations
        - Avoids performance impact on individual operations
        - Ensures long-running applications eventually clean up
    
    Args:
        cache_dir_func: Function that returns the cache directory Path
        probability: Probability of triggering pruning (0.0-1.0)
        ttl_seconds: Maximum age in seconds for cache entries
    
    Returns:
        None (pruning happens silently in background)
    
    Note:
        This function never raises exceptions - failures are silently ignored
        to ensure caching never breaks the main functionality.
    """
    # Probabilistic trigger
    if random.random() > probability:
        return
    
    try:
        cache_dir = cache_dir_func()
        
        # Quick pruning pass - check files and remove expired/corrupted ones
        # This keeps the operation fast even with large cache directories
        for cache_file in cache_dir.glob("*.json"):
            try:
                # Try to load and validate the JSON structure
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check if entry has required timestamp field
                if 'timestamp' not in data:
                    # Missing timestamp = corrupted, delete it
                    cache_file.unlink()
                    continue
                
                # Check if entry is expired based on timestamp
                entry_timestamp = data.get('timestamp', 0)
                entry_age = time.time() - entry_timestamp
                
                if entry_age > ttl_seconds:
                    cache_file.unlink()
                    
            except (OSError, IOError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                # Invalid or corrupted cache file, try to delete it
                try:
                    cache_file.unlink()
                except OSError:
                    pass
    
    except (OSError, IOError, AttributeError):
        # Silently ignore failures - auto-pruning is a best-effort optimization
        pass


class BenchmarkCacheEntry:
    """
    Container for a cached benchmark validation result.
    
    Attributes:
        serial_time: Measured serial execution time (seconds)
        parallel_time: Measured parallel execution time (seconds)
        actual_speedup: Measured speedup (serial_time / parallel_time)
        n_jobs: Number of workers used
        chunksize: Chunk size used
        timestamp: When this entry was created
        system_info: System configuration at cache time
        cache_version: Version of cache format
    """
    
    def __init__(
        self,
        serial_time: float,
        parallel_time: float,
        actual_speedup: float,
        n_jobs: int,
        chunksize: int,
        timestamp: float,
        system_info: Dict[str, Any],
        cache_version: int = CACHE_VERSION
    ):
        self.serial_time = serial_time
        self.parallel_time = parallel_time
        self.actual_speedup = actual_speedup
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.timestamp = timestamp
        self.system_info = system_info
        self.cache_version = cache_version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "serial_time": self.serial_time,
            "parallel_time": self.parallel_time,
            "actual_speedup": self.actual_speedup,
            "n_jobs": self.n_jobs,
            "chunksize": self.chunksize,
            "timestamp": self.timestamp,
            "system_info": self.system_info,
            "cache_version": self.cache_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkCacheEntry":
        """Create BenchmarkCacheEntry from dictionary."""
        return cls(
            serial_time=data["serial_time"],
            parallel_time=data["parallel_time"],
            actual_speedup=data["actual_speedup"],
            n_jobs=data["n_jobs"],
            chunksize=data["chunksize"],
            timestamp=data["timestamp"],
            system_info=data["system_info"],
            cache_version=data.get("cache_version", 1)
        )
    
    def is_expired(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
        """Check if this cache entry has expired."""
        age = time.time() - self.timestamp
        return age > ttl_seconds
    
    def is_system_compatible(self) -> Tuple[bool, str]:
        """
        Check if cached benchmark is compatible with current system.
        
        Returns tuple of (is_compatible, reason):
        - is_compatible: False if key system parameters have changed
        - reason: Human-readable explanation of why cache is incompatible
        
        Benchmark results are highly system-dependent.
        """
        current_cores = get_physical_cores()
        current_memory = get_available_memory()
        current_start_method = get_multiprocessing_start_method()
        
        cached_cores = self.system_info.get("physical_cores", 0)
        cached_memory = self.system_info.get("available_memory", 0)
        cached_start_method = self.system_info.get("start_method", "")
        
        # Benchmark results are system-specific - require exact match
        if cached_cores != current_cores:
            return False, f"Physical core count changed (cached: {cached_cores}, current: {current_cores})"
        
        if cached_start_method != current_start_method:
            return False, f"Multiprocessing start method changed (cached: {cached_start_method}, current: {current_start_method})"
        
        # Memory within 10% tolerance (stricter than optimization cache)
        if cached_memory > 0:
            memory_ratio = current_memory / cached_memory
            if not (0.9 <= memory_ratio <= 1.1):
                cached_gb = cached_memory / (1024**3)
                current_gb = current_memory / (1024**3)
                return False, f"Available memory changed significantly (cached: {cached_gb:.2f}GB, current: {current_gb:.2f}GB)"
        
        return True, ""


def get_benchmark_cache_dir() -> Path:
    """
    Get the benchmark cache directory path.
    
    Returns:
        Path to benchmark cache directory (creates if doesn't exist)
    """
    # Use same base as optimization cache but separate subdirectory
    if platform.system() == "Windows":
        cache_base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif platform.system() == "Darwin":  # macOS
        cache_base = Path.home() / "Library" / "Caches"
    else:  # Linux and others
        cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    
    cache_dir = cache_base / "amorsize" / "benchmark_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def compute_benchmark_cache_key(func: Callable, data_size: int) -> str:
    """
    Compute a cache key for a benchmark validation.
    
    The key is based on:
    1. Function bytecode hash (detects function changes)
    2. Data size (exact match for benchmark validity)
    
    Args:
        func: Function being benchmarked
        data_size: Number of items in the benchmark dataset
    
    Returns:
        Cache key string
    """
    # Hash function bytecode to detect changes
    try:
        func_code = func.__code__.co_code
        func_hash = hashlib.sha256(func_code).hexdigest()[:16]
    except AttributeError:
        # For built-in functions or methods without __code__
        func_hash = hashlib.sha256(str(func).encode()).hexdigest()[:16]
    
    # For benchmarks, we need exact data size (no bucketing)
    # Benchmarks are repeatable only with same workload size
    cache_key = f"benchmark_{func_hash}_{data_size}_v{CACHE_VERSION}"
    return cache_key


def save_benchmark_cache_entry(
    cache_key: str,
    serial_time: float,
    parallel_time: float,
    actual_speedup: float,
    n_jobs: int,
    chunksize: int
) -> None:
    """
    Save a benchmark validation result to the cache.
    
    Args:
        cache_key: Unique key for this benchmark
        serial_time: Measured serial execution time
        parallel_time: Measured parallel execution time
        actual_speedup: Measured speedup
        n_jobs: Number of workers used
        chunksize: Chunk size used
    """
    try:
        cache_dir = get_benchmark_cache_dir()
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
        entry = BenchmarkCacheEntry(
            serial_time=serial_time,
            parallel_time=parallel_time,
            actual_speedup=actual_speedup,
            n_jobs=n_jobs,
            chunksize=chunksize,
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
        pass


def load_benchmark_cache_entry(
    cache_key: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> Tuple[Optional[BenchmarkCacheEntry], str]:
    """
    Load a cached benchmark validation result.
    
    This function includes automatic cache pruning: with a small probability
    (default 5%), it will trigger cleanup of expired entries. This ensures
    cache directories don't grow unbounded over time without requiring
    explicit user action.
    
    Args:
        cache_key: Unique key for the benchmark
        ttl_seconds: Maximum age in seconds (default: 7 days)
    
    Returns:
        Tuple of (BenchmarkCacheEntry, miss_reason):
        - BenchmarkCacheEntry if found and valid, None if invalid/missing
        - miss_reason: Empty string on success, or explanation why cache missed
    """
    # Probabilistically trigger automatic cache pruning
    # This distributes cleanup cost and prevents unbounded growth
    _maybe_auto_prune_cache(get_benchmark_cache_dir, ttl_seconds=ttl_seconds)
    
    try:
        cache_dir = get_benchmark_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None, "No cached benchmark result found for this workload"
        
        # Load cache entry
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        entry = BenchmarkCacheEntry.from_dict(data)
        
        # Validate cache entry
        if entry.cache_version != CACHE_VERSION:
            return None, f"Cache format version mismatch (cached: v{entry.cache_version}, current: v{CACHE_VERSION})"
        
        if entry.is_expired(ttl_seconds):
            age_days = (time.time() - entry.timestamp) / (24 * 60 * 60)
            ttl_days = ttl_seconds / (24 * 60 * 60)
            return None, f"Cache entry expired (age: {age_days:.1f} days, TTL: {ttl_days:.1f} days)"
        
        is_compatible, incompatibility_reason = entry.is_system_compatible()
        if not is_compatible:
            return None, incompatibility_reason
        
        return entry, ""
        
    except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
        return None, f"Failed to load cache: {type(e).__name__}"


def clear_benchmark_cache() -> int:
    """
    Clear all cached benchmark results.
    
    Returns:
        Number of cache entries deleted
    """
    try:
        cache_dir = get_benchmark_cache_dir()
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


class CacheStats:
    """
    Statistics about cache usage and effectiveness.
    
    Attributes:
        total_entries: Total number of cache entries
        valid_entries: Number of valid (non-expired, compatible) entries
        expired_entries: Number of expired entries
        incompatible_entries: Number of system-incompatible entries
        total_size_bytes: Total disk space used by cache (bytes)
        oldest_entry_age: Age of oldest entry (seconds), None if no entries
        newest_entry_age: Age of newest entry (seconds), None if no entries
        cache_dir: Path to cache directory
    """
    
    def __init__(
        self,
        total_entries: int = 0,
        valid_entries: int = 0,
        expired_entries: int = 0,
        incompatible_entries: int = 0,
        total_size_bytes: int = 0,
        oldest_entry_age: Optional[float] = None,
        newest_entry_age: Optional[float] = None,
        cache_dir: Optional[str] = None
    ):
        self.total_entries = total_entries
        self.valid_entries = valid_entries
        self.expired_entries = expired_entries
        self.incompatible_entries = incompatible_entries
        self.total_size_bytes = total_size_bytes
        self.oldest_entry_age = oldest_entry_age
        self.newest_entry_age = newest_entry_age
        self.cache_dir = cache_dir
    
    def __repr__(self):
        return (f"CacheStats(total={self.total_entries}, valid={self.valid_entries}, "
                f"expired={self.expired_entries}, incompatible={self.incompatible_entries}, "
                f"size={self._format_bytes(self.total_size_bytes)})")
    
    def __str__(self):
        lines = [
            "=== Cache Statistics ===",
            f"Cache directory: {self.cache_dir}",
            f"Total entries: {self.total_entries}",
            f"  Valid entries: {self.valid_entries}",
            f"  Expired entries: {self.expired_entries}",
            f"  Incompatible entries: {self.incompatible_entries}",
            f"Total cache size: {self._format_bytes(self.total_size_bytes)}",
        ]
        
        if self.oldest_entry_age is not None:
            lines.append(f"Oldest entry age: {self._format_age(self.oldest_entry_age)}")
        if self.newest_entry_age is not None:
            lines.append(f"Newest entry age: {self._format_age(self.newest_entry_age)}")
        
        return "\n".join(lines)
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes in human-readable form."""
        if bytes_val < 1024:
            return f"{bytes_val}B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.2f}KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / (1024**2):.2f}MB"
        else:
            return f"{bytes_val / (1024**3):.2f}GB"
    
    def _format_age(self, seconds: float) -> str:
        """Format age in human-readable form."""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            return f"{seconds / 60:.1f} minutes"
        elif seconds < 86400:
            return f"{seconds / 3600:.1f} hours"
        else:
            return f"{seconds / 86400:.1f} days"


def get_cache_stats(ttl_seconds: int = DEFAULT_TTL_SECONDS) -> CacheStats:
    """
    Get statistics about the optimization cache.
    
    This function analyzes the cache directory and returns comprehensive
    statistics including entry counts, disk usage, and age information.
    Useful for monitoring cache effectiveness and identifying cleanup needs.
    
    Args:
        ttl_seconds: Maximum age for valid entries (default: 7 days)
    
    Returns:
        CacheStats object with cache statistics
    
    Example:
        >>> stats = get_cache_stats()
        >>> print(stats)
        === Cache Statistics ===
        Cache directory: /home/user/.cache/amorsize/optimization_cache
        Total entries: 42
          Valid entries: 38
          Expired entries: 3
          Incompatible entries: 1
        Total cache size: 156.45KB
        Oldest entry age: 6.2 days
        Newest entry age: 2.3 hours
    """
    try:
        cache_dir = get_cache_dir()
        
        total_entries = 0
        valid_entries = 0
        expired_entries = 0
        incompatible_entries = 0
        total_size_bytes = 0
        oldest_timestamp = None
        newest_timestamp = None
        current_time = time.time()
        
        for cache_file in cache_dir.glob("*.json"):
            try:
                # Count file and get size
                total_entries += 1
                total_size_bytes += cache_file.stat().st_size
                
                # Load and validate entry
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                entry = CacheEntry.from_dict(data)
                
                # Track timestamps
                entry_timestamp = entry.timestamp
                if oldest_timestamp is None or entry_timestamp < oldest_timestamp:
                    oldest_timestamp = entry_timestamp
                if newest_timestamp is None or entry_timestamp > newest_timestamp:
                    newest_timestamp = entry_timestamp
                
                # Categorize entry
                if entry.cache_version != CACHE_VERSION:
                    incompatible_entries += 1
                elif entry.is_expired(ttl_seconds):
                    expired_entries += 1
                elif not entry.is_system_compatible():
                    incompatible_entries += 1
                else:
                    valid_entries += 1
                    
            except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError):
                # Corrupted entry - count as incompatible
                incompatible_entries += 1
        
        # Calculate ages
        oldest_age = None if oldest_timestamp is None else (current_time - oldest_timestamp)
        newest_age = None if newest_timestamp is None else (current_time - newest_timestamp)
        
        return CacheStats(
            total_entries=total_entries,
            valid_entries=valid_entries,
            expired_entries=expired_entries,
            incompatible_entries=incompatible_entries,
            total_size_bytes=total_size_bytes,
            oldest_entry_age=oldest_age,
            newest_entry_age=newest_age,
            cache_dir=str(cache_dir)
        )
        
    except (OSError, IOError):
        # Cache directory doesn't exist or isn't accessible
        return CacheStats(cache_dir=str(get_cache_dir()))


def get_benchmark_cache_stats(ttl_seconds: int = DEFAULT_TTL_SECONDS) -> CacheStats:
    """
    Get statistics about the benchmark cache.
    
    This function analyzes the benchmark cache directory and returns comprehensive
    statistics including entry counts, disk usage, and age information.
    Useful for monitoring cache effectiveness and identifying cleanup needs.
    
    Args:
        ttl_seconds: Maximum age for valid entries (default: 7 days)
    
    Returns:
        CacheStats object with benchmark cache statistics
    
    Example:
        >>> stats = get_benchmark_cache_stats()
        >>> print(stats)
        === Cache Statistics ===
        Cache directory: /home/user/.cache/amorsize/benchmark_cache
        Total entries: 15
          Valid entries: 14
          Expired entries: 1
          Incompatible entries: 0
        Total cache size: 42.18KB
        Oldest entry age: 4.1 days
        Newest entry age: 1.5 hours
    """
    try:
        cache_dir = get_benchmark_cache_dir()
        
        total_entries = 0
        valid_entries = 0
        expired_entries = 0
        incompatible_entries = 0
        total_size_bytes = 0
        oldest_timestamp = None
        newest_timestamp = None
        current_time = time.time()
        
        for cache_file in cache_dir.glob("*.json"):
            try:
                # Count file and get size
                total_entries += 1
                total_size_bytes += cache_file.stat().st_size
                
                # Load and validate entry
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                entry = BenchmarkCacheEntry.from_dict(data)
                
                # Track timestamps
                entry_timestamp = entry.timestamp
                if oldest_timestamp is None or entry_timestamp < oldest_timestamp:
                    oldest_timestamp = entry_timestamp
                if newest_timestamp is None or entry_timestamp > newest_timestamp:
                    newest_timestamp = entry_timestamp
                
                # Categorize entry
                if entry.cache_version != CACHE_VERSION:
                    incompatible_entries += 1
                elif entry.is_expired(ttl_seconds):
                    expired_entries += 1
                elif not entry.is_system_compatible():
                    incompatible_entries += 1
                else:
                    valid_entries += 1
                    
            except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError):
                # Corrupted entry - count as incompatible
                incompatible_entries += 1
        
        # Calculate ages
        oldest_age = None if oldest_timestamp is None else (current_time - oldest_timestamp)
        newest_age = None if newest_timestamp is None else (current_time - newest_timestamp)
        
        return CacheStats(
            total_entries=total_entries,
            valid_entries=valid_entries,
            expired_entries=expired_entries,
            incompatible_entries=incompatible_entries,
            total_size_bytes=total_size_bytes,
            oldest_entry_age=oldest_age,
            newest_entry_age=newest_age,
            cache_dir=str(cache_dir)
        )
        
    except (OSError, IOError):
        # Cache directory doesn't exist or isn't accessible
        return CacheStats(cache_dir=str(get_benchmark_cache_dir()))


def prewarm_cache(
    func: Callable,
    workload_profiles: Optional[list] = None,
    optimization_result: Optional['OptimizationResult'] = None,
    force: bool = False
) -> int:
    """
    Prewarm the optimization cache to eliminate first-run penalty.
    
    This function pre-populates the cache with optimization results, allowing
    subsequent optimize() calls to return instantly without performing dry runs
    or overhead measurements. This is especially valuable for:
    
    - Serverless/Lambda functions (fast cold starts)
    - Production deployments (consistent first-run performance)
    - Development iteration (faster testing cycles)
    - CI/CD pipelines (predictable build times)
    
    Usage:
        There are two modes of operation:
        
        1. **Automatic mode** (workload_profiles specified):
           Prewarming with common workload patterns for a function.
           
           ```python
           # Prewarm with default patterns (CPU-bound, various sizes)
           prewarm_cache(my_function)
           
           # Prewarm with custom patterns
           patterns = [
               {"data_size": 100, "avg_time": 0.001},    # Small, fast
               {"data_size": 10000, "avg_time": 0.01},   # Large, moderate
           ]
           prewarm_cache(my_function, workload_profiles=patterns)
           ```
        
        2. **Manual mode** (optimization_result specified):
           Prewarming from an actual optimization result.
           
           ```python
           # Run optimization once
           result = optimize(my_function, sample_data)
           
           # Prewarm cache with this result for future runs
           prewarm_cache(my_function, optimization_result=result)
           ```
    
    Args:
        func: Function to prewarm cache for
        workload_profiles: List of workload patterns to prewarm with.
                          Each dict should have "data_size" and "avg_time" keys.
                          If None, uses sensible defaults for common patterns.
        optimization_result: Existing OptimizationResult to store in cache.
                           If provided, workload_profiles is ignored.
        force: If True, overwrites existing cache entries. If False, skips
               entries that already exist in cache. Default: False.
    
    Returns:
        Number of cache entries created or updated
    
    Raises:
        ValueError: If neither workload_profiles nor optimization_result provided
        TypeError: If workload_profiles format is invalid
    
    Examples:
        >>> # Prewarm with default patterns
        >>> count = prewarm_cache(expensive_function)
        >>> print(f"Prewarmed {count} cache entries")
        
        >>> # Prewarm from optimization result
        >>> result = optimize(func, data)
        >>> prewarm_cache(func, optimization_result=result)
        
        >>> # Custom workload patterns
        >>> patterns = [
        ...     {"data_size": 50, "avg_time": 0.005},
        ...     {"data_size": 500, "avg_time": 0.01},
        ... ]
        >>> prewarm_cache(func, workload_profiles=patterns, force=True)
    
    Note:
        - Prewarming does not validate that the function works or that the
          parameters are optimal. It simply populates the cache.
        - For accurate prewarming, use optimization_result from a real run.
        - For quick prewarming, use workload_profiles with estimated patterns.
        - Cache entries include system information and will be invalidated
          if system configuration changes (cores, memory, start method).
    """
    # Validate inputs
    if optimization_result is None and workload_profiles is None:
        # Use default workload profiles for common patterns
        workload_profiles = _get_default_workload_profiles()
    
    entries_created = 0
    
    # Mode 1: Prewarm from optimization result
    if optimization_result is not None:
        # Extract workload characteristics from the result
        # We need to estimate data_size and avg_time from the result
        # Use the cache key from the result if available, or create one
        
        try:
            # Try to get data size from the result
            if hasattr(optimization_result, 'data') and hasattr(optimization_result.data, '__len__'):
                data_size = len(optimization_result.data)
            else:
                # Estimate from profile if available
                if hasattr(optimization_result, 'profile') and optimization_result.profile is not None:
                    data_size = optimization_result.profile.total_items
                else:
                    # Default to medium size if unknown
                    data_size = 1000
            
            # Estimate avg time from profile
            if hasattr(optimization_result, 'profile') and optimization_result.profile is not None:
                avg_time = optimization_result.profile.avg_execution_time
            else:
                # Default to moderate time if unknown
                avg_time = 0.01
            
            # Compute cache key
            cache_key = compute_cache_key(func, data_size, avg_time)
            
            # Check if entry already exists
            if not force:
                existing_entry, _ = load_cache_entry(cache_key)
                if existing_entry is not None:
                    # Entry already exists, skip
                    return 0
            
            # Save to cache
            save_cache_entry(
                cache_key=cache_key,
                n_jobs=optimization_result.n_jobs,
                chunksize=optimization_result.chunksize,
                executor_type=optimization_result.executor_type,
                estimated_speedup=optimization_result.estimated_speedup,
                reason=optimization_result.reason,
                warnings=optimization_result.warnings
            )
            entries_created = 1
            
        except (AttributeError, TypeError, ValueError):
            # Invalid optimization result, skip
            pass
    
    # Mode 2: Prewarm from workload profiles
    else:
        for profile in workload_profiles:
            try:
                # Validate profile format
                if not isinstance(profile, dict):
                    continue
                if "data_size" not in profile or "avg_time" not in profile:
                    continue
                
                data_size = profile["data_size"]
                avg_time = profile["avg_time"]
                
                # Validate values
                if not isinstance(data_size, int) or data_size <= 0:
                    continue
                if not isinstance(avg_time, (int, float)) or avg_time <= 0:
                    continue
                
                # Compute cache key
                cache_key = compute_cache_key(func, data_size, avg_time)
                
                # Check if entry already exists
                if not force:
                    existing_entry, _ = load_cache_entry(cache_key)
                    if existing_entry is not None:
                        # Entry already exists, skip
                        continue
                
                # Compute reasonable optimization parameters based on workload
                # This is a simplified heuristic - real optimization would be more sophisticated
                n_jobs, chunksize, executor_type, estimated_speedup, reason, warnings = \
                    _estimate_optimization_parameters(data_size, avg_time)
                
                # Save to cache
                save_cache_entry(
                    cache_key=cache_key,
                    n_jobs=n_jobs,
                    chunksize=chunksize,
                    executor_type=executor_type,
                    estimated_speedup=estimated_speedup,
                    reason=reason,
                    warnings=warnings
                )
                entries_created += 1
                
            except (TypeError, ValueError, KeyError):
                # Invalid profile, skip
                continue
    
    return entries_created


def _get_default_workload_profiles() -> list:
    """
    Get default workload profiles for cache prewarming.
    
    These profiles cover common use cases with distinct buckets:
    - Tiny/instant: Very quick operations
    - Small/fast: Quick operations on small datasets
    - Medium/moderate: Typical batch processing
    - Large/slow: Heavy computation on large datasets
    - XLarge/very_slow: Very heavy computation
    
    Returns:
        List of workload profile dictionaries
    """
    return [
        # Tiny/instant: data_size < 10, avg_time < 0.0001
        {"data_size": 5, "avg_time": 0.00005},
        
        # Small/fast: data_size 10-100, avg_time 0.0001-0.001
        {"data_size": 50, "avg_time": 0.0005},
        
        # Medium/moderate: data_size 100-1000, avg_time 0.001-0.01
        {"data_size": 500, "avg_time": 0.003},
        
        # Large/moderate: data_size 1000-10000, avg_time 0.001-0.01
        {"data_size": 2000, "avg_time": 0.007},
        
        # Large/slow: data_size 1000-10000, avg_time 0.01-0.1
        {"data_size": 5000, "avg_time": 0.03},
        
        # XLarge/slow: data_size >= 10000, avg_time 0.01-0.1
        {"data_size": 15000, "avg_time": 0.07},
        
        # XLarge/very_slow: data_size >= 10000, avg_time >= 0.1
        {"data_size": 20000, "avg_time": 0.15},
    ]


def _estimate_optimization_parameters(
    data_size: int,
    avg_time: float
) -> Tuple[int, int, str, float, str, list]:
    """
    Estimate optimization parameters for cache prewarming.
    
    This is a simplified heuristic that provides reasonable defaults without
    performing actual measurements. For accurate optimization, use the full
    optimize() function.
    
    Args:
        data_size: Number of items in workload
        avg_time: Average time per item (seconds)
    
    Returns:
        Tuple of (n_jobs, chunksize, executor_type, estimated_speedup, reason, warnings)
    """
    physical_cores = get_physical_cores()
    spawn_cost_estimate = get_spawn_cost_estimate()
    
    # Estimate total serial time
    total_time = data_size * avg_time
    
    # Heuristic: If total time is very short (< spawn cost), use serial
    if total_time < spawn_cost_estimate:
        return (
            1, 1, "process",
            1.0,
            "Function too fast - overhead dominates (prewarmed estimate)",
            ["This is a prewarmed cache entry with estimated parameters"]
        )
    
    # Heuristic: Use physical cores for parallelization
    n_jobs = min(physical_cores, data_size)
    
    # Heuristic: Target ~0.2s per chunk
    target_chunk_duration = 0.2
    if avg_time > 0:
        ideal_chunksize = max(1, int(target_chunk_duration / avg_time))
        chunksize = min(ideal_chunksize, max(1, data_size // n_jobs))
    else:
        chunksize = max(1, data_size // n_jobs)
    
    # Estimate speedup (simplified Amdahl's Law)
    # Assume 95% parallelizable (conservative estimate)
    parallel_fraction = 0.95
    overhead_fraction = 0.1  # 10% overhead estimate
    theoretical_speedup = n_jobs * parallel_fraction
    estimated_speedup = theoretical_speedup * (1 - overhead_fraction)
    estimated_speedup = max(1.0, min(estimated_speedup, n_jobs * 0.8))
    
    # Determine executor type (always use process for prewarming)
    executor_type = "process"
    
    # Create reason
    reason = f"Prewarmed: {n_jobs} workers with chunks of {chunksize} (estimated parameters)"
    
    # Add warning
    warnings = [
        "This is a prewarmed cache entry with estimated parameters",
        "For accurate optimization, run optimize() once to replace this entry"
    ]
    
    return (n_jobs, chunksize, executor_type, estimated_speedup, reason, warnings)


def export_cache(
    output_file: str,
    include_expired: bool = False,
    include_incompatible: bool = False,
    ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> int:
    """
    Export cache entries to a portable file format.
    
    This function exports the optimization cache to a JSON file that can be:
    - Shared with team members
    - Version controlled for reproducible builds
    - Deployed to production environments
    - Imported on different machines
    
    Args:
        output_file: Path to output file (will be created/overwritten)
        include_expired: Include expired entries (default: False)
        include_incompatible: Include system-incompatible entries (default: False)
        ttl_seconds: TTL for determining expiration (default: 7 days)
    
    Returns:
        Number of entries exported
    
    Example:
        >>> # Export only valid entries
        >>> count = export_cache('cache_backup.json')
        >>> print(f"Exported {count} valid cache entries")
        
        >>> # Export all entries including expired
        >>> count = export_cache('full_cache.json', include_expired=True)
        
        >>> # Export to version control
        >>> export_cache('production_cache.json')
        >>> # Commit to git for reproducible builds
    """
    try:
        cache_dir = get_cache_dir()
        entries = []
        
        for cache_file in cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                entry = CacheEntry.from_dict(data)
                
                # Filter based on parameters
                if not include_expired and entry.is_expired(ttl_seconds):
                    continue
                
                if not include_incompatible:
                    is_compatible, _ = entry.is_system_compatible()
                    if not is_compatible:
                        continue
                
                # Include cache key in export for reimport
                cache_key = cache_file.stem
                entry_data = data.copy()
                entry_data['cache_key'] = cache_key
                entries.append(entry_data)
                
            except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted entries
                continue
        
        # Write to output file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            'version': CACHE_VERSION,
            'export_timestamp': time.time(),
            'export_system': {
                'platform': platform.system(),
                'physical_cores': get_physical_cores(),
                'available_memory': get_available_memory(),
                'start_method': get_multiprocessing_start_method()
            },
            'entries': entries
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return len(entries)
        
    except (OSError, IOError) as e:
        raise IOError(f"Failed to export cache: {e}")


def import_cache(
    input_file: str,
    merge_strategy: str = "skip",
    validate_compatibility: bool = True,
    update_timestamps: bool = False
) -> Tuple[int, int, int]:
    """
    Import cache entries from an exported file.
    
    This function imports cache entries that were previously exported,
    enabling cache sharing across environments and reproducible builds.
    
    Args:
        input_file: Path to exported cache file
        merge_strategy: How to handle existing entries:
            - "skip": Skip entries that already exist (default)
            - "overwrite": Overwrite existing entries
            - "update": Only update if exported entry is newer
        validate_compatibility: Check system compatibility before import (default: True)
        update_timestamps: Update timestamps to current time (default: False)
    
    Returns:
        Tuple of (imported_count, skipped_count, incompatible_count)
    
    Example:
        >>> # Import cache from team member
        >>> imported, skipped, incompatible = import_cache('teammate_cache.json')
        >>> print(f"Imported {imported}, skipped {skipped}, incompatible {incompatible}")
        
        >>> # Deploy to production with overwrite
        >>> imported, _, _ = import_cache('production_cache.json', merge_strategy='overwrite')
        
        >>> # Import without compatibility check (use with caution)
        >>> import_cache('cache.json', validate_compatibility=False)
    
    Raises:
        IOError: If file cannot be read or is invalid
        ValueError: If merge_strategy is invalid
    """
    if merge_strategy not in ("skip", "overwrite", "update"):
        raise ValueError(f"Invalid merge_strategy: {merge_strategy}. Must be 'skip', 'overwrite', or 'update'")
    
    try:
        # Load export file
        input_path = Path(input_file)
        if not input_path.exists():
            raise IOError(f"Import file not found: {input_file}")
        
        with open(input_path, 'r') as f:
            export_data = json.load(f)
        
        # Validate export format
        if 'version' not in export_data or 'entries' not in export_data:
            raise IOError("Invalid export file format: missing required fields")
        
        # Check version compatibility
        export_version = export_data['version']
        if export_version != CACHE_VERSION:
            raise IOError(f"Incompatible cache version: export={export_version}, current={CACHE_VERSION}")
        
        cache_dir = get_cache_dir()
        current_time = time.time()
        
        imported_count = 0
        skipped_count = 0
        incompatible_count = 0
        
        for entry_data in export_data['entries']:
            try:
                # Extract cache key
                cache_key = entry_data.get('cache_key')
                if not cache_key:
                    skipped_count += 1
                    continue
                
                # Create entry for validation
                entry = CacheEntry.from_dict(entry_data)
                
                # Validate compatibility if requested
                if validate_compatibility:
                    is_compatible, reason = entry.is_system_compatible()
                    if not is_compatible:
                        incompatible_count += 1
                        continue
                
                # Check if entry already exists
                cache_file = cache_dir / f"{cache_key}.json"
                entry_exists = cache_file.exists()
                
                # Apply merge strategy
                should_import = False
                if not entry_exists:
                    should_import = True
                elif merge_strategy == "overwrite":
                    should_import = True
                elif merge_strategy == "update":
                    # Only import if exported entry is newer
                    try:
                        with open(cache_file, 'r') as f:
                            existing_data = json.load(f)
                        existing_timestamp = existing_data.get('timestamp', 0)
                        if entry.timestamp > existing_timestamp:
                            should_import = True
                        else:
                            skipped_count += 1
                    except (OSError, IOError, json.JSONDecodeError):
                        should_import = True  # Corrupted existing entry
                else:  # merge_strategy == "skip"
                    skipped_count += 1
                
                if should_import:
                    # Update timestamp if requested
                    if update_timestamps:
                        entry_data['timestamp'] = current_time
                    
                    # Remove cache_key from data before saving
                    save_data = {k: v for k, v in entry_data.items() if k != 'cache_key'}
                    
                    # Write to cache
                    with open(cache_file, 'w') as f:
                        json.dump(save_data, f, indent=2)
                    
                    imported_count += 1
                    
            except (KeyError, ValueError, json.JSONDecodeError):
                # Skip malformed entries
                skipped_count += 1
        
        return (imported_count, skipped_count, incompatible_count)
        
    except (OSError, IOError) as e:
        raise IOError(f"Failed to import cache: {e}")
    except json.JSONDecodeError as e:
        raise IOError(f"Invalid JSON in import file: {e}")
