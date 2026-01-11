"""
Tests for k-NN hyperparameter tuning (Iteration 124).

Tests automatic selection of optimal k value using cross-validation.
"""

import time
import pytest
from amorsize.ml_prediction import (
    SimpleLinearPredictor,
    TrainingData,
    WorkloadFeatures,
    ENABLE_K_TUNING,
    K_RANGE_MIN,
    K_RANGE_MAX,
    MIN_SAMPLES_FOR_K_TUNING,
    DEFAULT_K_VALUE
)


def create_test_features(
    data_size: int = 1000,
    estimated_item_time: float = 0.01,
    physical_cores: int = 4,
    available_memory: int = 8 * 1024 ** 3,
    start_method: str = 'fork',
    pickle_size: int = 100,
    coefficient_of_variation: float = 0.1,
    function_complexity: int = 50
) -> WorkloadFeatures:
    """Helper to create WorkloadFeatures for testing."""
    return WorkloadFeatures(
        data_size=data_size,
        estimated_item_time=estimated_item_time,
        physical_cores=physical_cores,
        available_memory=available_memory,
        start_method=start_method,
        pickle_size=pickle_size,
        coefficient_of_variation=coefficient_of_variation,
        function_complexity=function_complexity
    )


def create_synthetic_training_data(n_samples: int = 20) -> list:
    """
    Create synthetic training data with known patterns.
    
    Pattern: n_jobs increases with physical_cores, chunksize decreases with data_size.
    """
    training_data = []
    
    for i in range(n_samples):
        # Vary key features
        cores = 2 + (i % 8)  # 2-9 cores
        data_size = 1000 + i * 500  # 1000-10000+ items
        
        # Create pattern: n_jobs ~ cores, chunksize ~ 1000/sqrt(data_size)
        n_jobs = min(cores, 8)
        chunksize = max(10, int(1000 / (data_size ** 0.5)))
        
        features = create_test_features(
            data_size=data_size,
            physical_cores=cores,
            estimated_item_time=0.001 + i * 0.0001
        )
        
        sample = TrainingData(
            features=features,
            n_jobs=n_jobs,
            chunksize=chunksize,
            speedup=1.5,
            timestamp=time.time(),
            weight=1.0
        )
        training_data.append(sample)
    
    return training_data


class TestKTuningConstants:
    """Test that k tuning constants are properly defined."""
    
    def test_constants_exist(self):
        """Test that all k tuning constants are defined."""
        assert isinstance(ENABLE_K_TUNING, bool)
        assert isinstance(K_RANGE_MIN, int)
        assert isinstance(K_RANGE_MAX, int)
        assert isinstance(MIN_SAMPLES_FOR_K_TUNING, int)
        assert isinstance(DEFAULT_K_VALUE, int)
    
    def test_constants_valid_values(self):
        """Test that constants have reasonable values."""
        assert K_RANGE_MIN >= 1
        assert K_RANGE_MAX > K_RANGE_MIN
        # Need enough samples for cross-validation
        # At minimum we need k+1 samples for LOOCV with k neighbors
        assert MIN_SAMPLES_FOR_K_TUNING >= K_RANGE_MAX
        assert DEFAULT_K_VALUE >= K_RANGE_MIN
        assert DEFAULT_K_VALUE <= K_RANGE_MAX


class TestSimpleLinearPredictorKTuning:
    """Test SimpleLinearPredictor k tuning functionality."""
    
    def test_initialization_with_auto_tune(self):
        """Test that predictor initializes with auto_tune_k parameter."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        assert predictor.auto_tune_k is True
        assert predictor._optimal_k is None
        assert predictor._k_tuning_dirty is True
        assert predictor._last_k_tuning_size == 0
    
    def test_initialization_without_auto_tune(self):
        """Test that predictor can disable auto tuning."""
        predictor = SimpleLinearPredictor(k=7, auto_tune_k=False)
        assert predictor.auto_tune_k is False
        assert predictor.k == 7
    
    def test_k_tuning_requires_sufficient_data(self):
        """Test that k tuning requires minimum samples."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add insufficient samples (less than MIN_SAMPLES_FOR_K_TUNING)
        for i in range(10):
            features = create_test_features(data_size=1000 + i * 100)
            sample = TrainingData(features, n_jobs=4, chunksize=100, speedup=1.5, timestamp=time.time())
            predictor.add_training_sample(sample)
        
        # Try to update k tuning
        predictor._update_k_tuning()
        
        # Should use default k since not enough samples
        assert predictor._optimal_k == predictor.k
    
    def test_k_tuning_with_sufficient_data(self):
        """Test that k tuning works with sufficient samples."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add sufficient samples
        training_data = create_synthetic_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING + 5)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Update k tuning
        predictor._update_k_tuning()
        
        # Should have selected an optimal k
        assert predictor._optimal_k is not None
        assert K_RANGE_MIN <= predictor._optimal_k <= K_RANGE_MAX
        assert predictor._k_tuning_dirty is False
        assert predictor._last_k_tuning_size == len(training_data)
    
    def test_k_tuning_retune_on_significant_growth(self):
        """Test that k is retuned when training data grows significantly."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add initial samples
        initial_samples = create_synthetic_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING)
        for sample in initial_samples:
            predictor.add_training_sample(sample)
        
        # Trigger initial tuning
        predictor._update_k_tuning()
        initial_optimal_k = predictor._optimal_k
        
        # Add more samples (>20% growth to trigger retune)
        additional_samples_needed = int(MIN_SAMPLES_FOR_K_TUNING * 0.25)  # 25% growth
        for i in range(additional_samples_needed):
            features = create_test_features(data_size=5000 + i * 100)
            sample = TrainingData(features, n_jobs=4, chunksize=50, speedup=1.8, timestamp=time.time())
            predictor.add_training_sample(sample)
        
        # k tuning should be marked dirty
        assert predictor._k_tuning_dirty is True
        
        # Update k tuning again
        predictor._update_k_tuning()
        
        # Should have retuned
        assert predictor._k_tuning_dirty is False
        assert predictor._last_k_tuning_size > MIN_SAMPLES_FOR_K_TUNING
    
    def test_loocv_score_calculation(self):
        """Test Leave-One-Out Cross-Validation score calculation."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add small dataset for LOOCV
        training_data = create_synthetic_training_data(n_samples=20)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Calculate LOOCV score for k=3
        score_k3 = predictor._loocv_score(k_test=3)
        
        # Score should be finite and non-negative
        assert score_k3 < float('inf')
        assert score_k3 >= 0.0
        
        # Try different k values - scores should vary
        score_k5 = predictor._loocv_score(k_test=5)
        score_k7 = predictor._loocv_score(k_test=7)
        
        # Scores should be different (not all the same)
        scores = [score_k3, score_k5, score_k7]
        assert len(set(scores)) > 1, "Different k values should produce different scores"
    
    def test_kfold_cv_score_calculation(self):
        """Test k-Fold Cross-Validation score calculation."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add larger dataset for k-fold CV
        training_data = create_synthetic_training_data(n_samples=50)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Calculate k-fold CV score for k=3
        score_k3 = predictor._kfold_cv_score(k_test=3, n_folds=5)
        
        # Score should be finite and non-negative
        assert score_k3 < float('inf')
        assert score_k3 >= 0.0
        
        # Try different k values
        score_k5 = predictor._kfold_cv_score(k_test=5, n_folds=5)
        score_k7 = predictor._kfold_cv_score(k_test=7, n_folds=5)
        
        # Scores should vary
        scores = [score_k3, score_k5, score_k7]
        assert len(set(scores)) > 1
    
    def test_select_optimal_k(self):
        """Test that optimal k selection works correctly."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add synthetic data with known pattern
        training_data = create_synthetic_training_data(n_samples=30)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Select optimal k
        optimal_k = predictor._select_optimal_k()
        
        # Should return a valid k in the range
        assert K_RANGE_MIN <= optimal_k <= K_RANGE_MAX
        assert isinstance(optimal_k, int)
    
    def test_predict_uses_optimal_k(self):
        """Test that predict uses optimal k when available."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add training data
        training_data = create_synthetic_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING + 5)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Make a prediction (this should trigger k tuning)
        test_features = create_test_features(data_size=5000, physical_cores=6)
        result = predictor.predict(test_features, confidence_threshold=0.5)
        
        # Verify k tuning was performed
        assert predictor._optimal_k is not None
        assert predictor._k_tuning_dirty is False
        
        # Verify prediction result includes k information
        if result is not None:
            assert f"k={predictor._optimal_k}" in result.reason
    
    def test_predict_without_auto_tune_k(self):
        """Test that predict works when auto_tune_k is disabled."""
        predictor = SimpleLinearPredictor(k=7, auto_tune_k=False)
        
        # Add training data
        training_data = create_synthetic_training_data(n_samples=20)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Make a prediction
        test_features = create_test_features(data_size=5000, physical_cores=6)
        result = predictor.predict(test_features, confidence_threshold=0.5)
        
        # Should not have performed k tuning
        assert predictor._optimal_k is None
        
        # Should use user-specified k=7
        if result is not None:
            # Reason should not mention optimal k
            assert "optimal k=" not in result.reason


class TestKTuningEdgeCases:
    """Test edge cases for k tuning."""
    
    def test_k_tuning_with_constant_predictions(self):
        """Test k tuning when all samples have same optimal parameters."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add samples with identical n_jobs and chunksize
        for i in range(MIN_SAMPLES_FOR_K_TUNING + 5):
            features = create_test_features(data_size=1000 + i * 100)
            sample = TrainingData(features, n_jobs=4, chunksize=100, speedup=1.5, timestamp=time.time())
            predictor.add_training_sample(sample)
        
        # Should still be able to select an optimal k
        optimal_k = predictor._select_optimal_k()
        assert K_RANGE_MIN <= optimal_k <= K_RANGE_MAX
    
    def test_k_tuning_with_noisy_data(self):
        """Test k tuning with noisy/random data."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        import random
        random.seed(42)  # For reproducibility
        
        # Add noisy data
        for i in range(MIN_SAMPLES_FOR_K_TUNING + 10):
            features = create_test_features(
                data_size=random.randint(1000, 10000),
                physical_cores=random.randint(2, 8)
            )
            n_jobs = random.randint(1, 8)
            chunksize = random.randint(10, 1000)
            sample = TrainingData(features, n_jobs=n_jobs, chunksize=chunksize, speedup=1.5, timestamp=time.time())
            predictor.add_training_sample(sample)
        
        # Should still work without errors
        optimal_k = predictor._select_optimal_k()
        assert K_RANGE_MIN <= optimal_k <= K_RANGE_MAX
    
    def test_find_neighbors_from_list(self):
        """Test _find_neighbors_from_list helper method."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Create candidate samples
        candidates = create_synthetic_training_data(n_samples=10)
        
        # Create query features
        query_features = create_test_features(data_size=5000, physical_cores=5)
        
        # Find neighbors
        neighbors = predictor._find_neighbors_from_list(query_features, candidates, k=3)
        
        # Should return k neighbors
        assert len(neighbors) == 3
        
        # Should be sorted by distance
        distances = [dist for dist, _ in neighbors]
        assert distances == sorted(distances)
        
        # Each neighbor should be a tuple of (distance, TrainingData)
        for dist, sample in neighbors:
            assert isinstance(dist, float)
            assert isinstance(sample, TrainingData)
    
    def test_k_tuning_cache_behavior(self):
        """Test that k tuning results are cached properly."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add training data
        training_data = create_synthetic_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING + 5)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # First tuning
        predictor._update_k_tuning()
        first_optimal_k = predictor._optimal_k
        first_tuning_size = predictor._last_k_tuning_size
        
        # Mark as not dirty
        assert predictor._k_tuning_dirty is False
        
        # Call update again - should not retune
        predictor._update_k_tuning()
        
        # Should have same results
        assert predictor._optimal_k == first_optimal_k
        assert predictor._last_k_tuning_size == first_tuning_size


class TestKTuningIntegration:
    """Integration tests for k tuning with other features."""
    
    def test_k_tuning_with_clustering(self):
        """Test that k tuning works with workload clustering."""
        predictor = SimpleLinearPredictor(
            k=5,
            auto_tune_k=True,
            enable_clustering=True
        )
        
        # Add training data
        training_data = create_synthetic_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING + 10)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Make prediction (triggers k tuning and clustering)
        test_features = create_test_features(data_size=5000, physical_cores=6)
        result = predictor.predict(test_features, confidence_threshold=0.5)
        
        # Both k tuning and clustering should work
        assert predictor._optimal_k is not None
        # Clustering may or may not be active depending on data
    
    def test_k_tuning_with_feature_selection(self):
        """Test that k tuning works with feature selection."""
        predictor = SimpleLinearPredictor(
            k=5,
            auto_tune_k=True,
            enable_feature_selection=True
        )
        
        # Add training data
        training_data = create_synthetic_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING + 10)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Make prediction
        test_features = create_test_features(data_size=5000, physical_cores=6)
        result = predictor.predict(test_features, confidence_threshold=0.5)
        
        # k tuning should work
        assert predictor._optimal_k is not None
    
    def test_k_tuning_verbose_output(self):
        """Test that verbose mode outputs k tuning information."""
        predictor = SimpleLinearPredictor(k=5, auto_tune_k=True)
        
        # Add training data
        training_data = create_synthetic_training_data(n_samples=MIN_SAMPLES_FOR_K_TUNING + 5)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Make prediction with verbose=True (should print k tuning info)
        test_features = create_test_features(data_size=5000, physical_cores=6)
        
        # Capture output would require capsys fixture, but we can at least verify it doesn't crash
        result = predictor.predict(test_features, confidence_threshold=0.5, verbose=True)
        
        # Should complete without errors
        assert predictor._optimal_k is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
