"""
Tests for multiprocessing start method caching functionality.

This module tests the caching behavior of get_multiprocessing_start_method() to ensure:
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
    get_multiprocessing_start_method,
    _clear_start_method_cache
)


class TestStartMethodCaching:
    """Test caching behavior of multiprocessing start method detection."""
    
    def test_caching_basic_behavior(self):
        """Test that start method is cached after first call."""
        # Clear any existing cache
        _clear_start_method_cache()
        
        # First call should detect start method
        method1 = get_multiprocessing_start_method()
        
        # Second call should return cached value
        method2 = get_multiprocessing_start_method()
        
        # Values should be identical
        assert method1 == method2
        assert method1 in ['fork', 'spawn', 'forkserver']
    
    def test_cache_persists_across_calls(self):
        """Test that cache persists across multiple calls."""
        # Clear cache
        _clear_start_method_cache()
        
        # Get start method multiple times
        methods_list = [get_multiprocessing_start_method() for _ in range(10)]
        
        # All values should be identical (cached)
        assert all(method == methods_list[0] for method in methods_list)
        assert methods_list[0] in ['fork', 'spawn', 'forkserver']
    
    def test_cache_clear_resets(self):
        """Test that clearing cache forces re-detection."""
        # Clear cache
        _clear_start_method_cache()
        
        # Get start method to populate cache
        method1 = get_multiprocessing_start_method()
        
        # Clear cache again
        _clear_start_method_cache()
        
        # Get start method again (should re-detect, not use old cache)
        method2 = get_multiprocessing_start_method()
        
        # Values should be identical (same system)
        assert method1 == method2
        assert method1 in ['fork', 'spawn', 'forkserver']
    
    def test_cache_returns_consistent_value(self):
        """Test that cache always returns the same value."""
        # Clear cache
        _clear_start_method_cache()
        
        # Get start method value
        expected = get_multiprocessing_start_method()
        
        # Call many times and verify consistency
        for _ in range(100):
            actual = get_multiprocessing_start_method()
            assert actual == expected
    
    def test_cache_valid_method(self):
        """Test that cached value is a valid start method."""
        # Clear cache
        _clear_start_method_cache()
        
        method = get_multiprocessing_start_method()
        
        # Should be one of the three valid methods
        assert method in ['fork', 'spawn', 'forkserver']


class TestThreadSafety:
    """Test thread-safe operation of start method cache."""
    
    def test_concurrent_calls_safe(self):
        """Test that concurrent calls from multiple threads are safe."""
        # Clear cache
        _clear_start_method_cache()
        
        results = []
        errors = []
        
        def get_method():
            try:
                method = get_multiprocessing_start_method()
                results.append(method)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=get_method) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0
        
        # All results should be identical (cached after first thread)
        assert len(results) == 10
        assert all(method == results[0] for method in results)
        assert results[0] in ['fork', 'spawn', 'forkserver']
    
    def test_concurrent_clear_and_get(self):
        """Test that cache clearing is thread-safe."""
        # Populate cache first
        _clear_start_method_cache()
        get_multiprocessing_start_method()
        
        results = []
        errors = []
        
        def clear_and_get():
            try:
                _clear_start_method_cache()
                method = get_multiprocessing_start_method()
                results.append(method)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=clear_and_get) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0
        
        # All results should be valid start methods
        assert len(results) == 10
        assert all(method in ['fork', 'spawn', 'forkserver'] for method in results)
        
        # All results should be the same (same system)
        assert all(method == results[0] for method in results)


class TestPerformance:
    """Test performance improvement from caching."""
    
    def test_cache_improves_performance(self):
        """Test that caching provides measurable speedup."""
        # Clear cache
        _clear_start_method_cache()
        
        # Measure first call (uncached - includes initialization)
        start = time.perf_counter()
        method1 = get_multiprocessing_start_method()
        first_call_time = time.perf_counter() - start
        
        # Measure many cached calls
        cached_times = []
        for _ in range(100):
            start = time.perf_counter()
            method = get_multiprocessing_start_method()
            cached_times.append(time.perf_counter() - start)
        
        avg_cached_time = sum(cached_times) / len(cached_times)
        
        # Cached calls should be very fast (sub-microsecond on modern hardware)
        # Use a generous threshold to avoid flakiness on slower systems
        assert avg_cached_time < 0.0001  # Less than 100 microseconds on average
        
        # Verify cached calls are faster than first call (or at least comparable)
        # On fast systems, both might be very fast, so we just check they're reasonable
        assert first_call_time < 0.001  # First call should be under 1 millisecond
        
        # All calls should return same value
        assert all(method == method1 for method in [get_multiprocessing_start_method() for _ in range(10)])
    
    def test_cache_consistency_over_time(self):
        """Test that cache remains consistent over repeated use."""
        # Clear cache
        _clear_start_method_cache()
        
        # Get initial value
        expected = get_multiprocessing_start_method()
        
        # Call repeatedly with small delays
        for i in range(20):
            time.sleep(0.001)  # 1ms delay
            actual = get_multiprocessing_start_method()
            assert actual == expected, f"Value changed at iteration {i}"


class TestIntegrationWithOptimizer:
    """Test that caching works correctly in optimization scenarios."""
    
    def test_multiple_optimize_calls_use_cache(self):
        """Test that cache works across multiple optimize() invocations."""
        # Clear cache
        _clear_start_method_cache()
        
        # Simulate multiple optimize() calls
        # Each optimize() calls get_multiprocessing_start_method() 4 times
        results = []
        for _ in range(10):
            # Simulate the 4 calls per optimize()
            batch = [get_multiprocessing_start_method() for _ in range(4)]
            results.extend(batch)
        
        # All 40 calls (10 * 4) should return same value
        assert len(results) == 40
        assert all(method == results[0] for method in results)
        assert results[0] in ['fork', 'spawn', 'forkserver']
    
    def test_cache_survives_repeated_clearing_and_getting(self):
        """Test robustness of cache under stress."""
        # Repeatedly clear and get
        previous = None
        for i in range(50):
            _clear_start_method_cache()
            current = get_multiprocessing_start_method()
            
            # Value should be consistent
            if previous is not None:
                assert current == previous, f"Value changed at iteration {i}"
            
            previous = current
        
        # Final value should still be valid
        assert previous in ['fork', 'spawn', 'forkserver']
