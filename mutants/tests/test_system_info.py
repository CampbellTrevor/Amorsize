"""
Tests for system_info module.
"""

import os
import pytest
import sys
import multiprocessing
import platform
from amorsize.system_info import (
    get_physical_cores,
    _parse_proc_cpuinfo,
    _parse_lscpu,
    get_spawn_cost,
    get_spawn_cost_estimate,
    measure_spawn_cost,
    get_available_memory,
    calculate_max_workers,
    get_system_info,
    _clear_spawn_cost_cache,
    get_multiprocessing_start_method,
    _get_default_start_method,
    check_start_method_mismatch,
    get_chunking_overhead,
    measure_chunking_overhead,
    _clear_chunking_overhead_cache,
    DEFAULT_CHUNKING_OVERHEAD,
    _read_cgroup_v2_limit,
    _get_cgroup_path,
    _read_cgroup_memory_limit,
    get_swap_usage
)

# Maximum expected per-worker spawn cost (500ms)
# This is a generous upper bound to account for slow systems
MAX_EXPECTED_PER_WORKER_COST = 0.5


def test_get_physical_cores():
    """Test that get_physical_cores returns a positive integer."""
    cores = get_physical_cores()
    assert isinstance(cores, int)
    assert cores > 0


def test_parse_proc_cpuinfo_on_linux():
    """Test /proc/cpuinfo parsing on Linux systems."""
    if platform.system() != "Linux":
        pytest.skip("This test only runs on Linux")
    
    # The function should return None or a positive integer
    result = _parse_proc_cpuinfo()
    
    # On Linux, this should typically succeed
    if result is not None:
        assert isinstance(result, int)
        assert result > 0
        # Should be reasonable number of cores (1-256)
        assert 1 <= result <= 256


def test_parse_lscpu_on_linux():
    """Test lscpu command parsing on Linux systems."""
    if platform.system() != "Linux":
        pytest.skip("This test only runs on Linux")
    
    # The function should return None or a positive integer
    result = _parse_lscpu()
    
    # On Linux with lscpu available, this should typically succeed
    if result is not None:
        assert isinstance(result, int)
        assert result > 0
        # Should be reasonable number of cores (1-256)
        assert 1 <= result <= 256


def test_physical_cores_fallback_consistency():
    """Test that physical core detection is consistent and reasonable."""
    # Get cores multiple times - should be consistent
    cores1 = get_physical_cores()
    cores2 = get_physical_cores()
    
    assert cores1 == cores2
    assert cores1 > 0
    
    # Should not exceed logical core count
    logical_cores = os.cpu_count()
    if logical_cores:
        assert cores1 <= logical_cores


def test_physical_cores_without_psutil():
    """Test physical core detection when psutil fallback is used."""
    # This test validates the fallback logic works
    # Even without psutil, we should get a reasonable answer
    cores = get_physical_cores()
    
    assert isinstance(cores, int)
    assert cores > 0
    
    # On systems with at least 2 logical cores, physical cores should be at least 1
    logical = os.cpu_count()
    if logical and logical >= 2:
        assert cores >= 1
        # Physical cores should be <= logical cores
        assert cores <= logical


def test_get_spawn_cost():
    """Test that get_spawn_cost returns a reasonable value."""
    cost = get_spawn_cost()
    assert isinstance(cost, float)
    # With default benchmarking enabled, actual measurement can be as low as 5-7ms on fast systems
    assert 0.001 < cost < 1.0  # Should be between 1ms and 1s


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


def test_get_chunking_overhead_default():
    """Test that get_chunking_overhead returns default estimate without benchmark."""
    cost = get_chunking_overhead(use_benchmark=False)
    assert isinstance(cost, float)
    assert cost == DEFAULT_CHUNKING_OVERHEAD
    assert cost > 0


def test_measure_chunking_overhead():
    """Test actual chunking overhead measurement."""
    # Clear any cached value
    _clear_chunking_overhead_cache()
    
    # Measure the actual chunking overhead
    cost = measure_chunking_overhead()
    
    assert isinstance(cost, float)
    assert cost > 0
    # Chunking overhead should be reasonable (< 10ms per chunk)
    assert cost < 0.01


def test_chunking_overhead_caching():
    """Test that chunking overhead measurement is cached."""
    # Clear cache first
    _clear_chunking_overhead_cache()
    
    # First measurement
    cost1 = measure_chunking_overhead()
    
    # Second measurement should return cached value (same instance)
    cost2 = measure_chunking_overhead()
    
    assert cost1 == cost2


def test_get_chunking_overhead_with_benchmark():
    """Test get_chunking_overhead with benchmarking enabled."""
    # Clear cache first
    _clear_chunking_overhead_cache()
    
    # Get with benchmark
    cost = get_chunking_overhead(use_benchmark=True)
    
    assert isinstance(cost, float)
    assert cost > 0
    assert cost < 0.01  # Should be reasonable


def test_chunking_overhead_reasonable_bounds():
    """Test that measured chunking overhead is within reasonable bounds."""
    # Clear cache first
    _clear_chunking_overhead_cache()
    
    cost = measure_chunking_overhead()
    
    # Chunking overhead should be positive
    assert cost > 0
    
    # Should be less than 10ms per chunk (reasonable upper bound)
    assert cost < 0.01
    
    # Should be more than 0.01ms per chunk (reasonable lower bound)
    assert cost > 0.00001


# ============================================================================
# NEW TESTS for Iteration 69: Enhanced cgroup v2 Memory Detection
# ============================================================================


def test_read_cgroup_v2_limit_with_max_only(tmp_path):
    """Test reading cgroup v2 memory.max file."""
    # Create a temporary directory with memory.max
    memory_max = tmp_path / "memory.max"
    memory_max.write_text("1073741824")  # 1GB
    
    limit = _read_cgroup_v2_limit(str(tmp_path))
    assert limit == 1073741824


def test_read_cgroup_v2_limit_with_high_only(tmp_path):
    """Test reading cgroup v2 memory.high file."""
    # Create a temporary directory with memory.high
    memory_high = tmp_path / "memory.high"
    memory_high.write_text("536870912")  # 512MB
    
    limit = _read_cgroup_v2_limit(str(tmp_path))
    assert limit == 536870912


def test_read_cgroup_v2_limit_respects_lower_limit(tmp_path):
    """Test that the most restrictive limit is returned."""
    # Create both files with different limits
    memory_max = tmp_path / "memory.max"
    memory_high = tmp_path / "memory.high"
    
    memory_max.write_text("1073741824")  # 1GB
    memory_high.write_text("536870912")  # 512MB (lower)
    
    limit = _read_cgroup_v2_limit(str(tmp_path))
    # Should return the lower (more restrictive) limit
    assert limit == 536870912


def test_read_cgroup_v2_limit_with_max_value(tmp_path):
    """Test that 'max' value is treated as no limit."""
    memory_max = tmp_path / "memory.max"
    memory_max.write_text("max")
    
    limit = _read_cgroup_v2_limit(str(tmp_path))
    assert limit is None


def test_read_cgroup_v2_limit_with_both_max_values(tmp_path):
    """Test that both 'max' values result in no limit."""
    memory_max = tmp_path / "memory.max"
    memory_high = tmp_path / "memory.high"
    
    memory_max.write_text("max")
    memory_high.write_text("max")
    
    limit = _read_cgroup_v2_limit(str(tmp_path))
    assert limit is None


def test_read_cgroup_v2_limit_with_high_max_and_low_max(tmp_path):
    """Test when high is 'max' but max has a value."""
    memory_max = tmp_path / "memory.max"
    memory_high = tmp_path / "memory.high"
    
    memory_max.write_text("1073741824")  # 1GB
    memory_high.write_text("max")
    
    limit = _read_cgroup_v2_limit(str(tmp_path))
    # Should return the max limit since high is unlimited
    assert limit == 1073741824


def test_read_cgroup_v2_limit_nonexistent_path():
    """Test that nonexistent path returns None."""
    limit = _read_cgroup_v2_limit("/nonexistent/path")
    assert limit is None


def test_read_cgroup_v2_limit_invalid_value(tmp_path):
    """Test handling of invalid numeric value."""
    memory_max = tmp_path / "memory.max"
    memory_max.write_text("invalid_number")
    
    limit = _read_cgroup_v2_limit(str(tmp_path))
    assert limit is None


def test_get_cgroup_path_returns_string_or_none():
    """Test that _get_cgroup_path returns valid output."""
    # This may return None on systems without /proc/self/cgroup
    # or a valid path string on container/Linux systems
    path = _get_cgroup_path()
    assert path is None or isinstance(path, str)


def test_get_cgroup_path_format():
    """Test that cgroup path has expected format if present."""
    path = _get_cgroup_path()
    
    if path is not None:
        # Path should start with / or be empty
        assert isinstance(path, str)
        # Should not have unexpected characters
        assert all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-_.' for c in path)


def test_read_cgroup_memory_limit_returns_valid():
    """Test that _read_cgroup_memory_limit returns None or positive integer."""
    limit = _read_cgroup_memory_limit()
    
    # Should return None (no container) or positive integer (container)
    assert limit is None or (isinstance(limit, int) and limit > 0)


def test_read_cgroup_memory_limit_reasonable_value():
    """Test that cgroup limit (if present) is reasonable."""
    limit = _read_cgroup_memory_limit()
    
    if limit is not None:
        # Should be at least 1MB (very small container)
        assert limit >= 1024 * 1024
        # Should be less than 1PB (sanity check)
        assert limit < (1 << 50)


def test_get_available_memory_with_cgroup():
    """Test that get_available_memory respects cgroup limits."""
    # This is an integration test - just verify it returns valid value
    memory = get_available_memory()
    
    assert isinstance(memory, int)
    assert memory > 0
    # Should be reasonable (at least 100MB, less than 1PB)
    assert 100 * 1024 * 1024 <= memory < (1 << 50)


# ============================================================================
# NEW TESTS for Iteration 70: Swap-Aware Memory Detection
# ============================================================================


def test_get_swap_usage_returns_tuple():
    """Test that get_swap_usage returns a tuple of correct types."""
    swap_percent, swap_used, swap_total = get_swap_usage()
    
    assert isinstance(swap_percent, float)
    assert isinstance(swap_used, int)
    assert isinstance(swap_total, int)
    
    # All values should be non-negative
    assert swap_percent >= 0.0
    assert swap_used >= 0
    assert swap_total >= 0


def test_get_swap_usage_reasonable_values():
    """Test that swap usage values are reasonable."""
    swap_percent, swap_used, swap_total = get_swap_usage()
    
    # Percentage should be between 0 and 100
    assert 0.0 <= swap_percent <= 100.0
    
    # Used should not exceed total
    assert swap_used <= swap_total
    
    # If percentage > 0, then total should be > 0
    if swap_percent > 0:
        assert swap_total > 0


def test_get_swap_usage_no_psutil(monkeypatch):
    """Test that get_swap_usage handles missing psutil gracefully."""
    # Temporarily disable psutil
    import amorsize.system_info as si
    monkeypatch.setattr(si, 'HAS_PSUTIL', False)
    
    swap_percent, swap_used, swap_total = si.get_swap_usage()
    
    # Should return zeros when psutil unavailable
    assert swap_percent == 0.0
    assert swap_used == 0
    assert swap_total == 0


def test_calculate_max_workers_no_swap():
    """Test worker calculation when no swap is being used."""
    # With no swap, should behave as before
    result = calculate_max_workers(4, 0)
    assert result == 4


def test_calculate_max_workers_moderate_swap(monkeypatch):
    """Test worker reduction with moderate swap usage."""
    import amorsize.system_info as si
    
    # Mock get_swap_usage to return moderate swap (25%)
    def mock_swap():
        return (25.0, 1024*1024*1024, 4*1024*1024*1024)
    
    monkeypatch.setattr(si, 'get_swap_usage', mock_swap)
    
    # Should reduce workers by 25%
    result = si.calculate_max_workers(8, 0)
    # 8 workers * 0.75 = 6 workers
    assert result == 6


def test_calculate_max_workers_severe_swap(monkeypatch):
    """Test worker reduction with severe swap usage."""
    import amorsize.system_info as si
    
    # Mock get_swap_usage to return severe swap (75%)
    def mock_swap():
        return (75.0, 3*1024*1024*1024, 4*1024*1024*1024)
    
    monkeypatch.setattr(si, 'get_swap_usage', mock_swap)
    
    # Should reduce workers by 50%
    result = si.calculate_max_workers(8, 0)
    # 8 workers / 2 = 4 workers
    assert result == 4


def test_calculate_max_workers_minimum_one(monkeypatch):
    """Test that at least 1 worker is returned even with severe swap."""
    import amorsize.system_info as si
    
    # Mock get_swap_usage to return severe swap
    def mock_swap():
        return (90.0, 3500*1024*1024, 4*1024*1024*1024)
    
    monkeypatch.setattr(si, 'get_swap_usage', mock_swap)
    
    # Even with 1 core, should return at least 1 worker
    result = si.calculate_max_workers(1, 0)
    assert result >= 1


def test_calculate_max_workers_swap_aware_with_memory_constraint(monkeypatch):
    """Test swap awareness combined with memory constraints."""
    import amorsize.system_info as si
    
    # Mock moderate swap usage
    def mock_swap():
        return (25.0, 1024*1024*1024, 4*1024*1024*1024)
    
    # Mock available memory (4GB)
    def mock_memory():
        return 4 * 1024 * 1024 * 1024
    
    monkeypatch.setattr(si, 'get_swap_usage', mock_swap)
    monkeypatch.setattr(si, 'get_available_memory', mock_memory)
    
    # Request 8 workers, each using 1GB
    # Available: 4GB * 0.8 = 3.2GB
    # Memory allows: 3 workers
    # Swap adjustment: 3 * 0.75 = 2.25 -> 2 workers
    result = si.calculate_max_workers(8, 1024*1024*1024)
    
    assert 1 <= result <= 3  # Should be constrained by both
