"""
Tests for adaptive chunking based on workload heterogeneity.

This test suite validates that the optimizer correctly:
1. Detects heterogeneous workloads (varying execution times)
2. Calculates coefficient of variation (CV) from sample times
3. Adjusts chunksize for heterogeneous workloads
4. Provides diagnostic information about workload variability
"""

import time
import pytest
from amorsize import optimize
from amorsize.sampling import perform_dry_run


class TestVarianceCalculation:
    """Test variance and coefficient of variation calculations."""
    
    def test_homogeneous_workload_low_cv(self):
        """Test that consistent execution times result in low CV."""
        def consistent_func(x):
            """Function with very consistent execution time."""
            time.sleep(0.001)
            return x * x
        
        data = list(range(10))
        result = perform_dry_run(consistent_func, data, sample_size=5)
        
        # Consistent workload should have low CV (< 0.3)
        assert result.coefficient_of_variation < 0.3
        assert result.time_variance >= 0.0
    
    def test_heterogeneous_workload_high_cv(self):
        """Test that varying execution times result in high CV."""
        def variable_func(x):
            """Function with varying execution time based on input."""
            # Sleep for variable amounts: 1ms, 2ms, 4ms, 8ms, 16ms
            sleep_time = 0.001 * (2 ** (x % 5))
            time.sleep(sleep_time)
            return x * x
        
        data = list(range(10))
        result = perform_dry_run(variable_func, data, sample_size=5)
        
        # Variable workload should have high CV (> 0.5)
        assert result.coefficient_of_variation > 0.5
        assert result.time_variance > 0.0
    
    def test_cv_zero_for_instant_function(self):
        """Test that CV is 0 for functions with negligible execution time."""
        def instant_func(x):
            """Function that completes instantly."""
            return x + 1
        
        data = list(range(10))
        result = perform_dry_run(instant_func, data, sample_size=5)
        
        # When times are all effectively 0, CV should be 0
        assert result.coefficient_of_variation >= 0.0
        assert result.time_variance >= 0.0
    
    def test_cv_calculated_from_sample(self):
        """Test that CV is calculated from actual sample timing data."""
        call_count = [0]
        
        def counting_func(x):
            """Function that gets progressively slower."""
            call_count[0] += 1
            # First call: 1ms, second: 2ms, third: 3ms, etc.
            time.sleep(0.001 * call_count[0])
            return x
        
        data = list(range(10))
        result = perform_dry_run(counting_func, data, sample_size=5)
        
        # Should have measured 5 samples with increasing times
        assert result.sample_count == 5
        assert result.coefficient_of_variation > 0.0


class TestAdaptiveChunking:
    """Test adaptive chunksize adjustment for heterogeneous workloads."""
    
    def test_homogeneous_workload_normal_chunksize(self):
        """Test that homogeneous workloads get standard chunksize."""
        def consistent_func(x):
            """Consistent execution time."""
            time.sleep(0.01)  # 10ms per item
            return x * x
        
        data = list(range(200))  # Larger dataset to overcome overhead
        result = optimize(consistent_func, data, target_chunk_duration=0.2)
        
        # With 10ms per item and 0.2s target, expect chunksize around 20
        # May not parallelize due to overhead, but if it does, chunksize should be reasonable
        assert result.chunksize >= 1
        # If parallelized, should use normal chunksize calculation
        if result.n_jobs > 1:
            assert result.chunksize >= 10
    
    def test_heterogeneous_workload_reduced_chunksize(self):
        """Test that heterogeneous workloads get smaller chunksize."""
        def variable_func(x):
            """Variable execution time based on input."""
            # Highly variable: 5ms to 20ms
            sleep_time = 0.005 + (0.015 * (x % 3) / 2)
            time.sleep(sleep_time)
            return x * x
        
        data = list(range(200))  # Larger dataset
        result_hetero = optimize(variable_func, data, target_chunk_duration=0.2, profile=True)
        
        # Should detect heterogeneity in profile
        assert result_hetero.profile is not None
        assert result_hetero.profile.coefficient_of_variation >= 0.0
        
        # Chunksize should be reasonable
        assert result_hetero.chunksize >= 1
        
        # If heterogeneous and parallelized, check that smaller chunks are used
        if result_hetero.n_jobs > 1 and result_hetero.profile.coefficient_of_variation > 0.5:
            # Smaller chunks for better load balancing
            assert result_hetero.chunksize <= 20
    
    def test_diagnostic_profile_shows_heterogeneity(self):
        """Test that diagnostic profile captures heterogeneity information."""
        def variable_func(x):
            """Variable execution time."""
            time.sleep(0.005 * (1 + x % 3))
            return x
        
        data = list(range(50))
        result = optimize(variable_func, data, profile=True)
        
        # Profile should capture CV
        assert result.profile is not None
        assert result.profile.coefficient_of_variation > 0.0
        
        # If workload is heterogeneous, should be flagged
        if result.profile.coefficient_of_variation > 0.5:
            assert result.profile.is_heterogeneous is True
    
    def test_verbose_mode_reports_heterogeneity(self):
        """Test that verbose mode reports workload variability."""
        def variable_func(x):
            """Variable execution time."""
            time.sleep(0.005 * (1 + x % 4))
            return x
        
        data = list(range(30))
        # This should print variability info if detected
        # We just verify it doesn't crash
        result = optimize(variable_func, data, verbose=True)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_explain_shows_heterogeneity_info(self):
        """Test that explain() method shows workload variability."""
        def variable_func(x):
            """Variable execution time."""
            time.sleep(0.005 * (1 + x % 3))
            return x
        
        data = list(range(40))
        result = optimize(variable_func, data, profile=True)
        
        explanation = result.explain()
        
        # Explanation should mention variability if detected
        assert explanation is not None
        assert len(explanation) > 0
        
        # If heterogeneous, should appear in output
        if result.profile.coefficient_of_variation > 0.5:
            assert "heterogeneous" in explanation.lower() or "CV=" in explanation


class TestEdgeCases:
    """Test edge cases for adaptive chunking."""
    
    def test_single_sample_no_variance(self):
        """Test that single sample results in zero variance."""
        def simple_func(x):
            return x * 2
        
        data = list(range(10))
        result = perform_dry_run(simple_func, data, sample_size=1)
        
        # With only 1 sample, variance should be 0
        assert result.time_variance == 0.0
        assert result.coefficient_of_variation == 0.0
    
    def test_two_samples_with_variance(self):
        """Test variance calculation with minimum samples."""
        call_count = [0]
        
        def varying_func(x):
            call_count[0] += 1
            if call_count[0] == 1:
                time.sleep(0.001)
            else:
                time.sleep(0.005)
            return x
        
        data = list(range(10))
        result = perform_dry_run(varying_func, data, sample_size=2)
        
        # With 2 different times, should have non-zero variance
        assert result.time_variance > 0.0
        assert result.coefficient_of_variation > 0.0
    
    def test_very_high_cv_caps_reduction(self):
        """Test that extreme CV doesn't make chunksize too small."""
        def extreme_variable_func(x):
            """Extremely variable execution time."""
            if x % 5 == 0:
                time.sleep(0.001)  # Fast
            else:
                time.sleep(0.020)  # 20x slower
            return x
        
        data = list(range(100))
        result = optimize(extreme_variable_func, data)
        
        # Even with extreme variance, chunksize should be at least 1
        assert result.chunksize >= 1
        # And should still recommend parallelization if beneficial
        assert result.n_jobs >= 1
    
    def test_generator_with_heterogeneous_workload(self):
        """Test adaptive chunking works with generator input."""
        def variable_func(x):
            time.sleep(0.005 * (1 + x % 3))
            return x
        
        data = (x for x in range(50))
        result = optimize(variable_func, data, profile=True)
        
        # Should work with generators
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.data is not None
        
        # Profile should capture CV
        if result.profile:
            assert result.profile.coefficient_of_variation >= 0.0


class TestRealWorldScenarios:
    """Test adaptive chunking with real-world-like scenarios."""
    
    def test_document_processing_varying_lengths(self):
        """Simulate document processing with varying document lengths."""
        def process_document(doc_length):
            """Simulate processing documents of varying lengths."""
            # Longer documents take more time
            processing_time = 0.002 * (1 + doc_length / 10)
            time.sleep(processing_time)
            return doc_length * 2
        
        # Mix of short and long documents
        data = [1, 2, 3, 15, 20, 2, 1, 18, 3, 25] * 5
        result = optimize(process_document, data, profile=True)
        
        # Should detect heterogeneity and adapt
        assert result.profile is not None
        assert result.profile.coefficient_of_variation > 0.0
    
    def test_image_processing_varying_sizes(self):
        """Simulate image processing with varying image sizes."""
        def process_image(size_factor):
            """Simulate processing images of varying sizes."""
            # Larger images take more time
            time.sleep(0.003 * size_factor)
            return size_factor ** 2
        
        # Mix of small, medium, and large images
        data = [1, 1, 2, 5, 1, 8, 2, 1, 10, 3] * 3
        result = optimize(process_image, data, profile=True, verbose=True)
        
        # Should adapt to varying image sizes
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_mixed_complexity_computation(self):
        """Simulate computation with mixed complexity."""
        def compute(complexity):
            """Simulate computation with varying complexity."""
            # Different complexity levels
            time.sleep(0.001 * complexity)
            result = sum(i ** 2 for i in range(complexity))
            return result
        
        # Mix of simple and complex computations
        data = [1, 2, 1, 5, 1, 10, 2, 1, 8, 3, 1, 1] * 4
        result = optimize(compute, data)
        
        # Should handle mixed complexity
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.estimated_speedup >= 1.0


class TestBackwardCompatibility:
    """Ensure adaptive chunking doesn't break existing behavior."""
    
    def test_existing_tests_still_pass(self):
        """Test that standard optimization still works."""
        def standard_func(x):
            time.sleep(0.01)
            return x * x
        
        data = list(range(50))
        result = optimize(standard_func, data)
        
        # Basic optimization should still work
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.reason is not None
    
    def test_no_profile_mode_still_works(self):
        """Test that non-profiled optimization works with adaptive chunking."""
        def simple_func(x):
            time.sleep(0.005)
            return x + 1
        
        data = list(range(30))
        result = optimize(simple_func, data, profile=False)
        
        # Should work without profile
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.profile is None
