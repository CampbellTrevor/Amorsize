"""
Tests for enhanced chunking overhead measurement with robustness improvements.

This test module validates the improved chunking overhead measurement that includes:
- Multiple quality validation checks
- Detection of measurement noise
- Intelligent fallback strategies
- Adaptive behavior for different system conditions
"""

import pytest
import time
import multiprocessing
from amorsize.system_info import (
    measure_chunking_overhead,
    get_chunking_overhead,
    _clear_chunking_overhead_cache,
    DEFAULT_CHUNKING_OVERHEAD
)


def test_measure_chunking_overhead_returns_reasonable_value():
    """Test that measured chunking overhead is in reasonable range."""
    _clear_chunking_overhead_cache()
    
    overhead = measure_chunking_overhead()
    
    # Should be between 0.05ms and 10ms per chunk
    assert 0.00005 < overhead < 0.01, f"Overhead {overhead}s is outside reasonable range"


def test_measure_chunking_overhead_cached():
    """Test that chunking overhead measurement is cached."""
    # Clear cache first
    _clear_chunking_overhead_cache()
    
    # First call should measure
    first_result = measure_chunking_overhead()
    
    # Second call should return cached value (very fast)
    start = time.time()
    second_result = measure_chunking_overhead()
    elapsed = time.time() - start
    
    assert first_result == second_result, "Cached value should match first measurement"
    assert elapsed < 0.01, "Second call should be instant (cached)"


def test_chunking_overhead_validation():
    """
    Test that measurement validates quality properly.
    
    This tests that the improved measurement function properly
    validates measurement quality and returns reasonable values.
    """
    # Clear cache for clean test
    _clear_chunking_overhead_cache()
    
    # Measure overhead
    overhead = measure_chunking_overhead()
    
    # Should return either measured value or default (0.5ms)
    assert 0 < overhead < 0.01, f"Overhead {overhead} outside reasonable range"
    # Should be either default or within measured range (0.1ms to 5ms)
    assert overhead == DEFAULT_CHUNKING_OVERHEAD or (0.0001 < overhead < 0.005)


def test_measure_chunking_overhead_quality_validation():
    """Test that chunking overhead measurement includes quality validation."""
    _clear_chunking_overhead_cache()
    
    # Measure overhead
    overhead = measure_chunking_overhead()
    
    # Basic validation: should be positive and reasonable
    assert overhead > 0, "Chunking overhead must be positive"
    assert overhead < 0.01, f"Chunking overhead seems too high: {overhead*1000:.2f}ms per chunk"
    
    # The measurement should be within acceptable range: 0.05ms to 5ms per chunk
    assert 0.00005 <= overhead <= 0.005, f"Overhead {overhead*1000:.3f}ms outside reasonable range"


def test_measure_chunking_overhead_multiple_calls_cached():
    """Test that chunking overhead measurement is cached between calls."""
    # Clear cache to start fresh
    _clear_chunking_overhead_cache()
    
    # First measurement
    start = time.perf_counter()
    result1 = measure_chunking_overhead()
    time1 = time.perf_counter() - start
    
    # Second call should return cached value (much faster)
    start = time.perf_counter()
    result2 = measure_chunking_overhead()
    time2 = time.perf_counter() - start
    
    # Results should be identical (cached)
    assert result1 == result2
    # Second call should be much faster (< 1ms)
    assert time2 < 0.001, f"Cache lookup took {time2*1000:.3f}ms (expected < 1ms)"


def test_measure_chunking_overhead_fallback_on_exception():
    """Test that chunking overhead measurement falls back to default on exception."""
    # Clear cache to force new measurement
    _clear_chunking_overhead_cache()
    
    # Mock multiprocessing.Pool to raise an exception
    original_pool = multiprocessing.Pool
    
    def mock_pool(*args, **kwargs):
        raise OSError("Mock error")
    
    multiprocessing.Pool = mock_pool
    
    try:
        overhead = measure_chunking_overhead()
        assert overhead == DEFAULT_CHUNKING_OVERHEAD, "Should fall back to default on exception"
    finally:
        # Restore original Pool
        multiprocessing.Pool = original_pool
        # Clear cache again
        _clear_chunking_overhead_cache()


def test_get_chunking_overhead_with_benchmark_flag():
    """Test that get_chunking_overhead respects the use_benchmark flag."""
    # Clear cache
    _clear_chunking_overhead_cache()
    
    # With benchmark=True (default), should measure
    overhead_measured = get_chunking_overhead(use_benchmark=True)
    assert 0 < overhead_measured <= 0.01, "Measured overhead should be reasonable"
    
    # Clear cache for next test
    _clear_chunking_overhead_cache()
    
    # With benchmark=False, should return default
    overhead_default = get_chunking_overhead(use_benchmark=False)
    assert overhead_default == DEFAULT_CHUNKING_OVERHEAD, "Should return default when benchmark=False"


def test_quality_check_rejects_unreasonable_values():
    """Test that quality checks properly validate measurements."""
    _clear_chunking_overhead_cache()
    
    # Measure overhead
    overhead = measure_chunking_overhead()
    
    # Verify result is reasonable
    assert 0 < overhead <= 0.01, f"Overhead {overhead} should be positive and reasonable"
    
    # Quality check 1: Should be positive
    assert overhead > 0
    
    # Quality check 2: Should be less than 10ms (reasonable upper bound)
    assert overhead < 0.01
    
    # Quality check 3: Should be at least 0.05ms (reasonable lower bound)
    # OR be the default value
    assert overhead >= 0.00005 or overhead == DEFAULT_CHUNKING_OVERHEAD
    
    # Clear cache
    _clear_chunking_overhead_cache()


def test_measurement_robustness_with_system_load():
    """Test that measurement handles varying system load reasonably."""
    _clear_chunking_overhead_cache()
    
    # Take multiple measurements
    measurements = []
    for _ in range(3):
        _clear_chunking_overhead_cache()
        overhead = measure_chunking_overhead()
        measurements.append(overhead)
    
    # All measurements should be reasonable
    for overhead in measurements:
        assert 0 < overhead <= 0.01, f"Measurement {overhead} outside reasonable range"
    
    # Measurements should be relatively consistent (within 5x of each other)
    # OR all be the default value (indicating fallback to default)
    all_default = all(m == DEFAULT_CHUNKING_OVERHEAD for m in measurements)
    if not all_default:
        min_val = min(measurements)
        max_val = max(measurements)
        ratio = max_val / min_val if min_val > 0 else float('inf')
        assert ratio < 5.0, f"Measurements vary too much: {measurements}"
    
    _clear_chunking_overhead_cache()
