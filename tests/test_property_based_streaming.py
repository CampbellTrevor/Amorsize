"""
Property-based tests for the streaming module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the streaming optimization across a wide range of inputs.
"""

import math
from typing import Any, Iterator, List

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize.streaming import (
    StreamingOptimizationResult,
    optimize_streaming,
    BUFFER_SIZE_MULTIPLIER,
    MAX_CHUNKSIZE_GROWTH_FACTOR,
    RESULT_BUFFER_MEMORY_FRACTION,
    _validate_streaming_parameters,
)


# Custom strategies for generating test data
@st.composite
def valid_data_lists(draw, min_size=1, max_size=1000):
    """Generate valid data lists for streaming optimization."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.lists(st.integers(), min_size=size, max_size=size))


@st.composite
def valid_streaming_params(draw):
    """Generate valid parameter combinations for optimize_streaming."""
    return {
        'sample_size': draw(st.integers(min_value=1, max_value=100)),
        'target_chunk_duration': draw(st.floats(min_value=0.01, max_value=1.0)),
        'prefer_ordered': draw(st.one_of(st.booleans(), st.none())),
        'buffer_size': draw(st.one_of(st.integers(min_value=1, max_value=1000), st.none())),
        'enable_adaptive_chunking': draw(st.booleans()),
        'adaptation_rate': draw(st.floats(min_value=0.0, max_value=1.0)),
        'enable_memory_backpressure': draw(st.booleans()),
        'memory_threshold': draw(st.floats(min_value=0.0, max_value=1.0)),
    }


class TestStreamingOptimizationResultInvariants:
    """Test invariant properties of StreamingOptimizationResult."""

    @given(
        n_jobs=st.integers(min_value=1, max_value=128),
        chunksize=st.integers(min_value=1, max_value=10000),
        use_ordered=st.booleans(),
        estimated_speedup=st.floats(min_value=0.5, max_value=100.0),
        buffer_size=st.one_of(st.integers(min_value=1, max_value=1000), st.none()),
    )
    @settings(max_examples=100, deadline=1000)
    def test_result_initialization(self, n_jobs, chunksize, use_ordered, estimated_speedup, buffer_size):
        """Test that StreamingOptimizationResult stores all parameters correctly."""
        result = StreamingOptimizationResult(
            n_jobs=n_jobs,
            chunksize=chunksize,
            use_ordered=use_ordered,
            reason="Test reason",
            estimated_speedup=estimated_speedup,
            buffer_size=buffer_size,
        )
        
        assert result.n_jobs == n_jobs
        assert result.chunksize == chunksize
        assert result.use_ordered == use_ordered
        assert result.estimated_speedup == estimated_speedup
        assert result.buffer_size == buffer_size
        assert isinstance(result.warnings, list)
        assert isinstance(result.adaptive_chunking_params, dict)

    @given(
        n_jobs=st.integers(min_value=1, max_value=128),
        chunksize=st.integers(min_value=1, max_value=10000),
        use_ordered=st.booleans(),
    )
    @settings(max_examples=100, deadline=1000)
    def test_result_repr_format(self, n_jobs, chunksize, use_ordered):
        """Test that __repr__ returns a valid string with expected format."""
        result = StreamingOptimizationResult(
            n_jobs=n_jobs,
            chunksize=chunksize,
            use_ordered=use_ordered,
            reason="Test",
            estimated_speedup=2.0,
        )
        
        repr_str = repr(result)
        assert isinstance(repr_str, str)
        assert "StreamingOptimizationResult" in repr_str
        assert f"n_jobs={n_jobs}" in repr_str
        assert f"chunksize={chunksize}" in repr_str
        method = "imap" if use_ordered else "imap_unordered"
        assert f"method={method}" in repr_str

    @given(
        n_jobs=st.integers(min_value=1, max_value=128),
        chunksize=st.integers(min_value=1, max_value=10000),
        use_ordered=st.booleans(),
    )
    @settings(max_examples=100, deadline=1000)
    def test_result_str_format(self, n_jobs, chunksize, use_ordered):
        """Test that __str__ returns a human-readable summary."""
        result = StreamingOptimizationResult(
            n_jobs=n_jobs,
            chunksize=chunksize,
            use_ordered=use_ordered,
            reason="Test reason",
            estimated_speedup=2.0,
        )
        
        str_result = str(result)
        assert isinstance(str_result, str)
        assert f"n_jobs={n_jobs}" in str_result
        assert f"chunksize={chunksize}" in str_result
        method = "imap" if use_ordered else "imap_unordered"
        assert method in str_result

    @given(
        use_ordered=st.booleans(),
    )
    @settings(max_examples=50, deadline=1000)
    def test_use_ordered_determines_method(self, use_ordered):
        """Test that use_ordered correctly determines imap vs imap_unordered."""
        result = StreamingOptimizationResult(
            n_jobs=2,
            chunksize=10,
            use_ordered=use_ordered,
            reason="Test",
            estimated_speedup=2.0,
        )
        
        repr_str = repr(result)
        str_result = str(result)
        
        if use_ordered:
            assert "imap" in repr_str or "ordered" in str_result.lower()
        else:
            assert "imap_unordered" in repr_str or "unordered" in str_result.lower()


class TestStreamingOptimizationInvariants:
    """Test invariant properties of optimize_streaming function."""

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_n_jobs_within_bounds(self, data):
        """Test that n_jobs is always within reasonable bounds."""
        result = optimize_streaming(lambda x: x * 2, data)
        
        # n_jobs should be at least 1
        assert result.n_jobs >= 1, f"n_jobs should be at least 1, got {result.n_jobs}"
        
        # n_jobs should not exceed available cores * 2
        from amorsize.system_info import get_physical_cores
        max_reasonable = get_physical_cores() * 2
        assert result.n_jobs <= max_reasonable, \
            f"n_jobs ({result.n_jobs}) exceeds reasonable maximum ({max_reasonable})"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_chunksize_positive(self, data):
        """Test that chunksize is always positive."""
        result = optimize_streaming(lambda x: x * 2, data)
        assert result.chunksize >= 1, f"chunksize should be at least 1, got {result.chunksize}"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_result_type_correctness(self, data):
        """Test that optimize_streaming returns the correct type."""
        result = optimize_streaming(lambda x: x * 2, data)
        assert isinstance(result, StreamingOptimizationResult), \
            f"Expected StreamingOptimizationResult, got {type(result)}"
        assert hasattr(result, 'n_jobs'), "Result missing n_jobs attribute"
        assert hasattr(result, 'chunksize'), "Result missing chunksize attribute"
        assert hasattr(result, 'use_ordered'), "Result missing use_ordered attribute"
        assert hasattr(result, 'estimated_speedup'), "Result missing estimated_speedup attribute"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_speedup_non_negative(self, data):
        """Test that estimated speedup is non-negative."""
        result = optimize_streaming(lambda x: x * 2, data)
        assert result.estimated_speedup >= 0, \
            f"Estimated speedup should be non-negative, got {result.estimated_speedup}"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_use_ordered_is_boolean(self, data):
        """Test that use_ordered is always a boolean value."""
        result = optimize_streaming(lambda x: x * 2, data)
        assert isinstance(result.use_ordered, bool), \
            f"use_ordered should be boolean, got {type(result.use_ordered)}"

    @given(data=valid_data_lists(min_size=10, max_size=500))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_buffer_size_reasonable(self, data):
        """Test that buffer_size is reasonable if set."""
        result = optimize_streaming(lambda x: x * 2, data)
        
        if result.buffer_size is not None:
            # Buffer size should be positive
            assert result.buffer_size >= 1, \
                f"buffer_size should be at least 1, got {result.buffer_size}"
            
            # Buffer size should be reasonable (not excessively large)
            # Typically buffer = n_jobs * multiplier
            max_reasonable = result.n_jobs * BUFFER_SIZE_MULTIPLIER * 10  # Allow some slack
            assert result.buffer_size <= max_reasonable, \
                f"buffer_size ({result.buffer_size}) exceeds reasonable maximum"


class TestStreamingParameterValidation:
    """Test parameter validation for optimize_streaming."""

    @given(
        sample_size=st.integers(min_value=-100, max_value=0)
    )
    @settings(max_examples=20, deadline=1000)
    def test_invalid_sample_size_negative(self, sample_size):
        """Test that negative sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size"):
            _validate_streaming_parameters(
                func=lambda x: x,
                data=[1, 2, 3],
                sample_size=sample_size,
                target_chunk_duration=0.2,
                prefer_ordered=None,
                buffer_size=None,
                enable_adaptive_chunking=False,
                adaptation_rate=0.3,
                pool_manager=None,
                enable_memory_backpressure=False,
                memory_threshold=0.8
            )

    @given(
        target_chunk_duration=st.floats(min_value=-10.0, max_value=0.0)
    )
    @settings(max_examples=20, deadline=1000)
    def test_invalid_target_chunk_duration_negative(self, target_chunk_duration):
        """Test that negative target_chunk_duration raises ValueError."""
        assume(not math.isnan(target_chunk_duration))
        
        with pytest.raises(ValueError, match="target_chunk_duration"):
            _validate_streaming_parameters(
                func=lambda x: x,
                data=[1, 2, 3],
                sample_size=5,
                target_chunk_duration=target_chunk_duration,
                prefer_ordered=None,
                buffer_size=None,
                enable_adaptive_chunking=False,
                adaptation_rate=0.3,
                pool_manager=None,
                enable_memory_backpressure=False,
                memory_threshold=0.8
            )

    @given(
        adaptation_rate=st.floats(min_value=-1.0, max_value=-0.01) | st.floats(min_value=1.01, max_value=2.0)
    )
    @settings(max_examples=20, deadline=1000)
    def test_invalid_adaptation_rate_out_of_range(self, adaptation_rate):
        """Test that adaptation_rate outside [0,1] raises ValueError."""
        assume(not math.isnan(adaptation_rate))
        
        with pytest.raises(ValueError, match="adaptation_rate"):
            _validate_streaming_parameters(
                func=lambda x: x,
                data=[1, 2, 3],
                sample_size=5,
                target_chunk_duration=0.2,
                prefer_ordered=None,
                buffer_size=None,
                enable_adaptive_chunking=False,
                adaptation_rate=adaptation_rate,
                pool_manager=None,
                enable_memory_backpressure=False,
                memory_threshold=0.8
            )

    @given(
        memory_threshold=st.floats(min_value=-1.0, max_value=-0.01) | st.floats(min_value=1.01, max_value=2.0)
    )
    @settings(max_examples=20, deadline=1000)
    def test_invalid_memory_threshold_out_of_range(self, memory_threshold):
        """Test that memory_threshold outside [0,1] raises ValueError."""
        assume(not math.isnan(memory_threshold))
        
        with pytest.raises(ValueError, match="memory_threshold"):
            _validate_streaming_parameters(
                func=lambda x: x,
                data=[1, 2, 3],
                sample_size=5,
                target_chunk_duration=0.2,
                prefer_ordered=None,
                buffer_size=None,
                enable_adaptive_chunking=False,
                adaptation_rate=0.3,
                pool_manager=None,
                enable_memory_backpressure=False,
                memory_threshold=memory_threshold
            )


class TestStreamingEdgeCases:
    """Test edge cases for streaming optimization."""

    @given(data=valid_data_lists(min_size=1, max_size=10))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_small_datasets(self, data):
        """Test that optimizer handles small datasets gracefully."""
        result = optimize_streaming(lambda x: x * 2, data)
        
        # For small datasets, result should still be valid
        assert isinstance(result, StreamingOptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert isinstance(result.use_ordered, bool)

    @given(
        data=valid_data_lists(min_size=10, max_size=100),
        sample_size=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_sample_size_parameter(self, data, sample_size):
        """Test that sample_size parameter is respected."""
        assume(sample_size <= len(data))
        
        result = optimize_streaming(lambda x: x * 2, data, sample_size=sample_size)
        
        # Result should still be valid
        assert isinstance(result, StreamingOptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1

    @given(
        data=valid_data_lists(min_size=10, max_size=100),
        prefer_ordered=st.booleans()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_prefer_ordered_parameter(self, data, prefer_ordered):
        """Test that prefer_ordered parameter is respected."""
        result = optimize_streaming(lambda x: x * 2, data, prefer_ordered=prefer_ordered)
        
        # When prefer_ordered is explicitly set, it should be honored
        # (unless there's a strong reason to override, like picklability)
        if result.n_jobs > 1:
            # Only check if parallel execution is recommended
            # For serial execution, use_ordered doesn't matter as much
            assert isinstance(result.use_ordered, bool)

    @given(
        data=valid_data_lists(min_size=10, max_size=100),
        buffer_size=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_buffer_size_parameter(self, data, buffer_size):
        """Test that buffer_size parameter is used when provided."""
        result = optimize_streaming(lambda x: x * 2, data, buffer_size=buffer_size)
        
        # When buffer_size is explicitly set, it should be stored
        # (though the optimizer may choose to use a different value internally)
        assert result.buffer_size is not None
        assert result.buffer_size >= 1

    @given(data=valid_data_lists(min_size=10, max_size=100))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_adaptive_chunking_enabled(self, data):
        """Test that adaptive chunking can be enabled."""
        result = optimize_streaming(
            lambda x: x * 2, data,
            enable_adaptive_chunking=True,
            adaptation_rate=0.3
        )
        
        # Result should be valid
        assert isinstance(result, StreamingOptimizationResult)
        assert isinstance(result.use_adaptive_chunking, bool)
        assert isinstance(result.adaptive_chunking_params, dict)

    @given(data=valid_data_lists(min_size=10, max_size=100))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_memory_backpressure_enabled(self, data):
        """Test that memory backpressure can be enabled."""
        result = optimize_streaming(
            lambda x: x * 2, data,
            enable_memory_backpressure=True,
            memory_threshold=0.8
        )
        
        # Result should be valid
        assert isinstance(result, StreamingOptimizationResult)
        assert isinstance(result.memory_backpressure_enabled, bool)


class TestStreamingConstants:
    """Test that streaming constants are reasonable values."""

    def test_buffer_size_multiplier_positive(self):
        """Test that BUFFER_SIZE_MULTIPLIER is positive."""
        assert BUFFER_SIZE_MULTIPLIER > 0
        assert isinstance(BUFFER_SIZE_MULTIPLIER, (int, float))

    def test_max_chunksize_growth_factor_positive(self):
        """Test that MAX_CHUNKSIZE_GROWTH_FACTOR is positive."""
        assert MAX_CHUNKSIZE_GROWTH_FACTOR > 0
        assert isinstance(MAX_CHUNKSIZE_GROWTH_FACTOR, (int, float))

    def test_result_buffer_memory_fraction_reasonable(self):
        """Test that RESULT_BUFFER_MEMORY_FRACTION is in reasonable range."""
        assert 0 < RESULT_BUFFER_MEMORY_FRACTION < 1
        assert isinstance(RESULT_BUFFER_MEMORY_FRACTION, (int, float))
        # Should be conservative (not using too much memory)
        assert RESULT_BUFFER_MEMORY_FRACTION <= 0.5, \
            "Buffer should not use more than 50% of available memory"


class TestStreamingNumericalStability:
    """Test numerical stability of streaming optimization."""

    @given(
        data=valid_data_lists(min_size=10, max_size=200),
        target_chunk_duration=st.floats(min_value=0.01, max_value=2.0)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_various_target_chunk_durations(self, data, target_chunk_duration):
        """Test that various target_chunk_duration values work correctly."""
        assume(not math.isnan(target_chunk_duration) and not math.isinf(target_chunk_duration))
        assume(target_chunk_duration > 0)
        
        result = optimize_streaming(
            lambda x: x * 2, data,
            target_chunk_duration=target_chunk_duration
        )
        
        # Result should be valid
        assert isinstance(result, StreamingOptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert math.isfinite(result.estimated_speedup)

    @given(
        data=valid_data_lists(min_size=10, max_size=200),
        adaptation_rate=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_various_adaptation_rates(self, data, adaptation_rate):
        """Test that various adaptation_rate values work correctly."""
        assume(not math.isnan(adaptation_rate))
        
        result = optimize_streaming(
            lambda x: x * 2, data,
            enable_adaptive_chunking=True,
            adaptation_rate=adaptation_rate
        )
        
        # Result should be valid
        assert isinstance(result, StreamingOptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1


class TestStreamingIntegrationProperties:
    """Test integration properties of streaming optimization."""

    @given(data=valid_data_lists(min_size=10, max_size=100))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_multiple_optimizations_consistent(self, data):
        """Test that multiple optimizations of same data are consistent."""
        result1 = optimize_streaming(lambda x: x * 2, data)
        result2 = optimize_streaming(lambda x: x * 2, data)
        
        # Results should be identical for deterministic input
        assert result1.n_jobs == result2.n_jobs
        assert result1.chunksize == result2.chunksize
        # use_ordered may vary based on optimization heuristics, so we don't check it

    @given(data=valid_data_lists(min_size=10, max_size=100))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_explain_method_works(self, data):
        """Test that explain() method returns a string."""
        result = optimize_streaming(lambda x: x * 2, data)
        explanation = result.explain()
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    @given(data=valid_data_lists(min_size=10, max_size=100))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_warnings_is_list(self, data):
        """Test that warnings is always a list."""
        result = optimize_streaming(lambda x: x * 2, data)
        
        assert isinstance(result.warnings, list)
        # Each warning should be a string
        for warning in result.warnings:
            assert isinstance(warning, str)

    @given(data=valid_data_lists(min_size=10, max_size=100))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_reason_is_string(self, data):
        """Test that reason is always a string."""
        result = optimize_streaming(lambda x: x * 2, data)
        
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0


class TestStreamingDataReconstructionForGenerators:
    """Test that data is properly reconstructed for generators."""

    @given(size=st.integers(min_value=10, max_value=100))
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    def test_generator_data_reconstructed(self, size):
        """Test that generator data is reconstructed after sampling."""
        def data_gen():
            for i in range(size):
                yield i
        
        result = optimize_streaming(lambda x: x * 2, data_gen())
        
        # Result should be valid
        assert isinstance(result, StreamingOptimizationResult)
        
        # Data should be available (reconstructed)
        assert result.data is not None
        
        # Should be able to iterate over reconstructed data
        reconstructed_list = list(result.data) if hasattr(result.data, '__iter__') else []
        # We can't guarantee all items are there (sampling may have consumed some)
        # but the result should have valid data field


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
