"""
Demo: Workload Type Detection (CPU-bound vs I/O-bound)

This example demonstrates Amorsize's ability to detect whether your workload
is CPU-bound, I/O-bound, or mixed, and provide appropriate recommendations.
"""

import time
from amorsize import optimize


def example_1_cpu_bound_workload():
    """Example 1: CPU-intensive computation (CPU-bound)"""
    print("=" * 70)
    print("EXAMPLE 1: CPU-Bound Workload")
    print("=" * 70)
    
    def cpu_heavy(x):
        """Pure computation - CPU-bound."""
        result = 0
        for i in range(50000):
            result += i ** 2
        return result + x
    
    data = range(100)
    
    print("\nOptimizing CPU-intensive function...")
    result = optimize(cpu_heavy, data, verbose=True, profile=True)
    
    print(f"\n✓ Recommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"✓ Workload type: {result.profile.workload_type}")
    print(f"✓ CPU utilization: {result.profile.cpu_time_ratio * 100:.1f}%")
    print(f"✓ Expected speedup: {result.estimated_speedup:.2f}x")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")


def example_2_io_bound_workload():
    """Example 2: I/O-intensive operations (I/O-bound)"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: I/O-Bound Workload")
    print("=" * 70)
    
    def io_heavy(x):
        """Simulates I/O wait (file/network/database operations)."""
        time.sleep(0.01)  # 10ms simulates I/O wait
        return x * 2
    
    data = range(50)
    
    print("\nOptimizing I/O-intensive function...")
    result = optimize(io_heavy, data, verbose=True, profile=True)
    
    print(f"\n✓ Recommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"✓ Workload type: {result.profile.workload_type}")
    print(f"✓ CPU utilization: {result.profile.cpu_time_ratio * 100:.1f}%")
    
    if result.warnings:
        print("\nWarnings & Recommendations:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
    
    print("\n💡 For I/O-bound tasks, consider using:")
    print("   - concurrent.futures.ThreadPoolExecutor (threading)")
    print("   - asyncio (async/await)")
    print("   Both have lower overhead than multiprocessing for I/O operations.")


def example_3_mixed_workload():
    """Example 3: Mixed CPU and I/O operations (Mixed)"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Mixed Workload (CPU + I/O)")
    print("=" * 70)
    
    def mixed_work(x):
        """Some computation + some I/O wait."""
        # Some CPU work
        result = sum(i ** 2 for i in range(10000))
        # Some I/O wait
        time.sleep(0.002)  # 2ms I/O wait
        return result + x
    
    data = range(50)
    
    print("\nOptimizing mixed CPU/I/O function...")
    result = optimize(mixed_work, data, verbose=True, profile=True)
    
    print(f"\n✓ Recommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"✓ Workload type: {result.profile.workload_type}")
    print(f"✓ CPU utilization: {result.profile.cpu_time_ratio * 100:.1f}%")
    
    if result.warnings:
        print("\nWarnings & Recommendations:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")


def example_4_diagnostic_profile():
    """Example 4: Detailed workload analysis with diagnostic profile"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Detailed Workload Analysis")
    print("=" * 70)
    
    def compute_task(x):
        """CPU-intensive task."""
        return sum(i ** 2 for i in range(20000))
    
    data = range(200)
    
    print("\nAnalyzing workload characteristics...")
    result = optimize(compute_task, data, profile=True)
    
    # Access workload type information
    print(f"\nWorkload Classification:")
    print(f"  Type: {result.profile.workload_type}")
    print(f"  CPU Time Ratio: {result.profile.cpu_time_ratio:.3f}")
    print(f"  Explanation: ", end="")
    
    if result.profile.workload_type == "cpu_bound":
        print("High CPU utilization - multiprocessing is appropriate")
    elif result.profile.workload_type == "io_bound":
        print("Low CPU utilization - consider threading or asyncio")
    else:
        print("Balanced CPU/I/O - evaluate based on your specific needs")
    
    print(f"\nPerformance Metrics:")
    print(f"  Avg execution time: {result.profile.avg_execution_time * 1000:.2f}ms per item")
    print(f"  Estimated speedup: {result.profile.estimated_speedup:.2f}x")
    print(f"  Parallel efficiency: {result.profile.speedup_efficiency * 100:.1f}%")
    
    # Show full diagnostic report
    print("\n" + "-" * 70)
    print("Full Diagnostic Report:")
    print("-" * 70)
    print(result.explain())


def example_5_real_world_comparison():
    """Example 5: Real-world comparison - File processing vs API calls"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Real-World Scenario Comparison")
    print("=" * 70)
    
    print("\nScenario A: Image processing (CPU-intensive)")
    def process_image(img_id):
        """Simulates CPU-intensive image processing."""
        # Simulate image transformation computations
        result = 0
        for _ in range(30000):
            result += img_id ** 2
        return result
    
    result_a = optimize(process_image, range(100), profile=True)
    print(f"  Workload type: {result_a.profile.workload_type}")
    print(f"  CPU utilization: {result_a.profile.cpu_time_ratio * 100:.1f}%")
    print(f"  Recommendation: Use multiprocessing with n_jobs={result_a.n_jobs}")
    
    print("\nScenario B: API calls (I/O-intensive)")
    def fetch_api_data(item_id):
        """Simulates network I/O for API calls."""
        time.sleep(0.015)  # 15ms simulates network latency
        return {"id": item_id, "data": "result"}
    
    result_b = optimize(fetch_api_data, range(50), profile=True)
    print(f"  Workload type: {result_b.profile.workload_type}")
    print(f"  CPU utilization: {result_b.profile.cpu_time_ratio * 100:.1f}%")
    if result_b.warnings:
        print(f"  ⚠ Warning: {result_b.warnings[0][:80]}...")
        print(f"  Recommendation: Use ThreadPoolExecutor or asyncio instead")


if __name__ == "__main__":
    print("\n")
    print("🔍 WORKLOAD TYPE DETECTION DEMO")
    print("=" * 70)
    print("This demo shows how Amorsize detects CPU-bound vs I/O-bound workloads")
    print("and provides appropriate parallelization recommendations.")
    print()
    
    try:
        example_1_cpu_bound_workload()
        example_2_io_bound_workload()
        example_3_mixed_workload()
        example_4_diagnostic_profile()
        example_5_real_world_comparison()
        
        print("\n" + "=" * 70)
        print("✓ Demo completed successfully!")
        print("=" * 70)
        print()
        print("Key Takeaways:")
        print("  1. CPU-bound: Use multiprocessing (Amorsize optimizes this)")
        print("  2. I/O-bound: Use threading or asyncio (lower overhead)")
        print("  3. Mixed: Evaluate based on which dominates your workload")
        print("  4. Amorsize detects workload type and warns when inappropriate")
        print()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
