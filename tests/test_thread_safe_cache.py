"""
Tests for thread-safe global cache in system_info module.

This module tests that the global caches for spawn cost and chunking overhead
are thread-safe and handle concurrent access correctly.
"""

import pytest
import threading
import time

from amorsize.system_info import (
    measure_spawn_cost,
    measure_chunking_overhead,
    _clear_spawn_cost_cache,
    _clear_chunking_overhead_cache,
    get_spawn_cost,
    get_chunking_overhead,
)


class TestThreadSafeSpawnCostCache:
    """Test thread-safe caching of spawn cost measurements."""
    
    def test_concurrent_spawn_cost_calls_single_measurement(self):
        """Test that concurrent calls result in consistent cached values."""
        # Clear cache before test
        _clear_spawn_cost_cache()
        
        # Create 10 threads that will all try to measure simultaneously
        threads = []
        results = []
        
        def call_measure():
            result = measure_spawn_cost()
            results.append(result)
        
        # Start threads
        for _ in range(10):
            t = threading.Thread(target=call_measure)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # All threads should get the same result (no race condition)
        assert len(set(results)) == 1, "All threads should get same cached value"
        assert results[0] > 0, "Cached value should be valid"
    
    def test_spawn_cost_cache_clear_is_thread_safe(self):
        """Test that cache clearing is thread-safe."""
        # Pre-populate cache
        _clear_spawn_cost_cache()
        cost1 = measure_spawn_cost()
        
        # Clear from multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=_clear_spawn_cost_cache)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Should be able to measure again after clearing
        cost2 = measure_spawn_cost()
        assert cost2 > 0, "Should get valid measurement after cache clear"
    
    def test_spawn_cost_double_check_locking(self):
        """Test that double-check locking pattern works correctly."""
        _clear_spawn_cost_cache()
        
        # First call populates cache
        cost1 = measure_spawn_cost()
        
        # Second call should use cache (fast)
        start = time.perf_counter()
        cost2 = measure_spawn_cost()
        elapsed = time.perf_counter() - start
        
        # Should be instant (< 1ms) since it's cached
        assert elapsed < 0.001, "Cached value should be returned instantly"
        assert cost1 == cost2, "Should get same cached value"
    
    def test_spawn_cost_no_race_on_write(self):
        """Test that no race condition exists when writing to cache."""
        _clear_spawn_cost_cache()
        
        results = []
        
        def measure_and_store():
            cost = measure_spawn_cost()
            results.append(cost)
        
        # Create multiple threads
        threads = []
        for _ in range(20):
            t = threading.Thread(target=measure_and_store)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All results should be identical (no partial writes)
        assert len(set(results)) == 1, "All threads should see same cached value"
        assert results[0] > 0, "Cached value should be valid"


class TestThreadSafeChunkingOverheadCache:
    """Test thread-safe caching of chunking overhead measurements."""
    
    def test_concurrent_chunking_overhead_calls_single_measurement(self):
        """Test that concurrent calls result in consistent cached values."""
        # Clear cache before test
        _clear_chunking_overhead_cache()
        
        results = []
        
        def call_measure():
            result = measure_chunking_overhead()
            results.append(result)
        
        # Create 10 threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=call_measure)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All threads should get the same result
        assert len(set(results)) == 1, "All threads should get same cached value"
        assert results[0] > 0, "Cached value should be valid"
    
    def test_chunking_overhead_cache_clear_is_thread_safe(self):
        """Test that cache clearing is thread-safe."""
        # Pre-populate cache
        _clear_chunking_overhead_cache()
        overhead1 = measure_chunking_overhead()
        
        # Clear from multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=_clear_chunking_overhead_cache)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Should be able to measure again after clearing
        overhead2 = measure_chunking_overhead()
        assert overhead2 > 0, "Should get valid measurement after cache clear"
    
    def test_chunking_overhead_double_check_locking(self):
        """Test that double-check locking pattern works correctly."""
        _clear_chunking_overhead_cache()
        
        # First call populates cache
        overhead1 = measure_chunking_overhead()
        
        # Second call should use cache (fast)
        start = time.perf_counter()
        overhead2 = measure_chunking_overhead()
        elapsed = time.perf_counter() - start
        
        # Should be instant (< 1ms) since it's cached
        assert elapsed < 0.001, "Cached value should be returned instantly"
        assert overhead1 == overhead2, "Should get same cached value"
    
    def test_chunking_overhead_no_race_on_write(self):
        """Test that no race condition exists when writing to cache."""
        _clear_chunking_overhead_cache()
        
        results = []
        
        def measure_and_store():
            overhead = measure_chunking_overhead()
            results.append(overhead)
        
        # Create multiple threads
        threads = []
        for _ in range(20):
            t = threading.Thread(target=measure_and_store)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All results should be identical (no partial writes)
        assert len(set(results)) == 1, "All threads should see same cached value"
        assert results[0] > 0, "Cached value should be valid"


class TestThreadSafetyCombined:
    """Test thread-safety of both caches together."""
    
    def test_concurrent_mixed_operations(self):
        """Test concurrent operations on both caches simultaneously."""
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        spawn_results = []
        chunking_results = []
        
        def measure_spawn():
            cost = measure_spawn_cost()
            spawn_results.append(cost)
        
        def measure_chunking():
            overhead = measure_chunking_overhead()
            chunking_results.append(overhead)
        
        # Create mixed threads
        threads = []
        for _ in range(10):
            t1 = threading.Thread(target=measure_spawn)
            t2 = threading.Thread(target=measure_chunking)
            threads.extend([t1, t2])
            t1.start()
            t2.start()
        
        for t in threads:
            t.join()
        
        # Each cache should have consistent values
        assert len(set(spawn_results)) == 1, "Spawn cost should be consistent"
        assert len(set(chunking_results)) == 1, "Chunking overhead should be consistent"
        assert spawn_results[0] > 0, "Spawn cost should be valid"
        assert chunking_results[0] > 0, "Chunking overhead should be valid"
    
    def test_independent_cache_locks(self):
        """Test that the two caches use independent locks."""
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        # Measure both in parallel - should not deadlock
        spawn_result = [None]
        chunking_result = [None]
        
        def measure_spawn():
            spawn_result[0] = measure_spawn_cost()
        
        def measure_chunking():
            chunking_result[0] = measure_chunking_overhead()
        
        t1 = threading.Thread(target=measure_spawn)
        t2 = threading.Thread(target=measure_chunking)
        
        t1.start()
        t2.start()
        
        # Join with timeout to detect deadlock
        t1.join(timeout=5.0)
        t2.join(timeout=5.0)
        
        assert not t1.is_alive(), "Spawn measurement should complete"
        assert not t2.is_alive(), "Chunking measurement should complete"
        assert spawn_result[0] is not None, "Should have spawn result"
        assert chunking_result[0] is not None, "Should have chunking result"


class TestBackwardCompatibility:
    """Test that thread-safe changes don't break existing behavior."""
    
    def test_get_spawn_cost_still_works(self):
        """Test that get_spawn_cost works as before."""
        _clear_spawn_cost_cache()
        cost = get_spawn_cost()
        assert cost > 0, "Should return valid spawn cost"
        assert isinstance(cost, float), "Should return float"
    
    def test_get_chunking_overhead_still_works(self):
        """Test that get_chunking_overhead works as before."""
        _clear_chunking_overhead_cache()
        overhead = get_chunking_overhead()
        assert overhead > 0, "Should return valid chunking overhead"
        assert isinstance(overhead, float), "Should return float"
    
    def test_caching_still_works(self):
        """Test that caching still provides performance benefit."""
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        # First calls (slow)
        start1 = time.perf_counter()
        cost1 = measure_spawn_cost()
        time1 = time.perf_counter() - start1
        
        # Second calls (fast - cached)
        start2 = time.perf_counter()
        cost2 = measure_spawn_cost()
        time2 = time.perf_counter() - start2
        
        # Cached call should be much faster
        assert time2 < time1 * 0.1, "Cached call should be at least 10x faster"
        assert cost1 == cost2, "Should get same value from cache"
    
    def test_cache_clear_still_works(self):
        """Test that cache clearing still works."""
        # Populate caches
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        cost1 = measure_spawn_cost()
        overhead1 = measure_chunking_overhead()
        
        # Clear and remeasure
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        cost2 = measure_spawn_cost()
        overhead2 = measure_chunking_overhead()
        
        # Should get valid values (may be slightly different due to measurement variance)
        assert cost2 > 0, "Should get valid spawn cost after clear"
        assert overhead2 > 0, "Should get valid overhead after clear"
