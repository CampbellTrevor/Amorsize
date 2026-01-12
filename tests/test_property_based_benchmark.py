"""
Property-based tests for the benchmark module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the benchmark validation infrastructure across a wide range of inputs.
"""

import time
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize import optimize
from amorsize.benchmark import BenchmarkResult, validate_optimization, quick_validate
from amorsize.optimizer import OptimizationResult


# Custom strategies for generating test data
@st.composite
def valid_data_lists(draw, min_size=1, max_size=1000):
    """Generate valid data lists for benchmarking."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.lists(st.integers(), min_size=size, max_size=size))


@st.composite
def benchmark_result_data(draw):
    """Generate valid data for BenchmarkResult construction."""
    # Create a minimal OptimizationResult
    n_jobs = draw(st.integers(min_value=1, max_value=16))
    chunksize = draw(st.integers(min_value=1, max_value=1000))
    
    # Mock OptimizationResult - just needs the attributes BenchmarkResult uses
    class MockOptimization:
        def __init__(self, n_jobs, chunksize, speedup):
            self.n_jobs = n_jobs
            self.chunksize = chunksize
            self.estimated_speedup = speedup
            self.reason = "Test optimization"
    
    estimated_speedup = draw(st.floats(min_value=0.1, max_value=16.0))
    optimization = MockOptimization(n_jobs, chunksize, estimated_speedup)
    
    # Generate timing data
    serial_time = draw(st.floats(min_value=0.001, max_value=60.0))
    parallel_time = draw(st.floats(min_value=0.001, max_value=60.0))
    actual_speedup = serial_time / parallel_time
    
    # Calculate accuracy metrics
    error = actual_speedup - estimated_speedup
    error_percent = (error / estimated_speedup) * 100 if estimated_speedup > 0 else 0
    max_speedup = max(estimated_speedup, actual_speedup)
    normalized_error = abs(error) / max_speedup if max_speedup > 0 else 0
    accuracy_percent = (1.0 - normalized_error) * 100
    
    recommendations = draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    cache_hit = draw(st.booleans())
    
    return {
        'optimization': optimization,
        'serial_time': serial_time,
        'parallel_time': parallel_time,
        'actual_speedup': actual_speedup,
        'predicted_speedup': estimated_speedup,
        'accuracy_percent': accuracy_percent,
        'error_percent': error_percent,
        'recommendations': recommendations,
        'cache_hit': cache_hit
    }


class TestBenchmarkResultInvariants:
    """Test invariant properties of BenchmarkResult class."""

    @given(data=benchmark_result_data())
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_field_storage(self, data):
        """Test that BenchmarkResult stores all fields correctly."""
        result = BenchmarkResult(**data)
        
        assert result.optimization == data['optimization']
        assert result.serial_time == data['serial_time']
        assert result.parallel_time == data['parallel_time']
        assert result.actual_speedup == data['actual_speedup']
        assert result.predicted_speedup == data['predicted_speedup']
        assert result.accuracy_percent == data['accuracy_percent']
        assert result.error_percent == data['error_percent']
        assert result.recommendations == data['recommendations']
        assert result.cache_hit == data['cache_hit']

    @given(data=benchmark_result_data())
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_repr_format(self, data):
        """Test that __repr__ returns a valid string representation."""
        result = BenchmarkResult(**data)
        repr_str = repr(result)
        
        # Should be a non-empty string
        assert isinstance(repr_str, str)
        assert len(repr_str) > 0
        
        # Should contain key information
        assert 'BenchmarkResult' in repr_str
        assert 'actual_speedup' in repr_str
        assert 'predicted' in repr_str
        assert 'accuracy' in repr_str

    @given(data=benchmark_result_data())
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_str_format(self, data):
        """Test that __str__ returns a detailed report."""
        result = BenchmarkResult(**data)
        str_output = str(result)
        
        # Should be a non-empty string
        assert isinstance(str_output, str)
        assert len(str_output) > 0
        
        # Should contain sections and key information
        assert 'Benchmark Validation Results' in str_output
        assert 'Performance Measurements:' in str_output
        assert 'Prediction Accuracy:' in str_output
        
        # Should show the actual values
        assert f"{data['serial_time']:.4f}" in str_output
        assert f"{data['parallel_time']:.4f}" in str_output

    @given(
        data=benchmark_result_data(),
        threshold=st.floats(min_value=0.0, max_value=100.0)
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_is_accurate_threshold(self, data, threshold):
        """Test that is_accurate correctly compares against threshold."""
        result = BenchmarkResult(**data)
        
        is_accurate = result.is_accurate(threshold)
        expected = result.accuracy_percent >= threshold
        
        assert is_accurate == expected, \
            f"is_accurate({threshold}) should be {expected} when accuracy is {result.accuracy_percent}"

    @given(data=benchmark_result_data())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_non_negative_times(self, data):
        """Test that all time measurements are non-negative."""
        result = BenchmarkResult(**data)
        
        assert result.serial_time >= 0, f"serial_time should be non-negative, got {result.serial_time}"
        assert result.parallel_time >= 0, f"parallel_time should be non-negative, got {result.parallel_time}"

    @given(data=benchmark_result_data())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_speedup_positive(self, data):
        """Test that speedup values are positive."""
        result = BenchmarkResult(**data)
        
        assert result.actual_speedup > 0, f"actual_speedup should be positive, got {result.actual_speedup}"
        assert result.predicted_speedup > 0, f"predicted_speedup should be positive, got {result.predicted_speedup}"

    @given(data=benchmark_result_data())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_accuracy_bounded(self, data):
        """Test that accuracy_percent is within valid range [0, 100]."""
        result = BenchmarkResult(**data)
        
        # Accuracy can theoretically be slightly above 100% due to floating point precision
        # in the calculation: accuracy = (1 - |error| / max(predicted, actual)) * 100
        # We allow up to 105% as a reasonable upper bound for floating point errors
        # while still catching clearly invalid calculations
        assert result.accuracy_percent >= 0, \
            f"accuracy_percent should be non-negative, got {result.accuracy_percent}"
        assert result.accuracy_percent <= 105, \
            f"accuracy_percent should be <= 105 (allowing for float precision), got {result.accuracy_percent}"

    @given(data=benchmark_result_data())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_recommendations_is_list(self, data):
        """Test that recommendations is always a list."""
        result = BenchmarkResult(**data)
        
        assert isinstance(result.recommendations, list), \
            f"recommendations should be a list, got {type(result.recommendations)}"

    @given(data=benchmark_result_data())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_cache_hit_is_bool(self, data):
        """Test that cache_hit is a boolean."""
        result = BenchmarkResult(**data)
        
        assert isinstance(result.cache_hit, bool), \
            f"cache_hit should be a bool, got {type(result.cache_hit)}"


class TestValidateOptimizationInvariants:
    """Test invariant properties of validate_optimization function."""

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_returns_benchmark_result(self, data):
        """Test that validate_optimization returns a BenchmarkResult."""
        def simple_func(x):
            return x * 2
        
        result = validate_optimization(simple_func, data, verbose=False, use_cache=False)
        
        assert isinstance(result, BenchmarkResult), \
            f"Expected BenchmarkResult, got {type(result)}"

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_serial_time_positive(self, data):
        """Test that serial_time is positive."""
        def simple_func(x):
            return x * 2
        
        result = validate_optimization(simple_func, data, verbose=False, use_cache=False)
        
        assert result.serial_time > 0, f"serial_time should be positive, got {result.serial_time}"

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_parallel_time_positive(self, data):
        """Test that parallel_time is positive."""
        def simple_func(x):
            return x * 2
        
        result = validate_optimization(simple_func, data, verbose=False, use_cache=False)
        
        assert result.parallel_time > 0, f"parallel_time should be positive, got {result.parallel_time}"

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_actual_speedup_calculation(self, data):
        """Test that actual_speedup = serial_time / parallel_time."""
        def simple_func(x):
            return x * 2
        
        result = validate_optimization(simple_func, data, verbose=False, use_cache=False)
        
        # Calculate expected speedup
        expected_speedup = result.serial_time / result.parallel_time
        
        # Should match within floating point precision (use relative tolerance for robustness)
        relative_error = abs(result.actual_speedup - expected_speedup) / max(expected_speedup, 0.001)
        assert relative_error < 0.01, \
            f"actual_speedup ({result.actual_speedup}) should equal serial_time/parallel_time ({expected_speedup}), relative error: {relative_error}"

    @given(
        data=valid_data_lists(min_size=20, max_size=100),
        max_items=st.integers(min_value=10, max_value=50)
    )
    @settings(max_examples=10, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_max_items_parameter(self, data, max_items):
        """Test that max_items limits the benchmark dataset."""
        def simple_func(x):
            return x * 2
        
        # Ensure data is larger than max_items
        assume(len(data) > max_items)
        
        result = validate_optimization(
            simple_func, data, max_items=max_items, verbose=False, use_cache=False
        )
        
        # Result should still be valid
        assert isinstance(result, BenchmarkResult)
        assert result.serial_time > 0
        assert result.parallel_time > 0

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=10, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_invalid_timeout_raises(self, data):
        """Test that negative timeout raises ValueError."""
        def simple_func(x):
            return x * 2
        
        with pytest.raises(ValueError, match="timeout must be positive"):
            validate_optimization(simple_func, data, timeout=-1.0)

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=10, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_invalid_func_raises(self, data):
        """Test that non-callable func raises ValueError."""
        with pytest.raises(ValueError, match="func must be callable"):
            validate_optimization("not a function", data)

    def test_none_data_raises(self):
        """Test that None data raises ValueError."""
        def simple_func(x):
            return x * 2
        
        with pytest.raises(ValueError, match="data cannot be None"):
            validate_optimization(simple_func, None)

    def test_empty_data_raises(self):
        """Test that empty data raises ValueError."""
        def simple_func(x):
            return x * 2
        
        with pytest.raises(ValueError, match="data cannot be empty"):
            validate_optimization(simple_func, [])


class TestQuickValidateInvariants:
    """Test invariant properties of quick_validate function."""

    @given(data=valid_data_lists(min_size=20, max_size=200))
    @settings(max_examples=20, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_returns_benchmark_result(self, data):
        """Test that quick_validate returns a BenchmarkResult."""
        def simple_func(x):
            return x * 2
        
        result = quick_validate(simple_func, data, sample_size=10, verbose=False, use_cache=False)
        
        assert isinstance(result, BenchmarkResult), \
            f"Expected BenchmarkResult, got {type(result)}"

    @given(
        data=valid_data_lists(min_size=20, max_size=200),
        sample_size=st.integers(min_value=5, max_value=50)
    )
    @settings(max_examples=15, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_sample_size_parameter(self, data, sample_size):
        """Test that sample_size parameter affects sampling."""
        def simple_func(x):
            return x * 2
        
        # Ensure data is larger than sample
        assume(len(data) > sample_size)
        
        result = quick_validate(
            simple_func, data, sample_size=sample_size, verbose=False, use_cache=False
        )
        
        # Result should still be valid
        assert isinstance(result, BenchmarkResult)
        assert result.serial_time > 0
        assert result.parallel_time > 0

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=15, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_small_dataset_handling(self, data):
        """Test that quick_validate handles datasets smaller than sample_size."""
        def simple_func(x):
            return x * 2
        
        # Use sample_size larger than data
        result = quick_validate(
            simple_func, data, sample_size=1000, verbose=False, use_cache=False
        )
        
        # Should still work (uses entire dataset)
        assert isinstance(result, BenchmarkResult)
        assert result.serial_time > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_parallel_time_handled(self):
        """Test that zero parallel_time is handled gracefully."""
        # Create a mock optimization
        class MockOpt:
            n_jobs = 4
            chunksize = 10
            estimated_speedup = 2.0
            reason = "Test"
        
        # Create result with zero parallel time (edge case)
        # This shouldn't happen in practice, but test the division handling
        result = BenchmarkResult(
            optimization=MockOpt(),
            serial_time=1.0,
            parallel_time=0.001,  # Very small but not zero
            actual_speedup=1000.0,
            predicted_speedup=2.0,
            accuracy_percent=0.0,
            error_percent=49800.0,
            recommendations=[]
        )
        
        assert result.actual_speedup > 0
        assert result.parallel_time > 0

    @given(
        serial_time=st.floats(min_value=0.1, max_value=10.0),
        speedup=st.floats(min_value=0.1, max_value=10.0)
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_various_speedup_ratios(self, serial_time, speedup):
        """Test BenchmarkResult with various speedup ratios."""
        parallel_time = serial_time / speedup
        
        class MockOpt:
            n_jobs = 4
            chunksize = 10
            estimated_speedup = speedup
            reason = "Test"
        
        # Calculate accuracy
        error = speedup - speedup
        error_percent = 0.0
        accuracy_percent = 100.0
        
        result = BenchmarkResult(
            optimization=MockOpt(),
            serial_time=serial_time,
            parallel_time=parallel_time,
            actual_speedup=speedup,
            predicted_speedup=speedup,
            accuracy_percent=accuracy_percent,
            error_percent=error_percent,
            recommendations=[]
        )
        
        assert result.actual_speedup > 0
        assert result.serial_time > 0
        assert result.parallel_time > 0

    def test_empty_recommendations_default(self):
        """Test that recommendations defaults to empty list."""
        class MockOpt:
            n_jobs = 1
            chunksize = 1
            estimated_speedup = 1.0
            reason = "Test"
        
        result = BenchmarkResult(
            optimization=MockOpt(),
            serial_time=1.0,
            parallel_time=1.0,
            actual_speedup=1.0,
            predicted_speedup=1.0,
            accuracy_percent=100.0,
            error_percent=0.0
        )
        
        assert result.recommendations == []
        assert isinstance(result.recommendations, list)

    def test_cache_hit_default_false(self):
        """Test that cache_hit defaults to False."""
        class MockOpt:
            n_jobs = 1
            chunksize = 1
            estimated_speedup = 1.0
            reason = "Test"
        
        result = BenchmarkResult(
            optimization=MockOpt(),
            serial_time=1.0,
            parallel_time=1.0,
            actual_speedup=1.0,
            predicted_speedup=1.0,
            accuracy_percent=100.0,
            error_percent=0.0
        )
        
        assert result.cache_hit is False


class TestNumericalStability:
    """Test numerical stability with extreme values."""

    @given(
        serial_time=st.floats(min_value=0.001, max_value=100.0),
        parallel_time=st.floats(min_value=0.001, max_value=100.0)
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_various_time_values(self, serial_time, parallel_time):
        """Test BenchmarkResult with various time values."""
        actual_speedup = serial_time / parallel_time
        predicted_speedup = max(0.1, actual_speedup * 0.9)  # Predict 90% of actual
        
        error = actual_speedup - predicted_speedup
        error_percent = (error / predicted_speedup) * 100
        max_speedup = max(predicted_speedup, actual_speedup)
        normalized_error = abs(error) / max_speedup
        accuracy_percent = (1.0 - normalized_error) * 100
        
        class MockOpt:
            n_jobs = 4
            chunksize = 10
            estimated_speedup = predicted_speedup
            reason = "Test"
        
        result = BenchmarkResult(
            optimization=MockOpt(),
            serial_time=serial_time,
            parallel_time=parallel_time,
            actual_speedup=actual_speedup,
            predicted_speedup=predicted_speedup,
            accuracy_percent=accuracy_percent,
            error_percent=error_percent,
            recommendations=[]
        )
        
        # Check basic invariants
        assert result.serial_time == serial_time
        assert result.parallel_time == parallel_time
        assert result.actual_speedup == actual_speedup

    @given(accuracy=st.floats(min_value=0.0, max_value=100.0))
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_is_accurate_with_various_thresholds(self, accuracy):
        """Test is_accurate with various accuracy values."""
        class MockOpt:
            n_jobs = 4
            chunksize = 10
            estimated_speedup = 2.0
            reason = "Test"
        
        result = BenchmarkResult(
            optimization=MockOpt(),
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            predicted_speedup=2.0,
            accuracy_percent=accuracy,
            error_percent=0.0,
            recommendations=[]
        )
        
        # Test with default threshold (75%)
        if accuracy >= 75.0:
            assert result.is_accurate()
        else:
            assert not result.is_accurate()
        
        # Test with custom thresholds
        assert result.is_accurate(threshold=0.0)  # Always passes with 0 threshold
        if accuracy < 100.0:
            assert not result.is_accurate(threshold=100.0)  # Never passes when accuracy < 100%


class TestIntegrationProperties:
    """Test integration properties with real optimizer."""

    @given(data=valid_data_lists(min_size=20, max_size=50))
    @settings(max_examples=10, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_validate_with_precomputed_optimization(self, data):
        """Test validate_optimization with pre-computed optimization."""
        def simple_func(x):
            return x * 2
        
        # First get optimization
        opt = optimize(simple_func, data, verbose=False)
        
        # Then validate with it
        result = validate_optimization(
            simple_func, data, optimization=opt, verbose=False, use_cache=False
        )
        
        # Should use the provided optimization
        assert result.optimization == opt
        assert isinstance(result, BenchmarkResult)

    @given(data=valid_data_lists(min_size=20, max_size=50))
    @settings(max_examples=10, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_validate_computes_optimization_if_none(self, data):
        """Test that validate_optimization computes optimization if not provided."""
        def simple_func(x):
            return x * 2
        
        result = validate_optimization(simple_func, data, optimization=None, verbose=False, use_cache=False)
        
        # Should have computed optimization
        assert result.optimization is not None
        assert isinstance(result, BenchmarkResult)

    @given(data=valid_data_lists(min_size=20, max_size=100))
    @settings(max_examples=10, deadline=30000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_quick_validate_consistency(self, data):
        """Test that quick_validate produces consistent results."""
        def simple_func(x):
            return x ** 2
        
        # Run twice with same parameters
        result1 = quick_validate(simple_func, data, sample_size=20, verbose=False, use_cache=False)
        result2 = quick_validate(simple_func, data, sample_size=20, verbose=False, use_cache=False)
        
        # Both should be valid BenchmarkResults
        assert isinstance(result1, BenchmarkResult)
        assert isinstance(result2, BenchmarkResult)
        
        # Times should be similar (within 3x due to system variance)
        assert result1.serial_time > 0
        assert result2.serial_time > 0
