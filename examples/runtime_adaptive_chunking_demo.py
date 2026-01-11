"""
Demo: Runtime Adaptive Chunk Size Tuning

This example demonstrates the new runtime adaptive chunking feature (AdaptiveChunkingPool)
that dynamically adjusts chunk sizes DURING execution based on observed performance.

This is distinct from the static adaptive chunking (CV-based) done by optimize().

Use Case:
    When processing workloads with highly variable execution times, static chunk 
    sizes can lead to poor load balancing. The AdaptiveChunkingPool monitors 
    execution times and automatically adjusts chunk sizes to maintain optimal 
    throughput and minimize stragglers.
"""

import time
import random
from amorsize import optimize
from amorsize.adaptive_chunking import AdaptiveChunkingPool, create_adaptive_pool


def process_document(doc_length):
    """
    Simulate document processing with variable complexity.
    
    Longer documents take more time to process, creating a heterogeneous
    workload where execution times vary significantly.
    """
    # Simulate processing time proportional to document length
    processing_time = 0.001 * doc_length
    time.sleep(processing_time)
    
    # Return some result (e.g., word count, sentiment, etc.)
    return doc_length * 10  # Simulated result


def example_1_basic_usage():
    """
    Example 1: Basic usage of AdaptiveChunkingPool
    
    Shows how to use runtime adaptive chunking with optimize() recommendations.
    """
    print("=" * 70)
    print("Example 1: Basic Runtime Adaptive Chunking")
    print("=" * 70)
    
    # Create heterogeneous workload: mix of short and long documents
    # In real-world: document lengths vary (emails, articles, books, etc.)
    documents = []
    for _ in range(100):
        # Mix of short (1-5), medium (10-20), and long (50-100) documents
        length = random.choice([
            random.randint(1, 5),      # 33% short
            random.randint(10, 20),    # 33% medium
            random.randint(50, 100)    # 33% long
        ])
        documents.append(length)
    
    # Step 1: Use optimize() to get initial recommendations
    print("\nOptimizing parallelization parameters...")
    result = optimize(process_document, documents[:10], verbose=False)
    
    print(f"\nOptimizer recommends: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # Step 2: Use AdaptiveChunkingPool for runtime adaptation
    print("\nProcessing documents with runtime adaptive chunking...")
    start_time = time.perf_counter()
    
    with create_adaptive_pool(result.n_jobs, result.chunksize) as pool:
        results = pool.map(process_document, documents)
        stats = pool.get_stats()
    
    elapsed = time.perf_counter() - start_time
    
    print(f"\nProcessing complete in {elapsed:.2f}s")
    print(f"Processed {len(results)} documents")
    print(f"\nAdaptation statistics:")
    print(f"  Initial chunk size:  {result.chunksize}")
    print(f"  Final chunk size:    {stats['current_chunksize']}")
    print(f"  Adaptations made:    {stats['adaptation_count']}")
    print(f"  Avg chunk duration:  {stats['average_chunk_duration']:.3f}s")


def example_2_comparison():
    """
    Example 2: Compare adaptive vs non-adaptive chunking
    
    Demonstrates the performance benefit of adaptation for heterogeneous workloads.
    """
    print("\n" + "=" * 70)
    print("Example 2: Runtime Adaptive vs Non-Adaptive Comparison")
    print("=" * 70)
    
    # Create highly variable workload
    documents = []
    for i in range(200):
        # Create extreme variability: some very fast, some very slow
        if i % 10 == 0:
            length = random.randint(80, 120)  # Slow documents (10%)
        else:
            length = random.randint(1, 10)    # Fast documents (90%)
        documents.append(length)
    
    # Test 1: Without runtime adaptation
    print("\n[1/2] Processing WITHOUT runtime adaptation...")
    start_time = time.perf_counter()
    
    with AdaptiveChunkingPool(
        n_jobs=2,
        initial_chunksize=20,
        enable_adaptation=False  # Disabled
    ) as pool:
        results1 = pool.map(process_document, documents)
        stats1 = pool.get_stats()
    
    time_without = time.perf_counter() - start_time
    
    # Test 2: With runtime adaptation
    print("\n[2/2] Processing WITH runtime adaptation...")
    start_time = time.perf_counter()
    
    with AdaptiveChunkingPool(
        n_jobs=2,
        initial_chunksize=20,
        enable_adaptation=True,  # Enabled
        adaptation_rate=0.5  # Moderate adaptation speed
    ) as pool:
        results2 = pool.map(process_document, documents)
        stats2 = pool.get_stats()
    
    time_with = time.perf_counter() - start_time
    
    # Compare results
    print(f"\n{'Metric':<30} {'Without Adaptation':<20} {'With Adaptation':<20}")
    print("-" * 70)
    print(f"{'Execution time:':<30} {time_without:<20.2f} {time_with:<20.2f}")
    print(f"{'Chunk size:':<30} {stats1['current_chunksize']:<20} {stats2['current_chunksize']:<20}")
    print(f"{'Adaptations made:':<30} {stats1['adaptation_count']:<20} {stats2['adaptation_count']:<20}")
    print(f"{'Avg chunk duration:':<30} {stats1['average_chunk_duration']:<20.3f} {stats2['average_chunk_duration']:<20.3f}")
    
    if time_with < time_without:
        improvement = ((time_without - time_with) / time_without) * 100
        print(f"\n✓ Runtime adaptive chunking was {improvement:.1f}% faster!")
    else:
        print(f"\n✓ Both completed successfully (timing may vary in test environments)")


def example_3_custom_adaptation():
    """
    Example 3: Custom adaptation parameters
    
    Shows how to fine-tune runtime adaptation behavior for specific use cases.
    """
    print("\n" + "=" * 70)
    print("Example 3: Custom Runtime Adaptation Parameters")
    print("=" * 70)
    
    documents = [random.randint(1, 50) for _ in range(150)]
    
    # Scenario 1: Conservative adaptation (slow changes, stable)
    print("\nScenario 1: Conservative runtime adaptation (adaptation_rate=0.2)")
    with AdaptiveChunkingPool(
        n_jobs=2,
        initial_chunksize=15,
        adaptation_rate=0.2,  # Low rate = slow, stable adaptation
        target_chunk_duration=0.3
    ) as pool:
        results = pool.map(process_document, documents)
        stats = pool.get_stats()
    
    print(f"  Adaptations made: {stats['adaptation_count']}")
    print(f"  Final chunk size: {stats['current_chunksize']}")
    
    # Scenario 2: Aggressive adaptation (fast changes, responsive)
    print("\nScenario 2: Aggressive runtime adaptation (adaptation_rate=0.8)")
    with AdaptiveChunkingPool(
        n_jobs=2,
        initial_chunksize=15,
        adaptation_rate=0.8,  # High rate = fast, responsive adaptation
        target_chunk_duration=0.3
    ) as pool:
        results = pool.map(process_document, documents)
        stats = pool.get_stats()
    
    print(f"  Adaptations made: {stats['adaptation_count']}")
    print(f"  Final chunk size: {stats['current_chunksize']}")
    
    # Scenario 3: With bounds
    print("\nScenario 3: With min/max bounds")
    with AdaptiveChunkingPool(
        n_jobs=2,
        initial_chunksize=20,
        min_chunksize=5,   # Won't go below 5
        max_chunksize=30,  # Won't go above 30
        adaptation_rate=0.5
    ) as pool:
        results = pool.map(process_document, documents)
        stats = pool.get_stats()
    
    print(f"  Adaptations made: {stats['adaptation_count']}")
    print(f"  Final chunk size: {stats['current_chunksize']} (bounded between 5 and 30)")


def example_4_when_to_use():
    """
    Example 4: When to use runtime adaptive chunking
    
    Guidelines for choosing when runtime adaptive chunking provides benefits.
    """
    print("\n" + "=" * 70)
    print("Example 4: When to Use Runtime Adaptive Chunking")
    print("=" * 70)
    
    print("""
Runtime adaptive chunking (AdaptiveChunkingPool) is most beneficial for:

✓ GOOD USE CASES:
  • Document processing with varying lengths
  • Image processing with varying sizes/complexity
  • Database queries with varying complexity
  • API calls with unpredictable response times
  • Mixed computational tasks (simple + complex)
  • Any workload with CV (coefficient of variation) > 0.5

✗ LESS BENEFICIAL FOR:
  • Homogeneous workloads (consistent execution times)
  • Very small datasets (< 100 items)
  • When overhead of adaptation exceeds benefits
  • Extremely fast functions (< 1ms per item)

HOW TO DECIDE:
  1. Run optimize() with profile=True
  2. Check result.profile.coefficient_of_variation
  3. If CV > 0.5: Use AdaptiveChunkingPool for runtime adaptation
  4. If CV < 0.3: Regular Pool with static chunking is fine

NOTE: The static adaptive chunking (CV-based adjustment in optimize()) 
      runs BEFORE execution. Runtime adaptive chunking runs DURING execution.
      They complement each other!

EXAMPLE:
    """)
    
    # Demo with actual check
    def fast_uniform_func(x):
        time.sleep(0.001)
        return x * 2
    
    data = list(range(50))
    result = optimize(fast_uniform_func, data, profile=True)
    
    if result.profile:
        cv = result.profile.coefficient_of_variation
        print(f"  Measured CV: {cv:.2f}")
        
        if cv > 0.5:
            print("  → Recommendation: Use AdaptiveChunkingPool for runtime adaptation")
        elif cv > 0.3:
            print("  → Recommendation: Runtime adaptive chunking may help slightly")
        else:
            print("  → Recommendation: Regular Pool with static chunking is sufficient")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RUNTIME ADAPTIVE CHUNK SIZE TUNING DEMO")
    print("Dynamic adaptation during execution for heterogeneous workloads")
    print("=" * 70)
    
    # Run all examples
    example_1_basic_usage()
    example_2_comparison()
    example_3_custom_adaptation()
    example_4_when_to_use()
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
    print("\nKey takeaways:")
    print("  1. AdaptiveChunkingPool adjusts chunk size DURING execution")
    print("  2. Check CV in optimize() profile to decide if it will help")
    print("  3. Tune adaptation_rate for your specific workload")
    print("  4. Monitor get_stats() to verify improvement")
    print("  5. Complements static adaptive chunking from optimize()")
    print()
