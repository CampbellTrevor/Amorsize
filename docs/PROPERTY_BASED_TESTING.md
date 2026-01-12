# Property-Based Testing with Hypothesis

## Overview

Amorsize uses property-based testing with [Hypothesis](https://hypothesis.readthedocs.io/) to automatically discover edge cases and verify invariant properties across a wide range of inputs.

Unlike traditional unit tests that test specific examples, property-based tests define **properties** that should hold for **all possible inputs** and let Hypothesis generate hundreds of test cases automatically.

## Why Property-Based Testing?

**Benefits:**
- **Automatic edge case discovery**: Hypothesis generates test cases you might not think of
- **Comprehensive coverage**: Tests hundreds of input combinations automatically
- **Regression prevention**: Hypothesis remembers failing cases for future runs
- **Minimal test code**: One property test replaces dozens of example-based tests
- **Better confidence**: Verifies properties hold for all inputs, not just examples

**Example:**
Instead of writing:
```python
def test_n_jobs_positive_case_1():
    result = optimize(func, [1, 2, 3])
    assert result.n_jobs >= 1

def test_n_jobs_positive_case_2():
    result = optimize(func, range(100))
    assert result.n_jobs >= 1

# ... dozens more cases
```

You write:
```python
@given(data=st.lists(st.integers(), min_size=1, max_size=1000))
def test_n_jobs_positive(data):
    result = optimize(lambda x: x * 2, data)
    assert result.n_jobs >= 1  # Tested with 100+ generated inputs
```

## Running Property-Based Tests

### Install Dependencies

```bash
pip install -e ".[dev]"  # Includes hypothesis
```

### Run Property-Based Tests

```bash
# Run all property-based tests
pytest tests/test_property_based_optimizer.py -v

# Run specific test class
pytest tests/test_property_based_optimizer.py::TestOptimizerInvariants -v

# Run with more examples (default is 50-100)
pytest tests/test_property_based_optimizer.py --hypothesis-seed=0
```

## Test Structure

Property-based tests are organized into logical groups:

### 1. **Invariant Properties** (`TestOptimizerInvariants`)

Properties that must **always** hold, regardless of input:

- `test_n_jobs_within_bounds`: n_jobs is between 1 and reasonable maximum
- `test_chunksize_positive`: chunksize is always >= 1
- `test_result_type_correctness`: optimize() returns OptimizationResult
- `test_speedup_non_negative`: estimated_speedup is non-negative
- `test_sample_size_parameter`: sample_size parameter is respected

### 2. **Edge Cases** (`TestOptimizerEdgeCases`)

Boundary conditions and special inputs:

- `test_empty_list`: Empty data handled gracefully
- `test_single_item`: Single-item lists work
- `test_very_small_lists`: Lists with 2-5 items
- `test_generator_input`: Generators preserved correctly
- `test_range_input`: Range objects handled

### 3. **Consistency** (`TestOptimizerConsistency`)

Determinism and reproducibility:

- `test_deterministic_for_same_input`: Same input → same output
- `test_verbose_mode_consistency`: verbose flag doesn't affect result

### 4. **Robustness** (`TestOptimizerRobustness`)

Different data types and structures:

- `test_different_list_sizes`: Various list sizes (10-100 items)
- `test_float_data`: Floating-point numbers
- `test_string_data`: String processing
- `test_tuple_data`: Tuple data structures

### 5. **Diagnostics** (`TestOptimizerDiagnostics`)

Profiling and diagnostic features:

- `test_diagnostic_profile_exists`: Profile data available when requested

## How Hypothesis Works

### 1. Generate Test Cases

Hypothesis uses **strategies** to generate test inputs:

```python
from hypothesis import strategies as st

# Generate lists of integers with 10-500 items
data = st.lists(st.integers(), min_size=10, max_size=500)

# Generate floats in a range
duration = st.floats(min_value=0.05, max_value=1.0)

# Generate booleans
verbose = st.booleans()
```

### 2. Run Property Tests

For each generated input, Hypothesis:
1. Runs your test function
2. Checks if the assertion passes
3. If it fails, **shrinks** the input to find minimal failing case

### 3. Remember Failures

Hypothesis saves failing cases in `.hypothesis/` directory:
- Automatically replays previous failures
- Prevents regressions
- Provides reproduce commands

### 4. Shrinking Example

If this fails:
```python
@given(data=st.lists(st.integers(), min_size=10))
def test_something(data):
    result = optimize(lambda x: x * 2, data)
    assert result.n_jobs > 0
```

Hypothesis will:
1. Find a failing case (e.g., `data = [999, -123, 0, 42, ...]`)
2. **Shrink** it to minimal failing case (e.g., `data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`)
3. Show you the minimal case for debugging

## Writing New Property-Based Tests

### Template

```python
from hypothesis import given, settings, strategies as st

@given(
    data=st.lists(st.integers(), min_size=10, max_size=500),
    sample_size=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50, deadline=5000)
def test_my_property(data, sample_size):
    """Test that my property holds."""
    # Ensure preconditions
    assume(sample_size <= len(data))
    
    # Run optimizer
    result = optimize(lambda x: x * 2, data, sample_size=sample_size)
    
    # Verify postconditions (the "property")
    assert result.n_jobs >= 1
    assert result.chunksize >= 1
```

### Key Decorators

- `@given(...)`: Specify input strategies
- `@settings(...)`: Configure test behavior
  - `max_examples`: Number of test cases (default: 100)
  - `deadline`: Max time per test (milliseconds)
  - `suppress_health_check`: Disable specific warnings

### Using `assume()`

Filter generated inputs with preconditions:

```python
@given(data=st.lists(st.integers()), sample_size=st.integers(min_value=1))
def test_something(data, sample_size):
    # Skip cases where sample_size > data length
    assume(sample_size <= len(data))
    
    result = optimize(lambda x: x * 2, data, sample_size=sample_size)
    # ...
```

## Common Strategies

### Built-in Strategies

```python
from hypothesis import strategies as st

# Basic types
st.integers()                    # Any integer
st.integers(min_value=1, max_value=100)  # 1-100
st.floats()                      # Any float
st.floats(min_value=0.0, max_value=1.0)  # 0.0-1.0
st.text()                        # Any string
st.booleans()                    # True or False

# Collections
st.lists(st.integers())          # List of integers
st.lists(st.integers(), min_size=10, max_size=100)  # 10-100 items
st.tuples(st.integers(), st.text())  # Tuple (int, str)
st.dictionaries(st.text(), st.integers())  # Dict[str, int]

# Sampling
st.sampled_from([1, 2, 3, 4, 5])  # Pick from list
st.one_of(st.integers(), st.floats())  # Either int or float
```

### Custom Strategies

For complex data structures:

```python
from hypothesis import strategies as st

@st.composite
def valid_data_lists(draw, min_size=1, max_size=1000):
    """Generate valid data lists for optimization."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.lists(st.integers(), min_size=size, max_size=size))

# Use in tests
@given(data=valid_data_lists(min_size=50, max_size=200))
def test_with_custom_strategy(data):
    # ...
```

## Debugging Failing Tests

### 1. Read the Shrunk Example

Hypothesis shows the **minimal failing case**:

```
Falsifying example: test_n_jobs_positive(
    data=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
)
```

This is the **simplest** input that triggers the failure.

### 2. Reproduce the Failure

Hypothesis provides a reproduce command:

```python
@reproduce_failure('6.150.0', b'AXicczRyZMCEACJsAtY=')
@given(data=st.lists(st.integers()))
def test_something(data):
    # ...
```

Add this decorator to reproduce the exact failure.

### 3. Add Explicit Test

Once debugged, add the failing case as a regular unit test:

```python
def test_specific_edge_case():
    """Regression test for discovered edge case."""
    data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    result = optimize(lambda x: x * 2, data)
    assert result.n_jobs >= 1
```

## Configuration

### Pytest Integration

In `pytest.ini`:

```ini
[pytest]
# Hypothesis profile (default, CI, debug)
hypothesis_profile = default

[tool:pytest]
hypothesis_profile = default
```

### Hypothesis Profiles

In `conftest.py`:

```python
from hypothesis import settings, Verbosity

# Default profile
settings.register_profile("default", max_examples=50, deadline=5000)

# CI profile (more thorough)
settings.register_profile("ci", max_examples=200, deadline=10000)

# Debug profile (verbose)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)

# Load profile based on environment
import os
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
```

## Best Practices

### ✅ DO

1. **Test invariants**: Properties that must always hold
2. **Use meaningful assertions**: Clear error messages
3. **Add health checks**: Use `suppress_health_check` for known slow tests
4. **Document properties**: Explain what property is being tested
5. **Keep tests fast**: Set reasonable `deadline` values
6. **Use `assume()` for preconditions**: Filter invalid inputs

### ❌ DON'T

1. **Don't test implementation details**: Test observable behavior
2. **Don't use `@example()` for everything**: Let Hypothesis generate cases
3. **Don't set `max_examples` too high**: Slow CI/CD pipelines
4. **Don't ignore `assume()` overuse**: Too many assumes = inefficient testing
5. **Don't test unstable properties**: Non-deterministic behavior

## Performance Considerations

### Test Duration

Property-based tests run **many** examples (default: 100):

- **One test** = 100+ optimizer runs
- **20 tests** = 2000+ optimizer runs
- **Total time**: ~1-5 minutes for full suite

### Optimization Tips

1. **Reduce `max_examples` for slow tests**:
   ```python
   @settings(max_examples=20)  # Instead of default 100
   ```

2. **Increase `deadline` for slow operations**:
   ```python
   @settings(deadline=10000)  # 10 seconds per test
   ```

3. **Suppress health checks for known issues**:
   ```python
   @settings(suppress_health_check=[HealthCheck.too_slow])
   ```

4. **Use smaller data ranges**:
   ```python
   data=st.lists(st.integers(), min_size=10, max_size=100)  # Not 1000
   ```

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Run property-based tests
  run: |
    pytest tests/test_property_based_optimizer.py -v
  env:
    HYPOTHESIS_PROFILE: ci
```

### Continuous Shrinking

Hypothesis database (`.hypothesis/`) should be:
- **Committed to git**: Preserves failing cases
- **Updated by CI**: Finds new edge cases on every run
- **Reviewed on failures**: Check for new regressions

## Resources

- **Hypothesis Documentation**: https://hypothesis.readthedocs.io/
- **Property-Based Testing Introduction**: https://increment.com/testing/in-praise-of-property-based-testing/
- **Hypothesis Strategies Reference**: https://hypothesis.readthedocs.io/en/latest/data.html

## Example: Complete Property Test

```python
from hypothesis import given, settings, strategies as st, assume
import pytest

from amorsize import optimize
from amorsize.optimizer import OptimizationResult


@given(
    data=st.lists(st.integers(), min_size=10, max_size=500),
    sample_size=st.integers(min_value=1, max_value=10),
    verbose=st.booleans()
)
@settings(
    max_examples=50,
    deadline=5000,
    suppress_health_check=[HealthCheck.too_slow]
)
def test_optimize_comprehensive(data, sample_size, verbose):
    """
    Property: optimize() always returns valid result for any input.
    
    This test verifies multiple invariants:
    1. Result type is correct
    2. n_jobs is positive and reasonable
    3. chunksize is positive
    4. estimated_speedup is non-negative
    5. Verbose mode doesn't break anything
    """
    # Precondition: sample_size must be valid
    assume(sample_size <= len(data))
    
    # Run optimizer
    result = optimize(
        lambda x: x * 2,
        data,
        sample_size=sample_size,
        verbose=verbose
    )
    
    # Verify invariants
    assert isinstance(result, OptimizationResult), \
        f"Expected OptimizationResult, got {type(result)}"
    
    assert result.n_jobs >= 1, \
        f"n_jobs must be >= 1, got {result.n_jobs}"
    
    assert result.chunksize >= 1, \
        f"chunksize must be >= 1, got {result.chunksize}"
    
    assert result.estimated_speedup >= 0, \
        f"speedup must be >= 0, got {result.estimated_speedup}"
    
    from amorsize.system_info import get_physical_cores
    max_reasonable = get_physical_cores() * 2
    assert result.n_jobs <= max_reasonable, \
        f"n_jobs ({result.n_jobs}) exceeds reasonable max ({max_reasonable})"
```

## Summary

Property-based testing with Hypothesis:
- ✅ Discovers edge cases automatically
- ✅ Tests hundreds of inputs with minimal code
- ✅ Shrinks failures to minimal cases
- ✅ Prevents regressions
- ✅ Builds confidence in robustness

**Result**: More comprehensive testing with less code!
