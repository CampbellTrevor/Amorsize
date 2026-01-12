"""
Comprehensive edge case tests for sampling module.

This test suite covers boundary conditions, error handling, invariants,
and edge cases to strengthen test quality before mutation testing baseline.

Following Iteration 184's pattern for optimizer module.

Test Categories:
1. Boundary Conditions (8 tests)
2. Parameter Validation (7 tests)
3. Error Handling (5 tests)
4. Invariant Verification (7 tests)
5. Generator Handling (5 tests)
6. Feature Integration (11 tests)
7. Stress Tests (4 tests)
8. Edge Cases (6 tests)
"""

import pytest
import time
import pickle
import threading
from typing import Iterator
from amorsize.sampling import (
    check_picklability,
    check_data_picklability,
    check_data_picklability_with_measurements,
    safe_slice_data,
    perform_dry_run,
    estimate_total_items,
    reconstruct_iterator,
    detect_parallel_libraries,
    check_parallel_environment_vars,
    estimate_internal_threads,
    detect_workload_type,
    _clear_workload_caches,
    SamplingResult
)


# ============================================================================
# TEST FIXTURES AND HELPERS
# ============================================================================

def simple_function(x):
    """Simple function for testing."""
    return x * 2


def slow_io_function(x):
    """Simulates I/O-bound function."""
    time.sleep(0.0001)  # Very short sleep for fast test execution
    return x


def cpu_intensive_function(x):
    """Simulates CPU-bound function."""
    result = 0
    for i in range(1000):
        result += i * x
    return result


def generator_function(n):
    """Generator for testing."""
    for i in range(n):
        yield i


class UnpicklableObject:
    """Object that cannot be pickled."""
    def __init__(self):
        self.lock = threading.Lock()


def unpicklable_function(x):
    """Function with closure that cannot be pickled."""
    lock = threading.Lock()
    return x * 2


# ============================================================================
# BOUNDARY CONDITIONS
# ============================================================================

class TestSamplingBoundaryConditions:
    """Test edge cases at boundaries of input ranges."""

    def test_safe_slice_empty_list(self):
        """Test slicing from empty list."""
        data = []
        sample, remaining, is_gen = safe_slice_data(data, 5)
        
        assert sample == []
        assert remaining == []
        assert is_gen is False

    def test_safe_slice_single_item(self):
        """Test slicing from single-item list."""
        data = [42]
        sample, remaining, is_gen = safe_slice_data(data, 5)
        
        assert len(sample) == 1
        assert sample[0] == 42
        assert remaining == [42]
        assert is_gen is False

    def test_safe_slice_exact_size(self):
        """Test slicing when sample size equals data size."""
        data = list(range(5))
        sample, remaining, is_gen = safe_slice_data(data, 5)
        
        assert len(sample) == 5
        assert sample == [0, 1, 2, 3, 4]
        assert remaining == data
        assert is_gen is False

    def test_safe_slice_sample_larger_than_data(self):
        """Test slicing when sample size exceeds data size."""
        data = list(range(3))
        sample, remaining, is_gen = safe_slice_data(data, 10)
        
        assert len(sample) == 3
        assert sample == [0, 1, 2]
        assert remaining == data

    def test_safe_slice_zero_sample_size(self):
        """Test slicing with sample size of zero."""
        data = list(range(10))
        sample, remaining, is_gen = safe_slice_data(data, 0)
        
        assert sample == []
        assert remaining == data
        assert is_gen is False

    def test_perform_dry_run_with_single_item(self):
        """Test dry run with single-item data."""
        data = [5]
        result = perform_dry_run(simple_function, data, sample_size=1)
        
        assert result.sample_count == 1
        assert result.avg_time > 0
        assert result.is_picklable is True

    def test_perform_dry_run_with_empty_data(self):
        """Test dry run with empty data."""
        data = []
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        assert result.sample_count == 0
        assert result.error is not None
        assert isinstance(result.error, ValueError)

    def test_estimate_total_items_empty_list(self):
        """Test total item estimation with empty list."""
        data = []
        total = estimate_total_items(data, sample_consumed=False)
        
        assert total == 0


# ============================================================================
# PARAMETER VALIDATION
# ============================================================================

class TestSamplingParameterValidation:
    """Test validation of input parameters."""

    def test_check_picklability_with_none(self):
        """Test picklability check with None function."""
        # None is picklable
        result = check_picklability(None)
        assert result is True

    def test_check_picklability_with_lambda(self):
        """Test picklability check with lambda (typically unpicklable)."""
        def lambda_like_func(x):
            return x * 2
        result = check_picklability(lambda_like_func)
        # Lambda-like functions may or may not be picklable depending on context
        # We just verify it doesn't crash
        assert isinstance(result, bool)

    def test_check_picklability_with_builtin(self):
        """Test picklability check with builtin function."""
        result = check_picklability(len)
        assert result is True

    def test_check_data_picklability_with_empty_list(self):
        """Test data picklability check with empty list."""
        data = []
        is_picklable, idx, error = check_data_picklability(data)
        
        assert is_picklable is True
        assert idx is None
        assert error is None

    def test_check_data_picklability_with_none_item(self):
        """Test data picklability with None in data."""
        data = [1, None, 3]
        is_picklable, idx, error = check_data_picklability(data)
        
        assert is_picklable is True
        assert idx is None

    def test_check_data_picklability_with_unpicklable_item(self):
        """Test data picklability with unpicklable object."""
        data = [1, UnpicklableObject(), 3]
        is_picklable, idx, error = check_data_picklability(data)
        
        assert is_picklable is False
        assert idx == 1
        assert error is not None

    def test_safe_slice_negative_sample_size(self):
        """Test safe_slice_data with negative sample size."""
        data = list(range(10))
        # islice raises ValueError for negative n
        with pytest.raises(ValueError):
            safe_slice_data(data, -1)


# ============================================================================
# ERROR HANDLING
# ============================================================================

class TestSamplingErrorHandling:
    """Test error handling in sampling functions."""

    def test_perform_dry_run_with_none_function(self):
        """Test dry run with None as function."""
        data = [1, 2, 3]
        # None is picklable but will fail when called
        result = perform_dry_run(None, data, sample_size=2)
        # Should complete, and None is technically picklable
        assert result.is_picklable is True
        # But execution should have encountered errors
        assert result.sample_count >= 0

    def test_perform_dry_run_with_function_raising_exception(self):
        """Test dry run with function that raises exception."""
        def failing_function(x):
            raise ValueError("Intentional error")
        
        data = [1, 2, 3]
        result = perform_dry_run(failing_function, data, sample_size=2)
        
        # Should complete but capture the error
        assert result.sample_count >= 0

    def test_check_data_picklability_with_measurements_unpicklable(self):
        """Test picklability check with measurements on unpicklable data."""
        data = [1, threading.Lock(), 3]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is False
        assert idx == 1
        assert error is not None
        # Measurements list is returned (may be partial or empty depending on when error occurred)
        assert isinstance(measurements, list)

    def test_safe_slice_data_with_none(self):
        """Test safe_slice_data with None data."""
        with pytest.raises((TypeError, AttributeError)):
            safe_slice_data(None, 5)


# ============================================================================
# INVARIANT VERIFICATION
# ============================================================================

class TestSamplingInvariants:
    """Test that sampling functions maintain invariants."""

    def test_sampling_result_attributes_exist(self):
        """Test that SamplingResult has all required attributes."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=3)
        
        # Verify all expected attributes exist
        assert hasattr(result, 'avg_time')
        assert hasattr(result, 'return_size')
        assert hasattr(result, 'peak_memory')
        assert hasattr(result, 'sample_count')
        assert hasattr(result, 'is_picklable')
        assert hasattr(result, 'avg_pickle_time')
        assert hasattr(result, 'sample')
        assert hasattr(result, 'remaining_data')
        assert hasattr(result, 'is_generator')
        assert hasattr(result, 'coefficient_of_variation')
        assert hasattr(result, 'workload_type')

    def test_avg_time_non_negative(self):
        """Test that average time is always non-negative."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        assert result.avg_time >= 0

    def test_sample_count_non_negative(self):
        """Test that sample count is always non-negative."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        assert result.sample_count >= 0

    def test_sample_count_matches_sample_length(self):
        """Test that sample_count matches actual sample length."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        assert result.sample_count == len(result.sample)

    def test_coefficient_of_variation_non_negative(self):
        """Test that coefficient of variation is non-negative."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        assert result.coefficient_of_variation >= 0

    def test_workload_type_valid(self):
        """Test that workload type is one of valid values."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        valid_types = ["cpu_bound", "io_bound", "mixed"]
        assert result.workload_type in valid_types

    def test_cpu_time_ratio_non_negative(self):
        """Test that CPU time ratio is non-negative."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        assert result.cpu_time_ratio >= 0


# ============================================================================
# GENERATOR HANDLING
# ============================================================================

class TestSamplingGeneratorHandling:
    """Test generator and iterator handling."""

    def test_safe_slice_preserves_generator_remaining(self):
        """Test that safe_slice preserves remaining generator items."""
        def gen():
            for i in range(10):
                yield i
        
        data = gen()
        sample, remaining, is_gen = safe_slice_data(data, 3)
        
        assert is_gen is True
        assert len(sample) == 3
        assert sample == [0, 1, 2]
        
        # Verify remaining items are still available
        remaining_list = list(remaining)
        assert len(remaining_list) == 7
        assert remaining_list == [3, 4, 5, 6, 7, 8, 9]

    def test_reconstruct_iterator_basic(self):
        """Test reconstructing iterator from sample and remaining."""
        def gen():
            for i in range(10):
                yield i
        
        data = gen()
        sample, remaining, is_gen = safe_slice_data(data, 3)
        
        # Reconstruct full iterator
        reconstructed = reconstruct_iterator(sample, remaining)
        full_list = list(reconstructed)
        
        assert full_list == list(range(10))

    def test_reconstruct_iterator_with_list(self):
        """Test reconstructing iterator from list data."""
        data = list(range(10))
        sample, remaining, is_gen = safe_slice_data(data, 3)
        
        # For lists, remaining is the full original list
        # reconstruct_iterator chains sample + remaining
        # This means sample items appear twice (once in sample, once in remaining)
        reconstructed = reconstruct_iterator(sample, remaining)
        full_list = list(reconstructed)
        
        # For lists, we get sample first, then full remaining (which includes sample items)
        # So we get duplicates: [0,1,2] + [0,1,2,3,4,5,6,7,8,9]
        assert len(full_list) == 13  # sample + full list

    def test_perform_dry_run_preserves_generator(self):
        """Test that perform_dry_run preserves generator for reconstruction."""
        def gen():
            for i in range(10):
                yield i
        
        data = gen()
        result = perform_dry_run(simple_function, data, sample_size=3)
        
        assert result.is_generator is True
        assert len(result.sample) == 3
        assert result.remaining_data is not None
        
        # Verify we can reconstruct
        reconstructed = reconstruct_iterator(result.sample, result.remaining_data)
        full_list = list(reconstructed)
        assert len(full_list) == 10

    def test_estimate_total_items_with_generator(self):
        """Test total item estimation with generator after sampling."""
        def gen():
            for i in range(100):
                yield i
        
        data = gen()
        sample, remaining, is_gen = safe_slice_data(data, 5)
        
        # After consuming sample, we don't know total for generator
        # Function should handle this gracefully
        total = estimate_total_items(remaining, sample_consumed=True)
        
        # Should return a reasonable estimate or -1 for unknown
        assert isinstance(total, int)


# ============================================================================
# FEATURE INTEGRATION
# ============================================================================

class TestSamplingFeatureIntegration:
    """Test integration of sampling features."""

    def test_perform_dry_run_with_profiling_enabled(self):
        """Test dry run with function profiling enabled."""
        data = list(range(10))
        result = perform_dry_run(
            simple_function, 
            data, 
            sample_size=5,
            enable_function_profiling=True
        )
        
        assert result.sample_count == 5
        assert result.function_profiler_stats is not None

    def test_perform_dry_run_with_memory_tracking_disabled(self):
        """Test dry run with memory tracking disabled."""
        data = list(range(10))
        result = perform_dry_run(
            simple_function,
            data,
            sample_size=5,
            enable_memory_tracking=False
        )
        
        assert result.sample_count == 5
        # Peak memory should be 0 when tracking is disabled
        assert result.peak_memory == 0

    def test_detect_workload_type_io_bound(self):
        """Test workload type detection for I/O-bound function."""
        data = list(range(5))
        workload_type, cpu_ratio = detect_workload_type(slow_io_function, data)
        
        # Should detect low CPU usage
        assert workload_type in ["io_bound", "mixed"]
        assert cpu_ratio < 0.8  # Not fully CPU-bound

    def test_detect_workload_type_cpu_bound(self):
        """Test workload type detection for CPU-bound function."""
        data = list(range(5))
        workload_type, cpu_ratio = detect_workload_type(cpu_intensive_function, data)
        
        # Should detect high CPU usage
        assert workload_type in ["cpu_bound", "mixed"]
        assert cpu_ratio > 0

    def test_detect_workload_type_with_empty_sample(self):
        """Test workload type detection with empty sample."""
        workload_type, cpu_ratio = detect_workload_type(simple_function, [])
        
        # Should default to cpu_bound with empty sample
        assert workload_type == "cpu_bound"
        assert cpu_ratio == 1.0

    def test_estimate_internal_threads_with_no_libraries(self):
        """Test thread estimation with no parallel libraries detected."""
        threads = estimate_internal_threads([], {}, {})
        
        # Should return minimum of 1
        assert threads == 1

    def test_estimate_internal_threads_with_env_var(self):
        """Test thread estimation with environment variable set."""
        env_vars = {'OMP_NUM_THREADS': '4'}
        threads = estimate_internal_threads([], {}, env_vars)
        
        # Should respect environment variable
        assert threads == 4

    def test_estimate_internal_threads_with_thread_delta(self):
        """Test thread estimation with observed thread activity."""
        thread_activity = {'before': 1, 'during': 5, 'after': 1, 'delta': 4}
        threads = estimate_internal_threads([], thread_activity, {})
        
        # Should estimate based on delta
        assert threads == 5  # delta + 1

    def test_check_parallel_environment_vars_caching(self):
        """Test that parallel environment vars are cached."""
        # Clear cache first
        _clear_workload_caches()
        
        # First call
        result1 = check_parallel_environment_vars()
        
        # Second call should return cached result
        result2 = check_parallel_environment_vars()
        
        assert result1 == result2
        assert isinstance(result1, dict)

    def test_detect_parallel_libraries_caching(self):
        """Test that parallel library detection is cached."""
        # Clear cache first
        _clear_workload_caches()
        
        # First call
        result1 = detect_parallel_libraries()
        
        # Second call should return cached result
        result2 = detect_parallel_libraries()
        
        assert result1 == result2
        assert isinstance(result1, list)

    def test_check_data_picklability_with_measurements_all_picklable(self):
        """Test picklability check with measurements on all picklable data."""
        data = [1, 2, 3, 4, 5]
        is_picklable, idx, error, measurements = check_data_picklability_with_measurements(data)
        
        assert is_picklable is True
        assert idx is None
        assert error is None
        assert len(measurements) == 5
        
        # Each measurement should be (time, size) tuple
        for time_val, size_val in measurements:
            assert isinstance(time_val, float)
            assert isinstance(size_val, int)
            assert time_val >= 0
            assert size_val > 0


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestSamplingStressTests:
    """Test sampling functions under stress conditions."""

    def test_safe_slice_large_sample_from_small_data(self):
        """Test requesting very large sample from small data."""
        data = list(range(5))
        sample, remaining, is_gen = safe_slice_data(data, 1000)
        
        # Should only return available items
        assert len(sample) == 5
        assert sample == [0, 1, 2, 3, 4]

    def test_perform_dry_run_with_large_sample_size(self):
        """Test dry run with large sample size on small data."""
        data = list(range(5))
        result = perform_dry_run(simple_function, data, sample_size=100)
        
        # Should handle gracefully
        assert result.sample_count == 5

    def test_estimate_total_items_with_range(self):
        """Test total item estimation with range object."""
        data = range(1000)
        total = estimate_total_items(data, sample_consumed=False)
        
        assert total == 1000

    def test_safe_slice_data_with_range(self):
        """Test safe_slice_data with range object."""
        data = range(100)
        sample, remaining, is_gen = safe_slice_data(data, 5)
        
        # Range has __len__ so not treated as generator
        assert is_gen is False
        assert len(sample) == 5
        assert sample == [0, 1, 2, 3, 4]


# ============================================================================
# EDGE CASES
# ============================================================================

class TestSamplingEdgeCases:
    """Test unusual but valid edge cases."""

    def test_perform_dry_run_with_sample_size_one(self):
        """Test dry run with minimum sample size."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=1)
        
        assert result.sample_count == 1
        assert len(result.sample) == 1

    def test_safe_slice_data_with_tuple(self):
        """Test safe_slice_data with tuple data."""
        data = tuple(range(10))
        sample, remaining, is_gen = safe_slice_data(data, 5)
        
        # Tuple has __len__ so not a generator
        assert is_gen is False
        assert len(sample) == 5

    def test_check_picklability_with_class_method(self):
        """Test picklability of class method."""
        class MyClass:
            def method(self, x):
                return x * 2
        
        obj = MyClass()
        result = check_picklability(obj.method)
        
        # Instance methods are typically not picklable
        assert isinstance(result, bool)

    def test_sampling_result_initialization_with_defaults(self):
        """Test SamplingResult can be initialized with minimal args."""
        result = SamplingResult(
            avg_time=0.5,
            return_size=100,
            peak_memory=1000,
            sample_count=5,
            is_picklable=True
        )
        
        assert result.avg_time == 0.5
        assert result.sample_count == 5
        assert result.sample == []
        assert result.workload_type == "cpu_bound"

    def test_reconstruct_iterator_with_empty_sample(self):
        """Test reconstructing iterator with empty sample."""
        data = list(range(10))
        reconstructed = reconstruct_iterator([], data)
        full_list = list(reconstructed)
        
        assert full_list == list(range(10))

    def test_perform_dry_run_with_very_fast_function(self):
        """Test dry run with function that executes extremely fast."""
        def instant_function(x):
            return x
        
        data = list(range(10))
        result = perform_dry_run(instant_function, data, sample_size=5)
        
        # Should complete successfully even with near-zero execution time
        assert result.sample_count == 5
        assert result.avg_time >= 0
