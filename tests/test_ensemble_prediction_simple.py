"""Simple tests for ensemble prediction functionality (Iteration 125)."""

import pytest
from amorsize.ml_prediction import (
    SimpleLinearPredictor,
    WorkloadFeatures,
    TrainingData,
    ENABLE_ENSEMBLE_PREDICTION,
    MIN_SAMPLES_FOR_ENSEMBLE
)


class TestEnsembleBasics:
    """Test basic ensemble functionality."""
    
    def test_ensemble_constants_defined(self):
        """Ensemble constants should be defined."""
        assert ENABLE_ENSEMBLE_PREDICTION is not None
        assert MIN_SAMPLES_FOR_ENSEMBLE >= 10
    
    def test_predictor_has_ensemble_option(self):
        """Predictor should have ensemble parameter."""
        p1 = SimpleLinearPredictor(enable_ensemble=True)
        assert p1.enable_ensemble is True
        
        p2 = SimpleLinearPredictor(enable_ensemble=False)
        assert p2.enable_ensemble is False
    
    def test_ensemble_weights_initialized(self):
        """Ensemble weights should be initialized."""
        predictor = SimpleLinearPredictor(enable_ensemble=True)
        assert hasattr(predictor, 'ensemble_weights')
        assert isinstance(predictor.ensemble_weights, dict)
        assert len(predictor.ensemble_weights) > 0
    
    def test_import_successful(self):
        """Should be able to import ensemble constants from main module."""
        from amorsize import ENABLE_ENSEMBLE_PREDICTION, MIN_SAMPLES_FOR_ENSEMBLE
        assert ENABLE_ENSEMBLE_PREDICTION is not None
        assert MIN_SAMPLES_FOR_ENSEMBLE > 0


class TestEnsembleIntegration:
    """Test ensemble integration with existing features."""
    
    def test_predictor_with_all_features(self):
        """Predictor should initialize with all features enabled."""
        predictor = SimpleLinearPredictor(
            k=5,
            enable_clustering=True,
            enable_feature_selection=True,
            auto_tune_k=True,
            enable_ensemble=True
        )
        
        assert predictor.k == 5
        assert predictor.enable_clustering is True
        assert predictor.enable_feature_selection is True
        assert predictor.auto_tune_k is True
        assert predictor.enable_ensemble is True
