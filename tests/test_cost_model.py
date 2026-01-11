"""
Tests for advanced cost modeling module.
"""

import pytest
from amorsize.cost_model import (
    CacheInfo,
    NUMAInfo,
    MemoryBandwidthInfo,
    SystemTopology,
    detect_cache_info,
    detect_numa_info,
    estimate_memory_bandwidth,
    detect_system_topology,
    estimate_cache_coherency_overhead,
    estimate_memory_bandwidth_impact,
    estimate_false_sharing_overhead,
    calculate_advanced_amdahl_speedup,
)


class TestCacheDetection:
    """Tests for cache detection functionality."""
    
    def test_detect_cache_info_returns_valid_info(self):
        """Test that cache detection returns valid CacheInfo."""
        cache_info = detect_cache_info()
        
        assert isinstance(cache_info, CacheInfo)
        assert cache_info.l1_size > 0
        assert cache_info.l2_size >= 0  # L2 might not be detected
        assert cache_info.l3_size >= 0  # L3 might not be detected
        assert cache_info.cache_line_size > 0
        assert cache_info.cache_line_size in [32, 64, 128]  # Common cache line sizes
    
    def test_cache_hierarchy_makes_sense(self):
        """Test that cache sizes follow expected hierarchy (L1 < L2 < L3)."""
        cache_info = detect_cache_info()
        
        # L1 should be smallest (if all detected)
        if cache_info.l2_size > 0:
            assert cache_info.l1_size <= cache_info.l2_size
        
        if cache_info.l3_size > 0 and cache_info.l2_size > 0:
            assert cache_info.l2_size <= cache_info.l3_size
    
    def test_cache_sizes_in_reasonable_range(self):
        """Test that detected cache sizes are in reasonable ranges."""
        cache_info = detect_cache_info()
        
        # L1: typically 16KB-64KB
        assert 8 * 1024 <= cache_info.l1_size <= 128 * 1024
        
        # L2: typically 128KB-4MB (if detected)
        if cache_info.l2_size > 0:
            assert 64 * 1024 <= cache_info.l2_size <= 8 * 1024 * 1024
        
        # L3: typically 2MB-64MB (if detected)
        if cache_info.l3_size > 0:
            assert 1 * 1024 * 1024 <= cache_info.l3_size <= 128 * 1024 * 1024


class TestNUMADetection:
    """Tests for NUMA topology detection."""
    
    def test_detect_numa_info_returns_valid_info(self):
        """Test that NUMA detection returns valid NUMAInfo."""
        numa_info = detect_numa_info(physical_cores=4)
        
        assert isinstance(numa_info, NUMAInfo)
        assert numa_info.numa_nodes > 0
        assert numa_info.cores_per_node > 0
        assert isinstance(numa_info.has_numa, bool)
    
    def test_numa_nodes_and_cores_multiply_correctly(self):
        """Test that numa_nodes × cores_per_node ≈ physical_cores."""
        for physical_cores in [2, 4, 8, 16, 32]:
            numa_info = detect_numa_info(physical_cores=physical_cores)
            
            # Total cores should approximately match
            total_cores = numa_info.numa_nodes * numa_info.cores_per_node
            # Allow for some rounding (division)
            assert abs(total_cores - physical_cores) <= numa_info.numa_nodes
    
    def test_single_numa_node_has_numa_false(self):
        """Test that single NUMA node sets has_numa=False."""
        numa_info = detect_numa_info(physical_cores=4)
        
        if numa_info.numa_nodes == 1:
            assert numa_info.has_numa is False
    
    def test_multiple_numa_nodes_has_numa_true(self):
        """Test that multiple NUMA nodes sets has_numa=True."""
        # This test might not trigger on single-socket systems
        # but validates the logic when NUMA is detected
        numa_info = detect_numa_info(physical_cores=32)
        
        if numa_info.numa_nodes > 1:
            assert numa_info.has_numa is True


class TestMemoryBandwidthEstimation:
    """Tests for memory bandwidth estimation."""
    
    def test_estimate_memory_bandwidth_returns_valid_info(self):
        """Test that memory bandwidth estimation returns valid info."""
        bandwidth_info = estimate_memory_bandwidth()
        
        assert isinstance(bandwidth_info, MemoryBandwidthInfo)
        assert bandwidth_info.bandwidth_gb_per_sec > 0
        assert isinstance(bandwidth_info.is_estimated, bool)
        assert bandwidth_info.is_estimated is True  # Always estimated currently
    
    def test_memory_bandwidth_in_reasonable_range(self):
        """Test that estimated bandwidth is in reasonable range."""
        bandwidth_info = estimate_memory_bandwidth()
        
        # Modern systems: 20-200 GB/s typical
        # Consumer DDR4: 20-50 GB/s
        # Server DDR4/DDR5: 50-200 GB/s
        assert 10.0 <= bandwidth_info.bandwidth_gb_per_sec <= 500.0


class TestSystemTopologyDetection:
    """Tests for complete system topology detection."""
    
    def test_detect_system_topology_returns_complete_info(self):
        """Test that system topology detection returns all components."""
        topology = detect_system_topology(physical_cores=4)
        
        assert isinstance(topology, SystemTopology)
        assert isinstance(topology.cache_info, CacheInfo)
        assert isinstance(topology.numa_info, NUMAInfo)
        assert isinstance(topology.memory_bandwidth, MemoryBandwidthInfo)
        assert topology.physical_cores == 4
    
    def test_topology_components_are_consistent(self):
        """Test that topology components are internally consistent."""
        physical_cores = 8
        topology = detect_system_topology(physical_cores=physical_cores)
        
        # Physical cores should match
        assert topology.physical_cores == physical_cores
        
        # NUMA info should be consistent with physical cores
        total_cores = topology.numa_info.numa_nodes * topology.numa_info.cores_per_node
        assert abs(total_cores - physical_cores) <= topology.numa_info.numa_nodes


class TestCacheCoherencyOverhead:
    """Tests for cache coherency overhead estimation."""
    
    def test_single_worker_has_no_overhead(self):
        """Test that single worker has no cache coherency overhead."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        numa_info = NUMAInfo(numa_nodes=1, cores_per_node=4, has_numa=False)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=1,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        assert overhead == 1.0
    
    def test_overhead_increases_with_workers(self):
        """Test that overhead increases with more workers."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        numa_info = NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False)
        
        overhead_2 = estimate_cache_coherency_overhead(
            n_jobs=2,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        overhead_8 = estimate_cache_coherency_overhead(
            n_jobs=8,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        assert overhead_2 > 1.0
        assert overhead_8 > overhead_2
    
    def test_cache_pressure_increases_overhead(self):
        """Test that exceeding L3 cache increases overhead."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=1*1024*1024, cache_line_size=64)
        numa_info = NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False)
        
        # Small working set (fits in cache)
        overhead_small = estimate_cache_coherency_overhead(
            n_jobs=4,
            data_size_per_item=1024,  # 4KB total
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        # Large working set (exceeds cache)
        overhead_large = estimate_cache_coherency_overhead(
            n_jobs=4,
            data_size_per_item=1024*1024,  # 4MB total > 1MB L3
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        assert overhead_large > overhead_small
    
    def test_numa_increases_overhead(self):
        """Test that NUMA topology increases overhead."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        
        # Single NUMA node
        numa_single = NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False)
        overhead_single = estimate_cache_coherency_overhead(
            n_jobs=8,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_single
        )
        
        # Multiple NUMA nodes (workers span nodes)
        numa_multi = NUMAInfo(numa_nodes=2, cores_per_node=4, has_numa=True)
        overhead_multi = estimate_cache_coherency_overhead(
            n_jobs=8,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_multi
        )
        
        assert overhead_multi > overhead_single


class TestMemoryBandwidthImpact:
    """Tests for memory bandwidth saturation impact."""
    
    def test_single_worker_no_bandwidth_impact(self):
        """Test that single worker has no bandwidth impact."""
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True)
        
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=1,
            data_size_per_item=1024,
            items_per_second_per_core=100.0,
            memory_bandwidth=bandwidth_info
        )
        
        assert slowdown == 1.0
    
    def test_low_bandwidth_demand_no_impact(self):
        """Test that low bandwidth demand has no impact."""
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True)
        
        # Low demand: 4 cores × 1KB × 100 items/s = 400KB/s << 40GB/s
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=4,
            data_size_per_item=1024,
            items_per_second_per_core=100.0,
            memory_bandwidth=bandwidth_info
        )
        
        assert slowdown == 1.0
    
    def test_high_bandwidth_demand_causes_slowdown(self):
        """Test that high bandwidth demand causes slowdown."""
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=1.0, is_estimated=True)  # Low bandwidth
        
        # High demand: 8 cores × 1MB × 1000 items/s = 8GB/s > 1GB/s
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=8,
            data_size_per_item=1024*1024,
            items_per_second_per_core=1000.0,
            memory_bandwidth=bandwidth_info
        )
        
        assert slowdown < 1.0  # Should have slowdown
    
    def test_slowdown_capped_at_50_percent(self):
        """Test that slowdown is capped at 50%."""
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=0.1, is_estimated=True)  # Very low
        
        # Extreme demand that would cause >50% slowdown
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=16,
            data_size_per_item=10*1024*1024,
            items_per_second_per_core=1000.0,
            memory_bandwidth=bandwidth_info
        )
        
        assert slowdown >= 0.5  # Should be capped


class TestFalseSharingOverhead:
    """Tests for false sharing overhead estimation."""
    
    def test_single_worker_no_false_sharing(self):
        """Test that single worker has no false sharing."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=1,
            return_size=32,
            cache_line_size=64
        )
        
        assert overhead == 1.0
    
    def test_large_objects_no_false_sharing(self):
        """Test that large objects (>= cache line) have no false sharing."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=8,
            return_size=128,  # Larger than cache line
            cache_line_size=64
        )
        
        assert overhead == 1.0
    
    def test_small_objects_have_false_sharing(self):
        """Test that small objects (< cache line) can have false sharing."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=8,
            return_size=16,  # Much smaller than cache line
            cache_line_size=64
        )
        
        assert overhead > 1.0
    
    def test_overhead_increases_with_workers(self):
        """Test that false sharing overhead increases with workers."""
        overhead_2 = estimate_false_sharing_overhead(
            n_jobs=2,
            return_size=16,
            cache_line_size=64
        )
        
        overhead_8 = estimate_false_sharing_overhead(
            n_jobs=8,
            return_size=16,
            cache_line_size=64
        )
        
        assert overhead_8 > overhead_2


class TestAdvancedAmdahlSpeedup:
    """Tests for advanced Amdahl's Law speedup calculation."""
    
    def test_single_worker_speedup_is_one(self):
        """Test that single worker has speedup close to 1.0."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=1,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        
        # Single worker has overhead (spawn, IPC) so speedup can be < 1.0
        # This is realistic - serial execution with multiprocessing overhead
        # can be slower than pure serial execution
        assert 0.5 <= speedup <= 1.1
    
    def test_speedup_increases_with_workers(self):
        """Test that speedup generally increases with more workers."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=8
        )
        
        speedup_2, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.05,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=2,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        
        speedup_4, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.05,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=4,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        
        assert speedup_4 > speedup_2
        assert speedup_2 > 1.0
    
    def test_speedup_capped_at_n_jobs(self):
        """Test that speedup cannot exceed n_jobs."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=8
        )
        
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=100.0,  # Long compute time
            pickle_overhead_per_item=0.00001,  # Tiny overhead
            spawn_cost_per_worker=0.001,  # Tiny spawn cost
            chunking_overhead_per_chunk=0.00001,  # Tiny chunking
            n_jobs=4,
            chunksize=1000,
            total_items=10000,
            data_pickle_overhead_per_item=0.00001,
            system_topology=topology,
            data_size_per_item=100,
            return_size_per_item=100
        )
        
        assert speedup <= 4.0
    
    def test_overhead_breakdown_included(self):
        """Test that overhead breakdown is returned."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        speedup, breakdown = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=4,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        
        # Verify all expected keys are present
        assert 'spawn_overhead' in breakdown
        assert 'parallel_compute' in breakdown
        assert 'data_ipc_overhead' in breakdown
        assert 'result_ipc_overhead' in breakdown
        assert 'chunking_overhead' in breakdown
        assert 'cache_coherency_factor' in breakdown
        assert 'bandwidth_slowdown' in breakdown
        assert 'false_sharing_factor' in breakdown
        assert 'basic_parallel_compute' in breakdown
        
        # Verify values are reasonable
        assert breakdown['spawn_overhead'] > 0
        assert breakdown['parallel_compute'] > 0
        assert breakdown['cache_coherency_factor'] >= 1.0
        assert 0.0 < breakdown['bandwidth_slowdown'] <= 1.0
        assert breakdown['false_sharing_factor'] >= 1.0
    
    def test_advanced_model_vs_basic_comparison(self):
        """Test that advanced model differs from basic model for some cases."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 1*1024*1024, 64),  # Small L3
            numa_info=NUMAInfo(2, 4, True),  # NUMA system
            memory_bandwidth=MemoryBandwidthInfo(20.0, True),  # Moderate bandwidth
            physical_cores=8
        )
        
        # Case with high cache pressure, NUMA, and small objects
        speedup_advanced, breakdown = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.05,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=8,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=100*1024,  # Large data (cache pressure)
            return_size_per_item=16  # Small return (false sharing)
        )
        
        # With NUMA, cache pressure, and false sharing, advanced factors should apply
        assert breakdown['cache_coherency_factor'] > 1.0
        assert breakdown['false_sharing_factor'] > 1.0
        
        # Advanced compute time should be higher than basic
        assert breakdown['parallel_compute'] > breakdown['basic_parallel_compute']


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_zero_workers(self):
        """Test that zero workers returns speedup of 1.0."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=0,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        
        assert speedup == 1.0
    
    def test_zero_compute_time(self):
        """Test that zero compute time returns speedup of 1.0."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=0.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=4,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        
        assert speedup == 1.0
    
    def test_zero_items(self):
        """Test handling of zero items."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        # Should not crash with zero items
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=4,
            chunksize=100,
            total_items=0,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        
        # Should return some value (doesn't matter much with 0 items)
        assert speedup >= 0.0
