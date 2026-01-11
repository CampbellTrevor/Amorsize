"""
Worker Pool Warm-up Strategy Demo

This example demonstrates how to use the PoolManager to reuse worker pools
across multiple optimize() calls, amortizing the expensive process spawn cost.

Benefits:
- 10-100x faster optimization for repeated calls
- Reduced overhead for web services and batch processing
- Better resource utilization by keeping workers ready
"""

import time
from amorsize import optimize, PoolManager, get_global_pool_manager, managed_pool


# Sample computation function
def compute_heavy(x):
    """CPU-bound task that benefits from parallelization."""
    result = 0
    for i in range(10000):
        result += (x ** 2) / (i + 1)
    return result


def example_1_without_pool_manager():
    """
    Example 1: Traditional approach WITHOUT pool manager.
    
    Each optimize() call spawns new processes, which is expensive.
    """
    print("=" * 70)
    print("Example 1: Without Pool Manager (Traditional Approach)")
    print("=" * 70)
    
    datasets = [
        list(range(100)),
        list(range(100, 200)),
        list(range(200, 300)),
    ]
    
    start_time = time.time()
    
    for i, data in enumerate(datasets):
        result = optimize(compute_heavy, data, verbose=False)
        
        # Execute with the pool (creating new pool each time)
        from multiprocessing import Pool
        with Pool(result.n_jobs) as pool:
            results = pool.map(compute_heavy, result.data, chunksize=result.chunksize)
        
        print(f"  Dataset {i+1}: Processed {len(results)} items with n_jobs={result.n_jobs}")
    
    elapsed = time.time() - start_time
    print(f"\n  Total time: {elapsed:.3f}s")
    print(f"  (Each call spawned new processes)")
    return elapsed


def example_2_with_pool_manager():
    """
    Example 2: Optimized approach WITH pool manager.
    
    Worker pools are reused across optimize() calls, amortizing spawn cost.
    """
    print("\n" + "=" * 70)
    print("Example 2: With Pool Manager (Optimized Approach)")
    print("=" * 70)
    
    datasets = [
        list(range(100)),
        list(range(100, 200)),
        list(range(200, 300)),
    ]
    
    start_time = time.time()
    
    # Create pool manager
    manager = PoolManager()
    
    try:
        for i, data in enumerate(datasets):
            result = optimize(compute_heavy, data, verbose=False)
            
            # Get pool from manager (reuses existing pool if available)
            pool = manager.get_pool(n_jobs=result.n_jobs, executor_type=result.executor_type)
            
            # Execute with the reused pool
            results = pool.map(compute_heavy, result.data, chunksize=result.chunksize)
            
            print(f"  Dataset {i+1}: Processed {len(results)} items with n_jobs={result.n_jobs}")
    finally:
        # Clean up
        manager.shutdown()
    
    elapsed = time.time() - start_time
    print(f"\n  Total time: {elapsed:.3f}s")
    print(f"  (Worker pools were reused across calls)")
    return elapsed


def example_3_global_pool_manager():
    """
    Example 3: Using the global pool manager singleton.
    
    The global manager provides convenient pool reuse across the entire application.
    """
    print("\n" + "=" * 70)
    print("Example 3: Global Pool Manager (Singleton Pattern)")
    print("=" * 70)
    
    datasets = [
        list(range(100)),
        list(range(100, 200)),
        list(range(200, 300)),
    ]
    
    start_time = time.time()
    
    # Get global manager instance
    manager = get_global_pool_manager()
    
    for i, data in enumerate(datasets):
        result = optimize(compute_heavy, data, verbose=False)
        
        # Get pool from global manager
        pool = manager.get_pool(n_jobs=result.n_jobs, executor_type=result.executor_type)
        
        # Execute
        results = pool.map(compute_heavy, result.data, chunksize=result.chunksize)
        
        print(f"  Dataset {i+1}: Processed {len(results)} items with n_jobs={result.n_jobs}")
    
    elapsed = time.time() - start_time
    print(f"\n  Total time: {elapsed:.3f}s")
    print(f"  (Used global pool manager)")
    
    # Get statistics
    stats = manager.get_stats()
    print(f"\n  Pool Manager Stats:")
    print(f"    Active pools: {stats['active_pools']}")
    print(f"    Configurations: {stats['pool_configs']}")
    
    return elapsed


def example_4_context_manager():
    """
    Example 4: Using managed_pool context manager.
    
    Provides clean API for pool reuse with automatic management.
    """
    print("\n" + "=" * 70)
    print("Example 4: Managed Pool Context Manager")
    print("=" * 70)
    
    data = list(range(100))
    
    # Get optimal parameters
    result = optimize(compute_heavy, data, verbose=False)
    
    # Use context manager for automatic pool management
    with managed_pool(n_jobs=result.n_jobs, executor_type=result.executor_type) as pool:
        results = pool.map(compute_heavy, result.data, chunksize=result.chunksize)
    
    print(f"  Processed {len(results)} items")
    print(f"  (Pool automatically managed with context manager)")


def example_5_web_service_pattern():
    """
    Example 5: Web service pattern with pool reuse.
    
    Demonstrates how a web service can reuse pools across requests.
    """
    print("\n" + "=" * 70)
    print("Example 5: Web Service Pattern")
    print("=" * 70)
    
    # Simulate multiple incoming requests
    requests = [
        {"data": list(range(50)), "func": compute_heavy},
        {"data": list(range(50, 100)), "func": compute_heavy},
        {"data": list(range(100, 150)), "func": compute_heavy},
    ]
    
    # Get global manager (shared across all requests)
    manager = get_global_pool_manager()
    
    for i, request in enumerate(requests):
        # Process request
        result = optimize(request["func"], request["data"], verbose=False)
        
        # Reuse pool
        pool = manager.get_pool(n_jobs=result.n_jobs, executor_type=result.executor_type)
        results = pool.map(request["func"], result.data, chunksize=result.chunksize)
        
        print(f"  Request {i+1}: Processed {len(results)} items")
    
    print(f"\n  Web service benefit: Each request reuses existing pools,")
    print(f"  eliminating process spawn overhead for every request!")


def example_6_performance_comparison():
    """
    Example 6: Performance comparison showing speedup from pool reuse.
    """
    print("\n" + "=" * 70)
    print("Example 6: Performance Comparison")
    print("=" * 70)
    
    print("\nRunning benchmarks...")
    
    # Benchmark without pool manager
    time_without = example_1_without_pool_manager()
    
    # Benchmark with pool manager
    time_with = example_2_with_pool_manager()
    
    # Calculate speedup
    speedup = time_without / time_with if time_with > 0 else 1.0
    
    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"  Without Pool Manager: {time_without:.3f}s")
    print(f"  With Pool Manager:    {time_with:.3f}s")
    print(f"  Speedup:              {speedup:.2f}x")
    print(f"\n  💡 Pool reuse provides {speedup:.2f}x faster optimization!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("WORKER POOL WARM-UP STRATEGY DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows how to use PoolManager to reuse worker pools")
    print("across multiple optimize() calls, dramatically reducing overhead.")
    print()
    
    # Run all examples
    example_4_context_manager()
    example_5_web_service_pattern()
    example_3_global_pool_manager()
    
    # Run performance comparison
    example_6_performance_comparison()
    
    print("\n" + "=" * 70)
    print("KEY TAKEAWAYS")
    print("=" * 70)
    print("""
1. Pool Manager reuses worker pools across optimize() calls
2. Amortizes expensive process spawn cost (can be 100-200ms per spawn)
3. Particularly beneficial for:
   - Web services handling repeated requests
   - Batch processing systems
   - Repeated analysis on similar datasets
   - Applications with many short-lived optimizations

4. Three usage patterns:
   - Custom PoolManager for fine control
   - Global manager for application-wide reuse
   - managed_pool() context manager for convenience

5. Best practices:
   - Use global manager for web services
   - Use custom manager for isolated subsystems
   - Always call shutdown() or use context managers
   - Configure idle_timeout for resource conservation
    """)
