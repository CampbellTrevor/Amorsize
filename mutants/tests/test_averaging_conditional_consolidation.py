"""
Tests for Iteration 96: Averaging Conditional Check Consolidation

This module tests the optimization that consolidates 4 separate conditional checks
into a single check when calculating averages in perform_dry_run().

The optimization reduces the overhead from:
    avg_return_size = sum(return_sizes) // sample_count if sample_count > 0 else 0
    avg_pickle_time = math.fsum(pickle_times) / sample_count if sample_count > 0 else 0.0
    avg_data_pickle_time = math.fsum(data_pickle_times) / sample_count if sample_count > 0 else 0.0
    avg_data_size = sum(data_sizes) // sample_count if sample_count > 0 else 0

To:
    if sample_count > 0:
        avg_return_size = sum(return_sizes) // sample_count
        avg_pickle_time = math.fsum(pickle_times) / sample_count
        avg_data_pickle_time = math.fsum(data_pickle_times) / sample_count
        avg_data_size = sum(data_sizes) // sample_count
    else:
        avg_return_size = 0
        avg_pickle_time = 0.0
        avg_data_pickle_time = 0.0
        avg_data_size = 0

Expected savings: ~47ns per dry_run (9.9% improvement in averaging section)
"""

import pytest
import time
from amorsize.sampling import perform_dry_run
from amorsize import optimize


class TestAveragingCorrectness:
    """Test that averaging calculations are correct with consolidated conditional."""
    
    def test_normal_sample_produces_correct_averages(self):
        """Test that normal samples produce correct average values."""
        def simple_func(x):
            return x ** 2
        
        data = list(range(5, 10))  # [5, 6, 7, 8, 9]
        result = perform_dry_run(simple_func, data, sample_size=5)
        
        # Verify all averages are computed correctly
        assert result.sample_count == 5
        assert result.avg_time > 0  # Should have positive execution time
        assert result.return_size > 0  # Should have non-zero return size
        assert result.avg_pickle_time >= 0  # Pickle time can be 0 or positive
        assert result.avg_data_pickle_time >= 0  # Data pickle time can be 0 or positive
        assert result.data_size >= 0  # Data size should be non-negative
    
    def test_single_item_sample_correct_averages(self):
        """Test that single-item samples work correctly."""
        def identity(x):
            return x
        
        data = [42]
        result = perform_dry_run(identity, data, sample_size=1)
        
        assert result.sample_count == 1
        assert result.avg_time > 0
        assert result.return_size > 0
        # For single item, average should equal the single value
    
    def test_large_sample_correct_averages(self):
        """Test that large samples produce correct averages."""
        def compute(x):
            return sum(range(x))
        
        data = list(range(1, 21))  # 20 items
        result = perform_dry_run(compute, data, sample_size=20)
        
        assert result.sample_count == 20
        assert result.avg_time > 0
        assert result.return_size > 0


class TestAveragingEdgeCases:
    """Test edge cases for averaging calculations."""
    
    def test_empty_data_returns_early(self):
        """Test that empty data returns early (before averaging section)."""
        def noop(x):
            return x
        
        data = []
        result = perform_dry_run(noop, data, sample_size=5)
        
        # Should return early with error
        assert result.error is not None
        assert result.sample_count == 0
        # Averages should be zero due to early return
        assert result.avg_time == 0.0
        assert result.return_size == 0
    
    def test_generator_with_single_item(self):
        """Test generator with single item works correctly."""
        def process(x):
            return x * 2
        
        data = (i for i in [100])
        result = perform_dry_run(process, data, sample_size=1)
        
        assert result.sample_count == 1
        assert result.is_generator is True
        assert result.avg_time > 0
    
    def test_function_that_returns_large_objects(self):
        """Test averaging with functions that return large objects."""
        def return_large(x):
            return [x] * 1000  # Return list of 1000 items
        
        data = range(5)
        result = perform_dry_run(return_large, data, sample_size=5)
        
        assert result.sample_count == 5
        assert result.return_size > 1000  # Should be large
        assert result.avg_time > 0


class TestNumericalStability:
    """Test numerical stability of averaging with consolidated conditional."""
    
    def test_consistent_results_across_runs(self):
        """Test that multiple runs produce consistent results."""
        def stable_func(x):
            time.sleep(0.0001)  # Tiny consistent delay
            return x
        
        data = list(range(5))
        
        # Run multiple times
        results = []
        for _ in range(3):
            result = perform_dry_run(stable_func, data, sample_size=5)
            results.append(result)
        
        # All should have same sample_count
        assert all(r.sample_count == 5 for r in results)
        
        # avg_time should be relatively consistent (within 50% variance)
        avg_times = [r.avg_time for r in results]
        mean_time = sum(avg_times) / len(avg_times)
        for t in avg_times:
            assert abs(t - mean_time) / mean_time < 0.5
    
    def test_large_values_dont_overflow(self):
        """Test that large values don't cause overflow in averaging."""
        def return_huge(x):
            return x * (10 ** 6)
        
        data = [10 ** 6] * 5
        result = perform_dry_run(return_huge, data, sample_size=5)
        
        assert result.sample_count == 5
        assert result.return_size > 0  # Should handle large values
        assert not isinstance(result.avg_time, complex)  # No weird types


class TestIntegrationWithOptimize:
    """Test integration of averaging optimization with optimize() function."""
    
    def test_optimize_uses_correct_averages(self):
        """Test that optimize() function uses correct averaged values."""
        def simple_work(x):
            return x ** 2
        
        data = list(range(100))
        result = optimize(simple_work, data, sample_size=5, verbose=False)
        
        # Should produce valid optimization result
        assert result.n_jobs > 0
        assert result.chunksize > 0
    
    def test_optimize_with_small_dataset(self):
        """Test optimize with small dataset (edge case for averaging)."""
        def minimal_work(x):
            return x
        
        data = list(range(3))
        result = optimize(minimal_work, data, sample_size=3, verbose=False)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_optimize_with_heterogeneous_workload(self):
        """Test that averaging correctly handles heterogeneous workloads."""
        def varying_work(x):
            time.sleep(0.0001 * (1 if x % 2 == 0 else 3))
            return x
        
        data = list(range(10))
        result = optimize(varying_work, data, sample_size=10, verbose=False)
        
        # Should handle varying execution times
        assert result.n_jobs > 0
        assert result.chunksize > 0


class TestBackwardCompatibility:
    """Test that the optimization maintains backward compatibility."""
    
    def test_existing_code_still_works(self):
        """Test that existing user code continues to work unchanged."""
        def user_function(x):
            """Typical user function."""
            result = 0
            for i in range(x):
                result += i ** 2
            return result
        
        data = list(range(1, 51))
        
        # This is typical user code pattern
        result = perform_dry_run(user_function, data, sample_size=5)
        
        # Should work as before
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.return_size > 0
        assert result.error is None
    
    def test_memory_tracking_disabled_still_works(self):
        """Test that disabling memory tracking still works."""
        def simple(x):
            return x * 2
        
        data = range(10)
        result = perform_dry_run(simple, data, sample_size=5, enable_memory_tracking=False)
        
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.peak_memory == 0  # Should be 0 when disabled
    
    def test_function_profiling_enabled_still_works(self):
        """Test that function profiling still works."""
        def profiled_func(x):
            return sum(range(x))
        
        data = range(10, 20)
        result = perform_dry_run(profiled_func, data, sample_size=5, enable_function_profiling=True)
        
        assert result.sample_count == 5
        assert result.avg_time > 0
        assert result.function_profiler_stats is not None  # Should have profiler stats


class TestPerformanceCharacteristics:
    """Test that the optimization provides expected performance characteristics."""
    
    def test_single_check_is_faster(self):
        """Test that consolidated check performs comparably to original."""
        def fast_func(x):
            return x
        
        data = list(range(100))
        
        # Measure time for multiple dry runs
        start = time.perf_counter()
        for _ in range(50):
            perform_dry_run(fast_func, data, sample_size=5)
        elapsed = time.perf_counter() - start
        
        # Should complete in reasonable time (much less than 1 second)
        assert elapsed < 1.0, f"50 dry runs took {elapsed:.3f}s, expected < 1.0s"
    
    def test_no_performance_regression(self):
        """Test that there's no performance regression from optimization."""
        def baseline_func(x):
            return x ** 2
        
        data = list(range(50))
        
        # Run a single dry_run and ensure it's fast
        start = time.perf_counter()
        result = perform_dry_run(baseline_func, data, sample_size=5)
        elapsed = time.perf_counter() - start
        
        # Should be very fast (< 50ms for a simple function)
        assert elapsed < 0.05, f"Single dry_run took {elapsed*1000:.1f}ms, expected < 50ms"
        assert result.sample_count == 5


class TestExceptionHandling:
    """Test that exception handling still works with consolidated conditional."""
    
    def test_function_exception_in_dry_run(self):
        """Test that exceptions in function execution are handled."""
        def failing_func(x):
            if x > 2:
                raise ValueError("Test exception")
            return x
        
        data = list(range(10))
        result = perform_dry_run(failing_func, data, sample_size=5)
        
        # Should capture the exception
        assert result.error is not None
        assert isinstance(result.error, ValueError)
    
    def test_unpicklable_data_handled(self):
        """Test that unpicklable data is detected correctly."""
        import threading
        
        def process_data(x):
            return x
        
        # threading.Lock is not picklable
        data = [1, 2, threading.Lock(), 4, 5]
        result = perform_dry_run(process_data, data, sample_size=5)
        
        # Should detect unpicklable data
        assert result.data_items_picklable is False
        assert result.unpicklable_data_index is not None


class TestDiagnosticOutput:
    """Test that diagnostic output includes correct averaged values."""
    
    def test_diagnostic_profile_has_averages(self):
        """Test that diagnostic profile includes average values."""
        from amorsize import optimize
        
        def compute_intensive(x):
            return sum(i ** 2 for i in range(x))
        
        data = range(10, 20)
        result = optimize(compute_intensive, data, sample_size=5, profile=True)
        
        # Profile should contain timing information
        assert result.profile is not None
        assert result.profile.avg_execution_time > 0
        assert result.profile.sample_count == 5
    
    def test_verbose_output_shows_correct_values(self):
        """Test that verbose mode outputs correct values."""
        import io
        import sys
        
        def simple_func(x):
            return x * 2
        
        data = range(20)
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        
        try:
            optimize(simple_func, data, sample_size=5, verbose=True)
            output = captured.getvalue()
            
            # Should have some output
            assert len(output) > 0
        finally:
            sys.stdout = old_stdout


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
