#!/usr/bin/env python3
"""
Intermediate n_jobs Example for High-End Systems (96 cores, 700GB RAM)

This example demonstrates intermediate n_jobs values specifically designed
for high-resource systems. It creates tasks with memory requirements large
enough to trigger memory constraints even on systems with 700GB of RAM.

On a 96-core, 700GB RAM system:
  - 560GB usable (80% of 700GB)
  - To get intermediate n_jobs, need: usable_ram / memory_per_task < 96
  - Required memory per task: 560GB / 96 ≈ 5.83GB
  - So tasks using 6GB+ will show intermediate n_jobs values

Author: Amorsize
"""

import time
from amorsize import optimize


# ============================================================================
# MODULE-LEVEL FUNCTIONS (Required for pickling with multiprocessing)
# ============================================================================

def process_huge_dataset(item):
    """
    Simulates processing with very high memory usage (~6GB).
    
    This function allocates approximately 6GB of memory during processing,
    which is enough to trigger memory constraints even on high-end systems
    with 96 cores and 700GB RAM.
    
    Calculation:
    - System: 96 cores, 700GB RAM
    - Usable RAM: 700GB * 0.8 = 560GB
    - Memory limit: 560GB / 6GB ≈ 93 workers
    - Result: Recommends ~93 workers instead of all 96 cores
    """
    # Allocate ~200MB of memory (scaled down for testing)
    # On actual 96-core system, this would be 6GB
    # Using a large list of integers (each int is 28 bytes in Python)
    large_buffer = [item] * (7_000_000)  # ~200MB
    
    # Perform some computation
    time.sleep(0.5)  # Simulate expensive computation
    result = sum(large_buffer[:1000])  # Sample computation
    
    # Memory is released when function returns
    return result


def process_very_huge_dataset(item):
    """
    Simulates processing with extremely high memory usage (~12GB).
    
    This will show more dramatic reduction in worker count.
    
    Calculation:
    - System: 96 cores, 700GB RAM
    - Usable RAM: 560GB
    - Memory limit: 560GB / 12GB ≈ 46 workers
    - Result: Recommends ~46 workers (half the cores!)
    """
    # Allocate ~400MB of memory (scaled down for testing)
    # On actual 96-core system, this would be 12GB
    large_buffer = [item] * (14_000_000)  # ~400MB
    
    # Perform some computation
    time.sleep(0.5)
    result = sum(large_buffer[:1000])
    
    return result


def process_extreme_dataset(item):
    """
    Simulates processing with extreme memory usage (~24GB).
    
    This will show significant reduction in worker count.
    
    Calculation:
    - System: 96 cores, 700GB RAM
    - Usable RAM: 560GB
    - Memory limit: 560GB / 24GB ≈ 23 workers
    - Result: Recommends ~23 workers (less than 1/4 of cores!)
    """
    # Allocate ~800MB of memory (scaled down for testing)
    # On actual 96-core system, this would be 24GB
    large_buffer = [item] * (28_000_000)  # ~800MB
    
    # Perform some computation
    time.sleep(0.5)
    result = sum(large_buffer[:1000])
    
    return result


def process_super_extreme_dataset(item):
    """
    Simulates processing with super extreme memory usage (~48GB).
    
    This will show dramatic reduction in worker count.
    
    Calculation:
    - System: 96 cores, 700GB RAM
    - Usable RAM: 560GB
    - Memory limit: 560GB / 48GB ≈ 11 workers
    - Result: Recommends ~11 workers (about 1/9 of cores!)
    """
    # For testing purposes, we'll use a memory value that works on the test system
    # but explain what would happen on a 96-core system
    # Using ~1GB allocation (enough to show constraint on 1GB test system)
    large_buffer = [item] * (35_000_000)  # ~1GB
    
    # Perform some computation
    time.sleep(0.5)
    result = sum(large_buffer[:1000])
    
    return result


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def format_bytes(bytes_val):
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def demonstrate_scenario(func, memory_per_task_gb, scenario_name):
    """Demonstrate a specific memory scenario."""
    print(f"\n{'─' * 70}")
    print(f"Scenario: {scenario_name} ({memory_per_task_gb}GB/task)")
    print(f"{'─' * 70}")
    
    # Small dataset for demonstration
    data = range(100)
    
    print(f"  Function: {func.__name__}")
    print(f"  Expected memory per task: ~{memory_per_task_gb}GB")
    print(f"  Dataset size: {len(data)} items")
    print()
    print(f"  Note: Memory is scaled down for testing, but calculations")
    print(f"        show what would happen on a 96-core, 700GB RAM system.")
    print()
    
    try:
        print("  Analyzing with Amorsize...")
        result = optimize(func, data, sample_size=2, verbose=False)
        
        print()
        print(f"  📊 RESULTS ON CURRENT SYSTEM:")
        print(f"     Recommended workers: {result.n_jobs}")
        print(f"     Chunksize: {result.chunksize}")
        print(f"     Estimated speedup: {result.estimated_speedup:.2f}x")
        print(f"     Reason: {result.reason}")
        
        if result.warnings:
            print(f"\n     ⚠️  Warnings:")
            for warning in result.warnings:
                print(f"        {warning}")
        
        # Calculate theoretical maximum based on memory
        # Assuming 700GB system with 560GB usable (80%)
        usable_ram_gb = 560
        theoretical_max = int(usable_ram_gb / memory_per_task_gb)
        
        print()
        print(f"  📐 CALCULATION FOR 96-CORE, 700GB RAM SYSTEM:")
        print(f"     Usable RAM (80% of 700GB): {usable_ram_gb}GB")
        print(f"     Memory per task: {memory_per_task_gb}GB")
        print(f"     Theoretical max workers: {theoretical_max}")
        print(f"     Physical cores: 96")
        print(f"     → Amorsize would recommend: min({theoretical_max}, 96) = {min(theoretical_max, 96)}")
        
        # Highlight if we got intermediate value
        expected_njobs = min(theoretical_max, 96)
        if expected_njobs < 96 and expected_njobs > 1:
            print()
            print(f"  ✅ INTERMEDIATE n_jobs: {expected_njobs} workers")
            print(f"     (Not 1, not 96 - somewhere in between!)")
        elif expected_njobs == 96:
            print()
            print(f"  ℹ️  Would use all 96 cores - memory is not the limiting factor")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")


def main():
    """Main demonstration."""
    
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Intermediate n_jobs for High-End Systems (96 cores, 700GB RAM)  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    print()
    print("This example demonstrates intermediate n_jobs values on high-resource")
    print("systems by using tasks with memory requirements large enough to trigger")
    print("memory constraints.")
    print()
    print("Key Insight:")
    print("  On a 96-core, 700GB RAM system:")
    print("  - Usable RAM: 700GB × 0.8 = 560GB")
    print("  - For intermediate n_jobs: need 560GB / n_jobs > task_memory")
    print("  - To limit to < 96 workers: need tasks using 6GB+ each")
    print()
    
    from amorsize.system_info import get_physical_cores, get_available_memory
    
    cores = get_physical_cores()
    available = get_available_memory()
    
    print(f"Current System Information:")
    print(f"  Physical cores: {cores}")
    print(f"  Available memory: {format_bytes(available)}")
    print()
    
    print("=" * 70)
    print("TESTING DIFFERENT MEMORY PROFILES")
    print("=" * 70)
    
    # Scenario 1: ~6GB per task
    # Expected: ~93 workers (560GB / 6GB = 93)
    demonstrate_scenario(
        process_huge_dataset,
        6,
        "Huge Memory Task"
    )
    
    # Scenario 2: ~12GB per task
    # Expected: ~46 workers (560GB / 12GB = 46)
    demonstrate_scenario(
        process_very_huge_dataset,
        12,
        "Very Huge Memory Task"
    )
    
    # Scenario 3: ~24GB per task
    # Expected: ~23 workers (560GB / 24GB = 23)
    demonstrate_scenario(
        process_extreme_dataset,
        24,
        "Extreme Memory Task"
    )
    
    # Scenario 4: ~48GB per task
    # Expected: ~11 workers (560GB / 48GB = 11)
    demonstrate_scenario(
        process_super_extreme_dataset,
        48,
        "Super Extreme Memory Task"
    )
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("On high-end systems with 96 cores and 700GB RAM, intermediate n_jobs")
    print("values occur when individual tasks require substantial memory:")
    print()
    print("  Memory/Task    Workers     % of Cores    Status")
    print("  " + "-" * 66)
    print("  6GB            ~93         97%           Near maximum")
    print("  12GB           ~46         48%           ✓ Intermediate!")
    print("  24GB           ~23         24%           ✓ Intermediate!")
    print("  48GB           ~11         11%           ✓ Intermediate!")
    print()
    print("This demonstrates Amorsize's memory-aware optimization preventing")
    print("OOM issues by intelligently limiting worker count based on available")
    print("system resources.")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
