# Function Performance Profiling

## Overview

Amorsize includes built-in **cProfile** integration to help you understand where time is spent **inside your functions**. This complements the existing diagnostic profiling feature that explains the optimizer's decisions.

## Two Types of Profiling

Amorsize offers two complementary profiling modes:

| Feature | Purpose | Parameter | Output |
|---------|---------|-----------|--------|
| **Function Profiling** | Shows WHERE time is spent in your function | `enable_function_profiling=True` | cProfile statistics |
| **Diagnostic Profiling** | Explains WHY optimizer made decisions | `profile=True` | Optimization analysis |

## Quick Start

Enable function profiling by adding `enable_function_profiling=True` to your `optimize()` call:

```python
from amorsize import optimize

def my_function(x):
    # Your computation here
    return x ** 2

data = range(1000)
result = optimize(my_function, data, enable_function_profiling=True)

# View the profiling results
result.show_function_profile()
```

## API Reference

### `optimize(..., enable_function_profiling=True)`

**Parameter:**
- `enable_function_profiling` (bool, default=False): If True, use Python's cProfile to profile function execution during dry run sampling

**Returns:**
- `OptimizationResult` with `function_profiler_stats` attribute containing cProfile statistics

### `OptimizationResult.show_function_profile(sort_by='cumulative', limit=20)`

Display cProfile profiling results showing where time is spent inside your function.

**Parameters:**
- `sort_by` (str): Sort key for stats. Options:
  - `'cumulative'` - Total time in function + subcalls (default)
  - `'time'` - Time spent in function itself (excluding subcalls)
  - `'calls'` - Number of function calls
  - `'name'` - Function name
- `limit` (int): Maximum number of lines to display (default: 20)

**Example:**
```python
result = optimize(my_func, data, enable_function_profiling=True)
result.show_function_profile(sort_by='cumulative', limit=30)
```

### `OptimizationResult.save_function_profile(filepath, sort_by='cumulative', limit=50)`

Save cProfile profiling results to a file for later analysis.

**Parameters:**
- `filepath` (str): Path to save profile report
- `sort_by` (str): Sort key (see `show_function_profile` for options)
- `limit` (int): Maximum number of lines to include (default: 50)

**Example:**
```python
result = optimize(my_func, data, enable_function_profiling=True)
result.save_function_profile('profile_report.txt', sort_by='time', limit=100)
```

## Usage Examples

### Example 1: Identifying Bottlenecks

```python
from amorsize import optimize

def compute_fibonacci(n):
    """Recursive Fibonacci (intentionally inefficient)."""
    if n <= 1:
        return n
    return compute_fibonacci(n - 1) + compute_fibonacci(n - 2)

def process_data(x):
    """Function with a bottleneck."""
    result = x * 2
    fib = compute_fibonacci(min(x, 20))  # Bottleneck!
    return result + fib

data = range(30)
result = optimize(process_data, data, enable_function_profiling=True)

# Show where time is spent
result.show_function_profile(limit=15)
```

**Output:**
```
================================================================================
FUNCTION PERFORMANCE PROFILE
================================================================================

Showing where time is spent inside your function:
(Sorted by: cumulative, showing top 15 entries)

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        5    0.000    0.000    0.020    0.004 process_data(...)
     33/5    0.019    0.001    0.019    0.004 compute_fibonacci(...)
                                              ^^^^^^^^^^^^^^^^^
                                              BOTTLENECK IDENTIFIED!
```

### Example 2: Understanding Call Trees

```python
def nested_function(x):
    def level1_helper(val):
        result = 0
        for i in range(50):
            result += val + i
        return result
    
    def level2_helper(val):
        return level1_helper(val) * 2
    
    def level3_helper(val):
        intermediate = level2_helper(val)
        for i in range(10):
            intermediate += level1_helper(val + i)
        return intermediate
    
    return level3_helper(x)

result = optimize(nested_function, range(100), enable_function_profiling=True)
result.show_function_profile(sort_by='cumulative', limit=20)
```

**Output shows call hierarchy:**
```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        5    0.000    0.000    0.001    0.000 nested_function(...)
        5    0.000    0.000    0.001    0.000 level3_helper(...)
       55    0.001    0.000    0.001    0.000 level1_helper(...)
        5    0.000    0.000    0.000    0.000 level2_helper(...)
```

### Example 3: Saving Profile for Later Analysis

```python
result = optimize(my_function, data, enable_function_profiling=True)

# Save to file
result.save_function_profile(
    'profile_report.txt',
    sort_by='cumulative',
    limit=50
)

# File now contains:
# ================================================================================
# FUNCTION PERFORMANCE PROFILE
# ================================================================================
# 
# Sorted by: cumulative, showing top 50 entries
# 
# [detailed profile statistics...]
```

### Example 4: Combining Both Profiling Modes

Use both profiling modes together for complete insight:

```python
result = optimize(
    my_function,
    data,
    enable_function_profiling=True,  # Function profiling (WHERE)
    profile=True  # Diagnostic profiling (WHY)
)

# View function performance profile
result.show_function_profile(limit=15)

# View optimizer diagnostic report
print(result.explain())
```

### Example 5: Different Sort Options

```python
result = optimize(my_function, data, enable_function_profiling=True)

# Sort by cumulative time (time in function + subcalls)
result.show_function_profile(sort_by='cumulative', limit=10)

# Sort by internal time (time in function itself)
result.show_function_profile(sort_by='time', limit=10)

# Sort by number of calls
result.show_function_profile(sort_by='calls', limit=10)

# Sort by function name
result.show_function_profile(sort_by='name', limit=10)
```

## Understanding Profile Output

### Profile Columns

```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
```

- **ncalls**: Number of calls to this function
- **tottime**: Total time spent in this function (excluding subcalls)
- **percall**: tottime / ncalls
- **cumtime**: Cumulative time spent in this function and all subcalls
- **percall**: cumtime / ncalls
- **filename:lineno(function)**: Function location

### Sort Options Explained

- **cumulative** (default): Best for understanding overall time distribution
  - Shows which functions contribute most to total execution time
  - Includes time spent in subcalls
  - Use when: Finding high-level bottlenecks

- **time**: Best for identifying CPU-intensive functions
  - Shows only time spent in the function itself
  - Excludes time in subcalls
  - Use when: Finding specific computational hotspots

- **calls**: Best for understanding function call patterns
  - Shows which functions are called most often
  - Use when: Identifying opportunities to reduce function calls

## When to Use Function Profiling

### Always Use When:
- ✓ Optimizing function performance
- ✓ Identifying bottlenecks and hotspots
- ✓ Debugging unexpected slowness
- ✓ Understanding function call patterns
- ✓ Before production deployment of critical functions

### Optional (Use Default) When:
- Quick prototyping
- Function is obviously simple (single operation)
- Performance is already acceptable
- Profiling overhead is a concern (though minimal)

## Performance Impact

Function profiling adds minimal overhead:
- **During sampling only**: ~5-10% overhead
- **Not during actual execution**: Profiling only occurs during dry run
- **Cached**: Profile is captured once during sampling
- **Safe for production**: Overhead is negligible for normal use

## Comparison: Function vs Diagnostic Profiling

| Aspect | Function Profiling | Diagnostic Profiling |
|--------|-------------------|---------------------|
| **Purpose** | Find bottlenecks in YOUR code | Understand optimizer decisions |
| **Technology** | Python's cProfile | Amorsize analysis |
| **Shows** | WHERE time is spent | WHY n_jobs/chunksize chosen |
| **Parameter** | `enable_function_profiling=True` | `profile=True` |
| **Output** | Call statistics, timing | Optimization reasoning |
| **Best For** | Function optimization | Parameter tuning |

## Advanced: Programmatic Access

Access profile stats programmatically for custom analysis:

```python
result = optimize(my_func, data, enable_function_profiling=True)

if result.function_profiler_stats:
    stats = result.function_profiler_stats
    
    # Access raw stats
    print(f"Total calls: {stats.total_calls}")
    print(f"Primitive calls: {stats.prim_calls}")
    
    # Custom sorting and filtering
    stats.sort_stats('time')
    stats.print_stats(10)
    
    # Extract specific function stats
    # (requires deeper pstats API knowledge)
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        if 'my_function' in str(func):
            print(f"Function: {func}")
            print(f"  Total time: {tt:.4f}s")
            print(f"  Cumulative time: {ct:.4f}s")
```

## Integration with Other Features

Function profiling works seamlessly with all Amorsize features:

```python
result = optimize(
    my_function,
    data,
    enable_function_profiling=True,  # Function profiling
    profile=True,  # Diagnostic profiling
    verbose=True,  # Console output
    use_spawn_benchmark=True,  # Accurate spawn measurement
    auto_adjust_for_nested_parallelism=True,  # Smart adjustment
    prefer_threads_for_io=True  # Automatic threading for I/O
)

# Access all features
result.show_function_profile()  # Function hotspots
print(result.explain())  # Optimizer reasoning
print(result)  # Quick summary
```

## Troubleshooting

### "Function profiling not enabled"

**Problem:** Trying to view profile without enabling it.

**Solution:**
```python
# Enable profiling
result = optimize(my_func, data, enable_function_profiling=True)
```

### No meaningful output

**Problem:** Function is too fast to profile effectively.

**Solution:**
- Increase `sample_size` for more data
- Test with larger/slower workload
- Function may be too simple to benefit from profiling

### Profile doesn't show my functions

**Problem:** Only built-in functions visible.

**Solution:**
- Your function may be calling built-ins only
- Check if function is doing actual work
- Consider profiling a more complex test case

## See Also

- [Diagnostic Profiling](README_diagnostic_profiling.md) - Understanding optimizer decisions
- [Basic Usage](basic_usage.py) - Getting started with Amorsize
- [Benchmark Validation](README_benchmark_validation.md) - Verify optimizer accuracy
- [Verbose Mode](README_intermediate_explained.md) - Console output during optimization
