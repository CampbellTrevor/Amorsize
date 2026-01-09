#!/usr/bin/env python3
"""
Comprehensive test cases with expensive functions and various data scenarios
to demonstrate and test the Amorsize optimizer.

This file contains realistic, expensive computational tasks that benefit from
parallelization, along with test data of varying sizes and characteristics.
"""

import time
import math
import hashlib
from multiprocessing import Pool
from amorsize import optimize


# ============================================================================
# Expensive Computational Functions
# ============================================================================

def prime_factorization(n):
    """
    Expensive: Prime factorization of a number.
    Computational complexity: O(sqrt(n))
    """
    factors = []
    divisor = 2
    while divisor * divisor <= n:
        while n % divisor == 0:
            factors.append(divisor)
            n //= divisor
        divisor += 1
    if n > 1:
        factors.append(n)
    return factors


def monte_carlo_pi_estimation(iterations):
    """
    Expensive: Monte Carlo estimation of Pi.
    Computational complexity: O(iterations)
    """
    import random
    inside_circle = 0
    for _ in range(iterations):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1:
            inside_circle += 1
    return 4 * inside_circle / iterations


def matrix_multiplication(size):
    """
    Expensive: Matrix multiplication.
    Computational complexity: O(n^3)
    """
    # Create two random matrices
    import random
    matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
    matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]
    
    # Multiply matrices
    result = [[0 for _ in range(size)] for _ in range(size)]
    for i in range(size):
        for j in range(size):
            for k in range(size):
                result[i][j] += matrix_a[i][k] * matrix_b[k][j]
    
    return result[0][0]  # Return just first element to reduce serialization


def fibonacci_recursive(n):
    """
    Expensive: Recursive Fibonacci (intentionally inefficient).
    Computational complexity: O(2^n)
    Limited to n <= 35 to avoid excessive computation
    """
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def cryptographic_hash_chain(data):
    """
    Expensive: Repeated cryptographic hashing.
    Computational complexity: O(iterations)
    """
    iterations = 10000
    result = str(data).encode()
    for _ in range(iterations):
        result = hashlib.sha256(result).digest()
    return result.hex()


def numerical_integration(n):
    """
    Expensive: Numerical integration using Simpson's rule.
    Computational complexity: O(steps)
    """
    steps = 100000
    
    def f(x):
        return math.sin(x) * math.exp(-x/10) + math.cos(x**2)
    
    h = (n / steps)
    result = f(0) + f(n)
    
    for i in range(1, steps):
        x = i * h
        if i % 2 == 0:
            result += 2 * f(x)
        else:
            result += 4 * f(x)
    
    return result * h / 3


def string_processing_heavy(text_length):
    """
    Expensive: Heavy string processing operations.
    Computational complexity: O(n^2)
    """
    text = "a" * text_length
    result = []
    
    for i in range(len(text)):
        for j in range(i, min(i + 100, len(text))):
            result.append(text[i:j].upper())
    
    return len(result)


def nested_loop_computation(n):
    """
    Expensive: Nested loops with mathematical operations.
    Computational complexity: O(n^3)
    """
    result = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result += math.sqrt(i + 1) * math.log(j + 1) * math.sin(k)
    return result


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_prime_test_data(size='medium'):
    """Generate test data for prime factorization."""
    data_sizes = {
        'small': list(range(10000, 10100)),
        'medium': list(range(100000, 100500)),
        'large': list(range(1000000, 1001000)),
        'xlarge': list(range(10000000, 10005000))
    }
    return data_sizes.get(size, data_sizes['medium'])


def generate_monte_carlo_data(size='medium'):
    """Generate test data for Monte Carlo simulations."""
    data_sizes = {
        'small': [1000] * 100,
        'medium': [5000] * 500,
        'large': [10000] * 1000,
        'xlarge': [50000] * 2000
    }
    return data_sizes.get(size, data_sizes['medium'])


def generate_matrix_data(size='medium'):
    """Generate test data for matrix operations."""
    data_sizes = {
        'small': [10] * 50,
        'medium': [20] * 100,
        'large': [30] * 200,
        'xlarge': [40] * 500
    }
    return data_sizes.get(size, data_sizes['medium'])


def generate_fibonacci_data(size='medium'):
    """Generate test data for Fibonacci calculation."""
    data_sizes = {
        'small': list(range(25, 30)),
        'medium': list(range(30, 35)),
        'large': list(range(32, 37)),
    }
    return data_sizes.get(size, data_sizes['medium'])


def generate_hash_data(size='medium'):
    """Generate test data for cryptographic operations."""
    data_sizes = {
        'small': list(range(100)),
        'medium': list(range(500)),
        'large': list(range(1000)),
        'xlarge': list(range(5000))
    }
    return data_sizes.get(size, data_sizes['medium'])


def generate_integration_data(size='medium'):
    """Generate test data for numerical integration."""
    data_sizes = {
        'small': [float(x) for x in range(10, 20)],
        'medium': [float(x) for x in range(10, 100)],
        'large': [float(x) for x in range(10, 200)],
        'xlarge': [float(x) for x in range(10, 500)]
    }
    return data_sizes.get(size, data_sizes['medium'])


# ============================================================================
# Test Runner
# ============================================================================

def run_optimization_test(func, data, description):
    """Run optimization analysis and optionally execute with multiprocessing."""
    print("\n" + "=" * 70)
    print(f"Test: {description}")
    print("=" * 70)
    
    # Analyze optimal parameters
    print("\n[1] Analyzing optimal parameters...")
    result = optimize(func, data, verbose=True)
    
    print(f"\n[2] Optimization Result:")
    print(f"    n_jobs: {result.n_jobs}")
    print(f"    chunksize: {result.chunksize}")
    print(f"    estimated_speedup: {result.estimated_speedup:.2f}x")
    print(f"    reason: {result.reason}")
    
    if result.warnings:
        print(f"    warnings: {result.warnings}")
    
    # Execute with recommendations (limited execution for demo)
    test_subset = data[:min(10, len(data))]  # Use subset for actual execution
    
    print(f"\n[3] Executing with recommendations (subset of {len(test_subset)} items)...")
    
    if result.n_jobs > 1:
        try:
            start = time.time()
            with Pool(processes=result.n_jobs) as pool:
                results = pool.map(func, test_subset, chunksize=result.chunksize)
            parallel_time = time.time() - start
            print(f"    Parallel execution time: {parallel_time:.3f}s")
            print(f"    Results computed: {len(results)}")
        except Exception as e:
            print(f"    Parallel execution failed: {e}")
    else:
        start = time.time()
        results = [func(x) for x in test_subset]
        serial_time = time.time() - start
        print(f"    Serial execution time: {serial_time:.3f}s")
        print(f"    Results computed: {len(results)}")
    
    return result


def main():
    """Run all test cases."""
    print("=" * 70)
    print("AMORSIZE - Expensive Function Test Suite")
    print("=" * 70)
    print("\nThis test suite demonstrates the optimizer with various expensive")
    print("computational tasks and different data characteristics.")
    
    # Test 1: Prime Factorization (CPU-bound, variable complexity)
    run_optimization_test(
        prime_factorization,
        generate_prime_test_data('medium'),
        "Prime Factorization (Medium Dataset)"
    )
    
    # Test 2: Monte Carlo Simulation (CPU-bound, consistent complexity)
    run_optimization_test(
        monte_carlo_pi_estimation,
        generate_monte_carlo_data('small'),
        "Monte Carlo Pi Estimation (Small Dataset)"
    )
    
    # Test 3: Matrix Multiplication (CPU-bound, O(n^3))
    run_optimization_test(
        matrix_multiplication,
        generate_matrix_data('small'),
        "Matrix Multiplication (Small Matrices)"
    )
    
    # Test 4: Fibonacci Recursive (CPU-bound, exponential)
    run_optimization_test(
        fibonacci_recursive,
        generate_fibonacci_data('small'),
        "Recursive Fibonacci (Small Values)"
    )
    
    # Test 5: Cryptographic Hashing (CPU-bound, many iterations)
    run_optimization_test(
        cryptographic_hash_chain,
        generate_hash_data('medium'),
        "Cryptographic Hash Chain (Medium Dataset)"
    )
    
    # Test 6: Numerical Integration (CPU-bound, mathematical)
    run_optimization_test(
        numerical_integration,
        generate_integration_data('small'),
        "Numerical Integration (Small Dataset)"
    )
    
    # Test 7: Nested Loop Computation (CPU-bound, O(n^3))
    run_optimization_test(
        nested_loop_computation,
        [10, 15, 20, 25, 30],
        "Nested Loop Computation (Small Values)"
    )
    
    # Test 8: String Processing (Memory-intensive)
    run_optimization_test(
        string_processing_heavy,
        [100, 200, 300, 400, 500],
        "Heavy String Processing (Small Strings)"
    )
    
    print("\n" + "=" * 70)
    print("Test Suite Complete!")
    print("=" * 70)
    print("\nKey Observations:")
    print("  - Functions with longer execution times (> 10ms) benefit from parallelization")
    print("  - Fast functions (< 1ms) are recommended for serial execution")
    print("  - Optimal chunksize increases with faster functions")
    print("  - Memory-intensive tasks may have reduced worker counts")
    print("=" * 70)


if __name__ == "__main__":
    main()
