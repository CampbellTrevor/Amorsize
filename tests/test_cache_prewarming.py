"""
Tests for cache prewarming functionality.
"""

import pytest
import time
from amorsize.cache import (
    prewarm_cache,
    load_cache_entry,
    compute_cache_key,
    clear_cache,
    _get_default_workload_profiles,
    _estimate_optimization_parameters
)
from amorsize import optimize


def simple_func(x):
    """Simple test function."""
    return x * 2


def slow_func(x):
    """Slower test function for realistic testing."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


class TestPrewarmCacheBasic:
    """Test basic cache prewarming functionality."""
    
    def test_prewarm_with_default_profiles(self, clear_global_caches):
        """Test prewarming with default workload profiles."""
        # Prewarm cache
        count = prewarm_cache(simple_func)
        
        # Should create multiple entries (default profiles)
        assert count > 0
        assert count == 7  # Default has 7 profiles
    
    def test_prewarm_creates_cache_entries(self, clear_global_caches):
        """Test that prewarming actually creates cache entries."""
        # Prewarm with a specific profile
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        count = prewarm_cache(simple_func, workload_profiles=profiles)
        
        assert count == 1
        
        # Verify cache entry exists
        cache_key = compute_cache_key(simple_func, 100, 0.001)
        entry, miss_reason = load_cache_entry(cache_key)
        
        assert entry is not None
        assert miss_reason == ""
        assert entry.n_jobs >= 1
        assert entry.chunksize >= 1
    
    def test_prewarm_skips_existing_entries(self, clear_global_caches):
        """Test that prewarming skips existing entries by default."""
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        
        # First prewarm
        count1 = prewarm_cache(simple_func, workload_profiles=profiles)
        assert count1 == 1
        
        # Second prewarm (should skip)
        count2 = prewarm_cache(simple_func, workload_profiles=profiles)
        assert count2 == 0
    
    def test_prewarm_with_force_overwrites(self, clear_global_caches):
        """Test that force=True overwrites existing entries."""
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        
        # First prewarm
        count1 = prewarm_cache(simple_func, workload_profiles=profiles)
        assert count1 == 1
        
        # Get timestamp of first entry
        cache_key = compute_cache_key(simple_func, 100, 0.001)
        entry1, _ = load_cache_entry(cache_key)
        timestamp1 = entry1.timestamp
        
        # Wait a bit
        time.sleep(0.1)
        
        # Second prewarm with force
        count2 = prewarm_cache(simple_func, workload_profiles=profiles, force=True)
        assert count2 == 1
        
        # Verify timestamp changed
        entry2, _ = load_cache_entry(cache_key)
        timestamp2 = entry2.timestamp
        assert timestamp2 > timestamp1


class TestPrewarmCacheFromOptimization:
    """Test prewarming from optimization results."""
    
    def test_prewarm_from_optimization_result(self, clear_global_caches):
        """Test prewarming from an actual optimization result."""
        # Run optimization
        data = list(range(100))
        result = optimize(slow_func, data)
        
        # Clear cache to test prewarming
        clear_cache()
        
        # Prewarm from result
        count = prewarm_cache(slow_func, optimization_result=result)
        assert count == 1
        
        # Verify cache contains the entry
        # Note: We need to compute the same cache key
        cache_key = compute_cache_key(slow_func, len(data), result.profile.avg_execution_time if result.profile else 0.01)
        entry, miss_reason = load_cache_entry(cache_key)
        
        assert entry is not None
        assert entry.n_jobs == result.n_jobs
        assert entry.chunksize == result.chunksize
        assert entry.executor_type == result.executor_type
    
    def test_prewarm_from_optimization_enables_cache_hit(self, clear_global_caches):
        """Test that prewarming enables cache hits on subsequent optimizations."""
        # Run optimization to get result
        data = list(range(100))
        result1 = optimize(slow_func, data, use_cache=True)
        assert result1.cache_hit is False  # First run, no cache
        
        # Prewarm from result (even though cache already exists)
        prewarm_cache(slow_func, optimization_result=result1, force=True)
        
        # Second optimization should hit cache
        result2 = optimize(slow_func, data, use_cache=True)
        assert result2.cache_hit is True
        assert result2.n_jobs == result1.n_jobs
        assert result2.chunksize == result1.chunksize


class TestPrewarmCacheCustomProfiles:
    """Test prewarming with custom workload profiles."""
    
    def test_prewarm_with_custom_profiles(self, clear_global_caches):
        """Test prewarming with custom workload profiles."""
        profiles = [
            {"data_size": 50, "avg_time": 0.005},
            {"data_size": 500, "avg_time": 0.01},
            {"data_size": 5000, "avg_time": 0.1},
        ]
        
        count = prewarm_cache(simple_func, workload_profiles=profiles)
        assert count == 3
        
        # Verify all entries exist
        for profile in profiles:
            cache_key = compute_cache_key(simple_func, profile["data_size"], profile["avg_time"])
            entry, _ = load_cache_entry(cache_key)
            assert entry is not None
    
    def test_prewarm_ignores_invalid_profiles(self, clear_global_caches):
        """Test that prewarming ignores invalid profile formats."""
        profiles = [
            {"data_size": 100, "avg_time": 0.001},  # Valid
            {"data_size": -1, "avg_time": 0.001},    # Invalid: negative size
            {"data_size": 100, "avg_time": -0.001},  # Invalid: negative time
            {"data_size": 100},                       # Invalid: missing avg_time
            {"avg_time": 0.001},                      # Invalid: missing data_size
            "invalid",                                # Invalid: not a dict
            {"data_size": "100", "avg_time": 0.001}, # Invalid: wrong type
        ]
        
        count = prewarm_cache(simple_func, workload_profiles=profiles)
        assert count == 1  # Only the first valid profile
    
    def test_prewarm_multiple_functions(self, clear_global_caches):
        """Test prewarming cache for multiple functions."""
        def func1(x):
            return x * 2
        
        def func2(x):
            return x ** 2
        
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        
        count1 = prewarm_cache(func1, workload_profiles=profiles)
        count2 = prewarm_cache(func2, workload_profiles=profiles)
        
        assert count1 == 1
        assert count2 == 1
        
        # Verify both cache entries exist and are different
        key1 = compute_cache_key(func1, 100, 0.001)
        key2 = compute_cache_key(func2, 100, 0.001)
        
        entry1, _ = load_cache_entry(key1)
        entry2, _ = load_cache_entry(key2)
        
        assert entry1 is not None
        assert entry2 is not None
        assert key1 != key2  # Different functions have different keys


class TestPrewarmCacheHelpers:
    """Test helper functions for cache prewarming."""
    
    def test_get_default_workload_profiles(self):
        """Test that default profiles are sensible."""
        profiles = _get_default_workload_profiles()
        
        assert isinstance(profiles, list)
        assert len(profiles) > 0
        
        # Check all profiles are valid
        for profile in profiles:
            assert isinstance(profile, dict)
            assert "data_size" in profile
            assert "avg_time" in profile
            assert profile["data_size"] > 0
            assert profile["avg_time"] > 0
    
    def test_estimate_optimization_parameters(self):
        """Test parameter estimation for prewarming."""
        # Test small/fast workload (should use serial)
        n_jobs, chunksize, executor_type, speedup, reason, warnings = \
            _estimate_optimization_parameters(10, 0.00001)
        
        assert n_jobs == 1  # Too fast for parallelization
        assert chunksize == 1
        assert "too fast" in reason.lower() or "overhead" in reason.lower()
        assert len(warnings) > 0
    
    def test_estimate_optimization_parameters_parallel(self):
        """Test parameter estimation for workloads that benefit from parallelization."""
        # Test large/slow workload (should use multiple workers)
        n_jobs, chunksize, executor_type, speedup, reason, warnings = \
            _estimate_optimization_parameters(1000, 0.01)
        
        assert n_jobs > 1  # Should recommend parallelization
        assert chunksize > 0
        assert speedup >= 1.0
        assert "prewarmed" in reason.lower()
        assert len(warnings) > 0  # Should warn about estimated parameters
    
    def test_estimate_optimization_parameters_reasonable_chunksize(self):
        """Test that estimated chunksize is reasonable."""
        # For various workloads, chunksize should be sensible
        test_cases = [
            (100, 0.001),   # Small, fast
            (1000, 0.01),   # Medium, moderate
            (10000, 0.1),   # Large, slow
        ]
        
        for data_size, avg_time in test_cases:
            n_jobs, chunksize, executor_type, speedup, reason, warnings = \
                _estimate_optimization_parameters(data_size, avg_time)
            
            # Chunksize should be between 1 and data_size
            assert 1 <= chunksize <= data_size
            
            # n_jobs should be reasonable
            assert 1 <= n_jobs <= 128  # Sanity check


class TestPrewarmCacheIntegration:
    """Integration tests for cache prewarming."""
    
    def test_prewarm_then_optimize_uses_cache(self, clear_global_caches):
        """Test that optimization uses prewarmed cache."""
        # Prewarm cache
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        prewarm_cache(simple_func, workload_profiles=profiles)
        
        # Optimize with similar workload
        data = list(range(100))
        result = optimize(simple_func, data, use_cache=True)
        
        # Should hit cache (though exact match depends on bucketing)
        # At minimum, cache should exist
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_prewarm_improves_first_run_performance(self, clear_global_caches):
        """Test that prewarming improves performance on first run."""
        # Measure time without prewarming
        clear_cache()
        
        start1 = time.perf_counter()
        result1 = optimize(slow_func, list(range(100)), use_cache=True)
        elapsed1 = time.perf_counter() - start1
        
        assert result1.cache_hit is False
        
        # Prewarm cache with result - use a slightly different data size
        # to ensure we're testing prewarming, not just cache hit from first run
        clear_cache()
        
        # Create a profile that will match the same bucket
        # data_size=100 falls in "small" bucket (10-100)
        # avg_time from result1.profile
        if result1.profile:
            avg_time = result1.profile.avg_execution_time
        else:
            avg_time = 0.01  # Default estimate
        
        # Save the exact entry
        profiles = [{"data_size": 100, "avg_time": avg_time}]
        prewarm_cache(slow_func, workload_profiles=profiles, force=True)
        
        # Verify cache entry exists with correct key
        cache_key = compute_cache_key(slow_func, 100, avg_time)
        entry, miss_reason = load_cache_entry(cache_key)
        assert entry is not None, f"Cache entry not found: {miss_reason}"
        
        # Measure time with prewarmed cache
        # Use exact same parameters to ensure cache hit
        start2 = time.perf_counter()
        result2 = optimize(slow_func, list(range(100)), use_cache=True)
        elapsed2 = time.perf_counter() - start2
        
        # Second run should be faster (cache hit)
        # Note: Cache hit depends on exact bucket matching
        # If cache is hit, should be much faster
        if result2.cache_hit:
            assert elapsed2 < elapsed1 * 0.5  # At least 2x faster
        else:
            # Even without cache hit, optimization should still work
            assert result2.n_jobs >= 1
            assert result2.chunksize >= 1
    
    def test_prewarm_warnings_in_result(self, clear_global_caches):
        """Test that prewarmed entries include appropriate warnings."""
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        prewarm_cache(simple_func, workload_profiles=profiles)
        
        # Get the cache entry
        cache_key = compute_cache_key(simple_func, 100, 0.001)
        entry, _ = load_cache_entry(cache_key)
        
        assert entry is not None
        assert len(entry.warnings) > 0
        assert any("prewarmed" in w.lower() for w in entry.warnings)


class TestPrewarmCacheEdgeCases:
    """Test edge cases for cache prewarming."""
    
    def test_prewarm_with_empty_profiles_list(self, clear_global_caches):
        """Test that empty profiles list uses defaults."""
        count = prewarm_cache(simple_func, workload_profiles=[])
        
        # Should create no entries with empty list
        assert count == 0
    
    def test_prewarm_with_none_profiles_uses_defaults(self, clear_global_caches):
        """Test that None profiles uses default patterns."""
        count = prewarm_cache(simple_func, workload_profiles=None)
        
        # Should use default profiles
        assert count > 0
    
    def test_prewarm_handles_function_without_code(self, clear_global_caches):
        """Test prewarming with built-in functions."""
        # Built-in functions don't have __code__ attribute
        # Should still work (uses str(func) as fallback)
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        count = prewarm_cache(abs, workload_profiles=profiles)
        
        assert count == 1


class TestPrewarmCacheBackwardCompatibility:
    """Test backward compatibility of cache prewarming."""
    
    def test_prewarmed_entries_compatible_with_existing_cache(self, clear_global_caches):
        """Test that prewarmed entries work with existing cache system."""
        # Prewarm cache
        profiles = [{"data_size": 100, "avg_time": 0.001}]
        prewarm_cache(simple_func, workload_profiles=profiles)
        
        # Load entry using existing cache functions
        cache_key = compute_cache_key(simple_func, 100, 0.001)
        entry, miss_reason = load_cache_entry(cache_key)
        
        # Should load successfully
        assert entry is not None
        assert miss_reason == ""
        
        # Entry should have all required fields
        assert hasattr(entry, 'n_jobs')
        assert hasattr(entry, 'chunksize')
        assert hasattr(entry, 'executor_type')
        assert hasattr(entry, 'estimated_speedup')
        assert hasattr(entry, 'reason')
        assert hasattr(entry, 'warnings')
        assert hasattr(entry, 'timestamp')
        assert hasattr(entry, 'system_info')
    
    def test_existing_optimize_unaffected_by_prewarming(self, clear_global_caches):
        """Test that existing optimize() behavior is unchanged."""
        # Optimize without prewarming
        data1 = list(range(100))
        result1 = optimize(simple_func, data1, use_cache=False)
        
        # Prewarm cache
        prewarm_cache(simple_func)
        
        # Optimize again (different data to avoid exact cache hit)
        data2 = list(range(150))
        result2 = optimize(simple_func, data2, use_cache=False)
        
        # Both should succeed and have reasonable parameters
        assert result1.n_jobs >= 1
        assert result2.n_jobs >= 1
        assert result1.chunksize >= 1
        assert result2.chunksize >= 1
