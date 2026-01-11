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
        chunking_overhead_per_chunk=0.0005,
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
        chunking_overhead_per_chunk=0.0005,
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
        chunking_overhead_per_chunk=0.0005,
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    speedup_4 = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
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
        chunking_overhead_per_chunk=0.0005,
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Low pickle overhead per item
    speedup_low_pickle = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,  # 0.1ms per item
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
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
        chunking_overhead_per_chunk=0.0005,
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
        chunking_overhead_per_chunk=0.0005,
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
        chunking_overhead_per_chunk=0.0005,
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
        chunking_overhead_per_chunk=0.0,
        n_jobs=8,
        chunksize=100,
        total_items=1000
    )
    
    # Should be capped at n_jobs
    assert speedup <= 8.0


def test_calculate_amdahl_speedup_chunking_overhead():
    """Test that chunking overhead affects speedup properly."""
    # High chunking overhead
    speedup_high_chunking = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.01,  # 10ms per chunk (high)
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Low chunking overhead
    speedup_low_chunking = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0001,
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0001,  # 0.1ms per chunk (low)
        n_jobs=2,
        chunksize=10,
        total_items=100
    )
    
    # Lower chunking overhead should give better speedup
    assert speedup_low_chunking > speedup_high_chunking


def test_calculate_amdahl_speedup_ipc_overlap():
    """Test that IPC overlap factor improves speedup estimates."""
    # With the overlap factor of 0.5, IPC overhead should be halved
    # This test verifies the overlap provides better speedup than pure serial IPC
    
    # Scenario: High IPC overhead relative to compute time
    speedup = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.005,  # 5ms per item (significant overhead)
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
        n_jobs=4,
        chunksize=25,
        total_items=100,
        data_pickle_overhead_per_item=0.003  # 3ms per item for data
    )
    
    # With overlap factor:
    # - Serial time: 10.0s
    # - Spawn: 0.04s (4 * 0.01)
    # - Compute: 2.5s (10.0 / 4)
    # - Result IPC: 0.25s (0.005 * 100 * 0.5)
    # - Data IPC: 0.15s (0.003 * 100 * 0.5)
    # - Chunking: 0.002s (0.0005 * 4)
    # - Total parallel: ~2.94s
    # - Speedup: 10.0 / 2.94 ≈ 3.4x
    
    assert speedup > 3.0, f"Expected speedup > 3.0 with overlap, got {speedup}"
    assert speedup <= 4.0, f"Speedup cannot exceed n_jobs (4), got {speedup}"
    
    # Without overlap (hypothetical), parallel time would be:
    # 0.04 + 2.5 + 0.5 + 0.3 + 0.002 = 3.34s → speedup ≈ 3.0x
    # With 0.5 overlap: 0.04 + 2.5 + 0.25 + 0.15 + 0.002 = 2.94s → speedup ≈ 3.4x


def test_calculate_amdahl_speedup_overlap_factor_value():
    """Test that overlap factor is applied correctly to IPC overhead."""
    # Create two scenarios: one with no IPC, one with significant IPC
    # The difference should reflect the overlap factor
    
    speedup_no_ipc = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0,
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
        n_jobs=2,
        chunksize=50,
        total_items=100,
        data_pickle_overhead_per_item=0.0
    )
    
    speedup_with_ipc = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.01,  # 1s total without overlap, 0.5s with
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
        n_jobs=2,
        chunksize=50,
        total_items=100,
        data_pickle_overhead_per_item=0.01  # 1s total without overlap, 0.5s with
    )
    
    # No IPC: parallel_time = 0.02 + 5.0 + 0.001 = 5.021s, speedup = 1.99x
    # With IPC: parallel_time = 0.02 + 5.0 + 0.5 + 0.5 + 0.001 = 6.021s, speedup = 1.66x
    # The IPC overhead (with 0.5 factor) should reduce speedup
    assert speedup_with_ipc < speedup_no_ipc
    assert speedup_with_ipc > 1.5  # Still beneficial despite overhead


def test_calculate_amdahl_speedup_data_and_result_ipc():
    """Test that both data and result IPC overhead are accounted for with overlap."""
    # Test with only data IPC
    speedup_data_only = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.0,
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
        n_jobs=4,
        chunksize=25,
        total_items=100,
        data_pickle_overhead_per_item=0.005
    )
    
    # Test with only result IPC
    speedup_result_only = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.005,
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
        n_jobs=4,
        chunksize=25,
        total_items=100,
        data_pickle_overhead_per_item=0.0
    )
    
    # Test with both data and result IPC
    speedup_both = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.005,
        spawn_cost_per_worker=0.01,
        chunking_overhead_per_chunk=0.0005,
        n_jobs=4,
        chunksize=25,
        total_items=100,
        data_pickle_overhead_per_item=0.005
    )
    
    # With equal data and result overhead, both should give similar speedup
    assert abs(speedup_data_only - speedup_result_only) < 0.01
    
    # Combined overhead should give lower speedup than individual
    assert speedup_both < speedup_data_only
    assert speedup_both < speedup_result_only
