#!/usr/bin/env python3
"""
Intermediate n_jobs Example: When Optimal Workers < Max Cores

This example demonstrates specific scenarios where Amorsize recommends
a number of workers that is BETWEEN 1 and the maximum number of cores.

Three scenarios are shown:
1. Memory constraints limiting worker count
2. Dataset size too small to benefit from all cores
3. Overhead vs benefit trade-off
"""

import time
import sys
from multiprocessing import Pool
from amorsize import optimize


# ============================================================================
# Scenario 1: Simulated Memory Constraint
# ============================================================================

def demonstrate_simulated_memory_constraint():
    """
    Demonstrate how we can simulate a memory-constrained scenario.
    """
    print("=" * 70)
    print("SCENARIO 1: Simulated Memory Constraint")
    print("=" * 70)
    print()
    print("When peak_memory * n_workers > available_memory * 0.8,")
    print("Amorsize will reduce the number of workers.")
    print()
    
    # Let's manually show what Amorsize calculates
    from amorsize.system_info import get_physical_cores, get_available_memory, calculate_max_workers
    
    physical_cores = get_physical_cores()
    available_memory = get_available_memory()
    
    print(f"System Info:")
    print(f"  Physical cores: {physical_cores}")
    print(f"  Available memory: {available_memory / (1024**3):.2f} GB")
    print()
    
    # Simulate different memory requirements
    memory_scenarios = [
        ("Low memory task", 10 * 1024 * 1024),      # 10 MB
        ("Medium memory task", 100 * 1024 * 1024),  # 100 MB
        ("High memory task", 500 * 1024 * 1024),    # 500 MB
        ("Very high memory task", 800 * 1024 * 1024), # 800 MB
    ]
    
    print("Memory-based worker limits:")
    print(f"{'Task Type':<25} {'Memory/Task':<15} {'Max Workers':<15}")
    print("-" * 55)
    
    for task_name, memory_per_task in memory_scenarios:
        max_workers = calculate_max_workers(physical_cores, memory_per_task)
        memory_mb = memory_per_task / (1024**2)
        print(f"{task_name:<25} {memory_mb:>6.0f} MB      {max_workers:>3} workers")
    
    print()
    print("Key Insight: As memory per task increases, max workers decreases")
    print(f"             to stay within available memory ({available_memory / (1024**3):.2f} GB)")
    print()


# ============================================================================
# Scenario 2: Small Dataset Size
# ============================================================================

def demonstrate_small_dataset():
    """
    With a small dataset, using all cores creates too much overhead.
    Amorsize may recommend fewer workers.
    """
    print("\n" + "=" * 70)
    print("SCENARIO 2: Small Dataset - Overhead Dominates")
    print("=" * 70)
    print()
    print("When dataset is small, the overhead of spawning many workers")
    print("outweighs the benefits. Amorsize will recommend fewer workers.")
    print()
    
    def moderate_task(x):
        """A moderately expensive task."""
        result = 0
        for i in range(5000):
            result += x ** 2 + i
        return result
    
    # Test with different dataset sizes
    dataset_sizes = [10, 50, 100, 500, 1000, 5000]
    
    print(f"{'Dataset Size':<15} {'Recommended':<15} {'Reason':<40}")
    print("-" * 70)
    
    for size in dataset_sizes:
        data = list(range(size))
        result = optimize(moderate_task, data, sample_size=min(5, size), verbose=False)
        reason_short = result.reason[:37] + "..." if len(result.reason) > 40 else result.reason
        print(f"{size:<15} {f'{result.n_jobs} workers':<15} {reason_short:<40}")
    
    print()
    print("Observation: Smaller datasets may get fewer workers due to")
    print("             overhead vs benefit trade-offs.")
    print()


# ============================================================================
# Scenario 3: Practical Example with Intermediate n_jobs
# ============================================================================

def demonstrate_practical_intermediate():
    """
    A practical example that shows intermediate n_jobs.
    """
    print("\n" + "=" * 70)
    print("SCENARIO 3: Practical Example - Image Processing Simulation")
    print("=" * 70)
    print()
    
    def process_image_with_memory(image_id):
        """
        Simulate image processing that requires significant memory.
        Each "image" needs a temporary buffer for processing.
        """
        import random
        
        # Simulate loading and processing an image
        # Real scenario: loading a 4K image into memory for processing
        image_size = 3840 * 2160 * 3  # 4K RGB image
        
        # Create a temporary buffer (simulating image data)
        # In reality, this might be a numpy array
        buffer_size = image_size // 100  # Scaled down for demo
        image_buffer = [random.random() for _ in range(buffer_size)]
        
        # Simulate image processing operations
        time.sleep(0.01)  # Simulate I/O and processing time
        
        # Apply some transformations
        result = sum(image_buffer[:100]) / 100
        
        return result
    
    # Simulate a batch of images to process
    image_batch = list(range(200))
    
    print("Processing a batch of 200 images...")
    print("Each image requires temporary memory buffer during processing.")
    print()
    
    result = optimize(process_image_with_memory, image_batch, sample_size=5, verbose=True)
    
    print(f"\n📊 OPTIMIZATION RESULT:")
    print(f"   Recommended workers: {result.n_jobs}")
    print(f"   Chunksize: {result.chunksize}")
    print(f"   Estimated speedup: {result.estimated_speedup:.2f}x")
    print(f"   Reason: {result.reason}")
    
    from amorsize.system_info import get_physical_cores
    cores = get_physical_cores()
    
    if result.warnings:
        print(f"\n   ⚠️ Warnings:")
        for warning in result.warnings:
            print(f"      {warning}")
    
    print()
    if 1 < result.n_jobs < cores:
        print(f"   ✓ SUCCESS: Got intermediate n_jobs = {result.n_jobs}")
        print(f"             (between 1 and {cores} cores)")
    elif result.n_jobs == cores:
        print(f"   → Using all {cores} cores")
    else:
        print(f"   → Serial execution (n_jobs=1)")
    print()


# ============================================================================
# Scenario 4: Dataset Characteristics
# ============================================================================

def demonstrate_dataset_characteristics():
    """
    Show how dataset characteristics affect n_jobs recommendation.
    """
    print("\n" + "=" * 70)
    print("SCENARIO 4: How Dataset Characteristics Affect n_jobs")
    print("=" * 70)
    print()
    
    def expensive_task(x):
        """An expensive computational task."""
        result = 0
        for i in range(10000):
            result += (x ** 2) / (i + 1)
        return result
    
    scenarios = [
        ("Very small dataset", list(range(5))),
        ("Small dataset", list(range(20))),
        ("Medium dataset", list(range(100))),
        ("Large dataset", list(range(1000))),
        ("Very large dataset", list(range(10000))),
    ]
    
    print(f"{'Scenario':<25} {'Size':<10} {'n_jobs':<10} {'Chunksize':<12} {'Speedup':<10}")
    print("-" * 70)
    
    for name, data in scenarios:
        result = optimize(expensive_task, data, sample_size=min(3, len(data)), verbose=False)
        speedup_str = f"{result.estimated_speedup:.1f}x" if result.estimated_speedup > 1 else "1.0x"
        print(f"{name:<25} {len(data):<10} {result.n_jobs:<10} {result.chunksize:<12} {speedup_str:<10}")
    
    print()
    print("Pattern: Dataset size influences n_jobs recommendation")
    print("         • Very small: May recommend serial (overhead too high)")
    print("         • Small: May recommend fewer workers")
    print("         • Large: Can utilize all available cores")
    print()


# ============================================================================
# Explanation Section
# ============================================================================

def explain_intermediate_njobs():
    """
    Explain when and why intermediate n_jobs values occur.
    """
    print("\n" + "=" * 70)
    print("WHY INTERMEDIATE n_jobs VALUES OCCUR")
    print("=" * 70)
    print()
    
    print("Amorsize calculates optimal n_jobs using:")
    print()
    print("  n_jobs = min(")
    print("      physical_cores,")
    print("      available_memory / estimated_memory_per_worker,")
    print("      optimal_based_on_overhead")
    print("  )")
    print()
    print("Intermediate values (1 < n_jobs < max_cores) happen when:")
    print()
    print("  1. MEMORY CONSTRAINTS")
    print("     • Each worker needs significant RAM")
    print("     • available_memory / memory_per_worker < physical_cores")
    print("     • Example: 8 cores, but only RAM for 4 workers")
    print()
    print("  2. SMALL DATASET SIZE")
    print("     • Dataset too small to benefit from all cores")
    print("     • Overhead of spawning workers > benefit")
    print("     • Example: 100 items with 16 cores → maybe use only 4")
    print()
    print("  3. OVERHEAD vs BENEFIT TRADE-OFF")
    print("     • Function is moderately expensive")
    print("     • Full parallelization adds too much overhead")
    print("     • Sweet spot is somewhere in the middle")
    print()
    print("  4. CHUNKING OPTIMIZATION")
    print("     • Optimal chunksize may not divide evenly")
    print("     • Using fewer workers with larger chunks can be better")
    print("     • Reduces IPC overhead while maintaining parallelism")
    print()
    print("Real-world scenarios:")
    print("  • Image processing: Each image needs 100MB → limit to 4 workers on 16GB RAM")
    print("  • Video frames: Processing 100 frames on 32-core machine → use 8 cores")
    print("  • Data analysis: Large DataFrames → memory limits worker count")
    print("  • ML inference: Model size limits concurrent workers")
    print()


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main execution."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Intermediate n_jobs: When Optimal Workers < Max Cores  ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Run demonstrations
    demonstrate_simulated_memory_constraint()
    demonstrate_small_dataset()
    demonstrate_practical_intermediate()
    demonstrate_dataset_characteristics()
    explain_intermediate_njobs()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Amorsize intelligently determines the optimal n_jobs by considering:")
    print("  ✓ Available physical cores")
    print("  ✓ Memory constraints")
    print("  ✓ Dataset size")
    print("  ✓ Function execution time")
    print("  ✓ Overhead vs benefit trade-offs")
    print()
    print("Result: You get the TRULY optimal number of workers,")
    print("        not just the maximum possible!")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
