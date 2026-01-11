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
- k-Nearest Neighbors model (no external ML dependencies)
- Supports both batch (optimize) and streaming (optimize_streaming) workloads
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

# Import cost model for hardware-aware features (optional)
try:
    from .cost_model import detect_system_topology, SystemTopology
    _HAS_COST_MODEL = True
except ImportError:
    _HAS_COST_MODEL = False
    SystemTopology = None


# Minimum number of training samples needed for prediction
MIN_TRAINING_SAMPLES = 3

# Confidence threshold for using predictions (0-1)
# Below this threshold, fall back to dry-run sampling
# Note: optimize() function uses 0.7 as default for consistency with conservative approach
DEFAULT_CONFIDENCE_THRESHOLD = 0.7

# Filename format for ML training data
ML_TRAINING_FILE_FORMAT = "ml_training_{func_hash}_{timestamp}.json"

# Streaming prediction constants
# Default buffer size multiplier (buffer = n_jobs * multiplier)
DEFAULT_BUFFER_SIZE_MULTIPLIER = 3

# Memory fraction to use for result buffering (10% of available memory)
STREAMING_BUFFER_MEMORY_FRACTION = 0.1

# Coefficient of variation threshold for heterogeneous workload detection
HETEROGENEOUS_CV_THRESHOLD = 0.5

# Large dataset threshold for auto-selecting imap_unordered
LARGE_DATASET_THRESHOLD = 10000

# Calibration constants (Iteration 116)
# Filename format for calibration data
CALIBRATION_FILE = "ml_calibration.json"

# Minimum samples needed to adjust confidence threshold
MIN_CALIBRATION_SAMPLES = 10

# How much to adjust threshold based on accuracy (conservative factor)
CALIBRATION_ADJUSTMENT_FACTOR = 0.1

# Cross-system learning constants (Iteration 117)
# Filename format for system fingerprint
SYSTEM_FINGERPRINT_FILE = "system_fingerprint.json"

# Minimum similarity score to use cross-system data (0-1 scale)
# 0.8 means systems must be at least 80% similar
MIN_SYSTEM_SIMILARITY = 0.8

# Weight factor for cross-system samples (reduces their influence)
# Local system data gets weight 1.0, similar systems get this weight
CROSS_SYSTEM_WEIGHT = 0.7

# Normalization ranges for SystemFingerprint similarity calculation
# These ranges reflect typical hardware configurations as of 2024
MAX_EXPECTED_CORES = 128  # Up to 128 physical cores (high-end servers)
MIN_CACHE_MB = 1.0  # Minimum L3 cache size (1 MB)
MAX_CACHE_MB = 256.0  # Maximum L3 cache size (256 MB for high-end CPUs)
MIN_BANDWIDTH_GB_S = 10.0  # Minimum memory bandwidth (10 GB/s)
MAX_BANDWIDTH_GB_S = 1000.0  # Maximum memory bandwidth (1000 GB/s for high-end systems)
MAX_NUMA_NODES = 8  # Maximum NUMA nodes (typical for high-end servers)


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
        adaptive_chunking_enabled: Whether adaptive chunking is recommended (Iteration 119)
        adaptation_rate: Recommended adaptation rate (0-1) if adaptive chunking enabled (Iteration 119)
        min_chunksize: Recommended minimum chunk size if adaptive chunking enabled (Iteration 119)
        max_chunksize: Recommended maximum chunk size if adaptive chunking enabled (Iteration 119)
    """
    
    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        confidence: float,
        reason: str,
        training_samples: int,
        feature_match_score: float,
        adaptive_chunking_enabled: Optional[bool] = None,
        adaptation_rate: Optional[float] = None,
        min_chunksize: Optional[int] = None,
        max_chunksize: Optional[int] = None
    ):
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.confidence = confidence
        self.reason = reason
        self.training_samples = training_samples
        self.feature_match_score = feature_match_score
        self.adaptive_chunking_enabled = adaptive_chunking_enabled
        self.adaptation_rate = adaptation_rate
        self.min_chunksize = min_chunksize
        self.max_chunksize = max_chunksize
    
    def __repr__(self):
        return (
            f"PredictionResult(n_jobs={self.n_jobs}, "
            f"chunksize={self.chunksize}, "
            f"confidence={self.confidence:.2f})"
        )


class StreamingPredictionResult(PredictionResult):
    """
    Container for ML prediction results specific to streaming workloads.
    
    Extends PredictionResult with streaming-specific parameters like
    buffer size and ordering preference.
    
    Attributes:
        n_jobs: Predicted number of workers
        chunksize: Predicted chunk size
        confidence: Confidence score (0-1) for this prediction
        reason: Explanation of prediction
        training_samples: Number of historical samples used for training
        feature_match_score: How well the current workload matches training data
        buffer_size: Predicted optimal buffer size for imap/imap_unordered
        use_ordered: Whether to use ordered (imap) vs unordered (imap_unordered)
    """
    
    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        confidence: float,
        reason: str,
        training_samples: int,
        feature_match_score: float,
        buffer_size: Optional[int] = None,
        use_ordered: bool = True
    ):
        super().__init__(
            n_jobs=n_jobs,
            chunksize=chunksize,
            confidence=confidence,
            reason=reason,
            training_samples=training_samples,
            feature_match_score=feature_match_score
        )
        self.buffer_size = buffer_size if buffer_size is not None else n_jobs * 3
        self.use_ordered = use_ordered
    
    def __repr__(self):
        method = "imap" if self.use_ordered else "imap_unordered"
        return (
            f"StreamingPredictionResult(n_jobs={self.n_jobs}, "
            f"chunksize={self.chunksize}, "
            f"buffer_size={self.buffer_size}, "
            f"method={method}, "
            f"confidence={self.confidence:.2f})"
        )


class CalibrationData:
    """
    Container for confidence calibration tracking data (Iteration 116).
    
    Tracks prediction accuracy over time to enable adaptive confidence threshold
    adjustment. This allows the system to learn when high confidence actually
    correlates with accurate predictions.
    
    Attributes:
        predictions: List of (confidence, accuracy) tuples from past predictions
        adjusted_threshold: Current calibrated confidence threshold
        last_update: Timestamp of last calibration update
        baseline_threshold: Original threshold before calibration
    """
    
    def __init__(
        self,
        predictions: Optional[List[Tuple[float, float]]] = None,
        adjusted_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        last_update: Optional[float] = None,
        baseline_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ):
        self.predictions = predictions if predictions is not None else []
        self.adjusted_threshold = adjusted_threshold
        self.last_update = last_update if last_update is not None else time.time()
        self.baseline_threshold = baseline_threshold
    
    def add_prediction_result(self, confidence: float, accuracy: float):
        """
        Add a new prediction result for calibration.
        
        Args:
            confidence: Confidence score that was assigned (0-1)
            accuracy: Actual accuracy achieved (0-1, higher is better)
        """
        self.predictions.append((confidence, accuracy))
        self.last_update = time.time()
    
    def get_calibration_stats(self) -> Dict[str, float]:
        """
        Calculate calibration statistics from prediction history.
        
        Returns:
            Dictionary with calibration metrics:
                - mean_accuracy: Average prediction accuracy
                - high_confidence_accuracy: Accuracy when confidence >= threshold
                - low_confidence_accuracy: Accuracy when confidence < threshold
                - optimal_threshold: Suggested threshold based on accuracy curve
                - sample_count: Number of calibration samples
        """
        if not self.predictions:
            return {
                'mean_accuracy': 0.0,
                'high_confidence_accuracy': 0.0,
                'low_confidence_accuracy': 0.0,
                'optimal_threshold': self.baseline_threshold,
                'sample_count': 0
            }
        
        # Calculate overall mean accuracy
        accuracies = [acc for _, acc in self.predictions]
        mean_accuracy = sum(accuracies) / len(accuracies)
        
        # Split by current threshold
        high_conf_predictions = [(c, a) for c, a in self.predictions if c >= self.adjusted_threshold]
        low_conf_predictions = [(c, a) for c, a in self.predictions if c < self.adjusted_threshold]
        
        high_conf_accuracy = (
            sum(a for _, a in high_conf_predictions) / len(high_conf_predictions)
            if high_conf_predictions else 0.0
        )
        low_conf_accuracy = (
            sum(a for _, a in low_conf_predictions) / len(low_conf_predictions)
            if low_conf_predictions else 0.0
        )
        
        # Find optimal threshold by maximizing accuracy above threshold
        # Try thresholds from 0.5 to 0.95 in steps of 0.05
        best_threshold = self.baseline_threshold
        best_score = 0.0
        
        for threshold in [0.5 + i * 0.05 for i in range(10)]:
            above_threshold = [a for c, a in self.predictions if c >= threshold]
            if len(above_threshold) >= 3:  # Need at least 3 samples
                avg_accuracy = sum(above_threshold) / len(above_threshold)
                # Score balances accuracy and sample count
                score = avg_accuracy * min(1.0, len(above_threshold) / 10.0)
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
        
        return {
            'mean_accuracy': mean_accuracy,
            'high_confidence_accuracy': high_conf_accuracy,
            'low_confidence_accuracy': low_conf_accuracy,
            'optimal_threshold': best_threshold,
            'sample_count': len(self.predictions)
        }
    
    def recalibrate_threshold(self) -> float:
        """
        Recalibrate confidence threshold based on prediction history.
        
        Uses calibration statistics to adjust the threshold:
        - If high-confidence predictions are accurate, lower threshold slightly
        - If high-confidence predictions are inaccurate, raise threshold
        
        Returns:
            New calibrated threshold
        """
        if len(self.predictions) < MIN_CALIBRATION_SAMPLES:
            # Not enough data for calibration yet
            return self.adjusted_threshold
        
        stats = self.get_calibration_stats()
        
        # If we have a clearly better threshold, move toward it
        optimal = stats['optimal_threshold']
        current = self.adjusted_threshold
        
        # Use conservative adjustment factor to avoid oscillation
        adjustment = (optimal - current) * CALIBRATION_ADJUSTMENT_FACTOR
        new_threshold = current + adjustment
        
        # Clamp to reasonable bounds [0.5, 0.95]
        new_threshold = max(0.5, min(0.95, new_threshold))
        
        self.adjusted_threshold = new_threshold
        return new_threshold


class SystemFingerprint:
    """
    Hardware fingerprint for cross-system learning (Iteration 117).
    
    Captures key hardware characteristics that influence multiprocessing
    performance, enabling model transfer across similar systems.
    
    Attributes:
        physical_cores: Number of physical CPU cores
        l3_cache_mb: L3 cache size in megabytes
        numa_nodes: Number of NUMA nodes
        memory_bandwidth_gb_s: Memory bandwidth in GB/s
        start_method: Multiprocessing start method (fork/spawn/forkserver)
        system_id: Unique identifier for this system configuration
    """
    
    def __init__(
        self,
        physical_cores: int,
        l3_cache_mb: float,
        numa_nodes: int,
        memory_bandwidth_gb_s: float,
        start_method: str
    ):
        self.physical_cores = physical_cores
        self.l3_cache_mb = l3_cache_mb
        self.numa_nodes = numa_nodes
        self.memory_bandwidth_gb_s = memory_bandwidth_gb_s
        self.start_method = start_method
        
        # Generate unique system ID from key characteristics
        # This helps identify identical systems vs similar systems
        system_str = f"{physical_cores}_{l3_cache_mb:.1f}_{numa_nodes}_{memory_bandwidth_gb_s:.1f}_{start_method}"
        self.system_id = hashlib.sha256(system_str.encode()).hexdigest()[:16]
    
    def similarity(self, other: 'SystemFingerprint') -> float:
        """
        Calculate similarity score with another system (0-1 scale).
        
        Uses weighted Euclidean distance in normalized feature space.
        Systems are considered similar if they have comparable:
        - Core count (most important)
        - Cache size (important for data locality)
        - NUMA topology (important for memory access patterns)
        - Memory bandwidth (important for memory-bound workloads)
        - Start method (affects process spawn overhead)
        
        Args:
            other: Another system fingerprint to compare with
        
        Returns:
            Similarity score: 1.0 = identical, 0.0 = completely different
        """
        # Normalize features to [0, 1] for comparison
        # Use same ranges as WorkloadFeatures
        norm_cores_self = min(1.0, self.physical_cores / MAX_EXPECTED_CORES)
        norm_cores_other = min(1.0, other.physical_cores / MAX_EXPECTED_CORES)
        
        # Log scale for cache (MIN_CACHE_MB to MAX_CACHE_MB range)
        norm_cache_self = self._normalize_log(self.l3_cache_mb, MIN_CACHE_MB, MAX_CACHE_MB)
        norm_cache_other = self._normalize_log(other.l3_cache_mb, MIN_CACHE_MB, MAX_CACHE_MB)
        
        # Linear scale for NUMA nodes (1 to MAX_NUMA_NODES range)
        norm_numa_self = min(1.0, self.numa_nodes / MAX_NUMA_NODES)
        norm_numa_other = min(1.0, other.numa_nodes / MAX_NUMA_NODES)
        
        # Log scale for bandwidth (MIN_BANDWIDTH_GB_S to MAX_BANDWIDTH_GB_S range)
        norm_bw_self = self._normalize_log(self.memory_bandwidth_gb_s, MIN_BANDWIDTH_GB_S, MAX_BANDWIDTH_GB_S)
        norm_bw_other = self._normalize_log(other.memory_bandwidth_gb_s, MIN_BANDWIDTH_GB_S, MAX_BANDWIDTH_GB_S)
        
        # Start method: fork=0.0, spawn=1.0, forkserver=0.5
        norm_sm_self = {'fork': 0.0, 'spawn': 1.0, 'forkserver': 0.5}.get(self.start_method, 0.5)
        norm_sm_other = {'fork': 0.0, 'spawn': 1.0, 'forkserver': 0.5}.get(other.start_method, 0.5)
        
        # Calculate weighted Euclidean distance
        # Weights reflect importance for multiprocessing performance
        weights = {
            'cores': 2.0,       # Most important: determines parallelism capacity
            'cache': 1.5,       # Important: affects data locality
            'numa': 1.5,        # Important: affects memory access patterns
            'bandwidth': 1.0,   # Moderate: affects memory-bound workloads
            'start_method': 1.0 # Moderate: affects spawn overhead
        }
        
        squared_diff = (
            weights['cores'] * (norm_cores_self - norm_cores_other) ** 2 +
            weights['cache'] * (norm_cache_self - norm_cache_other) ** 2 +
            weights['numa'] * (norm_numa_self - norm_numa_other) ** 2 +
            weights['bandwidth'] * (norm_bw_self - norm_bw_other) ** 2 +
            weights['start_method'] * (norm_sm_self - norm_sm_other) ** 2
        )
        
        # Calculate distance
        total_weight = sum(weights.values())
        distance = math.sqrt(squared_diff / total_weight)
        
        # Convert distance to similarity (1.0 = identical, 0.0 = max distance)
        # Max possible distance is sqrt(1) = 1.0 in normalized space
        similarity = max(0.0, 1.0 - distance)
        
        return similarity
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'physical_cores': self.physical_cores,
            'l3_cache_mb': self.l3_cache_mb,
            'numa_nodes': self.numa_nodes,
            'memory_bandwidth_gb_s': self.memory_bandwidth_gb_s,
            'start_method': self.start_method,
            'system_id': self.system_id
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SystemFingerprint':
        """Create from dictionary (JSON deserialization)."""
        return SystemFingerprint(
            physical_cores=data['physical_cores'],
            l3_cache_mb=data['l3_cache_mb'],
            numa_nodes=data['numa_nodes'],
            memory_bandwidth_gb_s=data['memory_bandwidth_gb_s'],
            start_method=data['start_method']
        )
    
    def __repr__(self):
        return (
            f"SystemFingerprint(cores={self.physical_cores}, "
            f"cache={self.l3_cache_mb:.1f}MB, "
            f"numa={self.numa_nodes}, "
            f"bandwidth={self.memory_bandwidth_gb_s:.1f}GB/s, "
            f"method={self.start_method})"
        )


class WorkloadFeatures:
    """
    Extracted features from a workload for ML prediction.
    
    Features are normalized to [0, 1] range for better model performance.
    Enhanced in Iteration 104 with additional features for 15-25% accuracy improvement.
    Enhanced in Iteration 114 with hardware-aware features (cache, NUMA, bandwidth).
    """
    
    def __init__(
        self,
        data_size: int,
        estimated_item_time: float,
        physical_cores: int,
        available_memory: int,
        start_method: str,
        pickle_size: Optional[int] = None,
        coefficient_of_variation: Optional[float] = None,
        function_complexity: Optional[int] = None,
        system_topology: Optional['SystemTopology'] = None
    ):
        # Raw features (original 5)
        self.data_size = data_size
        self.estimated_item_time = estimated_item_time
        self.physical_cores = physical_cores
        self.available_memory = available_memory
        self.start_method = start_method
        
        # Raw features (new 3 - enhanced features from Iteration 104)
        self.pickle_size = pickle_size or 0
        self.coefficient_of_variation = coefficient_of_variation or 0.0
        self.function_complexity = function_complexity or 0
        
        # Raw features (new 4 - hardware-aware features from Iteration 114)
        # These are extracted from system_topology if available
        if system_topology is not None and _HAS_COST_MODEL:
            self.l3_cache_size = system_topology.cache_info.l3_size
            self.numa_nodes = system_topology.numa_info.numa_nodes
            self.memory_bandwidth_gb_s = system_topology.memory_bandwidth.bandwidth_gb_per_sec
            self.has_numa = 1 if system_topology.numa_info.has_numa else 0
        else:
            # Default values when cost model unavailable
            self.l3_cache_size = 8 * 1024 * 1024  # 8MB (conservative default)
            self.numa_nodes = 1
            self.memory_bandwidth_gb_s = 25.0  # DDR4-3200 single channel estimate
            self.has_numa = 0
        
        # Normalized features (0-1 range) - original 5
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
        
        # Normalized features (0-1 range) - new 3
        # Log scale for pickle size (typical range: 10 bytes to 10MB)
        self.norm_pickle_size = self._normalize_log(max(1, pickle_size or 1), 10, 1e7)
        
        # Linear scale for CV (typical range: 0 to 2.0, higher means more heterogeneous)
        # CV values are typically:
        #   - CV < 0.3: homogeneous (consistent execution times)
        #   - CV 0.3-0.7: moderately heterogeneous
        #   - CV > 0.7: highly heterogeneous (significant variance)
        # CV > 2.0 is rare but theoretically possible for extremely variable workloads
        self.norm_cv = min(1.0, (coefficient_of_variation or 0.0) / 2.0)
        
        # Log scale for function complexity (bytecode size, typical: 100 to 10000 bytes)
        self.norm_complexity = self._normalize_log(max(1, function_complexity or 1), 100, 10000)
        
        # Normalized features (0-1 range) - new 4 hardware-aware features (Iteration 114)
        # Log scale for L3 cache size (typical range: 1MB to 256MB)
        # Larger cache = better data locality for multi-core workloads
        self.norm_l3_cache = self._normalize_log(max(1e6, self.l3_cache_size), 1e6, 256e6)
        
        # Linear scale for NUMA nodes (typical range: 1 to 8)
        # More NUMA nodes = higher cross-node memory access penalty
        self.norm_numa_nodes = min(1.0, self.numa_nodes / 8.0)
        
        # Log scale for memory bandwidth (typical range: 10 GB/s to 1000 GB/s)
        # Higher bandwidth = better support for memory-intensive parallel workloads
        self.norm_memory_bandwidth = self._normalize_log(max(10.0, self.memory_bandwidth_gb_s), 10.0, 1000.0)
        
        # Binary feature for NUMA presence (0 or 1)
        # Has NUMA = need to consider cross-node penalties
        self.norm_has_numa = float(self.has_numa)
    
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
        """
        Convert features to a vector for model input.
        
        Enhanced in Iteration 104 with 8 features (was 5).
        Enhanced in Iteration 114 with 12 features (was 8) - added hardware-aware features.
        """
        return [
            self.norm_data_size,
            self.norm_time,
            self.norm_cores,
            self.norm_memory,
            self.norm_start_method,
            self.norm_pickle_size,
            self.norm_cv,
            self.norm_complexity,
            self.norm_l3_cache,
            self.norm_numa_nodes,
            self.norm_memory_bandwidth,
            self.norm_has_numa
        ]
    
    def distance(self, other: "WorkloadFeatures") -> float:
        """
        Calculate Euclidean distance to another feature vector.
        
        Used to determine how similar two workloads are.
        Returns value in [0, sqrt(12)] range (12 features - updated in Iteration 114).
        """
        vec1 = self.to_vector()
        vec2 = other.to_vector()
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


class TrainingData:
    """
    Training data point from historical optimization.
    
    Supports both batch and streaming workloads. For streaming workloads,
    additional parameters like buffer_size and use_ordered are included.
    
    Enhanced in Iteration 117 with system_fingerprint for cross-system learning.
    Enhanced in Iteration 119 with adaptive_chunking parameters for ML learning.
    """
    
    def __init__(
        self,
        features: WorkloadFeatures,
        n_jobs: int,
        chunksize: int,
        speedup: float,
        timestamp: float,
        buffer_size: Optional[int] = None,
        use_ordered: Optional[bool] = None,
        is_streaming: bool = False,
        system_fingerprint: Optional[SystemFingerprint] = None,
        weight: float = 1.0,
        adaptive_chunking_enabled: Optional[bool] = None,
        adaptation_rate: Optional[float] = None,
        min_chunksize: Optional[int] = None,
        max_chunksize: Optional[int] = None
    ):
        self.features = features
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.speedup = speedup
        self.timestamp = timestamp
        # Streaming-specific parameters (Iteration 115)
        self.buffer_size = buffer_size
        self.use_ordered = use_ordered
        self.is_streaming = is_streaming
        
        # Cross-system learning (Iteration 117)
        self.system_fingerprint = system_fingerprint
        self.weight = weight  # Allows weighting samples from similar systems
        
        # Adaptive chunking parameters (Iteration 119)
        self.adaptive_chunking_enabled = adaptive_chunking_enabled
        self.adaptation_rate = adaptation_rate
        self.min_chunksize = min_chunksize
        self.max_chunksize = max_chunksize


class SimpleLinearPredictor:
    """
    k-Nearest Neighbors predictor for n_jobs and chunksize.
    
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
        # Convert distance [0, sqrt(12)] to similarity [1, 0] (12 features - updated in Iteration 114)
        feature_match_score = max(0.0, 1.0 - (avg_distance / math.sqrt(12)))
        
        reason = (
            f"Predicted from {len(neighbors)} similar historical workloads "
            f"(confidence: {confidence:.1%}, match score: {feature_match_score:.1%})"
        )
        
        # Predict adaptive chunking parameters (Iteration 119)
        # Only recommend adaptive chunking if CV is high (heterogeneous workload)
        # and we have training samples that used adaptive chunking successfully
        adaptive_params = self._predict_adaptive_chunking(neighbors, features)
        
        return PredictionResult(
            n_jobs=n_jobs_pred,
            chunksize=chunksize_pred,
            confidence=confidence,
            reason=reason,
            training_samples=len(self.training_data),
            feature_match_score=feature_match_score,
            adaptive_chunking_enabled=adaptive_params['enabled'],
            adaptation_rate=adaptive_params['adaptation_rate'],
            min_chunksize=adaptive_params['min_chunksize'],
            max_chunksize=adaptive_params['max_chunksize']
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
        # sqrt(12) is the maximum distance with 12 features (updated in Iteration 114)
        proximity_score = max(0.0, 1.0 - (avg_distance / math.sqrt(12)))
        
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
        Enhanced in Iteration 117 to also consider cross-system weights.
        
        Returns:
            Tuple of (n_jobs, chunksize)
        """
        # Calculate weights (inverse distance with small epsilon to avoid division by zero)
        epsilon = 0.01
        distance_weights = [1.0 / (dist + epsilon) for dist, _ in neighbors]
        
        # Apply cross-system weights (Iteration 117)
        # Combine distance-based weight with sample weight (for cross-system data)
        combined_weights = [
            dw * sample.weight for dw, (_, sample) in zip(distance_weights, neighbors)
        ]
        
        total_weight = sum(combined_weights)
        
        # Weighted average
        n_jobs_weighted = sum(
            w * sample.n_jobs for w, (_, sample) in zip(combined_weights, neighbors)
        ) / total_weight
        
        chunksize_weighted = sum(
            w * sample.chunksize for w, (_, sample) in zip(combined_weights, neighbors)
        ) / total_weight
        
        # Round to integers and ensure minimum values
        n_jobs = max(1, round(n_jobs_weighted))
        chunksize = max(1, round(chunksize_weighted))
        
        return n_jobs, chunksize
    
    def _predict_adaptive_chunking(
        self,
        neighbors: List[Tuple[float, TrainingData]],
        features: WorkloadFeatures
    ) -> Dict[str, Any]:
        """
        Predict adaptive chunking parameters based on neighbors.
        
        Adaptive chunking is recommended when:
        1. Workload has high coefficient of variation (CV > 0.3)
        2. Similar historical workloads benefited from adaptive chunking
        
        Args:
            neighbors: k-nearest neighbors with their distances
            features: Current workload features
        
        Returns:
            Dictionary with adaptive chunking recommendations:
                - enabled: Whether to enable adaptive chunking
                - adaptation_rate: Recommended adaptation rate (0-1)
                - min_chunksize: Recommended minimum chunk size
                - max_chunksize: Recommended maximum chunk size (None = no limit)
        """
        # Check if workload is heterogeneous (high CV)
        cv = features.coefficient_of_variation
        is_heterogeneous = cv > 0.3
        
        # Check if neighbors used adaptive chunking successfully
        neighbors_with_adaptive = [
            (dist, sample) for dist, sample in neighbors
            if sample.adaptive_chunking_enabled is True
        ]
        
        # Recommend adaptive chunking if workload is heterogeneous
        # AND either we have no data or neighbors used it successfully
        if not is_heterogeneous:
            # Homogeneous workload - no benefit from adaptive chunking
            return {
                'enabled': False,
                'adaptation_rate': None,
                'min_chunksize': None,
                'max_chunksize': None
            }
        
        # For heterogeneous workloads, recommend adaptive chunking
        # If we have neighbors that used it, learn from them
        # Otherwise use sensible defaults
        
        if neighbors_with_adaptive:
            # Learn from similar workloads that used adaptive chunking
            # Calculate weighted average of their parameters
            epsilon = 0.01
            distance_weights = [1.0 / (dist + epsilon) for dist, _ in neighbors_with_adaptive]
            combined_weights = [
                dw * sample.weight for dw, (_, sample) in zip(distance_weights, neighbors_with_adaptive)
            ]
            total_weight = sum(combined_weights)
            
            # Weighted average of adaptation rate
            adaptation_rates = [
                sample.adaptation_rate for _, sample in neighbors_with_adaptive
                if sample.adaptation_rate is not None
            ]
            if adaptation_rates and total_weight > 0:
                adaptation_rate = sum(
                    w * sample.adaptation_rate 
                    for w, (_, sample) in zip(combined_weights, neighbors_with_adaptive)
                    if sample.adaptation_rate is not None
                ) / total_weight
            else:
                # Default: moderate adaptation for CV 0.3-0.7, aggressive for CV > 0.7
                adaptation_rate = 0.3 if cv < 0.7 else 0.5
            
            # Weighted average of min_chunksize
            min_chunksizes = [
                sample.min_chunksize for _, sample in neighbors_with_adaptive
                if sample.min_chunksize is not None
            ]
            if min_chunksizes and total_weight > 0:
                min_chunksize = max(1, round(sum(
                    w * sample.min_chunksize 
                    for w, (_, sample) in zip(combined_weights, neighbors_with_adaptive)
                    if sample.min_chunksize is not None
                ) / total_weight))
            else:
                min_chunksize = 1  # Default minimum
            
            # Weighted average of max_chunksize (if specified)
            max_chunksizes = [
                sample.max_chunksize for _, sample in neighbors_with_adaptive
                if sample.max_chunksize is not None
            ]
            if max_chunksizes and total_weight > 0:
                max_chunksize = max(min_chunksize + 1, round(sum(
                    w * sample.max_chunksize 
                    for w, (_, sample) in zip(combined_weights, neighbors_with_adaptive)
                    if sample.max_chunksize is not None
                ) / total_weight))
            else:
                max_chunksize = None  # No limit by default
        else:
            # No training data with adaptive chunking - use sensible defaults
            # Adaptation rate based on CV: higher CV = more aggressive adaptation
            if cv > 0.7:
                adaptation_rate = 0.5  # Aggressive adaptation for highly heterogeneous
            elif cv > 0.5:
                adaptation_rate = 0.4  # Moderate-aggressive
            else:
                adaptation_rate = 0.3  # Moderate adaptation
            
            min_chunksize = 1
            max_chunksize = None  # No limit
        
        return {
            'enabled': True,
            'adaptation_rate': adaptation_rate,
            'min_chunksize': min_chunksize,
            'max_chunksize': max_chunksize
        }
    
    def analyze_feature_importance(self) -> Dict[str, float]:
        """
        Analyze which features contribute most to prediction differences.
        
        Uses variance-based importance: features with higher variance across
        training samples have more potential to discriminate between different
        optimal parameters.
        
        Returns:
            Dictionary mapping feature names to importance scores (0-1, higher = more important)
        
        Example:
            >>> predictor = SimpleLinearPredictor()
            >>> # ... add training samples ...
            >>> importance = predictor.analyze_feature_importance()
            >>> print(f"Most important feature: {max(importance, key=importance.get)}")
        """
        if len(self.training_data) < 2:
            # Need at least 2 samples to compute variance
            return {}
        
        # Updated in Iteration 118 to include all 12 features
        # (added l3_cache_size, numa_nodes, memory_bandwidth, has_numa from Iteration 114)
        feature_names = [
            'data_size',
            'execution_time',
            'physical_cores',
            'available_memory',
            'start_method',
            'pickle_size',
            'coefficient_of_variation',
            'function_complexity',
            'l3_cache_size',
            'numa_nodes',
            'memory_bandwidth',
            'has_numa'
        ]
        
        # Extract feature vectors
        feature_vectors = [sample.features.to_vector() for sample in self.training_data]
        
        # Compute variance for each feature across all samples
        feature_variances = []
        num_features = len(feature_vectors[0])
        
        for i in range(num_features):
            values = [vec[i] for vec in feature_vectors]
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            feature_variances.append(variance)
        
        # Normalize variances to [0, 1] range
        max_variance = max(feature_variances) if feature_variances else 1.0
        if max_variance > 0:
            normalized_importance = {
                name: var / max_variance
                for name, var in zip(feature_names, feature_variances)
            }
        else:
            normalized_importance = {name: 0.0 for name in feature_names}
        
        return normalized_importance
    
    def analyze_feature_importance_correlation(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze feature importance using correlation with optimal parameters.
        
        This method calculates how strongly each feature correlates with the
        optimal n_jobs and chunksize values. Features with high correlation
        are more predictive of the optimal parameters.
        
        Returns:
            Dictionary with 'n_jobs' and 'chunksize' keys, each mapping feature
            names to correlation scores (0-1, higher = stronger correlation).
            Also includes 'combined' which averages both correlations.
        
        Example:
            >>> predictor = SimpleLinearPredictor()
            >>> # ... add training samples ...
            >>> importance = predictor.analyze_feature_importance_correlation()
            >>> print(f"Features most correlated with n_jobs: {importance['n_jobs']}")
            >>> print(f"Features most correlated with chunksize: {importance['chunksize']}")
            >>> print(f"Overall most important: {max(importance['combined'], key=importance['combined'].get)}")
        """
        if len(self.training_data) < 2:
            # Need at least 2 samples to compute correlation
            return {'n_jobs': {}, 'chunksize': {}, 'combined': {}}
        
        feature_names = [
            'data_size',
            'execution_time',
            'physical_cores',
            'available_memory',
            'start_method',
            'pickle_size',
            'coefficient_of_variation',
            'function_complexity',
            'l3_cache_size',
            'numa_nodes',
            'memory_bandwidth',
            'has_numa'
        ]
        
        # Extract feature vectors and targets
        feature_vectors = [sample.features.to_vector() for sample in self.training_data]
        n_jobs_values = [sample.n_jobs for sample in self.training_data]
        chunksize_values = [sample.chunksize for sample in self.training_data]
        
        num_features = len(feature_vectors[0])
        
        # Calculate correlation for each feature with n_jobs
        n_jobs_correlations = []
        for i in range(num_features):
            feature_values = [vec[i] for vec in feature_vectors]
            corr = self._calculate_correlation(feature_values, n_jobs_values)
            n_jobs_correlations.append(abs(corr))  # Use absolute value
        
        # Calculate correlation for each feature with chunksize
        chunksize_correlations = []
        for i in range(num_features):
            feature_values = [vec[i] for vec in feature_vectors]
            corr = self._calculate_correlation(feature_values, chunksize_values)
            chunksize_correlations.append(abs(corr))  # Use absolute value
        
        # Normalize correlations to [0, 1] range
        # Handle case where all correlations are 0.0 (avoid division by zero)
        max_n_jobs_corr = max(n_jobs_correlations) if n_jobs_correlations and max(n_jobs_correlations) > 0 else 1.0
        max_chunksize_corr = max(chunksize_correlations) if chunksize_correlations and max(chunksize_correlations) > 0 else 1.0
        
        n_jobs_importance = {}
        chunksize_importance = {}
        combined_importance = {}
        
        for i, name in enumerate(feature_names):
            n_jobs_score = n_jobs_correlations[i] / max_n_jobs_corr
            chunksize_score = chunksize_correlations[i] / max_chunksize_corr
            
            n_jobs_importance[name] = n_jobs_score
            chunksize_importance[name] = chunksize_score
            # Combined is average of both correlations
            combined_importance[name] = (n_jobs_score + chunksize_score) / 2.0
        
        return {
            'n_jobs': n_jobs_importance,
            'chunksize': chunksize_importance,
            'combined': combined_importance
        }
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient between two variables.
        
        Args:
            x: First variable values
            y: Second variable values
        
        Returns:
            Correlation coefficient in [-1, 1] range
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        
        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        # Calculate covariance and standard deviations
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        std_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
        std_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))
        
        # Avoid division by zero
        if std_x == 0 or std_y == 0:
            return 0.0
        
        return cov / (std_x * std_y)
    
    def track_prediction_performance(
        self,
        features: WorkloadFeatures,
        predicted_n_jobs: int,
        predicted_chunksize: int,
        actual_n_jobs: int,
        actual_chunksize: int
    ) -> Dict[str, float]:
        """
        Track prediction accuracy by comparing predicted vs actual parameters.
        
        This helps monitor model performance over time and identify when
        the model needs retraining or when confidence thresholds should be adjusted.
        
        Args:
            features: Features used for prediction
            predicted_n_jobs: Model's prediction for n_jobs
            predicted_chunksize: Model's prediction for chunksize
            actual_n_jobs: Actual optimal n_jobs from dry-run
            actual_chunksize: Actual optimal chunksize from dry-run
        
        Returns:
            Dictionary with performance metrics:
                - n_jobs_error: Absolute error in n_jobs prediction
                - n_jobs_relative_error: Relative error (0-1, lower is better)
                - chunksize_error: Absolute error in chunksize prediction
                - chunksize_relative_error: Relative error (0-1, lower is better)
                - overall_accuracy: Combined accuracy score (0-1, higher is better)
        
        Example:
            >>> predictor = SimpleLinearPredictor()
            >>> # ... make prediction ...
            >>> metrics = predictor.track_prediction_performance(
            ...     features, pred_n_jobs=4, pred_chunksize=100,
            ...     actual_n_jobs=4, actual_chunksize=95
            ... )
            >>> print(f"Prediction accuracy: {metrics['overall_accuracy']:.1%}")
        """
        # Calculate absolute errors
        n_jobs_error = abs(predicted_n_jobs - actual_n_jobs)
        chunksize_error = abs(predicted_chunksize - actual_chunksize)
        
        # Calculate relative errors (0-1, capped at 1.0)
        n_jobs_relative = min(1.0, n_jobs_error / max(1, actual_n_jobs))
        chunksize_relative = min(1.0, chunksize_error / max(1, actual_chunksize))
        
        # Overall accuracy: average of (1 - relative_error) for both parameters
        # This gives a score where 1.0 = perfect, 0.0 = completely wrong
        overall_accuracy = 1.0 - ((n_jobs_relative + chunksize_relative) / 2.0)
        
        return {
            'n_jobs_error': n_jobs_error,
            'n_jobs_relative_error': n_jobs_relative,
            'chunksize_error': chunksize_error,
            'chunksize_relative_error': chunksize_relative,
            'overall_accuracy': overall_accuracy
        }


def _get_ml_cache_dir() -> Path:
    """Get directory for storing ML training data."""
    home = Path.home()
    cache_dir = home / ".cache" / "amorsize" / "ml_training"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _load_calibration_data() -> CalibrationData:
    """
    Load confidence calibration data from cache (Iteration 116).
    
    Returns:
        CalibrationData object with historical calibration information
    """
    cache_dir = _get_ml_cache_dir()
    calibration_file = cache_dir / CALIBRATION_FILE
    
    if not calibration_file.exists():
        return CalibrationData()
    
    try:
        with open(calibration_file, 'r') as f:
            data = json.load(f)
        
        return CalibrationData(
            predictions=[(p['confidence'], p['accuracy']) for p in data.get('predictions', [])],
            adjusted_threshold=data.get('adjusted_threshold', DEFAULT_CONFIDENCE_THRESHOLD),
            last_update=data.get('last_update', time.time()),
            baseline_threshold=data.get('baseline_threshold', DEFAULT_CONFIDENCE_THRESHOLD)
        )
    except Exception:
        # If load fails, return fresh calibration data
        return CalibrationData()


def _save_calibration_data(calibration: CalibrationData) -> bool:
    """
    Save confidence calibration data to cache (Iteration 116).
    
    Args:
        calibration: CalibrationData object to save
    
    Returns:
        True if successfully saved, False otherwise
    """
    cache_dir = _get_ml_cache_dir()
    calibration_file = cache_dir / CALIBRATION_FILE
    
    try:
        # Prepare data for JSON serialization
        data = {
            'predictions': [
                {'confidence': conf, 'accuracy': acc}
                for conf, acc in calibration.predictions
            ],
            'adjusted_threshold': calibration.adjusted_threshold,
            'last_update': calibration.last_update,
            'baseline_threshold': calibration.baseline_threshold,
            'version': '1.0'  # For future compatibility
        }
        
        # Atomic write: write to temp file then rename
        temp_file = calibration_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Atomic rename
        temp_file.replace(calibration_file)
        return True
    except Exception:
        return False


def _get_current_system_fingerprint() -> SystemFingerprint:
    """
    Create fingerprint for the current system (Iteration 117).
    
    Captures hardware characteristics for cross-system learning:
    - Physical core count
    - L3 cache size
    - NUMA topology
    - Memory bandwidth
    - Multiprocessing start method
    
    Returns:
        SystemFingerprint for current system
    """
    physical_cores = get_physical_cores()
    start_method = get_multiprocessing_start_method()
    
    # Get hardware topology if available
    if _HAS_COST_MODEL:
        try:
            topology = detect_system_topology()
            l3_cache_mb = topology.cache_info.l3_size / (1024 * 1024)
            numa_nodes = topology.numa_info.numa_nodes
            memory_bandwidth_gb_s = topology.memory_bandwidth.bandwidth_gb_per_sec
        except Exception:
            # Fallback to defaults if detection fails
            l3_cache_mb = 8.0  # 8MB conservative default
            numa_nodes = 1
            memory_bandwidth_gb_s = 25.0  # DDR4-3200 single channel
    else:
        # Defaults when cost model unavailable
        l3_cache_mb = 8.0
        numa_nodes = 1
        memory_bandwidth_gb_s = 25.0
    
    return SystemFingerprint(
        physical_cores=physical_cores,
        l3_cache_mb=l3_cache_mb,
        numa_nodes=numa_nodes,
        memory_bandwidth_gb_s=memory_bandwidth_gb_s,
        start_method=start_method
    )


def _save_system_fingerprint(fingerprint: SystemFingerprint) -> bool:
    """
    Save system fingerprint to cache (Iteration 117).
    
    Stores the current system's hardware characteristics for cross-system
    learning. This fingerprint is used to identify similar systems and
    enable model transfer.
    
    Args:
        fingerprint: SystemFingerprint object to save
    
    Returns:
        True if successfully saved, False otherwise
    """
    cache_dir = _get_ml_cache_dir()
    fingerprint_file = cache_dir / SYSTEM_FINGERPRINT_FILE
    
    try:
        # Prepare data for JSON serialization
        data = {
            'fingerprint': fingerprint.to_dict(),
            'last_updated': time.time(),
            'version': '1.0'  # For future compatibility
        }
        
        # Atomic write: write to temp file then rename
        temp_file = fingerprint_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Atomic rename
        temp_file.replace(fingerprint_file)
        return True
    except Exception:
        return False


def _load_system_fingerprint() -> Optional[SystemFingerprint]:
    """
    Load system fingerprint from cache (Iteration 117).
    
    Returns:
        SystemFingerprint if found, None if not cached or invalid
    """
    cache_dir = _get_ml_cache_dir()
    fingerprint_file = cache_dir / SYSTEM_FINGERPRINT_FILE
    
    try:
        if not fingerprint_file.exists():
            return None
        
        with open(fingerprint_file, 'r') as f:
            data = json.load(f)
        
        return SystemFingerprint.from_dict(data['fingerprint'])
    except Exception:
        return None


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


def _compute_function_complexity(func: Callable) -> int:
    """
    Compute a complexity metric for a function based on bytecode size.
    
    This is a simple but effective proxy for function complexity:
    - More bytecode = more complex logic
    - Helps ML model differentiate simple vs complex functions
    
    Args:
        func: Function to analyze
    
    Returns:
        Size of function bytecode in bytes (0 if cannot be computed)
    """
    try:
        func_code = func.__code__.co_code
        return len(func_code)
    except AttributeError:
        # For built-in functions or methods without __code__
        # Return 0 as we can't determine complexity
        return 0


def load_training_data_from_cache() -> List[TrainingData]:
    """
    Load training data from optimization cache.
    
    Scans the cache directory for successful optimization results
    and extracts training data from them. Also loads data from online
    learning (actual execution results).
    
    Enhanced in Iteration 104 to extract pickle_size, coefficient_of_variation,
    and function_complexity features when available.
    
    Enhanced in Iteration 112 to include online learning data from actual executions.
    
    Returns:
        List of TrainingData samples from both cache and online learning
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
                
                # Get enhanced features (new in Iteration 104)
                pickle_size = cache_entry.get('pickle_size', None)
                coefficient_of_variation = cache_entry.get('coefficient_of_variation', None)
                function_complexity = cache_entry.get('function_complexity', None)
                
                # Create features
                # Note: system_topology is not stored in cache files
                # Will use default values for hardware features when loading old data
                features = WorkloadFeatures(
                    data_size=data_size,
                    estimated_item_time=exec_time,
                    physical_cores=physical_cores,
                    available_memory=available_memory,
                    start_method=start_method,
                    pickle_size=pickle_size,
                    coefficient_of_variation=coefficient_of_variation,
                    function_complexity=function_complexity,
                    system_topology=None  # Not stored in cache, use defaults
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
                
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                # Skip corrupted or incompatible cache entries
                continue
    
    except (OSError, IOError, PermissionError):
        # If cache access fails, return empty list
        # This is not a critical error - prediction will just fall back to dry-run
        pass
    except ImportError:
        # get_cache_dir may not be available
        pass
    
    # Also load online learning training data (from actual executions)
    # This data is typically more accurate as it reflects real performance
    # load_ml_training_data() already has its own exception handling
    online_learning_data = load_ml_training_data()
    training_data.extend(online_learning_data)
    
    return training_data


def predict_parameters(
    func: Callable,
    data_size: int,
    estimated_item_time: float = 0.01,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    verbose: bool = False,
    pickle_size: Optional[int] = None,
    coefficient_of_variation: Optional[float] = None,
    use_calibration: bool = True
) -> Optional[PredictionResult]:
    """
    Predict optimal n_jobs and chunksize using ML model.
    
    This function attempts to predict parameters without dry-run sampling
    by learning from historical optimization data.
    
    Enhanced in Iteration 104 with additional features for improved accuracy.
    Enhanced in Iteration 116 with confidence calibration for adaptive thresholds.
    
    Args:
        func: Function to optimize (used for grouping related workloads)
        data_size: Number of items in the dataset
        estimated_item_time: Rough estimate of per-item execution time (seconds)
        confidence_threshold: Minimum confidence to return prediction (0-1)
        verbose: If True, print diagnostic information
        pickle_size: Average pickle size of return objects (bytes) - optional
        coefficient_of_variation: CV of execution times (0-2) - optional
        use_calibration: If True, use calibrated confidence threshold (Iteration 116)
    
    Returns:
        PredictionResult if confident enough, None if should fall back to dry-run
    
    Example:
        >>> result = predict_parameters(my_func, 10000, 0.001)
        >>> if result and result.confidence > 0.7:
        ...     print(f"Using ML prediction: n_jobs={result.n_jobs}")
        ... else:
        ...     print("Falling back to dry-run sampling")
    """
    # Load calibration data if enabled (Iteration 116)
    if use_calibration:
        try:
            calibration = _load_calibration_data()
            # Use calibrated threshold if we have enough calibration samples
            if len(calibration.predictions) >= MIN_CALIBRATION_SAMPLES:
                effective_threshold = calibration.adjusted_threshold
                if verbose:
                    print(f"ML Prediction: Using calibrated threshold {effective_threshold:.2f} "
                          f"(baseline: {confidence_threshold:.2f}, samples: {len(calibration.predictions)})")
            else:
                effective_threshold = confidence_threshold
        except Exception:
            # If calibration load fails, use default threshold
            effective_threshold = confidence_threshold
    else:
        effective_threshold = confidence_threshold
    
    # Compute function complexity
    function_complexity = _compute_function_complexity(func)
    
    # Detect system topology for hardware-aware features (Iteration 114)
    system_topology = None
    if _HAS_COST_MODEL:
        try:
            physical_cores = get_physical_cores()
            system_topology = detect_system_topology(physical_cores)
        except Exception:
            # Graceful fallback if topology detection fails
            system_topology = None
    
    # Extract features for current workload
    features = WorkloadFeatures(
        data_size=data_size,
        estimated_item_time=estimated_item_time,
        physical_cores=get_physical_cores(),
        available_memory=get_available_memory(),
        start_method=get_multiprocessing_start_method(),
        pickle_size=pickle_size,
        coefficient_of_variation=coefficient_of_variation,
        function_complexity=function_complexity,
        system_topology=system_topology
    )
    
    # Load training data from cache
    training_data = load_training_data_from_cache()
    
    if verbose:
        print(f"ML Prediction: Loaded {len(training_data)} training samples from cache")
        if _HAS_COST_MODEL and system_topology:
            print(f"ML Prediction: Using 12 features (enhanced with hardware topology)")
        else:
            print(f"ML Prediction: Using 12 features (with default hardware values)")
    
    if len(training_data) < MIN_TRAINING_SAMPLES:
        if verbose:
            print(f"ML Prediction: Insufficient training data ({len(training_data)} < {MIN_TRAINING_SAMPLES})")
        return None
    
    # Create predictor and add training data
    predictor = SimpleLinearPredictor(k=min(5, len(training_data)))
    for sample in training_data:
        predictor.add_training_sample(sample)
    
    # Make prediction using effective (possibly calibrated) threshold
    prediction = predictor.predict(features, effective_threshold)
    
    if verbose:
        if prediction:
            print(f"ML Prediction: Success - n_jobs={prediction.n_jobs}, "
                  f"chunksize={prediction.chunksize}, confidence={prediction.confidence:.1%}")
        else:
            print(f"ML Prediction: Low confidence (< {effective_threshold:.1%}), falling back to dry-run")
    
    return prediction


def predict_streaming_parameters(
    func: Callable,
    data_size: int,
    estimated_item_time: float = 0.01,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    verbose: bool = False,
    pickle_size: Optional[int] = None,
    coefficient_of_variation: Optional[float] = None,
    prefer_ordered: Optional[bool] = None
) -> Optional[StreamingPredictionResult]:
    """
    Predict optimal streaming parameters (n_jobs, chunksize, buffer_size) using ML model.
    
    This function extends predict_parameters() to also predict streaming-specific
    parameters like buffer_size and ordering preference (imap vs imap_unordered).
    
    Args:
        func: Function to optimize (used for grouping related workloads)
        data_size: Number of items in the dataset
        estimated_item_time: Rough estimate of per-item execution time (seconds)
        confidence_threshold: Minimum confidence to return prediction (0-1)
        verbose: If True, print diagnostic information
        pickle_size: Average pickle size of return objects (bytes) - optional
        coefficient_of_variation: CV of execution times (0-2) - optional
        prefer_ordered: User preference for ordering (None = auto-decide)
    
    Returns:
        StreamingPredictionResult if confident enough, None if should fall back to dry-run
    
    Example:
        >>> result = predict_streaming_parameters(my_func, 10000, 0.001)
        >>> if result and result.confidence > 0.7:
        ...     print(f"Using ML prediction: n_jobs={result.n_jobs}, buffer={result.buffer_size}")
        ... else:
        ...     print("Falling back to dry-run sampling")
    """
    # First get base prediction using standard predict_parameters
    base_prediction = predict_parameters(
        func=func,
        data_size=data_size,
        estimated_item_time=estimated_item_time,
        confidence_threshold=confidence_threshold,
        verbose=verbose,
        pickle_size=pickle_size,
        coefficient_of_variation=coefficient_of_variation
    )
    
    if base_prediction is None:
        if verbose:
            print("ML Streaming Prediction: Base prediction failed, falling back to dry-run")
        return None
    
    # Calculate buffer size based on n_jobs
    # Default: n_jobs * DEFAULT_BUFFER_SIZE_MULTIPLIER for good throughput
    buffer_size = base_prediction.n_jobs * DEFAULT_BUFFER_SIZE_MULTIPLIER
    
    # Adjust buffer size based on estimated memory usage
    physical_cores = get_physical_cores()
    available_memory = get_available_memory()
    
    if pickle_size and pickle_size > 0:
        # Conservative buffer: use STREAMING_BUFFER_MEMORY_FRACTION of available memory
        max_buffer_memory = available_memory * STREAMING_BUFFER_MEMORY_FRACTION
        max_buffer_items = int(max_buffer_memory / pickle_size)
        
        # Clamp buffer size to memory constraint
        if max_buffer_items < buffer_size:
            buffer_size = max(base_prediction.n_jobs, max_buffer_items)
            if verbose:
                print(f"ML Streaming Prediction: Adjusted buffer_size to {buffer_size} "
                      f"based on memory constraints")
    
    # Determine ordering preference
    # Use unordered (imap_unordered) if user doesn't care and it's beneficial
    use_ordered = True
    if prefer_ordered is None:
        # Auto-decide: use unordered if workload is heterogeneous or data is large
        # Unordered provides better load balancing for heterogeneous workloads
        if coefficient_of_variation is not None and coefficient_of_variation > HETEROGENEOUS_CV_THRESHOLD:
            use_ordered = False
            if verbose:
                print(f"ML Streaming Prediction: Recommending imap_unordered "
                      f"for heterogeneous workload (CV={coefficient_of_variation:.2f})")
        elif data_size > LARGE_DATASET_THRESHOLD:
            # For large datasets, unordered can provide better throughput
            use_ordered = False
            if verbose:
                print(f"ML Streaming Prediction: Recommending imap_unordered "
                      f"for large dataset ({data_size} items)")
    else:
        use_ordered = prefer_ordered
        if verbose:
            method = "imap" if use_ordered else "imap_unordered"
            print(f"ML Streaming Prediction: Using user preference: {method}")
    
    # Create streaming-specific result
    streaming_result = StreamingPredictionResult(
        n_jobs=base_prediction.n_jobs,
        chunksize=base_prediction.chunksize,
        confidence=base_prediction.confidence,
        reason=f"ML prediction for streaming workload: {base_prediction.reason}",
        training_samples=base_prediction.training_samples,
        feature_match_score=base_prediction.feature_match_score,
        buffer_size=buffer_size,
        use_ordered=use_ordered
    )
    
    if verbose:
        method = "imap" if use_ordered else "imap_unordered"
        print(f"ML Streaming Prediction: Success")
        print(f"  n_jobs={streaming_result.n_jobs}, "
              f"chunksize={streaming_result.chunksize}, "
              f"buffer_size={streaming_result.buffer_size}")
        print(f"  method={method}, confidence={streaming_result.confidence:.1%}")
    
    return streaming_result


def update_model_from_execution(
    func: Callable,
    data_size: int,
    estimated_item_time: float,
    actual_n_jobs: int,
    actual_chunksize: int,
    actual_speedup: float,
    pickle_size: Optional[int] = None,
    coefficient_of_variation: Optional[float] = None,
    adaptive_chunking_enabled: Optional[bool] = None,
    adaptation_rate: Optional[float] = None,
    min_chunksize: Optional[int] = None,
    max_chunksize: Optional[int] = None,
    verbose: bool = False
) -> bool:
    """
    Update ML model with actual execution results (online learning).
    
    This function implements online learning by adding actual execution results
    to the training data, allowing the model to continuously improve without
    manual retraining.
    
    Args:
        func: The function that was executed
        data_size: Number of items processed
        estimated_item_time: Estimated per-item execution time (seconds)
        actual_n_jobs: Actual number of workers that were optimal
        actual_chunksize: Actual chunk size that was optimal
        actual_speedup: Actual speedup achieved
        pickle_size: Average pickle size of return objects (bytes)
        coefficient_of_variation: CV of execution times (0-2)
        adaptive_chunking_enabled: Whether adaptive chunking was used (Iteration 119)
        adaptation_rate: Adaptation rate if adaptive chunking was used (Iteration 119)
        min_chunksize: Minimum chunk size if adaptive chunking was used (Iteration 119)
        max_chunksize: Maximum chunk size if adaptive chunking was used (Iteration 119)
        verbose: If True, print diagnostic information
    
    Returns:
        True if successfully updated, False otherwise
    
    Example:
        >>> # After executing with optimized parameters
        >>> result = optimize(my_func, data, verbose=True)
        >>> # Execute and measure actual performance
        >>> actual_speedup = measure_actual_speedup(...)
        >>> # Update model with results
        >>> update_model_from_execution(
        ...     my_func, len(data), 0.001,
        ...     result.n_jobs, result.chunksize, actual_speedup
        ... )
    """
    try:
        # Compute function complexity
        function_complexity = _compute_function_complexity(func)
        
        # Detect system topology for hardware-aware features (Iteration 114)
        system_topology = None
        if _HAS_COST_MODEL:
            try:
                physical_cores = get_physical_cores()
                system_topology = detect_system_topology(physical_cores)
            except Exception:
                # Graceful fallback if topology detection fails
                system_topology = None
        
        # Create features for this execution
        features = WorkloadFeatures(
            data_size=data_size,
            estimated_item_time=estimated_item_time,
            physical_cores=get_physical_cores(),
            available_memory=get_available_memory(),
            start_method=get_multiprocessing_start_method(),
            pickle_size=pickle_size,
            coefficient_of_variation=coefficient_of_variation,
            function_complexity=function_complexity,
            system_topology=system_topology
        )
        
        # Capture system fingerprint for cross-system learning (Iteration 117)
        system_fingerprint = _get_current_system_fingerprint()
        
        # Save system fingerprint if not already saved
        if _load_system_fingerprint() is None:
            _save_system_fingerprint(system_fingerprint)
        
        # Create training sample from execution results
        training_sample = TrainingData(
            features=features,
            n_jobs=actual_n_jobs,
            chunksize=actual_chunksize,
            speedup=actual_speedup,
            timestamp=time.time(),
            system_fingerprint=system_fingerprint,
            adaptive_chunking_enabled=adaptive_chunking_enabled,
            adaptation_rate=adaptation_rate,
            min_chunksize=min_chunksize,
            max_chunksize=max_chunksize
        )
        
        # Save to cache in ML-specific format for training
        # This uses the same cache infrastructure but with execution results
        cache_dir = _get_ml_cache_dir()
        
        # Generate unique filename using the format constant
        func_hash = _compute_function_signature(func)
        timestamp_ms = int(time.time() * 1000)  # Milliseconds for uniqueness
        cache_file = cache_dir / ML_TRAINING_FILE_FORMAT.format(
            func_hash=func_hash,
            timestamp=timestamp_ms
        )
        
        # Prepare data for JSON serialization
        training_data = {
            'features': {
                'data_size': features.data_size,
                'estimated_item_time': features.estimated_item_time,
                'physical_cores': features.physical_cores,
                'available_memory': features.available_memory,
                'start_method': features.start_method,
                'pickle_size': pickle_size,
                'coefficient_of_variation': coefficient_of_variation,
                'function_complexity': function_complexity
            },
            'n_jobs': actual_n_jobs,
            'chunksize': actual_chunksize,
            'speedup': actual_speedup,
            'timestamp': training_sample.timestamp,
            'function_signature': func_hash,
            # Cross-system learning (Iteration 117)
            'system_fingerprint': system_fingerprint.to_dict() if system_fingerprint else None,
            # Adaptive chunking parameters (Iteration 119)
            'adaptive_chunking_enabled': adaptive_chunking_enabled,
            'adaptation_rate': adaptation_rate,
            'min_chunksize': min_chunksize,
            'max_chunksize': max_chunksize
        }
        
        # Write to file atomically
        temp_file = cache_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        temp_file.replace(cache_file)
        
        if verbose:
            print(f"✓ Online Learning: Added training sample to model")
            print(f"  n_jobs={actual_n_jobs}, chunksize={actual_chunksize}, speedup={actual_speedup:.2f}x")
            print(f"  Training data saved to: {cache_file.name}")
        
        return True
        
    except (OSError, IOError, PermissionError) as e:
        # File system errors
        if verbose:
            print(f"⚠ Online Learning: Failed to write training data: {e}")
        return False
    except (TypeError, ValueError) as e:
        # JSON serialization errors
        if verbose:
            print(f"⚠ Online Learning: Failed to serialize training data: {e}")
        return False
    except Exception as e:
        # Catch-all for unexpected errors
        if verbose:
            print(f"⚠ Online Learning: Unexpected error: {e}")
        return False


def update_model_from_streaming_execution(
    func: Callable,
    data_size: int,
    estimated_item_time: float,
    actual_n_jobs: int,
    actual_chunksize: int,
    actual_speedup: float,
    buffer_size: int,
    use_ordered: bool,
    pickle_size: Optional[int] = None,
    coefficient_of_variation: Optional[float] = None,
    verbose: bool = False
) -> bool:
    """
    Update ML model with actual streaming execution results (online learning for streaming).
    
    This function implements online learning specifically for streaming workloads,
    capturing streaming-specific parameters like buffer_size and use_ordered (imap vs imap_unordered).
    
    Args:
        func: The function that was executed in streaming mode
        data_size: Number of items processed
        estimated_item_time: Estimated per-item execution time (seconds)
        actual_n_jobs: Actual number of workers that were optimal
        actual_chunksize: Actual chunk size that was optimal
        actual_speedup: Actual speedup achieved
        buffer_size: Buffer size used for imap/imap_unordered
        use_ordered: Whether ordered (imap) was used vs unordered (imap_unordered)
        pickle_size: Average pickle size of return objects (bytes)
        coefficient_of_variation: CV of execution times (0-2)
        verbose: If True, print diagnostic information
    
    Returns:
        True if successfully updated, False otherwise
    
    Example:
        >>> # After streaming execution with optimized parameters
        >>> result = optimize_streaming(my_func, data, enable_ml_prediction=True)
        >>> # Execute and measure actual performance
        >>> actual_speedup = measure_actual_speedup(...)
        >>> # Update model with streaming results
        >>> update_model_from_streaming_execution(
        ...     my_func, len(data), 0.001,
        ...     result.n_jobs, result.chunksize, actual_speedup,
        ...     result.buffer_size, result.use_ordered
        ... )
    
    New in Iteration 115:
        This function enables streaming workloads to benefit from online learning,
        just like batch workloads. The model learns optimal buffer sizes and ordering
        preferences over time for better predictions.
    """
    try:
        # Compute function complexity
        function_complexity = _compute_function_complexity(func)
        
        # Detect system topology for hardware-aware features (Iteration 114)
        system_topology = None
        if _HAS_COST_MODEL:
            try:
                physical_cores = get_physical_cores()
                system_topology = detect_system_topology(physical_cores)
            except Exception:
                # Graceful fallback if topology detection fails
                system_topology = None
        
        # Create features for this execution
        features = WorkloadFeatures(
            data_size=data_size,
            estimated_item_time=estimated_item_time,
            physical_cores=get_physical_cores(),
            available_memory=get_available_memory(),
            start_method=get_multiprocessing_start_method(),
            pickle_size=pickle_size,
            coefficient_of_variation=coefficient_of_variation,
            function_complexity=function_complexity,
            system_topology=system_topology
        )
        
        # Create training sample from streaming execution results
        training_sample = TrainingData(
            features=features,
            n_jobs=actual_n_jobs,
            chunksize=actual_chunksize,
            speedup=actual_speedup,
            timestamp=time.time(),
            buffer_size=buffer_size,
            use_ordered=use_ordered,
            is_streaming=True
        )
        
        # Save to cache in ML-specific format for training
        cache_dir = _get_ml_cache_dir()
        
        # Generate unique filename using the format constant
        func_hash = _compute_function_signature(func)
        timestamp_ms = int(time.time() * 1000)  # Milliseconds for uniqueness
        # Use "streaming" prefix to distinguish from batch training data
        cache_file = cache_dir / f"ml_training_streaming_{func_hash}_{timestamp_ms}.json"
        
        # Prepare data for JSON serialization (includes streaming parameters)
        training_data = {
            'features': {
                'data_size': features.data_size,
                'estimated_item_time': features.estimated_item_time,
                'physical_cores': features.physical_cores,
                'available_memory': features.available_memory,
                'start_method': features.start_method,
                'pickle_size': pickle_size,
                'coefficient_of_variation': coefficient_of_variation,
                'function_complexity': function_complexity
            },
            'n_jobs': actual_n_jobs,
            'chunksize': actual_chunksize,
            'speedup': actual_speedup,
            'timestamp': training_sample.timestamp,
            'function_signature': func_hash,
            # Streaming-specific parameters (Iteration 115)
            'buffer_size': buffer_size,
            'use_ordered': use_ordered,
            'is_streaming': True
        }
        
        # Write to file atomically
        temp_file = cache_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        temp_file.replace(cache_file)
        
        if verbose:
            print(f"✓ Streaming Online Learning: Added training sample to model")
            print(f"  n_jobs={actual_n_jobs}, chunksize={actual_chunksize}, speedup={actual_speedup:.2f}x")
            print(f"  buffer_size={buffer_size}, use_ordered={use_ordered}")
            print(f"  Training data saved to: {cache_file.name}")
        
        return True
        
    except (OSError, IOError, PermissionError) as e:
        # File system errors
        if verbose:
            print(f"⚠ Streaming Online Learning: Failed to write training data: {e}")
        return False
    except (TypeError, ValueError) as e:
        # JSON serialization errors
        if verbose:
            print(f"⚠ Streaming Online Learning: Failed to serialize training data: {e}")
        return False
    except Exception as e:
        # Catch-all for unexpected errors
        if verbose:
            print(f"⚠ Streaming Online Learning: Unexpected error: {e}")
        return False


def track_prediction_accuracy(
    predicted_result: PredictionResult,
    actual_n_jobs: int,
    actual_chunksize: int,
    verbose: bool = False
) -> bool:
    """
    Track accuracy of a prediction for confidence calibration (Iteration 116).
    
    This function updates the calibration system with the accuracy of a prediction,
    enabling the system to adaptively adjust confidence thresholds over time.
    
    Call this function after:
    1. Making a prediction with predict_parameters()
    2. Running the actual optimization (dry-run or execution)
    3. Obtaining the actual optimal parameters
    
    The system will use this information to recalibrate confidence thresholds,
    making the ML vs dry-run trade-off more intelligent over time.
    
    Args:
        predicted_result: The prediction that was made
        actual_n_jobs: Actual optimal n_jobs from dry-run/execution
        actual_chunksize: Actual optimal chunksize from dry-run/execution
        verbose: If True, print diagnostic information
    
    Returns:
        True if successfully tracked, False otherwise
    
    Example:
        >>> # Make a prediction
        >>> prediction = predict_parameters(my_func, 10000, 0.001)
        >>> # Run actual optimization
        >>> result = optimize(my_func, data, enable_ml_prediction=False)
        >>> # Track accuracy for calibration
        >>> track_prediction_accuracy(
        ...     prediction, result.n_jobs, result.chunksize, verbose=True
        ... )
    """
    try:
        # Load current calibration data
        calibration = _load_calibration_data()
        
        # Calculate prediction accuracy
        n_jobs_error = abs(predicted_result.n_jobs - actual_n_jobs)
        chunksize_error = abs(predicted_result.chunksize - actual_chunksize)
        
        # Calculate relative errors
        n_jobs_relative = min(1.0, n_jobs_error / max(1, actual_n_jobs))
        chunksize_relative = min(1.0, chunksize_error / max(1, actual_chunksize))
        
        # Overall accuracy: 1.0 = perfect, 0.0 = completely wrong
        accuracy = 1.0 - ((n_jobs_relative + chunksize_relative) / 2.0)
        
        # Add to calibration data
        calibration.add_prediction_result(
            confidence=predicted_result.confidence,
            accuracy=accuracy
        )
        
        if verbose:
            print(f"Calibration: Tracked prediction accuracy {accuracy:.1%} "
                  f"(confidence was {predicted_result.confidence:.1%})")
            print(f"Calibration: n_jobs error={n_jobs_error}, chunksize error={chunksize_error}")
        
        # Recalibrate threshold if we have enough samples
        if len(calibration.predictions) >= MIN_CALIBRATION_SAMPLES:
            old_threshold = calibration.adjusted_threshold
            new_threshold = calibration.recalibrate_threshold()
            
            if verbose and abs(new_threshold - old_threshold) > 0.01:
                stats = calibration.get_calibration_stats()
                print(f"Calibration: Adjusted threshold from {old_threshold:.2f} to {new_threshold:.2f}")
                print(f"Calibration: Mean accuracy={stats['mean_accuracy']:.1%}, "
                      f"high-conf accuracy={stats['high_confidence_accuracy']:.1%}")
        
        # Save updated calibration data
        success = _save_calibration_data(calibration)
        
        if verbose and success:
            print(f"Calibration: Saved data ({len(calibration.predictions)} samples)")
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"Failed to track prediction accuracy: {e}")
        return False


def get_calibration_stats(verbose: bool = False) -> Dict[str, Any]:
    """
    Get current calibration statistics (Iteration 116).
    
    Returns information about the confidence calibration system, including
    prediction accuracy history and current threshold settings.
    
    Args:
        verbose: If True, print diagnostic information
    
    Returns:
        Dictionary with calibration statistics:
            - adjusted_threshold: Current calibrated threshold
            - baseline_threshold: Original threshold before calibration
            - mean_accuracy: Average prediction accuracy
            - high_confidence_accuracy: Accuracy when confidence >= threshold
            - sample_count: Number of calibration samples
            - last_update: Timestamp of last update
    
    Example:
        >>> stats = get_calibration_stats(verbose=True)
        >>> print(f"Current threshold: {stats['adjusted_threshold']:.2f}")
        >>> print(f"Mean accuracy: {stats['mean_accuracy']:.1%}")
    """
    try:
        calibration = _load_calibration_data()
        stats = calibration.get_calibration_stats()
        
        result = {
            'adjusted_threshold': calibration.adjusted_threshold,
            'baseline_threshold': calibration.baseline_threshold,
            'mean_accuracy': stats['mean_accuracy'],
            'high_confidence_accuracy': stats['high_confidence_accuracy'],
            'low_confidence_accuracy': stats['low_confidence_accuracy'],
            'optimal_threshold': stats['optimal_threshold'],
            'sample_count': stats['sample_count'],
            'last_update': calibration.last_update
        }
        
        if verbose:
            print(f"Calibration Statistics:")
            print(f"  Adjusted threshold: {result['adjusted_threshold']:.2f}")
            print(f"  Baseline threshold: {result['baseline_threshold']:.2f}")
            print(f"  Mean accuracy: {result['mean_accuracy']:.1%}")
            print(f"  High-confidence accuracy: {result['high_confidence_accuracy']:.1%}")
            print(f"  Sample count: {result['sample_count']}")
        
        return result
        
    except Exception:
        # Return defaults if calibration data unavailable
        return {
            'adjusted_threshold': DEFAULT_CONFIDENCE_THRESHOLD,
            'baseline_threshold': DEFAULT_CONFIDENCE_THRESHOLD,
            'mean_accuracy': 0.0,
            'high_confidence_accuracy': 0.0,
            'low_confidence_accuracy': 0.0,
            'optimal_threshold': DEFAULT_CONFIDENCE_THRESHOLD,
            'sample_count': 0,
            'last_update': 0.0
        }


def load_ml_training_data(
    enable_cross_system: bool = True,
    min_similarity: float = MIN_SYSTEM_SIMILARITY,
    verbose: bool = False
) -> List[TrainingData]:
    """
    Load training data specifically saved by online learning.
    
    This loads data from ml_training_*.json files saved by
    update_model_from_execution(), which contain actual execution results.
    
    Enhanced in Iteration 117 with cross-system learning support.
    When enable_cross_system=True, loads training data from similar systems
    and weights it based on hardware similarity.
    
    Args:
        enable_cross_system: If True, load and weight data from similar systems
        min_similarity: Minimum similarity score (0-1) to include cross-system data
        verbose: If True, print diagnostic information
    
    Returns:
        List of TrainingData samples from online learning (local + cross-system)
    """
    training_data = []
    
    # Get current system fingerprint for cross-system weighting
    current_system = None
    if enable_cross_system:
        current_system = _get_current_system_fingerprint()
        if verbose:
            print(f"Cross-System Learning: Current system: {current_system}")
    
    try:
        cache_dir = _get_ml_cache_dir()
        
        # Load ML-specific training files
        for cache_file in cache_dir.glob("ml_training_*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Extract features
                feat_dict = data.get('features', {})
                # Note: system_topology is not stored in cache files
                # Will use default values for hardware features when loading old data
                features = WorkloadFeatures(
                    data_size=feat_dict.get('data_size', 1000),
                    estimated_item_time=feat_dict.get('estimated_item_time', 0.01),
                    physical_cores=feat_dict.get('physical_cores', get_physical_cores()),
                    available_memory=feat_dict.get('available_memory', get_available_memory()),
                    start_method=feat_dict.get('start_method', get_multiprocessing_start_method()),
                    pickle_size=feat_dict.get('pickle_size'),
                    coefficient_of_variation=feat_dict.get('coefficient_of_variation'),
                    function_complexity=feat_dict.get('function_complexity'),
                    system_topology=None  # Not stored in cache, use defaults
                )
                
                # Load system fingerprint if available (Iteration 117)
                sample_system = None
                system_fingerprint_dict = data.get('system_fingerprint')
                if system_fingerprint_dict:
                    try:
                        sample_system = SystemFingerprint.from_dict(system_fingerprint_dict)
                    except (KeyError, TypeError):
                        # Old data without fingerprint or corrupted fingerprint
                        sample_system = None
                
                # Calculate sample weight based on system similarity
                weight = 1.0  # Default weight for local system data
                if enable_cross_system and current_system and sample_system:
                    # Check if this is from current system or different system
                    if sample_system.system_id != current_system.system_id:
                        # Different system - calculate similarity
                        similarity = current_system.similarity(sample_system)
                        
                        if similarity < min_similarity:
                            # System too different, skip this sample
                            if verbose:
                                print(f"Cross-System Learning: Skipping sample from "
                                      f"{sample_system} (similarity={similarity:.2f})")
                            continue
                        
                        # Apply cross-system weight based on similarity
                        weight = CROSS_SYSTEM_WEIGHT * similarity
                        
                        if verbose:
                            print(f"Cross-System Learning: Including sample from similar system "
                                  f"(similarity={similarity:.2f}, weight={weight:.2f})")
                
                # Create training sample (with streaming support from Iteration 115)
                sample = TrainingData(
                    features=features,
                    n_jobs=data['n_jobs'],
                    chunksize=data['chunksize'],
                    speedup=data.get('speedup', 1.0),
                    timestamp=data.get('timestamp', time.time()),
                    buffer_size=data.get('buffer_size'),  # Streaming parameter
                    use_ordered=data.get('use_ordered'),  # Streaming parameter
                    is_streaming=data.get('is_streaming', False),  # Streaming flag
                    system_fingerprint=sample_system,  # Cross-system learning (Iteration 117)
                    weight=weight,  # Cross-system weight (Iteration 117)
                    # Adaptive chunking parameters (Iteration 119)
                    adaptive_chunking_enabled=data.get('adaptive_chunking_enabled'),
                    adaptation_rate=data.get('adaptation_rate'),
                    min_chunksize=data.get('min_chunksize'),
                    max_chunksize=data.get('max_chunksize')
                )
                
                training_data.append(sample)
                
            except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
                # Skip corrupted or invalid files
                # Could log these in verbose mode for debugging
                if verbose:
                    print(f"Warning: Skipping corrupted training file: {cache_file.name}")
                continue
            except (OSError, IOError) as e:
                # Skip files with read errors
                continue
    
    except (OSError, IOError, PermissionError):
        # If cache directory access fails, return empty list
        # This is not a critical error - prediction will just have less data
        pass
    
    if verbose and enable_cross_system:
        local_count = sum(1 for s in training_data 
                         if s.system_fingerprint and current_system and
                         s.system_fingerprint.system_id == current_system.system_id)
        cross_system_count = len(training_data) - local_count
        print(f"Cross-System Learning: Loaded {len(training_data)} total samples "
              f"({local_count} local, {cross_system_count} cross-system)")
    
    return training_data


# Export public API
__all__ = [
    'predict_parameters',
    'predict_streaming_parameters',
    'update_model_from_execution',
    'update_model_from_streaming_execution',
    'track_prediction_accuracy',
    'get_calibration_stats',
    'load_ml_training_data',
    'PredictionResult',
    'StreamingPredictionResult',
    'CalibrationData',
    'SystemFingerprint',
    'WorkloadFeatures',
    'TrainingData',
    'SimpleLinearPredictor',
    'MIN_TRAINING_SAMPLES',
    'DEFAULT_CONFIDENCE_THRESHOLD',
    'MIN_SYSTEM_SIMILARITY',
    'CROSS_SYSTEM_WEIGHT',
    '_compute_function_complexity'
]
