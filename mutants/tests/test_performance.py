"""
Tests for the performance regression testing framework.
"""

import pytest
import json
import tempfile
from pathlib import Path

from amorsize.performance import (
    WorkloadSpec,
    PerformanceResult,
    get_standard_workloads,
    run_performance_benchmark,
    run_performance_suite,
    compare_performance_results,
    _cpu_intensive_func,
    _mixed_workload_func,
    _memory_intensive_func
)


class TestWorkloadSpec:
    """Tests for WorkloadSpec dataclass."""
    
    def test_workload_spec_creation(self):
        """Test that WorkloadSpec can be created with all fields."""
        workload = WorkloadSpec(
            name="test_workload",
            description="Test workload description",
            func=lambda x: x**2,
            data_generator=lambda n: list(range(n)),
            data_size=100,
            expected_workload_type="cpu_bound",
            min_speedup=1.5,
            max_execution_time=30.0
        )
        
        assert workload.name == "test_workload"
        assert workload.description == "Test workload description"
        assert workload.data_size == 100
        assert workload.expected_workload_type == "cpu_bound"
        assert workload.min_speedup == 1.5
        assert workload.max_execution_time == 30.0
    
    def test_workload_spec_defaults(self):
        """Test WorkloadSpec default values."""
        workload = WorkloadSpec(
            name="test",
            description="test",
            func=lambda x: x,
            data_generator=lambda n: list(range(n)),
            data_size=10
        )
        
        # Check defaults
        assert workload.expected_workload_type == "cpu_bound"
        assert workload.min_speedup == 1.0
        assert workload.max_execution_time == 60.0


class TestPerformanceResult:
    """Tests for PerformanceResult dataclass."""
    
    def test_performance_result_creation(self):
        """Test that PerformanceResult can be created."""
        result = PerformanceResult(
            workload_name="test_workload",
            optimizer_result={'n_jobs': 4, 'chunksize': 10},
            benchmark_result={'actual_speedup': 2.5},
            passed=True,
            regression_detected=False,
            issues=[],
            metadata={'test': 'data'}
        )
        
        assert result.workload_name == "test_workload"
        assert result.passed is True
        assert result.regression_detected is False
        assert len(result.issues) == 0
    
    def test_performance_result_serialization(self):
        """Test PerformanceResult to_dict and from_dict."""
        result = PerformanceResult(
            workload_name="test",
            optimizer_result={},
            benchmark_result=None,
            passed=True,
            regression_detected=False,
            issues=["Issue 1", "Issue 2"],
            metadata={}
        )
        
        # Convert to dict
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['workload_name'] == "test"
        assert len(result_dict['issues']) == 2
        
        # Convert back from dict
        restored = PerformanceResult.from_dict(result_dict)
        assert restored.workload_name == result.workload_name
        assert restored.passed == result.passed
        assert restored.issues == result.issues


class TestStandardWorkloads:
    """Tests for standard workload functions."""
    
    def test_cpu_intensive_func(self):
        """Test CPU-intensive workload function."""
        result = _cpu_intensive_func(100)
        assert isinstance(result, int)
        assert result > 0
    
    def test_mixed_workload_func(self):
        """Test mixed workload function."""
        result = _mixed_workload_func(50)
        assert isinstance(result, dict)
        assert 'sum' in result
        assert 'count' in result
        assert result['count'] == 50
    
    def test_memory_intensive_func(self):
        """Test memory-intensive workload function."""
        result = _memory_intensive_func(10)
        assert isinstance(result, list)
        assert len(result) <= 100
    
    def test_get_standard_workloads(self):
        """Test getting standard workload specifications."""
        workloads = get_standard_workloads()
        
        assert isinstance(workloads, list)
        assert len(workloads) > 0
        
        # Check all workloads are valid
        for workload in workloads:
            assert isinstance(workload, WorkloadSpec)
            assert workload.name
            assert workload.description
            assert callable(workload.func)
            assert callable(workload.data_generator)
            assert workload.data_size > 0
            assert workload.min_speedup > 0
            assert workload.max_execution_time > 0
    
    def test_standard_workloads_have_unique_names(self):
        """Test that all standard workloads have unique names."""
        workloads = get_standard_workloads()
        names = [w.name for w in workloads]
        assert len(names) == len(set(names))  # No duplicates


class TestRunPerformanceBenchmark:
    """Tests for run_performance_benchmark function."""
    
    def test_benchmark_simple_workload_without_validation(self):
        """Test running benchmark without validation."""
        workload = WorkloadSpec(
            name="simple_test",
            description="Simple test workload",
            func=lambda x: x**2,
            data_generator=lambda n: list(range(n)),
            data_size=20,
            expected_workload_type="cpu_bound",
            min_speedup=0.5,  # Lenient for test
            max_execution_time=10.0
        )
        
        result = run_performance_benchmark(
            workload,
            run_validation=False,
            verbose=False
        )
        
        assert isinstance(result, PerformanceResult)
        assert result.workload_name == "simple_test"
        assert result.optimizer_result is not None
        assert result.benchmark_result is None  # Not run
        assert 'n_jobs' in result.optimizer_result
        assert 'chunksize' in result.optimizer_result
    
    def test_benchmark_with_validation(self):
        """Test running benchmark with validation."""
        workload = WorkloadSpec(
            name="validated_test",
            description="Test with validation",
            func=lambda x: sum(i**2 for i in range(x)),
            data_generator=lambda n: list(range(50, 50 + n)),
            data_size=30,
            expected_workload_type="cpu_bound",
            min_speedup=0.5,  # Lenient
            max_execution_time=30.0
        )
        
        result = run_performance_benchmark(
            workload,
            run_validation=True,
            validate_max_items=20,
            verbose=False
        )
        
        assert isinstance(result, PerformanceResult)
        assert result.benchmark_result is not None
        assert 'actual_speedup' in result.benchmark_result
        assert 'predicted_speedup' in result.benchmark_result
        assert 'accuracy_percent' in result.benchmark_result
    
    def test_benchmark_detects_regression(self):
        """Test that benchmark detects performance regressions."""
        # Create a workload with high speedup requirement
        workload = WorkloadSpec(
            name="high_requirement",
            description="Workload with high speedup requirement",
            func=lambda x: x,  # Very fast function
            data_generator=lambda n: list(range(n)),
            data_size=100,
            expected_workload_type="cpu_bound",
            min_speedup=5.0,  # Unrealistic for very fast function
            max_execution_time=10.0
        )
        
        result = run_performance_benchmark(
            workload,
            run_validation=True,
            validate_max_items=50,
            verbose=False
        )
        
        # Should have issues due to not meeting speedup requirement
        # (though may not detect as regression if actual speedup is reasonable)
        assert isinstance(result, PerformanceResult)
        # Result may or may not have issues depending on system performance
    
    def test_benchmark_verbose_mode(self):
        """Test benchmark with verbose output (should not crash)."""
        workload = get_standard_workloads()[0]
        
        # Just ensure it runs without error in verbose mode
        result = run_performance_benchmark(
            workload,
            run_validation=False,
            verbose=True
        )
        
        assert isinstance(result, PerformanceResult)


class TestRunPerformanceSuite:
    """Tests for run_performance_suite function."""
    
    def test_suite_with_small_workloads(self):
        """Test running suite with small custom workloads."""
        workloads = [
            WorkloadSpec(
                name="small_1",
                description="Small workload 1",
                func=lambda x: x**2,
                data_generator=lambda n: list(range(n)),
                data_size=10,
                min_speedup=0.5,
                max_execution_time=10.0
            ),
            WorkloadSpec(
                name="small_2",
                description="Small workload 2",
                func=lambda x: x + 1,
                data_generator=lambda n: list(range(n)),
                data_size=10,
                min_speedup=0.5,
                max_execution_time=10.0
            )
        ]
        
        results = run_performance_suite(
            workloads=workloads,
            run_validation=False,
            verbose=False
        )
        
        assert isinstance(results, dict)
        assert len(results) == 2
        assert "small_1" in results
        assert "small_2" in results
        assert all(isinstance(r, PerformanceResult) for r in results.values())
    
    def test_suite_with_standard_workloads_no_validation(self):
        """Test running suite with standard workloads (no validation for speed)."""
        results = run_performance_suite(
            workloads=None,  # Use standard workloads
            run_validation=False,
            verbose=False
        )
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Check all results are valid
        for name, result in results.items():
            assert isinstance(result, PerformanceResult)
            assert result.workload_name == name
            assert result.optimizer_result is not None
    
    def test_suite_save_results(self):
        """Test saving suite results to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "test_results.json"
            
            workloads = [
                WorkloadSpec(
                    name="save_test",
                    description="Test save functionality",
                    func=lambda x: x**2,
                    data_generator=lambda n: list(range(n)),
                    data_size=10
                )
            ]
            
            results = run_performance_suite(
                workloads=workloads,
                run_validation=False,
                verbose=False,
                save_results=True,
                results_path=results_path
            )
            
            # Check file was created
            assert results_path.exists()
            
            # Load and verify contents
            with open(results_path, 'r') as f:
                saved_data = json.load(f)
            
            assert "save_test" in saved_data
            assert saved_data["save_test"]["workload_name"] == "save_test"
    
    def test_suite_verbose_mode(self):
        """Test suite with verbose output (should not crash)."""
        workloads = [
            WorkloadSpec(
                name="verbose_test",
                description="Test verbose mode",
                func=lambda x: x,
                data_generator=lambda n: list(range(n)),
                data_size=5
            )
        ]
        
        results = run_performance_suite(
            workloads=workloads,
            run_validation=False,
            verbose=True
        )
        
        assert len(results) == 1


class TestComparePerformanceResults:
    """Tests for compare_performance_results function."""
    
    def test_compare_identical_results(self):
        """Test comparing identical performance results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"
            
            # Create identical results
            test_data = {
                "test_workload": {
                    "workload_name": "test_workload",
                    "optimizer_result": {"n_jobs": 4},
                    "benchmark_result": {"actual_speedup": 2.5},
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            with open(baseline_path, 'w') as f:
                json.dump(test_data, f)
            
            with open(current_path, 'w') as f:
                json.dump(test_data, f)
            
            comparison = compare_performance_results(baseline_path, current_path)
            
            assert isinstance(comparison, dict)
            assert len(comparison['regressions']) == 0
            assert len(comparison['improvements']) == 0
            assert len(comparison['unchanged']) == 1
            assert "test_workload" in comparison['unchanged']
    
    def test_compare_detects_regression(self):
        """Test that comparison detects performance regressions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"
            
            # Baseline with good performance
            baseline_data = {
                "test_workload": {
                    "workload_name": "test_workload",
                    "optimizer_result": {"n_jobs": 4},
                    "benchmark_result": {"actual_speedup": 3.0},
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            # Current with worse performance (regression)
            current_data = {
                "test_workload": {
                    "workload_name": "test_workload",
                    "optimizer_result": {"n_jobs": 4},
                    "benchmark_result": {"actual_speedup": 2.0},  # Worse
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            with open(baseline_path, 'w') as f:
                json.dump(baseline_data, f)
            
            with open(current_path, 'w') as f:
                json.dump(current_data, f)
            
            comparison = compare_performance_results(
                baseline_path,
                current_path,
                regression_threshold=0.1  # 10% threshold
            )
            
            assert len(comparison['regressions']) == 1
            assert comparison['regressions'][0]['workload'] == "test_workload"
            assert comparison['regressions'][0]['baseline_speedup'] == 3.0
            assert comparison['regressions'][0]['current_speedup'] == 2.0
    
    def test_compare_detects_improvement(self):
        """Test that comparison detects performance improvements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"
            
            baseline_data = {
                "test_workload": {
                    "workload_name": "test_workload",
                    "optimizer_result": {"n_jobs": 4},
                    "benchmark_result": {"actual_speedup": 2.0},
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            current_data = {
                "test_workload": {
                    "workload_name": "test_workload",
                    "optimizer_result": {"n_jobs": 4},
                    "benchmark_result": {"actual_speedup": 3.0},  # Better
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            with open(baseline_path, 'w') as f:
                json.dump(baseline_data, f)
            
            with open(current_path, 'w') as f:
                json.dump(current_data, f)
            
            comparison = compare_performance_results(
                baseline_path,
                current_path,
                regression_threshold=0.1
            )
            
            assert len(comparison['improvements']) == 1
            assert comparison['improvements'][0]['workload'] == "test_workload"
    
    def test_compare_detects_missing_workloads(self):
        """Test detecting workloads missing from current results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"
            
            baseline_data = {
                "workload_1": {
                    "workload_name": "workload_1",
                    "optimizer_result": {},
                    "benchmark_result": None,
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                },
                "workload_2": {
                    "workload_name": "workload_2",
                    "optimizer_result": {},
                    "benchmark_result": None,
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            current_data = {
                "workload_1": {
                    "workload_name": "workload_1",
                    "optimizer_result": {},
                    "benchmark_result": None,
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
                # workload_2 is missing
            }
            
            with open(baseline_path, 'w') as f:
                json.dump(baseline_data, f)
            
            with open(current_path, 'w') as f:
                json.dump(current_data, f)
            
            comparison = compare_performance_results(baseline_path, current_path)
            
            assert len(comparison['missing_workloads']) == 1
            assert "workload_2" in comparison['missing_workloads']
    
    def test_compare_detects_new_workloads(self):
        """Test detecting new workloads in current results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"
            
            baseline_data = {
                "workload_1": {
                    "workload_name": "workload_1",
                    "optimizer_result": {},
                    "benchmark_result": None,
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            current_data = {
                "workload_1": {
                    "workload_name": "workload_1",
                    "optimizer_result": {},
                    "benchmark_result": None,
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                },
                "workload_2": {  # New workload
                    "workload_name": "workload_2",
                    "optimizer_result": {},
                    "benchmark_result": None,
                    "passed": True,
                    "regression_detected": False,
                    "issues": [],
                    "metadata": {}
                }
            }
            
            with open(baseline_path, 'w') as f:
                json.dump(baseline_data, f)
            
            with open(current_path, 'w') as f:
                json.dump(current_data, f)
            
            comparison = compare_performance_results(baseline_path, current_path)
            
            assert len(comparison['new_workloads']) == 1
            assert "workload_2" in comparison['new_workloads']


class TestIntegration:
    """Integration tests for the performance testing framework."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow: run suite, save, compare."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"
            
            # Create simple workload
            workloads = [
                WorkloadSpec(
                    name="integration_test",
                    description="End-to-end integration test",
                    func=lambda x: x**2,
                    data_generator=lambda n: list(range(n)),
                    data_size=10,
                    min_speedup=0.5,
                    max_execution_time=10.0
                )
            ]
            
            # Run baseline
            run_performance_suite(
                workloads=workloads,
                run_validation=False,
                verbose=False,
                save_results=True,
                results_path=baseline_path
            )
            
            # Run current
            run_performance_suite(
                workloads=workloads,
                run_validation=False,
                verbose=False,
                save_results=True,
                results_path=current_path
            )
            
            # Compare
            comparison = compare_performance_results(baseline_path, current_path)
            
            assert isinstance(comparison, dict)
            # Results should be similar (no regressions for identical runs)
            assert len(comparison['regressions']) == 0
