#!/usr/bin/env python3
"""
Memory-Constrained Parallelization Example

This example demonstrates a scenario where Amorsize recommends an optimal
number of workers that is NEITHER 1 NOR the maximum number of cores.

This happens when:
1. Memory constraints limit the number of workers
2. The function is memory-intensive
3. Available RAM / Memory per worker < Physical cores

The example processes large in-memory data structures where each worker
needs significant RAM, forcing Amorsize to recommend fewer workers than
available cores to avoid running out of memory (OOM).
"""

import sys
import time
import random
from multiprocessing import Pool
from amorsize import optimize


# ============================================================================
# Memory-Intensive Function
# ============================================================================

def process_large_dataset(data_id):
    """
    Simulate processing that requires significant memory.
    
    This function creates large temporary data structures in memory,
    simulating real-world scenarios like:
    - Image processing with large temporary buffers
    - Data analysis with intermediate DataFrames
    - Scientific computing with large matrices
    - Video processing with frame buffers
    """
    # Allocate a large chunk of memory (simulating ~50MB per task)
    # In real scenarios, this might be:
    # - Loading and processing an image
    # - Creating temporary pandas DataFrames
    # - Building intermediate computation matrices
    large_buffer = [random.random() for _ in range(6_250_000)]  # ~50MB
    
    # Simulate some computation on this data
    result = 0
    for i in range(1000):
        result += sum(large_buffer[i:i+100]) / 100
    
    # Return a small result (the large buffer gets garbage collected)
    return result / 1000


def process_medium_dataset(data_id):
    """
    A medium-memory function for comparison.
    
    Uses moderate memory (~20MB per task).
    """
    # Allocate moderate memory (~20MB)
    medium_buffer = [random.random() for _ in range(2_500_000)]  # ~20MB
    
    # Some computation
    result = 0
    for i in range(500):
        result += sum(medium_buffer[i:i+100]) / 100
    
    return result / 500


def process_small_dataset(data_id):
    """
    A low-memory function for comparison.
    
    Uses minimal memory (~1MB per task).
    """
    # Allocate small memory (~1MB)
    small_buffer = [random.random() for _ in range(125_000)]  # ~1MB
    
    # Some computation
    result = 0
    for i in range(100):
        result += sum(small_buffer[i:i+50]) / 50
    
    return result / 100


# ============================================================================
# Demonstration Functions
# ============================================================================

def demonstrate_memory_constraint():
    """
    Demonstrate how memory constraints affect the optimal n_jobs.
    """
    print("=" * 70)
    print("MEMORY-CONSTRAINED PARALLELIZATION DEMONSTRATION")
    print("=" * 70)
    print("\nThis example shows scenarios where optimal n_jobs is between 1")
    print("and the maximum number of cores due to memory constraints.")
    print()
    
    # Get system info
    from amorsize.system_info import get_physical_cores, get_available_memory
    
    physical_cores = get_physical_cores()
    available_memory_gb = get_available_memory() / (1024**3)
    
    print(f"System Information:")
    print(f"  Physical cores: {physical_cores}")
    print(f"  Available memory: {available_memory_gb:.2f} GB")
    print()
    
    # Test data
    data = list(range(100))
    
    # Scenario 1: Large memory per task
    print("\n" + "=" * 70)
    print("SCENARIO 1: High Memory Usage per Task (~50MB)")
    print("=" * 70)
    print("\nFunction: process_large_dataset")
    print("Expected: Amorsize will limit workers due to memory constraints")
    print()
    
    result_large = optimize(process_large_dataset, data, sample_size=3, verbose=True)
    
    print(f"\n📊 RESULTS:")
    print(f"   Recommended workers: {result_large.n_jobs}")
    print(f"   Physical cores: {physical_cores}")
    print(f"   Chunksize: {result_large.chunksize}")
    print(f"   Estimated speedup: {result_large.estimated_speedup:.2f}x")
    print(f"   Reason: {result_large.reason}")
    
    if result_large.warnings:
        print(f"\n   ⚠️  Warnings:")
        for warning in result_large.warnings:
            print(f"      - {warning}")
    
    if 1 < result_large.n_jobs < physical_cores:
        print(f"\n   ✓ SUCCESS: Optimal n_jobs ({result_large.n_jobs}) is between 1 and max cores ({physical_cores})!")
        print(f"      Memory constraints limited parallelism to avoid OOM.")
    elif result_large.n_jobs == physical_cores:
        print(f"\n   → Using all cores ({result_large.n_jobs}) - system has enough memory")
    else:
        print(f"\n   → Serial execution recommended ({result_large.n_jobs})")
    
    # Scenario 2: Medium memory per task
    print("\n\n" + "=" * 70)
    print("SCENARIO 2: Medium Memory Usage per Task (~20MB)")
    print("=" * 70)
    print("\nFunction: process_medium_dataset")
    print()
    
    result_medium = optimize(process_medium_dataset, data, sample_size=3, verbose=True)
    
    print(f"\n📊 RESULTS:")
    print(f"   Recommended workers: {result_medium.n_jobs}")
    print(f"   Physical cores: {physical_cores}")
    print(f"   Chunksize: {result_medium.chunksize}")
    print(f"   Estimated speedup: {result_medium.estimated_speedup:.2f}x")
    
    if result_medium.warnings:
        print(f"\n   ⚠️  Warnings:")
        for warning in result_medium.warnings:
            print(f"      - {warning}")
    
    # Scenario 3: Low memory per task
    print("\n\n" + "=" * 70)
    print("SCENARIO 3: Low Memory Usage per Task (~1MB)")
    print("=" * 70)
    print("\nFunction: process_small_dataset")
    print()
    
    result_small = optimize(process_small_dataset, data, sample_size=3, verbose=True)
    
    print(f"\n📊 RESULTS:")
    print(f"   Recommended workers: {result_small.n_jobs}")
    print(f"   Physical cores: {physical_cores}")
    print(f"   Chunksize: {result_small.chunksize}")
    print(f"   Estimated speedup: {result_small.estimated_speedup:.2f}x")
    
    # Summary
    print("\n\n" + "=" * 70)
    print("SUMMARY COMPARISON")
    print("=" * 70)
    print(f"\n{'Function':<25} {'Memory/Task':<15} {'Recommended':<15} {'Cores':<10}")
    print("-" * 70)
    print(f"{'process_large_dataset':<25} {'~50MB':<15} {f'{result_large.n_jobs} workers':<15} {physical_cores:<10}")
    print(f"{'process_medium_dataset':<25} {'~20MB':<15} {f'{result_medium.n_jobs} workers':<15} {physical_cores:<10}")
    print(f"{'process_small_dataset':<25} {'~1MB':<15} {f'{result_small.n_jobs} workers':<15} {physical_cores:<10}")
    
    print("\n" + "=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    print()
    print("1. Memory-Intensive Tasks:")
    print("   When each task requires significant memory, Amorsize")
    print("   automatically reduces the number of workers to prevent")
    print("   running out of memory (OOM killer).")
    print()
    print("2. Optimal n_jobs Calculation:")
    print("   n_jobs = min(physical_cores, available_memory / memory_per_task)")
    print()
    print("3. Real-World Applications:")
    print("   - Image/video processing with large frame buffers")
    print("   - Data analysis with large intermediate DataFrames")
    print("   - Scientific computing with large matrices")
    print("   - Machine learning with large model inference")
    print()
    print("4. Why This Matters:")
    print("   Without this check, spawning too many workers would cause:")
    print("   - System to start swapping (very slow)")
    print("   - OS to kill processes (OOM killer)")
    print("   - System instability and crashes")
    print()
    
    return result_large, result_medium, result_small


def demonstrate_actual_execution():
    """
    Optionally demonstrate actual execution with the recommendations.
    """
    print("\n\n" + "=" * 70)
    print("OPTIONAL: ACTUAL EXECUTION DEMONSTRATION")
    print("=" * 70)
    print()
    print("Would you like to run actual execution with a small subset?")
    print("(This will use the recommended parameters)")
    print()
    
    # For automated runs, skip this
    # In interactive mode, you could ask for user input
    print("Skipping actual execution in automated mode.")
    print("To test actual execution, run the smaller subset manually.")


def create_contrived_example():
    """
    Create a more contrived example where we force an intermediate n_jobs.
    """
    print("\n\n" + "=" * 70)
    print("CONTRIVED EXAMPLE: Forcing Intermediate n_jobs")
    print("=" * 70)
    print()
    print("We can create scenarios where n_jobs is strictly between 1 and max:")
    print()
    
    def memory_heavy_task(x):
        """
        Artificially create a scenario with specific memory requirements
        that force an intermediate n_jobs value.
        """
        # Create a large temporary structure
        # Adjust size to force specific memory constraints
        size = 5_000_000  # ~40MB
        temp_data = [x * i for i in range(size)]
        result = sum(temp_data[:1000]) / 1000
        return result
    
    data = list(range(50))
    
    print("Testing memory_heavy_task with specific memory profile...")
    result = optimize(memory_heavy_task, data, sample_size=3, verbose=True)
    
    print(f"\n📊 RESULT:")
    print(f"   Recommended workers: {result.n_jobs}")
    print(f"   Chunksize: {result.chunksize}")
    
    from amorsize.system_info import get_physical_cores
    physical_cores = get_physical_cores()
    
    if 1 < result.n_jobs < physical_cores:
        print(f"\n   ✓ Achieved intermediate n_jobs: {result.n_jobs} (between 1 and {physical_cores})")
    else:
        print(f"\n   Note: Got {result.n_jobs} workers (system-dependent)")
        print(f"         Intermediate values depend on available memory")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  AMORSIZE: Memory-Constrained Parallelization Example  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Main demonstration
    demonstrate_memory_constraint()
    
    # Contrived example
    create_contrived_example()
    
    print("\n\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()
    print("Amorsize intelligently determines the optimal number of workers by")
    print("considering BOTH computational and memory constraints.")
    print()
    print("When memory per task is high:")
    print("  → n_jobs will be less than physical cores to avoid OOM")
    print()
    print("When memory per task is low:")
    print("  → n_jobs will use all available physical cores")
    print()
    print("This automatic optimization prevents system instability and ensures")
    print("reliable, efficient parallel processing!")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
