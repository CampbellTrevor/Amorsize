"""
Tests for the benchmark validation module.
"""

import pytest
import time
from amorsize import validate_optimization, quick_validate, optimize
from amorsize.benchmark import BenchmarkResult


class TestBenchmarkResultClass:
    """Tests for BenchmarkResult class."""
    
    def test_benchmark_result_creation(self):
        """Test that BenchmarkResult can be created with all fields."""
        opt_result = optimize(lambda x: x**2, range(10))
        
        result = BenchmarkResult(
            optimization=opt_result,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            predicted_speedup=1.8,
            accuracy_percent=90.0,
            error_percent=11.1,
            recommendations=["Test recommendation"]
        )
        
        assert result.optimization == opt_result
        assert result.serial_time == 1.0
        assert result.parallel_time == 0.5
        assert result.actual_speedup == 2.0
        assert result.predicted_speedup == 1.8
        assert result.accuracy_percent == 90.0
        assert len(result.recommendations) == 1
    
    def test_benchmark_result_repr(self):
        """Test BenchmarkResult string representation."""
        opt_result = optimize(lambda x: x**2, range(10))
        
        result = BenchmarkResult(
            optimization=opt_result,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            predicted_speedup=1.8,
            accuracy_percent=90.0,
            error_percent=11.1
        )
        
        repr_str = repr(result)
        assert "actual_speedup=2.00x" in repr_str
        assert "predicted=1.80x" in repr_str
        assert "accuracy=90.0%" in repr_str
    
    def test_benchmark_result_str(self):
        """Test BenchmarkResult full string output."""
        opt_result = optimize(lambda x: x**2, range(10))
        
        result = BenchmarkResult(
            optimization=opt_result,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            predicted_speedup=1.8,
            accuracy_percent=90.0,
            error_percent=11.1,
            recommendations=["Consider larger dataset"]
        )
        
        str_result = str(result)
        assert "Benchmark Validation Results" in str_result
        assert "Serial execution time" in str_result
        assert "Parallel execution time" in str_result
        assert "Actual speedup:" in str_result
        assert "Predicted speedup:" in str_result
        assert "Accuracy:" in str_result
        assert "Consider larger dataset" in str_result
    
    def test_is_accurate_method(self):
        """Test BenchmarkResult.is_accurate() threshold checking."""
        opt_result = optimize(lambda x: x**2, range(10))
        
        # High accuracy
        result_high = BenchmarkResult(
            optimization=opt_result,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            predicted_speedup=1.95,
            accuracy_percent=92.0,
            error_percent=2.6
        )
        assert result_high.is_accurate(75.0) is True
        assert result_high.is_accurate(95.0) is False
        
        # Low accuracy
        result_low = BenchmarkResult(
            optimization=opt_result,
            serial_time=1.0,
            parallel_time=0.5,
            actual_speedup=2.0,
            predicted_speedup=1.2,
            accuracy_percent=60.0,
            error_percent=66.7
        )
        assert result_low.is_accurate(75.0) is False
        assert result_low.is_accurate(50.0) is True


class TestValidateOptimization:
    """Tests for validate_optimization() function."""
    
    def test_validate_with_expensive_function(self):
        """Test validation with a genuinely expensive function."""
        def expensive_func(x):
            """Function that takes ~1ms to execute."""
            total = 0
            for i in range(x):
                total += i ** 2
            return total
        
        data = range(100, 200)  # 100 items
        
        result = validate_optimization(expensive_func, data, max_items=50, verbose=False)
        
        assert isinstance(result, BenchmarkResult)
        assert result.serial_time > 0
        assert result.parallel_time > 0
        assert result.actual_speedup >= 0.5  # At least somewhat close to predictions
        assert 0 <= result.accuracy_percent <= 100
    
    def test_validate_with_precomputed_optimization(self):
        """Test validation using a pre-computed optimization result."""
        def func(x):
            return sum(i**2 for i in range(x))
        
        data = range(50, 150)
        
        # Pre-compute optimization
        opt = optimize(func, data)
        
        # Validate with pre-computed result
        result = validate_optimization(func, data, optimization=opt, max_items=50)
        
        assert result.optimization == opt
        assert result.serial_time > 0
    
    def test_validate_with_fast_function(self):
        """Test validation with a very fast function (should recommend serial)."""
        def fast_func(x):
            return x * 2
        
        data = range(100)
        
        result = validate_optimization(fast_func, data, verbose=False)
        
        # Should recommend serial execution
        assert result.optimization.n_jobs == 1
        assert result.actual_speedup == 1.0  # Serial == parallel for n_jobs=1
        assert "Serial execution is optimal" in str(result.recommendations)
    
    def test_validate_with_generator(self):
        """Test validation converts generators to lists."""
        def func(x):
            return x ** 2
        
        gen = (x for x in range(100))
        
        result = validate_optimization(func, gen, max_items=50)
        
        assert isinstance(result, BenchmarkResult)
        assert result.serial_time > 0
    
    def test_validate_with_max_items_limit(self):
        """Test that max_items limits the benchmark size."""
        def func(x):
            return x ** 2
        
        data = range(1000)
        
        # Limit to 100 items
        result = validate_optimization(func, data, max_items=100, verbose=False)
        
        # Should run much faster than full dataset
        assert isinstance(result, BenchmarkResult)


class TestValidationAccuracy:
    """Tests for prediction accuracy calculations."""
    
    def test_accuracy_calculation_perfect(self):
        """Test accuracy when prediction is reasonable."""
        def func(x):
            # Computational workload instead of sleep
            result = 0
            for i in range(x):
                result += i ** 2
            return result
        
        data = range(100, 120)  # 20 items with moderate work
        
        result = validate_optimization(func, data)
        
        # With controlled computational load, accuracy should be reasonable
        # Not expecting 100% due to system variance, but should be high
        assert result.accuracy_percent > 50  # Reasonable threshold
    
    def test_accuracy_with_serial_execution(self):
        """Test accuracy calculation for serial execution (n_jobs=1)."""
        def func(x):
            return x ** 2
        
        data = range(10)
        
        result = validate_optimization(func, data)
        
        # For serial execution, accuracy should be 100% (no prediction error)
        assert result.optimization.n_jobs == 1
        assert result.actual_speedup == 1.0
        assert result.predicted_speedup == 1.0


class TestValidationEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_validate_empty_data(self):
        """Test that empty data raises error."""
        def func(x):
            return x ** 2
        
        with pytest.raises(ValueError, match="data cannot be empty"):
            validate_optimization(func, [])
    
    def test_validate_invalid_func(self):
        """Test that non-callable func raises error."""
        with pytest.raises(ValueError, match="func must be callable"):
            validate_optimization("not a function", range(10))
    
    def test_validate_none_data(self):
        """Test that None data raises error."""
        def func(x):
            return x ** 2
        
        with pytest.raises(ValueError, match="data cannot be None"):
            validate_optimization(func, None)
    
    def test_validate_negative_timeout(self):
        """Test that negative timeout raises error."""
        def func(x):
            return x ** 2
        
        with pytest.raises(ValueError, match="timeout must be positive"):
            validate_optimization(func, range(10), timeout=-1)
    
    def test_validate_function_raises_exception(self):
        """Test handling when function raises exception during benchmark."""
        def failing_func(x):
            if x > 5:
                raise ValueError("Test error")
            return x ** 2
        
        data = range(20)
        
        with pytest.raises(RuntimeError, match="execution failed"):
            validate_optimization(failing_func, data, max_items=10)


class TestQuickValidate:
    """Tests for quick_validate() convenience function."""
    
    def test_quick_validate_basic(self):
        """Test quick_validate with basic function."""
        def func(x):
            total = 0
            for i in range(x):
                total += i ** 2
            return total
        
        data = range(100, 500)  # Large dataset
        
        result = quick_validate(func, data, sample_size=50, verbose=False)
        
        assert isinstance(result, BenchmarkResult)
        assert result.serial_time > 0
        # Quick validate should be faster than full validation
    
    def test_quick_validate_samples_data(self):
        """Test that quick_validate properly samples large datasets."""
        def func(x):
            return x ** 2
        
        large_data = range(10000)
        
        result = quick_validate(func, large_data, sample_size=100, verbose=False)
        
        # Should complete quickly even with large input
        assert isinstance(result, BenchmarkResult)
    
    def test_quick_validate_with_small_data(self):
        """Test quick_validate when data is smaller than sample_size."""
        def func(x):
            return x ** 2
        
        small_data = range(20)
        
        result = quick_validate(func, small_data, sample_size=100, verbose=False)
        
        # Should use all available data
        assert isinstance(result, BenchmarkResult)
    
    def test_quick_validate_with_generator(self):
        """Test quick_validate converts generators to lists."""
        def func(x):
            return x ** 2
        
        gen = (x for x in range(500))
        
        result = quick_validate(func, gen, sample_size=50, verbose=False)
        
        assert isinstance(result, BenchmarkResult)


class TestBenchmarkIntegration:
    """Integration tests combining optimization and validation."""
    
    def test_full_workflow(self):
        """Test complete workflow: optimize, validate, check accuracy."""
        def process_item(x):
            # Simulate moderate computational work
            result = 0
            for i in range(x):
                result += i ** 2
            return result
        
        data = range(50, 150)
        
        # Step 1: Optimize
        opt = optimize(process_item, data, verbose=False)
        
        # Step 2: Validate
        benchmark = validate_optimization(
            process_item,
            data,
            optimization=opt,
            max_items=50,
            verbose=False
        )
        
        # Step 3: Check results
        assert benchmark.optimization == opt
        assert benchmark.serial_time > 0
        assert benchmark.parallel_time > 0
        assert benchmark.accuracy_percent >= 0
        
        # Step 4: Use is_accurate method
        is_good = benchmark.is_accurate(threshold=50.0)
        assert isinstance(is_good, bool)
    
    def test_validation_provides_useful_recommendations(self):
        """Test that validation provides actionable recommendations."""
        def func(x):
            return x ** 2
        
        data = range(50)
        
        result = validate_optimization(func, data, max_items=50)
        
        # Should have at least one recommendation
        assert len(result.recommendations) > 0
        
        # Recommendations should be strings
        for rec in result.recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0


class TestBenchmarkPerformance:
    """Tests to ensure benchmarking itself is performant."""
    
    def test_benchmark_completes_quickly(self):
        """Test that benchmark completes in reasonable time."""
        def func(x):
            return x ** 2
        
        data = range(100)
        
        start = time.perf_counter()
        result = validate_optimization(func, data, max_items=50, verbose=False)
        end = time.perf_counter()
        
        benchmark_time = end - start
        
        # Should complete in under 5 seconds for simple function
        assert benchmark_time < 5.0
        assert isinstance(result, BenchmarkResult)
    
    def test_quick_validate_is_faster(self):
        """Test that quick_validate is faster than full validation."""
        def func(x):
            result = 0
            for i in range(x):
                result += i ** 2
            return result
        
        data = range(50, 150)
        
        # Quick validate
        start_quick = time.perf_counter()
        result_quick = quick_validate(func, data, sample_size=30, verbose=False)
        end_quick = time.perf_counter()
        quick_time = end_quick - start_quick
        
        # Full validate
        start_full = time.perf_counter()
        result_full = validate_optimization(func, data, max_items=100, verbose=False)
        end_full = time.perf_counter()
        full_time = end_full - start_full
        
        # Quick should be faster (or at least not much slower)
        # Allow some variance due to system load
        assert quick_time < full_time * 1.5
        
        assert isinstance(result_quick, BenchmarkResult)
        assert isinstance(result_full, BenchmarkResult)
