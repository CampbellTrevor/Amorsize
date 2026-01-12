# Amorsize Test Suite

This directory contains comprehensive test cases for the Amorsize optimizer.

## Test Files

### `test_system_info.py`
Tests for system information detection:
- Physical core detection
- Spawn cost calculation
- Available memory detection
- Max workers calculation

### `test_sampling.py`
Tests for the sampling module:
- Function picklability checking
- Data slicing (lists and generators)
- Dry-run execution
- Exception handling
- Memory tracking

### `test_optimizer.py`
Tests for the main optimizer:
- Optimization with various function types
- Generator handling
- Empty data handling
- Custom parameters
- Result representation

### `test_expensive_scenarios.py` ⭐ NEW
Comprehensive test suite with expensive computational functions:
- **21 test cases** covering real-world scenarios
- **Expensive functions** including:
  - Prime factorization
  - Cryptographic hashing
  - Matrix operations
  - Recursive Fibonacci
  - Mathematical computations
  - Numerical integration
  - String processing
- **Data characteristics tests**:
  - Uniform vs varying complexity
  - Small vs large datasets
  - Generator inputs
- **Real-world scenarios**:
  - Data processing pipelines
  - Image processing simulation
  - Scientific computations
- **Performance benchmarks**:
  - Actual parallel execution validation
  - Speedup estimation accuracy

### `test_expensive_functions.py` ⭐ NEW
Standalone executable test suite (not pytest):
- **8 comprehensive test cases** with detailed output
- Demonstrates optimizer with various expensive tasks
- Shows optimization analysis and actual execution
- Can be run directly: `python tests/test_expensive_functions.py`
- Includes performance measurements and observations

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test file:
```bash
pytest tests/test_expensive_scenarios.py -v
```

### Run tests with coverage:
```bash
pytest tests/ --cov=amorsize --cov-report=html
```

### Run only fast tests (exclude benchmarks):
```bash
pytest tests/ -m "not slow"
```

### Run performance benchmarks:
```bash
pytest tests/test_expensive_scenarios.py -m slow -v
```

### Run the standalone test suite:
```bash
python tests/test_expensive_functions.py
```

## Test Categories

### Unit Tests
- `test_system_info.py`
- `test_sampling.py`
- Core functionality tests in `test_optimizer.py`

### Integration Tests
- `test_expensive_scenarios.py` - Real-world expensive functions
- `test_expensive_functions.py` - Executable demonstrations

### Performance Tests
- Marked with `@pytest.mark.slow`
- Include actual parallel execution
- Validate speedup estimations

## Test Coverage

Current test coverage: **23 unit tests + 21 scenario tests = 44 tests total**

All tests verify:
- ✅ Correct optimization parameters
- ✅ Error handling
- ✅ Edge cases (empty data, errors, generators)
- ✅ Different data characteristics
- ✅ Real-world usage patterns
- ✅ Performance with expensive functions

## Adding New Tests

When adding new test cases:

1. **For unit tests**: Add to appropriate existing file
2. **For expensive functions**: Add to `test_expensive_scenarios.py`
3. **For demonstrations**: Add to `test_expensive_functions.py`

### Example Test Template

```python
def test_my_expensive_function():
    """Test description."""
    def my_expensive_func(x):
        # Expensive operation
        return result
    
    data = list(range(100))
    result = optimize(my_expensive_func, data, sample_size=5)
    
    assert result.n_jobs >= 1
    assert result.chunksize >= 1
    # Add specific assertions based on expected behavior
```

## Notes

- Functions defined locally in tests may not be picklable
- Use module-level functions for parallelization tests
- Performance tests may vary based on system hardware
- Some tests are intentionally slow to demonstrate expensive operations
