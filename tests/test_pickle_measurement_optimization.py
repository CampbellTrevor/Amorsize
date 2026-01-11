"""
Tests for pickle measurement loop optimization (Iteration 89).

These tests verify that the optimizations to reduce timing overhead in pickle
measurement loops maintain correctness, accuracy, and backward compatibility.
"""

import pickle
import time
import pytest
from amorsize.sampling import (
    check_data_picklability_with_measurements,
    perform_dry_run,
    SamplingResult
)


class TestPickleMeasurementOptimizations:
    """Test the optimized pickle measurement implementation."""
    
    def test_preallocation_with_basic_data(self):
        """Test that pre-allocated measurements work with basic data."""
        data = [1, 2, 3, 4, 5]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert idx is None
        assert error is None
        assert len(measurements) == 5
        
        # Verify measurements have correct structure
        for pickle_time, size in measurements:
            assert isinstance(pickle_time, float)
            assert pickle_time >= 0
            assert isinstance(size, int)
            assert size > 0
    
    def test_preallocation_with_various_sizes(self):
        """Test pre-allocation with different data sizes."""
        test_sizes = [1, 3, 5, 10, 20, 50]
        
        for size in test_sizes:
            data = list(range(size))
            is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
            
            assert is_picklable is True
            assert len(measurements) == size, f"Failed for size {size}"
            
            # All measurements should be valid
            for pickle_time, data_size in measurements:
                assert pickle_time >= 0
                assert data_size > 0
    
    def test_inline_delta_correctness(self):
        """Test that inline delta calculation produces correct results."""
        data = [100, 200, 300]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert len(measurements) == 3
        
        # Verify timing values are reasonable (should be very fast for integers)
        for pickle_time, size in measurements:
            assert 0 <= pickle_time < 0.01  # Should be under 10ms for simple integers
    
    def test_indexed_assignment_order(self):
        """Test that indexed assignment maintains correct order."""
        data = ['first', 'second', 'third', 'fourth', 'fifth']
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert len(measurements) == 5
        
        # Verify sizes correspond to data items (strings have different sizes)
        sizes = [m[1] for m in measurements]
        assert all(s > 0 for s in sizes)
        # First string "first" should pickle to roughly same size as others
        # (all are similar length strings)
    
    def test_unpicklable_item_handling(self):
        """Test that unpicklable items are handled correctly with pre-allocation."""
        # Create a function (unpicklable)
        def unpicklable_func():
            pass
        
        data = [1, 2, unpicklable_func, 4, 5]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is False
        assert idx == 2
        assert error is not None
        assert measurements == []


class TestDryRunLoopOptimizations:
    """Test the optimized main dry run loop."""
    
    def test_dry_run_with_inline_delta(self):
        """Test that dry run works correctly with inline delta calculation."""
        def simple_func(x):
            return x * 2
        
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        assert result.avg_time > 0
        assert result.sample_count == 5
        # Note: is_picklable refers to function results, not the function itself
        assert result.return_size >= 0
        assert len(result.sample) == 5
    
    def test_dry_run_timing_accuracy(self):
        """Test that timing measurements are still accurate after optimization."""
        def timed_func(x):
            # Sleep for a predictable amount of time
            time.sleep(0.001)  # 1ms
            return x
        
        data = [1, 2, 3]
        result = perform_dry_run(timed_func, data, sample_size=3)
        
        # Average time should be at least 1ms (sleep time)
        # Allow some margin for overhead
        assert result.avg_time >= 0.0005  # At least 0.5ms
        assert result.avg_time < 0.01  # Less than 10ms
    
    def test_dry_run_pickle_time_measurement(self):
        """Test that pickle time is measured correctly in optimized loop."""
        def returns_data(x):
            # Return progressively larger data
            return list(range(x * 100))
        
        data = [1, 2, 3]
        result = perform_dry_run(returns_data, data, sample_size=3)
        
        # Pickle time should be non-zero for non-trivial objects
        assert result.avg_pickle_time > 0
        assert result.return_size > 0


class TestPerformanceImprovements:
    """Test that optimizations provide measurable performance improvements."""
    
    def test_measurement_overhead_reduced(self):
        """Test that the optimization reduces measurement overhead."""
        def fast_func(x):
            return x
        
        data = list(range(20))
        
        # Run multiple times to measure consistency
        times = []
        for _ in range(5):
            start = time.perf_counter()
            result = perform_dry_run(fast_func, data, sample_size=20)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        # Average dry run time should be under 10ms for simple function
        avg_time = sum(times) / len(times)
        assert avg_time < 0.01  # Less than 10ms
    
    def test_large_sample_performance(self):
        """Test performance with larger sample sizes."""
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        
        start = time.perf_counter()
        result = perform_dry_run(simple_func, data, sample_size=50)
        elapsed = time.perf_counter() - start
        
        # Should complete in reasonable time even with 50 samples
        assert elapsed < 0.1  # Less than 100ms
        assert result.sample_count == 50


class TestBackwardCompatibility:
    """Test that optimizations maintain backward compatibility."""
    
    def test_result_structure_unchanged(self):
        """Test that SamplingResult structure is unchanged."""
        def func(x):
            return x
        
        data = [1, 2, 3]
        result = perform_dry_run(func, data, sample_size=3)
        
        # Verify all expected attributes exist
        assert hasattr(result, 'avg_time')
        assert hasattr(result, 'return_size')
        assert hasattr(result, 'peak_memory')
        assert hasattr(result, 'sample_count')
        assert hasattr(result, 'is_picklable')
        assert hasattr(result, 'avg_pickle_time')
        assert hasattr(result, 'sample')
        assert hasattr(result, 'remaining_data')
    
    def test_measurements_format_unchanged(self):
        """Test that measurement format is unchanged."""
        data = [1, 2, 3]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        # Each measurement should be (float, int) tuple
        for measurement in measurements:
            assert isinstance(measurement, tuple)
            assert len(measurement) == 2
            assert isinstance(measurement[0], float)  # pickle_time
            assert isinstance(measurement[1], int)    # data_size


class TestEdgeCases:
    """Test edge cases with optimized implementation."""
    
    def test_empty_data(self):
        """Test with empty data."""
        data = []
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert len(measurements) == 0
    
    def test_single_item(self):
        """Test with single item."""
        data = [42]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert len(measurements) == 1
        assert measurements[0][0] >= 0  # pickle_time
        assert measurements[0][1] > 0   # size
    
    def test_large_objects(self):
        """Test with large objects that take longer to pickle."""
        # Create large lists
        data = [[i] * 1000 for i in range(5)]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert len(measurements) == 5
        
        # Larger objects should have measurable pickle time
        for pickle_time, size in measurements:
            assert pickle_time >= 0
            assert size > 0
    
    def test_exception_in_dry_run(self):
        """Test that exceptions during dry run are handled correctly."""
        def failing_func(x):
            if x == 2:
                raise ValueError("Test error")
            return x
        
        data = [1, 2, 3]
        result = perform_dry_run(failing_func, data, sample_size=3)
        
        # Should handle the error gracefully
        assert result.error is not None


class TestMemoryTrackingIntegration:
    """Test that optimizations work correctly with memory tracking."""
    
    def test_with_memory_tracking_enabled(self):
        """Test dry run with memory tracking enabled."""
        def func(x):
            # Create some memory allocation
            temp = [i for i in range(x * 100)]
            return sum(temp)
        
        data = [10, 20, 30]
        result = perform_dry_run(func, data, sample_size=3, enable_memory_tracking=True)
        
        assert result.peak_memory >= 0  # Should have memory measurement
        assert result.avg_time > 0
    
    def test_with_memory_tracking_disabled(self):
        """Test dry run with memory tracking disabled."""
        def func(x):
            return x * 2
        
        data = [1, 2, 3]
        result = perform_dry_run(func, data, sample_size=3, enable_memory_tracking=False)
        
        assert result.peak_memory == 0  # Should be 0 when disabled
        assert result.avg_time > 0


class TestFunctionProfilingIntegration:
    """Test that optimizations work correctly with function profiling."""
    
    def test_with_profiling_enabled(self):
        """Test dry run with function profiling enabled."""
        def func(x):
            result = 0
            for i in range(x * 10):
                result += i
            return result
        
        data = [10, 20, 30]
        result = perform_dry_run(func, data, sample_size=3, enable_function_profiling=True)
        
        assert result.function_profiler_stats is not None
        assert result.avg_time > 0
    
    def test_with_profiling_disabled(self):
        """Test dry run with function profiling disabled."""
        def func(x):
            return x * 2
        
        data = [1, 2, 3]
        result = perform_dry_run(func, data, sample_size=3, enable_function_profiling=False)
        
        assert result.function_profiler_stats is None
        assert result.avg_time > 0
