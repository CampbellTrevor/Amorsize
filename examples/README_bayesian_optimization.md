# Bayesian Optimization for Parameter Tuning

Amorsize includes **Bayesian optimization** for intelligent parameter search. This uses Gaussian Process-based optimization to find near-optimal `n_jobs` and `chunksize` with fewer benchmark trials than grid search.

## Why Bayesian Optimization?

**Grid search** tests all possible combinations:
- For 10 n_jobs values × 10 chunksize values = **100 benchmarks**
- Exhaustive but expensive

**Bayesian optimization** intelligently explores the space:
- Uses past results to predict promising configurations
- Typically finds near-optimal parameters in **15-30 trials**
- Much faster for expensive benchmarks

## Installation

Bayesian optimization requires `scikit-optimize`:

```bash
# Install scikit-optimize separately
pip install scikit-optimize

# Or install with amorsize
pip install amorsize[bayesian]
```

## Basic Usage

```python
from amorsize import bayesian_tune_parameters

def expensive_function(x):
    """Your CPU-intensive function."""
    result = 0
    for i in range(x * 100):
        result += i ** 2
    return result

data = range(100, 500)

# Find optimal parameters with 20 intelligent trials
result = bayesian_tune_parameters(
    expensive_function,
    data,
    n_iterations=20,
    verbose=True
)

print(f"Best: n_jobs={result.best_n_jobs}, chunksize={result.best_chunksize}")
print(f"Speedup: {result.best_speedup:.2f}x")
print(f"Tested only {result.configurations_tested} configurations")
```

## Key Features

### 1. Intelligent Search

Bayesian optimization uses Gaussian Processes to model the objective function and an acquisition function to decide which configuration to try next:

```python
result = bayesian_tune_parameters(
    expensive_function,
    data,
    n_iterations=25,  # Try 25 configurations intelligently
    verbose=True
)
```

### 2. Custom Search Bounds

Specify bounds for the search space:

```python
result = bayesian_tune_parameters(
    expensive_function,
    data,
    n_jobs_min=2,
    n_jobs_max=8,
    chunksize_min=5,
    chunksize_max=100,
    n_iterations=20
)
```

### 3. Start Near Optimizer Hint

Use the optimizer's quick prediction as a starting point:

```python
result = bayesian_tune_parameters(
    expensive_function,
    data,
    use_optimizer_hint=True,  # Start near optimizer recommendation
    n_iterations=20
)

print(f"Optimizer suggested: {result.optimization_hint.n_jobs}")
print(f"Bayesian found: {result.best_n_jobs}")
```

### 4. Reproducible Results

Use `random_state` for reproducibility:

```python
result = bayesian_tune_parameters(
    expensive_function,
    data,
    n_iterations=20,
    random_state=42  # Same seed = same results
)
```

### 5. Threading Support

Works with ThreadPoolExecutor for I/O-bound workloads:

```python
result = bayesian_tune_parameters(
    io_bound_function,
    data,
    prefer_threads_for_io=True,
    n_iterations=20
)
```

## Complete Example

```python
from amorsize import bayesian_tune_parameters

def compute_heavy(x):
    """Expensive computation."""
    return sum(i ** 2 + i ** 0.5 for i in range(x * 100))

# Large dataset - benchmarking is expensive
data = range(100, 1000)

# Bayesian optimization: find near-optimal with 30 trials
result = bayesian_tune_parameters(
    compute_heavy,
    data,
    n_iterations=30,
    verbose=True
)

print(result)
# Output:
# === Auto-Tuning Results ===
#
# Search Strategy: bayesian
# Executor Type: process
# Configurations Tested: 31
#
# Performance:
#   Serial execution time:   15.234s
#   Best parallel time:      4.123s
#   Best speedup:            3.69x
#
# Optimal Configuration:
#   n_jobs:     4
#   chunksize:  42

# Save for future use
result.save_config('optimal_params.json', function_name='compute_heavy')
```

## When to Use

**Use Bayesian Optimization when:**
- ✅ Benchmarking is expensive (slow function or large dataset)
- ✅ Search space is large (many possible configurations)
- ✅ You need near-optimal results efficiently
- ✅ Time/resources are limited

**Use Grid Search when:**
- ✅ Search space is small (few configurations)
- ✅ Benchmarking is fast
- ✅ You want exhaustive testing
- ✅ You need to see all results

## Comparison: Bayesian vs Grid

```python
import time

# Bayesian: 20 intelligent trials
start = time.time()
bayesian_result = bayesian_tune_parameters(func, data, n_iterations=20)
bayesian_time = time.time() - start

# Grid: All combinations (100 trials)
start = time.time()
grid_result = tune_parameters(
    func, data,
    n_jobs_range=list(range(1, 11)),      # 10 values
    chunksize_range=list(range(1, 101, 10))  # 10 values
)
grid_time = time.time() - start

print(f"Bayesian: {bayesian_result.best_speedup:.2f}x in {bayesian_time:.1f}s")
print(f"Grid:     {grid_result.best_speedup:.2f}x in {grid_time:.1f}s")
# Bayesian: 3.45x in 25.3s (20 trials)
# Grid:     3.52x in 126.7s (100 trials)
# → Bayesian found similar result 5× faster
```

## Advanced Options

### Number of Iterations

More iterations = better results but longer runtime:

```python
# Quick search (15-20 iterations)
result = bayesian_tune_parameters(func, data, n_iterations=15)

# Thorough search (30-50 iterations)
result = bayesian_tune_parameters(func, data, n_iterations=40)
```

### Timeouts

Prevent slow configurations from hanging:

```python
result = bayesian_tune_parameters(
    func, data,
    n_iterations=20,
    timeout_per_config=30.0  # Max 30s per configuration
)
```

### Without Optimizer Hint

Skip the initial optimizer analysis (faster startup):

```python
result = bayesian_tune_parameters(
    func, data,
    use_optimizer_hint=False,  # Pure Bayesian, no optimizer hint
    n_iterations=25
)
```

## How It Works

Bayesian optimization uses a **Gaussian Process** to model the relationship between parameters and execution time:

1. **Initialization**: Try a few random configurations
2. **Modeling**: Build a probabilistic model of the objective function
3. **Acquisition**: Use Expected Improvement to pick the most promising configuration
4. **Update**: Benchmark the chosen configuration and update the model
5. **Repeat**: Continue until budget (n_iterations) is exhausted

This approach **balances exploration** (trying new areas) and **exploitation** (refining known good areas).

## Graceful Fallback

If `scikit-optimize` is not installed, Bayesian optimization automatically falls back to grid search:

```python
result = bayesian_tune_parameters(func, data, n_iterations=20)
# Warning: scikit-optimize not available. Falling back to grid search.
# Returns: TuningResult with search_strategy="grid"
```

## See Also

- [Basic Tuning Guide](README_tuning.md) - Grid search and quick_tune
- [Full Example](../examples/bayesian_optimization_demo.py) - Complete demonstration
- [Comparison Mode](README_comparison_mode.md) - Compare multiple strategies
- [Configuration Management](README_config.md) - Save and reuse optimal parameters

## API Reference

```python
def bayesian_tune_parameters(
    func: Callable,
    data: Union[List, range, Iterator],
    n_iterations: int = 20,
    n_jobs_min: int = 1,
    n_jobs_max: Optional[int] = None,
    chunksize_min: int = 1,
    chunksize_max: Optional[int] = None,
    use_optimizer_hint: bool = True,
    verbose: bool = False,
    timeout_per_config: Optional[float] = None,
    prefer_threads_for_io: bool = False,
    random_state: Optional[int] = None
) -> TuningResult
```

**Parameters:**
- `func`: Function to optimize
- `data`: Input data
- `n_iterations`: Number of configurations to test (default: 20)
- `n_jobs_min/max`: Bounds for n_jobs search (default: 1 to physical_cores)
- `chunksize_min/max`: Bounds for chunksize search (default: 1 to data_size//2)
- `use_optimizer_hint`: Start near optimizer recommendation (default: True)
- `verbose`: Print progress (default: False)
- `timeout_per_config`: Max seconds per benchmark (default: None)
- `prefer_threads_for_io`: Use ThreadPoolExecutor (default: False)
- `random_state`: Random seed for reproducibility (default: None)

**Returns:**
- `TuningResult` with optimal parameters and benchmark data
