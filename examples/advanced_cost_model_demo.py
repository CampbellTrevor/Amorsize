"""
Advanced Cost Modeling Demo - Comparing Basic vs Advanced Amdahl's Law

This example demonstrates the difference between basic Amdahl's Law and the
advanced cost model that accounts for hardware-level effects.

The advanced model considers:
- Cache coherency overhead (L1/L2/L3 cache effects)
- Memory bandwidth saturation (memory bus contention)
- NUMA penalties (cross-node access overhead)
- False sharing (cache line ping-ponging)

This provides more accurate speedup predictions on multi-core systems.
"""

import time
import numpy as np
from amorsize import optimize


def cpu_intensive_small_data(x):
    """
    CPU-intensive function with small data (fits in cache).
    
    This workload should benefit from parallelization with minimal
    cache coherency overhead since data fits in cache.
    """
    result = 0
    for i in range(1000):
        result += x ** 2 + x ** 0.5
    return result


def cpu_intensive_large_data(x):
    """
    CPU-intensive function with large working set (exceeds L3 cache).
    
    This workload will experience cache pressure and coherency overhead
    when running on many cores.
    """
    # Create a large array that exceeds typical L3 cache (8-32MB)
    # 1M float64 elements = 8MB
    large_array = np.random.rand(1024 * 1024)  # 1M elements = 8MB array
    return np.sum(large_array * x)


def memory_intensive(x):
    """
    Memory-intensive function that stresses memory bandwidth.
    
    This workload will show memory bandwidth saturation effects
    when many cores compete for memory access.
    """
    # Repeatedly read and write large arrays
    size = 512 * 1024  # 4MB
    arr1 = np.random.rand(size)
    arr2 = np.random.rand(size)
    arr3 = arr1 * arr2
    return np.mean(arr3) * x


def returns_small_objects(x):
    """
    Function returning very small objects (potential false sharing).
    
    Returns an integer, which is much smaller than a cache line (64 bytes).
    With many workers, this could cause false sharing as multiple small
    results might share cache lines.
    """
    return x * 2


def print_comparison(func, data, description):
    """
    Compare basic and advanced cost models for a given function.
    """
    print(f"\n{'=' * 80}")
    print(f"Testing: {description}")
    print('=' * 80)
    
    # Optimize with basic cost model
    print("\n[1] Basic Cost Model (Standard Amdahl's Law)")
    print("-" * 80)
    result_basic = optimize(
        func,
        data,
        verbose=False,
        use_advanced_cost_model=False,
        profile=True
    )
    print(f"Recommendation: n_jobs={result_basic.n_jobs}, chunksize={result_basic.chunksize}")
    print(f"Estimated speedup: {result_basic.estimated_speedup:.2f}x")
    print(f"Efficiency: {result_basic.profile.speedup_efficiency * 100:.1f}%")
    
    # Optimize with advanced cost model
    print("\n[2] Advanced Cost Model (Hardware-Aware)")
    print("-" * 80)
    result_advanced = optimize(
        func,
        data,
        verbose=False,
        use_advanced_cost_model=True,
        profile=True
    )
    print(f"Recommendation: n_jobs={result_advanced.n_jobs}, chunksize={result_advanced.chunksize}")
    print(f"Estimated speedup: {result_advanced.estimated_speedup:.2f}x")
    print(f"Efficiency: {result_advanced.profile.speedup_efficiency * 100:.1f}%")
    
    # Show difference
    speedup_diff = result_basic.estimated_speedup - result_advanced.estimated_speedup
    print("\n[3] Comparison")
    print("-" * 80)
    print(f"Speedup difference: {speedup_diff:+.2f}x")
    
    if speedup_diff > 0.1:
        print("⚠️  Basic model overestimates speedup (hardware effects reduce performance)")
    elif speedup_diff < -0.1:
        print("✓  Advanced model predicts better performance")
    else:
        print("✓  Both models agree (hardware effects minimal)")
    
    # Show which hardware effects are significant
    if hasattr(result_advanced.profile, 'overhead_breakdown'):
        print("\nHardware effects considered by advanced model:")
        # Note: We'd need to store these in the profile for this to work
        print("  - Cache coherency overhead")
        print("  - Memory bandwidth saturation")
        print("  - NUMA penalties")
        print("  - False sharing")


def main():
    """
    Run demonstrations comparing basic and advanced cost models.
    """
    print("=" * 80)
    print("ADVANCED COST MODELING DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo compares basic Amdahl's Law with the advanced cost model")
    print("that accounts for hardware-level effects.")
    
    # Test 1: CPU-intensive with small data (minimal hardware effects)
    print_comparison(
        cpu_intensive_small_data,
        range(1000),
        "CPU-intensive, small data (fits in cache)"
    )
    
    # Test 2: CPU-intensive with large data (cache pressure)
    print_comparison(
        cpu_intensive_large_data,
        range(100),
        "CPU-intensive, large data (cache pressure)"
    )
    
    # Test 3: Memory-intensive (bandwidth saturation)
    print_comparison(
        memory_intensive,
        range(100),
        "Memory-intensive (bandwidth saturation)"
    )
    
    # Test 4: Small return objects (false sharing potential)
    print_comparison(
        returns_small_objects,
        range(10000),
        "Small return objects (false sharing potential)"
    )
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
The advanced cost model provides more accurate predictions by considering:

1. Cache Coherency: Overhead when multiple cores access shared data
   - Increases with core count and cache pressure
   - More significant when working set exceeds L3 cache

2. Memory Bandwidth: Saturation when many cores compete for memory
   - Becomes bottleneck for memory-intensive workloads
   - Can limit scaling beyond certain core counts

3. NUMA Penalties: Overhead when workers span NUMA nodes
   - Significant on multi-socket systems
   - Remote memory access is 20-40% slower

4. False Sharing: Cache line ping-ponging with small objects
   - Occurs when return objects < cache line size (64 bytes)
   - Overhead increases with core count

When to use advanced cost model:
✓ Large core counts (>8 cores)
✓ NUMA systems (multi-socket servers)
✓ Memory-intensive workloads
✓ Working sets that exceed L3 cache
✓ When accuracy is critical

When basic model is sufficient:
✓ Small core counts (≤4 cores)
✓ CPU-intensive workloads with small data
✓ Quick estimates where precision isn't critical
✓ When optimization time matters more than accuracy
""")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: This example requires numpy. Install with: pip install numpy")
