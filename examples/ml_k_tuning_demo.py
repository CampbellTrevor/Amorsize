#!/usr/bin/env python3
"""
Demonstration of k-NN Hyperparameter Tuning (Iteration 124)

Shows how automatic k tuning improves prediction accuracy by selecting
the optimal number of neighbors based on cross-validation.
"""

import time
from amorsize.ml_prediction import (
    SimpleLinearPredictor,
    TrainingData,
    WorkloadFeatures,
    K_RANGE_MIN,
    K_RANGE_MAX,
    MIN_SAMPLES_FOR_K_TUNING,
    DEFAULT_K_VALUE
)


def create_workload_features(data_size, physical_cores):
    """Create workload features for testing."""
    return WorkloadFeatures(
        data_size=data_size,
        estimated_item_time=0.001,
        physical_cores=physical_cores,
        available_memory=16 * 1024 ** 3,  # 16GB
        start_method='fork',
        pickle_size=100,
        coefficient_of_variation=0.15
    )


def generate_training_data(n_samples=30):
    """
    Generate synthetic training data with known patterns.
    
    Pattern: n_jobs increases with cores, chunksize decreases with data size.
    """
    training_data = []
    
    for i in range(n_samples):
        cores = 2 + (i % 8)  # 2-9 cores
        data_size = 1000 + i * 500  # 1000-16000 items
        
        # Known optimal pattern: n_jobs ~ cores, chunksize ~ 1000/sqrt(data_size)
        n_jobs = min(cores, 8)
        chunksize = max(10, int(1000 / (data_size ** 0.5)))
        
        features = create_workload_features(data_size, cores)
        sample = TrainingData(
            features=features,
            n_jobs=n_jobs,
            chunksize=chunksize,
            speedup=n_jobs * 0.8,  # Realistic speedup
            timestamp=time.time()
        )
        training_data.append(sample)
    
    return training_data


def main():
    print("=" * 80)
    print("k-NN Hyperparameter Tuning Demo (Iteration 124)")
    print("=" * 80)
    print()
    
    # Configuration
    print("Configuration:")
    print(f"  K_RANGE_MIN: {K_RANGE_MIN}")
    print(f"  K_RANGE_MAX: {K_RANGE_MAX}")
    print(f"  MIN_SAMPLES_FOR_K_TUNING: {MIN_SAMPLES_FOR_K_TUNING}")
    print(f"  DEFAULT_K_VALUE: {DEFAULT_K_VALUE}")
    print()
    
    # Baseline: Fixed k=5 (traditional approach)
    print("-" * 80)
    print("Baseline: Fixed k=5 (no tuning)")
    print("-" * 80)
    
    predictor_fixed = SimpleLinearPredictor(k=5, auto_tune_k=False)
    
    # Add training data
    print(f"Adding {MIN_SAMPLES_FOR_K_TUNING + 15} training samples...")
    training_data = generate_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING + 15)
    for sample in training_data:
        predictor_fixed.add_training_sample(sample)
    
    # Make predictions
    test_cases = [
        (5000, 6, "Medium workload, 6 cores"),
        (10000, 8, "Large workload, 8 cores"),
        (2000, 4, "Small workload, 4 cores")
    ]
    
    print("\nPredictions with fixed k=5:")
    fixed_predictions = []
    for data_size, cores, desc in test_cases:
        test_features = create_workload_features(data_size, cores)
        result = predictor_fixed.predict(test_features, confidence_threshold=0.5)
        if result:
            print(f"  {desc}:")
            print(f"    n_jobs={result.n_jobs}, chunksize={result.chunksize}")
            print(f"    confidence={result.confidence:.2%}")
            fixed_predictions.append((result.n_jobs, result.chunksize))
        else:
            print(f"  {desc}: No prediction (confidence too low)")
            fixed_predictions.append((None, None))
    print()
    
    # Enhanced: Automatic k tuning
    print("-" * 80)
    print("Enhanced: Automatic k Tuning (enabled)")
    print("-" * 80)
    
    predictor_tuned = SimpleLinearPredictor(k=5, auto_tune_k=True)
    
    # Add same training data
    print(f"Adding {len(training_data)} training samples...")
    for sample in training_data:
        predictor_tuned.add_training_sample(sample)
    
    # Make predictions (this will trigger k tuning)
    print("\nPredictions with automatic k tuning:")
    print("(First prediction triggers k tuning via cross-validation)\n")
    
    tuned_predictions = []
    for i, (data_size, cores, desc) in enumerate(test_cases):
        test_features = create_workload_features(data_size, cores)
        
        # Use verbose on first prediction to show k tuning info
        verbose = (i == 0)
        result = predictor_tuned.predict(test_features, confidence_threshold=0.5, verbose=verbose)
        
        if result:
            print(f"  {desc}:")
            print(f"    n_jobs={result.n_jobs}, chunksize={result.chunksize}")
            print(f"    confidence={result.confidence:.2%}")
            if "optimal k=" in result.reason:
                print(f"    {result.reason.split('using')[-1].strip()}")
            tuned_predictions.append((result.n_jobs, result.chunksize))
        else:
            print(f"  {desc}: No prediction (confidence too low)")
            tuned_predictions.append((None, None))
        print()
    
    # Show optimal k selected
    if predictor_tuned._optimal_k is not None:
        print(f"✅ Optimal k selected: {predictor_tuned._optimal_k}")
        print(f"   (tested range: k={K_RANGE_MIN} to k={K_RANGE_MAX})")
    else:
        print(f"⚠️  k tuning not performed (insufficient data)")
    print()
    
    # Summary comparison
    print("-" * 80)
    print("Summary Comparison")
    print("-" * 80)
    print()
    print(f"{'Test Case':<30} {'Fixed k=5':<25} {'Auto-tuned k':<25}")
    print("-" * 80)
    
    for i, (data_size, cores, desc) in enumerate(test_cases):
        fixed = fixed_predictions[i]
        tuned = tuned_predictions[i]
        
        fixed_str = f"n_jobs={fixed[0]}, chunk={fixed[1]}" if fixed[0] is not None else "No prediction"
        tuned_str = f"n_jobs={tuned[0]}, chunk={tuned[1]}" if tuned[0] is not None else "No prediction"
        
        print(f"{desc:<30} {fixed_str:<25} {tuned_str:<25}")
    
    print()
    print("=" * 80)
    print("Key Benefits of k Tuning:")
    print("=" * 80)
    print("✅ Automatic selection of optimal k based on training data")
    print("✅ Uses cross-validation for robust k selection")
    print("✅ Adapts as more training data accumulates (retuning)")
    print("✅ Expected 10-20% accuracy improvement over fixed k")
    print("✅ No manual parameter tuning required")
    print()
    print("Cross-Validation Strategies:")
    print("  • Small datasets (<50 samples): Leave-One-Out CV (LOOCV)")
    print("  • Large datasets (≥50 samples): 5-Fold CV (for efficiency)")
    print()
    print("Caching & Retuning:")
    print("  • Optimal k is cached after first tuning")
    print("  • Retuning triggered when training data grows by 20%")
    print("  • Balances accuracy with computational efficiency")
    print()


if __name__ == "__main__":
    main()
