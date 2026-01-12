"""
Tests for function hash caching optimization.

This module tests the performance optimization that caches function
bytecode hashes to avoid repeated SHA256 computations.
"""

import time
import pytest
from amorsize.cache import compute_cache_key, _function_hash_cache, _function_hash_cache_lock


def test_function_hash_is_cached():
    """Test that function hash is cached after first computation."""
    # Clear the cache first
    with _function_hash_cache_lock:
        _function_hash_cache.clear()
    
    def test_func(x):
        return x * 2
    
    # First call should cache the hash
    key1 = compute_cache_key(test_func, 100, 0.001)
    
    # Check that the function is now in the cache
    func_id = id(test_func)
    assert func_id in _function_hash_cache
    
    # Second call should use cached hash
    key2 = compute_cache_key(test_func, 100, 0.001)
    
    # Keys should be identical
    assert key1 == key2


def test_function_hash_cache_different_functions():
    """Test that different functions can have different or same cached hashes."""
    # Clear the cache first
    with _function_hash_cache_lock:
        _function_hash_cache.clear()
    
    def func1(x):
        return x * 2
    
    def func2(x):
        """Different function with significantly different code."""
        result = 0
        for i in range(100):
            result += x * i
        return result
    
    # Compute keys for both functions
    key1 = compute_cache_key(func1, 100, 0.001)
    key2 = compute_cache_key(func2, 100, 0.001)
    
    # Keys should be different (different function hashes)
    assert key1 != key2
    
    # Both should be cached
    assert id(func1) in _function_hash_cache
    assert id(func2) in _function_hash_cache
    
    # Cached hashes should be different
    assert _function_hash_cache[id(func1)] != _function_hash_cache[id(func2)]


def test_function_hash_cache_performance():
    """Test that cached hash lookups provide measurable performance benefit."""
    # Clear the cache first
    with _function_hash_cache_lock:
        _function_hash_cache.clear()
    
    def test_func(x):
        return x ** 2
    
    # Measure first call (should compute hash) - use fewer iterations for cold cache
    start = time.perf_counter()
    for _ in range(10):
        # Force cache clear each time to measure uncached performance
        with _function_hash_cache_lock:
            _function_hash_cache.clear()
        key1 = compute_cache_key(test_func, 100, 0.001)
    uncached_10_time = time.perf_counter() - start
    
    # Do one call to cache it
    compute_cache_key(test_func, 100, 0.001)
    
    # Measure cached calls (should use cache)
    start = time.perf_counter()
    for _ in range(10):
        key2 = compute_cache_key(test_func, 100, 0.001)
    cached_10_time = time.perf_counter() - start
    
    # Cached calls should be faster
    # Cache eliminates SHA256 computation which is the most expensive part
    speedup = uncached_10_time / max(cached_10_time, 0.000001)
    
    # Print timing info for debugging
    print(f"\nUncached 10 calls: {uncached_10_time*1000:.3f}ms ({uncached_10_time*100:.1f}μs per call)")
    print(f"Cached 10 calls: {cached_10_time*1000:.3f}ms ({cached_10_time*100:.1f}μs per call)")
    print(f"Speedup: {speedup:.1f}x")
    
    # Verify meaningful speedup (at least 1.5x to account for measurement noise)
    # The speedup may be modest because bucketing logic still runs
    assert speedup >= 1.5, f"Expected at least 1.5x speedup, got {speedup:.1f}x"
    
    # Verify that cached time is reasonably fast (< 20μs per call)
    # This is generous to account for system variability and load
    avg_cached_time_us = (cached_10_time / 10) * 1_000_000
    assert avg_cached_time_us < 20.0, f"Cached calls should be fast, got {avg_cached_time_us:.1f}μs"


def test_function_hash_cache_thread_safety():
    """Test that function hash cache is thread-safe."""
    import threading
    
    # Clear the cache first
    with _function_hash_cache_lock:
        _function_hash_cache.clear()
    
    def test_func(x):
        return x * 2
    
    # Track which threads succeeded
    results = []
    errors = []
    
    def compute_key():
        try:
            key = compute_cache_key(test_func, 100, 0.001)
            results.append(key)
        except Exception as e:
            errors.append(e)
    
    # Create multiple threads computing the same key
    threads = [threading.Thread(target=compute_key) for _ in range(10)]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # No errors should occur
    assert len(errors) == 0, f"Thread safety errors: {errors}"
    
    # All results should be identical
    assert len(results) == 10
    assert len(set(results)) == 1, "All threads should get the same key"
    
    # Function should be cached exactly once
    assert id(test_func) in _function_hash_cache


def test_function_hash_builtin_function():
    """Test that built-in functions are handled correctly."""
    # Clear the cache first
    with _function_hash_cache_lock:
        _function_hash_cache.clear()
    
    # Use a built-in function (no __code__ attribute)
    key = compute_cache_key(len, 100, 0.001)
    
    # Should return a valid key
    assert isinstance(key, str)
    assert len(key) > 0
    
    # Should be cached
    assert id(len) in _function_hash_cache


def test_function_hash_cache_consistency():
    """Test that cache produces consistent results across multiple calls."""
    # Clear the cache first
    with _function_hash_cache_lock:
        _function_hash_cache.clear()
    
    def test_func(x):
        return x * 2
    
    # Compute key multiple times
    keys = [compute_cache_key(test_func, 100, 0.001) for _ in range(10)]
    
    # All keys should be identical
    assert len(set(keys)) == 1, "Cache should produce consistent results"


def test_function_hash_different_workloads_same_function():
    """Test that same function with different workloads produces different keys."""
    # Clear the cache first
    with _function_hash_cache_lock:
        _function_hash_cache.clear()
    
    def test_func(x):
        return x * 2
    
    # Different data sizes
    key_small = compute_cache_key(test_func, 10, 0.001)
    key_large = compute_cache_key(test_func, 10000, 0.001)
    
    # Keys should differ due to size bucketing
    assert key_small != key_large
    
    # But function hash should be cached only once
    assert id(test_func) in _function_hash_cache


class TestFunctionHashCacheOptimization:
    """Test class for function hash cache optimization features."""
    
    def test_cache_reduces_redundant_hashing(self):
        """Test that cache reduces redundant hash computations."""
        # Clear the cache first
        with _function_hash_cache_lock:
            _function_hash_cache.clear()
        
        def func1(x):
            return x * 2
        
        def func2(x):
            return x * 3
        
        # Compute keys for multiple functions multiple times
        # This simulates repeated optimization calls in a real application
        for _ in range(5):
            compute_cache_key(func1, 100, 0.001)
            compute_cache_key(func2, 100, 0.001)
        
        # Only 2 functions should be cached (not 10 entries)
        assert len(_function_hash_cache) == 2
        assert id(func1) in _function_hash_cache
        assert id(func2) in _function_hash_cache
    
    def test_cache_handles_lambda_functions(self):
        """Test that lambda functions are cached correctly."""
        # Clear the cache first
        with _function_hash_cache_lock:
            _function_hash_cache.clear()
        
        # Create lambda function
        lambda_func = lambda x: x * 2
        
        # Compute key
        key = compute_cache_key(lambda_func, 100, 0.001)
        
        # Should be cached
        assert id(lambda_func) in _function_hash_cache
        assert isinstance(key, str)
