"""
Property-based tests for the distributed_cache module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the distributed caching system across a wide range of inputs.

Note: These tests focus on the API contract and invariants, not on actual
Redis integration (which is tested separately in test_distributed_cache.py).
"""

import time
import threading
from typing import Any, Dict, List, Optional
from unittest import mock

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

# Try to import redis for testing
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from amorsize.distributed_cache import (
    DistributedCacheConfig,
    _make_redis_key,
    _clear_redis_enabled_cache,
    REDIS_ENABLED_CACHE_TTL,
)


class TestDistributedCacheConfigInvariants:
    """Test invariant properties that should always hold for DistributedCacheConfig."""

    @given(
        redis_url=st.text(min_size=1, max_size=200),
        key_prefix=st.text(min_size=0, max_size=50),
        ttl_seconds=st.integers(min_value=1, max_value=2592000)  # 1 second to 30 days
    )
    @settings(max_examples=100, deadline=1000)
    def test_config_initialization_stores_values(self, redis_url, key_prefix, ttl_seconds):
        """Test that DistributedCacheConfig properly stores initialization values."""
        config = DistributedCacheConfig(
            redis_url=redis_url,
            key_prefix=key_prefix,
            ttl_seconds=ttl_seconds
        )
        
        assert config.redis_url == redis_url, "Redis URL should be stored"
        assert config.key_prefix == key_prefix, "Key prefix should be stored"
        assert config.ttl_seconds == ttl_seconds, "TTL should be stored"

    @given(
        socket_timeout=st.floats(min_value=0.1, max_value=60.0),
        socket_connect_timeout=st.floats(min_value=0.1, max_value=60.0),
        max_connections=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=50, deadline=1000)
    def test_config_timeout_values_positive(self, socket_timeout, socket_connect_timeout, max_connections):
        """Test that timeout values and connection limits are positive."""
        config = DistributedCacheConfig(
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            max_connections=max_connections
        )
        
        assert config.socket_timeout > 0, "Socket timeout should be positive"
        assert config.socket_connect_timeout > 0, "Connect timeout should be positive"
        assert config.max_connections > 0, "Max connections should be positive"

    @given(retry_on_timeout=st.booleans())
    @settings(max_examples=20, deadline=500)
    def test_config_retry_flag_is_boolean(self, retry_on_timeout):
        """Test that retry_on_timeout is properly stored as boolean."""
        config = DistributedCacheConfig(retry_on_timeout=retry_on_timeout)
        
        assert isinstance(config.retry_on_timeout, bool), "Retry flag should be boolean"
        assert config.retry_on_timeout == retry_on_timeout, "Retry flag should match input"

    @given(ttl_seconds=st.integers(min_value=1, max_value=2592000))
    @settings(max_examples=50, deadline=500)
    def test_config_ttl_in_reasonable_range(self, ttl_seconds):
        """Test that TTL values are in reasonable range (1 second to 30 days)."""
        config = DistributedCacheConfig(ttl_seconds=ttl_seconds)
        
        assert 1 <= config.ttl_seconds <= 2592000, "TTL should be in reasonable range"


class TestRedisKeyGeneration:
    """Test invariant properties of Redis key generation."""

    @given(cache_key=st.text(min_size=1, max_size=200))
    @settings(max_examples=100, deadline=1000)
    def test_make_redis_key_deterministic(self, cache_key):
        """Test that _make_redis_key is deterministic for the same input."""
        with mock.patch('amorsize.distributed_cache._redis_client', None):
            key1 = _make_redis_key(cache_key)
            key2 = _make_redis_key(cache_key)
            
            assert key1 == key2, "Same input should produce same Redis key"

    @given(cache_key=st.text(min_size=1, max_size=200))
    @settings(max_examples=100, deadline=1000)
    def test_make_redis_key_includes_prefix(self, cache_key):
        """Test that _make_redis_key includes the prefix."""
        with mock.patch('amorsize.distributed_cache._redis_client', None):
            redis_key = _make_redis_key(cache_key)
            
            # Default prefix is "amorsize:"
            assert "amorsize:" in redis_key, "Redis key should include prefix"

    @given(cache_key=st.text(min_size=1, max_size=200))
    @settings(max_examples=100, deadline=1000)
    def test_make_redis_key_contains_original_key(self, cache_key):
        """Test that _make_redis_key contains the original cache key."""
        with mock.patch('amorsize.distributed_cache._redis_client', None):
            redis_key = _make_redis_key(cache_key)
            
            assert cache_key in redis_key, "Redis key should contain original cache key"

    @given(
        cache_key1=st.text(min_size=1, max_size=100),
        cache_key2=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=100, deadline=1000)
    def test_make_redis_key_unique_for_different_inputs(self, cache_key1, cache_key2):
        """Test that different cache keys produce different Redis keys."""
        assume(cache_key1 != cache_key2)  # Only test when keys are different
        
        with mock.patch('amorsize.distributed_cache._redis_client', None):
            redis_key1 = _make_redis_key(cache_key1)
            redis_key2 = _make_redis_key(cache_key2)
            
            assert redis_key1 != redis_key2, "Different cache keys should produce different Redis keys"

    @given(cache_key=st.text(min_size=1, max_size=200))
    @settings(max_examples=50, deadline=1000)
    def test_make_redis_key_returns_string(self, cache_key):
        """Test that _make_redis_key always returns a string."""
        with mock.patch('amorsize.distributed_cache._redis_client', None):
            redis_key = _make_redis_key(cache_key)
            
            assert isinstance(redis_key, str), "Redis key should be a string"


class TestRedisCacheEnablingInvariants:
    """Test invariant properties of Redis cache enabled status checking."""

    def setup_method(self):
        """Clear cache before each test."""
        _clear_redis_enabled_cache()

    def teardown_method(self):
        """Clear cache after each test."""
        _clear_redis_enabled_cache()

    @settings(max_examples=20, deadline=1000)
    @given(iterations=st.integers(min_value=2, max_value=10))
    def test_clear_redis_enabled_cache_clears_state(self, iterations):
        """Test that _clear_redis_enabled_cache properly clears cached state."""
        from amorsize import distributed_cache
        
        # Set some cached values
        distributed_cache._cached_redis_enabled = True
        distributed_cache._redis_enabled_cache_timestamp = time.time()
        
        # Clear cache
        _clear_redis_enabled_cache()
        
        # Verify state is cleared
        assert distributed_cache._cached_redis_enabled is None
        assert distributed_cache._redis_enabled_cache_timestamp is None

    @settings(max_examples=20, deadline=2000)
    @given(num_threads=st.integers(min_value=2, max_value=10))
    def test_clear_redis_enabled_cache_thread_safe(self, num_threads):
        """Test that _clear_redis_enabled_cache is thread-safe."""
        from amorsize import distributed_cache
        
        # Set some cached values
        distributed_cache._cached_redis_enabled = True
        distributed_cache._redis_enabled_cache_timestamp = time.time()
        
        # Clear from multiple threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=_clear_redis_enabled_cache)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should complete without errors and state should be cleared
        assert distributed_cache._cached_redis_enabled is None
        assert distributed_cache._redis_enabled_cache_timestamp is None

    def test_redis_enabled_cache_ttl_constant_is_positive(self):
        """Test that REDIS_ENABLED_CACHE_TTL is a positive float."""
        assert isinstance(REDIS_ENABLED_CACHE_TTL, (int, float)), "TTL should be numeric"
        assert REDIS_ENABLED_CACHE_TTL > 0, "TTL should be positive"
        assert REDIS_ENABLED_CACHE_TTL <= 60, "TTL should be reasonable (<=60s)"


class TestDistributedCacheAPIContract:
    """Test the API contract for distributed cache functions."""

    def setup_method(self):
        """Setup before each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()
        _clear_redis_enabled_cache()

    def teardown_method(self):
        """Cleanup after each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()
        _clear_redis_enabled_cache()

    @given(
        cache_key=st.text(min_size=1, max_size=200),
        n_jobs=st.integers(min_value=1, max_value=128),
        chunksize=st.integers(min_value=1, max_value=10000)
    )
    @settings(max_examples=50, deadline=1000)
    def test_save_to_distributed_cache_accepts_valid_inputs(self, cache_key, n_jobs, chunksize):
        """Test that save_to_distributed_cache accepts valid inputs without crashing."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        # Should not crash, even if Redis is not configured (returns False)
        result = save_to_distributed_cache(
            cache_key=cache_key,
            n_jobs=n_jobs,
            chunksize=chunksize,
            executor_type="process",
            estimated_speedup=2.0,
            reason="test",
            warnings=[]
        )
        
        # When not configured, should return False
        assert isinstance(result, bool), "Should return boolean"
        assert result is False, "Should return False when Redis not configured"

    @given(
        n_jobs=st.integers(min_value=1, max_value=128),
        chunksize=st.integers(min_value=1, max_value=10000),
        estimated_speedup=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=1000)
    def test_save_to_distributed_cache_handles_various_numeric_values(self, n_jobs, chunksize, estimated_speedup):
        """Test that save_to_distributed_cache handles various numeric values correctly."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=n_jobs,
            chunksize=chunksize,
            executor_type="process",
            estimated_speedup=estimated_speedup,
            reason="test",
            warnings=[]
        )
        
        assert isinstance(result, bool), "Should return boolean"

    @given(cache_key=st.text(min_size=1, max_size=200))
    @settings(max_examples=50, deadline=1000)
    def test_load_from_distributed_cache_returns_tuple(self, cache_key):
        """Test that load_from_distributed_cache always returns a tuple."""
        from amorsize.distributed_cache import load_from_distributed_cache
        
        result = load_from_distributed_cache(cache_key)
        
        assert isinstance(result, tuple), "Should return tuple"
        assert len(result) == 2, "Should return tuple of length 2"
        
        entry, miss_reason = result
        # When not configured, entry should be None
        assert entry is None, "Entry should be None when not configured"
        assert isinstance(miss_reason, str), "Miss reason should be string"

    @given(warnings=st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=10))
    @settings(max_examples=50, deadline=1000)
    def test_save_to_distributed_cache_accepts_warnings_list(self, warnings):
        """Test that save_to_distributed_cache accepts various warnings lists."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=2.0,
            reason="test",
            warnings=warnings
        )
        
        assert isinstance(result, bool), "Should return boolean"

    @given(executor_type=st.sampled_from(["process", "thread"]))
    @settings(max_examples=10, deadline=500)
    def test_save_to_distributed_cache_accepts_valid_executor_types(self, executor_type):
        """Test that save_to_distributed_cache accepts valid executor types."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=4,
            chunksize=100,
            executor_type=executor_type,
            estimated_speedup=2.0,
            reason="test",
            warnings=[]
        )
        
        assert isinstance(result, bool), "Should return boolean"

    @given(reason=st.text(min_size=0, max_size=200))
    @settings(max_examples=50, deadline=1000)
    def test_save_to_distributed_cache_accepts_various_reasons(self, reason):
        """Test that save_to_distributed_cache accepts various reason strings."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=2.0,
            reason=reason,
            warnings=[]
        )
        
        assert isinstance(result, bool), "Should return boolean"


class TestDistributedCacheNumericalStability:
    """Test numerical stability of distributed cache operations."""

    def setup_method(self):
        """Setup before each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()

    def teardown_method(self):
        """Cleanup after each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()

    @given(
        estimated_speedup=st.floats(
            min_value=0.01,
            max_value=1000.0,
            allow_nan=False,
            allow_infinity=False
        )
    )
    @settings(max_examples=50, deadline=1000)
    def test_save_handles_various_speedup_values(self, estimated_speedup):
        """Test that save handles various speedup values without overflow/underflow."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=estimated_speedup,
            reason="test",
            warnings=[]
        )
        
        assert isinstance(result, bool), "Should handle speedup value and return boolean"

    @given(
        n_jobs=st.integers(min_value=1, max_value=1024),  # Very large worker counts
        chunksize=st.integers(min_value=1, max_value=1000000)  # Very large chunksizes
    )
    @settings(max_examples=50, deadline=1000)
    def test_save_handles_extreme_values(self, n_jobs, chunksize):
        """Test that save handles extreme parameter values."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=n_jobs,
            chunksize=chunksize,
            executor_type="process",
            estimated_speedup=2.0,
            reason="test",
            warnings=[]
        )
        
        assert isinstance(result, bool), "Should handle extreme values and return boolean"


class TestDistributedCacheEdgeCases:
    """Test edge cases in distributed cache operations."""

    def setup_method(self):
        """Setup before each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()
        _clear_redis_enabled_cache()

    def teardown_method(self):
        """Cleanup after each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()
        _clear_redis_enabled_cache()

    @given(cache_key=st.text(min_size=0, max_size=0))
    @settings(max_examples=10, deadline=500)
    def test_load_with_empty_cache_key(self, cache_key):
        """Test that load handles empty cache key gracefully."""
        from amorsize.distributed_cache import load_from_distributed_cache
        
        # Should handle empty string without crashing
        result = load_from_distributed_cache(cache_key)
        
        assert isinstance(result, tuple), "Should return tuple"
        assert len(result) == 2, "Should return tuple of length 2"

    @given(warnings=st.lists(st.text(), min_size=0, max_size=0))
    @settings(max_examples=10, deadline=500)
    def test_save_with_empty_warnings(self, warnings):
        """Test that save handles empty warnings list."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=2.0,
            reason="test",
            warnings=warnings
        )
        
        assert isinstance(result, bool), "Should handle empty warnings"

    def test_is_distributed_cache_enabled_when_not_configured(self):
        """Test that is_distributed_cache_enabled returns False when not configured."""
        from amorsize.distributed_cache import is_distributed_cache_enabled
        
        result = is_distributed_cache_enabled()
        
        assert isinstance(result, bool), "Should return boolean"
        assert result is False, "Should be False when not configured"

    def test_disable_distributed_cache_when_not_configured(self):
        """Test that disable works even when not configured."""
        from amorsize.distributed_cache import disable_distributed_cache
        
        # Should not crash
        disable_distributed_cache()
        # No assertion needed - just verifying it doesn't crash

    @given(
        n_jobs=st.just(1),  # Minimum value
        chunksize=st.just(1)  # Minimum value
    )
    @settings(max_examples=10, deadline=500)
    def test_save_with_minimum_values(self, n_jobs, chunksize):
        """Test that save handles minimum parameter values."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        result = save_to_distributed_cache(
            cache_key="test_key",
            n_jobs=n_jobs,
            chunksize=chunksize,
            executor_type="process",
            estimated_speedup=1.0,
            reason="",
            warnings=[]
        )
        
        assert isinstance(result, bool), "Should handle minimum values"


class TestDistributedCacheIntegration:
    """Test integration properties of distributed cache system."""

    def setup_method(self):
        """Setup before each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()
        _clear_redis_enabled_cache()

    def teardown_method(self):
        """Cleanup after each test."""
        from amorsize.distributed_cache import disable_distributed_cache
        disable_distributed_cache()
        _clear_redis_enabled_cache()

    @given(num_operations=st.integers(min_value=1, max_value=20))
    @settings(max_examples=20, deadline=2000)
    def test_multiple_save_operations_consistent(self, num_operations):
        """Test that multiple save operations behave consistently."""
        from amorsize.distributed_cache import save_to_distributed_cache
        
        results = []
        for i in range(num_operations):
            result = save_to_distributed_cache(
                cache_key=f"test_key_{i}",
                n_jobs=4,
                chunksize=100,
                executor_type="process",
                estimated_speedup=2.0,
                reason="test",
                warnings=[]
            )
            results.append(result)
        
        # All operations should return same type
        assert all(isinstance(r, bool) for r in results), "All saves should return boolean"
        # When not configured, all should return False
        assert all(r is False for r in results), "All saves should return False when not configured"

    @given(num_operations=st.integers(min_value=1, max_value=20))
    @settings(max_examples=20, deadline=2000)
    def test_multiple_load_operations_consistent(self, num_operations):
        """Test that multiple load operations behave consistently."""
        from amorsize.distributed_cache import load_from_distributed_cache
        
        results = []
        for i in range(num_operations):
            result = load_from_distributed_cache(f"test_key_{i}")
            results.append(result)
        
        # All operations should return tuples
        assert all(isinstance(r, tuple) for r in results), "All loads should return tuple"
        assert all(len(r) == 2 for r in results), "All loads should return tuple of length 2"
        # When not configured, all entries should be None
        assert all(r[0] is None for r in results), "All entries should be None when not configured"
        assert all(isinstance(r[1], str) for r in results), "All miss reasons should be strings"

    @settings(max_examples=10, deadline=1000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(num_threads=st.integers(min_value=2, max_value=10))
    def test_concurrent_operations_thread_safe(self, num_threads):
        """Test that concurrent save/load operations are thread-safe."""
        from amorsize.distributed_cache import save_to_distributed_cache, load_from_distributed_cache
        
        results = []
        lock = threading.Lock()
        
        def worker(thread_id):
            # Save operation
            save_result = save_to_distributed_cache(
                cache_key=f"test_key_{thread_id}",
                n_jobs=4,
                chunksize=100,
                executor_type="process",
                estimated_speedup=2.0,
                reason="test",
                warnings=[]
            )
            
            # Load operation
            load_result = load_from_distributed_cache(f"test_key_{thread_id}")
            
            with lock:
                results.append((save_result, load_result))
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should complete without errors
        assert len(results) == num_threads, "All threads should complete"
        # All saves should return booleans
        assert all(isinstance(r[0], bool) for r in results), "All saves should return boolean"
        # All loads should return tuples
        assert all(isinstance(r[1], tuple) for r in results), "All loads should return tuple"
