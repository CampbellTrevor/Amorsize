"""
System information module for detecting hardware and OS constraints.
"""

import os
import platform
from typing import Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


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


def get_spawn_cost() -> float:
    """
    Estimate the process spawn cost based on OS.
    
    Returns:
        Estimated spawn cost in seconds.
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


def get_available_memory() -> int:
    """
    Get available system memory in bytes.
    
    Returns:
        Available memory in bytes. Returns a large default if psutil unavailable.
    """
    if HAS_PSUTIL:
        return psutil.virtual_memory().available
    
    # Return a conservative estimate if psutil is unavailable (1GB)
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
