"""
Advanced cost modeling for multiprocessing performance prediction.

This module provides sophisticated cost models that account for hardware-level
effects beyond basic Amdahl's Law, including:
- Cache effects (L1/L2/L3 cache misses, cache coherency overhead)
- NUMA architecture (non-uniform memory access penalties)
- Memory bandwidth saturation (contention when multiple cores access memory)
- False sharing (cache line ping-ponging between cores)

These models provide more accurate speedup predictions for multi-core workloads.
"""

import os
import platform
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CacheInfo:
    """Information about CPU cache hierarchy."""
    l1_size: int  # L1 cache size in bytes
    l2_size: int  # L2 cache size in bytes
    l3_size: int  # L3 cache size in bytes
    cache_line_size: int  # Cache line size in bytes (typically 64)
    

@dataclass
class NUMAInfo:
    """Information about NUMA topology."""
    numa_nodes: int  # Number of NUMA nodes
    cores_per_node: int  # Cores per NUMA node
    has_numa: bool  # Whether system has NUMA architecture
    

@dataclass
class MemoryBandwidthInfo:
    """Information about memory bandwidth characteristics."""
    bandwidth_gb_per_sec: float  # Peak memory bandwidth in GB/s
    is_estimated: bool  # Whether this is an estimate vs measured


@dataclass
class SystemTopology:
    """Complete system topology information for cost modeling."""
    cache_info: CacheInfo
    numa_info: NUMAInfo
    memory_bandwidth: MemoryBandwidthInfo
    physical_cores: int
    

def _parse_size_string(size_str: str) -> int:
    """
    Parse a size string like '256K', '8M', '2.5G' into bytes.
    
    Args:
        size_str: Size string with K/M/G suffix
    
    Returns:
        Size in bytes
    """
    import re
    # Match number (with optional decimal) and unit
    match = re.match(r'^\s*([\d.]+)\s*([KMG])?', size_str.upper())
    if not match:
        return 0
    
    value = float(match.group(1))
    unit = match.group(2)
    
    if unit == 'K':
        return int(value * 1024)
    elif unit == 'M':
        return int(value * 1024 * 1024)
    elif unit == 'G':
        return int(value * 1024 * 1024 * 1024)
    else:
        return int(value)


def _parse_lscpu_cache() -> Optional[CacheInfo]:
    """
    Parse cache information from lscpu on Linux systems.
    
    Returns:
        CacheInfo object if successful, None otherwise
    """
    try:
        import subprocess
        result = subprocess.run(
            ['lscpu', '-C'],
            capture_output=True,
            text=True,
            timeout=1.0
        )
        
        if result.returncode != 0:
            return None
        
        # Parse lscpu cache output
        # Format: NAME ONE-SIZE ALL-SIZE WAYS TYPE LEVEL
        l1_size = 0
        l2_size = 0
        l3_size = 0
        cache_line_size = 64  # Default
        
        for line in result.stdout.split('\n'):
            if not line.strip() or line.startswith('NAME'):
                continue
            
            parts = line.split()
            if len(parts) >= 6:
                level = parts[5]
                all_size_str = parts[2]
                
                # Parse size using helper function
                size_bytes = _parse_size_string(all_size_str)
                
                if level == '1':
                    l1_size = size_bytes
                elif level == '2':
                    l2_size = size_bytes
                elif level == '3':
                    l3_size = size_bytes
        
        if l1_size > 0:
            return CacheInfo(
                l1_size=l1_size,
                l2_size=l2_size,
                l3_size=l3_size,
                cache_line_size=cache_line_size
            )
        
        return None
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired, ValueError):
        return None


def _parse_sysfs_cache() -> Optional[CacheInfo]:
    """
    Parse cache information from /sys/devices/system/cpu on Linux.
    
    Returns:
        CacheInfo object if successful, None otherwise
    """
    try:
        # Read cache info from /sys for CPU 0
        cache_base = "/sys/devices/system/cpu/cpu0/cache"
        if not os.path.exists(cache_base):
            return None
        
        l1_size = 0
        l2_size = 0
        l3_size = 0
        cache_line_size = 64  # Default
        
        # Iterate through cache indices
        for i in range(4):  # Usually index0-index3
            index_path = os.path.join(cache_base, f"index{i}")
            if not os.path.exists(index_path):
                continue
            
            # Read level
            level_path = os.path.join(index_path, "level")
            if not os.path.exists(level_path):
                continue
            
            with open(level_path, 'r') as f:
                level = int(f.read().strip())
            
            # Read size
            size_path = os.path.join(index_path, "size")
            if not os.path.exists(size_path):
                continue
            
            with open(size_path, 'r') as f:
                size_str = f.read().strip()
            
            # Parse size using helper function
            size_bytes = _parse_size_string(size_str)
            
            # Read coherency_line_size if available
            coherency_path = os.path.join(index_path, "coherency_line_size")
            if os.path.exists(coherency_path):
                with open(coherency_path, 'r') as f:
                    cache_line_size = int(f.read().strip())
            
            # Assign to appropriate level
            if level == 1:
                l1_size = max(l1_size, size_bytes)  # Take max if we see L1D and L1I
            elif level == 2:
                l2_size = max(l2_size, size_bytes)
            elif level == 3:
                l3_size = max(l3_size, size_bytes)
        
        if l1_size > 0:
            return CacheInfo(
                l1_size=l1_size,
                l2_size=l2_size,
                l3_size=l3_size,
                cache_line_size=cache_line_size
            )
        
        return None
    except (IOError, ValueError):
        return None


def detect_cache_info() -> CacheInfo:
    """
    Detect CPU cache hierarchy information.
    
    Returns:
        CacheInfo object with detected or estimated cache sizes
        
    Detection Strategy:
        1. Try lscpu -C (modern Linux)
        2. Try /sys/devices/system/cpu (Linux sysfs)
        3. Use conservative estimates based on CPU generation
    """
    # Try lscpu first
    cache_info = _parse_lscpu_cache()
    if cache_info is not None:
        return cache_info
    
    # Try sysfs
    cache_info = _parse_sysfs_cache()
    if cache_info is not None:
        return cache_info
    
    # Fall back to conservative estimates
    # Modern CPUs typically have:
    # - L1: 32-64KB per core
    # - L2: 256KB-1MB per core
    # - L3: 8-64MB shared
    return CacheInfo(
        l1_size=32 * 1024,      # 32KB L1
        l2_size=256 * 1024,     # 256KB L2
        l3_size=8 * 1024 * 1024,  # 8MB L3
        cache_line_size=64      # Standard 64-byte cache line
    )


def _detect_numa_linux() -> Optional[NUMAInfo]:
    """
    Detect NUMA topology on Linux using numactl or /sys.
    
    Returns:
        NUMAInfo object if NUMA detected, None otherwise
    """
    try:
        # Try numactl first
        import subprocess
        result = subprocess.run(
            ['numactl', '--hardware'],
            capture_output=True,
            text=True,
            timeout=1.0
        )
        
        if result.returncode == 0:
            # Parse numactl output
            numa_nodes = 0
            for line in result.stdout.split('\n'):
                if 'available:' in line and 'nodes' in line:
                    # Format: "available: N nodes (0-N-1)"
                    match = re.search(r'available:\s*(\d+)\s+nodes', line)
                    if match:
                        numa_nodes = int(match.group(1))
                        break
            
            if numa_nodes > 1:
                # Estimate cores per node (will be refined by caller)
                return NUMAInfo(
                    numa_nodes=numa_nodes,
                    cores_per_node=1,  # Placeholder
                    has_numa=True
                )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass
    
    # Try /sys/devices/system/node
    try:
        node_path = "/sys/devices/system/node"
        if os.path.exists(node_path):
            # Count node directories (node0, node1, etc.)
            numa_nodes = 0
            for entry in os.listdir(node_path):
                if entry.startswith('node') and entry[4:].isdigit():
                    numa_nodes += 1
            
            if numa_nodes > 1:
                return NUMAInfo(
                    numa_nodes=numa_nodes,
                    cores_per_node=1,  # Placeholder
                    has_numa=True
                )
    except (IOError, OSError):
        pass
    
    return None


def detect_numa_info(physical_cores: int) -> NUMAInfo:
    """
    Detect NUMA (Non-Uniform Memory Access) topology.
    
    Args:
        physical_cores: Number of physical CPU cores
    
    Returns:
        NUMAInfo object with detected or estimated NUMA topology
        
    Detection Strategy:
        1. Try numactl --hardware (Linux with numactl)
        2. Try /sys/devices/system/node (Linux sysfs)
        3. Assume single NUMA node (most common for consumer hardware)
    """
    system = platform.system()
    
    if system == "Linux":
        numa_info = _detect_numa_linux()
        if numa_info is not None:
            # Calculate cores per node
            numa_info.cores_per_node = physical_cores // numa_info.numa_nodes
            return numa_info
    
    # Default: single NUMA node (no NUMA)
    return NUMAInfo(
        numa_nodes=1,
        cores_per_node=physical_cores,
        has_numa=False
    )


def estimate_memory_bandwidth() -> MemoryBandwidthInfo:
    """
    Estimate system memory bandwidth.
    
    Returns:
        MemoryBandwidthInfo with estimated bandwidth
        
    Estimation Strategy:
        Based on typical system configurations:
        - DDR4-2400: ~19 GB/s per channel
        - DDR4-3200: ~25 GB/s per channel
        - DDR5-4800: ~38 GB/s per channel
        - Server systems: Multiple channels (2-8)
        - Consumer systems: 2 channels typical
        
        We use conservative estimates based on CPU generation markers.
    """
    # Conservative estimate: DDR4 dual-channel
    # Most consumer systems have 2 channels × ~20 GB/s = 40 GB/s
    # Server systems can have much more
    bandwidth_gb_s = 40.0
    
    # Try to detect if this is a server system (more bandwidth)
    try:
        # Server CPUs often have "Xeon" or "EPYC" in the name
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Xeon' in cpuinfo or 'EPYC' in cpuinfo:
                # Server systems typically have 4-8 channels
                bandwidth_gb_s = 100.0  # Conservative server estimate
    except (IOError, OSError):
        pass
    
    return MemoryBandwidthInfo(
        bandwidth_gb_per_sec=bandwidth_gb_s,
        is_estimated=True
    )


def detect_system_topology(physical_cores: int) -> SystemTopology:
    """
    Detect complete system topology for advanced cost modeling.
    
    Args:
        physical_cores: Number of physical CPU cores
    
    Returns:
        SystemTopology object with detected hardware information
        
    This function combines all topology detection:
    - Cache hierarchy (L1/L2/L3 sizes)
    - NUMA architecture (nodes and core distribution)
    - Memory bandwidth (estimated peak throughput)
    """
    return SystemTopology(
        cache_info=detect_cache_info(),
        numa_info=detect_numa_info(physical_cores),
        memory_bandwidth=estimate_memory_bandwidth(),
        physical_cores=physical_cores
    )


def estimate_cache_coherency_overhead(
    n_jobs: int,
    data_size_per_item: int,
    cache_info: CacheInfo,
    numa_info: NUMAInfo
) -> float:
    """
    Estimate cache coherency overhead for multi-core execution.
    
    Args:
        n_jobs: Number of parallel workers
        data_size_per_item: Size of data per work item in bytes
        cache_info: Cache hierarchy information
        numa_info: NUMA topology information
    
    Returns:
        Estimated overhead factor (multiplicative, >= 1.0)
        
    Theory:
        Cache coherency overhead occurs when multiple cores access and modify
        shared memory. The overhead grows with:
        - Number of cores (more cores = more coherency traffic)
        - Working set size relative to L3 cache (cache misses)
        - NUMA boundaries (cross-node access is slower)
        
    Model:
        overhead = 1.0 + (coherency_factor × scale_factor)
        where:
        - coherency_factor: Base overhead per core (typical: 2-5%)
        - scale_factor: Increases with core count and cache pressure
    """
    if n_jobs <= 1:
        return 1.0  # No overhead with single worker
    
    # Base coherency overhead per core (2-5% typical)
    base_coherency_overhead = 0.03  # 3% per additional core
    
    # Calculate cache pressure
    # If working set exceeds L3, coherency overhead increases
    l3_size = cache_info.l3_size
    working_set_per_core = data_size_per_item
    total_working_set = working_set_per_core * n_jobs
    
    # Cache pressure multiplier (1.0 if fits in L3, higher if spills to RAM)
    if total_working_set <= l3_size:
        cache_pressure = 1.0
    else:
        # Linear increase in overhead as working set exceeds cache
        cache_pressure = 1.0 + (total_working_set - l3_size) / l3_size * 0.5
        cache_pressure = min(cache_pressure, 2.0)  # Cap at 2x
    
    # NUMA multiplier (cross-node access adds overhead)
    numa_multiplier = 1.0
    if numa_info.has_numa and n_jobs > numa_info.cores_per_node:
        # Overhead increases when workers span NUMA nodes
        # Typical NUMA penalty: 20-40% for remote access
        numa_multiplier = 1.2
    
    # Calculate total overhead
    # Overhead scales sub-linearly with core count (not all cores contend equally)
    scale_factor = (n_jobs - 1) ** 0.8  # Sub-linear scaling
    overhead_factor = 1.0 + (base_coherency_overhead * scale_factor * cache_pressure * numa_multiplier)
    
    return overhead_factor


def estimate_memory_bandwidth_impact(
    n_jobs: int,
    data_size_per_item: int,
    items_per_second_per_core: float,
    memory_bandwidth: MemoryBandwidthInfo
) -> float:
    """
    Estimate memory bandwidth saturation impact on speedup.
    
    Args:
        n_jobs: Number of parallel workers
        data_size_per_item: Size of data per work item in bytes
        items_per_second_per_core: Processing rate per core
        memory_bandwidth: Memory bandwidth information
    
    Returns:
        Slowdown factor due to bandwidth saturation (0.0 to 1.0)
        1.0 = no slowdown, 0.5 = 50% slowdown
        
    Theory:
        When multiple cores compete for memory bandwidth, they can saturate
        the memory bus. This is particularly common for memory-intensive workloads.
        
        Memory bandwidth becomes a bottleneck when:
        total_bandwidth_demand > available_bandwidth
        
    Model:
        If demand <= bandwidth: no impact (factor = 1.0)
        If demand > bandwidth: linear slowdown based on saturation ratio
    """
    if n_jobs <= 1:
        return 1.0  # No bandwidth contention with single core
    
    # Calculate memory bandwidth demand
    # Assume data is read once and written once per item (read + write)
    bytes_per_item = data_size_per_item * 2  # Read + write
    bandwidth_demand_per_core = bytes_per_item * items_per_second_per_core
    total_bandwidth_demand_gb_s = (bandwidth_demand_per_core * n_jobs) / (1024 ** 3)
    
    available_bandwidth_gb_s = memory_bandwidth.bandwidth_gb_per_sec
    
    # Calculate saturation ratio
    if total_bandwidth_demand_gb_s <= available_bandwidth_gb_s:
        # No saturation - cores get full bandwidth
        return 1.0
    
    # Bandwidth saturated - cores must share
    # Slowdown is proportional to over-subscription
    saturation_ratio = total_bandwidth_demand_gb_s / available_bandwidth_gb_s
    
    # Each core gets reduced bandwidth
    # slowdown_factor = available / demanded = 1 / saturation_ratio
    slowdown_factor = 1.0 / saturation_ratio
    
    # But we don't slow down more than 50% (other factors dominate beyond that)
    slowdown_factor = max(slowdown_factor, 0.5)
    
    return slowdown_factor


def estimate_false_sharing_overhead(
    n_jobs: int,
    return_size: int,
    cache_line_size: int
) -> float:
    """
    Estimate false sharing overhead.
    
    Args:
        n_jobs: Number of parallel workers
        return_size: Size of return objects in bytes
        cache_line_size: CPU cache line size (typically 64 bytes)
    
    Returns:
        Overhead factor (multiplicative, >= 1.0)
        
    Theory:
        False sharing occurs when multiple cores modify data that resides in
        the same cache line, causing cache line ping-ponging and invalidation.
        
        This is most likely when:
        - Small return objects (< cache line size)
        - Many workers
        - Shared data structures
        
    Model:
        For small return objects that might share cache lines, add overhead.
        Overhead increases with core count and decreases with object size.
    """
    if n_jobs <= 1:
        return 1.0  # No false sharing with single core
    
    # If return objects are large (> cache line), false sharing unlikely
    if return_size >= cache_line_size:
        return 1.0
    
    # For small objects, estimate false sharing probability
    # Multiple small objects might share cache lines
    objects_per_cache_line = cache_line_size / max(return_size, 1)
    
    # If multiple objects fit in cache line, false sharing more likely
    if objects_per_cache_line > 1:
        # Base overhead per core (1-3% typical for false sharing)
        base_overhead = 0.02
        # Scale with core count (more cores = more contention)
        overhead_factor = 1.0 + (base_overhead * (n_jobs - 1) ** 0.5)
        return overhead_factor
    
    return 1.0


def calculate_advanced_amdahl_speedup(
    total_compute_time: float,
    pickle_overhead_per_item: float,
    spawn_cost_per_worker: float,
    chunking_overhead_per_chunk: float,
    n_jobs: int,
    chunksize: int,
    total_items: int,
    data_pickle_overhead_per_item: float,
    system_topology: SystemTopology,
    data_size_per_item: int,
    return_size_per_item: int
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate realistic speedup using advanced cost modeling.
    
    This extends basic Amdahl's Law with hardware-level cost models:
    - Cache coherency overhead (L1/L2/L3 cache effects)
    - Memory bandwidth saturation (memory bus contention)
    - NUMA penalties (cross-node access overhead)
    - False sharing (cache line ping-ponging)
    
    Args:
        total_compute_time: Total serial computation time (seconds)
        pickle_overhead_per_item: Time to pickle one result (seconds)
        spawn_cost_per_worker: Time to spawn one worker process (seconds)
        chunking_overhead_per_chunk: Time per chunk for task distribution (seconds)
        n_jobs: Number of parallel workers
        chunksize: Items per chunk
        total_items: Total number of items to process
        data_pickle_overhead_per_item: Time to pickle one input data item (seconds)
        system_topology: System hardware topology information
        data_size_per_item: Size of input data per item (bytes)
        return_size_per_item: Size of return object per item (bytes)
    
    Returns:
        Tuple of (speedup, overhead_breakdown) where:
        - speedup: Estimated speedup factor (>1.0 means parallelization helps)
        - overhead_breakdown: Dict with detailed overhead components
    """
    if n_jobs <= 0 or total_compute_time <= 0:
        return 1.0, {}
    
    # Serial execution time (baseline)
    serial_time = total_compute_time
    
    # Basic parallel execution breakdown (from basic Amdahl's Law)
    spawn_overhead = spawn_cost_per_worker * n_jobs
    parallel_compute_time = total_compute_time / n_jobs
    data_ipc_overhead = data_pickle_overhead_per_item * total_items
    result_ipc_overhead = pickle_overhead_per_item * total_items
    num_chunks = max(1, (total_items + chunksize - 1) // chunksize)
    chunking_overhead = chunking_overhead_per_chunk * num_chunks
    
    # Advanced cost factors
    
    # 1. Cache coherency overhead
    cache_coherency_factor = estimate_cache_coherency_overhead(
        n_jobs=n_jobs,
        data_size_per_item=data_size_per_item,
        cache_info=system_topology.cache_info,
        numa_info=system_topology.numa_info
    )
    
    # 2. Memory bandwidth impact
    # Estimate items per second per core
    avg_time_per_item = total_compute_time / total_items if total_items > 0 else 0.01
    items_per_second_per_core = 1.0 / avg_time_per_item if avg_time_per_item > 0 else 100.0
    
    bandwidth_slowdown = estimate_memory_bandwidth_impact(
        n_jobs=n_jobs,
        data_size_per_item=data_size_per_item,
        items_per_second_per_core=items_per_second_per_core,
        memory_bandwidth=system_topology.memory_bandwidth
    )
    
    # 3. False sharing overhead
    false_sharing_factor = estimate_false_sharing_overhead(
        n_jobs=n_jobs,
        return_size=return_size_per_item,
        cache_line_size=system_topology.cache_info.cache_line_size
    )
    
    # Apply advanced cost factors to parallel compute time
    # Cache coherency and false sharing are multiplicative overheads
    adjusted_parallel_compute = parallel_compute_time * cache_coherency_factor * false_sharing_factor
    
    # Bandwidth slowdown reduces effective parallelism
    # If bandwidth is 50% saturated, effective cores = n_jobs * 0.5
    adjusted_parallel_compute = adjusted_parallel_compute / bandwidth_slowdown
    
    # Total parallel execution time with advanced costs
    parallel_time = (
        spawn_overhead +
        adjusted_parallel_compute +
        data_ipc_overhead +
        result_ipc_overhead +
        chunking_overhead
    )
    
    # Calculate speedup
    if parallel_time > 0:
        speedup = serial_time / parallel_time
        # Speedup cannot exceed n_jobs (theoretical maximum)
        speedup = min(speedup, float(n_jobs))
    else:
        speedup = 1.0
    
    # Detailed overhead breakdown
    overhead_breakdown = {
        'spawn_overhead': spawn_overhead,
        'parallel_compute': adjusted_parallel_compute,
        'data_ipc_overhead': data_ipc_overhead,
        'result_ipc_overhead': result_ipc_overhead,
        'chunking_overhead': chunking_overhead,
        'cache_coherency_factor': cache_coherency_factor,
        'bandwidth_slowdown': bandwidth_slowdown,
        'false_sharing_factor': false_sharing_factor,
        'basic_parallel_compute': parallel_compute_time,  # For comparison
    }
    
    return speedup, overhead_breakdown
