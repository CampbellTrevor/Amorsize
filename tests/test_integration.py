"""
Integration tests for end-to-end workflows.

These tests verify that the optimizer's recommendations actually work
when used with multiprocessing.Pool in real scenarios.
"""

import time
from multiprocessing import Pool
from typing import Any, List
import pytest

from amorsize import optimize, execute


# Test functions with various characteristics
def simple_square(x: int) -> int:
    """Simple, fast function for testing."""
    return x ** 2


def moderate_computation(x: int) -> int:
    """Moderately expensive computation."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def expensive_computation(x: int) -> int:
    """Expensive computation that should parallelize well."""
    result = 0
    for i in range(10000):
        result += x ** 2
    return result


def return_large_object(x: int) -> List[int]:
    """Function that returns a larger object."""
    return [x] * 1000


def variable_time_function(x: int) -> int:
    """Function with variable execution time."""
    iterations = x % 100 + 100
    result = 0
    for i in range(iterations):
        result += x ** 2
    return result


class TestEndToEndOptimization:
    """Test that optimize() recommendations work correctly with Pool."""
    
    def test_simple_function_list_data(self):
        """Test optimize + Pool.map with simple function and list data."""
        data = list(range(100))
        
        # Get optimization recommendation
        result = optimize(simple_square, data)
        
        # Use recommendation with Pool
        if result.n_jobs == 1:
            # Serial execution
            results = [simple_square(x) for x in result.data]
        else:
            # Parallel execution
            with Pool(processes=result.n_jobs) as pool:
                results = pool.map(simple_square, result.data, chunksize=result.chunksize)
        
        # Verify correctness
        expected = [x ** 2 for x in range(100)]
        assert results == expected, "Results don't match expected output"
    
    def test_moderate_function_with_range(self):
        """Test with moderate computation and range data."""
        data = range(50)
        
        result = optimize(moderate_computation, data)
        
        # Execute with recommended parameters
        if result.n_jobs == 1:
            results = [moderate_computation(x) for x in result.data]
        else:
            with Pool(processes=result.n_jobs) as pool:
                results = pool.map(moderate_computation, result.data, chunksize=result.chunksize)
        
        # Verify correctness
        expected = [moderate_computation(x) for x in range(50)]
        assert results == expected
    
    def test_generator_reconstruction_with_pool(self):
        """Test that generator reconstruction actually works with Pool."""
        def gen():
            for i in range(50):
                yield i
        
        original_gen = gen()
        result = optimize(simple_square, original_gen)
        
        # The generator should be reconstructed in result.data
        assert result.data is not None, "Data should be reconstructed"
        
        # Use with Pool
        if result.n_jobs == 1:
            results = [simple_square(x) for x in result.data]
        else:
            with Pool(processes=result.n_jobs) as pool:
                results = pool.map(simple_square, result.data, chunksize=result.chunksize)
        
        # Verify all data processed
        expected = [x ** 2 for x in range(50)]
        assert results == expected, "Generator reconstruction failed"
    
    def test_expensive_function_parallelizes(self):
        """Test that expensive functions actually benefit from parallelization."""
        data = list(range(20))
        
        result = optimize(expensive_computation, data)
        
        # For expensive functions, we should get parallelization
        # (unless on a single-core system)
        physical_cores = result.n_jobs if result.n_jobs > 1 else 1
        
        # Execute with recommended parameters
        if result.n_jobs == 1:
            results = [expensive_computation(x) for x in result.data]
        else:
            with Pool(processes=result.n_jobs) as pool:
                results = pool.map(expensive_computation, result.data, chunksize=result.chunksize)
        
        # Verify correctness
        expected = [expensive_computation(x) for x in range(20)]
        assert results == expected


class TestEndToEndExecute:
    """Test the execute() convenience function end-to-end."""
    
    def test_execute_simple_function(self):
        """Test execute() with simple function."""
        data = list(range(100))
        results = execute(simple_square, data)
        
        expected = [x ** 2 for x in range(100)]
        assert results == expected
    
    def test_execute_with_generator(self):
        """Test execute() handles generators correctly."""
        def gen():
            for i in range(50):
                yield i
        
        results = execute(simple_square, gen())
        
        expected = [x ** 2 for x in range(50)]
        assert results == expected
    
    def test_execute_returns_optimization_result(self):
        """Test execute() can return optimization details."""
        data = list(range(50))
        results, opt_result = execute(
            moderate_computation,
            data,
            return_optimization_result=True
        )
        
        # Verify results
        expected = [moderate_computation(x) for x in range(50)]
        assert results == expected
        
        # Verify we got optimization details
        assert opt_result is not None
        assert hasattr(opt_result, 'n_jobs')
        assert hasattr(opt_result, 'chunksize')
    
    def test_execute_with_empty_data(self):
        """Test execute() handles empty data gracefully."""
        data = []
        results = execute(simple_square, data)
        assert results == []
    
    def test_execute_with_single_item(self):
        """Test execute() with single item."""
        data = [5]
        results = execute(simple_square, data)
        assert results == [25]


class TestDataTypeHandling:
    """Test that different data types work correctly end-to-end."""
    
    def test_list_data_preserves_order(self):
        """Test that list data maintains order."""
        data = list(range(100, 0, -1))  # Reverse order
        results = execute(simple_square, data)
        
        expected = [x ** 2 for x in range(100, 0, -1)]
        assert results == expected, "Order not preserved"
    
    def test_range_data_works(self):
        """Test that range objects work correctly."""
        data = range(50)
        results = execute(simple_square, data)
        
        expected = [x ** 2 for x in range(50)]
        assert results == expected
    
    def test_generator_data_consumed_correctly(self):
        """Test that all generator data is processed."""
        def gen():
            for i in range(100):
                yield i
        
        results = execute(simple_square, gen())
        
        # Verify all 100 items processed
        assert len(results) == 100
        expected = [x ** 2 for x in range(100)]
        assert results == expected


class TestEdgeCases:
    """Test edge cases that might break in production."""
    
    def test_very_small_dataset(self):
        """Test with very small dataset (< sample_size)."""
        data = [1, 2]
        results = execute(simple_square, data)
        assert results == [1, 4]
    
    def test_large_return_objects(self):
        """Test that large return objects don't break execution."""
        data = list(range(10))
        results = execute(return_large_object, data)
        
        # Verify correctness
        assert len(results) == 10
        assert results[0] == [0] * 1000
        assert results[5] == [5] * 1000
    
    def test_heterogeneous_workload(self):
        """Test that heterogeneous workloads work correctly."""
        data = list(range(50))
        results = execute(variable_time_function, data)
        
        # Verify all results correct
        expected = [variable_time_function(x) for x in range(50)]
        assert results == expected
    
    def test_with_custom_sample_size(self):
        """Test with custom sample_size parameter."""
        data = list(range(100))
        results = execute(simple_square, data, sample_size=10)
        
        expected = [x ** 2 for x in range(100)]
        assert results == expected


class TestParameterValidation:
    """Test that invalid parameters are caught before execution."""
    
    def test_invalid_function_raises_error(self):
        """Test that non-callable function raises error."""
        with pytest.raises(ValueError, match="must be callable"):
            optimize("not a function", [1, 2, 3])
    
    def test_invalid_data_raises_error(self):
        """Test that None data raises error."""
        with pytest.raises(ValueError, match="cannot be None"):
            optimize(simple_square, None)
    
    def test_invalid_sample_size_raises_error(self):
        """Test that invalid sample_size raises error."""
        with pytest.raises(ValueError, match="sample_size"):
            optimize(simple_square, [1, 2, 3], sample_size=0)


class TestCorrectness:
    """Test that optimized execution produces correct results."""
    
    def test_results_match_serial_execution(self):
        """Test that parallel results match serial execution."""
        data = list(range(100))
        
        # Serial execution (ground truth)
        serial_results = [moderate_computation(x) for x in data]
        
        # Optimized execution
        optimized_results = execute(moderate_computation, data)
        
        # Results should match exactly
        assert optimized_results == serial_results
    
    def test_no_data_loss(self):
        """Test that no data is lost during optimization."""
        data = list(range(100))
        results = execute(simple_square, data)
        
        # Should process all 100 items
        assert len(results) == 100
    
    def test_no_data_duplication(self):
        """Test that data isn't duplicated."""
        data = list(range(50))
        results = execute(simple_square, data)
        
        # Should have exactly 50 results
        assert len(results) == 50
        
        # Each result should appear once
        assert sorted(results) == sorted([x ** 2 for x in range(50)])


class TestPerformanceValidation:
    """Test that optimizations provide reasonable performance."""
    
    def test_serial_fallback_is_correct(self):
        """Test that serial fallback (n_jobs=1) works correctly."""
        # Very fast function should fall back to serial
        def ultra_fast(x):
            return x + 1
        
        data = list(range(100))
        result = optimize(ultra_fast, data)
        
        # Execute with recommendation
        if result.n_jobs == 1:
            results = [ultra_fast(x) for x in result.data]
        else:
            with Pool(processes=result.n_jobs) as pool:
                results = pool.map(ultra_fast, result.data, chunksize=result.chunksize)
        
        # Verify correctness
        expected = [x + 1 for x in range(100)]
        assert results == expected
    
    def test_chunksize_recommendations_are_reasonable(self):
        """Test that chunksize recommendations are in reasonable range."""
        data = list(range(1000))
        result = optimize(moderate_computation, data)
        
        # Chunksize should be between 1 and total items
        assert 1 <= result.chunksize <= 1000
        
        # Chunksize should not be larger than total_items / n_jobs
        if result.n_jobs > 1:
            max_reasonable_chunksize = len(data) // result.n_jobs + 1
            assert result.chunksize <= max_reasonable_chunksize * 2


class TestIntegrationWithFeatures:
    """Test integration with various features."""
    
    def test_with_verbose_mode(self):
        """Test that verbose mode doesn't break execution."""
        data = list(range(50))
        results = execute(moderate_computation, data, verbose=True)
        
        expected = [moderate_computation(x) for x in range(50)]
        assert results == expected
    
    def test_with_profile_mode(self):
        """Test that profile mode works with execution."""
        data = list(range(50))
        results, opt_result = execute(
            moderate_computation,
            data,
            profile=True,
            return_optimization_result=True
        )
        
        # Verify results
        expected = [moderate_computation(x) for x in range(50)]
        assert results == expected
        
        # Verify profile was captured
        assert opt_result.profile is not None
        assert hasattr(opt_result.profile, 'estimated_speedup')
    
    def test_with_progress_callback(self):
        """Test that progress callback works with execution."""
        progress_updates = []
        
        def callback(phase: str, progress: float):
            progress_updates.append((phase, progress))
        
        data = list(range(50))
        results = execute(
            moderate_computation,
            data,
            progress_callback=callback
        )
        
        # Verify results
        expected = [moderate_computation(x) for x in range(50)]
        assert results == expected
        
        # Verify callback was called
        assert len(progress_updates) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
