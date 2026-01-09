# Diagnostic Profiling Mode

## Overview

Amorsize's diagnostic profiling mode provides comprehensive insight into why the optimizer made specific recommendations. This feature helps you understand the trade-offs between parallelization overhead and performance gains, enabling better optimization decisions.

## Quick Start

Enable profiling by adding `profile=True` to your `optimize()` call:

```python
from amorsize import optimize

def my_function(x):
    # Your computation here
    return x ** 2

data = range(1000)
result = optimize(my_function, data, profile=True)

# View the detailed diagnostic report
print(result.explain())
```

## What's Included in the Diagnostic Report

The diagnostic profile captures and explains:

### 1. Workload Analysis
- Function execution time per item
- Pickle/IPC serialization overhead
- Return object size
- Memory usage per call
- Total items and estimated serial execution time

### 2. System Resources
- Physical and logical CPU cores
- Available memory
- Multiprocessing start method (fork/spawn/forkserver)
- Process spawn cost measurement
- Task distribution overhead

### 3. Optimization Decision
- CPU-based worker limit
- Memory-based worker limit
- Optimal chunk size calculation
- Target chunk duration

### 4. Performance Prediction
- Theoretical maximum speedup
- Estimated actual speedup (accounting for overhead)
- Parallel efficiency percentage
- Detailed time breakdown:
  - Computation time
  - Process spawn overhead
  - IPC/serialization overhead
  - Task distribution overhead
- Overhead distribution percentages

### 5. Rejection Reasons (if applicable)
- Why parallelization was not recommended
- Specific metrics that triggered rejection

### 6. Active Constraints
- Memory limitations
- Non-standard start methods
- Data size unknowns (generators)

### 7. Recommendations
- Actionable suggestions based on analysis
- Alternative approaches for edge cases
- Performance optimization tips

## Usage Examples

### Example 1: Understanding Why Parallelization Was Rejected

```python
from amorsize import optimize

def fast_function(x):
    return x * 2

data = range(10000)
result = optimize(fast_function, data, profile=True)

print(result.explain())
```

Output shows:
```
[5] REJECTION REASONS
  ✗ Function execution time (0.7μs) is below 1ms threshold
  ✗ Parallelization overhead would exceed computation time
```

### Example 2: Analyzing Successful Parallelization

```python
from amorsize import optimize

def expensive_function(x):
    result = 0
    for i in range(10000):
        result += x ** 2
    return result

data = range(500)
result = optimize(expensive_function, data, profile=True)

print(f"Speedup: {result.estimated_speedup:.2f}x")
print(f"Efficiency: {result.profile.speedup_efficiency * 100:.1f}%")
print("\nFull report:")
print(result.explain())
```

### Example 3: Programmatic Access to Diagnostic Data

The `DiagnosticProfile` object provides structured access to all metrics:

```python
result = optimize(my_function, data, profile=True)

if result.profile:
    # Access timing information
    print(f"Execution time: {result.profile.avg_execution_time}s")
    print(f"Pickle overhead: {result.profile.avg_pickle_time}s")
    
    # Access system information
    print(f"Physical cores: {result.profile.physical_cores}")
    print(f"Spawn cost: {result.profile.spawn_cost}s")
    
    # Access optimization decisions
    print(f"Optimal chunksize: {result.profile.optimal_chunksize}")
    print(f"Max workers (CPU): {result.profile.max_workers_cpu}")
    print(f"Max workers (RAM): {result.profile.max_workers_memory}")
    
    # Access performance predictions
    print(f"Theoretical speedup: {result.profile.theoretical_max_speedup}x")
    print(f"Estimated speedup: {result.profile.estimated_speedup}x")
    print(f"Efficiency: {result.profile.speedup_efficiency * 100}%")
    
    # Get overhead breakdown
    breakdown = result.profile.get_overhead_breakdown()
    print(f"Spawn overhead: {breakdown['spawn']}%")
    print(f"IPC overhead: {breakdown['ipc']}%")
    print(f"Chunking overhead: {breakdown['chunking']}%")
    
    # Check for issues
    if result.profile.rejection_reasons:
        print("Rejection reasons:", result.profile.rejection_reasons)
    if result.profile.constraints:
        print("Active constraints:", result.profile.constraints)
    if result.profile.recommendations:
        print("Recommendations:", result.profile.recommendations)
```

### Example 4: Memory Constraint Analysis

```python
def large_return_function(x):
    return [x] * 100000  # Large object

data = range(1000)
result = optimize(large_return_function, data, profile=True)

print(result.explain())
```

The diagnostic report will show:
```
[6] ACTIVE CONSTRAINTS
  ⚠ Result memory (953.67MB) exceeds safety threshold (512.00MB)

[7] RECOMMENDATIONS
  💡 Consider using pool.imap_unordered() for memory-efficient streaming
  💡 Or process data in batches to control memory consumption
```

## Performance Impact

The profiling mode adds minimal overhead:

```python
import time

data = range(100)

# Without profiling
start = time.perf_counter()
result1 = optimize(my_function, data, profile=False)
time_without = time.perf_counter() - start

# With profiling
start = time.perf_counter()
result2 = optimize(my_function, data, profile=True)
time_with = time.perf_counter() - start

print(f"Overhead: {(time_with - time_without) * 1000:.2f}ms")
```

Typical overhead: < 1ms (just data structure population)

## When to Use Profiling

### Always Use When:
- Debugging unexpected optimization decisions
- Optimizing critical production workloads
- Understanding system-specific behavior
- Documenting optimization rationale
- Troubleshooting performance issues

### Optional (Use Default) When:
- Quick prototyping
- Running in tight loops (minimize overhead)
- Optimization decision is clear and expected

## Integration with Verbose Mode

Profiling and verbose mode work independently:

```python
# Just profiling - detailed report available via explain()
result = optimize(func, data, profile=True, verbose=False)
print(result.explain())

# Just verbose - prints during optimization
result = optimize(func, data, profile=False, verbose=True)

# Both - immediate console output + detailed report
result = optimize(func, data, profile=True, verbose=True)
print(result.explain())
```

## Advanced: Custom Analysis

Build custom analysis tools using the diagnostic data:

```python
def analyze_optimization(func, data):
    result = optimize(func, data, profile=True)
    
    profile = result.profile
    
    # Custom analysis
    if profile.estimated_speedup < 1.5:
        print("⚠ Low speedup - consider alternatives")
    
    if profile.speedup_efficiency < 0.6:
        print("⚠ Low efficiency - high overhead")
    
    overhead_total = (profile.overhead_spawn + 
                     profile.overhead_ipc + 
                     profile.overhead_chunking)
    compute_total = profile.parallel_compute_time
    
    if overhead_total > compute_total:
        print("⚠ Overhead exceeds computation!")
    
    return result

# Use custom analyzer
result = analyze_optimization(my_function, my_data)
```

## API Reference

### `optimize(..., profile=True)`

**Parameter:**
- `profile` (bool, default=False): Enable diagnostic profiling

**Returns:**
- `OptimizationResult` with populated `profile` attribute

### `OptimizationResult.explain()`

**Returns:**
- `str`: Formatted diagnostic report with all analysis sections

**Usage:**
```python
result = optimize(func, data, profile=True)
print(result.explain())
```

### `DiagnosticProfile` Attributes

**Sampling Results:**
- `avg_execution_time` (float): Average execution time per item
- `avg_pickle_time` (float): Average serialization time per item
- `return_size_bytes` (int): Average return object size
- `peak_memory_bytes` (int): Peak memory usage per call
- `sample_count` (int): Number of items sampled
- `is_picklable` (bool): Whether function is picklable

**System Information:**
- `physical_cores` (int): Physical CPU cores detected
- `logical_cores` (int): Logical CPU cores (with hyperthreading)
- `spawn_cost` (float): Process spawn cost in seconds
- `chunking_overhead` (float): Task distribution overhead per chunk
- `available_memory` (int): Available system memory in bytes
- `multiprocessing_start_method` (str): fork/spawn/forkserver

**Workload Characteristics:**
- `total_items` (int): Total number of items to process
- `estimated_serial_time` (float): Estimated serial execution time
- `estimated_result_memory` (int): Estimated memory for all results

**Decision Factors:**
- `max_workers_cpu` (int): Worker limit from CPU cores
- `max_workers_memory` (int): Worker limit from memory
- `optimal_chunksize` (int): Calculated optimal chunk size
- `target_chunk_duration` (float): Target duration per chunk

**Overhead Breakdown:**
- `overhead_spawn` (float): Total spawn overhead
- `overhead_ipc` (float): Total IPC/serialization overhead
- `overhead_chunking` (float): Total task distribution overhead
- `parallel_compute_time` (float): Parallelized computation time

**Speedup Analysis:**
- `theoretical_max_speedup` (float): Theoretical maximum (= n_jobs)
- `estimated_speedup` (float): Estimated actual speedup
- `speedup_efficiency` (float): Ratio of actual to theoretical (0-1)

**Decision Path:**
- `rejection_reasons` (List[str]): Why parallelization was rejected
- `constraints` (List[str]): Active constraints affecting decision
- `recommendations` (List[str]): Actionable optimization suggestions

### `DiagnosticProfile` Methods

**`format_time(seconds: float) -> str`**
- Formats time in human-readable units (μs/ms/s)

**`format_bytes(bytes: int) -> str`**
- Formats bytes in human-readable units (B/KB/MB/GB)

**`get_overhead_breakdown() -> Dict[str, float]`**
- Returns percentage breakdown of overhead components
- Keys: 'spawn', 'ipc', 'chunking'
- Values: Percentages (sum to 100)

**`explain_decision() -> str`**
- Generates comprehensive human-readable diagnostic report
- Same as `OptimizationResult.explain()`

## See Also

- [Basic Usage](basic_usage.py) - Getting started with Amorsize
- [Verbose Mode](README_intermediate_explained.md) - Console output during optimization
- [Memory Safety](memory_safety_demo.py) - Handling large return objects
- [Generator Safety](README_generator_safety.md) - Working with generators
