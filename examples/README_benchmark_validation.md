# Benchmark Validation Guide

## Overview

The benchmark validation feature allows you to **empirically verify** that Amorsize's optimizer recommendations are accurate for your specific system and workload. Instead of just trusting predictions, you can run actual benchmarks and see how well the predictions match reality.

## Why Use Benchmark Validation?

### The Problem

Amorsize makes predictions about parallel performance based on:
- Function execution time (measured via sampling)
- System characteristics (cores, spawn costs, memory)
- Mathematical models (Amdahl's Law with overhead)

But predictions can be affected by:
- System-specific factors (CPU throttling, background processes)
- Cache effects and memory patterns
- Workload characteristics not captured in sampling
- OS scheduler behavior

### The Solution

Benchmark validation runs **actual serial and parallel execution** on your data and compares:
- **Predicted speedup** (what the optimizer estimated)
- **Actual speedup** (what really happened)
- **Accuracy** (how close the prediction was)

This gives you:
- ✅ **Confidence** in production deployments
- ✅ **Validation** of system-specific behavior
- ✅ **Insights** into prediction accuracy
- ✅ **Recommendations** for improving results

## Quick Start

### Basic Validation

```python
from amorsize import optimize, validate_optimization

def expensive_function(x):
    """Your computation."""
    return sum(i**2 for i in range(x))

data = range(100, 500)

# Step 1: Get optimizer recommendations
opt = optimize(expensive_function, data)

# Step 2: Validate with actual benchmarks
result = validate_optimization(expensive_function, data, optimization=opt)

# Step 3: Check results
print(result)
# Output:
# === Benchmark Validation Results ===
# 
# Optimizer Recommendation: n_jobs=2, chunksize=50
# 
# Performance Measurements:
#   Serial execution time:   2.4531s
#   Parallel execution time: 1.3245s
#   Actual speedup:          1.85x
#   Predicted speedup:       1.78x
# 
# Prediction Accuracy:
#   Accuracy:                96.2%
#   Error:                   +3.9%
# 
# ✅ Excellent prediction accuracy!
```

### Quick Validation (Fast)

For large datasets, use `quick_validate()` to sample a subset:

```python
from amorsize import quick_validate

# Large dataset - 10,000 items
data = range(100, 10100)

# Validate using only 100 sampled items (much faster)
result = quick_validate(expensive_function, data, sample_size=100)

print(f"Quick check: {result.accuracy_percent:.1f}% accurate")
# Output: Quick check: 94.3% accurate
```

## API Reference

### `validate_optimization()`

Comprehensive validation with full benchmarking.

```python
def validate_optimization(
    func: Callable,
    data: Union[List, Iterator],
    optimization: Optional[OptimizationResult] = None,
    max_items: Optional[int] = None,
    timeout: float = 60.0,
    verbose: bool = False
) -> BenchmarkResult
```

**Parameters:**
- `func`: Function to benchmark (must accept single argument)
- `data`: Input data (list, generator, or iterator)
- `optimization`: Pre-computed `OptimizationResult` (if `None`, computes automatically)
- `max_items`: Limit benchmark to first N items (for large datasets)
- `timeout`: Maximum time for each benchmark in seconds (default: 60s)
- `verbose`: Print detailed progress information (default: False)

**Returns:**
- `BenchmarkResult` with actual vs predicted performance comparison

**Example:**
```python
# With pre-computed optimization
opt = optimize(func, data)
result = validate_optimization(func, data, optimization=opt, verbose=True)

# Without pre-computed optimization (computes automatically)
result = validate_optimization(func, data, max_items=500, verbose=True)
```

### `quick_validate()`

Fast validation using data sampling.

```python
def quick_validate(
    func: Callable,
    data: Union[List, Iterator],
    sample_size: int = 100,
    verbose: bool = False
) -> BenchmarkResult
```

**Parameters:**
- `func`: Function to benchmark
- `data`: Input data
- `sample_size`: Number of items to sample (default: 100)
- `verbose`: Print progress information (default: False)

**Returns:**
- `BenchmarkResult` based on sampled data

**Example:**
```python
# Quick confidence check
result = quick_validate(func, large_dataset, sample_size=50)

if result.is_accurate(threshold=75):
    print("✓ Recommendations appear reliable")
```

### `BenchmarkResult`

Result container with performance comparison.

**Attributes:**
- `optimization`: Original `OptimizationResult` being validated
- `serial_time`: Measured serial execution time (seconds)
- `parallel_time`: Measured parallel execution time (seconds)
- `actual_speedup`: Measured speedup factor
- `predicted_speedup`: Optimizer's predicted speedup
- `accuracy_percent`: Prediction accuracy (0-100%)
- `error_percent`: Prediction error percentage (can be negative)
- `recommendations`: List of actionable insights

**Methods:**
- `is_accurate(threshold=75.0)`: Check if accuracy meets threshold
- `__str__()`: Human-readable report
- `__repr__()`: Compact representation

**Example:**
```python
result = validate_optimization(func, data)

# Check accuracy
if result.is_accurate(threshold=80):
    print("✓ High accuracy")

# Access measurements
print(f"Serial: {result.serial_time:.3f}s")
print(f"Parallel: {result.parallel_time:.3f}s")
print(f"Speedup: {result.actual_speedup:.2f}x")

# View recommendations
for rec in result.recommendations:
    print(f"  • {rec}")
```

## Usage Patterns

### Pattern 1: Pre-Deployment Validation

Validate recommendations before deploying to production:

```python
# 1. Optimize workload
opt = optimize(critical_function, production_data)

# 2. Validate on representative sample
result = validate_optimization(
    critical_function,
    production_data,
    optimization=opt,
    max_items=1000  # Limit runtime
)

# 3. Make deployment decision
if result.is_accurate(threshold=75):
    print(f"✓ Deploy with n_jobs={opt.n_jobs}, chunksize={opt.chunksize}")
else:
    print("⚠️ Investigate system-specific factors")
    for rec in result.recommendations:
        print(f"  • {rec}")
```

### Pattern 2: System Profiling

Profile your specific system to understand its characteristics:

```python
# Test with different workload types
workloads = [
    ("Fast", lambda x: x**2),
    ("Medium", lambda x: sum(i**2 for i in range(x))),
    ("Slow", lambda x: sum(i**3 for i in range(x*10)))
]

for name, func in workloads:
    result = quick_validate(func, range(50, 150), sample_size=50)
    print(f"{name:8s}: accuracy={result.accuracy_percent:.1f}%")

# Output:
# Fast    : accuracy=85.2%
# Medium  : accuracy=92.7%
# Slow    : accuracy=95.3%
```

### Pattern 3: Iterative Optimization

Use validation feedback to refine your approach:

```python
# Initial optimization
opt1 = optimize(func, data)
result1 = validate_optimization(func, data, optimization=opt1, max_items=200)

if result1.actual_speedup < result1.predicted_speedup * 0.7:
    # Actual performance significantly below prediction
    print("System factors detected. Trying more conservative settings...")
    
    # Try with fewer workers
    opt2 = optimize(func, data, verbose=True)
    result2 = validate_optimization(func, data, optimization=opt2, max_items=200)
    
    # Compare
    if result2.accuracy_percent > result1.accuracy_percent:
        print("✓ More conservative settings improved accuracy")
```

### Pattern 4: Development Iteration

Quick checks during development:

```python
def development_check(func, data):
    """Quick validation during development."""
    result = quick_validate(func, data, sample_size=50, verbose=False)
    
    if result.is_accurate(threshold=70):
        print("✓ Good - optimizer working as expected")
        return True
    else:
        print(f"⚠️ Accuracy only {result.accuracy_percent:.1f}%")
        print("Consider: ", result.recommendations[0])
        return False

# Use during development
if development_check(my_function, test_data):
    print("Ready for more extensive testing")
```

## Understanding Results

### Accuracy Interpretation

| Accuracy | Interpretation | Action |
|----------|---------------|--------|
| ≥ 90% | Excellent | Trust and deploy |
| 75-89% | Good | Deploy with confidence |
| 60-74% | Moderate | Deploy with monitoring |
| < 60% | Low | Investigate system factors |

### Error Interpretation

**Positive error** (actual > predicted):
- System is more efficient than estimated
- Good news - better performance than expected
- May indicate conservative overhead estimates

**Negative error** (actual < predicted):
- System is less efficient than estimated
- Investigate potential issues:
  - CPU throttling or thermal issues
  - Background system load
  - Memory contention
  - Cache effects

### Common Recommendations

**"Serial execution is optimal for this workload"**
- Function is too fast for parallelization
- Overhead dominates any benefit
- Keep n_jobs=1

**"Parallel execution is slower than serial"**
- Actual benchmarks show negative speedup
- Consider increasing workload complexity
- May need to increase data size

**"Significant deviation from prediction"**
- System-specific factors affecting performance
- Profile system under load
- Check for resource contention

## Performance Considerations

### Benchmark Runtime

Validation involves running both serial and parallel execution:

| Dataset Size | max_items | Typical Runtime |
|--------------|-----------|-----------------|
| Small (< 100) | All | < 1 second |
| Medium (100-1000) | 100-500 | 1-10 seconds |
| Large (> 1000) | 500-1000 | 10-60 seconds |
| Very Large | Use `quick_validate()` | 1-5 seconds |

**Tips for large datasets:**
1. Use `max_items` to limit benchmark size
2. Use `quick_validate()` for fast checks
3. Sample data evenly across the range
4. Consider representative subsets

### When to Validate

**Always validate:**
- ✅ Before production deployment
- ✅ After system upgrades
- ✅ When accuracy is critical
- ✅ For new workload types

**Consider quick validation:**
- ✅ During development iteration
- ✅ For confidence checks
- ✅ With very large datasets
- ✅ When time is limited

**Skip validation:**
- ✅ For well-understood, stable workloads
- ✅ When predictions have been validated before
- ✅ For non-critical prototyping
- ✅ When system behavior is known

## Troubleshooting

### Low Accuracy (< 75%)

**Possible causes:**
1. **System load**: Background processes competing for resources
2. **CPU throttling**: Thermal management reducing performance
3. **Memory effects**: Cache behavior not captured in sampling
4. **Workload variance**: Heterogeneous tasks with high variability
5. **OS scheduler**: Non-deterministic scheduling decisions

**Solutions:**
- Run validation when system is idle
- Check CPU frequency scaling settings
- Increase sample size for heterogeneous workloads
- Use `max_items` to test different dataset sizes
- Profile with `optimize(..., profile=True)` for insights

### Validation Takes Too Long

**Solutions:**
1. Use `max_items` to limit benchmark size:
   ```python
   result = validate_optimization(func, data, max_items=500)
   ```

2. Use `quick_validate()` for sampling:
   ```python
   result = quick_validate(func, data, sample_size=100)
   ```

3. Reduce timeout for faster failure:
   ```python
   result = validate_optimization(func, data, timeout=30.0)
   ```

### Function Fails During Validation

If your function works with `optimize()` but fails during `validate_optimization()`:

**Check:**
1. Function is deterministic (same input → same output)
2. Function doesn't rely on external state
3. Function handles edge cases in dataset
4. No side effects that accumulate

**Example fix:**
```python
# Bad: Relies on external state
counter = 0
def bad_func(x):
    global counter
    counter += 1
    return x + counter

# Good: Pure function
def good_func(x):
    return x + 1
```

## Advanced Topics

### Custom Accuracy Thresholds

Adjust thresholds based on your needs:

```python
# Strict threshold for critical systems
if result.is_accurate(threshold=90):
    deploy_to_production()

# Relaxed threshold for prototyping
if result.is_accurate(threshold=60):
    continue_development()
```

### Validation in CI/CD

Integrate validation into continuous integration:

```python
def test_optimizer_accuracy():
    """CI/CD test for optimizer accuracy."""
    result = quick_validate(production_func, test_data, sample_size=50)
    
    # Fail CI if accuracy too low
    assert result.is_accurate(threshold=70), \
        f"Optimizer accuracy too low: {result.accuracy_percent:.1f}%"
    
    # Warn if accuracy degraded
    if result.accuracy_percent < 80:
        print(f"WARNING: Accuracy below 80% ({result.accuracy_percent:.1f}%)")
```

### Comparing Multiple Approaches

Validate different optimization strategies:

```python
# Strategy 1: Auto optimization
opt1 = optimize(func, data)
result1 = validate_optimization(func, data, optimization=opt1, max_items=200)

# Strategy 2: Conservative (serial)
from amorsize.optimizer import OptimizationResult
opt2 = OptimizationResult(n_jobs=1, chunksize=1, reason="Conservative", 
                          estimated_speedup=1.0, data=data)
result2 = validate_optimization(func, data, optimization=opt2, max_items=200)

# Compare
print(f"Auto:         {result1.actual_speedup:.2f}x (accuracy: {result1.accuracy_percent:.1f}%)")
print(f"Conservative: {result2.actual_speedup:.2f}x (accuracy: {result2.accuracy_percent:.1f}%)")

# Choose best
if result1.actual_speedup > result2.actual_speedup * 1.1:
    print("→ Use auto optimization")
else:
    print("→ Use conservative approach")
```

## Examples

See `examples/benchmark_validation_demo.py` for comprehensive examples:
- Basic validation workflow
- Quick validation for large datasets
- Production deployment validation
- System profiling and characterization
- Iterative optimization refinement
- Accuracy threshold checking
- Error investigation

## See Also

- [Diagnostic Profiling](README_diagnostic_profiling.md) - Understanding optimizer decisions
- [Basic Usage](../README.md#quick-start) - Getting started with Amorsize
- [Execute Function](README_execute.md) - One-line optimization and execution
- [CLI Interface](README_cli.md) - Command-line optimization tools

## Best Practices

1. **Validate before production**: Always validate critical workloads
2. **Use max_items**: Limit validation runtime for large datasets
3. **Check accuracy**: Use `is_accurate()` with appropriate thresholds
4. **Read recommendations**: Act on the insights provided
5. **Profile system**: Understand your hardware characteristics
6. **Iterate**: Refine based on validation feedback
7. **Document**: Record validation results for reference
8. **Monitor**: Track accuracy over time and across systems

## Summary

Benchmark validation provides **empirical confidence** in optimizer recommendations:

- ✅ Run actual serial vs parallel execution
- ✅ Compare predicted vs actual performance
- ✅ Get accuracy metrics and recommendations
- ✅ Make informed deployment decisions
- ✅ Understand system-specific behavior

Use it to **trust, verify, and refine** your parallelization strategy!
