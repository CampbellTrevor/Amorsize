"""
Test cases for the execute() convenience function.
"""

import pytest
from amorsize import execute, optimize


# Test functions
def simple_square(x):
    """Simple function for testing."""
    return x ** 2


def simple_add_ten(x):
    """Simple function that adds 10."""
    return x + 10


def expensive_computation(x):
    """More expensive function for testing parallel execution."""
    result = 0
    for i in range(100):
        result += x ** 2 + i
    return result


def identity(x):
    """Identity function for testing."""
    return x


class TestExecuteBasics:
    """Test basic execute() functionality."""
    
    def test_execute_simple_list(self):
        """Test execute with simple list input."""
        data = [1, 2, 3, 4, 5]
        results = execute(simple_square, data)
        
        assert results == [1, 4, 9, 16, 25]
        assert len(results) == len(data)
    
    def test_execute_range(self):
        """Test execute with range input."""
        data = range(10)
        results = execute(simple_add_ten, data)
        
        expected = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        assert results == expected
    
    def test_execute_generator(self):
        """Test execute with generator input."""
        data = (x for x in range(5))
        results = execute(simple_square, data)
        
        assert results == [0, 1, 4, 9, 16]
    
    def test_execute_empty_data(self):
        """Test execute with empty data."""
        results = execute(simple_square, [])
        assert results == []
    
    def test_execute_single_item(self):
        """Test execute with single item."""
        results = execute(simple_square, [5])
        assert results == [25]


class TestExecuteOptimization:
    """Test that execute properly optimizes and executes."""
    
    def test_execute_respects_optimization(self):
        """Test that execute uses optimized parameters."""
        data = list(range(100))
        
        # Get optimization result separately
        opt_result = optimize(expensive_computation, data, sample_size=3)
        
        # Execute and get optimization result
        results, exec_opt_result = execute(
            expensive_computation,
            data,
            sample_size=3,
            return_optimization_result=True
        )
        
        # Should have same optimization decision (n_jobs)
        assert exec_opt_result.n_jobs == opt_result.n_jobs
        # Chunksize may vary slightly due to sampling variance, check they're close
        assert abs(exec_opt_result.chunksize - opt_result.chunksize) < max(10, opt_result.chunksize * 0.1)
        
        # Results should be correct
        assert len(results) == 100
        assert results[0] == expensive_computation(0)
        assert results[99] == expensive_computation(99)
    
    def test_execute_serial_path(self):
        """Test that serial execution (n_jobs=1) doesn't create Pool."""
        # Fast function should trigger serial execution
        def fast_func(x):
            return x * 2
        
        data = range(10)
        results = execute(fast_func, data, verbose=False)
        
        # Should complete successfully with correct results
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    
    def test_execute_parallel_path(self):
        """Test that expensive function triggers parallel execution."""
        data = list(range(50))
        
        # Use expensive function that should parallelize
        results, opt_result = execute(
            expensive_computation,
            data,
            sample_size=5,
            return_optimization_result=True
        )
        
        # Should have correct results
        assert len(results) == 50
        expected = [expensive_computation(x) for x in data]
        assert results == expected


class TestExecuteParameters:
    """Test execute parameter passing."""
    
    def test_execute_sample_size(self):
        """Test that sample_size parameter is used."""
        data = list(range(100))
        
        results1, opt1 = execute(
            expensive_computation,
            data,
            sample_size=3,
            return_optimization_result=True
        )
        
        results2, opt2 = execute(
            expensive_computation,
            data,
            sample_size=10,
            return_optimization_result=True
        )
        
        # Both should produce correct results
        assert len(results1) == 100
        assert len(results2) == 100
    
    def test_execute_verbose_mode(self):
        """Test that verbose mode works."""
        data = range(20)
        
        # Should not raise any errors in verbose mode
        results = execute(simple_square, data, verbose=True)
        assert len(results) == 20
    
    def test_execute_with_profile(self):
        """Test execute with profiling enabled."""
        data = list(range(30))
        
        results, opt_result = execute(
            expensive_computation,
            data,
            profile=True,
            return_optimization_result=True
        )
        
        # Should have profile
        assert opt_result.profile is not None
        assert opt_result.profile.sample_count > 0
        assert len(results) == 30
    
    def test_execute_target_chunk_duration(self):
        """Test custom target_chunk_duration."""
        data = list(range(50))
        
        results = execute(
            expensive_computation,
            data,
            target_chunk_duration=0.1
        )
        
        assert len(results) == 50
    
    def test_execute_auto_adjust_disabled(self):
        """Test with auto_adjust_for_nested_parallelism disabled."""
        data = range(20)
        
        results = execute(
            simple_square,
            data,
            auto_adjust_for_nested_parallelism=False
        )
        
        assert len(results) == 20


class TestExecuteReturnMode:
    """Test different return modes."""
    
    def test_execute_default_return(self):
        """Test default return mode (results only)."""
        data = range(10)
        result = execute(simple_square, data)
        
        # Should return list, not tuple
        assert isinstance(result, list)
        assert result == [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
    
    def test_execute_with_optimization_result(self):
        """Test return mode with optimization result."""
        data = range(10)
        result = execute(simple_square, data, return_optimization_result=True)
        
        # Should return tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        results, opt_result = result
        assert isinstance(results, list)
        assert opt_result.n_jobs >= 1
        assert opt_result.chunksize >= 1
    
    def test_execute_return_optimization_with_profile(self):
        """Test returning optimization result with profile."""
        data = list(range(30))
        
        results, opt_result = execute(
            expensive_computation,
            data,
            profile=True,
            return_optimization_result=True
        )
        
        assert len(results) == 30
        assert opt_result.profile is not None
        
        # Can call explain()
        explanation = opt_result.explain()
        assert isinstance(explanation, str)
        assert len(explanation) > 0


class TestExecuteEdgeCases:
    """Test edge cases and error handling."""
    
    def test_execute_invalid_function(self):
        """Test execute with invalid function."""
        with pytest.raises(ValueError):
            execute(None, [1, 2, 3])
    
    def test_execute_invalid_data(self):
        """Test execute with invalid data."""
        with pytest.raises(ValueError):
            execute(simple_square, None)
    
    def test_execute_invalid_sample_size(self):
        """Test execute with invalid sample_size."""
        with pytest.raises(ValueError):
            execute(simple_square, [1, 2, 3], sample_size=-1)
    
    def test_execute_invalid_target_duration(self):
        """Test execute with invalid target_chunk_duration."""
        with pytest.raises(ValueError):
            execute(simple_square, [1, 2, 3], target_chunk_duration=-0.1)
    
    def test_execute_large_dataset(self):
        """Test execute with larger dataset."""
        data = range(200)
        results = execute(identity, data)
        
        assert len(results) == 200
        assert results[0] == 0
        assert results[199] == 199
    
    def test_execute_with_progress_callback(self):
        """Test execute with progress callback."""
        progress_updates = []
        
        def callback(phase, progress):
            progress_updates.append((phase, progress))
        
        data = list(range(50))
        results = execute(
            expensive_computation,
            data,
            progress_callback=callback
        )
        
        assert len(results) == 50
        assert len(progress_updates) > 0
        assert progress_updates[0][1] == 0.0  # First update is 0.0
        assert progress_updates[-1][1] == 1.0  # Last update is 1.0


class TestExecuteIntegration:
    """Integration tests combining multiple features."""
    
    def test_execute_full_workflow(self):
        """Test complete workflow with all features."""
        progress_updates = []
        
        def progress_callback(phase, progress):
            progress_updates.append(phase)
        
        data = list(range(100))
        results, opt_result = execute(
            expensive_computation,
            data,
            sample_size=5,
            verbose=False,
            profile=True,
            return_optimization_result=True,
            progress_callback=progress_callback
        )
        
        # Verify results
        assert len(results) == 100
        expected = [expensive_computation(x) for x in data]
        assert results == expected
        
        # Verify optimization
        assert opt_result.n_jobs >= 1
        assert opt_result.chunksize >= 1
        
        # Verify profile
        assert opt_result.profile is not None
        assert opt_result.profile.sample_count == 5
        
        # Verify progress callbacks
        assert len(progress_updates) > 0
        assert "Starting optimization" in progress_updates
        assert "Optimization complete" in progress_updates
    
    def test_execute_comparison_with_manual(self):
        """Test that execute produces same results as manual Pool usage."""
        from multiprocessing import Pool
        
        data = list(range(50))
        
        # Using execute
        results_execute = execute(expensive_computation, data, sample_size=5)
        
        # Using optimize + manual Pool
        opt_result = optimize(expensive_computation, data, sample_size=5)
        if opt_result.n_jobs == 1:
            results_manual = [expensive_computation(x) for x in opt_result.data]
        else:
            with Pool(opt_result.n_jobs) as pool:
                results_manual = pool.map(
                    expensive_computation,
                    opt_result.data,
                    chunksize=opt_result.chunksize
                )
        
        # Should produce identical results
        assert results_execute == results_manual
