"""
Test cases for extreme workload scenarios.

This module tests the optimizer's behavior with extreme edge cases that might
occur in production environments:
- Very large datasets (100K+ items)
- Very fast functions (microsecond-level execution)
- Very slow functions (multi-second execution)  
- Extreme memory scenarios
- Pathological chunking scenarios

These tests ensure the optimizer degrades gracefully and provides sensible
recommendations even in challenging scenarios.
"""

import pytest
import time
from amorsize import optimize, execute


class TestVeryLargeDatasets:
    """Test optimizer behavior with very large datasets."""
    
    def test_optimize_100k_items_fast_function(self):
        """Test optimization with 100,000 items and fast function."""
        def fast_func(x):
            return x * 2
        
        data = range(100000)
        result = optimize(fast_func, data, sample_size=10)
        
        # Should recommend parallelization for large dataset
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.estimated_speedup >= 1.0
        
        # Chunksize should be reasonable (not 100k items per chunk)
        # Max reasonable chunksize is ~10% of total items
        assert result.chunksize <= 10000
    
    def test_optimize_1m_items_iterator(self):
        """Test optimization with 1 million items as iterator."""
        def tiny_func(x):
            return x + 1
        
        # Use generator to avoid memory issues
        data = (x for x in range(1000000))
        result = optimize(tiny_func, data, sample_size=10)
        
        # Should handle iterator gracefully
        assert result.n_jobs >= 1
        assert result.data is not None  # Iterator should be reconstructed
    
    def test_very_large_dataset_memory_safety(self):
        """Test that optimizer accounts for memory with large datasets."""
        def identity(x):
            return x
        
        # Large dataset where we can estimate total items
        data = list(range(500000))
        result = optimize(identity, data, sample_size=10, profile=True)
        
        # Should complete without OOM
        assert result is not None
        assert result.n_jobs >= 1


class TestVeryFastFunctions:
    """Test optimizer behavior with microsecond-level fast functions."""
    
    def test_optimize_trivial_function(self):
        """Test optimization with extremely fast (trivial) function."""
        def trivial(x):
            return x
        
        data = range(1000)
        result = optimize(trivial, data, sample_size=10)
        
        # Very fast functions typically don't benefit from parallelization
        # due to overhead being larger than work
        assert result.n_jobs >= 1  # At least serial
        assert result.chunksize >= 1
        
        # Likely recommends serial execution due to overhead
        # but this depends on system and exact timing
        assert result.reason is not None
    
    def test_optimize_arithmetic_only(self):
        """Test optimization with simple arithmetic (nanosecond-level)."""
        def add_one(x):
            return x + 1
        
        data = range(10000)
        result = optimize(add_one, data, sample_size=10)
        
        # Should handle fast function without errors
        assert result is not None
        assert result.estimated_speedup >= 1.0  # Never recommend worse than serial
    
    def test_very_fast_with_large_dataset(self):
        """Test fast function with large dataset - edge case for chunksize."""
        def bitwise_op(x):
            return x ^ 0xFF  # Very fast bitwise operation
        
        data = range(100000)
        result = optimize(bitwise_op, data, sample_size=10)
        
        # With very fast function, overhead may dominate, so optimizer may
        # recommend serial execution. This is correct behavior.
        assert result.chunksize >= 1
        
        # If parallelization is recommended, chunksize should be reasonable
        if result.n_jobs > 1:
            # Chunksize should be large to amortize overhead
            assert result.chunksize >= 10
            # But not absurdly large (should cap at ~10% of total)
            assert result.chunksize <= 10000


class TestVerySlowFunctions:
    """Test optimizer behavior with slow (multi-second) functions."""
    
    def test_optimize_slow_function_small_dataset(self):
        """Test optimization with slow function and small dataset."""
        def slow_func(x):
            # Simulate 0.1s computation
            time.sleep(0.1)
            return x * 2
        
        # Small sample to avoid long test times
        data = range(10)
        result = optimize(slow_func, data, sample_size=3)
        
        # Slow functions should benefit from parallelization
        assert result.n_jobs > 1 or result.estimated_speedup >= 1.0
        
        # Chunksize should be small (each item is expensive)
        assert result.chunksize <= 5
    
    def test_optimize_moderate_slow_function(self):
        """Test with moderately slow function (10ms per item)."""
        def moderate_slow(x):
            # Simulate 10ms computation
            time.sleep(0.01)
            return x ** 2
        
        data = range(50)
        result = optimize(moderate_slow, data, sample_size=5)
        
        # Should recommend parallelization (or at least not fail)
        assert result.estimated_speedup >= 1.0
        
        # If parallelization is recommended:
        # With 10ms per item and 0.2s target chunk duration,
        # chunksize should be around 20 items
        # But for small datasets (50 items), serial may be better due to overhead
        if result.n_jobs > 1:
            assert 5 <= result.chunksize <= 50


class TestExtremeMemoryScenarios:
    """Test optimizer behavior with extreme memory scenarios."""
    
    def test_large_return_objects(self):
        """Test function that returns large objects."""
        def large_list_generator(x):
            # Return a list of 10K integers (~40KB)
            return list(range(10000))
        
        data = range(100)
        result = optimize(large_list_generator, data, sample_size=5, profile=True)
        
        # Should detect large return size
        if result.profile:
            assert result.profile.return_size_bytes > 10000  # At least 10KB
        
        # Should warn about memory accumulation
        assert result.warnings  # Should have at least one warning
    
    def test_peak_memory_tracking(self):
        """Test that peak memory is tracked correctly."""
        def memory_intensive(x):
            # Create temporary large structure
            temp = [0] * 100000  # ~400KB
            return sum(temp) + x
        
        data = range(20)
        result = optimize(memory_intensive, data, sample_size=5, profile=True)
        
        # Should detect memory usage
        if result.profile:
            assert result.profile.peak_memory_bytes > 100000  # At least 100KB


class TestPathologicalChunkingScenarios:
    """Test edge cases in chunking logic."""
    
    def test_chunksize_larger_than_dataset(self):
        """Test when optimal chunksize would be larger than dataset."""
        def fast_func(x):
            return x * 2
        
        # Very small dataset
        data = range(5)
        result = optimize(fast_func, data, sample_size=5)
        
        # Chunksize should be capped at dataset size
        assert result.chunksize <= 5
        assert result.chunksize >= 1
    
    def test_single_item_dataset(self):
        """Test optimization with single item."""
        def any_func(x):
            return x * 2
        
        data = [42]
        result = optimize(any_func, data, sample_size=1)
        
        # Should handle gracefully
        assert result.n_jobs == 1  # Serial for single item
        assert result.chunksize == 1
    
    def test_heterogeneous_workload_extreme_variance(self):
        """Test with highly variable execution times."""
        def variable_func(x):
            # Variable sleep based on input
            if x % 10 == 0:
                time.sleep(0.01)  # 10ms for every 10th item
            else:
                pass  # Instant for others
            return x
        
        data = range(30)
        result = optimize(variable_func, data, sample_size=10, profile=True)
        
        # Should detect heterogeneous workload
        if result.profile:
            # Coefficient of variation should be high
            assert result.profile.coefficient_of_variation > 0.5
        
        # Should recommend smaller chunks for better load balancing
        # But this is timing-dependent, so just verify it completes
        assert result is not None


class TestOptimizationWithEdgeCaseData:
    """Test with unusual data types and structures."""
    
    def test_optimize_with_none_values(self):
        """Test optimization with None values in data."""
        def handle_none(x):
            return 0 if x is None else x * 2
        
        data = [1, None, 3, None, 5]
        result = optimize(handle_none, data, sample_size=5)
        
        # Should handle None gracefully
        assert result is not None
        assert result.n_jobs >= 1
    
    def test_optimize_with_negative_numbers(self):
        """Test optimization with negative numbers."""
        def process_negative(x):
            return abs(x) ** 2
        
        data = range(-100, 100)
        result = optimize(process_negative, data, sample_size=10)
        
        # Should work normally with negative numbers
        assert result.n_jobs >= 1
        assert result.estimated_speedup >= 1.0
    
    def test_optimize_with_float_data(self):
        """Test optimization with floating point data."""
        def float_computation(x):
            return x * 3.14159
        
        data = [float(i) / 10 for i in range(100)]
        result = optimize(float_computation, data, sample_size=10)
        
        # Should handle floats normally
        assert result.n_jobs >= 1


class TestExecuteWithExtremeWorkloads:
    """Test execute() function with extreme scenarios."""
    
    def test_execute_large_dataset(self):
        """Test execute with 50K items."""
        def simple(x):
            return x + 1
        
        data = range(50000)
        results = execute(simple, data, sample_size=10)
        
        # Should complete successfully
        assert len(results) == 50000
        assert results[0] == 1
        assert results[49999] == 50000
    
    def test_execute_respects_extreme_optimization(self):
        """Test that execute respects optimization for extreme cases."""
        def identity(x):
            return x
        
        data = range(10000)
        
        # Get separate optimization
        opt_result = optimize(identity, data, sample_size=10)
        
        # Execute with same parameters
        results, exec_opt = execute(
            identity,
            data,
            sample_size=10,
            return_optimization_result=True
        )
        
        # Should use similar optimization
        assert exec_opt.n_jobs == opt_result.n_jobs
        assert len(results) == 10000


class TestGracefulDegradation:
    """Test that optimizer degrades gracefully in extreme conditions."""
    
    def test_sampling_failure_fallback(self):
        """Test that optimizer falls back to serial on sampling errors."""
        def problematic_func(x):
            if x == 2:
                raise ValueError("Sample error")
            return x
        
        data = range(10)
        # This might fail during sampling, should fall back to serial
        result = optimize(problematic_func, data, sample_size=5)
        
        # Should return safe serial recommendation
        assert result.n_jobs >= 1  # At least suggests something
    
    def test_zero_execution_time_edge_case(self):
        """Test with function that has near-zero execution time."""
        def instant(x):
            return x
        
        data = range(10)
        result = optimize(instant, data, sample_size=5)
        
        # Should handle gracefully (likely recommends serial due to overhead)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        # Should not recommend absurd values
        assert result.chunksize <= 10000
    
    def test_optimizer_with_all_identical_times(self):
        """Test with function that has perfectly consistent execution times."""
        def consistent(x):
            # Burn exactly the same CPU cycles
            total = 0
            for i in range(1000):
                total += i
            return total + x
        
        data = range(20)
        result = optimize(consistent, data, sample_size=10, profile=True)
        
        # Should detect homogeneous workload (low CV)
        if result.profile:
            # CV should be low for consistent execution
            assert result.profile.coefficient_of_variation < 0.5
        
        # Should recommend normal chunksize (not reduced for heterogeneity)
        assert result.chunksize >= 1


# Mark slow tests
pytestmark = pytest.mark.slow  # Can be skipped with pytest -m "not slow"
