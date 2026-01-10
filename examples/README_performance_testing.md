# Performance Regression Testing

Amorsize includes a comprehensive performance regression testing framework to ensure optimizer accuracy doesn't degrade with code changes. This guide explains how to use the performance testing tools.

## Overview

The performance testing framework provides:

- **Standardized benchmark workloads** for consistent testing across versions
- **Automated regression detection** to catch performance degradations
- **Historical comparison** to track optimizer accuracy over time
- **CI/CD integration** for continuous performance monitoring

## Quick Start

### Running the Standard Benchmark Suite

```python
from amorsize import run_performance_suite

# Run all standard workloads with validation
results = run_performance_suite(
    run_validation=True,
    verbose=True,
    save_results=True,
    results_path="baseline.json"
)

# Check results
passed = sum(1 for r in results.values() if r.passed)
print(f"Passed: {passed}/{len(results)} benchmarks")
```

### Comparing Performance Across Versions

```python
from amorsize import compare_performance_results
from pathlib import Path

# Compare baseline vs current
comparison = compare_performance_results(
    baseline_path=Path("baseline.json"),
    current_path=Path("current.json"),
    regression_threshold=0.1  # 10% threshold
)

# Check for regressions
if comparison['regressions']:
    print("⚠️  Performance regressions detected!")
    for reg in comparison['regressions']:
        print(f"  {reg['workload']}: "
              f"{reg['baseline_speedup']:.2f}x → {reg['current_speedup']:.2f}x "
              f"({reg['change_percent']:.1f}%)")
```

## Standard Benchmark Workloads

The framework includes 5 standard workloads covering different patterns:

### 1. CPU-Intensive
Pure computation (prime checking and factorization)
```python
from amorsize import get_standard_workloads

workloads = get_standard_workloads()
cpu_workload = workloads[0]  # cpu_intensive
```

**Expected behavior:** High speedup with multiprocessing

### 2. Mixed Workload
Combination of computation and I/O simulation
```python
mixed_workload = workloads[1]  # mixed_workload
```

**Expected behavior:** Moderate speedup, may benefit from threading

### 3. Memory-Intensive
Large intermediate data structures
```python
memory_workload = workloads[2]  # memory_intensive
```

**Expected behavior:** Good speedup but memory-constrained

### 4. Fast Function
Very quick execution (may not benefit from parallelism)
```python
fast_workload = workloads[3]  # fast_function
```

**Expected behavior:** May show negative scaling due to overhead

### 5. Variable-Time
Heterogeneous workload with varying execution times
```python
variable_workload = workloads[4]  # variable_time
```

**Expected behavior:** Benefits from adaptive chunking

## Creating Custom Workloads

Define your own benchmark workloads for specific use cases:

```python
from amorsize import WorkloadSpec, run_performance_benchmark

# Define custom workload
custom_workload = WorkloadSpec(
    name="image_processing",
    description="Image transformation pipeline",
    func=process_image,
    data_generator=lambda n: [generate_test_image(i) for i in range(n)],
    data_size=50,
    expected_workload_type="cpu_bound",
    min_speedup=2.0,
    max_execution_time=60.0
)

# Run benchmark
result = run_performance_benchmark(
    custom_workload,
    run_validation=True,
    verbose=True
)

print(f"Passed: {result.passed}")
print(f"Issues: {result.issues}")
```

## Running Individual Benchmarks

Test a single workload in detail:

```python
from amorsize import run_performance_benchmark, get_standard_workloads

workload = get_standard_workloads()[0]  # CPU-intensive

result = run_performance_benchmark(
    workload,
    run_validation=True,
    validate_max_items=50,
    verbose=True
)

# Access detailed results
print(f"Optimizer recommendation: {result.optimizer_result}")
print(f"Benchmark validation: {result.benchmark_result}")
print(f"Regression detected: {result.regression_detected}")
```

## CI/CD Integration

### Pytest Integration

Add performance tests to your test suite:

```python
# tests/test_performance_regression.py
import pytest
from pathlib import Path
from amorsize import run_performance_suite, compare_performance_results

@pytest.mark.slow
def test_no_performance_regression():
    """Ensure optimizer performance hasn't regressed."""
    baseline_path = Path("benchmarks/baseline.json")
    
    # Run current benchmarks
    results = run_performance_suite(
        run_validation=True,
        validate_max_items=30,
        save_results=True,
        results_path=Path("benchmarks/current.json")
    )
    
    # All benchmarks should pass
    failed = [name for name, r in results.items() if not r.passed]
    assert not failed, f"Failed benchmarks: {failed}"
    
    # Compare against baseline if it exists
    if baseline_path.exists():
        comparison = compare_performance_results(
            baseline_path,
            Path("benchmarks/current.json"),
            regression_threshold=0.15  # 15% tolerance
        )
        
        # No regressions should be detected
        assert not comparison['regressions'], \
            f"Performance regressions: {comparison['regressions']}"
```

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  pull_request:
    branches: [ main ]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e ".[full,dev]"
    
    - name: Run performance benchmarks
      run: |
        python -c "from amorsize import run_performance_suite; \
                   results = run_performance_suite(verbose=True, save_results=True); \
                   exit(0 if all(r.passed for r in results.values()) else 1)"
    
    - name: Upload benchmark results
      uses: actions/upload-artifact@v4
      with:
        name: performance-results
        path: performance_results.json
```

## Understanding Results

### PerformanceResult Structure

Each benchmark returns a `PerformanceResult` with:

```python
{
    'workload_name': 'cpu_intensive',
    'optimizer_result': {
        'n_jobs': 8,
        'chunksize': 25,
        'estimated_speedup': 6.5
    },
    'benchmark_result': {
        'actual_speedup': 6.2,
        'predicted_speedup': 6.5,
        'accuracy_percent': 95.4
    },
    'passed': True,
    'regression_detected': False,
    'issues': [],
    'metadata': {...}
}
```

### Pass/Fail Criteria

A benchmark passes if:
- ✅ No exceptions during optimization or validation
- ✅ Actual speedup meets minimum threshold (workload-specific)
- ✅ Execution time within maximum allowed
- ✅ Prediction accuracy reasonable (>50%)

A benchmark fails if:
- ❌ Speedup below 80% of minimum threshold (regression)
- ❌ Execution time exceeds maximum
- ❌ Prediction accuracy very poor (<50%)
- ❌ Optimizer crashes or produces invalid recommendations

### Regression Detection

Regressions are detected by comparing:
1. **Speedup changes** - Actual speedup drops significantly
2. **Accuracy changes** - Prediction accuracy degrades
3. **Execution time** - Processing becomes slower

Threshold (default 10%) determines sensitivity:
- Lower threshold (5%) = More sensitive, catches small regressions
- Higher threshold (20%) = Less sensitive, reduces false positives

## Best Practices

### 1. Establish Baseline Early
```python
# Run once on known-good version
from amorsize import run_performance_suite

run_performance_suite(
    run_validation=True,
    save_results=True,
    results_path="baseline.json"
)
```

### 2. Run Before Major Changes
Test performance before merging significant code changes:
```bash
python -m amorsize.performance --baseline baseline.json --current current.json
```

### 3. Monitor Trends Over Time
Track optimizer accuracy across versions:
```python
from amorsize import run_performance_suite
import datetime

# Include version in filename
version = "v0.2.0"
timestamp = datetime.datetime.now().strftime("%Y%m%d")
results_path = f"benchmarks/{version}_{timestamp}.json"

run_performance_suite(save_results=True, results_path=results_path)
```

### 4. Use Appropriate Thresholds
Adjust regression thresholds based on your needs:
- **Strict (5%)** - For production systems where consistency is critical
- **Moderate (10%)** - For general development (recommended)
- **Lenient (20%)** - For experimental features or noisy environments

### 5. Test on Representative Systems
Run benchmarks on systems similar to production:
```python
# Save system info with results
from amorsize import run_performance_suite

results = run_performance_suite(
    verbose=True,
    save_results=True,
    results_path=f"benchmarks/system_{platform.node()}.json"
)
```

## Troubleshooting

### Benchmark Takes Too Long
Reduce validation sample size:
```python
results = run_performance_suite(
    run_validation=True,
    validate_max_items=20,  # Smaller sample
    verbose=True
)
```

### False Positives
Increase regression threshold or disable validation:
```python
results = run_performance_suite(
    run_validation=False,  # Faster, less sensitive
    verbose=True
)
```

### System-Specific Variations
Results may vary across different systems. Use consistent hardware for comparisons or increase tolerance:
```python
comparison = compare_performance_results(
    baseline_path,
    current_path,
    regression_threshold=0.20  # 20% tolerance for cross-system
)
```

## API Reference

### Core Functions

#### `run_performance_suite()`
Run the full benchmark suite with all standard workloads.

**Parameters:**
- `workloads` (List[WorkloadSpec], optional): Custom workloads (default: standard)
- `run_validation` (bool): Run empirical validation (default: True)
- `validate_max_items` (int): Max items for validation (default: 50)
- `verbose` (bool): Print progress (default: False)
- `save_results` (bool): Save to file (default: False)
- `results_path` (Path, optional): Output path (default: ./performance_results.json)

**Returns:** Dict[str, PerformanceResult]

#### `run_performance_benchmark()`
Run a single benchmark workload.

**Parameters:**
- `workload` (WorkloadSpec): Workload specification
- `run_validation` (bool): Run empirical validation (default: True)
- `validate_max_items` (int): Max items for validation (default: 50)
- `verbose` (bool): Print progress (default: False)

**Returns:** PerformanceResult

#### `compare_performance_results()`
Compare two benchmark result files to detect regressions.

**Parameters:**
- `baseline_path` (Path): Path to baseline results JSON
- `current_path` (Path): Path to current results JSON
- `regression_threshold` (float): Threshold for regression detection (default: 0.1)

**Returns:** Dict with comparison results

#### `get_standard_workloads()`
Get the standard benchmark workload specifications.

**Returns:** List[WorkloadSpec]

### Data Classes

#### `WorkloadSpec`
Specification for a benchmark workload.

**Attributes:**
- `name` (str): Human-readable name
- `description` (str): What this workload tests
- `func` (Callable): Function to benchmark
- `data_generator` (Callable): Generates test data
- `data_size` (int): Number of items to process
- `expected_workload_type` (str): Expected type (cpu_bound, io_bound, mixed)
- `min_speedup` (float): Minimum acceptable speedup
- `max_execution_time` (float): Maximum execution time in seconds

#### `PerformanceResult`
Result from running a performance benchmark.

**Attributes:**
- `workload_name` (str): Name of workload
- `optimizer_result` (Dict): OptimizationResult serialized
- `benchmark_result` (Dict): BenchmarkResult serialized (if validation run)
- `passed` (bool): Whether benchmark passed
- `regression_detected` (bool): Whether regression detected
- `issues` (List[str]): Issues found
- `metadata` (Dict): Additional metadata

## Example Workflows

### Development Workflow

```python
# 1. Establish baseline on clean main branch
from amorsize import run_performance_suite

baseline = run_performance_suite(
    run_validation=True,
    verbose=True,
    save_results=True,
    results_path="baseline.json"
)

# 2. Make code changes
# ... edit code ...

# 3. Run benchmarks after changes
current = run_performance_suite(
    run_validation=True,
    verbose=True,
    save_results=True,
    results_path="current.json"
)

# 4. Compare results
from amorsize import compare_performance_results

comparison = compare_performance_results(
    Path("baseline.json"),
    Path("current.json")
)

# 5. Review results
if comparison['regressions']:
    print("⚠️  Regressions detected - investigate before merging")
    for reg in comparison['regressions']:
        print(f"  {reg}")
else:
    print("✅ No regressions - safe to merge")
```

### Continuous Monitoring

```python
# Run periodically (e.g., nightly) to track trends
import datetime
from pathlib import Path
from amorsize import run_performance_suite

# Run suite
results = run_performance_suite(run_validation=True, verbose=True)

# Save with timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
save_path = Path(f"benchmarks/daily/{timestamp}.json")
save_path.parent.mkdir(parents=True, exist_ok=True)

# Serialize and save
import json
results_dict = {name: r.to_dict() for name, r in results.items()}
with open(save_path, 'w') as f:
    json.dump(results_dict, f, indent=2)

print(f"Results saved to {save_path}")
```

## See Also

- [Benchmark Validation](README_benchmark_validation.md) - Empirical validation of optimizer predictions
- [History Tracking](README_history.md) - Track and compare optimization results over time
- [System Validation](README_system_validation.md) - Validate measurement accuracy
