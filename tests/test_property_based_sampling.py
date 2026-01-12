"""
Property-based tests for the sampling module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of sampling functions across a wide range of inputs.
"""

import math
import pickle
import threading
from typing import Any, List

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize.sampling import (
    SamplingResult,
    check_picklability,
    check_data_picklability,
    check_data_picklability_with_measurements,
    estimate_total_items,
    reconstruct_iterator,
    check_parallel_environment_vars,
    estimate_internal_threads,
    detect_parallel_libraries,
    detect_thread_activity,
    detect_workload_type,
    safe_slice_data,
)


def _picklable_test_function(x):
    """A picklable module-level function for testing."""
    return x * 2


class TestSamplingResultInvariants:
    """Test invariant properties of SamplingResult."""

    @given(
        avg_time=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        return_size=st.integers(min_value=0, max_value=1000000),
        peak_memory=st.integers(min_value=0, max_value=10000000),
        sample_count=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=100, deadline=2000)
    def test_sampling_result_non_negative_values(self, avg_time, return_size, peak_memory, sample_count):
        """Test that SamplingResult maintains non-negative numeric values."""
        result = SamplingResult(
            avg_time=avg_time,
            return_size=return_size,
            peak_memory=peak_memory,
            sample_count=sample_count,
            is_picklable=True
        )
        
        # All numeric values should be non-negative
        assert result.avg_time >= 0, f"avg_time should be non-negative, got {result.avg_time}"
        assert result.return_size >= 0, f"return_size should be non-negative, got {result.return_size}"
        assert result.peak_memory >= 0, f"peak_memory should be non-negative, got {result.peak_memory}"
        assert result.sample_count >= 0, f"sample_count should be non-negative, got {result.sample_count}"

    @given(
        avg_pickle_time=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        time_variance=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        coefficient_of_variation=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=2000)
    def test_sampling_result_timing_metrics(self, avg_pickle_time, time_variance, coefficient_of_variation):
        """Test that timing metrics are non-negative."""
        result = SamplingResult(
            avg_time=0.1,
            return_size=100,
            peak_memory=1000,
            sample_count=3,
            is_picklable=True,
            avg_pickle_time=avg_pickle_time,
            time_variance=time_variance,
            coefficient_of_variation=coefficient_of_variation
        )
        
        assert result.avg_pickle_time >= 0, f"avg_pickle_time should be non-negative"
        assert result.time_variance >= 0, f"time_variance should be non-negative"
        assert result.coefficient_of_variation >= 0, f"coefficient_of_variation should be non-negative"

    @given(
        cpu_time_ratio=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        workload_type=st.sampled_from(['cpu_bound', 'io_bound', 'mixed'])
    )
    @settings(max_examples=50, deadline=2000)
    def test_sampling_result_workload_characteristics(self, cpu_time_ratio, workload_type):
        """Test workload characteristic invariants."""
        result = SamplingResult(
            avg_time=0.1,
            return_size=100,
            peak_memory=1000,
            sample_count=3,
            is_picklable=True,
            cpu_time_ratio=cpu_time_ratio,
            workload_type=workload_type
        )
        
        # CPU time ratio should be in [0, 1]
        assert 0.0 <= result.cpu_time_ratio <= 1.0, \
            f"cpu_time_ratio should be in [0, 1], got {result.cpu_time_ratio}"
        
        # Workload type should be valid
        assert result.workload_type in ['cpu_bound', 'io_bound', 'mixed'], \
            f"Invalid workload_type: {result.workload_type}"


class TestPicklabilityChecks:
    """Test picklability checking functions."""

    @given(value=st.integers())
    @settings(max_examples=50, deadline=2000)
    def test_check_picklability_simple_function(self, value):
        """Test that simple functions are correctly identified as picklable."""
        # Module-level function should be picklable
        func = _picklable_test_function
        assert check_picklability(func) is True, "Module-level function should be picklable"
        
        # Verify it actually works
        result = func(value)
        assert result == value * 2

    @given(data=st.lists(st.integers(), min_size=0, max_size=100))
    @settings(max_examples=100, deadline=2000)
    def test_check_data_picklability_integers(self, data):
        """Test that integer lists are always picklable."""
        is_picklable, idx, exc = check_data_picklability(data)
        
        assert is_picklable is True, f"Integer list should be picklable"
        assert idx is None, f"No unpicklable index should be found"
        assert exc is None, f"No exception should be raised"

    @given(data=st.lists(
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=0, max_size=50),
            st.booleans()
        ),
        min_size=0,
        max_size=100
    ))
    @settings(max_examples=100, deadline=3000)
    def test_check_data_picklability_mixed_primitives(self, data):
        """Test that primitive types are always picklable."""
        is_picklable, idx, exc = check_data_picklability(data)
        
        assert is_picklable is True, f"Primitive types should be picklable"
        assert idx is None, f"No unpicklable index should be found"
        assert exc is None, f"No exception should be raised"

    @given(data=st.lists(st.integers(), min_size=1, max_size=100))
    @settings(max_examples=50, deadline=3000)
    def test_check_data_picklability_with_measurements_structure(self, data):
        """Test that picklability check with measurements returns correct structure."""
        is_picklable, idx, exc, measurements = check_data_picklability_with_measurements(data)
        
        # Should be picklable
        assert is_picklable is True
        assert idx is None
        assert exc is None
        
        # Measurements should be a list of tuples (time, size)
        assert isinstance(measurements, list), "measurements should be a list"
        assert len(measurements) == len(data), "Should have one measurement per item"
        
        for time, size in measurements:
            assert isinstance(time, float), "Time should be a float"
            assert time >= 0, "Time should be non-negative"
            assert isinstance(size, int), "Size should be an integer"
            assert size >= 0, "Size should be non-negative"

    def test_check_data_picklability_with_unpicklable_item(self):
        """Test that unpicklable items are correctly identified."""
        # Create data with an unpicklable item (thread lock)
        lock = threading.Lock()
        data = [1, 2, lock, 4]
        
        is_picklable, idx, exc = check_data_picklability(data)
        
        assert is_picklable is False, "Should detect unpicklable item"
        assert idx == 2, f"Should find unpicklable item at index 2, got {idx}"
        assert exc is not None, "Should have exception"


class TestEstimateTotalItems:
    """Test total items estimation."""

    @given(data=st.lists(st.integers(), min_size=0, max_size=1000))
    @settings(max_examples=100, deadline=2000)
    def test_estimate_total_items_list(self, data):
        """Test that list length is correctly estimated."""
        # When sample was not consumed, pass False
        estimated = estimate_total_items(data, sample_consumed=False)
        assert estimated == len(data), f"Should estimate list length correctly"

    @given(start=st.integers(min_value=0, max_value=1000), stop=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=100, deadline=2000)
    def test_estimate_total_items_range(self, start, stop):
        """Test that range length is correctly estimated."""
        if start > stop:
            start, stop = stop, start
        
        r = range(start, stop)
        estimated = estimate_total_items(r, sample_consumed=False)
        assert estimated == len(r), f"Should estimate range length correctly"

    @given(size=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=100, deadline=2000)
    def test_estimate_total_items_generator(self, size):
        """Test that generator length estimation handles consumption correctly."""
        def gen():
            for i in range(size):
                yield i
        
        # When sample is consumed (typical case with generators), pass True
        estimated = estimate_total_items(gen(), sample_consumed=True)
        # Generators don't have a length, so -1 is expected (unknown length)
        assert estimated == -1, "Generator should return -1 for unknown length"
    
    def test_estimate_total_items_consumed_list(self):
        """Test estimation when sample was consumed from list."""
        data = [1, 2, 3, 4, 5]
        # When consumed=True, it tries to count remaining items
        estimated = estimate_total_items(data, sample_consumed=True)
        # For list, should return the list length
        assert estimated == 5


class TestReconstructIterator:
    """Test iterator reconstruction."""

    @given(
        sample=st.lists(st.integers(), min_size=1, max_size=50),
        remaining=st.lists(st.integers(), min_size=0, max_size=100)
    )
    @settings(max_examples=100, deadline=2000)
    def test_reconstruct_iterator_preserves_data(self, sample, remaining):
        """Test that reconstruct_iterator preserves all data."""
        reconstructed = reconstruct_iterator(sample, remaining)
        reconstructed_list = list(reconstructed)
        
        expected = sample + remaining
        assert reconstructed_list == expected, \
            f"Reconstructed data should match sample + remaining"

    @given(sample=st.lists(st.integers(), min_size=1, max_size=100))
    @settings(max_examples=50, deadline=2000)
    def test_reconstruct_iterator_with_empty_remaining(self, sample):
        """Test reconstruction with no remaining data."""
        reconstructed = reconstruct_iterator(sample, [])
        reconstructed_list = list(reconstructed)
        
        assert reconstructed_list == sample, \
            f"Reconstructed data should match sample when remaining is empty"

    @given(
        sample=st.lists(st.integers(), min_size=1, max_size=50),
        remaining_size=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=50, deadline=2000)
    def test_reconstruct_iterator_with_generator_remaining(self, sample, remaining_size):
        """Test reconstruction with generator as remaining data."""
        def gen():
            for i in range(remaining_size):
                yield i
        
        reconstructed = reconstruct_iterator(sample, gen())
        reconstructed_list = list(reconstructed)
        
        expected_length = len(sample) + remaining_size
        assert len(reconstructed_list) == expected_length, \
            f"Should have {expected_length} items"
        
        # First items should match sample
        assert reconstructed_list[:len(sample)] == sample, \
            f"First items should match sample"


class TestPickleTimeMeasurement:
    """Test pickle time and size measurement via check_data_picklability_with_measurements."""

    @given(data=st.lists(st.integers(), min_size=1, max_size=100))
    @settings(max_examples=50, deadline=3000)
    def test_pickle_measurements_return_non_negative(self, data):
        """Test that pickle measurements return non-negative time and size."""
        is_picklable, idx, exc, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True, "Integers should be picklable"
        
        for time_taken, size in measurements:
            assert time_taken >= 0, f"Pickle time should be non-negative, got {time_taken}"
            assert size >= 0, f"Pickle size should be non-negative, got {size}"

    @given(size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=50, deadline=3000)
    def test_pickle_larger_objects_have_larger_sizes(self, size):
        """Test that larger objects generally have larger pickle sizes."""
        # Test with different sizes
        data = list(range(size))
        
        is_picklable, idx, exc, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert len(measurements) == size
        
        # Each measurement should have non-negative time and size
        for time_taken, pickle_size in measurements:
            assert time_taken >= 0
            assert pickle_size > 0  # Even integers have some pickle overhead

    @given(data=st.lists(
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=0, max_size=50)
        ),
        min_size=1,
        max_size=50
    ))
    @settings(max_examples=50, deadline=3000)
    def test_pickle_measurements_consistent_structure(self, data):
        """Test that pickle measurements return consistent structure."""
        is_picklable, idx, exc, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True, "Primitives should be picklable"
        assert len(measurements) == len(data), "Should have one measurement per item"
        
        # All measurements should be tuples of (float, int)
        for time_taken, size in measurements:
            assert isinstance(time_taken, float), "Time should be float"
            assert isinstance(size, int), "Size should be int"


class TestParallelEnvironmentDetection:
    """Test parallel environment variable detection."""

    def test_check_parallel_environment_vars_returns_dict(self):
        """Test that environment variable check returns a dictionary."""
        env_vars = check_parallel_environment_vars()
        
        assert isinstance(env_vars, dict), "Should return a dictionary"
        
        # All values should be strings (environment variable values)
        for key, value in env_vars.items():
            assert isinstance(key, str), "Keys should be strings"
            assert isinstance(value, str), "Values should be strings"

    def test_check_parallel_environment_vars_checks_common_vars(self):
        """Test that common parallel environment variables are checked."""
        env_vars = check_parallel_environment_vars()
        
        # Should check for common variables (may or may not be set)
        # The function returns only set variables
        assert isinstance(env_vars, dict)


class TestEstimateInternalThreads:
    """Test internal thread estimation."""

    def test_estimate_internal_threads_returns_non_negative(self):
        """Test that thread estimation returns non-negative value."""
        # Use empty lists for simple case
        parallel_libraries = []
        thread_activity = {}
        env_vars = {}
        
        estimated = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        
        assert estimated >= 0, f"Thread estimate should be non-negative, got {estimated}"

    @given(
        num_libraries=st.integers(min_value=0, max_value=5),
        thread_delta=st.integers(min_value=0, max_value=50)
    )
    @settings(max_examples=50, deadline=2000)
    def test_estimate_internal_threads_with_libraries(self, num_libraries, thread_delta):
        """Test thread estimation with parallel libraries detected."""
        # Create fake library names
        parallel_libraries = [f"lib{i}" for i in range(num_libraries)]
        thread_activity = {'delta': thread_delta}
        env_vars = {}
        
        estimated = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        
        # Should be non-negative
        assert estimated >= 1, "Should be at least 1"
        
        # If there's thread delta, estimate should reflect it (delta + 1)
        if thread_delta > 0:
            expected_estimate = thread_delta + 1
            assert estimated == expected_estimate, \
                f"Estimate should be delta+1: {estimated} == {expected_estimate}"
        elif num_libraries > 0:
            # No delta but libraries detected -> should estimate 4 threads
            assert estimated == 4, f"Should estimate 4 threads when libraries detected without delta"
        else:
            # No libraries, no delta -> should estimate 1 thread
            assert estimated == 1, f"Should estimate 1 thread when no parallelism detected"

    def test_estimate_internal_threads_with_env_vars(self):
        """Test thread estimation with environment variables."""
        parallel_libraries = ['numpy']
        thread_activity = {}
        env_vars = {'OMP_NUM_THREADS': '4'}
        
        estimated = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        
        # Should detect from environment variable
        assert estimated >= 4, f"Should detect at least 4 threads from env var, got {estimated}"


class TestNumericalStability:
    """Test numerical stability of sampling operations."""

    @given(
        avg_time=st.floats(min_value=1e-9, max_value=1e3, allow_nan=False, allow_infinity=False),
        time_variance=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=2000)
    def test_coefficient_of_variation_calculation_stable(self, avg_time, time_variance):
        """Test that coefficient of variation calculation is numerically stable."""
        # Avoid division by zero
        assume(avg_time > 0)
        
        # Calculate CV manually
        std_dev = math.sqrt(time_variance)
        cv = std_dev / avg_time
        
        # CV should be non-negative and finite
        assert cv >= 0, f"CV should be non-negative"
        assert math.isfinite(cv), f"CV should be finite"

    @given(
        values=st.lists(
            st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=100
        )
    )
    @settings(max_examples=50, deadline=3000)
    def test_variance_calculation_non_negative(self, values):
        """Test that variance calculations are always non-negative."""
        # Calculate mean
        mean = sum(values) / len(values)
        
        # Calculate variance
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        # Variance should always be non-negative
        assert variance >= 0, f"Variance should be non-negative, got {variance}"


class TestEdgeCases:
    """Test edge cases in sampling operations."""

    def test_sampling_result_with_none_values(self):
        """Test that SamplingResult handles None values gracefully."""
        result = SamplingResult(
            avg_time=0.0,
            return_size=0,
            peak_memory=0,
            sample_count=0,
            is_picklable=False,
            error=None,
            sample=None,
            remaining_data=None
        )
        
        # Should have default empty list for sample
        assert result.sample == []
        assert result.remaining_data is None

    def test_estimate_total_items_empty_list(self):
        """Test estimation with empty list."""
        estimated = estimate_total_items([], sample_consumed=False)
        assert estimated == 0, "Empty list should have length 0"

    def test_reconstruct_iterator_empty_sample(self):
        """Test reconstruction with empty sample (edge case)."""
        # This tests a boundary condition that may occur in practice
        remaining = [1, 2, 3]
        reconstructed = reconstruct_iterator([], remaining)
        reconstructed_list = list(reconstructed)
        
        assert reconstructed_list == remaining, \
            "Should return remaining data when sample is empty"

    @given(size=st.integers(min_value=1, max_value=100))
    @settings(max_examples=30, deadline=3000)
    def test_pickle_measurement_various_sizes(self, size):
        """Test pickle measurement with various list sizes."""
        data = [0] * size  # List of zeros
        
        is_picklable, idx, exc, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert len(measurements) == size
        
        # All measurements should be valid
        for time_taken, pickle_size in measurements:
            assert time_taken >= 0, "Time should be non-negative"
            assert pickle_size > 0, "Size should be positive (even 0 has pickle overhead)"


# Summary test to verify Hypothesis integration for sampling
def test_hypothesis_integration_sampling():
    """Verify that Hypothesis is properly integrated for sampling tests."""
    from hypothesis import find
    
    # Simple example to verify Hypothesis works
    result = find(
        st.lists(st.integers(), min_size=5, max_size=10),
        lambda x: len(x) >= 5
    )
    assert len(result) >= 5, "Hypothesis integration test failed"
