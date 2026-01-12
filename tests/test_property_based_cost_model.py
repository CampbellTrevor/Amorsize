"""
Property-based tests for the cost_model module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of cost modeling functions across a wide range of inputs.
"""

import math
from typing import Any, Tuple

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

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
    _parse_size_string,
)


class TestCacheInfoInvariants:
    """Test invariant properties of CacheInfo dataclass."""

    @given(
        l1_size=st.integers(min_value=0, max_value=1024*1024),
        l2_size=st.integers(min_value=0, max_value=10*1024*1024),
        l3_size=st.integers(min_value=0, max_value=100*1024*1024),
        cache_line_size=st.integers(min_value=1, max_value=256)
    )
    @settings(max_examples=100, deadline=2000)
    def test_cache_info_non_negative_values(self, l1_size, l2_size, l3_size, cache_line_size):
        """Test that CacheInfo maintains non-negative values."""
        cache = CacheInfo(
            l1_size=l1_size,
            l2_size=l2_size,
            l3_size=l3_size,
            cache_line_size=cache_line_size
        )
        
        assert cache.l1_size >= 0, f"l1_size should be non-negative, got {cache.l1_size}"
        assert cache.l2_size >= 0, f"l2_size should be non-negative, got {cache.l2_size}"
        assert cache.l3_size >= 0, f"l3_size should be non-negative, got {cache.l3_size}"
        assert cache.cache_line_size >= 1, f"cache_line_size should be positive, got {cache.cache_line_size}"

    @given(
        l1_size=st.integers(min_value=1, max_value=1024*1024),
        l2_size=st.integers(min_value=1, max_value=10*1024*1024),
        l3_size=st.integers(min_value=1, max_value=100*1024*1024),
    )
    @settings(max_examples=50, deadline=2000)
    def test_cache_hierarchy_typical_ordering(self, l1_size, l2_size, l3_size):
        """Test that typical cache hierarchy holds (L1 <= L2 <= L3)."""
        # For realistic inputs, assume cache hierarchy ordering
        assume(l1_size <= l2_size)
        assume(l2_size <= l3_size)
        
        cache = CacheInfo(
            l1_size=l1_size,
            l2_size=l2_size,
            l3_size=l3_size,
            cache_line_size=64
        )
        
        assert cache.l1_size <= cache.l2_size, "L1 should be <= L2"
        assert cache.l2_size <= cache.l3_size, "L2 should be <= L3"


class TestNUMAInfoInvariants:
    """Test invariant properties of NUMAInfo dataclass."""

    @given(
        numa_nodes=st.integers(min_value=1, max_value=16),
        cores_per_node=st.integers(min_value=1, max_value=128),
        has_numa=st.booleans()
    )
    @settings(max_examples=100, deadline=2000)
    def test_numa_info_positive_values(self, numa_nodes, cores_per_node, has_numa):
        """Test that NUMAInfo maintains positive values."""
        numa = NUMAInfo(
            numa_nodes=numa_nodes,
            cores_per_node=cores_per_node,
            has_numa=has_numa
        )
        
        assert numa.numa_nodes >= 1, f"numa_nodes should be at least 1, got {numa.numa_nodes}"
        assert numa.cores_per_node >= 1, f"cores_per_node should be at least 1, got {numa.cores_per_node}"
        assert isinstance(numa.has_numa, bool), f"has_numa should be bool, got {type(numa.has_numa)}"

    @given(
        numa_nodes=st.integers(min_value=1, max_value=1),
        cores_per_node=st.integers(min_value=1, max_value=128),
    )
    @settings(max_examples=50, deadline=2000)
    def test_single_numa_node_no_numa(self, numa_nodes, cores_per_node):
        """Test that single NUMA node typically means no NUMA."""
        numa = NUMAInfo(
            numa_nodes=numa_nodes,
            cores_per_node=cores_per_node,
            has_numa=False
        )
        
        # Single node systems shouldn't have NUMA
        if numa.numa_nodes == 1:
            assert not numa.has_numa, "Single node system shouldn't have NUMA"


class TestMemoryBandwidthInfoInvariants:
    """Test invariant properties of MemoryBandwidthInfo dataclass."""

    @given(
        bandwidth_gb_per_sec=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        is_estimated=st.booleans()
    )
    @settings(max_examples=100, deadline=2000)
    def test_memory_bandwidth_positive(self, bandwidth_gb_per_sec, is_estimated):
        """Test that MemoryBandwidthInfo maintains positive bandwidth."""
        bandwidth = MemoryBandwidthInfo(
            bandwidth_gb_per_sec=bandwidth_gb_per_sec,
            is_estimated=is_estimated
        )
        
        assert bandwidth.bandwidth_gb_per_sec > 0, \
            f"bandwidth should be positive, got {bandwidth.bandwidth_gb_per_sec}"
        assert isinstance(bandwidth.is_estimated, bool), \
            f"is_estimated should be bool, got {type(bandwidth.is_estimated)}"

    @given(
        bandwidth_gb_per_sec=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=2000)
    def test_memory_bandwidth_reasonable_range(self, bandwidth_gb_per_sec):
        """Test that bandwidth is in reasonable range (1-1000 GB/s)."""
        # Realistic range: consumer DDR4 (~20 GB/s) to server systems (~500 GB/s)
        assume(1.0 <= bandwidth_gb_per_sec <= 1000.0)
        
        bandwidth = MemoryBandwidthInfo(
            bandwidth_gb_per_sec=bandwidth_gb_per_sec,
            is_estimated=True
        )
        
        assert 1.0 <= bandwidth.bandwidth_gb_per_sec <= 1000.0, \
            f"bandwidth should be in reasonable range, got {bandwidth.bandwidth_gb_per_sec}"


class TestParseSizeString:
    """Test properties of _parse_size_string function."""

    @given(
        value=st.integers(min_value=0, max_value=1000),
        unit=st.sampled_from(['', 'K', 'M', 'G'])
    )
    @settings(max_examples=100, deadline=2000)
    def test_parse_size_string_non_negative(self, value, unit):
        """Test that parsed sizes are non-negative."""
        size_str = f"{value}{unit}"
        parsed = _parse_size_string(size_str)
        
        assert parsed >= 0, f"Parsed size should be non-negative, got {parsed}"

    @given(value=st.integers(min_value=1, max_value=100))
    @settings(max_examples=50, deadline=2000)
    def test_parse_size_string_units(self, value):
        """Test that unit conversions are correct."""
        # Test K unit (kilobytes)
        parsed_k = _parse_size_string(f"{value}K")
        assert parsed_k == value * 1024, f"K conversion incorrect: {parsed_k} != {value * 1024}"
        
        # Test M unit (megabytes)
        parsed_m = _parse_size_string(f"{value}M")
        assert parsed_m == value * 1024 * 1024, f"M conversion incorrect"
        
        # Test G unit (gigabytes)
        parsed_g = _parse_size_string(f"{value}G")
        assert parsed_g == value * 1024 * 1024 * 1024, f"G conversion incorrect"

    @given(value=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=50, deadline=2000)
    def test_parse_size_string_no_unit(self, value):
        """Test that no unit means bytes."""
        size_str = str(value)
        parsed = _parse_size_string(size_str)
        assert parsed == value, f"No unit should mean bytes, got {parsed} != {value}"

    @given(invalid_str=st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))
    @settings(max_examples=50, deadline=2000)
    def test_parse_size_string_invalid_returns_zero(self, invalid_str):
        """Test that invalid strings return 0."""
        # Skip if string happens to contain valid patterns
        assume(not any(c in invalid_str.upper() for c in ['K', 'M', 'G']))
        assume(not any(c.isdigit() for c in invalid_str))
        
        parsed = _parse_size_string(invalid_str)
        assert parsed == 0, f"Invalid string should return 0, got {parsed}"


class TestDetectCacheInfo:
    """Test properties of detect_cache_info function."""

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_detect_cache_info_returns_valid_cache(self, _dummy):
        """Test that detect_cache_info returns valid CacheInfo."""
        cache = detect_cache_info()
        
        assert isinstance(cache, CacheInfo), f"Should return CacheInfo, got {type(cache)}"
        assert cache.l1_size >= 0, "l1_size should be non-negative"
        assert cache.l2_size >= 0, "l2_size should be non-negative"
        assert cache.l3_size >= 0, "l3_size should be non-negative"
        assert cache.cache_line_size > 0, "cache_line_size should be positive"

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_detect_cache_info_reasonable_values(self, _dummy):
        """Test that detected cache sizes are in reasonable range."""
        cache = detect_cache_info()
        
        # L1: typically 16KB-128KB per core
        assert 0 <= cache.l1_size <= 10 * 1024 * 1024, "l1_size should be reasonable"
        
        # L2: typically 128KB-2MB per core
        assert 0 <= cache.l2_size <= 50 * 1024 * 1024, "l2_size should be reasonable"
        
        # L3: typically 2MB-128MB shared
        assert 0 <= cache.l3_size <= 500 * 1024 * 1024, "l3_size should be reasonable"
        
        # Cache line: typically 64 bytes, but 32-128 is valid
        assert 16 <= cache.cache_line_size <= 256, "cache_line_size should be reasonable"

    @settings(max_examples=5, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_detect_cache_info_deterministic(self, _dummy):
        """Test that detect_cache_info returns same values on repeated calls."""
        cache1 = detect_cache_info()
        cache2 = detect_cache_info()
        
        # Should be deterministic (same system, same results)
        assert cache1.l1_size == cache2.l1_size, "l1_size should be deterministic"
        assert cache1.l2_size == cache2.l2_size, "l2_size should be deterministic"
        assert cache1.l3_size == cache2.l3_size, "l3_size should be deterministic"
        assert cache1.cache_line_size == cache2.cache_line_size, "cache_line_size should be deterministic"


class TestDetectNUMAInfo:
    """Test properties of detect_numa_info function."""

    @given(physical_cores=st.integers(min_value=1, max_value=256))
    @settings(max_examples=50, deadline=5000)
    def test_detect_numa_info_returns_valid_numa(self, physical_cores):
        """Test that detect_numa_info returns valid NUMAInfo."""
        numa = detect_numa_info(physical_cores)
        
        assert isinstance(numa, NUMAInfo), f"Should return NUMAInfo, got {type(numa)}"
        assert numa.numa_nodes >= 1, "numa_nodes should be at least 1"
        assert numa.cores_per_node >= 1, "cores_per_node should be at least 1"
        assert isinstance(numa.has_numa, bool), "has_numa should be bool"

    @given(physical_cores=st.integers(min_value=1, max_value=256))
    @settings(max_examples=50, deadline=5000)
    def test_detect_numa_info_cores_distribution(self, physical_cores):
        """Test that cores are distributed across NUMA nodes correctly."""
        numa = detect_numa_info(physical_cores)
        
        # Total cores should match or be less than physical_cores
        # (cores_per_node * numa_nodes might be slightly less due to integer division)
        total_cores_estimate = numa.cores_per_node * numa.numa_nodes
        assert total_cores_estimate <= physical_cores + numa.numa_nodes, \
            f"Core distribution incorrect: {total_cores_estimate} vs {physical_cores}"

    @given(physical_cores=st.integers(min_value=1, max_value=256))
    @settings(max_examples=20, deadline=5000)
    def test_detect_numa_info_single_node_for_small_systems(self, physical_cores):
        """Test that small systems typically have single NUMA node."""
        numa = detect_numa_info(physical_cores)
        
        # Most consumer systems have 1 NUMA node
        if numa.numa_nodes == 1:
            assert numa.cores_per_node == physical_cores, \
                "Single node should have all cores"
            # Single node systems typically don't have NUMA
            # (but this is system-dependent, so not enforced)


class TestEstimateMemoryBandwidth:
    """Test properties of estimate_memory_bandwidth function."""

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_estimate_memory_bandwidth_positive(self, _dummy):
        """Test that estimated bandwidth is positive."""
        bandwidth = estimate_memory_bandwidth()
        
        assert isinstance(bandwidth, MemoryBandwidthInfo), \
            f"Should return MemoryBandwidthInfo, got {type(bandwidth)}"
        assert bandwidth.bandwidth_gb_per_sec > 0, \
            f"bandwidth should be positive, got {bandwidth.bandwidth_gb_per_sec}"
        assert isinstance(bandwidth.is_estimated, bool), "is_estimated should be bool"

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_estimate_memory_bandwidth_reasonable_range(self, _dummy):
        """Test that estimated bandwidth is in reasonable range."""
        bandwidth = estimate_memory_bandwidth()
        
        # Consumer systems: 10-60 GB/s typical (DDR4 dual-channel)
        # Server systems: 60-500 GB/s (multi-channel, DDR5)
        assert 10.0 <= bandwidth.bandwidth_gb_per_sec <= 500.0, \
            f"bandwidth should be in reasonable range, got {bandwidth.bandwidth_gb_per_sec}"

    @settings(max_examples=10, deadline=5000)
    @given(st.integers(min_value=0, max_value=0))
    def test_estimate_memory_bandwidth_is_estimated(self, _dummy):
        """Test that is_estimated flag is set correctly."""
        bandwidth = estimate_memory_bandwidth()
        
        # Current implementation always estimates (doesn't measure)
        assert bandwidth.is_estimated is True, "is_estimated should be True"


class TestDetectSystemTopology:
    """Test properties of detect_system_topology function."""

    @given(physical_cores=st.integers(min_value=1, max_value=256))
    @settings(max_examples=20, deadline=10000)
    def test_detect_system_topology_returns_valid_topology(self, physical_cores):
        """Test that detect_system_topology returns valid SystemTopology."""
        topology = detect_system_topology(physical_cores)
        
        assert isinstance(topology, SystemTopology), \
            f"Should return SystemTopology, got {type(topology)}"
        assert isinstance(topology.cache_info, CacheInfo), "cache_info should be CacheInfo"
        assert isinstance(topology.numa_info, NUMAInfo), "numa_info should be NUMAInfo"
        assert isinstance(topology.memory_bandwidth, MemoryBandwidthInfo), \
            "memory_bandwidth should be MemoryBandwidthInfo"
        assert topology.physical_cores == physical_cores, \
            f"physical_cores should match input: {topology.physical_cores} != {physical_cores}"

    @given(physical_cores=st.integers(min_value=1, max_value=256))
    @settings(max_examples=20, deadline=10000)
    def test_detect_system_topology_components_valid(self, physical_cores):
        """Test that all topology components are valid."""
        topology = detect_system_topology(physical_cores)
        
        # Cache info should be valid
        assert topology.cache_info.l1_size >= 0, "l1_size should be non-negative"
        assert topology.cache_info.cache_line_size > 0, "cache_line_size should be positive"
        
        # NUMA info should be valid
        assert topology.numa_info.numa_nodes >= 1, "numa_nodes should be at least 1"
        assert topology.numa_info.cores_per_node >= 1, "cores_per_node should be at least 1"
        
        # Memory bandwidth should be valid
        assert topology.memory_bandwidth.bandwidth_gb_per_sec > 0, "bandwidth should be positive"
        
        # Physical cores should match
        assert topology.physical_cores >= 1, "physical_cores should be at least 1"


class TestCacheCoherencyOverhead:
    """Test properties of estimate_cache_coherency_overhead function."""

    @given(
        n_jobs=st.integers(min_value=1, max_value=256),
        data_size_per_item=st.integers(min_value=0, max_value=100*1024*1024),
    )
    @settings(max_examples=100, deadline=2000)
    def test_cache_coherency_overhead_at_least_one(self, n_jobs, data_size_per_item):
        """Test that overhead factor is at least 1.0."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        numa_info = NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=n_jobs,
            data_size_per_item=data_size_per_item,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        assert overhead >= 1.0, f"Overhead should be at least 1.0, got {overhead}"

    @given(data_size_per_item=st.integers(min_value=0, max_value=100*1024*1024))
    @settings(max_examples=50, deadline=2000)
    def test_cache_coherency_overhead_single_job_no_overhead(self, data_size_per_item):
        """Test that single job has no overhead (factor = 1.0)."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        numa_info = NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False)
        
        overhead = estimate_cache_coherency_overhead(
            n_jobs=1,
            data_size_per_item=data_size_per_item,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        assert overhead == 1.0, f"Single job should have no overhead, got {overhead}"

    @given(
        n_jobs=st.integers(min_value=2, max_value=32),
        data_size_per_item=st.integers(min_value=1000, max_value=10*1024*1024),
    )
    @settings(max_examples=50, deadline=2000)
    def test_cache_coherency_overhead_increases_with_jobs(self, n_jobs, data_size_per_item):
        """Test that overhead increases with more jobs."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        numa_info = NUMAInfo(numa_nodes=1, cores_per_node=32, has_numa=False)
        
        overhead_low = estimate_cache_coherency_overhead(
            n_jobs=2,
            data_size_per_item=data_size_per_item,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        overhead_high = estimate_cache_coherency_overhead(
            n_jobs=n_jobs,
            data_size_per_item=data_size_per_item,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        # More jobs should have equal or higher overhead
        assert overhead_high >= overhead_low, \
            f"Overhead should increase with jobs: {overhead_high} < {overhead_low}"

    @given(
        n_jobs=st.integers(min_value=2, max_value=16),
    )
    @settings(max_examples=50, deadline=2000)
    def test_cache_coherency_overhead_numa_penalty(self, n_jobs):
        """Test that NUMA systems have higher overhead."""
        cache_info = CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64)
        data_size = 1024 * 1024  # 1 MB
        
        # Single NUMA node
        numa_single = NUMAInfo(numa_nodes=1, cores_per_node=16, has_numa=False)
        overhead_single = estimate_cache_coherency_overhead(
            n_jobs=n_jobs,
            data_size_per_item=data_size,
            cache_info=cache_info,
            numa_info=numa_single
        )
        
        # Multiple NUMA nodes (cores span nodes)
        numa_multi = NUMAInfo(numa_nodes=2, cores_per_node=8, has_numa=True)
        overhead_multi = estimate_cache_coherency_overhead(
            n_jobs=n_jobs,
            data_size_per_item=data_size,
            cache_info=cache_info,
            numa_info=numa_multi
        )
        
        # Multi-NUMA should have equal or higher overhead when jobs span nodes
        if n_jobs > numa_multi.cores_per_node:
            assert overhead_multi >= overhead_single, \
                f"NUMA overhead should be higher: {overhead_multi} < {overhead_single}"


class TestMemoryBandwidthImpact:
    """Test properties of estimate_memory_bandwidth_impact function."""

    @given(
        n_jobs=st.integers(min_value=1, max_value=256),
        data_size_per_item=st.integers(min_value=0, max_value=10*1024*1024),
        items_per_second_per_core=st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=2000)
    def test_bandwidth_impact_between_zero_and_one(self, n_jobs, data_size_per_item, items_per_second_per_core):
        """Test that bandwidth impact is between 0.0 and 1.0."""
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True)
        
        impact = estimate_memory_bandwidth_impact(
            n_jobs=n_jobs,
            data_size_per_item=data_size_per_item,
            items_per_second_per_core=items_per_second_per_core,
            memory_bandwidth=bandwidth_info
        )
        
        assert 0.0 <= impact <= 1.0, f"Impact should be in [0, 1], got {impact}"

    @given(
        data_size_per_item=st.integers(min_value=0, max_value=10*1024*1024),
        items_per_second_per_core=st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=2000)
    def test_bandwidth_impact_single_job_no_impact(self, data_size_per_item, items_per_second_per_core):
        """Test that single job has no bandwidth impact (factor = 1.0)."""
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True)
        
        impact = estimate_memory_bandwidth_impact(
            n_jobs=1,
            data_size_per_item=data_size_per_item,
            items_per_second_per_core=items_per_second_per_core,
            memory_bandwidth=bandwidth_info
        )
        
        assert impact == 1.0, f"Single job should have no bandwidth impact, got {impact}"

    @given(
        n_jobs=st.integers(min_value=2, max_value=32),
        data_size_per_item=st.integers(min_value=1000, max_value=1024*1024),
    )
    @settings(max_examples=50, deadline=2000)
    def test_bandwidth_impact_low_demand_no_impact(self, n_jobs, data_size_per_item):
        """Test that low bandwidth demand has minimal impact."""
        # Very slow processing rate (low bandwidth demand)
        items_per_second_per_core = 0.1
        bandwidth_info = MemoryBandwidthInfo(bandwidth_gb_per_sec=100.0, is_estimated=True)
        
        impact = estimate_memory_bandwidth_impact(
            n_jobs=n_jobs,
            data_size_per_item=data_size_per_item,
            items_per_second_per_core=items_per_second_per_core,
            memory_bandwidth=bandwidth_info
        )
        
        # Low demand should result in no slowdown (factor = 1.0)
        assert impact == 1.0, f"Low demand should have no impact, got {impact}"


class TestFalseSharingOverhead:
    """Test properties of estimate_false_sharing_overhead function."""

    @given(
        n_jobs=st.integers(min_value=1, max_value=256),
        return_size=st.integers(min_value=0, max_value=10*1024),
        cache_line_size=st.integers(min_value=16, max_value=256),
    )
    @settings(max_examples=100, deadline=2000)
    def test_false_sharing_overhead_at_least_one(self, n_jobs, return_size, cache_line_size):
        """Test that overhead factor is at least 1.0."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=n_jobs,
            return_size=return_size,
            cache_line_size=cache_line_size
        )
        
        assert overhead >= 1.0, f"Overhead should be at least 1.0, got {overhead}"

    @given(
        return_size=st.integers(min_value=0, max_value=10*1024),
        cache_line_size=st.integers(min_value=16, max_value=256),
    )
    @settings(max_examples=50, deadline=2000)
    def test_false_sharing_overhead_single_job_no_overhead(self, return_size, cache_line_size):
        """Test that single job has no overhead (factor = 1.0)."""
        overhead = estimate_false_sharing_overhead(
            n_jobs=1,
            return_size=return_size,
            cache_line_size=cache_line_size
        )
        
        assert overhead == 1.0, f"Single job should have no overhead, got {overhead}"

    @given(
        n_jobs=st.integers(min_value=2, max_value=32),
        cache_line_size=st.integers(min_value=64, max_value=128),
    )
    @settings(max_examples=50, deadline=2000)
    def test_false_sharing_large_objects_no_overhead(self, n_jobs, cache_line_size):
        """Test that large objects have no false sharing overhead."""
        # Large return size (larger than cache line)
        return_size = cache_line_size * 2
        
        overhead = estimate_false_sharing_overhead(
            n_jobs=n_jobs,
            return_size=return_size,
            cache_line_size=cache_line_size
        )
        
        assert overhead == 1.0, f"Large objects should have no false sharing, got {overhead}"

    @given(
        n_jobs=st.integers(min_value=2, max_value=32),
        cache_line_size=st.integers(min_value=64, max_value=128),
    )
    @settings(max_examples=50, deadline=2000)
    def test_false_sharing_small_objects_overhead(self, n_jobs, cache_line_size):
        """Test that small objects may have false sharing overhead."""
        # Small return size (much smaller than cache line)
        return_size = cache_line_size // 4
        
        overhead = estimate_false_sharing_overhead(
            n_jobs=n_jobs,
            return_size=return_size,
            cache_line_size=cache_line_size
        )
        
        # Small objects with multiple jobs should have some overhead
        if n_jobs > 1:
            assert overhead >= 1.0, f"Small objects should have overhead, got {overhead}"


class TestAdvancedAmdahlSpeedup:
    """Test properties of calculate_advanced_amdahl_speedup function."""

    @given(
        total_compute_time=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        n_jobs=st.integers(min_value=1, max_value=32),
        chunksize=st.integers(min_value=1, max_value=1000),
        total_items=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=100, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_advanced_speedup_positive(self, total_compute_time, n_jobs, chunksize, total_items):
        """Test that speedup is always positive."""
        # Ensure total_items >= n_jobs * chunksize for valid chunking
        assume(total_items >= chunksize)
        
        topology = SystemTopology(
            cache_info=CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64),
            numa_info=NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False),
            memory_bandwidth=MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True),
            physical_cores=8
        )
        
        speedup, overhead = calculate_advanced_amdahl_speedup(
            total_compute_time=total_compute_time,
            pickle_overhead_per_item=0.0001,
            spawn_cost_per_worker=0.015,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            data_pickle_overhead_per_item=0.0001,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=256
        )
        
        assert speedup > 0, f"Speedup should be positive, got {speedup}"

    @given(
        total_compute_time=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        n_jobs=st.integers(min_value=1, max_value=32),
        total_items=st.integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=50, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_advanced_speedup_bounded_by_n_jobs(self, total_compute_time, n_jobs, total_items):
        """Test that speedup cannot exceed n_jobs (theoretical maximum)."""
        chunksize = max(1, total_items // n_jobs)
        
        topology = SystemTopology(
            cache_info=CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64),
            numa_info=NUMAInfo(numa_nodes=1, cores_per_node=32, has_numa=False),
            memory_bandwidth=MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True),
            physical_cores=32
        )
        
        speedup, overhead = calculate_advanced_amdahl_speedup(
            total_compute_time=total_compute_time,
            pickle_overhead_per_item=0.0001,
            spawn_cost_per_worker=0.015,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            data_pickle_overhead_per_item=0.0001,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=256
        )
        
        assert speedup <= float(n_jobs), \
            f"Speedup ({speedup}) should not exceed n_jobs ({n_jobs})"

    @given(
        total_compute_time=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        total_items=st.integers(min_value=10, max_value=1000),
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_advanced_speedup_single_job_is_one(self, total_compute_time, total_items):
        """Test that single job has speedup of 1.0."""
        topology = SystemTopology(
            cache_info=CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64),
            numa_info=NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False),
            memory_bandwidth=MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True),
            physical_cores=8
        )
        
        speedup, overhead = calculate_advanced_amdahl_speedup(
            total_compute_time=total_compute_time,
            pickle_overhead_per_item=0.0,
            spawn_cost_per_worker=0.0,
            chunking_overhead_per_chunk=0.0,
            n_jobs=1,
            chunksize=1,
            total_items=total_items,
            data_pickle_overhead_per_item=0.0,
            system_topology=topology,
            data_size_per_item=0,
            return_size_per_item=0
        )
        
        # Single job with no overhead should have speedup close to 1.0
        assert 0.9 <= speedup <= 1.1, f"Single job speedup should be ~1.0, got {speedup}"

    @given(
        total_compute_time=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        n_jobs=st.integers(min_value=2, max_value=16),
        total_items=st.integers(min_value=100, max_value=1000),
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_advanced_speedup_returns_overhead_breakdown(self, total_compute_time, n_jobs, total_items):
        """Test that overhead breakdown is returned and valid."""
        chunksize = max(1, total_items // (n_jobs * 2))
        
        topology = SystemTopology(
            cache_info=CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64),
            numa_info=NUMAInfo(numa_nodes=1, cores_per_node=16, has_numa=False),
            memory_bandwidth=MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True),
            physical_cores=16
        )
        
        speedup, overhead = calculate_advanced_amdahl_speedup(
            total_compute_time=total_compute_time,
            pickle_overhead_per_item=0.0001,
            spawn_cost_per_worker=0.015,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            data_pickle_overhead_per_item=0.0001,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=256
        )
        
        # Check that overhead breakdown contains expected keys
        assert isinstance(overhead, dict), "Overhead should be a dictionary"
        assert 'spawn_overhead' in overhead, "Missing spawn_overhead"
        assert 'parallel_compute' in overhead, "Missing parallel_compute"
        assert 'cache_coherency_factor' in overhead, "Missing cache_coherency_factor"
        assert 'bandwidth_slowdown' in overhead, "Missing bandwidth_slowdown"
        assert 'false_sharing_factor' in overhead, "Missing false_sharing_factor"
        
        # All overhead components should be non-negative
        assert overhead['spawn_overhead'] >= 0, "spawn_overhead should be non-negative"
        assert overhead['parallel_compute'] >= 0, "parallel_compute should be non-negative"
        assert overhead['cache_coherency_factor'] >= 1.0, "cache_coherency_factor should be >= 1.0"
        assert 0 <= overhead['bandwidth_slowdown'] <= 1.0, "bandwidth_slowdown should be in [0, 1]"
        assert overhead['false_sharing_factor'] >= 1.0, "false_sharing_factor should be >= 1.0"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @settings(max_examples=20, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_zero_compute_time_handled(self, _dummy):
        """Test that zero compute time is handled gracefully."""
        topology = SystemTopology(
            cache_info=CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64),
            numa_info=NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False),
            memory_bandwidth=MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True),
            physical_cores=8
        )
        
        speedup, overhead = calculate_advanced_amdahl_speedup(
            total_compute_time=0.0,
            pickle_overhead_per_item=0.0001,
            spawn_cost_per_worker=0.015,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=4,
            chunksize=10,
            total_items=100,
            data_pickle_overhead_per_item=0.0001,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=256
        )
        
        # Should return speedup of 1.0 for zero compute time
        assert speedup == 1.0, f"Zero compute time should have speedup 1.0, got {speedup}"

    @settings(max_examples=20, deadline=2000)
    @given(st.integers(min_value=0, max_value=0))
    def test_zero_n_jobs_handled(self, _dummy):
        """Test that zero n_jobs is handled gracefully."""
        topology = SystemTopology(
            cache_info=CacheInfo(l1_size=32*1024, l2_size=256*1024, l3_size=8*1024*1024, cache_line_size=64),
            numa_info=NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False),
            memory_bandwidth=MemoryBandwidthInfo(bandwidth_gb_per_sec=40.0, is_estimated=True),
            physical_cores=8
        )
        
        speedup, overhead = calculate_advanced_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.0001,
            spawn_cost_per_worker=0.015,
            chunking_overhead_per_chunk=0.0005,
            n_jobs=0,
            chunksize=10,
            total_items=100,
            data_pickle_overhead_per_item=0.0001,
            system_topology=topology,
            data_size_per_item=1024,
            return_size_per_item=256
        )
        
        # Should return speedup of 1.0 for zero n_jobs
        assert speedup == 1.0, f"Zero n_jobs should have speedup 1.0, got {speedup}"

    @given(
        l1_size=st.integers(min_value=0, max_value=0),
        l2_size=st.integers(min_value=0, max_value=0),
        l3_size=st.integers(min_value=0, max_value=0),
    )
    @settings(max_examples=20, deadline=2000)
    def test_zero_cache_sizes_handled(self, l1_size, l2_size, l3_size):
        """Test that zero cache sizes are handled gracefully."""
        cache_info = CacheInfo(
            l1_size=l1_size,
            l2_size=l2_size,
            l3_size=l3_size,
            cache_line_size=64
        )
        numa_info = NUMAInfo(numa_nodes=1, cores_per_node=8, has_numa=False)
        
        # Should not crash with zero cache sizes
        overhead = estimate_cache_coherency_overhead(
            n_jobs=4,
            data_size_per_item=1024,
            cache_info=cache_info,
            numa_info=numa_info
        )
        
        assert overhead >= 1.0, f"Overhead should be at least 1.0, got {overhead}"
