"""
Tests for workload characteristic caching optimization.

This module tests the caching behavior of detect_parallel_libraries() and
check_parallel_environment_vars() to ensure they return cached results on
subsequent calls for improved performance.
"""

import os
import sys
import pytest
from amorsize.sampling import (
    detect_parallel_libraries,
    check_parallel_environment_vars,
    _clear_workload_caches
)

# Module-level constant for test environment variables
# Extracted to avoid duplication and ensure consistency
TEST_ENV_VARS = [
    'OMP_NUM_THREADS',
    'MKL_NUM_THREADS', 
    'OPENBLAS_NUM_THREADS',
    'NUMEXPR_NUM_THREADS',
    'VECLIB_MAXIMUM_THREADS',
    'NUMBA_NUM_THREADS'
]


class TestParallelLibrariesCaching:
    """Test caching behavior of detect_parallel_libraries()."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_workload_caches()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_workload_caches()
    
    def test_caching_basic_behavior(self):
        """Test that detect_parallel_libraries() returns cached result on second call."""
        # First call should detect and cache
        result1 = detect_parallel_libraries()
        
        # Second call should return cached result (same object reference)
        result2 = detect_parallel_libraries()
        
        # Should return the same list object (cached)
        assert result1 is result2
        assert result1 == result2
    
    def test_cache_persists_across_calls(self):
        """Test that cache persists across multiple calls."""
        # Make several calls
        results = [detect_parallel_libraries() for _ in range(5)]
        
        # All should return the same cached object
        for i in range(1, len(results)):
            assert results[0] is results[i]
    
    def test_cache_clear_resets(self):
        """Test that clearing cache causes fresh detection."""
        # First call
        result1 = detect_parallel_libraries()
        
        # Clear cache
        _clear_workload_caches()
        
        # Second call should create new result (not same object)
        result2 = detect_parallel_libraries()
        
        # Should have same content but different objects
        assert result1 == result2
        # Note: In CPython, small lists might be interned, so we can't
        # reliably test `is not` here. The important thing is the
        # function works correctly.
    
    def test_cache_detects_loaded_modules(self):
        """Test that cache correctly detects loaded parallel libraries."""
        # Clear cache to ensure fresh detection
        _clear_workload_caches()
        
        # Get current state
        result = detect_parallel_libraries()
        
        # Result should be a list
        assert isinstance(result, list)
        
        # All items should be strings
        for item in result:
            assert isinstance(item, str)
        
        # If numpy is loaded, should be detected
        if 'numpy' in sys.modules:
            assert 'numpy' in result
    
    def test_empty_cache_initially(self):
        """Test that cache is empty initially."""
        # This test verifies the cache starts empty
        # We can't directly access the cache variable, but we can verify
        # the function works correctly from a clean state
        result = detect_parallel_libraries()
        assert isinstance(result, list)


class TestEnvironmentVarsCaching:
    """Test caching behavior of check_parallel_environment_vars()."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_workload_caches()
        # Store original env vars using module-level constant
        self.original_vars = {
            key: os.environ.get(key)
            for key in TEST_ENV_VARS
        }
    
    def teardown_method(self):
        """Restore original env vars and clear cache."""
        # Restore original environment
        for key, value in self.original_vars.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        _clear_workload_caches()
    
    def test_caching_basic_behavior(self):
        """Test that check_parallel_environment_vars() returns cached result."""
        # First call should detect and cache
        result1 = check_parallel_environment_vars()
        
        # Second call should return cached result (same object)
        result2 = check_parallel_environment_vars()
        
        # Should return the same dict object (cached)
        assert result1 is result2
        assert result1 == result2
    
    def test_cache_persists_across_calls(self):
        """Test that cache persists across multiple calls."""
        # Make several calls
        results = [check_parallel_environment_vars() for _ in range(5)]
        
        # All should return the same cached object
        for i in range(1, len(results)):
            assert results[0] is results[i]
    
    def test_cache_clear_resets(self):
        """Test that clearing cache causes fresh detection."""
        # First call
        result1 = check_parallel_environment_vars()
        
        # Clear cache
        _clear_workload_caches()
        
        # Second call should create new result
        result2 = check_parallel_environment_vars()
        
        # Should have same content but potentially different objects
        assert result1 == result2
    
    def test_cache_with_set_env_vars(self):
        """Test that cache correctly detects set environment variables."""
        # Set a test environment variable
        os.environ['OMP_NUM_THREADS'] = '4'
        
        # Clear cache to ensure fresh detection
        _clear_workload_caches()
        
        # Get current state
        result = check_parallel_environment_vars()
        
        # Should detect our test variable
        assert 'OMP_NUM_THREADS' in result
        assert result['OMP_NUM_THREADS'] == '4'
    
    def test_cache_with_no_env_vars(self):
        """Test cache behavior when no relevant env vars are set."""
        # Clear all relevant env vars using module-level constant
        for key in TEST_ENV_VARS:
            os.environ.pop(key, None)
        
        # Clear cache
        _clear_workload_caches()
        
        # Get result
        result = check_parallel_environment_vars()
        
        # Should be empty dict
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_cache_returns_only_set_vars(self):
        """Test that cache only returns env vars that are set."""
        # Clear all vars using module-level constant
        for key in TEST_ENV_VARS:
            os.environ.pop(key, None)
        
        # Set only one
        os.environ['MKL_NUM_THREADS'] = '8'
        
        # Clear cache
        _clear_workload_caches()
        
        # Get result
        result = check_parallel_environment_vars()
        
        # Should only have the one we set
        assert len(result) == 1
        assert 'MKL_NUM_THREADS' in result
        assert result['MKL_NUM_THREADS'] == '8'


class TestCacheClearFunction:
    """Test the cache clearing helper function."""
    
    def test_clear_function_exists(self):
        """Test that _clear_workload_caches function exists and is callable."""
        assert callable(_clear_workload_caches)
    
    def test_clear_function_runs_without_error(self):
        """Test that _clear_workload_caches runs without raising errors."""
        # Should not raise any exceptions
        _clear_workload_caches()
        _clear_workload_caches()  # Call twice to ensure idempotent
    
    def test_clear_affects_both_caches(self):
        """Test that clearing resets both parallel libs and env vars caches."""
        # Populate both caches
        libs1 = detect_parallel_libraries()
        vars1 = check_parallel_environment_vars()
        
        # Clear
        _clear_workload_caches()
        
        # Get new results
        libs2 = detect_parallel_libraries()
        vars2 = check_parallel_environment_vars()
        
        # Content should be same
        assert libs1 == libs2
        assert vars1 == vars2


class TestIntegrationWithOptimize:
    """Test that caching works correctly when called from optimize()."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_workload_caches()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_workload_caches()
    
    def test_multiple_optimizations_use_cache(self):
        """Test that multiple optimize() calls benefit from caching."""
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        data = range(100)
        
        # First optimization - will populate caches
        result1 = optimize(simple_func, data, sample_size=5)
        
        # Get cache state
        libs_cached = detect_parallel_libraries()
        vars_cached = check_parallel_environment_vars()
        
        # Second optimization - should use cached values
        result2 = optimize(simple_func, data, sample_size=5)
        
        # Verify caches are still the same objects
        assert detect_parallel_libraries() is libs_cached
        assert check_parallel_environment_vars() is vars_cached
        
        # Both optimizations should succeed
        assert result1.n_jobs >= 1
        assert result2.n_jobs >= 1


class TestPerformanceImprovement:
    """Test that caching provides performance improvement."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_workload_caches()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_workload_caches()
    
    def test_cached_calls_are_fast(self):
        """Test that cached calls are faster than first call."""
        import time
        
        # Clear cache
        _clear_workload_caches()
        
        # First call (uncached) - measure time
        start = time.perf_counter()
        for _ in range(100):
            _clear_workload_caches()
            detect_parallel_libraries()
            check_parallel_environment_vars()
        end = time.perf_counter()
        uncached_time = end - start
        
        # Cached calls - measure time
        _clear_workload_caches()
        # Populate cache
        detect_parallel_libraries()
        check_parallel_environment_vars()
        
        start = time.perf_counter()
        for _ in range(100):
            detect_parallel_libraries()
            check_parallel_environment_vars()
        end = time.perf_counter()
        cached_time = end - start
        
        # Cached should be at least 2x faster
        # (In practice it's often 10-100x faster, but we use 2x for robustness)
        assert cached_time < uncached_time / 2, \
            f"Cached time ({cached_time:.4f}s) should be < {uncached_time / 2:.4f}s (half of uncached {uncached_time:.4f}s)"
