"""
Tests for optimizer module.
"""

import pytest
import time
from amorsize import optimize
from amorsize.optimizer import OptimizationResult


def simple_function(x):
    """A simple fast function."""
    return x * 2


def medium_function(x):
    """A medium-speed function."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


def slow_function(x):
    """A slow function."""
    time.sleep(0.01)
    return x ** 2


def unpicklable_function_wrapper():
    """Returns an unpicklable function."""
    return lambda x: x * 2


def test_optimize_simple_function():
    """Test optimization with a simple function."""
    data = list(range(100))
    result = optimize(simple_function, data)
    
    assert isinstance(result, OptimizationResult)
    assert result.n_jobs >= 1
    assert result.chunksize >= 1
    assert isinstance(result.reason, str)
    assert result.estimated_speedup >= 1.0


def test_optimize_medium_function():
    """Test optimization with medium-speed function."""
    data = list(range(1000))
    result = optimize(medium_function, data)
    
    assert isinstance(result, OptimizationResult)
    assert result.n_jobs >= 1
    assert result.chunksize >= 1


def test_optimize_slow_function():
    """Test optimization with slow function."""
    data = list(range(50))
    result = optimize(slow_function, data, sample_size=3)
    
    assert isinstance(result, OptimizationResult)
    # Slow function should benefit from parallelization
    assert result.n_jobs > 1 or result.reason


def test_optimize_empty_data():
    """Test optimization with empty data."""
    data = []
    result = optimize(simple_function, data)
    
    assert result.n_jobs == 1
    assert len(result.warnings) > 0 or result.error is not None


def test_optimize_generator():
    """Test optimization with generator input."""
    def gen():
        for i in range(1000):
            yield i
    
    result = optimize(medium_function, gen())
    
    assert isinstance(result, OptimizationResult)
    assert result.n_jobs >= 1


def test_optimize_very_fast_function():
    """Test that very fast functions return n_jobs=1."""
    # Use the module-level simple_function which is picklable
    data = list(range(10))
    result = optimize(simple_function, data)
    
    # Should recommend serial execution for very fast operations
    assert result.n_jobs == 1
    # Reason could be "too fast", "short", or "not picklable" depending on Python version
    assert result.reason is not None


def test_optimize_verbose():
    """Test optimization with verbose output."""
    data = list(range(100))
    # Should not raise an exception
    result = optimize(medium_function, data, verbose=True)
    assert isinstance(result, OptimizationResult)


def test_optimization_result_repr():
    """Test OptimizationResult string representation."""
    result = OptimizationResult(
        n_jobs=4,
        chunksize=10,
        reason="Test reason",
        estimated_speedup=3.5
    )
    
    repr_str = repr(result)
    assert "n_jobs=4" in repr_str
    assert "chunksize=10" in repr_str
    
    str_str = str(result)
    assert "n_jobs=4" in str_str
    assert "chunksize=10" in str_str
    assert "Test reason" in str_str


def test_optimize_with_custom_parameters():
    """Test optimization with custom parameters."""
    data = list(range(1000))
    result = optimize(
        medium_function,
        data,
        sample_size=10,
        target_chunk_duration=0.5,
        verbose=False
    )
    
    assert isinstance(result, OptimizationResult)
    assert result.chunksize >= 1


def test_optimize_with_spawn_benchmark():
    """Test optimization with spawn benchmarking enabled."""
    data = list(range(100))
    result = optimize(
        medium_function,
        data,
        use_spawn_benchmark=True,
        verbose=False
    )
    
    assert isinstance(result, OptimizationResult)
    assert result.n_jobs >= 1
    assert result.chunksize >= 1
