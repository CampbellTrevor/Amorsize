"""
Comprehensive edge case tests for the cost_model module.

This test suite covers boundary conditions, parameter validation, error handling,
invariants, and integration scenarios to strengthen test quality before mutation
testing baseline.

Follows the pattern from Iterations 184-186 (optimizer, sampling, system_info).
"""

import os
import platform
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from amorsize.cost_model import (
    CacheInfo,
    NUMAInfo,
    MemoryBandwidthInfo,
    SystemTopology,
    _parse_size_string,
    _parse_lscpu_cache,
    _parse_sysfs_cache,
    detect_cache_info,
    detect_numa_info,
    estimate_memory_bandwidth,
    detect_system_topology,
    estimate_cache_coherency_overhead,
    estimate_memory_bandwidth_impact,
    estimate_false_sharing_overhead,
    calculate_advanced_amdahl_speedup,
)


# =============================================================================
# 1. BOUNDARY CONDITIONS
# =============================================================================

class TestParseSizeStringBoundaries:
    """Test edge cases in size string parsing."""
    
    def test_parse_size_string_empty(self):
        """Empty string should return 0."""
        assert _parse_size_string("") == 0
    
    def test_parse_size_string_whitespace_only(self):
        """Whitespace-only string should return 0."""
        assert _parse_size_string("   ") == 0
    
    def test_parse_size_string_invalid_format(self):
        """Invalid format should return 0."""
        assert _parse_size_string("invalid") == 0
        assert _parse_size_string("KB256") == 0
        assert _parse_size_string("@#$") == 0
    
    def test_parse_size_string_zero(self):
        """Zero value should be parsed correctly."""
        assert _parse_size_string("0") == 0
        assert _parse_size_string("0K") == 0
        assert _parse_size_string("0M") == 0
    
    def test_parse_size_string_no_unit(self):
        """Number without unit should be treated as bytes."""
        assert _parse_size_string("1024") == 1024
        assert _parse_size_string("512") == 512
    
    def test_parse_size_string_decimal(self):
        """Decimal values should be handled."""
        assert _parse_size_string("2.5K") == int(2.5 * 1024)
        assert _parse_size_string("1.5M") == int(1.5 * 1024 * 1024)
        assert _parse_size_string("0.5G") == int(0.5 * 1024 * 1024 * 1024)
    
    def test_parse_size_string_lowercase(self):
        """Lowercase units should work (case-insensitive)."""
        assert _parse_size_string("256k") == 256 * 1024
        assert _parse_size_string("8m") == 8 * 1024 * 1024
        assert _parse_size_string("2g") == 2 * 1024 * 1024 * 1024
    
    def test_parse_size_string_with_spaces(self):
        """Spaces in string should be handled."""
        assert _parse_size_string(" 256 K ") == 256 * 1024
        assert _parse_size_string("  8  M  ") == 8 * 1024 * 1024
    
    def test_parse_size_string_very_large(self):
        """Very large sizes should be handled."""
        assert _parse_size_string("128G") == 128 * 1024 * 1024 * 1024
        assert _parse_size_string("999M") == 999 * 1024 * 1024


class TestCacheCoherencyBoundaries:
    """Test boundary conditions for cache coherency overhead."""
    
    def test_zero_workers(self):
        """Zero workers should return 1.0 (no overhead)."""
        cache_info = CacheInfo(32*1024, 256*1024, 8*1024*1024, 64)
        numa_info = NUMAInfo(1, 4, False)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=0,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        assert overhead == 1.0
    
    def test_negative_workers(self):
        """Negative workers should be handled gracefully."""
        cache_info = CacheInfo(32*1024, 256*1024, 8*1024*1024, 64)
        numa_info = NUMAInfo(1, 4, False)
        
        # Should not crash, likely returns 1.0 for non-positive values
        overhead = estimate_cache_coherency_overhead(
            n_jobs=-1,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        assert overhead >= 1.0
    
    def test_zero_data_size(self):
        """Zero data size should be handled."""
        cache_info = CacheInfo(32*1024, 256*1024, 8*1024*1024, 64)
        numa_info = NUMAInfo(1, 4, False)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=4,
            data_size_per_item=0,
            cache_info=cache_info,
            numa_info=numa_info
        )
        assert overhead >= 1.0
    
    def test_extremely_large_data_size(self):
        """Very large data size should be capped appropriately."""
        cache_info = CacheInfo(32*1024, 256*1024, 8*1024*1024, 64)
        numa_info = NUMAInfo(1, 4, False)
        
        # Data much larger than L3 (should hit cache pressure cap)
        overhead = estimate_cache_coherency_overhead(
            n_jobs=8,
            data_size_per_item=1024*1024*1024,  # 1GB per item
            cache_info=cache_info,
            numa_info=numa_info
        )
        # Should be bounded (not infinite)
        assert 1.0 <= overhead <= 10.0
    
    def test_very_high_worker_count(self):
        """Very high worker count should be handled."""
        cache_info = CacheInfo(32*1024, 256*1024, 8*1024*1024, 64)
        numa_info = NUMAInfo(1, 128, False)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=128,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        # Should be bounded
        assert 1.0 <= overhead <= 20.0


class TestMemoryBandwidthBoundaries:
    """Test boundary conditions for memory bandwidth impact."""
    
    def test_zero_items_per_second(self):
        """Zero processing rate should have no bandwidth impact."""
        bandwidth_info = MemoryBandwidthInfo(40.0, True)
        
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=4,
            data_size_per_item=1024,
            items_per_second_per_core=0.0,
            memory_bandwidth=bandwidth_info
        )
        assert slowdown == 1.0
    
    def test_negative_items_per_second(self):
        """Negative processing rate should be handled."""
        bandwidth_info = MemoryBandwidthInfo(40.0, True)
        
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=4,
            data_size_per_item=1024,
            items_per_second_per_core=-100.0,
            memory_bandwidth=bandwidth_info
        )
        # Should be bounded between 0.5 and 1.0
        assert 0.5 <= slowdown <= 1.0
    
    def test_extremely_high_bandwidth_demand(self):
        """Extreme bandwidth demand should be capped at 0.5."""
        bandwidth_info = MemoryBandwidthInfo(0.001, True)  # Very low bandwidth
        
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=128,
            data_size_per_item=1024*1024*1024,  # 1GB
            items_per_second_per_core=10000.0,
            memory_bandwidth=bandwidth_info
        )
        # Should be capped at 0.5 (50% slowdown)
        assert slowdown == 0.5
    
    def test_zero_data_size(self):
        """Zero data size should have no bandwidth impact."""
        bandwidth_info = MemoryBandwidthInfo(40.0, True)
        
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=8,
            data_size_per_item=0,
            items_per_second_per_core=1000.0,
            memory_bandwidth=bandwidth_info
        )
        assert slowdown == 1.0


class TestFalseSharingBoundaries:
    """Test boundary conditions for false sharing overhead."""
    
    def test_zero_return_size(self):
        """Zero return size should be handled."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=4,
            return_size=0,
            cache_line_size=64
        )
        assert overhead >= 1.0
    
    def test_negative_return_size(self):
        """Negative return size should be handled."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=4,
            return_size=-1,
            cache_line_size=64
        )
        # Should not crash
        assert overhead >= 1.0
    
    def test_return_size_equals_cache_line(self):
        """Return size exactly equal to cache line."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=4,
            return_size=64,
            cache_line_size=64
        )
        # Should be at boundary, no false sharing
        assert overhead == 1.0
    
    def test_cache_line_size_zero(self):
        """Zero cache line size should not crash."""
        # This is an error condition, but should be handled gracefully
        # Function returns 1.0 (no false sharing) rather than crashing
        overhead = estimate_false_sharing_overhead(
            n_jobs=4,
            return_size=16,
            cache_line_size=0
        )
        # Should handle gracefully and return 1.0
        assert overhead == 1.0


# =============================================================================
# 2. PARAMETER VALIDATION
# =============================================================================

class TestParameterValidation:
    """Test parameter validation and handling."""
    
    def test_detect_numa_info_negative_cores(self):
        """Negative physical cores should be handled."""
        # Should not crash
        numa_info = detect_numa_info(physical_cores=-1)
        assert isinstance(numa_info, NUMAInfo)
        assert numa_info.numa_nodes > 0
    
    def test_detect_numa_info_zero_cores(self):
        """Zero physical cores should be handled."""
        numa_info = detect_numa_info(physical_cores=0)
        assert isinstance(numa_info, NUMAInfo)
        assert numa_info.numa_nodes > 0
    
    def test_detect_system_topology_extreme_cores(self):
        """Very high core count should be handled."""
        topology = detect_system_topology(physical_cores=1024)
        assert isinstance(topology, SystemTopology)
        assert topology.physical_cores == 1024
    
    def test_calculate_advanced_amdahl_negative_values(self):
        """Negative parameter values should be handled."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        # Negative compute time
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=-10.0,
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
        # Should handle gracefully
        assert speedup >= 0.0
    
    def test_calculate_advanced_amdahl_negative_chunksize(self):
        """Negative chunksize should be handled."""
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
            n_jobs=4,
            chunksize=-100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        # Should handle gracefully
        assert speedup >= 0.0


# =============================================================================
# 3. ERROR HANDLING
# =============================================================================

class TestErrorHandling:
    """Test error handling for various failure modes."""
    
    def test_parse_lscpu_cache_command_not_found(self):
        """Missing lscpu command should return None."""
        with patch('subprocess.run', side_effect=OSError("lscpu not found")):
            result = _parse_lscpu_cache()
            assert result is None
    
    def test_parse_lscpu_cache_timeout(self):
        """Timeout should be handled and return None."""
        import subprocess
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('lscpu', 1.0)):
            result = _parse_lscpu_cache()
            assert result is None
    
    def test_parse_lscpu_cache_nonzero_return(self):
        """Non-zero return code should return None."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            result = _parse_lscpu_cache()
            assert result is None
    
    def test_parse_lscpu_cache_malformed_output(self):
        """Malformed lscpu output should be handled."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "malformed\ngarbage\ndata"
        
        with patch('subprocess.run', return_value=mock_result):
            result = _parse_lscpu_cache()
            # Should return None or handle gracefully
            assert result is None or isinstance(result, CacheInfo)
    
    def test_parse_sysfs_cache_missing_directory(self):
        """Missing /sys directory should return None."""
        with patch('os.path.exists', return_value=False):
            result = _parse_sysfs_cache()
            assert result is None
    
    def test_parse_sysfs_cache_permission_error(self):
        """Permission error should be handled."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = _parse_sysfs_cache()
                assert result is None
    
    def test_estimate_memory_bandwidth_cpuinfo_error(self):
        """Error reading /proc/cpuinfo should be handled."""
        with patch('builtins.open', side_effect=IOError("File not found")):
            result = estimate_memory_bandwidth()
            # Should return fallback estimate
            assert isinstance(result, MemoryBandwidthInfo)
            assert result.bandwidth_gb_per_sec > 0


# =============================================================================
# 4. INVARIANT VERIFICATION
# =============================================================================

class TestInvariants:
    """Test that functions maintain expected invariants."""
    
    def test_cache_info_sizes_non_negative(self):
        """Cache sizes should never be negative."""
        cache_info = detect_cache_info()
        assert cache_info.l1_size >= 0
        assert cache_info.l2_size >= 0
        assert cache_info.l3_size >= 0
        assert cache_info.cache_line_size > 0
    
    def test_numa_info_positive_values(self):
        """NUMA info should have positive values."""
        for cores in [1, 2, 4, 8, 16]:
            numa_info = detect_numa_info(physical_cores=cores)
            assert numa_info.numa_nodes > 0
            assert numa_info.cores_per_node > 0
    
    def test_numa_nodes_multiply_to_cores(self):
        """NUMA nodes × cores_per_node should approximate physical_cores."""
        for physical_cores in [2, 4, 8, 16, 32, 64]:
            numa_info = detect_numa_info(physical_cores=physical_cores)
            total = numa_info.numa_nodes * numa_info.cores_per_node
            # Allow some rounding error
            assert abs(total - physical_cores) <= numa_info.numa_nodes
    
    def test_memory_bandwidth_positive(self):
        """Memory bandwidth should always be positive."""
        bandwidth_info = estimate_memory_bandwidth()
        assert bandwidth_info.bandwidth_gb_per_sec > 0
        assert isinstance(bandwidth_info.is_estimated, bool)
    
    def test_cache_coherency_overhead_at_least_one(self):
        """Cache coherency overhead should be >= 1.0."""
        cache_info = CacheInfo(32*1024, 256*1024, 8*1024*1024, 64)
        numa_info = NUMAInfo(1, 8, False)
        
        for n_jobs in [1, 2, 4, 8]:
            overhead = estimate_cache_coherency_overhead(
                n_jobs=n_jobs,
                data_size_per_item=1024,
                cache_info=cache_info,
                numa_info=numa_info
            )
            assert overhead >= 1.0
    
    def test_memory_bandwidth_slowdown_bounded(self):
        """Memory bandwidth slowdown should be between 0.5 and 1.0."""
        bandwidth_info = MemoryBandwidthInfo(40.0, True)
        
        for n_jobs in [1, 2, 4, 8, 16]:
            slowdown = estimate_memory_bandwidth_impact(
                n_jobs=n_jobs,
                data_size_per_item=1024,
                items_per_second_per_core=100.0,
                memory_bandwidth=bandwidth_info
            )
            assert 0.5 <= slowdown <= 1.0
    
    def test_false_sharing_overhead_at_least_one(self):
        """False sharing overhead should be >= 1.0."""
        for n_jobs in [1, 2, 4, 8]:
            for return_size in [8, 16, 32, 64, 128]:
                overhead = estimate_false_sharing_overhead(
                    n_jobs=n_jobs,
                    return_size=return_size,
                    cache_line_size=64
                )
                assert overhead >= 1.0
    
    def test_advanced_amdahl_speedup_positive(self):
        """Speedup should always be non-negative."""
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
            n_jobs=4,
            chunksize=100,
            total_items=1000,
            data_pickle_overhead_per_item=0.0005,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        assert speedup >= 0.0
    
    def test_speedup_bounded_by_n_jobs(self):
        """Speedup should not exceed n_jobs (theoretical maximum)."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=8
        )
        
        for n_jobs in [2, 4, 8]:
            speedup, _ = calculate_advanced_amdahl_speedup(
                total_compute_time=100.0,  # Long compute
                pickle_overhead_per_item=0.00001,  # Minimal overhead
                spawn_cost_per_worker=0.001,
                chunking_overhead_per_chunk=0.00001,
                n_jobs=n_jobs,
                chunksize=1000,
                total_items=10000,
                data_pickle_overhead_per_item=0.00001,
                system_topology=topology,
                data_size_per_item=100,
                return_size_per_item=100
            )
            # Speedup can't exceed n_jobs
            assert speedup <= n_jobs + 0.1  # Small epsilon for floating point


# =============================================================================
# 5. INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Test integration between components."""
    
    def test_detect_system_topology_consistency(self):
        """All topology components should be consistent."""
        for physical_cores in [2, 4, 8, 16]:
            topology = detect_system_topology(physical_cores=physical_cores)
            
            # Verify all components present
            assert isinstance(topology.cache_info, CacheInfo)
            assert isinstance(topology.numa_info, NUMAInfo)
            assert isinstance(topology.memory_bandwidth, MemoryBandwidthInfo)
            assert topology.physical_cores == physical_cores
            
            # Verify NUMA consistency
            total_cores = topology.numa_info.numa_nodes * topology.numa_info.cores_per_node
            assert abs(total_cores - physical_cores) <= topology.numa_info.numa_nodes
    
    def test_advanced_amdahl_with_realistic_topology(self):
        """Test with real detected topology."""
        topology = detect_system_topology(physical_cores=4)
        
        speedup, breakdown = calculate_advanced_amdahl_speedup(
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
        
        # Should produce reasonable results
        assert 0.5 <= speedup <= 4.1
        assert all(key in breakdown for key in [
            'spawn_overhead', 'parallel_compute', 'cache_coherency_factor',
            'bandwidth_slowdown', 'false_sharing_factor'
        ])
    
    def test_overhead_breakdown_structure(self):
        """Test that breakdown dictionary has expected structure."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        _, breakdown = calculate_advanced_amdahl_speedup(
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
        
        # Verify all expected keys
        expected_keys = [
            'spawn_overhead', 'parallel_compute', 'data_ipc_overhead',
            'result_ipc_overhead', 'chunking_overhead', 'cache_coherency_factor',
            'bandwidth_slowdown', 'false_sharing_factor', 'basic_parallel_compute'
        ]
        for key in expected_keys:
            assert key in breakdown
            assert isinstance(breakdown[key], (int, float))


# =============================================================================
# 6. STRESS TESTS
# =============================================================================

class TestStressConditions:
    """Test behavior under stress conditions."""
    
    def test_extremely_large_cache_sizes(self):
        """Very large cache sizes should be handled."""
        cache_info = CacheInfo(
            l1_size=1024*1024,       # 1MB L1 (unrealistic)
            l2_size=100*1024*1024,   # 100MB L2 (unrealistic)
            l3_size=1024*1024*1024,  # 1GB L3 (future-proof)
            cache_line_size=128
        )
        numa_info = NUMAInfo(1, 8, False)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=8,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        # Should still be reasonable
        assert 1.0 <= overhead <= 5.0
    
    def test_many_numa_nodes(self):
        """Large number of NUMA nodes should be handled."""
        numa_info = NUMAInfo(numa_nodes=16, cores_per_node=8, has_numa=True)
        cache_info = CacheInfo(32*1024, 256*1024, 8*1024*1024, 64)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=128,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        # Should be bounded
        assert 1.0 <= overhead <= 30.0
    
    def test_very_high_memory_bandwidth(self):
        """Very high bandwidth should be handled."""
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=1000.0, is_estimated=True)
        
        slowdown = estimate_memory_bandwidth_impact(
            n_jobs=128,
            data_size_per_item=1024*1024,
            items_per_second_per_core=1000.0,
            memory_bandwidth=bandwidth_info
        )
        # With very high bandwidth, should not saturate
        assert slowdown == 1.0
    
    def test_tiny_objects_many_workers(self):
        """Tiny objects with many workers should show false sharing."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=128,
            return_size=1,  # 1 byte
            cache_line_size=64
        )
        # Should have significant overhead
        assert overhead > 1.0
    
    def test_advanced_amdahl_extreme_parameters(self):
        """Extreme parameter combinations should be handled."""
        topology = SystemTopology(
            cache_info=CacheInfo(
                l1_size=1024*1024,
                l2_size=100*1024*1024,
                l3_size=1024*1024*1024,
                cache_line_size=128
            ),
            numa_info=NUMAInfo(numa_nodes=16, cores_per_node=16, has_numa=True),
            memory_bandwidth=MemoryBandwidthInfo(500.0, True),
            physical_cores=256
        )
        
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=1000.0,
            pickle_overhead_per_item=0.1,
            spawn_cost_per_worker=1.0,
            chunking_overhead_per_chunk=0.01,
            n_jobs=256,
            chunksize=10,
            total_items=100000,
            data_pickle_overhead_per_item=0.1,
            system_topology=topology,
            data_size_per_item=1024*1024,
            return_size_per_item=1024
        )
        # Should be bounded and reasonable
        assert 0.0 <= speedup <= 256.0


# =============================================================================
# 7. PLATFORM-SPECIFIC TESTS
# =============================================================================

class TestPlatformSpecific:
    """Test platform-specific behavior."""
    
    def test_detect_cache_info_fallback(self):
        """Fallback should work when detection fails."""
        with patch('amorsize.cost_model._parse_lscpu_cache', return_value=None):
            with patch('amorsize.cost_model._parse_sysfs_cache', return_value=None):
                cache_info = detect_cache_info()
                
                # Should return fallback estimates
                assert isinstance(cache_info, CacheInfo)
                assert cache_info.l1_size > 0
                assert cache_info.l2_size > 0
                assert cache_info.l3_size > 0
    
    def test_detect_numa_info_non_linux(self):
        """Non-Linux systems should return single NUMA node."""
        # On non-Linux, should return default (single node)
        if platform.system() != "Linux":
            numa_info = detect_numa_info(physical_cores=4)
            assert numa_info.numa_nodes == 1
            assert numa_info.has_numa is False
    
    def test_estimate_memory_bandwidth_server_detection(self):
        """Server CPU detection should work if /proc/cpuinfo available."""
        # Mock server CPU
        mock_cpuinfo = "model name: Intel(R) Xeon(R) CPU E5-2680 v4"
        
        with patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=lambda s: MagicMock(read=lambda: mock_cpuinfo), __exit__=lambda *args: None))):
            bandwidth_info = estimate_memory_bandwidth()
            # Server should have higher bandwidth estimate
            # But this depends on whether the mock is actually used
            assert bandwidth_info.bandwidth_gb_per_sec > 0


# =============================================================================
# 8. SPECIFIC EDGE CASES
# =============================================================================

class TestSpecificEdgeCases:
    """Test specific edge cases discovered or predicted."""
    
    def test_single_item_workload(self):
        """Single item workload should be handled."""
        topology = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 4, False),
            memory_bandwidth=MemoryBandwidthInfo(40.0, True),
            physical_cores=4
        )
        
        speedup, _ = calculate_advanced_amdahl_speedup(
            total_compute_time=1.0,
            pickle_overhead_per_item=0.001,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.001,
            n_jobs=4,
            chunksize=1,
            total_items=1,
            data_pickle_overhead_per_item=0.001,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        # Should handle gracefully
        assert speedup >= 0.0
    
    def test_chunksize_larger_than_total_items(self):
        """Chunksize larger than total items should be handled."""
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
            chunking_overhead_per_chunk=0.001,
            n_jobs=4,
            chunksize=10000,  # Much larger than items
            total_items=100,
            data_pickle_overhead_per_item=0.001,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=1024
        )
        assert speedup >= 0.0
    
    def test_dataclass_instantiation(self):
        """Dataclasses should be instantiated correctly."""
        cache = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        assert cache.l1_size == 32*1024
        assert cache.cache_line_size == 64
        
        numa = NUMAInfo(numa_nodes=2, cores_per_node=4, has_numa=True)
        assert numa.numa_nodes == 2
        assert numa.has_numa is True
        
        bandwidth = MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True)
        assert bandwidth.bandwidth_gb_per_sec == 40.0
        assert bandwidth.is_estimated is True
        
        topology = SystemTopology(
            cache_info=cache,
            numa_info=numa,
            memory_bandwidth=bandwidth,
            physical_cores=8
        )
        assert topology.physical_cores == 8
        assert topology.cache_info.l1_size == 32*1024
