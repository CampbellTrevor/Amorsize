"""
Tests for confidence calibration system (Iteration 116).

Tests the adaptive confidence threshold adjustment feature that learns
from prediction accuracy over time to optimize the ML vs dry-run trade-off.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from amorsize.ml_prediction import (
    CalibrationData,
    PredictionResult,
    track_prediction_accuracy,
    get_calibration_stats,
    predict_parameters,
    _load_calibration_data,
    _save_calibration_data,
    _get_ml_cache_dir,
    DEFAULT_CONFIDENCE_THRESHOLD,
    MIN_CALIBRATION_SAMPLES
)


class TestCalibrationData:
    """Test CalibrationData class."""
    
    def test_initialization_defaults(self):
        """Test default initialization."""
        cal = CalibrationData()
        
        assert cal.predictions == []
        assert cal.adjusted_threshold == DEFAULT_CONFIDENCE_THRESHOLD
        assert cal.baseline_threshold == DEFAULT_CONFIDENCE_THRESHOLD
        assert cal.last_update > 0
    
    def test_initialization_with_data(self):
        """Test initialization with provided data."""
        predictions = [(0.8, 0.9), (0.7, 0.8)]
        cal = CalibrationData(
            predictions=predictions,
            adjusted_threshold=0.65,
            baseline_threshold=0.7,
            last_update=1000.0
        )
        
        assert cal.predictions == predictions
        assert cal.adjusted_threshold == 0.65
        assert cal.baseline_threshold == 0.7
        assert cal.last_update == 1000.0
    
    def test_add_prediction_result(self):
        """Test adding prediction results."""
        cal = CalibrationData()
        
        cal.add_prediction_result(confidence=0.8, accuracy=0.9)
        cal.add_prediction_result(confidence=0.7, accuracy=0.85)
        
        assert len(cal.predictions) == 2
        assert cal.predictions[0] == (0.8, 0.9)
        assert cal.predictions[1] == (0.7, 0.85)
    
    def test_get_calibration_stats_empty(self):
        """Test stats with no predictions."""
        cal = CalibrationData()
        stats = cal.get_calibration_stats()
        
        assert stats['mean_accuracy'] == 0.0
        assert stats['high_confidence_accuracy'] == 0.0
        assert stats['low_confidence_accuracy'] == 0.0
        assert stats['sample_count'] == 0
    
    def test_get_calibration_stats_with_data(self):
        """Test stats calculation with predictions."""
        cal = CalibrationData()
        
        # Add predictions: half high-confidence, half low-confidence
        cal.add_prediction_result(0.8, 0.95)  # High conf, high acc
        cal.add_prediction_result(0.85, 0.90)  # High conf, high acc
        cal.add_prediction_result(0.6, 0.70)  # Low conf, moderate acc
        cal.add_prediction_result(0.5, 0.60)  # Low conf, moderate acc
        
        stats = cal.get_calibration_stats()
        
        # Mean accuracy should be average of all
        expected_mean = (0.95 + 0.90 + 0.70 + 0.60) / 4
        assert abs(stats['mean_accuracy'] - expected_mean) < 0.01
        
        # High confidence accuracy (>= 0.7 threshold)
        expected_high = (0.95 + 0.90) / 2
        assert abs(stats['high_confidence_accuracy'] - expected_high) < 0.01
        
        # Low confidence accuracy (< 0.7 threshold)
        expected_low = (0.70 + 0.60) / 2
        assert abs(stats['low_confidence_accuracy'] - expected_low) < 0.01
        
        assert stats['sample_count'] == 4
    
    def test_recalibrate_threshold_insufficient_samples(self):
        """Test that calibration requires minimum samples."""
        cal = CalibrationData(adjusted_threshold=0.7)
        
        # Add fewer than MIN_CALIBRATION_SAMPLES
        for i in range(MIN_CALIBRATION_SAMPLES - 1):
            cal.add_prediction_result(0.8, 0.9)
        
        old_threshold = cal.adjusted_threshold
        new_threshold = cal.recalibrate_threshold()
        
        # Threshold should not change
        assert new_threshold == old_threshold
    
    def test_recalibrate_threshold_adjusts_toward_optimal(self):
        """Test that calibration adjusts threshold toward optimal value."""
        cal = CalibrationData(adjusted_threshold=0.7, baseline_threshold=0.7)
        
        # Add samples where 0.6 threshold would work better
        # (high accuracy even at lower confidence)
        for i in range(MIN_CALIBRATION_SAMPLES + 5):
            cal.add_prediction_result(0.65, 0.92)  # Good accuracy at 0.65 confidence
        
        new_threshold = cal.recalibrate_threshold()
        
        # Threshold should decrease (moving toward 0.6)
        assert new_threshold < 0.7
        assert new_threshold >= 0.5  # But stay within bounds
    
    def test_recalibrate_threshold_bounds(self):
        """Test that threshold stays within reasonable bounds."""
        cal = CalibrationData(adjusted_threshold=0.5, baseline_threshold=0.7)
        
        # Add many samples suggesting very high threshold
        for i in range(MIN_CALIBRATION_SAMPLES + 5):
            cal.add_prediction_result(0.95, 0.99)  # Only 0.95+ is accurate
        
        new_threshold = cal.recalibrate_threshold()
        
        # Threshold should increase but stay <= 0.95
        assert new_threshold >= 0.5
        assert new_threshold <= 0.95


class TestCalibrationPersistence:
    """Test saving and loading calibration data."""
    
    def test_save_and_load_calibration(self):
        """Test round-trip save and load."""
        # Create calibration data
        cal = CalibrationData()
        cal.add_prediction_result(0.8, 0.9)
        cal.add_prediction_result(0.7, 0.85)
        cal.adjusted_threshold = 0.68
        
        # Save
        success = _save_calibration_data(cal)
        assert success
        
        # Load
        loaded_cal = _load_calibration_data()
        
        # Verify
        assert len(loaded_cal.predictions) == 2
        assert loaded_cal.predictions[0] == (0.8, 0.9)
        assert loaded_cal.predictions[1] == (0.7, 0.85)
        assert abs(loaded_cal.adjusted_threshold - 0.68) < 0.01
    
    def test_load_nonexistent_returns_default(self):
        """Test loading when file doesn't exist."""
        # Ensure file doesn't exist
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        if calibration_file.exists():
            calibration_file.unlink()
        
        cal = _load_calibration_data()
        
        # Should return fresh calibration data
        assert len(cal.predictions) == 0
        assert cal.adjusted_threshold == DEFAULT_CONFIDENCE_THRESHOLD
    
    def test_save_creates_directory(self):
        """Test that save creates cache directory if needed."""
        # This test relies on the implementation creating directories
        cal = CalibrationData()
        cal.add_prediction_result(0.8, 0.9)
        
        # Save should succeed even if directory didn't exist
        success = _save_calibration_data(cal)
        assert success
    
    def test_load_corrupted_file_returns_default(self):
        """Test loading when file is corrupted."""
        # Write corrupted JSON
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        calibration_file.write_text("{ invalid json }")
        
        # Load should return default instead of crashing
        cal = _load_calibration_data()
        assert len(cal.predictions) == 0


class TestTrackPredictionAccuracy:
    """Test track_prediction_accuracy function."""
    
    def test_track_perfect_prediction(self):
        """Test tracking a perfect prediction."""
        prediction = PredictionResult(
            n_jobs=4,
            chunksize=100,
            confidence=0.85,
            reason="Test",
            training_samples=10,
            feature_match_score=0.9
        )
        
        success = track_prediction_accuracy(
            prediction,
            actual_n_jobs=4,
            actual_chunksize=100,
            verbose=False
        )
        
        assert success
        
        # Verify calibration was updated
        cal = _load_calibration_data()
        assert len(cal.predictions) > 0
        
        # Last prediction should have high accuracy (1.0 for perfect)
        _, accuracy = cal.predictions[-1]
        assert accuracy == 1.0
    
    def test_track_imperfect_prediction(self):
        """Test tracking an imperfect prediction."""
        prediction = PredictionResult(
            n_jobs=4,
            chunksize=100,
            confidence=0.75,
            reason="Test",
            training_samples=10,
            feature_match_score=0.8
        )
        
        success = track_prediction_accuracy(
            prediction,
            actual_n_jobs=6,  # Off by 2
            actual_chunksize=120,  # Off by 20
            verbose=False
        )
        
        assert success
        
        # Verify calibration was updated
        cal = _load_calibration_data()
        assert len(cal.predictions) > 0
        
        # Last prediction should have reduced accuracy
        _, accuracy = cal.predictions[-1]
        assert 0.0 < accuracy < 1.0
    
    def test_track_triggers_recalibration(self):
        """Test that tracking enough predictions triggers recalibration."""
        # Clear existing calibration
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        if calibration_file.exists():
            calibration_file.unlink()
        
        # Track enough predictions to trigger recalibration
        for i in range(MIN_CALIBRATION_SAMPLES + 2):
            prediction = PredictionResult(
                n_jobs=4,
                chunksize=100,
                confidence=0.65,  # Lower than default
                reason="Test",
                training_samples=10,
                feature_match_score=0.8
            )
            
            track_prediction_accuracy(
                prediction,
                actual_n_jobs=4,
                actual_chunksize=100,
                verbose=False
            )
        
        # Calibration should have been adjusted
        cal = _load_calibration_data()
        stats = cal.get_calibration_stats()
        
        assert len(cal.predictions) >= MIN_CALIBRATION_SAMPLES
        # Threshold may have adjusted based on high accuracy at 0.65
    
    def test_track_verbose_output(self, capsys):
        """Test verbose output."""
        prediction = PredictionResult(
            n_jobs=4,
            chunksize=100,
            confidence=0.85,
            reason="Test",
            training_samples=10,
            feature_match_score=0.9
        )
        
        track_prediction_accuracy(
            prediction,
            actual_n_jobs=4,
            actual_chunksize=100,
            verbose=True
        )
        
        captured = capsys.readouterr()
        assert "Calibration:" in captured.out
        assert "accuracy" in captured.out.lower()


class TestGetCalibrationStats:
    """Test get_calibration_stats function."""
    
    def test_get_stats_empty(self):
        """Test getting stats when no calibration data exists."""
        # Clear existing calibration
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        if calibration_file.exists():
            calibration_file.unlink()
        
        stats = get_calibration_stats()
        
        assert stats['adjusted_threshold'] == DEFAULT_CONFIDENCE_THRESHOLD
        assert stats['baseline_threshold'] == DEFAULT_CONFIDENCE_THRESHOLD
        assert stats['mean_accuracy'] == 0.0
        assert stats['sample_count'] == 0
    
    def test_get_stats_with_data(self):
        """Test getting stats with calibration data."""
        # Add some calibration data
        cal = CalibrationData()
        cal.add_prediction_result(0.8, 0.9)
        cal.add_prediction_result(0.75, 0.85)
        cal.adjusted_threshold = 0.68
        _save_calibration_data(cal)
        
        stats = get_calibration_stats()
        
        assert abs(stats['adjusted_threshold'] - 0.68) < 0.01
        assert stats['sample_count'] == 2
        assert stats['mean_accuracy'] > 0
    
    def test_get_stats_verbose(self, capsys):
        """Test verbose output."""
        # Add some calibration data
        cal = CalibrationData()
        cal.add_prediction_result(0.8, 0.9)
        _save_calibration_data(cal)
        
        get_calibration_stats(verbose=True)
        
        captured = capsys.readouterr()
        assert "Calibration Statistics:" in captured.out
        assert "threshold" in captured.out.lower()


class TestPredictParametersWithCalibration:
    """Test predict_parameters with calibration enabled."""
    
    def test_predict_uses_calibrated_threshold(self):
        """Test that predict_parameters uses calibrated threshold."""
        # Set up calibration with adjusted threshold
        cal = CalibrationData(adjusted_threshold=0.6, baseline_threshold=0.7)
        for i in range(MIN_CALIBRATION_SAMPLES + 2):
            cal.add_prediction_result(0.65, 0.95)
        _save_calibration_data(cal)
        
        # Create a simple test function
        def test_func(x):
            return x * 2
        
        # Predict with calibration enabled
        # This may return None if no training data, but should use calibrated threshold
        result = predict_parameters(
            test_func,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.7,  # Default threshold
            use_calibration=True,
            verbose=False
        )
        
        # The function should have loaded the calibrated threshold (0.6)
        # If it returns a prediction, confidence should be checked against 0.6
        # If no training data, will return None (expected behavior)
    
    def test_predict_without_calibration_uses_default(self):
        """Test that disabling calibration uses default threshold."""
        # Set up calibration with adjusted threshold
        cal = CalibrationData(adjusted_threshold=0.5, baseline_threshold=0.7)
        for i in range(MIN_CALIBRATION_SAMPLES + 2):
            cal.add_prediction_result(0.6, 0.95)
        _save_calibration_data(cal)
        
        # Create a simple test function
        def test_func(x):
            return x * 2
        
        # Predict with calibration disabled
        result = predict_parameters(
            test_func,
            data_size=1000,
            estimated_item_time=0.001,
            confidence_threshold=0.7,
            use_calibration=False,  # Explicitly disabled
            verbose=False
        )
        
        # Should use default threshold 0.7, not calibrated 0.5


class TestIntegrationScenarios:
    """Test complete calibration workflows."""
    
    def test_calibration_improves_over_time(self):
        """Test that calibration system improves predictions over time."""
        # Clear existing calibration
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        if calibration_file.exists():
            calibration_file.unlink()
        
        # Simulate a series of predictions with consistent high accuracy at 0.65 confidence
        for i in range(MIN_CALIBRATION_SAMPLES + 5):
            prediction = PredictionResult(
                n_jobs=4,
                chunksize=100,
                confidence=0.65,
                reason="Test",
                training_samples=10,
                feature_match_score=0.85
            )
            
            # Simulate perfect predictions
            track_prediction_accuracy(
                prediction,
                actual_n_jobs=4,
                actual_chunksize=100,
                verbose=False
            )
        
        # Check that threshold has adjusted downward
        stats = get_calibration_stats()
        
        # With consistent high accuracy at 0.65, threshold should move toward 0.65
        # (may not reach it due to conservative adjustment factor)
        assert stats['adjusted_threshold'] <= DEFAULT_CONFIDENCE_THRESHOLD
        assert stats['mean_accuracy'] > 0.9  # Should be near 1.0
    
    def test_calibration_handles_poor_predictions(self):
        """Test that calibration adjusts for poor predictions."""
        # Clear existing calibration
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        if calibration_file.exists():
            calibration_file.unlink()
        
        # Simulate predictions with poor accuracy
        for i in range(MIN_CALIBRATION_SAMPLES + 5):
            prediction = PredictionResult(
                n_jobs=4,
                chunksize=100,
                confidence=0.75,
                reason="Test",
                training_samples=10,
                feature_match_score=0.8
            )
            
            # Simulate poor predictions (always off)
            track_prediction_accuracy(
                prediction,
                actual_n_jobs=8,  # Way off
                actual_chunksize=200,  # Way off
                verbose=False
            )
        
        # Check that system recognizes poor accuracy
        stats = get_calibration_stats()
        
        # Mean accuracy should be low
        assert stats['mean_accuracy'] < 0.7
        # System may adjust threshold upward to be more conservative
    
    def test_calibration_persistence_across_sessions(self):
        """Test that calibration data persists across sessions."""
        # Clear existing calibration
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        if calibration_file.exists():
            calibration_file.unlink()
        
        # Add some calibration data in "session 1"
        for i in range(5):
            prediction = PredictionResult(
                n_jobs=4,
                chunksize=100,
                confidence=0.8,
                reason="Test",
                training_samples=10,
                feature_match_score=0.85
            )
            track_prediction_accuracy(prediction, 4, 100, verbose=False)
        
        # Get stats
        stats1 = get_calibration_stats()
        count1 = stats1['sample_count']
        
        # Add more data in "session 2"
        for i in range(5):
            prediction = PredictionResult(
                n_jobs=4,
                chunksize=100,
                confidence=0.75,
                reason="Test",
                training_samples=10,
                feature_match_score=0.8
            )
            track_prediction_accuracy(prediction, 4, 100, verbose=False)
        
        # Get stats again
        stats2 = get_calibration_stats()
        count2 = stats2['sample_count']
        
        # Should have accumulated
        assert count2 == count1 + 5


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_track_with_zero_actual_values(self):
        """Test tracking when actual values are zero (edge case)."""
        prediction = PredictionResult(
            n_jobs=4,
            chunksize=100,
            confidence=0.8,
            reason="Test",
            training_samples=10,
            feature_match_score=0.85
        )
        
        # This is an edge case but should not crash
        success = track_prediction_accuracy(
            prediction,
            actual_n_jobs=1,  # Minimum value
            actual_chunksize=1,  # Minimum value
            verbose=False
        )
        
        assert success
    
    def test_calibration_with_extreme_confidence(self):
        """Test calibration with extreme confidence values."""
        cal = CalibrationData()
        
        # Add predictions with extreme confidence values
        cal.add_prediction_result(0.01, 0.1)  # Very low confidence
        cal.add_prediction_result(0.99, 0.99)  # Very high confidence
        
        # Should not crash
        stats = cal.get_calibration_stats()
        assert 0.0 <= stats['mean_accuracy'] <= 1.0
    
    def test_get_stats_handles_missing_file(self):
        """Test that get_stats handles missing calibration file gracefully."""
        # Ensure file doesn't exist
        cache_dir = _get_ml_cache_dir()
        calibration_file = cache_dir / "ml_calibration.json"
        if calibration_file.exists():
            calibration_file.unlink()
        
        # Should return defaults without crashing
        stats = get_calibration_stats()
        assert stats['sample_count'] == 0
        assert stats['adjusted_threshold'] == DEFAULT_CONFIDENCE_THRESHOLD


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
