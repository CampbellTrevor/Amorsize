"""
Tests for threading support for I/O-bound workloads.

Tests the automatic detection and use of ThreadPoolExecutor
for I/O-bound workloads instead of multiprocessing.Pool.
"""

import time
import pytest
from amorsize import optimize, execute


def io_bound_function(x):
    """I/O-bound function (<30% CPU utilization)."""
    time.sleep(0.001)  # Simulate I/O wait
    return x * 2


def cpu_bound_function(x):
    """CPU-bound function (>70% CPU utilization)."""
    result = 0
    for i in range(10000):
        result += i ** 2
    return x + result


def mixed_function(x):
    """Mixed workload (30-70% CPU utilization)."""
    time.sleep(0.0005)  # Some I/O
    result = sum(i ** 2 for i in range(1000))  # Some CPU
    return x + result


class TestThreadingDetection:
    """Test automatic threading detection for I/O-bound workloads."""
    
    def test_io_bound_uses_threading_by_default(self):
        """I/O-bound workload should use ThreadPoolExecutor by default."""
        data = list(range(50))
        result = optimize(io_bound_function, data, sample_size=5, profile=True)
        
        # Should detect I/O-bound workload
        assert result.profile.workload_type == "io_bound"
        assert result.profile.cpu_time_ratio < 0.3
        
        # Should use threading
        assert result.executor_type == "thread"
    
    def test_cpu_bound_uses_multiprocessing(self):
        """CPU-bound workload should use multiprocessing.Pool."""
        data = list(range(30))
        result = optimize(cpu_bound_function, data, sample_size=3, profile=True)
        
        # Should detect CPU-bound workload
        assert result.profile.workload_type == "cpu_bound"
        assert result.profile.cpu_time_ratio >= 0.7
        
        # Should use multiprocessing
        assert result.executor_type == "process"
    
    def test_opt_out_with_prefer_threads_false(self):
        """Can opt-out of threading with prefer_threads_for_io=False."""
        data = list(range(50))
        result = optimize(
            io_bound_function,
            data,
            sample_size=5,
            prefer_threads_for_io=False,
            profile=True
        )
        
        # Should detect I/O-bound workload
        assert result.profile.workload_type == "io_bound"
        
        # But should still use multiprocessing (opted out)
        assert result.executor_type == "process"
    
    def test_mixed_workload_uses_multiprocessing(self):
        """Mixed workloads should use multiprocessing by default."""
        data = list(range(30))
        result = optimize(mixed_function, data, sample_size=3, profile=True)
        
        # Workload type could be mixed or io_bound depending on timing
        assert result.profile.workload_type in ("mixed", "io_bound", "cpu_bound")
        
        # Mixed workloads use multiprocessing by default
        # (only pure I/O-bound gets threading)
        if result.profile.workload_type == "io_bound":
            assert result.executor_type == "thread"
        else:
            assert result.executor_type == "process"


class TestExecuteWithThreading:
    """Test execute() function with threading."""
    
    def test_execute_uses_threading_for_io_bound(self):
        """execute() should use ThreadPoolExecutor for I/O-bound tasks."""
        data = list(range(50))
        
        results, opt_result = execute(
            io_bound_function,
            data,
            sample_size=5,
            return_optimization_result=True
        )
        
        # Should detect I/O-bound and use threading
        if opt_result.n_jobs > 1:  # Only if parallelization recommended
            assert opt_result.executor_type == "thread"
        
        # Results should be correct
        assert len(results) == 50
        assert results[0] == io_bound_function(0)
        assert results[49] == io_bound_function(49)
    
    def test_execute_uses_multiprocessing_for_cpu_bound(self):
        """execute() should use multiprocessing.Pool for CPU-bound tasks."""
        data = list(range(20))
        
        results, opt_result = execute(
            cpu_bound_function,
            data,
            sample_size=3,
            return_optimization_result=True
        )
        
        # Should use multiprocessing for CPU-bound
        assert opt_result.executor_type == "process"
        
        # Results should be correct
        assert len(results) == 20
        assert results[0] == cpu_bound_function(0)
    
    def test_execute_with_prefer_threads_false(self):
        """execute() should respect prefer_threads_for_io=False."""
        data = list(range(50))
        
        results, opt_result = execute(
            io_bound_function,
            data,
            sample_size=5,
            prefer_threads_for_io=False,
            return_optimization_result=True
        )
        
        # Should use multiprocessing even for I/O-bound
        assert opt_result.executor_type == "process"
        
        # Results should still be correct
        assert len(results) == 50


class TestThreadingOptimizationResult:
    """Test OptimizationResult with executor_type field."""
    
    def test_optimization_result_has_executor_type(self):
        """OptimizationResult should have executor_type field."""
        data = list(range(50))
        result = optimize(io_bound_function, data, sample_size=5)
        
        # Should have executor_type attribute
        assert hasattr(result, 'executor_type')
        assert result.executor_type in ("thread", "process")
    
    def test_optimization_result_repr_includes_executor_type(self):
        """OptimizationResult.__repr__() should include executor_type."""
        data = list(range(50))
        result = optimize(io_bound_function, data, sample_size=5)
        
        repr_str = repr(result)
        assert "executor_type" in repr_str
        assert result.executor_type in repr_str
    
    def test_optimization_result_str_includes_executor_type(self):
        """OptimizationResult.__str__() should include executor_type."""
        data = list(range(50))
        result = optimize(io_bound_function, data, sample_size=5)
        
        str_result = str(result)
        assert "executor=" in str_result
        assert result.executor_type in str_result


class TestThreadingEdgeCases:
    """Test edge cases for threading support."""
    
    def test_serial_execution_has_executor_type(self):
        """Serial execution (n_jobs=1) should still have executor_type."""
        # Very fast function should trigger serial execution
        data = list(range(10))
        result = optimize(lambda x: x * 2, data, sample_size=3)
        
        # Should have executor_type even for serial execution
        assert hasattr(result, 'executor_type')
        assert result.executor_type in ("thread", "process")
    
    def test_empty_data_has_executor_type(self):
        """Empty data should still have executor_type."""
        data = []
        result = optimize(io_bound_function, data)
        
        # Should have executor_type
        assert hasattr(result, 'executor_type')
        assert result.executor_type in ("thread", "process")
    
    def test_generator_with_io_bound(self):
        """Generators should work with I/O-bound threading."""
        data = (x for x in range(50))
        result = optimize(io_bound_function, data, sample_size=5)
        
        # Should have executor_type
        assert hasattr(result, 'executor_type')
        
        # Reconstructed data should be usable
        assert result.data is not None


class TestThreadingIntegration:
    """Integration tests for threading support."""
    
    def test_full_workflow_io_bound(self):
        """Test complete workflow with I/O-bound function."""
        def io_task(x):
            time.sleep(0.001)
            return x ** 2
        
        data = list(range(50))
        
        # Optimize
        opt_result = optimize(io_task, data, sample_size=5, profile=True)
        
        # Should detect I/O-bound
        assert opt_result.profile.workload_type == "io_bound"
        
        # Should recommend threading if parallel
        if opt_result.n_jobs > 1:
            assert opt_result.executor_type == "thread"
        
        # Execute
        results = execute(io_task, data, sample_size=5)
        
        # Results should be correct
        assert len(results) == 50
        assert results[0] == 0
        assert results[10] == 100
    
    def test_comparison_cpu_vs_io_bound(self):
        """Compare CPU-bound vs I/O-bound executor choices."""
        data = list(range(30))
        
        # I/O-bound function
        io_result = optimize(io_bound_function, data, sample_size=5, profile=True)
        
        # CPU-bound function
        cpu_result = optimize(cpu_bound_function, data, sample_size=3, profile=True)
        
        # Should detect different workload types
        assert io_result.profile.workload_type == "io_bound"
        assert cpu_result.profile.workload_type == "cpu_bound"
        
        # Should choose different executors (if both parallelize)
        if io_result.n_jobs > 1:
            assert io_result.executor_type == "thread"
        if cpu_result.n_jobs > 1:
            assert cpu_result.executor_type == "process"


class TestThreadingBackwardCompatibility:
    """Test that threading support doesn't break existing code."""
    
    def test_existing_code_still_works(self):
        """Existing code without prefer_threads_for_io should work."""
        data = list(range(50))
        
        # Old-style call (no prefer_threads_for_io parameter)
        result = optimize(cpu_bound_function, data, sample_size=3)
        
        # Should work and have all expected fields
        assert hasattr(result, 'n_jobs')
        assert hasattr(result, 'chunksize')
        assert hasattr(result, 'executor_type')
        assert hasattr(result, 'estimated_speedup')
    
    def test_default_behavior_is_threading_enabled(self):
        """Default behavior should enable threading for I/O-bound."""
        data = list(range(50))
        result = optimize(io_bound_function, data, sample_size=5, profile=True)
        
        # Default should detect I/O-bound and use threading
        assert result.profile.workload_type == "io_bound"
        if result.n_jobs > 1:
            assert result.executor_type == "thread"


class TestThreadingValidation:
    """Test parameter validation for threading support."""
    
    def test_prefer_threads_for_io_must_be_bool(self):
        """prefer_threads_for_io must be a boolean."""
        data = list(range(10))
        
        # Should raise ValueError for non-boolean
        with pytest.raises(ValueError, match="prefer_threads_for_io must be a boolean"):
            optimize(io_bound_function, data, prefer_threads_for_io="true")
        
        with pytest.raises(ValueError, match="prefer_threads_for_io must be a boolean"):
            optimize(io_bound_function, data, prefer_threads_for_io=1)
    
    def test_prefer_threads_for_io_accepts_true(self):
        """prefer_threads_for_io=True should work."""
        data = list(range(10))
        result = optimize(io_bound_function, data, prefer_threads_for_io=True)
        assert hasattr(result, 'executor_type')
    
    def test_prefer_threads_for_io_accepts_false(self):
        """prefer_threads_for_io=False should work."""
        data = list(range(10))
        result = optimize(io_bound_function, data, prefer_threads_for_io=False)
        assert hasattr(result, 'executor_type')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
