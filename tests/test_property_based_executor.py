"""
Property-based tests for executor module using Hypothesis.

These tests verify invariants and properties that should hold for all inputs,
automatically generating thousands of edge cases to test the executor's robustness.
"""

import time
from hypothesis import given, strategies as st, settings, assume
import pytest

from amorsize.executor import execute, _execute_serial
from amorsize.hooks import HookManager, HookEvent, HookContext


# ============================================================================
# Test Strategies (Input Generators)
# ============================================================================

@st.composite
def simple_function_strategy(draw):
    """Generate simple, picklable functions for testing."""
    operation = draw(st.sampled_from(['square', 'double', 'increment', 'identity']))
    
    if operation == 'square':
        return lambda x: x ** 2
    elif operation == 'double':
        return lambda x: x * 2
    elif operation == 'increment':
        return lambda x: x + 1
    else:  # identity
        return lambda x: x


@st.composite
def data_list_strategy(draw):
    """Generate lists of various sizes with integers."""
    size = draw(st.integers(min_value=1, max_value=100))
    return draw(st.lists(st.integers(min_value=-100, max_value=100), min_size=size, max_size=size))


# ============================================================================
# 1. Execute Function - Basic Invariants
# ============================================================================

class TestExecuteBasicInvariants:
    """Test basic invariants of the execute() function."""
    
    @given(data=st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=50))
    @settings(deadline=5000, max_examples=50)
    def test_execute_preserves_data_length(self, data):
        """Execute should return same number of results as input items."""
        def square(x):
            return x ** 2
        
        results = execute(square, data, verbose=False)
        
        assert len(results) == len(data), f"Expected {len(data)} results, got {len(results)}"
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=50)
    def test_execute_deterministic(self, data):
        """Execute should produce same results for same inputs."""
        def add_ten(x):
            return x + 10
        
        results1 = execute(add_ten, data, verbose=False)
        results2 = execute(add_ten, data, verbose=False)
        
        assert results1 == results2, "Execute should be deterministic"
    
    @given(
        data=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=50),
        sample_size=st.integers(min_value=1, max_value=10)
    )
    @settings(deadline=5000, max_examples=50)
    def test_execute_respects_sample_size(self, data, sample_size):
        """Execute should work with various sample sizes."""
        def double(x):
            return x * 2
        
        # Should not raise exception
        results = execute(double, data, sample_size=sample_size, verbose=False)
        
        assert len(results) == len(data)
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=50)
    def test_execute_with_return_optimization_result(self, data):
        """Execute with return_optimization_result=True returns tuple."""
        def identity(x):
            return x
        
        result = execute(identity, data, return_optimization_result=True, verbose=False)
        
        assert isinstance(result, tuple), "Should return tuple when return_optimization_result=True"
        assert len(result) == 2, "Should return (results, optimization_result)"
        
        results, opt_result = result
        assert len(results) == len(data), "Results length should match data length"
        assert hasattr(opt_result, 'n_jobs'), "Should have optimization result"
        assert hasattr(opt_result, 'chunksize'), "Should have chunksize"


# ============================================================================
# 2. Execute Function - Correctness Invariants
# ============================================================================

class TestExecuteCorrectnessInvariants:
    """Test correctness properties of execute()."""
    
    @given(data=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=50)
    def test_execute_produces_correct_results(self, data):
        """Execute should produce mathematically correct results."""
        def square(x):
            return x ** 2
        
        results = execute(square, data, verbose=False)
        expected = [x ** 2 for x in data]
        
        assert results == expected, f"Results don't match expected values"
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=50)
    def test_execute_preserves_order(self, data):
        """Execute should preserve input order in output."""
        def identity(x):
            return x
        
        results = execute(identity, data, verbose=False)
        
        assert results == data, "Execute should preserve order"
    
    @given(
        data=st.lists(st.integers(min_value=1, max_value=50), min_size=2, max_size=20),
        multiplier=st.integers(min_value=1, max_value=10)
    )
    @settings(deadline=5000, max_examples=50)
    def test_execute_with_parameterized_function(self, data, multiplier):
        """Execute should work with functions using closures."""
        def multiply_by_n(x):
            return x * multiplier
        
        results = execute(multiply_by_n, data, verbose=False)
        expected = [x * multiplier for x in data]
        
        assert results == expected, f"Parameterized function results incorrect"


# ============================================================================
# 3. Execute Function - Edge Cases
# ============================================================================

class TestExecuteEdgeCases:
    """Test edge cases in execute()."""
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=5))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_small_datasets(self, data):
        """Execute should handle very small datasets correctly."""
        def square(x):
            return x ** 2
        
        results = execute(square, data, verbose=False)
        
        assert len(results) == len(data)
        assert results == [x ** 2 for x in data]
    
    @given(value=st.integers())
    @settings(deadline=3000, max_examples=30)
    def test_execute_with_single_item(self, value):
        """Execute should handle single-item lists."""
        def increment(x):
            return x + 1
        
        results = execute(increment, [value], verbose=False)
        
        assert len(results) == 1
        assert results[0] == value + 1
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=50)
    def test_execute_with_verbose_false(self, data):
        """Execute with verbose=False should not print output."""
        def square(x):
            return x ** 2
        
        # Should execute without printing (tested by not raising exception)
        results = execute(square, data, verbose=False)
        
        assert len(results) == len(data)
    
    @given(data=st.lists(st.integers(min_value=0, max_value=10), min_size=5, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_fast_function(self, data):
        """Execute should handle very fast functions (might choose serial)."""
        def fast_function(x):
            return x  # Extremely fast
        
        results = execute(fast_function, data, verbose=False)
        
        assert results == data, "Fast function should still produce correct results"


# ============================================================================
# 4. Serial Execution Path - Invariants
# ============================================================================

class TestSerialExecutionInvariants:
    """Test serial execution helper function."""
    
    @given(
        data=st.lists(st.integers(), min_size=1, max_size=30),
        chunksize=st.integers(min_value=1, max_value=10)
    )
    @settings(deadline=5000, max_examples=50)
    def test_serial_execution_preserves_length(self, data, chunksize):
        """Serial execution should return same number of results."""
        def square(x):
            return x ** 2
        
        start_time = time.time()
        results = _execute_serial(
            func=square,
            data=data,
            hooks=None,
            start_time=start_time,
            chunksize=chunksize,
            use_fine_grained_tracking=False
        )
        
        assert len(results) == len(data)
    
    @given(data=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=50)
    def test_serial_execution_correctness(self, data):
        """Serial execution should produce correct results."""
        def double(x):
            return x * 2
        
        start_time = time.time()
        results = _execute_serial(
            func=double,
            data=data,
            hooks=None,
            start_time=start_time,
            chunksize=5,
            use_fine_grained_tracking=False
        )
        expected = [x * 2 for x in data]
        
        assert results == expected


# ============================================================================
# 5. Hook Integration - Invariants
# ============================================================================

class TestHookIntegrationInvariants:
    """Test hook integration in execute()."""
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_hooks_preserves_results(self, data):
        """Execute with hooks should still produce correct results."""
        hook_manager = HookManager()
        progress_called = []
        
        def progress_hook(context: HookContext):
            progress_called.append(context.percent_complete)
        
        hook_manager.register(HookEvent.ON_PROGRESS, progress_hook)
        
        def square(x):
            return x ** 2
        
        results = execute(square, data, hooks=hook_manager, verbose=False)
        expected = [x ** 2 for x in data]
        
        assert results == expected, "Hooks should not affect results"
    
    @given(data=st.lists(st.integers(), min_size=5, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_triggers_hooks(self, data):
        """Execute should trigger registered hooks."""
        hook_manager = HookManager()
        hook_calls = []
        
        def test_hook(context: HookContext):
            hook_calls.append(context.event)
        
        hook_manager.register(HookEvent.PRE_EXECUTE, test_hook)
        hook_manager.register(HookEvent.POST_EXECUTE, test_hook)
        
        def identity(x):
            return x
        
        execute(identity, data, hooks=hook_manager, verbose=False)
        
        # Should have at least PRE_EXECUTE and POST_EXECUTE events
        assert len(hook_calls) >= 2, "Should trigger hooks"
        assert HookEvent.PRE_EXECUTE in hook_calls, "Should trigger PRE_EXECUTE"
        assert HookEvent.POST_EXECUTE in hook_calls, "Should trigger POST_EXECUTE"


# ============================================================================
# 6. Progress Callback - Invariants
# ============================================================================

class TestProgressCallbackInvariants:
    """Test progress callback functionality."""
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_progress_callback(self, data):
        """Execute with progress callback should still produce correct results."""
        progress_updates = []
        
        def progress_cb(message: str, progress: float):
            progress_updates.append((message, progress))
        
        def square(x):
            return x ** 2
        
        results = execute(square, data, progress_callback=progress_cb, verbose=False)
        expected = [x ** 2 for x in data]
        
        assert results == expected, "Progress callback should not affect results"
        # Progress callback may or may not be called depending on optimization decision
        assert isinstance(progress_updates, list), "Should collect progress updates"


# ============================================================================
# 7. Numerical Stability - Invariants
# ============================================================================

class TestNumericalStabilityInvariants:
    """Test numerical stability of execute()."""
    
    @given(data=st.lists(st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_floats(self, data):
        """Execute should handle floating point numbers correctly."""
        def multiply(x):
            return x * 1.5
        
        results = execute(multiply, data, verbose=False)
        
        assert len(results) == len(data)
        
        # Check results are close to expected (within floating point precision)
        for i, (result, input_val) in enumerate(zip(results, data)):
            expected = input_val * 1.5
            assert abs(result - expected) < 1e-10, f"Result {i} not close to expected"
    
    @given(data=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=30))
    @settings(deadline=5000, max_examples=50)
    def test_execute_with_negative_numbers(self, data):
        """Execute should handle negative numbers correctly."""
        def absolute(x):
            return abs(x)
        
        results = execute(absolute, data, verbose=False)
        expected = [abs(x) for x in data]
        
        assert results == expected
        assert all(r >= 0 for r in results), "All results should be non-negative"


# ============================================================================
# 8. Configuration Parameters - Invariants
# ============================================================================

class TestConfigurationParametersInvariants:
    """Test various configuration parameters."""
    
    @given(
        data=st.lists(st.integers(), min_size=1, max_size=20),
        target_duration=st.floats(min_value=0.1, max_value=1.0)
    )
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_target_chunk_duration(self, data, target_duration):
        """Execute should work with various target chunk durations."""
        def square(x):
            return x ** 2
        
        results = execute(square, data, target_chunk_duration=target_duration, verbose=False)
        
        assert len(results) == len(data)
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_spawn_benchmark_disabled(self, data):
        """Execute should work with spawn benchmark disabled."""
        def identity(x):
            return x
        
        results = execute(identity, data, use_spawn_benchmark=False, verbose=False)
        
        assert results == data
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_chunking_benchmark_disabled(self, data):
        """Execute should work with chunking benchmark disabled."""
        def identity(x):
            return x
        
        results = execute(identity, data, use_chunking_benchmark=False, verbose=False)
        
        assert results == data


# ============================================================================
# 9. Data Type Handling - Invariants
# ============================================================================

class TestDataTypeHandlingInvariants:
    """Test handling of various data types."""
    
    @given(data=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_strings(self, data):
        """Execute should handle string data correctly."""
        def uppercase(s):
            return s.upper()
        
        results = execute(uppercase, data, verbose=False)
        expected = [s.upper() for s in data]
        
        assert results == expected
    
    @given(data=st.lists(st.lists(st.integers(), min_size=1, max_size=5), min_size=1, max_size=10))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_nested_lists(self, data):
        """Execute should handle nested list data."""
        def sum_list(lst):
            return sum(lst)
        
        results = execute(sum_list, data, verbose=False)
        expected = [sum(lst) for lst in data]
        
        assert results == expected
    
    @given(data=st.lists(st.tuples(st.integers(), st.integers()), min_size=1, max_size=20))
    @settings(deadline=5000, max_examples=30)
    def test_execute_with_tuples(self, data):
        """Execute should handle tuple data."""
        def sum_tuple(t):
            return t[0] + t[1]
        
        results = execute(sum_tuple, data, verbose=False)
        expected = [t[0] + t[1] for t in data]
        
        assert results == expected


# ============================================================================
# 10. Error Handling - Properties
# ============================================================================

class TestErrorHandlingProperties:
    """Test error handling properties."""
    
    @given(data=st.lists(st.integers(), min_size=1, max_size=10))
    @settings(deadline=5000, max_examples=20)
    def test_execute_with_none_function_raises(self, data):
        """Execute should raise ValueError with None function."""
        with pytest.raises(ValueError):
            execute(None, data, verbose=False)
    
    def test_execute_with_empty_data_raises(self):
        """Execute should handle empty data appropriately."""
        def square(x):
            return x ** 2
        
        # Empty list - should either work or raise a clear error
        try:
            results = execute(square, [], verbose=False)
            # If it works, should return empty list
            assert results == []
        except (ValueError, IndexError):
            # Acceptable to raise error for empty data
            pass


# ============================================================================
# 11. Integration Tests - Properties
# ============================================================================

class TestIntegrationProperties:
    """Test integration properties of execute()."""
    
    @given(
        data=st.lists(st.integers(min_value=1, max_value=50), min_size=5, max_size=30),
        sample_size=st.integers(min_value=1, max_value=5)
    )
    @settings(deadline=10000, max_examples=20)
    def test_execute_full_pipeline(self, data, sample_size):
        """Execute full pipeline with all features."""
        def compute_factorial_mod(x):
            """Compute factorial mod 1000 (moderately expensive)."""
            result = 1
            for i in range(1, min(x, 20) + 1):
                result = (result * i) % 1000
            return result
        
        # Full pipeline execution
        results = execute(
            compute_factorial_mod,
            data,
            sample_size=sample_size,
            verbose=False,
            use_spawn_benchmark=True,
            use_chunking_benchmark=True
        )
        
        assert len(results) == len(data), "Should process all items"
        
        # Verify results are correct
        expected = [compute_factorial_mod(x) for x in data]
        assert results == expected, "Results should be correct"


# ============================================================================
# 12. Performance Characteristics - Invariants
# ============================================================================

class TestPerformanceCharacteristicsInvariants:
    """Test performance-related invariants."""
    
    @given(data=st.lists(st.integers(), min_size=10, max_size=50))
    @settings(deadline=10000, max_examples=20)
    def test_execute_completes_in_reasonable_time(self, data):
        """Execute should complete in reasonable time."""
        def simple_operation(x):
            return x + 1
        
        start_time = time.time()
        results = execute(simple_operation, data, verbose=False)
        elapsed = time.time() - start_time
        
        # Should complete quickly (< 5 seconds for this simple operation)
        assert elapsed < 5.0, f"Execute took too long: {elapsed}s"
        assert len(results) == len(data)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
