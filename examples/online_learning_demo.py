#!/usr/bin/env python3
"""
Online Learning Demo for Amorsize

This example demonstrates how online learning improves ML predictions over time
by learning from actual execution results.

Key Features Demonstrated:
1. Initial execution without ML predictions (dry-run sampling)
2. Subsequent executions use ML predictions (10-100x faster)
3. Online learning updates the model with actual results
4. Model improves with more executions
5. Comparison of prediction accuracy over time

Run this example to see how the ML model learns and improves!
"""

import time
from pathlib import Path

from amorsize import execute, optimize
from amorsize.ml_prediction import (
    predict_parameters,
    load_ml_training_data,
    update_model_from_execution,
    _get_ml_cache_dir
)


# Example workload functions
def cpu_intensive_small(x):
    """Small CPU-intensive workload."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


def cpu_intensive_medium(x):
    """Medium CPU-intensive workload."""
    result = 0
    for i in range(500):
        result += x ** 2
    return result


def cpu_intensive_large(x):
    """Large CPU-intensive workload."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def demo_basic_online_learning():
    """Demonstrate basic online learning functionality."""
    print("=" * 80)
    print("DEMO 1: Basic Online Learning")
    print("=" * 80)
    print()
    
    print("This demo shows how online learning updates the model after each execution.")
    print()
    
    # Clear training data to start fresh
    cache_dir = _get_ml_cache_dir()
    for f in cache_dir.glob("ml_training_*.json"):
        f.unlink()
    
    print(f"Training samples before: {len(load_ml_training_data())}")
    print()
    
    # First execution - will use dry-run sampling
    print("Execution 1: Running with online learning enabled...")
    data1 = range(1000)
    results1 = execute(
        cpu_intensive_small,
        data1,
        verbose=True,
        enable_online_learning=True
    )
    print(f"Processed {len(results1)} items")
    print()
    
    print(f"Training samples after execution 1: {len(load_ml_training_data())}")
    print()
    
    # Second execution - may use ML prediction
    print("Execution 2: Running similar workload...")
    data2 = range(1200)
    results2 = execute(
        cpu_intensive_small,
        data2,
        verbose=True,
        enable_online_learning=True
    )
    print(f"Processed {len(results2)} items")
    print()
    
    print(f"Training samples after execution 2: {len(load_ml_training_data())}")
    print()
    
    print("✓ Model has been updated with actual execution results!")
    print()


def demo_model_improvement_over_time():
    """Demonstrate how the model improves with more data."""
    print("=" * 80)
    print("DEMO 2: Model Improvement Over Time")
    print("=" * 80)
    print()
    
    print("This demo shows how prediction confidence increases with more training data.")
    print()
    
    # Clear training data
    cache_dir = _get_ml_cache_dir()
    for f in cache_dir.glob("ml_training_*.json"):
        f.unlink()
    
    # Execute multiple times with different data sizes
    data_sizes = [500, 1000, 1500, 2000, 2500]
    
    for i, size in enumerate(data_sizes, 1):
        print(f"Execution {i}: Processing {size} items...")
        
        data = range(size)
        
        # Check if ML prediction is available
        prediction = predict_parameters(
            func=cpu_intensive_medium,
            data_size=size,
            estimated_item_time=0.001,
            verbose=False
        )
        
        if prediction:
            print(f"  ML Prediction available: n_jobs={prediction.n_jobs}, "
                  f"chunksize={prediction.chunksize}, confidence={prediction.confidence:.1%}")
        else:
            print("  ML Prediction: Not available (will use dry-run sampling)")
        
        # Execute with online learning
        results = execute(
            cpu_intensive_medium,
            data,
            verbose=False,
            enable_online_learning=True
        )
        
        training_samples = len(load_ml_training_data())
        print(f"  Training samples: {training_samples}")
        print()
    
    print(f"✓ Final training samples: {len(load_ml_training_data())}")
    print("✓ Model has learned from actual execution patterns!")
    print()


def demo_different_workload_types():
    """Demonstrate online learning with different workload types."""
    print("=" * 80)
    print("DEMO 3: Learning from Different Workload Types")
    print("=" * 80)
    print()
    
    print("This demo shows how the model learns from different workload characteristics.")
    print()
    
    workloads = [
        ("Small", cpu_intensive_small, 1000),
        ("Medium", cpu_intensive_medium, 1000),
        ("Large", cpu_intensive_large, 500),
    ]
    
    for name, func, size in workloads:
        print(f"Executing {name} workload ({size} items)...")
        
        data = range(size)
        results = execute(
            func,
            data,
            verbose=True,
            enable_online_learning=True
        )
        
        print(f"Completed: {len(results)} items processed")
        print()
    
    print(f"✓ Model trained on {len(load_ml_training_data())} diverse workloads")
    print()


def demo_prediction_accuracy_tracking():
    """Demonstrate tracking prediction accuracy over time."""
    print("=" * 80)
    print("DEMO 4: Prediction Accuracy Tracking")
    print("=" * 80)
    print()
    
    print("This demo shows how to track prediction accuracy as the model learns.")
    print()
    
    # Ensure we have some training data
    if len(load_ml_training_data()) < 3:
        print("Building initial training data...")
        for size in [500, 1000, 1500]:
            execute(
                cpu_intensive_medium,
                range(size),
                verbose=False,
                enable_online_learning=True
            )
        print(f"Training samples: {len(load_ml_training_data())}")
        print()
    
    # Now test prediction vs actual
    test_size = 1200
    
    print(f"Testing prediction for {test_size} items...")
    
    # Get ML prediction
    prediction = predict_parameters(
        func=cpu_intensive_medium,
        data_size=test_size,
        estimated_item_time=0.001,
        verbose=True
    )
    
    if prediction:
        print(f"\nML Prediction:")
        print(f"  n_jobs: {prediction.n_jobs}")
        print(f"  chunksize: {prediction.chunksize}")
        print(f"  confidence: {prediction.confidence:.1%}")
        print(f"  feature_match_score: {prediction.feature_match_score:.1%}")
    
    # Get actual optimization result
    print("\nRunning actual optimization...")
    result = optimize(
        func=cpu_intensive_medium,
        data=range(test_size),
        verbose=True
    )
    
    print(f"\nActual Optimization:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    
    if prediction:
        # Compare prediction vs actual
        n_jobs_error = abs(prediction.n_jobs - result.n_jobs)
        chunksize_error = abs(prediction.chunksize - result.chunksize)
        
        print(f"\nPrediction Accuracy:")
        print(f"  n_jobs error: {n_jobs_error} workers")
        print(f"  chunksize error: {chunksize_error} items")
        
        if n_jobs_error <= 1 and chunksize_error <= 50:
            print("  ✓ Excellent prediction accuracy!")
        elif n_jobs_error <= 2 and chunksize_error <= 100:
            print("  ✓ Good prediction accuracy")
        else:
            print("  ⚠ Prediction could be improved with more training data")
    
    print()


def demo_benchmark_ml_speedup():
    """Benchmark ML prediction speedup vs dry-run sampling."""
    print("=" * 80)
    print("DEMO 5: ML Prediction Speedup Benchmark")
    print("=" * 80)
    print()
    
    print("This demo measures the speedup from using ML prediction vs dry-run sampling.")
    print()
    
    # Ensure we have training data
    if len(load_ml_training_data()) < 5:
        print("Building training data for benchmark...")
        for size in [500, 1000, 1500, 2000, 2500]:
            execute(
                cpu_intensive_medium,
                range(size),
                verbose=False,
                enable_online_learning=True
            )
        print(f"Training samples: {len(load_ml_training_data())}")
        print()
    
    test_size = 1500
    
    # Time ML prediction
    print("Timing ML prediction...")
    start = time.time()
    prediction = predict_parameters(
        func=cpu_intensive_medium,
        data_size=test_size,
        estimated_item_time=0.001,
        verbose=False
    )
    ml_time = time.time() - start
    
    print(f"  ML prediction time: {ml_time*1000:.2f}ms")
    if prediction:
        print(f"  Result: n_jobs={prediction.n_jobs}, chunksize={prediction.chunksize}")
    
    # Time dry-run sampling (with use_ml_prediction=False)
    print("\nTiming dry-run sampling...")
    start = time.time()
    result = optimize(
        func=cpu_intensive_medium,
        data=range(test_size),
        verbose=False,
        use_ml_prediction=False  # Force dry-run
    )
    dryrun_time = time.time() - start
    
    print(f"  Dry-run time: {dryrun_time*1000:.2f}ms")
    print(f"  Result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    # Calculate speedup
    if ml_time > 0 and prediction:
        speedup = dryrun_time / ml_time
        print(f"\n✓ ML prediction is {speedup:.1f}x faster than dry-run sampling!")
    else:
        print("\n⚠ ML prediction not available (need more training data)")
    
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "AMORSIZE ONLINE LEARNING DEMO" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    print("This demo shows how online learning improves ML predictions over time.")
    print("The model learns from actual execution results and becomes more accurate.")
    print()
    
    demos = [
        ("Basic Online Learning", demo_basic_online_learning),
        ("Model Improvement", demo_model_improvement_over_time),
        ("Different Workloads", demo_different_workload_types),
        ("Accuracy Tracking", demo_prediction_accuracy_tracking),
        ("ML Speedup Benchmark", demo_benchmark_ml_speedup),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"⚠ Demo {i} ({name}) failed: {e}")
            print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total training samples collected: {len(load_ml_training_data())}")
    print()
    print("Key Benefits of Online Learning:")
    print("  ✓ No manual model retraining required")
    print("  ✓ Model automatically improves with each execution")
    print("  ✓ Learns from actual workload behavior, not estimates")
    print("  ✓ 10-100x faster optimization after initial training")
    print("  ✓ Adapts to different workload types automatically")
    print()
    print("Best Practices:")
    print("  • Enable online learning during development and testing")
    print("  • Let the model accumulate 10+ samples for good accuracy")
    print("  • Use verbose=True to monitor prediction confidence")
    print("  • Check prediction accuracy periodically")
    print()


if __name__ == "__main__":
    main()
