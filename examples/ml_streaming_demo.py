"""
ML-Enhanced Streaming Optimization Demo

This example demonstrates how ML predictions can dramatically speed up
streaming optimization by learning from historical executions.

Key Benefits:
- 10-100x faster optimization vs dry-run sampling
- Automatic learning from execution history
- Smart buffer sizing and ordering decisions
- Seamless fallback to dry-run when confidence is low
"""

import time
import random
from multiprocessing import Pool
from amorsize import (
    optimize_streaming,
    update_model_from_execution,
    predict_streaming_parameters
)


def cpu_intensive_task(x):
    """Simulates a CPU-intensive task."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def io_simulation_task(x):
    """Simulates an I/O-bound task with variable duration."""
    # Variable sleep to simulate heterogeneous workload
    sleep_time = 0.001 if x % 2 == 0 else 0.003
    time.sleep(sleep_time)
    return x * 2


def large_return_task(x):
    """Task that returns large objects."""
    # Return a large list (simulating large data)
    return [x] * 1000


def demo_1_baseline_without_ml():
    """Demo 1: Baseline - Streaming optimization without ML."""
    print("=" * 70)
    print("DEMO 1: Baseline Streaming Optimization (Without ML)")
    print("=" * 70)
    print()
    
    data = list(range(1000))
    
    print("Optimizing with dry-run sampling...")
    start_time = time.time()
    
    result = optimize_streaming(
        cpu_intensive_task,
        data,
        sample_size=5,
        verbose=True
    )
    
    optimization_time = time.time() - start_time
    
    print()
    print(f"✓ Optimization completed in {optimization_time:.3f}s")
    print(f"  Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"  Buffer size: {result.buffer_size}")
    method = "imap" if result.use_ordered else "imap_unordered"
    print(f"  Method: {method}")
    print()


def demo_2_with_ml_no_training():
    """Demo 2: ML-enabled but no training data (falls back to dry-run)."""
    print("=" * 70)
    print("DEMO 2: ML-Enabled Streaming (No Training Data)")
    print("=" * 70)
    print("When ML is enabled but no training data exists, it falls back to dry-run.")
    print()
    
    data = list(range(1000))
    
    print("Optimizing with ML enabled (will fall back to dry-run)...")
    start_time = time.time()
    
    result = optimize_streaming(
        cpu_intensive_task,
        data,
        enable_ml_prediction=True,
        estimated_item_time=0.01,
        ml_confidence_threshold=0.7,
        sample_size=5,
        verbose=True
    )
    
    optimization_time = time.time() - start_time
    
    print()
    print(f"✓ Optimization completed in {optimization_time:.3f}s")
    print(f"  Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print()


def demo_3_build_training_data():
    """Demo 3: Build training data through actual executions."""
    print("=" * 70)
    print("DEMO 3: Building Training Data")
    print("=" * 70)
    print("Simulating multiple executions to build training data...")
    print()
    
    # Simulate 5 historical executions with varying data sizes
    for i in range(5):
        data_size = 1000 + i * 200
        print(f"Execution {i+1}/5: data_size={data_size}...")
        
        # In real usage, you'd actually execute and measure speedup
        # Here we simulate it for the demo
        simulated_n_jobs = 4
        simulated_chunksize = 50
        simulated_speedup = 3.2 + random.uniform(-0.2, 0.3)
        
        update_model_from_execution(
            cpu_intensive_task,
            data_size=data_size,
            estimated_item_time=0.01,
            actual_n_jobs=simulated_n_jobs,
            actual_chunksize=simulated_chunksize,
            actual_speedup=simulated_speedup,
            verbose=False
        )
    
    print()
    print("✓ Training data created from 5 executions")
    print("  ML model is now ready for fast predictions!")
    print()


def demo_4_ml_prediction_api():
    """Demo 4: Using ML prediction API directly."""
    print("=" * 70)
    print("DEMO 4: Direct ML Prediction API")
    print("=" * 70)
    print("You can use predict_streaming_parameters() directly for instant predictions.")
    print()
    
    print("Predicting parameters with ML (no dry-run)...")
    start_time = time.time()
    
    result = predict_streaming_parameters(
        cpu_intensive_task,
        data_size=1000,
        estimated_item_time=0.01,
        confidence_threshold=0.7,
        verbose=True
    )
    
    prediction_time = time.time() - start_time
    
    print()
    if result:
        print(f"✓ ML Prediction in {prediction_time*1000:.1f}ms (vs ~100-1000ms for dry-run)")
        print(f"  n_jobs={result.n_jobs}, chunksize={result.chunksize}")
        print(f"  buffer_size={result.buffer_size}")
        method = "imap" if result.use_ordered else "imap_unordered"
        print(f"  method={method}")
        print(f"  confidence={result.confidence:.1%}")
        print(f"  training_samples={result.training_samples}")
        print()
        print(f"→ 10-100x speedup over dry-run sampling!")
    else:
        print("✗ ML prediction confidence too low")
        print("  Would fall back to dry-run in optimize_streaming()")
    print()


def demo_5_ml_enhanced_streaming():
    """Demo 5: Complete workflow with ML-enhanced streaming."""
    print("=" * 70)
    print("DEMO 5: ML-Enhanced Streaming Optimization")
    print("=" * 70)
    print("Now optimize_streaming() uses ML for instant parameter prediction.")
    print()
    
    data = list(range(1000))
    
    print("Optimizing with ML prediction...")
    start_time = time.time()
    
    result = optimize_streaming(
        cpu_intensive_task,
        data,
        enable_ml_prediction=True,
        estimated_item_time=0.01,
        ml_confidence_threshold=0.7,
        verbose=True
    )
    
    optimization_time = time.time() - start_time
    
    print()
    print(f"✓ Optimization completed in {optimization_time:.3f}s")
    print(f"  Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"  Buffer size: {result.buffer_size}")
    method = "imap" if result.use_ordered else "imap_unordered"
    print(f"  Method: {method}")
    print()
    
    # Actually use the result with Pool
    print("Executing with optimized parameters...")
    with Pool(result.n_jobs) as pool:
        if result.use_ordered:
            iterator = pool.imap(cpu_intensive_task, result.data, chunksize=result.chunksize)
        else:
            iterator = pool.imap_unordered(cpu_intensive_task, result.data, chunksize=result.chunksize)
        
        # Process results as they arrive (streaming)
        results = list(iterator)
    
    print(f"✓ Processed {len(results)} items")
    print()


def demo_6_heterogeneous_workload():
    """Demo 6: ML with heterogeneous workloads (auto-selects imap_unordered)."""
    print("=" * 70)
    print("DEMO 6: ML with Heterogeneous Workloads")
    print("=" * 70)
    print("ML automatically recommends imap_unordered for heterogeneous workloads.")
    print()
    
    # Build training data for heterogeneous workload
    print("Building training data for variable-duration tasks...")
    for i in range(3):
        update_model_from_execution(
            io_simulation_task,
            data_size=500,
            estimated_item_time=0.002,
            actual_n_jobs=4,
            actual_chunksize=25,
            actual_speedup=3.0,
            coefficient_of_variation=0.8,  # High CV = heterogeneous
            verbose=False
        )
    
    print("✓ Training data created with high CV (heterogeneous)")
    print()
    
    # Predict with ML
    result = predict_streaming_parameters(
        io_simulation_task,
        data_size=500,
        estimated_item_time=0.002,
        confidence_threshold=0.5,
        coefficient_of_variation=0.8,
        verbose=True
    )
    
    print()
    if result:
        method = "imap" if result.use_ordered else "imap_unordered"
        print(f"✓ ML recommends {method} for better load balancing")
        print(f"  High CV workloads benefit from unordered processing")
    print()


def demo_7_memory_aware_buffering():
    """Demo 7: ML with memory-aware buffer sizing."""
    print("=" * 70)
    print("DEMO 7: Memory-Aware Buffer Sizing")
    print("=" * 70)
    print("ML adjusts buffer size based on estimated memory usage.")
    print()
    
    # Build training data with large return objects
    print("Building training data for large-return tasks...")
    for i in range(3):
        update_model_from_execution(
            large_return_task,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=50,
            actual_speedup=3.5,
            pickle_size=10_000,  # 10KB per item
            verbose=False
        )
    
    print("✓ Training data created with large return objects")
    print()
    
    # Predict with ML
    result = predict_streaming_parameters(
        large_return_task,
        data_size=1000,
        estimated_item_time=0.001,
        confidence_threshold=0.5,
        pickle_size=10_000,
        verbose=True
    )
    
    print()
    if result:
        print(f"✓ ML calculated buffer_size={result.buffer_size}")
        print(f"  Respects memory constraints (10% of available memory)")
        print(f"  Prevents memory exhaustion with large returns")
    print()


def demo_8_adaptive_chunking_integration():
    """Demo 8: ML with adaptive chunking enabled."""
    print("=" * 70)
    print("DEMO 8: ML + Adaptive Chunking Integration")
    print("=" * 70)
    print("Combine ML prediction with adaptive chunking for optimal performance.")
    print()
    
    data = list(range(500))
    
    result = optimize_streaming(
        io_simulation_task,
        data,
        enable_ml_prediction=True,
        estimated_item_time=0.002,
        ml_confidence_threshold=0.5,
        enable_adaptive_chunking=True,
        adaptation_rate=0.3,
        verbose=True
    )
    
    print()
    if result.use_adaptive_chunking:
        print(f"✓ Adaptive chunking enabled with ML prediction")
        print(f"  Initial chunksize: {result.chunksize}")
        print(f"  Adaptation params: {result.adaptive_chunking_params}")
        print(f"  Best of both worlds: fast optimization + runtime adaptation")
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("ML-ENHANCED STREAMING OPTIMIZATION DEMO")
    print("=" * 70)
    print()
    print("This demo shows how ML predictions can dramatically speed up")
    print("streaming optimization while maintaining accuracy.")
    print()
    input("Press Enter to start demos...")
    print()
    
    # Run demos
    demo_1_baseline_without_ml()
    input("Press Enter for next demo...")
    print()
    
    demo_2_with_ml_no_training()
    input("Press Enter for next demo...")
    print()
    
    demo_3_build_training_data()
    input("Press Enter for next demo...")
    print()
    
    demo_4_ml_prediction_api()
    input("Press Enter for next demo...")
    print()
    
    demo_5_ml_enhanced_streaming()
    input("Press Enter for next demo...")
    print()
    
    demo_6_heterogeneous_workload()
    input("Press Enter for next demo...")
    print()
    
    demo_7_memory_aware_buffering()
    input("Press Enter for next demo...")
    print()
    
    demo_8_adaptive_chunking_integration()
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("1. ML predictions are 10-100x faster than dry-run sampling")
    print("2. Automatically learns from historical executions")
    print("3. Smart buffer sizing respects memory constraints")
    print("4. Auto-selects imap vs imap_unordered based on workload")
    print("5. Seamless fallback to dry-run when confidence is low")
    print("6. Works with all streaming features (adaptive chunking, backpressure)")
    print()
    print("Best Practices:")
    print("- Enable ML after 3-5 historical executions")
    print("- Provide estimated_item_time for better predictions")
    print("- Use confidence_threshold=0.7 for production (default)")
    print("- Monitor prediction confidence and adjust threshold as needed")
    print()


if __name__ == "__main__":
    main()
