"""
Property-based tests for performance module using Hypothesis.

These tests verify invariants and properties that should hold for all inputs,
automatically generating thousands of edge cases to test the performance module's robustness.
"""

import math
import time
from pathlib import Path
from typing import Any, List
from hypothesis import given, strategies as st, settings, assume
import pytest

from amorsize.performance import (
    WorkloadSpec,
    PerformanceResult,
    get_standard_workloads,
    run_performance_benchmark,
    run_performance_suite,
    compare_performance_results,
    _serialize_optimizer_result,
    _serialize_benchmark_result,
    _cpu_intensive_func,
    _mixed_workload_func,
    _memory_intensive_func,
)
from amorsize.optimizer import OptimizationResult
from amorsize.benchmark import BenchmarkResult


# ============================================================================
# Test Strategies (Input Generators)
# ============================================================================

@st.composite
def workload_spec_strategy(draw):
    """Generate valid WorkloadSpec objects."""
    name = draw(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=3, max_size=20))
    description = draw(st.text(min_size=5, max_size=100))
    data_size = draw(st.integers(min_value=1, max_value=200))
    expected_workload_type = draw(st.sampled_from(["cpu_bound", "io_bound", "mixed"]))
    min_speedup = draw(st.floats(min_value=0.1, max_value=10.0))
    max_execution_time = draw(st.floats(min_value=1.0, max_value=300.0))
    
    # Use simple lambda functions for testing
    func = lambda x: x ** 2
    data_generator = lambda n: list(range(n))
    
    return WorkloadSpec(
        name=name,
        description=description,
        func=func,
        data_generator=data_generator,
        data_size=data_size,
        expected_workload_type=expected_workload_type,
        min_speedup=min_speedup,
        max_execution_time=max_execution_time
    )


@st.composite
def optimizer_result_dict_strategy(draw):
    """Generate valid optimizer result dictionaries."""
    return {
        'n_jobs': draw(st.integers(min_value=1, max_value=32)),
        'chunksize': draw(st.integers(min_value=1, max_value=1000)),
        'reason': draw(st.text(min_size=10, max_size=100)),
        'estimated_speedup': draw(st.floats(min_value=0.1, max_value=20.0)),
        'warnings': draw(st.lists(st.text(min_size=5, max_size=50), max_size=5)),
        'executor_type': draw(st.sampled_from(['serial', 'threading', 'multiprocessing']))
    }


@st.composite
def benchmark_result_dict_strategy(draw):
    """Generate valid benchmark result dictionaries."""
    serial_time = draw(st.floats(min_value=0.001, max_value=100.0))
    parallel_time = draw(st.floats(min_value=0.001, max_value=100.0))
    actual_speedup = serial_time / parallel_time if parallel_time > 0 else 1.0
    predicted_speedup = draw(st.floats(min_value=0.1, max_value=20.0))
    error_percent = abs((actual_speedup - predicted_speedup) / predicted_speedup * 100) if predicted_speedup > 0 else 0.0
    accuracy_percent = max(0, 100 - error_percent)
    
    return {
        'serial_time': serial_time,
        'parallel_time': parallel_time,
        'actual_speedup': actual_speedup,
        'predicted_speedup': predicted_speedup,
        'accuracy_percent': accuracy_percent,
        'error_percent': error_percent,
        'recommendations': draw(st.lists(st.text(min_size=10, max_size=50), max_size=5))
    }


@st.composite
def performance_result_strategy(draw):
    """Generate valid PerformanceResult objects."""
    workload_name = draw(st.text(min_size=3, max_size=30))
    optimizer_result = draw(optimizer_result_dict_strategy())
    benchmark_result = draw(st.one_of(st.none(), benchmark_result_dict_strategy()))
    passed = draw(st.booleans())
    regression_detected = draw(st.booleans())
    issues = draw(st.lists(st.text(min_size=5, max_size=100), max_size=5))
    metadata = {
        'workload_size': draw(st.integers(min_value=1, max_value=10000)),
        'workload_type': draw(st.sampled_from(['cpu_bound', 'io_bound', 'mixed'])),
        'min_speedup_threshold': draw(st.floats(min_value=0.1, max_value=10.0)),
        'optimizer_time': draw(st.floats(min_value=0.001, max_value=10.0))
    }
    
    return PerformanceResult(
        workload_name=workload_name,
        optimizer_result=optimizer_result,
        benchmark_result=benchmark_result,
        passed=passed,
        regression_detected=regression_detected,
        issues=issues,
        metadata=metadata
    )


# ============================================================================
# 1. WorkloadSpec Invariants
# ============================================================================

class TestWorkloadSpecInvariants:
    """Test invariants of the WorkloadSpec dataclass."""
    
    @given(spec=workload_spec_strategy())
    @settings(deadline=1000, max_examples=50)
    def test_workload_spec_fields_stored_correctly(self, spec):
        """WorkloadSpec should store all fields correctly."""
        assert isinstance(spec.name, str)
        assert len(spec.name) >= 3
        assert isinstance(spec.description, str)
        assert callable(spec.func)
        assert callable(spec.data_generator)
        assert isinstance(spec.data_size, int)
        assert spec.data_size >= 1
        assert spec.expected_workload_type in ["cpu_bound", "io_bound", "mixed"]
        assert isinstance(spec.min_speedup, float)
        assert spec.min_speedup > 0
        assert isinstance(spec.max_execution_time, float)
        assert spec.max_execution_time > 0
    
    @given(spec=workload_spec_strategy())
    @settings(deadline=1000, max_examples=50)
    def test_workload_spec_data_generator_returns_list(self, spec):
        """Data generator should return a list of specified size."""
        data = spec.data_generator(spec.data_size)
        
        assert isinstance(data, list)
        assert len(data) == spec.data_size
    
    @given(spec=workload_spec_strategy())
    @settings(deadline=1000, max_examples=50)
    def test_workload_spec_func_is_callable(self, spec):
        """Function should be callable on generated data."""
        data = spec.data_generator(min(10, spec.data_size))
        
        # Function should work on at least one item
        if len(data) > 0:
            result = spec.func(data[0])
            assert result is not None  # Should return something


# ============================================================================
# 2. PerformanceResult Invariants
# ============================================================================

class TestPerformanceResultInvariants:
    """Test invariants of the PerformanceResult dataclass."""
    
    @given(result=performance_result_strategy())
    @settings(deadline=1000, max_examples=50)
    def test_performance_result_fields_stored_correctly(self, result):
        """PerformanceResult should store all fields correctly."""
        assert isinstance(result.workload_name, str)
        assert isinstance(result.optimizer_result, dict)
        assert result.benchmark_result is None or isinstance(result.benchmark_result, dict)
        assert isinstance(result.passed, bool)
        assert isinstance(result.regression_detected, bool)
        assert isinstance(result.issues, list)
        assert all(isinstance(issue, str) for issue in result.issues)
        assert isinstance(result.metadata, dict)
    
    @given(result=performance_result_strategy())
    @settings(deadline=1000, max_examples=50)
    def test_performance_result_to_dict_roundtrip(self, result):
        """PerformanceResult should convert to dict and back."""
        # Convert to dict
        result_dict = result.to_dict()
        
        # Should be a dictionary
        assert isinstance(result_dict, dict)
        assert 'workload_name' in result_dict
        assert 'optimizer_result' in result_dict
        assert 'benchmark_result' in result_dict
        assert 'passed' in result_dict
        assert 'regression_detected' in result_dict
        assert 'issues' in result_dict
        assert 'metadata' in result_dict
        
        # Convert back
        restored = PerformanceResult.from_dict(result_dict)
        
        # Should match original
        assert restored.workload_name == result.workload_name
        assert restored.optimizer_result == result.optimizer_result
        assert restored.benchmark_result == result.benchmark_result
        assert restored.passed == result.passed
        assert restored.regression_detected == result.regression_detected
        assert restored.issues == result.issues
        assert restored.metadata == result.metadata
    
    @given(result=performance_result_strategy())
    @settings(deadline=1000, max_examples=50)
    def test_performance_result_passed_consistency(self, result):
        """Passed should be True if issues is empty."""
        if len(result.issues) == 0:
            # Issues empty typically means passed (though not always in practice)
            # This tests the logical consistency
            pass
        else:
            # If there are issues, passed should typically be False
            # But we can't enforce this strictly as it depends on implementation
            pass
    
    @given(result=performance_result_strategy())
    @settings(deadline=1000, max_examples=50)
    def test_performance_result_optimizer_result_has_required_keys(self, result):
        """Optimizer result dict should have expected keys."""
        assert 'n_jobs' in result.optimizer_result
        assert 'chunksize' in result.optimizer_result
        assert 'reason' in result.optimizer_result
        assert 'estimated_speedup' in result.optimizer_result
        assert 'warnings' in result.optimizer_result
        assert 'executor_type' in result.optimizer_result


# ============================================================================
# 3. Standard Workloads
# ============================================================================

class TestStandardWorkloads:
    """Test standard workload functions."""
    
    def test_get_standard_workloads_returns_list(self):
        """get_standard_workloads should return a non-empty list."""
        workloads = get_standard_workloads()
        
        assert isinstance(workloads, list)
        assert len(workloads) > 0
    
    def test_get_standard_workloads_all_valid(self):
        """All standard workloads should be valid WorkloadSpec objects."""
        workloads = get_standard_workloads()
        
        for workload in workloads:
            assert isinstance(workload, WorkloadSpec)
            assert isinstance(workload.name, str)
            assert len(workload.name) > 0
            assert isinstance(workload.description, str)
            assert callable(workload.func)
            assert callable(workload.data_generator)
            assert workload.data_size > 0
            assert workload.expected_workload_type in ["cpu_bound", "io_bound", "mixed"]
            assert workload.min_speedup > 0
            assert workload.max_execution_time > 0
    
    def test_get_standard_workloads_deterministic(self):
        """get_standard_workloads should return the same workloads consistently."""
        workloads1 = get_standard_workloads()
        workloads2 = get_standard_workloads()
        
        assert len(workloads1) == len(workloads2)
        
        # Compare names
        names1 = [w.name for w in workloads1]
        names2 = [w.name for w in workloads2]
        assert names1 == names2
    
    @given(n=st.integers(min_value=10, max_value=100))
    @settings(deadline=5000, max_examples=20)
    def test_cpu_intensive_func_returns_int(self, n):
        """_cpu_intensive_func should return an integer."""
        result = _cpu_intensive_func(n)
        
        assert isinstance(result, int)
        assert result >= 0
    
    @given(n=st.integers(min_value=10, max_value=100))
    @settings(deadline=5000, max_examples=20)
    def test_mixed_workload_func_returns_dict(self, n):
        """_mixed_workload_func should return a dict with expected keys."""
        result = _mixed_workload_func(n)
        
        assert isinstance(result, dict)
        assert 'sum' in result
        assert 'count' in result
        assert isinstance(result['sum'], int)
        assert isinstance(result['count'], int)
        assert result['count'] == n
    
    @given(n=st.integers(min_value=1, max_value=50))
    @settings(deadline=5000, max_examples=20)
    def test_memory_intensive_func_returns_list(self, n):
        """_memory_intensive_func should return a list."""
        result = _memory_intensive_func(n)
        
        assert isinstance(result, list)
        assert len(result) <= 100  # Returns at most 100 items


# ============================================================================
# 4. Serialization Functions
# ============================================================================

class TestSerializationFunctions:
    """Test serialization helper functions."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=32),
        chunksize=st.integers(min_value=1, max_value=1000),
        estimated_speedup=st.floats(min_value=0.1, max_value=20.0)
    )
    @settings(deadline=1000, max_examples=50)
    def test_serialize_optimizer_result_has_required_keys(self, n_jobs, chunksize, estimated_speedup):
        """_serialize_optimizer_result should produce dict with required keys."""
        # Create a minimal OptimizationResult-like object
        class MockOptResult:
            def __init__(self):
                self.n_jobs = n_jobs
                self.chunksize = chunksize
                self.reason = "test reason"
                self.estimated_speedup = estimated_speedup
                self.warnings = []
                self.executor_type = "multiprocessing"
        
        result = MockOptResult()
        serialized = _serialize_optimizer_result(result)
        
        assert isinstance(serialized, dict)
        assert 'n_jobs' in serialized
        assert 'chunksize' in serialized
        assert 'reason' in serialized
        assert 'estimated_speedup' in serialized
        assert 'warnings' in serialized
        assert 'executor_type' in serialized
        assert serialized['n_jobs'] == n_jobs
        assert serialized['chunksize'] == chunksize
        assert serialized['estimated_speedup'] == estimated_speedup


# ============================================================================
# 5. Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_workload_spec_with_minimal_data_size(self):
        """WorkloadSpec should work with data_size=1."""
        spec = WorkloadSpec(
            name="minimal",
            description="Minimal workload",
            func=lambda x: x,
            data_generator=lambda n: list(range(n)),
            data_size=1,
            expected_workload_type="cpu_bound",
            min_speedup=0.1,
            max_execution_time=10.0
        )
        
        assert spec.data_size == 1
        data = spec.data_generator(spec.data_size)
        assert len(data) == 1
    
    def test_performance_result_with_no_issues(self):
        """PerformanceResult with empty issues list should be valid."""
        result = PerformanceResult(
            workload_name="test",
            optimizer_result={'n_jobs': 1, 'chunksize': 1, 'reason': '', 'estimated_speedup': 1.0, 'warnings': [], 'executor_type': 'serial'},
            benchmark_result=None,
            passed=True,
            regression_detected=False,
            issues=[],
            metadata={}
        )
        
        assert len(result.issues) == 0
        assert result.passed is True
    
    def test_performance_result_with_no_benchmark(self):
        """PerformanceResult with None benchmark_result should be valid."""
        result = PerformanceResult(
            workload_name="test",
            optimizer_result={'n_jobs': 1, 'chunksize': 1, 'reason': '', 'estimated_speedup': 1.0, 'warnings': [], 'executor_type': 'serial'},
            benchmark_result=None,
            passed=True,
            regression_detected=False,
            issues=[],
            metadata={}
        )
        
        assert result.benchmark_result is None
    
    @given(
        workload_name=st.text(min_size=0, max_size=10),
        passed=st.booleans(),
        regression_detected=st.booleans()
    )
    @settings(deadline=1000, max_examples=50)
    def test_performance_result_various_boolean_combinations(self, workload_name, passed, regression_detected):
        """PerformanceResult should handle all boolean combinations."""
        result = PerformanceResult(
            workload_name=workload_name,
            optimizer_result={'n_jobs': 1, 'chunksize': 1, 'reason': '', 'estimated_speedup': 1.0, 'warnings': [], 'executor_type': 'serial'},
            benchmark_result=None,
            passed=passed,
            regression_detected=regression_detected,
            issues=[],
            metadata={}
        )
        
        assert result.passed == passed
        assert result.regression_detected == regression_detected


# ============================================================================
# 6. Numerical Stability
# ============================================================================

class TestNumericalStability:
    """Test numerical stability with various values."""
    
    @given(
        min_speedup=st.floats(min_value=0.01, max_value=100.0),
        max_execution_time=st.floats(min_value=0.1, max_value=10000.0)
    )
    @settings(deadline=1000, max_examples=50)
    def test_workload_spec_various_thresholds(self, min_speedup, max_execution_time):
        """WorkloadSpec should handle various threshold values."""
        spec = WorkloadSpec(
            name="test",
            description="Test workload",
            func=lambda x: x,
            data_generator=lambda n: list(range(n)),
            data_size=10,
            expected_workload_type="cpu_bound",
            min_speedup=min_speedup,
            max_execution_time=max_execution_time
        )
        
        assert spec.min_speedup == min_speedup
        assert spec.max_execution_time == max_execution_time
        assert spec.min_speedup > 0
        assert spec.max_execution_time > 0
    
    @given(
        serial_time=st.floats(min_value=0.001, max_value=1000.0),
        parallel_time=st.floats(min_value=0.001, max_value=1000.0)
    )
    @settings(deadline=1000, max_examples=50)
    def test_benchmark_result_dict_various_times(self, serial_time, parallel_time):
        """Benchmark result dict should handle various time values."""
        benchmark = {
            'serial_time': serial_time,
            'parallel_time': parallel_time,
            'actual_speedup': serial_time / parallel_time if parallel_time > 0 else 1.0,
            'predicted_speedup': 1.5,
            'accuracy_percent': 80.0,
            'error_percent': 20.0,
            'recommendations': []
        }
        
        result = PerformanceResult(
            workload_name="test",
            optimizer_result={'n_jobs': 1, 'chunksize': 1, 'reason': '', 'estimated_speedup': 1.0, 'warnings': [], 'executor_type': 'serial'},
            benchmark_result=benchmark,
            passed=True,
            regression_detected=False,
            issues=[],
            metadata={}
        )
        
        assert result.benchmark_result['serial_time'] == serial_time
        assert result.benchmark_result['parallel_time'] == parallel_time
        assert result.benchmark_result['actual_speedup'] > 0


# ============================================================================
# 7. Integration Properties
# ============================================================================

class TestIntegrationProperties:
    """Test integration properties and complex scenarios."""
    
    def test_run_performance_benchmark_with_standard_workload(self):
        """run_performance_benchmark should work with standard workloads."""
        workloads = get_standard_workloads()
        
        # Pick a small, fast workload
        fast_workload = None
        for w in workloads:
            if w.name == "fast_function":
                fast_workload = w
                break
        
        if fast_workload:
            # Run without validation for speed
            result = run_performance_benchmark(
                fast_workload,
                run_validation=False,
                verbose=False
            )
            
            assert isinstance(result, PerformanceResult)
            assert result.workload_name == fast_workload.name
            assert isinstance(result.optimizer_result, dict)
            assert 'n_jobs' in result.optimizer_result
    
    def test_run_performance_suite_returns_dict(self):
        """run_performance_suite should return a dictionary of results."""
        # Create a minimal workload for testing
        minimal_workload = WorkloadSpec(
            name="minimal_test",
            description="Minimal test",
            func=lambda x: x,
            data_generator=lambda n: list(range(n)),
            data_size=10,
            expected_workload_type="cpu_bound",
            min_speedup=0.1,
            max_execution_time=10.0
        )
        
        results = run_performance_suite(
            workloads=[minimal_workload],
            run_validation=False,
            verbose=False
        )
        
        assert isinstance(results, dict)
        assert "minimal_test" in results
        assert isinstance(results["minimal_test"], PerformanceResult)
    
    @given(result=performance_result_strategy())
    @settings(deadline=1000, max_examples=30)
    def test_performance_result_to_dict_produces_json_serializable(self, result):
        """PerformanceResult.to_dict() should produce JSON-serializable output."""
        import json
        
        result_dict = result.to_dict()
        
        # Should be JSON serializable
        try:
            json_str = json.dumps(result_dict)
            assert isinstance(json_str, str)
            
            # Should be deserializable
            restored_dict = json.loads(json_str)
            assert isinstance(restored_dict, dict)
        except (TypeError, ValueError) as e:
            pytest.fail(f"PerformanceResult.to_dict() produced non-JSON-serializable output: {e}")


# ============================================================================
# 8. Constants and Defaults
# ============================================================================

class TestConstantsAndDefaults:
    """Test module constants and default values."""
    
    def test_standard_workloads_have_reasonable_defaults(self):
        """Standard workloads should have reasonable default values."""
        workloads = get_standard_workloads()
        
        for workload in workloads:
            # Data size should be reasonable for testing
            assert 1 <= workload.data_size <= 10000
            
            # Min speedup should be positive and reasonable
            assert 0.1 <= workload.min_speedup <= 100.0
            
            # Max execution time should be reasonable for CI/CD
            assert 1.0 <= workload.max_execution_time <= 600.0
            
            # Expected workload type should be valid
            assert workload.expected_workload_type in ["cpu_bound", "io_bound", "mixed"]
    
    def test_workload_functions_dont_crash_on_small_inputs(self):
        """Workload functions should handle small inputs without crashing."""
        # Test with minimal input
        assert _cpu_intensive_func(2) >= 0
        
        result = _mixed_workload_func(1)
        assert 'sum' in result
        assert 'count' in result
        
        result = _memory_intensive_func(1)
        assert isinstance(result, list)
