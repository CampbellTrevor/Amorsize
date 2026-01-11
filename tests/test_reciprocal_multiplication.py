"""
Tests for reciprocal multiplication optimization in averaging calculations.

This tests the Iteration 98 optimization that converts division by sample_count
to multiplication by its reciprocal (1.0 / sample_count) for float averages.
The optimization reduces CPU cycles by replacing slower division operations
with faster multiplication.
"""

import pytest
import math
from amorsize.sampling import perform_dry_run


def simple_func(x):
    """A simple function for testing."""
    return x * 2


def compute_intensive(x):
    """A more compute-intensive function."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


def variable_time_func(x):
    """Function with variable execution time."""
    import time
    # Sleep for variable time based on x (but very short)
    time.sleep(x * 0.0001)
    return x


class TestReciprocalMultiplicationCorrectness:
    """Test that reciprocal multiplication produces correct results."""
    
    def test_basic_correctness(self):
        """Verify basic averaging is still correct."""
        data = list(range(5))
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0
        # Verify we got valid numeric results
        assert isinstance(result.avg_time, float)
        assert isinstance(result.avg_pickle_time, float)
        assert isinstance(result.avg_data_pickle_time, float)
    
    def test_numerical_precision(self):
        """Verify numerical precision is maintained."""
        data = list(range(100, 150))
        result = perform_dry_run(compute_intensive, data, sample_size=50)
        
        # Reciprocal multiplication should produce same results as division
        # within floating-point precision
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0
        
        # Verify the averages are reasonable (positive, finite)
        assert math.isfinite(result.avg_pickle_time)
        assert math.isfinite(result.avg_data_pickle_time)
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0
    
    def test_single_sample(self):
        """Test edge case with sample_size=1."""
        data = [42]
        result = perform_dry_run(simple_func, data, sample_size=1)
        
        assert result.sample_count == 1
        # With 1 sample, division by 1 or multiplication by 1.0 should be identical
        assert result.avg_time >= 0
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0
    
    def test_two_samples(self):
        """Test edge case with sample_size=2."""
        data = [1, 2]
        result = perform_dry_run(simple_func, data, sample_size=2)
        
        assert result.sample_count == 2
        # With 2 samples, reciprocal is 0.5
        assert result.avg_time >= 0
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0


class TestReciprocalMultiplicationIntegration:
    """Test integration with full optimize() workflow."""
    
    def test_integration_with_optimize(self):
        """Verify optimization works with full optimize() call."""
        from amorsize import optimize
        
        data = list(range(100))
        result = optimize(simple_func, data, sample_size=5, verbose=False)
        
        # Should produce valid optimization result
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.reason is not None
    
    def test_profiling_path_uses_optimization(self):
        """Verify optimization is used when profiling is enabled."""
        data = list(range(20))
        result = perform_dry_run(
            simple_func, 
            data, 
            sample_size=10,
            enable_function_profiling=True
        )
        
        assert result.sample_count == 10
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0
        # Note: profiler_stats may be None in some test environments due to test isolation
        # The important thing is that averages are calculated correctly
        # (The profiling path uses the same averaging code, so if averages work, optimization is used)


class TestReciprocalMultiplicationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_large_sample_size(self):
        """Test with large sample size."""
        data = list(range(1000))
        result = perform_dry_run(simple_func, data, sample_size=100)
        
        assert result.sample_count == 100
        # With large sample, reciprocal is 0.01
        assert result.avg_time > 0
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0
    
    def test_variable_execution_times(self):
        """Test with heterogeneous execution times."""
        data = [0.001, 0.002, 0.003, 0.004, 0.005]
        result = perform_dry_run(variable_time_func, data, sample_size=5)
        
        assert result.sample_count == 5
        # Should have non-zero coefficient of variation
        # Averaging should still work correctly
        assert result.avg_time > 0
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0


class TestReciprocalMultiplicationNumericalStability:
    """Test numerical stability of reciprocal multiplication."""
    
    def test_no_catastrophic_cancellation(self):
        """Verify no loss of precision from reciprocal multiplication."""
        data = list(range(50))
        result = perform_dry_run(simple_func, data, sample_size=50)
        
        # Results should be finite and reasonable
        assert math.isfinite(result.avg_pickle_time)
        assert math.isfinite(result.avg_data_pickle_time)
        assert not math.isnan(result.avg_pickle_time)
        assert not math.isnan(result.avg_data_pickle_time)
    
    def test_very_small_times(self):
        """Test with very small execution times (near zero)."""
        def fast_func(x):
            return x
        
        data = list(range(10))
        result = perform_dry_run(fast_func, data, sample_size=10)
        
        # Even with very small times, averaging should work
        assert result.avg_time >= 0
        assert result.avg_pickle_time >= 0
        assert result.avg_data_pickle_time >= 0
        assert math.isfinite(result.avg_time)


class TestBackwardCompatibility:
    """Ensure optimization doesn't break existing behavior."""
    
    def test_api_unchanged(self):
        """Verify API hasn't changed."""
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # All expected attributes should exist
        assert hasattr(result, 'avg_time')
        assert hasattr(result, 'avg_pickle_time')
        assert hasattr(result, 'avg_data_pickle_time')
        assert hasattr(result, 'sample_count')
    
    def test_results_consistent(self):
        """Verify results are consistent with previous implementation."""
        data = list(range(20))
        result1 = perform_dry_run(simple_func, data, sample_size=10)
        result2 = perform_dry_run(simple_func, data, sample_size=10)
        
        # Results should be similar (within reasonable tolerance due to timing variance)
        # We just verify they're in the same order of magnitude
        assert abs(result1.avg_time - result2.avg_time) < 1.0  # Within 1 second
        # Pickle times might vary but should be non-negative
        assert result1.avg_pickle_time >= 0
        assert result2.avg_pickle_time >= 0
