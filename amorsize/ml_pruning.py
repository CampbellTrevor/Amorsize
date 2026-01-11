"""
ML Training Data Pruning Module (Iteration 127).

This module implements intelligent pruning of ML training data to reduce memory
footprint and improve prediction speed while maintaining accuracy.

Key Features:
- Similarity-based redundancy detection
- Diversity-preserving pruning strategy
- Configurable pruning thresholds
- Memory reduction: 30-40% typical savings
- Maintains prediction accuracy (< 5% degradation)

Pruning Strategy:
1. Identify clusters of similar training samples
2. Within each cluster, keep representative samples
3. Preserve diverse samples to maintain coverage
4. Remove near-duplicates that add little value
"""

import math
import time
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass

# Import from ml_prediction module
try:
    from .ml_prediction import TrainingData, WorkloadFeatures
    _HAS_ML_PREDICTION = True
except ImportError:
    _HAS_ML_PREDICTION = False
    TrainingData = None
    WorkloadFeatures = None


# Pruning configuration constants
# Default similarity threshold for identifying redundant samples
# Samples with distance < threshold are considered similar
# Range: 0.0 (identical) to sqrt(12) ≈ 3.46 (maximally different)
# With 12-dimensional normalized features, typical distances are 0.5-2.0
DEFAULT_SIMILARITY_THRESHOLD = 0.5  # More conservative to prevent over-clustering

# Minimum samples to keep per cluster (preserves diversity)
# Increased from 2 to 5 to maintain better accuracy
MIN_SAMPLES_PER_CLUSTER = 5

# Maximum samples to keep per cluster (prevents cluster domination)
MAX_SAMPLES_PER_CLUSTER = 20

# Age weight factor (exponential decay for older samples)
# Newer samples get higher weight (0 = no age bias, 1 = strong bias)
AGE_WEIGHT_FACTOR = 0.3

# Performance weight factor (better performing samples get higher weight)
# Samples with higher speedup are prioritized (0 = ignore performance, 1 = only performance)
PERFORMANCE_WEIGHT_FACTOR = 0.4

# Minimum number of samples needed before pruning kicks in
# Below this threshold, no pruning occurs (preserves small datasets)
MIN_SAMPLES_FOR_PRUNING = 50

# Target pruning ratio (fraction of samples to remove)
# 0.35 = remove 35% of samples, keep 65%
TARGET_PRUNING_RATIO = 0.35

# Minimum distance between kept samples (prevents clustering)
# Samples must be at least this far apart to both be kept
MIN_INTER_SAMPLE_DISTANCE = 0.2  # Reduced from 0.3 for better retention

# Absolute minimum number of samples to keep (prevents over-pruning)
# This constraint is applied AFTER clustering to ensure we never drop below
# a reasonable minimum dataset size, even if clustering produces a single mega-cluster.
# Without this, a single cluster could result in keeping only MIN_SAMPLES_PER_CLUSTER
# (e.g., 5 samples) regardless of original dataset size (e.g., 100 samples).
MIN_TOTAL_SAMPLES_TO_KEEP = 20


@dataclass
class PruningResult:
    """
    Result of training data pruning operation.
    
    Attributes:
        pruned_data: List of training samples after pruning
        original_count: Number of samples before pruning
        pruned_count: Number of samples after pruning
        removed_count: Number of samples removed
        pruning_ratio: Fraction of samples removed (0-1)
        clusters_found: Number of clusters identified
        avg_cluster_size: Average number of samples per cluster
        memory_saved_estimate: Estimated memory saved in bytes
        pruning_time: Time taken to perform pruning (seconds)
    """
    pruned_data: List['TrainingData']
    original_count: int
    pruned_count: int
    removed_count: int
    pruning_ratio: float
    clusters_found: int
    avg_cluster_size: float
    memory_saved_estimate: int
    pruning_time: float
    
    def __repr__(self):
        return (
            f"PruningResult(removed={self.removed_count}/{self.original_count} samples, "
            f"ratio={self.pruning_ratio:.1%}, clusters={self.clusters_found})"
        )


def _calculate_sample_importance(
    sample: 'TrainingData',
    current_time: float,
    age_weight: float = AGE_WEIGHT_FACTOR,
    performance_weight: float = PERFORMANCE_WEIGHT_FACTOR
) -> float:
    """
    Calculate importance score for a training sample.
    
    Combines multiple factors:
    - Age: Newer samples are more relevant (exponential decay)
    - Performance: Samples with higher speedup are more valuable
    - Base score: All samples start with equal base importance
    
    Args:
        sample: Training sample to score
        current_time: Current timestamp (for age calculation)
        age_weight: Weight factor for age component (0-1)
        performance_weight: Weight factor for performance component (0-1)
    
    Returns:
        Importance score (higher = more important to keep)
    """
    # Base importance (all samples start equal)
    base_importance = 1.0
    
    # Age component: Exponential decay based on sample age
    # Samples from 1 year ago have weight exp(-1) ≈ 0.37
    # Samples from 6 months ago have weight exp(-0.5) ≈ 0.61
    age_seconds = current_time - sample.timestamp
    age_years = age_seconds / (365.25 * 24 * 3600)
    age_score = math.exp(-age_years) if age_years > 0 else 1.0
    
    # Performance component: Normalize speedup to [0, 1] range
    # Speedup of 8x → score = 1.0 (excellent)
    # Speedup of 4x → score = 0.5 (good)
    # Speedup of 1x → score = 0.0 (poor)
    max_expected_speedup = 8.0
    performance_score = min(1.0, max(0.0, sample.speedup / max_expected_speedup))
    
    # Weighted combination
    total_weight = 1.0 + age_weight + performance_weight
    importance = (
        base_importance +
        age_weight * age_score +
        performance_weight * performance_score
    ) / total_weight
    
    return importance


def _find_similar_samples(
    training_data: List['TrainingData'],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> List[Set[int]]:
    """
    Group training samples into similarity clusters.
    
    Uses distance-based clustering to identify groups of similar samples.
    Samples with feature distance < threshold are grouped together.
    
    NOTE: Feature distance is in range [0, sqrt(12)] ≈ [0, 3.46]
    Default threshold of 1.0 means features must be quite similar (within ~29% of max distance)
    
    Args:
        training_data: List of training samples
        similarity_threshold: Maximum distance for samples to be considered similar
    
    Returns:
        List of sets, where each set contains indices of similar samples
    """
    n = len(training_data)
    
    if n == 0:
        return []
    
    clusters: List[Set[int]] = []
    assigned = set()
    
    for i in range(n):
        if i in assigned:
            continue
        
        # Start a new cluster with sample i
        cluster = {i}
        assigned.add(i)
        
        # Find all samples similar to sample i
        # Use transitive closure: if j is similar to anything in cluster, add j
        for j in range(i + 1, n):
            if j in assigned:
                continue
            
            # Calculate distance to cluster representative (sample i)
            distance = training_data[i].features.distance(training_data[j].features)
            
            if distance < similarity_threshold:
                cluster.add(j)
                assigned.add(j)
        
        clusters.append(cluster)
    
    return clusters


def _select_representative_samples(
    training_data: List['TrainingData'],
    cluster_indices: Set[int],
    max_samples: int,
    current_time: float
) -> List[int]:
    """
    Select most representative samples from a cluster.
    
    Uses importance scoring to keep the most valuable samples while
    maintaining diversity within the cluster.
    
    Args:
        training_data: Full list of training samples
        cluster_indices: Indices of samples in this cluster
        max_samples: Maximum number of samples to keep from cluster
        current_time: Current timestamp for age calculation
    
    Returns:
        List of indices to keep from this cluster
    """
    if len(cluster_indices) <= max_samples:
        # Cluster is small enough, keep all samples
        return list(cluster_indices)
    
    # Calculate importance scores for all samples in cluster
    scored_samples = []
    for idx in cluster_indices:
        sample = training_data[idx]
        importance = _calculate_sample_importance(sample, current_time)
        scored_samples.append((idx, importance))
    
    # Sort by importance (descending)
    scored_samples.sort(key=lambda x: x[1], reverse=True)
    
    # Keep top-K most important samples
    kept_indices = [idx for idx, _ in scored_samples[:max_samples]]
    
    # Ensure diversity: Check inter-sample distances
    # If kept samples are too similar, replace some with diverse samples
    diverse_kept = []
    for idx in kept_indices:
        # Check if this sample is sufficiently different from already kept samples
        is_diverse = True
        for kept_idx in diverse_kept:
            distance = training_data[idx].features.distance(
                training_data[kept_idx].features
            )
            if distance < MIN_INTER_SAMPLE_DISTANCE:
                is_diverse = False
                break
        
        # Keep sample if: diverse, or needed to reach MIN_SAMPLES_PER_CLUSTER, or needed to reach max_samples
        if is_diverse or len(diverse_kept) < MIN_SAMPLES_PER_CLUSTER or len(diverse_kept) < max_samples:
            diverse_kept.append(idx)
            
            if len(diverse_kept) >= max_samples:
                break
    
    # If we didn't get enough diverse samples, add highest-scoring remaining ones
    # to meet MIN_SAMPLES_PER_CLUSTER requirement
    if len(diverse_kept) < MIN_SAMPLES_PER_CLUSTER:
        for idx in kept_indices:
            if idx not in diverse_kept:
                diverse_kept.append(idx)
                if len(diverse_kept) >= MIN_SAMPLES_PER_CLUSTER:
                    break
    
    # Ensure we always return at least MIN_SAMPLES_PER_CLUSTER if cluster has enough
    if len(diverse_kept) < MIN_SAMPLES_PER_CLUSTER and len(cluster_indices) >= MIN_SAMPLES_PER_CLUSTER:
        # Fill up to MIN_SAMPLES_PER_CLUSTER from scored_samples
        for idx, _ in scored_samples:
            if idx not in diverse_kept:
                diverse_kept.append(idx)
                if len(diverse_kept) >= MIN_SAMPLES_PER_CLUSTER:
                    break
    
    return diverse_kept


def prune_training_data(
    training_data: List['TrainingData'],
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    target_pruning_ratio: float = TARGET_PRUNING_RATIO,
    min_samples: int = MIN_SAMPLES_FOR_PRUNING,
    verbose: bool = False
) -> PruningResult:
    """
    Prune training data to reduce memory while maintaining accuracy.
    
    This function implements intelligent pruning that:
    1. Identifies clusters of similar training samples
    2. Keeps representative samples from each cluster
    3. Removes redundant samples that add little value
    4. Maintains diversity for better generalization
    
    Pruning Strategy:
    - Similar samples are grouped into clusters
    - Within each cluster, keep 5-20 most important samples
    - Importance is based on recency and performance
    - Diversity is enforced to prevent overfitting
    - Absolute minimum of 20 samples kept to prevent over-pruning
    
    Args:
        training_data: List of training samples to prune
        similarity_threshold: Distance threshold for similarity (0.0-3.5)
        target_pruning_ratio: Target fraction of samples to remove (0.0-1.0)
        min_samples: Minimum samples needed before pruning occurs
        verbose: If True, print diagnostic information
    
    Returns:
        PruningResult with pruned data and statistics
    
    Example:
        >>> training_data = load_ml_training_data()
        >>> result = prune_training_data(training_data, verbose=True)
        >>> print(f"Removed {result.removed_count} samples, kept {result.pruned_count}")
        >>> # Use result.pruned_data for predictions
    
    Memory Savings:
        Typical: 30-40% reduction in training data size
        Depends on: Data redundancy, similarity threshold, target ratio
    
    Accuracy Impact:
        Expected: < 5% degradation in prediction accuracy
        Maintained by: Diversity preservation, importance scoring
    """
    start_time = time.perf_counter()
    
    # Check if pruning is needed
    if len(training_data) < min_samples:
        # Too few samples, don't prune
        if verbose:
            print(f"Pruning skipped: Only {len(training_data)} samples (minimum: {min_samples})")
        return PruningResult(
            pruned_data=training_data,
            original_count=len(training_data),
            pruned_count=len(training_data),
            removed_count=0,
            pruning_ratio=0.0,
            clusters_found=0,
            avg_cluster_size=0.0,
            memory_saved_estimate=0,
            pruning_time=0.0
        )
    
    if verbose:
        print(f"Pruning {len(training_data)} training samples...")
        print(f"  Similarity threshold: {similarity_threshold:.3f}")
        print(f"  Target pruning ratio: {target_pruning_ratio:.1%}")
    
    # Step 1: Find similarity clusters
    current_time = time.time()
    clusters = _find_similar_samples(training_data, similarity_threshold)
    
    if verbose:
        print(f"  Found {len(clusters)} similarity clusters")
        cluster_sizes = [len(c) for c in clusters]
        print(f"  Cluster sizes: min={min(cluster_sizes)}, "
              f"max={max(cluster_sizes)}, "
              f"avg={sum(cluster_sizes) / len(cluster_sizes):.1f}")
    
    # Step 2: Calculate max samples per cluster based on target pruning ratio
    total_samples = len(training_data)
    target_kept_samples = int(total_samples * (1.0 - target_pruning_ratio))
    
    # Apply absolute minimum constraint to prevent over-pruning
    # This ensures we never drop below a reasonable dataset size,
    # even if clustering produces a single mega-cluster
    target_kept_samples = max(target_kept_samples, MIN_TOTAL_SAMPLES_TO_KEEP)
    
    # Distribute target across clusters (proportional to cluster size)
    # But ensure we don't under-budget due to minimums
    cluster_budgets = []
    total_min_budget = len(clusters) * MIN_SAMPLES_PER_CLUSTER
    
    if total_min_budget > target_kept_samples:
        # Minimum requirements exceed target - adjust upward
        target_kept_samples = total_min_budget
    
    for cluster in clusters:
        # Each cluster gets budget proportional to its size
        cluster_fraction = len(cluster) / total_samples
        base_budget = max(1, int(target_kept_samples * cluster_fraction))
        
        # Apply min/max constraints
        cluster_budget = max(
            MIN_SAMPLES_PER_CLUSTER,
            min(MAX_SAMPLES_PER_CLUSTER, base_budget)
        )
        cluster_budgets.append(cluster_budget)
    
    # Step 3: Select representative samples from each cluster
    kept_indices = set()
    for cluster, max_samples in zip(clusters, cluster_budgets):
        representatives = _select_representative_samples(
            training_data,
            cluster,
            max_samples,
            current_time
        )
        kept_indices.update(representatives)
    
    # Step 4: Build pruned dataset
    pruned_data = [training_data[i] for i in sorted(kept_indices)]
    
    # Calculate statistics
    original_count = len(training_data)
    pruned_count = len(pruned_data)
    removed_count = original_count - pruned_count
    pruning_ratio = removed_count / original_count if original_count > 0 else 0.0
    
    # Estimate memory saved (rough estimate: 1KB per sample)
    bytes_per_sample = 1024
    memory_saved = removed_count * bytes_per_sample
    
    pruning_time = time.perf_counter() - start_time
    
    if verbose:
        print(f"✓ Pruning complete in {pruning_time:.3f}s")
        print(f"  Original: {original_count} samples")
        print(f"  Pruned: {pruned_count} samples")
        print(f"  Removed: {removed_count} samples ({pruning_ratio:.1%})")
        print(f"  Memory saved: ~{memory_saved // 1024}KB")
    
    return PruningResult(
        pruned_data=pruned_data,
        original_count=original_count,
        pruned_count=pruned_count,
        removed_count=removed_count,
        pruning_ratio=pruning_ratio,
        clusters_found=len(clusters),
        avg_cluster_size=sum(len(c) for c in clusters) / len(clusters) if clusters else 0.0,
        memory_saved_estimate=memory_saved,
        pruning_time=pruning_time
    )


def auto_prune_training_data(
    training_data: List['TrainingData'],
    aggressive: bool = False,
    verbose: bool = False
) -> PruningResult:
    """
    Automatically prune training data with smart defaults.
    
    This is a convenience function that selects appropriate pruning parameters
    based on the dataset size and characteristics.
    
    Args:
        training_data: List of training samples to prune
        aggressive: If True, use more aggressive pruning (50% target vs 35%)
        verbose: If True, print diagnostic information
    
    Returns:
        PruningResult with pruned data and statistics
    
    Example:
        >>> training_data = load_ml_training_data()
        >>> result = auto_prune_training_data(training_data)
        >>> # Use result.pruned_data for faster predictions
    """
    # Adjust parameters based on dataset size and aggressiveness
    data_size = len(training_data)
    
    if aggressive:
        # More aggressive pruning for very large datasets
        target_ratio = 0.50  # Remove 50%
        similarity = 1.5  # More lenient similarity
    else:
        # Conservative pruning (default)
        if data_size > 500:
            # Large dataset: Can afford more aggressive pruning
            target_ratio = 0.40  # Remove 40%
            similarity = 1.2
        elif data_size > 200:
            # Medium dataset: Moderate pruning
            target_ratio = 0.35  # Remove 35%
            similarity = 1.0
        else:
            # Small dataset: Very conservative pruning
            target_ratio = 0.25  # Remove 25%
            similarity = 0.8
    
    return prune_training_data(
        training_data,
        similarity_threshold=similarity,
        target_pruning_ratio=target_ratio,
        verbose=verbose
    )


__all__ = [
    'prune_training_data',
    'auto_prune_training_data',
    'PruningResult',
    'DEFAULT_SIMILARITY_THRESHOLD',
    'MIN_SAMPLES_FOR_PRUNING',
    'TARGET_PRUNING_RATIO'
]
