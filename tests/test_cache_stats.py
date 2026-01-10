"""
Tests for cache statistics and introspection functionality.

This module tests the cache statistics features added in Iteration 73,
which provide visibility into cache usage, effectiveness, and health.
"""

import json
import time
from pathlib import Path
import pytest

from amorsize import optimize, validate_optimization, get_cache_stats, get_benchmark_cache_stats, CacheStats
from amorsize.cache import (
    get_cache_dir,
    get_benchmark_cache_dir,
    save_cache_entry,
    save_benchmark_cache_entry,
    compute_cache_key,
    compute_benchmark_cache_key
)


def simple_func(x):
    """Simple test function."""
    return x * 2


def slow_func(x):
    """Slower test function for benchmark tests."""
    time.sleep(0.001)  # 1ms
    return x * 2


class TestCacheStatsClass:
    """Test the CacheStats class itself."""
    
    def test_cache_stats_initialization(self):
        """Test CacheStats initialization."""
        stats = CacheStats()
        assert stats.total_entries == 0
        assert stats.valid_entries == 0
        assert stats.expired_entries == 0
        assert stats.incompatible_entries == 0
        assert stats.total_size_bytes == 0
        assert stats.oldest_entry_age is None
        assert stats.newest_entry_age is None
        assert stats.cache_dir is None
    
    def test_cache_stats_with_values(self):
        """Test CacheStats with actual values."""
        stats = CacheStats(
            total_entries=10,
            valid_entries=8,
            expired_entries=1,
            incompatible_entries=1,
            total_size_bytes=50000,
            oldest_entry_age=86400.0,  # 1 day
            newest_entry_age=3600.0,  # 1 hour
            cache_dir="/tmp/test"
        )
        
        assert stats.total_entries == 10
        assert stats.valid_entries == 8
        assert stats.expired_entries == 1
        assert stats.incompatible_entries == 1
        assert stats.total_size_bytes == 50000
        assert stats.oldest_entry_age == 86400.0
        assert stats.newest_entry_age == 3600.0
        assert stats.cache_dir == "/tmp/test"
    
    def test_cache_stats_repr(self):
        """Test CacheStats __repr__ method."""
        stats = CacheStats(
            total_entries=5,
            valid_entries=4,
            expired_entries=1,
            incompatible_entries=0,
            total_size_bytes=2048
        )
        
        repr_str = repr(stats)
        assert "CacheStats" in repr_str
        assert "total=5" in repr_str
        assert "valid=4" in repr_str
        assert "expired=1" in repr_str
        assert "incompatible=0" in repr_str
        assert "KB" in repr_str  # 2048 bytes = 2KB
    
    def test_cache_stats_str(self):
        """Test CacheStats __str__ method."""
        stats = CacheStats(
            total_entries=10,
            valid_entries=8,
            expired_entries=1,
            incompatible_entries=1,
            total_size_bytes=50000,
            oldest_entry_age=86400.0,
            newest_entry_age=3600.0,
            cache_dir="/tmp/test"
        )
        
        str_output = str(stats)
        assert "=== Cache Statistics ===" in str_output
        assert "Total entries: 10" in str_output
        assert "Valid entries: 8" in str_output
        assert "Expired entries: 1" in str_output
        assert "Incompatible entries: 1" in str_output
        assert "/tmp/test" in str_output
        assert "day" in str_output.lower()  # Oldest age formatting
        assert "hour" in str_output.lower()  # Newest age formatting
    
    def test_format_bytes(self):
        """Test byte formatting."""
        stats = CacheStats()
        
        # Test different sizes
        assert "B" in stats._format_bytes(100)
        assert "KB" in stats._format_bytes(2048)
        assert "MB" in stats._format_bytes(2 * 1024 * 1024)
        assert "GB" in stats._format_bytes(2 * 1024 * 1024 * 1024)
    
    def test_format_age(self):
        """Test age formatting."""
        stats = CacheStats()
        
        # Test different ages
        assert "second" in stats._format_age(30)
        assert "minute" in stats._format_age(120)
        assert "hour" in stats._format_age(7200)
        assert "day" in stats._format_age(172800)


class TestGetCacheStats:
    """Test get_cache_stats() function."""
    
    def test_empty_cache_stats(self):
        """Test cache stats for empty cache."""
        stats = get_cache_stats()
        
        assert stats.total_entries == 0
        assert stats.valid_entries == 0
        assert stats.expired_entries == 0
        assert stats.incompatible_entries == 0
        assert stats.total_size_bytes == 0
        assert stats.oldest_entry_age is None
        assert stats.newest_entry_age is None
        assert stats.cache_dir is not None
        assert str(get_cache_dir()) in stats.cache_dir
    
    def test_cache_stats_with_valid_entries(self):
        """Test cache stats with valid entries."""
        # Create some cache entries with significantly different sizes to avoid bucketing
        
        # Use very different data sizes to ensure different cache keys
        # (bucketing groups similar sizes)
        result1 = optimize(simple_func, list(range(10)), use_cache=True)  # tiny bucket
        result2 = optimize(simple_func, list(range(150)), use_cache=True)  # medium bucket
        result3 = optimize(simple_func, list(range(2000)), use_cache=True)  # large bucket
        
        stats = get_cache_stats()
        
        # Should have at least 3 entries (one per bucket)
        assert stats.total_entries >= 3
        assert stats.valid_entries >= 3
        assert stats.total_size_bytes > 0
        assert stats.oldest_entry_age is not None
        assert stats.newest_entry_age is not None
        
        # Ages should be very recent (< 1 second)
        assert stats.newest_entry_age < 2.0
        assert stats.oldest_entry_age >= stats.newest_entry_age
    
    def test_cache_stats_with_expired_entries(self):
        """Test cache stats correctly identifies expired entries."""
        cache_dir = get_cache_dir()
        
        # Create a valid cache entry
        cache_key = "test_expired_entry"
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=10,
            executor_type="process",
            estimated_speedup=1.5,
            reason="Test entry",
            warnings=[]
        )
        
        # Manually modify its timestamp to be expired (8 days old)
        cache_file = cache_dir / f"{cache_key}.json"
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        # Set timestamp to 8 days ago
        data['timestamp'] = time.time() - (8 * 24 * 60 * 60)
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
        
        # Get stats with default TTL (7 days)
        stats = get_cache_stats()
        
        # Should detect at least one expired entry
        assert stats.expired_entries >= 1
    
    def test_cache_stats_with_corrupted_entries(self):
        """Test cache stats correctly identifies corrupted entries."""
        cache_dir = get_cache_dir()
        
        # Create a corrupted cache file (invalid JSON)
        corrupted_file = cache_dir / "corrupted_entry.json"
        with open(corrupted_file, 'w') as f:
            f.write("{ this is not valid json }")
        
        stats = get_cache_stats()
        
        # Should count corrupted entry as incompatible
        assert stats.incompatible_entries >= 1
        
        # Clean up
        corrupted_file.unlink()
    
    def test_cache_stats_ttl_parameter(self):
        """Test cache stats respects custom TTL."""
        # Create a cache entry
        cache_key = "test_ttl_entry"
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=10,
            executor_type="process",
            estimated_speedup=1.5,
            reason="Test entry",
            warnings=[]
        )
        
        # Modify timestamp to be 2 days old
        cache_file = get_cache_dir() / f"{cache_key}.json"
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        data['timestamp'] = time.time() - (2 * 24 * 60 * 60)
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
        
        # With 1 day TTL, should be expired
        stats_short_ttl = get_cache_stats(ttl_seconds=1 * 24 * 60 * 60)
        
        # With 7 day TTL, should be valid
        stats_long_ttl = get_cache_stats(ttl_seconds=7 * 24 * 60 * 60)
        
        # The entry should be expired with short TTL but valid with long TTL
        # (Can't assert exact counts due to potential other entries, but can check categories)
        assert stats_short_ttl.expired_entries > stats_long_ttl.expired_entries or \
               stats_short_ttl.valid_entries < stats_long_ttl.valid_entries


class TestGetBenchmarkCacheStats:
    """Test get_benchmark_cache_stats() function."""
    
    def test_empty_benchmark_cache_stats(self):
        """Test benchmark cache stats for empty cache."""
        stats = get_benchmark_cache_stats()
        
        assert stats.total_entries == 0
        assert stats.valid_entries == 0
        assert stats.expired_entries == 0
        assert stats.incompatible_entries == 0
        assert stats.total_size_bytes == 0
        assert stats.oldest_entry_age is None
        assert stats.newest_entry_age is None
        assert stats.cache_dir is not None
        assert str(get_benchmark_cache_dir()) in stats.cache_dir
    
    def test_benchmark_cache_stats_with_valid_entries(self):
        """Test benchmark cache stats with valid entries."""
        # Create some benchmark cache entries
        data = list(range(50))
        
        # Run validations to populate benchmark cache
        result1 = validate_optimization(slow_func, data[:20], use_cache=True)
        result2 = validate_optimization(slow_func, data[:30], use_cache=True)
        result3 = validate_optimization(slow_func, data[:40], use_cache=True)
        
        stats = get_benchmark_cache_stats()
        
        # Should have at least 3 entries
        assert stats.total_entries >= 3
        assert stats.valid_entries >= 3
        assert stats.total_size_bytes > 0
        assert stats.oldest_entry_age is not None
        assert stats.newest_entry_age is not None
        
        # Ages should be recent
        assert stats.newest_entry_age < 5.0  # Within 5 seconds
        assert stats.oldest_entry_age >= stats.newest_entry_age
    
    def test_benchmark_cache_stats_with_expired_entries(self):
        """Test benchmark cache stats identifies expired benchmark entries."""
        cache_dir = get_benchmark_cache_dir()
        
        # Create a valid benchmark cache entry
        cache_key = "benchmark_expired_entry"
        save_benchmark_cache_entry(
            cache_key=cache_key,
            serial_time=10.0,
            parallel_time=5.0,
            actual_speedup=2.0,
            n_jobs=2,
            chunksize=10
        )
        
        # Modify timestamp to be expired (8 days old)
        cache_file = cache_dir / f"{cache_key}.json"
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        data['timestamp'] = time.time() - (8 * 24 * 60 * 60)
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
        
        stats = get_benchmark_cache_stats()
        
        # Should detect at least one expired entry
        assert stats.expired_entries >= 1
    
    def test_benchmark_cache_stats_with_corrupted_entries(self):
        """Test benchmark cache stats identifies corrupted entries."""
        cache_dir = get_benchmark_cache_dir()
        
        # Create a corrupted cache file
        corrupted_file = cache_dir / "corrupted_benchmark.json"
        with open(corrupted_file, 'w') as f:
            f.write("{ invalid json }")
        
        stats = get_benchmark_cache_stats()
        
        # Should count corrupted entry as incompatible
        assert stats.incompatible_entries >= 1
        
        # Clean up
        corrupted_file.unlink()


class TestCacheStatsIntegration:
    """Integration tests for cache statistics."""
    
    def test_cache_stats_after_multiple_optimizations(self):
        """Test cache stats accurately tracks multiple optimizations."""
        # Perform optimizations with very different sizes to avoid cache key collisions
        # The cache uses bucketing, so we need to use sizes that fall into different buckets:
        # tiny (<10), small (10-100), medium (100-1000), large (1000-10000), xlarge (>10000)
        
        sizes_and_buckets = [
            (5, "tiny"),
            (50, "small"),
            (500, "medium"),
            (5000, "large"),
            (15000, "xlarge")
        ]
        
        for size, bucket_name in sizes_and_buckets:
            result = optimize(simple_func, list(range(size)), use_cache=True)
        
        stats = get_cache_stats()
        
        # Should have at least 5 entries (one per bucket)
        assert stats.total_entries >= 5
        assert stats.valid_entries >= 5
        
        # String representation should be informative
        stats_str = str(stats)
        assert "Total entries" in stats_str
        assert "Valid entries" in stats_str
    
    def test_both_cache_stats_independent(self):
        """Test that optimization and benchmark cache stats are independent."""
        # Populate optimization cache
        opt_result = optimize(simple_func, list(range(100)), use_cache=True)
        
        # Populate benchmark cache
        bench_result = validate_optimization(slow_func, list(range(30)), use_cache=True)
        
        # Get both stats
        opt_stats = get_cache_stats()
        bench_stats = get_benchmark_cache_stats()
        
        # Both should have entries
        assert opt_stats.total_entries > 0
        assert bench_stats.total_entries > 0
        
        # Cache directories should be different
        assert opt_stats.cache_dir != bench_stats.cache_dir
        assert "optimization_cache" in opt_stats.cache_dir
        assert "benchmark_cache" in bench_stats.cache_dir
    
    def test_cache_stats_performance(self):
        """Test that cache stats collection is fast."""
        # Create cache entries in different buckets to ensure multiple entries
        # Use very different sizes to span multiple cache key buckets
        sizes = [5, 50, 500, 5000, 15000, 8, 80, 800, 8000, 20000]
        
        for size in sizes:
            result = optimize(simple_func, list(range(size)), use_cache=True)
        
        # Measure stats collection time
        start_time = time.time()
        stats = get_cache_stats()
        elapsed_time = time.time() - start_time
        
        # Should be very fast (< 100ms even with many entries)
        assert elapsed_time < 0.1
        # Should have multiple entries (at least 5 different buckets)
        assert stats.total_entries >= 5


class TestCacheStatsExport:
    """Test that cache stats functions are properly exported."""
    
    def test_cache_stats_importable(self):
        """Test that CacheStats class is importable from main package."""
        from amorsize import CacheStats
        
        stats = CacheStats()
        assert isinstance(stats, CacheStats)
    
    def test_get_cache_stats_importable(self):
        """Test that get_cache_stats is importable from main package."""
        from amorsize import get_cache_stats
        
        stats = get_cache_stats()
        assert isinstance(stats, CacheStats)
    
    def test_get_benchmark_cache_stats_importable(self):
        """Test that get_benchmark_cache_stats is importable from main package."""
        from amorsize import get_benchmark_cache_stats
        
        stats = get_benchmark_cache_stats()
        assert isinstance(stats, CacheStats)
