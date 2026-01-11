# Amorsize Performance Tuning Guide

This comprehensive guide teaches you how to extract maximum performance from Amorsize by understanding the underlying cost model, tuning parameters for your specific workload, and applying advanced optimization techniques.

## Table of Contents

- [Understanding the Cost Model](#understanding-the-cost-model)
- [Tuning target_chunk_duration](#tuning-target_chunk_duration)
- [Hardware-Specific Optimization](#hardware-specific-optimization)
- [Workload Analysis and Profiling](#workload-analysis-and-profiling)
- [Advanced Configuration Options](#advanced-configuration-options)
- [Benchmarking and Validation](#benchmarking-and-validation)
- [System-Specific Optimizations](#system-specific-optimizations)
- [Performance Troubleshooting](#performance-troubleshooting)
- [Extreme Performance Scenarios](#extreme-performance-scenarios)

---

## Understanding the Cost Model

Amorsize uses a sophisticated cost model based on **Amdahl's Law** with enhancements for real-world multiprocessing overhead. Understanding this model helps you make informed tuning decisions.

### The Core Formula

The parallel execution time is calculated as:

```
parallel_time = spawn_overhead + parallel_compute_time + ipc_overhead + chunking_overhead
```

Where:
- **spawn_overhead** = `spawn_cost_per_worker × n_jobs`
- **parallel_compute_time** = `total_compute_time / n_jobs`
- **ipc_overhead** = `(data_pickle_time + result_pickle_time) × total_items`
- **chunking_overhead** = `chunking_cost_per_chunk × num_chunks`

### Speedup Calculation

```
speedup = serial_time / parallel_time
```

The optimizer seeks to maximize speedup while respecting hardware and memory constraints.

### The Five Overhead Components

#### 1. **Spawn Cost** (Process Creation)

**What it is:** Time to create and initialize worker processes.

**Typical values:**
- Linux (`fork`): 10-15ms per worker
- Windows/macOS (`spawn`): 150-250ms per worker
- `forkserver`: 50-100ms per worker

**Impact:** Fixed cost paid once at pool creation. More expensive on Windows/macOS.

**Measured by:** `measure_spawn_cost()` in `system_info.py`

```python
from amorsize.system_info import measure_spawn_cost, get_multiprocessing_start_method

spawn_cost = measure_spawn_cost()
start_method = get_multiprocessing_start_method()
print(f"Start method: {start_method}, Spawn cost: {spawn_cost*1000:.1f}ms")
# Output: Start method: fork, Spawn cost: 12.3ms
```

**Tuning insight:** On Linux with `fork`, spawn cost is negligible. On Windows/macOS with `spawn`, you need larger workloads to amortize the 200ms+ per-worker cost.

#### 2. **IPC Overhead** (Inter-Process Communication)

**What it is:** Time to serialize (pickle) input data and results for transfer between processes.

**Components:**
- **Input serialization:** Data → pickle → transfer to worker
- **Result serialization:** Result → pickle → transfer back to main process

**Typical values:**
- Small primitives (int, float): <1μs
- NumPy arrays (1MB): 1-5ms
- Complex objects: 10-100ms

**Impact:** Linear with number of items. Can dominate for large data structures.

**Measured by:** Dry-run sampling in `sampling.py`

```python
from amorsize import optimize

def process_data(data):
    return data ** 2

# Amorsize measures pickle overhead during optimization
result = optimize(process_data, range(1000), verbose=True)
# Logs show: "Input pickle overhead: 0.002ms per item"
```

**Tuning insight:** Minimize data transfer by:
- Passing indices instead of full objects
- Using shared memory for large arrays (NumPy with multiprocessing.Array)
- Returning only essential results

#### 3. **Chunking Overhead** (Task Distribution)

**What it is:** Time spent in the multiprocessing queue distributing tasks to workers.

**Typical values:** 0.1-1ms per chunk

**Impact:** Scales with number of chunks. More chunks = more overhead.

**Formula:** `num_chunks = ceil(total_items / chunksize)`

**Measured by:** `measure_chunking_overhead()` in `system_info.py`

**Tuning insight:** Larger chunksizes reduce chunking overhead but may hurt load balancing.

#### 4. **Cache Effects** (Hardware-Level)

**What it is:** L1/L2/L3 cache miss penalties, cache coherency overhead, false sharing.

**Impact:** Becomes significant when:
- Working set > L3 cache size
- Many cores compete for shared cache lines
- Data structures cause false sharing

**Advanced model:** Available via `cost_model.py` for cache-aware optimization:

```python
from amorsize.cost_model import detect_system_topology, estimate_cache_coherency_overhead

topology = detect_system_topology(physical_cores=8)
print(f"L1: {topology.cache_info.l1_size/1024:.0f}KB")
print(f"L2: {topology.cache_info.l2_size/1024:.0f}KB")
print(f"L3: {topology.cache_info.l3_size/(1024**2):.0f}MB")

# Estimate cache overhead for your workload
overhead = estimate_cache_coherency_overhead(
    n_jobs=8,
    data_size_per_item=1024,  # 1KB per item
    cache_info=topology.cache_info,
    numa_info=topology.numa_info
)
print(f"Cache coherency overhead: {(overhead-1)*100:.1f}%")
```

**Tuning insight:** Keep working set per core < L3 cache size / n_jobs for best performance.

#### 5. **Memory Bandwidth Saturation**

**What it is:** Memory bus contention when multiple cores compete for RAM access.

**Typical bandwidth:**
- Consumer DDR4 (dual-channel): ~40 GB/s
- Server DDR4 (quad-channel): ~100 GB/s
- Server DDR5 (octa-channel): ~200 GB/s

**Impact:** Memory-intensive workloads hit bandwidth limits before CPU limits.

**Formula:** `bandwidth_demand = (data_size × 2) × items_per_second × n_jobs`

**Tuning insight:** For memory-bound workloads, optimal `n_jobs` < physical cores.

### Amdahl's Law with IPC Overlap

Amorsize uses an **enhanced Amdahl's Law** that accounts for IPC/pickle overhead occurring partially in parallel with computation:

```python
# Traditional Amdahl's Law (pessimistic):
parallel_time = spawn + (compute / n_jobs) + ipc + chunking

# Enhanced model with IPC overlap (more realistic):
ipc_overlap_factor = 0.3  # 30% of IPC happens in parallel
serial_ipc = ipc * (1 - ipc_overlap_factor)
parallel_ipc = (ipc * ipc_overlap_factor) / n_jobs
parallel_time = spawn + (compute / n_jobs) + parallel_ipc + serial_ipc + chunking
```

This reflects reality where:
- Workers receive data while main process prepares next chunk
- Result collection overlaps with ongoing computation
- OS-level buffering hides some IPC latency

---

## Tuning target_chunk_duration

The `target_chunk_duration` parameter is **the most important tuning knob** in Amorsize. It controls the trade-off between load balancing and overhead.

### What It Controls

`target_chunk_duration` sets the desired execution time for each chunk:

```python
chunksize = ceil(target_chunk_duration / avg_time_per_item)
```

**Default:** 0.2 seconds (200ms)

### The Trade-Off

#### Smaller chunks (lower duration):
- ✅ **Better load balancing** - Workers finish at similar times
- ✅ **Lower latency** - First results arrive sooner
- ✅ **Better for heterogeneous workloads** - Variable item times average out
- ❌ **More chunking overhead** - More queue operations
- ❌ **Less efficient for fast functions** - Overhead becomes significant

#### Larger chunks (higher duration):
- ✅ **Lower chunking overhead** - Fewer queue operations
- ✅ **Better for fast functions** - Amortize overhead across many items
- ✅ **Better cache locality** - Process related items together
- ❌ **Worse load balancing** - Some workers may finish much earlier
- ❌ **Higher latency** - Wait longer for first results

### When to Tune

#### Increase `target_chunk_duration` (0.5s - 2.0s) when:

1. **Function is very fast** (< 1ms per item):
```python
def fast_function(x):
    return x ** 2  # Takes 0.1ms

# With default 0.2s target, chunksize = 2000 items
# Increase to reduce overhead
result = optimize(fast_function, data, target_chunk_duration=1.0)
# Now chunksize = 10000 items, less queue overhead
```

2. **Workload is homogeneous** (uniform execution time):
```python
def uniform_task(image_path):
    return resize_image(image_path, (800, 600))

# All images same size, take same time
# Large chunks are safe - no load imbalance risk
result = optimize(uniform_task, images, target_chunk_duration=1.0)
```

3. **Throughput > Latency**:
```python
# Batch processing where total time matters more than first-result latency
result = optimize(process_record, records, target_chunk_duration=2.0)
```

#### Decrease `target_chunk_duration` (0.05s - 0.1s) when:

1. **Function is variable** (heterogeneous execution time):
```python
def process_document(doc):
    # Small docs: 10ms, Large docs: 500ms
    return analyze_text(doc)

# Small chunks ensure good load balancing
result = optimize(process_document, documents, target_chunk_duration=0.1)
```

2. **Latency matters** (streaming/real-time):
```python
from amorsize import optimize_streaming

# Want results as soon as possible
for result in optimize_streaming(process_item, data_stream, target_chunk_duration=0.05):
    handle_result(result)  # Process results immediately
```

3. **Long-running workload** (better progress tracking):
```python
def long_task(item):
    return expensive_computation(item)  # Takes 5-10s per item

# Smaller chunks provide more frequent progress updates
result = optimize(long_task, items, target_chunk_duration=0.1)
```

### Measuring Impact

Use diagnostic profiling to see chunking overhead:

```python
result = optimize(my_func, data, profile=True, target_chunk_duration=0.2)
print(result.explain())
# Look for "Overhead distribution" section:
# Spawn: 5.2%
# IPC: 78.3%
# Chunking: 16.5%  <- If high, increase target_chunk_duration
```

**Rule of thumb:** Chunking overhead should be < 10% of total parallel time.

### Advanced: Dynamic Adjustment

For mixed workloads, use adaptive chunking:

```python
from amorsize import optimize_with_adaptive_chunking

# Automatically adjusts chunksize based on runtime feedback
result = optimize_with_adaptive_chunking(
    variable_function,
    data,
    initial_chunk_duration=0.2,
    min_chunk_duration=0.05,
    max_chunk_duration=1.0
)
```

---

## Hardware-Specific Optimization

Different hardware requires different optimization strategies.

### Consumer Laptops (2-4 Cores)

**Characteristics:**
- Limited cores (2-4 physical)
- Moderate RAM (8-16GB)
- Thermal throttling under sustained load

**Optimization strategy:**

```python
# Conservative n_jobs to avoid throttling
# On 2-4 core laptops, use 2 workers to leave headroom for:
# - OS background tasks
# - Thermal management (reduce heat generation)
# - Battery life (less aggressive parallelism)
result = optimize(
    my_func,
    data,
    max_workers=2,  # Use only 2 of 4 cores to avoid thermal issues
    target_chunk_duration=0.3  # Larger chunks for efficiency
)
```

**Best practices:**
- Use `max_workers` to limit cores and prevent thermal issues
- Larger chunks reduce overhead on limited cores
- Monitor CPU temperature during long runs
- Consider battery impact - parallelism drains faster

### Workstation (8-16 Cores)

**Characteristics:**
- Many cores (8-16 physical)
- Ample RAM (32-64GB)
- Good cooling, sustained performance

**Optimization strategy:**

```python
# Let Amorsize use all available cores
result = optimize(
    my_func,
    data,
    target_chunk_duration=0.2  # Default works well
)
```

**Best practices:**
- Trust automatic n_jobs detection
- Profile to ensure all cores utilized
- Watch for memory bottlenecks with many workers
- Verify speedup scales linearly with cores

### HPC/Server (32+ Cores)

**Characteristics:**
- Many cores (32-128+)
- Large RAM (128GB-1TB)
- NUMA architecture (multiple memory nodes)
- High memory bandwidth

**Optimization strategy:**

```python
from amorsize.cost_model import detect_system_topology

# Check for NUMA architecture
topology = detect_system_topology(physical_cores=64)
if topology.numa_info.has_numa:
    # Limit workers per NUMA node to avoid cross-node penalties
    workers_per_node = topology.numa_info.cores_per_node
    print(f"NUMA detected: {topology.numa_info.numa_nodes} nodes, "
          f"{workers_per_node} cores/node")
    
    # Optimize for NUMA locality
    result = optimize(
        my_func,
        data,
        max_workers=workers_per_node * topology.numa_info.numa_nodes,
        target_chunk_duration=0.15  # Smaller for better distribution
    )
else:
    # No NUMA - use all cores
    result = optimize(my_func, data)
```

**Best practices:**
- Respect NUMA boundaries when possible
- Use `numactl` to pin processes to nodes
- Profile memory bandwidth saturation
- Consider task placement for data locality

### Cloud Instances

#### Small Instance (2 vCPUs)
```python
# vCPUs often share physical cores
result = optimize(
    my_func,
    data,
    max_workers=1,  # vCPUs don't scale like physical cores
    target_chunk_duration=0.5
)
```

#### Large Instance (32+ vCPUs)
```python
# Full physical cores, optimize aggressively
result = optimize(
    my_func,
    data,
    target_chunk_duration=0.1  # Better load balancing at scale
)
```

**Cloud-specific tips:**
- Verify vCPU vs physical core mapping
- Test scaling on actual instance type
- Watch for noisy neighbor effects
- Use spot instances for batch workloads

### GPU-Accelerated Systems

When combining CPU parallelism with GPU:

```python
def gpu_accelerated_task(batch):
    # Use CPU parallelism for data prep
    prepared = [preprocess(item) for item in batch]
    # GPU for computation
    results = gpu_batch_compute(prepared)
    return results

# Optimize data prep pipeline, not GPU computation
result = optimize(
    preprocess_only,
    data,
    n_jobs=8  # CPU cores for data prep
)
```

**Best practices:**
- Don't parallelize GPU kernels (they're already parallel)
- Use CPU parallelism for data loading/preprocessing
- Pipeline CPU prep with GPU compute
- Profile to find bottleneck (CPU prep vs GPU compute)

---

## Workload Analysis and Profiling

Understanding your workload characteristics is essential for optimal performance.

### Step 1: Function Profiling

Use `enable_function_profiling=True` to see where time is spent:

```python
result = optimize(
    my_function,
    data,
    enable_function_profiling=True,
    profile=True
)

# Show internal function breakdown
result.show_function_profile(sort_by='cumulative', limit=20)
```

**Example output:**
```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      100    0.015    0.000    0.250    0.002 my_module.py:42(my_function)
      100    0.120    0.001    0.120    0.001 {built-in method numpy.fft.fft}
      100    0.080    0.001    0.080    0.001 {built-in method numpy.linalg.solve}
      100    0.035    0.000    0.035    0.000 {built-in method numpy.dot}
```

**Insights:**
- `cumtime` = total time including subcalls
- `tottime` = time in function itself (excluding subcalls)
- Look for unexpected bottlenecks

### Step 2: Diagnostic Profiling

Get comprehensive system and overhead analysis:

```python
result = optimize(my_func, data, profile=True, verbose=True)
print(result.explain())
```

**Example output:**
```
======================================================================
AMORSIZE DIAGNOSTIC PROFILE
======================================================================

[1] WORKLOAD ANALYSIS
----------------------------------------------------------------------
  Function execution time:  12.45ms per item
  Input pickle overhead:    0.021ms per item
  Output pickle overhead:   0.087ms per item
  Input data size:          1.23KB
  Return object size:       4.56KB
  Peak memory per call:     8.90MB
  Workload variability:     CV=0.15 (homogeneous)
  Workload type:            cpu-bound (CPU utilization: 98.2%)
  Total items to process:   10000
  Estimated serial time:    2m 4.5s

[2] SYSTEM RESOURCES
----------------------------------------------------------------------
  Physical CPU cores:       8
  Logical CPU cores:        16
  Available memory:         15.23GB
  Start method:             fork
  Process spawn cost:       12.3ms per worker
  Chunking overhead:        0.42ms per chunk

[3] OPTIMIZATION DECISION
----------------------------------------------------------------------
  Max workers (CPU limit):  8
  Max workers (RAM limit):  24
  Optimal chunksize:        16
  Target chunk duration:    200.0ms

[4] PERFORMANCE PREDICTION
----------------------------------------------------------------------
  Theoretical max speedup:  8.00x
  Estimated actual speedup: 6.87x
  Parallel efficiency:      85.9%

  Time breakdown (parallel execution):
    Computation:            15.8s
    Process spawn:          0.10s
    IPC/Pickle:             1.08s
    Task distribution:      0.26s

  Overhead distribution:
    Spawn:                  6.9%
    IPC:                    75.0%
    Chunking:               18.1%
```

**Key insights:**
- **CV < 0.3:** Homogeneous - can use larger chunks
- **CPU utilization > 80%:** CPU-bound - good parallelization candidate
- **IPC overhead high:** Reduce data transfer size
- **Chunking overhead high:** Increase `target_chunk_duration`

### Step 3: Workload Classification

```python
from amorsize import optimize

result = optimize(my_func, data, profile=True)
profile = result.profile

if profile.workload_type == 'cpu_bound':
    print("✓ Excellent parallelization candidate")
    print(f"  CPU utilization: {profile.cpu_time_ratio*100:.1f}%")
elif profile.workload_type == 'io_bound':
    print("⚠ Consider threading instead of multiprocessing")
    print(f"  CPU utilization: {profile.cpu_time_ratio*100:.1f}%")
elif profile.workload_type == 'mixed':
    print("➜ May benefit from hybrid approach")
```

**Workload types:**
- **cpu_bound:** CPU time > 80% of wall time
- **io_bound:** CPU time < 50% of wall time
- **mixed:** 50-80% CPU time

### Step 4: Heterogeneity Analysis

```python
result = optimize(my_func, data, profile=True)
profile = result.profile

cv = profile.coefficient_of_variation
print(f"Coefficient of Variation: {cv:.2f}")

if cv < 0.3:
    print("✓ Homogeneous workload - large chunks OK")
    print(f"  Consider target_chunk_duration=0.5s")
elif cv < 0.7:
    print("➜ Moderate variability - default settings OK")
elif cv >= 0.7:
    print("⚠ Highly heterogeneous workload")
    print(f"  Consider target_chunk_duration=0.1s for better load balancing")
    print(f"  Or use adaptive chunking")
```

**Coefficient of Variation (CV):**
- CV = `stddev / mean` of execution times
- CV < 0.3: Homogeneous (uniform times)
- CV > 0.7: Heterogeneous (variable times)

---

## Advanced Configuration Options

Fine-tune optimization behavior with advanced parameters.

### Memory Safety

Control memory-based worker limiting:

```python
from amorsize import optimize

# Automatic memory-aware worker limiting
result = optimize(
    memory_intensive_func,
    data,
    max_workers=None,  # Auto-detect with memory awareness
    verbose=True
)
# Logs: "Memory constraint: Limiting to 4 workers (8GB available, 2GB per job)"

# Override for specific memory budget
result = optimize(
    memory_intensive_func,
    data,
    max_workers=16,  # Force 16 workers
    respect_memory_limit=False  # Disable automatic limiting
)
```

### Load-Aware Optimization

Adjust workers based on current system load:

```python
from amorsize.system_info import (
    calculate_load_aware_workers,
    get_physical_cores,
    get_current_cpu_load,
    get_memory_pressure
)

# Check current system load
cpu_load = get_current_cpu_load()
memory_pressure = get_memory_pressure()
print(f"CPU: {cpu_load:.1f}%, Memory: {memory_pressure:.1f}%")

# Automatically reduce workers if system is busy
physical_cores = get_physical_cores()
optimal_workers = calculate_load_aware_workers(
    physical_cores=physical_cores,
    estimated_job_ram=1024*1024*1024,  # 1GB per job
    cpu_threshold=70.0,    # Reduce if CPU > 70%
    memory_threshold=75.0, # Reduce if memory > 75%
    aggressive_reduction=True  # More aggressive under load
)

result = optimize(my_func, data, max_workers=optimal_workers)
```

### Benchmarking Configuration

Control overhead measurement:

```python
# Fast mode - use estimates (no benchmarking)
result = optimize(
    my_func,
    data,
    use_spawn_benchmark=False,  # Use OS-based estimate
    use_chunking_benchmark=False  # Use default estimate
)

# Precise mode - measure everything
result = optimize(
    my_func,
    data,
    use_spawn_benchmark=True,  # Measure actual spawn cost
    use_chunking_benchmark=True,  # Measure actual chunking overhead
    sample_size=50  # More samples for precise measurement
)
```

### Sampling Configuration

Control dry-run behavior:

```python
# Quick optimization (fewer samples)
result = optimize(
    my_func,
    data,
    sample_size=10,  # Minimum samples
    max_sample_time=1.0  # Stop after 1 second
)

# Precise optimization (more samples)
result = optimize(
    my_func,
    data,
    sample_size=100,  # Many samples
    max_sample_time=10.0,  # Up to 10 seconds
    confidence_level=0.99  # Higher confidence
)
```

### Caching Configuration

Use historical data to skip profiling:

```python
from amorsize import optimize
from amorsize.cache import Cache

# Enable caching
cache = Cache()

# First run - full profiling
result = optimize(my_func, data, cache=cache)
# Logs: "Cache miss - performing full profiling"

# Second run - instant result
result = optimize(my_func, data, cache=cache)
# Logs: "Cache hit - using cached parameters"

# Clear cache if function changed
cache.clear()
```

### Executor Selection

Choose between multiprocessing and threading:

```python
# Force threading for I/O-bound tasks
result = optimize(
    io_bound_func,
    data,
    executor_type='thread'  # Use ThreadPoolExecutor
)

# Force multiprocessing for CPU-bound tasks
result = optimize(
    cpu_bound_func,
    data,
    executor_type='process'  # Use multiprocessing.Pool
)

# Auto-detect based on workload
result = optimize(
    unknown_func,
    data,
    executor_type='auto'  # Default: auto-detect
)
```

---

## Benchmarking and Validation

Verify that Amorsize's predictions match reality.

### Basic Validation

Compare predicted vs actual speedup:

```python
from amorsize import optimize, execute
import time

# Get optimization recommendation
result = optimize(my_func, data, profile=True)
print(f"Predicted speedup: {result.estimated_speedup:.2f}x")

# Measure serial execution
start = time.perf_counter()
serial_results = [my_func(item) for item in data]
serial_time = time.perf_counter() - start

# Measure parallel execution
start = time.perf_counter()
parallel_results = execute(
    my_func,
    data,
    n_jobs=result.n_jobs,
    chunksize=result.chunksize
)
parallel_time = time.perf_counter() - start

# Calculate actual speedup
actual_speedup = serial_time / parallel_time
prediction_error = abs(actual_speedup - result.estimated_speedup) / result.estimated_speedup

print(f"\nActual speedup: {actual_speedup:.2f}x")
print(f"Prediction error: {prediction_error*100:.1f}%")

if prediction_error < 0.1:
    print("✓ Excellent prediction accuracy")
elif prediction_error < 0.2:
    print("✓ Good prediction accuracy")
else:
    print("⚠ High prediction error - investigate")
```

### Comprehensive Benchmarking

Use built-in benchmark validation:

```python
from amorsize import benchmark_validate

# Comprehensive validation across multiple configurations
report = benchmark_validate(
    my_func,
    data,
    n_jobs_range=[1, 2, 4, 8],
    chunksize_range=[1, 10, 100, 1000],
    num_trials=5  # Run each config 5 times
)

# Analyze results
print(report.summary())
# Shows: Best config, prediction accuracy, overhead breakdown

# Visualize performance
report.plot_speedup_curve()
report.plot_overhead_breakdown()
```

### A/B Testing Configurations

Compare different tuning strategies:

```python
import time

configs = [
    {'name': 'Default', 'target_chunk_duration': 0.2},
    {'name': 'Fast chunks', 'target_chunk_duration': 0.1},
    {'name': 'Large chunks', 'target_chunk_duration': 0.5},
    {'name': 'Conservative workers', 'max_workers': 4},
]

results = []
for config in configs:
    start = time.perf_counter()
    result = execute(my_func, data, **{k: v for k, v in config.items() if k != 'name'})
    elapsed = time.perf_counter() - start
    results.append({'name': config['name'], 'time': elapsed})

# Find best configuration
best = min(results, key=lambda x: x['time'])
print(f"Best configuration: {best['name']} ({best['time']:.2f}s)")
```

---

## System-Specific Optimizations

Platform-specific tuning for maximum performance.

### Linux Optimization

**Leverage fork() advantages:**

```python
import multiprocessing
multiprocessing.set_start_method('fork', force=True)

# fork is 10-15x faster than spawn
from amorsize import optimize
result = optimize(my_func, data)
# Spawn cost: ~12ms per worker vs ~200ms on Windows
```

**NUMA awareness:**

```bash
# Check NUMA topology
numactl --hardware

# Pin workers to specific nodes
numactl --cpunodebind=0 --membind=0 python my_script.py
```

**Huge pages for large datasets:**

```bash
# Enable transparent huge pages
echo always > /sys/kernel/mm/transparent_hugepage/enabled

# Check usage
cat /proc/meminfo | grep Huge
```

### Windows Optimization

**Minimize spawn overhead:**

```python
# Ensure all imports and initialization are inside if __name__ == '__main__'
if __name__ == '__main__':
    # Windows requires explicit protection
    from amorsize import optimize
    
    # Use larger chunks to amortize spawn cost
    result = optimize(
        my_func,
        data,
        target_chunk_duration=0.5  # Larger chunks on Windows
    )
```

**Process priority:**

```python
import psutil
import os

# Set high priority for compute-intensive tasks
p = psutil.Process(os.getpid())
p.nice(psutil.HIGH_PRIORITY_CLASS)  # Windows-specific
```

### macOS Optimization

**Handle spawn start method:**

```python
# macOS uses spawn by default (Python 3.8+)
import multiprocessing

# Can use fork for better performance (but may have issues with GUI apps)
try:
    multiprocessing.set_start_method('fork', force=True)
except RuntimeError:
    pass  # Already set

from amorsize import optimize
result = optimize(my_func, data)
```

**Thermal management:**

```python
import subprocess

# Check thermal pressure
try:
    result = subprocess.run(
        ['pmset', '-g', 'thermlog'],
        capture_output=True,
        text=True
    )
    if 'CPU_Speed_Limit' in result.stdout:
        print("⚠ Thermal throttling detected")
        # Use fewer workers to reduce heat
        result = optimize(my_func, data, max_workers=2)
except:
    pass
```

### Docker/Container Optimization

**Respect container limits:**

```python
from amorsize.system_info import get_available_memory
import os

# Check cgroup memory limit
memory_bytes = get_available_memory()
memory_gb = memory_bytes / (1024**3)
print(f"Container memory limit: {memory_gb:.1f}GB")

# Check CPU quota
try:
    with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us') as f:
        quota = int(f.read().strip())
    with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us') as f:
        period = int(f.read().strip())
    if quota > 0:
        container_cpus = quota / period
        print(f"Container CPU limit: {container_cpus:.1f} cores")
        result = optimize(my_func, data, max_workers=int(container_cpus))
except:
    result = optimize(my_func, data)
```

**Docker-specific tips:**
- Use `--cpus` and `--memory` flags appropriately
- Amorsize auto-detects cgroup v1 and v2 limits
- Test with actual container limits, not host specs

---

## Performance Troubleshooting

Common issues and solutions.

### Issue 1: Lower Than Expected Speedup

**Symptoms:** Actual speedup < 50% of theoretical maximum

**Diagnosis:**

```python
result = optimize(my_func, data, profile=True)
print(result.explain())

# Check overhead breakdown
breakdown = result.profile.get_overhead_breakdown()
print(f"Spawn: {breakdown['spawn']:.1f}%")
print(f"IPC: {breakdown['ipc']:.1f}%")
print(f"Chunking: {breakdown['chunking']:.1f}%")
```

**Solutions:**

If **IPC overhead > 50%:**
```python
# Reduce data transfer size
def optimized_func(index):
    # Load data inside worker
    data = load_from_disk(index)
    return process(data)

result = optimize(optimized_func, range(len(data)))
```

If **Spawn overhead > 20%:**
```python
# Use larger chunks to amortize spawn cost
result = optimize(my_func, data, target_chunk_duration=1.0)
```

If **Chunking overhead > 15%:**
```python
# Increase chunk size
result = optimize(my_func, data, target_chunk_duration=0.5)
```

### Issue 2: No Speedup (Speedup ≈ 1.0x)

**Symptoms:** Parallel execution takes same time as serial

**Diagnosis:**

```python
result = optimize(my_func, data, profile=True, verbose=True)
# Check rejection reasons
if result.profile.rejection_reasons:
    for reason in result.profile.rejection_reasons:
        print(f"✗ {reason}")
```

**Common causes:**

1. **Function too fast:**
```python
# If avg_execution_time < 1ms, overhead dominates
# Solution: Batch items together
def batched_func(items):
    return [my_fast_func(x) for x in items]

# Create batches
batches = [data[i:i+100] for i in range(0, len(data), 100)]
result = optimize(batched_func, batches)
```

2. **Workload too small:**
```python
# Need enough items to justify parallelism
# Rule of thumb: total_time > 10 * spawn_cost * n_jobs
min_items = 10 * result.profile.spawn_cost * result.n_jobs / result.profile.avg_execution_time
print(f"Need at least {min_items:.0f} items for speedup")
```

3. **I/O bound:**
```python
# Use threading instead
result = optimize(my_func, data, executor_type='thread')
```

### Issue 3: Memory Errors / OOM Kills

**Symptoms:** Process killed, out of memory errors

**Diagnosis:**

```python
result = optimize(my_func, data, profile=True)
estimated_ram_per_worker = result.profile.peak_memory_bytes
total_ram_needed = estimated_ram_per_worker * result.n_jobs
available_ram = result.profile.available_memory

print(f"RAM needed: {total_ram_needed/(1024**3):.1f}GB")
print(f"RAM available: {available_ram/(1024**3):.1f}GB")

if total_ram_needed > available_ram * 0.8:
    print("⚠ Insufficient memory!")
```

**Solutions:**

```python
# Reduce workers
result = optimize(my_func, data, max_workers=2)

# Or use batch processing
from amorsize import execute_batch
results = execute_batch(
    my_func,
    data,
    batch_size=1000,  # Process 1000 items at a time
    max_memory_gb=8   # Keep memory under 8GB
)
```

### Issue 4: Excessive CPU Usage / Thermal Throttling

**Symptoms:** High CPU usage but low performance, thermal warnings

**Solution:**

```python
# Limit workers to reduce heat/power
result = optimize(
    my_func,
    data,
    max_workers=4,  # Use fewer cores
    target_chunk_duration=0.3  # Larger chunks = less switching
)
```

---

## Extreme Performance Scenarios

Advanced patterns for specialized use cases.

### Scenario 1: Millions of Tiny Tasks

**Challenge:** 10M+ items, each takes < 1ms

**Solution: Aggressive batching**

```python
def batch_wrapper(batch_indices):
    """Process 1000 items per task"""
    return [tiny_func(data[i]) for i in batch_indices]

# Create batches of 1000 items each
batch_size = 1000
batches = [range(i, min(i + batch_size, len(data))) 
           for i in range(0, len(data), batch_size)]

result = optimize(
    batch_wrapper,
    batches,
    target_chunk_duration=1.0  # Large chunks for batched work
)
```

**Expected speedup:** 5-7x on 8 cores

### Scenario 2: Highly Variable Execution Time

**Challenge:** Some items take 1ms, others take 1000ms

**Solution: Small chunks + adaptive scheduling**

```python
from amorsize import optimize_with_adaptive_chunking

result = optimize_with_adaptive_chunking(
    variable_func,
    data,
    initial_chunk_duration=0.05,  # Start with small chunks
    adaptation_rate=0.2,           # Adjust quickly
    min_chunk_duration=0.01,       # Allow very small chunks
    max_chunk_duration=0.5         # Cap maximum chunk size
)
```

**Expected speedup:** 7-7.5x on 8 cores (vs 5-6x with static chunks)

### Scenario 3: Large Return Objects

**Challenge:** Each result is 10MB+, causes memory pressure

**Solution: Streaming with incremental processing**

```python
from amorsize import optimize_streaming

# Process results as they arrive, don't accumulate in memory
for result in optimize_streaming(my_func, data, target_chunk_duration=0.1):
    # Save to disk immediately
    save_to_disk(result)
    # Free memory
    del result
```

**Memory usage:** O(chunksize) instead of O(total_items)

### Scenario 4: NUMA System (64+ Cores)

**Challenge:** Cross-NUMA penalties hurt performance

**Solution: NUMA-aware worker placement**

```python
from amorsize.cost_model import detect_system_topology

topology = detect_system_topology(physical_cores=64)
if topology.numa_info.has_numa:
    # Split work across NUMA nodes
    nodes = topology.numa_info.numa_nodes
    cores_per_node = topology.numa_info.cores_per_node
    
    # Process each NUMA node separately
    for node in range(nodes):
        node_data = data[node::nodes]  # Interleaved distribution
        result = optimize(
            my_func,
            node_data,
            max_workers=cores_per_node,  # Workers per node
            target_chunk_duration=0.15
        )
```

**Expected improvement:** 10-20% over naive approach

### Scenario 5: Real-Time Streaming with Latency Constraints

**Challenge:** Process continuous data stream with < 100ms latency

**Solution: Small chunks + pipelined execution**

```python
from amorsize import optimize_streaming

# Minimize latency with small chunks
for result in optimize_streaming(
    process_frame,
    video_stream,
    target_chunk_duration=0.03,  # 30ms chunks
    max_workers=4  # Balance parallelism vs latency
):
    # Display result immediately
    display_frame(result)  # < 100ms from input to output
```

---

## Summary: Quick Reference

### Default Settings (Good Starting Point)

```python
result = optimize(my_func, data, verbose=True)
```

### High-Performance Tuning

```python
result = optimize(
    my_func,
    data,
    target_chunk_duration=0.15,  # Better load balancing
    use_spawn_benchmark=True,    # Precise measurement
    sample_size=50,              # More samples
    profile=True                 # Enable diagnostics
)
```

### Memory-Constrained Tuning

```python
result = optimize(
    my_func,
    data,
    max_workers=4,               # Limit memory usage
    target_chunk_duration=0.5,   # Larger chunks
    verbose=True
)
```

### Low-Latency Tuning

```python
from amorsize import optimize_streaming

for result in optimize_streaming(
    my_func,
    data,
    target_chunk_duration=0.05,  # Small chunks
    max_workers=4                # Limit for latency
):
    process_immediately(result)
```

### I/O-Bound Tuning

```python
result = optimize(
    io_bound_func,
    data,
    executor_type='thread',      # Use threading
    max_workers=20               # More threads OK
)
```

---

## Additional Resources

- [Best Practices Guide](BEST_PRACTICES.md) - When and how to parallelize
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [API Documentation](../README.md) - Complete API reference
- [Examples](../examples/) - Real-world usage examples

---

**Need help?** File an issue at https://github.com/CampbellTrevor/Amorsize/issues
