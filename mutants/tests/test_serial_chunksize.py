"""
Tests for chunksize behavior when n_jobs=1 (serial execution).

This test module ensures that when the optimizer determines serial execution
is best, it returns sensible chunksize values that don't exceed the total
number of items in the dataset.
"""

import pytest
from amorsize import optimize


def test_chunksize_capped_for_tiny_workload():
    """Test that chunksize is capped at total_items for very small workloads."""
    def fast_work(x):
        return x ** 2
    
    # Very small workload - should recommend serial execution
    result = optimize(fast_work, range(3), sample_size=5, verbose=False)
    
    assert result.n_jobs == 1, "Should recommend serial execution for tiny workload"
    assert result.chunksize <= 3, f"Chunksize ({result.chunksize}) should not exceed total items (3)"
    assert result.chunksize >= 1, "Chunksize must be at least 1"
    assert result.estimated_speedup == 1.0, "Serial execution has 1.0x speedup by definition"


def test_chunksize_capped_for_various_small_workloads():
    """Test chunksize capping for various small workload sizes."""
    def fast_work(x):
        return x ** 2
    
    test_sizes = [1, 2, 3, 5, 10, 20]
    
    for n in test_sizes:
        result = optimize(fast_work, range(n), verbose=False)
        
        if result.n_jobs == 1:
            # For serial execution, chunksize should not exceed total items
            assert result.chunksize <= n, (
                f"For n={n}, chunksize ({result.chunksize}) should not exceed total items"
            )
            assert result.chunksize >= 1, f"Chunksize must be at least 1 for n={n}"


def test_chunksize_reasonable_for_single_item():
    """Test chunksize for single-item dataset."""
    def fast_work(x):
        return x ** 2
    
    result = optimize(fast_work, [42], verbose=False)
    
    assert result.n_jobs == 1, "Single item should use serial execution"
    assert result.chunksize == 1, f"Single item should have chunksize=1, got {result.chunksize}"


def test_chunksize_for_empty_list():
    """Test chunksize handling for empty dataset."""
    def fast_work(x):
        return x ** 2
    
    result = optimize(fast_work, [], verbose=False)
    
    assert result.n_jobs == 1, "Empty dataset should use serial execution"
    # For empty dataset, chunksize can be any positive value since it doesn't matter
    assert result.chunksize >= 1, "Chunksize must be at least 1"


def test_chunksize_data_smaller_than_sample_size():
    """Test that data smaller than sample_size is handled correctly."""
    def fast_work(x):
        return x ** 2
    
    # Data has 3 items but we request sample_size=5
    result = optimize(fast_work, range(3), sample_size=5, verbose=False)
    
    assert result.n_jobs == 1, "Should recommend serial execution"
    assert result.chunksize <= 3, (
        f"Chunksize ({result.chunksize}) should not exceed total items (3) "
        "even when data is smaller than sample_size"
    )


def test_parallel_chunksize_not_affected():
    """Test that parallel execution chunksize calculation is not affected by the fix."""
    import time
    
    def slow_work(x):
        """Slow enough to benefit from parallelization."""
        time.sleep(0.01)
        return x ** 2
    
    result = optimize(slow_work, range(100), verbose=False)
    
    if result.n_jobs > 1:
        # For parallel execution, chunksize can be larger than total_items/n_jobs
        # The optimizer may recommend larger chunks based on target_chunk_duration
        assert result.chunksize >= 1, "Chunksize must be at least 1"
        # Don't enforce upper bound for parallel execution - it's calculated differently


def test_serial_execution_with_constraints():
    """Test chunksize when serial execution is forced by constraints (not workload size)."""
    def fast_work(x):
        return x ** 2
    
    # Even with reasonable workload, if n_jobs=1 is recommended for other reasons
    # (e.g., memory constraints), chunksize should still be sensible
    result = optimize(fast_work, range(50), verbose=False)
    
    if result.n_jobs == 1:
        assert result.chunksize <= 50, (
            f"For serial execution with 50 items, chunksize ({result.chunksize}) "
            "should not exceed total items"
        )
        assert result.chunksize >= 1, "Chunksize must be at least 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
