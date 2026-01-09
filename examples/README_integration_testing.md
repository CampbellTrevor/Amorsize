# Integration Testing Guide

## Overview

This guide explains how to validate that Amorsize's optimization recommendations work correctly in real-world scenarios with `multiprocessing.Pool`. Integration testing ensures that:

1. **Correctness**: Optimized execution produces the same results as serial execution
2. **Completeness**: All data is processed (no loss, no duplication)
3. **Performance**: Parallelization provides expected speedup
4. **Robustness**: Edge cases are handled gracefully

## Why Integration Testing Matters

While unit tests validate individual components, **integration tests validate the entire workflow**:

- ✅ `optimize()` recommendations actually work with `Pool.map()`
- ✅ Generator reconstruction doesn't lose data
- ✅ Chunksize and n_jobs produce correct results
- ✅ All features work together (profiling, callbacks, etc.)
- ✅ Edge cases don't break in production

## Basic Integration Pattern

### Pattern 1: Manual Pool Management

```python
from multiprocessing import Pool
from amorsize import optimize

def computation(x: int) -> int:
    return x ** 2

data = list(range(100))

# Step 1: Get optimization recommendation
result = optimize(computation, data)

# Step 2: Use recommendation with Pool
if result.n_jobs == 1:
    # Serial execution
    results = [computation(x) for x in result.data]
else:
    # Parallel execution
    with Pool(processes=result.n_jobs) as pool:
        results = pool.map(computation, result.data, chunksize=result.chunksize)

# Step 3: Verify correctness
expected = [computation(x) for x in range(100)]
assert results == expected, "Results should match"
```

**Key Points:**
- Always use `result.data` (not original data) to handle generator reconstruction
- Check `n_jobs == 1` to avoid Pool overhead for serial execution
- Verify results match expected output

### Pattern 2: Using execute() (Recommended)

```python
from amorsize import execute

def computation(x: int) -> int:
    return x ** 2

data = list(range(100))

# One-line optimization and execution
results = execute(computation, data)

# Verify correctness
expected = [computation(x) for x in range(100)]
assert results == expected
```

**Advantages:**
- Simpler API (1 line vs 7+ lines)
- Automatic Pool management
- Handles serial/parallel cases automatically
- Recommended for most use cases

## Testing Correctness

### Test Pattern: Ground Truth Comparison

```python
def test_correctness():
    """Verify optimized execution matches serial execution."""
    
    def computation(x: int) -> int:
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    data = list(range(100))
    
    # Ground truth (serial execution)
    serial_results = [computation(x) for x in data]
    
    # Optimized execution
    optimized_results = execute(computation, data)
    
    # Validate
    assert len(serial_results) == len(optimized_results), "Length should match"
    assert serial_results == optimized_results, "Results should match exactly"
```

**What to Check:**
1. ✅ Same number of results
2. ✅ Same values in same order
3. ✅ No data loss
4. ✅ No data duplication

## Testing Data Types

### Lists

```python
def test_list_data():
    data = list(range(100))
    results = execute(simple_function, data)
    
    # Verify all items processed
    assert len(results) == 100
    
    # Verify order preserved
    expected = [simple_function(x) for x in range(100)]
    assert results == expected
```

### Generators

```python
def test_generator_data():
    def gen():
        for i in range(100):
            yield i
    
    # Generator should be reconstructed automatically
    results = execute(simple_function, gen())
    
    # Verify all data processed (no loss)
    assert len(results) == 100
    
    # Verify correctness
    expected = [simple_function(x) for x in range(100)]
    assert results == expected
```

**Critical for Generators:**
- Amorsize reconstructs generators using `itertools.chain`
- All data should be processed (not just items after sample)
- Test with `execute()` or use `result.data` with `optimize()`

### Ranges

```python
def test_range_data():
    data = range(100)
    results = execute(simple_function, data)
    
    # Range should work like list
    expected = [simple_function(x) for x in range(100)]
    assert results == expected
```

## Testing Edge Cases

### Empty Data

```python
def test_empty_data():
    results = execute(simple_function, [])
    assert results == [], "Empty data should return empty list"
```

### Single Item

```python
def test_single_item():
    results = execute(simple_function, [5])
    assert results == [25], "Single item should work"
```

### Very Small Dataset (< sample_size)

```python
def test_small_dataset():
    # Dataset smaller than default sample_size (5)
    results = execute(simple_function, [1, 2, 3])
    assert results == [1, 4, 9], "Should handle small datasets"
```

### Large Return Objects

```python
def test_large_return_objects():
    def return_large_object(x: int) -> List[int]:
        return [x] * 1000  # 1000-element list
    
    data = list(range(10))
    results = execute(return_large_object, data)
    
    # Should still work correctly
    assert len(results) == 10
    assert results[0] == [0] * 1000
```

### Heterogeneous Workloads

```python
def test_heterogeneous_workload():
    def variable_time(x: int) -> int:
        # Execution time varies by input
        iterations = (x % 10) * 1000 + 1000
        result = 0
        for i in range(iterations):
            result += x
        return result
    
    data = list(range(50))
    results = execute(variable_time, data)
    
    # Adaptive chunking should handle this
    expected = [variable_time(x) for x in range(50)]
    assert results == expected
```

## Testing Performance

### Validate Speedup Predictions

```python
import time

def test_speedup_accuracy():
    """Verify speedup predictions are reasonable."""
    
    def expensive(x: int) -> int:
        result = 0
        for i in range(10000):
            result += x ** 2
        return result
    
    data = list(range(50))
    
    # Get prediction
    result = optimize(expensive, data)
    predicted_speedup = result.estimated_speedup
    
    # Measure serial time
    start = time.time()
    serial_results = [expensive(x) for x in data]
    serial_time = time.time() - start
    
    # Measure parallel time (if recommended)
    if result.n_jobs > 1:
        start = time.time()
        with Pool(processes=result.n_jobs) as pool:
            parallel_results = pool.map(expensive, result.data, chunksize=result.chunksize)
        parallel_time = time.time() - start
        
        actual_speedup = serial_time / parallel_time
        
        # Verify correctness
        assert parallel_results == serial_results
        
        # Prediction should be within 50% of actual
        error = abs(predicted_speedup - actual_speedup) / actual_speedup
        assert error < 0.5, f"Prediction error too large: {error*100:.1f}%"
```

### Validate Serial Fallback

```python
def test_serial_fallback():
    """Verify that fast functions correctly fall back to serial."""
    
    def ultra_fast(x):
        return x + 1
    
    data = list(range(100))
    result = optimize(ultra_fast, data)
    
    # Should recommend serial execution
    # (or very low n_jobs on high-core systems)
    assert result.n_jobs <= 2, "Fast function should use serial or minimal parallelization"
    
    # Execution should still work correctly
    if result.n_jobs == 1:
        results = [ultra_fast(x) for x in result.data]
    else:
        with Pool(processes=result.n_jobs) as pool:
            results = pool.map(ultra_fast, result.data, chunksize=result.chunksize)
    
    expected = [x + 1 for x in range(100)]
    assert results == expected
```

## Testing with Advanced Features

### With Progress Callbacks

```python
def test_with_progress_callback():
    """Verify progress callbacks work with execution."""
    
    progress_updates = []
    
    def callback(phase: str, progress: float):
        progress_updates.append((phase, progress))
    
    data = list(range(50))
    results = execute(
        computation,
        data,
        progress_callback=callback
    )
    
    # Verify execution worked
    expected = [computation(x) for x in range(50)]
    assert results == expected
    
    # Verify callback was called
    assert len(progress_updates) > 0, "Callback should be called"
    assert progress_updates[-1][1] == 1.0, "Should reach 100%"
```

### With Diagnostic Profiling

```python
def test_with_profiling():
    """Verify profiling works with execution."""
    
    data = list(range(50))
    results, opt_result = execute(
        computation,
        data,
        profile=True,
        return_optimization_result=True
    )
    
    # Verify execution
    expected = [computation(x) for x in range(50)]
    assert results == expected
    
    # Verify profile captured
    assert opt_result.profile is not None
    assert hasattr(opt_result.profile, 'estimated_speedup')
    assert opt_result.profile.estimated_speedup > 0
```

### With Verbose Mode

```python
def test_with_verbose():
    """Verify verbose mode doesn't break execution."""
    
    data = list(range(50))
    results = execute(computation, data, verbose=True)
    
    expected = [computation(x) for x in range(50)]
    assert results == expected
```

## Best Practices

### 1. Always Verify Correctness First

```python
# Good: Verify results match expected
serial_results = [func(x) for x in data]
optimized_results = execute(func, data)
assert serial_results == optimized_results

# Bad: Assume optimization is correct without verification
results = execute(func, data)  # Hope it works?
```

### 2. Test with Multiple Data Types

```python
# Test with list
test_with_list_data()

# Test with generator
test_with_generator_data()

# Test with range
test_with_range_data()
```

### 3. Test Edge Cases

```python
# Empty data
test_empty_data()

# Single item
test_single_item()

# Very small dataset
test_small_dataset()

# Large return objects
test_large_returns()

# Heterogeneous workload
test_variable_time()
```

### 4. Validate Against Ground Truth

```python
def validate_optimization(func, data):
    """Standard validation pattern."""
    
    # Ground truth
    serial = [func(x) for x in data]
    
    # Optimized
    optimized = execute(func, data)
    
    # Compare
    assert len(serial) == len(optimized), "Length mismatch"
    assert serial == optimized, "Results don't match"
    
    return True
```

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestEndToEndOptimization -v

# Run with coverage
pytest tests/test_integration.py --cov=amorsize

# Run integration demo
python examples/integration_testing_demo.py
```

## Common Issues and Solutions

### Issue 1: Generator Data Loss

**Problem:** Using original generator after `optimize()` loses sampled data.

```python
# Wrong
gen = data_generator()
result = optimize(func, gen)
with Pool(result.n_jobs) as pool:
    results = pool.map(func, gen)  # Missing sampled items!
```

**Solution:** Always use `result.data`:

```python
# Correct
gen = data_generator()
result = optimize(func, gen)
with Pool(result.n_jobs) as pool:
    results = pool.map(func, result.data)  # All data included
```

**Better:** Use `execute()`:

```python
# Best
results = execute(func, data_generator())  # Handles everything
```

### Issue 2: Forgetting to Check n_jobs

**Problem:** Creating Pool when serial execution recommended.

```python
# Wrong
result = optimize(func, data)
with Pool(result.n_jobs) as pool:  # Even if n_jobs=1!
    results = pool.map(func, result.data)
```

**Solution:** Check `n_jobs` before creating Pool:

```python
# Correct
result = optimize(func, data)
if result.n_jobs == 1:
    results = [func(x) for x in result.data]
else:
    with Pool(result.n_jobs) as pool:
        results = pool.map(func, result.data, chunksize=result.chunksize)
```

**Better:** Use `execute()`:

```python
# Best
results = execute(func, data)  # Handles serial/parallel automatically
```

### Issue 3: Not Using Recommended chunksize

**Problem:** Ignoring `chunksize` parameter.

```python
# Wrong
with Pool(result.n_jobs) as pool:
    results = pool.map(func, result.data)  # Default chunksize!
```

**Solution:** Always use recommended `chunksize`:

```python
# Correct
with Pool(result.n_jobs) as pool:
    results = pool.map(func, result.data, chunksize=result.chunksize)
```

## Complete Example

Here's a complete integration test following all best practices:

```python
import pytest
from multiprocessing import Pool
from amorsize import optimize, execute


def test_complete_integration():
    """Complete integration test with all best practices."""
    
    # Define computation
    def computation(x: int) -> int:
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    # Test with multiple data types
    test_cases = [
        ("list", list(range(100))),
        ("range", range(100)),
        ("generator", (x for x in range(100))),
    ]
    
    for data_type, data in test_cases:
        print(f"\nTesting with {data_type}...")
        
        # Ground truth
        serial_results = [computation(x) for x in range(100)]
        
        # Pattern 1: Manual optimization
        result = optimize(computation, data)
        if result.n_jobs == 1:
            results = [computation(x) for x in result.data]
        else:
            with Pool(result.n_jobs) as pool:
                results = pool.map(computation, result.data, chunksize=result.chunksize)
        
        # Validate
        assert len(results) == 100, f"{data_type}: Wrong length"
        assert results == serial_results, f"{data_type}: Results don't match"
        
        print(f"✅ {data_type} passed")
    
    # Pattern 2: Using execute()
    print("\nTesting with execute()...")
    results = execute(computation, list(range(100)))
    assert results == serial_results
    print("✅ execute() passed")
    
    print("\n✅ All integration tests passed!")


if __name__ == '__main__':
    test_complete_integration()
```

## See Also

- [Test Suite](../tests/test_integration.py) - Complete integration test suite
- [Demo](integration_testing_demo.py) - Interactive examples
- [API Documentation](../README.md) - Full API reference
- [Examples](README.md) - Usage examples

## Summary

Integration testing ensures that Amorsize's optimizations work correctly in production:

1. ✅ Test with `optimize()` + `Pool.map()` pattern
2. ✅ Test with `execute()` convenience function
3. ✅ Validate correctness against ground truth
4. ✅ Test all data types (list, generator, range)
5. ✅ Test edge cases (empty, single item, small dataset)
6. ✅ Verify generator reconstruction
7. ✅ Validate performance predictions
8. ✅ Test with advanced features (profiling, callbacks)

**Recommended Approach:** Use `execute()` for simplicity, validate against serial execution for correctness.
