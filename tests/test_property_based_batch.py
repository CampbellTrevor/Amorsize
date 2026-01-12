"""
Property-based tests for batch processing utilities using Hypothesis.

This module tests batch processing operations using property-based testing to
automatically generate thousands of edge cases for:
- process_in_batches() parameter validation
- Batch size calculation and memory constraints
- Result preservation across batches
- estimate_safe_batch_size() correctness
- Edge cases (empty data, single items, large datasets)
"""

import pickle
import sys
import threading
from typing import Any, List

import pytest
from hypothesis import given, strategies as st, settings, assume

from amorsize.batch import (
    process_in_batches,
    estimate_safe_batch_size,
)


# ============================================================================
# Custom Hypothesis Strategies
# ============================================================================

@st.composite
def valid_batch_size(draw):
    """Generate valid batch sizes (positive integers)."""
    return draw(st.integers(min_value=1, max_value=1000))


@st.composite
def valid_max_memory_percent(draw):
    """Generate valid memory percentages (0 < x <= 1)."""
    return draw(st.floats(min_value=0.01, max_value=1.0))


@st.composite
def valid_sample_size(draw):
    """Generate valid sample sizes (positive integers)."""
    return draw(st.integers(min_value=1, max_value=100))


@st.composite
def data_list_strategy(draw, min_size=0, max_size=500):
    """Generate test data lists of various sizes."""
    return draw(st.lists(
        st.integers(min_value=-1000, max_value=1000),
        min_size=min_size,
        max_size=max_size
    ))


# Test functions for use in property-based tests
def square(x):
    """Simple function for testing."""
    return x ** 2


def double(x):
    """Another simple function."""
    return x * 2


def identity(x):
    """Identity function."""
    return x


def returns_small_list(x):
    """Function that returns a small list."""
    return [x, x * 2]


# ============================================================================
# Test process_in_batches() Invariants
# ============================================================================

class TestProcessInBatchesInvariants:
    """Test invariants of process_in_batches function."""
    
    @given(
        data=data_list_strategy(min_size=1, max_size=100),
        batch_size=valid_batch_size()
    )
    @settings(deadline=5000)
    def test_returns_list(self, data, batch_size):
        """process_in_batches should always return a list."""
        result = process_in_batches(square, data, batch_size=batch_size)
        assert isinstance(result, list)
    
    @given(
        data=data_list_strategy(min_size=1, max_size=100),
        batch_size=valid_batch_size()
    )
    @settings(deadline=5000)
    def test_preserves_result_count(self, data, batch_size):
        """process_in_batches should return same number of results as input items."""
        result = process_in_batches(square, data, batch_size=batch_size)
        assert len(result) == len(data)
    
    @given(
        data=data_list_strategy(min_size=1, max_size=100),
        batch_size=valid_batch_size()
    )
    @settings(deadline=5000)
    def test_preserves_result_correctness(self, data, batch_size):
        """process_in_batches should produce correct results."""
        result = process_in_batches(square, data, batch_size=batch_size)
        expected = [x ** 2 for x in data]
        assert result == expected
    
    @given(
        data=data_list_strategy(min_size=1, max_size=100),
        batch_size=valid_batch_size()
    )
    @settings(deadline=5000)
    def test_preserves_order(self, data, batch_size):
        """process_in_batches should preserve input order."""
        result = process_in_batches(identity, data, batch_size=batch_size)
        assert result == data


class TestProcessInBatchesBatchSizeCalculation:
    """Test batch size calculation logic."""
    
    @given(data=data_list_strategy(min_size=1, max_size=100))
    @settings(deadline=5000)
    def test_auto_batch_size_completes(self, data):
        """Auto batch size calculation should complete successfully."""
        result = process_in_batches(square, data)  # No batch_size specified
        assert len(result) == len(data)
        assert result == [x ** 2 for x in data]
    
    @given(
        data=data_list_strategy(min_size=1, max_size=100),
        max_memory_percent=valid_max_memory_percent()
    )
    @settings(deadline=5000)
    def test_respects_max_memory_percent(self, data, max_memory_percent):
        """Auto batch size should respect max_memory_percent parameter."""
        # Just verify it completes without error
        result = process_in_batches(
            square,
            data,
            max_memory_percent=max_memory_percent
        )
        assert len(result) == len(data)
    
    @given(
        data=data_list_strategy(min_size=1, max_size=100),
        sample_size=valid_sample_size()
    )
    @settings(deadline=5000)
    def test_respects_sample_size(self, data, sample_size):
        """Auto batch size should respect sample_size parameter."""
        result = process_in_batches(
            square,
            data,
            sample_size=sample_size
        )
        assert len(result) == len(data)


class TestProcessInBatchesParameterValidation:
    """Test parameter validation for process_in_batches."""
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    def test_rejects_non_callable_func(self, data):
        """Should reject non-callable func parameter."""
        with pytest.raises(ValueError, match="func must be callable"):
            process_in_batches("not_callable", data, batch_size=10)
    
    @given(
        data=data_list_strategy(min_size=1, max_size=50),
        batch_size=st.integers(max_value=0)
    )
    def test_rejects_non_positive_batch_size(self, data, batch_size):
        """Should reject non-positive batch_size."""
        with pytest.raises(ValueError, match="batch_size must be a positive integer"):
            process_in_batches(square, data, batch_size=batch_size)
    
    @given(
        data=data_list_strategy(min_size=1, max_size=50),
        max_memory_percent=st.floats(max_value=0.0)
    )
    def test_rejects_non_positive_max_memory_percent(self, data, max_memory_percent):
        """Should reject non-positive max_memory_percent."""
        assume(max_memory_percent <= 0.0)
        with pytest.raises(ValueError, match="max_memory_percent must be between 0 and 1"):
            process_in_batches(square, data, max_memory_percent=max_memory_percent)
    
    @given(
        data=data_list_strategy(min_size=1, max_size=50),
        max_memory_percent=st.floats(min_value=1.01, max_value=10.0)
    )
    def test_rejects_max_memory_percent_above_one(self, data, max_memory_percent):
        """Should reject max_memory_percent > 1.0."""
        with pytest.raises(ValueError, match="max_memory_percent must be between 0 and 1"):
            process_in_batches(square, data, max_memory_percent=max_memory_percent)
    
    @given(
        data=data_list_strategy(min_size=1, max_size=50),
        sample_size=st.integers(max_value=0)
    )
    def test_rejects_non_positive_sample_size(self, data, sample_size):
        """Should reject non-positive sample_size."""
        with pytest.raises(ValueError, match="sample_size must be a positive integer"):
            process_in_batches(square, data, sample_size=sample_size)
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    def test_rejects_non_boolean_verbose(self, data):
        """Should reject non-boolean verbose parameter."""
        with pytest.raises(ValueError, match="verbose must be a boolean"):
            process_in_batches(square, data, batch_size=10, verbose="not_bool")


class TestProcessInBatchesEdgeCases:
    """Test edge cases for process_in_batches."""
    
    def test_empty_data(self):
        """Should handle empty data correctly."""
        result = process_in_batches(square, [], batch_size=10)
        assert result == []
    
    @given(value=st.integers())
    @settings(deadline=5000)
    def test_single_item(self, value):
        """Should handle single item correctly."""
        result = process_in_batches(square, [value], batch_size=1)
        assert result == [value ** 2]
    
    @given(value=st.integers())
    @settings(deadline=5000)
    def test_single_item_large_batch(self, value):
        """Should handle single item with large batch size."""
        result = process_in_batches(square, [value], batch_size=100)
        assert result == [value ** 2]
    
    @given(
        data=data_list_strategy(min_size=1, max_size=50),
        batch_size=st.just(1)
    )
    @settings(deadline=5000)
    def test_batch_size_one(self, data, batch_size):
        """Should handle batch size of 1."""
        result = process_in_batches(square, data, batch_size=batch_size)
        assert len(result) == len(data)
        assert result == [x ** 2 for x in data]
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_batch_size_larger_than_data(self, data):
        """Should handle batch size larger than data size."""
        batch_size = len(data) + 100
        result = process_in_batches(square, data, batch_size=batch_size)
        assert len(result) == len(data)
        assert result == [x ** 2 for x in data]
    
    @given(data=data_list_strategy(min_size=2, max_size=100))
    @settings(deadline=5000)
    def test_exact_multiple_batches(self, data):
        """Should handle data size exactly divisible by batch size."""
        # Make data size a multiple of 10
        data = data[:len(data) // 10 * 10]
        assume(len(data) >= 10)
        result = process_in_batches(square, data, batch_size=10)
        assert len(result) == len(data)
        assert result == [x ** 2 for x in data]
    
    @given(data=data_list_strategy(min_size=1, max_size=100))
    @settings(deadline=5000)
    def test_uneven_batches(self, data):
        """Should handle data size not divisible by batch size."""
        # Make sure we have remainder
        data = data[:len(data) // 7 * 7 + 3] if len(data) > 3 else data
        result = process_in_batches(square, data, batch_size=7)
        assert len(result) == len(data)
        assert result == [x ** 2 for x in data]


class TestProcessInBatchesVerboseMode:
    """Test verbose mode output."""
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_verbose_true_completes(self, data):
        """Should complete with verbose=True."""
        result = process_in_batches(square, data, batch_size=10, verbose=True)
        assert len(result) == len(data)
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_verbose_false_completes(self, data):
        """Should complete with verbose=False."""
        result = process_in_batches(square, data, batch_size=10, verbose=False)
        assert len(result) == len(data)


class TestProcessInBatchesDifferentFunctions:
    """Test with different function types."""
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_identity_function(self, data):
        """Should work with identity function."""
        result = process_in_batches(identity, data, batch_size=10)
        assert result == data
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_double_function(self, data):
        """Should work with different functions."""
        result = process_in_batches(double, data, batch_size=10)
        assert result == [x * 2 for x in data]
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_function_returning_list(self, data):
        """Should work with functions returning complex objects."""
        result = process_in_batches(returns_small_list, data, batch_size=10)
        assert len(result) == len(data)
        assert all(isinstance(r, list) for r in result)
        assert all(r == [x, x * 2] for r, x in zip(result, data))


# ============================================================================
# Test estimate_safe_batch_size()
# ============================================================================

class TestEstimateSafeBatchSize:
    """Test estimate_safe_batch_size function."""
    
    @given(
        result_size=st.integers(min_value=1, max_value=1_000_000_000),
        max_memory_percent=valid_max_memory_percent()
    )
    def test_returns_positive_integer(self, result_size, max_memory_percent):
        """estimate_safe_batch_size should return positive integer."""
        batch_size = estimate_safe_batch_size(result_size, max_memory_percent)
        assert isinstance(batch_size, int)
        assert batch_size >= 1
    
    @given(
        result_size=st.integers(min_value=1, max_value=1_000_000),
        max_memory_percent=valid_max_memory_percent()
    )
    def test_inverse_relationship_with_result_size(self, result_size, max_memory_percent):
        """Larger result sizes should give smaller batch sizes."""
        small_result = result_size
        large_result = result_size * 10
        
        small_batch = estimate_safe_batch_size(small_result, max_memory_percent)
        large_batch = estimate_safe_batch_size(large_result, max_memory_percent)
        
        # Larger results should give smaller or equal batch sizes
        assert large_batch <= small_batch
    
    @given(
        result_size=st.integers(min_value=1, max_value=1_000_000)
    )
    def test_inverse_relationship_with_memory_percent(self, result_size):
        """Higher memory percent should give larger batch sizes."""
        low_percent = 0.1
        high_percent = 0.8
        
        low_batch = estimate_safe_batch_size(result_size, low_percent)
        high_batch = estimate_safe_batch_size(result_size, high_percent)
        
        # Higher memory percent should give larger or equal batch sizes
        assert high_batch >= low_batch
    
    @given(result_size=st.integers(max_value=0))
    def test_rejects_non_positive_result_size(self, result_size):
        """Should reject non-positive result_size."""
        with pytest.raises(ValueError, match="result_size_bytes must be positive"):
            estimate_safe_batch_size(result_size)
    
    @given(
        result_size=st.integers(min_value=1, max_value=1_000_000),
        max_memory_percent=st.floats(max_value=0.0)
    )
    def test_rejects_non_positive_max_memory_percent(self, result_size, max_memory_percent):
        """Should reject non-positive max_memory_percent."""
        assume(max_memory_percent <= 0.0)
        with pytest.raises(ValueError, match="max_memory_percent must be between 0 and 1"):
            estimate_safe_batch_size(result_size, max_memory_percent)
    
    @given(
        result_size=st.integers(min_value=1, max_value=1_000_000),
        max_memory_percent=st.floats(min_value=1.01, max_value=10.0)
    )
    def test_rejects_max_memory_percent_above_one(self, result_size, max_memory_percent):
        """Should reject max_memory_percent > 1.0."""
        with pytest.raises(ValueError, match="max_memory_percent must be between 0 and 1"):
            estimate_safe_batch_size(result_size, max_memory_percent)
    
    @given(result_size=st.integers(min_value=1, max_value=1_000_000))
    def test_default_max_memory_percent(self, result_size):
        """Should use default max_memory_percent of 0.5."""
        # Test that it works without specifying max_memory_percent
        batch_size = estimate_safe_batch_size(result_size)
        assert isinstance(batch_size, int)
        assert batch_size >= 1


class TestEstimateSafeBatchSizeEdgeCases:
    """Test edge cases for estimate_safe_batch_size."""
    
    def test_very_small_result_size(self):
        """Should handle very small result sizes."""
        batch_size = estimate_safe_batch_size(1)
        assert batch_size >= 1
    
    def test_very_large_result_size(self):
        """Should handle very large result sizes."""
        # 1GB result size
        batch_size = estimate_safe_batch_size(1024 * 1024 * 1024)
        assert batch_size >= 1
    
    def test_minimal_memory_percent(self):
        """Should handle minimal memory percent."""
        batch_size = estimate_safe_batch_size(1000, max_memory_percent=0.01)
        assert batch_size >= 1
    
    def test_maximal_memory_percent(self):
        """Should handle maximal memory percent."""
        batch_size = estimate_safe_batch_size(1000, max_memory_percent=1.0)
        assert batch_size >= 1


# ============================================================================
# Test Integration Properties
# ============================================================================

class TestBatchProcessingIntegration:
    """Test integration properties of batch processing."""
    
    @given(data=data_list_strategy(min_size=1, max_size=100))
    @settings(deadline=5000)
    def test_auto_batch_equals_manual_results(self, data):
        """Auto batch size should produce same results as manual batch size."""
        auto_result = process_in_batches(square, data)
        manual_result = process_in_batches(square, data, batch_size=10)
        
        # Both should produce correct results
        expected = [x ** 2 for x in data]
        assert auto_result == expected
        assert manual_result == expected
    
    @given(
        data=data_list_strategy(min_size=1, max_size=100),
        batch_size=valid_batch_size()
    )
    @settings(deadline=5000)
    def test_multiple_functions_same_data(self, data, batch_size):
        """Different functions should work on same data."""
        result1 = process_in_batches(square, data, batch_size=batch_size)
        result2 = process_in_batches(double, data, batch_size=batch_size)
        
        assert result1 == [x ** 2 for x in data]
        assert result2 == [x * 2 for x in data]
    
    @given(data=data_list_strategy(min_size=1, max_size=100))
    @settings(deadline=5000)
    def test_estimate_batch_size_works_with_process(self, data):
        """estimate_safe_batch_size output should work with process_in_batches."""
        # Estimate batch size for small results (integers)
        result_size = sys.getsizeof(0)
        batch_size = estimate_safe_batch_size(result_size, max_memory_percent=0.5)
        
        # Use estimated batch size
        result = process_in_batches(square, data, batch_size=batch_size)
        assert len(result) == len(data)
        assert result == [x ** 2 for x in data]


class TestThreadSafety:
    """Test thread safety of batch processing."""
    
    @given(data=data_list_strategy(min_size=10, max_size=50))
    @settings(deadline=10000)
    def test_concurrent_batch_processing(self, data):
        """Should handle concurrent batch processing calls."""
        results = [None, None]
        errors = []
        
        def worker(idx, func):
            try:
                results[idx] = process_in_batches(func, data, batch_size=10)
            except Exception as e:
                errors.append(e)
        
        # Run two batch operations concurrently
        threads = [
            threading.Thread(target=worker, args=(0, square)),
            threading.Thread(target=worker, args=(1, double))
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should complete without errors
        assert len(errors) == 0
        assert results[0] == [x ** 2 for x in data]
        assert results[1] == [x * 2 for x in data]


# ============================================================================
# Test Iterator Conversion
# ============================================================================

class TestIteratorHandling:
    """Test handling of iterator inputs."""
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_handles_range_input(self, data):
        """Should handle range objects as input."""
        n = len(data)
        result = process_in_batches(square, range(n), batch_size=10)
        assert result == [x ** 2 for x in range(n)]
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_handles_generator_input(self, data):
        """Should handle generator inputs (converts to list)."""
        gen = (x for x in data)
        result = process_in_batches(square, gen, batch_size=10)
        assert result == [x ** 2 for x in data]
    
    @given(data=data_list_strategy(min_size=1, max_size=50))
    @settings(deadline=5000)
    def test_handles_tuple_input(self, data):
        """Should handle tuple inputs (converts to list)."""
        tuple_data = tuple(data)
        result = process_in_batches(square, tuple_data, batch_size=10)
        assert result == [x ** 2 for x in data]
