"""
System information module for detecting hardware and OS constraints.
"""

import os
import platform
import subprocess
import sys
import time
import multiprocessing
import threading
from typing import Tuple, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Global cache for physical core count detection
_CACHED_PHYSICAL_CORES: Optional[int] = None
_physical_cores_lock = threading.Lock()

# Global cache for spawn cost measurement
_CACHED_SPAWN_COST: Optional[float] = None
_spawn_cost_lock = threading.Lock()

# Global cache for chunking overhead measurement
_CACHED_CHUNKING_OVERHEAD: Optional[float] = None
_chunking_overhead_lock = threading.Lock()

# Minimum reasonable marginal cost threshold (1ms)
# Below this, we assume measurement noise and fall back to single-worker measurement
MIN_REASONABLE_MARGINAL_COST = 0.001

# Spawn cost constants (in seconds) for different start methods
SPAWN_COST_FORK = 0.015        # fork with Copy-on-Write (~15ms)
SPAWN_COST_SPAWN = 0.2         # full interpreter initialization (~200ms)
SPAWN_COST_FORKSERVER = 0.075  # server process + fork (~75ms)

# Default chunking overhead estimate (in seconds per chunk)
# This is used as a fallback when measurement fails
DEFAULT_CHUNKING_OVERHEAD = 0.0005  # 0.5ms per chunk


def _clear_physical_cores_cache():
    """
    Clear the cached physical core count.
    
    This is primarily for testing purposes to ensure tests don't
    interfere with each other's cached values.
    
    Thread-safe: Uses lock to prevent race conditions.
    """
    global _CACHED_PHYSICAL_CORES
    with _physical_cores_lock:
        _CACHED_PHYSICAL_CORES = None


def _clear_spawn_cost_cache():
    """
    Clear the cached spawn cost measurement.
    
    This is primarily for testing purposes to ensure tests don't
    interfere with each other's cached values.
    
    Thread-safe: Uses lock to prevent race conditions.
    """
    global _CACHED_SPAWN_COST
    with _spawn_cost_lock:
        _CACHED_SPAWN_COST = None


def _clear_chunking_overhead_cache():
    """
    Clear the cached chunking overhead measurement.
    
    This is primarily for testing purposes to ensure tests don't
    interfere with each other's cached values.
    
    Thread-safe: Uses lock to prevent race conditions.
    """
    global _CACHED_CHUNKING_OVERHEAD
    with _chunking_overhead_lock:
        _CACHED_CHUNKING_OVERHEAD = None


def _parse_proc_cpuinfo() -> Optional[int]:
    """
    Parse /proc/cpuinfo to determine physical core count on Linux.
    
    Returns:
        Number of physical cores, or None if parsing fails
        
    Algorithm:
        Counts unique (physical_id, core_id) pairs in /proc/cpuinfo.
        This gives the actual number of physical cores, excluding hyperthreading.
    """
    try:
        if not os.path.exists('/proc/cpuinfo'):
            return None
        
        cores = set()
        current_physical_id = None
        current_core_id = None
        
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                line = line.strip()
                
                # Reset IDs when starting a new processor entry
                if line.startswith('processor'):
                    # Save the previous processor's core info if we have both IDs
                    if current_physical_id is not None and current_core_id is not None:
                        cores.add((current_physical_id, current_core_id))
                    # Reset for new processor entry
                    current_physical_id = None
                    current_core_id = None
                elif line.startswith('physical id'):
                    current_physical_id = line.split(':')[1].strip()
                elif line.startswith('core id'):
                    current_core_id = line.split(':')[1].strip()
            
            # Don't forget the last processor entry
            if current_physical_id is not None and current_core_id is not None:
                cores.add((current_physical_id, current_core_id))
        
        if cores:
            return len(cores)
        
        return None
    except (IOError, ValueError, IndexError):
        return None


def _parse_lscpu() -> Optional[int]:
    """
    Use lscpu command to determine physical core count on Linux.
    
    Returns:
        Number of physical cores, or None if command fails
        
    Note:
        This is a secondary fallback after /proc/cpuinfo parsing.
        lscpu is part of util-linux and should be available on most Linux systems.
    """
    try:
        # Run lscpu and capture output
        result = subprocess.run(
            ['lscpu', '-p=Core,Socket'],
            capture_output=True,
            text=True,
            timeout=1.0
        )
        
        if result.returncode != 0:
            return None
        
        # Parse the output to count unique (socket, core) pairs
        cores = set()
        for line in result.stdout.split('\n'):
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            parts = line.split(',')
            if len(parts) >= 2:
                core_id = parts[0].strip()
                socket_id = parts[1].strip()
                cores.add((socket_id, core_id))
        
        if cores:
            return len(cores)
        
        return None
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired, ValueError):
        return None


def get_physical_cores() -> int:
    """
    Get the number of physical CPU cores.
    
    The physical core count is cached globally after first detection since
    it's a system constant that never changes during program execution.
    Thread-safe: Uses lock to prevent concurrent detection.
    
    Returns:
        Number of physical cores, using the best available detection method
        
    Detection Strategy (in order of preference):
        1. psutil (most reliable, cross-platform)
        2. /proc/cpuinfo parsing (Linux, no dependencies)
        3. lscpu command (Linux, secondary fallback)
        4. Logical cores / 2 (conservative estimate for hyperthreading)
        5. 1 core (absolute fallback)
        
    Rationale:
        For CPU-bound tasks, using logical cores (with hyperthreading) can lead
        to over-subscription and worse performance. Physical cores provide better
        parallelization characteristics.
        
    Performance:
        Cached globally after first call to eliminate redundant system calls,
        file I/O, and subprocess spawns on subsequent calls. This is especially
        beneficial when multiple optimizations occur in the same program.
    """
    global _CACHED_PHYSICAL_CORES
    
    # Quick check without lock (optimization for common case)
    if _CACHED_PHYSICAL_CORES is not None:
        return _CACHED_PHYSICAL_CORES
    
    # Acquire lock for detection
    with _physical_cores_lock:
        # Double-check after acquiring lock (another thread may have detected)
        if _CACHED_PHYSICAL_CORES is not None:
            return _CACHED_PHYSICAL_CORES
        
        # Perform detection (only one thread reaches here)
        physical_cores = None
        
        # Strategy 1: Use psutil if available (best method)
        if HAS_PSUTIL:
            # psutil can distinguish between physical and logical cores
            physical = psutil.cpu_count(logical=False)
            if physical is not None:
                physical_cores = physical
        
        # Strategy 2: Try /proc/cpuinfo on Linux (no dependencies)
        if physical_cores is None and platform.system() == "Linux":
            physical = _parse_proc_cpuinfo()
            if physical is not None:
                physical_cores = physical
            else:
                # Strategy 3: Try lscpu command on Linux (secondary fallback)
                physical = _parse_lscpu()
                if physical is not None:
                    physical_cores = physical
        
        # Strategy 4: Conservative estimate - assume hyperthreading (logical / 2)
        # This is better than using all logical cores for CPU-bound tasks
        if physical_cores is None:
            logical = os.cpu_count()
            if logical is not None and logical > 1:
                # Assume hyperthreading is enabled (common on modern CPUs)
                # Divide by 2 to get approximate physical core count
                physical_cores = max(1, logical // 2)
        
        # Strategy 5: Absolute fallback
        if physical_cores is None:
            physical_cores = 1
        
        # Cache the result
        _CACHED_PHYSICAL_CORES = physical_cores
        return physical_cores


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
    Thread-safe: Uses lock to prevent concurrent measurements.
    
    Enhanced with quality validation to ensure reliable measurements across
    diverse system conditions (similar to chunking overhead measurement).
    
    Args:
        timeout: Maximum time to wait for measurement in seconds
    
    Returns:
        Measured per-worker spawn cost in seconds, or OS-based estimate on failure
        
    Algorithm:
        1. Measure time to create pool with 1 worker
        2. Measure time to create pool with 2 workers
        3. Calculate marginal cost: (time_2_workers - time_1_worker) / 1
        4. Validate measurement quality with multiple criteria
        5. Use intelligent fallback if measurement is unreliable
        
        This isolates the per-worker cost from fixed pool initialization overhead.
        
    Quality Validation:
        - Check 1: Reasonable range based on start method
        - Check 2: Signal strength (2-worker measurement significantly larger)
        - Check 3: Consistency with start method expectations
        - Check 4: Overhead fraction validation
        
    Fallback Strategy:
        If benchmarking fails or produces unreliable results, falls back to
        OS-based estimates based on the multiprocessing start method.
        
    Thread Safety:
        Uses a lock to ensure only one thread performs the measurement. If
        multiple threads call this function simultaneously, the first one
        performs the measurement while others wait for the result.
    """
    global _CACHED_SPAWN_COST
    
    # Quick check without lock (optimization for common case)
    if _CACHED_SPAWN_COST is not None:
        return _CACHED_SPAWN_COST
    
    # Acquire lock for measurement
    with _spawn_cost_lock:
        # Double-check after acquiring lock (another thread may have measured)
        if _CACHED_SPAWN_COST is not None:
            return _CACHED_SPAWN_COST
        
        # Perform measurement (only one thread reaches here)
        # Get fallback value early for quality checks
        fallback_estimate = get_spawn_cost_estimate()
        
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
            
            # Enhanced validation: Check multiple quality criteria
            # If marginal cost is positive and reasonable, use it with validation
            if marginal_cost > MIN_REASONABLE_MARGINAL_COST:
                per_worker_cost = marginal_cost
                
                # Quality check 1: Reasonable range based on start method
                # fork: 1ms to 100ms, spawn: 50ms to 1000ms, forkserver: 10ms to 500ms
                start_method = get_multiprocessing_start_method()
                if start_method == 'fork':
                    min_bound, max_bound = 0.001, 0.1  # 1ms to 100ms
                elif start_method == 'spawn':
                    min_bound, max_bound = 0.05, 1.0   # 50ms to 1000ms
                elif start_method == 'forkserver':
                    min_bound, max_bound = 0.01, 0.5   # 10ms to 500ms
                else:
                    # Unknown start method - use conservative bounds
                    min_bound, max_bound = 0.001, 1.0
                
                if not (min_bound <= per_worker_cost <= max_bound):
                    # Outside reasonable bounds for this start method
                    _CACHED_SPAWN_COST = fallback_estimate
                    return fallback_estimate
                
                # Quality check 2: Signal strength validation
                # 2-worker measurement should be at least 10% longer than 1-worker
                # This ensures we're measuring real spawn cost, not noise
                if time_2_workers < time_1_worker * 1.1:
                    # Signal too weak - likely measurement noise
                    _CACHED_SPAWN_COST = fallback_estimate
                    return fallback_estimate
                
                # Quality check 3: Consistency with start method expectations
                # Measured value should be within 10x of the expected value
                # This catches measurements that are wildly off
                if not (fallback_estimate / 10 <= per_worker_cost <= fallback_estimate * 10):
                    # Measurement inconsistent with expectations
                    _CACHED_SPAWN_COST = fallback_estimate
                    return fallback_estimate
                
                # Quality check 4: Overhead fraction validation
                # Marginal cost should be reasonable fraction of 2-worker time
                # If marginal cost > 90% of total time, something is wrong
                if marginal_cost > time_2_workers * 0.9:
                    # Overhead seems unrealistically high relative to total
                    _CACHED_SPAWN_COST = fallback_estimate
                    return fallback_estimate
                
                # All quality checks passed - use measured value
                _CACHED_SPAWN_COST = per_worker_cost
                return per_worker_cost
            else:
                # Marginal cost too small or negative - fall back to 1-worker measurement
                # But validate it first
                if MIN_REASONABLE_MARGINAL_COST <= time_1_worker <= max(0.1, fallback_estimate * 5):
                    # 1-worker measurement seems reasonable
                    _CACHED_SPAWN_COST = time_1_worker
                    return time_1_worker
                else:
                    # Even 1-worker measurement seems unreliable
                    _CACHED_SPAWN_COST = fallback_estimate
                    return fallback_estimate
            
        except (OSError, TimeoutError, ValueError, multiprocessing.ProcessError):
            # If measurement fails, fall back to OS-based estimate
            # OSError: System-level issues (e.g., resource exhaustion)
            # TimeoutError: Benchmark took too long
            # ValueError: Invalid parameter values
            # ProcessError: Multiprocessing-specific failures
            _CACHED_SPAWN_COST = fallback_estimate
            return fallback_estimate


def _minimal_worker(x):
    """Minimal no-op worker function for benchmarking chunking overhead."""
    return x


def measure_chunking_overhead(timeout: float = 2.0) -> float:
    """
    Measure the per-chunk overhead for task distribution in multiprocessing.Pool.
    
    This function measures the marginal cost of task distribution overhead by
    comparing execution with different chunk sizes. The overhead comes from:
    - Queue operations for task distribution
    - Context switches between workers
    - Task scheduling and management
    
    The measurement is cached globally to avoid repeated benchmarking.
    Thread-safe: Uses lock to prevent concurrent measurements.
    
    Args:
        timeout: Maximum time to wait for measurement in seconds
    
    Returns:
        Measured per-chunk overhead in seconds, or default estimate on failure
        
    Algorithm:
        1. Execute workload with large chunks (fewer chunks, less overhead)
        2. Execute workload with small chunks (more chunks, more overhead)
        3. Calculate marginal cost: (time_small - time_large) / (chunks_small - chunks_large)
        4. Validate measurement quality with multiple criteria
        5. Use intelligent fallback if measurement is unreliable
        
        This isolates the per-chunk overhead from the actual computation time.
        
    Improvements:
        - Multiple validation checks for measurement quality
        - Detects and handles measurement noise
        - Adaptive chunk size selection
        - More robust fallback strategies
        
    Fallback Strategy:
        If benchmarking fails or produces unreliable results, falls back to
        the default estimate (0.5ms per chunk).
        
    Thread Safety:
        Uses a lock to ensure only one thread performs the measurement. If
        multiple threads call this function simultaneously, the first one
        performs the measurement while others wait for the result.
    """
    global _CACHED_CHUNKING_OVERHEAD
    
    # Quick check without lock (optimization for common case)
    if _CACHED_CHUNKING_OVERHEAD is not None:
        return _CACHED_CHUNKING_OVERHEAD
    
    # Acquire lock for measurement
    with _chunking_overhead_lock:
        # Double-check after acquiring lock (another thread may have measured)
        if _CACHED_CHUNKING_OVERHEAD is not None:
            return _CACHED_CHUNKING_OVERHEAD
        
        # Perform measurement (only one thread reaches here)
        try:
            # Use 2 workers for consistency with real use cases
            n_workers = 2
            
            # Use a reasonable workload size
            total_items = 1000
            data = range(total_items)
            
            # Test with large chunks (fewer chunks, less overhead)
            # Use chunks of 100 items -> 10 chunks
            large_chunksize = 100
            num_large_chunks = (total_items + large_chunksize - 1) // large_chunksize
            
            start_large = time.perf_counter()
            with multiprocessing.Pool(processes=n_workers) as pool:
                list(pool.map(_minimal_worker, data, chunksize=large_chunksize))
            end_large = time.perf_counter()
            time_large = end_large - start_large
            
            # Test with small chunks (more chunks, more overhead)
            # Use chunks of 10 items -> 100 chunks
            small_chunksize = 10
            num_small_chunks = (total_items + small_chunksize - 1) // small_chunksize
            
            start_small = time.perf_counter()
            with multiprocessing.Pool(processes=n_workers) as pool:
                list(pool.map(_minimal_worker, data, chunksize=small_chunksize))
            end_small = time.perf_counter()
            time_small = end_small - start_small
            
            # Calculate marginal cost per chunk
            # Difference in execution time divided by difference in number of chunks
            time_diff = time_small - time_large
            chunk_diff = num_small_chunks - num_large_chunks
            
            # Enhanced validation: Check multiple quality criteria
            if chunk_diff > 0 and time_diff > 0:
                per_chunk_overhead = time_diff / chunk_diff
                
                # Quality check 1: Overhead should be positive and reasonable (< 10ms per chunk)
                if not (0 < per_chunk_overhead < 0.01):
                    _CACHED_CHUNKING_OVERHEAD = DEFAULT_CHUNKING_OVERHEAD
                    return DEFAULT_CHUNKING_OVERHEAD
                
                # Quality check 2: Measurement should show clear signal
                # The small-chunk run should take at least 5% longer than large-chunk
                # This ensures we're measuring real overhead, not noise
                if time_small < time_large * 1.05:
                    # Signal too weak - likely measurement noise
                    _CACHED_CHUNKING_OVERHEAD = DEFAULT_CHUNKING_OVERHEAD
                    return DEFAULT_CHUNKING_OVERHEAD
                
                # Quality check 3: Per-chunk overhead should be reasonable fraction of total time
                # If per-chunk overhead * num_chunks > 50% of total time, something is wrong
                estimated_total_overhead = per_chunk_overhead * num_small_chunks
                if estimated_total_overhead > time_small * 0.5:
                    # Overhead seems unrealistically high
                    _CACHED_CHUNKING_OVERHEAD = DEFAULT_CHUNKING_OVERHEAD
                    return DEFAULT_CHUNKING_OVERHEAD
                
                # Quality check 4: The overhead should be in a reasonable range
                # Based on empirical observations, overhead is typically 0.1ms to 5ms per chunk
                if not (0.0001 < per_chunk_overhead < 0.005):
                    # Outside reasonable bounds - use default
                    _CACHED_CHUNKING_OVERHEAD = DEFAULT_CHUNKING_OVERHEAD
                    return DEFAULT_CHUNKING_OVERHEAD
                
                # All quality checks passed - use measured value
                _CACHED_CHUNKING_OVERHEAD = per_chunk_overhead
                return per_chunk_overhead
            
            # If measurement conditions not met, fall back to default
            _CACHED_CHUNKING_OVERHEAD = DEFAULT_CHUNKING_OVERHEAD
            return DEFAULT_CHUNKING_OVERHEAD
            
        except (OSError, TimeoutError, ValueError, multiprocessing.ProcessError):
            # If measurement fails, fall back to default estimate
            _CACHED_CHUNKING_OVERHEAD = DEFAULT_CHUNKING_OVERHEAD
            return DEFAULT_CHUNKING_OVERHEAD


def get_chunking_overhead(use_benchmark: bool = True) -> float:
    """
    Get the per-chunk overhead, either measured or estimated.
    
    Args:
        use_benchmark: If True, measures actual chunking overhead. If False,
                      uses default estimate. Default is True for accuracy
                      as measurements are fast (~10ms) and cached globally.
    
    Returns:
        Chunking overhead in seconds per chunk
    """
    if use_benchmark:
        return measure_chunking_overhead()
    else:
        return DEFAULT_CHUNKING_OVERHEAD


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


def get_spawn_cost(use_benchmark: bool = True) -> float:
    """
    Get the process spawn cost, either measured or estimated.
    
    Args:
        use_benchmark: If True, measures actual spawn cost. If False,
                      uses start-method-based estimate. Default is True
                      for accuracy as measurements are fast (~15ms) and
                      cached globally.
    
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


def _read_cgroup_v2_limit(base_path: str) -> Optional[int]:
    """
    Read memory limit from cgroup v2 unified hierarchy.
    
    Args:
        base_path: Base path to check (e.g., "/sys/fs/cgroup")
    
    Returns:
        Memory limit in bytes, or None if not found or invalid
        
    Algorithm:
        1. Check memory.max (hard limit)
        2. Check memory.high (soft limit - use if lower than max)
        3. Return the most restrictive limit
        
    Note:
        In cgroup v2, memory.high is a "soft" limit where the kernel
        will throttle but not kill. memory.max is the "hard" limit where
        OOM kills happen. We respect both to be conservative.
    """
    max_limit = None
    high_limit = None
    
    # Check memory.max (hard limit)
    max_path = os.path.join(base_path, "memory.max")
    if os.path.exists(max_path):
        try:
            with open(max_path, 'r') as f:
                value = f.read().strip()
                # "max" means no limit
                if value != "max":
                    max_limit = int(value)
        except (IOError, ValueError):
            pass
    
    # Check memory.high (soft limit)
    high_path = os.path.join(base_path, "memory.high")
    if os.path.exists(high_path):
        try:
            with open(high_path, 'r') as f:
                value = f.read().strip()
                # "max" means no limit
                if value != "max":
                    high_limit = int(value)
        except (IOError, ValueError):
            pass
    
    # Return the most restrictive limit
    if max_limit is not None and high_limit is not None:
        return min(max_limit, high_limit)
    elif max_limit is not None:
        return max_limit
    elif high_limit is not None:
        return high_limit
    
    return None


def _get_cgroup_path() -> Optional[str]:
    """
    Get the cgroup path for the current process from /proc/self/cgroup.
    
    Returns:
        Cgroup path for the current process, or None if not found
        
    Rationale:
        In modern container environments, cgroup paths can be hierarchical.
        We need to read /proc/self/cgroup to find where our process is
        actually located in the cgroup hierarchy.
        
    Example /proc/self/cgroup formats:
        cgroup v2: 0::/docker/abc123...
        cgroup v1: 3:memory:/docker/abc123...
    """
    try:
        with open('/proc/self/cgroup', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(':')
                if len(parts) >= 3:
                    # cgroup v2 format: 0::/path
                    if parts[0] == '0' and parts[1] == '':
                        return parts[2]
                    # cgroup v1 format: N:controller:/path
                    elif 'memory' in parts[1]:
                        return parts[2]
    except (IOError, ValueError):
        pass
    
    return None


def _read_cgroup_memory_limit() -> Optional[int]:
    """
    Read memory limit from cgroup (Docker/container environments).
    
    Returns:
        Memory limit in bytes, or None if not in a container or can't read
        
    Rationale:
        Docker and other containers use cgroups to limit resources.
        Without this check, we'd see the host's total memory and
        potentially spawn too many workers, causing OOM kills.
        
    Enhanced Detection (Iteration 69):
        - Supports cgroup v2 unified hierarchy with hierarchical paths
        - Respects both memory.max (hard) and memory.high (soft) limits
        - Properly handles /proc/self/cgroup path resolution
        - Falls back gracefully through multiple strategies
        
    Detection Strategy:
        1. Try cgroup v2 with process-specific path (most accurate)
        2. Try cgroup v2 at root (simple containers)
        3. Try cgroup v1 (legacy systems)
    """
    # Strategy 1: cgroup v2 with process-specific path
    # This handles hierarchical cgroup paths in modern containers
    cgroup_path = _get_cgroup_path()
    if cgroup_path:
        # Try to read from the process-specific cgroup path
        # Handle both absolute paths and relative paths
        if cgroup_path.startswith('/'):
            cgroup_path = cgroup_path[1:]  # Remove leading slash
        
        full_path = os.path.join("/sys/fs/cgroup", cgroup_path)
        if os.path.exists(full_path):
            limit = _read_cgroup_v2_limit(full_path)
            if limit is not None:
                return limit
    
    # Strategy 2: cgroup v2 at root (simple containers like Docker with unified hierarchy)
    limit = _read_cgroup_v2_limit("/sys/fs/cgroup")
    if limit is not None:
        return limit
    
    # Strategy 3: cgroup v1 (legacy systems)
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
    
    # Strategy 4: cgroup v1 with process-specific path
    if cgroup_path:
        if cgroup_path.startswith('/'):
            cgroup_path = cgroup_path[1:]
        
        full_path = os.path.join("/sys/fs/cgroup/memory", cgroup_path, "memory.limit_in_bytes")
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    value = int(f.read().strip())
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


def get_swap_usage() -> Tuple[float, int, int]:
    """
    Get current swap memory usage information.
    
    Returns:
        Tuple of (swap_percent, swap_used_bytes, swap_total_bytes) where:
        - swap_percent: Percentage of swap being used (0-100)
        - swap_used_bytes: Amount of swap currently used in bytes
        - swap_total_bytes: Total swap space available in bytes
        
        Returns (0.0, 0, 0) if psutil is not available or swap detection fails.
        
    Rationale:
        When a system is actively using swap, it indicates memory pressure.
        Spawning additional workers in this state can cause severe performance
        degradation due to disk I/O thrashing as the kernel swaps memory pages
        to/from disk.
        
    Note:
        Some systems (like containers) may have no swap configured, which is
        normal and not an error condition.
    """
    if not HAS_PSUTIL:
        return 0.0, 0, 0
    
    try:
        swap = psutil.swap_memory()
        return swap.percent, swap.used, swap.total
    except (AttributeError, OSError):
        # AttributeError: Method not available on this platform
        # OSError: System call failed
        return 0.0, 0, 0


def calculate_max_workers(physical_cores: int, estimated_job_ram: int) -> int:
    """
    Calculate maximum number of workers based on memory constraints.
    
    Enhanced in Iteration 70 to account for swap usage. When the system
    is actively swapping, worker count is reduced to prevent disk thrashing.
    
    Args:
        physical_cores: Number of physical CPU cores
        estimated_job_ram: Estimated RAM usage per job in bytes
    
    Returns:
        Maximum number of workers, potentially reduced if system is swapping
        
    Swap-Aware Logic:
        - If swap usage < 10%: No adjustment (normal operation)
        - If swap usage 10-50%: Reduce workers by 25% (moderate pressure)
        - If swap usage > 50%: Reduce workers by 50% (severe pressure)
        
        This prevents spawning too many workers when the system is already
        under memory pressure, which would cause severe performance degradation.
    """
    available_ram = get_available_memory()
    
    # Leave some headroom (20%) for the system
    usable_ram = int(available_ram * 0.8)
    
    # Calculate memory-based limit
    if estimated_job_ram > 0:
        memory_limit = max(1, usable_ram // estimated_job_ram)
    else:
        memory_limit = physical_cores
    
    # Apply swap-aware adjustment
    base_workers = min(physical_cores, memory_limit)
    
    # Check swap usage
    swap_percent, _, _ = get_swap_usage()
    
    if swap_percent > 50.0:
        # Severe swap usage - reduce workers by 50%
        adjusted_workers = max(1, base_workers // 2)
    elif swap_percent > 10.0:
        # Moderate swap usage - reduce workers by 25%
        adjusted_workers = max(1, int(base_workers * 0.75))
    else:
        # No significant swap usage - use full worker count
        adjusted_workers = base_workers
    
    return adjusted_workers


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
