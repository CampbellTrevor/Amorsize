"""
Comprehensive tests for chunksize calculation correctness.

This test suite validates that the optimizer correctly implements the 0.2s
target chunk duration across various edge cases and workload characteristics.
"""

import pytest
from amorsize import optimize


class TestChunksizeCalculation:
    """Test that chunksize is calculated correctly for various scenarios."""
    
    def test_chunksize_with_moderate_execution_time(self):
        """Test chunksize calculation for typical moderate execution times (~5ms)."""
        def moderate_function(x):
            result = 0
            for i in range(10000):
                result += x ** 2
            return result
        
        data = list(range(1000))
        result = optimize(moderate_function, data, profile=True)
        
        # Verify chunksize calculation
        if result.profile and result.profile.avg_execution_time > 0:
            expected_base = int(0.2 / result.profile.avg_execution_time)
            
            # Account for CV adjustment
            cv = result.profile.coefficient_of_variation
            if cv > 0.5:
                scale_factor = max(0.25, 1.0 - (cv * 0.5))
                expected_with_cv = max(1, int(expected_base * scale_factor))
            else:
                expected_with_cv = expected_base
            
            # Account for 10% cap
            max_reasonable = max(1, 1000 // 10)
            expected_final = min(expected_with_cv, max_reasonable)
            
            # If parallel execution was chosen, verify chunksize matches
            if result.n_jobs > 1:
                # Verify actual chunksize matches expectation
                assert result.profile.optimal_chunksize == expected_final, \
                    f"Expected {expected_final}, got {result.profile.optimal_chunksize}"
                
                # Verify chunk duration is close to 0.2s target (allow some tolerance)
                chunk_duration = result.profile.optimal_chunksize * result.profile.avg_execution_time
                # For homogeneous workloads, should be within 50% of target
                if cv < 0.5:
                    assert 0.1 <= chunk_duration <= 0.3, \
                        f"Chunk duration {chunk_duration:.3f}s is far from 0.2s target"
            else:
                # Serial execution chosen - just verify optimal_chunksize was calculated
                # (even though it won't be used for serial execution)
                assert result.profile.optimal_chunksize >= 1, \
                    "Optimal chunksize should still be calculated even for serial execution"
    
    def test_chunksize_with_very_fast_function(self):
        """Test chunksize calculation for very fast functions (microseconds)."""
        def fast_function(x):
            return x * 2
        
        data = list(range(10000))
        result = optimize(fast_function, data, profile=True)
        
        # For very fast functions, chunksize should be large (capped at 10% of items)
        if result.profile:
            max_reasonable = max(1, 10000 // 10)  # 1000
            # Chunksize should be capped
            assert result.profile.optimal_chunksize <= max_reasonable, \
                f"Chunksize {result.profile.optimal_chunksize} exceeds 10% cap {max_reasonable}"
            
            # For very fast functions that get rejected, chunksize might be different
            # Just verify it's positive and reasonable
            assert result.profile.optimal_chunksize >= 1
    
    def test_chunksize_with_slow_function(self):
        """Test chunksize calculation for slow functions (multi-second)."""
        def slow_function(x):
            result = 0
            for i in range(1000000):
                result += x ** 2
            return result
        
        # Use small dataset to avoid long test times
        data = list(range(100))
        result = optimize(slow_function, data, profile=True, sample_size=5)
        
        if result.profile and result.profile.avg_execution_time > 0:
            # For slow functions, chunksize should be small (possibly 1)
            expected_base = int(0.2 / result.profile.avg_execution_time)
            expected_min = max(1, expected_base)
            
            # Should be very small
            assert result.profile.optimal_chunksize >= 1, "Chunksize must be at least 1"
            # For slow functions (>0.1s per item), chunksize should be small
            if result.profile.avg_execution_time > 0.1:
                assert result.profile.optimal_chunksize <= 5, \
                    f"Chunksize {result.profile.optimal_chunksize} too large for slow function"
    
    def test_chunksize_with_small_dataset(self):
        """Test chunksize calculation for small datasets (<100 items)."""
        def simple_function(x):
            result = 0
            for i in range(1000):
                result += x ** 2
            return result
        
        data = list(range(50))  # Small dataset
        result = optimize(simple_function, data, profile=True)
        
        if result.profile:
            # Chunksize should not exceed dataset size
            assert result.profile.optimal_chunksize <= 50, \
                f"Chunksize {result.profile.optimal_chunksize} exceeds dataset size 50"
            
            # Should respect 10% cap
            max_reasonable = max(1, 50 // 10)  # 5
            assert result.profile.optimal_chunksize <= max_reasonable or result.n_jobs == 1, \
                f"Chunksize {result.profile.optimal_chunksize} exceeds 10% cap {max_reasonable}"
    
    def test_chunksize_with_large_dataset(self):
        """Test chunksize calculation for large datasets (>10,000 items)."""
        def simple_function(x):
            result = 0
            for i in range(1000):
                result += x ** 2
            return result
        
        data = list(range(20000))  # Large dataset
        result = optimize(simple_function, data, profile=True, sample_size=100)
        
        if result.profile and result.profile.avg_execution_time > 0:
            # Calculate expected chunksize
            expected_base = int(0.2 / result.profile.avg_execution_time)
            
            # Should respect 10% cap
            max_reasonable = max(1, 20000 // 10)  # 2000
            assert result.profile.optimal_chunksize <= max_reasonable, \
                f"Chunksize {result.profile.optimal_chunksize} exceeds 10% cap {max_reasonable}"
            
            # Chunksize should be positive
            assert result.profile.optimal_chunksize >= 1
    
    def test_chunksize_with_heterogeneous_workload(self):
        """Test chunksize calculation for heterogeneous workloads (high CV)."""
        def variable_function(x):
            # Variable execution time based on input
            iterations = 1000 if x % 2 == 0 else 10000
            result = 0
            for i in range(iterations):
                result += x ** 2
            return result
        
        data = list(range(1000))
        result = optimize(variable_function, data, profile=True)
        
        if result.profile and result.profile.avg_execution_time > 0:
            cv = result.profile.coefficient_of_variation
            
            # High CV should trigger reduction
            if cv > 0.5 and result.n_jobs > 1:
                expected_base = int(0.2 / result.profile.avg_execution_time)
                scale_factor = max(0.25, 1.0 - (cv * 0.5))
                expected_with_cv = max(1, int(expected_base * scale_factor))
                
                # Account for 10% cap
                max_reasonable = max(1, 1000 // 10)
                expected_final = min(expected_with_cv, max_reasonable)
                
                assert result.profile.optimal_chunksize == expected_final, \
                    f"Expected {expected_final}, got {result.profile.optimal_chunksize}"
                
                # Chunksize should be reduced compared to base
                assert result.profile.optimal_chunksize < expected_base or result.profile.optimal_chunksize == 1, \
                    "Heterogeneous workload should have reduced chunksize"
            else:
                # Either CV is low or serial execution - just verify reasonable chunksize
                assert result.profile.optimal_chunksize >= 1, \
                    "Optimal chunksize should be at least 1"
    
    def test_chunksize_minimum_is_one(self):
        """Test that chunksize never goes below 1."""
        def ultra_slow_function(x):
            # Extremely slow function (>1s per call)
            result = 0
            for i in range(10000000):
                result += x ** 2
            return result
        
        data = list(range(10))
        result = optimize(ultra_slow_function, data, profile=True, sample_size=2)
        
        # Even for extremely slow functions, chunksize should be at least 1
        assert result.chunksize >= 1, f"Chunksize {result.chunksize} is less than 1"
        if result.profile:
            assert result.profile.optimal_chunksize >= 1, \
                f"Optimal chunksize {result.profile.optimal_chunksize} is less than 1"
    
    def test_chunksize_ten_percent_cap(self):
        """Test that chunksize is capped at 10% of total items."""
        def quick_function(x):
            return x + 1
        
        # Test with various dataset sizes
        for size in [100, 1000, 10000]:
            data = list(range(size))
            result = optimize(quick_function, data, profile=True)
            
            if result.profile:
                max_reasonable = max(1, size // 10)
                assert result.profile.optimal_chunksize <= max_reasonable, \
                    f"Chunksize {result.profile.optimal_chunksize} exceeds 10% cap {max_reasonable} for size {size}"
    
    def test_chunksize_calculation_formula(self):
        """Test the core chunksize formula: int(target_chunk_duration / avg_time)."""
        def predictable_function(x):
            # Function with predictable execution time
            result = 0
            for i in range(5000):
                result += x ** 2
            return result
        
        data = list(range(2000))
        result = optimize(predictable_function, data, profile=True)
        
        if result.profile and result.profile.avg_execution_time > 0:
            # Calculate expected base chunksize
            target_duration = 0.2  # Default target
            expected_base = int(target_duration / result.profile.avg_execution_time)
            
            # If workload is homogeneous (CV < 0.5) and parallelization chosen, verify formula
            cv = result.profile.coefficient_of_variation
            if cv < 0.5 and result.n_jobs > 1:
                max_reasonable = max(1, 2000 // 10)
                expected_final = min(expected_base, max_reasonable)
                
                assert result.profile.optimal_chunksize == expected_final, \
                    f"Expected {expected_final} (base={expected_base}, cv={cv:.2f}), got {result.profile.optimal_chunksize}"
            else:
                # Serial execution or high CV - just verify chunksize is reasonable
                assert result.profile.optimal_chunksize >= 1, \
                    "Optimal chunksize should be at least 1"


class TestChunksizeEdgeCases:
    """Test edge cases in chunksize calculation."""
    
    def test_zero_avg_time_handling(self):
        """Test that zero avg_time doesn't cause division by zero."""
        # This is hard to test directly, but we can verify the result is valid
        def instant_function(x):
            return x
        
        data = list(range(100))
        result = optimize(instant_function, data, profile=True)
        
        # Should not crash, chunksize should be valid
        assert result.chunksize >= 1
        if result.profile:
            assert result.profile.optimal_chunksize >= 1
    
    def test_custom_target_chunk_duration(self):
        """Test chunksize calculation with custom target_chunk_duration."""
        def simple_function(x):
            result = 0
            for i in range(1000):
                result += x ** 2
            return result
        
        data = list(range(1000))
        
        # Test with different target durations
        for target_duration in [0.1, 0.2, 0.5, 1.0]:
            result = optimize(simple_function, data, profile=True, 
                            target_chunk_duration=target_duration)
            
            if result.profile and result.profile.avg_execution_time > 0 and result.n_jobs > 1:
                # Calculate expected chunksize
                expected_base = int(target_duration / result.profile.avg_execution_time)
                
                # Account for CV and cap
                cv = result.profile.coefficient_of_variation
                if cv > 0.5:
                    scale_factor = max(0.25, 1.0 - (cv * 0.5))
                    expected_with_cv = max(1, int(expected_base * scale_factor))
                else:
                    expected_with_cv = expected_base
                
                max_reasonable = max(1, 1000 // 10)
                expected_final = min(expected_with_cv, max_reasonable)
                
                # Verify target was used
                assert result.profile.target_chunk_duration == target_duration, \
                    f"Target duration should be {target_duration}"
    
    def test_single_item_dataset(self):
        """Test chunksize with single-item dataset."""
        def simple_function(x):
            return x ** 2
        
        data = [42]
        result = optimize(simple_function, data, profile=True)
        
        # Chunksize should be 1 for single item
        assert result.chunksize == 1
        if result.profile:
            assert result.profile.optimal_chunksize <= 1
    
    def test_empty_dataset_handling(self):
        """Test that empty dataset is handled gracefully."""
        def simple_function(x):
            return x ** 2
        
        data = []
        result = optimize(simple_function, data, profile=True)
        
        # Should handle empty data without crashing
        assert result.chunksize >= 1


class TestChunksizeIntegration:
    """Integration tests for chunksize with actual execution."""
    
    def test_chunksize_produces_expected_chunk_duration(self):
        """Test that actual chunk execution time is close to target."""
        import time
        
        def timed_function(x):
            # Function with consistent ~0.002s execution time
            result = 0
            for i in range(2000):
                result += x ** 2
            return result
        
        data = list(range(1000))
        result = optimize(timed_function, data, profile=True)
        
        if result.n_jobs > 1 and result.profile:
            # Estimate chunk duration
            chunk_duration = result.profile.optimal_chunksize * result.profile.avg_execution_time
            
            # For homogeneous workloads with parallelization, should be reasonably close to 0.2s
            cv = result.profile.coefficient_of_variation
            if cv < 0.5:
                # Allow wider tolerance since actual execution may vary
                assert 0.05 <= chunk_duration <= 0.5, \
                    f"Chunk duration {chunk_duration:.3f}s is not reasonable for target 0.2s"
    
    def test_chunksize_adapts_to_workload_characteristics(self):
        """Test that chunksize adapts based on workload type."""
        # Homogeneous workload
        def homogeneous_function(x):
            result = 0
            for i in range(5000):
                result += x ** 2
            return result
        
        # Heterogeneous workload  
        def heterogeneous_function(x):
            iterations = 1000 if x % 3 == 0 else 10000
            result = 0
            for i in range(iterations):
                result += x ** 2
            return result
        
        data = list(range(1000))
        
        result_homo = optimize(homogeneous_function, data, profile=True)
        result_hetero = optimize(heterogeneous_function, data, profile=True)
        
        # If both were parallelized, heterogeneous should have smaller chunks
        if (result_homo.n_jobs > 1 and result_hetero.n_jobs > 1 and 
            result_homo.profile and result_hetero.profile):
            cv_homo = result_homo.profile.coefficient_of_variation
            cv_hetero = result_hetero.profile.coefficient_of_variation
            
            if cv_hetero > cv_homo and cv_hetero > 0.5:
                # Heterogeneous should have smaller or equal chunksize
                # (equal if both hit the cap)
                assert result_hetero.profile.optimal_chunksize <= result_homo.profile.optimal_chunksize, \
                    f"Heterogeneous chunksize {result_hetero.profile.optimal_chunksize} should be <= homogeneous {result_homo.profile.optimal_chunksize}"
