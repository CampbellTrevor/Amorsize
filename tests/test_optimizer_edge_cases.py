"""
Edge case tests for optimizer module to improve mutation testing coverage.

This module adds comprehensive edge case testing for scenarios that are likely
to be revealed by mutation testing, including:
- Boundary conditions (zero, negative, maximum values)
- Error handling paths
- Platform-specific behaviors
- Rare execution paths
"""

import pytest
import sys
import platform
from amorsize import optimize
from amorsize.optimizer import OptimizationResult, DiagnosticProfile


def simple_func(x):
    """Simple function for testing."""
    return x * 2


def error_func(x):
    """Function that raises an error."""
    if x < 0:
        raise ValueError("Negative input")
    return x * 2


def test_optimize_single_item():
    """Test optimization with exactly one item (boundary condition)."""
    data = [1]
    result = optimize(simple_func, data)
    
    assert isinstance(result, OptimizationResult)
    assert result.n_jobs == 1  # Should not parallelize single item
    assert result.chunksize >= 1
    assert "too small" in result.reason.lower() or "single" in result.reason.lower() or "short" in result.reason.lower()


def test_optimize_two_items():
    """Test optimization with two items (minimal parallelizable size)."""
    data = [1, 2]
    result = optimize(simple_func, data)
    
    assert isinstance(result, OptimizationResult)
    assert result.n_jobs >= 1
    assert result.chunksize >= 1


def test_optimize_negative_sample_size():
    """Test that negative sample_size is handled gracefully."""
    data = list(range(100))
    
    # Should either use default or raise ValueError
    try:
        result = optimize(simple_func, data, sample_size=-1)
        # If it doesn't raise, should use a positive sample size
        assert result.n_jobs >= 1
    except ValueError as e:
        # Expected: validation should catch negative sample_size
        assert "sample_size" in str(e).lower()


def test_optimize_zero_sample_size():
    """Test that zero sample_size is handled gracefully."""
    data = list(range(100))
    
    # Should either use default or raise ValueError
    try:
        result = optimize(simple_func, data, sample_size=0)
        # If it doesn't raise, should use a positive sample size
        assert result.n_jobs >= 1
    except ValueError as e:
        # Expected: validation should catch zero sample_size
        assert "sample_size" in str(e).lower()


def test_optimize_extremely_large_sample_size():
    """Test with sample_size larger than data size."""
    data = list(range(10))
    # Request sample size larger than data
    result = optimize(simple_func, data, sample_size=1000)
    
    assert isinstance(result, OptimizationResult)
    # Should handle gracefully, capping at data size
    assert result.n_jobs >= 1


def test_optimize_negative_target_chunk_duration():
    """Test that negative target_chunk_duration is handled gracefully."""
    data = list(range(100))
    
    # Should either use default or raise ValueError
    try:
        result = optimize(simple_func, data, target_chunk_duration=-0.1)
        # If it doesn't raise, should use a positive duration
        assert result.n_jobs >= 1
    except ValueError as e:
        # Expected: validation should catch negative duration
        assert "target_chunk_duration" in str(e).lower()


def test_optimize_zero_target_chunk_duration():
    """Test that zero target_chunk_duration is handled gracefully."""
    data = list(range(100))
    
    # Should either use default or raise ValueError
    try:
        result = optimize(simple_func, data, target_chunk_duration=0.0)
        # If it doesn't raise, should use a positive duration
        assert result.n_jobs >= 1
    except ValueError as e:
        # Expected: validation should catch zero duration
        assert "target_chunk_duration" in str(e).lower()


def test_optimize_with_warnings():
    """Test that warnings are captured when appropriate."""
    # Very small data should generate a warning
    data = [1]
    result = optimize(simple_func, data)
    
    assert isinstance(result, OptimizationResult)
    # Should have either a warning or an error for tiny datasets
    assert len(result.warnings) > 0 or result.error is not None or "small" in result.reason.lower()


def test_optimize_result_attributes():
    """Test that OptimizationResult has all required attributes."""
    data = list(range(100))
    result = optimize(simple_func, data)
    
    # Verify all key attributes exist and have appropriate types
    assert hasattr(result, 'n_jobs')
    assert hasattr(result, 'chunksize')
    assert hasattr(result, 'reason')
    assert hasattr(result, 'estimated_speedup')
    assert hasattr(result, 'warnings')
    
    assert isinstance(result.n_jobs, int)
    assert isinstance(result.chunksize, int)
    assert isinstance(result.reason, str)
    assert isinstance(result.estimated_speedup, (int, float))
    assert isinstance(result.warnings, list)


def test_diagnostic_profile_initialization():
    """Test DiagnosticProfile can be initialized with defaults."""
    profile = DiagnosticProfile()
    
    # Verify initialization creates valid default values
    assert profile.avg_execution_time >= 0.0
    assert profile.sample_count >= 0
    assert profile.physical_cores >= 1
    assert profile.logical_cores >= 1
    assert profile.total_items >= 0


def test_optimize_with_profiling():
    """Test that profiling can be enabled without errors."""
    data = list(range(100))
    result = optimize(simple_func, data, profile=True)
    
    assert isinstance(result, OptimizationResult)
    # Diagnostic profile should be available
    assert result.profile is not None
    assert isinstance(result.profile, DiagnosticProfile)


def test_optimize_preserves_generator_when_not_consumed():
    """Test that generator is not fully consumed during optimization."""
    call_count = []
    
    def counting_gen():
        """Generator that tracks how many items were yielded."""
        for i in range(1000):
            call_count.append(i)
            yield i
    
    gen = counting_gen()
    result = optimize(simple_func, gen)
    
    # Should sample only a small portion, not all 1000 items
    assert isinstance(result, OptimizationResult)
    # Sample size should be much less than 1000
    assert len(call_count) < 1000, "Generator was fully consumed during sampling"


def test_optimize_with_none_data():
    """Test optimization with None as data."""
    # Should raise ValueError with clear message
    with pytest.raises(ValueError, match="data parameter cannot be None"):
        result = optimize(simple_func, None)  # type: ignore


def test_optimize_with_dict_data():
    """Test optimization with dictionary (unsupported iterable)."""
    data = {1: 'a', 2: 'b', 3: 'c'}
    
    # Pool.map expects sequence or iterator, not dict directly
    # Should handle gracefully or raise TypeError
    try:
        result = optimize(simple_func, data)  # type: ignore
        # If it doesn't raise, verify it handles gracefully
        assert isinstance(result, OptimizationResult)
    except (TypeError, ValueError):
        # Expected: dict is not a valid data type for Pool.map
        pass


def test_optimize_result_str_repr():
    """Test that OptimizationResult __str__ and __repr__ work correctly."""
    data = list(range(100))
    result = optimize(simple_func, data)
    
    # Both should return non-empty strings
    str_repr = str(result)
    repr_repr = repr(result)
    
    assert isinstance(str_repr, str)
    assert len(str_repr) > 0
    assert isinstance(repr_repr, str)
    assert len(repr_repr) > 0
    
    # Should contain key information
    assert str(result.n_jobs) in str_repr or str(result.n_jobs) in repr_repr


def test_optimize_with_sample_size_boundary():
    """Test optimization with sample_size=1 (boundary condition)."""
    data = list(range(1000))
    result = optimize(simple_func, data, sample_size=1)
    
    assert isinstance(result, OptimizationResult)
    # Should work with minimal sample
    assert result.n_jobs >= 1


def test_optimize_with_large_sample_size():
    """Test optimization with very large sample_size."""
    data = list(range(100))
    result = optimize(simple_func, data, sample_size=50)
    
    assert isinstance(result, OptimizationResult)
    # Should handle gracefully
    assert result.n_jobs >= 1


def test_optimize_with_progress_callback():
    """Test that progress callback doesn't break optimization."""
    data = list(range(100))
    callback_called = []
    
    def callback(msg, progress):
        callback_called.append((msg, progress))
    
    result = optimize(simple_func, data, progress_callback=callback)
    
    assert isinstance(result, OptimizationResult)
    # Callback may or may not be called depending on implementation
    assert result.n_jobs >= 1


def test_optimize_reason_not_empty():
    """Test that reason is always provided."""
    data = list(range(100))
    result = optimize(simple_func, data)
    
    assert isinstance(result.reason, str)
    assert len(result.reason) > 0, "Reason should always explain the decision"


def test_optimize_speedup_non_negative():
    """Test that estimated speedup is never negative."""
    data = list(range(100))
    result = optimize(simple_func, data)
    
    assert result.estimated_speedup >= 0.0, "Speedup cannot be negative"


def test_optimize_chunksize_positive():
    """Test that chunksize is always positive."""
    data = list(range(100))
    result = optimize(simple_func, data)
    
    assert result.chunksize >= 1, "Chunksize must be at least 1"


def test_optimize_n_jobs_positive():
    """Test that n_jobs is always positive."""
    data = list(range(100))
    result = optimize(simple_func, data)
    
    assert result.n_jobs >= 1, "n_jobs must be at least 1"


def test_optimize_with_very_small_target_duration():
    """Test with extremely small target chunk duration."""
    data = list(range(100))
    result = optimize(simple_func, data, target_chunk_duration=0.0001)
    
    assert isinstance(result, OptimizationResult)
    # Should handle gracefully, even if unusual
    assert result.chunksize >= 1


def test_optimize_with_very_large_target_duration():
    """Test with very large target chunk duration."""
    data = list(range(100))
    result = optimize(simple_func, data, target_chunk_duration=10.0)
    
    assert isinstance(result, OptimizationResult)
    # Should handle gracefully, may result in large chunksize
    assert result.chunksize >= 1
