"""
Test suite for ML-based prediction functionality.

Tests the ml_prediction module for fast parameter estimation without dry-run sampling.
"""

import pytest
import time
from amorsize.ml_prediction import (
    WorkloadFeatures,
    TrainingData,
    SimpleLinearPredictor,
    predict_parameters,
    MIN_TRAINING_SAMPLES,
    DEFAULT_CONFIDENCE_THRESHOLD
)
from amorsize import optimize


# Test functions
def simple_function(x):
    """Simple test function."""
    return x * 2


def expensive_function(x):
    """Expensive test function."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


# ============================================================================
# WorkloadFeatures Tests
# ============================================================================

class TestWorkloadFeatures:
    """Test suite for WorkloadFeatures class."""
    
    def test_feature_creation(self):
        """Test creating workload features."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,  # 16GB
            start_method='fork'
        )
        
        assert features.data_size == 1000
        assert features.estimated_item_time == 0.01
        assert features.physical_cores == 8
        assert features.start_method == 'fork'
        
    def test_feature_normalization(self):
        """Test that features are normalized to [0, 1] range."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.001,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork'
        )
        
        # All normalized values should be in [0, 1]
        assert 0.0 <= features.norm_data_size <= 1.0
        assert 0.0 <= features.norm_time <= 1.0
        assert 0.0 <= features.norm_cores <= 1.0
        assert 0.0 <= features.norm_memory <= 1.0
        assert 0.0 <= features.norm_start_method <= 1.0
    
    def test_feature_vector(self):
        """Test converting features to vector."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork'
        )
        
        vector = features.to_vector()
        assert len(vector) == 5
        assert all(isinstance(v, float) for v in vector)
        assert all(0.0 <= v <= 1.0 for v in vector)
    
    def test_feature_distance(self):
        """Test distance calculation between feature vectors."""
        features1 = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork'
        )
        
        features2 = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork'
        )
        
        # Distance to self should be 0
        distance = features1.distance(features2)
        assert distance == 0.0
        
        # Distance to different features should be > 0
        features3 = WorkloadFeatures(
            data_size=10000,  # Different size
            estimated_item_time=0.001,
            physical_cores=16,
            available_memory=32 * 1024**3,
            start_method='spawn'
        )
        
        distance2 = features1.distance(features3)
        assert distance2 > 0.0


# ============================================================================
# SimpleLinearPredictor Tests
# ============================================================================

class TestSimpleLinearPredictor:
    """Test suite for SimpleLinearPredictor class."""
    
    def test_predictor_creation(self):
        """Test creating a predictor."""
        predictor = SimpleLinearPredictor(k=5)
        assert predictor.k == 5
        assert len(predictor.training_data) == 0
    
    def test_add_training_sample(self):
        """Test adding training samples."""
        predictor = SimpleLinearPredictor(k=5)
        
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork'
        )
        
        sample = TrainingData(
            features=features,
            n_jobs=4,
            chunksize=50,
            speedup=3.5,
            timestamp=time.time()
        )
        
        predictor.add_training_sample(sample)
        assert len(predictor.training_data) == 1
    
    def test_predict_insufficient_data(self):
        """Test that prediction fails with insufficient training data."""
        predictor = SimpleLinearPredictor(k=5)
        
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork'
        )
        
        # Should fail with no training data
        prediction = predictor.predict(features)
        assert prediction is None
        
        # Should still fail with only 2 samples (minimum is 3)
        for _ in range(2):
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=50,
                speedup=3.5,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        prediction = predictor.predict(features)
        assert prediction is None
    
    def test_predict_with_sufficient_data(self):
        """Test prediction with sufficient training data."""
        predictor = SimpleLinearPredictor(k=3)
        
        # Add 5 training samples with similar features
        for i in range(5):
            features = WorkloadFeatures(
                data_size=1000 + i * 10,  # Slightly varying sizes
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=16 * 1024**3,
                start_method='fork'
            )
            
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=50,
                speedup=3.5,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        # Predict for similar workload
        test_features = WorkloadFeatures(
            data_size=1020,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork'
        )
        
        # Lower confidence threshold for this test
        prediction = predictor.predict(test_features, confidence_threshold=0.3)
        
        # Should get a prediction
        assert prediction is not None
        assert prediction.n_jobs >= 1
        assert prediction.chunksize >= 1
        assert 0.0 <= prediction.confidence <= 1.0
    
    def test_predict_low_confidence(self):
        """Test that low confidence predictions are rejected."""
        predictor = SimpleLinearPredictor(k=3)
        
        # Add training samples with very different features
        for i in range(3):
            features = WorkloadFeatures(
                data_size=1000 * (i + 1),  # Very different sizes
                estimated_item_time=0.001 * (i + 1),
                physical_cores=4 * (i + 1),
                available_memory=8 * 1024**3 * (i + 1),
                start_method=['fork', 'spawn', 'forkserver'][i]
            )
            
            sample = TrainingData(
                features=features,
                n_jobs=(i + 1) * 2,
                chunksize=(i + 1) * 20,
                speedup=2.0,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        # Try to predict for very different workload
        test_features = WorkloadFeatures(
            data_size=100000,  # Much larger than training
            estimated_item_time=0.1,
            physical_cores=32,
            available_memory=128 * 1024**3,
            start_method='spawn'
        )
        
        # Should fail due to low confidence (high threshold)
        prediction = predictor.predict(test_features, confidence_threshold=0.9)
        assert prediction is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestMLPredictionIntegration:
    """Integration tests for ML prediction with optimize()."""
    
    def test_optimize_with_ml_disabled(self):
        """Test that optimize works normally with ML disabled."""
        data = list(range(100))
        result = optimize(simple_function, data, use_ml_prediction=False)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_optimize_with_ml_enabled_no_training_data(self):
        """Test that optimize falls back gracefully when ML has no training data."""
        data = list(range(100))
        result = optimize(simple_function, data, use_ml_prediction=True, verbose=False)
        
        # Should fall back to traditional optimization
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_ml_confidence_threshold_validation(self):
        """Test that invalid confidence thresholds are rejected."""
        data = list(range(100))
        
        # Confidence threshold must be between 0 and 1
        with pytest.raises(ValueError, match="ml_confidence_threshold must be between 0.0 and 1.0"):
            optimize(simple_function, data, use_ml_prediction=True, ml_confidence_threshold=-0.1)
        
        with pytest.raises(ValueError, match="ml_confidence_threshold must be between 0.0 and 1.0"):
            optimize(simple_function, data, use_ml_prediction=True, ml_confidence_threshold=1.5)
    
    def test_ml_prediction_parameter_types(self):
        """Test parameter type validation for ML prediction."""
        data = list(range(100))
        
        # use_ml_prediction must be boolean
        with pytest.raises(ValueError, match="use_ml_prediction must be a boolean"):
            optimize(simple_function, data, use_ml_prediction="true")
        
        # ml_confidence_threshold must be numeric
        with pytest.raises(ValueError, match="ml_confidence_threshold must be a number"):
            optimize(simple_function, data, use_ml_prediction=True, ml_confidence_threshold="0.7")


# ============================================================================
# API Tests
# ============================================================================

class TestPredictParametersAPI:
    """Test the public predict_parameters API."""
    
    def test_predict_parameters_no_training_data(self):
        """Test predict_parameters with no training data."""
        result = predict_parameters(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.01,
            verbose=False
        )
        
        # Should return None (insufficient training data)
        assert result is None
    
    def test_predict_parameters_with_verbose(self):
        """Test predict_parameters with verbose output."""
        result = predict_parameters(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.01,
            verbose=True  # Should print diagnostic info
        )
        
        # Should return None but print messages
        assert result is None


# ============================================================================
# Edge Cases
# ============================================================================

class TestMLPredictionEdgeCases:
    """Test edge cases for ML prediction."""
    
    def test_empty_data(self):
        """Test ML prediction with empty data."""
        data = []
        result = optimize(simple_function, data, use_ml_prediction=True)
        
        # Should handle gracefully (likely return serial execution)
        assert result.n_jobs >= 1
    
    def test_generator_data(self):
        """Test ML prediction with generator data."""
        data = (x for x in range(100))
        result = optimize(simple_function, data, use_ml_prediction=True)
        
        # Should work (will fall back since generators don't have len())
        assert result.n_jobs >= 1
    
    def test_small_dataset(self):
        """Test ML prediction with very small dataset."""
        data = list(range(5))
        result = optimize(simple_function, data, use_ml_prediction=True)
        
        # Should handle gracefully
        assert result.n_jobs >= 1


# ============================================================================
# Constants Tests
# ============================================================================

class TestMLPredictionConstants:
    """Test module-level constants."""
    
    def test_min_training_samples(self):
        """Test MIN_TRAINING_SAMPLES constant."""
        assert MIN_TRAINING_SAMPLES >= 1
        assert isinstance(MIN_TRAINING_SAMPLES, int)
    
    def test_default_confidence_threshold(self):
        """Test DEFAULT_CONFIDENCE_THRESHOLD constant."""
        assert 0.0 <= DEFAULT_CONFIDENCE_THRESHOLD <= 1.0
        assert isinstance(DEFAULT_CONFIDENCE_THRESHOLD, float)
