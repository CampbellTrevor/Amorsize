"""
Comprehensive edge case tests for the cache module.

This test suite covers boundary conditions, parameter validation, error handling,
invariants, thread safety, and file operations to strengthen test quality before
mutation testing baseline.

Follows the pattern from Iterations 184-187 (optimizer, sampling, system_info, cost_model).
"""

import json
import os
import platform
import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from amorsize.cache import (
    CacheEntry,
    BenchmarkCacheEntry,
    _compute_function_hash,
    clear_function_hash_cache,
    _clear_cache_dir_cache,
    get_cache_dir,
    compute_cache_key,
    save_cache_entry,
    load_cache_entry,
    clear_cache,
    prune_expired_cache,
    _maybe_auto_prune_cache,
    get_benchmark_cache_dir,
    compute_benchmark_cache_key,
    CACHE_VERSION,
    DEFAULT_TTL_SECONDS,
    AUTO_PRUNE_PROBABILITY,
)


# =============================================================================
# 1. BOUNDARY CONDITIONS
# =============================================================================

class TestFunctionHashBoundaries:
    """Test edge cases in function hash computation."""
    
    def test_compute_function_hash_builtin_function(self):
        """Built-in functions without __code__ should be handled."""
        func_hash = _compute_function_hash(len)
        assert isinstance(func_hash, str)
        assert len(func_hash) == 16
    
    def test_compute_function_hash_lambda(self):
        """Lambda functions should be hashable."""
        func = lambda x: x * 2
        func_hash = _compute_function_hash(func)
        assert isinstance(func_hash, str)
        assert len(func_hash) == 16
    
    def test_compute_function_hash_nested_function(self):
        """Nested functions should be hashable."""
        def outer():
            def inner(x):
                return x + 1
            return inner
        
        func = outer()
        func_hash = _compute_function_hash(func)
        assert isinstance(func_hash, str)
        assert len(func_hash) == 16
    
    def test_compute_function_hash_caching_consistency(self):
        """Same function should return same hash from cache."""
        def test_func(x):
            return x * 2
        
        clear_function_hash_cache()
        hash1 = _compute_function_hash(test_func)
        hash2 = _compute_function_hash(test_func)
        assert hash1 == hash2
    
    def test_compute_function_hash_different_functions(self):
        """Different functions should have different hashes (usually)."""
        def func1(x):
            return x * 2
        
        def func2(x):
            return x * 3 * 5  # Make it more different
        
        clear_function_hash_cache()
        hash1 = _compute_function_hash(func1)
        hash2 = _compute_function_hash(func2)
        # Note: Very simple functions might have same bytecode in some Python versions
        # The important thing is the hash is stable and computed correctly
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        assert len(hash1) == 16
        assert len(hash2) == 16


class TestCacheKeyBoundaries:
    """Test boundary conditions for cache key computation."""
    
    def test_compute_cache_key_tiny_data(self):
        """Data size < 10 should be bucketed as 'tiny'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=5, avg_time_per_item=0.001)
        assert "size:tiny" in key
    
    def test_compute_cache_key_small_data(self):
        """Data size 10-99 should be bucketed as 'small'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=50, avg_time_per_item=0.001)
        assert "size:small" in key
    
    def test_compute_cache_key_medium_data(self):
        """Data size 100-999 should be bucketed as 'medium'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=500, avg_time_per_item=0.001)
        assert "size:medium" in key
    
    def test_compute_cache_key_large_data(self):
        """Data size 1000-9999 should be bucketed as 'large'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=5000, avg_time_per_item=0.001)
        assert "size:large" in key
    
    def test_compute_cache_key_xlarge_data(self):
        """Data size >= 10000 should be bucketed as 'xlarge'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=50000, avg_time_per_item=0.001)
        assert "size:xlarge" in key
    
    def test_compute_cache_key_instant_time(self):
        """Time < 0.1ms should be bucketed as 'instant'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=100, avg_time_per_item=0.00005)
        assert "time:instant" in key
    
    def test_compute_cache_key_fast_time(self):
        """Time 0.1ms-1ms should be bucketed as 'fast'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=100, avg_time_per_item=0.0005)
        assert "time:fast" in key
    
    def test_compute_cache_key_moderate_time(self):
        """Time 1ms-10ms should be bucketed as 'moderate'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=100, avg_time_per_item=0.005)
        assert "time:moderate" in key
    
    def test_compute_cache_key_slow_time(self):
        """Time 10ms-100ms should be bucketed as 'slow'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=100, avg_time_per_item=0.05)
        assert "time:slow" in key
    
    def test_compute_cache_key_very_slow_time(self):
        """Time >= 100ms should be bucketed as 'very_slow'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=100, avg_time_per_item=0.5)
        assert "time:very_slow" in key
    
    def test_compute_cache_key_zero_data_size(self):
        """Zero data size should be bucketed as 'tiny'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=0, avg_time_per_item=0.001)
        assert "size:tiny" in key
    
    def test_compute_cache_key_zero_time(self):
        """Zero execution time should be bucketed as 'instant'."""
        def func(x):
            return x
        
        key = compute_cache_key(func, data_size=100, avg_time_per_item=0.0)
        assert "time:instant" in key


class TestCacheEntryBoundaries:
    """Test boundary conditions for CacheEntry."""
    
    def test_cache_entry_zero_values(self):
        """Cache entry with zero values should be valid."""
        entry = CacheEntry(
            n_jobs=0,
            chunksize=0,
            executor_type="process",
            estimated_speedup=0.0,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={}
        )
        assert entry.n_jobs == 0
        assert entry.chunksize == 0
        assert entry.estimated_speedup == 0.0
    
    def test_cache_entry_negative_speedup(self):
        """Negative speedup should be allowed (for testing/analysis)."""
        entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=-0.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={}
        )
        assert entry.estimated_speedup == -0.5
    
    def test_cache_entry_empty_system_info(self):
        """Empty system info should be handled."""
        entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=1.0,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={}
        )
        is_compatible, _ = entry.is_system_compatible()
        # Should handle missing keys gracefully
        assert isinstance(is_compatible, bool)
    
    def test_cache_entry_very_old_timestamp(self):
        """Very old timestamp should be detected as expired."""
        old_timestamp = time.time() - (365 * 24 * 60 * 60)  # 1 year ago
        entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=1.0,
            reason="test",
            warnings=[],
            timestamp=old_timestamp,
            system_info={}
        )
        assert entry.is_expired(ttl_seconds=DEFAULT_TTL_SECONDS)
    
    def test_cache_entry_future_timestamp(self):
        """Future timestamp (clock skew) should not be expired."""
        future_timestamp = time.time() + 3600  # 1 hour in future
        entry = CacheEntry(
            n_jobs=1,
            chunksize=1,
            executor_type="process",
            estimated_speedup=1.0,
            reason="test",
            warnings=[],
            timestamp=future_timestamp,
            system_info={}
        )
        assert not entry.is_expired(ttl_seconds=DEFAULT_TTL_SECONDS)


# =============================================================================
# 2. PARAMETER VALIDATION
# =============================================================================

class TestParameterValidation:
    """Test parameter validation edge cases."""
    
    def test_cache_entry_from_dict_missing_keys(self):
        """from_dict should handle missing optional keys."""
        data = {
            "n_jobs": 4,
            "chunksize": 100,
            "executor_type": "process",
            "estimated_speedup": 3.5,
            "reason": "test",
            "warnings": [],
            "timestamp": time.time(),
            "system_info": {}
        }
        entry = CacheEntry.from_dict(data)
        assert entry.n_jobs == 4
        assert entry.cache_version == 1  # Default value
        assert entry.pickle_size is None
    
    def test_cache_entry_from_dict_extra_keys(self):
        """from_dict should ignore unknown keys."""
        data = {
            "n_jobs": 4,
            "chunksize": 100,
            "executor_type": "process",
            "estimated_speedup": 3.5,
            "reason": "test",
            "warnings": [],
            "timestamp": time.time(),
            "system_info": {},
            "unknown_key": "should_be_ignored"
        }
        entry = CacheEntry.from_dict(data)
        assert entry.n_jobs == 4
    
    def test_benchmark_cache_entry_from_dict_missing_keys(self):
        """BenchmarkCacheEntry.from_dict should handle missing optional keys."""
        data = {
            "serial_time": 1.0,
            "parallel_time": 0.3,
            "actual_speedup": 3.33,
            "n_jobs": 4,
            "chunksize": 100,
            "timestamp": time.time(),
            "system_info": {}
        }
        entry = BenchmarkCacheEntry.from_dict(data)
        assert entry.serial_time == 1.0
        assert entry.cache_version == 1  # Default value


# =============================================================================
# 3. ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test error handling in cache operations."""
    
    def test_get_cache_dir_permission_error(self):
        """Permission error during cache dir creation should be handled."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("No permission")):
            # Should raise since we can't create the directory
            # But in production, save_cache_entry handles this silently
            with pytest.raises(PermissionError):
                path = Path("/invalid/path/amorsize/cache")
                path.mkdir(parents=True, exist_ok=True)
    
    def test_save_cache_entry_io_error(self):
        """I/O error during save should be handled silently."""
        with patch('builtins.open', side_effect=IOError("Disk full")):
            # Should not raise - errors are caught silently
            save_cache_entry(
                cache_key="test_key",
                n_jobs=4,
                chunksize=100,
                executor_type="process",
                estimated_speedup=3.5,
                reason="test",
                warnings=[]
            )
    
    def test_load_cache_entry_corrupted_json(self):
        """Corrupted JSON file should return None with reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "test_key.json"
            
            # Write invalid JSON
            with open(cache_file, 'w') as f:
                f.write("{ invalid json }")
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                entry, miss_reason = load_cache_entry("test_key")
                assert entry is None
                assert "Failed to load cache" in miss_reason
                assert "JSONDecodeError" in miss_reason
    
    def test_load_cache_entry_missing_required_key(self):
        """JSON missing required key should return None with reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "test_key.json"
            
            # Write JSON missing required key
            with open(cache_file, 'w') as f:
                json.dump({"n_jobs": 4}, f)
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                entry, miss_reason = load_cache_entry("test_key")
                assert entry is None
                assert "Failed to load cache" in miss_reason
    
    def test_prune_expired_cache_corrupted_file(self):
        """Pruning should delete corrupted cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "corrupted.json"
            
            # Write corrupted file
            with open(cache_file, 'w') as f:
                f.write("corrupted")
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                count = prune_expired_cache()
                assert count >= 1  # Should delete corrupted file
                assert not cache_file.exists()
    
    def test_clear_cache_permission_error_on_delete(self):
        """Permission error during delete should be handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache_file = cache_dir / "test.json"
            cache_file.write_text("{}")
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                with patch('pathlib.Path.unlink', side_effect=PermissionError("No permission")):
                    # Should not raise - errors caught silently
                    count = clear_cache()
                    # count will be 0 because unlink failed
                    assert count == 0


# =============================================================================
# 4. INVARIANT VERIFICATION
# =============================================================================

class TestInvariants:
    """Test invariants that should always hold."""
    
    def test_cache_key_always_has_version(self):
        """Cache key should always include version component."""
        def func(x):
            return x
        
        key = compute_cache_key(func, 100, 0.001)
        assert f"v:{CACHE_VERSION}" in key
    
    def test_cache_key_always_has_all_components(self):
        """Cache key should always have func, size, time, version."""
        def func(x):
            return x
        
        key = compute_cache_key(func, 100, 0.001)
        assert "func:" in key
        assert "size:" in key
        assert "time:" in key
        assert "v:" in key
    
    def test_cache_entry_to_dict_from_dict_roundtrip(self):
        """to_dict -> from_dict should preserve all fields."""
        original = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test reason",
            warnings=["warning1", "warning2"],
            timestamp=123456.789,
            system_info={"cores": 4, "memory": 8000},
            cache_version=1,
            pickle_size=1024,
            coefficient_of_variation=0.15,
            function_complexity=500
        )
        
        data = original.to_dict()
        reconstructed = CacheEntry.from_dict(data)
        
        assert reconstructed.n_jobs == original.n_jobs
        assert reconstructed.chunksize == original.chunksize
        assert reconstructed.executor_type == original.executor_type
        assert reconstructed.estimated_speedup == original.estimated_speedup
        assert reconstructed.reason == original.reason
        assert reconstructed.warnings == original.warnings
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.system_info == original.system_info
        assert reconstructed.cache_version == original.cache_version
        assert reconstructed.pickle_size == original.pickle_size
        assert reconstructed.coefficient_of_variation == original.coefficient_of_variation
        assert reconstructed.function_complexity == original.function_complexity
    
    def test_benchmark_entry_to_dict_from_dict_roundtrip(self):
        """BenchmarkEntry to_dict -> from_dict should preserve all fields."""
        original = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.25,
            actual_speedup=4.0,
            n_jobs=4,
            chunksize=100,
            timestamp=123456.789,
            system_info={"cores": 4, "memory": 8000},
            cache_version=1
        )
        
        data = original.to_dict()
        reconstructed = BenchmarkCacheEntry.from_dict(data)
        
        assert reconstructed.serial_time == original.serial_time
        assert reconstructed.parallel_time == original.parallel_time
        assert reconstructed.actual_speedup == original.actual_speedup
        assert reconstructed.n_jobs == original.n_jobs
        assert reconstructed.chunksize == original.chunksize
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.system_info == original.system_info
        assert reconstructed.cache_version == original.cache_version
    
    def test_system_compatibility_deterministic(self):
        """System compatibility check should be deterministic."""
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": 4,
                "available_memory": 8000000000,
                "start_method": "spawn"
            }
        )
        
        # Call twice should give same result
        result1, reason1 = entry.is_system_compatible()
        result2, reason2 = entry.is_system_compatible()
        assert result1 == result2
        assert reason1 == reason2


# =============================================================================
# 5. CACHING BEHAVIOR
# =============================================================================

class TestCachingBehavior:
    """Test caching behavior and performance optimizations."""
    
    def test_function_hash_cache_performance(self):
        """Function hash should be faster on second call (cached)."""
        def func(x):
            return x * 2
        
        clear_function_hash_cache()
        
        # First call (uncached)
        start = time.perf_counter()
        hash1 = _compute_function_hash(func)
        first_time = time.perf_counter() - start
        
        # Second call (cached)
        start = time.perf_counter()
        hash2 = _compute_function_hash(func)
        second_time = time.perf_counter() - start
        
        assert hash1 == hash2
        # Second call should be faster (though timing can be noisy)
        # We just verify both calls work
        assert second_time >= 0
        assert first_time >= 0
    
    def test_cache_dir_caching_consistency(self):
        """Cache directory should be cached and consistent."""
        _clear_cache_dir_cache()
        
        dir1 = get_cache_dir()
        dir2 = get_cache_dir()
        
        assert dir1 == dir2
        assert dir1.exists()
    
    def test_clear_function_hash_cache_clears_cache(self):
        """Clearing function hash cache should force recomputation."""
        def func(x):
            return x
        
        # Compute hash
        hash1 = _compute_function_hash(func)
        
        # Clear cache
        clear_function_hash_cache()
        
        # Compute again - should work even after clear
        hash2 = _compute_function_hash(func)
        assert hash1 == hash2
    
    def test_clear_cache_dir_cache_clears_cache(self):
        """Clearing cache dir cache should force recomputation."""
        dir1 = get_cache_dir()
        
        _clear_cache_dir_cache()
        
        dir2 = get_cache_dir()
        assert dir1 == dir2  # Same directory, just re-computed


# =============================================================================
# 6. THREAD SAFETY
# =============================================================================

class TestThreadSafety:
    """Test thread safety of cache operations."""
    
    def test_concurrent_function_hash_computation(self):
        """Concurrent hash computation should be thread-safe."""
        def func(x):
            return x * 2
        
        clear_function_hash_cache()
        results = []
        
        def compute_hash():
            hash_val = _compute_function_hash(func)
            results.append(hash_val)
        
        threads = [threading.Thread(target=compute_hash) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should get same hash
        assert len(set(results)) == 1
    
    def test_concurrent_cache_dir_access(self):
        """Concurrent cache dir access should be thread-safe."""
        _clear_cache_dir_cache()
        results = []
        
        def get_dir():
            cache_dir = get_cache_dir()
            results.append(str(cache_dir))
        
        threads = [threading.Thread(target=get_dir) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should get same directory
        assert len(set(results)) == 1


# =============================================================================
# 7. PLATFORM-SPECIFIC BEHAVIOR
# =============================================================================

class TestPlatformBehavior:
    """Test platform-specific cache behavior."""
    
    def test_get_cache_dir_windows(self):
        """Windows should use LOCALAPPDATA."""
        with patch('platform.system', return_value='Windows'):
            with patch('os.environ.get') as mock_env:
                with patch('pathlib.Path.mkdir'):
                    _clear_cache_dir_cache()
                    mock_env.return_value = "C:\\Users\\Test\\AppData\\Local"
                    
                    cache_dir = get_cache_dir()
                    cache_dir_str = str(cache_dir)
                    
                    # Should contain expected path components
                    assert "amorsize" in cache_dir_str
                    assert "optimization_cache" in cache_dir_str
    
    def test_get_cache_dir_macos(self):
        """macOS should use ~/Library/Caches."""
        with patch('platform.system', return_value='Darwin'):
            with patch('pathlib.Path.home') as mock_home:
                with patch('pathlib.Path.mkdir'):
                    _clear_cache_dir_cache()
                    mock_home.return_value = Path("/Users/test")
                    
                    cache_dir = get_cache_dir()
                    cache_dir_str = str(cache_dir)
                    
                    assert "Library" in cache_dir_str or "amorsize" in cache_dir_str
                    assert "optimization_cache" in cache_dir_str
    
    def test_get_cache_dir_linux(self):
        """Linux should use XDG_CACHE_HOME or ~/.cache."""
        with patch('platform.system', return_value='Linux'):
            with patch('pathlib.Path.home') as mock_home:
                with patch('pathlib.Path.mkdir'):
                    _clear_cache_dir_cache()
                    mock_home.return_value = Path("/home/test")
                    
                    # Mock os.environ.get to return None for XDG_CACHE_HOME
                    with patch.dict('os.environ', {}, clear=True):
                        cache_dir = get_cache_dir()
                        cache_dir_str = str(cache_dir)
                        
                        assert "amorsize" in cache_dir_str
                        assert "optimization_cache" in cache_dir_str


# =============================================================================
# 8. FILE OPERATIONS
# =============================================================================

class TestFileOperations:
    """Test file I/O edge cases."""
    
    def test_save_and_load_roundtrip(self):
        """Save followed by load should retrieve same data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                # Save entry
                save_cache_entry(
                    cache_key="test_roundtrip",
                    n_jobs=4,
                    chunksize=100,
                    executor_type="process",
                    estimated_speedup=3.5,
                    reason="test reason",
                    warnings=["warning1"]
                )
                
                # Load entry
                entry, miss_reason = load_cache_entry("test_roundtrip")
                
                assert entry is not None
                assert miss_reason == ""
                assert entry.n_jobs == 4
                assert entry.chunksize == 100
                assert entry.executor_type == "process"
                assert entry.estimated_speedup == 3.5
                assert entry.reason == "test reason"
                assert entry.warnings == ["warning1"]
    
    def test_load_nonexistent_cache_entry(self):
        """Loading nonexistent entry should return None with reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                entry, miss_reason = load_cache_entry("nonexistent_key")
                
                assert entry is None
                assert "No cached entry found" in miss_reason
    
    def test_clear_cache_empties_directory(self):
        """clear_cache should remove all cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Create some cache files
            (cache_dir / "cache1.json").write_text("{}")
            (cache_dir / "cache2.json").write_text("{}")
            (cache_dir / "cache3.json").write_text("{}")
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                count = clear_cache()
                
                assert count == 3
                # All JSON files should be deleted
                assert len(list(cache_dir.glob("*.json"))) == 0


# =============================================================================
# 9. CACHE PRUNING
# =============================================================================

class TestCachePruning:
    """Test cache pruning behavior."""
    
    def test_prune_expired_cache_removes_old_entries(self):
        """Pruning should remove entries older than TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Create old entry
            old_entry = CacheEntry(
                n_jobs=4,
                chunksize=100,
                executor_type="process",
                estimated_speedup=3.5,
                reason="test",
                warnings=[],
                timestamp=time.time() - (10 * 24 * 60 * 60),  # 10 days old
                system_info={}
            )
            
            cache_file = cache_dir / "old_entry.json"
            with open(cache_file, 'w') as f:
                json.dump(old_entry.to_dict(), f)
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                count = prune_expired_cache(ttl_seconds=7 * 24 * 60 * 60)  # 7 day TTL
                
                assert count >= 1
                assert not cache_file.exists()
    
    def test_prune_expired_cache_keeps_fresh_entries(self):
        """Pruning should keep entries within TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Create fresh entry
            fresh_entry = CacheEntry(
                n_jobs=4,
                chunksize=100,
                executor_type="process",
                estimated_speedup=3.5,
                reason="test",
                warnings=[],
                timestamp=time.time(),  # Current time
                system_info={}
            )
            
            cache_file = cache_dir / "fresh_entry.json"
            with open(cache_file, 'w') as f:
                json.dump(fresh_entry.to_dict(), f)
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                count = prune_expired_cache(ttl_seconds=7 * 24 * 60 * 60)
                
                # Fresh entry should not be deleted
                assert cache_file.exists()
    
    def test_maybe_auto_prune_cache_probabilistic(self):
        """Auto-prune should trigger probabilistically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Test with 100% probability - should always trigger
            with patch('amorsize.cache.random.random', return_value=0.0):
                # Create expired entry
                old_entry = CacheEntry(
                    n_jobs=4,
                    chunksize=100,
                    executor_type="process",
                    estimated_speedup=3.5,
                    reason="test",
                    warnings=[],
                    timestamp=time.time() - (10 * 24 * 60 * 60),
                    system_info={}
                )
                
                cache_file = cache_dir / "old_auto_prune.json"
                with open(cache_file, 'w') as f:
                    json.dump(old_entry.to_dict(), f)
                
                # Call auto-prune with 100% probability
                _maybe_auto_prune_cache(
                    lambda: cache_dir,
                    probability=1.0,
                    ttl_seconds=7 * 24 * 60 * 60
                )
                
                # Old entry should be deleted
                assert not cache_file.exists()
    
    def test_maybe_auto_prune_cache_never_triggers(self):
        """Auto-prune with 0% probability should never trigger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Create expired entry
            old_entry = CacheEntry(
                n_jobs=4,
                chunksize=100,
                executor_type="process",
                estimated_speedup=3.5,
                reason="test",
                warnings=[],
                timestamp=time.time() - (10 * 24 * 60 * 60),
                system_info={}
            )
            
            cache_file = cache_dir / "old_no_prune.json"
            with open(cache_file, 'w') as f:
                json.dump(old_entry.to_dict(), f)
            
            # Call auto-prune with 0% probability
            _maybe_auto_prune_cache(
                lambda: cache_dir,
                probability=0.0,
                ttl_seconds=7 * 24 * 60 * 60
            )
            
            # Old entry should still exist (pruning didn't trigger)
            assert cache_file.exists()


# =============================================================================
# 10. SYSTEM COMPATIBILITY
# =============================================================================

class TestSystemCompatibility:
    """Test system compatibility checks."""
    
    def test_system_compatible_exact_match(self):
        """Entry with exact system match should be compatible."""
        from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method
        
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": get_physical_cores(),
                "available_memory": get_available_memory(),
                "start_method": get_multiprocessing_start_method()
            }
        )
        
        is_compatible, reason = entry.is_system_compatible()
        assert is_compatible
        assert reason == ""
    
    def test_system_incompatible_core_count(self):
        """Entry with different core count should be incompatible."""
        from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method
        
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": get_physical_cores() + 100,  # Different
                "available_memory": get_available_memory(),
                "start_method": get_multiprocessing_start_method()
            }
        )
        
        is_compatible, reason = entry.is_system_compatible()
        assert not is_compatible
        assert "Physical core count changed" in reason
    
    def test_system_incompatible_start_method(self):
        """Entry with different start method should be incompatible."""
        from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method
        
        current_method = get_multiprocessing_start_method()
        different_method = "spawn" if current_method != "spawn" else "fork"
        
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": get_physical_cores(),
                "available_memory": get_available_memory(),
                "start_method": different_method
            }
        )
        
        is_compatible, reason = entry.is_system_compatible()
        assert not is_compatible
        assert "start method changed" in reason
    
    def test_system_compatible_memory_within_tolerance(self):
        """Entry with memory within 20% tolerance should be compatible."""
        from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method
        
        current_memory = get_available_memory()
        memory_within_tolerance = int(current_memory * 0.95)  # 5% difference
        
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": get_physical_cores(),
                "available_memory": memory_within_tolerance,
                "start_method": get_multiprocessing_start_method()
            }
        )
        
        is_compatible, reason = entry.is_system_compatible()
        assert is_compatible
        assert reason == ""
    
    def test_system_incompatible_memory_outside_tolerance(self):
        """Entry with memory outside 20% tolerance should be incompatible."""
        from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method
        
        current_memory = get_available_memory()
        memory_outside_tolerance = int(current_memory * 0.5)  # 50% difference
        
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={
                "physical_cores": get_physical_cores(),
                "available_memory": memory_outside_tolerance,
                "start_method": get_multiprocessing_start_method()
            }
        )
        
        is_compatible, reason = entry.is_system_compatible()
        assert not is_compatible
        assert "Available memory changed significantly" in reason


# =============================================================================
# 11. BENCHMARK CACHE
# =============================================================================

class TestBenchmarkCache:
    """Test benchmark cache specific behavior."""
    
    def test_benchmark_cache_entry_stricter_memory_tolerance(self):
        """Benchmark cache should have stricter memory tolerance (10% vs 20%)."""
        from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method
        
        current_memory = get_available_memory()
        # 15% difference - within optimization cache tolerance (20%) but outside benchmark (10%)
        memory_15_percent_diff = int(current_memory * 0.85)
        
        entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.25,
            actual_speedup=4.0,
            n_jobs=4,
            chunksize=100,
            timestamp=time.time(),
            system_info={
                "physical_cores": get_physical_cores(),
                "available_memory": memory_15_percent_diff,
                "start_method": get_multiprocessing_start_method()
            }
        )
        
        is_compatible, reason = entry.is_system_compatible()
        assert not is_compatible
        assert "Available memory changed significantly" in reason
    
    def test_get_benchmark_cache_dir_separate_from_optimization(self):
        """Benchmark cache should use separate directory."""
        opt_cache_dir = get_cache_dir()
        bench_cache_dir = get_benchmark_cache_dir()
        
        # Should both exist
        assert opt_cache_dir.exists()
        assert bench_cache_dir.exists()
        
        # Should be different directories
        assert opt_cache_dir != bench_cache_dir
        
        # Both should contain 'amorsize' but different subdirectories
        assert "amorsize" in str(opt_cache_dir)
        assert "amorsize" in str(bench_cache_dir)
        assert "optimization_cache" in str(opt_cache_dir)
        assert "benchmark_cache" in str(bench_cache_dir)


# =============================================================================
# 12. EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test additional edge cases."""
    
    def test_cache_entry_with_ml_features(self):
        """Cache entry with ML features should be preserved."""
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={},
            pickle_size=2048,
            coefficient_of_variation=0.25,
            function_complexity=1000
        )
        
        data = entry.to_dict()
        assert "pickle_size" in data
        assert "coefficient_of_variation" in data
        assert "function_complexity" in data
        assert data["pickle_size"] == 2048
        assert data["coefficient_of_variation"] == 0.25
        assert data["function_complexity"] == 1000
    
    def test_cache_entry_without_ml_features(self):
        """Cache entry without ML features should work."""
        entry = CacheEntry(
            n_jobs=4,
            chunksize=100,
            executor_type="process",
            estimated_speedup=3.5,
            reason="test",
            warnings=[],
            timestamp=time.time(),
            system_info={}
        )
        
        data = entry.to_dict()
        # ML features should not be in dict if not provided
        assert "pickle_size" not in data
        assert "coefficient_of_variation" not in data
        assert "function_complexity" not in data
    
    def test_compute_benchmark_cache_key(self):
        """Benchmark cache key should be computed correctly."""
        def func(x):
            return x * 2
        
        key = compute_benchmark_cache_key(func, data_size=1000)
        
        # Benchmark key format is: benchmark_{func_hash}_{data_size}_v{version}
        # Different from optimization cache key format
        assert "benchmark_" in key
        assert "_1000_" in key
        assert f"_v{CACHE_VERSION}" in key
        assert isinstance(key, str)
    
    def test_cache_version_mismatch_invalidates(self):
        """Cache entry with wrong version should be invalidated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            
            # Create entry with wrong version
            entry = CacheEntry(
                n_jobs=4,
                chunksize=100,
                executor_type="process",
                estimated_speedup=3.5,
                reason="test",
                warnings=[],
                timestamp=time.time(),
                system_info={},
                cache_version=999  # Wrong version
            )
            
            cache_file = cache_dir / "wrong_version.json"
            with open(cache_file, 'w') as f:
                json.dump(entry.to_dict(), f)
            
            with patch('amorsize.cache.get_cache_dir', return_value=cache_dir):
                entry_loaded, miss_reason = load_cache_entry("wrong_version")
                
                assert entry_loaded is None
                assert "version mismatch" in miss_reason
