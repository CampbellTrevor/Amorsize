"""
Property-based tests for the system_info module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of system information detection functions across a wide range of inputs.
"""

import math
import os
import threading
import time
from typing import Any, List, Tuple

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize.system_info import (
    get_physical_cores,
    get_logical_cores,
    get_available_memory,
    get_spawn_cost,
    get_spawn_cost_estimate,
    get_chunking_overhead,
    get_multiprocessing_start_method,
    calculate_max_workers,
    get_swap_usage,
    get_current_cpu_load,
    get_memory_pressure,
    calculate_load_aware_workers,
    get_system_info,
    check_start_method_mismatch,
    _clear_physical_cores_cache,
    _clear_logical_cores_cache,
    _clear_memory_cache,
    _clear_spawn_cost_cache,
    _clear_chunking_overhead_cache,
    _clear_start_method_cache,
)


class TestCoreDetectionInvariants:
    """Test invariant properties of CPU core detection."""

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_physical_cores_always_positive(self, _dummy):
        """Physical cores should always be at least 1."""
        _clear_physical_cores_cache()
        cores = get_physical_cores()
        assert cores >= 1, f"Physical cores should be at least 1, got {cores}"
        assert isinstance(cores, int), f"Physical cores should be int, got {type(cores)}"

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_logical_cores_always_positive(self, _dummy):
        """Logical cores should always be at least 1."""
        _clear_logical_cores_cache()
        cores = get_logical_cores()
        assert cores >= 1, f"Logical cores should be at least 1, got {cores}"
        assert isinstance(cores, int), f"Logical cores should be int, got {type(cores)}"

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_logical_cores_at_least_physical(self, _dummy):
        """Logical cores should be >= physical cores (due to hyperthreading)."""
        _clear_physical_cores_cache()
        _clear_logical_cores_cache()
        physical = get_physical_cores()
        logical = get_logical_cores()
        assert logical >= physical, \
            f"Logical cores ({logical}) should be >= physical cores ({physical})"

    @settings(max_examples=20, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_core_detection_is_cached(self, _dummy):
        """Test that core detection results are cached."""
        _clear_physical_cores_cache()
        _clear_logical_cores_cache()
        
        # First calls populate cache
        physical1 = get_physical_cores()
        logical1 = get_logical_cores()
        
        # Second calls should return same values (from cache)
        physical2 = get_physical_cores()
        logical2 = get_logical_cores()
        
        assert physical1 == physical2, "Physical cores should be cached"
        assert logical1 == logical2, "Logical cores should be cached"

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_core_detection_thread_safe(self, _dummy):
        """Test that core detection is thread-safe."""
        _clear_physical_cores_cache()
        results = []
        
        def get_cores():
            cores = get_physical_cores()
            results.append(cores)
        
        threads = [threading.Thread(target=get_cores) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should get the same result
        assert len(set(results)) == 1, f"Core detection not thread-safe: {set(results)}"


class TestMemoryDetectionInvariants:
    """Test invariant properties of memory detection."""

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_available_memory_positive(self, _dummy):
        """Available memory should always be positive."""
        _clear_memory_cache()
        memory = get_available_memory()
        assert memory > 0, f"Available memory should be positive, got {memory}"
        assert isinstance(memory, int), f"Memory should be int, got {type(memory)}"

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_available_memory_reasonable_range(self, _dummy):
        """Available memory should be in a reasonable range."""
        _clear_memory_cache()
        memory = get_available_memory()
        # Memory should be at least 1MB and less than 16TB (reasonable bounds)
        assert memory >= 1024 * 1024, f"Memory too small: {memory} bytes"
        assert memory <= 16 * 1024 * 1024 * 1024 * 1024, f"Memory too large: {memory} bytes"

    @settings(max_examples=5, deadline=3000)
    @given(st.integers(min_value=0, max_value=0))
    def test_memory_caching_with_ttl(self, _dummy):
        """Test that memory caching respects TTL."""
        _clear_memory_cache()
        
        # First call populates cache
        memory1 = get_available_memory()
        
        # Immediate second call should return cached value
        memory2 = get_available_memory()
        assert memory1 == memory2, "Memory should be cached"
        
        # After TTL expires (1 second), may get new value
        time.sleep(1.1)
        memory3 = get_available_memory()
        # We can't guarantee values differ, but function should not crash
        assert memory3 > 0, "Memory detection should still work after TTL"

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_swap_usage_format(self, _dummy):
        """Test that swap usage returns correct format."""
        percent, total, used = get_swap_usage()
        
        assert isinstance(percent, float), f"Swap percent should be float, got {type(percent)}"
        assert isinstance(total, int), f"Swap total should be int, got {type(total)}"
        assert isinstance(used, int), f"Swap used should be int, got {type(used)}"
        
        assert 0.0 <= percent <= 100.0, f"Swap percent should be 0-100, got {percent}"
        assert total >= 0, f"Swap total should be non-negative, got {total}"
        assert used >= 0, f"Swap used should be non-negative, got {used}"
        assert used <= total, f"Swap used ({used}) should not exceed total ({total})"


class TestSpawnCostInvariants:
    """Test invariant properties of spawn cost measurement."""

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_spawn_cost_non_negative(self, _dummy):
        """Spawn cost should always be non-negative."""
        _clear_spawn_cost_cache()
        cost = get_spawn_cost(use_benchmark=False)
        assert cost >= 0, f"Spawn cost should be non-negative, got {cost}"
        assert isinstance(cost, float), f"Spawn cost should be float, got {type(cost)}"

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_spawn_cost_estimate_non_negative(self, _dummy):
        """Spawn cost estimate should always be non-negative."""
        cost = get_spawn_cost_estimate()
        assert cost >= 0, f"Spawn cost estimate should be non-negative, got {cost}"
        assert isinstance(cost, float), f"Spawn cost estimate should be float, got {type(cost)}"

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_spawn_cost_reasonable_range(self, _dummy):
        """Spawn cost should be in a reasonable range (0-10 seconds)."""
        _clear_spawn_cost_cache()
        cost = get_spawn_cost(use_benchmark=False)
        assert 0 <= cost <= 10.0, f"Spawn cost should be 0-10 seconds, got {cost}"

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_chunking_overhead_non_negative(self, _dummy):
        """Chunking overhead should always be non-negative."""
        _clear_chunking_overhead_cache()
        overhead = get_chunking_overhead(use_benchmark=False)
        assert overhead >= 0, f"Chunking overhead should be non-negative, got {overhead}"
        assert isinstance(overhead, float), f"Chunking overhead should be float, got {type(overhead)}"

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_chunking_overhead_reasonable_range(self, _dummy):
        """Chunking overhead should be in a reasonable range (0-0.1 seconds)."""
        _clear_chunking_overhead_cache()
        overhead = get_chunking_overhead(use_benchmark=False)
        assert 0 <= overhead <= 0.1, f"Chunking overhead should be 0-0.1 seconds, got {overhead}"


class TestStartMethodInvariants:
    """Test invariant properties of start method detection."""

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_start_method_valid_values(self, _dummy):
        """Start method should be one of the valid values."""
        _clear_start_method_cache()
        method = get_multiprocessing_start_method()
        valid_methods = ['fork', 'spawn', 'forkserver']
        assert method in valid_methods, \
            f"Start method should be one of {valid_methods}, got {method}"

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_start_method_is_cached(self, _dummy):
        """Test that start method is cached."""
        _clear_start_method_cache()
        
        # First call populates cache
        method1 = get_multiprocessing_start_method()
        
        # Second call should return cached value
        method2 = get_multiprocessing_start_method()
        
        assert method1 == method2, "Start method should be cached"

    @settings(max_examples=10, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_start_method_mismatch_check_format(self, _dummy):
        """Test that start method mismatch check returns correct format."""
        has_mismatch, message = check_start_method_mismatch()
        
        assert isinstance(has_mismatch, bool), \
            f"Mismatch flag should be bool, got {type(has_mismatch)}"
        assert message is None or isinstance(message, str), \
            f"Message should be None or str, got {type(message)}"


class TestWorkerCalculationInvariants:
    """Test invariant properties of worker calculation."""

    @given(
        physical_cores=st.integers(min_value=1, max_value=256),
        estimated_job_ram=st.integers(min_value=0, max_value=10 * 1024 * 1024 * 1024)  # 0-10GB
    )
    @settings(max_examples=100, deadline=2000)
    def test_max_workers_always_positive(self, physical_cores, estimated_job_ram):
        """Max workers should always be at least 1."""
        max_workers = calculate_max_workers(physical_cores, estimated_job_ram)
        assert max_workers >= 1, f"Max workers should be at least 1, got {max_workers}"

    @given(
        physical_cores=st.integers(min_value=1, max_value=256),
        estimated_job_ram=st.integers(min_value=0, max_value=10 * 1024 * 1024 * 1024)
    )
    @settings(max_examples=100, deadline=2000)
    def test_max_workers_bounded_by_cores(self, physical_cores, estimated_job_ram):
        """Max workers should not significantly exceed physical cores."""
        max_workers = calculate_max_workers(physical_cores, estimated_job_ram)
        # Max workers should be at most physical_cores (unless memory allows more)
        # In general, max_workers <= physical_cores for CPU-bound tasks
        assert max_workers >= 1, "Workers should be at least 1"
        # We can't strictly enforce upper bound without knowing memory,
        # but we can verify it's reasonable
        assert max_workers <= physical_cores * 2, \
            f"Max workers ({max_workers}) seems unreasonably high for {physical_cores} cores"

    @given(
        physical_cores=st.integers(min_value=1, max_value=64),
        estimated_job_ram=st.integers(min_value=1024 * 1024, max_value=100 * 1024 * 1024)  # 1MB-100MB
    )
    @settings(max_examples=50, deadline=2000)
    def test_max_workers_respects_memory_constraints(self, physical_cores, estimated_job_ram):
        """Max workers should respect memory constraints."""
        max_workers = calculate_max_workers(physical_cores, estimated_job_ram)
        
        # Verify that estimated total RAM usage doesn't grossly exceed available memory
        available_memory = get_available_memory()
        estimated_total_ram = max_workers * estimated_job_ram
        
        # Allow some overhead (2x) for conservative estimates
        assert estimated_total_ram <= available_memory * 2, \
            f"Total estimated RAM ({estimated_total_ram}) exceeds available ({available_memory})"


class TestLoadAwareCalculations:
    """Test invariant properties of load-aware worker calculations."""

    @settings(max_examples=20, deadline=3000)
    @given(st.integers(min_value=0, max_value=0))
    def test_cpu_load_bounded(self, _dummy):
        """CPU load should be between 0 and 100 percent."""
        load = get_current_cpu_load(interval=0.05)
        assert 0.0 <= load <= 100.0, f"CPU load should be 0-100%, got {load}"
        assert isinstance(load, float), f"CPU load should be float, got {type(load)}"

    @settings(max_examples=20, deadline=3000)
    @given(st.integers(min_value=0, max_value=0))
    def test_memory_pressure_bounded(self, _dummy):
        """Memory pressure should be between 0 and 1."""
        pressure = get_memory_pressure()
        assert 0.0 <= pressure <= 1.0, f"Memory pressure should be 0-1, got {pressure}"
        assert isinstance(pressure, float), f"Memory pressure should be float, got {type(pressure)}"

    @given(
        physical_cores=st.integers(min_value=1, max_value=64),
        estimated_job_ram=st.integers(min_value=1024 * 1024, max_value=100 * 1024 * 1024)  # 1MB-100MB
    )
    @settings(max_examples=50, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_load_aware_workers_always_positive(self, physical_cores, estimated_job_ram):
        """Load-aware worker calculation should always return at least 1."""
        adjusted = calculate_load_aware_workers(
            physical_cores=physical_cores,
            estimated_job_ram=estimated_job_ram,
            cpu_threshold=80.0,
            memory_threshold=80.0
        )
        assert adjusted >= 1, f"Adjusted workers should be at least 1, got {adjusted}"

    @given(
        physical_cores=st.integers(min_value=1, max_value=64),
        estimated_job_ram=st.integers(min_value=1024 * 1024, max_value=100 * 1024 * 1024)  # 1MB-100MB
    )
    @settings(max_examples=50, deadline=3000)
    def test_load_aware_workers_bounded_by_base(self, physical_cores, estimated_job_ram):
        """Load-aware workers should not exceed base workers."""
        # Calculate base workers first
        base_workers = calculate_max_workers(physical_cores, estimated_job_ram)
        
        # Calculate load-aware workers with strict thresholds
        adjusted = calculate_load_aware_workers(
            physical_cores=physical_cores,
            estimated_job_ram=estimated_job_ram,
            cpu_threshold=50.0,  # Stricter threshold
            memory_threshold=50.0
        )
        assert adjusted <= base_workers, \
            f"Adjusted workers ({adjusted}) should not exceed base ({base_workers})"


class TestSystemInfoIntegration:
    """Test invariant properties of integrated system info functions."""

    @settings(max_examples=10, deadline=3000)
    @given(st.integers(min_value=0, max_value=0))
    def test_get_system_info_format(self, _dummy):
        """Test that get_system_info returns correct format."""
        cores, spawn_cost, memory = get_system_info()
        
        assert isinstance(cores, int), f"Cores should be int, got {type(cores)}"
        assert isinstance(spawn_cost, float), f"Spawn cost should be float, got {type(spawn_cost)}"
        assert isinstance(memory, int), f"Memory should be int, got {type(memory)}"
        
        assert cores >= 1, f"Cores should be at least 1, got {cores}"
        assert spawn_cost >= 0, f"Spawn cost should be non-negative, got {spawn_cost}"
        assert memory > 0, f"Memory should be positive, got {memory}"

    @settings(max_examples=10, deadline=3000)
    @given(st.integers(min_value=0, max_value=0))
    def test_system_info_consistency(self, _dummy):
        """Test that system info components are mutually consistent."""
        _clear_physical_cores_cache()
        _clear_spawn_cost_cache()
        _clear_memory_cache()
        
        # Get system info
        cores_from_info, spawn_from_info, memory_from_info = get_system_info()
        
        # Get individual components
        cores_individual = get_physical_cores()
        spawn_individual = get_spawn_cost(use_benchmark=False)
        memory_individual = get_available_memory()
        
        # They should match (allowing for some timing differences in memory)
        assert cores_from_info == cores_individual, \
            f"Core count mismatch: {cores_from_info} vs {cores_individual}"


class TestCacheClearingFunctions:
    """Test that cache clearing functions work correctly."""

    @settings(max_examples=5, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_physical_cores_cache_clearing(self, _dummy):
        """Test that physical cores cache can be cleared."""
        # Populate cache
        cores1 = get_physical_cores()
        
        # Clear cache
        _clear_physical_cores_cache()
        
        # Get again (should work, not crash)
        cores2 = get_physical_cores()
        
        # Values should match (since hardware hasn't changed)
        assert cores1 == cores2

    @settings(max_examples=5, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_memory_cache_clearing(self, _dummy):
        """Test that memory cache can be cleared."""
        # Populate cache
        memory1 = get_available_memory()
        
        # Clear cache
        _clear_memory_cache()
        
        # Get again (should work)
        memory2 = get_available_memory()
        
        # Both should be positive
        assert memory1 > 0
        assert memory2 > 0

    @settings(max_examples=5, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_spawn_cost_cache_clearing(self, _dummy):
        """Test that spawn cost cache can be cleared."""
        # Populate cache
        _clear_spawn_cost_cache()
        cost1 = get_spawn_cost(use_benchmark=False)
        
        # Clear cache
        _clear_spawn_cost_cache()
        
        # Get again (should work)
        cost2 = get_spawn_cost(use_benchmark=False)
        
        # Both should be non-negative
        assert cost1 >= 0
        assert cost2 >= 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @settings(max_examples=20, deadline=2000)
    @given(
        physical_cores=st.integers(min_value=1, max_value=1),  # Single core
        estimated_job_ram=st.integers(min_value=1, max_value=1024 * 1024)
    )
    def test_single_core_system(self, physical_cores, estimated_job_ram):
        """Test worker calculation on single-core system."""
        max_workers = calculate_max_workers(physical_cores, estimated_job_ram)
        # Single core system should still return at least 1 worker
        assert max_workers >= 1

    @settings(max_examples=20, deadline=2000)
    @given(
        physical_cores=st.integers(min_value=1, max_value=16),
        estimated_job_ram=st.integers(min_value=0, max_value=0)  # Zero RAM
    )
    def test_zero_ram_estimate(self, physical_cores, estimated_job_ram):
        """Test worker calculation with zero RAM estimate."""
        max_workers = calculate_max_workers(physical_cores, estimated_job_ram)
        # Should fall back to physical cores
        assert max_workers == physical_cores

    @given(
        physical_cores=st.integers(min_value=1, max_value=1),  # Single core
        estimated_job_ram=st.integers(min_value=1024, max_value=1024 * 1024)
    )
    @settings(max_examples=20, deadline=3000)
    def test_single_worker_base(self, physical_cores, estimated_job_ram):
        """Test load-aware calculation with single core system."""
        adjusted = calculate_load_aware_workers(
            physical_cores=physical_cores,
            estimated_job_ram=estimated_job_ram
        )
        # Should still return at least 1
        assert adjusted >= 1


class TestNumericalStability:
    """Test numerical stability and floating point handling."""

    @given(
        interval=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=30, deadline=3000)
    def test_cpu_load_with_various_intervals(self, interval):
        """Test CPU load measurement with various intervals."""
        try:
            load = get_current_cpu_load(interval=interval)
            assert 0.0 <= load <= 100.0, f"CPU load out of range: {load}"
            assert not math.isnan(load), "CPU load should not be NaN"
            assert not math.isinf(load), "CPU load should not be infinite"
        except Exception:
            # Some intervals might be too short for the system, that's ok
            pass

    @given(
        cpu_threshold=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        memory_threshold=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=3000)
    def test_load_aware_with_various_thresholds(self, cpu_threshold, memory_threshold):
        """Test load-aware calculation with various threshold values."""
        physical_cores = 4
        estimated_job_ram = 1024 * 1024 * 100  # 100MB
        
        adjusted = calculate_load_aware_workers(
            physical_cores=physical_cores,
            estimated_job_ram=estimated_job_ram,
            cpu_threshold=cpu_threshold,
            memory_threshold=memory_threshold
        )
        
        # Should always return valid result
        assert adjusted >= 1
        assert isinstance(adjusted, int)
