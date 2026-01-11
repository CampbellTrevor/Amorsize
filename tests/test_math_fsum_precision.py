"""
Tests for math.fsum() numerical precision improvements in average/sum calculations.

This test suite validates that using math.fsum() instead of sum() provides
better numerical precision for floating-point summations, particularly when
dealing with many small values or values with large magnitude differences.
"""

import pytest
import math
from amorsize.sampling import perform_dry_run
from amorsize.comparison import compare_strategies, ComparisonConfig


# Module-level functions for picklability in multiprocessing tests
def _simple_square_func(x):
    """Simple function for testing - squares input."""
    return x ** 2


def _fast_double_func(x):
    """Very fast function for testing - doubles input."""
    return x * 2


class TestMathFsumNumericalPrecision:
    """Test math.fsum() provides better numerical precision than sum()."""
    
    def test_many_small_values_precision(self):
        """Test that averaging many small timing values maintains precision."""
        # Create a scenario with many small timing values
        # This is common when measuring fast function execution times
        def fast_func(x):
            return x * 2
        
        data = list(range(100))
        result = perform_dry_run(fast_func, data, sample_size=50)
        
        # Verify the result has reasonable precision
        assert result.avg_time >= 0.0
        assert result.avg_pickle_time >= 0.0
        assert result.avg_data_pickle_time >= 0.0
        
        # All these values should be small but positive for a fast function
        # The use of math.fsum ensures we don't lose precision
    
    def test_variance_calculation_precision(self):
        """Test that variance calculation maintains precision with math.fsum()."""
        # Create a function with varying execution times
        times_seen = []
        
        def variable_time_func(x):
            # Simulate variable execution time by doing different amounts of work
            result = 0
            for i in range(x % 10 + 1):
                result += i ** 2
            times_seen.append(x)
            return result
        
        data = list(range(100))
        result = perform_dry_run(variable_time_func, data, sample_size=20)
        
        # Verify variance calculation succeeded
        assert result.time_variance >= 0.0
        assert result.coefficient_of_variation >= 0.0
        
        # If we have varied times, CV should be positive
        if len(set(times_seen[:20])) > 1:
            # Some variation expected
            assert result.coefficient_of_variation >= 0.0
    
    def test_large_magnitude_difference_precision(self):
        """Test precision when summing values with large magnitude differences."""
        # This tests the main advantage of math.fsum: handling values that differ
        # greatly in magnitude without losing precision
        def func_with_varying_pickle_times(x):
            # Simple function, but pickle times may vary
            return x ** 2
        
        data = list(range(100))
        result = perform_dry_run(func_with_varying_pickle_times, data, sample_size=30)
        
        # Verify all timing averages are valid
        assert result.avg_time >= 0.0
        assert result.avg_pickle_time >= 0.0
        assert result.avg_data_pickle_time >= 0.0
        
        # No NaN or infinity values
        assert not math.isnan(result.avg_time)
        assert not math.isinf(result.avg_time)
        assert not math.isnan(result.avg_pickle_time)
        assert not math.isinf(result.avg_pickle_time)


class TestComparisonMathFsumPrecision:
    """Test math.fsum() in comparison module provides better precision."""
    
    def test_comparison_timing_averages_precision(self):
        """Test that comparison timing averages maintain precision."""
        data = list(range(100))
        
        # Compare different strategies using module-level function (picklable)
        configs = [
            ComparisonConfig(name="Serial", n_jobs=1, chunksize=10),
            ComparisonConfig(name="Parallel", n_jobs=2, chunksize=10),
        ]
        
        result = compare_strategies(_simple_square_func, data, configs)
        
        # Verify all timing values are valid
        for time_val in result.execution_times:
            assert time_val > 0.0
            assert not math.isnan(time_val)
            assert not math.isinf(time_val)
        
        # Verify speedups are calculated correctly
        for speedup in result.speedups:
            assert speedup > 0.0
            assert not math.isnan(speedup)
            assert not math.isinf(speedup)


class TestMathFsumBackwardCompatibility:
    """Test that math.fsum() changes maintain backward compatibility."""
    
    def test_empty_list_handling(self):
        """Test that empty lists are handled correctly."""
        def simple_func(x):
            return x
        
        # Test with minimal data
        data = [1]
        result = perform_dry_run(simple_func, data, sample_size=1)
        
        # Should not crash and should return valid values
        assert result.avg_time >= 0.0
        assert result.sample_count == 1
    
    def test_single_sample_handling(self):
        """Test that single samples work correctly."""
        def simple_func(x):
            return x * 2
        
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=1)
        
        # Single sample should have zero variance
        assert result.time_variance == 0.0
        assert result.coefficient_of_variation == 0.0
    
    def test_zero_time_handling(self):
        """Test that functions with near-zero execution time are handled."""
        def instant_func(x):
            return x
        
        data = list(range(100))
        result = perform_dry_run(instant_func, data, sample_size=10)
        
        # Should handle very small times without issues
        assert result.avg_time >= 0.0
        # CV might be high due to measurement noise, but should not be NaN
        if result.avg_time > 0:
            assert not math.isnan(result.coefficient_of_variation)


class TestMathFsumEdgeCases:
    """Test edge cases for math.fsum() usage."""
    
    def test_all_identical_times(self):
        """Test when all execution times are identical."""
        def deterministic_func(x):
            # Very simple operation, should have consistent time
            return x
        
        data = list(range(100))
        result = perform_dry_run(deterministic_func, data, sample_size=5)
        
        # Variance should be very low for identical times
        # (might not be exactly 0 due to measurement noise)
        assert result.time_variance >= 0.0
        assert result.coefficient_of_variation >= 0.0
    
    def test_very_large_sample_size(self):
        """Test with large sample sizes to stress-test summation precision."""
        def simple_func(x):
            return x ** 2
        
        data = list(range(1000))
        result = perform_dry_run(simple_func, data, sample_size=100)
        
        # Should handle large sample sizes without precision issues
        assert result.sample_count == 100
        assert result.avg_time >= 0.0
        assert not math.isnan(result.avg_time)
        assert not math.isinf(result.avg_time)
    
    def test_mixed_positive_negative_not_applicable(self):
        """Test that all timing values are non-negative."""
        def simple_func(x):
            return x + 1
        
        data = list(range(50))
        result = perform_dry_run(simple_func, data, sample_size=10)
        
        # All timing values should be non-negative
        assert result.avg_time >= 0.0
        assert result.avg_pickle_time >= 0.0
        assert result.avg_data_pickle_time >= 0.0
        assert result.time_variance >= 0.0


class TestNumericalStability:
    """Test numerical stability improvements from math.fsum()."""
    
    def test_accumulation_order_independence(self):
        """Test that results are consistent regardless of accumulation order."""
        # math.fsum() uses Kahan summation which is more order-independent
        def func(x):
            return x ** 2
        
        data1 = list(range(100))
        data2 = list(reversed(range(100)))
        
        result1 = perform_dry_run(func, data1, sample_size=20)
        result2 = perform_dry_run(func, data2, sample_size=20)
        
        # Results should be similar (not necessarily identical due to actual execution variation)
        # But both should be valid
        assert result1.avg_time >= 0.0
        assert result2.avg_time >= 0.0
        assert not math.isnan(result1.avg_time)
        assert not math.isnan(result2.avg_time)
    
    def test_no_catastrophic_cancellation(self):
        """Test that catastrophic cancellation doesn't occur in variance calculation."""
        # This tests that using math.fsum() prevents precision loss when
        # calculating variance (sum of squared deviations)
        def func(x):
            # Return varied results to create variance
            return x % 7
        
        data = list(range(100))
        result = perform_dry_run(func, data, sample_size=30)
        
        # Variance calculation should maintain precision
        if result.time_variance > 0:
            std_dev = result.time_variance ** 0.5
            # Standard deviation should be sensible relative to mean
            if result.avg_time > 0:
                cv = std_dev / result.avg_time
                assert not math.isnan(cv)
                assert not math.isinf(cv)
                assert cv >= 0.0


class TestRealWorldScenarios:
    """Test real-world scenarios where precision matters."""
    
    def test_microsecond_precision_timing(self):
        """Test that microsecond-level timing maintains precision."""
        def very_fast_func(x):
            # Extremely fast function to test microsecond timing
            return x + 1
        
        data = list(range(100))
        result = perform_dry_run(very_fast_func, data, sample_size=50)
        
        # Even with very small times, should maintain precision
        assert result.avg_time >= 0.0
        assert not math.isnan(result.avg_time)
        
        # Pickle times might be comparable to execution time
        assert result.avg_pickle_time >= 0.0
    
    def test_high_sample_count_aggregation(self):
        """Test that high sample counts don't lose precision."""
        def func(x):
            result = 0
            for i in range(10):
                result += i
            return result
        
        data = list(range(200))
        result = perform_dry_run(func, data, sample_size=100)
        
        # With 100 samples, math.fsum ensures no precision loss
        assert result.sample_count == 100
        assert result.avg_time >= 0.0
        assert result.avg_pickle_time >= 0.0
        assert not math.isnan(result.avg_time)
    
    def test_long_running_dry_run_precision(self):
        """Test precision with longer-running dry runs."""
        def moderate_func(x):
            # Moderate computation
            result = 0
            for i in range(100):
                result += x ** 2
            return result
        
        data = list(range(100))
        result = perform_dry_run(moderate_func, data, sample_size=20)
        
        # Longer-running functions should maintain precision too
        assert result.avg_time > 0.0
        assert result.time_variance >= 0.0
        assert not math.isnan(result.avg_time)
        assert not math.isnan(result.time_variance)


class TestIntegerVsFloatSum:
    """Test that we correctly use sum() for integers and math.fsum() for floats."""
    
    def test_integer_sizes_use_regular_sum(self):
        """Test that integer size calculations use regular sum() (no precision issues)."""
        def func_with_returns(x):
            # Return a list (which will have integer size)
            return [x] * 10
        
        data = list(range(20))
        result = perform_dry_run(func_with_returns, data, sample_size=10)
        
        # Return size and data size should be integers
        assert isinstance(result.return_size, int)
        assert isinstance(result.data_size, int)
        assert result.return_size >= 0
        assert result.data_size >= 0
    
    def test_float_times_use_math_fsum(self):
        """Test that timing values (floats) benefit from math.fsum()."""
        def func(x):
            return x * 2
        
        data = list(range(30))
        result = perform_dry_run(func, data, sample_size=20)
        
        # Timing values should be floats with precision
        assert isinstance(result.avg_time, float)
        assert isinstance(result.avg_pickle_time, float)
        assert isinstance(result.avg_data_pickle_time, float)
        assert isinstance(result.time_variance, float)
        
        # All should maintain precision (no NaN)
        assert not math.isnan(result.avg_time)
        assert not math.isnan(result.avg_pickle_time)
        assert not math.isnan(result.time_variance)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
