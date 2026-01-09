"""
Tests for system_info module.
"""

import pytest
from amorsize.system_info import (
    get_physical_cores,
    get_spawn_cost,
    get_spawn_cost_estimate,
    measure_spawn_cost,
    get_available_memory,
    calculate_max_workers,
    get_system_info,
    _clear_spawn_cost_cache
)


def test_get_physical_cores():
    """Test that get_physical_cores returns a positive integer."""
    cores = get_physical_cores()
    assert isinstance(cores, int)
    assert cores > 0


def test_get_spawn_cost():
    """Test that get_spawn_cost returns a reasonable value."""
    cost = get_spawn_cost()
    assert isinstance(cost, float)
    assert 0.01 < cost < 1.0  # Should be between 10ms and 1s


def test_get_spawn_cost_estimate():
    """Test that get_spawn_cost_estimate returns OS-based values."""
    cost = get_spawn_cost_estimate()
    assert isinstance(cost, float)
    assert 0.01 < cost < 1.0


def test_measure_spawn_cost():
    """Test actual spawn cost measurement."""
    cost = measure_spawn_cost(timeout=5.0)
    assert isinstance(cost, float)
    assert cost > 0
    # Should be reasonable (between 1ms and 5s)
    assert 0.001 < cost < 5.0


def test_spawn_cost_caching():
    """Test that spawn cost measurement is cached."""
    # Clear cache first using the public API
    _clear_spawn_cost_cache()
    
    # First call should measure
    cost1 = measure_spawn_cost()
    
    # Second call should return cached value (should be instant)
    import time
    start = time.perf_counter()
    cost2 = measure_spawn_cost()
    elapsed = time.perf_counter() - start
    
    assert cost1 == cost2
    assert elapsed < 0.01  # Should be nearly instant due to caching


def test_get_spawn_cost_with_benchmark():
    """Test get_spawn_cost with benchmarking enabled."""
    cost = get_spawn_cost(use_benchmark=True)
    assert isinstance(cost, float)
    assert cost > 0


def test_get_available_memory():
    """Test that get_available_memory returns a positive integer."""
    memory = get_available_memory()
    assert isinstance(memory, int)
    assert memory > 0


def test_calculate_max_workers():
    """Test max workers calculation."""
    # Test with no memory constraint
    result = calculate_max_workers(4, 0)
    assert result == 4
    
    # Test with memory constraint
    result = calculate_max_workers(8, 1024 * 1024 * 1024)  # 1GB per job
    assert result >= 1
    assert result <= 8


def test_get_system_info():
    """Test that get_system_info returns a tuple of correct types."""
    cores, spawn_cost, memory = get_system_info()
    
    assert isinstance(cores, int)
    assert isinstance(spawn_cost, float)
    assert isinstance(memory, int)
    
    assert cores > 0
    assert spawn_cost > 0
    assert memory > 0
