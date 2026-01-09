"""
Tests for system_info module.
"""

import pytest
import sys
import multiprocessing
import platform
from amorsize.system_info import (
    get_physical_cores,
    get_spawn_cost,
    get_spawn_cost_estimate,
    measure_spawn_cost,
    get_available_memory,
    calculate_max_workers,
    get_system_info,
    _clear_spawn_cost_cache,
    get_multiprocessing_start_method,
    _get_default_start_method,
    check_start_method_mismatch
)

# Maximum expected per-worker spawn cost (500ms)
# This is a generous upper bound to account for slow systems
MAX_EXPECTED_PER_WORKER_COST = 0.5


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
    # Clear cache to ensure fresh measurement
    _clear_spawn_cost_cache()
    
    cost = measure_spawn_cost(timeout=5.0)
    assert isinstance(cost, float)
    assert cost > 0
    # Should be reasonable (between 1ms and 5s)
    assert 0.001 < cost < 5.0


def test_measure_spawn_cost_marginal():
    """Test that spawn cost measures marginal per-worker cost."""
    # Clear cache to ensure fresh measurement
    _clear_spawn_cost_cache()
    
    # The marginal cost should generally be less than full pool creation
    # since it removes fixed initialization overhead
    cost = measure_spawn_cost(timeout=5.0)
    
    # On most systems, per-worker spawn should be under the maximum expected cost
    assert cost < MAX_EXPECTED_PER_WORKER_COST
    
    # Should still be positive and measurable
    assert cost > 0


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


def test_get_multiprocessing_start_method():
    """Test that get_multiprocessing_start_method returns a valid method."""
    method = get_multiprocessing_start_method()
    assert isinstance(method, str)
    assert method in ("fork", "spawn", "forkserver")


def test_get_default_start_method():
    """Test that _get_default_start_method returns the correct OS default."""
    default = _get_default_start_method()
    assert isinstance(default, str)
    assert default in ("fork", "spawn", "forkserver")
    
    # Verify OS-specific defaults
    system = platform.system()
    if system == "Windows":
        assert default == "spawn"
    elif system == "Darwin":
        # macOS defaults to spawn in Python 3.8+
        if sys.version_info >= (3, 8):
            assert default == "spawn"
        else:
            assert default == "fork"
    else:
        # Linux and other Unix systems default to fork
        assert default == "fork"


def test_get_spawn_cost_estimate_uses_start_method():
    """Test that spawn cost estimate is based on actual start method, not just OS."""
    # Clear cache to ensure fresh measurement
    _clear_spawn_cost_cache()
    
    cost = get_spawn_cost_estimate()
    assert isinstance(cost, float)
    assert cost > 0
    
    # The cost should match the current start method
    method = get_multiprocessing_start_method()
    if method == "fork":
        # Fork should be fast (10-20ms range)
        assert 0.01 <= cost <= 0.05
    elif method == "spawn":
        # Spawn should be slower (150-250ms range)
        assert 0.1 <= cost <= 0.5
    elif method == "forkserver":
        # Forkserver should be middle ground (50-150ms range)
        assert 0.03 <= cost <= 0.2


def test_check_start_method_mismatch():
    """Test start method mismatch detection."""
    is_mismatch, message = check_start_method_mismatch()
    
    assert isinstance(is_mismatch, bool)
    
    if is_mismatch:
        # If there's a mismatch, there should be a warning message
        assert message is not None
        assert isinstance(message, str)
        assert len(message) > 0
    else:
        # If no mismatch, message should be None
        assert message is None


def test_start_method_mismatch_logic():
    """Test the logic of start method mismatch detection."""
    actual = get_multiprocessing_start_method()
    default = _get_default_start_method()
    is_mismatch, message = check_start_method_mismatch()
    
    # If actual matches default, there should be no mismatch
    if actual == default:
        assert not is_mismatch
        assert message is None
    else:
        # If they differ, there should be a mismatch
        assert is_mismatch
        assert message is not None
        # Message should mention both methods
        assert actual in message
        assert default in message
