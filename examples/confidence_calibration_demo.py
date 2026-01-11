"""
Demonstration of Confidence Calibration for ML Predictions (Iteration 116).

This example shows how the confidence calibration system adaptively adjusts
confidence thresholds based on actual prediction accuracy, optimizing the
ML vs dry-run trade-off over time.

Key Concepts:
- Tracks prediction accuracy over time
- Adjusts confidence threshold based on historical performance
- Enables smarter ML vs dry-run decisions
- Improves automatically without manual intervention
"""

import time
from amorsize import (
    optimize,
    predict_parameters,
    track_prediction_accuracy,
    get_calibration_stats
)


def cpu_bound_task(n):
    """Example CPU-bound task."""
    result = 0
    for i in range(n):
        result += i ** 2
    return result


def io_simulation_task(n):
    """Example task simulating I/O."""
    time.sleep(0.001 * n)
    return n * 2


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def demo_1_baseline_stats():
    """Demo 1: Check baseline calibration statistics."""
    print_section("Demo 1: Baseline Calibration Statistics")
    
    stats = get_calibration_stats(verbose=True)
    
    print(f"\nInitial calibration state:")
    print(f"  Adjusted threshold: {stats['adjusted_threshold']:.2f}")
    print(f"  Baseline threshold: {stats['baseline_threshold']:.2f}")
    print(f"  Sample count: {stats['sample_count']}")
    
    if stats['sample_count'] > 0:
        print(f"  Mean accuracy: {stats['mean_accuracy']:.1%}")
        print(f"\n📊 System has {stats['sample_count']} calibration samples")
    else:
        print(f"\n📊 No calibration data yet - system will use default threshold")


def demo_2_simulate_predictions():
    """Demo 2: Simulate a series of predictions and track accuracy."""
    print_section("Demo 2: Building Calibration Data")
    
    print("\nSimulating 15 predictions with varying accuracy...")
    print("(In practice, these would come from actual ML predictions)")
    
    # Simulate different prediction scenarios
    scenarios = [
        # (confidence, n_jobs_pred, chunksize_pred, n_jobs_actual, chunksize_actual, description)
        (0.85, 4, 100, 4, 100, "Perfect prediction at high confidence"),
        (0.82, 4, 95, 4, 100, "Near-perfect at high confidence"),
        (0.78, 4, 90, 4, 100, "Good at medium-high confidence"),
        (0.75, 4, 100, 4, 100, "Perfect at medium confidence"),
        (0.72, 4, 100, 4, 100, "Perfect at medium confidence"),
        (0.68, 4, 95, 4, 100, "Good at medium-low confidence"),
        (0.65, 4, 100, 4, 100, "Perfect at medium-low confidence"),
        (0.62, 4, 90, 4, 100, "Good at lower confidence"),
        (0.80, 6, 120, 4, 100, "Poor at high confidence"),
        (0.85, 4, 95, 4, 100, "Good at high confidence"),
        (0.70, 4, 100, 4, 100, "Perfect at medium confidence"),
        (0.65, 4, 100, 4, 100, "Perfect at medium-low confidence"),
        (0.88, 4, 100, 4, 100, "Perfect at high confidence"),
        (0.60, 4, 95, 4, 100, "Good at low confidence"),
        (0.75, 4, 100, 4, 100, "Perfect at medium confidence"),
    ]
    
    from amorsize.ml_prediction import PredictionResult
    
    for i, (conf, nj_pred, cs_pred, nj_actual, cs_actual, desc) in enumerate(scenarios, 1):
        # Create a mock prediction result
        prediction = PredictionResult(
            n_jobs=nj_pred,
            chunksize=cs_pred,
            confidence=conf,
            reason="Simulated prediction",
            training_samples=10,
            feature_match_score=0.8
        )
        
        # Track accuracy
        success = track_prediction_accuracy(
            prediction,
            actual_n_jobs=nj_actual,
            actual_chunksize=cs_actual,
            verbose=False
        )
        
        # Calculate accuracy for display
        n_jobs_err = abs(nj_pred - nj_actual)
        chunksize_err = abs(cs_pred - cs_actual)
        n_jobs_rel_err = n_jobs_err / max(1, nj_actual)
        chunksize_rel_err = chunksize_err / max(1, cs_actual)
        accuracy = 1.0 - ((n_jobs_rel_err + chunksize_rel_err) / 2.0)
        
        status = "✓" if success else "✗"
        print(f"{status} Sample {i:2d}: conf={conf:.2f}, accuracy={accuracy:.1%} - {desc}")
    
    print(f"\n📊 Tracked {len(scenarios)} predictions")


def demo_3_observe_calibration():
    """Demo 3: Observe how calibration adjusted the threshold."""
    print_section("Demo 3: Calibration Adjustment")
    
    stats = get_calibration_stats(verbose=False)
    
    print("\nCalibration system analysis:")
    print(f"  Sample count: {stats['sample_count']}")
    print(f"  Mean accuracy: {stats['mean_accuracy']:.1%}")
    print(f"  High-confidence accuracy (≥ threshold): {stats['high_confidence_accuracy']:.1%}")
    print(f"  Low-confidence accuracy (< threshold): {stats['low_confidence_accuracy']:.1%}")
    
    print(f"\nThreshold adjustment:")
    print(f"  Baseline threshold: {stats['baseline_threshold']:.2f}")
    print(f"  Adjusted threshold: {stats['adjusted_threshold']:.2f}")
    
    if stats['adjusted_threshold'] < stats['baseline_threshold']:
        diff = stats['baseline_threshold'] - stats['adjusted_threshold']
        print(f"  ⬇️  Decreased by {diff:.3f} (system is more confident)")
        print(f"  💡 Predictions with confidence ≥ {stats['adjusted_threshold']:.2f} will be used")
    elif stats['adjusted_threshold'] > stats['baseline_threshold']:
        diff = stats['adjusted_threshold'] - stats['baseline_threshold']
        print(f"  ⬆️  Increased by {diff:.3f} (system is more conservative)")
        print(f"  💡 Only predictions with confidence ≥ {stats['adjusted_threshold']:.2f} will be used")
    else:
        print(f"  ➡️  No change (threshold still at {stats['baseline_threshold']:.2f})")
    
    print(f"\nOptimal threshold (from analysis): {stats['optimal_threshold']:.2f}")
    print(f"  This is the threshold that maximizes accuracy above the threshold")


def demo_4_compare_thresholds():
    """Demo 4: Compare behavior with vs without calibration."""
    print_section("Demo 4: Impact of Calibration on Decision-Making")
    
    stats = get_calibration_stats(verbose=False)
    
    print("\nSimulating prediction decision with confidence = 0.68:")
    
    baseline_threshold = stats['baseline_threshold']
    adjusted_threshold = stats['adjusted_threshold']
    test_confidence = 0.68
    
    print(f"\n  Prediction confidence: {test_confidence:.2f}")
    print(f"\n  Without calibration (baseline threshold = {baseline_threshold:.2f}):")
    if test_confidence >= baseline_threshold:
        print(f"    ✅ Use ML prediction (confidence {test_confidence:.2f} ≥ {baseline_threshold:.2f})")
    else:
        print(f"    ❌ Fall back to dry-run (confidence {test_confidence:.2f} < {baseline_threshold:.2f})")
    
    print(f"\n  With calibration (adjusted threshold = {adjusted_threshold:.2f}):")
    if test_confidence >= adjusted_threshold:
        print(f"    ✅ Use ML prediction (confidence {test_confidence:.2f} ≥ {adjusted_threshold:.2f})")
        print(f"    💡 Saves time by avoiding dry-run!")
    else:
        print(f"    ❌ Fall back to dry-run (confidence {test_confidence:.2f} < {adjusted_threshold:.2f})")
    
    # Show impact
    if (test_confidence < baseline_threshold) and (test_confidence >= adjusted_threshold):
        print(f"\n  🎯 Calibration enables ML prediction for this case!")
        print(f"     This prediction would have fallen back to dry-run without calibration.")
    elif (test_confidence >= baseline_threshold) and (test_confidence < adjusted_threshold):
        print(f"\n  🛡️  Calibration prevents potentially inaccurate ML prediction!")
        print(f"     This prediction would have been used without calibration.")


def demo_5_continuous_improvement():
    """Demo 5: Show how calibration continues to improve over time."""
    print_section("Demo 5: Continuous Improvement")
    
    print("\nAdding 10 more high-quality predictions at 0.65 confidence...")
    
    from amorsize.ml_prediction import PredictionResult
    
    # Add more perfect predictions at lower confidence
    for i in range(10):
        prediction = PredictionResult(
            n_jobs=4,
            chunksize=100,
            confidence=0.65,
            reason="High-quality prediction",
            training_samples=15,
            feature_match_score=0.9
        )
        
        track_prediction_accuracy(
            prediction,
            actual_n_jobs=4,
            actual_chunksize=100,
            verbose=False
        )
    
    # Get updated stats
    stats_new = get_calibration_stats(verbose=False)
    
    print(f"\nUpdated calibration statistics:")
    print(f"  Sample count: {stats_new['sample_count']}")
    print(f"  Mean accuracy: {stats_new['mean_accuracy']:.1%}")
    print(f"  Adjusted threshold: {stats_new['adjusted_threshold']:.2f}")
    
    print(f"\n💡 The system continues to learn and adapt!")
    print(f"   As more predictions are tracked, the threshold becomes more accurate.")
    print(f"   This happens automatically without any manual intervention.")


def demo_6_real_world_usage():
    """Demo 6: Show how to use calibration in real optimization."""
    print_section("Demo 6: Real-World Usage Example")
    
    print("\nReal-world workflow:")
    print("  1. Call predict_parameters() with use_calibration=True (default)")
    print("  2. If prediction confidence is high, use it")
    print("  3. If prediction confidence is low, run dry-run optimization")
    print("  4. Call track_prediction_accuracy() to improve future predictions")
    
    print("\nExample code:")
    print("```python")
    print("# Try to predict parameters")
    print("prediction = predict_parameters(")
    print("    my_func, data_size=10000, estimated_item_time=0.001,")
    print("    use_calibration=True  # Use calibrated threshold (default)")
    print(")")
    print("")
    print("if prediction and prediction.confidence >= threshold:")
    print("    # Use ML prediction (fast)")
    print("    result = execute(my_func, data, n_jobs=prediction.n_jobs,")
    print("                     chunksize=prediction.chunksize)")
    print("else:")
    print("    # Fall back to dry-run optimization")
    print("    result = optimize(my_func, data, enable_ml_prediction=False)")
    print("    ")
    print("    # Track accuracy for calibration")
    print("    if prediction:")
    print("        track_prediction_accuracy(")
    print("            prediction, result.n_jobs, result.chunksize")
    print("        )")
    print("```")
    
    print("\n✨ The system learns and improves automatically!")


def demo_7_benefits_summary():
    """Demo 7: Summarize benefits of confidence calibration."""
    print_section("Demo 7: Benefits Summary")
    
    stats = get_calibration_stats(verbose=False)
    
    print("\n🎯 Key Benefits of Confidence Calibration:")
    print("\n  1. Adaptive Thresholds")
    print("     • Automatically adjusts based on actual prediction accuracy")
    print("     • No manual tuning required")
    
    print("\n  2. Better ML vs Dry-Run Trade-off")
    print("     • Uses ML when it's actually accurate")
    print("     • Falls back to dry-run when needed")
    print("     • Optimizes for both speed and accuracy")
    
    print("\n  3. Continuous Improvement")
    print("     • Learns from every prediction")
    print("     • Gets better over time")
    print("     • Adapts to your specific workloads")
    
    print("\n  4. Zero Configuration")
    print("     • Works automatically")
    print("     • No hyperparameters to tune")
    print("     • Just enable use_calibration=True")
    
    print("\n  5. Conservative Adjustment")
    print("     • Uses small adjustment steps to avoid oscillation")
    print("     • Requires minimum samples before adjusting")
    print("     • Stays within reasonable bounds [0.5, 0.95]")
    
    if stats['sample_count'] >= 10:
        print(f"\n📊 Current System Status:")
        print(f"   • {stats['sample_count']} predictions tracked")
        print(f"   • {stats['mean_accuracy']:.1%} mean accuracy")
        print(f"   • Threshold adjusted to {stats['adjusted_threshold']:.2f}")
        print(f"   • System is learning and improving!")
    else:
        print(f"\n📊 Current System Status:")
        print(f"   • {stats['sample_count']} predictions tracked")
        print(f"   • Need {10 - stats['sample_count']} more for full calibration")
        print(f"   • System will improve as more data is collected")


def main():
    """Run all demonstrations."""
    print("=" * 70)
    print("  CONFIDENCE CALIBRATION DEMONSTRATION (Iteration 116)")
    print("=" * 70)
    print("\nThis demo shows how the ML prediction system learns to optimize")
    print("its confidence threshold based on actual prediction accuracy.")
    
    try:
        demo_1_baseline_stats()
        demo_2_simulate_predictions()
        demo_3_observe_calibration()
        demo_4_compare_thresholds()
        demo_5_continuous_improvement()
        demo_6_real_world_usage()
        demo_7_benefits_summary()
        
        print("\n" + "=" * 70)
        print("  DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("\n✨ The calibration system enables intelligent, adaptive ML predictions!")
        print("   Run this demo again to see how the system continues to improve.")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
