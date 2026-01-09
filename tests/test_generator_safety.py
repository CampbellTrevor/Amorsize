"""
Tests for generator safety and data preservation in the optimizer.

This module tests the critical engineering constraint:
"Iterator Preservation: NEVER consume a generator without restoring it."
"""

import pytest
from amorsize import optimize


def simple_func(x):
    """Simple test function."""
    return x * 2


def expensive_func(x):
    """Expensive test function."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def test_generator_data_preservation():
    """
    Test that generators are properly reconstructed after sampling.
    
    This is the primary test for the generator safety feature.
    When a user passes a generator to optimize(), the sampling process
    consumes some items. We must ensure all items are still accessible
    via result.data.
    """
    def data_gen():
        for i in range(100):
            yield i
    
    # Call optimize with generator
    gen = data_gen()
    result = optimize(expensive_func, gen, sample_size=5)
    
    # result.data should contain all 100 items
    data_list = list(result.data)
    
    assert len(data_list) == 100, \
        f"Expected 100 items, got {len(data_list)}. Generator not properly reconstructed!"
    assert data_list == list(range(100)), \
        "Generator items not in correct order or not complete"


def test_list_data_unchanged():
    """
    Test that list inputs are returned unchanged in result.data.
    
    For list inputs, we don't need reconstruction, so result.data
    should just be the original list.
    """
    data = list(range(100))
    result = optimize(expensive_func, data, sample_size=5)
    
    # For lists, result.data should be the same object
    assert result.data is data or result.data == data, \
        "List data should be returned unchanged"
    
    # Should still have all items
    assert len(list(result.data)) == 100, \
        "List should have all items"


def test_range_data_unchanged():
    """
    Test that range objects work correctly.
    
    Range objects have __len__ so they're not consumed like generators.
    """
    data = range(100)
    result = optimize(expensive_func, data, sample_size=5)
    
    # Should have all items
    data_list = list(result.data)
    assert len(data_list) == 100, \
        "Range should have all items"
    assert data_list == list(range(100)), \
        "Range items not in correct order"


def test_generator_with_actual_multiprocessing():
    """
    Test that the reconstructed generator can be used with multiprocessing.Pool.
    
    This is the real-world use case: user gets recommendations and then
    uses result.data for actual parallel execution.
    """
    from multiprocessing import Pool
    
    def data_gen():
        for i in range(50):
            yield i
    
    gen = data_gen()
    result = optimize(expensive_func, gen, sample_size=5)
    
    # If parallel execution is recommended, use it
    if result.n_jobs > 1:
        with Pool(processes=result.n_jobs) as pool:
            results = pool.map(expensive_func, result.data, chunksize=result.chunksize)
    else:
        # Serial execution
        results = list(map(expensive_func, result.data))
    
    # Should process all 50 items
    assert len(results) == 50, \
        f"Expected 50 results, got {len(results)}"


def test_generator_with_different_sample_sizes():
    """
    Test that generator reconstruction works with various sample sizes.
    """
    for sample_size in [1, 3, 5, 10, 20]:
        def data_gen():
            for i in range(100):
                yield i
        
        gen = data_gen()
        result = optimize(expensive_func, gen, sample_size=sample_size)
        
        data_list = list(result.data)
        assert len(data_list) == 100, \
            f"With sample_size={sample_size}, expected 100 items, got {len(data_list)}"
        assert data_list == list(range(100)), \
            f"With sample_size={sample_size}, items not in correct order"


def test_generator_with_fast_function():
    """
    Test that generator safety works even when optimization recommends serial execution.
    """
    def data_gen():
        for i in range(100):
            yield i
    
    gen = data_gen()
    # simple_func is very fast, should recommend serial execution
    result = optimize(simple_func, gen, sample_size=5)
    
    # Should still have all items in result.data
    data_list = list(result.data)
    assert len(data_list) == 100, \
        "Generator should be reconstructed even for fast functions"
    
    # Verify serial execution was recommended
    assert result.n_jobs == 1, \
        "Fast function should recommend serial execution"


def test_generator_error_handling():
    """
    Test that generator data is preserved even when optimization encounters errors.
    """
    def data_gen():
        for i in range(100):
            yield i
    
    # Unpicklable function (lambda)
    unpicklable_func = lambda x: x * 2
    
    gen = data_gen()
    result = optimize(unpicklable_func, gen, sample_size=5)
    
    # Even with error, result.data should be available
    assert result.data is not None, \
        "result.data should be available even on error"
    
    # Should still be able to use the data
    data_list = list(result.data)
    assert len(data_list) == 100, \
        "Generator should be reconstructed even after pickling error"


def test_empty_generator():
    """
    Test handling of empty generators.
    """
    def empty_gen():
        return
        yield  # Never reached
    
    gen = empty_gen()
    result = optimize(expensive_func, gen, sample_size=5)
    
    # Should handle gracefully
    assert result.n_jobs == 1, \
        "Empty generator should recommend serial execution"
    assert result.data is not None, \
        "result.data should exist even for empty generator"


def test_generator_consumed_only_once():
    """
    Test that the generator is only consumed during sampling, not multiple times.
    
    This ensures we're not accidentally consuming the generator multiple times
    in different parts of the optimize() function.
    """
    consumption_count = 0
    
    def tracking_gen():
        nonlocal consumption_count
        for i in range(100):
            consumption_count += 1
            yield i
    
    gen = tracking_gen()
    result = optimize(expensive_func, gen, sample_size=5)
    
    # Should have consumed all items exactly once during sampling and reconstruction
    # Initial consumption: sample_size items
    # Reconstruction: itertools.chain doesn't consume until iteration
    # So consumption_count should be sample_size at this point
    assert consumption_count == 5, \
        f"Expected 5 items consumed during sampling, got {consumption_count}"
    
    # Now consume result.data
    data_list = list(result.data)
    
    # Now all 100 items should be consumed
    assert consumption_count == 100, \
        f"Expected 100 total items consumed, got {consumption_count}"
    assert len(data_list) == 100, \
        "Should have all 100 items in result.data"


def test_result_data_field_exists():
    """
    Test that OptimizationResult always has a data field.
    """
    data = list(range(100))
    result = optimize(expensive_func, data, sample_size=5)
    
    assert hasattr(result, 'data'), \
        "OptimizationResult should have a 'data' attribute"
    assert result.data is not None, \
        "result.data should not be None"


def test_documentation_example():
    """
    Test the example from the docstring to ensure it works as documented.
    """
    def expensive_function(x):
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    # Create a generator (simulates reading from file/database/network)
    gen = (x for x in range(100))
    
    # Get recommendations
    result = optimize(expensive_function, gen, sample_size=5)
    
    # Use result.data instead of original generator
    processed_data = list(result.data)
    
    # Should have all 100 items
    assert len(processed_data) == 100, \
        "Documentation example should preserve all data"
    assert processed_data == list(range(100)), \
        "Documentation example should have items in correct order"
