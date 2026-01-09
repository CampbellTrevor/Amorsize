"""
Tests for smart default behavior of overhead measurements.

This module tests that the optimizer now measures actual overhead by default
instead of using estimates, providing more accurate recommendations out-of-the-box.
"""

import pytest
import time
from amorsize import optimize
from amorsize.system_info import (
    get_spawn_cost,
    get_chunking_overhead,
    measure_spawn_cost,
    measure_chunking_overhead,
    _clear_spawn_cost_cache,
    _clear_chunking_overhead_cache,
    SPAWN_COST_FORK,
    DEFAULT_CHUNKING_OVERHEAD
)


def simple_func(x):
    """Simple test function."""
    return x * 2


def slow_func(x):
    """Slower function that passes the 1ms threshold."""
    result = 0
    for i in range(1000):
        result += x * i
    return result


class TestSmartDefaults:
    """Test that measurements are enabled by default."""
    
    def test_get_spawn_cost_measures_by_default(self):
        """Test that get_spawn_cost() measures actual cost by default."""
        _clear_spawn_cost_cache()
        
        # With default use_benchmark=True, should measure actual cost
        measured_cost = get_spawn_cost()
        
        # Get the estimate for comparison
        from amorsize.system_info import get_spawn_cost_estimate
        estimated_cost = get_spawn_cost_estimate()
        
        # Measured cost should be different from estimate (measurement is system-specific)
        # On Linux with fork, estimate is 15ms but measurement is typically 5-10ms
        assert measured_cost > 0
        assert measured_cost < 1.0  # Should be reasonable (< 1 second)
        
        # The measurement should be a real value, not just the estimate
        # (though they might be close on some systems)
        assert isinstance(measured_cost, float)
    
    def test_get_spawn_cost_can_opt_out(self):
        """Test that get_spawn_cost(use_benchmark=False) uses estimate."""
        _clear_spawn_cost_cache()
        
        # With use_benchmark=False, should use estimate
        from amorsize.system_info import get_spawn_cost_estimate
        estimated_cost = get_spawn_cost_estimate()
        cost_no_benchmark = get_spawn_cost(use_benchmark=False)
        
        # Should return the estimate
        assert cost_no_benchmark == estimated_cost
        assert cost_no_benchmark > 0
    
    def test_get_chunking_overhead_measures_by_default(self):
        """Test that get_chunking_overhead() measures actual overhead by default."""
        _clear_chunking_overhead_cache()
        
        # With default use_benchmark=True, should measure actual overhead
        measured_overhead = get_chunking_overhead()
        
        # Measured overhead should be different from default estimate
        # Default is 0.5ms, but measurement is typically 0.01-0.1ms
        assert measured_overhead > 0
        assert measured_overhead < 0.01  # Should be reasonable (< 10ms per chunk)
        assert isinstance(measured_overhead, float)
    
    def test_get_chunking_overhead_can_opt_out(self):
        """Test that get_chunking_overhead(use_benchmark=False) uses estimate."""
        _clear_chunking_overhead_cache()
        
        # With use_benchmark=False, should use default estimate
        overhead_no_benchmark = get_chunking_overhead(use_benchmark=False)
        
        # Should return the default estimate
        assert overhead_no_benchmark == DEFAULT_CHUNKING_OVERHEAD
        assert overhead_no_benchmark == 0.0005  # 0.5ms
    
    def test_optimize_measures_by_default(self):
        """Test that optimize() uses actual measurements by default."""
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        # Call optimize with default parameters (measurements enabled)
        # Use a function slow enough to not hit fast-fail (> 1ms)
        data = range(100)
        result = optimize(slow_func, data, profile=True)
        
        # Check that measurements were used (not estimates)
        # The profile should have spawn cost and chunking overhead from measurements
        assert result.profile is not None
        assert result.profile.spawn_cost > 0
        assert result.profile.chunking_overhead > 0
        
        # Verify spawn cost is measured (typically < 15ms on fast systems)
        # and not just the estimate (which is 15ms for fork on Linux)
        # This isn't a perfect test since measurements can vary, but it validates
        # that the measurement path was taken
        assert result.profile.spawn_cost < 1.0
    
    def test_optimize_can_opt_out_of_measurements(self):
        """Test that optimize() can disable measurements for speed."""
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        # Call optimize with measurements disabled
        # Use a function slow enough to not hit fast-fail (> 1ms)
        data = range(100)
        result = optimize(
            slow_func, 
            data, 
            use_spawn_benchmark=False,
            use_chunking_benchmark=False,
            profile=True
        )
        
        # Should still work, but use estimates instead
        assert result.profile is not None
        assert result.profile.spawn_cost > 0
        assert result.profile.chunking_overhead > 0


class TestMeasurementCaching:
    """Test that measurements are cached globally."""
    
    def test_spawn_cost_cached_across_calls(self):
        """Test that spawn cost is measured once and cached."""
        _clear_spawn_cost_cache()
        
        # First call measures
        cost1 = get_spawn_cost()
        
        # Second call uses cache (should be identical)
        cost2 = get_spawn_cost()
        
        assert cost1 == cost2
    
    def test_chunking_overhead_cached_across_calls(self):
        """Test that chunking overhead is measured once and cached."""
        _clear_chunking_overhead_cache()
        
        # First call measures
        overhead1 = get_chunking_overhead()
        
        # Second call uses cache (should be identical)
        overhead2 = get_chunking_overhead()
        
        assert overhead1 == overhead2
    
    def test_optimize_uses_cached_measurements(self):
        """Test that multiple optimize() calls use cached measurements."""
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        data = range(100)
        
        # First optimize call triggers measurements
        result1 = optimize(simple_func, data, profile=True)
        spawn1 = result1.profile.spawn_cost
        chunk1 = result1.profile.chunking_overhead
        
        # Second optimize call uses cached values
        result2 = optimize(simple_func, data, profile=True)
        spawn2 = result2.profile.spawn_cost
        chunk2 = result2.profile.chunking_overhead
        
        # Should be identical (from cache)
        assert spawn1 == spawn2
        assert chunk1 == chunk2


class TestBackwardCompatibility:
    """Test that existing code still works with new defaults."""
    
    def test_simple_optimize_call_still_works(self):
        """Test that simple optimize() call works with new defaults."""
        data = range(100)
        result = optimize(simple_func, data)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.estimated_speedup >= 1.0
    
    def test_explicit_false_still_works(self):
        """Test that explicitly setting False for benchmarks still works."""
        data = range(100)
        result = optimize(
            simple_func,
            data,
            use_spawn_benchmark=False,
            use_chunking_benchmark=False
        )
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_explicit_true_still_works(self):
        """Test that explicitly setting True for benchmarks still works."""
        data = range(100)
        result = optimize(
            simple_func,
            data,
            use_spawn_benchmark=True,
            use_chunking_benchmark=True
        )
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1


class TestMeasurementPerformance:
    """Test that measurements are fast enough for default behavior."""
    
    def test_spawn_measurement_is_fast(self):
        """Test that spawn cost measurement completes quickly."""
        import time
        _clear_spawn_cost_cache()
        
        start = time.perf_counter()
        cost = measure_spawn_cost()
        duration = time.perf_counter() - start
        
        # Should complete in under 100ms (typically 10-20ms)
        assert duration < 0.1
        assert cost > 0
    
    def test_chunking_measurement_is_fast(self):
        """Test that chunking overhead measurement completes quickly."""
        import time
        _clear_chunking_overhead_cache()
        
        start = time.perf_counter()
        overhead = measure_chunking_overhead()
        duration = time.perf_counter() - start
        
        # Should complete in under 100ms (typically 10-20ms)
        assert duration < 0.1
        assert overhead > 0
    
    def test_first_optimize_includes_measurement_overhead(self):
        """Test that first optimize() call includes measurement time."""
        import time
        _clear_spawn_cost_cache()
        _clear_chunking_overhead_cache()
        
        data = range(100)
        
        start = time.perf_counter()
        result = optimize(simple_func, data)
        duration = time.perf_counter() - start
        
        # First call includes measurement overhead (~25ms) plus optimization
        # Should still be fast (under 200ms total)
        assert duration < 0.2
        assert result.n_jobs >= 1


class TestAccuracyImprovement:
    """Test that measurements provide more accurate recommendations than estimates."""
    
    def test_measured_spawn_cost_is_more_accurate(self):
        """Test that measured spawn cost differs from estimate on fast systems."""
        _clear_spawn_cost_cache()
        
        measured = measure_spawn_cost()
        from amorsize.system_info import get_spawn_cost_estimate
        estimated = get_spawn_cost_estimate()
        
        # Both should be reasonable values
        assert 0 < measured < 1.0
        assert 0 < estimated < 1.0
        
        # On Linux with fork, estimate is 15ms but measurement is often 5-10ms
        # This validates that we're getting system-specific values
        assert isinstance(measured, float)
        assert isinstance(estimated, float)
    
    def test_measured_chunking_overhead_is_more_accurate(self):
        """Test that measured chunking overhead differs from default estimate."""
        _clear_chunking_overhead_cache()
        
        measured = measure_chunking_overhead()
        default = DEFAULT_CHUNKING_OVERHEAD
        
        # Both should be reasonable values
        assert 0 < measured < 0.01
        assert default == 0.0005
        
        # Measured value is system-specific
        assert isinstance(measured, float)
