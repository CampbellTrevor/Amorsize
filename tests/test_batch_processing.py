"""
Test suite for batch processing utilities.
"""

import pytest
from amorsize import process_in_batches, estimate_safe_batch_size


# Test functions
def square(x):
    """Simple function for testing."""
    return x ** 2


def double(x):
    """Another simple function."""
    return x * 2


def returns_large_object(x):
    """Function that returns a large object."""
    return [x] * 10000  # ~80KB list


def slow_function(x):
    """Function with some computation."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


# ============================================================================
# Test process_in_batches() - Basic Functionality
# ============================================================================

def test_process_in_batches_basic():
    """Test basic batch processing."""
    data = list(range(100))
    results = process_in_batches(square, data, batch_size=10)
    
    # Check all results are correct
    assert len(results) == 100
    assert results == [x ** 2 for x in range(100)]


def test_process_in_batches_single_batch():
    """Test with batch size larger than data."""
    data = list(range(10))
    results = process_in_batches(square, data, batch_size=100)
    
    assert len(results) == 10
    assert results == [x ** 2 for x in range(10)]


def test_process_in_batches_exact_batches():
    """Test with data size exactly divisible by batch size."""
    data = list(range(50))
    results = process_in_batches(square, data, batch_size=10)
    
    assert len(results) == 50
    assert results == [x ** 2 for x in range(50)]


def test_process_in_batches_uneven_batches():
    """Test with data size not divisible by batch size."""
    data = list(range(55))
    results = process_in_batches(square, data, batch_size=10)
    
    # Should create 6 batches: 10+10+10+10+10+5
    assert len(results) == 55
    assert results == [x ** 2 for x in range(55)]


def test_process_in_batches_batch_size_one():
    """Test with batch size of 1."""
    data = list(range(5))
    results = process_in_batches(square, data, batch_size=1)
    
    assert len(results) == 5
    assert results == [x ** 2 for x in range(5)]


# ============================================================================
# Test process_in_batches() - Auto-calculated Batch Size
# ============================================================================

def test_process_in_batches_auto_batch_size():
    """Test automatic batch size calculation."""
    data = list(range(100))
    results = process_in_batches(square, data)  # No batch_size specified
    
    # Should complete successfully and return correct results
    assert len(results) == 100
    assert results == [x ** 2 for x in range(100)]


def test_process_in_batches_auto_batch_size_large_results():
    """Test auto batch size with large return objects."""
    data = list(range(50))
    # Function returns large objects, should use smaller batches
    results = process_in_batches(returns_large_object, data, max_memory_percent=0.1)
    
    assert len(results) == 50
    # Each result should be a list of length 10000
    assert all(len(r) == 10000 for r in results)


def test_process_in_batches_auto_batch_size_custom_memory_percent():
    """Test auto batch size with custom memory percentage."""
    data = list(range(30))
    results = process_in_batches(square, data, max_memory_percent=0.3)
    
    assert len(results) == 30
    assert results == [x ** 2 for x in range(30)]


# ============================================================================
# Test process_in_batches() - Data Type Handling
# ============================================================================

def test_process_in_batches_with_list():
    """Test with list input."""
    data = [1, 2, 3, 4, 5]
    results = process_in_batches(square, data, batch_size=2)
    
    assert results == [1, 4, 9, 16, 25]


def test_process_in_batches_with_range():
    """Test with range input."""
    data = range(10)
    results = process_in_batches(square, data, batch_size=3)
    
    assert results == [x ** 2 for x in range(10)]


def test_process_in_batches_with_generator():
    """Test with generator input."""
    def gen():
        for i in range(10):
            yield i
    
    results = process_in_batches(square, gen(), batch_size=3)
    
    assert results == [x ** 2 for x in range(10)]


# ============================================================================
# Test process_in_batches() - Parameter Passing
# ============================================================================

def test_process_in_batches_with_verbose():
    """Test verbose mode."""
    data = list(range(20))
    # Should not raise exception
    results = process_in_batches(square, data, batch_size=5, verbose=True)
    
    assert len(results) == 20


def test_process_in_batches_with_sample_size():
    """Test custom sample size parameter."""
    data = list(range(50))
    results = process_in_batches(square, data, batch_size=10, sample_size=3)
    
    assert len(results) == 50
    assert results == [x ** 2 for x in range(50)]


def test_process_in_batches_with_optimize_kwargs():
    """Test passing additional kwargs to optimize()."""
    data = list(range(30))
    results = process_in_batches(
        square,
        data,
        batch_size=10,
        target_chunk_duration=0.1,  # Passed to optimize()
        profile=True  # Passed to optimize()
    )
    
    assert len(results) == 30


# ============================================================================
# Test process_in_batches() - Edge Cases
# ============================================================================

def test_process_in_batches_empty_data():
    """Test with empty data."""
    results = process_in_batches(square, [], batch_size=10)
    
    assert results == []


def test_process_in_batches_single_item():
    """Test with single item."""
    results = process_in_batches(square, [5], batch_size=10)
    
    assert results == [25]


def test_process_in_batches_large_batch_size():
    """Test with very large batch size."""
    data = list(range(10))
    results = process_in_batches(square, data, batch_size=1000000)
    
    assert len(results) == 10


# ============================================================================
# Test process_in_batches() - Validation
# ============================================================================

def test_process_in_batches_invalid_func():
    """Test with non-callable function."""
    with pytest.raises(ValueError, match="func must be callable"):
        process_in_batches(None, [1, 2, 3], batch_size=2)


def test_process_in_batches_invalid_batch_size_negative():
    """Test with negative batch size."""
    with pytest.raises(ValueError, match="batch_size must be a positive integer"):
        process_in_batches(square, [1, 2, 3], batch_size=-1)


def test_process_in_batches_invalid_batch_size_zero():
    """Test with zero batch size."""
    with pytest.raises(ValueError, match="batch_size must be a positive integer"):
        process_in_batches(square, [1, 2, 3], batch_size=0)


def test_process_in_batches_invalid_batch_size_float():
    """Test with float batch size."""
    with pytest.raises(ValueError, match="batch_size must be a positive integer"):
        process_in_batches(square, [1, 2, 3], batch_size=2.5)


def test_process_in_batches_invalid_memory_percent_negative():
    """Test with negative memory percent."""
    with pytest.raises(ValueError, match="max_memory_percent must be between 0 and 1"):
        process_in_batches(square, [1, 2, 3], max_memory_percent=-0.1)


def test_process_in_batches_invalid_memory_percent_too_large():
    """Test with memory percent > 1."""
    with pytest.raises(ValueError, match="max_memory_percent must be between 0 and 1"):
        process_in_batches(square, [1, 2, 3], max_memory_percent=1.5)


def test_process_in_batches_invalid_sample_size():
    """Test with invalid sample size."""
    with pytest.raises(ValueError, match="sample_size must be a positive integer"):
        process_in_batches(square, [1, 2, 3], batch_size=2, sample_size=-1)


def test_process_in_batches_invalid_verbose():
    """Test with invalid verbose parameter."""
    with pytest.raises(ValueError, match="verbose must be a boolean"):
        process_in_batches(square, [1, 2, 3], batch_size=2, verbose="yes")


# ============================================================================
# Test estimate_safe_batch_size()
# ============================================================================

def test_estimate_safe_batch_size_basic():
    """Test basic batch size estimation."""
    # 1MB results, should return reasonable batch size
    result_size = 1024 * 1024  # 1MB
    batch_size = estimate_safe_batch_size(result_size)
    
    assert batch_size >= 1
    assert isinstance(batch_size, int)


def test_estimate_safe_batch_size_small_results():
    """Test with small result size."""
    result_size = 100  # 100 bytes
    batch_size = estimate_safe_batch_size(result_size)
    
    # Should allow many items
    assert batch_size > 1000


def test_estimate_safe_batch_size_large_results():
    """Test with large result size."""
    result_size = 100 * 1024 * 1024  # 100MB
    batch_size = estimate_safe_batch_size(result_size)
    
    # Should be conservative
    assert batch_size >= 1


def test_estimate_safe_batch_size_custom_memory_percent():
    """Test with custom memory percentage."""
    result_size = 1024 * 1024  # 1MB
    
    # More conservative (30% vs 50% default)
    batch_size_30 = estimate_safe_batch_size(result_size, max_memory_percent=0.3)
    batch_size_50 = estimate_safe_batch_size(result_size, max_memory_percent=0.5)
    
    # 30% should give smaller batch than 50%
    assert batch_size_30 < batch_size_50


def test_estimate_safe_batch_size_validation_zero():
    """Test validation with zero result size."""
    with pytest.raises(ValueError, match="result_size_bytes must be positive"):
        estimate_safe_batch_size(0)


def test_estimate_safe_batch_size_validation_negative():
    """Test validation with negative result size."""
    with pytest.raises(ValueError, match="result_size_bytes must be positive"):
        estimate_safe_batch_size(-100)


def test_estimate_safe_batch_size_validation_memory_percent():
    """Test validation with invalid memory percent."""
    with pytest.raises(ValueError, match="max_memory_percent must be between 0 and 1"):
        estimate_safe_batch_size(1024, max_memory_percent=1.5)


# ============================================================================
# Integration Tests
# ============================================================================

def test_batch_processing_integration_complete_workflow():
    """Test complete workflow: process data, verify all results."""
    data = list(range(100))
    results = process_in_batches(slow_function, data, batch_size=20, verbose=True)
    
    # Verify all items processed
    assert len(results) == 100
    
    # Verify results are correct
    expected = [slow_function(x) for x in range(100)]
    assert results == expected


def test_batch_processing_integration_with_estimation():
    """Test using estimate_safe_batch_size with process_in_batches."""
    # Estimate safe batch size
    result_size = 10000  # Assume 10KB results
    batch_size = estimate_safe_batch_size(result_size, max_memory_percent=0.4)
    
    # Use estimated batch size
    data = list(range(50))
    results = process_in_batches(square, data, batch_size=batch_size)
    
    assert len(results) == 50
    assert results == [x ** 2 for x in range(50)]
