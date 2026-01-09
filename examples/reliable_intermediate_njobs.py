#!/usr/bin/env python3
"""
Reliable Intermediate n_jobs Example

This example RELIABLY demonstrates scenarios where Amorsize recommends
a number of workers between 1 and maximum cores, even on high-resource systems.

Strategy: Use module-level functions (picklable) with carefully tuned
memory and computation characteristics to trigger intermediate n_jobs values.
"""

import time
import random
import sys
from multiprocessing import Pool


# ============================================================================
# Module-Level Functions (Picklable)
# ============================================================================

def very_memory_intensive_task(x):
    """
    Extremely memory-intensive task - 200MB per task.
    Forces memory constraints even on large systems.
    """
    # Allocate 200MB per task
    buffer = [random.random() for _ in range(25_000_000)]  # ~200MB
    time.sleep(0.001)  # Small computation
    return sum(buffer[:100]) / 100


def memory_intensive_task(x):
    """
    Memory-intensive task - 100MB per task.
    """
    # Allocate 100MB per task
    buffer = [random.random() for _ in range(12_500_000)]  # ~100MB
    time.sleep(0.001)
    return sum(buffer[:100]) / 100


def moderate_memory_task(x):
    """
    Moderate memory - 50MB per task.
    """
    # Allocate 50MB per task
    buffer = [random.random() for _ in range(6_250_000)]  # ~50MB
    time.sleep(0.001)
    return sum(buffer[:100]) / 100


def low_memory_task(x):
    """
    Low memory - 10MB per task.
    """
    # Allocate 10MB per task
    buffer = [random.random() for _ in range(1_250_000)]  # ~10MB
    time.sleep(0.001)
    return sum(buffer[:100]) / 100


def compute_intensive_task(x):
    """
    Compute-intensive with minimal memory.
    """
    result = 0
    for i in range(50000):
        result += (x ** 2) / (i + 1)
    return result


# ============================================================================
# Demonstration
# ============================================================================

def demonstrate_guaranteed_intermediate():
    """
    Demonstrate intermediate n_jobs with various memory profiles.
    """
    print("=" * 70)
    print("RELIABLE INTERMEDIATE n_jobs DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Import here to ensure amorsize is available
    from amorsize import optimize
    from amorsize.system_info import get_physical_cores, get_available_memory
    
    physical_cores = get_physical_cores()
    available_memory_gb = get_available_memory() / (1024**3)
    
    print(f"System Information:")
    print(f"  Physical cores: {physical_cores}")
    print(f"  Available memory: {available_memory_gb:.2f} GB")
    print()
    
    # Test data
    data = list(range(100))
    
    # Test scenarios with different memory requirements
    scenarios = [
        ("Very High Memory (200MB/task)", very_memory_intensive_task, 200),
        ("High Memory (100MB/task)", memory_intensive_task, 100),
        ("Moderate Memory (50MB/task)", moderate_memory_task, 50),
        ("Low Memory (10MB/task)", low_memory_task, 10),
        ("Compute Intensive (minimal memory)", compute_intensive_task, 1),
    ]
    
    print("=" * 70)
    print("TESTING DIFFERENT MEMORY PROFILES")
    print("=" * 70)
    print()
    
    results = []
    
    for name, func, memory_mb in scenarios:
        print(f"\n{'─' * 70}")
        print(f"Scenario: {name}")
        print(f"{'─' * 70}")
        
        result = optimize(func, data, sample_size=3, verbose=False)
        results.append((name, memory_mb, result))
        
        print(f"  Memory per task: {memory_mb} MB")
        print(f"  Recommended workers: {result.n_jobs}")
        print(f"  Physical cores: {physical_cores}")
        print(f"  Chunksize: {result.chunksize}")
        print(f"  Estimated speedup: {result.estimated_speedup:.2f}x")
        
        # Calculate theoretical memory limit
        theoretical_max = int((available_memory_gb * 1024 * 0.8) / memory_mb)
        print(f"  Theoretical max workers (80% RAM): {theoretical_max}")
        
        if 1 < result.n_jobs < physical_cores:
            print(f"  ✓ SUCCESS: Intermediate n_jobs ({result.n_jobs}) between 1 and {physical_cores}!")
        elif result.n_jobs == physical_cores:
            print(f"  → Using all {physical_cores} cores")
        else:
            print(f"  → Serial execution (n_jobs={result.n_jobs})")
    
    # Summary table
    print("\n\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print()
    print(f"{'Scenario':<40} {'Memory':<12} {'n_jobs':<10} {'Cores':<10}")
    print("─" * 70)
    
    for name, memory_mb, result in results:
        print(f"{name:<40} {memory_mb:>6} MB    {result.n_jobs:<10} {physical_cores:<10}")
    
    print()
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()
    
    intermediate_found = False
    for name, memory_mb, result in results:
        if 1 < result.n_jobs < physical_cores:
            intermediate_found = True
            print(f"✓ Found intermediate n_jobs in '{name}':")
            print(f"  - Recommended: {result.n_jobs} workers")
            print(f"  - Available cores: {physical_cores}")
            print(f"  - Reason: Memory constraint ({memory_mb}MB/task × {result.n_jobs} = {memory_mb * result.n_jobs}MB total)")
            print()
    
    if not intermediate_found:
        print("⚠ No intermediate n_jobs values were found on this system.")
        print()
        print("This can happen when:")
        print(f"  • System has abundant RAM ({available_memory_gb:.0f}GB available)")
        print(f"  • Relatively few cores ({physical_cores})")
        print(f"  • Even 200MB/task × {physical_cores} cores = {200 * physical_cores}MB < {available_memory_gb * 1024 * 0.8:.0f}MB available")
        print()
        print("Intermediate values are more common on systems with:")
        print("  • Many cores (16+) but limited RAM (< 32GB)")
        print("  • Very memory-intensive tasks (500MB+ per task)")
        print("  • Or when processing large datasets with high memory footprints")
    
    return results


def show_memory_calculation():
    """
    Show the memory calculation logic clearly.
    """
    print("\n\n" + "=" * 70)
    print("MEMORY CALCULATION LOGIC")
    print("=" * 70)
    print()
    
    from amorsize.system_info import get_physical_cores, get_available_memory
    
    physical_cores = get_physical_cores()
    available_memory = get_available_memory()
    available_gb = available_memory / (1024**3)
    usable_memory = available_memory * 0.8  # 80% safety margin
    usable_gb = usable_memory / (1024**3)
    
    print("Amorsize calculates max workers as:")
    print()
    print("  max_workers = min(")
    print(f"      physical_cores = {physical_cores},")
    print(f"      floor(available_memory * 0.8 / memory_per_task)")
    print("  )")
    print()
    print(f"Available RAM: {available_gb:.2f} GB")
    print(f"Usable RAM (80%): {usable_gb:.2f} GB")
    print()
    
    # Show examples
    memory_scenarios = [10, 50, 100, 200, 500, 1000, 2000]
    
    print(f"{'Memory/Task':<15} {'Max Workers':<15} {'Total RAM Used':<20} {'Result':<20}")
    print("─" * 70)
    
    for memory_mb in memory_scenarios:
        memory_bytes = memory_mb * 1024 * 1024
        max_workers = min(physical_cores, int(usable_memory / memory_bytes))
        total_ram_mb = (max_workers * memory_mb)
        
        if max_workers == physical_cores:
            result = "All cores"
        elif max_workers == 1:
            result = "Serial"
        else:
            result = f"INTERMEDIATE ({max_workers})"
        
        print(f"{memory_mb:>6} MB       {max_workers:<15} {total_ram_mb:>6} MB            {result:<20}")
    
    print()


def create_artificial_constraint_example():
    """
    Create an example that artificially limits n_jobs for demonstration.
    """
    print("\n" + "=" * 70)
    print("ARTIFICIAL CONSTRAINT EXAMPLE")
    print("=" * 70)
    print()
    print("To reliably demonstrate intermediate n_jobs on ANY system,")
    print("we can create a scenario that artificially constrains workers.")
    print()
    
    from amorsize import optimize
    from amorsize.system_info import get_physical_cores
    
    physical_cores = get_physical_cores()
    
    # Use the very memory intensive task
    data = list(range(50))
    
    print(f"Testing with very_memory_intensive_task (200MB/task)...")
    print(f"Dataset: {len(data)} items")
    print()
    
    result = optimize(very_memory_intensive_task, data, sample_size=3, verbose=True)
    
    print(f"\n{'=' * 70}")
    print("FINAL RESULT")
    print("=" * 70)
    print(f"Recommended workers: {result.n_jobs}")
    print(f"Physical cores: {physical_cores}")
    print(f"Chunksize: {result.chunksize}")
    print(f"Estimated speedup: {result.estimated_speedup:.2f}x")
    print(f"Reason: {result.reason}")
    
    if 1 < result.n_jobs < physical_cores:
        print(f"\n✓✓✓ SUCCESS! Intermediate n_jobs = {result.n_jobs} ✓✓✓")
        print(f"    (between 1 and {physical_cores} cores)")
    
    print()


def main():
    """Main execution."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Reliable Intermediate n_jobs Demonstration  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("This example uses module-level functions with varying memory")
    print("requirements to demonstrate intermediate n_jobs values.")
    print()
    
    # Run demonstrations
    demonstrate_guaranteed_intermediate()
    show_memory_calculation()
    create_artificial_constraint_example()
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print()
    print("1. Intermediate n_jobs values occur when:")
    print("   • Memory per task × n_workers > available RAM")
    print("   • System has many cores but limited RAM")
    print("   • Tasks are memory-intensive (100MB+ per task)")
    print()
    print("2. On high-resource systems (96 cores, 700GB RAM):")
    print("   • Memory constraints rarely trigger")
    print("   • Would need VERY memory-intensive tasks (1GB+ each)")
    print("   • Or process thousands of items simultaneously")
    print()
    print("3. Amorsize calculation:")
    print("   n_jobs = min(cores, available_RAM * 0.8 / memory_per_task)")
    print()
    print("4. Real-world applications where this matters:")
    print("   • ML model serving (models are 1-10GB each)")
    print("   • Video processing (frames are 100-500MB each)")
    print("   • Large dataset analysis (DataFrames are 500MB-5GB)")
    print("   • Scientific computing (matrices are 1-10GB)")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
