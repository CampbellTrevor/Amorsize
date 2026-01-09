# Auto-Tuning Guide

This guide explains how to use Amorsize's auto-tuning feature to empirically find the optimal `n_jobs` and `chunksize` parameters for your specific workload.

## Why Auto-Tuning?

While `optimize()` provides fast recommendations based on analytical models, **auto-tuning** uses empirical benchmarking to find the actual optimal configuration through trial and error. This is useful when:

- You need the absolute best performance
- Your workload has complex characteristics that are hard to model
- You want to validate optimizer predictions
- System-specific factors significantly impact performance

## Quick Start

### Python API

```python
from amorsize import tune_parameters, quick_tune

def expensive_func(x):
    """Your CPU-intensive function."""
    return sum(i**2 for i in range(x))

data = range(100, 500)

# Option 1: Full tuning (more thorough)
result = tune_parameters(expensive_func, data, verbose=True)
print(f"Optimal: n_jobs={result.best_n_jobs}, chunksize={result.best_chunksize}")
print(f"Speedup: {result.best_speedup:.2f}x")

# Option 2: Quick tuning (faster)
result = quick_tune(expensive_func, data, verbose=True)
```

### Command Line

```bash
# Quick tuning (minimal search space)
python -m amorsize tune mymodule.func --data-range 1000 --quick --verbose

# Full tuning with custom search space
python -m amorsize tune mymodule.func --data-range 1000 \
    --n-jobs-range 1 2 4 8 \
    --chunksize-range 10 50 100 \
    --verbose

# JSON output for scripting
python -m amorsize tune math.factorial --data-range 500 --json

# Save result to history
python -m amorsize tune mymodule.func --data-range 1000 \
    --save-result "my_tuning_v1"
```

## Python API Reference

### `tune_parameters(func, data, ...)`

Automatically find optimal parameters through grid search.

**Parameters:**

- `func` (Callable): Function to optimize (must accept single argument)
- `data` (Iterable): Input data (list, range, or iterator)
- `n_jobs_range` (List[int], optional): List of n_jobs values to test
  - Default: `[1, physical_cores//2, physical_cores]` plus optimizer hint
- `chunksize_range` (List[int], optional): List of chunksize values to test
  - Default: Smart selection based on data size plus optimizer hint
- `use_optimizer_hint` (bool): Include optimizer recommendation in search (default: True)
- `verbose` (bool): Print progress during search (default: False)
- `timeout_per_config` (float, optional): Maximum seconds per configuration
- `prefer_threads_for_io` (bool): Use ThreadPoolExecutor instead of multiprocessing.Pool

**Returns:**

`TuningResult` with attributes:
- `best_n_jobs`: Optimal number of workers
- `best_chunksize`: Optimal chunk size
- `best_time`: Execution time with optimal config (seconds)
- `best_speedup`: Speedup vs serial execution
- `serial_time`: Baseline serial execution time
- `configurations_tested`: Number of configs benchmarked
- `all_results`: Dict mapping `(n_jobs, chunksize)` to execution time
- `optimization_hint`: Initial optimizer recommendation
- `search_strategy`: Strategy used ("grid", etc.)
- `executor_type`: "process" or "thread"

**Methods:**

- `get_top_configurations(n=5)`: Get top N configurations by execution time

**Example:**

```python
from amorsize import tune_parameters

def process_item(x):
    """Expensive computation."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result

data = range(10000)

# Full tuning with custom search space
result = tune_parameters(
    process_item, 
    data,
    n_jobs_range=[1, 2, 4, 8],
    chunksize_range=[50, 100, 200],
    verbose=True
)

print(result)
# === Auto-Tuning Results ===
# 
# Search Strategy: grid
# Configurations Tested: 13
# 
# Performance:
#   Serial execution time:   45.2341s
#   Best parallel time:      7.8932s
#   Best speedup:            5.73x
# 
# Optimal Configuration:
#   n_jobs:     8
#   chunksize:  100

# Use optimal configuration
from multiprocessing import Pool
with Pool(processes=result.best_n_jobs) as pool:
    results = pool.map(process_item, data, chunksize=result.best_chunksize)
```

### `quick_tune(func, data, ...)`

Quick auto-tuning with minimal search space (faster but less thorough).

**Parameters:**

- `func` (Callable): Function to optimize
- `data` (Iterable): Input data
- `verbose` (bool): Print progress (default: False)
- `prefer_threads_for_io` (bool): Use ThreadPoolExecutor

**Returns:** `TuningResult`

**Example:**

```python
from amorsize import quick_tune

# Quick tuning for fast iteration
result = quick_tune(process_item, data, verbose=True)
print(f"Quick result: {result.best_n_jobs}x{result.best_chunksize} = {result.best_speedup:.2f}x")
```

## CLI Reference

### Basic Usage

```bash
# Quick tuning (minimal search, fast)
python -m amorsize tune module.function --data-range N --quick

# Full tuning (comprehensive search)
python -m amorsize tune module.function --data-range N
```

### Data Sources

```bash
# Range data
python -m amorsize tune math.factorial --data-range 1000

# File input (one item per line)
python -m amorsize tune mymodule.process --data-file input.txt

# Stdin
cat data.txt | python -m amorsize tune mymodule.func --data-stdin
```

### Search Space Customization

```bash
# Custom n_jobs range
python -m amorsize tune mymodule.func --data-range 1000 \
    --n-jobs-range 1 2 4 8 16

# Custom chunksize range
python -m amorsize tune mymodule.func --data-range 1000 \
    --chunksize-range 10 50 100 200

# Both
python -m amorsize tune mymodule.func --data-range 1000 \
    --n-jobs-range 2 4 8 \
    --chunksize-range 50 100 150
```

### Options

```bash
# Quick mode (faster)
--quick

# Disable optimizer hint
--no-optimizer-hint

# Use threads instead of processes
--threads

# Timeout per configuration
--timeout-per-config 60.0

# Verbose output
--verbose

# JSON output
--json

# Save to history
--save-result "my_experiment_v1"
```

### Examples

#### Example 1: Basic Tuning

```bash
python -m amorsize tune math.factorial --data-range 500 --quick --verbose
```

Output:
```
Optimizer hint: n_jobs=4, chunksize=50

=== Auto-Tuning Configuration ===
Function: factorial
Data items: 500
Executor: process
Testing n_jobs: [1, 2, 4]
Testing chunksizes: [1, 25, 50]
Total configurations: 10

Starting benchmark...

Benchmarking serial execution...
  Serial time: 0.1234s

[1/9] Testing n_jobs=1, chunksize=1... 0.1456s (0.85x)
[2/9] Testing n_jobs=1, chunksize=25... 0.1389s (0.89x)
[3/9] Testing n_jobs=1, chunksize=50... 0.1401s (0.88x)
[4/9] Testing n_jobs=2, chunksize=1... 0.0891s (1.39x) ⭐ NEW BEST
[5/9] Testing n_jobs=2, chunksize=25... 0.0723s (1.71x) ⭐ NEW BEST
[6/9] Testing n_jobs=2, chunksize=50... 0.0745s (1.66x)
[7/9] Testing n_jobs=4, chunksize=1... 0.0567s (2.18x) ⭐ NEW BEST
[8/9] Testing n_jobs=4, chunksize=25... 0.0412s (3.00x) ⭐ NEW BEST
[9/9] Testing n_jobs=4, chunksize=50... 0.0434s (2.84x)

=== Tuning Complete ===
Best configuration: n_jobs=4, chunksize=25
Best time: 0.0412s (3.00x speedup)
```

#### Example 2: Comprehensive Search

```bash
python -m amorsize tune mymodule.expensive_func --data-range 10000 \
    --n-jobs-range 1 2 4 8 16 \
    --chunksize-range 10 50 100 200 500 \
    --verbose
```

#### Example 3: JSON Output for Scripting

```bash
python -m amorsize tune math.factorial --data-range 500 --json | jq '.best_speedup'
```

Output:
```json
{
  "best_n_jobs": 4,
  "best_chunksize": 25,
  "best_time": 0.0412,
  "best_speedup": 3.00,
  "serial_time": 0.1234,
  "configurations_tested": 10,
  "search_strategy": "grid",
  "executor_type": "process",
  "top_configurations": [
    [4, 25, 0.0412, 3.00],
    [4, 50, 0.0434, 2.84],
    [4, 1, 0.0567, 2.18]
  ],
  "optimizer_hint": {
    "n_jobs": 4,
    "chunksize": 50,
    "estimated_speedup": 2.8
  }
}
```

## Comparison: Optimizer vs Auto-Tuning

### Use `optimize()` when:
- ✅ You need fast recommendations (< 1 second)
- ✅ Your workload is relatively straightforward
- ✅ You want to avoid the overhead of benchmarking
- ✅ You're exploring different functions quickly

### Use `tune_parameters()` when:
- ✅ You need the absolute best performance
- ✅ You have time for empirical benchmarking
- ✅ Your workload has complex characteristics
- ✅ System-specific factors matter
- ✅ You want to validate optimizer accuracy

### Use `quick_tune()` when:
- ✅ You want better accuracy than `optimize()` but faster than full tuning
- ✅ You're iterating on function improvements
- ✅ You want a good-enough configuration quickly

## Best Practices

### 1. Start with Quick Tune

```python
# Fast initial assessment
result = quick_tune(func, data, verbose=True)

# If speedup is good enough, use it
if result.best_speedup > 2.0:
    optimal_config = (result.best_n_jobs, result.best_chunksize)
else:
    # Otherwise, do full tuning
    result = tune_parameters(func, data, verbose=True)
```

### 2. Use Representative Data

```python
# Bad: Tiny sample won't show real behavior
small_data = range(10)
result = tune_parameters(func, small_data)  # Not representative!

# Good: Use realistic data size
real_data = range(10000)
result = tune_parameters(func, real_data)
```

### 3. Customize Search Space for Large Datasets

```python
# For very large datasets, limit the search space
large_data = range(1000000)

# Test fewer configurations
result = tune_parameters(
    func, large_data,
    n_jobs_range=[1, 4, 8],      # Only 3 values
    chunksize_range=[100, 500],   # Only 2 values
    verbose=True
)
```

### 4. Compare with Optimizer

```python
from amorsize import optimize, tune_parameters

# Get both recommendations
opt_result = optimize(func, data)
tune_result = tune_parameters(func, data, verbose=True)

print(f"Optimizer: {opt_result.n_jobs}x{opt_result.chunksize} = {opt_result.estimated_speedup:.2f}x")
print(f"Tuning:    {tune_result.best_n_jobs}x{tune_result.best_chunksize} = {tune_result.best_speedup:.2f}x")

# Check if they match
if (opt_result.n_jobs == tune_result.best_n_jobs and 
    opt_result.chunksize == tune_result.best_chunksize):
    print("✅ Optimizer recommendation confirmed by tuning!")
```

### 5. Save Results to History

```python
from amorsize import tune_parameters
from amorsize.history import save_result

result = tune_parameters(func, data, verbose=True)

# Convert to comparison result format for history
from amorsize.comparison import ComparisonResult, ComparisonConfig

best_config = ComparisonConfig(
    name=f"Tuned {result.best_n_jobs}x{result.best_chunksize}",
    n_jobs=result.best_n_jobs,
    chunksize=result.best_chunksize
)

comparison = ComparisonResult(
    best_config=best_config,
    best_time=result.best_time,
    serial_time=result.serial_time,
    best_speedup=result.best_speedup,
    configs=[best_config],
    execution_times=[result.best_time],
    speedups=[result.best_speedup],
    timing_details={}
)

entry_id = save_result(comparison, "my_tuning_experiment")
print(f"Saved as: {entry_id}")
```

## Performance Tips

### 1. Use Timeout for Safety

```python
# Prevent slow configs from taking too long
result = tune_parameters(
    func, data,
    timeout_per_config=60.0,  # Max 60s per config
    verbose=True
)
```

### 2. Use Threads for I/O-Bound

```python
def io_bound_func(url):
    """Fetch data from URL."""
    response = requests.get(url)
    return response.text

# Use threads for I/O-bound workload
result = tune_parameters(
    io_bound_func,
    urls,
    prefer_threads_for_io=True,
    verbose=True
)
```

### 3. Disable Optimizer Hint for Pure Empiricism

```python
# If you don't trust the optimizer, disable its hint
result = tune_parameters(
    func, data,
    use_optimizer_hint=False,
    n_jobs_range=[1, 2, 4, 8],
    chunksize_range=[10, 50, 100],
    verbose=True
)
```

## Troubleshooting

### Q: Tuning takes too long

**Solution 1:** Use `quick_tune()` instead
```python
result = quick_tune(func, data, verbose=True)
```

**Solution 2:** Reduce search space
```python
result = tune_parameters(
    func, data,
    n_jobs_range=[1, 4],      # Fewer values
    chunksize_range=[50],      # Single value
    verbose=True
)
```

**Solution 3:** Add timeout
```python
result = tune_parameters(
    func, data,
    timeout_per_config=30.0,
    verbose=True
)
```

### Q: Serial is always fastest

This is normal for:
- Very fast functions (< 1ms per item)
- Small datasets (< 100 items)
- Functions with high IPC overhead

The tuning correctly identifies that parallelization won't help.

### Q: Results vary between runs

This is expected due to system noise. Run multiple times and average:

```python
results = []
for i in range(3):
    result = tune_parameters(func, data)
    results.append((result.best_n_jobs, result.best_chunksize, result.best_speedup))

# Analyze consistency
print(f"Run 1: {results[0]}")
print(f"Run 2: {results[1]}")
print(f"Run 3: {results[2]}")
```

## See Also

- [Optimizer Guide](README.md) - Fast analytical recommendations
- [Benchmark Validation](README_benchmark_validation.md) - Validate optimizer predictions
- [Comparison Mode](README_comparison_mode.md) - Compare multiple strategies
- [History Tracking](README_history.md) - Save and compare results over time
