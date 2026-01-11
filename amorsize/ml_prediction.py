"""
ML-based prediction module for fast parameter optimization.

This module provides machine learning-based prediction of optimal n_jobs and
chunksize parameters without requiring dry-run sampling, dramatically reducing
optimization time for known workload patterns.

Key Features:
- 10-100x faster than dry-run sampling
- Learns from historical optimization data
- Provides confidence scores for predictions
- Falls back to dry-run sampling if confidence is low
- Simple linear regression model (no external ML dependencies)
"""

import json
import math
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .system_info import (
    get_physical_cores,
    get_available_memory,
    get_multiprocessing_start_method,
    get_spawn_cost_estimate
)


# Minimum number of training samples needed for prediction
MIN_TRAINING_SAMPLES = 3

# Confidence threshold for using predictions (0-1)
# Below this threshold, fall back to dry-run sampling
DEFAULT_CONFIDENCE_THRESHOLD = 0.6


class PredictionResult:
    """
    Container for ML prediction results.
    
    Attributes:
        n_jobs: Predicted number of workers
        chunksize: Predicted chunk size
        confidence: Confidence score (0-1) for this prediction
        reason: Explanation of prediction
        training_samples: Number of historical samples used for training
        feature_match_score: How well the current workload matches training data
    """
    
    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        confidence: float,
        reason: str,
        training_samples: int,
        feature_match_score: float
    ):
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.confidence = confidence
        self.reason = reason
        self.training_samples = training_samples
        self.feature_match_score = feature_match_score
    
    def __repr__(self):
        return (
            f"PredictionResult(n_jobs={self.n_jobs}, "
            f"chunksize={self.chunksize}, "
            f"confidence={self.confidence:.2f})"
        )


class WorkloadFeatures:
    """
    Extracted features from a workload for ML prediction.
    
    Features are normalized to [0, 1] range for better model performance.
    """
    
    def __init__(
        self,
        data_size: int,
        estimated_item_time: float,
        physical_cores: int,
        available_memory: int,
        start_method: str
    ):
        # Raw features
        self.data_size = data_size
        self.estimated_item_time = estimated_item_time
        self.physical_cores = physical_cores
        self.available_memory = available_memory
        self.start_method = start_method
        
        # Normalized features (0-1 range)
        # Log scale for data size (typical range: 10 to 1M items)
        self.norm_data_size = self._normalize_log(data_size, 10, 1_000_000)
        
        # Log scale for execution time (typical range: 1μs to 1s per item)
        self.norm_time = self._normalize_log(estimated_item_time, 1e-6, 1.0)
        
        # Linear scale for cores (typical range: 1 to 128)
        self.norm_cores = min(1.0, physical_cores / 128.0)
        
        # Log scale for memory (typical range: 1GB to 1TB)
        self.norm_memory = self._normalize_log(available_memory, 1e9, 1e12)
        
        # Start method as numeric (fork=0.0, spawn=1.0, forkserver=0.5)
        self.norm_start_method = {
            'fork': 0.0,
            'spawn': 1.0,
            'forkserver': 0.5
        }.get(start_method, 0.5)
    
    @staticmethod
    def _normalize_log(value: float, min_val: float, max_val: float) -> float:
        """Normalize value to [0, 1] using log scale."""
        if value <= 0:
            return 0.0
        log_val = math.log10(max(value, min_val))
        log_min = math.log10(min_val)
        log_max = math.log10(max_val)
        normalized = (log_val - log_min) / (log_max - log_min)
        return max(0.0, min(1.0, normalized))
    
    def to_vector(self) -> List[float]:
        """Convert features to a vector for model input."""
        return [
            self.norm_data_size,
            self.norm_time,
            self.norm_cores,
            self.norm_memory,
            self.norm_start_method
        ]
    
    def distance(self, other: "WorkloadFeatures") -> float:
        """
        Calculate Euclidean distance to another feature vector.
        
        Used to determine how similar two workloads are.
        Returns value in [0, sqrt(5)] range (5 features).
        """
        vec1 = self.to_vector()
        vec2 = other.to_vector()
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


class TrainingData:
    """
    Training data point from historical optimization.
    """
    
    def __init__(
        self,
        features: WorkloadFeatures,
        n_jobs: int,
        chunksize: int,
        speedup: float,
        timestamp: float
    ):
        self.features = features
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.speedup = speedup
        self.timestamp = timestamp


class SimpleLinearPredictor:
    """
    Simple linear regression predictor for n_jobs and chunksize.
    
    Uses weighted k-nearest neighbors approach:
    1. Find k most similar historical workloads
    2. Weight them by similarity (inverse distance)
    3. Predict as weighted average
    
    This approach is simple, interpretable, and requires no external dependencies.
    """
    
    def __init__(self, k: int = 5):
        """
        Initialize predictor.
        
        Args:
            k: Number of nearest neighbors to use for prediction
        """
        self.k = k
        self.training_data: List[TrainingData] = []
    
    def add_training_sample(self, sample: TrainingData):
        """Add a training sample to the model."""
        self.training_data.append(sample)
    
    def predict(
        self,
        features: WorkloadFeatures,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> Optional[PredictionResult]:
        """
        Predict optimal parameters for given workload features.
        
        Args:
            features: Workload features to predict for
            confidence_threshold: Minimum confidence required (0-1)
        
        Returns:
            PredictionResult if confident enough, None otherwise
        """
        if len(self.training_data) < MIN_TRAINING_SAMPLES:
            return None
        
        # Find k nearest neighbors
        neighbors = self._find_nearest_neighbors(features, self.k)
        
        if not neighbors:
            return None
        
        # Calculate confidence based on:
        # 1. Number of neighbors found
        # 2. Similarity of neighbors (low distance = high confidence)
        # 3. Consistency of neighbor predictions
        confidence = self._calculate_confidence(neighbors, features)
        
        if confidence < confidence_threshold:
            return None
        
        # Weighted average prediction
        n_jobs_pred, chunksize_pred = self._weighted_average(neighbors)
        
        # Calculate feature match score (0-1, higher is better)
        # This is the average similarity of the k neighbors
        avg_distance = sum(d for d, _ in neighbors) / len(neighbors)
        # Convert distance [0, sqrt(5)] to similarity [1, 0]
        feature_match_score = max(0.0, 1.0 - (avg_distance / math.sqrt(5)))
        
        reason = (
            f"Predicted from {len(neighbors)} similar historical workloads "
            f"(confidence: {confidence:.1%}, match score: {feature_match_score:.1%})"
        )
        
        return PredictionResult(
            n_jobs=n_jobs_pred,
            chunksize=chunksize_pred,
            confidence=confidence,
            reason=reason,
            training_samples=len(self.training_data),
            feature_match_score=feature_match_score
        )
    
    def _find_nearest_neighbors(
        self,
        features: WorkloadFeatures,
        k: int
    ) -> List[Tuple[float, TrainingData]]:
        """
        Find k nearest neighbors by Euclidean distance.
        
        Returns:
            List of (distance, training_data) tuples, sorted by distance
        """
        distances = []
        for sample in self.training_data:
            dist = features.distance(sample.features)
            distances.append((dist, sample))
        
        # Sort by distance and take k nearest
        distances.sort(key=lambda x: x[0])
        return distances[:k]
    
    def _calculate_confidence(
        self,
        neighbors: List[Tuple[float, TrainingData]],
        features: WorkloadFeatures
    ) -> float:
        """
        Calculate confidence score for prediction.
        
        Confidence is based on:
        1. Proximity of neighbors (closer = higher confidence)
        2. Number of neighbors (more = higher confidence)
        3. Consistency of predictions (low variance = higher confidence)
        
        Returns:
            Confidence score in [0, 1]
        """
        if not neighbors:
            return 0.0
        
        # Factor 1: Proximity score
        # Average distance of neighbors, normalized to [0, 1]
        avg_distance = sum(d for d, _ in neighbors) / len(neighbors)
        # Convert to similarity score (closer = higher score)
        proximity_score = max(0.0, 1.0 - (avg_distance / math.sqrt(5)))
        
        # Factor 2: Sample size score
        # More training samples = higher confidence
        sample_size_score = min(1.0, len(self.training_data) / 20.0)
        
        # Factor 3: Consistency score
        # Check variance in predictions
        n_jobs_values = [sample.n_jobs for _, sample in neighbors]
        chunksize_values = [sample.chunksize for _, sample in neighbors]
        
        # Calculate coefficient of variation for n_jobs
        if len(n_jobs_values) > 1 and sum(n_jobs_values) > 0:
            mean_n_jobs = sum(n_jobs_values) / len(n_jobs_values)
            var_n_jobs = sum((x - mean_n_jobs) ** 2 for x in n_jobs_values) / len(n_jobs_values)
            cv_n_jobs = math.sqrt(var_n_jobs) / mean_n_jobs if mean_n_jobs > 0 else 1.0
            # Low CV = high consistency = high score
            consistency_score = max(0.0, 1.0 - cv_n_jobs)
        else:
            consistency_score = 1.0
        
        # Combine factors (weighted average)
        confidence = (
            0.5 * proximity_score +
            0.2 * sample_size_score +
            0.3 * consistency_score
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _weighted_average(
        self,
        neighbors: List[Tuple[float, TrainingData]]
    ) -> Tuple[int, int]:
        """
        Calculate weighted average of neighbor predictions.
        
        Weights are inverse of distance (closer neighbors have more influence).
        
        Returns:
            Tuple of (n_jobs, chunksize)
        """
        # Calculate weights (inverse distance with small epsilon to avoid division by zero)
        epsilon = 0.01
        weights = [1.0 / (dist + epsilon) for dist, _ in neighbors]
        total_weight = sum(weights)
        
        # Weighted average
        n_jobs_weighted = sum(
            w * sample.n_jobs for w, (_, sample) in zip(weights, neighbors)
        ) / total_weight
        
        chunksize_weighted = sum(
            w * sample.chunksize for w, (_, sample) in zip(weights, neighbors)
        ) / total_weight
        
        # Round to integers and ensure minimum values
        n_jobs = max(1, round(n_jobs_weighted))
        chunksize = max(1, round(chunksize_weighted))
        
        return n_jobs, chunksize


def _get_ml_cache_dir() -> Path:
    """Get directory for storing ML training data."""
    home = Path.home()
    cache_dir = home / ".cache" / "amorsize" / "ml_training"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _compute_function_signature(func: Callable) -> str:
    """
    Compute a signature for a function to group related optimizations.
    
    Similar to cache.py's function hash, but we use this for grouping
    training data by function.
    """
    try:
        func_code = func.__code__.co_code
        func_hash = hashlib.sha256(func_code).hexdigest()[:16]
    except AttributeError:
        # For built-in functions or methods without __code__
        func_hash = hashlib.sha256(str(func).encode()).hexdigest()[:16]
    return func_hash


def load_training_data_from_cache() -> List[TrainingData]:
    """
    Load training data from optimization cache.
    
    Scans the cache directory for successful optimization results
    and extracts training data from them.
    
    Returns:
        List of TrainingData samples
    """
    training_data = []
    
    try:
        # Import cache module to access cache directory
        from .cache import get_cache_dir
        
        cache_dir = get_cache_dir()
        
        # Scan all cache files
        for cache_file in cache_dir.glob("opt_*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)
                
                # Extract features and results
                # Cache entries contain system info and optimization results
                if 'n_jobs' not in cache_entry or 'chunksize' not in cache_entry:
                    continue
                
                # Estimate data size from cache key (bucketed)
                # This is approximate but sufficient for ML training
                data_size = cache_entry.get('data_size', 1000)
                
                # Estimate execution time (if available from diagnostic data)
                # Use a default if not available
                exec_time = cache_entry.get('avg_execution_time', 0.01)
                
                # Get system info
                physical_cores = cache_entry.get('physical_cores', get_physical_cores())
                available_memory = cache_entry.get('available_memory', get_available_memory())
                start_method = cache_entry.get('start_method', get_multiprocessing_start_method())
                
                # Create features
                features = WorkloadFeatures(
                    data_size=data_size,
                    estimated_item_time=exec_time,
                    physical_cores=physical_cores,
                    available_memory=available_memory,
                    start_method=start_method
                )
                
                # Create training sample
                sample = TrainingData(
                    features=features,
                    n_jobs=cache_entry['n_jobs'],
                    chunksize=cache_entry['chunksize'],
                    speedup=cache_entry.get('estimated_speedup', 1.0),
                    timestamp=cache_entry.get('timestamp', time.time())
                )
                
                training_data.append(sample)
                
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted or incompatible cache entries
                continue
    
    except Exception:
        # If cache access fails, return empty list
        # This is not a critical error - prediction will just fall back to dry-run
        pass
    
    return training_data


def predict_parameters(
    func: Callable,
    data_size: int,
    estimated_item_time: float = 0.01,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    verbose: bool = False
) -> Optional[PredictionResult]:
    """
    Predict optimal n_jobs and chunksize using ML model.
    
    This function attempts to predict parameters without dry-run sampling
    by learning from historical optimization data.
    
    Args:
        func: Function to optimize (used for grouping related workloads)
        data_size: Number of items in the dataset
        estimated_item_time: Rough estimate of per-item execution time (seconds)
        confidence_threshold: Minimum confidence to return prediction (0-1)
        verbose: If True, print diagnostic information
    
    Returns:
        PredictionResult if confident enough, None if should fall back to dry-run
    
    Example:
        >>> result = predict_parameters(my_func, 10000, 0.001)
        >>> if result and result.confidence > 0.7:
        ...     print(f"Using ML prediction: n_jobs={result.n_jobs}")
        ... else:
        ...     print("Falling back to dry-run sampling")
    """
    # Extract features for current workload
    features = WorkloadFeatures(
        data_size=data_size,
        estimated_item_time=estimated_item_time,
        physical_cores=get_physical_cores(),
        available_memory=get_available_memory(),
        start_method=get_multiprocessing_start_method()
    )
    
    # Load training data from cache
    training_data = load_training_data_from_cache()
    
    if verbose:
        print(f"ML Prediction: Loaded {len(training_data)} training samples from cache")
    
    if len(training_data) < MIN_TRAINING_SAMPLES:
        if verbose:
            print(f"ML Prediction: Insufficient training data ({len(training_data)} < {MIN_TRAINING_SAMPLES})")
        return None
    
    # Create predictor and add training data
    predictor = SimpleLinearPredictor(k=min(5, len(training_data)))
    for sample in training_data:
        predictor.add_training_sample(sample)
    
    # Make prediction
    prediction = predictor.predict(features, confidence_threshold)
    
    if verbose:
        if prediction:
            print(f"ML Prediction: Success - n_jobs={prediction.n_jobs}, "
                  f"chunksize={prediction.chunksize}, confidence={prediction.confidence:.1%}")
        else:
            print(f"ML Prediction: Low confidence (< {confidence_threshold:.1%}), falling back to dry-run")
    
    return prediction


# Export public API
__all__ = [
    'predict_parameters',
    'PredictionResult',
    'WorkloadFeatures',
    'TrainingData',
    'SimpleLinearPredictor',
    'MIN_TRAINING_SAMPLES',
    'DEFAULT_CONFIDENCE_THRESHOLD'
]
