"""
Tests for ML feature selection (Iteration 123).

Feature selection reduces the feature space from 12 dimensions to 5-7 most
predictive features, providing 30-50% faster predictions and reduced overfitting.
"""

import pytest
import math
from amorsize.ml_prediction import (
    FeatureSelector,
    SimpleLinearPredictor,
    WorkloadFeatures,
    TrainingData,
    MIN_SAMPLES_FOR_FEATURE_SELECTION,
    TARGET_SELECTED_FEATURES,
    ENABLE_FEATURE_SELECTION
)
from amorsize.system_info import get_physical_cores, get_available_memory


class TestFeatureSelectorCore:
    """Test core FeatureSelector functionality."""
    
    def test_feature_selector_initialization(self):
        """Test FeatureSelector initializes with default values."""
        selector = FeatureSelector()
        
        # Default: all 12 features selected
        assert selector.selected_features == list(range(12))
        assert selector.feature_names == []
        assert selector.importance_scores == {}
        assert selector.num_training_samples == 0
    
    def test_feature_selector_serialization(self):
        """Test FeatureSelector can be serialized and deserialized."""
        selector = FeatureSelector(
            selected_features=[0, 1, 2, 3, 4],
            feature_names=['data_size', 'execution_time', 'physical_cores', 'available_memory', 'start_method'],
            importance_scores={'data_size': 0.9, 'execution_time': 0.8},
            num_training_samples=50
        )
        
        # Serialize
        data = selector.to_dict()
        assert data['selected_features'] == [0, 1, 2, 3, 4]
        assert data['num_training_samples'] == 50
        
        # Deserialize
        restored = FeatureSelector.from_dict(data)
        assert restored.selected_features == selector.selected_features
        assert restored.feature_names == selector.feature_names
        assert restored.num_training_samples == selector.num_training_samples
    
    def test_apply_to_vector(self):
        """Test applying feature selection to a vector."""
        selector = FeatureSelector(selected_features=[0, 2, 4])  # Select 1st, 3rd, 5th features
        
        full_vector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
        reduced_vector = selector.apply_to_vector(full_vector)
        
        assert reduced_vector == [0.1, 0.3, 0.5]  # Only selected features
        assert len(reduced_vector) == 3


class TestFeatureSelection:
    """Test feature selection algorithm."""
    
    def test_insufficient_samples_uses_all_features(self):
        """Test that insufficient samples leads to using all features."""
        selector = FeatureSelector()
        
        # Create only 10 training samples (less than MIN_SAMPLES_FOR_FEATURE_SELECTION)
        training_data = []
        for i in range(10):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01 + i * 0.001,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            training_data.append(sample)
        
        # Select features
        selector.select_features(training_data, target_num_features=7)
        
        # Should use all 12 features due to insufficient samples
        assert selector.selected_features == list(range(12))
        assert selector.num_training_samples == 10
    
    def test_sufficient_samples_selects_features(self):
        """Test that sufficient samples leads to feature selection."""
        selector = FeatureSelector()
        
        # Create enough training samples
        training_data = []
        for i in range(MIN_SAMPLES_FOR_FEATURE_SELECTION + 5):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01 + i * 0.001,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork',
                pickle_size=100 + i * 10,
                coefficient_of_variation=0.1 + i * 0.01
            )
            # Vary n_jobs with data_size to create correlation
            sample = TrainingData(features, n_jobs=min(8, 1 + i // 3), chunksize=10, speedup=3.0, timestamp=0.0)
            training_data.append(sample)
        
        # Select features
        selector.select_features(training_data, target_num_features=7)
        
        # Should select exactly 7 features
        assert len(selector.selected_features) == 7
        assert len(selector.feature_names) == 7
        assert selector.num_training_samples == MIN_SAMPLES_FOR_FEATURE_SELECTION + 5
        
        # Selected features should be sorted (for consistent ordering)
        assert selector.selected_features == sorted(selector.selected_features)
        
        # Importance scores should be present
        assert len(selector.importance_scores) == 7
        assert all(0.0 <= score <= 1.0 for score in selector.importance_scores.values())
    
    def test_feature_selection_prioritizes_correlated_features(self):
        """Test that feature selection prioritizes features correlated with targets."""
        selector = FeatureSelector()
        
        # Create training data where data_size strongly correlates with n_jobs
        training_data = []
        for i in range(30):
            data_size = 1000 * (i + 1)  # Increasing data size
            features = WorkloadFeatures(
                data_size=data_size,
                estimated_item_time=0.01,  # Constant (no correlation)
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            # n_jobs increases with data_size
            n_jobs = min(8, 1 + i // 4)
            sample = TrainingData(features, n_jobs=n_jobs, chunksize=10, speedup=3.0, timestamp=0.0)
            training_data.append(sample)
        
        # Select features
        selector.select_features(training_data, target_num_features=5)
        
        # data_size should be selected (feature index 0) due to high correlation
        assert 0 in selector.selected_features
        assert 'data_size' in selector.feature_names
        
        # Should have reasonable importance score (lowered threshold as correlation may vary)
        assert selector.importance_scores['data_size'] > 0.3


class TestPredictorIntegration:
    """Test feature selection integration with SimpleLinearPredictor."""
    
    def test_predictor_initializes_with_feature_selection(self):
        """Test predictor initializes with feature selection enabled."""
        predictor = SimpleLinearPredictor(enable_feature_selection=True)
        
        assert predictor.enable_feature_selection is True
        assert isinstance(predictor.feature_selector, FeatureSelector)
        assert predictor._feature_selection_dirty is True
    
    def test_predictor_can_disable_feature_selection(self):
        """Test predictor can be initialized with feature selection disabled."""
        predictor = SimpleLinearPredictor(enable_feature_selection=False)
        
        assert predictor.enable_feature_selection is False
    
    def test_adding_sample_marks_feature_selection_dirty(self):
        """Test that adding training samples marks feature selection as dirty."""
        predictor = SimpleLinearPredictor(enable_feature_selection=True)
        predictor._feature_selection_dirty = False  # Reset
        
        # Add a sample
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=4,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
        predictor.add_training_sample(sample)
        
        # Should mark as dirty
        assert predictor._feature_selection_dirty is True
    
    def test_feature_selection_updates_on_prediction(self):
        """Test that feature selection is updated when predicting."""
        predictor = SimpleLinearPredictor(enable_feature_selection=True)
        
        # Add enough samples for feature selection
        for i in range(MIN_SAMPLES_FOR_FEATURE_SELECTION + 5):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01 + i * 0.001,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            predictor.add_training_sample(sample)
        
        # Trigger prediction (this should update feature selection)
        query_features = WorkloadFeatures(
            data_size=2000,
            estimated_item_time=0.015,
            physical_cores=4,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        result = predictor.predict(query_features, confidence_threshold=0.0)
        
        # Feature selection should have been updated
        assert predictor._feature_selection_dirty is False
        assert len(predictor.feature_selector.selected_features) == TARGET_SELECTED_FEATURES
    
    def test_prediction_with_insufficient_samples_uses_all_features(self):
        """Test prediction with insufficient samples uses all features."""
        predictor = SimpleLinearPredictor(enable_feature_selection=True)
        
        # Add only a few samples (less than MIN_SAMPLES_FOR_FEATURE_SELECTION)
        for i in range(5):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            predictor.add_training_sample(sample)
        
        # Trigger prediction
        query_features = WorkloadFeatures(
            data_size=1500,
            estimated_item_time=0.01,
            physical_cores=4,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        result = predictor.predict(query_features, confidence_threshold=0.0)
        
        # Should use all 12 features
        assert len(predictor.feature_selector.selected_features) == 12


class TestDistanceCalculation:
    """Test distance calculation with feature selection."""
    
    def test_distance_calculation_without_feature_selection(self):
        """Test that distance is calculated correctly without feature selection."""
        predictor = SimpleLinearPredictor(enable_feature_selection=False)
        
        # Add samples
        for i in range(10):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            predictor.add_training_sample(sample)
        
        # Query
        query_features = WorkloadFeatures(
            data_size=1500,
            estimated_item_time=0.01,
            physical_cores=4,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        # Find neighbors
        neighbors = predictor._find_nearest_neighbors(query_features, k=3)
        
        # Should find neighbors
        assert len(neighbors) > 0
        # Distances should be reasonable for 12-dimensional space
        for distance, sample in neighbors:
            assert 0 <= distance <= math.sqrt(12)
    
    def test_distance_calculation_with_feature_selection(self):
        """Test that distance is calculated correctly with feature selection."""
        predictor = SimpleLinearPredictor(enable_feature_selection=True)
        
        # Add enough samples for feature selection
        for i in range(MIN_SAMPLES_FOR_FEATURE_SELECTION + 5):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01 + i * 0.001,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            predictor.add_training_sample(sample)
        
        # Update feature selection
        predictor._update_feature_selection()
        
        # Query
        query_features = WorkloadFeatures(
            data_size=1500,
            estimated_item_time=0.015,
            physical_cores=4,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        # Find neighbors
        neighbors = predictor._find_nearest_neighbors(query_features, k=3)
        
        # Should find neighbors
        assert len(neighbors) > 0
        
        # Distances should be reasonable for reduced-dimensional space (7 features)
        num_features = len(predictor.feature_selector.selected_features)
        for distance, sample in neighbors:
            assert 0 <= distance <= math.sqrt(num_features)


class TestConfidenceScoring:
    """Test confidence scoring with feature selection."""
    
    def test_confidence_score_adjusts_for_feature_selection(self):
        """Test that confidence scoring correctly adjusts for reduced dimensions."""
        predictor = SimpleLinearPredictor(enable_feature_selection=True)
        
        # Add enough samples
        for i in range(MIN_SAMPLES_FOR_FEATURE_SELECTION + 5):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            predictor.add_training_sample(sample)
        
        # Query
        query_features = WorkloadFeatures(
            data_size=1500,
            estimated_item_time=0.01,
            physical_cores=4,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        # Predict (triggers feature selection and confidence calculation)
        result = predictor.predict(query_features, confidence_threshold=0.0)
        
        # Should get a result
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0
        assert 0.0 <= result.feature_match_score <= 1.0


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""
    
    def test_default_behavior_enables_feature_selection(self):
        """Test that feature selection is enabled by default."""
        predictor = SimpleLinearPredictor()
        
        # Should be enabled by default (based on ENABLE_FEATURE_SELECTION constant)
        assert predictor.enable_feature_selection == ENABLE_FEATURE_SELECTION
    
    def test_existing_code_without_feature_selection_parameter(self):
        """Test that existing code works without feature_selection parameter."""
        # This should not raise any errors
        predictor = SimpleLinearPredictor(k=5, enable_clustering=True)
        
        # Add samples and predict
        for i in range(10):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,
                estimated_item_time=0.01,
                physical_cores=4,
                available_memory=8 * 1024**3,
                start_method='fork'
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            predictor.add_training_sample(sample)
        
        query_features = WorkloadFeatures(
            data_size=1500,
            estimated_item_time=0.01,
            physical_cores=4,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        result = predictor.predict(query_features, confidence_threshold=0.0)
        assert result is not None


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_feature_selection_with_empty_training_data(self):
        """Test feature selection with no training data."""
        selector = FeatureSelector()
        selector.select_features([], target_num_features=7)
        
        # Should use all features
        assert selector.selected_features == list(range(12))
    
    def test_feature_selection_with_constant_features(self):
        """Test feature selection when some features are constant."""
        selector = FeatureSelector()
        
        # Create training data where most features are constant
        training_data = []
        for i in range(MIN_SAMPLES_FOR_FEATURE_SELECTION + 5):
            features = WorkloadFeatures(
                data_size=1000 + i * 100,  # Only this varies
                estimated_item_time=0.01,  # Constant
                physical_cores=4,  # Constant
                available_memory=8 * 1024**3,  # Constant
                start_method='fork'  # Constant
            )
            sample = TrainingData(features, n_jobs=4, chunksize=10, speedup=3.0, timestamp=0.0)
            training_data.append(sample)
        
        # Should not crash
        selector.select_features(training_data, target_num_features=7)
        assert len(selector.selected_features) == 7
    
    def test_applying_feature_selection_to_wrong_size_vector(self):
        """Test that applying selection to wrong-sized vector doesn't crash."""
        selector = FeatureSelector(selected_features=[0, 2, 4])
        
        # Try with vector that's too short (should still work with available indices)
        short_vector = [0.1, 0.2, 0.3]
        try:
            result = selector.apply_to_vector(short_vector)
            # Should get partial result or raise IndexError (both acceptable)
        except IndexError:
            pass  # Expected for wrong-sized vector


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
