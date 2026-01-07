"""
Tests for system_info module.
"""

import pytest
from amorsize.system_info import (
    get_physical_cores,
    get_spawn_cost,
    get_available_memory,
    calculate_max_workers,
    get_system_info
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
