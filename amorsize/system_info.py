"""
System information module for detecting hardware and OS constraints.
"""

import os
import platform
import sys
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

# Minimum reasonable marginal cost threshold (1ms)
# Below this, we assume measurement noise and fall back to single-worker measurement
MIN_REASONABLE_MARGINAL_COST = 0.001

# Spawn cost constants (in seconds) for different start methods
SPAWN_COST_FORK = 0.015        # fork with Copy-on-Write (~15ms)
SPAWN_COST_SPAWN = 0.2         # full interpreter initialization (~200ms)
SPAWN_COST_FORKSERVER = 0.075  # server process + fork (~75ms)


def _clear_spawn_cost_cache():
    """
    Clear the cached spawn cost measurement.
    
    This is primarily for testing purposes to ensure tests don't
    interfere with each other's cached values.
    """
    global _CACHED_SPAWN_COST
    _CACHED_SPAWN_COST = None


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
    Measure the actual per-worker process spawn cost by benchmarking.
    
    This function measures the marginal cost of spawning additional workers
    by comparing pool creation times with different worker counts. This gives
    a more accurate per-worker cost than measuring a single worker pool.
    
    The measurement is cached globally to avoid repeated benchmarking.
    
    Args:
        timeout: Maximum time to wait for measurement in seconds
    
    Returns:
        Measured per-worker spawn cost in seconds, or OS-based estimate on failure
        
    Algorithm:
        1. Measure time to create pool with 1 worker
        2. Measure time to create pool with 2 workers
        3. Calculate marginal cost: (time_2_workers - time_1_worker) / 1
        
        This isolates the per-worker cost from fixed pool initialization overhead.
        
    Fallback Strategy:
        If benchmarking fails (e.g., multiprocessing not available,
        timeout exceeded), falls back to OS-based estimates.
    """
    global _CACHED_SPAWN_COST
    
    # Return cached value if available
    if _CACHED_SPAWN_COST is not None:
        return _CACHED_SPAWN_COST
    
    try:
        # Measure time to create pool with 1 worker
        start_1 = time.perf_counter()
        with multiprocessing.Pool(processes=1) as pool:
            result = pool.apply_async(_noop_worker, (None,))
            result.get(timeout=timeout)
        end_1 = time.perf_counter()
        time_1_worker = end_1 - start_1
        
        # Measure time to create pool with 2 workers
        start_2 = time.perf_counter()
        with multiprocessing.Pool(processes=2) as pool:
            # Submit tasks to ensure both workers are initialized
            results = [pool.apply_async(_noop_worker, (None,)) for _ in range(2)]
            for result in results:
                result.get(timeout=timeout)
        end_2 = time.perf_counter()
        time_2_workers = end_2 - start_2
        
        # Calculate marginal cost per worker
        # This removes fixed pool initialization overhead
        marginal_cost = time_2_workers - time_1_worker
        
        # Ensure we have a reasonable positive value
        # If marginal cost is negative or tiny, fall back to the 1-worker measurement
        if marginal_cost > MIN_REASONABLE_MARGINAL_COST:
            per_worker_cost = marginal_cost
        else:
            # Fallback: use the single worker measurement
            per_worker_cost = time_1_worker
        
        # Cache the result
        _CACHED_SPAWN_COST = per_worker_cost
        return per_worker_cost
        
    except (OSError, TimeoutError, ValueError, multiprocessing.ProcessError) as e:
        # If measurement fails, fall back to OS-based estimate
        # OSError: System-level issues (e.g., resource exhaustion)
        # TimeoutError: Benchmark took too long
        # ValueError: Invalid parameter values
        # ProcessError: Multiprocessing-specific failures
        _CACHED_SPAWN_COST = get_spawn_cost_estimate()
        return _CACHED_SPAWN_COST


def get_multiprocessing_start_method() -> str:
    """
    Get the current multiprocessing start method.
    
    Returns:
        The current start method name ('fork', 'spawn', or 'forkserver')
        
    Rationale:
        The start method determines how child processes are created:
        - 'fork': Uses fork() (fast, Linux/Unix default, not available on Windows)
        - 'spawn': Starts fresh interpreter (slow, Windows/macOS default, safest)
        - 'forkserver': Uses a server process (middle ground, Unix only)
        
    Note:
        Users can override the default with multiprocessing.set_start_method().
        This function detects the actual method being used, not the OS default.
    """
    # Try to get the start method, allowing None if not yet initialized
    method = None
    try:
        method = multiprocessing.get_start_method()
    except RuntimeError:
        # Context not initialized yet
        method = multiprocessing.get_start_method(allow_none=True)
    
    # If still None, return the OS default
    if method is None:
        return _get_default_start_method()
    
    return method


def _get_default_start_method() -> str:
    """
    Get the default multiprocessing start method for the current OS.
    
    Returns:
        Default start method name for the current platform
        
    OS Defaults:
        - Linux/Unix: 'fork'
        - Windows: 'spawn'
        - macOS (Python >= 3.8): 'spawn'
        - macOS (Python < 3.8): 'fork'
    """
    system = platform.system()
    
    if system == "Windows":
        return "spawn"
    elif system == "Darwin":
        # macOS changed default from fork to spawn in Python 3.8
        if sys.version_info >= (3, 8):
            return "spawn"
        else:
            return "fork"
    else:
        # Linux and other Unix systems default to fork
        return "fork"


def get_spawn_cost_estimate() -> float:
    """
    Estimate the process spawn cost based on actual start method.
    
    This is a fallback when actual measurement is not possible.
    
    Returns:
        Estimated spawn cost in seconds based on start method
        
    Rationale:
        - fork: Uses fork() with copy-on-write, very fast (~10-15ms measured)
        - spawn: Starts fresh interpreter, requires module imports (~200ms)
        - forkserver: Server process + fork, middle ground (~50-100ms)
        
    Important:
        This function now checks the ACTUAL start method being used,
        not just the OS. A user can set spawn on Linux, making spawn
        cost 13x higher than the old OS-based estimate would suggest.
    """
    start_method = get_multiprocessing_start_method()
    
    if start_method == "fork":
        # Fork with Copy-on-Write - very fast
        return SPAWN_COST_FORK
    elif start_method == "spawn":
        # Spawn requires full interpreter initialization
        return SPAWN_COST_SPAWN
    elif start_method == "forkserver":
        # Forkserver uses a pre-started server process, faster than spawn
        # but slower than direct fork
        return SPAWN_COST_FORKSERVER
    else:
        # Unknown method - use conservative estimate (halfway between fork and spawn)
        return (SPAWN_COST_FORK + SPAWN_COST_SPAWN) / 2


def get_spawn_cost(use_benchmark: bool = False) -> float:
    """
    Get the process spawn cost, either measured or estimated.
    
    Args:
        use_benchmark: If True, measures actual spawn cost. If False,
                      uses start-method-based estimate (default: False for speed)
    
    Returns:
        Spawn cost in seconds
    """
    if use_benchmark:
        return measure_spawn_cost()
    else:
        return get_spawn_cost_estimate()


def check_start_method_mismatch() -> Tuple[bool, Optional[str]]:
    """
    Check if the current start method differs from the OS default.
    
    Returns:
        Tuple of (is_mismatch, warning_message) where:
        - is_mismatch: True if start method differs from OS default
        - warning_message: Explanation of the mismatch (None if no mismatch)
        
    Use Case:
        This detects when users have explicitly set a non-default start method,
        which can significantly affect spawn costs and optimization decisions.
        
        Example: User sets 'spawn' on Linux for safety reasons, but this makes
        spawning 13x slower (200ms vs 15ms), changing optimal parallelization.
    """
    actual = get_multiprocessing_start_method()
    default = _get_default_start_method()
    
    if actual != default:
        if actual == "spawn" and default == "fork":
            return True, (
                f"Using '{actual}' start method on a system that defaults to '{default}'. "
                f"This increases spawn cost from ~{int(SPAWN_COST_FORK * 1000)}ms to ~{int(SPAWN_COST_SPAWN * 1000)}ms per worker. "
                f"Consider using 'fork' or 'forkserver' for better performance."
            )
        elif actual == "fork" and default == "spawn":
            return True, (
                f"Using '{actual}' start method on a system that defaults to '{default}'. "
                f"This is faster but may have issues with threads or locks. "
                f"Spawn cost estimates adjusted accordingly (~{int(SPAWN_COST_FORK * 1000)}ms vs ~{int(SPAWN_COST_SPAWN * 1000)}ms)."
            )
        else:
            return True, (
                f"Using '{actual}' start method instead of OS default '{default}'. "
                f"Spawn cost estimates have been adjusted."
            )
    
    return False, None


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
