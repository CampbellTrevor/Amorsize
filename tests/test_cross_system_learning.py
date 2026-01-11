"""
Tests for cross-system learning (Iteration 117).

These tests verify that the ML prediction system can leverage training data
from similar hardware configurations.
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from amorsize.ml_prediction import (
    SystemFingerprint,
    TrainingData,
    WorkloadFeatures,
    load_ml_training_data,
    update_model_from_execution,
    _get_current_system_fingerprint,
    _save_system_fingerprint,
    _load_system_fingerprint,
    MIN_SYSTEM_SIMILARITY,
    CROSS_SYSTEM_WEIGHT,
    _get_ml_cache_dir
)


class TestSystemFingerprint:
    """Test SystemFingerprint class functionality."""
    
    def test_create_fingerprint(self):
        """Test creating a system fingerprint."""
        fp = SystemFingerprint(
            physical_cores=8,
            l3_cache_mb=16.0,
            numa_nodes=1,
            memory_bandwidth_gb_s=42.0,
            start_method='fork'
        )
        
        assert fp.physical_cores == 8
        assert fp.l3_cache_mb == 16.0
        assert fp.numa_nodes == 1
        assert fp.memory_bandwidth_gb_s == 42.0
        assert fp.start_method == 'fork'
        assert len(fp.system_id) == 16  # SHA256 hash truncated to 16 chars
    
    def test_fingerprint_system_id_consistency(self):
        """Test that identical systems get same ID."""
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        fp2 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        
        assert fp1.system_id == fp2.system_id
    
    def test_fingerprint_system_id_difference(self):
        """Test that different systems get different IDs."""
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        fp2 = SystemFingerprint(16, 32.0, 2, 84.0, 'spawn')
        
        assert fp1.system_id != fp2.system_id
    
    def test_identical_systems_similarity(self):
        """Test that identical systems have similarity = 1.0."""
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        fp2 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        
        similarity = fp1.similarity(fp2)
        assert similarity == pytest.approx(1.0, abs=0.01)
    
    def test_very_similar_systems(self):
        """Test that very similar systems have high similarity."""
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        fp2 = SystemFingerprint(8, 16.0, 1, 43.0, 'fork')  # Slightly different bandwidth
        
        similarity = fp1.similarity(fp2)
        assert similarity > 0.95  # Should be very similar
    
    def test_different_core_counts_lower_similarity(self):
        """Test that different core counts reduce similarity significantly."""
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        fp2 = SystemFingerprint(32, 16.0, 1, 42.0, 'fork')  # 4x more cores
        
        similarity = fp1.similarity(fp2)
        assert similarity < 0.9  # Should be noticeably different (adjusted from 0.8)
    
    def test_completely_different_systems(self):
        """Test that very different systems have low similarity."""
        fp1 = SystemFingerprint(4, 4.0, 1, 25.0, 'spawn')   # Small laptop
        fp2 = SystemFingerprint(64, 128.0, 4, 200.0, 'fork')  # Large server
        
        similarity = fp1.similarity(fp2)
        assert similarity < 0.5  # Should be quite different
    
    def test_fingerprint_serialization(self):
        """Test converting fingerprint to/from dict."""
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        
        # Serialize
        data = fp1.to_dict()
        assert data['physical_cores'] == 8
        assert data['l3_cache_mb'] == 16.0
        assert data['system_id'] == fp1.system_id
        
        # Deserialize
        fp2 = SystemFingerprint.from_dict(data)
        assert fp2.physical_cores == fp1.physical_cores
        assert fp2.l3_cache_mb == fp1.l3_cache_mb
        assert fp2.system_id == fp1.system_id
    
    def test_fingerprint_repr(self):
        """Test fingerprint string representation."""
        fp = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        repr_str = repr(fp)
        
        assert 'cores=8' in repr_str
        assert 'cache=16.0MB' in repr_str
        assert 'numa=1' in repr_str
        assert 'fork' in repr_str


class TestSystemFingerprintPersistence:
    """Test saving and loading system fingerprints."""
    
    def test_save_and_load_fingerprint(self, tmp_path, monkeypatch):
        """Test saving and loading a system fingerprint."""
        # Use temporary directory for cache
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        
        # Save
        success = _save_system_fingerprint(fp1)
        assert success
        
        # Load
        fp2 = _load_system_fingerprint()
        assert fp2 is not None
        assert fp2.physical_cores == fp1.physical_cores
        assert fp2.system_id == fp1.system_id
    
    def test_load_nonexistent_fingerprint(self, tmp_path, monkeypatch):
        """Test loading when no fingerprint exists."""
        # Use temporary directory for cache
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        fp = _load_system_fingerprint()
        assert fp is None
    
    def test_load_corrupted_fingerprint(self, tmp_path, monkeypatch):
        """Test loading corrupted fingerprint data."""
        # Use temporary directory for cache
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        # Write corrupted JSON
        fp_file = tmp_path / 'system_fingerprint.json'
        with open(fp_file, 'w') as f:
            f.write('{"corrupt": "data"')
        
        fp = _load_system_fingerprint()
        assert fp is None


class TestGetCurrentSystemFingerprint:
    """Test getting current system fingerprint."""
    
    def test_get_current_fingerprint(self):
        """Test getting fingerprint for current system."""
        fp = _get_current_system_fingerprint()
        
        assert fp is not None
        assert fp.physical_cores >= 1
        assert fp.l3_cache_mb > 0
        assert fp.numa_nodes >= 1
        assert fp.memory_bandwidth_gb_s > 0
        assert fp.start_method in ['fork', 'spawn', 'forkserver']
    
    def test_fingerprint_consistency(self):
        """Test that getting fingerprint twice gives same ID."""
        fp1 = _get_current_system_fingerprint()
        fp2 = _get_current_system_fingerprint()
        
        assert fp1.system_id == fp2.system_id


class TestTrainingDataWithFingerprint:
    """Test TrainingData with system fingerprint support."""
    
    def test_training_data_with_fingerprint(self):
        """Test creating training data with fingerprint."""
        fp = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        td = TrainingData(
            features=features,
            n_jobs=4,
            chunksize=100,
            speedup=3.5,
            timestamp=time.time(),
            system_fingerprint=fp,
            weight=0.9
        )
        
        assert td.system_fingerprint == fp
        assert td.weight == 0.9
    
    def test_training_data_default_weight(self):
        """Test that default weight is 1.0."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        td = TrainingData(
            features=features,
            n_jobs=4,
            chunksize=100,
            speedup=3.5,
            timestamp=time.time()
        )
        
        assert td.weight == 1.0


class TestCrossSystemDataLoading:
    """Test loading training data with cross-system support."""
    
    def test_load_with_cross_system_disabled(self, tmp_path, monkeypatch):
        """Test loading data with cross-system learning disabled."""
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        # Create training file with fingerprint
        fp = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        training_file = tmp_path / 'ml_training_test_12345.json'
        data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 8 * 1024**3,
                'start_method': 'fork',
                'pickle_size': 100,
                'coefficient_of_variation': 0.1,
                'function_complexity': 500
            },
            'n_jobs': 4,
            'chunksize': 100,
            'speedup': 3.5,
            'timestamp': time.time(),
            'function_signature': 'test123',
            'system_fingerprint': fp.to_dict()
        }
        
        with open(training_file, 'w') as f:
            json.dump(data, f)
        
        # Load with cross-system disabled
        samples = load_ml_training_data(enable_cross_system=False)
        
        assert len(samples) == 1
        assert samples[0].weight == 1.0  # No weighting applied
    
    def test_load_with_similar_system(self, tmp_path, monkeypatch):
        """Test loading data from similar system."""
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        # Mock current system
        current_fp = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        monkeypatch.setattr('amorsize.ml_prediction._get_current_system_fingerprint', 
                           lambda: current_fp)
        
        # Create training file from slightly different system
        sample_fp = SystemFingerprint(8, 16.0, 1, 43.0, 'fork')  # Similar system
        training_file = tmp_path / 'ml_training_test_12345.json'
        data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 8 * 1024**3,
                'start_method': 'fork',
                'pickle_size': 100,
                'coefficient_of_variation': 0.1,
                'function_complexity': 500
            },
            'n_jobs': 4,
            'chunksize': 100,
            'speedup': 3.5,
            'timestamp': time.time(),
            'function_signature': 'test123',
            'system_fingerprint': sample_fp.to_dict()
        }
        
        with open(training_file, 'w') as f:
            json.dump(data, f)
        
        # Load with cross-system enabled
        samples = load_ml_training_data(enable_cross_system=True)
        
        assert len(samples) == 1
        # Should be included with weight close to CROSS_SYSTEM_WEIGHT (similarity ~1.0)
        assert samples[0].weight > 0.6
    
    def test_filter_dissimilar_system(self, tmp_path, monkeypatch):
        """Test that dissimilar systems are filtered out."""
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        # Mock current system (small laptop)
        current_fp = SystemFingerprint(4, 4.0, 1, 25.0, 'spawn')
        monkeypatch.setattr('amorsize.ml_prediction._get_current_system_fingerprint', 
                           lambda: current_fp)
        
        # Create training file from very different system (large server)
        sample_fp = SystemFingerprint(64, 128.0, 4, 200.0, 'fork')
        training_file = tmp_path / 'ml_training_test_12345.json'
        data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 64,
                'available_memory': 128 * 1024**3,
                'start_method': 'fork',
                'pickle_size': 100,
                'coefficient_of_variation': 0.1,
                'function_complexity': 500
            },
            'n_jobs': 32,
            'chunksize': 100,
            'speedup': 20.0,
            'timestamp': time.time(),
            'function_signature': 'test123',
            'system_fingerprint': sample_fp.to_dict()
        }
        
        with open(training_file, 'w') as f:
            json.dump(data, f)
        
        # Load with default min_similarity (0.8)
        samples = load_ml_training_data(enable_cross_system=True)
        
        # Should be filtered out due to low similarity
        assert len(samples) == 0
    
    def test_load_local_and_cross_system_data(self, tmp_path, monkeypatch):
        """Test loading mix of local and cross-system data."""
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        # Mock current system
        current_fp = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        monkeypatch.setattr('amorsize.ml_prediction._get_current_system_fingerprint', 
                           lambda: current_fp)
        
        # Create local training file
        local_file = tmp_path / 'ml_training_local_12345.json'
        local_data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 8 * 1024**3,
                'start_method': 'fork',
                'pickle_size': 100,
                'coefficient_of_variation': 0.1,
                'function_complexity': 500
            },
            'n_jobs': 4,
            'chunksize': 100,
            'speedup': 3.5,
            'timestamp': time.time(),
            'function_signature': 'test123',
            'system_fingerprint': current_fp.to_dict()
        }
        
        with open(local_file, 'w') as f:
            json.dump(local_data, f)
        
        # Create cross-system training file
        similar_fp = SystemFingerprint(8, 16.0, 1, 43.0, 'fork')
        cross_file = tmp_path / 'ml_training_cross_67890.json'
        cross_data = {
            'features': {
                'data_size': 2000,
                'estimated_item_time': 0.02,
                'physical_cores': 8,
                'available_memory': 8 * 1024**3,
                'start_method': 'fork',
                'pickle_size': 200,
                'coefficient_of_variation': 0.2,
                'function_complexity': 600
            },
            'n_jobs': 6,
            'chunksize': 150,
            'speedup': 4.5,
            'timestamp': time.time(),
            'function_signature': 'test456',
            'system_fingerprint': similar_fp.to_dict()
        }
        
        with open(cross_file, 'w') as f:
            json.dump(cross_data, f)
        
        # Load all data
        samples = load_ml_training_data(enable_cross_system=True)
        
        assert len(samples) == 2
        # Local sample should have weight 1.0
        local_samples = [s for s in samples if s.n_jobs == 4]
        assert len(local_samples) == 1
        assert local_samples[0].weight == 1.0
        
        # Cross-system sample should have weighted
        cross_samples = [s for s in samples if s.n_jobs == 6]
        assert len(cross_samples) == 1
        assert cross_samples[0].weight < 1.0
    
    def test_load_old_data_without_fingerprint(self, tmp_path, monkeypatch):
        """Test loading old training data without fingerprint (backward compatibility)."""
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        # Create old-style training file without fingerprint
        training_file = tmp_path / 'ml_training_old_12345.json'
        data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 8 * 1024**3,
                'start_method': 'fork',
                'pickle_size': 100,
                'coefficient_of_variation': 0.1,
                'function_complexity': 500
            },
            'n_jobs': 4,
            'chunksize': 100,
            'speedup': 3.5,
            'timestamp': time.time(),
            'function_signature': 'test123'
            # No system_fingerprint field
        }
        
        with open(training_file, 'w') as f:
            json.dump(data, f)
        
        # Should load successfully with default weight
        samples = load_ml_training_data(enable_cross_system=True)
        
        assert len(samples) == 1
        assert samples[0].system_fingerprint is None
        assert samples[0].weight == 1.0


class TestUpdateModelWithFingerprint:
    """Test that update_model_from_execution saves fingerprint."""
    
    def test_update_saves_fingerprint(self, tmp_path, monkeypatch):
        """Test that update_model_from_execution saves system fingerprint."""
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        def dummy_func(x):
            return x * 2
        
        # Update model
        success = update_model_from_execution(
            func=dummy_func,
            data_size=1000,
            estimated_item_time=0.01,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5
        )
        
        assert success
        
        # Load and verify fingerprint was saved
        samples = load_ml_training_data(enable_cross_system=False)
        assert len(samples) == 1
        assert samples[0].system_fingerprint is not None
        assert samples[0].system_fingerprint.physical_cores >= 1


class TestCrossSystemWeighting:
    """Test that cross-system weights are applied in predictions."""
    
    def test_weight_affects_prediction(self):
        """Test that sample weights affect predictions."""
        from amorsize.ml_prediction import SimpleLinearPredictor
        
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        # Create predictor with more samples for reliable prediction
        predictor = SimpleLinearPredictor(k=3)
        
        # Add heavily weighted sample
        fp1 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        for i in range(3):
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=100,
                speedup=3.5,
                timestamp=time.time() + i,
                system_fingerprint=fp1,
                weight=1.0  # Full weight (local system)
            )
            predictor.add_training_sample(sample)
        
        # Add lightly weighted sample
        fp2 = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        sample2 = TrainingData(
            features=features,
            n_jobs=8,
            chunksize=50,
            speedup=5.0,
            timestamp=time.time(),
            system_fingerprint=fp2,
            weight=0.3  # Low weight (dissimilar system)
        )
        predictor.add_training_sample(sample2)
        
        # Predict - should be closer to heavily weighted samples
        result = predictor.predict(features, confidence_threshold=0.0)
        
        assert result is not None
        # Should be closer to sample1 (n_jobs=4) than sample2 (n_jobs=8)
        assert result.n_jobs <= 5


class TestCrossSystemVerboseOutput:
    """Test verbose output for cross-system learning."""
    
    def test_verbose_output_reports_cross_system_samples(self, tmp_path, monkeypatch, capsys):
        """Test that verbose mode reports cross-system sample counts."""
        monkeypatch.setattr('amorsize.ml_prediction._get_ml_cache_dir', lambda: tmp_path)
        
        # Mock current system
        current_fp = SystemFingerprint(8, 16.0, 1, 42.0, 'fork')
        monkeypatch.setattr('amorsize.ml_prediction._get_current_system_fingerprint', 
                           lambda: current_fp)
        
        # Create local and cross-system files
        local_file = tmp_path / 'ml_training_local_1.json'
        local_data = {
            'features': {'data_size': 1000, 'estimated_item_time': 0.01, 
                        'physical_cores': 8, 'available_memory': 8*1024**3, 
                        'start_method': 'fork'},
            'n_jobs': 4, 'chunksize': 100, 'speedup': 3.5,
            'timestamp': time.time(), 'function_signature': 'test',
            'system_fingerprint': current_fp.to_dict()
        }
        with open(local_file, 'w') as f:
            json.dump(local_data, f)
        
        similar_fp = SystemFingerprint(8, 16.0, 1, 43.0, 'fork')
        cross_file = tmp_path / 'ml_training_cross_2.json'
        cross_data = {
            'features': {'data_size': 2000, 'estimated_item_time': 0.02, 
                        'physical_cores': 8, 'available_memory': 8*1024**3, 
                        'start_method': 'fork'},
            'n_jobs': 6, 'chunksize': 150, 'speedup': 4.5,
            'timestamp': time.time(), 'function_signature': 'test',
            'system_fingerprint': similar_fp.to_dict()
        }
        with open(cross_file, 'w') as f:
            json.dump(cross_data, f)
        
        # Load with verbose
        samples = load_ml_training_data(enable_cross_system=True, verbose=True)
        
        captured = capsys.readouterr()
        assert '1 local' in captured.out
        assert '1 cross-system' in captured.out


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
