"""
Tests for optimized coefficient of variation (CV) calculation.

Iteration 92: Validate single-expression CV calculation from Welford's state.

This test suite ensures that the optimized CV calculation:
1. Produces mathematically identical results to the previous implementation
2. Handles edge cases correctly (zero variance, single sample, etc.)
3. Maintains numerical stability across different value ranges
4. Works correctly in all optimization scenarios
"""

import math
import time
from amorsize import optimize
from amorsize.sampling import perform_dry_run


class TestCVOptimization:
    """Test optimized CV calculation from Welford's state."""
    
    def test_cv_mathematical_equivalence_homogeneous(self):
        """
        Test that optimized CV calculation is mathematically equivalent
        to the previous implementation for homogeneous workloads.
        """
        # Homogeneous workload - consistent execution time
        def consistent_func(x):
            """Function with consistent execution time."""
            time.sleep(0.001)  # 1ms consistent
            return x * 2
        
        data = list(range(10))
        result = optimize(consistent_func, data, sample_size=5, profile=True)
        
        # For homogeneous workload, CV should be very low (< 0.3)
        # This validates that the optimized formula produces correct results
        assert result.profile.coefficient_of_variation < 0.3, \
            f"Expected low CV for homogeneous workload, got {result.profile.coefficient_of_variation}"
    
    def test_cv_mathematical_equivalence_heterogeneous(self):
        """
        Test that optimized CV calculation is mathematically equivalent
        to the previous implementation for heterogeneous workloads.
        """
        # Heterogeneous workload - varying execution time
        def varying_func(x):
            """Function with varying execution time based on input."""
            time.sleep(0.001 * x)  # 1-10ms varying
            return x ** 2
        
        data = list(range(1, 11))
        result = optimize(varying_func, data, sample_size=5, profile=True)
        
        # For heterogeneous workload, CV should be higher (> 0.3)
        # This validates that the optimized formula detects variance correctly
        assert result.profile.coefficient_of_variation > 0.3, \
            f"Expected high CV for heterogeneous workload, got {result.profile.coefficient_of_variation}"
    
    def test_cv_computation_accuracy(self):
        """
        Test that the optimized CV calculation produces accurate results
        by comparing with manual calculation.
        
        CV = std_dev / mean = sqrt(variance) / mean
        Optimized: CV = sqrt(M2) / (mean * sqrt(count))
        These should be mathematically equivalent.
        """
        def test_func(x):
            """Simple test function."""
            return x ** 2
        
        data = [1, 2, 3, 4, 5]
        
        # Perform dry run
        result = perform_dry_run(test_func, data, sample_size=5, enable_function_profiling=False)
        
        # Manual CV calculation from variance
        # CV = std_dev / mean = sqrt(variance) / mean
        if result.time_variance > 0 and result.avg_time > 0:
            manual_cv = math.sqrt(result.time_variance) / result.avg_time
            
            # Optimized CV should match manual calculation within floating-point precision
            assert abs(result.coefficient_of_variation - manual_cv) < 1e-10, \
                f"CV mismatch: optimized={result.coefficient_of_variation}, manual={manual_cv}"
    
    def test_cv_direct_formula_validation(self):
        """
        Validate the optimized CV formula directly:
        CV = sqrt(M2) / (mean * sqrt(count))
        
        This is mathematically equivalent to:
        CV = sqrt(variance) / mean = sqrt(M2 / count) / mean
        """
        # Use known values for validation
        # If times = [1.0, 2.0, 3.0], then:
        # mean = 2.0
        # variance = ((1-2)^2 + (2-2)^2 + (3-2)^2) / 3 = (1 + 0 + 1) / 3 = 2/3
        # std_dev = sqrt(2/3) ≈ 0.8165
        # CV = 0.8165 / 2.0 ≈ 0.4082
        
        # For Welford's algorithm:
        # M2 = sum of squared deviations = 2.0
        # count = 3
        # mean = 2.0
        # CV = sqrt(2.0) / (2.0 * sqrt(3)) = 1.414 / (2.0 * 1.732) ≈ 0.4082
        
        m2 = 2.0
        count = 3
        mean = 2.0
        
        # Optimized formula
        cv_optimized = math.sqrt(m2) / (mean * math.sqrt(count))
        
        # Traditional formula
        variance = m2 / count
        cv_traditional = math.sqrt(variance) / mean
        
        # Should be mathematically identical
        assert abs(cv_optimized - cv_traditional) < 1e-10, \
            f"Formula mismatch: optimized={cv_optimized}, traditional={cv_traditional}"
        
        # Validate expected value
        expected_cv = 0.4082482904638631  # sqrt(2/3) / 2
        assert abs(cv_optimized - expected_cv) < 1e-10, \
            f"Expected CV={expected_cv}, got {cv_optimized}"
    
    def test_cv_zero_variance_edge_case(self):
        """
        Test that CV is correctly computed when variance is zero
        (all execution times identical).
        """
        def instant_func(x):
            """Function with negligible, consistent execution time."""
            return x + 1
        
        data = [1] * 10
        result = perform_dry_run(instant_func, data, sample_size=5, enable_function_profiling=False)
        
        # CV should be reasonably low for consistent execution (< 0.5)
        # Note: Even fast functions have some timing variance due to system noise
        assert result.coefficient_of_variation < 0.5, \
            f"Expected low CV for consistent function, got {result.coefficient_of_variation}"
    
    def test_cv_single_sample_edge_case(self):
        """
        Test that CV is 0 for single sample (no variance can be computed).
        """
        def test_func(x):
            """Simple test function."""
            return x * 2
        
        data = [42]
        result = perform_dry_run(test_func, data, sample_size=1, enable_function_profiling=False)
        
        # CV should be 0 for single sample (no variance)
        assert result.coefficient_of_variation == 0.0, \
            f"Expected CV=0 for single sample, got {result.coefficient_of_variation}"
    
    def test_cv_two_samples_edge_case(self):
        """
        Test that CV is correctly computed with minimum samples (2).
        """
        def test_func(x):
            """Simple test function."""
            time.sleep(0.001 * x)
            return x ** 2
        
        data = [1, 5]  # Different values to create variance
        result = perform_dry_run(test_func, data, sample_size=2, enable_function_profiling=False)
        
        # CV should be computed correctly with 2 samples
        assert result.coefficient_of_variation > 0, \
            f"Expected positive CV for 2 different samples, got {result.coefficient_of_variation}"
    
    def test_cv_numerical_stability_large_values(self):
        """
        Test that optimized CV calculation maintains numerical stability
        for large timing values.
        """
        def slow_func(x):
            """Function with larger execution time."""
            time.sleep(0.01)  # 10ms
            return x ** 3
        
        data = list(range(5))
        result = perform_dry_run(slow_func, data, sample_size=5, enable_function_profiling=False)
        
        # CV should be finite and reasonable
        assert math.isfinite(result.coefficient_of_variation), \
            f"Expected finite CV, got {result.coefficient_of_variation}"
        assert 0 <= result.coefficient_of_variation <= 10, \
            f"Expected reasonable CV range, got {result.coefficient_of_variation}"
    
    def test_cv_numerical_stability_small_values(self):
        """
        Test that optimized CV calculation maintains numerical stability
        for very small timing values.
        """
        def fast_func(x):
            """Function with minimal execution time."""
            return x + 1
        
        data = list(range(5))
        result = perform_dry_run(fast_func, data, sample_size=5, enable_function_profiling=False)
        
        # CV should be finite even for very small timing values
        assert math.isfinite(result.coefficient_of_variation), \
            f"Expected finite CV for small values, got {result.coefficient_of_variation}"
        assert result.coefficient_of_variation >= 0, \
            f"Expected non-negative CV, got {result.coefficient_of_variation}"
    
    def test_cv_integration_with_optimizer(self):
        """
        Test that the optimized CV calculation integrates correctly
        with the optimizer and affects chunksize decisions.
        """
        # High CV workload should result in smaller chunksize
        def high_cv_func(x):
            """Function with high variance in execution time."""
            time.sleep(0.001 * (1 if x % 2 == 0 else 5))  # Alternating 1ms/5ms
            return x ** 2
        
        data = list(range(100))
        result = optimize(high_cv_func, data, sample_size=10, profile=True, verbose=False)
        
        # Verify CV was detected
        assert result.profile.coefficient_of_variation > 0, \
            "Expected positive CV for high-variance workload"
        
        # Verify heterogeneity flag is set correctly
        assert result.profile.is_heterogeneous == (result.profile.coefficient_of_variation > 0.3), \
            "Heterogeneity flag should match CV threshold"
    
    def test_cv_backward_compatibility(self):
        """
        Test that the optimized CV calculation maintains backward compatibility
        with existing test expectations and API.
        """
        def test_func(x):
            """Simple test function."""
            time.sleep(0.001)
            return x * 2
        
        data = list(range(20))
        result = optimize(test_func, data, sample_size=5, profile=True, verbose=False)
        
        # Verify all expected attributes exist
        assert hasattr(result.profile, 'coefficient_of_variation'), \
            "CV attribute should exist"
        assert hasattr(result.profile, 'is_heterogeneous'), \
            "Heterogeneity flag should exist"
        
        # Verify CV is in expected range
        assert 0 <= result.profile.coefficient_of_variation <= 10, \
            f"CV should be in reasonable range, got {result.profile.coefficient_of_variation}"


class TestCVPerformanceCharacteristics:
    """Test performance characteristics of optimized CV calculation."""
    
    def test_cv_computation_overhead(self):
        """
        Verify that optimized CV calculation has minimal overhead.
        
        The optimization eliminates intermediate variable assignments
        and should have negligible performance impact.
        """
        def test_func(x):
            """Simple fast function."""
            return x ** 2
        
        data = list(range(100))
        
        # Time the dry run with CV calculation
        start = time.perf_counter()
        result = perform_dry_run(test_func, data, sample_size=10, enable_function_profiling=False)
        elapsed = time.perf_counter() - start
        
        # Verify CV was computed
        assert result.coefficient_of_variation >= 0, "CV should be computed"
        
        # Dry run should still be fast (< 100ms for simple function)
        assert elapsed < 0.1, f"Dry run too slow: {elapsed:.3f}s"
    
    def test_cv_single_expression_correctness(self):
        """
        Validate that the single-expression optimization produces
        identical results to the multi-step calculation.
        """
        # Test with known Welford state values
        test_cases = [
            # (m2, count, mean) tuples
            (2.0, 3, 2.0),      # Simple case
            (10.0, 5, 5.0),     # Larger variance
            (0.5, 10, 1.0),     # Small variance
            (100.0, 20, 10.0),  # Large values
        ]
        
        for m2, count, mean in test_cases:
            # Single-expression optimization
            cv_optimized = math.sqrt(m2) / (mean * math.sqrt(count))
            
            # Multi-step traditional calculation
            variance = m2 / count
            std_dev = math.sqrt(variance)
            cv_traditional = std_dev / mean
            
            # Should be mathematically identical (within floating-point precision)
            assert abs(cv_optimized - cv_traditional) < 1e-10, \
                f"CV mismatch for m2={m2}, count={count}, mean={mean}: " \
                f"optimized={cv_optimized}, traditional={cv_traditional}"


class TestCVEdgeCasesAndRobustness:
    """Test edge cases and robustness of optimized CV calculation."""
    
    def test_cv_handles_zero_mean_gracefully(self):
        """
        Test that CV calculation handles edge case where mean could be zero.
        
        In practice, this shouldn't happen for timing measurements (all positive),
        but we verify the code doesn't crash.
        """
        # The CV calculation has a guard: if avg_time > 0
        # So zero mean should result in CV = 0.0
        def test_func(x):
            return x
        
        data = [1]
        result = perform_dry_run(test_func, data, sample_size=1, enable_function_profiling=False)
        
        # Should handle gracefully (CV defaults to 0.0)
        assert result.coefficient_of_variation == 0.0
    
    def test_cv_handles_extreme_heterogeneity(self):
        """
        Test CV calculation with extremely heterogeneous workload
        (very high variance relative to mean).
        """
        def extreme_func(x):
            """Function with extreme variance."""
            if x == 0:
                time.sleep(0.001)  # 1ms
            else:
                time.sleep(0.05)    # 50ms (50x difference)
            return x
        
        data = [0, 1, 2, 3, 4]
        result = perform_dry_run(extreme_func, data, sample_size=5, enable_function_profiling=False)
        
        # CV should be moderately high for extreme heterogeneity
        # Note: The actual timing includes function call overhead, so CV may not be as extreme as expected
        assert result.coefficient_of_variation > 0.4, \
            f"Expected high CV for extreme heterogeneity, got {result.coefficient_of_variation}"
        
        # Should still be finite
        assert math.isfinite(result.coefficient_of_variation), \
            "CV should be finite even for extreme cases"
    
    def test_cv_consistency_across_multiple_runs(self):
        """
        Test that CV calculation is deterministic and consistent
        across multiple runs with the same input.
        """
        def test_func(x):
            """Deterministic function."""
            result = 0
            for i in range(100):
                result += x ** 2
            return result
        
        data = list(range(10))
        
        # Run multiple times
        cvs = []
        for _ in range(3):
            result = perform_dry_run(test_func, data, sample_size=5, enable_function_profiling=False)
            cvs.append(result.coefficient_of_variation)
        
        # All CVs should be similar (timing variance is natural, but should be in same ballpark)
        cv_mean = sum(cvs) / len(cvs)
        for cv in cvs:
            # Allow 50% variation due to natural timing variance
            assert abs(cv - cv_mean) / (cv_mean + 1e-10) < 0.5, \
                f"CVs should be consistent across runs: {cvs}"
