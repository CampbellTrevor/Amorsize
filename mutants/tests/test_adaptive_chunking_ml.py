"""
Tests for adaptive chunking integration with ML prediction system.

This module tests the integration of adaptive chunking parameters into the
ML prediction system (Iteration 119).
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from amorsize.ml_prediction import (
    TrainingData,
    WorkloadFeatures,
    SimpleLinearPredictor,
    PredictionResult,
    update_model_from_execution,
    load_ml_training_data,
    _get_ml_cache_dir,
    MIN_TRAINING_SAMPLES
)


class TestTrainingDataWithAdaptiveChunking:
    """Test TrainingData class with adaptive chunking parameters."""
    
    def test_training_data_with_adaptive_chunking(self):
        """Test creating TrainingData with adaptive chunking parameters."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.5  # Heterogeneous workload
        )
        
        sample = TrainingData(
            features=features,
            n_jobs=4,
            chunksize=25,
            speedup=3.5,
            timestamp=1234567890.0,
            adaptive_chunking_enabled=True,
            adaptation_rate=0.3,
            min_chunksize=1,
            max_chunksize=100
        )
        
        assert sample.adaptive_chunking_enabled is True
        assert sample.adaptation_rate == 0.3
        assert sample.min_chunksize == 1
        assert sample.max_chunksize == 100
    
    def test_training_data_without_adaptive_chunking(self):
        """Test creating TrainingData without adaptive chunking (backward compatibility)."""
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
            chunksize=25,
            speedup=3.5,
            timestamp=1234567890.0
        )
        
        # Fields should be None when not specified
        assert sample.adaptive_chunking_enabled is None
        assert sample.adaptation_rate is None
        assert sample.min_chunksize is None
        assert sample.max_chunksize is None


class TestPredictionResultWithAdaptiveChunking:
    """Test PredictionResult class with adaptive chunking recommendations."""
    
    def test_prediction_result_with_adaptive_chunking(self):
        """Test PredictionResult with adaptive chunking recommendations."""
        result = PredictionResult(
            n_jobs=4,
            chunksize=25,
            confidence=0.85,
            reason="Predicted from similar workloads",
            training_samples=10,
            feature_match_score=0.9,
            adaptive_chunking_enabled=True,
            adaptation_rate=0.4,
            min_chunksize=1,
            max_chunksize=100
        )
        
        assert result.adaptive_chunking_enabled is True
        assert result.adaptation_rate == 0.4
        assert result.min_chunksize == 1
        assert result.max_chunksize == 100
    
    def test_prediction_result_without_adaptive_chunking(self):
        """Test PredictionResult without adaptive chunking (backward compatibility)."""
        result = PredictionResult(
            n_jobs=4,
            chunksize=25,
            confidence=0.85,
            reason="Predicted from similar workloads",
            training_samples=10,
            feature_match_score=0.9
        )
        
        # Fields should be None when not specified
        assert result.adaptive_chunking_enabled is None
        assert result.adaptation_rate is None
        assert result.min_chunksize is None
        assert result.max_chunksize is None


class TestPredictAdaptiveChunking:
    """Test _predict_adaptive_chunking method."""
    
    def test_homogeneous_workload_no_adaptation(self):
        """Test that homogeneous workload (low CV) gets no adaptive chunking."""
        predictor = SimpleLinearPredictor(k=3)
        
        # Add training samples
        for i in range(5):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=16 * 1024**3,
                start_method='fork',
                coefficient_of_variation=0.1  # Low CV = homogeneous
            )
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=25,
                speedup=3.5,
                timestamp=float(i)
            )
            predictor.add_training_sample(sample)
        
        # Test prediction for homogeneous workload
        test_features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.2  # Low CV
        )
        
        result = predictor.predict(test_features, confidence_threshold=0.0)
        
        # Should not recommend adaptive chunking for homogeneous workload
        assert result.adaptive_chunking_enabled is False
        assert result.adaptation_rate is None
    
    def test_heterogeneous_workload_gets_adaptation(self):
        """Test that heterogeneous workload (high CV) gets adaptive chunking."""
        predictor = SimpleLinearPredictor(k=3)
        
        # Add training samples
        for i in range(5):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=16 * 1024**3,
                start_method='fork',
                coefficient_of_variation=0.6  # High CV = heterogeneous
            )
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=25,
                speedup=3.5,
                timestamp=float(i)
            )
            predictor.add_training_sample(sample)
        
        # Test prediction for heterogeneous workload
        test_features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.5  # High CV
        )
        
        result = predictor.predict(test_features, confidence_threshold=0.0)
        
        # Should recommend adaptive chunking for heterogeneous workload
        assert result.adaptive_chunking_enabled is True
        assert result.adaptation_rate is not None
        assert 0.0 <= result.adaptation_rate <= 1.0
        assert result.min_chunksize == 1
    
    def test_learns_adaptation_rate_from_neighbors(self):
        """Test that predictor learns adaptation rate from similar workloads."""
        predictor = SimpleLinearPredictor(k=3)
        
        # Add training samples with adaptive chunking
        for i in range(5):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=16 * 1024**3,
                start_method='fork',
                coefficient_of_variation=0.6
            )
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=25,
                speedup=3.5,
                timestamp=float(i),
                adaptive_chunking_enabled=True,
                adaptation_rate=0.4,  # All neighbors used rate 0.4
                min_chunksize=1,
                max_chunksize=100
            )
            predictor.add_training_sample(sample)
        
        # Test prediction for similar workload
        test_features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.6
        )
        
        result = predictor.predict(test_features, confidence_threshold=0.0)
        
        # Should learn rate close to 0.4 from neighbors
        assert result.adaptive_chunking_enabled is True
        assert result.adaptation_rate is not None
        assert 0.35 <= result.adaptation_rate <= 0.45  # Allow small variation
        assert result.max_chunksize is not None
        assert result.max_chunksize > result.min_chunksize
    
    def test_default_adaptation_rate_by_cv(self):
        """Test that default adaptation rate varies with CV."""
        predictor = SimpleLinearPredictor(k=3)
        
        # Add training samples without adaptive chunking info
        for i in range(5):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=16 * 1024**3,
                start_method='fork',
                coefficient_of_variation=0.5
            )
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=25,
                speedup=3.5,
                timestamp=float(i)
            )
            predictor.add_training_sample(sample)
        
        # Test with moderately heterogeneous workload (CV ~ 0.5)
        test_features_moderate = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.5
        )
        
        result_moderate = predictor.predict(test_features_moderate, confidence_threshold=0.0)
        
        # Test with highly heterogeneous workload (CV > 0.7)
        test_features_high = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.8
        )
        
        result_high = predictor.predict(test_features_high, confidence_threshold=0.0)
        
        # Higher CV should get more aggressive adaptation
        assert result_moderate.adaptive_chunking_enabled is True
        assert result_high.adaptive_chunking_enabled is True
        assert result_high.adaptation_rate > result_moderate.adaptation_rate


class TestUpdateModelWithAdaptiveChunking:
    """Test update_model_from_execution with adaptive chunking parameters."""
    
    @pytest.fixture
    def temp_cache_dir(self, monkeypatch):
        """Create temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Mock the cache directory to use temp directory
        def mock_get_cache_dir():
            return Path(temp_dir)
        
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', mock_get_cache_dir)
        
        yield Path(temp_dir)
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_update_model_with_adaptive_chunking(self, temp_cache_dir):
        """Test saving training data with adaptive chunking parameters."""
        def test_func(x):
            return x * 2
        
        success = update_model_from_execution(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            actual_n_jobs=4,
            actual_chunksize=25,
            actual_speedup=3.5,
            coefficient_of_variation=0.6,
            adaptive_chunking_enabled=True,
            adaptation_rate=0.4,
            min_chunksize=1,
            max_chunksize=100,
            verbose=False
        )
        
        assert success is True
        
        # Verify file was created
        cache_files = list(temp_cache_dir.glob("ml_training_*.json"))
        assert len(cache_files) == 1
        
        # Verify content
        import json
        with open(cache_files[0], 'r') as f:
            data = json.load(f)
        
        assert data['adaptive_chunking_enabled'] is True
        assert data['adaptation_rate'] == 0.4
        assert data['min_chunksize'] == 1
        assert data['max_chunksize'] == 100
    
    def test_update_model_without_adaptive_chunking(self, temp_cache_dir):
        """Test saving training data without adaptive chunking (backward compatibility)."""
        def test_func(x):
            return x * 2
        
        success = update_model_from_execution(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            actual_n_jobs=4,
            actual_chunksize=25,
            actual_speedup=3.5,
            coefficient_of_variation=0.2,
            verbose=False
        )
        
        assert success is True
        
        # Verify file was created
        cache_files = list(temp_cache_dir.glob("ml_training_*.json"))
        assert len(cache_files) == 1
        
        # Verify content - fields should be None
        import json
        with open(cache_files[0], 'r') as f:
            data = json.load(f)
        
        assert data['adaptive_chunking_enabled'] is None
        assert data['adaptation_rate'] is None
        assert data['min_chunksize'] is None
        assert data['max_chunksize'] is None


class TestLoadMLTrainingDataWithAdaptiveChunking:
    """Test load_ml_training_data with adaptive chunking parameters."""
    
    @pytest.fixture
    def temp_cache_dir(self, monkeypatch):
        """Create temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Mock the cache directory to use temp directory
        def mock_get_cache_dir():
            return Path(temp_dir)
        
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', mock_get_cache_dir)
        
        yield Path(temp_dir)
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_load_training_data_with_adaptive_chunking(self, temp_cache_dir):
        """Test loading training data that includes adaptive chunking parameters."""
        def test_func(x):
            return x * 2
        
        # Save training data with adaptive chunking
        update_model_from_execution(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            actual_n_jobs=4,
            actual_chunksize=25,
            actual_speedup=3.5,
            coefficient_of_variation=0.6,
            adaptive_chunking_enabled=True,
            adaptation_rate=0.4,
            min_chunksize=1,
            max_chunksize=100
        )
        
        # Load training data
        training_data = load_ml_training_data(enable_cross_system=False)
        
        assert len(training_data) == 1
        sample = training_data[0]
        
        assert sample.adaptive_chunking_enabled is True
        assert sample.adaptation_rate == 0.4
        assert sample.min_chunksize == 1
        assert sample.max_chunksize == 100
    
    def test_load_old_training_data_without_adaptive_chunking(self, temp_cache_dir):
        """Test loading old training data without adaptive chunking (backward compatibility)."""
        # Create old-format training file manually
        import json
        
        old_data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 16 * 1024**3,
                'start_method': 'fork',
                'coefficient_of_variation': 0.2
            },
            'n_jobs': 4,
            'chunksize': 25,
            'speedup': 3.5,
            'timestamp': 1234567890.0,
            'function_signature': 'test_func'
            # Note: No adaptive chunking fields
        }
        
        cache_file = temp_cache_dir / "ml_training_test_12345.json"
        with open(cache_file, 'w') as f:
            json.dump(old_data, f)
        
        # Load training data
        training_data = load_ml_training_data(enable_cross_system=False)
        
        assert len(training_data) == 1
        sample = training_data[0]
        
        # Old data should load with None values for adaptive chunking
        assert sample.adaptive_chunking_enabled is None
        assert sample.adaptation_rate is None
        assert sample.min_chunksize is None
        assert sample.max_chunksize is None


class TestEndToEndAdaptiveChunkingML:
    """End-to-end integration tests for adaptive chunking with ML."""
    
    @pytest.fixture
    def temp_cache_dir(self, monkeypatch):
        """Create temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        
        def mock_get_cache_dir():
            return Path(temp_dir)
        
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', mock_get_cache_dir)
        
        yield Path(temp_dir)
        
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_workflow_with_adaptive_chunking(self, temp_cache_dir):
        """Test complete workflow: train with adaptive chunking, then predict."""
        def test_func(x):
            return x * 2
        
        # Step 1: Build training data with adaptive chunking
        for i in range(5):
            update_model_from_execution(
                func=test_func,
                data_size=1000 + i * 100,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=20 + i,
                actual_speedup=3.0 + i * 0.1,
                coefficient_of_variation=0.5 + i * 0.05,
                adaptive_chunking_enabled=True,
                adaptation_rate=0.3 + i * 0.02,
                min_chunksize=1,
                max_chunksize=100
            )
        
        # Step 2: Load training data and create predictor
        training_data = load_ml_training_data(enable_cross_system=False)
        assert len(training_data) == 5
        
        predictor = SimpleLinearPredictor(k=3)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        # Step 3: Make prediction for similar heterogeneous workload
        test_features = WorkloadFeatures(
            data_size=1050,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.55  # Heterogeneous
        )
        
        result = predictor.predict(test_features, confidence_threshold=0.0)
        
        # Should get adaptive chunking recommendation
        assert result is not None
        assert result.adaptive_chunking_enabled is True
        assert result.adaptation_rate is not None
        assert 0.2 <= result.adaptation_rate <= 0.5  # Should be in learned range
        assert result.min_chunksize == 1
        assert result.max_chunksize == 100
    
    def test_mixed_training_data_with_and_without_adaptive_chunking(self, temp_cache_dir):
        """Test prediction when training data is mixed (some with, some without adaptive chunking)."""
        def test_func(x):
            return x * 2
        
        # Add samples without adaptive chunking (old data)
        for i in range(3):
            update_model_from_execution(
                func=test_func,
                data_size=1000 + i * 100,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=20 + i,
                actual_speedup=3.0,
                coefficient_of_variation=0.6
            )
        
        # Add samples with adaptive chunking (new data)
        for i in range(2):
            update_model_from_execution(
                func=test_func,
                data_size=1000 + i * 100,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=20 + i,
                actual_speedup=3.5,
                coefficient_of_variation=0.6,
                adaptive_chunking_enabled=True,
                adaptation_rate=0.4,
                min_chunksize=1,
                max_chunksize=100
            )
        
        # Load and predict
        training_data = load_ml_training_data(enable_cross_system=False)
        assert len(training_data) == 5
        
        predictor = SimpleLinearPredictor(k=3)
        for sample in training_data:
            predictor.add_training_sample(sample)
        
        test_features = WorkloadFeatures(
            data_size=1050,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=16 * 1024**3,
            start_method='fork',
            coefficient_of_variation=0.6
        )
        
        result = predictor.predict(test_features, confidence_threshold=0.0)
        
        # Should still recommend adaptive chunking for heterogeneous workload
        assert result.adaptive_chunking_enabled is True
        # Should learn from the 2 samples that had it, or use defaults
        assert result.adaptation_rate is not None
