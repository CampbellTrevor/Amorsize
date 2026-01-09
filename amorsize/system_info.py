"""
System information module for detecting hardware and OS constraints.
"""

import os
import platform
import time
import multiprocessing
from typing import Tuple, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Global cache for spawn cost measurement
_CACHED_SPAWN_COST: Optional[float] = None


def get_physical_cores() -> int:
    """
    Get the number of physical CPU cores.
    
    Returns:
        Number of physical cores. Falls back to logical cores if psutil is unavailable.
    """
    if HAS_PSUTIL:
        # psutil can distinguish between physical and logical cores
        physical = psutil.cpu_count(logical=False)
        if physical is not None:
            return physical
    
    # Fallback to logical cores
    logical = os.cpu_count()
    return logical if logical is not None else 1


def _noop_worker(_):
    """No-op worker function for benchmarking process spawn overhead."""
    pass


def measure_spawn_cost(timeout: float = 2.0) -> float:
    """
    Measure the actual process spawn cost by benchmarking.
    
    This function spawns a single worker process that does nothing,
    measuring the total overhead. The measurement is cached globally
    to avoid repeated benchmarking.
    
    Args:
        timeout: Maximum time to wait for measurement in seconds
    
    Returns:
        Measured spawn cost in seconds, or OS-based estimate on failure
        
    Fallback Strategy:
        If benchmarking fails (e.g., multiprocessing not available,
        timeout exceeded), falls back to OS-based estimates.
    """
    global _CACHED_SPAWN_COST
    
    # Return cached value if available
    if _CACHED_SPAWN_COST is not None:
        return _CACHED_SPAWN_COST
    
    try:
        # Measure time to spawn a single no-op worker
        start = time.perf_counter()
        
        # Use context manager to ensure proper cleanup
        with multiprocessing.Pool(processes=1) as pool:
            # Submit a no-op task and wait for it
            result = pool.apply_async(_noop_worker, (None,))
            result.get(timeout=timeout)
        
        end = time.perf_counter()
        measured_cost = end - start
        
        # Cache the result
        _CACHED_SPAWN_COST = measured_cost
        return measured_cost
        
    except (Exception, TimeoutError):
        # If measurement fails, fall back to OS-based estimate
        _CACHED_SPAWN_COST = get_spawn_cost_estimate()
        return _CACHED_SPAWN_COST


def get_spawn_cost_estimate() -> float:
    """
    Estimate the process spawn cost based on OS.
    
    This is a fallback when actual measurement is not possible.
    
    Returns:
        Estimated spawn cost in seconds based on OS type
        
    Rationale:
        - Linux: Uses fork() with copy-on-write, very fast (~50ms)
        - Windows/macOS: Uses spawn, requires interpreter reload (~200ms)
        - Unknown: Conservative middle ground (~150ms)
    """
    system = platform.system()
    
    if system == "Linux":
        # Linux uses fork (Copy-on-Write) - fast startup
        return 0.05
    elif system in ("Windows", "Darwin"):
        # Windows and macOS use spawn - higher startup cost
        return 0.2
    else:
        # Conservative estimate for unknown systems
        return 0.15


def get_spawn_cost(use_benchmark: bool = False) -> float:
    """
    Get the process spawn cost, either measured or estimated.
    
    Args:
        use_benchmark: If True, measures actual spawn cost. If False,
                      uses OS-based estimate (default: False for speed)
    
    Returns:
        Spawn cost in seconds
    """
    if use_benchmark:
        return measure_spawn_cost()
    else:
        return get_spawn_cost_estimate()


def _read_cgroup_memory_limit() -> Optional[int]:
    """
    Read memory limit from cgroup (Docker/container environments).
    
    Returns:
        Memory limit in bytes, or None if not in a container or can't read
        
    Rationale:
        Docker and other containers use cgroups to limit resources.
        Without this check, we'd see the host's total memory and
        potentially spawn too many workers, causing OOM kills.
    """
    # Try cgroup v2 first (newer systems)
    cgroup_v2_path = "/sys/fs/cgroup/memory.max"
    if os.path.exists(cgroup_v2_path):
        try:
            with open(cgroup_v2_path, 'r') as f:
                value = f.read().strip()
                # "max" means no limit
                if value != "max":
                    return int(value)
        except (IOError, ValueError):
            pass
    
    # Try cgroup v1
    cgroup_v1_path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
    if os.path.exists(cgroup_v1_path):
        try:
            with open(cgroup_v1_path, 'r') as f:
                value = int(f.read().strip())
                # Very large values (near max int64) indicate no limit
                if value < (1 << 62):
                    return value
        except (IOError, ValueError):
            pass
    
    return None


def get_available_memory() -> int:
    """
    Get available system memory in bytes, respecting container limits.
    
    Returns:
        Available memory in bytes. Returns a conservative default if
        detection fails.
        
    Container Handling:
        Checks for Docker/cgroup memory limits before falling back to
        system memory. This prevents OOM kills in containerized environments.
        
    Fallback Strategy:
        1. Try cgroup limits (Docker/containers)
        2. Try psutil for system memory
        3. Return 1GB conservative default
    """
    # First, check for container memory limits
    cgroup_limit = _read_cgroup_memory_limit()
    
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        system_available = vm.available
        
        # If we're in a container, respect the lower limit
        if cgroup_limit is not None:
            return min(cgroup_limit, system_available)
        
        return system_available
    elif cgroup_limit is not None:
        # No psutil, but we have cgroup limit
        return cgroup_limit
    
    # Return a conservative estimate if detection fails (1GB)
    # Better to underestimate than cause OOM
    return 1024 * 1024 * 1024


def calculate_max_workers(physical_cores: int, estimated_job_ram: int) -> int:
    """
    Calculate maximum number of workers based on memory constraints.
    
    Args:
        physical_cores: Number of physical CPU cores
        estimated_job_ram: Estimated RAM usage per job in bytes
    
    Returns:
        Maximum number of workers
    """
    available_ram = get_available_memory()
    
    # Leave some headroom (20%) for the system
    usable_ram = int(available_ram * 0.8)
    
    # Calculate memory-based limit
    if estimated_job_ram > 0:
        memory_limit = max(1, usable_ram // estimated_job_ram)
    else:
        memory_limit = physical_cores
    
    return min(physical_cores, memory_limit)


def get_system_info() -> Tuple[int, float, int]:
    """
    Get all relevant system information.
    
    Returns:
        Tuple of (physical_cores, spawn_cost, available_memory)
    """
    return (
        get_physical_cores(),
        get_spawn_cost(),
        get_available_memory()
    )
