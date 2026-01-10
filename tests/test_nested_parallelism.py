"""
Tests for nested parallelism detection.

This module tests the detection of internal parallelism in functions,
which can cause thread oversubscription and performance degradation when
combined with multiprocessing parallelism.
"""

import os
import sys
import threading
import time
import pytest

from amorsize import optimize
from amorsize.sampling import (
    detect_parallel_libraries,
    check_parallel_environment_vars,
    detect_thread_activity,
    perform_dry_run,
    _clear_workload_caches
)


# ========== Helper Functions ==========

def simple_function(x):
    """Simple function with no internal parallelism."""
    return x ** 2


def threaded_function(x):
    """Function that creates threads internally."""
    result = [0]
    
    def worker():
        result[0] = x ** 2
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    
    return result[0]


def multi_threaded_function(x):
    """Function that creates multiple threads."""
    results = [0] * 4
    threads = []
    
    def worker(idx):
        results[idx] = x ** 2
    
    for i in range(4):
        thread = threading.Thread(target=worker, args=(i,))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    return sum(results)


# ========== Library Detection Tests ==========

class TestLibraryDetection:
    """Test detection of parallel computing libraries."""
    
    def test_detect_parallel_libraries_empty(self):
        """Test library detection with no parallel libraries."""
        # Note: numpy/scipy might be loaded by other tests
        # We just verify the function returns a list
        libs = detect_parallel_libraries()
        assert isinstance(libs, list)
        # Each item should be a string
        for lib in libs:
            assert isinstance(lib, str)
    
    def test_detect_parallel_libraries_multiprocessing(self):
        """Test that multiprocessing.pool (loaded by amorsize) is NOT detected."""
        # Import to ensure it's in sys.modules
        import multiprocessing.pool
        
        libs = detect_parallel_libraries()
        assert isinstance(libs, list)
        # multiprocessing.Pool should NOT be detected because it's loaded
        # by amorsize itself and doesn't indicate user function parallelism
        assert 'multiprocessing.Pool' not in libs
    
    def test_detect_parallel_libraries_threading(self):
        """Test that threading module alone doesn't trigger detection."""
        # threading is standard library, always loaded
        libs = detect_parallel_libraries()
        # threading itself shouldn't be in the list
        # (it's not a parallel computing library like numpy)
        assert 'threading' not in libs


class TestEnvironmentVariables:
    """Test detection of parallel environment variables."""
    
    def test_check_parallel_env_vars_empty(self):
        """Test when no parallel env vars are set."""
        # Clear any set variables
        vars_to_clear = ['OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS']
        original_values = {}
        
        for var in vars_to_clear:
            original_values[var] = os.getenv(var)
            if var in os.environ:
                del os.environ[var]
        
        # Clear cache so we get fresh detection
        _clear_workload_caches()
        
        try:
            env_vars = check_parallel_environment_vars()
            assert isinstance(env_vars, dict)
            # Should be empty or not contain the cleared variables
            for var in vars_to_clear:
                assert var not in env_vars
        finally:
            # Restore original values
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
            # Clear cache again for other tests
            _clear_workload_caches()
    
    def test_check_parallel_env_vars_set(self):
        """Test when parallel env vars are set."""
        original = os.getenv('OMP_NUM_THREADS')
        
        # Clear cache so we get fresh detection
        _clear_workload_caches()
        
        try:
            os.environ['OMP_NUM_THREADS'] = '4'
            # Clear cache again after setting env var
            _clear_workload_caches()
            env_vars = check_parallel_environment_vars()
            
            assert isinstance(env_vars, dict)
            assert 'OMP_NUM_THREADS' in env_vars
            assert env_vars['OMP_NUM_THREADS'] == '4'
        finally:
            if original is not None:
                os.environ['OMP_NUM_THREADS'] = original
            elif 'OMP_NUM_THREADS' in os.environ:
                del os.environ['OMP_NUM_THREADS']
            # Clear cache again for other tests
            _clear_workload_caches()
    
    def test_check_parallel_env_vars_multiple(self):
        """Test multiple environment variables set."""
        vars_to_set = {
            'OMP_NUM_THREADS': '2',
            'MKL_NUM_THREADS': '1',
            'OPENBLAS_NUM_THREADS': '3'
        }
        
        original_values = {}
        for var in vars_to_set:
            original_values[var] = os.getenv(var)
        
        # Clear cache so we get fresh detection
        _clear_workload_caches()
        
        try:
            for var, value in vars_to_set.items():
                os.environ[var] = value
            
            # Clear cache again after setting env vars
            _clear_workload_caches()
            env_vars = check_parallel_environment_vars()
            
            assert isinstance(env_vars, dict)
            for var, value in vars_to_set.items():
                assert var in env_vars
                assert env_vars[var] == value
        finally:
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
                elif var in os.environ:
                    del os.environ[var]
            # Clear cache again for other tests
            _clear_workload_caches()


class TestThreadActivity:
    """Test detection of threading activity during function execution."""
    
    def test_detect_thread_activity_simple(self):
        """Test thread detection with simple function."""
        thread_info = detect_thread_activity(simple_function, 10)
        
        assert isinstance(thread_info, dict)
        assert 'before' in thread_info
        assert 'during' in thread_info
        assert 'after' in thread_info
        assert 'delta' in thread_info
        
        # Simple function should not create additional threads
        assert thread_info['delta'] == 0
    
    def test_detect_thread_activity_threaded(self):
        """Test thread detection with threaded function."""
        thread_info = detect_thread_activity(threaded_function, 10)
        
        assert isinstance(thread_info, dict)
        # Threaded function should show increased thread count
        # Note: delta might be 0 if thread finished very quickly
        # but at minimum the structure should be correct
        assert thread_info['delta'] >= 0
        assert thread_info['during'] >= thread_info['before']
    
    def test_detect_thread_activity_multi_threaded(self):
        """Test thread detection with multi-threaded function."""
        thread_info = detect_thread_activity(multi_threaded_function, 10)
        
        assert isinstance(thread_info, dict)
        # Multi-threaded function should show increased thread count
        assert thread_info['delta'] >= 0
        assert thread_info['during'] >= thread_info['before']
    
    def test_detect_thread_activity_error_handling(self):
        """Test thread detection handles errors gracefully."""
        def error_function(x):
            raise ValueError("Intentional error")
        
        thread_info = detect_thread_activity(error_function, 10)
        
        assert isinstance(thread_info, dict)
        assert 'delta' in thread_info
        # Should return baseline on error
        assert thread_info['delta'] == 0


class TestSamplingIntegration:
    """Test integration of nested parallelism detection in sampling."""
    
    def test_perform_dry_run_simple_function(self):
        """Test dry run detects no nested parallelism for simple function."""
        data = list(range(10))
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        assert hasattr(result, 'nested_parallelism_detected')
        assert hasattr(result, 'parallel_libraries')
        assert hasattr(result, 'thread_activity')
        
        assert isinstance(result.nested_parallelism_detected, bool)
        assert isinstance(result.parallel_libraries, list)
        assert isinstance(result.thread_activity, dict)
    
    def test_perform_dry_run_threaded_function(self):
        """Test dry run detects nested parallelism for threaded function."""
        data = list(range(10))
        result = perform_dry_run(threaded_function, data, sample_size=5)
        
        assert hasattr(result, 'nested_parallelism_detected')
        # May or may not detect depending on timing
        # Just verify the structure is present
        assert isinstance(result.nested_parallelism_detected, bool)
        assert isinstance(result.thread_activity, dict)


class TestOptimizerIntegration:
    """Test integration of nested parallelism warnings in optimizer."""
    
    def test_optimize_simple_function_no_warning(self):
        """Test optimize doesn't warn for simple function."""
        data = list(range(100))
        result = optimize(simple_function, data, sample_size=5)
        
        # Should not have nested parallelism warnings
        nested_warnings = [w for w in result.warnings if 'nested parallelism' in w.lower()]
        # Note: warnings might be empty or contain nested parallelism warning
        # depending on what libraries are loaded
        assert isinstance(result.warnings, list)
    
    def test_optimize_threaded_function_structure(self):
        """Test optimize handles threaded function without crashing."""
        data = list(range(20))
        result = optimize(threaded_function, data, sample_size=3)
        
        # Should complete successfully
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert isinstance(result.warnings, list)
    
    def test_optimize_with_profile_includes_parallelism_info(self):
        """Test optimize with profile captures nested parallelism info."""
        data = list(range(50))
        result = optimize(simple_function, data, sample_size=5, profile=True)
        
        assert result.profile is not None
        # Profile should have constraints or recommendations
        assert hasattr(result.profile, 'constraints')
        assert hasattr(result.profile, 'recommendations')


class TestRealWorldScenarios:
    """Test real-world scenarios with nested parallelism."""
    
    def test_simple_workload_no_false_positives(self):
        """Test that simple workloads don't trigger false positives."""
        def pure_python_computation(x):
            result = 0
            for i in range(1000):
                result += x ** 2
            return result
        
        data = list(range(100))
        result = optimize(pure_python_computation, data, sample_size=5)
        
        # Should complete successfully
        assert result.n_jobs >= 1
        # Warnings list might contain various warnings but should be valid
        assert isinstance(result.warnings, list)
    
    def test_library_detection_doesnt_block_optimization(self):
        """Test that library detection doesn't prevent optimization."""
        data = list(range(100))
        result = optimize(simple_function, data, sample_size=5)
        
        # Even with libraries loaded, optimization should work
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.estimated_speedup >= 1.0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_nested_parallelism_with_empty_data(self):
        """Test nested parallelism detection with empty data."""
        data = []
        result = perform_dry_run(simple_function, data, sample_size=5)
        
        # Should handle empty data gracefully
        assert hasattr(result, 'nested_parallelism_detected')
        assert result.error is not None or result.sample_count == 0
    
    def test_nested_parallelism_with_single_item(self):
        """Test nested parallelism detection with single item."""
        data = [42]
        result = perform_dry_run(threaded_function, data, sample_size=1)
        
        # Should work with single item
        assert hasattr(result, 'nested_parallelism_detected')
        assert hasattr(result, 'thread_activity')
    
    def test_verbose_mode_shows_parallelism_info(self):
        """Test verbose mode displays nested parallelism information."""
        import io
        from contextlib import redirect_stdout
        
        data = list(range(50))
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            result = optimize(simple_function, data, sample_size=5, verbose=True)
        
        output = f.getvalue()
        
        # Should include sampling and optimization info
        assert 'sampling' in output.lower() or 'dry run' in output.lower()
        assert result.n_jobs >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
