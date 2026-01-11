"""
Feature Importance Analysis Demo

Demonstrates how to use feature importance analysis to understand which
workload characteristics most influence optimal parallelization parameters.

This helps users:
1. Understand what drives optimization decisions
2. Identify which workload features to focus on measuring accurately
3. Debug unexpected optimization results
4. Guide future feature engineering

Run with: python examples/feature_importance_demo.py
"""

import time
from amorsize.ml_prediction import (
    SimpleLinearPredictor,
    WorkloadFeatures,
    TrainingData,
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_importance_scores(importance_dict, title="Feature Importance"):
    """Print feature importance scores in a formatted table."""
    print(f"\n{title}:")
    print("-" * 70)
    
    # Sort by importance (highest first)
    sorted_features = sorted(
        importance_dict.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for feature, score in sorted_features:
        # Create bar visualization
        bar_length = int(score * 40)  # 40 chars max
        bar = "█" * bar_length
        print(f"{feature:25s} {score:5.3f} {bar}")
    
    print("-" * 70)


def demo_1_basic_feature_importance():
    """Demo 1: Basic variance-based feature importance."""
    print_section("Demo 1: Basic Variance-Based Feature Importance")
    
    print("Building training data with diverse workloads...")
    predictor = SimpleLinearPredictor(k=5)
    
    # Create training data with varying characteristics
    for i in range(20):
        features = WorkloadFeatures(
            data_size=1000 * (i + 1),  # Varies significantly
            estimated_item_time=0.001 + i * 0.002,  # Varies moderately
            physical_cores=8,  # Constant (low importance)
            available_memory=16 * 1024**3,  # Constant (low importance)
            start_method='fork' if i % 2 == 0 else 'spawn',  # Alternates
            pickle_size=500 + i * 50,  # Varies moderately
            coefficient_of_variation=0.05 + i * 0.05,  # Varies significantly
            function_complexity=1000  # Constant (low importance)
        )
        sample = TrainingData(
            features=features,
            n_jobs=2 + i % 8,
            chunksize=50 + i * 10,
            speedup=1.5 + i * 0.1,
            timestamp=time.time()
        )
        predictor.add_training_sample(sample)
    
    # Analyze variance-based importance
    importance = predictor.analyze_feature_importance()
    
    print_importance_scores(importance, "Variance-Based Feature Importance")
    
    print("\nKey Insights:")
    print("• High variance features: data_size, coefficient_of_variation")
    print("• These features vary most across workloads")
    print("• They have the most potential to discriminate between different optimizations")
    print("• Constant features (physical_cores, function_complexity) have 0 importance")


def demo_2_correlation_based_importance():
    """Demo 2: Correlation-based feature importance."""
    print_section("Demo 2: Correlation-Based Feature Importance")
    
    print("Building training data with clear correlations...")
    predictor = SimpleLinearPredictor(k=5)
    
    # Create data where:
    # - data_size strongly correlates with n_jobs
    # - execution_time strongly correlates with chunksize
    # - Other features are less correlated
    for i in range(20):
        data_size = 1000 * (i + 1)
        exec_time = 0.001 * (i + 1)
        
        features = WorkloadFeatures(
            data_size=data_size,
            estimated_item_time=exec_time,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            pickle_size=1000,
            coefficient_of_variation=0.2,
            function_complexity=500
        )
        
        # n_jobs increases with data_size
        n_jobs = min(2 + i // 2, 12)
        
        # chunksize increases with execution time
        chunksize = 50 + int(exec_time * 50000)
        
        sample = TrainingData(
            features=features,
            n_jobs=n_jobs,
            chunksize=chunksize,
            speedup=1.5 + i * 0.1,
            timestamp=time.time()
        )
        predictor.add_training_sample(sample)
    
    # Analyze correlation-based importance
    importance = predictor.analyze_feature_importance_correlation()
    
    print_importance_scores(importance['n_jobs'], "Feature Importance for n_jobs")
    print_importance_scores(importance['chunksize'], "Feature Importance for chunksize")
    print_importance_scores(importance['combined'], "Combined Feature Importance")
    
    print("\nKey Insights:")
    print("• data_size highly correlates with n_jobs (more data → more workers)")
    print("• execution_time correlates with chunksize (slower tasks → larger chunks)")
    print("• Combined importance shows overall predictive value")
    print("• This helps understand which features drive each parameter")


def demo_3_comparing_importance_methods():
    """Demo 3: Comparing variance vs correlation importance."""
    print_section("Demo 3: Comparing Variance vs Correlation Importance")
    
    print("Building diverse training dataset...")
    predictor = SimpleLinearPredictor(k=5)
    
    # Create realistic training data
    for i in range(30):
        features = WorkloadFeatures(
            data_size=500 + i * 500,
            estimated_item_time=0.001 + i * 0.0005,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork' if i % 3 == 0 else 'spawn',
            pickle_size=500 + i * 100,
            coefficient_of_variation=0.1 + i * 0.02,
            function_complexity=500 + i * 50
        )
        sample = TrainingData(
            features=features,
            n_jobs=min(2 + i // 4, 12),
            chunksize=50 + i * 5,
            speedup=1.5 + i * 0.05,
            timestamp=time.time()
        )
        predictor.add_training_sample(sample)
    
    # Get both types of importance
    variance_importance = predictor.analyze_feature_importance()
    correlation_importance = predictor.analyze_feature_importance_correlation()
    
    print("\nComparison Table:")
    print("-" * 90)
    print(f"{'Feature':<25s} {'Variance':<15s} {'Corr(n_jobs)':<15s} {'Corr(chunk)':<15s} {'Combined':<15s}")
    print("-" * 90)
    
    for feature in variance_importance.keys():
        var_score = variance_importance[feature]
        n_jobs_score = correlation_importance['n_jobs'][feature]
        chunk_score = correlation_importance['chunksize'][feature]
        combined_score = correlation_importance['combined'][feature]
        
        print(
            f"{feature:<25s} "
            f"{var_score:5.3f}{'  ':8s} "
            f"{n_jobs_score:5.3f}{'  ':8s} "
            f"{chunk_score:5.3f}{'  ':8s} "
            f"{combined_score:5.3f}"
        )
    
    print("-" * 90)
    
    print("\nKey Differences:")
    print("• Variance: Measures feature variability (how much it changes)")
    print("• Correlation: Measures predictive power (how well it predicts outcomes)")
    print("• High variance ≠ high correlation (a feature can vary but not be predictive)")
    print("• Use variance to find diverse features")
    print("• Use correlation to find predictive features")


def demo_4_identifying_key_features():
    """Demo 4: Using importance to identify key features for measurement."""
    print_section("Demo 4: Identifying Key Features for Measurement")
    
    print("Analyzing which features are most critical to measure accurately...\n")
    
    predictor = SimpleLinearPredictor(k=5)
    
    # Simulate realistic production workload data
    for i in range(50):
        features = WorkloadFeatures(
            data_size=1000 + i * 200,
            estimated_item_time=0.005 + i * 0.001,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            pickle_size=1000 + i * 100,
            coefficient_of_variation=0.15 + i * 0.01,
            function_complexity=800 + i * 20
        )
        sample = TrainingData(
            features=features,
            n_jobs=min(4 + i // 8, 12),
            chunksize=100 + i * 2,
            speedup=2.0 + i * 0.03,
            timestamp=time.time()
        )
        predictor.add_training_sample(sample)
    
    correlation_importance = predictor.analyze_feature_importance_correlation()
    combined = correlation_importance['combined']
    
    # Categorize features by importance
    critical_features = {k: v for k, v in combined.items() if v > 0.7}
    important_features = {k: v for k, v in combined.items() if 0.4 < v <= 0.7}
    minor_features = {k: v for k, v in combined.items() if v <= 0.4}
    
    print("Feature Categorization by Importance:\n")
    
    if critical_features:
        print("🔴 CRITICAL (> 0.7) - Measure these very accurately:")
        for feature, score in sorted(critical_features.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {feature}: {score:.3f}")
        print()
    
    if important_features:
        print("🟡 IMPORTANT (0.4-0.7) - Measure these reasonably well:")
        for feature, score in sorted(important_features.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {feature}: {score:.3f}")
        print()
    
    if minor_features:
        print("🟢 MINOR (< 0.4) - Rough estimates acceptable:")
        for feature, score in sorted(minor_features.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {feature}: {score:.3f}")
        print()
    
    print("\nRecommendations:")
    print("• Focus measurement effort on critical features")
    print("• Use sampling or estimation for minor features")
    print("• This reduces overhead while maintaining accuracy")


def demo_5_hardware_features_importance():
    """Demo 5: Understanding hardware feature importance."""
    print_section("Demo 5: Hardware Feature Importance")
    
    print("Analyzing importance of hardware-aware features...\n")
    
    predictor = SimpleLinearPredictor(k=5)
    
    # Simulate workloads on different hardware configurations
    configs = [
        # Config 1: Small system
        {'cores': 4, 'cache': 6.0, 'numa': 1, 'bandwidth': 25.0},
        # Config 2: Medium system
        {'cores': 16, 'cache': 16.0, 'numa': 2, 'bandwidth': 50.0},
        # Config 3: Large system
        {'cores': 64, 'cache': 64.0, 'numa': 4, 'bandwidth': 200.0},
    ]
    
    for config_idx, config in enumerate(configs):
        for i in range(15):
            # Create SystemTopology mock (simplified)
            from types import SimpleNamespace
            topology = SimpleNamespace(
                cache_info=SimpleNamespace(l3_size=config['cache'] * 1024 * 1024),
                numa_info=SimpleNamespace(
                    numa_nodes=config['numa'],
                    has_numa=config['numa'] > 1  # True when multiple NUMA nodes present
                ),
                memory_bandwidth=SimpleNamespace(bandwidth_gb_per_sec=config['bandwidth'])
            )
            
            features = WorkloadFeatures(
                data_size=10000 + i * 1000,
                estimated_item_time=0.01 + i * 0.001,
                physical_cores=config['cores'],
                available_memory=16 * 1024**3,
                start_method='fork',
                pickle_size=1000,
                coefficient_of_variation=0.2,
                function_complexity=1000,
                system_topology=topology
            )
            
            # Optimal parameters depend on hardware
            n_jobs = min(config['cores'], 4 + i)
            chunksize = 50 + config_idx * 50 + i * 5
            
            sample = TrainingData(
                features=features,
                n_jobs=n_jobs,
                chunksize=chunksize,
                speedup=1.5 + i * 0.1,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
    
    importance = predictor.analyze_feature_importance()
    correlation = predictor.analyze_feature_importance_correlation()
    
    # Focus on hardware features
    hardware_features = [
        'physical_cores',
        'l3_cache_size',
        'numa_nodes',
        'memory_bandwidth',
        'has_numa'
    ]
    
    print("Hardware Feature Importance:\n")
    print(f"{'Feature':<25s} {'Variance':<12s} {'Correlation':<12s}")
    print("-" * 50)
    
    for feature in hardware_features:
        var_score = importance[feature]
        corr_score = correlation['combined'][feature]
        print(f"{feature:<25s} {var_score:5.3f}  {'  ':3s} {corr_score:5.3f}")
    
    print("-" * 50)
    
    print("\nKey Insights:")
    print("• physical_cores has high importance (different systems have different cores)")
    print("• NUMA topology matters for multi-node systems")
    print("• Cache size affects memory-bound workloads")
    print("• Memory bandwidth impacts parallel throughput")
    print("• Hardware features enable cross-system learning")


def demo_6_debugging_with_importance():
    """Demo 6: Using feature importance to debug unexpected results."""
    print_section("Demo 6: Debugging with Feature Importance")
    
    print("Scenario: Optimizer is recommending unexpectedly low n_jobs\n")
    
    predictor = SimpleLinearPredictor(k=5)
    
    # Add training data
    for i in range(20):
        features = WorkloadFeatures(
            data_size=10000 + i * 1000,
            estimated_item_time=0.001,  # Very fast items
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='spawn',  # High spawn cost
            pickle_size=100000 + i * 10000,  # Large pickle size (high overhead)
            coefficient_of_variation=0.1,
            function_complexity=100
        )
        sample = TrainingData(
            features=features,
            n_jobs=2 + i % 3,  # Low n_jobs due to overhead
            chunksize=500 + i * 50,
            speedup=1.2 + i * 0.05,
            timestamp=time.time()
        )
        predictor.add_training_sample(sample)
    
    correlation = predictor.analyze_feature_importance_correlation()
    
    print("Investigating n_jobs recommendations...\n")
    print_importance_scores(correlation['n_jobs'], "Features Influencing n_jobs")
    
    print("\nDiagnostic Analysis:")
    
    # Check which features are most important
    n_jobs_importance = correlation['n_jobs']
    top_features = sorted(n_jobs_importance.items(), key=lambda x: x[1], reverse=True)[:3]
    
    print(f"\nTop 3 features influencing n_jobs:")
    for feature, score in top_features:
        print(f"  {feature}: {score:.3f}")
    
    # Explanation
    if n_jobs_importance.get('pickle_size', 0) > 0.5:
        print("\n🔍 Finding: pickle_size has high importance!")
        print("   → Large serialization overhead is limiting parallelism")
        print("   → Consider reducing data passed to workers")
        print("   → Or use shared memory approaches")
    
    if n_jobs_importance.get('execution_time', 0) > 0.5:
        print("\n🔍 Finding: execution_time has high importance!")
        print("   → Very fast items mean overhead dominates")
        print("   → Low n_jobs is correct to avoid overhead")
        print("   → Consider batching items or reducing parallelism")
    
    if n_jobs_importance.get('start_method', 0) > 0.5:
        print("\n🔍 Finding: start_method has high importance!")
        print("   → Spawn start method has high overhead")
        print("   → This limits beneficial parallelism")
        print("   → Consider using fork if possible")
    
    print("\n💡 Recommendation: Feature importance reveals why n_jobs is low")


def main():
    """Run all feature importance demos."""
    print("\n" + "=" * 70)
    print("  FEATURE IMPORTANCE ANALYSIS DEMONSTRATION")
    print("  Iteration 118: Understanding What Drives Optimization")
    print("=" * 70)
    
    try:
        demo_1_basic_feature_importance()
        demo_2_correlation_based_importance()
        demo_3_comparing_importance_methods()
        demo_4_identifying_key_features()
        demo_5_hardware_features_importance()
        demo_6_debugging_with_importance()
        
        print_section("Summary and Best Practices")
        print("Feature Importance Analysis provides:")
        print("  ✅ Understanding of what drives optimization decisions")
        print("  ✅ Guidance on which features to measure accurately")
        print("  ✅ Debugging tools for unexpected results")
        print("  ✅ Insights into workload characteristics")
        print()
        print("Best Practices:")
        print("  • Use variance importance to understand feature diversity")
        print("  • Use correlation importance to understand predictive power")
        print("  • Focus measurement effort on high-importance features")
        print("  • Use importance for debugging optimization decisions")
        print("  • Consider hardware features for cross-system optimization")
        print()
        print("Integration:")
        print("  • Works with all ML prediction features")
        print("  • Compatible with cross-system learning (Iteration 117)")
        print("  • Supports confidence calibration (Iteration 116)")
        print("  • Includes hardware-aware features (Iteration 114)")
        print("\n" + "=" * 70)
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
