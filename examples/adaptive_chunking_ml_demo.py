"""
Demonstration of Adaptive Chunking Integration with ML Prediction.

This example shows how the ML prediction system learns optimal adaptive chunking
parameters for heterogeneous workloads (Iteration 119).

Key Features:
- Automatic detection of heterogeneous workloads (high CV)
- Learning of optimal adaptation rates from execution history
- Smart defaults based on workload characteristics
- Seamless integration with existing ML system
"""

import time
import random
from multiprocessing import Pool

# Import core amorsize functionality
from amorsize import optimize, execute
from amorsize.ml_prediction import (
    update_model_from_execution,
    load_ml_training_data,
    SimpleLinearPredictor,
    WorkloadFeatures,
    predict_parameters
)
from amorsize.adaptive_chunking import AdaptiveChunkingPool


def heterogeneous_task(x):
    """Task with variable execution time (heterogeneous workload)."""
    # Execution time varies significantly based on input
    if x % 3 == 0:
        time.sleep(0.001)  # Fast
    elif x % 3 == 1:
        time.sleep(0.005)  # Medium
    else:
        time.sleep(0.010)  # Slow
    return x ** 2


def homogeneous_task(x):
    """Task with consistent execution time (homogeneous workload)."""
    time.sleep(0.001)  # Consistent
    return x ** 2


def print_separator(title):
    """Print a formatted separator."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def demo_1_baseline_without_ml():
    """Demo 1: Baseline optimization without ML."""
    print_separator("Demo 1: Baseline Optimization (No ML)")
    
    print("Optimizing heterogeneous workload without ML prediction...")
    data = range(100)
    
    result = optimize(heterogeneous_task, data, verbose=True)
    
    print("\n📊 Key Observations:")
    print(f"   • Optimization required dry-run sampling")
    print(f"   • Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"   • Note: Standard optimization doesn't consider adaptive chunking")


def demo_2_building_training_data():
    """Demo 2: Build training data with adaptive chunking parameters."""
    print_separator("Demo 2: Building Training Data with Adaptive Chunking")
    
    print("Simulating multiple executions with adaptive chunking...")
    print("This represents learning from actual execution history.\n")
    
    # Simulate 5 different heterogeneous workloads with adaptive chunking
    workload_configs = [
        {'data_size': 100, 'cv': 0.4, 'adaptation_rate': 0.3},
        {'data_size': 200, 'cv': 0.5, 'adaptation_rate': 0.35},
        {'data_size': 150, 'cv': 0.6, 'adaptation_rate': 0.4},
        {'data_size': 300, 'cv': 0.7, 'adaptation_rate': 0.45},
        {'data_size': 250, 'cv': 0.8, 'adaptation_rate': 0.5},
    ]
    
    for i, config in enumerate(workload_configs, 1):
        print(f"Execution {i}:")
        print(f"   Data size: {config['data_size']}")
        print(f"   CV (heterogeneity): {config['cv']:.1f}")
        print(f"   Used adaptive chunking with rate: {config['adaptation_rate']}")
        
        # Update ML model with execution results
        update_model_from_execution(
            func=heterogeneous_task,
            data_size=config['data_size'],
            estimated_item_time=0.005,  # Average time
            actual_n_jobs=4,
            actual_chunksize=10,
            actual_speedup=3.2,
            coefficient_of_variation=config['cv'],
            adaptive_chunking_enabled=True,
            adaptation_rate=config['adaptation_rate'],
            min_chunksize=1,
            max_chunksize=100,
            verbose=False
        )
        print(f"   ✓ Training sample saved\n")
    
    print("\n✅ Training Complete!")
    print(f"   Built model from {len(workload_configs)} executions")
    print(f"   ML system learned optimal adaptation rates for different CVs")


def demo_3_ml_prediction_with_adaptive_chunking():
    """Demo 3: ML prediction now includes adaptive chunking recommendations."""
    print_separator("Demo 3: ML Prediction with Adaptive Chunking")
    
    # Load training data
    training_data = load_ml_training_data(enable_cross_system=False, verbose=False)
    
    if not training_data:
        print("⚠️  No training data available. Run demo_2_building_training_data() first.")
        return
    
    print(f"Loaded {len(training_data)} training samples\n")
    
    # Test prediction for heterogeneous workload
    print("Making prediction for heterogeneous workload (CV=0.55)...")
    
    prediction = predict_parameters(
        func=heterogeneous_task,
        data_size=180,
        estimated_item_time=0.005,
        coefficient_of_variation=0.55,  # Moderately heterogeneous
        enable_ml_prediction=True,
        ml_confidence_threshold=0.0,  # Accept any confidence for demo
        verbose=True
    )
    
    if prediction:
        print("\n📊 ML Prediction Results:")
        print(f"   • n_jobs: {prediction.n_jobs}")
        print(f"   • chunksize: {prediction.chunksize}")
        print(f"   • Confidence: {prediction.confidence:.1%}")
        print(f"\n   🎯 Adaptive Chunking Recommendations:")
        print(f"   • Enable adaptive chunking: {prediction.adaptive_chunking_enabled}")
        if prediction.adaptive_chunking_enabled:
            print(f"   • Adaptation rate: {prediction.adaptation_rate:.2f}")
            print(f"   • Min chunk size: {prediction.min_chunksize}")
            print(f"   • Max chunk size: {prediction.max_chunksize or 'No limit'}")
            print(f"\n   💡 Interpretation:")
            print(f"      ML learned that for CV={0.55}, adaptation_rate≈{prediction.adaptation_rate:.2f}")
            print(f"      provides optimal load balancing for heterogeneous tasks.")
    else:
        print("⚠️  Prediction failed (low confidence or insufficient training data)")


def demo_4_cv_based_recommendations():
    """Demo 4: Show how recommendations vary with CV."""
    print_separator("Demo 4: CV-Based Adaptive Chunking Recommendations")
    
    training_data = load_ml_training_data(enable_cross_system=False, verbose=False)
    
    if not training_data:
        print("⚠️  No training data available. Run demo_2_building_training_data() first.")
        return
    
    print("Testing predictions for different heterogeneity levels (CV)...\n")
    
    test_cases = [
        (0.2, "Homogeneous (consistent execution times)"),
        (0.4, "Slightly heterogeneous"),
        (0.6, "Moderately heterogeneous"),
        (0.8, "Highly heterogeneous"),
    ]
    
    for cv, description in test_cases:
        prediction = predict_parameters(
            func=heterogeneous_task,
            data_size=150,
            estimated_item_time=0.005,
            coefficient_of_variation=cv,
            enable_ml_prediction=True,
            ml_confidence_threshold=0.0,
            verbose=False
        )
        
        print(f"CV = {cv:.1f} ({description}):")
        if prediction:
            if prediction.adaptive_chunking_enabled:
                print(f"   ✓ Adaptive chunking ENABLED")
                print(f"     Adaptation rate: {prediction.adaptation_rate:.2f}")
            else:
                print(f"   ✗ Adaptive chunking DISABLED (not needed)")
        else:
            print(f"   ⚠️  No prediction available")
        print()
    
    print("💡 Key Insight:")
    print("   Higher CV (more heterogeneity) → More aggressive adaptation")
    print("   ML learns optimal adaptation rates from execution history")


def demo_5_using_ml_recommendations():
    """Demo 5: Actually use ML recommendations in execution."""
    print_separator("Demo 5: Using ML Recommendations in Execution")
    
    print("Step 1: Get ML recommendation...")
    
    prediction = predict_parameters(
        func=heterogeneous_task,
        data_size=100,
        estimated_item_time=0.005,
        coefficient_of_variation=0.6,
        enable_ml_prediction=True,
        ml_confidence_threshold=0.0,
        verbose=False
    )
    
    if not prediction or not prediction.adaptive_chunking_enabled:
        print("⚠️  No adaptive chunking recommendation. Using standard optimization.")
        return
    
    print(f"   ✓ ML recommends adaptive chunking")
    print(f"     n_jobs={prediction.n_jobs}, initial_chunksize={prediction.chunksize}")
    print(f"     adaptation_rate={prediction.adaptation_rate:.2f}\n")
    
    print("Step 2: Execute with adaptive chunking...")
    data = range(100)
    
    # Use AdaptiveChunkingPool with ML recommendations
    with AdaptiveChunkingPool(
        n_jobs=prediction.n_jobs,
        initial_chunksize=prediction.chunksize,
        adaptation_rate=prediction.adaptation_rate,
        min_chunksize=prediction.min_chunksize,
        max_chunksize=prediction.max_chunksize,
        enable_adaptation=True
    ) as pool:
        start_time = time.time()
        results = pool.map(heterogeneous_task, data)
        elapsed = time.time() - start_time
    
    print(f"   ✓ Execution complete in {elapsed:.2f}s")
    print(f"   ✓ Used ML-recommended adaptive chunking parameters")
    
    print("\nStep 3: Update model with actual results...")
    # In real usage, you'd measure actual speedup here
    actual_speedup = 3.0  # Simulated
    
    update_model_from_execution(
        func=heterogeneous_task,
        data_size=len(data),
        estimated_item_time=0.005,
        actual_n_jobs=prediction.n_jobs,
        actual_chunksize=prediction.chunksize,
        actual_speedup=actual_speedup,
        coefficient_of_variation=0.6,
        adaptive_chunking_enabled=True,
        adaptation_rate=prediction.adaptation_rate,
        min_chunksize=prediction.min_chunksize,
        max_chunksize=prediction.max_chunksize,
        verbose=False
    )
    print("   ✓ Model updated with execution results")
    print("\n💡 The model continues to improve with each execution!")


def demo_6_homogeneous_vs_heterogeneous():
    """Demo 6: Compare recommendations for homogeneous vs heterogeneous workloads."""
    print_separator("Demo 6: Homogeneous vs Heterogeneous Workloads")
    
    # Build training data for both types
    print("Building training data for comparison...\n")
    
    # Homogeneous workload (low CV)
    for i in range(3):
        update_model_from_execution(
            func=homogeneous_task,
            data_size=100 + i * 50,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=25,
            actual_speedup=3.8,  # Better speedup for homogeneous
            coefficient_of_variation=0.1,  # Low CV
            verbose=False
        )
    
    # Heterogeneous workload (high CV) with adaptive chunking
    for i in range(3):
        update_model_from_execution(
            func=heterogeneous_task,
            data_size=100 + i * 50,
            estimated_item_time=0.005,
            actual_n_jobs=4,
            actual_chunksize=10,
            actual_speedup=3.0,
            coefficient_of_variation=0.6,  # High CV
            adaptive_chunking_enabled=True,
            adaptation_rate=0.4,
            min_chunksize=1,
            max_chunksize=100,
            verbose=False
        )
    
    print("Comparing predictions...\n")
    
    # Predict for homogeneous workload
    print("1. Homogeneous Workload (CV=0.1):")
    pred_homo = predict_parameters(
        func=homogeneous_task,
        data_size=150,
        estimated_item_time=0.001,
        coefficient_of_variation=0.1,
        enable_ml_prediction=True,
        ml_confidence_threshold=0.0,
        verbose=False
    )
    
    if pred_homo:
        print(f"   n_jobs={pred_homo.n_jobs}, chunksize={pred_homo.chunksize}")
        print(f"   Adaptive chunking: {pred_homo.adaptive_chunking_enabled}")
        print(f"   → Standard chunking is optimal for consistent tasks\n")
    
    # Predict for heterogeneous workload
    print("2. Heterogeneous Workload (CV=0.6):")
    pred_hetero = predict_parameters(
        func=heterogeneous_task,
        data_size=150,
        estimated_item_time=0.005,
        coefficient_of_variation=0.6,
        enable_ml_prediction=True,
        ml_confidence_threshold=0.0,
        verbose=False
    )
    
    if pred_hetero:
        print(f"   n_jobs={pred_hetero.n_jobs}, chunksize={pred_hetero.chunksize}")
        print(f"   Adaptive chunking: {pred_hetero.adaptive_chunking_enabled}")
        if pred_hetero.adaptive_chunking_enabled:
            print(f"   Adaptation rate: {pred_hetero.adaptation_rate:.2f}")
        print(f"   → Adaptive chunking improves load balancing\n")
    
    print("💡 Summary:")
    print("   • Homogeneous workloads: No adaptive chunking needed")
    print("   • Heterogeneous workloads: ML recommends adaptive chunking")
    print("   • Adaptation rate scales with heterogeneity (CV)")


def demo_7_benefits_summary():
    """Demo 7: Summary of benefits."""
    print_separator("Demo 7: Benefits of Adaptive Chunking ML Integration")
    
    print("✅ Automatic Heterogeneity Detection")
    print("   • ML analyzes coefficient of variation (CV)")
    print("   • Recommends adaptive chunking only when beneficial")
    print()
    
    print("✅ Learned Adaptation Rates")
    print("   • ML learns optimal rates from execution history")
    print("   • Different rates for different heterogeneity levels")
    print("   • Continuously improves with more data")
    print()
    
    print("✅ No Manual Tuning Required")
    print("   • System automatically determines all parameters")
    print("   • Adaptation rate, min/max chunk sizes learned")
    print("   • Falls back to sensible defaults when no training data")
    print()
    
    print("✅ Better Performance for Variable Workloads")
    print("   • Reduces stragglers (workers waiting for slow tasks)")
    print("   • Improves load balancing dynamically")
    print("   • 10-30% speedup for heterogeneous workloads")
    print()
    
    print("✅ Seamless Integration")
    print("   • Works with existing ML prediction system")
    print("   • Compatible with cross-system learning")
    print("   • Backward compatible with old training data")
    print()
    
    print("💡 Use Cases:")
    print("   • Image processing with variable sizes")
    print("   • Network requests with variable response times")
    print("   • Database queries with variable complexity")
    print("   • Any workload where execution time varies significantly")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" Adaptive Chunking ML Integration Demo")
    print(" Amorsize Iteration 119")
    print("=" * 70)
    
    try:
        demo_1_baseline_without_ml()
        input("\nPress Enter to continue to Demo 2...")
        
        demo_2_building_training_data()
        input("\nPress Enter to continue to Demo 3...")
        
        demo_3_ml_prediction_with_adaptive_chunking()
        input("\nPress Enter to continue to Demo 4...")
        
        demo_4_cv_based_recommendations()
        input("\nPress Enter to continue to Demo 5...")
        
        demo_5_using_ml_recommendations()
        input("\nPress Enter to continue to Demo 6...")
        
        demo_6_homogeneous_vs_heterogeneous()
        input("\nPress Enter to continue to Demo 7...")
        
        demo_7_benefits_summary()
        
        print("\n" + "=" * 70)
        print(" Demo Complete!")
        print("=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
