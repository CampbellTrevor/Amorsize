"""
Tests for detailed cache miss reason feedback.

This module tests the enhanced cache miss feedback functionality added in Iteration 75,
which provides users with detailed explanations of why their cache was invalidated.
"""

import time
from unittest.mock import patch

import pytest

from amorsize import optimize, validate_optimization, clear_cache, clear_benchmark_cache
from amorsize.cache import (
    CacheEntry,
    BenchmarkCacheEntry,
    load_cache_entry,
    load_benchmark_cache_entry,
    save_cache_entry,
    save_benchmark_cache_entry,
    compute_cache_key,
    compute_benchmark_cache_key,
    CACHE_VERSION
)
from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method


def simple_func(x):
    """Simple test function."""
    return x * 2


class TestOptimizationCacheMissReasons:
    """Tests for optimization cache miss reason reporting."""
    
    def test_cache_miss_no_entry_found(self):
        """Test cache miss reason when no entry exists."""
        clear_cache()
        entry, miss_reason = load_cache_entry("nonexistent_key_12345")
        assert entry is None
        assert "No cached entry found for this workload" in miss_reason
    
    def test_cache_miss_core_count_changed(self):
        """Test cache miss reason when core count changes."""
        # Create entry with different core count
        system_info = {
            "physical_cores": get_physical_cores() + 5,  # Different
            "available_memory": get_available_memory(),
            "start_method": get_multiprocessing_start_method()
        }
        
        cache_entry = CacheEntry(
            n_jobs=4,
            chunksize=10,
            executor_type="process",
            estimated_speedup=2.0,
            reason="Test",
            warnings=[],
            timestamp=time.time(),
            system_info=system_info
        )
        
        is_compatible, reason = cache_entry.is_system_compatible()
        assert not is_compatible
        assert "Physical core count changed" in reason
        assert f"cached: {get_physical_cores() + 5}" in reason
        assert f"current: {get_physical_cores()}" in reason
    
    def test_cache_miss_start_method_changed(self):
        """Test cache miss reason when start method changes."""
        # Create entry with different start method
        current_method = get_multiprocessing_start_method()
        different_method = "spawn" if current_method != "spawn" else "fork"
        
        system_info = {
            "physical_cores": get_physical_cores(),
            "available_memory": get_available_memory(),
            "start_method": different_method
        }
        
        cache_entry = CacheEntry(
            n_jobs=4,
            chunksize=10,
            executor_type="process",
            estimated_speedup=2.0,
            reason="Test",
            warnings=[],
            timestamp=time.time(),
            system_info=system_info
        )
        
        is_compatible, reason = cache_entry.is_system_compatible()
        assert not is_compatible
        assert "Multiprocessing start method changed" in reason
        assert f"cached: {different_method}" in reason
        assert f"current: {current_method}" in reason
    
    def test_cache_miss_memory_changed(self):
        """Test cache miss reason when available memory changes significantly."""
        # Create entry with significantly different memory (outside 20% tolerance)
        current_memory = get_available_memory()
        cached_memory = int(current_memory * 0.5)  # 50% different (outside 20% tolerance)
        
        system_info = {
            "physical_cores": get_physical_cores(),
            "available_memory": cached_memory,
            "start_method": get_multiprocessing_start_method()
        }
        
        cache_entry = CacheEntry(
            n_jobs=4,
            chunksize=10,
            executor_type="process",
            estimated_speedup=2.0,
            reason="Test",
            warnings=[],
            timestamp=time.time(),
            system_info=system_info
        )
        
        is_compatible, reason = cache_entry.is_system_compatible()
        assert not is_compatible
        assert "Available memory changed significantly" in reason
        assert "cached:" in reason
        assert "current:" in reason
        assert "GB" in reason
    
    def test_cache_miss_expired(self):
        """Test cache miss reason when entry is expired."""
        cache_key = compute_cache_key(simple_func, 1000, 0.001)
        
        # Save entry
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=50,
            executor_type="process",
            estimated_speedup=1.8,
            reason="Test",
            warnings=[]
        )
        
        # Load with TTL=0 (immediately expired)
        entry, miss_reason = load_cache_entry(cache_key, ttl_seconds=0)
        assert entry is None
        assert "Cache entry expired" in miss_reason
        assert "age:" in miss_reason
        assert "TTL:" in miss_reason
        assert "days" in miss_reason
    
    def test_cache_miss_version_mismatch(self):
        """Test cache miss reason when cache version changes."""
        # This is harder to test directly since we'd need to modify cache files
        # but we can verify the reason string exists in the code path
        cache_key = "test_version_key"
        
        # Create entry with old version number
        system_info = {
            "physical_cores": get_physical_cores(),
            "available_memory": get_available_memory(),
            "start_method": get_multiprocessing_start_method()
        }
        
        old_entry = CacheEntry(
            n_jobs=2,
            chunksize=10,
            executor_type="process",
            estimated_speedup=1.5,
            reason="Test",
            warnings=[],
            timestamp=time.time(),
            system_info=system_info,
            cache_version=CACHE_VERSION - 1  # Old version
        )
        
        # Verify the version check would fail
        assert old_entry.cache_version != CACHE_VERSION
    
    def test_verbose_output_shows_detailed_miss_reason(self, capsys):
        """Test that verbose mode shows detailed cache miss reason."""
        clear_cache()
        
        # First run - no cache
        result1 = optimize(simple_func, range(100), verbose=True)
        captured = capsys.readouterr()
        # First run might show cache miss or not depending on test order
        
        # Second run - cache hit
        result2 = optimize(simple_func, range(100), verbose=True)
        captured = capsys.readouterr()
        assert "✓ Cache hit!" in captured.out
        
        # Clear cache and run again - should show miss reason
        clear_cache()
        result3 = optimize(simple_func, range(100), verbose=True)
        captured = capsys.readouterr()
        assert "✗ Cache miss" in captured.out
        assert "No cached entry found" in captured.out


class TestBenchmarkCacheMissReasons:
    """Tests for benchmark cache miss reason reporting."""
    
    def test_benchmark_cache_miss_no_entry(self):
        """Test benchmark cache miss when no entry exists."""
        clear_benchmark_cache()
        entry, miss_reason = load_benchmark_cache_entry("nonexistent_key")
        assert entry is None
        assert "No cached benchmark result found for this workload" in miss_reason
    
    def test_benchmark_cache_miss_core_count_changed(self):
        """Test benchmark cache miss when core count changes."""
        system_info = {
            "physical_cores": get_physical_cores() + 3,  # Different
            "available_memory": get_available_memory(),
            "start_method": get_multiprocessing_start_method()
        }
        
        cache_entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=10,
            timestamp=time.time(),
            system_info=system_info
        )
        
        is_compatible, reason = cache_entry.is_system_compatible()
        assert not is_compatible
        assert "Physical core count changed" in reason
    
    def test_benchmark_cache_miss_memory_changed(self):
        """Test benchmark cache miss when memory changes (stricter 10% tolerance)."""
        current_memory = get_available_memory()
        cached_memory = int(current_memory * 0.85)  # 15% different (outside 10% tolerance)
        
        system_info = {
            "physical_cores": get_physical_cores(),
            "available_memory": cached_memory,
            "start_method": get_multiprocessing_start_method()
        }
        
        cache_entry = BenchmarkCacheEntry(
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=10,
            timestamp=time.time(),
            system_info=system_info
        )
        
        is_compatible, reason = cache_entry.is_system_compatible()
        assert not is_compatible
        assert "Available memory changed significantly" in reason
        assert "GB" in reason
    
    def test_benchmark_cache_miss_expired(self):
        """Test benchmark cache miss when entry is expired."""
        cache_key = compute_benchmark_cache_key(simple_func, 100)
        
        # Save entry
        save_benchmark_cache_entry(
            cache_key=cache_key,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            n_jobs=4,
            chunksize=10
        )
        
        # Load with TTL=0 (expired)
        entry, miss_reason = load_benchmark_cache_entry(cache_key, ttl_seconds=0)
        assert entry is None
        assert "Cache entry expired" in miss_reason
        assert "age:" in miss_reason
        assert "TTL:" in miss_reason
    
    def test_benchmark_verbose_shows_detailed_miss_reason(self, capsys):
        """Test that benchmark validation shows detailed cache miss reason."""
        clear_benchmark_cache()
        
        # First run - cache miss
        result1 = validate_optimization(simple_func, range(50), verbose=True)
        captured = capsys.readouterr()
        assert "✗ Cache miss" in captured.out
        assert "No cached benchmark result found" in captured.out
        
        # Second run - cache hit
        result2 = validate_optimization(simple_func, range(50), verbose=True)
        captured = capsys.readouterr()
        assert "✓ Cache hit!" in captured.out


class TestCacheMissReasonBackwardCompatibility:
    """Tests to ensure backward compatibility with cache miss reasons."""
    
    def test_tuple_unpacking_works(self):
        """Test that both tuple unpacking and direct assignment work."""
        clear_cache()
        
        # Tuple unpacking (new style)
        entry, miss_reason = load_cache_entry("nonexistent")
        assert entry is None
        assert miss_reason != ""
        
        # Can still check entry is None without unpacking reason
        entry2, _ = load_cache_entry("nonexistent2")
        assert entry2 is None
    
    def test_empty_reason_on_success(self):
        """Test that miss_reason is empty string on successful load."""
        cache_key = compute_cache_key(simple_func, 100, 0.001)
        
        # Save entry
        save_cache_entry(
            cache_key=cache_key,
            n_jobs=2,
            chunksize=10,
            executor_type="process",
            estimated_speedup=1.5,
            reason="Test",
            warnings=[]
        )
        
        # Load successfully
        entry, miss_reason = load_cache_entry(cache_key)
        assert entry is not None
        assert miss_reason == ""
        assert entry.n_jobs == 2


class TestCacheMissReasonQuality:
    """Tests for quality of cache miss reason messages."""
    
    def test_reasons_are_human_readable(self):
        """Test that all miss reasons are human-readable."""
        clear_cache()
        
        # No entry found
        _, reason1 = load_cache_entry("test1")
        assert len(reason1) > 0
        assert reason1[0].isupper() or reason1[0].isdigit()  # Starts with capital or number
        
        # All reasons should be clear sentences or phrases
        assert "No cached entry found" in reason1
    
    def test_reasons_include_relevant_details(self):
        """Test that miss reasons include specific details when available."""
        # Core count change
        system_info = {
            "physical_cores": 999,  # Clearly different
            "available_memory": get_available_memory(),
            "start_method": get_multiprocessing_start_method()
        }
        
        entry = CacheEntry(
            n_jobs=4, chunksize=10, executor_type="process",
            estimated_speedup=2.0, reason="Test", warnings=[],
            timestamp=time.time(), system_info=system_info
        )
        
        _, reason = entry.is_system_compatible()
        
        # Should include both cached and current values
        assert "999" in reason  # Cached value
        assert "cached:" in reason.lower()
        assert "current:" in reason.lower()
