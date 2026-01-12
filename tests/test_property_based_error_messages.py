"""
Property-based tests for error_messages module using Hypothesis.

This module tests error message generation using property-based testing to
automatically generate thousands of edge cases for:
- Message generation functions with various inputs
- Message structure and formatting invariants
- Parameter handling (None, edge cases, types)
- Warning formatting with different types
- Message content validation
- Error message integration
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from amorsize.error_messages import (
    get_picklability_error_message,
    get_data_picklability_error_message,
    get_memory_constraint_message,
    get_no_speedup_benefit_message,
    get_workload_too_small_message,
    get_sampling_failure_message,
    format_warning_with_guidance,
    get_helpful_tips,
)


# ============================================================================
# Custom Hypothesis Strategies
# ============================================================================

@st.composite
def function_name_strategy(draw):
    """Generate valid function names."""
    return draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        )
    ))


@st.composite
def error_type_strategy(draw):
    """Generate common error type names."""
    return draw(st.sampled_from([
        "PicklingError",
        "AttributeError",
        "TypeError",
        "ValueError",
        "RuntimeError",
        "ImportError",
        None
    ]))


@st.composite
def exception_strategy(draw):
    """Generate exception objects."""
    error_class = draw(st.sampled_from([
        ValueError,
        RuntimeError,
        TypeError,
        AttributeError,
        ImportError,
    ]))
    message = draw(st.text(min_size=1, max_size=100))
    return error_class(message)


# ============================================================================
# Test: Picklability Error Messages
# ============================================================================

class TestPicklabilityErrorMessageProperties:
    """Property-based tests for picklability error messages."""

    @given(function_name=st.one_of(st.none(), function_name_strategy()))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_picklability_message_structure(self, function_name):
        """Picklability error message should have consistent structure."""
        message = get_picklability_error_message(function_name=function_name)
        
        # Message should be non-empty string
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Should have key sections
        assert "COMMON CAUSES:" in message
        assert "SOLUTIONS:" in message
        
        # Should be multi-line
        assert "\n" in message

    @given(function_name=function_name_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_picklability_message_includes_function_name(self, function_name):
        """Picklability message should include function name when provided."""
        message = get_picklability_error_message(function_name=function_name)
        
        # Should reference the function name
        assert function_name in message or f"'{function_name}'" in message

    @given(error_type=error_type_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_picklability_message_with_error_type(self, error_type):
        """Picklability message should handle error_type parameter."""
        message = get_picklability_error_message(error_type=error_type)
        
        # Should still generate valid message regardless of error_type
        assert isinstance(message, str)
        assert len(message) > 100  # Should be substantial

    @given(st.data())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_picklability_message_has_examples(self, data):
        """Picklability message should include code examples."""
        function_name = data.draw(st.one_of(st.none(), function_name_strategy()))
        message = get_picklability_error_message(function_name=function_name)
        
        # Should have before/after markers
        assert "❌" in message
        assert "✅" in message
        
        # Should have code examples
        assert "def " in message or "lambda" in message

    @given(st.data())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_picklability_message_has_solutions(self, data):
        """Picklability message should include actionable solutions."""
        message = get_picklability_error_message()
        
        # Should mention specific solutions
        assert "cloudpickle" in message.lower()
        assert "threading" in message.lower() or "thread" in message.lower()
        assert "regular function" in message.lower()


# ============================================================================
# Test: Data Picklability Error Messages
# ============================================================================

class TestDataPicklabilityErrorMessageProperties:
    """Property-based tests for data picklability error messages."""

    @given(
        index=st.integers(min_value=0, max_value=1000000),
        error_type=error_type_strategy(),
        item_type=st.one_of(st.none(), st.text(min_size=1, max_size=50))
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_picklability_message_structure(self, index, error_type, item_type):
        """Data picklability message should have consistent structure."""
        message = get_data_picklability_error_message(
            index=index,
            error_type=error_type,
            item_type=item_type
        )
        
        # Message should be non-empty string
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Should have key sections
        assert "COMMON CAUSES:" in message
        assert "SOLUTIONS:" in message

    @given(index=st.integers(min_value=0, max_value=1000000))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_picklability_message_includes_index(self, index):
        """Data picklability message should include item index."""
        message = get_data_picklability_error_message(index=index)
        
        # Should reference the index
        assert str(index) in message
        assert "index" in message.lower()

    @given(
        index=st.integers(min_value=0, max_value=100),
        item_type=st.text(min_size=1, max_size=50)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_picklability_message_includes_type(self, index, item_type):
        """Data picklability message should include item type when provided."""
        message = get_data_picklability_error_message(
            index=index,
            item_type=item_type
        )
        
        # Should reference the type
        assert item_type in message

    @given(index=st.integers(min_value=0, max_value=100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_picklability_message_has_examples(self, index):
        """Data picklability message should include code examples."""
        message = get_data_picklability_error_message(index=index)
        
        # Should have before/after markers
        assert "❌" in message
        assert "✅" in message
        
        # Should have code examples
        assert "def " in message or "open(" in message


# ============================================================================
# Test: Memory Constraint Messages
# ============================================================================

class TestMemoryConstraintMessageProperties:
    """Property-based tests for memory constraint messages."""

    @given(
        required_mb=st.floats(min_value=1.0, max_value=100000.0),
        available_mb=st.floats(min_value=1.0, max_value=100000.0),
        optimal_workers=st.integers(min_value=1, max_value=128),
        constrained_workers=st.integers(min_value=1, max_value=128)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_memory_constraint_message_structure(
        self, required_mb, available_mb, optimal_workers, constrained_workers
    ):
        """Memory constraint message should have consistent structure."""
        message = get_memory_constraint_message(
            required_mb=required_mb,
            available_mb=available_mb,
            optimal_workers=optimal_workers,
            constrained_workers=constrained_workers
        )
        
        # Message should be non-empty string
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Should have key section
        assert "SOLUTIONS:" in message

    @given(
        required_mb=st.floats(min_value=1.0, max_value=10000.0),
        available_mb=st.floats(min_value=1.0, max_value=10000.0),
        optimal_workers=st.integers(min_value=1, max_value=64),
        constrained_workers=st.integers(min_value=1, max_value=64)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_memory_constraint_message_includes_metrics(
        self, required_mb, available_mb, optimal_workers, constrained_workers
    ):
        """Memory constraint message should include all metrics."""
        message = get_memory_constraint_message(
            required_mb=required_mb,
            available_mb=available_mb,
            optimal_workers=optimal_workers,
            constrained_workers=constrained_workers
        )
        
        # Should reference worker counts
        assert str(optimal_workers) in message
        assert str(constrained_workers) in message

    @given(
        required_mb=st.floats(min_value=1.0, max_value=1000.0),
        available_mb=st.floats(min_value=1.0, max_value=1000.0),
        optimal_workers=st.integers(min_value=2, max_value=32),
        constrained_workers=st.integers(min_value=1, max_value=32)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_memory_constraint_message_has_solutions(
        self, required_mb, available_mb, optimal_workers, constrained_workers
    ):
        """Memory constraint message should include actionable solutions."""
        message = get_memory_constraint_message(
            required_mb=required_mb,
            available_mb=available_mb,
            optimal_workers=optimal_workers,
            constrained_workers=constrained_workers
        )
        
        # Should mention specific solutions
        assert "batch" in message.lower() or "batches" in message.lower()
        assert "streaming" in message.lower()
        assert "memory" in message.lower()


# ============================================================================
# Test: No Speedup Benefit Messages
# ============================================================================

class TestNoSpeedupBenefitMessageProperties:
    """Property-based tests for no speedup benefit messages."""

    @given(
        estimated_speedup=st.floats(min_value=0.5, max_value=1.5),
        avg_function_time_ms=st.floats(min_value=0.01, max_value=1000.0),
        overhead_ms=st.floats(min_value=0.1, max_value=10000.0),
        min_function_time_ms=st.floats(min_value=1.0, max_value=10000.0)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_no_speedup_message_structure(
        self, estimated_speedup, avg_function_time_ms, overhead_ms, min_function_time_ms
    ):
        """No speedup message should have consistent structure."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=estimated_speedup,
            avg_function_time_ms=avg_function_time_ms,
            overhead_ms=overhead_ms,
            min_function_time_ms=min_function_time_ms
        )
        
        # Message should be non-empty string
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Should have key sections
        assert "WHY THIS HAPPENS:" in message
        assert "SOLUTIONS:" in message

    @given(
        estimated_speedup=st.floats(min_value=0.8, max_value=1.2),
        avg_function_time_ms=st.floats(min_value=0.1, max_value=100.0),
        overhead_ms=st.floats(min_value=1.0, max_value=1000.0),
        min_function_time_ms=st.floats(min_value=10.0, max_value=1000.0)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_no_speedup_message_includes_metrics(
        self, estimated_speedup, avg_function_time_ms, overhead_ms, min_function_time_ms
    ):
        """No speedup message should include timing metrics."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=estimated_speedup,
            avg_function_time_ms=avg_function_time_ms,
            overhead_ms=overhead_ms,
            min_function_time_ms=min_function_time_ms
        )
        
        # Should reference some metrics
        assert "speedup" in message.lower()
        assert "overhead" in message.lower()

    @given(
        estimated_speedup=st.floats(min_value=0.5, max_value=1.5),
        avg_function_time_ms=st.floats(min_value=0.1, max_value=100.0),
        overhead_ms=st.floats(min_value=1.0, max_value=1000.0),
        min_function_time_ms=st.floats(min_value=10.0, max_value=1000.0)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_no_speedup_message_has_examples(
        self, estimated_speedup, avg_function_time_ms, overhead_ms, min_function_time_ms
    ):
        """No speedup message should include code examples."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=estimated_speedup,
            avg_function_time_ms=avg_function_time_ms,
            overhead_ms=overhead_ms,
            min_function_time_ms=min_function_time_ms
        )
        
        # Should have before/after markers
        assert "❌" in message
        assert "✅" in message
        
        # Should have code examples
        assert "def " in message


# ============================================================================
# Test: Workload Too Small Messages
# ============================================================================

class TestWorkloadTooSmallMessageProperties:
    """Property-based tests for workload too small messages."""

    @given(
        total_items=st.integers(min_value=1, max_value=1000),
        speedup_with_2_workers=st.floats(min_value=0.5, max_value=2.0),
        min_items_recommended=st.integers(min_value=10, max_value=10000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_workload_too_small_message_structure(
        self, total_items, speedup_with_2_workers, min_items_recommended
    ):
        """Workload too small message should have consistent structure."""
        message = get_workload_too_small_message(
            total_items=total_items,
            speedup_with_2_workers=speedup_with_2_workers,
            min_items_recommended=min_items_recommended
        )
        
        # Message should be non-empty string
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Should have key sections
        assert "WHY THIS HAPPENS:" in message
        assert "SOLUTIONS:" in message

    @given(
        total_items=st.integers(min_value=1, max_value=1000),
        speedup_with_2_workers=st.floats(min_value=0.8, max_value=1.5),
        min_items_recommended=st.integers(min_value=10, max_value=1000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_workload_too_small_message_includes_metrics(
        self, total_items, speedup_with_2_workers, min_items_recommended
    ):
        """Workload too small message should include item counts."""
        message = get_workload_too_small_message(
            total_items=total_items,
            speedup_with_2_workers=speedup_with_2_workers,
            min_items_recommended=min_items_recommended
        )
        
        # Should reference item counts
        assert str(total_items) in message
        assert str(min_items_recommended) in message

    @given(
        total_items=st.integers(min_value=1, max_value=100),
        speedup_with_2_workers=st.floats(min_value=0.9, max_value=1.2),
        min_items_recommended=st.integers(min_value=50, max_value=500)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_workload_too_small_message_has_solutions(
        self, total_items, speedup_with_2_workers, min_items_recommended
    ):
        """Workload too small message should include actionable solutions."""
        message = get_workload_too_small_message(
            total_items=total_items,
            speedup_with_2_workers=speedup_with_2_workers,
            min_items_recommended=min_items_recommended
        )
        
        # Should mention increasing dataset
        assert "increase" in message.lower() or "larger" in message.lower()


# ============================================================================
# Test: Sampling Failure Messages
# ============================================================================

class TestSamplingFailureMessageProperties:
    """Property-based tests for sampling failure messages."""

    @given(error=exception_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sampling_failure_message_structure(self, error):
        """Sampling failure message should have consistent structure."""
        message = get_sampling_failure_message(error)
        
        # Message should be non-empty string
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Should have key sections
        assert "COMMON CAUSES:" in message
        assert "SOLUTIONS:" in message

    @given(error=exception_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sampling_failure_message_includes_error_info(self, error):
        """Sampling failure message should include error information."""
        message = get_sampling_failure_message(error)
        
        # Should reference error type
        error_name = type(error).__name__
        assert error_name in message

    @given(error=exception_strategy())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sampling_failure_message_has_debugging_steps(self, error):
        """Sampling failure message should include debugging guidance."""
        message = get_sampling_failure_message(error)
        
        # Should mention testing and validation
        assert "test" in message.lower() or "validate" in message.lower()
        assert "verbose" in message.lower()


# ============================================================================
# Test: Warning Formatting
# ============================================================================

class TestWarningFormattingProperties:
    """Property-based tests for warning formatting."""

    @given(warning_type=st.sampled_from([
        'io_bound', 'heterogeneous', 'nested_parallelism', 'memory_pressure'
    ]))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_warning_formatting_returns_list(self, warning_type):
        """Warning formatting should return list of strings."""
        warnings = format_warning_with_guidance(warning_type)
        
        # Should return list
        assert isinstance(warnings, list)
        assert len(warnings) > 0
        
        # All items should be strings
        assert all(isinstance(w, str) for w in warnings)

    @given(cv=st.floats(min_value=0.0, max_value=2.0))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_heterogeneous_warning_includes_cv(self, cv):
        """Heterogeneous warning should include CV value."""
        warnings = format_warning_with_guidance('heterogeneous', cv=cv)
        
        # Should have content
        assert len(warnings) > 0
        
        # Should mention heterogeneous
        warning_text = ' '.join(warnings)
        assert 'heterogeneous' in warning_text.lower() or 'cv' in warning_text.lower()

    @given(internal_threads=st.integers(min_value=1, max_value=128))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_nested_parallelism_warning_includes_threads(self, internal_threads):
        """Nested parallelism warning should include thread count."""
        warnings = format_warning_with_guidance(
            'nested_parallelism',
            internal_threads=internal_threads
        )
        
        # Should have content
        assert len(warnings) > 0
        
        # Should mention environment variables
        warning_text = ' '.join(warnings)
        assert 'threads' in warning_text.lower() or 'omp' in warning_text.lower()

    def test_io_bound_warning_mentions_threading(self):
        """I/O bound warning should mention threading."""
        warnings = format_warning_with_guidance('io_bound')
        
        warning_text = ' '.join(warnings)
        assert 'thread' in warning_text.lower()

    def test_memory_pressure_warning_mentions_streaming(self):
        """Memory pressure warning should mention streaming/batching."""
        warnings = format_warning_with_guidance('memory_pressure')
        
        warning_text = ' '.join(warnings)
        assert 'streaming' in warning_text.lower() or 'batch' in warning_text.lower()


# ============================================================================
# Test: Helpful Tips
# ============================================================================

class TestHelpfulTipsProperties:
    """Property-based tests for helpful tips."""

    def test_helpful_tips_structure(self):
        """Helpful tips should have consistent structure."""
        tips = get_helpful_tips()
        
        # Should be non-empty string
        assert isinstance(tips, str)
        assert len(tips) > 0
        
        # Should have multiple tips
        assert "1." in tips
        assert "2." in tips

    def test_helpful_tips_has_examples(self):
        """Helpful tips should include code examples."""
        tips = get_helpful_tips()
        
        # Should have code examples
        assert "optimize(" in tips
        assert "from amorsize import" in tips

    def test_helpful_tips_mentions_key_features(self):
        """Helpful tips should mention key features."""
        tips = get_helpful_tips()
        
        # Should mention important features
        assert "profile" in tips.lower() or "profiling" in tips.lower()
        assert "cache" in tips.lower() or "caching" in tips.lower()


# ============================================================================
# Test: Message Content Quality
# ============================================================================

class TestMessageContentQualityProperties:
    """Property-based tests for overall message quality."""

    @given(st.data())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_messages_are_substantial(self, data):
        """All error messages should be substantial (not too short)."""
        # Test each message type
        messages = [
            get_picklability_error_message(),
            get_data_picklability_error_message(0),
            get_memory_constraint_message(100.0, 1000.0, 8, 2),
            get_no_speedup_benefit_message(1.1, 5.0, 50.0, 60.0),
            get_workload_too_small_message(10, 1.05, 50),
            get_sampling_failure_message(ValueError("test")),
            get_helpful_tips()
        ]
        
        for message in messages:
            # Each should be substantial
            assert len(message) > 100
            
            # Should be multi-line
            assert "\n" in message

    @given(
        function_name=st.one_of(st.none(), function_name_strategy()),
        error_type=error_type_strategy()
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_messages_handle_none_parameters(self, function_name, error_type):
        """Messages should handle None parameters gracefully."""
        # Should not raise exceptions with None parameters
        message = get_picklability_error_message(
            function_name=function_name,
            error_type=error_type
        )
        
        assert isinstance(message, str)
        assert len(message) > 0

    @given(
        index=st.integers(min_value=0, max_value=1000),
        error_type=error_type_strategy(),
        item_type=st.one_of(st.none(), st.text(min_size=1, max_size=50))
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_message_handles_optional_parameters(
        self, index, error_type, item_type
    ):
        """Data picklability message should handle optional parameters."""
        # Should not raise exceptions
        message = get_data_picklability_error_message(
            index=index,
            error_type=error_type,
            item_type=item_type
        )
        
        assert isinstance(message, str)
        assert len(message) > 0


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestEdgeCasesProperties:
    """Property-based tests for edge cases."""

    def test_zero_index_data_picklability(self):
        """Data picklability should handle index 0."""
        message = get_data_picklability_error_message(0)
        
        assert "0" in message
        assert isinstance(message, str)

    @given(index=st.integers(min_value=1000000, max_value=10000000))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_large_index_data_picklability(self, index):
        """Data picklability should handle very large indices."""
        message = get_data_picklability_error_message(index)
        
        assert str(index) in message

    @given(
        required_mb=st.floats(min_value=0.001, max_value=0.1),
        available_mb=st.floats(min_value=100000.0, max_value=1000000.0)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_extreme_memory_ratios(self, required_mb, available_mb):
        """Memory constraint message should handle extreme ratios."""
        message = get_memory_constraint_message(
            required_mb=required_mb,
            available_mb=available_mb,
            optimal_workers=128,
            constrained_workers=1
        )
        
        assert isinstance(message, str)
        assert len(message) > 0

    @given(speedup=st.floats(min_value=0.01, max_value=0.5))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_very_low_speedup(self, speedup):
        """No speedup message should handle very low speedup values."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=speedup,
            avg_function_time_ms=1.0,
            overhead_ms=100.0,
            min_function_time_ms=150.0
        )
        
        assert isinstance(message, str)
        assert "speedup" in message.lower()

    def test_single_item_workload(self):
        """Workload too small message should handle single item."""
        message = get_workload_too_small_message(
            total_items=1,
            speedup_with_2_workers=0.9,
            min_items_recommended=100
        )
        
        assert "1" in message
        assert isinstance(message, str)

    @given(error_message=st.text(min_size=0, max_size=1000))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_sampling_failure_with_various_error_messages(self, error_message):
        """Sampling failure should handle various error message lengths."""
        error = RuntimeError(error_message)
        message = get_sampling_failure_message(error)
        
        assert isinstance(message, str)
        assert "RuntimeError" in message


# ============================================================================
# Test: Integration Properties
# ============================================================================

class TestIntegrationProperties:
    """Property-based tests for message integration scenarios."""

    @given(
        function_name=st.one_of(st.none(), function_name_strategy()),
        index=st.integers(min_value=0, max_value=1000)
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_message_generation(self, function_name, index):
        """Multiple messages can be generated without conflicts."""
        msg1 = get_picklability_error_message(function_name=function_name)
        msg2 = get_data_picklability_error_message(index=index)
        
        # Both should be valid
        assert isinstance(msg1, str) and len(msg1) > 0
        assert isinstance(msg2, str) and len(msg2) > 0
        
        # Should be different
        assert msg1 != msg2

    @given(
        warning_types=st.lists(
            st.sampled_from(['io_bound', 'heterogeneous', 'nested_parallelism', 'memory_pressure']),
            min_size=1,
            max_size=4,
            unique=True
        )
    )
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_warning_formats(self, warning_types):
        """Multiple warnings can be formatted without conflicts."""
        all_warnings = []
        for warning_type in warning_types:
            warnings = format_warning_with_guidance(warning_type)
            all_warnings.extend(warnings)
        
        # All should be valid strings
        assert all(isinstance(w, str) for w in all_warnings)
        assert len(all_warnings) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
