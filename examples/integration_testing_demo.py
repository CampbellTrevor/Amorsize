"""
Integration Testing Demo: End-to-End Workflows with Amorsize

This example demonstrates how to validate that Amorsize's optimization
recommendations actually work correctly when used with multiprocessing.Pool.
"""

import time
from multiprocessing import Pool
from typing import List

from amorsize import optimize, execute


# Example 1: Basic Integration Pattern
def example_1_basic_integration():
    """
    Demonstrates the basic pattern of using optimize() with Pool.map().
    
    This is the fundamental integration pattern that all users should follow.
    """
    print("=" * 70)
    print("Example 1: Basic Integration Pattern")
    print("=" * 70)
    
    def computation(x: int) -> int:
        """A moderately expensive computation."""
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    data = list(range(100))
    
    # Step 1: Get optimization recommendations
    result = optimize(computation, data, verbose=True)
    
    print(f"\nRecommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # Step 2: Use recommendations with Pool
    if result.n_jobs == 1:
        # Serial execution
        results = [computation(x) for x in result.data]
    else:
        # Parallel execution
        with Pool(processes=result.n_jobs) as pool:
            results = pool.map(computation, result.data, chunksize=result.chunksize)
    
    print(f"Processed {len(results)} items successfully")
    print(f"First few results: {results[:5]}")
    
    # Step 3: Verify correctness
    expected = [computation(x) for x in range(100)]
    if results == expected:
        print("✅ Results match expected output!")
    else:
        print("❌ Results don't match!")
    
    print()


# Example 2: Using execute() for Simplified Integration
def example_2_execute_convenience():
    """
    Demonstrates using execute() for automatic integration.
    
    This is the recommended approach for most use cases.
    """
    print("=" * 70)
    print("Example 2: Simplified Integration with execute()")
    print("=" * 70)
    
    def computation(x: int) -> int:
        """A moderately expensive computation."""
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    data = list(range(100))
    
    # One-line optimization and execution
    results = execute(computation, data, verbose=True)
    
    print(f"\nProcessed {len(results)} items successfully")
    print(f"First few results: {results[:5]}")
    
    # Verify correctness
    expected = [computation(x) for x in range(100)]
    if results == expected:
        print("✅ Results match expected output!")
    
    print()


# Example 3: Generator Integration
def example_3_generator_integration():
    """
    Demonstrates that generator reconstruction works correctly with Pool.
    
    This is critical for streaming data sources.
    """
    print("=" * 70)
    print("Example 3: Generator Integration")
    print("=" * 70)
    
    def computation(x: int) -> int:
        return x ** 2
    
    def data_generator():
        """Simulates a streaming data source."""
        for i in range(100):
            yield i
    
    # Use generator with optimize
    gen = data_generator()
    result = optimize(computation, gen, verbose=True)
    
    print(f"\nRecommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # The generator is reconstructed in result.data
    if result.n_jobs == 1:
        results = [computation(x) for x in result.data]
    else:
        with Pool(processes=result.n_jobs) as pool:
            results = pool.map(computation, result.data, chunksize=result.chunksize)
    
    print(f"Processed {len(results)} items from generator")
    
    # Verify all data was processed
    expected = [x ** 2 for x in range(100)]
    if results == expected:
        print("✅ All generator data processed correctly!")
    else:
        print(f"❌ Data loss detected! Expected {len(expected)}, got {len(results)}")
    
    print()


# Example 4: Performance Validation
def example_4_performance_validation():
    """
    Demonstrates validating that parallelization actually improves performance.
    
    This is useful for confirming the optimizer's recommendations.
    """
    print("=" * 70)
    print("Example 4: Performance Validation")
    print("=" * 70)
    
    def expensive_computation(x: int) -> int:
        """Expensive enough to benefit from parallelization."""
        result = 0
        for i in range(10000):
            result += x ** 2
        return result
    
    data = list(range(50))
    
    # Get recommendation
    result = optimize(expensive_computation, data, verbose=True)
    
    print(f"\nRecommendation: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Estimated speedup: {result.estimated_speedup}")
    
    # Benchmark serial execution
    start = time.time()
    serial_results = [expensive_computation(x) for x in data]
    serial_time = time.time() - start
    
    print(f"\nSerial execution: {serial_time:.3f}s")
    
    # Benchmark parallel execution (if recommended)
    if result.n_jobs > 1:
        start = time.time()
        with Pool(processes=result.n_jobs) as pool:
            parallel_results = pool.map(expensive_computation, result.data, chunksize=result.chunksize)
        parallel_time = time.time() - start
        
        actual_speedup = serial_time / parallel_time
        
        print(f"Parallel execution: {parallel_time:.3f}s")
        print(f"Actual speedup: {actual_speedup:.2f}x")
        
        # Verify correctness
        if parallel_results == serial_results:
            print("✅ Results match!")
        
        # Check prediction accuracy
        prediction_error = abs(result.estimated_speedup - actual_speedup) / result.estimated_speedup
        if prediction_error < 0.5:  # Within 50%
            print(f"✅ Prediction accurate (error: {prediction_error*100:.1f}%)")
        else:
            print(f"⚠️  Prediction off by {prediction_error*100:.1f}%")
    else:
        print("Parallel execution skipped (serial recommended)")
    
    print()


# Example 5: Edge Case Validation
def example_5_edge_cases():
    """
    Demonstrates handling various edge cases.
    
    This ensures robustness in production scenarios.
    """
    print("=" * 70)
    print("Example 5: Edge Case Validation")
    print("=" * 70)
    
    def computation(x: int) -> int:
        return x ** 2
    
    # Edge case 1: Empty data
    print("\nEdge Case 1: Empty Data")
    results = execute(computation, [])
    print(f"Empty data result: {results}")
    assert results == [], "Empty data should return empty list"
    print("✅ Passed")
    
    # Edge case 2: Single item
    print("\nEdge Case 2: Single Item")
    results = execute(computation, [5])
    print(f"Single item result: {results}")
    assert results == [25], "Single item should work"
    print("✅ Passed")
    
    # Edge case 3: Very small dataset (< sample_size)
    print("\nEdge Case 3: Dataset Smaller Than Sample Size")
    results = execute(computation, [1, 2, 3], sample_size=10)
    print(f"Small dataset result: {results}")
    assert results == [1, 4, 9], "Should handle small datasets"
    print("✅ Passed")
    
    # Edge case 4: Heterogeneous workload
    print("\nEdge Case 4: Heterogeneous Workload")
    def variable_work(x: int) -> int:
        iterations = (x % 10) * 1000 + 1000
        result = 0
        for i in range(iterations):
            result += x
        return result
    
    data = list(range(30))
    results = execute(variable_work, data, verbose=True)
    expected = [variable_work(x) for x in range(30)]
    assert results == expected, "Heterogeneous workload should work"
    print("✅ Passed")
    
    print("\n✅ All edge cases handled correctly!")
    print()


# Example 6: Integration with Advanced Features
def example_6_advanced_features():
    """
    Demonstrates integration with advanced features like profiling and callbacks.
    
    This shows how to use all features together.
    """
    print("=" * 70)
    print("Example 6: Integration with Advanced Features")
    print("=" * 70)
    
    def computation(x: int) -> int:
        result = 0
        for i in range(5000):
            result += x ** 2
        return result
    
    data = list(range(50))
    
    # Track progress
    progress_updates = []
    def progress_callback(phase: str, progress: float):
        progress_updates.append((phase, progress))
        if progress in [0.0, 0.5, 1.0]:
            print(f"Progress: {phase} ({progress*100:.0f}%)")
    
    # Use with profile and progress callback
    results, opt_result = execute(
        computation,
        data,
        profile=True,
        progress_callback=progress_callback,
        return_optimization_result=True,
        verbose=False  # Disable verbose to see progress more clearly
    )
    
    print(f"\nProcessed {len(results)} items")
    print(f"Progress updates received: {len(progress_updates)}")
    
    # Show diagnostic profile
    print("\n" + "=" * 70)
    print("Diagnostic Profile:")
    print("=" * 70)
    print(opt_result.explain())
    
    # Verify correctness
    expected = [computation(x) for x in range(50)]
    if results == expected:
        print("\n✅ Results correct with all features enabled!")
    
    print()


# Example 7: Correctness Validation Pattern
def example_7_correctness_validation():
    """
    Demonstrates a systematic approach to validating correctness.
    
    This pattern should be used in your own tests.
    """
    print("=" * 70)
    print("Example 7: Correctness Validation Pattern")
    print("=" * 70)
    
    def computation(x: int) -> List[int]:
        """Returns a more complex object."""
        return [x, x ** 2, x ** 3]
    
    data = list(range(50))
    
    # Step 1: Serial execution (ground truth)
    print("Computing ground truth (serial)...")
    serial_results = [computation(x) for x in data]
    
    # Step 2: Optimized execution
    print("Computing with optimization...")
    optimized_results = execute(computation, data, verbose=True)
    
    # Step 3: Detailed comparison
    print("\nValidating correctness:")
    
    # Check length
    if len(serial_results) == len(optimized_results):
        print(f"✅ Length matches: {len(serial_results)} items")
    else:
        print(f"❌ Length mismatch: {len(serial_results)} vs {len(optimized_results)}")
        return
    
    # Check order
    if serial_results == optimized_results:
        print("✅ Results match exactly (order preserved)")
    else:
        print("❌ Results don't match")
        return
    
    # Check individual items
    mismatches = 0
    for i, (serial, optimized) in enumerate(zip(serial_results, optimized_results)):
        if serial != optimized:
            print(f"❌ Mismatch at index {i}: {serial} vs {optimized}")
            mismatches += 1
    
    if mismatches == 0:
        print(f"✅ All {len(serial_results)} items match!")
    else:
        print(f"❌ {mismatches} mismatches found")
    
    print()


def main():
    """Run all integration examples."""
    examples = [
        example_1_basic_integration,
        example_2_execute_convenience,
        example_3_generator_integration,
        example_4_performance_validation,
        example_5_edge_cases,
        example_6_advanced_features,
        example_7_correctness_validation,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print("All Integration Examples Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
