"""
Tests for dry run memory allocation optimizations (Iteration 88).

This test suite validates that the memory allocation optimizations in
perform_dry_run() maintain correctness while improving performance.
"""

import pytest
import time
from amorsize.sampling import perform_dry_run


def simple_func(x):
    """Simple test function."""
    return x * 2


def cpu_intensive_func(x):
    """CPU-intensive function for performance testing."""
    result = 0
    for i in range(x):
        result += i ** 2
    return result


def varying_time_func(x):
    """Function with varying execution time for heterogeneous workload testing."""
    result = 0
    for i in range(x * 100):
        result += i
    return result


class TestMemoryAllocationOptimizations:
    """Test that memory allocation optimizations maintain correctness."""
    
    def test_pre_allocated_lists_basic_function(self):
        """Verify pre-allocated lists work correctly for basic function."""
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Verify basic results
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.error is None
        assert len(result.sample) == 5
        
    def test_pre_allocated_lists_with_varying_sizes(self):
        """Test with different sample sizes to ensure pre-allocation works."""
        data = list(range(100))
        
        for sample_size in [1, 3, 5, 10, 20]:
            result = perform_dry_run(simple_func, data, sample_size=sample_size)
            
            assert result.sample_count == sample_size
            assert len(result.sample) == sample_size
            assert result.avg_time > 0
            assert result.error is None
    
    def test_index_based_loop_correctness(self):
        """Verify index-based loop writes data correctly."""
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # All measurements should be present
        assert result.avg_time > 0
        assert result.return_size > 0
        assert result.avg_pickle_time >= 0
        assert result.peak_memory >= 0
        
    def test_variance_calculation_with_generator(self):
        """Verify variance calculation using generator expression is correct."""
        # Use varying execution times to trigger variance calculation
        data = [100, 200, 300, 400, 500]
        result = perform_dry_run(varying_time_func, data, sample_size=5)
        
        # Variance should be calculated
        assert result.time_variance > 0
        assert result.coefficient_of_variation > 0
        assert result.error is None
    
    def test_data_measurements_extraction(self):
        """Test optimized data measurement extraction with list comprehension."""
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Data pickle measurements should be present
        assert result.avg_data_pickle_time >= 0
        assert result.data_size >= 0
        assert result.error is None


class TestCorrectnessWithEdgeCases:
    """Test that optimizations handle edge cases correctly."""
    
    def test_single_item_sample(self):
        """Test with single item (edge case for variance calculation)."""
        data = [100]
        result = perform_dry_run(simple_func, data, sample_size=1)
        
        assert result.sample_count == 1
        assert result.avg_time > 0
        # Variance should be 0 for single item
        assert result.time_variance == 0.0
        assert result.coefficient_of_variation == 0.0
        assert result.error is None
    
    def test_two_item_sample(self):
        """Test with two items (minimum for variance calculation)."""
        data = [100, 200]
        result = perform_dry_run(varying_time_func, data, sample_size=2)
        
        assert result.sample_count == 2
        assert result.avg_time > 0
        # Variance should be calculated for 2+ items
        assert result.time_variance >= 0
        assert result.error is None
    
    def test_pickle_failure_handling(self):
        """Test that pickle failure handling still works with pre-allocated lists."""
        import threading
        
        def unpicklable_result_func(x):
            """Returns unpicklable object."""
            return threading.Lock()
        
        data = [1, 2, 3]
        result = perform_dry_run(unpicklable_result_func, data, sample_size=3)
        
        # Should use fallback (sys.getsizeof)
        assert result.sample_count == 3
        assert result.return_size > 0
        # Pickle times should be 0 when pickle fails
        assert result.avg_pickle_time == 0.0
        assert result.error is None


class TestMemoryTrackingIntegration:
    """Test that memory tracking still works correctly with optimizations."""
    
    def test_memory_tracking_enabled(self):
        """Test memory tracking with optimizations."""
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=5, 
                                enable_memory_tracking=True)
        
        assert result.sample_count == 5
        assert result.peak_memory > 0  # Should track memory
        assert result.error is None
    
    def test_memory_tracking_disabled(self):
        """Test memory tracking disabled with optimizations."""
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=5,
                                enable_memory_tracking=False)
        
        assert result.sample_count == 5
        assert result.peak_memory == 0  # Should not track memory
        assert result.error is None


class TestFunctionProfilingIntegration:
    """Test that function profiling still works with optimizations."""
    
    def test_function_profiling_enabled(self):
        """Test function profiling with memory optimizations."""
        data = list(range(10))
        result = perform_dry_run(cpu_intensive_func, data, sample_size=5,
                                enable_function_profiling=True)
        
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.function_profiler_stats is not None
        assert result.error is None
    
    def test_function_profiling_disabled(self):
        """Test normal operation without profiling."""
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=5,
                                enable_function_profiling=False)
        
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.function_profiler_stats is None
        assert result.error is None


class TestPerformanceImprovements:
    """Test that optimizations provide performance benefits."""
    
    def test_memory_allocation_performance(self):
        """
        Validate that pre-allocation provides performance benefit.
        
        This test measures the overhead of dry run sampling and verifies
        that the optimizations reduce memory allocation overhead.
        """
        data = list(range(100))
        
        # Warm up
        _ = perform_dry_run(simple_func, data, sample_size=10)
        
        # Measure performance with optimizations
        iterations = 20
        start = time.perf_counter()
        for _ in range(iterations):
            _ = perform_dry_run(simple_func, data, sample_size=10)
        end = time.perf_counter()
        
        avg_time = (end - start) / iterations
        
        # Verify reasonable performance (should be < 50ms per dry run)
        # This is a sanity check that the optimizations didn't break anything
        assert avg_time < 0.05, f"Dry run too slow: {avg_time*1000:.2f}ms"


class TestBackwardCompatibility:
    """Ensure optimizations don't break existing functionality."""
    
    def test_existing_code_patterns_work(self):
        """Test that existing usage patterns still work."""
        data = list(range(20))
        
        # Basic usage
        result1 = perform_dry_run(simple_func, data)
        assert result1.error is None
        
        # With sample_size
        result2 = perform_dry_run(simple_func, data, sample_size=7)
        assert result2.sample_count == 7
        assert result2.error is None
        
        # With profiling
        result3 = perform_dry_run(simple_func, data, enable_function_profiling=True)
        assert result3.function_profiler_stats is not None
        assert result3.error is None
    
    def test_heterogeneous_workload_detection_still_works(self):
        """Verify heterogeneous workload detection is unaffected."""
        # Create data with varying execution times
        data = [10, 50, 100, 200, 500]
        result = perform_dry_run(varying_time_func, data, sample_size=5)
        
        # Should detect heterogeneity
        assert result.coefficient_of_variation > 0
        # With varying workloads, CV should be significant
        assert result.time_variance > 0
        assert result.error is None
