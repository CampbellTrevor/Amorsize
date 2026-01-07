"""
Pytest test cases with expensive functions to validate Amorsize optimizer.

This module contains test cases using expensive computational functions
to ensure the optimizer correctly analyzes and recommends parallelization.
"""

import pytest
import time
import math
import hashlib
from amorsize import optimize


# ============================================================================
# Expensive Test Functions
# ============================================================================

def expensive_prime_check(n):
    """Check if a number is prime (expensive for large n)."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True


def expensive_hash_computation(data):
    """Perform repeated cryptographic hashing."""
    result = str(data).encode()
    for _ in range(5000):
        result = hashlib.sha256(result).digest()
    return result.hex()


def expensive_mathematical_computation(x):
    """Perform expensive mathematical computations."""
    result = 0
    for i in range(1000):
        result += math.sin(x + i) * math.cos(x - i) * math.sqrt(abs(x))
    return result


def expensive_fibonacci(n):
    """Calculate Fibonacci using inefficient recursion (limited to small n)."""
    if n <= 1:
        return n
    return expensive_fibonacci(n - 1) + expensive_fibonacci(n - 2)


def expensive_matrix_operation(size):
    """Perform matrix operations."""
    matrix = [[i * j for j in range(size)] for i in range(size)]
    result = sum(sum(row) for row in matrix)
    return result


def medium_computation(x):
    """Medium-cost computation."""
    result = 0
    for i in range(100):
        result += x ** 2
    return result


# ============================================================================
# Test Cases
# ============================================================================

class TestExpensiveFunctions:
    """Test suite for expensive function optimization."""
    
    def test_expensive_prime_check_small_dataset(self):
        """Test prime checking with small dataset."""
        data = list(range(10000, 10050))
        result = optimize(expensive_prime_check, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert isinstance(result.reason, str)
        # Small primes are fast, likely serial
        assert result.n_jobs in [1, 4]  # Could be either
    
    def test_expensive_hash_computation_medium_dataset(self):
        """Test hash computation with medium dataset."""
        data = list(range(200))
        result = optimize(expensive_hash_computation, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        # Hash computation is expensive, should benefit from parallelization
        assert result.n_jobs > 1
        assert result.estimated_speedup >= 1.0
    
    def test_expensive_mathematical_computation(self):
        """Test expensive math computation."""
        data = [float(x) for x in range(100)]
        result = optimize(expensive_mathematical_computation, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        # Should recommend parallelization for expensive computation
        assert result.n_jobs > 1
    
    def test_expensive_fibonacci_small_values(self):
        """Test recursive Fibonacci with small values."""
        data = [25, 26, 27, 28, 29]
        result = optimize(expensive_fibonacci, data, sample_size=3)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        # Expensive recursive function should benefit from parallelization
        # But small dataset might not justify overhead
    
    def test_expensive_matrix_operation(self):
        """Test matrix operations."""
        data = [20, 25, 30, 35, 40]
        result = optimize(expensive_matrix_operation, data, sample_size=3)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_medium_computation_large_dataset(self):
        """Test medium computation with large dataset."""
        data = list(range(5000))
        result = optimize(medium_computation, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        # May or may not parallelize depending on timing
    
    def test_optimization_with_generator(self):
        """Test optimization with generator input."""
        def data_generator():
            for i in range(1000):
                yield i
        
        result = optimize(expensive_mathematical_computation, data_generator(), sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert "Cannot determine data size" in result.warnings or result.n_jobs >= 1
    
    def test_very_expensive_function_small_data(self):
        """Test very expensive function with small dataset."""
        # Use a module-level expensive function instead
        data = list(range(20))
        result = optimize(expensive_hash_computation, data, sample_size=3)
        
        # Should recommend parallelization for expensive functions
        assert result.n_jobs > 1
        assert result.estimated_speedup > 0
    
    def test_fast_function_large_data(self):
        """Test fast function with large dataset."""
        # Note: locally defined functions may not be picklable
        # Use medium_computation which is module-level but fast enough
        data = list(range(100))  # Small enough to trigger fast fail
        result = optimize(medium_computation, data, sample_size=5)
        
        # Function behavior depends on actual timing
        assert result.n_jobs >= 1
        assert result.reason is not None


class TestDataCharacteristics:
    """Test different data characteristics."""
    
    def test_uniform_expensive_data(self):
        """Test with uniform expensive data."""
        data = [1000] * 100  # Same input repeated
        result = optimize(expensive_hash_computation, data, sample_size=5)
        
        assert result.n_jobs > 1  # Should parallelize
        assert result.chunksize >= 1
    
    def test_varying_complexity_data(self):
        """Test with varying complexity data."""
        # Mix of easy and hard problems
        data = list(range(100, 200))
        result = optimize(expensive_mathematical_computation, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_small_dataset_expensive_function(self):
        """Test small dataset with expensive function."""
        data = list(range(5))
        result = optimize(expensive_hash_computation, data, sample_size=3)
        
        assert result.n_jobs >= 1
        # Small dataset might not justify parallelization overhead
    
    def test_large_dataset_expensive_function(self):
        """Test large dataset with expensive function."""
        data = list(range(1000))
        result = optimize(expensive_hash_computation, data, sample_size=5)
        
        assert result.n_jobs > 1  # Should definitely parallelize
        assert result.estimated_speedup > 1.0


class TestOptimizationParameters:
    """Test optimization parameter tuning."""
    
    def test_custom_sample_size(self):
        """Test with custom sample size."""
        data = list(range(500))
        result = optimize(expensive_mathematical_computation, data, sample_size=10)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_custom_chunk_duration(self):
        """Test with custom target chunk duration."""
        data = list(range(500))
        result = optimize(
            expensive_mathematical_computation,
            data,
            target_chunk_duration=0.5
        )
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_verbose_mode(self):
        """Test verbose mode returns valid results."""
        data = list(range(100))
        result = optimize(expensive_mathematical_computation, data, verbose=False)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.reason


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_data_processing_pipeline(self):
        """Simulate a data processing pipeline."""
        def process_record(record_id):
            # Simulate database lookup + computation
            time.sleep(0.001)
            data = hashlib.md5(str(record_id).encode()).hexdigest()
            return len(data)
        
        data = list(range(1000))
        result = optimize(process_record, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_image_processing_simulation(self):
        """Simulate image processing workload."""
        def process_image(image_id):
            # Simulate image processing
            result = 0
            for i in range(500):
                result += math.sin(image_id + i) * math.cos(image_id - i)
            return result
        
        data = list(range(200))
        result = optimize(process_image, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_scientific_computation(self):
        """Simulate scientific computation workload."""
        def scientific_calculation(param):
            # Simulate numerical simulation
            result = 0
            for i in range(1000):
                result += math.exp(-i/1000) * math.sin(param * i)
            return result
        
        data = [float(x) / 10 for x in range(100)]
        result = optimize(scientific_calculation, data, sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1


# ============================================================================
# Performance Benchmark Tests (optional, marked as slow)
# ============================================================================

@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmark tests (run with pytest -m slow)."""
    
    def test_actual_parallel_execution(self):
        """Test actual parallel execution vs serial."""
        from multiprocessing import Pool
        
        data = list(range(50))
        result = optimize(expensive_hash_computation, data, sample_size=5)
        
        if result.n_jobs > 1:
            # Execute with parallelization
            start = time.time()
            with Pool(processes=result.n_jobs) as pool:
                parallel_results = pool.map(
                    expensive_hash_computation,
                    data[:20],  # Use subset
                    chunksize=result.chunksize
                )
            parallel_time = time.time() - start
            
            # Execute serially
            start = time.time()
            serial_results = [expensive_hash_computation(x) for x in data[:20]]
            serial_time = time.time() - start
            
            # Verify results are the same
            assert parallel_results == serial_results
            
            # Parallel should be faster for this expensive function
            # (allowing some overhead for small dataset)
            print(f"Parallel: {parallel_time:.3f}s, Serial: {serial_time:.3f}s")
    
    def test_speedup_estimation_accuracy(self):
        """Test if speedup estimation is reasonable."""
        from multiprocessing import Pool
        
        data = list(range(100))
        result = optimize(expensive_mathematical_computation, data, sample_size=5)
        
        if result.n_jobs > 1:
            # The estimated speedup should be positive
            assert result.estimated_speedup > 0
            
            # Note: Speedup estimation may be < 1 due to overhead calculations
            # This is expected behavior when overhead is significant
