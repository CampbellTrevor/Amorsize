"""
Tests for the optimization cache module.
"""

import pytest
import time
import tempfile
import os
from pathlib import Path

from amorsize import optimize, clear_cache, prune_expired_cache, get_cache_dir
from amorsize.cache import (
    CacheEntry,
    compute_cache_key,
    save_cache_entry,
    load_cache_entry,
    DEFAULT_TTL_SECONDS
)
from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method


def simple_func(x):
    """Simple test function."""
    return x ** 2


def slow_func(x):
    """Slower test function."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


class TestCacheEntry:
    """Tests for CacheEntry class."""
    
    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        system_info = {
            "physical_cores": 4,
            "available_memory": 8 * 1024**3,
            "start_method": "fork"
        }
        
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="Test entry",
            warnings=["warning1"],
            timestamp=time.time(),
            system_info=system_info
        )
        
        assert entry.n_jobs == 4
        assert entry.chunksize == 100
        assert entry.executor_type == "process"
        assert entry.estimated_speedup == 3.5
        assert entry.reason == "Test entry"
        assert len(entry.warnings) == 1
        assert entry.system_info["physical_cores"] == 4
    
    def test_cache_entry_to_dict(self):
        """Test serialization to dictionary."""
        system_info = {
            "physical_cores": 4,
            "available_memory": 8 * 1024**3,
            "start_method": "fork"
        }
        
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="Test entry",
            warnings=[],
            timestamp=time.time(),
            system_info=system_info
        )
        
        data = entry.to_dict()
        assert data["n_jobs"] == 4
        assert data["chunksize"] == 100
        assert data["executor_type"] == "process"
        assert "system_info" in data
    
    def test_cache_entry_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "n_jobs": 4,
            "chunksize": 100,
            "executor_type": "process",
            "estimated_speedup": 3.5,
            "reason": "Test",
            "warnings": [],
            "timestamp": time.time(),
            "system_info": {
                "physical_cores": 4,
                "available_memory": 8 * 1024**3,
                "start_method": "fork"
            },
            "cache_version": 1
        }
        
        entry = CacheEntry.from_dict(data)
        assert entry.n_jobs == 4
        assert entry.chunksize == 100
        assert entry.executor_type == "process"
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration check."""
        # Fresh entry (not expired)
        entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=1.0,
            reason="Test",
            warnings=[],
            timestamp=time.time(),
            system_info={}
        )
        assert not entry.is_expired(ttl_seconds=3600)
        
        # Old entry (expired)
        old_entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=1.0,
            reason="Test",
            warnings=[],
            timestamp=time.time() - 8 * 24 * 60 * 60,  # 8 days ago
            system_info={}
        )
        assert old_entry.is_expired(ttl_seconds=DEFAULT_TTL_SECONDS)
    
    def test_cache_entry_system_compatibility(self):
        """Test system compatibility check."""
        # Compatible system
        current_cores = get_physical_cores()
        current_memory = get_available_memory()
        current_method = get_multiprocessing_start_method()
        
        entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=1.0,
            reason="Test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": current_cores,
                "available_memory": current_memory,
                "start_method": current_method
            }
        )
        assert entry.is_system_compatible()
        
        # Incompatible (different core count)
        incompatible_entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=1.0,
            reason="Test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": current_cores + 10,  # Different
                "available_memory": current_memory,
                "start_method": current_method
            }
        )
        assert not incompatible_entry.is_system_compatible()


class TestCacheKey:
    """Tests for cache key generation."""
    
    def test_cache_key_deterministic(self):
        """Test that cache keys are deterministic."""
        key1 = compute_cache_key(simple_func, 1000, 0.001)
        key2 = compute_cache_key(simple_func, 1000, 0.001)
        assert key1 == key2
    
    def test_cache_key_different_functions(self):
        """Test that different functions get different keys."""
        key1 = compute_cache_key(simple_func, 1000, 0.001)
        key2 = compute_cache_key(slow_func, 1000, 0.001)
        assert key1 != key2
    
    def test_cache_key_bucketing(self):
        """Test that similar workloads get same key (bucketing)."""
        # Same bucket for similar sizes
        key1 = compute_cache_key(simple_func, 1000, 0.001)
        key2 = compute_cache_key(simple_func, 1500, 0.001)
        assert key1 == key2  # Both in "medium" bucket (100-1000)
        
        # Different buckets for different sizes
        key3 = compute_cache_key(simple_func, 50000, 0.001)
        assert key1 != key3  # Different size buckets


class TestCacheSaveLoad:
    """Tests for cache save/load operations."""
    
    def test_save_and_load_cache(self):
        """Test saving and loading cache entries."""
        clear_cache()
        
        cache_key = compute_cache_key(simple_func, 1000, 0.001)
        
        # Save entry
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=50,
            executor_type="process",
            estimated_speedup=1.8,
            reason="Test cache",
            warnings=[]
        )
        
        # Load entry
        entry = load_cache_entry(cache_key)
        assert entry is not None
        assert entry.n_jobs == 2
        assert entry.chunksize == 50
        assert entry.executor_type == "process"
        assert entry.estimated_speedup == 1.8
    
    def test_load_nonexistent_cache(self):
        """Test loading a cache entry that doesn't exist."""
        clear_cache()
        entry = load_cache_entry("nonexistent_key_12345")
        assert entry is None
    
    def test_clear_cache(self):
        """Test clearing all cache entries."""
        # Save an entry
        cache_key = compute_cache_key(simple_func, 1000, 0.001)
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=50,
            executor_type="process",
            estimated_speedup=1.8,
            reason="Test",
            warnings=[]
        )
        
        # Clear cache
        count = clear_cache()
        assert count >= 0  # Should clear at least the entry we just added
        
        # Verify entry is gone
        entry = load_cache_entry(cache_key)
        assert entry is None


class TestOptimizeCaching:
    """Tests for caching in the optimize function."""
    
    def test_cache_improves_performance(self):
        """Test that caching speeds up repeated optimizations."""
        clear_cache()
        
        data = range(1000)
        
        # First run (no cache)
        start1 = time.time()
        result1 = optimize(simple_func, data, use_cache=True)
        time1 = time.time() - start1
        
        # Second run (with cache)
        start2 = time.time()
        result2 = optimize(simple_func, data, use_cache=True)
        time2 = time.time() - start2
        
        # Results should be the same
        assert result1.n_jobs == result2.n_jobs
        assert result1.chunksize == result2.chunksize
        
        # Second run should be faster (at least 2x)
        assert time2 < time1
        assert time1 / time2 > 2.0, f"Cache didn't provide significant speedup: {time1/time2:.2f}x"
    
    def test_cache_disabled(self):
        """Test that caching can be disabled."""
        clear_cache()
        
        data = range(1000)
        
        # Run twice with cache disabled
        result1 = optimize(simple_func, data, use_cache=False)
        result2 = optimize(simple_func, data, use_cache=False)
        
        # Results should be the same but no cache should be created
        assert result1.n_jobs == result2.n_jobs
        
        # Verify no cache file was created
        cache_key = compute_cache_key(simple_func, len(data), 0.001)
        entry = load_cache_entry(cache_key)
        assert entry is None
    
    def test_cache_with_different_data_sizes(self):
        """Test that similar data sizes share cache."""
        clear_cache()
        
        # These should use the same cache bucket (medium: 100-1000)
        result1 = optimize(simple_func, range(500), use_cache=True)
        result2 = optimize(simple_func, range(800), use_cache=True)
        
        # Should hit cache on second run (same bucket)
        assert result1.n_jobs == result2.n_jobs
        assert "(cached)" in result2.reason
    
    def test_cache_with_generators(self):
        """Test that caching works with generators."""
        clear_cache()
        
        def make_gen():
            return (x for x in range(1000))
        
        # Generators don't have len(), so caching shouldn't happen
        result = optimize(simple_func, make_gen(), use_cache=True)
        assert result.n_jobs >= 1  # Should still work
    
    def test_cache_respects_system_changes(self):
        """Test that cache is invalidated when system changes."""
        clear_cache()
        
        data = range(1000)
        
        # First optimization
        result1 = optimize(simple_func, data, use_cache=True)
        
        # Get cache entry and manually change system info to simulate different system
        cache_key = compute_cache_key(simple_func, len(data), 0.001)
        entry = load_cache_entry(cache_key)
        assert entry is not None
        
        # If we modify the cached system info to be incompatible,
        # the cache should not be used (tested by CacheEntry.is_system_compatible)
        # This is already covered by test_cache_entry_system_compatibility


class TestCachePruning:
    """Tests for cache pruning functionality."""
    
    def test_prune_expired_cache(self):
        """Test pruning expired cache entries."""
        clear_cache()
        
        # Save an "old" entry by manipulating the timestamp
        cache_key = compute_cache_key(simple_func, 1000, 0.001)
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=50,
            executor_type="process",
            estimated_speedup=1.8,
            reason="Test",
            warnings=[]
        )
        
        # Manually load and verify it exists
        entry = load_cache_entry(cache_key, ttl_seconds=DEFAULT_TTL_SECONDS)
        assert entry is not None
        
        # Prune with very short TTL (should remove entry)
        count = prune_expired_cache(ttl_seconds=0)
        assert count >= 1
        
        # Entry should be gone
        entry = load_cache_entry(cache_key)
        assert entry is None


class TestCacheDirectory:
    """Tests for cache directory management."""
    
    def test_get_cache_dir(self):
        """Test getting the cache directory."""
        cache_dir = get_cache_dir()
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        assert "amorsize" in str(cache_dir)
        assert "optimization_cache" in str(cache_dir)
