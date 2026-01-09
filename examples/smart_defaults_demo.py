"""
Smart Default Overhead Measurements Demo

This demo shows how Amorsize now measures actual system overhead by default
instead of using estimates, providing more accurate recommendations.
"""

import time
from amorsize import optimize
from amorsize.system_info import (
    get_spawn_cost, 
    get_chunking_overhead,
    get_spawn_cost_estimate,
    _clear_spawn_cost_cache,
    _clear_chunking_overhead_cache
)


def expensive_computation(x):
    """CPU-intensive function for testing."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def demo_1_default_measurements():
    """Demo 1: Default behavior with measurements enabled."""
    print_section("Demo 1: Default Behavior (Measurements Enabled)")
    
    # Clear caches to show measurement behavior
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    print("\n📊 Measuring actual system overhead (one-time, cached)...")
    
    # Get measurements
    start = time.perf_counter()
    spawn_cost = get_spawn_cost()  # Default: use_benchmark=True
    chunking_overhead = get_chunking_overhead()  # Default: use_benchmark=True
    measurement_time = time.perf_counter() - start
    
    print(f"\n✅ Measurements complete in {measurement_time * 1000:.1f}ms:")
    print(f"   • Spawn cost: {spawn_cost * 1000:.2f}ms per worker")
    print(f"   • Chunking overhead: {chunking_overhead * 1000:.3f}ms per chunk")
    
    # Compare with estimates
    estimated_spawn = get_spawn_cost_estimate()
    print(f"\n📈 Comparison with OS estimates:")
    print(f"   • Estimated spawn cost: {estimated_spawn * 1000:.2f}ms")
    print(f"   • Measured spawn cost: {spawn_cost * 1000:.2f}ms")
    print(f"   • Accuracy improvement: {abs(estimated_spawn - spawn_cost) / estimated_spawn * 100:.1f}%")


def demo_2_optimize_with_measurements():
    """Demo 2: Using optimize() with default measurements."""
    print_section("Demo 2: Optimize with Measured Overhead")
    
    data = range(1000)
    
    print("\n🔍 Optimizing with actual measurements...")
    start = time.perf_counter()
    result = optimize(expensive_computation, data, profile=True, verbose=False)
    optimization_time = time.perf_counter() - start
    
    print(f"\n✅ Optimization complete in {optimization_time * 1000:.1f}ms:")
    print(f"   • Recommended n_jobs: {result.n_jobs}")
    print(f"   • Recommended chunksize: {result.chunksize}")
    print(f"   • Estimated speedup: {result.estimated_speedup:.2f}x")
    
    if result.profile:
        print(f"\n📊 System-specific measurements used:")
        print(f"   • Spawn cost: {result.profile.spawn_cost * 1000:.2f}ms per worker")
        print(f"   • Chunking overhead: {result.profile.chunking_overhead * 1000:.3f}ms per chunk")


def demo_3_cached_measurements():
    """Demo 3: Subsequent calls use cached measurements."""
    print_section("Demo 3: Measurement Caching")
    
    data = range(1000)
    
    print("\n🔄 First optimize() call (measures overhead)...")
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    start = time.perf_counter()
    result1 = optimize(expensive_computation, data)
    time1 = time.perf_counter() - start
    
    print(f"   • Time: {time1 * 1000:.1f}ms (includes measurement)")
    print(f"   • Result: n_jobs={result1.n_jobs}, chunksize={result1.chunksize}")
    
    print("\n⚡ Second optimize() call (uses cache)...")
    start = time.perf_counter()
    result2 = optimize(expensive_computation, data)
    time2 = time.perf_counter() - start
    
    print(f"   • Time: {time2 * 1000:.1f}ms (no measurement overhead)")
    print(f"   • Result: n_jobs={result2.n_jobs}, chunksize={result2.chunksize}")
    
    speedup = time1 / time2
    print(f"\n📈 Second call is {speedup:.1f}x faster (cache hit)")


def demo_4_opting_out():
    """Demo 4: Opting out of measurements for fastest startup."""
    print_section("Demo 4: Opting Out (Using Estimates)")
    
    data = range(1000)
    
    # Clear cache for fair comparison
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    print("\n⚡ With measurements disabled (fastest startup)...")
    start = time.perf_counter()
    result = optimize(
        expensive_computation, 
        data,
        use_spawn_benchmark=False,
        use_chunking_benchmark=False,
        profile=True
    )
    time_no_measure = time.perf_counter() - start
    
    print(f"   • Time: {time_no_measure * 1000:.1f}ms (using estimates)")
    print(f"   • Result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    if result.profile:
        print(f"\n📊 Using OS estimates:")
        print(f"   • Spawn cost (estimate): {result.profile.spawn_cost * 1000:.2f}ms")
        print(f"   • Chunking overhead (estimate): {result.profile.chunking_overhead * 1000:.3f}ms")


def demo_5_accuracy_comparison():
    """Demo 5: Comparing accuracy of measurements vs estimates."""
    print_section("Demo 5: Accuracy Improvement")
    
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    data = range(1000)
    
    print("\n📊 With estimates (old behavior):")
    result_estimates = optimize(
        expensive_computation,
        data,
        use_spawn_benchmark=False,
        use_chunking_benchmark=False,
        profile=True
    )
    print(f"   • n_jobs: {result_estimates.n_jobs}")
    print(f"   • chunksize: {result_estimates.chunksize}")
    print(f"   • Spawn cost: {result_estimates.profile.spawn_cost * 1000:.2f}ms (estimate)")
    print(f"   • Chunking: {result_estimates.profile.chunking_overhead * 1000:.3f}ms (estimate)")
    
    _clear_spawn_cost_cache()
    _clear_chunking_overhead_cache()
    
    print("\n📊 With measurements (new behavior):")
    result_measured = optimize(
        expensive_computation,
        data,
        use_spawn_benchmark=True,
        use_chunking_benchmark=True,
        profile=True
    )
    print(f"   • n_jobs: {result_measured.n_jobs}")
    print(f"   • chunksize: {result_measured.chunksize}")
    print(f"   • Spawn cost: {result_measured.profile.spawn_cost * 1000:.2f}ms (measured)")
    print(f"   • Chunking: {result_measured.profile.chunking_overhead * 1000:.3f}ms (measured)")
    
    print("\n✅ Measurement provides system-specific accuracy:")
    spawn_diff = abs(result_estimates.profile.spawn_cost - result_measured.profile.spawn_cost)
    chunk_diff = abs(result_estimates.profile.chunking_overhead - result_measured.profile.chunking_overhead)
    print(f"   • Spawn cost difference: {spawn_diff * 1000:.2f}ms")
    print(f"   • Chunking difference: {chunk_diff * 1000:.3f}ms")


def demo_6_detailed_profile():
    """Demo 6: Using diagnostic profile to see measurement details."""
    print_section("Demo 6: Detailed Diagnostic Profile")
    
    data = range(1000)
    
    print("\n🔍 Running optimization with detailed profiling...")
    result = optimize(expensive_computation, data, profile=True)
    
    print("\n📋 Complete diagnostic report:")
    print(result.explain())


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print(" Smart Default Overhead Measurements Demo")
    print(" Amorsize Iteration 12")
    print("=" * 70)
    
    try:
        demo_1_default_measurements()
        demo_2_optimize_with_measurements()
        demo_3_cached_measurements()
        demo_4_opting_out()
        demo_5_accuracy_comparison()
        demo_6_detailed_profile()
        
        print("\n" + "=" * 70)
        print(" ✅ All demos completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
