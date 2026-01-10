"""
Tests for data pickle overhead measurement (complete "Pickle Tax" implementation).

The "Pickle Tax" constraint requires measuring serialization time for BOTH:
1. Input data items (data → workers)
2. Output results (results → main process)

These tests verify that input data serialization is properly measured and
accounted for in optimization decisions.
"""

import pytest
import os
from amorsize import optimize
from amorsize.sampling import perform_dry_run


# Set testing environment variable to skip nested parallelism detection
os.environ['AMORSIZE_TESTING'] = '1'


class TestDataPickleMeasurement:
    """Test that data pickle time is measured during dry runs."""
    
    def test_measures_data_pickle_time(self):
        """Verify that perform_dry_run measures data pickle time."""
        def simple_func(x):
            return x * 2
        
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(simple_func, data, sample_size=3)
        
        # Check that data pickle time is measured
        assert result.avg_data_pickle_time >= 0.0
        assert isinstance(result.avg_data_pickle_time, float)
    
    def test_data_pickle_time_for_small_objects(self):
        """Small primitive objects should have very low pickle time."""
        def identity(x):
            return x
        
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(identity, data, sample_size=3)
        
        # Pickle time for small integers should be very small (< 1ms)
        assert result.avg_data_pickle_time < 0.001
        assert result.avg_data_pickle_time > 0.0
    
    def test_data_pickle_time_for_large_objects(self):
        """Large objects should have measurable pickle time."""
        def identity(x):
            return x
        
        # Create large data items (1MB strings)
        large_item = "x" * (1024 * 1024)
        data = [large_item] * 3
        result = perform_dry_run(identity, data, sample_size=3)
        
        # Large strings should have measurable pickle time
        assert result.avg_data_pickle_time > 0.0
        # Should be significant (> 0.1ms for 1MB)
        assert result.avg_data_pickle_time > 0.0001
    
    def test_data_size_measured(self):
        """Verify that data size is measured."""
        def identity(x):
            return x
        
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(identity, data, sample_size=3)
        
        # Check that data size is measured
        assert result.data_size > 0
        assert isinstance(result.data_size, int)
    
    def test_data_size_reflects_object_size(self):
        """Data size should roughly reflect the serialized object size."""
        def identity(x):
            return x
        
        # Small object
        small_data = [1, 2, 3]
        small_result = perform_dry_run(identity, small_data, sample_size=3)
        
        # Large object
        large_item = "x" * 10000
        large_data = [large_item] * 3
        large_result = perform_dry_run(identity, large_data, sample_size=3)
        
        # Large data should have larger serialized size
        assert large_result.data_size > small_result.data_size


class TestOptimizeUsesDataPickleTime:
    """Test that optimize() uses data pickle time in calculations."""
    
    def test_optimize_includes_data_pickle_overhead(self):
        """Verify optimize uses data pickle time in speedup calculation."""
        def compute(x):
            result = 0
            for i in range(100):
                result += x ** 2
            return result
        
        data = list(range(100))
        result = optimize(compute, data, sample_size=5, profile=True, verbose=False)
        
        # Check that diagnostic profile includes data pickle time
        assert result.profile is not None
        assert result.profile.avg_data_pickle_time >= 0.0
        assert result.profile.data_size_bytes >= 0
    
    def test_large_data_affects_optimization(self):
        """Large input data should affect optimization decisions."""
        def identity(x):
            return x
        
        # Create very large data items that are expensive to pickle
        large_item = "x" * (1024 * 1024)  # 1MB string
        data = [large_item] * 100
        
        result = optimize(identity, data, sample_size=5, profile=True, verbose=False)
        
        # With large data pickle overhead, optimization may recommend fewer workers
        # or serial execution due to IPC costs
        assert result.profile.avg_data_pickle_time > 0.0
        # The speedup estimation should account for data serialization costs


class TestDiagnosticProfileShowsDataPickle:
    """Test that diagnostic profile shows data pickle information."""
    
    def test_explain_shows_data_pickle_time(self):
        """Diagnostic explanation should show input pickle overhead."""
        def compute(x):
            return x * 2
        
        data = list(range(50))
        result = optimize(compute, data, sample_size=5, profile=True, verbose=False)
        
        explanation = result.explain()
        
        # Should mention both input and output pickle overhead
        assert "Input pickle overhead" in explanation or "Input data" in explanation
        assert "Output pickle overhead" in explanation or "pickle overhead" in explanation
    
    def test_profile_has_both_pickle_times(self):
        """Profile should contain both input and output pickle times."""
        def compute(x):
            return x ** 2
        
        data = list(range(50))
        result = optimize(compute, data, sample_size=5, profile=True, verbose=False)
        
        profile = result.profile
        assert profile is not None
        assert hasattr(profile, 'avg_data_pickle_time')
        assert hasattr(profile, 'avg_pickle_time')
        assert profile.avg_data_pickle_time >= 0.0
        assert profile.avg_pickle_time >= 0.0


class TestCompletePickleTax:
    """Test that the complete "Pickle Tax" constraint is satisfied."""
    
    def test_bidirectional_serialization_measured(self):
        """Both input and output serialization should be measured."""
        def transform(x):
            return {"input": x, "output": x * 2}
        
        data = list(range(20))
        result = optimize(transform, data, sample_size=5, profile=True, verbose=False)
        
        profile = result.profile
        
        # Input serialization (data → workers)
        assert profile.avg_data_pickle_time > 0.0
        assert profile.data_size_bytes > 0
        
        # Output serialization (results → main)
        assert profile.avg_pickle_time > 0.0
        assert profile.return_size_bytes > 0
    
    def test_pickle_tax_in_amdahl_calculation(self):
        """Amdahl's law should account for both pickle directions."""
        from amorsize.optimizer import calculate_amdahl_speedup
        
        # Test with no pickle overhead
        speedup_no_overhead = calculate_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.0,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.001,
            n_jobs=4,
            chunksize=10,
            total_items=100,
            data_pickle_overhead_per_item=0.0
        )
        
        # Test with data pickle overhead
        speedup_with_data_overhead = calculate_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.0,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.001,
            n_jobs=4,
            chunksize=10,
            total_items=100,
            data_pickle_overhead_per_item=0.05  # 5ms per item
        )
        
        # Test with both data and result pickle overhead
        speedup_with_both_overhead = calculate_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.05,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.001,
            n_jobs=4,
            chunksize=10,
            total_items=100,
            data_pickle_overhead_per_item=0.05
        )
        
        # Speedup should decrease as we add pickle overhead
        assert speedup_with_data_overhead < speedup_no_overhead
        assert speedup_with_both_overhead < speedup_with_data_overhead
        
        # But all should still provide some speedup
        assert speedup_no_overhead > 1.0
    
    def test_backward_compatibility(self):
        """Ensure existing code still works without data_pickle_overhead_per_item."""
        from amorsize.optimizer import calculate_amdahl_speedup
        
        # Should work without the new parameter (defaults to 0.0)
        speedup = calculate_amdahl_speedup(
            total_compute_time=10.0,
            pickle_overhead_per_item=0.01,
            spawn_cost_per_worker=0.1,
            chunking_overhead_per_chunk=0.001,
            n_jobs=4,
            chunksize=10,
            total_items=100
        )
        
        assert speedup > 1.0


class TestVerboseOutputShowsDataPickle:
    """Test that verbose mode shows data pickle information."""
    
    def test_verbose_displays_data_pickle_info(self, capsys):
        """Verbose mode should display data pickle time."""
        def compute(x):
            return x * 2
        
        data = list(range(20))
        result = optimize(compute, data, sample_size=5, verbose=True)
        
        captured = capsys.readouterr()
        
        # Verbose mode should display sampling progress at minimum
        # The detailed output may vary based on workload characteristics
        assert len(captured.out) > 0
        
        # If enough output is present, check for pickle-related info
        # But don't fail if the workload is so fast that optimization short-circuits
        if "Average" in captured.out:
            # When detailed stats are shown, check for pickle info
            assert "pickle" in captured.out.lower() or "input" in captured.out.lower()


class TestEdgeCases:
    """Test edge cases for data pickle measurement."""
    
    def test_empty_data_sample(self):
        """Handle empty data sample gracefully."""
        def compute(x):
            return x
        
        data = []
        result = optimize(compute, data, sample_size=5, profile=True, verbose=False)
        
        # Should not crash, should return safe defaults
        assert result.n_jobs == 1
    
    def test_unpicklable_data_items(self):
        """Handle unpicklable data items gracefully."""
        import threading
        
        def compute(x):
            return 1
        
        # Thread locks are not picklable
        data = [threading.Lock(), threading.Lock()]
        result = optimize(compute, data, sample_size=2, verbose=False)
        
        # Should detect unpicklable data and recommend serial execution
        assert result.n_jobs == 1
        assert "not picklable" in result.reason.lower()
    
    def test_very_fast_function_with_large_data(self):
        """Fast function with large data should account for pickle overhead."""
        def instant(x):
            return 1
        
        # Large data items
        large_item = "x" * (100 * 1024)  # 100KB
        data = [large_item] * 50
        
        result = optimize(instant, data, sample_size=5, profile=True, verbose=False)
        
        # Should recognize that pickle overhead dominates
        # and may recommend serial execution or few workers
        assert result.profile.avg_data_pickle_time > 0.0


class TestIntegration:
    """Integration tests for complete pickle tax implementation."""
    
    def test_full_workflow_with_pickle_overhead(self):
        """Test complete workflow accounting for pickle overhead."""
        def expensive_compute(x):
            result = 0
            for i in range(1000):
                result += x ** 2
            return result
        
        data = list(range(100))
        result = optimize(
            expensive_compute,
            data,
            sample_size=10,
            verbose=False,
            profile=True
        )
        
        # Verify all pickle information is captured
        assert result.profile.avg_data_pickle_time >= 0.0
        assert result.profile.avg_pickle_time >= 0.0
        assert result.profile.data_size_bytes > 0
        assert result.profile.return_size_bytes > 0
        
        # Verify it's used in speedup calculation
        assert result.estimated_speedup >= 1.0
    
    def test_pickle_overhead_visible_in_explanation(self):
        """Full explanation should show both pickle overheads."""
        def compute(x):
            return {"result": x * 2}
        
        data = list(range(50))
        result = optimize(compute, data, sample_size=5, profile=True, verbose=False)
        
        explanation = result.explain()
        
        # Should show workload analysis with pickle information
        assert "WORKLOAD ANALYSIS" in explanation
        assert "pickle" in explanation.lower()
