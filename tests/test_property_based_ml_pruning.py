"""
Property-based tests for the ml_pruning module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the ML training data pruning system across a wide range of inputs.
"""

import time
from typing import List

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

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
    MIN_SAMPLES_PER_CLUSTER,
    MIN_TOTAL_SAMPLES_TO_KEEP,
    MAX_SAMPLES_PER_CLUSTER,
    AGE_WEIGHT_FACTOR,
    PERFORMANCE_WEIGHT_FACTOR,
)

# Check if ML prediction module is available
try:
    from amorsize.ml_prediction import TrainingData, WorkloadFeatures
    HAS_ML_PREDICTION = True
except ImportError:
    HAS_ML_PREDICTION = False
    TrainingData = None
    WorkloadFeatures = None

# Skip all tests if ML prediction module is not available
pytestmark = pytest.mark.skipif(
    not HAS_ML_PREDICTION,
    reason="ML prediction module not available"
)


# Helper strategies for generating test data
@st.composite
def workload_features_strategy(draw):
    """Generate valid WorkloadFeatures instances."""
    return WorkloadFeatures(
        data_size=draw(st.integers(min_value=10, max_value=10000)),
        estimated_item_time=draw(st.floats(min_value=0.0001, max_value=1.0)),
        physical_cores=draw(st.integers(min_value=1, max_value=64)),
        available_memory=draw(st.integers(min_value=1024**2, max_value=128*1024**3)),
        start_method=draw(st.sampled_from(['fork', 'spawn', 'forkserver'])),
        pickle_size=draw(st.integers(min_value=1, max_value=100000)),
        coefficient_of_variation=draw(st.floats(min_value=0.0, max_value=2.0)),
        function_complexity=draw(st.integers(min_value=1, max_value=10000))
    )


# Fixed reference time for consistent test execution
_REFERENCE_TIME = 1700000000.0  # Fixed timestamp (Nov 2023)

@st.composite
def training_data_strategy(draw):
    """Generate valid TrainingData instances."""
    features = draw(workload_features_strategy())
    return TrainingData(
        features=features,
        n_jobs=draw(st.integers(min_value=1, max_value=64)),
        chunksize=draw(st.integers(min_value=1, max_value=1000)),
        speedup=draw(st.floats(min_value=0.1, max_value=20.0)),
        timestamp=draw(st.floats(min_value=_REFERENCE_TIME - 365*24*3600, max_value=_REFERENCE_TIME))
    )


@st.composite
def training_dataset_strategy(draw, min_size=0, max_size=200):
    """Generate a list of TrainingData instances."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(training_data_strategy()) for _ in range(size)]


class TestPruningResultInvariants:
    """Test invariant properties that should always hold for PruningResult."""

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_pruning_result_counts_consistent(self, training_dataset):
        """Test that pruning result counts are mathematically consistent."""
        result = prune_training_data(training_dataset)
        
        # Basic count consistency
        assert result.original_count == len(training_dataset)
        assert result.pruned_count == len(result.pruned_data)
        assert result.removed_count == result.original_count - result.pruned_count
        assert result.removed_count >= 0
        
        # Pruning ratio consistency
        if result.original_count > 0:
            expected_ratio = result.removed_count / result.original_count
            assert abs(result.pruning_ratio - expected_ratio) < 0.001

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_pruning_preserves_data_type(self, training_dataset):
        """Test that pruned data maintains correct types."""
        result = prune_training_data(training_dataset)
        
        assert isinstance(result, PruningResult)
        assert isinstance(result.pruned_data, list)
        assert all(isinstance(item, TrainingData) for item in result.pruned_data)

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_pruning_result_non_negative_values(self, training_dataset):
        """Test that all numeric fields in pruning result are non-negative."""
        result = prune_training_data(training_dataset)
        
        assert result.original_count >= 0
        assert result.pruned_count >= 0
        assert result.removed_count >= 0
        assert result.pruning_ratio >= 0.0
        assert result.pruning_ratio <= 1.0
        assert result.clusters_found >= 0
        assert result.avg_cluster_size >= 0.0
        assert result.memory_saved_estimate >= 0
        assert result.pruning_time >= 0.0

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_pruning_result_repr_works(self, training_dataset):
        """Test that PruningResult repr/str work without errors."""
        result = prune_training_data(training_dataset)
        
        repr_str = repr(result)
        assert isinstance(repr_str, str)
        assert "PruningResult" in repr_str
        assert str(result.removed_count) in repr_str

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_minimum_samples_preserved(self, training_dataset):
        """Test that pruning respects minimum sample constraints."""
        result = prune_training_data(training_dataset)
        
        # Should keep at least MIN_TOTAL_SAMPLES_TO_KEEP
        if result.original_count >= MIN_SAMPLES_FOR_PRUNING:
            assert result.pruned_count >= MIN_TOTAL_SAMPLES_TO_KEEP or \
                   result.pruned_count == result.original_count


class TestPruneTrainingDataInvariants:
    """Test invariants for the main pruning function."""

    @given(training_dataset=training_dataset_strategy(min_size=0, max_size=30))
    @settings(max_examples=50, deadline=2000)
    def test_small_dataset_not_pruned(self, training_dataset):
        """Test that datasets below minimum size are not pruned."""
        assume(len(training_dataset) < MIN_SAMPLES_FOR_PRUNING)
        
        result = prune_training_data(training_dataset)
        
        assert result.pruned_count == result.original_count
        assert result.removed_count == 0
        assert result.pruning_ratio == 0.0

    @given(
        training_dataset=training_dataset_strategy(min_size=50, max_size=150),
        similarity_threshold=st.floats(min_value=0.1, max_value=3.0),
        target_pruning_ratio=st.floats(min_value=0.1, max_value=0.8)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_pruning_respects_parameters(self, training_dataset, similarity_threshold, target_pruning_ratio):
        """Test that pruning respects input parameters."""
        result = prune_training_data(
            training_dataset,
            similarity_threshold=similarity_threshold,
            target_pruning_ratio=target_pruning_ratio
        )
        
        # Result should be valid
        assert isinstance(result, PruningResult)
        assert result.pruned_count <= result.original_count

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_pruned_data_subset_of_original(self, training_dataset):
        """Test that pruned data is a subset of original data."""
        result = prune_training_data(training_dataset)
        
        # All pruned samples should exist in original data
        # (checking by identity/reference)
        original_ids = {id(sample) for sample in training_dataset}
        pruned_ids = {id(sample) for sample in result.pruned_data}
        
        assert pruned_ids.issubset(original_ids)

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_clusters_found_reasonable(self, training_dataset):
        """Test that number of clusters found is reasonable."""
        result = prune_training_data(training_dataset)
        
        if result.original_count >= MIN_SAMPLES_FOR_PRUNING:
            # Should find at least 1 cluster if pruning occurred
            assert result.clusters_found >= 1
            # Should not have more clusters than samples
            assert result.clusters_found <= result.original_count

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_avg_cluster_size_reasonable(self, training_dataset):
        """Test that average cluster size is reasonable."""
        result = prune_training_data(training_dataset)
        
        if result.clusters_found > 0:
            # Average cluster size should be positive
            assert result.avg_cluster_size > 0.0
            # Average cluster size should not exceed total samples
            assert result.avg_cluster_size <= result.original_count


class TestAutoPruneInvariants:
    """Test invariants for the auto_prune function."""

    @given(
        training_dataset=training_dataset_strategy(min_size=50, max_size=150),
        aggressive=st.booleans()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_auto_prune_returns_valid_result(self, training_dataset, aggressive):
        """Test that auto_prune returns valid PruningResult."""
        result = auto_prune_training_data(training_dataset, aggressive=aggressive)
        
        assert isinstance(result, PruningResult)
        assert result.pruned_count <= result.original_count

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_auto_prune_aggressive_removes_more(self, training_dataset):
        """Test that aggressive mode removes more or equal samples."""
        result_normal = auto_prune_training_data(training_dataset, aggressive=False)
        result_aggressive = auto_prune_training_data(training_dataset, aggressive=True)
        
        # Aggressive should remove at least as many samples as normal
        # (may be equal if dataset characteristics prevent more removal)
        assert result_aggressive.removed_count >= result_normal.removed_count or \
               result_aggressive.pruned_count == MIN_TOTAL_SAMPLES_TO_KEEP

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_auto_prune_dataset_size_aware(self, training_dataset):
        """Test that auto_prune adjusts parameters based on dataset size."""
        result = auto_prune_training_data(training_dataset, aggressive=False)
        
        # Should produce valid result regardless of size
        assert isinstance(result, PruningResult)
        assert result.pruned_count > 0


class TestSampleImportanceInvariants:
    """Test invariants for sample importance calculation."""

    @given(
        training_sample=training_data_strategy(),
        current_time=st.floats(min_value=_REFERENCE_TIME, max_value=_REFERENCE_TIME + 1000),
        age_weight=st.floats(min_value=0.0, max_value=1.0),
        performance_weight=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100, deadline=1000)
    def test_importance_score_non_negative(self, training_sample, current_time, age_weight, performance_weight):
        """Test that importance scores are always non-negative."""
        importance = _calculate_sample_importance(
            training_sample,
            current_time,
            age_weight,
            performance_weight
        )
        
        assert importance >= 0.0

    @given(
        training_sample=training_data_strategy(),
        current_time=st.floats(min_value=_REFERENCE_TIME, max_value=_REFERENCE_TIME + 1000)
    )
    @settings(max_examples=100, deadline=1000)
    def test_importance_score_deterministic(self, training_sample, current_time):
        """Test that importance score is deterministic for same inputs."""
        score1 = _calculate_sample_importance(training_sample, current_time)
        score2 = _calculate_sample_importance(training_sample, current_time)
        
        assert score1 == score2

    @given(training_sample=training_data_strategy())
    @settings(max_examples=100, deadline=1000)
    def test_newer_samples_higher_importance(self, training_sample):
        """Test that newer samples generally have higher importance (with age weight)."""
        current_time = _REFERENCE_TIME
        
        # Create older version of sample (1 year ago)
        old_sample = TrainingData(
            features=training_sample.features,
            n_jobs=training_sample.n_jobs,
            chunksize=training_sample.chunksize,
            speedup=training_sample.speedup,
            timestamp=current_time - 365*24*3600
        )
        
        # Create newer version of sample (now)
        new_sample = TrainingData(
            features=training_sample.features,
            n_jobs=training_sample.n_jobs,
            chunksize=training_sample.chunksize,
            speedup=training_sample.speedup,
            timestamp=current_time
        )
        
        old_importance = _calculate_sample_importance(old_sample, current_time, age_weight=1.0)
        new_importance = _calculate_sample_importance(new_sample, current_time, age_weight=1.0)
        
        # New sample should have higher importance when age weight is significant
        assert new_importance >= old_importance

    @given(training_sample=training_data_strategy())
    @settings(max_examples=100, deadline=1000)
    def test_better_performance_higher_importance(self, training_sample):
        """Test that better performing samples have higher importance."""
        current_time = _REFERENCE_TIME
        
        # Create low performance version
        low_perf = TrainingData(
            features=training_sample.features,
            n_jobs=training_sample.n_jobs,
            chunksize=training_sample.chunksize,
            speedup=1.0,  # Low speedup
            timestamp=training_sample.timestamp
        )
        
        # Create high performance version
        high_perf = TrainingData(
            features=training_sample.features,
            n_jobs=training_sample.n_jobs,
            chunksize=training_sample.chunksize,
            speedup=8.0,  # High speedup
            timestamp=training_sample.timestamp
        )
        
        low_importance = _calculate_sample_importance(low_perf, current_time, performance_weight=1.0)
        high_importance = _calculate_sample_importance(high_perf, current_time, performance_weight=1.0)
        
        # High performance should have higher importance
        assert high_importance >= low_importance


class TestSimilarityClustering:
    """Test invariants for similarity-based clustering."""

    @given(training_dataset=training_dataset_strategy(min_size=0, max_size=50))
    @settings(max_examples=50, deadline=2000)
    def test_empty_dataset_returns_empty_clusters(self, training_dataset):
        """Test that empty dataset returns empty cluster list."""
        if len(training_dataset) == 0:
            clusters = _find_similar_samples(training_dataset)
            assert clusters == []

    @given(training_dataset=training_dataset_strategy(min_size=1, max_size=50))
    @settings(max_examples=50, deadline=2000)
    def test_all_samples_assigned_to_cluster(self, training_dataset):
        """Test that all samples are assigned to exactly one cluster."""
        assume(len(training_dataset) > 0)
        
        clusters = _find_similar_samples(training_dataset)
        
        # Collect all assigned indices
        assigned_indices = set()
        for cluster in clusters:
            assigned_indices.update(cluster)
        
        # Should have assigned all samples
        expected_indices = set(range(len(training_dataset)))
        assert assigned_indices == expected_indices

    @given(
        training_dataset=training_dataset_strategy(min_size=1, max_size=50),
        similarity_threshold=st.floats(min_value=0.1, max_value=3.0)
    )
    @settings(max_examples=50, deadline=2000)
    def test_cluster_count_bounded(self, training_dataset, similarity_threshold):
        """Test that number of clusters is bounded by dataset size."""
        assume(len(training_dataset) > 0)
        
        clusters = _find_similar_samples(training_dataset, similarity_threshold)
        
        # Should have at least 1 cluster and at most N clusters (one per sample)
        assert 1 <= len(clusters) <= len(training_dataset)

    @given(training_dataset=training_dataset_strategy(min_size=1, max_size=50))
    @settings(max_examples=50, deadline=2000)
    def test_clusters_non_overlapping(self, training_dataset):
        """Test that clusters don't overlap (samples in exactly one cluster)."""
        assume(len(training_dataset) > 0)
        
        clusters = _find_similar_samples(training_dataset)
        
        # Check for overlaps
        seen_indices = set()
        for cluster in clusters:
            for idx in cluster:
                assert idx not in seen_indices, f"Index {idx} appears in multiple clusters"
                seen_indices.add(idx)


class TestRepresentativeSampleSelection:
    """Test invariants for representative sample selection."""

    @given(
        training_dataset=training_dataset_strategy(min_size=10, max_size=50),
        max_samples=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=50, deadline=2000)
    def test_selection_respects_max_samples(self, training_dataset, max_samples):
        """Test that selection respects max_samples constraint."""
        cluster_indices = set(range(len(training_dataset)))
        current_time = _REFERENCE_TIME
        
        selected = _select_representative_samples(
            training_dataset,
            cluster_indices,
            max_samples,
            current_time
        )
        
        # Should not exceed max_samples (unless enforcing MIN_SAMPLES_PER_CLUSTER)
        assert len(selected) <= max(max_samples, MIN_SAMPLES_PER_CLUSTER)

    @given(training_dataset=training_dataset_strategy(min_size=10, max_size=50))
    @settings(max_examples=50, deadline=2000)
    def test_selection_returns_subset(self, training_dataset):
        """Test that selected samples are subset of cluster."""
        cluster_indices = set(range(len(training_dataset)))
        current_time = _REFERENCE_TIME
        max_samples = 5
        
        selected = _select_representative_samples(
            training_dataset,
            cluster_indices,
            max_samples,
            current_time
        )
        
        # All selected indices should be in original cluster
        assert set(selected).issubset(cluster_indices)

    @given(training_dataset=training_dataset_strategy(min_size=3, max_size=50))
    @settings(max_examples=50, deadline=2000)
    def test_small_cluster_keeps_all_samples(self, training_dataset):
        """Test that clusters smaller than max_samples keep all samples."""
        cluster_size = 3
        cluster_indices = set(range(cluster_size))
        current_time = _REFERENCE_TIME
        max_samples = 10  # Larger than cluster
        
        selected = _select_representative_samples(
            training_dataset[:cluster_size],
            cluster_indices,
            max_samples,
            current_time
        )
        
        # Should keep all samples
        assert len(selected) == cluster_size


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_constants_are_reasonable(self):
        """Test that module constants have reasonable values."""
        assert DEFAULT_SIMILARITY_THRESHOLD > 0.0
        assert DEFAULT_SIMILARITY_THRESHOLD < 10.0
        
        assert MIN_SAMPLES_PER_CLUSTER >= 1
        assert MIN_SAMPLES_PER_CLUSTER <= MAX_SAMPLES_PER_CLUSTER
        
        assert 0.0 <= AGE_WEIGHT_FACTOR <= 1.0
        assert 0.0 <= PERFORMANCE_WEIGHT_FACTOR <= 1.0
        
        assert MIN_SAMPLES_FOR_PRUNING >= MIN_TOTAL_SAMPLES_TO_KEEP
        
        assert 0.0 < TARGET_PRUNING_RATIO < 1.0
        
        assert MIN_TOTAL_SAMPLES_TO_KEEP > 0

    @given(training_dataset=training_dataset_strategy(min_size=0, max_size=5))
    @settings(max_examples=20, deadline=1000)
    def test_very_small_datasets(self, training_dataset):
        """Test handling of very small datasets."""
        result = prune_training_data(training_dataset)
        
        # Should not crash
        assert isinstance(result, PruningResult)
        # Small datasets should not be pruned
        assert result.pruned_count == result.original_count

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_verbose_mode_works(self, training_dataset):
        """Test that verbose mode doesn't crash."""
        # Should not raise any exceptions
        result = prune_training_data(training_dataset, verbose=True)
        assert isinstance(result, PruningResult)

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_extreme_similarity_threshold(self, training_dataset):
        """Test with extreme similarity thresholds."""
        # Very tight threshold (0.01) - should create many small clusters
        result_tight = prune_training_data(training_dataset, similarity_threshold=0.01)
        
        # Very loose threshold (10.0) - should create fewer, larger clusters
        result_loose = prune_training_data(training_dataset, similarity_threshold=10.0)
        
        # Both should produce valid results
        assert isinstance(result_tight, PruningResult)
        assert isinstance(result_loose, PruningResult)
        
        # Loose threshold should generally find fewer clusters
        # (unless dataset is very diverse)
        assert result_loose.clusters_found <= result_tight.clusters_found or \
               result_loose.clusters_found == 1

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_extreme_pruning_ratios(self, training_dataset):
        """Test with extreme pruning ratios."""
        # Very aggressive pruning (90%)
        result_aggressive = prune_training_data(training_dataset, target_pruning_ratio=0.9)
        
        # Very conservative pruning (1%)
        result_conservative = prune_training_data(training_dataset, target_pruning_ratio=0.01)
        
        # Both should produce valid results
        assert isinstance(result_aggressive, PruningResult)
        assert isinstance(result_conservative, PruningResult)
        
        # Should still respect minimum sample constraint
        assert result_aggressive.pruned_count >= MIN_TOTAL_SAMPLES_TO_KEEP or \
               result_aggressive.pruned_count == result_aggressive.original_count


class TestNumericalStability:
    """Test numerical stability across various input ranges."""

    @given(
        training_dataset=training_dataset_strategy(min_size=50, max_size=150),
        similarity_threshold=st.floats(min_value=0.1, max_value=3.0)
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_various_similarity_thresholds(self, training_dataset, similarity_threshold):
        """Test pruning with various similarity thresholds."""
        result = prune_training_data(training_dataset, similarity_threshold=similarity_threshold)
        
        assert isinstance(result, PruningResult)
        assert result.pruned_count <= result.original_count

    @given(
        training_dataset=training_dataset_strategy(min_size=50, max_size=150),
        target_ratio=st.floats(min_value=0.05, max_value=0.95)
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_various_pruning_ratios(self, training_dataset, target_ratio):
        """Test pruning with various target ratios."""
        result = prune_training_data(training_dataset, target_pruning_ratio=target_ratio)
        
        assert isinstance(result, PruningResult)
        assert result.pruned_count <= result.original_count


class TestIntegrationProperties:
    """Test integration properties across multiple components."""

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_multiple_pruning_operations_idempotent(self, training_dataset):
        """Test that pruning twice doesn't change result significantly."""
        # First pruning
        result1 = prune_training_data(training_dataset)
        
        # Second pruning on already pruned data
        result2 = prune_training_data(result1.pruned_data)
        
        # Second pruning should remove very few or no samples
        # (data is already pruned, below MIN_SAMPLES_FOR_PRUNING, or optimal)
        assert result2.removed_count <= result1.removed_count * 0.2 or \
               result2.original_count < MIN_SAMPLES_FOR_PRUNING

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_auto_prune_consistency(self, training_dataset):
        """Test that auto_prune produces consistent results."""
        result1 = auto_prune_training_data(training_dataset, aggressive=False)
        result2 = auto_prune_training_data(training_dataset, aggressive=False)
        
        # Should produce same pruned count (deterministic for same dataset)
        assert result1.pruned_count == result2.pruned_count

    @given(training_dataset=training_dataset_strategy(min_size=50, max_size=150))
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_memory_estimate_scales_with_removed_count(self, training_dataset):
        """Test that memory saved estimate scales with removed samples."""
        result = prune_training_data(training_dataset)
        
        if result.removed_count > 0:
            # Memory saved should be positive
            assert result.memory_saved_estimate > 0
            
            # Memory saved should scale roughly with removed count
            # (within reasonable bounds - each sample ~1KB)
            bytes_per_sample = result.memory_saved_estimate / result.removed_count
            assert 100 < bytes_per_sample < 100000  # Between 100 bytes and 100KB per sample
