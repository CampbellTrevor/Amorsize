"""
Streaming Enhancements Demo - Iteration 110

This example demonstrates the new streaming enhancements:
1. Adaptive chunking integration for heterogeneous workloads
2. Pool manager integration for pool reuse
3. Memory backpressure handling for memory-constrained environments

These features improve streaming performance and resource efficiency.
"""

import time
from multiprocessing import Pool
from amorsize import optimize_streaming, PoolManager, get_global_pool_manager


# =============================================================================
# Example Functions
# =============================================================================

def homogeneous_task(x):
    """Task with consistent execution time."""
    time.sleep(0.005)  # 5ms
    return x ** 2


def heterogeneous_task(x):
    """Task with variable execution time."""
    # Some items are fast, others slow
    if x % 5 == 0:
        time.sleep(0.020)  # 20ms for every 5th item
    else:
        time.sleep(0.002)  # 2ms for others
    return x ** 2


def large_result_task(x):
    """Task that returns large results."""
    # Returns ~80KB per item
    return [x] * 10000


# =============================================================================
# Example 1: Basic Streaming (No Enhancements)
# =============================================================================

def example_1_basic_streaming():
    """Basic streaming without enhancements."""
    print("="*70)
    print("EXAMPLE 1: Basic Streaming (No Enhancements)")
    print("="*70)
    
    data = range(100)
    
    # Optimize for streaming
    result = optimize_streaming(
        homogeneous_task,
        data,
        sample_size=5,
        verbose=True
    )
    
    print(f"\nOptimization Result:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  method: {'imap' if result.use_ordered else 'imap_unordered'}")
    print(f"  estimated speedup: {result.estimated_speedup:.2f}x")
    
    # Execute with recommended parameters
    if result.n_jobs > 1:
        with Pool(result.n_jobs) as pool:
            if result.use_ordered:
                iterator = pool.imap(homogeneous_task, result.data, chunksize=result.chunksize)
            else:
                iterator = pool.imap_unordered(homogeneous_task, result.data, chunksize=result.chunksize)
            
            # Process results incrementally
            start = time.time()
            results = list(iterator)
            duration = time.time() - start
            
            print(f"\n✓ Processed {len(results)} items in {duration:.2f}s")
    else:
        print("\n→ Serial execution recommended")


# =============================================================================
# Example 2: Adaptive Chunking for Heterogeneous Workloads
# =============================================================================

def example_2_adaptive_chunking():
    """Demonstrate adaptive chunking for heterogeneous workloads."""
    print("\n\n" + "="*70)
    print("EXAMPLE 2: Adaptive Chunking for Heterogeneous Workloads")
    print("="*70)
    
    data = range(100)
    
    # Optimize with adaptive chunking enabled
    result = optimize_streaming(
        heterogeneous_task,
        data,
        sample_size=10,
        enable_adaptive_chunking=True,
        adaptation_rate=0.3,  # Moderate adaptation speed
        verbose=True
    )
    
    print(f"\nOptimization Result:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  adaptive chunking: {result.use_adaptive_chunking}")
    if result.use_adaptive_chunking:
        print(f"  adaptation rate: {result.adaptive_chunking_params.get('adaptation_rate', 'N/A')}")
        print(f"  min chunksize: {result.adaptive_chunking_params.get('min_chunksize', 'N/A')}")
        print(f"  max chunksize: {result.adaptive_chunking_params.get('max_chunksize', 'N/A')}")
    
    print(f"\n💡 Adaptive chunking automatically adjusts chunk sizes during execution")
    print(f"   to maintain optimal load balancing for variable workloads.")


# =============================================================================
# Example 3: Pool Manager for Repeated Streaming Operations
# =============================================================================

def example_3_pool_manager():
    """Demonstrate pool manager for efficient pool reuse."""
    print("\n\n" + "="*70)
    print("EXAMPLE 3: Pool Manager for Repeated Streaming Operations")
    print("="*70)
    
    # Create a custom pool manager
    manager = PoolManager()
    
    try:
        # Process multiple datasets using the same pool
        datasets = [range(50), range(60), range(70)]
        
        print("\nProcessing 3 datasets with pool reuse...")
        start = time.time()
        
        for i, data in enumerate(datasets, 1):
            print(f"\n--- Dataset {i} ({len(list(data))} items) ---")
            
            # Optimize with pool manager
            result = optimize_streaming(
                homogeneous_task,
                data,
                pool_manager=manager,
                verbose=False
            )
            
            print(f"Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
            
            # Get pool from manager (reuses existing pool if configuration matches)
            if result.n_jobs > 1:
                pool = manager.get_pool(result.n_jobs, executor_type='process')
                
                # Use the pool
                if result.use_ordered:
                    iterator = pool.imap(homogeneous_task, result.data, chunksize=result.chunksize)
                else:
                    iterator = pool.imap_unordered(homogeneous_task, result.data, chunksize=result.chunksize)
                
                results = list(iterator)
                print(f"✓ Processed {len(results)} items")
        
        total_duration = time.time() - start
        print(f"\n✓ Total duration: {total_duration:.2f}s")
        print(f"\n💡 Pool manager eliminates spawn overhead by reusing worker processes")
        print(f"   across multiple streaming operations.")
        
        # Show pool statistics
        stats = manager.get_stats()
        print(f"\nPool Manager Statistics:")
        print(f"  Active pools: {stats['active_pools']}")
        print(f"  Configurations: {stats['pool_configs']}")
        
    finally:
        # Clean up
        manager.shutdown()
        print("\n✓ Pool manager shutdown complete")


# =============================================================================
# Example 4: Memory Backpressure for Large Results
# =============================================================================

def example_4_memory_backpressure():
    """Demonstrate memory backpressure for memory-constrained streaming."""
    print("\n\n" + "="*70)
    print("EXAMPLE 4: Memory Backpressure for Large Results")
    print("="*70)
    
    data = range(100)
    
    # Optimize with memory backpressure enabled
    result = optimize_streaming(
        large_result_task,
        data,
        sample_size=5,
        enable_memory_backpressure=True,
        memory_threshold=0.8,  # Trigger backpressure at 80% memory usage
        verbose=True
    )
    
    print(f"\nOptimization Result:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  buffer_size: {result.buffer_size}")
    print(f"  memory backpressure: {result.memory_backpressure_enabled}")
    
    print(f"\n💡 Memory backpressure limits buffer size to prevent OOM kills")
    print(f"   when processing tasks with large return values.")


# =============================================================================
# Example 5: All Enhancements Together
# =============================================================================

def example_5_all_enhancements():
    """Demonstrate all enhancements working together."""
    print("\n\n" + "="*70)
    print("EXAMPLE 5: All Enhancements Together")
    print("="*70)
    
    # Use global pool manager for application-wide reuse
    manager = get_global_pool_manager()
    
    data = range(100)
    
    # Optimize with all enhancements
    result = optimize_streaming(
        heterogeneous_task,
        data,
        sample_size=10,
        enable_adaptive_chunking=True,
        adaptation_rate=0.3,
        pool_manager=manager,
        enable_memory_backpressure=True,
        memory_threshold=0.8,
        buffer_size=None,  # Auto-calculate
        verbose=True
    )
    
    print(f"\nFull Configuration:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  adaptive chunking: {result.use_adaptive_chunking}")
    print(f"  buffer size: {result.buffer_size}")
    print(f"  memory backpressure: {result.memory_backpressure_enabled}")
    print(f"  pool manager: enabled")
    
    print(f"\n💡 Combining all enhancements provides:")
    print(f"   • Optimal load balancing (adaptive chunking)")
    print(f"   • Fast repeated operations (pool reuse)")
    print(f"   • Memory safety (backpressure)")


# =============================================================================
# Example 6: When to Use Each Enhancement
# =============================================================================

def example_6_best_practices():
    """Best practices for using streaming enhancements."""
    print("\n\n" + "="*70)
    print("EXAMPLE 6: When to Use Each Enhancement")
    print("="*70)
    
    print("\n1. ADAPTIVE CHUNKING")
    print("   Use when:")
    print("   ✓ Task execution times vary significantly (CV > 0.3)")
    print("   ✓ Processing mixed workloads (e.g., documents of different sizes)")
    print("   ✓ Load balancing is critical")
    print("   Don't use when:")
    print("   ✗ Tasks have consistent execution times (homogeneous)")
    print("   ✗ Overhead of adaptation exceeds benefits")
    
    print("\n2. POOL MANAGER")
    print("   Use when:")
    print("   ✓ Processing multiple datasets in sequence")
    print("   ✓ Repeated streaming operations")
    print("   ✓ Web services handling multiple requests")
    print("   ✓ Spawn overhead is significant relative to task duration")
    print("   Don't use when:")
    print("   ✗ Single-use streaming (one dataset)")
    print("   ✗ Pool configuration changes frequently")
    
    print("\n3. MEMORY BACKPRESSURE")
    print("   Use when:")
    print("   ✓ Tasks return large results (>1MB per item)")
    print("   ✓ Memory constraints are tight")
    print("   ✓ Risk of OOM kills")
    print("   ✓ Running in containers with memory limits")
    print("   Don't use when:")
    print("   ✗ Results are small (<1KB per item)")
    print("   ✗ Ample memory available")
    print("   ✗ Throughput is critical and memory is not a concern")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("STREAMING ENHANCEMENTS DEMONSTRATION")
    print("Iteration 110 - Adaptive Chunking, Pool Manager, Memory Backpressure")
    print("="*70)
    
    try:
        # Run examples
        example_1_basic_streaming()
        example_2_adaptive_chunking()
        example_3_pool_manager()
        example_4_memory_backpressure()
        example_5_all_enhancements()
        example_6_best_practices()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
