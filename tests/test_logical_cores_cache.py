"""
Tests for logical core count caching functionality.

This module tests the caching behavior of get_logical_cores() to ensure:
1. The cache is populated after first call
2. Subsequent calls use cached value (no re-detection)
3. Cache can be cleared for testing
4. Thread-safe operation
5. Performance improvement from caching
"""

import time
import threading
import pytest
from amorsize.system_info import (
    get_logical_cores,
    _clear_logical_cores_cache
)


class TestLogicalCoresCaching:
    """Test caching behavior of logical core count detection."""
    
    def test_caching_basic_behavior(self):
        """Test that logical core count is cached after first call."""
        # Clear any existing cache
        _clear_logical_cores_cache()
        
        # First call should detect cores
        cores1 = get_logical_cores()
        
        # Second call should return cached value
        cores2 = get_logical_cores()
        
        # Values should be identical
        assert cores1 == cores2
        assert cores1 > 0  # Sanity check - should have at least 1 core
    
    def test_cache_persists_across_calls(self):
        """Test that cache persists across multiple calls."""
        # Clear cache
        _clear_logical_cores_cache()
        
        # Get cores multiple times
        cores_list = [get_logical_cores() for _ in range(10)]
        
        # All values should be identical (cached)
        assert all(cores == cores_list[0] for cores in cores_list)
        assert cores_list[0] > 0
    
    def test_cache_clear_resets(self):
        """Test that clearing cache forces re-detection."""
        # Clear cache
        _clear_logical_cores_cache()
        
        # Get cores to populate cache
        cores1 = get_logical_cores()
        
        # Clear cache again
        _clear_logical_cores_cache()
        
        # Get cores again (should re-detect, not use old cache)
        cores2 = get_logical_cores()
        
        # Values should be identical (same system)
        assert cores1 == cores2
        assert cores1 > 0
    
    def test_cache_returns_consistent_value(self):
        """Test that cache always returns the same value."""
        # Clear cache
        _clear_logical_cores_cache()
        
        # Get cores value
        expected = get_logical_cores()
        
        # Call many times and verify consistency
        for _ in range(100):
            actual = get_logical_cores()
            assert actual == expected
    
    def test_cache_reasonable_value(self):
        """Test that cached value is reasonable (1-512 logical cores)."""
        # Clear cache
        _clear_logical_cores_cache()
        
        cores = get_logical_cores()
        
        # Should be at least 1 core
        assert cores >= 1
        
        # Should be less than 512 (reasonable upper bound for 2026)
        # Logical cores can be 2x physical due to hyperthreading
        assert cores <= 512


class TestThreadSafety:
    """Test thread-safe operation of logical cores cache."""
    
    def test_concurrent_calls_safe(self):
        """Test that concurrent calls from multiple threads are safe."""
        # Clear cache
        _clear_logical_cores_cache()
        
        results = []
        
        def get_and_store():
            cores = get_logical_cores()
            results.append(cores)
        
        # Start multiple threads calling get_logical_cores concurrently
        threads = [threading.Thread(target=get_and_store) for _ in range(10)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should get the same value
        assert len(results) == 10
        assert all(cores == results[0] for cores in results)
        assert results[0] > 0
    
    def test_concurrent_clear_and_get(self):
        """Test that concurrent clear and get operations don't cause issues."""
        # Clear cache initially
        _clear_logical_cores_cache()
        
        results = []
        
        def clear_and_get():
            _clear_logical_cores_cache()
            cores = get_logical_cores()
            results.append(cores)
        
        # Start threads that clear and get concurrently
        threads = [threading.Thread(target=clear_and_get) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All results should be valid (>= 1)
        assert len(results) == 5
        assert all(cores >= 1 for cores in results)
        
        # All results should be the same (same system)
        assert all(cores == results[0] for cores in results)


class TestCacheClearFunction:
    """Test the cache clearing helper function."""
    
    def test_clear_function_exists(self):
        """Test that clear function is accessible."""
        # Should not raise
        _clear_logical_cores_cache()
    
    def test_clear_function_runs_without_error(self):
        """Test that clear function runs without error."""
        # Populate cache
        get_logical_cores()
        
        # Clear should not raise
        _clear_logical_cores_cache()
        
        # Get again should work
        cores = get_logical_cores()
        assert cores > 0
    
    def test_multiple_clears_safe(self):
        """Test that clearing cache multiple times is safe."""
        for _ in range(10):
            _clear_logical_cores_cache()
        
        # Should still work
        cores = get_logical_cores()
        assert cores > 0


class TestPerformanceImprovement:
    """Test that caching provides performance improvement."""
    
    def test_cached_calls_are_fast(self):
        """Test that cached calls are faster than initial detection."""
        # Clear cache to start fresh
        _clear_logical_cores_cache()
        
        # Measure first call (detection via os.cpu_count)
        start1 = time.perf_counter()
        cores1 = get_logical_cores()
        time1 = time.perf_counter() - start1
        
        # Measure second call (cached)
        start2 = time.perf_counter()
        cores2 = get_logical_cores()
        time2 = time.perf_counter() - start2
        
        # Values should match
        assert cores1 == cores2
        
        # Cached call should be significantly faster
        # We expect at least 5x speedup from caching
        # os.cpu_count() is faster than physical core detection but still
        # involves system calls, while cached call is just a lookup
        # Avoid division by zero if cached call is extremely fast
        if time2 > 0:
            speedup = time1 / time2
            assert speedup > 5, (
                f"Cached call ({time2:.6f}s) should be at least 5x faster than "
                f"first call ({time1:.6f}s), but was only {speedup:.1f}x faster"
            )
        else:
            # Cached call is so fast it's effectively zero - that's excellent!
            assert time1 > 0  # First call should take measurable time
    
    def test_cache_eliminates_repeated_detection(self):
        """Test that cache eliminates repeated detection overhead."""
        # Clear cache
        _clear_logical_cores_cache()
        
        # First call (detection)
        get_logical_cores()
        
        # Measure time for 1000 cached calls
        start = time.perf_counter()
        for _ in range(1000):
            get_logical_cores()
        elapsed = time.perf_counter() - start
        
        # 1000 cached calls should take less than 1ms total
        # This demonstrates that we're not re-detecting on each call
        assert elapsed < 0.001, (
            f"1000 cached calls took {elapsed*1000:.3f}ms, "
            f"suggesting re-detection is happening"
        )


class TestIntegrationWithOptimizer:
    """Test that caching integrates properly with optimizer usage patterns."""
    
    def test_multiple_optimizations_use_cache(self):
        """Test that multiple optimize() calls benefit from caching."""
        from amorsize import optimize
        
        # Clear cache
        _clear_logical_cores_cache()
        
        def simple_func(x):
            return x * 2
        
        data = range(100)
        
        # Multiple optimizations should all benefit from cached cores
        # First optimization will detect cores
        result1 = optimize(simple_func, data)
        
        # Subsequent optimizations should use cached value
        result2 = optimize(simple_func, data)
        result3 = optimize(simple_func, data)
        
        # All should succeed
        assert result1.n_jobs > 0
        assert result2.n_jobs > 0
        assert result3.n_jobs > 0
    
    def test_cache_consistent_across_optimize_calls(self):
        """Test that logical cores value is consistent across optimize calls."""
        from amorsize import optimize
        
        # Clear cache
        _clear_logical_cores_cache()
        
        def simple_func(x):
            return x ** 2
        
        data = range(50)
        
        # Get results from multiple optimizations with profiling enabled
        results = [optimize(simple_func, data, profile=True) for _ in range(5)]
        
        # All should succeed and get consistent logical core count
        assert all(r.n_jobs > 0 for r in results)
        
        # Check diagnostic profiles report same logical cores
        profiles = [r.profile for r in results if r.profile]
        
        if profiles:
            logical_cores_values = [p.logical_cores for p in profiles]
            # All should report the same logical core count (it's cached)
            assert all(
                lc == logical_cores_values[0] 
                for lc in logical_cores_values
            ), f"Logical cores values differ: {logical_cores_values}"


class TestLogicalVsPhysicalCores:
    """Test relationship between logical and physical cores."""
    
    def test_logical_cores_at_least_physical(self):
        """Test that logical cores >= physical cores (due to hyperthreading)."""
        from amorsize.system_info import get_physical_cores
        
        # Clear both caches
        _clear_logical_cores_cache()
        from amorsize.system_info import _clear_physical_cores_cache
        _clear_physical_cores_cache()
        
        logical = get_logical_cores()
        physical = get_physical_cores()
        
        # Logical cores should be >= physical cores
        # Typically 2x physical on systems with hyperthreading
        assert logical >= physical, (
            f"Logical cores ({logical}) should be >= physical cores ({physical})"
        )
    
    def test_logical_cores_reasonable_multiple_of_physical(self):
        """Test that logical cores is a reasonable multiple of physical cores."""
        from amorsize.system_info import get_physical_cores
        
        # Clear both caches
        _clear_logical_cores_cache()
        from amorsize.system_info import _clear_physical_cores_cache
        _clear_physical_cores_cache()
        
        logical = get_logical_cores()
        physical = get_physical_cores()
        
        # Typical ratios: 1x (no HT), 2x (HT), sometimes 4x on certain CPUs
        # Should not exceed 4x in practice
        ratio = logical / physical
        assert 1 <= ratio <= 4, (
            f"Logical/Physical ratio ({ratio:.1f}) should be between 1x and 4x"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
