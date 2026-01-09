"""
Streaming Optimization Examples

This example demonstrates how to use optimize_streaming() for imap/imap_unordered
workloads where results are processed incrementally without memory accumulation.
"""

from amorsize import optimize_streaming, optimize, process_in_batches
from multiprocessing import Pool
import time


# ============================================================================
# Example 1: Basic Streaming Optimization
# ============================================================================

def expensive_computation(x):
    """Simulate expensive computation (~50ms)."""
    result = 0
    for i in range(50000):
        result += x ** 2
    return result


def example_1_basic_streaming():
    """Example 1: Basic streaming optimization."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Streaming Optimization")
    print("=" * 70)
    
    # Large dataset
    data = list(range(1000))
    
    # Optimize for streaming
    result = optimize_streaming(expensive_computation, data, verbose=True)
    
    # Use with pool.imap() or pool.imap_unordered()
    print(f"\nUsing optimized parameters:")
    print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"  method={'imap' if result.use_ordered else 'imap_unordered'}")
    
    with Pool(result.n_jobs) as pool:
        if result.use_ordered:
            iterator = pool.imap(expensive_computation, result.data, chunksize=result.chunksize)
        else:
            iterator = pool.imap_unordered(expensive_computation, result.data, chunksize=result.chunksize)
        
        # Process results as they become available
        count = 0
        for item in iterator:
            count += 1
            if count % 100 == 0:
                print(f"  Processed {count}/1000 items...")
        
        print(f"✓ Completed: Processed {count} items with streaming")


# ============================================================================
# Example 2: Streaming vs Batch vs Map - Memory Comparison
# ============================================================================

def large_result_function(x):
    """Function that returns large objects (100KB each)."""
    return [x] * 25000  # ~100KB per result


def example_2_memory_comparison():
    """Example 2: Compare streaming vs batch vs map for memory usage."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Streaming vs Batch vs Map - Memory Comparison")
    print("=" * 70)
    
    data = list(range(500))  # 500 items × 100KB = 50MB total
    
    print("\n--- Option 1: Pool.map() (accumulates all results) ---")
    map_result = optimize(large_result_function, data, sample_size=5)
    print(f"  Recommendation: n_jobs={map_result.n_jobs}, chunksize={map_result.chunksize}")
    if map_result.warnings:
        print(f"  ⚠ Warnings: {map_result.warnings[0][:80]}...")
    print(f"  Memory impact: All 50MB accumulated in memory")
    
    print("\n--- Option 2: process_in_batches() (sequential batches) ---")
    # Note: process_in_batches() is good for very large datasets
    # but processes batches sequentially
    print(f"  Processes batches sequentially with optimal parallelization per batch")
    print(f"  Memory impact: Peak = batch_size × result_size (controlled)")
    
    print("\n--- Option 3: imap_unordered() (streaming) ---")
    stream_result = optimize_streaming(large_result_function, data, sample_size=5, verbose=False)
    print(f"  Recommendation: n_jobs={stream_result.n_jobs}, chunksize={stream_result.chunksize}")
    print(f"  Method: {'imap' if stream_result.use_ordered else 'imap_unordered'}")
    print(f"  Memory impact: Process one result at a time (~100KB peak)")
    
    print("\n✓ Streaming is best for: large results, continuous processing")
    print("✓ Batching is best for: very large datasets, need memory safety")
    print("✓ Map is best for: moderate datasets, need all results at once")


# ============================================================================
# Example 3: Ordered vs Unordered Streaming
# ============================================================================

def example_3_ordered_vs_unordered():
    """Example 3: Demonstrate ordered vs unordered streaming."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Ordered vs Unordered Streaming")
    print("=" * 70)
    
    data = list(range(20))
    
    print("\n--- With prefer_ordered=True (imap) ---")
    ordered_result = optimize_streaming(
        expensive_computation,
        data,
        prefer_ordered=True,
        verbose=False
    )
    
    with Pool(ordered_result.n_jobs) as pool:
        iterator = pool.imap(expensive_computation, data, chunksize=ordered_result.chunksize)
        results = []
        for item in iterator:
            results.append(item)
    
    print(f"  First 5 results: {results[:5]}")
    print(f"  Results are in order: {results == sorted(results)}")
    
    print("\n--- With prefer_ordered=False (imap_unordered) ---")
    unordered_result = optimize_streaming(
        expensive_computation,
        data,
        prefer_ordered=False,
        verbose=False
    )
    
    with Pool(unordered_result.n_jobs) as pool:
        iterator = pool.imap_unordered(expensive_computation, data, chunksize=unordered_result.chunksize)
        results = []
        for item in iterator:
            results.append(item)
    
    print(f"  First 5 results: {results[:5]}")
    print(f"  Results are in order: {results == sorted(results)}")
    print(f"  ✓ imap_unordered is typically 10-20% faster but results arrive out of order")


# ============================================================================
# Example 4: Streaming with Generator (Infinite Stream)
# ============================================================================

def data_generator():
    """Simulate an infinite data stream."""
    for i in range(10000):
        yield i


def example_4_streaming_generator():
    """Example 4: Streaming with generator input."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Streaming with Generator (Simulated Infinite Stream)")
    print("=" * 70)
    
    # Generate streaming data
    data = data_generator()
    
    # Optimize for streaming
    result = optimize_streaming(expensive_computation, data, sample_size=5, verbose=False)
    
    print(f"Optimized for streaming:")
    print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"  method={'imap' if result.use_ordered else 'imap_unordered'}")
    
    # Process with imap (streaming style)
    with Pool(result.n_jobs) as pool:
        if result.use_ordered:
            iterator = pool.imap(expensive_computation, result.data, chunksize=result.chunksize)
        else:
            iterator = pool.imap_unordered(expensive_computation, result.data, chunksize=result.chunksize)
        
        # Process first 100 items from the stream
        count = 0
        for item in iterator:
            count += 1
            if count >= 100:
                break
            if count % 20 == 0:
                print(f"  Processed {count} items from stream...")
    
    print(f"✓ Processed {count} items from infinite stream")
    print(f"✓ Memory usage: Minimal (streaming, no accumulation)")


# ============================================================================
# Example 5: Streaming with Progress Tracking
# ============================================================================

def example_5_streaming_with_progress():
    """Example 5: Track progress while streaming."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Streaming with Progress Tracking")
    print("=" * 70)
    
    data = list(range(200))
    total = len(data)
    
    # Optimize
    result = optimize_streaming(expensive_computation, data, sample_size=5, verbose=False)
    
    print(f"Processing {total} items with n_jobs={result.n_jobs}...")
    
    # Process with progress tracking
    with Pool(result.n_jobs) as pool:
        if result.use_ordered:
            iterator = pool.imap(expensive_computation, data, chunksize=result.chunksize)
        else:
            iterator = pool.imap_unordered(expensive_computation, data, chunksize=result.chunksize)
        
        processed = 0
        for item in iterator:
            processed += 1
            if processed % 50 == 0 or processed == total:
                pct = (processed / total) * 100
                print(f"  Progress: {processed}/{total} ({pct:.0f}%)")
    
    print(f"✓ Completed: {processed} items processed")


# ============================================================================
# Example 6: Diagnostic Profiling for Streaming
# ============================================================================

def example_6_diagnostic_profiling():
    """Example 6: Use diagnostic profiling to understand streaming optimization."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Diagnostic Profiling for Streaming")
    print("=" * 70)
    
    data = list(range(500))
    
    # Enable profiling
    result = optimize_streaming(
        expensive_computation,
        data,
        sample_size=10,
        profile=True,
        verbose=False
    )
    
    # View detailed explanation
    print(result.explain())


# ============================================================================
# Example 7: Real-World Use Case - Log Processing
# ============================================================================

def process_log_line(line):
    """Simulate log line processing."""
    time.sleep(0.001)  # Simulate parsing/analysis
    # Extract timestamp, level, message, etc.
    return {
        'line': line,
        'processed': True,
        'length': len(str(line))
    }


def example_7_log_processing():
    """Example 7: Real-world log processing with streaming."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Real-World Log Processing (Streaming)")
    print("=" * 70)
    
    # Simulate log lines
    log_lines = [f"[INFO] Log entry {i}" for i in range(1000)]
    
    print(f"Processing {len(log_lines)} log entries...")
    
    # Optimize for streaming
    result = optimize_streaming(process_log_line, log_lines, sample_size=10, verbose=False)
    
    print(f"Using: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Method: {'imap' if result.use_ordered else 'imap_unordered'}")
    
    # Process logs with streaming
    start = time.perf_counter()
    with Pool(result.n_jobs) as pool:
        if result.use_ordered:
            iterator = pool.imap(process_log_line, log_lines, chunksize=result.chunksize)
        else:
            iterator = pool.imap_unordered(process_log_line, log_lines, chunksize=result.chunksize)
        
        # Write results to database/file as they arrive
        processed_count = 0
        for entry in iterator:
            # Simulate writing to database/file
            processed_count += 1
            if processed_count % 200 == 0:
                print(f"  Processed {processed_count} log entries...")
    
    end = time.perf_counter()
    elapsed = end - start
    
    print(f"\n✓ Processed {processed_count} log entries in {elapsed:.2f}s")
    print(f"  Throughput: {processed_count/elapsed:.0f} entries/sec")
    print(f"  Speedup: ~{result.estimated_speedup:.1f}x")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║       AMORSIZE STREAMING OPTIMIZATION EXAMPLES                    ║")
    print("║       Using imap/imap_unordered for Memory-Efficient Processing  ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    
    # Run examples
    example_1_basic_streaming()
    example_2_memory_comparison()
    example_3_ordered_vs_unordered()
    example_4_streaming_generator()
    example_5_streaming_with_progress()
    example_6_diagnostic_profiling()
    example_7_log_processing()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Use optimize_streaming() for large datasets or infinite streams")
    print("  • imap/imap_unordered process results incrementally (no memory accumulation)")
    print("  • imap_unordered is ~10-20% faster but results arrive out of order")
    print("  • Ideal for: log processing, data pipelines, continuous streams")
    print("  • Not ideal for: need all results at once, small datasets")
    print()
