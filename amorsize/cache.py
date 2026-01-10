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

from .system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method


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
