# Comparison Mode Guide

## Overview

The comparison mode feature allows you to **empirically compare multiple parallelization strategies** side-by-side to choose the best configuration for your specific workload. Instead of relying solely on the optimizer's predictions, you can run actual benchmarks and see real performance differences.

## Why Use Comparison Mode?

### The Problem

Choosing optimal parallelization parameters involves trade-offs:
- **Worker count**: More workers = more parallelism, but also more overhead
- **Chunk size**: Larger chunks = less overhead, smaller chunks = better load balancing
- **Executor type**: Threading vs multiprocessing depends on workload characteristics

The optimizer makes predictions based on models, but **comparison mode provides empirical validation**.

### The Solution

Comparison mode:
- ✅ **Benchmarks** multiple configurations with your actual function and data
- ✅ **Measures** real execution times (not estimates)
- ✅ **Compares** strategies side-by-side with speedup calculations
- ✅ **Recommends** insights based on actual performance
- ✅ **Validates** optimizer predictions against reality

## Quick Start

### Basic Comparison

```python
from amorsize import compare_strategies, ComparisonConfig

def expensive_func(x):
    return sum(i**2 for i in range(x))

data = range(100, 1000)

# Define strategies to compare
configs = [
    ComparisonConfig("Serial", n_jobs=1),
    ComparisonConfig("2 Workers", n_jobs=2, chunksize=50),
    ComparisonConfig("4 Workers", n_jobs=4, chunksize=25),
    ComparisonConfig("8 Workers", n_jobs=8, chunksize=13)
]

# Compare all strategies
result = compare_strategies(expensive_func, data, configs, verbose=True)

# View results
print(result)
```

Output:
```
Comparing 4 strategies on 900 items

[1/4] Testing: Serial: Serial execution
    Execution time: 2.4531s
[2/4] Testing: 2 Workers: 2 processs, chunksize=50
    Execution time: 1.3245s
[3/4] Testing: 4 Workers: 4 processs, chunksize=25
    Execution time: 0.8123s
[4/4] Testing: 8 Workers: 8 processs, chunksize=13
    Execution time: 0.7891s

=== Strategy Comparison Results ===

Strategy                       Time (s)     Speedup    Status         
----------------------------------------------------------------------
Serial                         2.4531       1.00x      ~ Similar      
2 Workers                      1.3245       1.85x      ✓ Faster       
4 Workers                      0.8123       3.02x      ✓ Faster       
8 Workers                      0.7891       3.11x      ⭐ FASTEST      

Best Strategy: 8 Workers
Best Time: 0.7891s
Best Speedup: 3.11x

Recommendations:
  • Best strategy uses 8 workers with chunksize 13
  • Excellent parallel efficiency (38.8%) - near-linear scaling
```

### Compare with Optimizer

```python
from amorsize import compare_with_optimizer, ComparisonConfig

# Compare optimizer against manual configurations
additional = [
    ComparisonConfig("Conservative", n_jobs=2, chunksize=450),
    ComparisonConfig("Aggressive", n_jobs=8, chunksize=113)
]

result, optimization = compare_with_optimizer(
    expensive_func,
    data,
    additional_configs=additional,
    verbose=True
)

print(result)
print(f"\nOptimizer recommended: n_jobs={optimization.n_jobs}")
print(f"Optimizer ranked: #{result.best_config_index + 1} out of {len(result.configs)}")
```

## API Reference

### `compare_strategies()`

Compare multiple parallelization strategies by benchmarking each.

```python
def compare_strategies(
    func: Callable,
    data: Union[List, Iterator],
    configs: List[ComparisonConfig],
    max_items: Optional[int] = None,
    timeout: float = 120.0,
    verbose: bool = False
) -> ComparisonResult
```

**Parameters:**
- `func`: Function to benchmark (must accept single argument)
- `data`: Input data (list, generator, or iterator)
- `configs`: List of `ComparisonConfig` objects to compare
- `max_items`: Maximum items to benchmark (limits runtime for large datasets)
- `timeout`: Maximum time for each benchmark in seconds (default: 120s)
- `verbose`: Print progress information (default: False)

**Returns:**
- `ComparisonResult` with execution times and speedups for each config

**Raises:**
- `ValueError`: If parameters are invalid
- `TimeoutError`: If any benchmark exceeds timeout

**Example:**
```python
configs = [
    ComparisonConfig("Serial", n_jobs=1),
    ComparisonConfig("Parallel", n_jobs=4, chunksize=25)
]

result = compare_strategies(func, data, configs, max_items=500, verbose=True)
```

### `compare_with_optimizer()`

Compare optimizer recommendation against alternative strategies.

```python
def compare_with_optimizer(
    func: Callable,
    data: Union[List, Iterator],
    additional_configs: Optional[List[ComparisonConfig]] = None,
    max_items: Optional[int] = None,
    timeout: float = 120.0,
    verbose: bool = False
) -> Tuple[ComparisonResult, OptimizationResult]
```

**Parameters:**
- `func`: Function to benchmark
- `data`: Input data
- `additional_configs`: Additional configurations to compare (optional)
- `max_items`: Maximum items to benchmark
- `timeout`: Maximum time per benchmark
- `verbose`: Print progress information

**Returns:**
- Tuple of `(ComparisonResult, OptimizationResult)`

**Example:**
```python
# Automatically includes Serial + Optimizer + additional configs
result, opt = compare_with_optimizer(
    func, data,
    additional_configs=[
        ComparisonConfig("Alt 1", n_jobs=2, chunksize=50),
        ComparisonConfig("Alt 2", n_jobs=4, chunksize=25)
    ],
    verbose=True
)

print(f"Optimizer: {opt.n_jobs} workers, chunksize {opt.chunksize}")
print(f"Best: {result.best_config.name}")
```

### `ComparisonConfig`

Configuration for a single strategy to compare.

```python
class ComparisonConfig:
    def __init__(
        self,
        name: str,
        n_jobs: int = 1,
        chunksize: int = 1,
        executor_type: str = "process"
    )
```

**Parameters:**
- `name`: Human-readable name for this configuration
- `n_jobs`: Number of workers (1 for serial, >= 1)
- `chunksize`: Chunk size for batching (>= 1)
- `executor_type`: "process", "thread", or "serial"

**Validation:**
- `n_jobs` must be >= 1
- `chunksize` must be >= 1
- `executor_type` must be "process", "thread", or "serial"

**Example:**
```python
# Serial execution
serial = ComparisonConfig("Serial", n_jobs=1)

# Multiprocessing
multi = ComparisonConfig("4 Workers", n_jobs=4, chunksize=25, executor_type="process")

# Threading
thread = ComparisonConfig("4 Threads", n_jobs=4, executor_type="thread")
```

### `ComparisonResult`

Result of comparing multiple parallelization strategies.

**Attributes:**
- `configs`: List of configurations that were compared
- `execution_times`: Execution times for each config (seconds)
- `speedups`: Speedup relative to first config (serial baseline)
- `best_config_index`: Index of fastest configuration
- `best_config`: Fastest configuration
- `best_time`: Execution time of best configuration
- `recommendations`: List of insights from comparison

**Methods:**
- `get_sorted_configs()`: Get configurations sorted by time (fastest first)
- `__str__()`: Human-readable formatted output
- `__repr__()`: Compact representation

**Example:**
```python
result = compare_strategies(func, data, configs)

# Access results
print(f"Best: {result.best_config.name}")
print(f"Time: {result.best_time:.4f}s")
print(f"Speedup: {result.speedups[result.best_config_index]:.2f}x")

# Get sorted list
for config, time, speedup in result.get_sorted_configs():
    print(f"{config.name}: {time:.4f}s ({speedup:.2f}x)")

# View recommendations
for rec in result.recommendations:
    print(f"• {rec}")
```

## Use Cases

### 1. Finding Optimal Worker Count

```python
# Compare different worker counts with same chunksize
configs = [
    ComparisonConfig("Serial", n_jobs=1),
    ComparisonConfig("2 Workers", n_jobs=2, chunksize=100),
    ComparisonConfig("4 Workers", n_jobs=4, chunksize=100),
    ComparisonConfig("8 Workers", n_jobs=8, chunksize=100),
    ComparisonConfig("16 Workers", n_jobs=16, chunksize=100)
]

result = compare_strategies(func, data, configs)
```

**Insight**: See where adding more workers stops helping (overhead dominates).

### 2. Tuning Chunk Size

```python
# Compare different chunksizes with same worker count
configs = [
    ComparisonConfig("Large (100)", n_jobs=4, chunksize=100),
    ComparisonConfig("Medium (50)", n_jobs=4, chunksize=50),
    ComparisonConfig("Small (25)", n_jobs=4, chunksize=25),
    ComparisonConfig("Tiny (10)", n_jobs=4, chunksize=10)
]

result = compare_strategies(func, data, configs)
```

**Insight**: Find the sweet spot between overhead (large chunks) and load balancing (small chunks).

### 3. Threading vs Multiprocessing

```python
# Compare executor types
configs = [
    ComparisonConfig("Serial", n_jobs=1),
    ComparisonConfig("Process (2)", n_jobs=2, chunksize=50, executor_type="process"),
    ComparisonConfig("Process (4)", n_jobs=4, chunksize=25, executor_type="process"),
    ComparisonConfig("Thread (2)", n_jobs=2, executor_type="thread"),
    ComparisonConfig("Thread (4)", n_jobs=4, executor_type="thread")
]

result = compare_strategies(io_bound_func, data, configs)
```

**Insight**: For I/O-bound workloads, threading often wins (lower overhead). For CPU-bound, multiprocessing wins (true parallelism).

### 4. Validating Optimizer Predictions

```python
# Get optimizer recommendation
opt = optimize(func, data)

# Validate with empirical benchmark
result, opt = compare_with_optimizer(func, data)

actual_speedup = result.speedups[1]  # Optimizer is second config
predicted_speedup = opt.estimated_speedup

error = abs(actual_speedup - predicted_speedup) / predicted_speedup * 100
print(f"Prediction error: {error:.1f}%")
```

**Insight**: Verify that optimizer predictions match reality for your system.

### 5. Quick Exploration (Large Datasets)

```python
# Limit benchmarking to first 1000 items for speed
result = compare_strategies(
    func,
    large_data,  # 100,000 items
    configs,
    max_items=1000,  # Only benchmark 1000
    verbose=True
)
```

**Insight**: Get quick indicative results without waiting for full benchmark.

## Performance Tips

### Minimizing Benchmark Time

1. **Use `max_items`** for large datasets:
   ```python
   # Instead of benchmarking all 100k items
   result = compare_strategies(func, data, configs, max_items=1000)
   ```

2. **Limit configurations**:
   ```python
   # Focus on most relevant strategies
   configs = [
       ComparisonConfig("Serial", n_jobs=1),
       ComparisonConfig("Optimal", n_jobs=4, chunksize=25)
   ]
   ```

3. **Set timeout**:
   ```python
   # Abort if any benchmark takes > 30s
   result = compare_strategies(func, data, configs, timeout=30)
   ```

### Ensuring Fair Comparison

1. **Run on quiet system**: Close other applications to minimize noise
2. **Use consistent data**: Same input for all configurations
3. **Warm up**: Run once before benchmarking to warm caches
4. **Multiple runs**: Run comparison multiple times and average results

### Interpreting Results

**Speedup < 1.0**: Parallel is slower than serial
- Overhead exceeds benefit
- Function too fast or data too small
- Consider increasing workload or using serial execution

**Speedup 1.0-1.5x**: Marginal improvement
- Overhead nearly equals benefit
- Parallelization questionable
- Consider if complexity is worth minor gain

**Speedup > 2.0x**: Good parallelization
- Benefit clearly outweighs overhead
- Worth the added complexity
- Monitor for scaling with data size

**Efficiency < 50%**: High overhead
- `efficiency = speedup / n_jobs`
- Significant time lost to overhead
- Consider reducing workers or optimizing function

**Efficiency > 85%**: Excellent scaling
- Near-linear speedup
- Overhead is minimal
- Well-suited for parallelization

## Best Practices

### 1. Start with Serial Baseline

Always include serial execution as the first config:
```python
configs = [
    ComparisonConfig("Serial", n_jobs=1),  # Baseline
    # ... other strategies
]
```

This provides a baseline for speedup calculation.

### 2. Test Edge Cases

Include extreme configurations to understand limits:
```python
configs = [
    ComparisonConfig("Serial", n_jobs=1),
    ComparisonConfig("Conservative (2)", n_jobs=2, chunksize=100),
    ComparisonConfig("Aggressive (16)", n_jobs=16, chunksize=10)
]
```

### 3. Use Descriptive Names

Make configs easily identifiable:
```python
# Good
ComparisonConfig("4 Workers, Large Chunks (50)", n_jobs=4, chunksize=50)

# Bad
ComparisonConfig("Config1", n_jobs=4, chunksize=50)
```

### 4. Document Recommendations

Save comparison results for future reference:
```python
result = compare_strategies(func, data, configs)

# Save to file
with open("comparison_results.txt", "w") as f:
    f.write(str(result))
    f.write("\n\nRecommendations:\n")
    for rec in result.recommendations:
        f.write(f"• {rec}\n")
```

### 5. Validate on Target System

Run comparisons on the same system where code will run:
```python
# Development machine
dev_result = compare_strategies(func, data, configs)

# Production machine
prod_result = compare_strategies(func, data, configs)

# Compare results
print(f"Dev best: {dev_result.best_config.name}")
print(f"Prod best: {prod_result.best_config.name}")
```

## Troubleshooting

### "Execution failed: Can't pickle"

**Problem**: Function or data contains unpicklable objects (lambdas, local functions, file handles).

**Solution**:
1. Define functions at module level (not inside other functions)
2. Use `executor_type="thread"` instead of `"process"`
3. Ensure data doesn't contain unpicklable objects

```python
# Bad - local function can't be pickled
def example():
    def func(x):
        return x ** 2
    compare_strategies(func, data, configs)  # Fails!

# Good - module-level function
def func(x):
    return x ** 2

def example():
    compare_strategies(func, data, configs)  # Works!
```

### "TimeoutError: exceeded timeout"

**Problem**: Benchmark taking too long.

**Solutions**:
1. Use `max_items` to limit data size
2. Increase `timeout` parameter
3. Reduce number of configurations
4. Check if function has infinite loop

```python
# Limit to 100 items and 60s timeout
result = compare_strategies(
    func, data, configs,
    max_items=100,
    timeout=60
)
```

### Inconsistent Results

**Problem**: Results vary between runs.

**Causes**:
- System load (other processes)
- CPU throttling
- Cache effects
- Random behavior in function

**Solutions**:
1. Run multiple times and average
2. Close other applications
3. Use larger datasets (reduces noise)
4. Check function for non-determinism

## Examples

See `examples/comparison_mode_demo.py` for 7 comprehensive examples:

1. **Basic Comparison**: Compare different worker counts
2. **Chunksize Tuning**: Find optimal chunksize
3. **Optimizer Validation**: Compare optimizer vs manual configs
4. **Threading vs Multiprocessing**: Choose best executor type
5. **Limited Dataset**: Quick exploration
6. **Recommendation Analysis**: Understand insights
7. **Integration**: Validate optimizer predictions

Run the demo:
```bash
python examples/comparison_mode_demo.py
```

## Summary

Comparison mode provides **empirical validation** of parallelization strategies:

- ✅ **Benchmark** multiple configurations side-by-side
- ✅ **Measure** actual execution times (not estimates)
- ✅ **Compare** performance with speedup calculations
- ✅ **Validate** optimizer predictions
- ✅ **Choose** best strategy for your workload

Use it to:
- Find optimal worker count and chunksize
- Compare threading vs multiprocessing
- Validate optimizer recommendations
- Understand parallelization trade-offs
- Make informed decisions about parallelization

**Next**: Use the best configuration from comparison mode in your production code!
