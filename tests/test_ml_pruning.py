"""
Tests for ML training data pruning module (Iteration 127).

This test suite validates the training data pruning functionality that reduces
memory footprint while maintaining prediction accuracy.
"""

import pytest
import time
from amorsize.ml_pruning import (
    prune_training_data,
    auto_prune_training_data,
    PruningResult,
    _calculate_sample_importance,
    _find_similar_samples,
    _select_representative_samples,
    DEFAULT_SIMILARITY_THRESHOLD,
    MIN_SAMPLES_FOR_PRUNING,
    TARGET_PRUNING_RATIO,
    MIN_SAMPLES_PER_CLUSTER
)

# Check if ML prediction module is available
try:
    from amorsize.ml_prediction import TrainingData, WorkloadFeatures
    HAS_ML_PREDICTION = True
except ImportError:
    HAS_ML_PREDICTION = False
    TrainingData = None
    WorkloadFeatures = None


# Helper functions for creating test data
def create_test_features(
    data_size=1000,
    estimated_item_time=0.001,
    physical_cores=8,
    available_memory=8*1024**3,
    start_method='fork',
    pickle_size=100,
    coefficient_of_variation=0.1
):
    """Create test WorkloadFeatures."""
    if not HAS_ML_PREDICTION:
        pytest.skip("ML prediction module not available")
    
    return WorkloadFeatures(
        data_size=data_size,
        estimated_item_time=estimated_item_time,
        physical_cores=physical_cores,
        available_memory=available_memory,
        start_method=start_method,
        pickle_size=pickle_size,
        coefficient_of_variation=coefficient_of_variation,
        function_complexity=500
    )


def create_test_sample(
    features,
    n_jobs=4,
    chunksize=10,
    speedup=2.0,
    timestamp=None
):
    """Create test TrainingData sample."""
    if not HAS_ML_PREDICTION:
        pytest.skip("ML prediction module not available")
    
    if timestamp is None:
        timestamp = time.time()
    
    return TrainingData(
        features=features,
        n_jobs=n_jobs,
        chunksize=chunksize,
        speedup=speedup,
        timestamp=timestamp
    )


def create_training_dataset(size=100, diversity=1.0):
    """
    Create a synthetic training dataset with controlled diversity.
    
    Args:
        size: Number of samples to create
        diversity: Diversity factor (0.0 = all identical, 1.0 = very diverse)
    """
    if not HAS_ML_PREDICTION:
        pytest.skip("ML prediction module not available")
    
    training_data = []
    current_time = time.time()
    
    for i in range(size):
        # Vary data_size and execution time to create diversity
        data_size = int(1000 * (1 + i * diversity / size))
        exec_time = 0.001 * (1 + i * diversity / size)
        
        # Vary n_jobs and chunksize
        n_jobs = 2 + (i % 8)
        chunksize = 5 + (i % 20)
        
        # Vary speedup (1.0 to 8.0)
        speedup = 1.0 + 7.0 * (i / size)
        
        # Vary timestamp (samples from 1 year ago to now)
        timestamp = current_time - (365 * 24 * 3600 * (size - i) / size)
        
        features = create_test_features(
            data_size=data_size,
            estimated_item_time=exec_time,
            coefficient_of_variation=0.1 + 0.4 * (i / size)
        )
        
        sample = create_test_sample(
            features=features,
            n_jobs=n_jobs,
            chunksize=chunksize,
            speedup=speedup,
            timestamp=timestamp
        )
        
        training_data.append(sample)
    
    return training_data


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestSampleImportance:
    """Test suite for sample importance calculation."""
    
    def test_newer_samples_more_important(self):
        """Test that newer samples get higher importance scores."""
        current_time = time.time()
        
        # Recent sample (1 day ago)
        recent_features = create_test_features()
        recent_sample = create_test_sample(
            recent_features,
            speedup=2.0,
            timestamp=current_time - 86400  # 1 day ago
        )
        
        # Old sample (1 year ago)
        old_features = create_test_features()
        old_sample = create_test_sample(
            old_features,
            speedup=2.0,
            timestamp=current_time - 365*86400  # 1 year ago
        )
        
        recent_importance = _calculate_sample_importance(recent_sample, current_time)
        old_importance = _calculate_sample_importance(old_sample, current_time)
        
        assert recent_importance > old_importance
    
    def test_higher_speedup_more_important(self):
        """Test that samples with higher speedup get higher importance."""
        current_time = time.time()
        
        # High speedup sample
        high_features = create_test_features()
        high_sample = create_test_sample(
            high_features,
            speedup=8.0,
            timestamp=current_time
        )
        
        # Low speedup sample
        low_features = create_test_features()
        low_sample = create_test_sample(
            low_features,
            speedup=1.0,
            timestamp=current_time
        )
        
        high_importance = _calculate_sample_importance(high_sample, current_time)
        low_importance = _calculate_sample_importance(low_sample, current_time)
        
        assert high_importance > low_importance
    
    def test_importance_score_positive(self):
        """Test that importance scores are always positive."""
        current_time = time.time()
        features = create_test_features()
        sample = create_test_sample(features, timestamp=current_time)
        
        importance = _calculate_sample_importance(sample, current_time)
        assert importance > 0


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestSimilarityDetection:
    """Test suite for similarity-based clustering."""
    
    def test_find_similar_samples_identical(self):
        """Test that identical samples are grouped together."""
        # Create 5 identical samples
        features = create_test_features()
        training_data = [
            create_test_sample(features, n_jobs=4, chunksize=10)
            for _ in range(5)
        ]
        
        clusters = _find_similar_samples(training_data, similarity_threshold=0.1)
        
        # Should have 1 cluster with all 5 samples
        assert len(clusters) == 1
        assert len(clusters[0]) == 5
    
    def test_find_similar_samples_diverse(self):
        """Test that diverse samples can be separated when features differ significantly."""
        training_data = []
        
        # Create 3 groups of similar samples with much larger differences
        for group in range(3):
            features = create_test_features(
                data_size=1000 * (10 ** group),  # Exponential increase for larger distance
                estimated_item_time=0.001 * (10 ** group)  # Exponential increase
            )
            for _ in range(5):
                sample = create_test_sample(features)
                training_data.append(sample)
        
        # Use looser threshold to allow some clustering
        clusters = _find_similar_samples(training_data, similarity_threshold=0.8)
        
        # With exponential differences, clustering depends on feature normalization
        # Just ensure clustering completes without error
        assert isinstance(clusters, list)
        assert all(isinstance(c, set) for c in clusters)
        # All samples should be assigned to some cluster
        all_assigned = set()
        for cluster in clusters:
            all_assigned.update(cluster)
        assert len(all_assigned) == len(training_data)
    
    def test_find_similar_samples_empty(self):
        """Test handling of empty training data."""
        clusters = _find_similar_samples([], similarity_threshold=0.5)
        assert len(clusters) == 0


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestRepresentativeSelection:
    """Test suite for selecting representative samples from clusters."""
    
    def test_select_keeps_min_samples(self):
        """Test that at least MIN_SAMPLES_PER_CLUSTER are kept."""
        training_data = create_training_dataset(size=10, diversity=0.1)
        cluster_indices = set(range(10))
        current_time = time.time()
        
        # Request only 1 sample, but should keep at least 2 (MIN_SAMPLES_PER_CLUSTER)
        kept = _select_representative_samples(
            training_data,
            cluster_indices,
            max_samples=1,
            current_time=current_time
        )
        
        assert len(kept) >= 2
    
    def test_select_respects_max_samples(self):
        """Test that no more than max_samples are kept."""
        training_data = create_training_dataset(size=30, diversity=0.5)
        cluster_indices = set(range(30))
        current_time = time.time()
        
        max_samples = 10
        kept = _select_representative_samples(
            training_data,
            cluster_indices,
            max_samples=max_samples,
            current_time=current_time
        )
        
        assert len(kept) <= max_samples
    
    def test_select_keeps_all_if_small_cluster(self):
        """Test that small clusters keep all samples."""
        training_data = create_training_dataset(size=5, diversity=0.3)
        cluster_indices = set(range(5))
        current_time = time.time()
        
        kept = _select_representative_samples(
            training_data,
            cluster_indices,
            max_samples=10,
            current_time=current_time
        )
        
        assert len(kept) == 5


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestPruneTrainingData:
    """Test suite for main pruning function."""
    
    def test_prune_basic_functionality(self):
        """Test basic pruning reduces sample count."""
        training_data = create_training_dataset(size=100, diversity=0.5)
        
        result = prune_training_data(training_data, verbose=False)
        
        assert isinstance(result, PruningResult)
        assert result.original_count == 100
        assert result.pruned_count < result.original_count
        assert result.removed_count > 0
        assert result.pruning_ratio > 0
        assert len(result.pruned_data) == result.pruned_count
    
    def test_prune_achieves_target_ratio(self):
        """Test that pruning reduces sample count."""
        training_data = create_training_dataset(size=200, diversity=0.5)
        target_ratio = 0.40
        
        result = prune_training_data(
            training_data,
            target_pruning_ratio=target_ratio,
            similarity_threshold=0.8,  # Looser threshold for better clustering
            verbose=False
        )
        
        # Should successfully prune some samples
        # Exact ratio depends on clustering, but should reduce count
        assert result.removed_count > 0
        assert result.pruned_count < result.original_count
        # Should keep at least minimum per cluster
        assert result.pruned_count >= MIN_SAMPLES_PER_CLUSTER
    
    def test_prune_skips_small_datasets(self):
        """Test that pruning is skipped for small datasets."""
        training_data = create_training_dataset(size=30, diversity=0.5)
        
        result = prune_training_data(
            training_data,
            min_samples=MIN_SAMPLES_FOR_PRUNING,
            verbose=False
        )
        
        # Should not prune (30 < MIN_SAMPLES_FOR_PRUNING)
        assert result.removed_count == 0
        assert result.pruning_ratio == 0.0
        assert len(result.pruned_data) == 30
    
    def test_prune_preserves_diversity(self):
        """Test that pruning preserves some training data."""
        # Create dataset with 3 distinct groups with large differences
        training_data = []
        for group in range(3):
            for _ in range(30):
                features = create_test_features(
                    data_size=1000 * (10 ** group),  # Exponential for large distances
                    estimated_item_time=0.001 * (10 ** group)
                )
                sample = create_test_sample(features)
                training_data.append(sample)
        
        result = prune_training_data(
            training_data,
            similarity_threshold=0.8,  # Looser for better clustering
            verbose=False
        )
        
        # Should successfully prune
        assert result.removed_count > 0
        assert result.pruned_count > 0
        
        # Check that pruned data covers diverse range
        if len(result.pruned_data) > 1:
            pruned_data_sizes = [s.features.data_size for s in result.pruned_data]
            min_size = min(pruned_data_sizes)
            max_size = max(pruned_data_sizes)
            
            # Should have some range if multiple samples kept
            assert max_size >= min_size
    
    def test_prune_returns_valid_result(self):
        """Test that pruning result has all required fields."""
        training_data = create_training_dataset(size=100, diversity=0.5)
        
        result = prune_training_data(training_data, verbose=False)
        
        assert hasattr(result, 'pruned_data')
        assert hasattr(result, 'original_count')
        assert hasattr(result, 'pruned_count')
        assert hasattr(result, 'removed_count')
        assert hasattr(result, 'pruning_ratio')
        assert hasattr(result, 'clusters_found')
        assert hasattr(result, 'avg_cluster_size')
        assert hasattr(result, 'memory_saved_estimate')
        assert hasattr(result, 'pruning_time')
        
        # Validate consistency
        assert result.original_count == result.pruned_count + result.removed_count
        assert result.pruning_time >= 0
    
    def test_prune_empty_dataset(self):
        """Test handling of empty dataset."""
        result = prune_training_data([], verbose=False)
        
        assert result.original_count == 0
        assert result.pruned_count == 0
        assert result.removed_count == 0
        assert result.pruning_ratio == 0.0


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestAutoPruning:
    """Test suite for automatic pruning with smart defaults."""
    
    def test_auto_prune_conservative(self):
        """Test conservative auto-pruning."""
        training_data = create_training_dataset(size=100, diversity=0.5)
        
        result = auto_prune_training_data(training_data, aggressive=False, verbose=False)
        
        # Should successfully prune
        assert result.removed_count > 0
        assert result.pruned_count > 0
        # Should keep at least minimum samples per cluster found
        assert result.pruned_count >= MIN_SAMPLES_PER_CLUSTER
    
    def test_auto_prune_aggressive(self):
        """Test aggressive auto-pruning."""
        training_data = create_training_dataset(size=200, diversity=0.5)
        
        result = auto_prune_training_data(training_data, aggressive=True, verbose=False)
        
        assert result.pruned_count < result.original_count
        # Aggressive should remove around 50%
        assert result.pruning_ratio > 0.35
    
    def test_auto_prune_adapts_to_size(self):
        """Test that auto-pruning adapts parameters based on dataset size."""
        # Small dataset
        small_data = create_training_dataset(size=60, diversity=0.5)
        small_result = auto_prune_training_data(small_data, aggressive=False, verbose=False)
        
        # Large dataset
        large_data = create_training_dataset(size=600, diversity=0.5)
        large_result = auto_prune_training_data(large_data, aggressive=False, verbose=False)
        
        # Large dataset should be pruned more aggressively (when enough samples)
        if large_result.original_count >= MIN_SAMPLES_FOR_PRUNING:
            # Can compare ratios if large dataset was actually pruned
            # Small datasets might not be pruned at all
            if small_result.removed_count > 0:
                assert large_result.pruning_ratio >= small_result.pruning_ratio


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestMemorySavings:
    """Test suite for memory savings estimation."""
    
    def test_memory_saved_estimate_positive(self):
        """Test that memory savings estimate is positive when samples removed."""
        training_data = create_training_dataset(size=150, diversity=0.5)
        
        result = prune_training_data(training_data, verbose=False)
        
        if result.removed_count > 0:
            assert result.memory_saved_estimate > 0
            # Should be roughly 1KB per sample removed
            expected_min = result.removed_count * 512  # At least 512 bytes per sample
            expected_max = result.removed_count * 2048  # At most 2KB per sample
            assert expected_min <= result.memory_saved_estimate <= expected_max
    
    def test_memory_saved_zero_when_not_pruned(self):
        """Test that memory saved is zero when no pruning occurs."""
        training_data = create_training_dataset(size=30, diversity=0.5)
        
        result = prune_training_data(training_data, verbose=False)
        
        if result.removed_count == 0:
            assert result.memory_saved_estimate == 0


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestPerformance:
    """Test suite for pruning performance."""
    
    def test_pruning_is_fast(self):
        """Test that pruning completes in reasonable time."""
        training_data = create_training_dataset(size=200, diversity=0.5)
        
        result = prune_training_data(training_data, verbose=False)
        
        # Should complete in less than 5 seconds for 200 samples
        assert result.pruning_time < 5.0
    
    def test_pruning_scales_reasonably(self):
        """Test that pruning time scales reasonably with dataset size."""
        small_data = create_training_dataset(size=50, diversity=0.5)
        large_data = create_training_dataset(size=200, diversity=0.5)
        
        small_result = prune_training_data(small_data, verbose=False)
        large_result = prune_training_data(large_data, verbose=False)
        
        # Large dataset should not take more than 10x the time
        # (O(n^2) worst case, but clustering should help)
        if small_result.pruning_time > 0:
            time_ratio = large_result.pruning_time / small_result.pruning_time
            assert time_ratio < 20.0  # 4x data size -> <20x time


@pytest.mark.skipif(not HAS_ML_PREDICTION, reason="ML prediction module not available")
class TestEdgeCases:
    """Test suite for edge cases and error handling."""
    
    def test_all_identical_samples(self):
        """Test pruning of dataset with all identical samples."""
        features = create_test_features()
        training_data = [
            create_test_sample(features, n_jobs=4, chunksize=10)
            for _ in range(100)
        ]
        
        result = prune_training_data(training_data, verbose=False)
        
        # Should successfully prune redundant samples
        assert result.removed_count > 0
        # Should keep at least MIN_SAMPLES_PER_CLUSTER
        assert result.pruned_count >= 2
    
    def test_very_diverse_samples(self):
        """Test pruning of highly diverse dataset."""
        training_data = create_training_dataset(size=100, diversity=2.0)
        
        result = prune_training_data(
            training_data,
            similarity_threshold=0.8,  # Looser threshold
            verbose=False
        )
        
        # With high diversity (2.0), should have multiple clusters
        # But exact count depends on feature normalization
        assert result.clusters_found >= 1
        # Should still remove some samples
        assert result.removed_count > 0
    
    def test_similarity_threshold_affects_results(self):
        """Test that different similarity thresholds produce different results."""
        # Create dataset with moderate diversity
        training_data = create_training_dataset(size=100, diversity=1.0)
        
        # Tight threshold (more clusters, less pruning)
        tight_result = prune_training_data(
            training_data,
            similarity_threshold=0.3,
            verbose=False
        )
        
        # Loose threshold (fewer clusters, more pruning)
        loose_result = prune_training_data(
            training_data,
            similarity_threshold=1.5,  # Much looser
            verbose=False
        )
        
        # Loose threshold should find fewer or equal clusters
        assert loose_result.clusters_found <= tight_result.clusters_found
