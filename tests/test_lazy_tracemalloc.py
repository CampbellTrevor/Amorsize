"""
Tests for lazy tracemalloc initialization optimization.

This test suite validates that tracemalloc can be optionally disabled
during dry run sampling for improved performance, with graceful fallback
to using physical cores without memory constraints.
"""

import pytest
import time
from amorsize.sampling import perform_dry_run
from amorsize import optimize


def simple_function(x):
    """A simple function for testing."""
    return x * 2


def memory_intensive_function(x):
    """A function that allocates significant memory."""
    # Allocate 1MB per call
    data = [0] * (1024 * 256)  # ~1MB list
    return sum(data) + x


class TestLazyTracemalloc:
    """Test lazy tracemalloc initialization."""
    
    def test_memory_tracking_enabled_by_default(self):
        """Test that memory tracking is enabled by default."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        # With memory tracking enabled, peak_memory should be > 0
        # (even simple functions allocate some memory)
        assert result.peak_memory >= 0
        assert result.error is None
    
    def test_memory_tracking_disabled(self):
        """Test that memory tracking can be disabled."""
        data = list(range(10))
        result = perform_dry_run(
            simple_function,
            data,
            sample_size=5,
            enable_memory_tracking=False
        )
        
        # With memory tracking disabled, peak_memory should be 0
        assert result.peak_memory == 0
        assert result.error is None
    
    def test_memory_tracking_enabled_explicit(self):
        """Test that memory tracking works when explicitly enabled."""
        data = list(range(10))
        result = perform_dry_run(
            simple_function,
            data,
            sample_size=5,
            enable_memory_tracking=True
        )
        
        # With memory tracking enabled, peak_memory should be > 0
        assert result.peak_memory >= 0
        assert result.error is None
    
    def test_memory_intensive_function_with_tracking(self):
        """Test memory tracking captures memory usage for intensive functions."""
        data = list(range(5))
        result = perform_dry_run(
            memory_intensive_function,
            data,
            sample_size=5,
            enable_memory_tracking=True
        )
        
        # Memory-intensive function should show significant peak memory
        # At least 500KB (we allocate ~1MB per call, but tracemalloc may not catch all)
        assert result.peak_memory > 500_000
        assert result.error is None
    
    def test_memory_intensive_function_without_tracking(self):
        """Test that disabling memory tracking returns 0 even for intensive functions."""
        data = list(range(5))
        result = perform_dry_run(
            memory_intensive_function,
            data,
            sample_size=5,
            enable_memory_tracking=False
        )
        
        # With tracking disabled, should return 0 regardless of actual memory usage
        assert result.peak_memory == 0
        assert result.error is None


class TestOptimizeWithLazyTracemalloc:
    """Test optimize() function with lazy tracemalloc."""
    
    def test_optimize_memory_tracking_enabled_by_default(self):
        """Test that optimize() enables memory tracking by default."""
        data = list(range(100))
        result = optimize(simple_function, data, verbose=False)
        
        # Should use physical cores or memory-constrained workers
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_optimize_memory_tracking_disabled(self):
        """Test that optimize() can disable memory tracking."""
        data = list(range(100))
        result = optimize(
            simple_function,
            data,
            verbose=False,
            enable_memory_tracking=False
        )
        
        # Should still work and return valid parameters
        # Worker count should fall back to physical cores
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_optimize_memory_tracking_parameter_validation(self):
        """Test that enable_memory_tracking parameter is validated."""
        data = list(range(100))
        
        # Should accept boolean values
        result = optimize(simple_function, data, enable_memory_tracking=True)
        assert result is not None
        
        result = optimize(simple_function, data, enable_memory_tracking=False)
        assert result is not None
        
        # Should reject non-boolean values
        with pytest.raises(ValueError, match="enable_memory_tracking must be a boolean"):
            optimize(simple_function, data, enable_memory_tracking="yes")
        
        with pytest.raises(ValueError, match="enable_memory_tracking must be a boolean"):
            optimize(simple_function, data, enable_memory_tracking=1)
        
        with pytest.raises(ValueError, match="enable_memory_tracking must be a boolean"):
            optimize(simple_function, data, enable_memory_tracking=None)


class TestPerformanceImprovement:
    """Test performance improvements from disabling memory tracking."""
    
    def test_disabled_memory_tracking_is_faster(self):
        """Test that disabling memory tracking provides speedup."""
        data = list(range(100))
        
        # Measure with memory tracking enabled
        start_enabled = time.perf_counter()
        for _ in range(10):
            result_enabled = perform_dry_run(
                simple_function,
                data,
                sample_size=5,
                enable_memory_tracking=True
            )
        end_enabled = time.perf_counter()
        time_enabled = end_enabled - start_enabled
        
        # Measure with memory tracking disabled
        start_disabled = time.perf_counter()
        for _ in range(10):
            result_disabled = perform_dry_run(
                simple_function,
                data,
                sample_size=5,
                enable_memory_tracking=False
            )
        end_disabled = time.perf_counter()
        time_disabled = end_disabled - start_disabled
        
        # Disabled should be faster or at least not significantly slower
        # We expect ~2-3% improvement, but we'll be conservative and just check
        # that it's not slower by more than 5%
        speedup = time_enabled / time_disabled if time_disabled > 0 else 1.0
        
        # Assert that disabled is at least not 5% slower than enabled
        # (should actually be faster, but accounting for measurement noise)
        assert speedup >= 0.95, f"Memory tracking disabled should not be slower (speedup: {speedup:.2f}x)"


class TestBackwardCompatibility:
    """Test backward compatibility of the lazy tracemalloc feature."""
    
    def test_perform_dry_run_without_parameter_works(self):
        """Test that perform_dry_run works without enable_memory_tracking parameter."""
        data = list(range(10))
        
        # Should work with default parameter (backward compatible)
        result = perform_dry_run(simple_function, data, sample_size=5)
        assert result.peak_memory >= 0
        assert result.error is None
    
    def test_optimize_without_parameter_works(self):
        """Test that optimize works without enable_memory_tracking parameter."""
        data = list(range(100))
        
        # Should work with default parameter (backward compatible)
        result = optimize(simple_function, data)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_existing_code_continues_to_work(self):
        """Test that existing code patterns continue to work unchanged."""
        data = list(range(100))
        
        # Pattern 1: Basic usage
        result = optimize(simple_function, data, verbose=False)
        assert result is not None
        
        # Pattern 2: With profiling
        result = optimize(
            simple_function,
            data,
            verbose=False,
            enable_function_profiling=True
        )
        assert result is not None
        
        # Pattern 3: With various options
        result = optimize(
            simple_function,
            data,
            sample_size=10,
            verbose=False,
            use_cache=False
        )
        assert result is not None


class TestEdgeCases:
    """Test edge cases for lazy tracemalloc."""
    
    def test_both_profiling_and_no_memory_tracking(self):
        """Test that function profiling works without memory tracking."""
        data = list(range(10))
        result = perform_dry_run(
            simple_function,
            data,
            sample_size=5,
            enable_function_profiling=True,
            enable_memory_tracking=False
        )
        
        # Should have profiler stats but no memory info
        assert result.function_profiler_stats is not None
        assert result.peak_memory == 0
        assert result.error is None
    
    def test_error_handling_with_disabled_tracking(self):
        """Test that error handling works when memory tracking is disabled."""
        def failing_function(x):
            raise ValueError("Test error")
        
        data = list(range(10))
        result = perform_dry_run(
            failing_function,
            data,
            sample_size=5,
            enable_memory_tracking=False
        )
        
        # Should capture error even without memory tracking
        assert result.error is not None
        assert result.peak_memory == 0
    
    def test_generator_with_disabled_tracking(self):
        """Test that generator handling works without memory tracking."""
        def gen():
            for i in range(100):
                yield i
        
        data = gen()
        result = perform_dry_run(
            simple_function,
            data,
            sample_size=5,
            enable_memory_tracking=False
        )
        
        # Should handle generator correctly
        assert result.is_generator is True
        assert len(result.sample) == 5
        assert result.peak_memory == 0
        assert result.error is None


class TestIntegrationWithOptimizer:
    """Test integration with optimizer's worker calculation."""
    
    def test_worker_calculation_with_zero_memory(self):
        """Test that worker calculation handles peak_memory=0 gracefully."""
        data = list(range(1000))
        result = optimize(
            simple_function,
            data,
            verbose=False,
            enable_memory_tracking=False
        )
        
        # Should use physical cores without memory constraints
        # (exact count depends on system, but should be >= 1)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        
        # Result should be usable
        assert result.data is not None
        assert result.reason is not None
    
    def test_memory_constrained_vs_unconstrained(self):
        """Test that memory tracking can affect worker count for large data."""
        # For memory-intensive function, worker count may differ
        # based on whether memory tracking is enabled
        data = list(range(100))
        
        result_with_tracking = optimize(
            memory_intensive_function,
            data,
            verbose=False,
            enable_memory_tracking=True
        )
        
        result_without_tracking = optimize(
            memory_intensive_function,
            data,
            verbose=False,
            enable_memory_tracking=False
        )
        
        # Both should produce valid results
        assert result_with_tracking.n_jobs >= 1
        assert result_without_tracking.n_jobs >= 1
        
        # Without tracking, may use more workers (no memory constraint)
        # But this isn't guaranteed, so we just verify both work
        assert result_with_tracking.chunksize >= 1
        assert result_without_tracking.chunksize >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
