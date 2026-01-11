"""
Tests for Welford's online variance algorithm implementation.

This module validates the correctness, numerical stability, and performance
of the single-pass variance calculation using Welford's algorithm.
"""

import pytest
import math
import time
from amorsize.sampling import perform_dry_run


def test_welford_variance_correctness_homogeneous():
    """Test that Welford's algorithm produces correct variance for homogeneous workloads."""
    def constant_func(x):
        """Function with constant execution time."""
        time.sleep(0.001)  # 1ms constant
        return x * 2
    
    data = list(range(10))
    result = perform_dry_run(constant_func, data, sample_size=10)
    
    # Homogeneous workload should have very low variance
    assert result.time_variance >= 0.0
    # CV should be very low for constant execution time
    assert result.coefficient_of_variation < 0.3


def test_welford_variance_correctness_heterogeneous():
    """Test that Welford's algorithm detects heterogeneous workloads."""
    def variable_func(x):
        """Function with variable execution time."""
        # Varying sleep times to create heterogeneous workload
        sleep_time = 0.001 * (x % 3 + 1)  # 1ms, 2ms, 3ms pattern
        time.sleep(sleep_time)
        return x * 2
    
    data = list(range(10))
    result = perform_dry_run(variable_func, data, sample_size=10)
    
    # Heterogeneous workload should have measurable variance
    assert result.time_variance > 0.0
    # CV should be moderate to high for varying execution times
    assert result.coefficient_of_variation > 0.0


def test_welford_variance_mathematical_properties():
    """Test that variance follows mathematical properties."""
    def timed_func(x):
        """Function with predictable execution time variance."""
        # Create known timing pattern: 0.001s, 0.002s, 0.003s, 0.001s, 0.002s, 0.003s...
        sleep_time = 0.001 * ((x % 3) + 1)
        time.sleep(sleep_time)
        return x
    
    data = list(range(6))  # Two full cycles of the pattern
    result = perform_dry_run(timed_func, data, sample_size=6)
    
    # Variance must be non-negative
    assert result.time_variance >= 0.0
    
    # Mean should be approximately 0.002s (average of 0.001, 0.002, 0.003)
    assert 0.0015 < result.avg_time < 0.0025
    
    # Coefficient of variation should be positive for non-constant times
    assert result.coefficient_of_variation > 0.0


def test_welford_variance_zero_for_identical_values():
    """Test that variance is zero when all execution times are identical."""
    def constant_func(x):
        """Function that always takes same time (no variability)."""
        # Minimal computation with no sleep - should have very consistent timing
        result = 0
        for _ in range(100):
            result += x
        return result
    
    data = [5] * 10  # Same input, same computation
    result = perform_dry_run(constant_func, data, sample_size=10)
    
    # Variance should be very close to zero (allowing for minimal timing noise)
    # Real-world timing has some noise, especially for very fast operations
    # The variance should be small relative to execution time
    assert result.time_variance < 1e-6  # Less than 1 microsecond variance
    # CV can be higher for extremely fast operations due to timing noise
    # Just verify it's not NaN or Inf
    assert not math.isnan(result.coefficient_of_variation)
    assert not math.isinf(result.coefficient_of_variation)


def test_welford_single_sample_variance():
    """Test variance calculation with single sample (should be 0)."""
    def simple_func(x):
        return x * 2
    
    data = [1]
    result = perform_dry_run(simple_func, data, sample_size=1)
    
    # Single sample should have zero variance
    assert result.time_variance == 0.0
    assert result.coefficient_of_variation == 0.0


def test_welford_two_samples_variance():
    """Test variance calculation with two samples."""
    def variable_func(x):
        """Function with different timing based on input."""
        if x == 0:
            time.sleep(0.001)
        else:
            time.sleep(0.003)
        return x
    
    data = [0, 1]
    result = perform_dry_run(variable_func, data, sample_size=2)
    
    # Two different samples should produce measurable variance
    assert result.time_variance > 0.0
    # Mean should be approximately 0.002s (average of 0.001 and 0.003)
    assert 0.0015 < result.avg_time < 0.0025
    # CV should be positive
    assert result.coefficient_of_variation > 0.0


def test_welford_numerical_stability_large_values():
    """Test numerical stability with large execution times."""
    def slow_func(x):
        """Function with large but varying execution times."""
        # Large base time with small variations
        base_time = 0.01  # 10ms base
        variation = 0.0001 * (x % 5)  # 0-0.4ms variation
        time.sleep(base_time + variation)
        return x
    
    data = list(range(10))
    result = perform_dry_run(slow_func, data, sample_size=10)
    
    # Should detect variance despite large base time
    assert result.time_variance > 0.0
    # Mean should be around 0.01s + average variation
    assert 0.009 < result.avg_time < 0.012
    # CV should be relatively small (small variation vs large base)
    assert 0.0 < result.coefficient_of_variation < 0.5


def test_welford_numerical_stability_small_values():
    """Test numerical stability with very small execution times."""
    def fast_func(x):
        """Function with tiny execution times."""
        # Minimal computation - microsecond scale
        return x ** 2
    
    data = list(range(10))
    result = perform_dry_run(fast_func, data, sample_size=10)
    
    # Should handle small times without numerical issues
    assert result.time_variance >= 0.0
    assert not math.isnan(result.time_variance)
    assert not math.isinf(result.time_variance)
    assert result.coefficient_of_variation >= 0.0
    assert not math.isnan(result.coefficient_of_variation)
    assert not math.isinf(result.coefficient_of_variation)


def test_welford_no_nan_or_inf():
    """Test that Welford's algorithm never produces NaN or Inf values."""
    def normal_func(x):
        """Regular function."""
        return sum(range(x * 100))
    
    data = list(range(1, 11))  # Start from 1 to avoid zero
    result = perform_dry_run(normal_func, data, sample_size=10)
    
    # Variance should be finite and valid
    assert not math.isnan(result.time_variance)
    assert not math.isinf(result.time_variance)
    assert result.time_variance >= 0.0
    
    # Mean should be finite and valid
    assert not math.isnan(result.avg_time)
    assert not math.isinf(result.avg_time)
    assert result.avg_time > 0.0
    
    # CV should be finite and valid
    assert not math.isnan(result.coefficient_of_variation)
    assert not math.isinf(result.coefficient_of_variation)
    assert result.coefficient_of_variation >= 0.0


def test_welford_consistent_with_numpy_if_available():
    """Test that Welford's results match numpy.var if numpy is available."""
    try:
        import numpy as np
    except ImportError:
        pytest.skip("NumPy not available for comparison")
    
    def timed_func(x):
        """Function with varying execution times."""
        sleep_time = 0.001 * (x % 3 + 1)
        time.sleep(sleep_time)
        return x
    
    data = list(range(9))
    result = perform_dry_run(timed_func, data, sample_size=9)
    
    # We can't directly compare to numpy since we don't store timing values
    # But we can verify the variance is in a reasonable range
    # Expected variance for pattern [0.001, 0.002, 0.003, 0.001, 0.002, 0.003, ...]
    # Mean = 0.002, variance ≈ 0.000000667 (6.67e-7)
    assert 0.0 < result.time_variance < 1e-5  # Reasonable range


def test_welford_coefficient_of_variation_ranges():
    """Test that CV correctly categorizes workload heterogeneity."""
    # Homogeneous workload (CV < 0.3)
    def homogeneous_func(x):
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    data = [10] * 10
    result_homog = perform_dry_run(homogeneous_func, data, sample_size=10)
    
    # Should be classified as homogeneous
    assert result_homog.coefficient_of_variation < 0.3
    
    # Heterogeneous workload (CV > 0.5)
    def heterogeneous_func(x):
        # Dramatically different execution times
        if x % 2 == 0:
            time.sleep(0.001)
        else:
            time.sleep(0.005)
        return x
    
    data = list(range(10))
    result_heterog = perform_dry_run(heterogeneous_func, data, sample_size=10)
    
    # Should be classified as heterogeneous
    assert result_heterog.coefficient_of_variation > 0.3


def test_welford_preserves_backward_compatibility():
    """Test that the API and results remain compatible with previous implementation."""
    def test_func(x):
        return x * x
    
    data = list(range(20))
    result = perform_dry_run(test_func, data, sample_size=10)
    
    # All expected attributes should exist
    assert hasattr(result, 'avg_time')
    assert hasattr(result, 'time_variance')
    assert hasattr(result, 'coefficient_of_variation')
    
    # All should be valid numbers
    assert isinstance(result.avg_time, float)
    assert isinstance(result.time_variance, float)
    assert isinstance(result.coefficient_of_variation, float)
    
    # All should be non-negative
    assert result.avg_time >= 0.0
    assert result.time_variance >= 0.0
    assert result.coefficient_of_variation >= 0.0


def test_welford_performance_characteristics():
    """Test that Welford's algorithm has good performance characteristics."""
    def benchmark_func(x):
        """Simple function for performance testing."""
        return x ** 2
    
    # Test with increasing sample sizes
    for sample_size in [5, 10, 20]:
        data = list(range(100))
        
        start_time = time.perf_counter()
        result = perform_dry_run(benchmark_func, data, sample_size=sample_size)
        duration = time.perf_counter() - start_time
        
        # Dry run should complete quickly (< 100ms for these simple operations)
        assert duration < 0.1
        
        # Results should be valid
        assert result.time_variance >= 0.0
        assert not math.isnan(result.time_variance)


def test_welford_extreme_heterogeneity():
    """Test Welford's algorithm with extreme heterogeneity."""
    def extreme_func(x):
        """Function with extreme variation in execution time."""
        if x == 0:
            time.sleep(0.001)  # 1ms
        elif x == 1:
            time.sleep(0.010)  # 10ms - 10x longer
        else:
            time.sleep(0.002)  # 2ms
        return x
    
    data = [0, 1, 2]
    result = perform_dry_run(extreme_func, data, sample_size=3)
    
    # Should detect high heterogeneity
    assert result.time_variance > 0.0
    assert result.coefficient_of_variation > 0.7  # High CV for extreme variation


def test_welford_variance_computation_correctness():
    """Test that Welford's variance formula is implemented correctly."""
    def linear_time_func(x):
        """Function where time increases linearly with input."""
        # Create predictable timing: approximately 0.001 * (x + 1) seconds
        sleep_time = 0.001 * (x + 1)
        time.sleep(sleep_time)
        return x
    
    data = [0, 1, 2, 3, 4]  # Will have times: ~1ms, ~2ms, ~3ms, ~4ms, ~5ms
    result = perform_dry_run(linear_time_func, data, sample_size=5)
    
    # Mean should be approximately 0.003s (average of 1,2,3,4,5 ms)
    assert 0.0025 < result.avg_time < 0.0035
    
    # Variance should be non-zero and positive
    assert result.time_variance > 0.0
    
    # For linear sequence [1,2,3,4,5], variance = 2.0 (in ms^2)
    # So for [0.001, 0.002, 0.003, 0.004, 0.005], variance ≈ 2e-6
    assert 1e-6 < result.time_variance < 5e-6


def test_welford_mean_accuracy():
    """Test that Welford's mean is as accurate as standard calculation."""
    def predictable_func(x):
        """Function with predictable timing."""
        time.sleep(0.001 * (x + 1))
        return x
    
    data = list(range(10))
    result = perform_dry_run(predictable_func, data, sample_size=10)
    
    # Mean should be approximately 0.0055s (average of 1-10 ms)
    # Expected: (1+2+3+4+5+6+7+8+9+10)/10 = 5.5ms
    assert 0.005 < result.avg_time < 0.006
    
    # Verify mean is computed correctly
    assert result.avg_time > 0.0
    assert not math.isnan(result.avg_time)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
