# Amorsize Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using Amorsize for parallelization optimization.

## Quick Reference

Jump to your issue:

- [Function Cannot Be Pickled](#function-cannot-be-pickled)
- [Data Cannot Be Pickled](#data-cannot-be-pickled)
- [Memory Constraints Limit Workers](#memory-constraints-limit-workers)
- [No Speedup from Parallelization](#no-speedup-from-parallelization)
- [Workload Too Small](#workload-too-small)
- [Sampling Failures](#sampling-failures)
- [Generator Exhausted](#generator-exhausted)
- [Windows/macOS Spawn Issues](#windowsmacos-spawn-issues)
- [Docker/Container Memory Issues](#dockercontainer-memory-issues)
- [Nested Parallelism Conflicts](#nested-parallelism-conflicts)
- [Import Errors in Workers](#import-errors-in-workers)
- [Performance Not as Expected](#performance-not-as-expected)

---

## Common Issues and Solutions

### Function Cannot Be Pickled

**Symptom:** Error message says function cannot be pickled, falls back to serial execution.

**Cause:** Multiprocessing requires functions to be serializable (picklable). Lambda functions, nested functions, and closures cannot be pickled by default.

**Solutions:**

#### 1. Convert Lambda to Regular Function

```python
# ❌ WRONG - Lambda cannot be pickled
func = lambda x: x**2

# ✅ CORRECT - Regular function works
def func(x):
    return x**2
```

#### 2. Move Nested Function to Module Level

```python
# ❌ WRONG - Nested function cannot be pickled
def outer_function():
    def process(x):
        return x**2
    
    result = optimize(process, data)

# ✅ CORRECT - Move to module level
def process(x):
    return x**2

def outer_function():
    result = optimize(process, data)
```

#### 3. Avoid Closures with External Variables

```python
# ❌ WRONG - Closure references external variable
multiplier = 10

def process(x):
    return x * multiplier  # References external variable

# ✅ CORRECT - Pass as parameter or use global
def process(x, multiplier=10):
    return x * multiplier

# OR use a class
class Processor:
    def __init__(self, multiplier):
        self.multiplier = multiplier
    
    def process(self, x):
        return x * self.multiplier

processor = Processor(10)
result = optimize(processor.process, data)
```

#### 4. Alternative: Use cloudpickle

```python
pip install cloudpickle

# cloudpickle can handle more complex functions
# Use with concurrent.futures.ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor
import cloudpickle

# Your complex function here
def complex_func(x):
    # Can use closures, lambdas, etc.
    return x**2
```

**See Also:** [examples/README_data_picklability.md](../examples/README_data_picklability.md)

---

### Data Cannot Be Pickled

**Symptom:** Error message says data item at index X cannot be pickled.

**Cause:** Your input data contains objects that cannot be serialized (file handles, database connections, locks, sockets).

**Solutions:**

#### 1. Pass File Paths, Not File Objects

```python
# ❌ WRONG - File objects cannot be pickled
files = [open(f, 'r') for f in filenames]
result = optimize(process_file, files)

# ✅ CORRECT - Pass paths, open in function
def process_file(filepath):
    with open(filepath, 'r') as f:
        return process_content(f.read())

result = optimize(process_file, filenames)
```

#### 2. Pass Connection Strings, Not Connections

```python
# ❌ WRONG - Database connections cannot be pickled
conn = sqlite3.connect('database.db')
queries = [(conn, q) for q in query_list]

# ✅ CORRECT - Create connection in each worker
def execute_query(query):
    conn = sqlite3.connect('database.db')
    result = conn.execute(query).fetchall()
    conn.close()
    return result

result = optimize(execute_query, query_list)
```

#### 3. Extract Serializable Data Only

```python
# ❌ WRONG - Complex objects with unpicklable parts
class ComplexObject:
    def __init__(self, data):
        self.data = data
        self.lock = threading.Lock()  # Cannot pickle
        self.file = open('temp.txt')  # Cannot pickle

# ✅ CORRECT - Extract only what you need
data_to_process = [(obj.id, obj.data) for obj in complex_objects]

def process(id, data):
    # Process with serializable data
    return transform(id, data)
```

#### 4. Use Shared Memory for Large Arrays (Python 3.8+)

```python
# For large numpy arrays
from multiprocessing import shared_memory
import numpy as np

# Create shared memory
shm = shared_memory.SharedMemory(create=True, size=arr.nbytes)
shared_arr = np.ndarray(arr.shape, dtype=arr.dtype, buffer=shm.buf)
shared_arr[:] = arr[:]

# Pass shape, dtype, and name instead of array
def process_with_shared(index, shm_name, shape, dtype):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    arr = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
    result = arr[index] * 2
    existing_shm.close()
    return result
```

**See Also:** [examples/README_data_picklability.md](../examples/README_data_picklability.md)

---

### Memory Constraints Limit Workers

**Symptom:** Warning that memory constraints limit worker count from optimal to lower value.

**Cause:** Each worker requires memory, and your system doesn't have enough RAM to run the optimal number of workers.

**Solutions:**

#### 1. Reduce Memory Footprint

```python
def memory_efficient(x):
    # ❌ Bad - Creates large intermediate structures
    intermediate = [x**i for i in range(10000)]
    result = sum(intermediate)
    
    # ✅ Good - Use generators
    result = sum(x**i for i in range(10000))
    
    # ✅ Good - Delete large temporaries
    temp = expensive_computation()
    result = process(temp)
    del temp  # Free memory immediately
    
    return result
```

#### 2. Use Batch Processing

```python
from amorsize import process_in_batches

# Process in smaller batches to control memory
results = process_in_batches(
    func, data,
    batch_size=100,          # Process 100 at a time
    max_memory_percent=0.5   # Use at most 50% of RAM
)
```

#### 3. Use Streaming for Large Datasets

```python
from amorsize import optimize_streaming
from multiprocessing import Pool

# For large datasets, use streaming
result = optimize_streaming(func, large_data)

with Pool(result.n_jobs) as pool:
    # Process results as they arrive (no accumulation)
    for item in pool.imap_unordered(func, result.data, chunksize=result.chunksize):
        process_result(item)  # Handle immediately
```

#### 4. Use NumPy Views Instead of Copies

```python
import numpy as np

def efficient_array_process(arr):
    # ❌ Bad - Creates copy
    subset = arr[10:100].copy()
    
    # ✅ Good - Uses view (no copy)
    subset = arr[10:100]
    result = np.sum(subset)
    return result
```

**See Also:** 
- [examples/README_batch_processing.md](../examples/README_batch_processing.md)
- [examples/README_streaming_optimization.md](../examples/README_streaming_optimization.md)

---

### No Speedup from Parallelization

**Symptom:** Optimizer recommends n_jobs=1 (serial) because parallelization provides no benefit.

**Cause:** Your function is too fast or your dataset is too small. The overhead of process creation and data serialization exceeds the time saved.

**Solutions:**

#### 1. Make Function Do More Work

```python
# ❌ Too fast - no parallel benefit
def fast_func(x):
    return x**2  # Microseconds

# ✅ Better - substantial work
def substantial_func(x):
    result = 0
    for i in range(1000):
        result += x**i
    return result  # Milliseconds
```

#### 2. Increase Dataset Size

```python
# ❌ Too small
data = range(10)  # 10 items

# ✅ Better
data = range(10000)  # 10,000 items
```

#### 3. Batch Multiple Items Together

```python
# Instead of processing individual items
def process_one(x):
    return x**2

# Batch them
def process_batch(items):
    return [x**2 for x in items]

# Create batches
batch_size = 10
batched_data = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]
result = optimize(process_batch, batched_data)
```

#### 4. Understand the Overhead

```python
from amorsize import optimize

# Use diagnostic mode to see why
result = optimize(func, data, profile=True, verbose=True)
print(result.explain())

# Check the timing breakdown
# Function time should be >> overhead time
```

**Rule of Thumb:** Function should take at least 10ms per call for parallel benefit with default settings.

---

### Workload Too Small

**Symptom:** Warning that workload is too small for effective parallelization.

**Cause:** You have too few items to process. The fixed overhead of creating workers outweighs the parallel benefit.

**Solutions:**

#### 1. Accumulate More Items

```python
# ❌ Processing immediately
def process_as_arrives(item):
    result = optimize(func, [item])  # Single item!

# ✅ Accumulate then process
accumulated_items = []
for item in stream:
    accumulated_items.append(item)
    
    if len(accumulated_items) >= 1000:  # Threshold
        results = optimize(func, accumulated_items)
        process_results(results)
        accumulated_items = []
```

#### 2. Make Each Item More Expensive

```python
# ❌ Simple operation
def simple(x):
    return x + 1

# ✅ More complex operation
def complex_operation(x):
    result = 0
    for i in range(10000):
        result += math.sin(x * i)
    return result
```

#### 3. Just Use Serial for Small Workloads

```python
# For small datasets, serial is fine
if len(data) < 100:
    results = [func(x) for x in data]
else:
    result = optimize(func, data)
    # Use result.n_jobs, result.chunksize
```

**Rule of Thumb:** Need at least 100+ items for parallel benefit in most cases.

---

### Sampling Failures

**Symptom:** Optimizer fails during sampling phase with an error.

**Cause:** Your function raises an exception when called with sample data, or your data is invalid.

**Solutions:**

#### 1. Test Function Manually

```python
# Test with your actual data
try:
    sample_item = next(iter(data))
    result = func(sample_item)
    print(f"Success: {result}")
except Exception as e:
    print(f"Function error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
```

#### 2. Validate Your Data

```python
# Check data is not empty
if not data or len(list(data)) == 0:
    print("Error: Data is empty")

# Check data types
for item in data[:5]:
    print(f"Item: {item}, Type: {type(item)}")

# For generators, ensure not exhausted
gen = my_generator()
data = list(gen)  # Convert to list if small enough
```

#### 3. Add Error Handling to Function

```python
def robust_function(x):
    if x is None:
        return 0  # Default for None
    
    try:
        return expensive_computation(x)
    except ValueError as e:
        # Handle specific errors gracefully
        return fallback_computation(x)
    except Exception as e:
        # Log unexpected errors
        print(f"Error processing {x}: {e}")
        raise
```

#### 4. Use Verbose Mode

```python
# Get detailed diagnostics
result = optimize(func, data, verbose=True)

# See exactly where it fails
```

---

### Generator Exhausted

**Symptom:** Error about iterator being exhausted, or optimization works but execution fails.

**Cause:** Generators can only be consumed once. Amorsize samples the data, which exhausts the generator.

**Solutions:**

#### 1. Use List Instead (If Small)

```python
# ❌ Generator will be exhausted
gen = (x for x in range(1000))
result = optimize(func, gen)

# ✅ Convert to list first
data = list(range(1000))
result = optimize(func, data)
```

#### 2. Amorsize Handles This Automatically

```python
# Amorsize preserves generators using itertools.chain
gen = (x for x in range(100000))
result = optimize(func, gen)

# result.data is a fresh iterator that can be used
with Pool(result.n_jobs) as pool:
    results = pool.map(func, result.data, chunksize=result.chunksize)
```

#### 3. Use a Generator Function

```python
# ❌ Generator expression exhausted
gen = (expensive_load(x) for x in filenames)

# ✅ Generator function can be called multiple times
def generate_data():
    for x in filenames:
        yield expensive_load(x)

# If you need to sample multiple times
result = optimize(func, generate_data())
```

**See Also:** [examples/README_generator_safety.md](../examples/README_generator_safety.md)

---

### Windows/macOS Spawn Issues

**Symptom:** Errors about pickling, or slow startup on Windows/macOS.

**Cause:** Windows and macOS (Python 3.8+) use `spawn` start method, which requires stricter pickling and has higher overhead.

**Solutions:**

#### 1. Protect Main Code

```python
# ❌ WRONG - Code runs in workers too
def my_function(x):
    return x**2

data = range(1000)
result = optimize(my_function, data)

# ✅ CORRECT - Protect with if __name__ == '__main__'
def my_function(x):
    return x**2

if __name__ == '__main__':
    data = range(1000)
    result = optimize(my_function, data)
```

#### 2. Define Functions at Module Level

```python
# ❌ WRONG - Function defined inside main
if __name__ == '__main__':
    def process(x):
        return x**2
    
    result = optimize(process, data)

# ✅ CORRECT - Function at module level
def process(x):
    return x**2

if __name__ == '__main__':
    result = optimize(process, data)
```

#### 3. Expect Higher Overhead

```python
# On Windows/macOS, spawn cost is ~200ms vs ~15ms for fork
# Amorsize automatically accounts for this

# For very fast functions, you may need more work per call
# to overcome the higher overhead
```

#### 4. Consider Using fork (Unix only)

```python
import multiprocessing

# On Unix systems (not Windows), can use fork
if hasattr(os, 'fork'):
    multiprocessing.set_start_method('fork')

# Must be called before any multiprocessing code
```

**See Also:** System-specific documentation in [examples/README_system_validation.md](../examples/README_system_validation.md)

---

### Docker/Container Memory Issues

**Symptom:** Workers killed by OOM (Out Of Memory), or memory limit warnings.

**Cause:** Docker/containers use cgroups to limit memory. Amorsize might see host memory instead of container limit.

**Verification:**

```python
from amorsize.system_info import get_available_memory

# Check what Amorsize sees
memory_bytes = get_available_memory()
memory_gb = memory_bytes / (1024**3)
print(f"Detected memory: {memory_gb:.2f} GB")

# Compare with your container limit
# docker run -m 2g  # Should show ~2 GB
```

**Solutions:**

#### 1. Amorsize Automatically Detects cgroup Limits

```python
# Amorsize checks these automatically:
# - /sys/fs/cgroup/memory.max (cgroup v2)
# - /sys/fs/cgroup/memory/memory.limit_in_bytes (cgroup v1)

# No action needed - should work automatically
```

#### 2. If Detection Fails, Set Environment Variable

```bash
# Set available memory manually
export AMORSIZE_MAX_MEMORY_GB=2

# Or in Python
import os
os.environ['AMORSIZE_MAX_MEMORY_GB'] = '2'
```

#### 3. Use Conservative Memory Settings

```python
from amorsize import optimize

# Use less memory than available
result = optimize(
    func, data,
    max_memory_percent=0.5  # Use only 50% of detected memory
)
```

#### 4. Monitor Memory Usage

```bash
# In container, monitor memory
docker stats

# Or with psutil
python3 -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

**Note:** Enhanced cgroup support added in Iteration 69.

---

### Nested Parallelism Conflicts

**Symptom:** Warning about nested parallelism detected, or system becomes unresponsive.

**Cause:** Your function uses libraries that spawn threads (NumPy, scikit-learn, etc.), causing oversubscription.

**Solutions:**

#### 1. Set Thread Environment Variables

```python
import os

# Before importing numpy/scipy/sklearn
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import numpy as np
# Now imports won't use multiple threads per process
```

#### 2. Amorsize Auto-Adjusts (Iteration 89)

```python
# Amorsize detects nested parallelism and adjusts workers
result = optimize(func, data, verbose=True)

# Will show: "Nested parallelism detected, reducing workers"
# auto_adjust_nested_parallelism=True by default
```

#### 3. Control Manually

```python
# Disable auto-adjustment if you want control
result = optimize(
    func, data,
    auto_adjust_nested_parallelism=False
)
```

#### 4. Set Thread Count in Function

```python
import threadpoolctl

def process(x):
    # Limit threads within each worker
    with threadpoolctl.threadpool_limits(limits=1):
        return numpy_intensive_computation(x)
```

**See Also:** [examples/README_nested_parallelism.md](../examples/README_nested_parallelism.md)

---

### Import Errors in Workers

**Symptom:** Workers fail with ImportError or ModuleNotFoundError.

**Cause:** With `spawn` start method, workers are fresh processes that need to import modules.

**Solutions:**

#### 1. Use Module-Level Imports

```python
# ❌ WRONG - Import inside function
def process(x):
    import numpy as np  # Imported every call!
    return np.sum(x)

# ✅ CORRECT - Import at module level
import numpy as np

def process(x):
    return np.sum(x)
```

#### 2. Ensure Modules Are Installed

```bash
# Install in your environment
pip install numpy scipy pandas

# Or in requirements.txt
numpy>=1.20.0
scipy>=1.7.0
```

#### 3. Check PYTHONPATH

```python
import sys
print("Python path:", sys.path)

# Add custom paths if needed
sys.path.append('/path/to/your/modules')
```

#### 4. Use Absolute Imports

```python
# ❌ Relative imports can fail
from .mymodule import func

# ✅ Absolute imports more reliable
from mypackage.mymodule import func
```

---

### Performance Not as Expected

**Symptom:** Actual speedup doesn't match predicted speedup.

**Cause:** Many factors: system load, memory bandwidth, cache effects, measurement variance.

**Diagnosis:**

#### 1. Use Benchmark Validation

```python
from amorsize import validate_optimization

# Compare predicted vs actual performance
result = validate_optimization(func, data, verbose=True)

print(f"Predicted speedup: {result.predicted_speedup:.2f}x")
print(f"Actual speedup: {result.actual_speedup:.2f}x")
print(f"Accuracy: {result.accuracy_percent:.1f}%")
```

#### 2. Use Diagnostic Profiling

```python
from amorsize import optimize

result = optimize(func, data, profile=True, verbose=True)
print(result.explain())

# Shows detailed breakdown:
# - Function execution time
# - Serialization overhead
# - Worker spawn cost
# - Memory usage
# - Amdahl's law calculation
```

#### 3. Compare Different Strategies

```python
from amorsize import compare_strategies

comparison = compare_strategies(
    func, data,
    strategies=['serial', 'all_cores', 'optimal'],
    verbose=True
)

# See which is actually fastest
```

#### 4. Check System Factors

```python
# System load
import psutil
print(f"CPU usage: {psutil.cpu_percent()}%")
print(f"Memory usage: {psutil.virtual_memory().percent}%")

# Other processes competing for resources?
print(f"Active processes: {len(psutil.pids())}")
```

**See Also:**
- [examples/README_benchmark_validation.md](../examples/README_benchmark_validation.md)
- [examples/README_diagnostic_profiling.md](../examples/README_diagnostic_profiling.md)
- [examples/README_comparison_mode.md](../examples/README_comparison_mode.md)

---

## Best Practices

### When to Use Amorsize

✅ **Good Use Cases:**
- CPU-bound workloads (heavy computation)
- Large datasets (1000+ items)
- Functions taking >10ms per call
- Repeated workloads (use config caching)
- Memory-intensive tasks (uses memory awareness)

❌ **Poor Use Cases:**
- I/O-bound workloads (use threads instead)
- Very fast functions (<1ms per call)
- Small datasets (<100 items)
- One-off scripts (overhead not worth it)
- Tasks requiring shared state

### Optimization Checklist

Before optimizing:

1. **Profile your function**
   ```python
   result = optimize(func, data, enable_function_profiling=True)
   ```

2. **Check if CPU-bound**
   ```python
   # If waiting on I/O, use ThreadPoolExecutor instead
   ```

3. **Validate your data and function**
   ```python
   # Test manually first
   result = func(data[0])
   ```

4. **Use verbose mode**
   ```python
   result = optimize(func, data, verbose=True)
   ```

5. **Validate predictions**
   ```python
   from amorsize import validate_optimization
   validation = validate_optimization(func, data)
   ```

### Common Patterns

#### Pattern 1: Simple Optimization

```python
from amorsize import execute

def my_function(x):
    # Your code here
    return result

data = range(10000)

# One-liner: optimize and execute
results = execute(my_function, data, verbose=True)
```

#### Pattern 2: Reusable Configuration

```python
from amorsize import optimize, load_config
from multiprocessing import Pool

# First run: optimize and save
result = optimize(func, sample_data)
result.save_config('production.json')

# Subsequent runs: load config (fast!)
config = load_config('production.json')
with Pool(config.n_jobs) as pool:
    results = pool.map(func, data, chunksize=config.chunksize)
```

#### Pattern 3: Streaming Large Data

```python
from amorsize import optimize_streaming
from multiprocessing import Pool

result = optimize_streaming(func, large_dataset)

with Pool(result.n_jobs) as pool:
    for item in pool.imap_unordered(func, result.data, chunksize=result.chunksize):
        # Process results as they arrive
        save_to_disk(item)
```

#### Pattern 4: Memory-Constrained Processing

```python
from amorsize import process_in_batches

# Automatically handles memory limits
results = process_in_batches(
    func, large_data,
    max_memory_percent=0.6,  # Use 60% of RAM
    verbose=True
)
```

---

## Diagnostic Tools

### 1. System Validation

```python
from amorsize import validate_system

# Check system capabilities
result = validate_system()
print(result.report())

# Shows:
# - Physical cores
# - Available memory
# - Start method (fork/spawn)
# - Spawn cost measurement
# - psutil availability
```

### 2. Function Profiling

```python
result = optimize(
    func, data,
    enable_function_profiling=True,
    verbose=True
)

# Shows line-by-line timing
result.show_function_profile()
```

### 3. Performance Benchmarking

```python
from amorsize import run_performance_benchmark

# Test with standard workloads
results = run_performance_benchmark(func, verbose=True)

# Compare against baselines
```

### 4. Cache Inspection

```python
from amorsize import get_cache_stats

stats = get_cache_stats()
print(f"Cache entries: {stats.total_entries}")
print(f"Cache size: {stats.size_mb:.2f} MB")
print(f"Hit rate: {stats.hit_rate:.1%}")
```

---

## Getting Help

### Enable Verbose Mode

Always start with verbose mode for detailed output:

```python
result = optimize(func, data, verbose=True)
```

### Use Diagnostic Profile

For deep analysis:

```python
result = optimize(func, data, profile=True, verbose=True)
print(result.explain())
```

### Check the Examples

Comprehensive examples in `examples/` directory:
- `basic_usage.py` - Simple examples
- `README_*.md` - Topic-specific guides

### Report Issues

When reporting issues, include:

1. Amorsize version
   ```python
   import amorsize
   print(amorsize.__version__)
   ```

2. System information
   ```python
   from amorsize import validate_system
   print(validate_system().report())
   ```

3. Minimal reproducible example

4. Full error message with traceback

5. Expected vs actual behavior

---

## Summary

Key takeaways:

1. **Functions and data must be picklable** - Use module-level functions, avoid lambdas
2. **Fast functions need parallel work** - Function should take >10ms per call
3. **Small datasets stay serial** - Need 100+ items for parallel benefit
4. **Use verbose mode** - Get detailed diagnostics
5. **Test manually first** - Validate function and data before optimizing
6. **Memory matters** - Use streaming/batching for large results
7. **System-aware** - Amorsize automatically detects OS, memory, cores
8. **Windows/macOS need protection** - Use `if __name__ == '__main__':`

For more information, see:
- [Main README](../README.md)
- [Examples Directory](../examples/)
- [API Documentation](../docs/)
