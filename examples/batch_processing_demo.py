"""
Demonstration of batch processing for memory-constrained workloads.

This example shows how to use process_in_batches() to safely process
large datasets that would otherwise cause memory exhaustion.
"""

from amorsize import process_in_batches, estimate_safe_batch_size, optimize
import time


# ============================================================================
# Example 1: Basic Batch Processing
# ============================================================================

def example_1_basic_batch_processing():
    """Basic usage with explicit batch size."""
    print("=" * 70)
    print("Example 1: Basic Batch Processing")
    print("=" * 70)
    
    def square(x):
        return x ** 2
    
    # Process 100 items in batches of 20
    data = list(range(100))
    results = process_in_batches(
        square,
        data,
        batch_size=20,
        verbose=True
    )
    
    print(f"\nFirst 10 results: {results[:10]}")
    print(f"Total results: {len(results)}")
    print()


# ============================================================================
# Example 2: Auto-calculated Batch Size
# ============================================================================

def example_2_auto_batch_size():
    """Let the library automatically calculate optimal batch size."""
    print("=" * 70)
    print("Example 2: Auto-calculated Batch Size")
    print("=" * 70)
    
    def process_item(x):
        # Simulate processing that returns moderately large results
        return [x] * 1000  # ~8KB result
    
    data = list(range(500))
    
    # No batch_size specified - automatically calculated
    print("Processing with auto-calculated batch size...")
    results = process_in_batches(
        process_item,
        data,
        max_memory_percent=0.3,  # Use max 30% of available memory
        verbose=True
    )
    
    print(f"\nTotal results: {len(results)}")
    print()


# ============================================================================
# Example 3: Handling Large Return Objects
# ============================================================================

def example_3_large_return_objects():
    """Process functions that return large objects."""
    print("=" * 70)
    print("Example 3: Large Return Objects")
    print("=" * 70)
    
    def load_and_process_image(img_id):
        """Simulate image processing with large results."""
        # Simulate a large processed image (1MB)
        return {
            'id': img_id,
            'data': [0] * 125000,  # ~1MB of integers
            'metadata': {'processed': True}
        }
    
    # Without batching, this would consume 1GB+ for 1000 images
    # With batching, we keep memory under control
    image_ids = list(range(100))  # Reduced for demo
    
    # Use conservative memory limit (10%)
    print("Processing images with memory-safe batching...")
    results = process_in_batches(
        load_and_process_image,
        image_ids,
        max_memory_percent=0.1,
        verbose=True
    )
    
    print(f"\nProcessed {len(results)} images safely")
    print()


# ============================================================================
# Example 4: Using estimate_safe_batch_size()
# ============================================================================

def example_4_manual_batch_size_estimation():
    """Manually estimate batch size before processing."""
    print("=" * 70)
    print("Example 4: Manual Batch Size Estimation")
    print("=" * 70)
    
    # Estimate batch size for 10MB results
    result_size = 10 * 1024 * 1024  # 10MB
    batch_size = estimate_safe_batch_size(
        result_size,
        max_memory_percent=0.5
    )
    
    print(f"Estimated safe batch size for 10MB results: {batch_size} items")
    print(f"This keeps memory under 50% of available RAM")
    
    # Now use the estimated batch size
    def expensive_computation(x):
        result = 0
        for i in range(10000):
            result += x ** 2
        return result
    
    data = list(range(100))
    results = process_in_batches(
        expensive_computation,
        data,
        batch_size=batch_size,
        verbose=True
    )
    
    print(f"\nProcessed {len(results)} items with estimated batch size")
    print()


# ============================================================================
# Example 5: Comparison with Direct optimize()
# ============================================================================

def example_5_comparison_with_optimize():
    """Compare batch processing with direct optimize()."""
    print("=" * 70)
    print("Example 5: When optimize() warns about memory")
    print("=" * 70)
    
    def returns_large_result(x):
        # Simulate large result (100KB)
        return [x] * 12500  # ~100KB
    
    data = list(range(1000))
    
    # First, see what optimize() says
    print("Running optimize() to analyze...")
    result = optimize(returns_large_result, data, sample_size=5, verbose=True)
    
    print(f"\nOptimization result:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  warnings: {result.warnings}")
    
    # If there's a memory warning, use batch processing
    has_memory_warning = any('memory' in w.lower() for w in result.warnings)
    
    if has_memory_warning:
        print("\n⚠️  Memory warning detected!")
        print("Using process_in_batches() instead...")
        
        results = process_in_batches(
            returns_large_result,
            data,
            batch_size=50,  # Process 50 items at a time
            verbose=True
        )
        print(f"\nSafely processed {len(results)} items in batches")
    else:
        print("\n✓ No memory warnings - safe to use normal Pool.map()")
    
    print()


# ============================================================================
# Example 6: Real-world Data Processing Pipeline
# ============================================================================

def example_6_data_processing_pipeline():
    """Realistic data processing pipeline."""
    print("=" * 70)
    print("Example 6: Real-world Data Processing Pipeline")
    print("=" * 70)
    
    def process_record(record):
        """Process a database record with multiple transformations."""
        # Simulate expensive processing
        time.sleep(0.001)  # 1ms per record
        
        return {
            'id': record['id'],
            'value': record['value'] ** 2,
            'processed': True,
            'metadata': {'steps': 5}
        }
    
    # Simulate 500 database records
    records = [{'id': i, 'value': i * 2} for i in range(500)]
    
    print("Processing database records in batches...")
    print("(This prevents memory accumulation of processed records)")
    
    start_time = time.time()
    
    results = process_in_batches(
        process_record,
        records,
        batch_size=100,
        sample_size=5,
        verbose=True
    )
    
    elapsed = time.time() - start_time
    
    print(f"\nCompleted in {elapsed:.2f} seconds")
    print(f"Processed {len(results)} records")
    print(f"Average: {elapsed/len(results)*1000:.2f}ms per record")
    print()


# ============================================================================
# Example 7: Combining with Progress Tracking
# ============================================================================

def example_7_with_progress_callback():
    """Use batch processing with progress callbacks."""
    print("=" * 70)
    print("Example 7: Batch Processing with Progress Tracking")
    print("=" * 70)
    
    # Progress tracking state
    progress_state = {'current_batch': 0, 'total_batches': 0}
    
    def progress_callback(phase, progress):
        """Track optimization progress."""
        if phase == "Starting optimization":
            progress_state['current_batch'] += 1
            print(f"  Batch {progress_state['current_batch']}/{progress_state['total_batches']}: Optimizing...")
    
    def compute(x):
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    data = list(range(200))
    batch_size = 50
    progress_state['total_batches'] = (len(data) + batch_size - 1) // batch_size
    
    print(f"Processing {len(data)} items in {progress_state['total_batches']} batches")
    print()
    
    results = process_in_batches(
        compute,
        data,
        batch_size=batch_size,
        progress_callback=progress_callback,
        verbose=False  # Use callback instead of verbose
    )
    
    print(f"\n✓ Completed all {len(results)} items")
    print()


# ============================================================================
# Run All Examples
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Batch Processing Examples")
    print("="*70 + "\n")
    
    example_1_basic_batch_processing()
    example_2_auto_batch_size()
    example_3_large_return_objects()
    example_4_manual_batch_size_estimation()
    example_5_comparison_with_optimize()
    example_6_data_processing_pipeline()
    example_7_with_progress_callback()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
