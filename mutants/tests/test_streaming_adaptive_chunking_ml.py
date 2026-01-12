"""
Tests for streaming adaptive chunking ML integration (Iteration 120).

This module tests the integration of adaptive chunking ML predictions with
streaming optimization, enabling ML to learn and predict optimal adaptation
rates for heterogeneous streaming workloads.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path

from amorsize.ml_prediction import (
    StreamingPredictionResult,
    predict_streaming_parameters,
    update_model_from_streaming_execution,
    _get_ml_cache_dir
)


def clear_ml_cache():
    """Helper to clear ML cache."""
    cache_dir = _get_ml_cache_dir()
    for f in cache_dir.glob("ml_training_*.json"):
        f.unlink()
    for f in cache_dir.glob("ml_calibration.json"):
        f.unlink()


class TestStreamingPredictionResultWithAdaptiveChunking:
    """Test StreamingPredictionResult with adaptive chunking parameters."""
    
    def test_streaming_result_with_adaptive_chunking(self):
        """Test creating StreamingPredictionResult with adaptive chunking."""
        result = StreamingPredictionResult(
            n_jobs=4,
            chunksize=10,
            confidence=0.85,
            reason="Test prediction",
            training_samples=5,
            feature_match_score=0.9,
            buffer_size=12,
            use_ordered=False,
            adaptive_chunking_enabled=True,
            adaptation_rate=0.3,
            min_chunksize=5,
            max_chunksize=40
        )
        
        assert result.n_jobs == 4
        assert result.chunksize == 10
        assert result.buffer_size == 12
        assert result.use_ordered is False
        assert result.adaptive_chunking_enabled is True
        assert result.adaptation_rate == 0.3
        assert result.min_chunksize == 5
        assert result.max_chunksize == 40
    
    def test_streaming_result_without_adaptive_chunking(self):
        """Test StreamingPredictionResult without adaptive chunking."""
        result = StreamingPredictionResult(
            n_jobs=2,
            chunksize=5,
            confidence=0.75,
            reason="Test prediction",
            training_samples=3,
            feature_match_score=0.8,
            buffer_size=6,
            use_ordered=True
        )
        
        assert result.adaptive_chunking_enabled is None
        assert result.adaptation_rate is None
        assert result.min_chunksize is None
        assert result.max_chunksize is None
    
    def test_streaming_result_repr_with_adaptive(self):
        """Test __repr__ includes adaptive chunking info."""
        result = StreamingPredictionResult(
            n_jobs=4,
            chunksize=10,
            confidence=0.85,
            reason="Test",
            training_samples=5,
            feature_match_score=0.9,
            buffer_size=12,
            use_ordered=False,
            adaptive_chunking_enabled=True,
            adaptation_rate=0.4
        )
        
        repr_str = repr(result)
        assert "adaptive_rate=0.4" in repr_str or "adaptive_rate=0.40" in repr_str


class TestPredictStreamingParametersWithAdaptiveChunking:
    """Test predict_streaming_parameters with adaptive chunking."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear cache before and after each test."""
        clear_ml_cache()
        yield
        clear_ml_cache()
    
    def test_streaming_prediction_includes_adaptive_chunking(self):
        """Test that streaming predictions include adaptive chunking from base prediction."""
        # Create a simple test function
        def test_func(x):
            return x * 2
        
        # Add training data with adaptive chunking
        from amorsize.ml_prediction import update_model_from_execution
        
        # Add samples with adaptive chunking enabled
        for i in range(5):
            update_model_from_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=10,
                actual_speedup=3.0,
                coefficient_of_variation=0.6,  # Heterogeneous
                adaptive_chunking_enabled=True,
                adaptation_rate=0.35,
                min_chunksize=5,
                max_chunksize=40
            )
        
        # Predict with heterogeneous workload
        result = predict_streaming_parameters(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            confidence_threshold=0.5,
            coefficient_of_variation=0.6
        )
        
        assert result is not None
        assert result.adaptive_chunking_enabled is True
        assert result.adaptation_rate is not None
        assert 0 < result.adaptation_rate <= 1
    
    def test_streaming_prediction_no_adaptive_for_homogeneous(self):
        """Test that homogeneous workloads don't get adaptive chunking."""
        def test_func(x):
            return x * 2
        
        from amorsize.ml_prediction import update_model_from_execution
        
        # Add samples without adaptive chunking (homogeneous)
        for i in range(5):
            update_model_from_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=10,
                actual_speedup=3.5,
                coefficient_of_variation=0.15,  # Homogeneous
                adaptive_chunking_enabled=False
            )
        
        # Predict with homogeneous workload
        result = predict_streaming_parameters(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            confidence_threshold=0.5,
            coefficient_of_variation=0.15
        )
        
        if result:  # May be None if confidence too low
            # Should not recommend adaptive chunking for homogeneous
            assert result.adaptive_chunking_enabled is False or result.adaptive_chunking_enabled is None


class TestUpdateModelFromStreamingExecutionWithAdaptiveChunking:
    """Test update_model_from_streaming_execution with adaptive chunking."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear cache before and after each test."""
        clear_ml_cache()
        yield
        clear_ml_cache()
    
    def test_update_streaming_model_with_adaptive_chunking(self):
        """Test updating model with adaptive chunking parameters."""
        def test_func(x):
            return x * 2
        
        success = update_model_from_streaming_execution(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            actual_n_jobs=4,
            actual_chunksize=10,
            actual_speedup=3.2,
            buffer_size=12,
            use_ordered=False,
            coefficient_of_variation=0.5,
            adaptive_chunking_enabled=True,
            adaptation_rate=0.3,
            min_chunksize=5,
            max_chunksize=40
        )
        
        assert success is True
        
        # Verify training file was created
        cache_dir = _get_ml_cache_dir()
        training_files = list(cache_dir.glob("ml_training_streaming_*.json"))
        assert len(training_files) > 0
        
        # Load and verify content
        import json
        with open(training_files[0], 'r') as f:
            data = json.load(f)
        
        assert data['adaptive_chunking_enabled'] is True
        assert data['adaptation_rate'] == 0.3
        assert data['min_chunksize'] == 5
        assert data['max_chunksize'] == 40
        assert data['is_streaming'] is True
        assert data['buffer_size'] == 12
        assert data['use_ordered'] is False
    
    def test_update_streaming_model_without_adaptive_chunking(self):
        """Test updating model without adaptive chunking."""
        def test_func(x):
            return x * 2
        
        success = update_model_from_streaming_execution(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            actual_n_jobs=4,
            actual_chunksize=10,
            actual_speedup=3.5,
            buffer_size=12,
            use_ordered=True,
            coefficient_of_variation=0.2  # Homogeneous
        )
        
        assert success is True
        
        # Verify training file
        cache_dir = _get_ml_cache_dir()
        training_files = list(cache_dir.glob("ml_training_streaming_*.json"))
        assert len(training_files) > 0
        
        # Load and verify content
        import json
        with open(training_files[0], 'r') as f:
            data = json.load(f)
        
        # Adaptive chunking fields should be None or absent
        assert data.get('adaptive_chunking_enabled') is None
        assert data.get('adaptation_rate') is None


class TestEndToEndStreamingAdaptiveChunkingML:
    """End-to-end tests for streaming adaptive chunking ML."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear cache before and after each test."""
        clear_ml_cache()
        yield
        clear_ml_cache()
    
    def test_end_to_end_heterogeneous_streaming(self):
        """Test complete workflow for heterogeneous streaming workload."""
        def test_func(x):
            return x * 2
        
        from amorsize.ml_prediction import update_model_from_execution
        
        # Step 1: Build training data with adaptive chunking
        for i in range(5):
            update_model_from_streaming_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=10,
                actual_speedup=3.0,
                buffer_size=12,
                use_ordered=False,
                coefficient_of_variation=0.6,  # Heterogeneous
                adaptive_chunking_enabled=True,
                adaptation_rate=0.35,
                min_chunksize=5,
                max_chunksize=40
            )
        
        # Step 2: Predict for similar heterogeneous workload
        result = predict_streaming_parameters(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            confidence_threshold=0.5,
            coefficient_of_variation=0.6
        )
        
        assert result is not None
        assert result.n_jobs > 1
        assert result.chunksize > 0
        assert result.buffer_size > 0
        
        # Should recommend adaptive chunking for heterogeneous workload
        assert result.adaptive_chunking_enabled is True
        assert result.adaptation_rate is not None
        assert 0 < result.adaptation_rate <= 1
    
    def test_end_to_end_homogeneous_streaming(self):
        """Test complete workflow for homogeneous streaming workload."""
        def test_func(x):
            return x * 2
        
        # Step 1: Build training data without adaptive chunking
        for i in range(5):
            update_model_from_streaming_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=10,
                actual_speedup=3.5,
                buffer_size=12,
                use_ordered=True,
                coefficient_of_variation=0.2,  # Homogeneous
                adaptive_chunking_enabled=False
            )
        
        # Step 2: Predict for similar homogeneous workload
        result = predict_streaming_parameters(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            confidence_threshold=0.5,
            coefficient_of_variation=0.2
        )
        
        if result:  # May be None if confidence too low
            # Should not recommend adaptive chunking
            assert result.adaptive_chunking_enabled is False or result.adaptive_chunking_enabled is None
    
    def test_learning_adaptation_rates_over_time(self):
        """Test that ML learns better adaptation rates over time."""
        def test_func(x):
            return x * 2
        
        # Add samples with different adaptation rates
        rates = [0.2, 0.3, 0.35, 0.4, 0.3]
        for rate in rates:
            update_model_from_streaming_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=10,
                actual_speedup=3.0,
                buffer_size=12,
                use_ordered=False,
                coefficient_of_variation=0.6,
                adaptive_chunking_enabled=True,
                adaptation_rate=rate,
                min_chunksize=5,
                max_chunksize=40
            )
        
        # Predict should learn from these samples
        result = predict_streaming_parameters(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            confidence_threshold=0.5,
            coefficient_of_variation=0.6
        )
        
        assert result is not None
        assert result.adaptive_chunking_enabled is True
        # Should learn an adaptation rate close to the average of training samples
        assert 0.2 <= result.adaptation_rate <= 0.4


class TestStreamingAdaptiveChunkingVerboseOutput:
    """Test verbose output for streaming adaptive chunking ML."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear cache before and after each test."""
        clear_ml_cache()
        yield
        clear_ml_cache()
    
    def test_verbose_output_includes_adaptive_info(self, capsys):
        """Test that verbose output includes adaptive chunking info."""
        def test_func(x):
            return x * 2
        
        # Add training data with adaptive chunking
        for i in range(5):
            update_model_from_streaming_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=10,
                actual_speedup=3.0,
                buffer_size=12,
                use_ordered=False,
                coefficient_of_variation=0.6,
                adaptive_chunking_enabled=True,
                adaptation_rate=0.35,
                min_chunksize=5,
                max_chunksize=40,
                verbose=True  # Enable verbose
            )
        
        captured = capsys.readouterr()
        assert "adaptive_chunking" in captured.out.lower() or "Streaming Online Learning" in captured.out
    
    def test_predict_verbose_includes_adaptive_info(self, capsys):
        """Test that prediction verbose output includes adaptive info."""
        def test_func(x):
            return x * 2
        
        # Add training data
        for i in range(5):
            update_model_from_streaming_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=10,
                actual_speedup=3.0,
                buffer_size=12,
                use_ordered=False,
                coefficient_of_variation=0.6,
                adaptive_chunking_enabled=True,
                adaptation_rate=0.35
            )
        
        # Predict with verbose
        result = predict_streaming_parameters(
            func=test_func,
            data_size=1000,
            estimated_item_time=0.01,
            confidence_threshold=0.5,
            coefficient_of_variation=0.6,
            verbose=True
        )
        
        if result and result.adaptive_chunking_enabled:
            captured = capsys.readouterr()
            assert "adaptive_chunking" in captured.out.lower()
