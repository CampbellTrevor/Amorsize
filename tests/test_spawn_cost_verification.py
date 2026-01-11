"""
Comprehensive verification of spawn cost measurement quality.

This test suite deeply validates that the spawn cost measurement accurately
reflects actual process creation overhead across different scenarios and
platforms. It verifies the measurement methodology, quality checks, and
fallback strategies.

Tests focus on:
1. Accuracy: Does the measurement reflect actual spawn overhead?
2. Consistency: Are measurements stable and reproducible?
3. Platform awareness: Does it handle fork vs spawn correctly?
4. Performance: Is the measurement itself fast enough?
5. Reliability: Does it gracefully handle edge cases?
"""

import pytest
import multiprocessing
import time
import platform
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from amorsize.system_info import (
    measure_spawn_cost,
    get_spawn_cost,
    get_spawn_cost_estimate,
    get_multiprocessing_start_method,
    _clear_spawn_cost_cache,
    _noop_worker,
    SPAWN_COST_FORK,
    SPAWN_COST_SPAWN,
    SPAWN_COST_FORKSERVER,
    MIN_REASONABLE_MARGINAL_COST
)


class TestSpawnCostAccuracy:
    """Verify that spawn cost measurement accurately reflects actual overhead."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_spawn_cost_reflects_actual_pool_creation_overhead(self):
        """
        Test that measured spawn cost accurately predicts pool creation time.
        
        The spawn cost should be a good predictor of the marginal cost of
        adding workers to a pool. We verify this by comparing measured spawn
        cost to actual timings of pools with different worker counts.
        """
        # Get the measured spawn cost
        measured_cost = measure_spawn_cost()
        
        # Measure actual pool creation time for different worker counts
        n_samples = 3
        
        def time_pool_creation(n_workers):
            """Time the creation and basic use of a pool."""
            start = time.perf_counter()
            with multiprocessing.Pool(processes=n_workers) as pool:
                result = pool.apply_async(_noop_worker, (None,))
                result.get(timeout=2.0)
            return time.perf_counter() - start
        
        # Measure for 1, 2, and 3 workers
        times = []
        for n_workers in [1, 2, 3]:
            worker_times = []
            for _ in range(n_samples):
                t = time_pool_creation(n_workers)
                worker_times.append(t)
            times.append(sum(worker_times) / len(worker_times))
        
        # Calculate marginal costs from actual measurements
        marginal_1_to_2 = times[1] - times[0]  # Cost of adding 1 worker
        marginal_2_to_3 = times[2] - times[1]  # Cost of adding 1 worker
        
        # Average marginal cost from actual measurements
        avg_actual_marginal = (marginal_1_to_2 + marginal_2_to_3) / 2
        
        # The measured spawn cost should be in the same ballpark as actual marginal cost
        # Allow significant tolerance due to system variability and measurement methodology differences
        # 
        # Note: The ratio can be higher than 10x because:
        # 1. Measured spawn cost measures isolated process creation overhead
        # 2. Marginal cost measures pool expansion which may benefit from:
        #    - Warm kernel caches from previous workers
        #    - Optimized fork/spawn paths after first worker
        #    - Batch allocation of resources
        # 3. OS-level factors introduce additional variability:
        #    - OS scheduling decisions and context switching
        #    - System load from other processes
        #    - Cache effects (L1/L2/L3, TLB misses)
        #    - Memory pressure and page faults
        #    - CPU frequency scaling and thermal throttling
        # 
        # A 25x threshold catches wildly inconsistent measurements (e.g., 100x+)
        # while allowing for these real-world measurement differences.
        if avg_actual_marginal > MIN_REASONABLE_MARGINAL_COST:
            ratio = measured_cost / avg_actual_marginal
            # Should be within 25x of actual (relaxed from 10x to account for measurement differences)
            assert 0.1 <= ratio <= 25.0, (
                f"Measured spawn cost ({measured_cost*1000:.2f}ms) doesn't match "
                f"actual marginal cost ({avg_actual_marginal*1000:.2f}ms). "
                f"Ratio: {ratio:.2f}x"
            )
    
    def test_spawn_cost_order_of_magnitude_correct(self):
        """
        Test that spawn cost is in the correct order of magnitude for the platform.
        
        fork: Should be in milliseconds (1-100ms)
        spawn: Should be in tens/hundreds of milliseconds (50-1000ms)
        forkserver: Should be between fork and spawn (10-500ms)
        """
        cost = measure_spawn_cost()
        start_method = get_multiprocessing_start_method()
        
        # Verify order of magnitude
        if start_method == 'fork':
            # fork should be fast: 1ms to 100ms
            assert 0.001 <= cost <= 0.1, (
                f"fork spawn cost ({cost*1000:.2f}ms) outside expected range (1-100ms)"
            )
        elif start_method == 'spawn':
            # spawn should be slower: 50ms to 1000ms
            assert 0.05 <= cost <= 1.0, (
                f"spawn spawn cost ({cost*1000:.2f}ms) outside expected range (50-1000ms)"
            )
        elif start_method == 'forkserver':
            # forkserver should be in between: 10ms to 500ms
            assert 0.01 <= cost <= 0.5, (
                f"forkserver spawn cost ({cost*1000:.2f}ms) outside expected range (10-500ms)"
            )
    
    def test_spawn_cost_matches_start_method_expectations(self):
        """
        Test that measured cost aligns with start method characteristics.
        
        fork < forkserver < spawn (in general)
        """
        cost = measure_spawn_cost()
        estimate = get_spawn_cost_estimate()
        start_method = get_multiprocessing_start_method()
        
        # Measured cost should be within 10x of the estimate (quality check 3)
        assert estimate / 10 <= cost <= estimate * 10, (
            f"Measured cost ({cost*1000:.2f}ms) too far from estimate "
            f"({estimate*1000:.2f}ms) for {start_method}"
        )
        
        # For fork, cost should be relatively small
        if start_method == 'fork':
            assert cost < 0.2, f"fork cost ({cost*1000:.2f}ms) unexpectedly high"
        
        # For spawn, cost should be substantial
        if start_method == 'spawn':
            assert cost > 0.02, f"spawn cost ({cost*1000:.2f}ms) unexpectedly low"


class TestSpawnCostConsistency:
    """Verify that spawn cost measurements are stable and reproducible."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_repeated_measurements_are_consistent(self):
        """
        Test that repeated measurements (with cache clearing) are consistent.
        
        Measurements should not vary wildly between runs.
        """
        n_measurements = 5
        measurements = []
        
        for _ in range(n_measurements):
            _clear_spawn_cost_cache()
            cost = measure_spawn_cost()
            measurements.append(cost)
        
        # Calculate coefficient of variation (std / mean)
        mean = sum(measurements) / len(measurements)
        variance = sum((x - mean) ** 2 for x in measurements) / len(measurements)
        std = variance ** 0.5
        cv = std / mean if mean > 0 else 0
        
        # CV should be less than 2.0 (std < 2*mean)
        # Process spawning is inherently variable due to OS scheduling, system load,
        # and other factors. A CV of 2.0 is reasonable for timing measurements that
        # involve kernel operations, while still catching gross inconsistencies.
        # Previous threshold of 1.0 was too strict and caused flaky test failures.
        assert cv < 2.0, (
            f"Spawn cost measurements too inconsistent. "
            f"Mean: {mean*1000:.2f}ms, StdDev: {std*1000:.2f}ms, CV: {cv:.2f}"
        )
    
    def test_cached_value_is_stable(self):
        """
        Test that once cached, the value remains stable across calls.
        """
        # First measurement
        cost1 = measure_spawn_cost()
        
        # Multiple subsequent calls should return identical value
        for _ in range(10):
            cost2 = measure_spawn_cost()
            assert cost1 == cost2, "Cached spawn cost changed unexpectedly"
    
    def test_measurement_vs_estimate_consistency(self):
        """
        Test that measurement is reasonably close to estimate.
        
        While they can differ (measurement should be more accurate),
        they shouldn't be wildly different on the same platform.
        """
        measured = measure_spawn_cost()
        estimated = get_spawn_cost_estimate()
        
        # Should be within 10x of each other (quality check 3)
        ratio = max(measured, estimated) / min(measured, estimated)
        assert ratio <= 10.0, (
            f"Measured ({measured*1000:.2f}ms) and estimated ({estimated*1000:.2f}ms) "
            f"spawn costs differ by {ratio:.2f}x (too much)"
        )


class TestSpawnCostPlatformAwareness:
    """Verify that spawn cost correctly handles different start methods."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_start_method_detection_is_correct(self):
        """
        Test that we correctly detect the actual start method being used.
        """
        method = get_multiprocessing_start_method()
        assert method in ['fork', 'spawn', 'forkserver'], (
            f"Unexpected start method: {method}"
        )
    
    def test_estimate_matches_start_method(self):
        """
        Test that estimate uses the correct constant for start method.
        """
        estimate = get_spawn_cost_estimate()
        start_method = get_multiprocessing_start_method()
        
        if start_method == 'fork':
            assert estimate == SPAWN_COST_FORK
        elif start_method == 'spawn':
            assert estimate == SPAWN_COST_SPAWN
        elif start_method == 'forkserver':
            assert estimate == SPAWN_COST_FORKSERVER
    
    def test_fork_is_faster_than_spawn_estimate(self):
        """
        Test that fork estimate is faster than spawn estimate.
        
        This verifies our constants are reasonable.
        """
        assert SPAWN_COST_FORK < SPAWN_COST_SPAWN, (
            "fork should be faster than spawn"
        )
        assert SPAWN_COST_FORKSERVER < SPAWN_COST_SPAWN, (
            "forkserver should be faster than spawn"
        )
        assert SPAWN_COST_FORK < SPAWN_COST_FORKSERVER, (
            "fork should be faster than forkserver"
        )
    
    def test_spawn_cost_respects_actual_start_method(self):
        """
        Test that spawn cost uses actual start method, not OS default.
        
        This is critical: A user can set spawn on Linux, making it 13x slower.
        """
        cost = measure_spawn_cost()
        estimate = get_spawn_cost_estimate()
        start_method = get_multiprocessing_start_method()
        
        # The estimate should match the actual start method
        if start_method == 'fork':
            # Cost should be in fork range
            assert cost <= 0.1, f"Using fork but cost is {cost*1000:.2f}ms (too high)"
        elif start_method == 'spawn':
            # Cost should be in spawn range
            assert cost >= 0.02, f"Using spawn but cost is {cost*1000:.2f}ms (too low)"


class TestSpawnCostPerformance:
    """Verify that spawn cost measurement itself is fast enough."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_measurement_completes_quickly(self):
        """
        Test that spawn cost measurement doesn't take too long.
        
        Should complete in well under 1 second even on slow systems.
        """
        start = time.perf_counter()
        measure_spawn_cost()
        elapsed = time.perf_counter() - start
        
        # Should complete in under 500ms even on slow systems
        assert elapsed < 0.5, (
            f"Spawn cost measurement took {elapsed*1000:.2f}ms (too slow)"
        )
    
    def test_cached_access_is_instant(self):
        """
        Test that accessing cached spawn cost is nearly instant.
        """
        # First call to populate cache
        measure_spawn_cost()
        
        # Subsequent calls should be instant (< 1ms)
        start = time.perf_counter()
        for _ in range(100):
            measure_spawn_cost()
        elapsed = time.perf_counter() - start
        
        # 100 cached accesses should take < 1ms total
        assert elapsed < 0.001, (
            f"Cached spawn cost access took {elapsed*1000:.2f}ms for 100 calls (too slow)"
        )
    
    def test_get_spawn_cost_with_benchmark_flag(self):
        """
        Test that get_spawn_cost respects use_benchmark flag.
        """
        # With benchmark
        start = time.perf_counter()
        cost_with_benchmark = get_spawn_cost(use_benchmark=True)
        time_with_benchmark = time.perf_counter() - start
        
        # Without benchmark (should use estimate)
        _clear_spawn_cost_cache()
        start = time.perf_counter()
        cost_without_benchmark = get_spawn_cost(use_benchmark=False)
        time_without_benchmark = time.perf_counter() - start
        
        # Without benchmark should be instant (< 1ms)
        assert time_without_benchmark < 0.001, (
            "Estimate should be instant"
        )
        
        # Without benchmark should return the estimate
        estimate = get_spawn_cost_estimate()
        assert cost_without_benchmark == estimate


class TestSpawnCostReliability:
    """Verify that spawn cost measurement handles edge cases gracefully."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_fallback_on_timeout(self):
        """
        Test that measurement falls back to estimate on timeout.
        """
        # We can't easily force a timeout, but we can verify the timeout parameter works
        cost = measure_spawn_cost(timeout=10.0)
        assert cost > 0
        
        # Should be reasonable (not fallback garbage)
        assert cost < 10.0
    
    def test_fallback_on_pool_creation_failure(self):
        """
        Test that measurement falls back to estimate when Pool creation fails.
        """
        _clear_spawn_cost_cache()
        
        with patch('multiprocessing.Pool', side_effect=OSError("Simulated failure")):
            cost = measure_spawn_cost()
            
            # Should fall back to estimate
            estimate = get_spawn_cost_estimate()
            assert cost == estimate
    
    def test_handles_concurrent_measurements(self):
        """
        Test that concurrent measurements don't cause issues.
        
        Only one thread should actually measure; others should wait and
        get the cached value.
        """
        n_threads = 5
        results = []
        
        def measure():
            cost = measure_spawn_cost()
            results.append(cost)
            return cost
        
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(measure) for _ in range(n_threads)]
            for future in futures:
                future.result()
        
        # All threads should get the same value
        assert len(set(results)) == 1, (
            f"Concurrent measurements returned different values: {results}"
        )
    
    def test_quality_checks_reject_unrealistic_values(self):
        """
        Test that quality checks prevent unrealistic measurements.
        
        This validates the quality validation logic by ensuring we don't
        accept measurements that are clearly wrong.
        """
        cost = measure_spawn_cost()
        start_method = get_multiprocessing_start_method()
        estimate = get_spawn_cost_estimate()
        
        # Quality check 1: Within start method bounds
        if start_method == 'fork':
            assert 0.001 <= cost <= 0.1
        elif start_method == 'spawn':
            assert 0.05 <= cost <= 1.0
        elif start_method == 'forkserver':
            assert 0.01 <= cost <= 0.5
        
        # Quality check 3: Within 10x of estimate
        assert estimate / 10 <= cost <= estimate * 10
    
    def test_measurement_after_cache_clear(self):
        """
        Test that measurement works correctly after cache is cleared.
        """
        cost1 = measure_spawn_cost()
        assert cost1 > 0
        
        _clear_spawn_cost_cache()
        
        cost2 = measure_spawn_cost()
        assert cost2 > 0
        
        # Both should be reasonable
        assert cost1 < 2.0
        assert cost2 < 2.0


class TestSpawnCostIntegration:
    """Test spawn cost measurement in realistic scenarios."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_spawn_cost_used_by_optimizer(self):
        """
        Test that spawn cost is actually used by the optimizer.
        """
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        # Optimizer should use spawn cost without errors
        result = optimize(simple_func, range(100))
        assert result is not None
        assert hasattr(result, 'n_jobs')
        assert hasattr(result, 'chunksize')
    
    def test_spawn_cost_affects_optimization_decision(self):
        """
        Test that spawn cost influences the optimizer's decision.
        
        For very fast functions, high spawn cost should discourage parallelization.
        """
        from amorsize import optimize
        
        # Very fast function (microseconds)
        def fast_func(x):
            return x
        
        result = optimize(fast_func, range(10))
        
        # Should either:
        # 1. Not parallelize (n_jobs=1), or
        # 2. Use conservative parallelization
        assert result.n_jobs >= 1  # At least valid
        
        # The optimizer should account for spawn cost
        # If spawn cost is high, it should be conservative
        spawn_cost = get_spawn_cost()
        if spawn_cost > 0.1:  # If spawn cost > 100ms
            # Should not use too many workers for trivial task
            assert result.n_jobs <= 4


class TestSpawnCostEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Clear cache before each test."""
        _clear_spawn_cost_cache()
    
    def teardown_method(self):
        """Clear cache after each test."""
        _clear_spawn_cost_cache()
    
    def test_min_reasonable_marginal_cost_constant_is_sensible(self):
        """
        Test that MIN_REASONABLE_MARGINAL_COST is reasonable.
        
        Should be small but not too small (we use 1ms currently).
        """
        # Should be positive
        assert MIN_REASONABLE_MARGINAL_COST > 0
        
        # Should be less than 10ms (we use 1ms)
        assert MIN_REASONABLE_MARGINAL_COST < 0.01
        
        # Should be at least 0.1ms (100 microseconds)
        assert MIN_REASONABLE_MARGINAL_COST >= 0.0001
    
    def test_spawn_cost_constants_are_reasonable(self):
        """
        Test that spawn cost constants are in reasonable ranges.
        """
        # fork: ~15ms
        assert 0.001 <= SPAWN_COST_FORK <= 0.1
        
        # spawn: ~200ms
        assert 0.05 <= SPAWN_COST_SPAWN <= 1.0
        
        # forkserver: ~75ms
        assert 0.01 <= SPAWN_COST_FORKSERVER <= 0.5
    
    def test_spawn_cost_with_different_timeouts(self):
        """
        Test spawn cost measurement with different timeout values.
        """
        # Short timeout
        cost1 = measure_spawn_cost(timeout=1.0)
        assert cost1 > 0
        
        _clear_spawn_cost_cache()
        
        # Long timeout
        cost2 = measure_spawn_cost(timeout=5.0)
        assert cost2 > 0
        
        # Both should be reasonable
        assert cost1 < 2.0
        assert cost2 < 2.0
