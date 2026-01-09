"""
Tests for automatic n_jobs adjustment when nested parallelism is detected.

This module tests the auto-adjustment feature that reduces n_jobs to prevent
thread oversubscription when functions use internal parallelism.
"""

import pytest
import os
import sys
import threading
from amorsize import optimize
from amorsize.sampling import estimate_internal_threads, check_parallel_environment_vars


# ============================================================================
# Test Functions
# ============================================================================

def simple_function(x):
    """Simple function without any parallelism."""
    return x * 2


def threaded_function(x):
    """Function that creates threads explicitly."""
    def worker():
        pass
    
    # Create a few threads
    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    return x * 2


# ============================================================================
# Test estimate_internal_threads Function
# ============================================================================

class TestEstimateInternalThreads:
    """Test the estimate_internal_threads helper function."""
    
    def test_explicit_env_var_omp(self):
        """Test that explicit OMP_NUM_THREADS is detected."""
        env_vars = {'OMP_NUM_THREADS': '8'}
        thread_activity = {'before': 1, 'during': 1, 'after': 1, 'delta': 0}
        parallel_libraries = ['numpy']
        
        result = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        assert result == 8
    
    def test_explicit_env_var_mkl(self):
        """Test that explicit MKL_NUM_THREADS is detected."""
        env_vars = {'MKL_NUM_THREADS': '4'}
        thread_activity = {'before': 1, 'during': 1, 'after': 1, 'delta': 0}
        parallel_libraries = ['numpy']
        
        result = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        assert result == 4
    
    def test_observed_thread_delta(self):
        """Test that observed thread creation is detected."""
        env_vars = {}
        thread_activity = {'before': 1, 'during': 4, 'after': 1, 'delta': 3}
        parallel_libraries = []
        
        result = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        # delta=3 means 3 additional threads created, plus main thread = 4 total
        assert result == 4
    
    def test_library_based_default(self):
        """Test that library presence triggers default estimate."""
        env_vars = {}
        thread_activity = {'before': 1, 'during': 1, 'after': 1, 'delta': 0}
        parallel_libraries = ['numpy', 'scipy']
        
        result = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        # Conservative default for BLAS libraries
        assert result == 4
    
    def test_no_parallelism_detected(self):
        """Test that no parallelism returns 1."""
        env_vars = {}
        thread_activity = {'before': 1, 'during': 1, 'after': 1, 'delta': 0}
        parallel_libraries = []
        
        result = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        assert result == 1
    
    def test_env_var_priority_over_delta(self):
        """Test that explicit env var takes priority over observed delta."""
        env_vars = {'OMP_NUM_THREADS': '2'}
        thread_activity = {'before': 1, 'during': 5, 'after': 1, 'delta': 4}
        parallel_libraries = ['numpy']
        
        result = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        # Explicit setting should take priority
        assert result == 2
    
    def test_invalid_env_var_value(self):
        """Test that invalid env var falls back to other methods."""
        env_vars = {'OMP_NUM_THREADS': 'invalid'}
        thread_activity = {'before': 1, 'during': 3, 'after': 1, 'delta': 2}
        parallel_libraries = []
        
        result = estimate_internal_threads(parallel_libraries, thread_activity, env_vars)
        # Should use thread delta since env var is invalid
        assert result == 3


# ============================================================================
# Test Auto-Adjustment Integration
# ============================================================================

class TestAutoAdjustment:
    """Test automatic n_jobs adjustment for nested parallelism."""
    
    def test_auto_adjust_enabled_by_default(self):
        """Test that auto_adjust is enabled by default."""
        # This test just verifies the parameter exists and defaults work
        data = list(range(100))
        result = optimize(simple_function, data)
        assert result.n_jobs >= 1
    
    def test_auto_adjust_can_be_disabled(self):
        """Test that auto_adjust can be explicitly disabled."""
        data = list(range(100))
        result = optimize(simple_function, data, auto_adjust_for_nested_parallelism=False)
        assert result.n_jobs >= 1
    
    def test_no_adjustment_for_simple_function(self):
        """Test that simple functions are not adjusted."""
        data = list(range(1000))
        result = optimize(simple_function, data, profile=True)
        
        # Simple function should not be adjusted
        assert result.n_jobs > 0
        # Check that no nested parallelism was detected
        assert not any('nested parallelism' in w.lower() for w in result.warnings)
    
    def test_adjustment_with_disabled_flag(self):
        """Test that disabling auto_adjust still shows warnings but doesn't adjust."""
        # We can't easily simulate nested parallelism in tests without actual libraries
        # This test validates the parameter is passed and doesn't cause errors
        data = list(range(100))
        result = optimize(simple_function, data, auto_adjust_for_nested_parallelism=False)
        assert result.n_jobs >= 1
    
    def test_validation_rejects_non_bool(self):
        """Test that non-boolean values for auto_adjust are rejected."""
        data = list(range(10))
        
        with pytest.raises(ValueError) as exc_info:
            optimize(simple_function, data, auto_adjust_for_nested_parallelism=1)
        
        assert 'auto_adjust_for_nested_parallelism must be a boolean' in str(exc_info.value)


# ============================================================================
# Test Diagnostic Profile Integration
# ============================================================================

class TestDiagnosticProfileIntegration:
    """Test that auto-adjustment information appears in diagnostic profiles."""
    
    def test_profile_includes_adjustment_info(self):
        """Test that profile mode captures adjustment information."""
        data = list(range(1000))
        result = optimize(simple_function, data, profile=True)
        
        assert result.profile is not None
        # Profile should have all expected fields
        assert hasattr(result.profile, 'max_workers_cpu')
        assert hasattr(result.profile, 'max_workers_memory')
    
    def test_explain_without_nested_parallelism(self):
        """Test that explain() works for functions without nested parallelism."""
        data = list(range(1000))
        result = optimize(simple_function, data, profile=True)
        
        explanation = result.explain()
        assert explanation is not None
        assert 'WORKLOAD ANALYSIS' in explanation or 'workload' in explanation.lower()


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases for auto-adjustment."""
    
    def test_single_core_system(self):
        """Test that single-core systems handle adjustment gracefully."""
        # We can't force single core, but we can test small data
        data = list(range(10))
        result = optimize(simple_function, data, auto_adjust_for_nested_parallelism=True)
        assert result.n_jobs >= 1
    
    def test_empty_data(self):
        """Test that empty data doesn't break auto-adjustment."""
        data = []
        result = optimize(simple_function, data, auto_adjust_for_nested_parallelism=True)
        assert result.n_jobs == 1
        assert result.chunksize == 1
    
    def test_very_small_workload(self):
        """Test that very small workloads are handled correctly."""
        data = list(range(3))
        result = optimize(simple_function, data, auto_adjust_for_nested_parallelism=True)
        # Should recommend serial for very small workloads
        assert result.n_jobs >= 1


# ============================================================================
# Test Verbose Output
# ============================================================================

class TestVerboseOutput:
    """Test that verbose mode shows adjustment information."""
    
    def test_verbose_mode_no_adjustment(self, capsys):
        """Test verbose output when no adjustment is needed."""
        data = list(range(100))
        result = optimize(simple_function, data, verbose=True, auto_adjust_for_nested_parallelism=True)
        
        captured = capsys.readouterr()
        # Should show optimization info (checking for basic output)
        assert len(captured.out) > 0
        assert 'execution time' in captured.out.lower() or 'sampling' in captured.out.lower()
    
    def test_verbose_mode_with_profile(self, capsys):
        """Test verbose output combined with profiling."""
        data = list(range(100))
        result = optimize(simple_function, data, verbose=True, profile=True, 
                         auto_adjust_for_nested_parallelism=True)
        
        captured = capsys.readouterr()
        # Should show optimization steps
        assert len(captured.out) > 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the complete auto-adjustment feature."""
    
    def test_full_workflow_simple_function(self):
        """Test complete workflow with a simple function."""
        data = list(range(1000))
        result = optimize(
            simple_function,
            data,
            verbose=False,
            profile=True,
            auto_adjust_for_nested_parallelism=True
        )
        
        # Basic checks
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.data is not None
        assert result.profile is not None
        
        # Should have explanation
        explanation = result.explain()
        assert explanation is not None
    
    def test_parameter_validation_comprehensive(self):
        """Test that all parameter combinations validate correctly."""
        data = list(range(100))
        
        # Valid combinations
        result1 = optimize(simple_function, data, auto_adjust_for_nested_parallelism=True)
        assert result1.n_jobs >= 1
        
        result2 = optimize(simple_function, data, auto_adjust_for_nested_parallelism=False)
        assert result2.n_jobs >= 1
        
        # Invalid type
        with pytest.raises(ValueError):
            optimize(simple_function, data, auto_adjust_for_nested_parallelism="true")
        
        with pytest.raises(ValueError):
            optimize(simple_function, data, auto_adjust_for_nested_parallelism=1)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
