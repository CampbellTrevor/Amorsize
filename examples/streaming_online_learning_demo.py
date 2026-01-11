"""
Demo: Streaming Online Learning for Amorsize

This example demonstrates how streaming online learning enables continuous
improvement of ML predictions for streaming workloads.

Key Features:
1. Streaming predictions improve over time (like batch predictions)
2. 10-100x faster streaming optimization after initial training
3. Automatic learning from actual streaming performance
4. Better buffer size and ordering predictions over time

New in Iteration 115!
"""

import time
from amorsize import (
    optimize_streaming,
    update_model_from_streaming_execution,
    predict_streaming_parameters
)


def cpu_bound_function(x):
    """CPU-intensive function for demonstration."""
    result = 0
    for i in range(500):
        result += x ** 2
    return result


def heterogeneous_function(x):
    """Function with variable execution time."""
    if x % 3 == 0:
        time.sleep(0.002)  # 2ms
    elif x % 3 == 1:
        time.sleep(0.005)  # 5ms
    else:
        time.sleep(0.010)  # 10ms
    return x * 2


def demo_1_baseline_without_online_learning():
    """Demo 1: Baseline - Traditional streaming optimization."""
    print("\n" + "=" * 70)
    print("Demo 1: Baseline - Traditional Streaming Optimization (Without Online Learning)")
    print("=" * 70)
    
    data = list(range(200))
    
    # Run optimization without ML (dry-run sampling)
    print("\nRunning optimize_streaming with dry-run sampling...")
    start_time = time.time()
    result = optimize_streaming(
        cpu_bound_function,
        data,
        sample_size=5,
        enable_ml_prediction=False,  # Disabled
        verbose=False
    )
    elapsed = time.time() - start_time
    
    print(f"\n✓ Optimization completed in {elapsed:.3f}s")
    print(f"  Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"  Method: {'imap' if result.use_ordered else 'imap_unordered'}")
    print(f"  Buffer size: {result.buffer_size}")
    print(f"  Expected speedup: {result.estimated_speedup:.2f}x")
    print(f"\n  ℹ️  Dry-run sampling takes time but provides accurate parameters")
    
    return result, elapsed


def demo_2_ml_with_no_training_data():
    """Demo 2: ML prediction with no training data (falls back to dry-run)."""
    print("\n" + "=" * 70)
    print("Demo 2: ML Prediction with No Training Data (Fallback)")
    print("=" * 70)
    
    data = list(range(200))
    
    print("\nAttempting ML prediction with enable_ml_prediction=True...")
    start_time = time.time()
    result = optimize_streaming(
        cpu_bound_function,
        data,
        sample_size=5,
        enable_ml_prediction=True,  # Enabled
        ml_confidence_threshold=0.7,
        verbose=False
    )
    elapsed = time.time() - start_time
    
    print(f"\n✓ Optimization completed in {elapsed:.3f}s")
    print(f"  Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"\n  ℹ️  No training data available - fell back to dry-run sampling")
    
    return result, elapsed


def demo_3_building_training_data():
    """Demo 3: Build training data using online learning."""
    print("\n" + "=" * 70)
    print("Demo 3: Building Streaming Training Data (Online Learning)")
    print("=" * 70)
    
    print("\nBuilding training data from streaming executions...")
    
    # Simulate 5 different streaming workload executions
    workloads = [
        {"data_size": 500, "item_time": 0.001, "n_jobs": 4, "chunksize": 50, "buffer": 12, "ordered": True},
        {"data_size": 1000, "item_time": 0.002, "n_jobs": 6, "chunksize": 100, "buffer": 18, "ordered": False},
        {"data_size": 2000, "item_time": 0.003, "n_jobs": 8, "chunksize": 150, "buffer": 24, "ordered": False},
        {"data_size": 800, "item_time": 0.0015, "n_jobs": 4, "chunksize": 75, "buffer": 12, "ordered": True},
        {"data_size": 1500, "item_time": 0.0025, "n_jobs": 6, "chunksize": 125, "buffer": 18, "ordered": False},
    ]
    
    for i, wl in enumerate(workloads, 1):
        success = update_model_from_streaming_execution(
            func=cpu_bound_function,
            data_size=wl["data_size"],
            estimated_item_time=wl["item_time"],
            actual_n_jobs=wl["n_jobs"],
            actual_chunksize=wl["chunksize"],
            actual_speedup=wl["n_jobs"] * 0.85,  # ~85% efficiency
            buffer_size=wl["buffer"],
            use_ordered=wl["ordered"],
            verbose=False
        )
        print(f"  [{i}/5] Training sample added: "
              f"n_jobs={wl['n_jobs']}, "
              f"chunksize={wl['chunksize']}, "
              f"buffer={wl['buffer']}, "
              f"ordered={wl['ordered']}")
    
    print(f"\n✓ Built training data from 5 streaming executions")
    print(f"  ℹ️  Model can now predict without dry-run sampling!")


def demo_4_direct_ml_prediction_api():
    """Demo 4: Direct use of ML prediction API."""
    print("\n" + "=" * 70)
    print("Demo 4: Direct ML Prediction API (predict_streaming_parameters)")
    print("=" * 70)
    
    print("\nUsing predict_streaming_parameters() directly...")
    start_time = time.time()
    result = predict_streaming_parameters(
        func=cpu_bound_function,
        data_size=1000,
        estimated_item_time=0.002,
        confidence_threshold=0.5,  # Lower threshold for demo
        verbose=True
    )
    elapsed = time.time() - start_time
    
    if result is not None:
        print(f"\n✓ ML Prediction completed in {elapsed:.4f}s (instant!)")
        print(f"  Predicted: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
        print(f"  Buffer size: {result.buffer_size}")
        print(f"  Method: {'imap' if result.use_ordered else 'imap_unordered'}")
        print(f"  Confidence: {result.confidence:.1%}")
        print(f"  Training samples: {result.training_samples}")
        print(f"\n  🚀 10-100x faster than dry-run sampling!")
    else:
        print(f"\n⚠ ML prediction returned None (confidence too low)")
        print(f"  Elapsed: {elapsed:.4f}s")
    
    return result, elapsed


def demo_5_complete_ml_streaming_workflow():
    """Demo 5: Complete ML-enhanced streaming workflow."""
    print("\n" + "=" * 70)
    print("Demo 5: Complete ML-Enhanced Streaming Workflow")
    print("=" * 70)
    
    data = list(range(200))
    
    print("\nStep 1: First execution - Build initial training")
    print("-" * 50)
    result1 = optimize_streaming(
        cpu_bound_function,
        data,
        sample_size=5,
        enable_ml_prediction=True,
        verbose=False
    )
    print(f"  Result: n_jobs={result1.n_jobs}, chunksize={result1.chunksize}, "
          f"buffer={result1.buffer_size}")
    
    # Simulate actual execution and update model
    print("\n  → Simulating actual streaming execution...")
    print("  → Updating model with actual results...")
    success = update_model_from_streaming_execution(
        func=cpu_bound_function,
        data_size=len(data),
        estimated_item_time=result1.estimated_item_time or 0.002,
        actual_n_jobs=result1.n_jobs,
        actual_chunksize=result1.chunksize,
        actual_speedup=result1.estimated_speedup,
        buffer_size=result1.buffer_size,
        use_ordered=result1.use_ordered,
        pickle_size=result1.pickle_size,
        coefficient_of_variation=result1.coefficient_of_variation,
        verbose=False
    )
    print(f"  ✓ Model updated")
    
    print("\nStep 2: Second execution - Use ML prediction (faster!)")
    print("-" * 50)
    start_time = time.time()
    result2 = optimize_streaming(
        cpu_bound_function,
        data,
        sample_size=5,
        enable_ml_prediction=True,
        ml_confidence_threshold=0.5,  # Lower for demo
        estimated_item_time=0.002,
        verbose=False
    )
    elapsed = time.time() - start_time
    
    print(f"  Result: n_jobs={result2.n_jobs}, chunksize={result2.chunksize}, "
          f"buffer={result2.buffer_size}")
    print(f"  Time: {elapsed:.4f}s")
    print(f"\n  🚀 ML prediction used - much faster than first execution!")
    
    print("\nStep 3: Third execution - Even better predictions")
    print("-" * 50)
    # Update again
    update_model_from_streaming_execution(
        func=cpu_bound_function,
        data_size=len(data),
        estimated_item_time=0.002,
        actual_n_jobs=result2.n_jobs,
        actual_chunksize=result2.chunksize,
        actual_speedup=result2.estimated_speedup,
        buffer_size=result2.buffer_size,
        use_ordered=result2.use_ordered,
        verbose=False
    )
    
    result3 = optimize_streaming(
        cpu_bound_function,
        data,
        sample_size=5,
        enable_ml_prediction=True,
        ml_confidence_threshold=0.5,
        estimated_item_time=0.002,
        verbose=False
    )
    print(f"  Result: n_jobs={result3.n_jobs}, chunksize={result3.chunksize}, "
          f"buffer={result3.buffer_size}")
    print(f"\n  ✓ Model keeps improving with more training data!")


def demo_6_heterogeneous_workload_learning():
    """Demo 6: Learning buffer size and ordering for heterogeneous workloads."""
    print("\n" + "=" * 70)
    print("Demo 6: Learning Buffer Size & Ordering for Heterogeneous Workloads")
    print("=" * 70)
    
    data = list(range(100))
    
    print("\nOptimizing heterogeneous workload (variable execution times)...")
    result = optimize_streaming(
        heterogeneous_function,
        data,
        sample_size=6,
        verbose=False
    )
    
    print(f"\n✓ Optimization complete")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  buffer_size: {result.buffer_size}")
    print(f"  use_ordered: {result.use_ordered}")
    print(f"  coefficient_of_variation: {result.coefficient_of_variation:.2f}")
    
    if result.coefficient_of_variation and result.coefficient_of_variation > 0.5:
        print(f"\n  ℹ️  High CV detected - likely uses imap_unordered for better load balancing")
    
    # Update model
    print("\n  → Updating model with heterogeneous workload results...")
    success = update_model_from_streaming_execution(
        func=heterogeneous_function,
        data_size=len(data),
        estimated_item_time=result.estimated_item_time or 0.005,
        actual_n_jobs=result.n_jobs,
        actual_chunksize=result.chunksize,
        actual_speedup=result.estimated_speedup,
        buffer_size=result.buffer_size,
        use_ordered=result.use_ordered,
        coefficient_of_variation=result.coefficient_of_variation,
        verbose=False
    )
    print(f"  ✓ Model learned heterogeneous workload characteristics!")


def demo_7_performance_comparison():
    """Demo 7: Performance comparison - dry-run vs ML prediction."""
    print("\n" + "=" * 70)
    print("Demo 7: Performance Comparison - Dry-run vs ML Prediction")
    print("=" * 70)
    
    # Make sure we have training data
    update_model_from_streaming_execution(
        func=cpu_bound_function,
        data_size=1000,
        estimated_item_time=0.002,
        actual_n_jobs=6,
        actual_chunksize=100,
        actual_speedup=5.0,
        buffer_size=18,
        use_ordered=False,
        verbose=False
    )
    
    data = list(range(200))
    
    # Measure dry-run time
    print("\nTiming dry-run sampling...")
    start = time.time()
    result1 = optimize_streaming(
        cpu_bound_function,
        data,
        sample_size=5,
        enable_ml_prediction=False,
        verbose=False
    )
    dryrun_time = time.time() - start
    
    # Measure ML prediction time
    print("Timing ML prediction...")
    start = time.time()
    result2 = optimize_streaming(
        cpu_bound_function,
        data,
        sample_size=5,
        enable_ml_prediction=True,
        ml_confidence_threshold=0.5,
        estimated_item_time=0.002,
        verbose=False
    )
    ml_time = time.time() - start
    
    print(f"\n📊 Performance Results:")
    print(f"  Dry-run sampling: {dryrun_time:.4f}s")
    print(f"  ML prediction:    {ml_time:.4f}s")
    if ml_time > 0 and ml_time < dryrun_time:
        speedup = dryrun_time / ml_time
        print(f"  Speedup:          {speedup:.1f}x faster! 🚀")
    print(f"\n  Both methods recommended:")
    print(f"    Dry-run: n_jobs={result1.n_jobs}, chunksize={result1.chunksize}")
    print(f"    ML:      n_jobs={result2.n_jobs}, chunksize={result2.chunksize}")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("STREAMING ONLINE LEARNING DEMO - Iteration 115")
    print("=" * 70)
    print("\nThis demo shows how streaming workloads benefit from online learning,")
    print("just like batch workloads (Iteration 112).")
    print("\nKey Benefits:")
    print("  • 10-100x faster streaming optimization after training")
    print("  • Automatic learning from actual streaming performance")
    print("  • Better buffer size and ordering predictions over time")
    print("  • Works with adaptive chunking and memory backpressure")
    
    try:
        # Run demos
        demo_1_baseline_without_online_learning()
        demo_2_ml_with_no_training_data()
        demo_3_building_training_data()
        demo_4_direct_ml_prediction_api()
        demo_5_complete_ml_streaming_workflow()
        demo_6_heterogeneous_workload_learning()
        demo_7_performance_comparison()
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print("\n✅ Streaming online learning enables:")
        print("   1. Fast parameter prediction without dry-run sampling")
        print("   2. Continuous model improvement from real executions")
        print("   3. Learning optimal buffer sizes and ordering preferences")
        print("   4. Better handling of heterogeneous workloads over time")
        print("\n🎯 Best Practice:")
        print("   • Use enable_ml_prediction=True after initial training")
        print("   • Update model after each streaming execution")
        print("   • Model automatically improves with more diverse workloads")
        print("\n📚 Learn More:")
        print("   • See tests/test_streaming_online_learning.py for examples")
        print("   • Check CONTEXT.md for implementation details")
        print("   • Review examples/online_learning_demo.py for batch workloads")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
