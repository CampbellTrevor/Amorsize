"""
Tests for online learning functionality in streaming optimization.

Tests cover:
- update_model_from_streaming_execution() function
- Integration with optimize_streaming() results
- Streaming-specific parameters (buffer_size, use_ordered)
- Training data persistence and loading
- Model improvement over time for streaming workloads
"""

import json
import time
from pathlib import Path

import pytest

from amorsize import (
    optimize_streaming,
    update_model_from_streaming_execution,
    predict_streaming_parameters,
    StreamingOptimizationResult
)
from amorsize.ml_prediction import (
    load_ml_training_data,
    _get_ml_cache_dir,
    TrainingData
)


# Test functions
def simple_function(x):
    """Simple test function."""
    time.sleep(0.001)  # 1ms per item
    return x ** 2


def cpu_intensive_function(x):
    """CPU-intensive test function."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


def heterogeneous_function(x):
    """Function with variable execution time."""
    if x % 2 == 0:
        time.sleep(0.001)
    else:
        time.sleep(0.005)
    return x * 2


class TestUpdateModelFromStreamingExecution:
    """Tests for update_model_from_streaming_execution function."""
    
    def test_update_basic(self):
        """Test basic streaming model update."""
        result = update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        assert result is True
    
    def test_update_with_enhanced_features(self):
        """Test streaming model update with enhanced features."""
        result = update_model_from_streaming_execution(
            func=simple_function,
            data_size=5000,
            estimated_item_time=0.002,
            actual_n_jobs=8,
            actual_chunksize=200,
            actual_speedup=6.2,
            buffer_size=24,
            use_ordered=False,
            pickle_size=1024,
            coefficient_of_variation=0.3,
            verbose=False
        )
        assert result is True
    
    def test_update_verbose_output(self, capsys):
        """Test verbose output during streaming model update."""
        result = update_model_from_streaming_execution(
            func=simple_function,
            data_size=100,
            estimated_item_time=0.01,
            actual_n_jobs=2,
            actual_chunksize=50,
            actual_speedup=1.8,
            buffer_size=6,
            use_ordered=True,
            verbose=True
        )
        assert result is True
        
        captured = capsys.readouterr()
        assert "Streaming Online Learning" in captured.out
        assert "n_jobs=2" in captured.out
        assert "chunksize=50" in captured.out
        assert "speedup=1.8" in captured.out
        assert "buffer_size=6" in captured.out
        assert "use_ordered=True" in captured.out
    
    def test_update_creates_training_file(self):
        """Test that streaming update creates a training file with streaming prefix."""
        cache_dir = _get_ml_cache_dir()
        
        # Count files before
        files_before = list(cache_dir.glob("ml_training_streaming_*.json"))
        count_before = len(files_before)
        
        # Update model
        result = update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        assert result is True
        
        # Count files after
        files_after = list(cache_dir.glob("ml_training_streaming_*.json"))
        count_after = len(files_after)
        
        # Should have created exactly one new file
        assert count_after == count_before + 1
    
    def test_update_training_file_content(self):
        """Test that streaming training file contains correct data."""
        cache_dir = _get_ml_cache_dir()
        
        # Get files before
        files_before = set(cache_dir.glob("ml_training_streaming_*.json"))
        
        # Update model with specific parameters
        buffer_size = 18
        use_ordered = False
        result = update_model_from_streaming_execution(
            func=cpu_intensive_function,
            data_size=2000,
            estimated_item_time=0.005,
            actual_n_jobs=6,
            actual_chunksize=150,
            actual_speedup=4.8,
            buffer_size=buffer_size,
            use_ordered=use_ordered,
            pickle_size=512,
            coefficient_of_variation=0.25,
            verbose=False
        )
        assert result is True
        
        # Find the new file
        files_after = set(cache_dir.glob("ml_training_streaming_*.json"))
        new_files = files_after - files_before
        assert len(new_files) == 1
        new_file = list(new_files)[0]
        
        # Load and verify content
        with open(new_file, 'r') as f:
            data = json.load(f)
        
        # Check basic structure
        assert 'features' in data
        assert 'n_jobs' in data
        assert 'chunksize' in data
        assert 'speedup' in data
        assert 'timestamp' in data
        
        # Check streaming-specific fields
        assert 'buffer_size' in data
        assert 'use_ordered' in data
        assert 'is_streaming' in data
        
        # Verify values
        assert data['n_jobs'] == 6
        assert data['chunksize'] == 150
        assert data['buffer_size'] == buffer_size
        assert data['use_ordered'] == use_ordered
        assert data['is_streaming'] is True
        assert abs(data['speedup'] - 4.8) < 0.01
        
        # Verify features
        features = data['features']
        assert features['data_size'] == 2000
        assert abs(features['estimated_item_time'] - 0.005) < 0.001
        assert features['pickle_size'] == 512
        assert abs(features['coefficient_of_variation'] - 0.25) < 0.01


class TestLoadMLTrainingDataStreaming:
    """Tests for loading streaming training data."""
    
    def test_load_includes_streaming_parameters(self):
        """Test that loaded data includes streaming parameters."""
        # Create streaming training sample
        update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        
        # Load training data
        training_data = load_ml_training_data()
        
        # Find streaming samples
        streaming_samples = [s for s in training_data if s.is_streaming]
        assert len(streaming_samples) > 0
        
        # Verify streaming parameters are present
        sample = streaming_samples[-1]  # Get most recent
        assert sample.buffer_size is not None
        assert sample.use_ordered is not None
        assert sample.is_streaming is True
    
    def test_load_distinguishes_batch_and_streaming(self):
        """Test that batch and streaming samples are properly distinguished."""
        from amorsize.ml_prediction import update_model_from_execution
        
        # Create batch training sample
        update_model_from_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            verbose=False
        )
        
        # Create streaming training sample
        update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        
        # Load all training data
        training_data = load_ml_training_data()
        
        # Separate batch and streaming
        batch_samples = [s for s in training_data if not s.is_streaming]
        streaming_samples = [s for s in training_data if s.is_streaming]
        
        # Should have both types
        assert len(batch_samples) > 0
        assert len(streaming_samples) > 0
        
        # Batch samples should not have streaming parameters
        for sample in batch_samples:
            # buffer_size and use_ordered may be None for batch samples
            assert sample.is_streaming is False
        
        # Streaming samples should have streaming parameters
        for sample in streaming_samples:
            assert sample.buffer_size is not None
            assert sample.use_ordered is not None
            assert sample.is_streaming is True


class TestStreamingOnlineLearningIntegration:
    """Tests for integration with optimize_streaming()."""
    
    def test_streaming_result_contains_training_data(self):
        """Test that StreamingOptimizationResult contains training data."""
        result = optimize_streaming(
            simple_function,
            list(range(100)),
            sample_size=5,
            verbose=False
        )
        
        # Check that result has training data fields
        assert isinstance(result, StreamingOptimizationResult)
        assert hasattr(result, 'estimated_item_time')
        assert hasattr(result, 'pickle_size')
        assert hasattr(result, 'coefficient_of_variation')
        
        # These should be populated when dry-run is performed
        if result.estimated_item_time is not None:
            assert result.estimated_item_time > 0
    
    def test_manual_online_learning_from_result(self):
        """Test manually updating model from streaming result."""
        # Get optimization result
        result = optimize_streaming(
            simple_function,
            list(range(100)),
            sample_size=5,
            verbose=False
        )
        
        # Use result to update model (simulating after actual execution)
        if result.estimated_item_time is not None:
            success = update_model_from_streaming_execution(
                func=simple_function,
                data_size=100,
                estimated_item_time=result.estimated_item_time,
                actual_n_jobs=result.n_jobs,
                actual_chunksize=result.chunksize,
                actual_speedup=result.estimated_speedup,
                buffer_size=result.buffer_size,
                use_ordered=result.use_ordered,
                pickle_size=result.pickle_size,
                coefficient_of_variation=result.coefficient_of_variation,
                verbose=False
            )
            assert success is True


class TestStreamingOnlineLearningImprovesModel:
    """Tests that streaming online learning improves predictions over time."""
    
    def test_streaming_training_data_accumulates(self):
        """Test that streaming training data accumulates over multiple updates."""
        # Clear any existing streaming data
        cache_dir = _get_ml_cache_dir()
        initial_count = len(list(cache_dir.glob("ml_training_streaming_*.json")))
        
        # Add multiple streaming training samples
        num_samples = 5
        for i in range(num_samples):
            update_model_from_streaming_execution(
                func=simple_function,
                data_size=1000 + i * 100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=100 + i * 10,
                actual_speedup=3.0 + i * 0.2,
                buffer_size=12 + i * 3,
                use_ordered=(i % 2 == 0),
                verbose=False
            )
        
        # Verify files were created
        final_count = len(list(cache_dir.glob("ml_training_streaming_*.json")))
        assert final_count >= initial_count + num_samples
    
    def test_streaming_samples_have_different_parameters(self):
        """Test that streaming samples capture parameter variations."""
        # Create diverse streaming samples
        update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        
        update_model_from_streaming_execution(
            func=simple_function,
            data_size=5000,
            estimated_item_time=0.002,
            actual_n_jobs=8,
            actual_chunksize=200,
            actual_speedup=6.8,
            buffer_size=24,
            use_ordered=False,
            verbose=False
        )
        
        # Load and verify diversity
        training_data = load_ml_training_data()
        streaming_samples = [s for s in training_data if s.is_streaming]
        
        if len(streaming_samples) >= 2:
            # Check that samples have different parameters
            s1, s2 = streaming_samples[-2:]  # Get last two
            
            # Should have different values
            different_params = (
                s1.buffer_size != s2.buffer_size or
                s1.use_ordered != s2.use_ordered or
                s1.n_jobs != s2.n_jobs or
                s1.chunksize != s2.chunksize
            )
            assert different_params


class TestStreamingOnlineLearningEdgeCases:
    """Tests for edge cases in streaming online learning."""
    
    def test_update_with_small_buffer(self):
        """Test update with minimum buffer size."""
        result = update_model_from_streaming_execution(
            func=simple_function,
            data_size=100,
            estimated_item_time=0.01,
            actual_n_jobs=2,
            actual_chunksize=10,
            actual_speedup=1.5,
            buffer_size=1,  # Minimum buffer
            use_ordered=True,
            verbose=False
        )
        assert result is True
    
    def test_update_with_large_buffer(self):
        """Test update with large buffer size."""
        result = update_model_from_streaming_execution(
            func=simple_function,
            data_size=10000,
            estimated_item_time=0.001,
            actual_n_jobs=16,
            actual_chunksize=500,
            actual_speedup=12.0,
            buffer_size=1000,  # Large buffer
            use_ordered=False,
            verbose=False
        )
        assert result is True
    
    def test_update_ordered_vs_unordered(self):
        """Test that both ordering modes are captured correctly."""
        # Ordered
        result1 = update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        assert result1 is True
        
        # Unordered
        result2 = update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.7,  # Slightly better for unordered
            buffer_size=12,
            use_ordered=False,
            verbose=False
        )
        assert result2 is True


class TestStreamingOnlineLearningCachePersistence:
    """Tests for cache persistence and file handling."""
    
    def test_streaming_training_data_persists_across_sessions(self):
        """Test that streaming training data persists across sessions."""
        # Add streaming training data
        update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        
        # Load in "new session" (just reload)
        training_data = load_ml_training_data()
        streaming_samples = [s for s in training_data if s.is_streaming]
        
        # Should have persisted
        assert len(streaming_samples) > 0
    
    def test_atomic_file_writes(self):
        """Test that streaming training files are written atomically."""
        cache_dir = _get_ml_cache_dir()
        
        # Update model
        result = update_model_from_streaming_execution(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=100,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            verbose=False
        )
        assert result is True
        
        # Should have no .tmp files left over
        tmp_files = list(cache_dir.glob("ml_training_streaming_*.tmp"))
        assert len(tmp_files) == 0


class TestStreamingPredictionWithOnlineLearning:
    """Tests that predictions improve with streaming online learning."""
    
    def test_prediction_uses_streaming_training_data(self):
        """Test that predictions can use streaming training data."""
        # Create streaming training samples
        for i in range(5):
            update_model_from_streaming_execution(
                func=simple_function,
                data_size=1000 + i * 100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=100,
                actual_speedup=3.2 + i * 0.1,
                buffer_size=12,
                use_ordered=True,
                verbose=False
            )
        
        # Try to predict (should work with sufficient training data)
        result = predict_streaming_parameters(
            func=simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.5,  # Lower threshold for testing
            verbose=False
        )
        
        # With training data, should get a prediction
        # (May be None if confidence too low, but at least shouldn't crash)
        if result is not None:
            assert result.n_jobs > 0
            assert result.chunksize > 0
            assert result.buffer_size > 0
            assert isinstance(result.use_ordered, bool)
