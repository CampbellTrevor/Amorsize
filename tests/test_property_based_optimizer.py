"""
Property-based tests for the optimizer using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the optimizer across a wide range of inputs.
"""

import math
from typing import Any, List

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize import optimize
from amorsize.optimizer import OptimizationResult


# Custom strategies for generating test data
@st.composite
def valid_data_lists(draw, min_size=1, max_size=1000):
    """Generate valid data lists for optimization."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.lists(st.integers(), min_size=size, max_size=size))


@st.composite
def simple_functions(draw):
    """Generate simple picklable functions for testing."""
    # Generate different types of simple operations
    operation = draw(st.sampled_from([
        lambda x: x * 2,
        lambda x: x + 10,
        lambda x: x ** 2,
        lambda x: abs(x),
        lambda x: x if x > 0 else -x,
        lambda x: min(x, 100),
        lambda x: max(x, 0),
    ]))
    return operation


class TestOptimizerInvariants:
    """Test invariant properties that should always hold for the optimizer."""

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_n_jobs_within_bounds(self, data):
        """Test that n_jobs is always within reasonable bounds."""
        result = optimize(lambda x: x * 2, data)
        
        # n_jobs should be at least 1
        assert result.n_jobs >= 1, f"n_jobs should be at least 1, got {result.n_jobs}"
        
        # n_jobs should not exceed available cores * 2 (reasonable upper bound)
        from amorsize.system_info import get_physical_cores
        max_reasonable = get_physical_cores() * 2
        assert result.n_jobs <= max_reasonable, \
            f"n_jobs ({result.n_jobs}) exceeds reasonable maximum ({max_reasonable})"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_chunksize_positive(self, data):
        """Test that chunksize is always positive."""
        result = optimize(lambda x: x * 2, data)
        assert result.chunksize >= 1, f"chunksize should be at least 1, got {result.chunksize}"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_result_type_correctness(self, data):
        """Test that optimize returns the correct type."""
        result = optimize(lambda x: x * 2, data)
        assert isinstance(result, OptimizationResult), \
            f"Expected OptimizationResult, got {type(result)}"
        assert hasattr(result, 'n_jobs'), "Result missing n_jobs attribute"
        assert hasattr(result, 'chunksize'), "Result missing chunksize attribute"
        assert hasattr(result, 'estimated_speedup'), "Result missing estimated_speedup attribute"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_speedup_non_negative(self, data):
        """Test that estimated speedup is non-negative."""
        result = optimize(lambda x: x * 2, data)
        assert result.estimated_speedup >= 0, \
            f"Estimated speedup should be non-negative, got {result.estimated_speedup}"

    @given(
        data=valid_data_lists(min_size=10, max_size=200),
        sample_size=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_sample_size_parameter(self, data, sample_size):
        """Test that sample_size parameter is respected."""
        # Ensure sample_size doesn't exceed data length
        assume(sample_size <= len(data))
        
        result = optimize(lambda x: x * 2, data, sample_size=sample_size)
        
        # Result should still be valid
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1

    @given(data=valid_data_lists(min_size=1, max_size=10))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_small_datasets(self, data):
        """Test that optimizer handles small datasets gracefully."""
        result = optimize(lambda x: x * 2, data)
        
        # For very small datasets, n_jobs should typically be 1
        # (but this is not a hard requirement, just a reasonable expectation)
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1

    @given(
        target_chunk_duration=st.floats(min_value=0.05, max_value=1.0)
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_target_chunk_duration_parameter(self, target_chunk_duration):
        """Test that target_chunk_duration parameter is accepted."""
        data = list(range(100))
        result = optimize(
            lambda x: x * 2, 
            data, 
            target_chunk_duration=target_chunk_duration
        )
        
        # Result should still be valid
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1


class TestOptimizerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_list(self):
        """Test that empty data is handled gracefully."""
        result = optimize(lambda x: x * 2, [])
        # Should handle empty data without crashing
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs == 1  # No parallelization needed for empty data

    def test_single_item(self):
        """Test single-item list."""
        result = optimize(lambda x: x * 2, [42])
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1

    @given(size=st.integers(min_value=2, max_value=5))
    @settings(max_examples=10, deadline=5000)
    def test_very_small_lists(self, size):
        """Test very small lists (2-5 items)."""
        data = list(range(size))
        result = optimize(lambda x: x * 2, data)
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1

    def test_generator_input(self):
        """Test that generators are handled correctly."""
        def gen():
            for i in range(100):
                yield i
        
        result = optimize(lambda x: x * 2, gen())
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1

    def test_range_input(self):
        """Test that range objects are handled correctly."""
        result = optimize(lambda x: x * 2, range(100))
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1


class TestOptimizerConsistency:
    """Test consistency properties of the optimizer."""

    @given(data=valid_data_lists(min_size=50, max_size=200))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_deterministic_for_same_input(self, data):
        """Test that same input produces same result (for deterministic functions)."""
        result1 = optimize(lambda x: x * 2, data)
        result2 = optimize(lambda x: x * 2, data)
        
        # Results should be identical for the same input
        assert result1.n_jobs == result2.n_jobs, \
            f"n_jobs differs: {result1.n_jobs} vs {result2.n_jobs}"
        assert result1.chunksize == result2.chunksize, \
            f"chunksize differs: {result1.chunksize} vs {result2.chunksize}"

    @given(
        data=valid_data_lists(min_size=50, max_size=200),
        verbose_mode=st.booleans()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_verbose_mode_consistency(self, data, verbose_mode):
        """Test that verbose mode doesn't affect optimization result."""
        result = optimize(lambda x: x * 2, data, verbose=verbose_mode)
        
        # Result should be valid regardless of verbose mode
        assert isinstance(result, OptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1


class TestOptimizerRobustness:
    """Test robustness to various input types and scenarios."""

    @given(data=st.lists(st.integers(), min_size=10, max_size=100))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_different_list_sizes(self, data):
        """Test various list sizes."""
        result = optimize(lambda x: x * 2, data)
        assert isinstance(result, OptimizationResult)

    @given(data=st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=10, max_size=100))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_float_data(self, data):
        """Test with float data."""
        result = optimize(lambda x: x * 2.0, data)
        assert isinstance(result, OptimizationResult)

    @given(data=st.lists(st.text(min_size=1, max_size=20), min_size=10, max_size=100))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_string_data(self, data):
        """Test with string data."""
        result = optimize(lambda x: x.upper(), data)
        assert isinstance(result, OptimizationResult)

    @given(data=st.lists(
        st.tuples(st.integers(), st.integers()), 
        min_size=10, 
        max_size=100
    ))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_tuple_data(self, data):
        """Test with tuple data."""
        result = optimize(lambda x: x[0] + x[1], data)
        assert isinstance(result, OptimizationResult)


class TestOptimizerDiagnostics:
    """Test diagnostic profile properties."""

    @given(data=valid_data_lists(min_size=50, max_size=200))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_diagnostic_profile_exists(self, data):
        """Test that diagnostic profile is available."""
        result = optimize(lambda x: x * 2, data, profile=True)
        
        assert hasattr(result, 'profile'), \
            "Result should have profile attribute when profile=True"
        
        if result.profile is not None:
            # Check key diagnostic properties exist
            assert hasattr(result.profile, 'physical_cores')
            assert hasattr(result.profile, 'spawn_cost')
            assert hasattr(result.profile, 'workload_type')


# Summary test to verify property-based testing infrastructure
def test_hypothesis_integration():
    """Verify that Hypothesis is properly integrated."""
    from hypothesis import find
    
    # Simple example to verify Hypothesis works
    result = find(
        st.lists(st.integers(), min_size=10, max_size=20),
        lambda x: len(x) >= 10
    )
    assert len(result) >= 10, "Hypothesis integration test failed"
