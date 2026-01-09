# Input Validation in Amorsize

## Overview

Starting from Iteration 11, Amorsize includes comprehensive input validation for the `optimize()` function. This ensures that invalid parameters are caught early with clear error messages, preventing confusing runtime errors or undefined behavior.

## What Gets Validated

### 1. Function Parameter (`func`)

The function must be:
- **Not None**: Cannot pass `None` as the function
- **Callable**: Must be a function, method, lambda, or other callable object

**Examples:**
```python
# ✗ Invalid - None
optimize(None, data)
# ValueError: Invalid parameter: func parameter cannot be None

# ✗ Invalid - Not callable
optimize(123, data)
# ValueError: Invalid parameter: func parameter must be callable, got int

# ✓ Valid - Regular function
def my_func(x):
    return x * 2
optimize(my_func, data)

# ✓ Valid - Lambda (though may fail picklability check)
optimize(lambda x: x * 2, data)
```

### 2. Data Parameter (`data`)

The data must be:
- **Not None**: Cannot pass `None` as data
- **Iterable**: Must have `__iter__` method (list, tuple, generator, range, etc.)

**Note**: Empty iterables are valid (e.g., `[]`), but will result in serial execution.

**Examples:**
```python
# ✗ Invalid - None
optimize(func, None)
# ValueError: Invalid parameter: data parameter cannot be None

# ✗ Invalid - Not iterable
optimize(func, 123)
# ValueError: Invalid parameter: data parameter must be iterable, got int

# ✓ Valid - List
optimize(func, [1, 2, 3])

# ✓ Valid - Generator
optimize(func, (x for x in range(100)))

# ✓ Valid - Range
optimize(func, range(1000))

# ✓ Valid - Empty list (handled by optimizer, returns serial)
optimize(func, [])
```

### 3. Sample Size Parameter (`sample_size`)

The sample size must be:
- **Integer**: Must be `int` type (not float, not string)
- **Positive**: Must be > 0
- **Reasonable**: Must be ≤ 10,000 (protection against memory exhaustion)

**Examples:**
```python
# ✗ Invalid - Negative
optimize(func, data, sample_size=-1)
# ValueError: Invalid parameter: sample_size must be positive, got -1

# ✗ Invalid - Zero
optimize(func, data, sample_size=0)
# ValueError: Invalid parameter: sample_size must be positive, got 0

# ✗ Invalid - Too large
optimize(func, data, sample_size=100000)
# ValueError: Invalid parameter: sample_size is unreasonably large (100000), maximum is 10000

# ✗ Invalid - Float
optimize(func, data, sample_size=5.5)
# ValueError: Invalid parameter: sample_size must be an integer, got float

# ✓ Valid - Minimum
optimize(func, data, sample_size=1)

# ✓ Valid - Default
optimize(func, data, sample_size=5)

# ✓ Valid - Maximum
optimize(func, data, sample_size=10000)
```

### 4. Target Chunk Duration Parameter (`target_chunk_duration`)

The target chunk duration must be:
- **Numeric**: Must be `int` or `float` (not string, not None)
- **Positive**: Must be > 0
- **Reasonable**: Must be ≤ 3600 seconds (1 hour)

**Examples:**
```python
# ✗ Invalid - Negative
optimize(func, data, target_chunk_duration=-0.1)
# ValueError: Invalid parameter: target_chunk_duration must be positive, got -0.1

# ✗ Invalid - Zero
optimize(func, data, target_chunk_duration=0)
# ValueError: Invalid parameter: target_chunk_duration must be positive, got 0

# ✗ Invalid - Too large
optimize(func, data, target_chunk_duration=10000)
# ValueError: Invalid parameter: target_chunk_duration is unreasonably large (10000s), maximum is 3600s

# ✗ Invalid - String
optimize(func, data, target_chunk_duration="0.2")
# ValueError: Invalid parameter: target_chunk_duration must be a number, got str

# ✓ Valid - Very small
optimize(func, data, target_chunk_duration=0.001)

# ✓ Valid - Default
optimize(func, data, target_chunk_duration=0.2)

# ✓ Valid - Integer
optimize(func, data, target_chunk_duration=1)

# ✓ Valid - Maximum
optimize(func, data, target_chunk_duration=3600)
```

### 5. Boolean Parameters (`verbose`, `use_spawn_benchmark`, `use_chunking_benchmark`, `profile`)

All boolean parameters must be:
- **Boolean type**: Must be `True` or `False` (not 0/1, not "true"/"false")

**Examples:**
```python
# ✗ Invalid - Integer instead of boolean
optimize(func, data, verbose=1)
# ValueError: Invalid parameter: verbose must be a boolean, got int

# ✗ Invalid - String instead of boolean
optimize(func, data, profile="true")
# ValueError: Invalid parameter: profile must be a boolean, got str

# ✓ Valid - Explicit True
optimize(func, data, verbose=True)

# ✓ Valid - Explicit False
optimize(func, data, verbose=False)

# ✓ Valid - All booleans
optimize(func, data, verbose=True, use_spawn_benchmark=False, profile=True)
```

## Why Validation Matters

### 1. Early Error Detection

Without validation, invalid parameters could cause:
- **Cryptic errors deep in the code**: "AttributeError: 'int' object has no attribute '__call__'"
- **Silent failures**: Wrong results without error messages
- **Undefined behavior**: Unpredictable outcomes

With validation, errors are caught immediately with clear messages:
```python
# Without validation (hypothetical):
optimize(123, [1, 2, 3])  # Crashes later with AttributeError

# With validation:
optimize(123, [1, 2, 3])
# ValueError: Invalid parameter: func parameter must be callable, got int
```

### 2. Protection Against Resource Exhaustion

Validation prevents potentially dangerous parameter values:
- **sample_size > 10,000**: Could exhaust memory during sampling
- **target_chunk_duration > 3600**: Unreasonable chunk sizes

### 3. Clear Error Messages

Every validation error provides:
- **What's wrong**: Clear description of the problem
- **What was provided**: The actual value that failed
- **What's expected**: The valid range or type

Example:
```
ValueError: Invalid parameter: sample_size is unreasonably large (100000), maximum is 10000
```

### 4. Type Safety

Python's duck typing can lead to subtle bugs. Validation enforces type contracts:
```python
# These look similar but have different types:
optimize(func, data, verbose=True)   # ✓ Valid
optimize(func, data, verbose=1)      # ✗ Invalid - not a boolean
```

## What Validation Does NOT Catch

Validation is for parameter correctness, not optimization-time issues:

### 1. Empty Data

Empty data is valid input but results in serial execution:
```python
result = optimize(func, [])  # ✓ Valid parameter
# Returns: n_jobs=1 (serial execution)
```

### 2. Unpicklable Functions

Function picklability is checked during optimization, not validation:
```python
result = optimize(lambda x: x * 2, [1, 2, 3])  # ✓ Valid parameter
# Returns: n_jobs=1 with reason "Function is not picklable"
```

### 3. Unpicklable Data

Data picklability is checked during sampling, not validation:
```python
import threading
data = [{"lock": threading.Lock()}]
result = optimize(func, data)  # ✓ Valid parameter
# Returns: n_jobs=1 with reason "Data items are not picklable"
```

### 4. Memory Issues

Large result objects are detected during optimization, not validation:
```python
result = optimize(func, range(1_000_000))  # ✓ Valid parameter
# May return warnings about memory constraints
```

## Best Practices

### 1. Catch Validation Errors

Wrap calls in try-except for graceful error handling:
```python
def safe_optimize(func, data, **kwargs):
    try:
        return optimize(func, data, **kwargs)
    except ValueError as e:
        print(f"Validation error: {e}")
        # Fall back to defaults or handle gracefully
        return optimize(func, data)  # Use defaults
```

### 2. Use Reasonable Parameter Values

Follow these guidelines:

**sample_size:**
- Small datasets (< 100 items): 5 (default)
- Medium datasets (100-10K items): 10-50
- Large datasets (> 10K items): 50-100
- Never exceed 10,000

**target_chunk_duration:**
- Fast functions (< 1ms): 0.1-0.5s
- Medium functions (1-100ms): 0.2s (default)
- Slow functions (> 100ms): 0.5-2.0s
- Never exceed 3600s

### 3. Validate User Input

If your code accepts user input for optimization parameters, validate it first:
```python
def optimize_with_user_params(func, data, user_sample_size):
    # Validate user input before passing to optimize()
    if not isinstance(user_sample_size, int):
        raise ValueError("sample_size must be an integer")
    if user_sample_size < 1 or user_sample_size > 10000:
        raise ValueError("sample_size must be between 1 and 10000")
    
    return optimize(func, data, sample_size=user_sample_size)
```

## Integration with Existing Code

Validation is **non-breaking**:
- All existing valid code continues to work
- Only invalid code that would have failed anyway now fails earlier with better errors
- No performance impact (validation is < 1μs)

## Running the Demo

See the comprehensive validation examples:
```bash
python examples/input_validation_demo.py
```

This demonstrates:
- All valid input patterns
- All validation errors with messages
- Best practices for safe usage

## Testing

The validation feature includes 31 comprehensive tests covering:
- All parameter types and constraints
- Edge cases (minimum, maximum, boundary values)
- Error messages and exception types
- Integration with existing functionality

Run tests:
```bash
pytest tests/test_input_validation.py -v
```

## Summary

Input validation in Amorsize:
- ✅ Catches invalid parameters early
- ✅ Provides clear, actionable error messages
- ✅ Protects against resource exhaustion
- ✅ Enforces type safety
- ✅ Non-breaking (existing valid code works unchanged)
- ✅ Minimal performance overhead (< 1μs)
- ✅ Comprehensive test coverage (31 tests)

This makes Amorsize safer and easier to use, especially in production environments where clear error messages are critical for debugging.
