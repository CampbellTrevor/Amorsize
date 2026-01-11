"""
Cross-System Learning Demo - Iteration 117

This example demonstrates how Amorsize can leverage ML training data from 
similar hardware configurations, enabling faster cold-start on new systems.

Key Features:
- Automatic hardware fingerprinting
- System similarity scoring
- Cross-system data loading and weighting
- Intelligent filtering of dissimilar systems
"""

import time
from amorsize import (
    optimize,
    update_model_from_execution,
    load_ml_training_data,
    SystemFingerprint,
    MIN_SYSTEM_SIMILARITY,
    CROSS_SYSTEM_WEIGHT
)
from amorsize.ml_prediction import _get_current_system_fingerprint


def demo_workload(x):
    """A simple workload for demonstration."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def print_separator(title):
    """Print a section separator."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def demo_1_system_fingerprinting():
    """Demo 1: Understanding System Fingerprinting"""
    print_separator("Demo 1: System Fingerprinting")
    
    print("System fingerprinting captures hardware characteristics that affect")
    print("multiprocessing performance:\n")
    
    # Get current system fingerprint
    fp = _get_current_system_fingerprint()
    
    print(f"Current System:")
    print(f"  Physical cores: {fp.physical_cores}")
    print(f"  L3 cache: {fp.l3_cache_mb:.1f} MB")
    print(f"  NUMA nodes: {fp.numa_nodes}")
    print(f"  Memory bandwidth: {fp.memory_bandwidth_gb_s:.1f} GB/s")
    print(f"  Start method: {fp.start_method}")
    print(f"  System ID: {fp.system_id}")
    
    print("\nThis fingerprint uniquely identifies your hardware configuration.")
    print("It's used to match training data from similar systems.")


def demo_2_similarity_scoring():
    """Demo 2: System Similarity Scoring"""
    print_separator("Demo 2: System Similarity Scoring")
    
    print("Systems are compared using weighted Euclidean distance in normalized space:")
    print("  - Core count (weight 2.0): Most important for parallelism")
    print("  - L3 cache (weight 1.5): Affects data locality")
    print("  - NUMA nodes (weight 1.5): Affects memory access patterns")
    print("  - Memory bandwidth (weight 1.0): Affects memory-bound workloads")
    print("  - Start method (weight 1.0): Affects spawn overhead\n")
    
    # Create example systems
    current = _get_current_system_fingerprint()
    similar = SystemFingerprint(
        physical_cores=current.physical_cores,
        l3_cache_mb=current.l3_cache_mb,
        numa_nodes=current.numa_nodes,
        memory_bandwidth_gb_s=current.memory_bandwidth_gb_s + 5.0,  # Slightly different
        start_method=current.start_method
    )
    different = SystemFingerprint(
        physical_cores=current.physical_cores * 4,  # Much more cores
        l3_cache_mb=current.l3_cache_mb * 4,
        numa_nodes=4,
        memory_bandwidth_gb_s=200.0,
        start_method='fork'
    )
    
    similarity_similar = current.similarity(similar)
    similarity_different = current.similarity(different)
    
    print(f"Current system vs very similar system:")
    print(f"  Similarity score: {similarity_similar:.3f} (very high)")
    print(f"  Would be included: {'Yes' if similarity_similar >= MIN_SYSTEM_SIMILARITY else 'No'}")
    
    print(f"\nCurrent system vs very different system:")
    print(f"  Similarity score: {similarity_different:.3f}")
    print(f"  Would be included: {'Yes' if similarity_different >= MIN_SYSTEM_SIMILARITY else 'No'}")
    
    print(f"\nDefault minimum similarity threshold: {MIN_SYSTEM_SIMILARITY}")
    print("Systems below this threshold are filtered out to ensure quality predictions.")


def demo_3_building_training_data():
    """Demo 3: Building Training Data with Fingerprints"""
    print_separator("Demo 3: Building Training Data with Fingerprints")
    
    print("When you run optimize() and update the model, the system fingerprint")
    print("is automatically captured and saved with the training data.\n")
    
    data = list(range(5000))
    
    print(f"Optimizing workload with {len(data)} items...")
    result = optimize(demo_workload, data, verbose=False)
    
    print(f"  Optimal n_jobs: {result.n_jobs}")
    print(f"  Optimal chunksize: {result.chunksize}")
    print(f"  Estimated speedup: {result.estimated_speedup:.2f}x")
    
    # Simulate updating model (in real usage, use execute() with enable_online_learning=True)
    print("\nUpdating model with execution results...")
    
    # Get estimated item time from diagnostic profile
    estimated_time = 0.001  # Default estimate
    if hasattr(result, 'diagnostic') and result.diagnostic:
        estimated_time = result.diagnostic.avg_serial_time / len(data) if len(data) > 0 else 0.001
    
    success = update_model_from_execution(
        func=demo_workload,
        data_size=len(data),
        estimated_item_time=estimated_time,
        actual_n_jobs=result.n_jobs,
        actual_chunksize=result.chunksize,
        actual_speedup=result.estimated_speedup,
        verbose=False
    )
    
    if success:
        print("✓ Training data saved with system fingerprint")
        
        # Load and show fingerprint
        samples = load_ml_training_data(enable_cross_system=False, verbose=False)
        if samples:
            fp = samples[-1].system_fingerprint
            if fp:
                print(f"  Saved fingerprint: {fp}")


def demo_4_cross_system_data_loading():
    """Demo 4: Loading Data from Similar Systems"""
    print_separator("Demo 4: Cross-System Data Loading")
    
    print("When enable_cross_system=True (default), load_ml_training_data()")
    print("automatically loads and weights data from similar systems.\n")
    
    # Load training data with cross-system support
    print("Loading training data with cross-system learning enabled...")
    samples = load_ml_training_data(enable_cross_system=True, verbose=True)
    
    if not samples:
        print("\nNo training data found yet. Run more optimizations to build data.")
        return
    
    print(f"\n✓ Loaded {len(samples)} training samples")
    
    # Analyze sample weights
    current_fp = _get_current_system_fingerprint()
    local_samples = [s for s in samples 
                    if s.system_fingerprint and 
                    s.system_fingerprint.system_id == current_fp.system_id]
    cross_samples = [s for s in samples 
                    if s.system_fingerprint and 
                    s.system_fingerprint.system_id != current_fp.system_id]
    
    print(f"\nSample breakdown:")
    print(f"  Local system samples: {len(local_samples)} (weight = 1.0)")
    print(f"  Cross-system samples: {len(cross_samples)}")
    
    if cross_samples:
        avg_weight = sum(s.weight for s in cross_samples) / len(cross_samples)
        print(f"  Average cross-system weight: {avg_weight:.2f}")
        print(f"  Cross-system weight factor: {CROSS_SYSTEM_WEIGHT}")


def demo_5_benefits_of_cross_system_learning():
    """Demo 5: Benefits of Cross-System Learning"""
    print_separator("Demo 5: Benefits of Cross-System Learning")
    
    print("Cross-system learning provides several key benefits:\n")
    
    print("1. FASTER COLD-START ON NEW SYSTEMS")
    print("   - New systems can immediately benefit from similar system data")
    print("   - Reduces need for dry-run sampling on first use")
    print("   - Especially valuable for CI/CD environments with fresh VMs")
    
    print("\n2. BETTER GENERALIZATION")
    print("   - Model learns from diverse hardware configurations")
    print("   - Predictions more robust to hardware variations")
    print("   - Adapts to workload characteristics across systems")
    
    print("\n3. INTELLIGENT FILTERING")
    print("   - Only uses data from sufficiently similar systems")
    print(f"   - Minimum similarity threshold: {MIN_SYSTEM_SIMILARITY}")
    print("   - Prevents poor predictions from dissimilar hardware")
    
    print("\n4. WEIGHTED PREDICTIONS")
    print("   - Local system data gets full weight (1.0)")
    print(f"   - Similar systems get reduced weight ({CROSS_SYSTEM_WEIGHT})")
    print("   - Weight scales with similarity score")
    print("   - Ensures local data dominates when available")
    
    print("\n5. ZERO CONFIGURATION")
    print("   - Automatic hardware fingerprinting")
    print("   - Automatic similarity calculation")
    print("   - Automatic weight adjustment")
    print("   - Works transparently with existing API")


def demo_6_comparison_with_without():
    """Demo 6: Comparing With/Without Cross-System Learning"""
    print_separator("Demo 6: Comparing With/Without Cross-System Learning")
    
    print("Let's compare loading training data with and without cross-system learning:\n")
    
    # Without cross-system learning
    print("WITHOUT cross-system learning:")
    samples_local = load_ml_training_data(enable_cross_system=False, verbose=False)
    print(f"  Samples loaded: {len(samples_local)}")
    print(f"  All samples: Local system only")
    
    # With cross-system learning
    print("\nWITH cross-system learning:")
    samples_cross = load_ml_training_data(enable_cross_system=True, verbose=False)
    print(f"  Samples loaded: {len(samples_cross)}")
    
    if len(samples_cross) > len(samples_local):
        additional = len(samples_cross) - len(samples_local)
        print(f"  Additional samples: {additional} from similar systems")
        print(f"  Benefit: {additional / len(samples_local) * 100:.0f}% more training data!")
    else:
        print("  (No cross-system data available in this demo)")
    
    print("\nCross-system learning provides more training data when:")
    print("  - Running on a new system for the first time")
    print("  - Upgrading hardware to similar configuration")
    print("  - Using containerized environments (e.g., Docker, Kubernetes)")
    print("  - CI/CD pipelines with ephemeral runners")


def demo_7_tuning_similarity_threshold():
    """Demo 7: Tuning Similarity Threshold"""
    print_separator("Demo 7: Tuning Similarity Threshold (Advanced)")
    
    print("The similarity threshold controls how strict cross-system matching is:\n")
    
    print(f"Default threshold: {MIN_SYSTEM_SIMILARITY}")
    print("  - Conservative: Only very similar systems included")
    print("  - Ensures high-quality cross-system predictions")
    print("  - Recommended for most use cases")
    
    print("\nLower threshold (e.g., 0.6):")
    print("  - More permissive: Includes moderately similar systems")
    print("  - More training data, but potentially lower quality")
    print("  - Use when: Local data is very sparse")
    
    print("\nHigher threshold (e.g., 0.9):")
    print("  - Very strict: Only nearly identical systems included")
    print("  - Fewer samples, but highest quality")
    print("  - Use when: Prediction accuracy is critical")
    
    print("\nExample: Loading with different thresholds...")
    
    # Try different thresholds
    for threshold in [0.6, 0.8, 0.9]:
        samples = load_ml_training_data(
            enable_cross_system=True,
            min_similarity=threshold,
            verbose=False
        )
        print(f"  Threshold {threshold:.1f}: {len(samples)} samples loaded")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("  CROSS-SYSTEM LEARNING DEMONSTRATION")
    print("  Iteration 117 - Hardware-Aware Model Transfer")
    print("=" * 80)
    
    demos = [
        demo_1_system_fingerprinting,
        demo_2_similarity_scoring,
        demo_3_building_training_data,
        demo_4_cross_system_data_loading,
        demo_5_benefits_of_cross_system_learning,
        demo_6_comparison_with_without,
        demo_7_tuning_similarity_threshold,
    ]
    
    for i, demo in enumerate(demos, 1):
        try:
            demo()
        except Exception as e:
            print(f"\nError in demo {i}: {e}")
            print("Continuing with next demo...\n")
    
    print_separator("Summary")
    print("Cross-system learning enables:")
    print("  ✅ Faster optimization on new systems")
    print("  ✅ Better prediction generalization")
    print("  ✅ Intelligent hardware-based filtering")
    print("  ✅ Automatic weight adjustment")
    print("  ✅ Zero configuration required")
    print("\nIntegrated seamlessly with:")
    print("  - predict_parameters() [uses cross-system data automatically]")
    print("  - update_model_from_execution() [saves fingerprint automatically]")
    print("  - load_ml_training_data() [supports enable_cross_system parameter]")
    print("\nFor more information, see:")
    print("  - ITERATION_117_SUMMARY.md")
    print("  - CONTEXT.md (next recommendations)")


if __name__ == '__main__':
    main()
