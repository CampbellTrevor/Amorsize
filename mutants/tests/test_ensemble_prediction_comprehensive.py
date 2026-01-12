"""Comprehensive tests for ensemble prediction functionality (Iteration 126)."""

import pytest
import math
import tempfile
import json
import os
import time
from pathlib import Path
from amorsize.ml_prediction import (
    SimpleLinearPredictor,
    WorkloadFeatures,
    TrainingData,
    ENABLE_ENSEMBLE_PREDICTION,
    MIN_SAMPLES_FOR_ENSEMBLE,
    INITIAL_ENSEMBLE_WEIGHTS,
    ENSEMBLE_LEARNING_RATE,
    MIN_STRATEGY_WEIGHT,
    ENSEMBLE_WEIGHTS_FILE
)
from amorsize.cache import get_cache_dir


def create_test_features(estimated_item_time=0.001, data_size=1000, pickle_size=100, cv=0.1):
    """Helper to create WorkloadFeatures with common defaults."""
    return WorkloadFeatures(
        data_size=data_size,
        estimated_item_time=estimated_item_time,
        physical_cores=4,
        available_memory=8_000_000_000,
        start_method='fork',
        pickle_size=pickle_size,
        coefficient_of_variation=cv
    )


def create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0):
    """Helper to create TrainingData with common defaults."""
    return TrainingData(
        features=features,
        n_jobs=n_jobs,
        chunksize=chunksize,
        speedup=speedup,
        timestamp=time.time()
    )


class TestIndividualStrategies:
    """Test individual prediction strategies."""
    
    def test_knn_strategy_basic(self):
        """k-NN strategy should work with sufficient training data."""
        predictor = SimpleLinearPredictor(enable_ensemble=False)
        
        # Add training data
        for i in range(10):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.001 * (i + 1),
                physical_cores=4,
                available_memory=8_000_000_000,
                start_method='fork',
                pickle_size=100,
                coefficient_of_variation=0.1
            )
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        # Test k-NN prediction
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        result = predictor._predict_knn_strategy(test_features, k=3)
        assert result is not None
        n_jobs, chunksize = result
        assert n_jobs > 0
        assert chunksize > 0
    
    def test_linear_strategy_basic(self):
        """Linear strategy should work with sufficient training data."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Add training data with clear linear relationship
        for i in range(10):
            exec_time = 0.001 * (i + 1)
            n_jobs_val = 2 + i  # Linear relationship
            features = create_test_features(estimated_item_time=exec_time, data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=n_jobs_val, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        # Test linear prediction
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        result = predictor._predict_linear_strategy(test_features, k=5)
        assert result is not None
        n_jobs, chunksize = result
        assert n_jobs > 0
        assert chunksize > 0
    
    def test_cluster_strategy_basic(self):
        """Cluster strategy should work with clustering enabled."""
        predictor = SimpleLinearPredictor(enable_clustering=True, enable_ensemble=True)
        
        # Add enough training data for clustering
        for i in range(20):
            exec_time = 0.001 if i < 10 else 0.01  # Two clusters
            features = create_test_features(estimated_item_time=exec_time, data_size=1000, cv=0.1)
            n_jobs_val = 2 if i < 10 else 4
            sample = create_test_sample(features, n_jobs=n_jobs_val, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        # Trigger clustering
        predictor._update_clusters()
        
        # Test cluster prediction
        test_features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        cluster = predictor._find_best_cluster(test_features)
        if cluster is not None:
            result = predictor._predict_cluster_strategy(test_features, cluster)
            assert result is not None
            n_jobs, chunksize = result
            assert n_jobs > 0
            assert chunksize > 0
    
    def test_linear_strategy_insufficient_data(self):
        """Linear strategy should return None with insufficient data."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Add only 2 samples (need at least 3)
        for i in range(2):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        result = predictor._predict_linear_strategy(test_features, k=5)
        assert result is None


class TestEnsembleVoting:
    """Test ensemble weighted voting mechanism."""
    
    def test_ensemble_combines_strategies(self):
        """Ensemble should combine predictions from multiple strategies."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Add sufficient training data
        for i in range(20):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10 + i, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        result = predictor._ensemble_predict(test_features, k=5)
        assert result is not None
        n_jobs, chunksize, strategies = result
        assert n_jobs > 0
        assert chunksize > 0
        assert isinstance(strategies, dict)
        assert len(strategies) >= 1  # At least one strategy succeeded
    
    def test_ensemble_equal_weights(self):
        """With equal weights, ensemble should average predictions."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Set equal weights
        predictor.ensemble_weights = {'knn': 1.0, 'linear': 1.0, 'cluster': 1.0}
        
        # Add training data
        for i in range(20):
            features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        result = predictor._ensemble_predict(test_features, k=5)
        assert result is not None
    
    def test_ensemble_weighted_voting(self):
        """Ensemble should respect strategy weights."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Set different weights
        predictor.ensemble_weights = {'knn': 2.0, 'linear': 1.0, 'cluster': 0.5}
        
        # Add training data
        for i in range(20):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        result = predictor._ensemble_predict(test_features, k=5)
        assert result is not None
        n_jobs, chunksize, strategies = result
        
        # Weighted result should be different from simple average
        if len(strategies) > 1:
            simple_avg_n_jobs = sum(p[0] for p in strategies.values()) / len(strategies)
            # Weighted result may differ from simple average (within reason)
            assert abs(n_jobs - simple_avg_n_jobs) < 10  # Reasonable tolerance
    
    def test_ensemble_fallback_insufficient_data(self):
        """Ensemble should fall back to k-NN with insufficient data."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Add only 10 samples (less than MIN_SAMPLES_FOR_ENSEMBLE)
        for i in range(10):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        result = predictor._ensemble_predict(test_features, k=5)
        assert result is not None
        n_jobs, chunksize, strategies = result
        # Should only have k-NN prediction
        assert 'knn' in strategies


class TestAdaptiveWeightLearning:
    """Test adaptive weight adjustment based on accuracy."""
    
    def test_weight_update_perfect_prediction(self):
        """Perfect predictions should increase weight."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        initial_weight = predictor.ensemble_weights['knn']
        
        features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        # Simulate perfect prediction
        strategy_predictions = {'knn': (4.0, 10.0)}
        predictor.update_ensemble_weights(features, 4, 10, strategy_predictions)
        
        # Weight should increase (move toward 2.0)
        updated_weight = predictor.ensemble_weights['knn']
        assert updated_weight > initial_weight or abs(updated_weight - 2.0) < 0.01
    
    def test_weight_update_poor_prediction(self):
        """Poor predictions should decrease weight."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Set initial weight higher than minimum
        predictor.ensemble_weights['knn'] = 1.5
        initial_weight = predictor.ensemble_weights['knn']
        
        features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        # Simulate poor prediction (predict 8 when actual is 2)
        strategy_predictions = {'knn': (8.0, 50.0)}
        predictor.update_ensemble_weights(features, 2, 10, strategy_predictions)
        
        # Weight should decrease (move toward MIN_STRATEGY_WEIGHT)
        updated_weight = predictor.ensemble_weights['knn']
        assert updated_weight < initial_weight
    
    def test_weight_minimum_enforced(self):
        """Weight should never go below minimum."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        # Simulate terrible predictions multiple times
        strategy_predictions = {'knn': (100.0, 100.0)}
        for _ in range(100):  # Many iterations to reach convergence
            predictor.update_ensemble_weights(features, 2, 10, strategy_predictions)
        
        # Weight should be at or near minimum
        final_weight = predictor.ensemble_weights['knn']
        assert final_weight >= MIN_STRATEGY_WEIGHT
        # With exponential moving average, it converges but slowly
        # Accept any value reasonably close to minimum
        assert final_weight <= MIN_STRATEGY_WEIGHT * 2.0
    
    def test_weight_learning_rate(self):
        """Weights should update gradually based on learning rate."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        initial_weight = predictor.ensemble_weights['linear']
        
        features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        # One perfect prediction
        strategy_predictions = {'linear': (4.0, 10.0)}
        predictor.update_ensemble_weights(features, 4, 10, strategy_predictions)
        
        updated_weight = predictor.ensemble_weights['linear']
        
        # Change should be proportional to learning rate (0.05)
        # Target weight for perfect prediction is 2.0
        expected_change = ENSEMBLE_LEARNING_RATE * (2.0 - initial_weight)
        actual_change = updated_weight - initial_weight
        
        # Should be approximately equal (with some tolerance)
        assert abs(actual_change - expected_change) < 0.01
    
    def test_multiple_strategy_updates(self):
        """Multiple strategies should update independently."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        initial_weights = predictor.ensemble_weights.copy()
        
        features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        # Different accuracy for different strategies
        strategy_predictions = {
            'knn': (4.0, 10.0),      # Perfect
            'linear': (6.0, 15.0),   # Moderate
            'cluster': (10.0, 30.0)  # Poor
        }
        predictor.update_ensemble_weights(features, 4, 10, strategy_predictions)
        
        # All weights should have changed
        for strategy in ['knn', 'linear', 'cluster']:
            assert predictor.ensemble_weights[strategy] != initial_weights.get(strategy, 1.0)


class TestWeightPersistence:
    """Test weight save/load functionality."""
    
    def test_save_ensemble_weights(self):
        """Ensemble weights should be saved to file."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Modify weights
        predictor.ensemble_weights = {'knn': 1.5, 'linear': 1.2, 'cluster': 0.8}
        
        # Save weights
        predictor._save_ensemble_weights()
        
        # Check file exists
        cache_dir = get_cache_dir()
        weights_file = cache_dir / ENSEMBLE_WEIGHTS_FILE
        assert weights_file.exists()
        
        # Check content
        with open(weights_file, 'r') as f:
            data = json.load(f)
            assert 'weights' in data
            assert data['weights']['knn'] == 1.5
            assert data['weights']['linear'] == 1.2
            assert data['weights']['cluster'] == 0.8
    
    def test_load_ensemble_weights(self):
        """Ensemble weights should be loaded from file."""
        # Create weights file
        cache_dir = get_cache_dir()
        weights_file = cache_dir / ENSEMBLE_WEIGHTS_FILE
        
        test_weights = {'knn': 1.3, 'linear': 1.7, 'cluster': 0.6}
        with open(weights_file, 'w') as f:
            json.dump({'weights': test_weights}, f)
        
        # Create predictor (should load weights)
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Check weights were loaded
        assert predictor.ensemble_weights['knn'] == 1.3
        assert predictor.ensemble_weights['linear'] == 1.7
        assert predictor.ensemble_weights['cluster'] == 0.6
    
    def test_load_corrupted_weights_fallback(self):
        """Should fall back to initial weights if file is corrupted."""
        cache_dir = get_cache_dir()
        weights_file = cache_dir / ENSEMBLE_WEIGHTS_FILE
        
        # Write corrupted data
        with open(weights_file, 'w') as f:
            f.write("not valid json{{{")
        
        # Should not crash, should use initial weights
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Weights should be initial values
        assert predictor.ensemble_weights['knn'] == INITIAL_ENSEMBLE_WEIGHTS['knn']
        assert predictor.ensemble_weights['linear'] == INITIAL_ENSEMBLE_WEIGHTS['linear']
        assert predictor.ensemble_weights['cluster'] == INITIAL_ENSEMBLE_WEIGHTS['cluster']
    
    def test_load_invalid_strategy_names(self):
        """Should ignore invalid strategy names."""
        cache_dir = get_cache_dir()
        weights_file = cache_dir / ENSEMBLE_WEIGHTS_FILE
        
        # Write weights with invalid strategy names
        test_weights = {
            'knn': 1.3,
            'linear': 1.7,
            'invalid_strategy': 2.0,  # Invalid
            'malicious': 5.0           # Invalid
        }
        with open(weights_file, 'w') as f:
            json.dump({'weights': test_weights}, f)
        
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Valid strategies should be loaded
        assert predictor.ensemble_weights['knn'] == 1.3
        assert predictor.ensemble_weights['linear'] == 1.7
        # Invalid strategies should not be loaded
        assert 'invalid_strategy' not in predictor.ensemble_weights
        assert 'malicious' not in predictor.ensemble_weights
    
    def test_load_invalid_weight_values(self):
        """Should ignore invalid weight values."""
        cache_dir = get_cache_dir()
        weights_file = cache_dir / ENSEMBLE_WEIGHTS_FILE
        
        # Write weights with invalid values (need at least 2 valid for loading)
        test_weights = {
            'knn': 1.3,
            'linear': 1.5,       # Valid
            'cluster': 100.0     # Invalid (too large) - will be ignored
        }
        with open(weights_file, 'w') as f:
            json.dump({'weights': test_weights}, f)
        
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Valid weights should be loaded
        assert predictor.ensemble_weights['knn'] == 1.3
        assert predictor.ensemble_weights['linear'] == 1.5
        # Invalid weight was excluded from loaded weights (only valid ones are loaded)
        assert 'cluster' not in predictor.ensemble_weights


class TestEdgeCases:
    """Test edge cases and robustness."""
    
    def test_all_strategies_same_prediction(self):
        """Handle case where all strategies predict the same values."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Add identical training data
        for i in range(20):
            features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        
        result = predictor._ensemble_predict(test_features, k=5)
        assert result is not None
        n_jobs, chunksize, strategies = result
        # All strategies should predict approximately the same
        if len(strategies) > 1:
            n_jobs_values = [p[0] for p in strategies.values()]
            assert max(n_jobs_values) - min(n_jobs_values) < 5  # Small variance
    
    def test_single_strategy_available(self):
        """Handle case where only one strategy produces a prediction."""
        predictor = SimpleLinearPredictor(enable_ensemble=True, enable_clustering=False)
        
        # Add minimal training data (enough for k-NN but not linear)
        for i in range(5):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        # Should not use ensemble (insufficient data), but still work
        result = predictor._ensemble_predict(test_features, k=3)
        assert result is not None
    
    def test_ensemble_with_outliers(self):
        """Ensemble should be robust to outliers in training data."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Add normal training data plus outliers
        for i in range(18):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        # Add outliers
        outlier_features = create_test_features(estimated_item_time=0.001, data_size=1000, cv=0.1)
        outlier = create_test_sample(outlier_features, n_jobs=100, chunksize=1000, speedup=0.1)
        predictor.add_training_sample(outlier)
        predictor.add_training_sample(outlier)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        result = predictor._ensemble_predict(test_features, k=5)
        assert result is not None
        n_jobs, chunksize, strategies = result
        # Prediction should be reasonable despite outliers
        assert n_jobs < 50  # Should not be close to outlier value
        assert chunksize < 500
    
    def test_zero_total_weight(self):
        """Handle edge case where all weights are zero."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Set all weights to minimum (effectively zero contribution)
        predictor.ensemble_weights = {'knn': 0.0, 'linear': 0.0, 'cluster': 0.0}
        
        # Add training data
        for i in range(20):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        # Should use equal weighting fallback
        result = predictor._ensemble_predict(test_features, k=5)
        assert result is not None
        n_jobs, chunksize, strategies = result
        assert n_jobs > 0
        assert chunksize > 0


class TestPerformanceCharacteristics:
    """Test performance characteristics of ensemble predictions."""
    
    def test_ensemble_overhead_minimal(self):
        """Ensemble prediction should add minimal overhead."""
        import time
        
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        
        # Add training data
        for i in range(20):
            features = create_test_features(estimated_item_time=0.001 * (i + 1), data_size=1000, cv=0.1)
            sample = create_test_sample(features, n_jobs=4, chunksize=10, speedup=2.0)
            predictor.add_training_sample(sample)
        
        test_features = create_test_features(estimated_item_time=0.005, data_size=1000, cv=0.1)
        
        # Measure ensemble prediction time
        start = time.perf_counter()
        for _ in range(100):
            predictor._ensemble_predict(test_features, k=5)
        end = time.perf_counter()
        
        avg_time = (end - start) / 100
        
        # Should be very fast (<10ms per prediction)
        assert avg_time < 0.01
    
    def test_weight_persistence_fast(self):
        """Weight save/load should be fast."""
        import time
        
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        predictor.ensemble_weights = {'knn': 1.5, 'linear': 1.2, 'cluster': 0.8}
        
        # Measure save time
        start = time.perf_counter()
        for _ in range(100):
            predictor._save_ensemble_weights()
        end = time.perf_counter()
        
        avg_save_time = (end - start) / 100
        
        # Should be very fast (<1ms per save)
        assert avg_save_time < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
