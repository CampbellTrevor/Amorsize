# Quick Profiling Guide

## TL;DR

```python
import cProfile
import pstats
from amorsize import optimize

# Profile your code
profiler = cProfile.Profile()
profiler.enable()

# Your code here
for _ in range(10):
    result = optimize(my_function, my_data)

profiler.disable()

# See results
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')  # Sort by cumulative time (total time including subcalls)
stats.print_stats(20)
```

## When to Profile

Profile when:
- ✅ Your code is slower than expected
- ✅ You're optimizing hot paths
- ✅ You want to understand where time is spent
- ✅ Before making performance changes (baseline)

Don't profile when:
- ❌ Code is already fast enough
- ❌ You haven't tried simple optimizations first
- ❌ You're just curious (profiling has overhead)

## Quick Performance Check

```python
import time
from amorsize import optimize

def quick_perf_check():
    """Check if optimize() is your bottleneck."""
    
    # Measure optimize() time
    start = time.perf_counter()
    result = optimize(my_function, my_data)
    optimize_time = time.perf_counter() - start
    
    # Measure actual execution time
    start = time.perf_counter()
    my_function(my_data[0])  # Single item
    func_time = time.perf_counter() - start
    
    print(f"optimize() time: {optimize_time*1000:.3f}ms")
    print(f"Function time: {func_time*1000:.3f}ms")
    
    if optimize_time < func_time:
        print("✅ optimize() is NOT your bottleneck")
        print("   Focus on optimizing your function instead")
    else:
        print("⚠️ optimize() might be slow")
        print("   Consider profiling to find why")
```

## Common Optimization Targets

### 1. Your Function (Most Common)

```python
# Instead of this slow function:
def slow_function(item):
    result = []
    for i in range(1000):
        result.append(expensive_computation(item, i))
    return result

# Optimize to:
def fast_function(item):
    # Use list comprehension (faster)
    return [expensive_computation(item, i) for i in range(1000)]

# Or use numpy if applicable:
import numpy as np
def numpy_function(item):
    # Vectorized operations are much faster
    return np.array([expensive_computation(item, i) for i in range(1000)])
```

### 2. Data Preparation

```python
# Instead of preparing data each time:
for item in data:
    prepared = prepare_data(item)  # Slow: repeated prep
    result = optimize(my_func, prepared)

# Prepare once:
prepared_data = [prepare_data(item) for item in data]
result = optimize(my_func, prepared_data)
```

### 3. Caching Results

```python
from functools import lru_cache

# Cache expensive computations (maxsize=128 stores 128 most recent results)
@lru_cache(maxsize=128)
def expensive_computation(x):
    # Heavy computation here
    return result

# Now repeated calls with same input are instant
```

## Interpreting Results

### cProfile Output Columns

```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
```

- **ncalls**: Number of times function was called
- **tottime**: Total time in this function (excluding subcalls)
- **percall**: tottime / ncalls
- **cumtime**: Total time in this function (including subcalls)
- **percall**: cumtime / ncalls

### What to Look For

1. **High cumtime**: Where most time is spent (including subcalls)
2. **High ncalls with measurable time**: Called many times, could cache
3. **High tottime**: Function itself is slow (not its subcalls)

### Example Analysis

```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
   100    0.050    0.001    0.200    0.002 mymodule.py:15(expensive_func)
  1000    0.010    0.000    0.010    0.000 mymodule.py:25(helper_func)
```

Interpretation:
- `expensive_func`: Called 100 times, spends 0.2s total (0.002s per call)
  - Optimization target: Reduce calls or speed up function
- `helper_func`: Called 1000 times, but only 0.01s total (0.00001s per call)
  - Not worth optimizing (already fast)

## Advanced: Line-by-Line Profiling

For detailed analysis, use `line_profiler`:

```bash
pip install line_profiler
```

```python
# Add @profile decorator (no import needed)
@profile
def my_function(data):
    result = []
    for item in data:  # Which line is slow?
        processed = process(item)
        result.append(processed)
    return result

# Run with:
# kernprof -l -v myscript.py
```

## Performance Tips

### General Python Optimization

1. **Use built-in functions** - They're optimized in C
   ```python
   # Slow
   result = []
   for x in data:
       result.append(x * 2)
   
   # Fast
   result = [x * 2 for x in data]
   
   # Faster (if applicable)
   result = list(map(lambda x: x * 2, data))
   ```

2. **Avoid repeated attribute lookups**
   ```python
   # Slow
   for i in range(len(data)):
       data.append(i)  # Looks up 'append' each iteration
   
   # Fast
   append = data.append
   for i in range(len(data)):
       append(i)  # Uses cached reference
   ```

3. **Use local variables**
   ```python
   # Slow (global lookup)
   CONSTANT = 100
   def func():
       return CONSTANT * 2
   
   # Fast (local variable)
   def func():
       constant = 100
       return constant * 2
   ```

### Amorsize-Specific Tips

1. **Use `verbose=False` in production** - Logging has overhead
   ```python
   result = optimize(func, data, verbose=False)
   ```

2. **Cache optimization results** - If optimizing same function repeatedly
   ```python
   from amorsize import optimize
   
   # Cache the optimization result
   cached_params = optimize(my_func, sample_data)
   
   # Reuse for similar workloads
   for batch in batches:
       # Use cached parameters directly
       with Pool(cached_params.n_jobs) as pool:
           results = pool.map(my_func, batch, chunksize=cached_params.chunksize)
   ```

3. **Adjust sample_size for faster optimization**
   ```python
   # Default: 3-10 samples (accurate but slower)
   result = optimize(func, data)
   
   # Fast: 3 samples (less accurate but faster)
   result = optimize(func, data, sample_size=3)
   ```

4. **Use `diagnostic_profile=False` if you don't need details**
   ```python
   result = optimize(func, data, diagnostic_profile=False)
   ```

## Real-World Example

```python
import time
import cProfile
import pstats
from amorsize import optimize

def my_computation(item):
    """Your actual computation."""
    time.sleep(0.001)  # Simulating work
    return item ** 2

def profile_application():
    """Profile your application to find bottlenecks."""
    
    # Create profiler
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your application code
    data = list(range(1000))
    
    # Profile the optimization
    result = optimize(my_computation, data)
    
    # Profile the execution
    from multiprocessing import Pool
    with Pool(result.n_jobs) as pool:
        results = pool.map(my_computation, data, chunksize=result.chunksize)
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    
    print("=" * 80)
    print("Top 20 functions by cumulative time:")
    print("=" * 80)
    stats.print_stats(20)
    
    print("\n" + "=" * 80)
    print("Functions called most often:")
    print("=" * 80)
    stats.sort_stats('ncalls')
    stats.print_stats(20)

if __name__ == '__main__':
    profile_application()
```

## Getting Help

- **Documentation**: See `docs/PERFORMANCE_OPTIMIZATION.md` for detailed methodology
- **GitHub Issues**: Report performance problems or questions
- **Examples**: Check `examples/` directory for profiling examples

## Summary

1. **Profile first** - Don't guess where time is spent
2. **Focus on high-impact changes** - Optimize functions with high cumtime
3. **Measure improvement** - Verify optimizations actually help
4. **Consider your function first** - Usually that's the bottleneck, not `optimize()`
5. **Use caching wisely** - For repeated computations with same inputs

Happy profiling! 🚀
