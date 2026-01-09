"""
Tests for sampling module.
"""

import pytest
import time
from amorsize.sampling import (
    check_picklability,
    safe_slice_data,
    perform_dry_run,
    estimate_total_items,
    SamplingResult,
    reconstruct_iterator
)


def simple_function(x):
    """A simple function for testing."""
    return x * 2


def slow_function(x):
    """A slow function for testing."""
    time.sleep(0.01)
    return x ** 2


class UnpicklableClass:
    """A class that cannot be pickled."""
    def __init__(self):
        self.func = lambda x: x


def test_check_picklability():
    """Test picklability checking."""
    # Regular function should be picklable
    assert check_picklability(simple_function) is True
    
    # Lambda should not be picklable (in most cases)
    lambda_func = lambda x: x * 2
    # Note: picklability of lambdas can vary by Python version


def test_safe_slice_data_list():
    """Test slicing from a list."""
    data = list(range(100))
    sample, reconstructed, is_gen = safe_slice_data(data, 5)
    
    assert len(sample) == 5
    assert sample == [0, 1, 2, 3, 4]
    assert is_gen is False
    assert reconstructed == data  # Original list unchanged


def test_safe_slice_data_generator():
    """Test slicing from a generator."""
    def gen():
        for i in range(100):
            yield i
    
    data = gen()
    sample, remaining, is_gen = safe_slice_data(data, 5)
    
    assert len(sample) == 5
    assert sample == [0, 1, 2, 3, 4]
    assert is_gen is True
    
    # Verify remaining data continues from where sample left off
    next_item = next(remaining)
    assert next_item == 5


def test_perform_dry_run_simple():
    """Test dry run with simple function."""
    data = list(range(10))
    result = perform_dry_run(simple_function, data, sample_size=5)
    
    assert isinstance(result, SamplingResult)
    assert result.error is None
    assert result.avg_time > 0
    assert result.sample_count == 5
    assert result.is_picklable is True


def test_perform_dry_run_slow():
    """Test dry run with slow function."""
    data = list(range(5))
    result = perform_dry_run(slow_function, data, sample_size=3)
    
    assert result.error is None
    assert result.avg_time > 0.008  # Should be at least ~10ms
    assert result.sample_count == 3


def test_perform_dry_run_empty_data():
    """Test dry run with empty data."""
    data = []
    result = perform_dry_run(simple_function, data, sample_size=5)
    
    assert result.sample_count == 0
    assert result.error is not None


def test_perform_dry_run_exception():
    """Test dry run with function that raises exception."""
    def error_function(x):
        raise ValueError("Test error")
    
    data = list(range(5))
    result = perform_dry_run(error_function, data, sample_size=3)
    
    assert result.error is not None
    assert isinstance(result.error, ValueError)


def test_estimate_total_items_list():
    """Test estimating items for a list."""
    data = list(range(100))
    count = estimate_total_items(data, False)
    assert count == 100


def test_estimate_total_items_generator():
    """Test estimating items for a generator."""
    def gen():
        for i in range(100):
            yield i
    
    data = gen()
    count = estimate_total_items(data, True)
    assert count == -1  # Cannot determine size


def test_reconstruct_iterator():
    """Test reconstructing an iterator from sample and remaining data."""
    def gen():
        for i in range(10):
            yield i
    
    data = gen()
    sample, remaining, is_gen = safe_slice_data(data, 3)
    
    # Reconstruct the full iterator
    reconstructed = reconstruct_iterator(sample, remaining)
    
    # Verify we get all items back in order
    result = list(reconstructed)
    assert result == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
