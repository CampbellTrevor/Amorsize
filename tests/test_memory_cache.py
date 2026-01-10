"""
Tests for available memory caching functionality.

This module tests the caching behavior of get_available_memory() to ensure:
1. The cache is populated after first call
2. Subsequent calls within TTL use cached value (no re-detection)
3. Cache expires after TTL and re-detects
4. Cache can be cleared for testing
5. Thread-safe operation
6. Performance improvement from caching
"""

import time
import threading
import pytest
from amorsize.system_info import (
    get_available_memory,
    _clear_memory_cache,
    MEMORY_CACHE_TTL
)


class TestMemoryCaching:
    """Test caching behavior of available memory detection."""
    
    def test_caching_basic_behavior(self):
        """Test that available memory is cached after first call."""
        # Clear any existing cache
        _clear_memory_cache()
        
        # First call should detect memory
        mem1 = get_available_memory()
        
        # Second call should return cached value
        mem2 = get_available_memory()
        
        # Values should be identical
        assert mem1 == mem2
        assert mem1 > 0  # Sanity check - should have some memory
    
    def test_cache_persists_within_ttl(self):
        """Test that cache persists across multiple calls within TTL."""
        # Clear cache
        _clear_memory_cache()
        
        # Get memory multiple times quickly (within TTL)
        mem_list = [get_available_memory() for _ in range(10)]
        
        # All values should be identical (cached)
        assert all(mem == mem_list[0] for mem in mem_list)
        assert mem_list[0] > 0
    
    def test_cache_expires_after_ttl(self):
        """Test that cache expires after TTL and re-detects."""
        # Clear cache
        _clear_memory_cache()
        
        # Get memory to populate cache
        mem1 = get_available_memory()
        
        # Wait for cache to expire (TTL + small buffer)
        time.sleep(MEMORY_CACHE_TTL + 0.1)
        
        # Get memory again (should re-detect, not use old cache)
        mem2 = get_available_memory()
        
        # Values should be close (same system, short time)
        # Allow for small variations in reported memory
        assert mem1 > 0
        assert mem2 > 0
        # Memory should be within 20% (accounting for system variations)
        assert abs(mem1 - mem2) < mem1 * 0.2
    
    def test_cache_clear_resets(self):
        """Test that clearing cache forces re-detection."""
        # Clear cache
        _clear_memory_cache()
        
        # Get memory to populate cache
        mem1 = get_available_memory()
        
        # Clear cache again
        _clear_memory_cache()
        
        # Get memory again (should re-detect, not use old cache)
        mem2 = get_available_memory()
        
        # Values should be close (same system)
        assert mem1 > 0
        assert mem2 > 0
        # Memory should be within 20%
        assert abs(mem1 - mem2) < mem1 * 0.2
    
    def test_cache_returns_consistent_value_within_ttl(self):
        """Test that cache returns the same value within TTL."""
        # Clear cache
        _clear_memory_cache()
        
        # Get memory value
        expected = get_available_memory()
        
        # Call many times quickly and verify consistency
        for _ in range(100):
            actual = get_available_memory()
            assert actual == expected
    
    def test_cache_reasonable_value(self):
        """Test that cached value is reasonable."""
        # Clear cache
        _clear_memory_cache()
        
        mem = get_available_memory()
        
        # Should be at least 100MB (conservative lower bound)
        assert mem >= 100 * 1024 * 1024
        
        # Should be less than 1TB (reasonable upper bound for 2026)
        assert mem <= 1024 * 1024 * 1024 * 1024


class TestThreadSafety:
    """Test thread-safe operation of memory cache."""
    
    def test_concurrent_calls_safe(self):
        """Test that concurrent calls from multiple threads are safe."""
        # Clear cache
        _clear_memory_cache()
        
        results = []
        
        def get_and_store():
            mem = get_available_memory()
            results.append(mem)
        
        # Start multiple threads calling get_available_memory concurrently
        threads = [threading.Thread(target=get_and_store) for _ in range(10)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should get a valid value
        assert len(results) == 10
        assert all(mem > 0 for mem in results)
        
        # All values should be identical (cached)
        assert all(mem == results[0] for mem in results)
    
    def test_concurrent_clear_and_get(self):
        """Test that concurrent clear and get operations don't cause issues."""
        # Clear cache initially
        _clear_memory_cache()
        
        results = []
        
        def clear_and_get():
            _clear_memory_cache()
            mem = get_available_memory()
            results.append(mem)
        
        # Start threads that clear and get concurrently
        threads = [threading.Thread(target=clear_and_get) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All results should be valid
        assert len(results) == 5
        assert all(mem > 0 for mem in results)
        
        # All results should be close (same system)
        avg_mem = sum(results) / len(results)
        for mem in results:
            assert abs(mem - avg_mem) < avg_mem * 0.2


class TestCacheClearFunction:
    """Test the cache clearing helper function."""
    
    def test_clear_function_exists(self):
        """Test that clear function is accessible."""
        # Should not raise
        _clear_memory_cache()
    
    def test_clear_function_runs_without_error(self):
        """Test that clear function runs without error."""
        # Populate cache
        get_available_memory()
        
        # Clear should not raise
        _clear_memory_cache()
        
        # Get again should work
        mem = get_available_memory()
        assert mem > 0
    
    def test_multiple_clears_safe(self):
        """Test that clearing cache multiple times is safe."""
        for _ in range(10):
            _clear_memory_cache()
        
        # Should still work
        mem = get_available_memory()
        assert mem > 0


class TestPerformanceImprovement:
    """Test that caching provides performance improvement."""
    
    def test_cached_calls_are_fast(self):
        """Test that cached calls are faster than initial detection."""
        # Clear cache to start fresh
        _clear_memory_cache()
        
        # Measure first call (detection)
        start1 = time.perf_counter()
        mem1 = get_available_memory()
        time1 = time.perf_counter() - start1
        
        # Measure second call (cached)
        start2 = time.perf_counter()
        mem2 = get_available_memory()
        time2 = time.perf_counter() - start2
        
        # Values should match
        assert mem1 == mem2
        
        # Cached call should be significantly faster
        # We expect at least 5x speedup from caching
        # First call may involve file I/O (/sys/fs/cgroup) and psutil system calls,
        # while cached call is just a timestamp check and lookup
        assert time2 < time1 / 5, (
            f"Cached call ({time2:.6f}s) should be at least 5x faster than "
            f"first call ({time1:.6f}s), but was only {time1/time2:.1f}x faster"
        )
    
    def test_cache_eliminates_repeated_detection(self):
        """Test that cache eliminates repeated detection overhead."""
        # Clear cache
        _clear_memory_cache()
        
        # First call (detection)
        get_available_memory()
        
        # Measure time for 100 cached calls
        start = time.perf_counter()
        for _ in range(100):
            get_available_memory()
        elapsed = time.perf_counter() - start
        
        # 100 cached calls should take less than 1ms total
        # This demonstrates that we're not re-detecting on each call
        assert elapsed < 0.001, (
            f"100 cached calls took {elapsed*1000:.3f}ms, "
            f"suggesting re-detection is happening"
        )
    
    def test_cache_performance_within_ttl(self):
        """Test that cache provides consistent performance within TTL."""
        # Clear cache
        _clear_memory_cache()
        
        # Populate cache
        get_available_memory()
        
        # Measure time for multiple calls within TTL
        timings = []
        for _ in range(10):
            start = time.perf_counter()
            get_available_memory()
            timings.append(time.perf_counter() - start)
        
        # All cached calls should be consistently fast (< 10μs each)
        for t in timings:
            assert t < 0.00001, (
                f"Cached call took {t*1000000:.1f}μs, expected < 10μs"
            )


class TestIntegrationWithOptimizer:
    """Test that caching integrates properly with optimizer usage patterns."""
    
    def test_multiple_optimizations_use_cache(self):
        """Test that multiple optimize() calls benefit from caching."""
        from amorsize import optimize
        
        # Clear cache
        _clear_memory_cache()
        
        def simple_func(x):
            return x * 2
        
        data = range(100)
        
        # Multiple optimizations should all benefit from cached memory
        # First optimization will detect memory
        result1 = optimize(simple_func, data)
        
        # Subsequent optimizations should use cached value (within TTL)
        result2 = optimize(simple_func, data)
        result3 = optimize(simple_func, data)
        
        # All should succeed
        assert result1.n_jobs > 0
        assert result2.n_jobs > 0
        assert result3.n_jobs > 0
    
    def test_cache_fast_for_rapid_optimizations(self):
        """Test that cache makes rapid optimizations faster."""
        from amorsize import optimize
        
        # Clear cache
        _clear_memory_cache()
        
        def simple_func(x):
            return x ** 2
        
        data = range(50)
        
        # Measure time for 5 rapid optimizations
        start = time.perf_counter()
        results = [optimize(simple_func, data) for _ in range(5)]
        elapsed = time.perf_counter() - start
        
        # All should succeed
        assert all(r.n_jobs > 0 for r in results)
        
        # Should complete reasonably fast (< 1 second for 5 optimizations)
        # This validates that caching is working and not causing slowdowns
        assert elapsed < 1.0, (
            f"5 optimizations took {elapsed:.3f}s, expected < 1s"
        )


class TestTTLBehavior:
    """Test time-to-live (TTL) behavior of memory cache."""
    
    def test_ttl_constant_reasonable(self):
        """Test that TTL constant is reasonable."""
        # TTL should be at least 0.1 seconds
        assert MEMORY_CACHE_TTL >= 0.1
        
        # TTL should be at most 60 seconds (memory can change)
        assert MEMORY_CACHE_TTL <= 60.0
    
    def test_cache_refreshes_after_ttl(self):
        """Test that cache refreshes after TTL expires."""
        # Clear cache
        _clear_memory_cache()
        
        # First call
        mem1 = get_available_memory()
        
        # Wait for TTL to expire
        time.sleep(MEMORY_CACHE_TTL + 0.1)
        
        # Second call should refresh cache (not use expired value)
        mem2 = get_available_memory()
        
        # Third call (immediately after) should use newly refreshed cache
        mem3 = get_available_memory()
        
        # mem2 and mem3 should be identical (same cache refresh)
        assert mem2 == mem3
        
        # All values should be reasonable
        assert mem1 > 0
        assert mem2 > 0
        assert mem3 > 0
    
    def test_ttl_prevents_stale_data(self):
        """Test that TTL prevents stale data from being used indefinitely."""
        # Clear cache
        _clear_memory_cache()
        
        # Get memory at different times
        measurements = []
        
        for i in range(3):
            mem = get_available_memory()
            measurements.append(mem)
            
            if i < 2:  # Don't sleep after last measurement
                # Wait for TTL to expire
                time.sleep(MEMORY_CACHE_TTL + 0.1)
        
        # All measurements should be valid
        assert all(mem > 0 for mem in measurements)
        
        # Measurements should be close (same system, short total time)
        avg_mem = sum(measurements) / len(measurements)
        for mem in measurements:
            assert abs(mem - avg_mem) < avg_mem * 0.2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
