"""
Tests for the improved Amdahl's Law speedup calculation.
"""

import pytest
from amorsize.optimizer import calculate_amdahl_speedup


def test_calculate_amdahl_speedup_basic():
    """Test basic Amdahl's Law calculation."""
    # 10 seconds of compute time, 2 workers
    speedup = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.001,
        spawn_cost_per_worker=0.01,
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Should get reasonable speedup
    assert speedup > 1.0
    assert speedup <= 2.0  # Can't exceed number of workers


def test_calculate_amdahl_speedup_high_overhead():
    """Test that high overhead reduces speedup."""
    # Very high spawn cost dominates
    speedup = calculate_amdahl_speedup(
        total_compute_time=1.0,
        pickle_overhead_per_item=0.0,
        spawn_cost_per_worker=0.5,  # High spawn cost
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Spawn cost is 1.0s (0.5 * 2), compute is 0.5s (1.0 / 2)
    # Total parallel time = 1.5s, serial time = 1.0s
    # Speedup should be < 1.0 (slower!)
    assert speedup < 1.0


def test_calculate_amdahl_speedup_many_workers():
    """Test that speedup scales with workers."""
    speedup_2 = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,
        spawn_cost_per_worker=0.01,
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    speedup_4 = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,
        spawn_cost_per_worker=0.01,
        n_jobs=4,
        chunksize=10,
        total_items=100
    )
    
    # More workers should give better speedup (up to a point)
    assert speedup_4 > speedup_2


def test_calculate_amdahl_speedup_pickle_overhead():
    """Test that pickle overhead is properly accounted for."""
    # High pickle overhead per item
    speedup_high_pickle = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.01,  # 10ms per item
        spawn_cost_per_worker=0.01,
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Low pickle overhead per item
    speedup_low_pickle = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,  # 0.1ms per item
        spawn_cost_per_worker=0.01,
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Lower pickle overhead should give better speedup
    assert speedup_low_pickle > speedup_high_pickle


def test_calculate_amdahl_speedup_zero_compute_time():
    """Test edge case with zero compute time."""
    speedup = calculate_amdahl_speedup(
        total_compute_time=0.0,
        pickle_overhead_per_item=0.001,
        spawn_cost_per_worker=0.01,
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Should return 1.0 (no parallelization benefit)
    assert speedup == 1.0


def test_calculate_amdahl_speedup_zero_workers():
    """Test edge case with zero workers."""
    speedup = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.001,
        spawn_cost_per_worker=0.01,
        n_jobs=0,
        chunksize=10,
        total_items=100
    )
    
    # Should return 1.0 (no workers = no parallelization)
    assert speedup == 1.0


def test_calculate_amdahl_speedup_realistic_scenario():
    """Test with realistic values from a typical workload."""
    # Simulate: 100 items, 0.1s each = 10s total
    # 4 workers, 10ms spawn cost each, 0.1ms pickle overhead per item
    speedup = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,
        spawn_cost_per_worker=0.01,
        n_jobs=4,
        chunksize=25,
        total_items=100
    )
    
    # Serial: 10s
    # Parallel: 0.04s spawn + 2.5s compute + 0.01s pickle + ~0.002s chunking
    # Expected speedup: ~3.9x
    assert 3.5 < speedup <= 4.0


def test_calculate_amdahl_speedup_cannot_exceed_n_jobs():
    """Test that speedup never exceeds theoretical maximum."""
    # Even with zero overhead, speedup shouldn't exceed n_jobs
    speedup = calculate_amdahl_speedup(
        total_compute_time=100.0,
        pickle_overhead_per_item=0.0,
        spawn_cost_per_worker=0.0,
        n_jobs=8,
        chunksize=100,
        total_items=1000
    )
    
    # Should be capped at n_jobs
    assert speedup <= 8.0
