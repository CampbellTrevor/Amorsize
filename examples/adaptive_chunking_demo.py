#!/usr/bin/env python3
"""
Adaptive Chunking Demo for Heterogeneous Workloads

This example demonstrates how Amorsize automatically detects workload
heterogeneity (varying execution times) and adapts the chunking strategy
for better load balancing.

Key Concepts:
- Coefficient of Variation (CV): Normalized measure of variability
- Homogeneous Workload: All items take similar time (CV < 0.3)
- Heterogeneous Workload: Items have varying execution times (CV > 0.5)
- Adaptive Chunking: Smaller chunks for heterogeneous workloads to enable
  better load distribution across workers
"""

import time
from multiprocessing import Pool
from amorsize import optimize


def example_1_homogeneous_workload():
    """
    Example 1: Homogeneous Workload (Consistent Execution Times)
    
    All items take approximately the same time to process.
    Result: Standard chunking strategy.
    """
    print("\n" + "="*70)
    print("Example 1: Homogeneous Workload")
    print("="*70)
    
    def consistent_processing(x):
        """Process all items with consistent time."""
        time.sleep(0.01)  # 10ms per item, very consistent
        return x ** 2
    
    data = list(range(100))
    
    print("\nOptimizing homogeneous workload...")
    result = optimize(consistent_processing, data, profile=True, verbose=True)
    
    print("\n" + "-"*70)
    print("Results:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  CV: {result.profile.coefficient_of_variation:.3f}")
    print(f"  Workload type: {'Heterogeneous' if result.profile.is_heterogeneous else 'Homogeneous'}")
    
    if result.profile.coefficient_of_variation < 0.3:
        print("\n✓ Low CV detected - using standard chunking strategy")
    
    return result


def example_2_heterogeneous_workload():
    """
    Example 2: Heterogeneous Workload (Varying Execution Times)
    
    Items have significantly different execution times.
    Result: Adaptive chunking with smaller chunks for better load balancing.
    """
    print("\n" + "="*70)
    print("Example 2: Heterogeneous Workload")
    print("="*70)
    
    def variable_processing(x):
        """Process items with highly variable execution times."""
        # Some items are fast (1ms), others slow (15ms)
        if x % 5 == 0:
            time.sleep(0.015)  # Slow items
        else:
            time.sleep(0.001)  # Fast items
        return x ** 2
    
    data = list(range(100))
    
    print("\nOptimizing heterogeneous workload...")
    result = optimize(variable_processing, data, profile=True, verbose=True)
    
    print("\n" + "-"*70)
    print("Results:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  CV: {result.profile.coefficient_of_variation:.3f}")
    print(f"  Workload type: {'Heterogeneous' if result.profile.is_heterogeneous else 'Homogeneous'}")
    
    if result.profile.coefficient_of_variation > 0.5:
        print(f"\n✓ High CV detected - using smaller chunks for load balancing")
        print(f"  Chunk reduction helps prevent idle workers while others process slow items")
    
    return result


def example_3_document_processing():
    """
    Example 3: Real-World Document Processing
    
    Simulate processing documents of varying lengths.
    Longer documents take more time.
    """
    print("\n" + "="*70)
    print("Example 3: Document Processing with Varying Lengths")
    print("="*70)
    
    # Simulate document lengths (words)
    document_lengths = [
        100, 150, 500, 200, 1000,  # Mix of short, medium, long
        120, 180, 800, 250, 150,
        100, 600, 200, 900, 140,
        110, 300, 700, 160, 400
    ] * 5  # 100 documents total
    
    def process_document(word_count):
        """Process document - longer documents take more time."""
        # Simulate: 1ms per 100 words
        processing_time = (word_count / 100) * 0.001
        time.sleep(processing_time)
        # Return word count as result
        return word_count
    
    print(f"\nProcessing {len(document_lengths)} documents...")
    print(f"  Shortest: {min(document_lengths)} words")
    print(f"  Longest: {max(document_lengths)} words")
    print(f"  Average: {sum(document_lengths) // len(document_lengths)} words")
    
    result = optimize(process_document, document_lengths, profile=True, verbose=True)
    
    print("\n" + "-"*70)
    print("Results:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  CV: {result.profile.coefficient_of_variation:.3f}")
    print(f"  Workload type: {'Heterogeneous' if result.profile.is_heterogeneous else 'Homogeneous'}")
    
    print("\n📊 Detailed Analysis:")
    print(result.explain())
    
    return result


def example_4_image_processing():
    """
    Example 4: Image Processing with Varying Sizes
    
    Simulate processing images of different sizes.
    Larger images take more time.
    """
    print("\n" + "="*70)
    print("Example 4: Image Processing with Varying Sizes")
    print("="*70)
    
    # Simulate image sizes (megapixels)
    image_sizes = [
        1.0, 2.0, 5.0, 1.5, 8.0,  # Mix of small, medium, large
        1.2, 3.0, 6.0, 2.0, 1.8,
        1.0, 4.0, 2.5, 7.0, 1.3,
        1.1, 3.5, 5.5, 2.2, 4.5
    ] * 3  # 60 images total
    
    def process_image(megapixels):
        """Process image - larger images take more time."""
        # Simulate: 2ms per megapixel
        processing_time = megapixels * 0.002
        time.sleep(processing_time)
        return megapixels
    
    print(f"\nProcessing {len(image_sizes)} images...")
    print(f"  Smallest: {min(image_sizes):.1f} MP")
    print(f"  Largest: {max(image_sizes):.1f} MP")
    print(f"  Average: {sum(image_sizes) / len(image_sizes):.1f} MP")
    
    result = optimize(process_image, image_sizes, profile=True, verbose=True)
    
    print("\n" + "-"*70)
    print("Results:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  CV: {result.profile.coefficient_of_variation:.3f}")
    print(f"  Workload type: {'Heterogeneous' if result.profile.is_heterogeneous else 'Homogeneous'}")
    
    return result


def example_5_comparison():
    """
    Example 5: Side-by-Side Comparison
    
    Compare homogeneous vs heterogeneous workloads.
    """
    print("\n" + "="*70)
    print("Example 5: Side-by-Side Comparison")
    print("="*70)
    
    # Homogeneous function
    def homogeneous_func(x):
        time.sleep(0.005)
        return x * 2
    
    # Heterogeneous function  
    def heterogeneous_func(x):
        if x % 3 == 0:
            time.sleep(0.010)  # Slow
        else:
            time.sleep(0.002)  # Fast
        return x * 2
    
    data = list(range(60))
    
    print("\nHomogeneous workload:")
    print("-" * 40)
    result_homo = optimize(homogeneous_func, data, profile=True)
    print(f"  CV: {result_homo.profile.coefficient_of_variation:.3f}")
    print(f"  Chunksize: {result_homo.chunksize}")
    print(f"  Type: Homogeneous (consistent times)")
    
    print("\nHeterogeneous workload:")
    print("-" * 40)
    result_hetero = optimize(heterogeneous_func, data, profile=True)
    print(f"  CV: {result_hetero.profile.coefficient_of_variation:.3f}")
    print(f"  Chunksize: {result_hetero.chunksize}")
    print(f"  Type: Heterogeneous (varying times)")
    
    print("\n" + "="*70)
    print("Comparison Summary:")
    print("="*70)
    print(f"Homogeneous CV:   {result_homo.profile.coefficient_of_variation:.3f} (low variance)")
    print(f"Heterogeneous CV: {result_hetero.profile.coefficient_of_variation:.3f} (high variance)")
    print(f"\nChunking Strategy:")
    print(f"  Homogeneous:   Standard chunks ({result_homo.chunksize})")
    print(f"  Heterogeneous: Adaptive chunks ({result_hetero.chunksize})")
    
    if result_hetero.chunksize < result_homo.chunksize:
        reduction = ((result_homo.chunksize - result_hetero.chunksize) / result_homo.chunksize) * 100
        print(f"\n✓ Heterogeneous workload uses {reduction:.0f}% smaller chunks")
        print(f"  This enables better load balancing and prevents idle workers")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("ADAPTIVE CHUNKING DEMONSTRATION")
    print("="*70)
    print("\nThis demo shows how Amorsize automatically detects workload")
    print("heterogeneity and adapts chunking for better performance.")
    
    # Run examples
    example_1_homogeneous_workload()
    example_2_heterogeneous_workload()
    example_3_document_processing()
    example_4_image_processing()
    example_5_comparison()
    
    print("\n" + "="*70)
    print("KEY TAKEAWAYS")
    print("="*70)
    print("1. Coefficient of Variation (CV) measures workload variability")
    print("   - CV < 0.3: Homogeneous (consistent execution times)")
    print("   - CV > 0.5: Heterogeneous (varying execution times)")
    print()
    print("2. Adaptive Chunking automatically adjusts for heterogeneity")
    print("   - Homogeneous: Standard chunks for efficiency")
    print("   - Heterogeneous: Smaller chunks for load balancing")
    print()
    print("3. Benefits of Adaptive Chunking:")
    print("   - Prevents worker idle time with heterogeneous workloads")
    print("   - Maintains efficiency with homogeneous workloads")
    print("   - No manual tuning required")
    print()
    print("4. Use profile=True to see detailed workload analysis")
    print("   - result.profile.coefficient_of_variation")
    print("   - result.profile.is_heterogeneous")
    print("   - result.explain() for full diagnostic report")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
