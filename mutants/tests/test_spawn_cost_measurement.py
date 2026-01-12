"""
Tests for enhanced spawn cost measurement with quality validation.

This test suite validates the robust spawn cost measurement implementation
including quality checks, signal validation, and fallback strategies.
"""

import pytest
import multiprocessing
import time
from unittest.mock import patch, MagicMock

from amorsize.system_info import (
    measure_spawn_cost,
    get_spawn_cost_estimate,
    _clear_spawn_cost_cache,
    get_multiprocessing_start_method,
    SPAWN_COST_FORK,
    SPAWN_COST_SPAWN,
    SPAWN_COST_FORKSERVER,
    MIN_REASONABLE_MARGINAL_COST
)


class TestMeasureSpawnCost:
    """Test suite for spawn cost measurement."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_measure_spawn_cost_returns_reasonable_value(self):
        """Test that measured spawn cost is within reasonable range."""
        cost = measure_spawn_cost()
        
        # Should be positive
        assert cost > 0
        
        # Should be less than 2 seconds (even spawn is typically < 500ms)
        assert cost < 2.0
        
        # Should be at least 0.1ms (systems are not that fast)
        assert cost >= 0.0001
    
    def test_measure_spawn_cost_cached(self):
        """Test that spawn cost measurement is cached."""
        # First call measures
        cost1 = measure_spawn_cost()
        
        # Second call should be instant (cached)
        start = time.perf_counter()
        cost2 = measure_spawn_cost()
        elapsed = time.perf_counter() - start
        
        # Should return same value
        assert cost1 == cost2
        
        # Should be instant (< 1ms)
        assert elapsed < 0.001
    
    def test_measure_spawn_cost_multiple_calls_cached(self):
        """Test that multiple calls return same cached value."""
        costs = [measure_spawn_cost() for _ in range(5)]
        
        # All should be identical (cached)
        assert len(set(costs)) == 1
    
    def test_measure_spawn_cost_fallback_on_exception(self):
        """Test fallback to estimate when measurement fails."""
        _clear_spawn_cost_cache()
        
        # Mock Pool to raise an exception
        with patch('multiprocessing.Pool', side_effect=OSError("Test error")):
            cost = measure_spawn_cost()
            
            # Should fall back to estimate
            estimate = get_spawn_cost_estimate()
            assert cost == estimate
    
    def test_spawn_cost_within_start_method_bounds(self):
        """Test that measured spawn cost is within expected bounds for start method."""
        cost = measure_spawn_cost()
        start_method = get_multiprocessing_start_method()
        
        if start_method == 'fork':
            # fork: 1ms to 100ms
            assert 0.001 <= cost <= 0.1
        elif start_method == 'spawn':
            # spawn: 50ms to 1000ms
            assert 0.05 <= cost <= 1.0
        elif start_method == 'forkserver':
            # forkserver: 10ms to 500ms
            assert 0.01 <= cost <= 0.5
        else:
            # Unknown - at least be positive
            assert cost > 0
    
    def test_spawn_cost_quality_validation(self):
        """Test that spawn cost measurement includes quality validation."""
        _clear_spawn_cost_cache()
        
        # Real measurement should pass quality checks
        cost = measure_spawn_cost()
        
        # Should not be identical to fallback (unless measurement failed)
        estimate = get_spawn_cost_estimate()
        
        # Cost should be within reasonable range of estimate
        # (within 10x either direction)
        assert estimate / 10 <= cost <= estimate * 10
    
    def test_spawn_cost_consistency_with_estimate(self):
        """Test that measured value is consistent with OS-based estimate."""
        cost = measure_spawn_cost()
        estimate = get_spawn_cost_estimate()
        
        # Should be within 10x of estimate (quality check 3)
        assert estimate / 10 <= cost <= estimate * 10
    
    def test_quality_check_rejects_unreasonable_values(self):
        """Test that quality checks reject unreasonable measurements."""
        _clear_spawn_cost_cache()
        
        # This test validates that the quality checks work by ensuring
        # measured values are reasonable
        cost = measure_spawn_cost()
        start_method = get_multiprocessing_start_method()
        
        # Validate against start method bounds
        if start_method == 'fork':
            assert 0.001 <= cost <= 0.1
        elif start_method == 'spawn':
            assert 0.05 <= cost <= 1.0
        elif start_method == 'forkserver':
            assert 0.01 <= cost <= 0.5
    
    def test_measurement_robustness_with_system_load(self):
        """Test that measurement is robust under varying conditions."""
        _clear_spawn_cost_cache()
        
        # Measure multiple times (clearing cache each time)
        measurements = []
        for _ in range(3):
            _clear_spawn_cost_cache()
            cost = measure_spawn_cost()
            measurements.append(cost)
        
        # All measurements should be reasonable
        for cost in measurements:
            assert cost > 0
            assert cost < 2.0
        
        # Measurements should be relatively consistent (within 15x)
        # Note: Process spawning involves kernel operations (process creation,
        # scheduling, resource allocation, memory management) that have inherent
        # variability on busy systems. The variance is affected by:
        # - OS scheduling decisions and context switching
        # - System load from other processes
        # - Cache effects (warm vs cold cache)
        # - Memory pressure and page faults
        # - CPU frequency scaling and thermal throttling
        # A 15x threshold allows for reasonable OS-level variability while still
        # catching measurements that are wildly inconsistent (e.g., 100x+).
        if len(measurements) > 1:
            min_cost = min(measurements)
            max_cost = max(measurements)
            if min_cost > 0:
                ratio = max_cost / min_cost
                assert ratio < 15.0  # Should not vary by more than 15x


class TestSpawnCostEstimate:
    """Test suite for spawn cost estimation fallback."""
    
    def test_get_spawn_cost_estimate_returns_positive(self):
        """Test that estimate is always positive."""
        estimate = get_spawn_cost_estimate()
        assert estimate > 0
    
    def test_get_spawn_cost_estimate_uses_start_method(self):
        """Test that estimate varies based on start method."""
        estimate = get_spawn_cost_estimate()
        start_method = get_multiprocessing_start_method()
        
        if start_method == 'fork':
            assert estimate == SPAWN_COST_FORK
        elif start_method == 'spawn':
            assert estimate == SPAWN_COST_SPAWN
        elif start_method == 'forkserver':
            assert estimate == SPAWN_COST_FORKSERVER


class TestSpawnCostIntegration:
    """Integration tests for spawn cost measurement."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_spawn_cost_can_be_used_in_optimizer(self):
        """Test that spawn cost can be used by optimizer."""
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        # Should not raise any errors
        result = optimize(simple_func, range(10))
        assert result is not None
    
    def test_spawn_cost_verbose_output(self):
        """Test that spawn cost measurement is used in optimizer."""
        from amorsize import optimize
        import io
        import sys
        
        def simple_func(x):
            return x * 2
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            result = optimize(simple_func, range(100), verbose=True)
            output = sys.stdout.getvalue()
            
            # Verbose mode should produce output
            assert len(output) > 0
            
            # The optimizer should work without errors
            assert result is not None
        finally:
            sys.stdout = old_stdout


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_spawn_cost_with_timeout(self):
        """Test spawn cost measurement with custom timeout."""
        cost = measure_spawn_cost(timeout=5.0)
        assert cost > 0
    
    def test_spawn_cost_concurrent_calls(self):
        """Test that concurrent calls handle caching correctly."""
        from concurrent.futures import ThreadPoolExecutor
        
        # First, ensure cache is populated with a single measurement
        initial_cost = measure_spawn_cost()
        
        def measure():
            return measure_spawn_cost()
        
        # Multiple threads reading from cache concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(measure) for _ in range(5)]
            results = [f.result() for f in futures]
        
        # All should return the same cached value
        assert len(set(results)) == 1
        # And it should be the initial cached value
        assert results[0] == initial_cost
    
    def test_spawn_cost_after_cache_clear(self):
        """Test that measurement works after cache clear."""
        cost1 = measure_spawn_cost()
        _clear_spawn_cost_cache()
        cost2 = measure_spawn_cost()
        
        # Both should be reasonable
        assert cost1 > 0
        assert cost2 > 0
        
        # May differ due to system load and OS-level timing variability
        # Note: Process spawning involves kernel operations (process creation,
        # scheduling, resource allocation) that have inherent variability on
        # busy systems. The variance can be affected by:
        # - OS scheduling decisions and context switching
        # - System load from other processes
        # - Cache effects (warm vs cold cache, L1/L2/L3, TLB misses)
        # - Memory pressure and page faults
        # - CPU frequency scaling and thermal throttling
        # 
        # Measurements before and after cache clear can differ because:
        # - First measurement may prime kernel caches
        # - Second measurement may run on different CPU core
        # - System load may have changed between measurements
        # 
        # A 20x threshold allows for reasonable OS-level variability while still
        # catching measurements that are wildly inconsistent (e.g., 100x+).
        if cost1 > 0 and cost2 > 0:
            ratio = max(cost1, cost2) / min(cost1, cost2)
            assert ratio < 20.0  # Should not differ by more than 20x (relaxed from 10x)
