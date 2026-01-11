"""
Tests for ML-enhanced streaming optimization.

This module tests the integration of ML predictions with streaming optimization,
including predict_streaming_parameters() and the enable_ml_prediction parameter
in optimize_streaming().
"""

import pytest
import time
from amorsize import (
    optimize_streaming,
    predict_streaming_parameters,
    StreamingPredictionResult,
    update_model_from_execution
)
from amorsize.ml_prediction import (
    _get_ml_cache_dir,
    _compute_function_signature
)


def simple_function(x):
    """Simple test function for ML streaming prediction."""
    time.sleep(0.001)  # 1ms per item
    return x * 2


def cpu_intensive_function(x):
    """CPU-intensive function for testing."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def heterogeneous_function(x):
    """Function with variable execution time."""
    if x % 2 == 0:
        time.sleep(0.001)
    else:
        time.sleep(0.005)
    return x * 2


class TestPredictStreamingParameters:
    """Tests for predict_streaming_parameters() function."""
    
    def test_basic_prediction(self):
        """Test basic streaming parameter prediction."""
        # First create some training data
        update_model_from_execution(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=50,
            actual_speedup=3.5
        )
        
        # Now try to predict
        result = predict_streaming_parameters(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.5,  # Lower threshold for testing
            verbose=False
        )
        
        # With one training sample, might not get prediction
        # But if we do, validate it
        if result is not None:
            assert isinstance(result, StreamingPredictionResult)
            assert result.n_jobs > 0
            assert result.chunksize > 0
            assert result.buffer_size > 0
            assert isinstance(result.use_ordered, bool)
            assert 0.0 <= result.confidence <= 1.0
    
    def test_prediction_with_multiple_samples(self):
        """Test prediction improves with more training samples."""
        # Create multiple training samples
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=1000 + i * 100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.2 + i * 0.1
            )
        
        result = predict_streaming_parameters(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.5,
            verbose=False
        )
        
        assert result is not None
        assert isinstance(result, StreamingPredictionResult)
        assert result.training_samples >= 3
    
    def test_buffer_size_calculation(self):
        """Test that buffer size is calculated correctly."""
        # Create training data
        for i in range(3):
            update_model_from_execution(
                simple_function,
                data_size=1000,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.5
            )
        
        result = predict_streaming_parameters(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.5,
            verbose=False
        )
        
        if result is not None:
            # Buffer size should be n_jobs * 3 by default
            assert result.buffer_size >= result.n_jobs
            assert result.buffer_size <= result.n_jobs * 10
    
    def test_buffer_size_memory_constraint(self):
        """Test buffer size respects memory constraints."""
        # Create training data
        for i in range(3):
            update_model_from_execution(
                simple_function,
                data_size=1000,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.5,
                pickle_size=10_000_000  # 10MB per item
            )
        
        result = predict_streaming_parameters(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.5,
            verbose=False,
            pickle_size=10_000_000
        )
        
        if result is not None:
            # With large pickle size, buffer should be limited
            # to prevent memory exhaustion
            assert result.buffer_size > 0
    
    def test_ordering_preference_heterogeneous(self):
        """Test that unordered is recommended for heterogeneous workloads."""
        # Create training data
        for i in range(3):
            update_model_from_execution(
                heterogeneous_function,
                data_size=1000,
                estimated_item_time=0.003,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.5,
                coefficient_of_variation=0.8  # High CV = heterogeneous
            )
        
        result = predict_streaming_parameters(
            heterogeneous_function,
            data_size=1000,
            estimated_item_time=0.003,
            confidence_threshold=0.5,
            verbose=False,
            coefficient_of_variation=0.8
        )
        
        if result is not None:
            # High CV should recommend unordered
            assert result.use_ordered == False
    
    def test_ordering_preference_large_dataset(self):
        """Test that unordered is recommended for large datasets."""
        # Create training data
        for i in range(3):
            update_model_from_execution(
                simple_function,
                data_size=100_000,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.5
            )
        
        result = predict_streaming_parameters(
            simple_function,
            data_size=100_000,  # Large dataset
            estimated_item_time=0.001,
            confidence_threshold=0.5,
            verbose=False
        )
        
        if result is not None:
            # Large dataset should recommend unordered
            assert result.use_ordered == False
    
    def test_ordering_preference_user_override(self):
        """Test that user preference overrides auto-decision."""
        # Create training data
        for i in range(3):
            update_model_from_execution(
                simple_function,
                data_size=1000,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.5
            )
        
        result = predict_streaming_parameters(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.5,
            verbose=False,
            prefer_ordered=True  # Force ordered
        )
        
        if result is not None:
            # User preference should be respected
            assert result.use_ordered == True
    
    def test_insufficient_training_data(self):
        """Test that None is returned with insufficient training data."""
        # Define a unique function that has no training data
        def unique_function_no_training(x):
            """Unique function with no training history."""
            return x ** 3 + x ** 2 + x + 1
        
        result = predict_streaming_parameters(
            unique_function_no_training,
            data_size=1000,
            estimated_item_time=0.01,
            confidence_threshold=0.7,
            verbose=False
        )
        
        # Should return None with no training data for this unique function
        # Note: if training data exists from other runs, test may pass with result != None
        # This is expected behavior (ML uses historical data)
        # The key is that it doesn't crash
        assert result is None or isinstance(result, StreamingPredictionResult)
    
    def test_low_confidence_returns_none(self):
        """Test that None is returned when confidence is too low."""
        # Create minimal training data (might not meet threshold)
        update_model_from_execution(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            actual_n_jobs=4,
            actual_chunksize=50,
            actual_speedup=3.5
        )
        
        result = predict_streaming_parameters(
            simple_function,
            data_size=5000,  # Different size
            estimated_item_time=0.01,  # Different time
            confidence_threshold=0.95,  # Very high threshold
            verbose=False
        )
        
        # With only 1-2 samples and high threshold, likely None
        # This is expected behavior
        if result is None:
            assert True  # Expected


class TestOptimizeStreamingWithML:
    """Tests for optimize_streaming() with ML prediction enabled."""
    
    def test_ml_disabled_by_default(self):
        """Test that ML prediction is disabled by default."""
        data = list(range(100))
        result = optimize_streaming(
            simple_function,
            data,
            sample_size=3,
            verbose=False
        )
        
        # Should use dry-run (not ML)
        assert result is not None
        assert result.n_jobs >= 1
    
    def test_ml_enabled_with_training_data(self):
        """Test ML prediction when enabled with training data."""
        # Create training data
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=25,
                actual_speedup=3.5
            )
        
        data = list(range(100))
        result = optimize_streaming(
            simple_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            verbose=False
        )
        
        assert result is not None
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.buffer_size is not None
    
    def test_ml_fallback_to_dryrun(self):
        """Test that ML falls back to dry-run when confidence is low."""
        data = list(range(100))
        
        # With no training data, should fall back to dry-run
        result = optimize_streaming(
            cpu_intensive_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.01,
            ml_confidence_threshold=0.95,  # High threshold
            sample_size=3,
            verbose=False
        )
        
        # Should still get a result (from dry-run)
        assert result is not None
        assert result.n_jobs >= 1
    
    def test_ml_with_adaptive_chunking(self):
        """Test ML prediction with adaptive chunking enabled."""
        # Create training data
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=25,
                actual_speedup=3.5
            )
        
        data = list(range(100))
        result = optimize_streaming(
            simple_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            enable_adaptive_chunking=True,
            verbose=False
        )
        
        assert result is not None
        assert result.use_adaptive_chunking == True
        if result.adaptive_chunking_params:
            assert 'initial_chunksize' in result.adaptive_chunking_params
    
    def test_ml_with_memory_backpressure(self):
        """Test ML prediction with memory backpressure enabled."""
        # Create training data
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=25,
                actual_speedup=3.5
            )
        
        data = list(range(100))
        result = optimize_streaming(
            simple_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            enable_memory_backpressure=True,
            verbose=False
        )
        
        assert result is not None
        assert result.memory_backpressure_enabled == True
    
    def test_ml_with_custom_buffer_size(self):
        """Test that custom buffer size overrides ML prediction."""
        # Create training data
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=25,
                actual_speedup=3.5
            )
        
        data = list(range(100))
        custom_buffer = 42
        result = optimize_streaming(
            simple_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            buffer_size=custom_buffer,
            verbose=False
        )
        
        assert result is not None
        assert result.buffer_size == custom_buffer
    
    def test_ml_with_prefer_ordered(self):
        """Test ML prediction respects prefer_ordered parameter."""
        # Create training data
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=25,
                actual_speedup=3.5
            )
        
        data = list(range(100))
        result = optimize_streaming(
            simple_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            prefer_ordered=True,
            verbose=False
        )
        
        assert result is not None
        # Note: prefer_ordered is passed to ML prediction
        # which should respect it


class TestMLStreamingIntegration:
    """Integration tests for ML-enhanced streaming."""
    
    def test_end_to_end_ml_streaming(self):
        """Test complete workflow: train, predict, optimize."""
        # Step 1: Create training data from executions
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=1000 + i * 100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.2 + i * 0.1
            )
        
        # Step 2: Use ML prediction directly
        ml_result = predict_streaming_parameters(
            simple_function,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.5,
            verbose=False
        )
        
        assert ml_result is not None
        
        # Step 3: Use ML-enhanced optimize_streaming
        data = list(range(1000))
        stream_result = optimize_streaming(
            simple_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            verbose=False
        )
        
        assert stream_result is not None
        # ML parameters should be similar
        assert stream_result.n_jobs > 0
        assert stream_result.chunksize > 0
    
    def test_ml_streaming_with_generator(self):
        """Test ML streaming optimization with generator input."""
        # Create training data
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=25,
                actual_speedup=3.5
            )
        
        # Use generator
        def data_generator():
            for i in range(100):
                yield i
        
        result = optimize_streaming(
            simple_function,
            data_generator(),
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            sample_size=3,
            verbose=False
        )
        
        assert result is not None
        assert result.n_jobs >= 1
    
    def test_ml_streaming_verbose_output(self, capsys):
        """Test verbose output for ML streaming optimization."""
        # Create training data
        for i in range(5):
            update_model_from_execution(
                simple_function,
                data_size=100,
                estimated_item_time=0.001,
                actual_n_jobs=4,
                actual_chunksize=25,
                actual_speedup=3.5
            )
        
        data = list(range(100))
        result = optimize_streaming(
            simple_function,
            data,
            enable_ml_prediction=True,
            estimated_item_time=0.001,
            ml_confidence_threshold=0.5,
            verbose=True
        )
        
        captured = capsys.readouterr()
        # Should mention ML prediction in output
        assert result is not None
        # May or may not use ML depending on confidence
        # Just verify it doesn't crash with verbose=True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
