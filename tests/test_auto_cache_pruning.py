"""
Tests for automatic cache pruning functionality.

This module tests the probabilistic automatic cache pruning that happens
during cache load operations to prevent unbounded cache directory growth.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from amorsize.cache import (
    AUTO_PRUNE_PROBABILITY,
    CacheEntry,
    BenchmarkCacheEntry,
    get_cache_dir,
    get_benchmark_cache_dir,
    load_cache_entry,
    load_benchmark_cache_entry,
    save_cache_entry,
    save_benchmark_cache_entry,
    compute_cache_key,
    compute_benchmark_cache_key,
    _maybe_auto_prune_cache,
    DEFAULT_TTL_SECONDS,
)


def simple_test_func(x):
    """Simple function for testing."""
    return x * 2


class TestAutoPruningInfrastructure:
    """Test the automatic pruning infrastructure."""
    
    def test_auto_prune_probability_is_low(self):
        """Verify that auto-pruning probability is low to minimize performance impact."""
        assert AUTO_PRUNE_PROBABILITY <= 0.1, "Auto-prune probability should be <= 10%"
        assert AUTO_PRUNE_PROBABILITY > 0.0, "Auto-prune probability should be > 0%"
    
    def test_maybe_auto_prune_cache_respects_probability(self):
        """Test that auto-pruning respects probability setting."""
        # With probability 0.0, should never trigger
        with patch('amorsize.cache.random.random', return_value=0.5):
            _maybe_auto_prune_cache(get_cache_dir, probability=0.0)
            # If it returns without error, it skipped pruning (correct)
        
        # With probability 1.0, should always trigger
        # (though it may not delete anything if no expired entries exist)
        with patch('amorsize.cache.random.random', return_value=0.5):
            _maybe_auto_prune_cache(get_cache_dir, probability=1.0)
            # If it returns without error, it attempted pruning (correct)
    
    def test_maybe_auto_prune_handles_missing_cache_dir(self):
        """Test that auto-pruning handles missing cache directory gracefully."""
        def fake_cache_dir():
            return Path("/nonexistent/fake/cache/dir")
        
        # Should not raise exception even with nonexistent directory
        _maybe_auto_prune_cache(fake_cache_dir, probability=1.0)
    
    def test_maybe_auto_prune_handles_corrupted_files(self, tmp_path):
        """Test that auto-pruning handles corrupted cache files gracefully."""
        # Create a temporary cache directory
        cache_dir = tmp_path / "test_cache"
        cache_dir.mkdir()
        
        # Create a corrupted cache file
        corrupted_file = cache_dir / "corrupted.json"
        corrupted_file.write_text("not valid json {{{")
        
        def fake_cache_dir():
            return cache_dir
        
        # Should not raise exception, should attempt to delete corrupted file
        with patch('amorsize.cache.random.random', return_value=0.0):  # Force trigger
            _maybe_auto_prune_cache(fake_cache_dir, probability=1.0)
        
        # Corrupted file should be deleted
        assert not corrupted_file.exists()


class TestOptimizationCacheAutoPruning:
    """Test automatic pruning for optimization cache."""
    
    def test_load_cache_entry_triggers_auto_prune(self):
        """Test that loading cache entry can trigger automatic pruning."""
        # Mock the random function to control when pruning triggers
        with patch('amorsize.cache.random.random', return_value=0.0):  # < 0.05, will trigger
            with patch('amorsize.cache._maybe_auto_prune_cache') as mock_prune:
                load_cache_entry("fake_key")
                
                # Verify auto-pruning was called
                assert mock_prune.called
                args, kwargs = mock_prune.call_args
                assert args[0] == get_cache_dir
                assert 'ttl_seconds' in kwargs
    
    def test_auto_prune_removes_expired_entries(self):
        """Test that auto-pruning removes expired cache entries."""
        # Create an expired cache entry
        cache_key = compute_cache_key(simple_test_func, 100, 0.001)
        
        # Save entry with old timestamp
        cache_dir = get_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        entry = CacheEntry(
            n_jobs=2,
            chunksize=50,
            executor_type="process",
            estimated_speedup=1.5,
            reason="test",
            warnings=[],
            timestamp=time.time() - (DEFAULT_TTL_SECONDS + 1),  # Expired
            system_info={
                "physical_cores": 2,
                "available_memory": 1000000,
                "start_method": "fork",
                "platform": "Linux",
                "python_version": "3.8"
            }
        )
        
        with open(cache_file, 'w') as f:
            json.dump(entry.to_dict(), f)
        
        assert cache_file.exists()
        
        # Force auto-pruning to trigger with probability=1.0
        _maybe_auto_prune_cache(get_cache_dir, probability=1.0)
        
        # Expired entry should be removed
        assert not cache_file.exists()
    
    def test_auto_prune_preserves_recent_entries(self):
        """Test that auto-pruning preserves recent cache entries."""
        # Create a recent cache entry
        cache_key = compute_cache_key(simple_test_func, 100, 0.001)
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=50,
            executor_type="process",
            estimated_speedup=1.5,
            reason="test",
            warnings=[]
        )
        
        cache_dir = get_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        assert cache_file.exists()
        
        # Force auto-pruning to trigger with probability=1.0
        _maybe_auto_prune_cache(get_cache_dir, probability=1.0)
        
        # Recent entry should still exist
        assert cache_file.exists()


class TestBenchmarkCacheAutoPruning:
    """Test automatic pruning for benchmark cache."""
    
    def test_load_benchmark_cache_triggers_auto_prune(self):
        """Test that loading benchmark cache entry can trigger automatic pruning."""
        # Mock the random function to control when pruning triggers
        with patch('amorsize.cache.random.random', return_value=0.0):  # < 0.05, will trigger
            with patch('amorsize.cache._maybe_auto_prune_cache') as mock_prune:
                load_benchmark_cache_entry("fake_key")
                
                # Verify auto-pruning was called
                assert mock_prune.called
                args, kwargs = mock_prune.call_args
                assert args[0] == get_benchmark_cache_dir
                assert 'ttl_seconds' in kwargs
    
    def test_benchmark_auto_prune_removes_expired_entries(self):
        """Test that auto-pruning removes expired benchmark cache entries."""
        # Create an expired benchmark cache entry
        cache_key = compute_benchmark_cache_key(simple_test_func, 100)
        
        # Save entry with old timestamp
        cache_dir = get_benchmark_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.6,
            actual_speedup=1.67,
            n_jobs=2,
            chunksize=50,
            timestamp=time.time() - (DEFAULT_TTL_SECONDS + 1),  # Expired
            system_info={
                "physical_cores": 2,
                "available_memory": 1000000,
                "start_method": "fork",
                "platform": "Linux",
                "python_version": "3.8"
            }
        )
        
        with open(cache_file, 'w') as f:
            json.dump(entry.to_dict(), f)
        
        assert cache_file.exists()
        
        # Force auto-pruning to trigger with probability=1.0
        _maybe_auto_prune_cache(get_benchmark_cache_dir, probability=1.0)
        
        # Expired entry should be removed
        assert not cache_file.exists()
    
    def test_benchmark_auto_prune_preserves_recent_entries(self):
        """Test that auto-pruning preserves recent benchmark cache entries."""
        # Create a recent benchmark cache entry
        cache_key = compute_benchmark_cache_key(simple_test_func, 100)
        save_benchmark_cache_entry(
            cache_key=cache_key,
            serial_time=1.0,
            parallel_time=0.6,
            actual_speedup=1.67,
            n_jobs=2,
            chunksize=50
        )
        
        cache_dir = get_benchmark_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        assert cache_file.exists()
        
        # Force auto-pruning to trigger with probability=1.0
        _maybe_auto_prune_cache(get_benchmark_cache_dir, probability=1.0)
        
        # Recent entry should still exist
        assert cache_file.exists()


class TestAutoPruningPerformance:
    """Test that automatic pruning doesn't impact performance significantly."""
    
    def test_auto_prune_is_fast_with_many_files(self, tmp_path):
        """Test that auto-pruning remains fast even with many cache files."""
        # Create a cache directory with many files
        cache_dir = tmp_path / "test_cache"
        cache_dir.mkdir()
        
        # Create 100 cache files (recent ones)
        for i in range(100):
            cache_file = cache_dir / f"cache_{i}.json"
            entry = CacheEntry(
                n_jobs=2,
                chunksize=50,
                executor_type="process",
                estimated_speedup=1.5,
                reason="test",
                warnings=[],
                timestamp=time.time(),  # Recent
                system_info={
                    "physical_cores": 2,
                    "available_memory": 1000000,
                    "start_method": "fork",
                    "platform": "Linux",
                    "python_version": "3.8"
                }
            )
            with open(cache_file, 'w') as f:
                json.dump(entry.to_dict(), f)
        
        def fake_cache_dir():
            return cache_dir
        
        # Measure time for auto-pruning
        start = time.perf_counter()
        _maybe_auto_prune_cache(fake_cache_dir, probability=1.0)
        elapsed = time.perf_counter() - start
        
        # Should complete quickly (< 100ms even with 100 files)
        assert elapsed < 0.1, f"Auto-pruning took {elapsed:.3f}s, expected < 0.1s"
    
    def test_load_with_auto_prune_disabled_is_fast(self):
        """Test that disabling auto-prune (probability=0) has no overhead."""
        # Create a cache entry
        cache_key = compute_cache_key(simple_test_func, 100, 0.001)
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=50,
            executor_type="process",
            estimated_speedup=1.5,
            reason="test",
            warnings=[]
        )
        
        # Mock random to always skip pruning
        with patch('amorsize.cache.random.random', return_value=0.99):  # > 0.05, will skip
            start = time.perf_counter()
            result = load_cache_entry(cache_key)
            elapsed = time.perf_counter() - start
        
        assert result is not None
        # Should be very fast since no pruning happened
        assert elapsed < 0.01, f"Load took {elapsed:.3f}s, expected < 0.01s"
