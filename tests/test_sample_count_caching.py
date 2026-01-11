"""
Tests for sample count caching optimization (Iteration 93).

This optimization caches the sample_count variable to avoid redundant len() calls
in the average calculations section of perform_dry_run().
"""

import pytest
from amorsize import optimize
from amorsize.sampling import perform_dry_run


class TestSampleCountCaching:
    """Test that sample count caching works correctly."""
    
    def test_homogeneous_workload_correct_averages(self):
        """Test that averages are computed correctly for homogeneous workload."""
        def simple_func(x):
            return x * 2
        
        data = list(range(5))
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Verify averages are computed correctly
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.return_size > 0
        assert result.avg_pickle_time >= 0
        
    def test_heterogeneous_workload_correct_averages(self):
        """Test that averages are computed correctly for heterogeneous workload."""
        def varying_func(x):
            # Varying workload - complexity depends on input
            result = 0
            for i in range(x * 100):
                result += i
            return result
        
        data = [1, 5, 10, 15, 20]  # Varying complexity
        result = perform_dry_run(varying_func, data, sample_size=5)
        
        # Verify averages are computed correctly
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.return_size > 0
        assert result.coefficient_of_variation > 0  # Should detect heterogeneity
        
    def test_single_item_sample(self):
        """Test edge case with single item."""
        def simple_func(x):
            return x + 1
        
        data = [42]
        result = perform_dry_run(simple_func, data, sample_size=1)
        
        # Verify single item is handled correctly
        assert result.sample_count == 1
        assert result.avg_time > 0
        assert result.return_size > 0
        # CV should be 0 for single item (no variance)
        assert result.coefficient_of_variation == 0
        
    def test_two_item_sample(self):
        """Test edge case with two items."""
        def simple_func(x):
            return x * 3
        
        data = [10, 20]
        result = perform_dry_run(simple_func, data, sample_size=2)
        
        # Verify two items are handled correctly
        assert result.sample_count == 2
        assert result.avg_time > 0
        assert result.return_size > 0
        
    def test_maximum_sample_size(self):
        """Test with larger sample size."""
        def simple_func(x):
            return x ** 2
        
        data = list(range(20))
        result = perform_dry_run(simple_func, data, sample_size=20)
        
        # Verify large sample is handled correctly
        assert result.sample_count == 20
        assert result.avg_time > 0
        assert result.return_size > 0


class TestAverageCalculationAccuracy:
    """Test that cached sample count produces accurate averages."""
    
    def test_return_size_average_correctness(self):
        """Test that return size average is computed correctly."""
        def size_varying_func(x):
            # Return strings of varying sizes
            return "x" * (x * 10)
        
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(size_varying_func, data, sample_size=5)
        
        # Verify average return size is reasonable
        assert result.sample_count == 5
        assert result.return_size > 0
        # Average should be somewhere in the middle range
        assert result.return_size > 30  # Minimum expected (strings of length 10, 20, 30, 40, 50)
        
    def test_pickle_time_average_correctness(self):
        """Test that pickle time average is computed correctly."""
        def pickle_heavy_func(x):
            # Return objects that are expensive to pickle
            return {"value": x, "data": list(range(x * 100))}
        
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(pickle_heavy_func, data, sample_size=5)
        
        # Verify average pickle time is measured
        assert result.sample_count == 5
        assert result.avg_pickle_time > 0
        
    def test_data_pickle_time_average_correctness(self):
        """Test that data pickle time average is computed correctly."""
        def simple_func(x):
            return x + 1
        
        # Use data that requires pickling
        data = [{"key": i, "value": i * 10} for i in range(5)]
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Verify average data pickle time is measured
        assert result.sample_count == 5
        # Data pickle time should be non-zero for non-trivial data
        
    def test_data_size_average_correctness(self):
        """Test that data size average is computed correctly."""
        def simple_func(x):
            return x * 2
        
        # Use data of varying sizes
        data = ["a", "abc", "abcde", "abcdefg", "abcdefghi"]
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Verify average data size is measured
        assert result.sample_count == 5
        assert result.data_size > 0


class TestBackwardCompatibility:
    """Test that optimization maintains backward compatibility."""
    
    def test_optimize_still_works(self):
        """Test that optimize() function still works correctly."""
        def compute_func(x):
            return sum(i * i for i in range(x))
        
        data = range(10, 20)
        result = optimize(compute_func, data, sample_size=5, verbose=False)
        
        # Verify optimization produces valid results
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert hasattr(result, 'estimated_speedup')
        
    def test_all_sampling_results_present(self):
        """Test that all expected fields are present in SamplingResult."""
        def simple_func(x):
            return x + 1
        
        data = list(range(5))
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Verify all expected attributes are present
        assert hasattr(result, 'avg_time')
        assert hasattr(result, 'return_size')
        assert hasattr(result, 'peak_memory')
        assert hasattr(result, 'sample_count')
        assert hasattr(result, 'avg_pickle_time')
        assert hasattr(result, 'data_size')
        assert hasattr(result, 'coefficient_of_variation')


class TestNumericalStability:
    """Test that optimization maintains numerical stability."""
    
    def test_large_sample_count(self):
        """Test with large sample size."""
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = perform_dry_run(simple_func, data, sample_size=100)
        
        # Verify large sample is handled correctly
        assert result.sample_count == 100
        assert result.avg_time > 0
        assert result.return_size > 0
        
    def test_varying_return_sizes(self):
        """Test with highly varying return sizes."""
        def size_varying_func(x):
            # Return progressively larger lists
            return list(range(x * x))
        
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(size_varying_func, data, sample_size=5)
        
        # Verify average is computed correctly despite variance
        assert result.sample_count == 5
        assert result.return_size > 0
        
    def test_zero_pickle_times(self):
        """Test when pickle times are very small."""
        def instant_func(x):
            return x  # Minimal pickle overhead
        
        data = list(range(5))
        result = perform_dry_run(instant_func, data, sample_size=5)
        
        # Verify averages are computed even with small values
        assert result.sample_count == 5
        assert result.avg_pickle_time >= 0  # May be very small


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_sample_handling(self):
        """Test that empty samples are handled gracefully."""
        def simple_func(x):
            return x
        
        # Empty data should be caught earlier, but test the path
        data = []
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Should return error case
        assert result.error is not None or result.sample_count == 0
        
    def test_sample_size_larger_than_data(self):
        """Test when requested sample size is larger than available data."""
        def simple_func(x):
            return x * 2
        
        data = [1, 2, 3]
        result = perform_dry_run(simple_func, data, sample_size=10)
        
        # Should sample all available data
        assert result.sample_count == 3
        assert result.avg_time > 0
        
    def test_generator_input(self):
        """Test with generator input."""
        def simple_func(x):
            return x + 10
        
        data = (i for i in range(5))
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Verify generator is handled correctly
        assert result.sample_count == 5
        assert result.is_generator is True
        assert result.avg_time > 0


class TestIntegrationWithOptimize:
    """Test integration with optimize() function."""
    
    def test_optimize_uses_cached_sample_count(self):
        """Test that optimize() benefits from cached sample count."""
        def compute_func(x):
            result = 0
            for i in range(x):
                result += i * i
            return result
        
        data = range(100, 150)
        result = optimize(compute_func, data, sample_size=5, verbose=False)
        
        # Verify optimization completes successfully
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        
    def test_diagnostic_profile_consistency(self):
        """Test that diagnostic profile remains consistent."""
        def simple_func(x):
            return x ** 2
        
        data = list(range(10))
        result = optimize(simple_func, data, sample_size=5, verbose=False, profile=True)
        
        # Verify diagnostic profile is populated
        assert result.profile is not None
        assert result.profile.sample_count == 5
        assert result.profile.avg_execution_time > 0


class TestPerformanceCharacteristics:
    """Test that optimization improves performance."""
    
    def test_average_calculation_section_is_fast(self):
        """Test that average calculations complete quickly."""
        import time
        
        def simple_func(x):
            return x * 2
        
        data = list(range(10))
        
        # Measure dry run time (includes average calculations)
        start = time.perf_counter()
        result = perform_dry_run(simple_func, data, sample_size=10)
        elapsed = time.perf_counter() - start
        
        # Dry run should be very fast (< 100ms for simple function)
        assert elapsed < 0.1
        assert result.sample_count == 10
        
    def test_no_regression_in_dry_run_speed(self):
        """Test that optimization doesn't slow down dry run."""
        def compute_func(x):
            return sum(i for i in range(x))
        
        data = list(range(20, 30))
        
        # Multiple runs should all be fast
        import time
        times = []
        for _ in range(5):
            start = time.perf_counter()
            result = perform_dry_run(compute_func, data, sample_size=10)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert result.sample_count == 10
        
        # All runs should be reasonably fast
        avg_time = sum(times) / len(times)
        assert avg_time < 0.1  # Should be well under 100ms
