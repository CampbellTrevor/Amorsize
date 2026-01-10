"""
Tests for benchmark result caching feature.
"""

import pytest
import time
from amorsize import validate_optimization, quick_validate, optimize, clear_benchmark_cache
from amorsize.cache import (
    compute_benchmark_cache_key,
    save_benchmark_cache_entry,
    load_benchmark_cache_entry,
    BenchmarkCacheEntry,
    get_benchmark_cache_dir
)


def simple_function(x):
    """Simple test function for benchmarking."""
    return x ** 2


def slow_function(x):
    """Slower function for testing benchmark timing."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


class TestBenchmarkCacheEntry:
    """Tests for BenchmarkCacheEntry class."""
    
    def test_cache_entry_creation(self):
        """Test that BenchmarkCacheEntry can be created with all fields."""
        entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=25,
            timestamp=time.time(),
            system_info={"physical_cores": 4, "available_memory": 8000000000}
        )
        
        assert entry.serial_time == 1.0
        assert entry.parallel_time == 0.5
        assert entry.actual_speedup == 2.0
        assert entry.n_jobs == 4
        assert entry.chunksize == 25
    
    def test_cache_entry_to_dict(self):
        """Test serialization of BenchmarkCacheEntry to dictionary."""
        entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=25,
            timestamp=time.time(),
            system_info={"physical_cores": 4}
        )
        
        data = entry.to_dict()
        assert isinstance(data, dict)
        assert data["serial_time"] == 1.0
        assert data["parallel_time"] == 0.5
        assert data["actual_speedup"] == 2.0
        assert data["n_jobs"] == 4
        assert data["chunksize"] == 25
    
    def test_cache_entry_from_dict(self):
        """Test deserialization of BenchmarkCacheEntry from dictionary."""
        data = {
            "serial_time": 1.0,
            "parallel_time": 0.5,
            "actual_speedup": 2.0,
            "n_jobs": 4,
            "chunksize": 25,
            "timestamp": time.time(),
            "system_info": {"physical_cores": 4},
            "cache_version": 1
        }
        
        entry = BenchmarkCacheEntry.from_dict(data)
        assert entry.serial_time == 1.0
        assert entry.parallel_time == 0.5
        assert entry.actual_speedup == 2.0
    
    def test_cache_entry_not_expired(self):
        """Test that fresh cache entries are not expired."""
        entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=25,
            timestamp=time.time(),
            system_info={"physical_cores": 4}
        )
        
        assert not entry.is_expired(ttl_seconds=86400)
    
    def test_cache_entry_expired(self):
        """Test that old cache entries are expired."""
        entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=25,
            timestamp=time.time() - 100000,  # Very old
            system_info={"physical_cores": 4}
        )
        
        assert entry.is_expired(ttl_seconds=86400)


class TestBenchmarkCacheKey:
    """Tests for benchmark cache key generation."""
    
    def test_compute_cache_key_returns_string(self):
        """Test that cache key is a string."""
        cache_key = compute_benchmark_cache_key(simple_function, 100)
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
    
    def test_same_function_same_size_same_key(self):
        """Test that same function and data size produce same key."""
        key1 = compute_benchmark_cache_key(simple_function, 100)
        key2 = compute_benchmark_cache_key(simple_function, 100)
        assert key1 == key2
    
    def test_different_size_different_key(self):
        """Test that different data sizes produce different keys."""
        key1 = compute_benchmark_cache_key(simple_function, 100)
        key2 = compute_benchmark_cache_key(simple_function, 200)
        assert key1 != key2
    
    def test_different_function_different_key(self):
        """Test that different functions produce different keys."""
        key1 = compute_benchmark_cache_key(simple_function, 100)
        key2 = compute_benchmark_cache_key(slow_function, 100)
        assert key1 != key2
    
    def test_cache_key_includes_version(self):
        """Test that cache key includes version number."""
        key = compute_benchmark_cache_key(simple_function, 100)
        assert "v1" in key or "_v1" in key or "v2" in key


class TestBenchmarkCacheSaveLoad:
    """Tests for saving and loading benchmark cache entries."""
    
    def test_save_and_load_cache_entry(self):
        """Test that we can save and load a cache entry."""
        cache_key = "test_benchmark_12345_100_v1"
        
        # Save entry
        save_benchmark_cache_entry(
            cache_key=cache_key,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=25
        )
        
        # Load entry
        entry, miss_reason = load_benchmark_cache_entry(cache_key)
        assert entry is not None
        assert miss_reason == ""
        assert entry.serial_time == 1.0
        assert entry.parallel_time == 0.5
        assert entry.actual_speedup == 2.0
        assert entry.n_jobs == 4
        assert entry.chunksize == 25
    
    def test_load_nonexistent_cache_entry(self):
        """Test that loading nonexistent entry returns None."""
        entry, miss_reason = load_benchmark_cache_entry("nonexistent_key_xyz")
        assert entry is None
        assert "No cached benchmark result found" in miss_reason
    
    def test_load_expired_cache_entry(self):
        """Test that expired entries return None."""
        cache_key = "test_expired_12345_100_v1"
        
        # Save entry with old timestamp
        save_benchmark_cache_entry(
            cache_key=cache_key,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=25
        )
        
        # Try to load with very short TTL
        entry, miss_reason = load_benchmark_cache_entry(cache_key, ttl_seconds=0)
        assert entry is None
        assert "expired" in miss_reason.lower()


class TestBenchmarkCacheIntegration:
    """Integration tests for benchmark caching with validate_optimization."""
    
    def test_benchmark_cache_miss_on_first_run(self):
        """Test that first benchmark run is a cache miss."""
        data = list(range(50))
        result = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        
        assert result is not None
        assert result.cache_hit is False
    
    def test_benchmark_cache_hit_on_second_run(self):
        """Test that second benchmark run is a cache hit."""
        data = list(range(50))
        
        # First run - cache miss
        result1 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        assert result1.cache_hit is False
        
        # Second run - cache hit
        result2 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        assert result2.cache_hit is True
        
        # Results should be identical
        assert result1.serial_time == result2.serial_time
        assert result1.parallel_time == result2.parallel_time
        assert result1.actual_speedup == result2.actual_speedup
    
    def test_benchmark_cache_disabled(self):
        """Test that caching can be disabled."""
        data = list(range(50))
        
        # First run with cache disabled
        result1 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=False
        )
        assert result1.cache_hit is False
        
        # Second run with cache disabled - still cache miss
        result2 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=False
        )
        assert result2.cache_hit is False
    
    def test_benchmark_cache_speedup(self):
        """Test that cached benchmarks are significantly faster."""
        data = list(range(50))
        
        # First run - uncached (slower)
        start1 = time.perf_counter()
        result1 = validate_optimization(
            slow_function,
            data,
            verbose=False,
            use_cache=True
        )
        time1 = time.perf_counter() - start1
        assert result1.cache_hit is False
        
        # Second run - cached (faster)
        start2 = time.perf_counter()
        result2 = validate_optimization(
            slow_function,
            data,
            verbose=False,
            use_cache=True
        )
        time2 = time.perf_counter() - start2
        assert result2.cache_hit is True
        
        # Cached run should be at least 5x faster
        speedup = time1 / time2
        assert speedup >= 5.0, f"Expected 5x+ speedup, got {speedup:.1f}x"
    
    def test_benchmark_cache_invalidated_by_data_size(self):
        """Test that cache is invalidated when data size changes."""
        data1 = list(range(50))
        data2 = list(range(100))
        
        # First run with 50 items
        result1 = validate_optimization(
            simple_function,
            data1,
            verbose=False,
            use_cache=True
        )
        assert result1.cache_hit is False
        
        # Second run with 100 items - different size, cache miss
        result2 = validate_optimization(
            simple_function,
            data2,
            verbose=False,
            use_cache=True
        )
        assert result2.cache_hit is False
    
    def test_quick_validate_caching(self):
        """Test that quick_validate also benefits from caching."""
        data = list(range(1000))
        
        # First run - cache miss
        result1 = quick_validate(
            simple_function,
            data,
            sample_size=50,
            verbose=False,
            use_cache=True
        )
        assert result1.cache_hit is False
        
        # Second run - cache hit
        result2 = quick_validate(
            simple_function,
            data,
            sample_size=50,
            verbose=False,
            use_cache=True
        )
        assert result2.cache_hit is True
    
    def test_benchmark_result_str_shows_cache_status(self):
        """Test that string representation shows (cached) for cached results."""
        data = list(range(50))
        
        # First run - uncached
        result1 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        str1 = str(result1)
        assert "(cached)" not in str1
        
        # Second run - cached
        result2 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        str2 = str(result2)
        assert "(cached)" in str2


class TestClearBenchmarkCache:
    """Tests for clearing benchmark cache."""
    
    def test_clear_benchmark_cache(self):
        """Test that clear_benchmark_cache removes all entries."""
        data = list(range(50))
        
        # Create cached entry
        result1 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        assert result1.cache_hit is False
        
        # Verify cache hit
        result2 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        assert result2.cache_hit is True
        
        # Clear cache
        count = clear_benchmark_cache()
        assert count >= 1
        
        # Verify cache miss after clear
        result3 = validate_optimization(
            simple_function,
            data,
            verbose=False,
            use_cache=True
        )
        assert result3.cache_hit is False
    
    def test_get_benchmark_cache_dir_creates_directory(self):
        """Test that cache directory is created."""
        cache_dir = get_benchmark_cache_dir()
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        assert "benchmark_cache" in str(cache_dir)
