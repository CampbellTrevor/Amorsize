"""
Tests for online learning functionality in ML prediction module.

Tests cover:
- update_model_from_execution() function
- load_ml_training_data() function
- Integration with execute() function
- Training data persistence
- Model improvement over time
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from amorsize.ml_prediction import (
    update_model_from_execution,
    load_ml_training_data,
    _get_ml_cache_dir,
    WorkloadFeatures,
    TrainingData
)
from amorsize.executor import execute


# Test functions
def simple_function(x):
    """Simple test function."""
    return x ** 2


def cpu_intensive_function(x):
    """CPU-intensive test function."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


class TestUpdateModelFromExecution:
    """Tests for update_model_from_execution function."""
    
    def test_update_basic(self):
        """Test basic model update."""
        result = update_model_from_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            verbose=False
        )
        assert result is True
    
    def test_update_with_enhanced_features(self):
        """Test model update with enhanced features."""
        result = update_model_from_execution(
            func=simple_function,
            data_size=5000,
            estimated_item_time=0.002,
            actual_n_jobs=8,
            actual_chunksize=200,
            actual_speedup=6.2,
            pickle_size=1024,
            coefficient_of_variation=0.3,
            verbose=False
        )
        assert result is True
    
    def test_update_verbose_output(self, capsys):
        """Test verbose output during model update."""
        result = update_model_from_execution(
            func=simple_function,
            data_size=100,
            estimated_item_time=0.01,
            actual_n_jobs=2,
            actual_chunksize=50,
            actual_speedup=1.8,
            verbose=True
        )
        assert result is True
        
        captured = capsys.readouterr()
        assert "Online Learning" in captured.out
        assert "n_jobs=2" in captured.out
        assert "chunksize=50" in captured.out
        assert "speedup=1.8" in captured.out
    
    def test_update_creates_training_file(self):
        """Test that update creates a training file."""
        cache_dir = _get_ml_cache_dir()
        
        # Count files before
        files_before = list(cache_dir.glob("ml_training_*.json"))
        
        # Update model
        update_model_from_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.0
        )
        
        # Count files after
        files_after = list(cache_dir.glob("ml_training_*.json"))
        
        # Should have one more file
        assert len(files_after) == len(files_before) + 1
    
    def test_update_training_file_content(self):
        """Test content of created training file."""
        cache_dir = _get_ml_cache_dir()
        
        # Update model
        update_model_from_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            pickle_size=512,
            coefficient_of_variation=0.2
        )
        
        # Find the most recent training file
        training_files = sorted(cache_dir.glob("ml_training_*.json"))
        assert len(training_files) > 0
        
        latest_file = training_files[-1]
        
        # Load and verify content
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        assert data['n_jobs'] == 4
        assert data['chunksize'] == 100
        assert abs(data['speedup'] - 3.5) < 0.01
        assert data['features']['data_size'] == 1000
        assert data['features']['pickle_size'] == 512
        assert abs(data['features']['coefficient_of_variation'] - 0.2) < 0.01


class TestLoadMLTrainingData:
    """Tests for load_ml_training_data function."""
    
    def test_load_empty(self):
        """Test loading when no training data exists."""
        # Clear cache first
        cache_dir = _get_ml_cache_dir()
        for f in cache_dir.glob("ml_training_*.json"):
            f.unlink()
        
        data = load_ml_training_data()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_load_after_update(self):
        """Test loading data after update."""
        # Clear cache first
        cache_dir = _get_ml_cache_dir()
        for f in cache_dir.glob("ml_training_*.json"):
            f.unlink()
        
        # Add some training samples
        update_model_from_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.0
        )
        
        update_model_from_execution(
            func=cpu_intensive_function,
            data_size=2000,
            estimated_item_time=0.002,
            actual_n_jobs=8,
            actual_chunksize=200,
            actual_speedup=5.5
        )
        
        # Load training data
        data = load_ml_training_data()
        
        assert len(data) >= 2
        assert all(isinstance(sample, TrainingData) for sample in data)
    
    def test_load_validates_data(self):
        """Test that corrupted files are skipped."""
        cache_dir = _get_ml_cache_dir()
        
        # Create a corrupted file
        corrupted_file = cache_dir / "ml_training_corrupted_123.json"
        with open(corrupted_file, 'w') as f:
            f.write("invalid json {{{")
        
        # Should not raise an error
        data = load_ml_training_data()
        assert isinstance(data, list)
        
        # Clean up
        corrupted_file.unlink()


class TestOnlineLearningIntegration:
    """Tests for online learning integration with execute()."""
    
    def test_execute_without_online_learning(self):
        """Test execute without online learning enabled."""
        data = range(10)
        results = execute(
            simple_function,
            data,
            verbose=False,
            enable_online_learning=False
        )
        assert len(results) == 10
        assert results[0] == 0
        assert results[5] == 25
    
    def test_execute_with_online_learning(self):
        """Test execute with online learning enabled."""
        cache_dir = _get_ml_cache_dir()
        files_before = list(cache_dir.glob("ml_training_*.json"))
        
        data = range(10)
        results = execute(
            simple_function,
            data,
            verbose=False,
            enable_online_learning=True
        )
        
        assert len(results) == 10
        
        # Check that a training file was created
        files_after = list(cache_dir.glob("ml_training_*.json"))
        assert len(files_after) > len(files_before)
    
    def test_execute_with_online_learning_verbose(self, capsys):
        """Test execute with online learning and verbose output."""
        data = range(10)
        results = execute(
            simple_function,
            data,
            verbose=True,
            enable_online_learning=True
        )
        
        assert len(results) == 10
        
        captured = capsys.readouterr()
        # Should show online learning message
        assert "ML model updated" in captured.out or "Online Learning" in captured.out
    
    def test_execute_with_return_optimization_result(self):
        """Test execute with online learning and return_optimization_result."""
        data = range(10)
        results, opt_result = execute(
            simple_function,
            data,
            verbose=False,
            enable_online_learning=True,
            return_optimization_result=True
        )
        
        assert len(results) == 10
        assert opt_result is not None
        assert hasattr(opt_result, 'n_jobs')
        assert hasattr(opt_result, 'chunksize')


class TestOnlineLearningImprovesModel:
    """Tests that online learning actually improves the model over time."""
    
    def test_training_data_accumulates(self):
        """Test that training data accumulates with multiple executions."""
        cache_dir = _get_ml_cache_dir()
        
        # Clear cache
        for f in cache_dir.glob("ml_training_*.json"):
            f.unlink()
        
        # Record initial count
        initial_count = len(load_ml_training_data())
        
        # Execute multiple times with online learning
        for i in range(3):
            data = range(100 * (i + 1))
            execute(
                cpu_intensive_function,
                data,
                verbose=False,
                enable_online_learning=True
            )
        
        # Check that we have more training samples than before
        training_data = load_ml_training_data()
        # Should have added at least 1 sample (may not be 3 due to caching)
        assert len(training_data) > initial_count
    
    def test_training_samples_have_different_features(self):
        """Test that different executions produce different training samples."""
        cache_dir = _get_ml_cache_dir()
        
        # Clear cache
        for f in cache_dir.glob("ml_training_*.json"):
            f.unlink()
        
        # Execute with different data sizes
        for size in [100, 500, 1000]:
            data = range(size)
            execute(
                simple_function,
                data,
                verbose=False,
                enable_online_learning=True
            )
        
        # Load and verify different features
        training_data = load_ml_training_data()
        
        # Check that we have samples with different data sizes
        data_sizes = [sample.features.data_size for sample in training_data]
        unique_sizes = set(data_sizes)
        
        # Should have at least 2 different sizes (may have more from previous tests)
        assert len(unique_sizes) >= 2


class TestOnlineLearningEdgeCases:
    """Tests for edge cases in online learning."""
    
    def test_update_with_zero_speedup(self):
        """Test update with zero speedup (degenerate case)."""
        result = update_model_from_execution(
            func=simple_function,
            data_size=100,
            estimated_item_time=0.01,
            actual_n_jobs=1,
            actual_chunksize=10,
            actual_speedup=0.0  # Zero speedup
        )
        assert result is True
    
    def test_update_with_single_worker(self):
        """Test update with single worker (serial execution)."""
        result = update_model_from_execution(
            func=simple_function,
            data_size=10,
            estimated_item_time=0.1,
            actual_n_jobs=1,
            actual_chunksize=1,
            actual_speedup=1.0
        )
        assert result is True
    
    def test_update_with_large_speedup(self):
        """Test update with very large speedup."""
        result = update_model_from_execution(
            func=simple_function,
            data_size=10000,
            estimated_item_time=0.001,
            actual_n_jobs=16,
            actual_chunksize=500,
            actual_speedup=15.9  # Near-linear speedup
        )
        assert result is True


class TestOnlineLearningCachePersistence:
    """Tests for cache persistence of online learning data."""
    
    def test_training_data_persists_across_sessions(self):
        """Test that training data persists after loading."""
        # Add training sample
        update_model_from_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5
        )
        
        # Load in "new session"
        data1 = load_ml_training_data()
        initial_count = len(data1)
        
        # Add more training
        update_model_from_execution(
            func=cpu_intensive_function,
            data_size=2000,
            estimated_item_time=0.002,
            actual_n_jobs=8,
            actual_chunksize=200,
            actual_speedup=6.0
        )
        
        # Load again
        data2 = load_ml_training_data()
        
        # Should have more samples
        assert len(data2) > initial_count
    
    def test_atomic_file_writes(self):
        """Test that file writes are atomic (no partial writes)."""
        cache_dir = _get_ml_cache_dir()
        
        # Update model
        update_model_from_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5
        )
        
        # Check that there are no .tmp files left behind
        tmp_files = list(cache_dir.glob("ml_training_*.tmp"))
        assert len(tmp_files) == 0
        
        # Check that all .json files are valid
        json_files = list(cache_dir.glob("ml_training_*.json"))
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)  # Should not raise
                assert 'n_jobs' in data
                assert 'chunksize' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
