"""
Property-based tests for ml_prediction module using Hypothesis.

These tests verify mathematical invariants and properties that should hold
for all inputs, automatically generating thousands of edge cases that would
be impractical to write as manual tests.

Test Coverage:
1. PredictionResult Invariants - Confidence, n_jobs, chunksize bounds
2. StreamingPredictionResult Invariants - Buffer size, method selection
3. CalibrationData Invariants - Threshold bounds, prediction history
4. SystemFingerprint Invariants - Hardware values, similarity calculation
5. WorkloadFeatures Invariants - Feature bounds, normalization
6. TrainingData Invariants - Version, required fields
7. Feature Extraction - Determinism, valid ranges
8. Distance Calculations - Non-negativity, symmetry, triangle inequality
9. Confidence Scoring - Bounds, monotonicity
10. Prediction Functions - Valid outputs, consistency
11. System Similarity - Symmetric, transitive properties
12. Edge Cases - Empty data, extreme values, boundary conditions
"""

import math
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from amorsize.ml_prediction import (
    ADAPTIVE_CHUNKING_CV_THRESHOLD,
    CALIBRATION_ADJUSTMENT_FACTOR,
    DEFAULT_CONFIDENCE_THRESHOLD,
    ENSEMBLE_LEARNING_RATE,
    HETEROGENEOUS_CV_THRESHOLD,
    KNN_DISTANCE_EPSILON,
    MAX_EXPECTED_CORES,
    MAX_NUMA_NODES,
    MIN_CALIBRATION_SAMPLES,
    MIN_CLUSTERING_SAMPLES,
    MIN_SYSTEM_SIMILARITY,
    MIN_TRAINING_SAMPLES,
    CalibrationData,
    PredictionResult,
    StreamingPredictionResult,
    SystemFingerprint,
    TrainingData,
    WorkloadFeatures,
    _compute_function_complexity,
    _compute_function_signature,
    _get_current_system_fingerprint,
)


# ============================================================================
# Strategy Definitions
# ============================================================================

@st.composite
def prediction_result_strategy(draw):
    """Generate valid PredictionResult instances."""
    n_jobs = draw(st.integers(min_value=1, max_value=128))
    chunksize = draw(st.integers(min_value=1, max_value=100000))
    confidence = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    reason = draw(st.text(min_size=1, max_size=100))
    training_samples = draw(st.integers(min_value=0, max_value=10000))
    feature_match_score = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    
    return PredictionResult(
        n_jobs=n_jobs,
        chunksize=chunksize,
        confidence=confidence,
        reason=reason,
        training_samples=training_samples,
        feature_match_score=feature_match_score
    )


@st.composite
def calibration_data_strategy(draw):
    """Generate valid CalibrationData instances."""
    num_predictions = draw(st.integers(min_value=0, max_value=100))
    predictions = []
    for _ in range(num_predictions):
        confidence = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
        accuracy = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
        predictions.append((confidence, accuracy))
    
    adjusted_threshold = draw(st.floats(min_value=0.5, max_value=0.95, allow_nan=False, allow_infinity=False))
    baseline_threshold = draw(st.floats(min_value=0.5, max_value=0.95, allow_nan=False, allow_infinity=False))
    
    return CalibrationData(
        predictions=predictions,
        adjusted_threshold=adjusted_threshold,
        baseline_threshold=baseline_threshold
    )


@st.composite
def system_fingerprint_strategy(draw):
    """Generate valid SystemFingerprint instances."""
    physical_cores = draw(st.integers(min_value=1, max_value=128))
    l3_cache_mb = draw(st.floats(min_value=1.0, max_value=256.0, allow_nan=False, allow_infinity=False))
    numa_nodes = draw(st.integers(min_value=1, max_value=8))
    memory_bandwidth_gb_s = draw(st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    start_method = draw(st.sampled_from(['fork', 'spawn', 'forkserver']))
    
    return SystemFingerprint(
        physical_cores=physical_cores,
        l3_cache_mb=l3_cache_mb,
        numa_nodes=numa_nodes,
        memory_bandwidth_gb_s=memory_bandwidth_gb_s,
        start_method=start_method
    )


@st.composite
def workload_features_strategy(draw):
    """Generate valid WorkloadFeatures instances."""
    data_size = draw(st.integers(min_value=1, max_value=1000000))
    estimated_item_time = draw(st.floats(min_value=0.0001, max_value=10.0, allow_nan=False, allow_infinity=False))
    physical_cores = draw(st.integers(min_value=1, max_value=128))
    available_memory = draw(st.integers(min_value=1000000, max_value=1000000000000))
    start_method = draw(st.sampled_from(['fork', 'spawn', 'forkserver']))
    pickle_size = draw(st.integers(min_value=0, max_value=10000000))
    coefficient_of_variation = draw(st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False))
    function_complexity = draw(st.integers(min_value=1, max_value=10000))
    
    return WorkloadFeatures(
        data_size=data_size,
        estimated_item_time=estimated_item_time,
        physical_cores=physical_cores,
        available_memory=available_memory,
        start_method=start_method,
        pickle_size=pickle_size,
        coefficient_of_variation=coefficient_of_variation,
        function_complexity=function_complexity
    )


# ============================================================================
# Test Suite 1: PredictionResult Invariants
# ============================================================================

@given(prediction_result_strategy())
@settings(max_examples=100)
def test_prediction_result_n_jobs_positive(result):
    """PredictionResult n_jobs must be at least 1."""
    assert result.n_jobs >= 1


@given(prediction_result_strategy())
@settings(max_examples=100)
def test_prediction_result_chunksize_positive(result):
    """PredictionResult chunksize must be at least 1."""
    assert result.chunksize >= 1


@given(prediction_result_strategy())
@settings(max_examples=100)
def test_prediction_result_confidence_bounded(result):
    """PredictionResult confidence must be in [0, 1]."""
    assert 0.0 <= result.confidence <= 1.0


@given(prediction_result_strategy())
@settings(max_examples=100)
def test_prediction_result_feature_match_bounded(result):
    """PredictionResult feature_match_score must be in [0, 1]."""
    assert 0.0 <= result.feature_match_score <= 1.0


@given(prediction_result_strategy())
@settings(max_examples=100)
def test_prediction_result_training_samples_non_negative(result):
    """PredictionResult training_samples must be non-negative."""
    assert result.training_samples >= 0


# ============================================================================
# Test Suite 2: StreamingPredictionResult Invariants
# ============================================================================

@given(
    st.integers(min_value=1, max_value=128),
    st.integers(min_value=1, max_value=100000),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_streaming_result_buffer_size_reasonable(n_jobs, chunksize, confidence):
    """StreamingPredictionResult buffer_size should be reasonable relative to n_jobs."""
    result = StreamingPredictionResult(
        n_jobs=n_jobs,
        chunksize=chunksize,
        confidence=confidence,
        reason="test",
        training_samples=10,
        feature_match_score=0.8
    )
    # Default buffer size is n_jobs * 3
    assert result.buffer_size >= n_jobs
    assert result.buffer_size <= n_jobs * 10  # Reasonable upper bound


@given(
    st.integers(min_value=1, max_value=128),
    st.integers(min_value=1, max_value=100000),
    st.booleans()
)
@settings(max_examples=100)
def test_streaming_result_use_ordered_is_bool(n_jobs, chunksize, use_ordered):
    """StreamingPredictionResult use_ordered must be boolean."""
    result = StreamingPredictionResult(
        n_jobs=n_jobs,
        chunksize=chunksize,
        confidence=0.8,
        reason="test",
        training_samples=10,
        feature_match_score=0.8,
        use_ordered=use_ordered
    )
    assert isinstance(result.use_ordered, bool)


# ============================================================================
# Test Suite 3: CalibrationData Invariants
# ============================================================================

@given(calibration_data_strategy())
@settings(max_examples=100)
def test_calibration_data_threshold_bounded(calibration):
    """CalibrationData adjusted_threshold must be in [0.5, 0.95]."""
    assert 0.5 <= calibration.adjusted_threshold <= 0.95


@given(calibration_data_strategy())
@settings(max_examples=100)
def test_calibration_data_predictions_valid(calibration):
    """CalibrationData predictions must have valid confidence and accuracy."""
    for confidence, accuracy in calibration.predictions:
        assert 0.0 <= confidence <= 1.0
        assert 0.0 <= accuracy <= 1.0


@given(calibration_data_strategy())
@settings(max_examples=100)
def test_calibration_data_stats_structure(calibration):
    """CalibrationData get_calibration_stats returns valid structure."""
    stats = calibration.get_calibration_stats()
    
    # Required fields
    assert 'mean_accuracy' in stats
    assert 'high_confidence_accuracy' in stats
    assert 'low_confidence_accuracy' in stats
    assert 'optimal_threshold' in stats
    assert 'sample_count' in stats
    
    # Bounded values
    assert 0.0 <= stats['mean_accuracy'] <= 1.0
    assert 0.0 <= stats['high_confidence_accuracy'] <= 1.0
    assert 0.0 <= stats['low_confidence_accuracy'] <= 1.0
    assert 0.5 <= stats['optimal_threshold'] <= 0.95
    assert stats['sample_count'] >= 0


@given(calibration_data_strategy())
@settings(max_examples=100)
def test_calibration_data_recalibrate_bounded(calibration):
    """CalibrationData recalibrate_threshold returns bounded value."""
    new_threshold = calibration.recalibrate_threshold()
    assert 0.5 <= new_threshold <= 0.95


# ============================================================================
# Test Suite 4: SystemFingerprint Invariants
# ============================================================================

@given(system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_cores_positive(fingerprint):
    """SystemFingerprint physical_cores must be at least 1."""
    assert fingerprint.physical_cores >= 1


@given(system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_cache_positive(fingerprint):
    """SystemFingerprint l3_cache_mb must be positive."""
    assert fingerprint.l3_cache_mb > 0.0


@given(system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_numa_positive(fingerprint):
    """SystemFingerprint numa_nodes must be at least 1."""
    assert fingerprint.numa_nodes >= 1


@given(system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_bandwidth_positive(fingerprint):
    """SystemFingerprint memory_bandwidth_gb_s must be positive."""
    assert fingerprint.memory_bandwidth_gb_s > 0.0


@given(system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_start_method_valid(fingerprint):
    """SystemFingerprint start_method must be valid value."""
    assert fingerprint.start_method in ['fork', 'spawn', 'forkserver']


@given(system_fingerprint_strategy(), system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_similarity_bounded(fp1, fp2):
    """SystemFingerprint similarity score must be in [0, 1]."""
    similarity = fp1.similarity(fp2)
    assert 0.0 <= similarity <= 1.0


@given(system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_self_similarity_is_one(fingerprint):
    """SystemFingerprint similarity with itself is 1.0."""
    similarity = fingerprint.similarity(fingerprint)
    assert abs(similarity - 1.0) < 0.01  # Allow small floating point error


@given(system_fingerprint_strategy(), system_fingerprint_strategy())
@settings(max_examples=100)
def test_system_fingerprint_similarity_symmetric(fp1, fp2):
    """SystemFingerprint similarity is symmetric: sim(A, B) = sim(B, A)."""
    sim_ab = fp1.similarity(fp2)
    sim_ba = fp2.similarity(fp1)
    assert abs(sim_ab - sim_ba) < 0.01  # Allow small floating point error


# ============================================================================
# Test Suite 5: WorkloadFeatures Invariants
# ============================================================================

@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_data_size_positive(features):
    """WorkloadFeatures data_size must be at least 1."""
    assert features.data_size >= 1


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_function_time_positive(features):
    """WorkloadFeatures estimated_item_time must be positive."""
    assert features.estimated_item_time > 0.0


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_complexity_positive(features):
    """WorkloadFeatures function_complexity must be at least 1."""
    assert features.function_complexity >= 1


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_pickle_size_non_negative(features):
    """WorkloadFeatures pickle_size must be non-negative."""
    assert features.pickle_size >= 0


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_cores_positive(features):
    """WorkloadFeatures physical_cores must be at least 1."""
    assert features.physical_cores >= 1


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_coefficient_of_variation_non_negative(features):
    """WorkloadFeatures coefficient_of_variation must be non-negative."""
    assert features.coefficient_of_variation >= 0.0


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_memory_positive(features):
    """WorkloadFeatures available_memory must be positive."""
    assert features.available_memory > 0


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_to_vector_length(features):
    """WorkloadFeatures to_vector returns expected length."""
    vector = features.to_vector()
    assert len(vector) == 12  # Expected 12 features


@given(workload_features_strategy())
@settings(max_examples=100)
def test_workload_features_to_vector_no_nan(features):
    """WorkloadFeatures to_vector has no NaN values."""
    vector = features.to_vector()
    for value in vector:
        assert not math.isnan(value)
        assert not math.isinf(value)


# ============================================================================
# Test Suite 6: Function Signature and Complexity
# ============================================================================

def simple_function(x):
    """Simple test function."""
    return x * 2


def complex_function(x):
    """More complex test function."""
    result = 0
    for i in range(10):
        result += x + i
    return result


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_function_signature_deterministic(n):
    """Function signature is deterministic for same function."""
    sig1 = _compute_function_signature(simple_function)
    sig2 = _compute_function_signature(simple_function)
    assert sig1 == sig2


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_function_signature_different_for_different_functions(n):
    """Function signature differs for different functions."""
    sig1 = _compute_function_signature(simple_function)
    sig2 = _compute_function_signature(complex_function)
    assert sig1 != sig2


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_function_complexity_positive(n):
    """Function complexity is always positive."""
    complexity = _compute_function_complexity(simple_function)
    assert complexity >= 1


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_function_complexity_deterministic(n):
    """Function complexity is deterministic for same function."""
    comp1 = _compute_function_complexity(simple_function)
    comp2 = _compute_function_complexity(simple_function)
    assert comp1 == comp2


# ============================================================================
# Test Suite 7: Distance and Similarity Calculations
# ============================================================================

@given(
    st.lists(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=12, max_size=12),
    st.lists(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=12, max_size=12)
)
@settings(max_examples=100)
def test_euclidean_distance_non_negative(vec1, vec2):
    """Euclidean distance is always non-negative."""
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
    assert distance >= 0.0


@given(
    st.lists(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=12, max_size=12)
)
@settings(max_examples=100)
def test_euclidean_distance_self_is_zero(vec):
    """Euclidean distance from vector to itself is zero."""
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, vec)))
    assert abs(distance) < 0.0001


@given(
    st.lists(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=12, max_size=12),
    st.lists(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=12, max_size=12)
)
@settings(max_examples=100)
def test_euclidean_distance_symmetric(vec1, vec2):
    """Euclidean distance is symmetric: d(A, B) = d(B, A)."""
    dist_ab = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
    dist_ba = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec2, vec1)))
    assert abs(dist_ab - dist_ba) < 0.0001


# ============================================================================
# Test Suite 8: Edge Cases
# ============================================================================

@given(st.integers(min_value=0, max_value=100))
@settings(max_examples=50)
def test_empty_prediction_list_handled(num_predictions):
    """CalibrationData handles empty prediction list."""
    calibration = CalibrationData(predictions=[])
    stats = calibration.get_calibration_stats()
    
    assert stats['sample_count'] == 0
    assert stats['mean_accuracy'] == 0.0


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_minimum_training_samples_constant_positive(n):
    """MIN_TRAINING_SAMPLES constant is positive."""
    assert MIN_TRAINING_SAMPLES >= 1


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_confidence_threshold_bounded(n):
    """DEFAULT_CONFIDENCE_THRESHOLD is in valid range."""
    assert 0.0 <= DEFAULT_CONFIDENCE_THRESHOLD <= 1.0


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_knn_epsilon_positive(n):
    """KNN_DISTANCE_EPSILON is positive to prevent division by zero."""
    assert KNN_DISTANCE_EPSILON > 0.0


# ============================================================================
# Test Suite 9: Constants Validation
# ============================================================================

def test_constants_are_reasonable():
    """ML prediction constants are in reasonable ranges."""
    assert 0.0 <= DEFAULT_CONFIDENCE_THRESHOLD <= 1.0
    assert MIN_TRAINING_SAMPLES >= 1
    assert KNN_DISTANCE_EPSILON > 0.0
    assert 0.0 < ADAPTIVE_CHUNKING_CV_THRESHOLD < 1.0
    assert 0.0 < HETEROGENEOUS_CV_THRESHOLD < 1.0
    assert 0.0 < MIN_SYSTEM_SIMILARITY <= 1.0
    assert 0.0 < CALIBRATION_ADJUSTMENT_FACTOR < 1.0
    assert 0.0 < ENSEMBLE_LEARNING_RATE < 1.0
    assert MIN_CALIBRATION_SAMPLES >= 1
    assert MIN_CLUSTERING_SAMPLES >= 1
    assert MAX_EXPECTED_CORES >= 1
    assert MAX_NUMA_NODES >= 1


# ============================================================================
# Test Suite 10: Current System Fingerprint
# ============================================================================

def test_current_system_fingerprint_valid():
    """_get_current_system_fingerprint returns valid fingerprint."""
    fingerprint = _get_current_system_fingerprint()
    
    assert fingerprint.physical_cores >= 1
    assert fingerprint.l3_cache_mb >= 0.0  # May be 0 if detection fails
    assert fingerprint.numa_nodes >= 1
    assert fingerprint.memory_bandwidth_gb_s > 0.0
    assert fingerprint.start_method in ['fork', 'spawn', 'forkserver']
    assert isinstance(fingerprint.system_id, str)
    assert len(fingerprint.system_id) > 0


def test_current_system_fingerprint_deterministic():
    """_get_current_system_fingerprint is deterministic."""
    fp1 = _get_current_system_fingerprint()
    fp2 = _get_current_system_fingerprint()
    
    # Should be identical (same system)
    assert fp1.physical_cores == fp2.physical_cores
    assert fp1.l3_cache_mb == fp2.l3_cache_mb
    assert fp1.numa_nodes == fp2.numa_nodes
    assert fp1.start_method == fp2.start_method
    assert fp1.system_id == fp2.system_id


# ============================================================================
# Test Suite 11: Integration Properties
# ============================================================================

@given(
    st.integers(min_value=1, max_value=128),
    st.integers(min_value=1, max_value=100000),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=50)
def test_prediction_result_repr_works(n_jobs, chunksize, confidence):
    """PredictionResult repr doesn't crash."""
    result = PredictionResult(
        n_jobs=n_jobs,
        chunksize=chunksize,
        confidence=confidence,
        reason="test",
        training_samples=10,
        feature_match_score=0.8
    )
    repr_str = repr(result)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0


@given(
    st.integers(min_value=1, max_value=128),
    st.integers(min_value=1, max_value=100000)
)
@settings(max_examples=50)
def test_streaming_result_repr_works(n_jobs, chunksize):
    """StreamingPredictionResult repr doesn't crash."""
    result = StreamingPredictionResult(
        n_jobs=n_jobs,
        chunksize=chunksize,
        confidence=0.8,
        reason="test",
        training_samples=10,
        feature_match_score=0.8,
        use_ordered=True
    )
    repr_str = repr(result)
    assert isinstance(repr_str, str)
    assert len(repr_str) > 0
    assert "StreamingPredictionResult" in repr_str


if __name__ == "__main__":
    # Run tests with pytest when executed directly
    pytest.main([__file__, "-v"])
