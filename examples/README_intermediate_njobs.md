# Intermediate n_jobs Examples

These examples demonstrate scenarios where Amorsize recommends an optimal number of workers that is **neither 1 nor the maximum number of cores**.

## Files

### 1. `memory_constrained_example.py`
Demonstrates memory-constrained parallelization where high memory usage per task limits the number of workers.

**Key Scenario:** When each task requires significant RAM (e.g., 50MB+), Amorsize calculates:
```
n_jobs = min(physical_cores, available_memory / memory_per_task)
```

**Run:** `python examples/memory_constrained_example.py`

### 2. `intermediate_njobs_demo.py`
Comprehensive demonstration of various scenarios that lead to intermediate n_jobs values.

**Scenarios covered:**
1. Memory constraints
2. Small dataset sizes
3. Overhead vs benefit trade-offs
4. Dataset characteristics

**Run:** `python examples/intermediate_njobs_demo.py`

## When Do Intermediate n_jobs Values Occur?

Amorsize recommends `1 < n_jobs < max_cores` in these situations:

### 1. Memory Constraints (Most Common)

When each worker requires significant memory:

```python
# Example: Each task uses ~500MB
def memory_intensive_task(data):
    large_buffer = allocate_500mb()  # Simulated
    return process(large_buffer, data)

# On a system with:
# - 8 cores
# - 4GB available RAM
# Result: Amorsize recommends 4 workers (not 8)
# Reason: 4GB / 500MB ≈ 8, but leaving headroom → 4 workers
```

**Real-world examples:**
- Image processing with large frame buffers
- Video processing
- Large DataFrame operations
- ML model inference with large models
- Scientific computing with large matrices

### 2. Small Dataset Size

When the dataset is too small to benefit from all cores:

```python
# Example: Processing 50 items on a 16-core machine
data = range(50)
result = optimize(expensive_function, data)
# May recommend 4-8 workers instead of 16
# Reason: Overhead of spawning 16 workers > benefit
```

### 3. Overhead vs Benefit Trade-off

When the function is moderately expensive:

```python
# Function takes ~10ms per item
# Spawning many workers adds overhead
# Sweet spot might be 4-6 workers on a 12-core machine
```

## Memory Calculation Example

Here's how Amorsize calculates memory-limited workers:

```python
from amorsize.system_info import calculate_max_workers

physical_cores = 8
memory_per_task = 500 * 1024 * 1024  # 500 MB

max_workers = calculate_max_workers(physical_cores, memory_per_task)
# With 4GB available RAM:
# available * 0.8 = 3.2GB usable
# 3.2GB / 500MB = 6.4 → 6 workers
# Result: 6 workers (not 8 cores)
```

## Testing Memory Constraints

To see memory constraints in action, you can test with different memory requirements:

### Low Memory (10MB per task)
```python
def low_memory_task(x):
    buffer = [0] * (1_250_000)  # ~10MB
    return process(buffer)

# Result: Likely uses all cores
```

### High Memory (500MB per task)
```python
def high_memory_task(x):
    buffer = [0] * (62_500_000)  # ~500MB
    return process(buffer)

# Result: Limited by available RAM
```

### Very High Memory (1GB per task)
```python
def very_high_memory_task(x):
    buffer = [0] * (125_000_000)  # ~1GB
    return process(buffer)

# Result: May only use 1-2 workers
```

## Expected Behavior

| System RAM | Cores | Memory/Task | Expected n_jobs | Reason |
|------------|-------|-------------|-----------------|---------|
| 16 GB      | 8     | 100 MB      | 8               | RAM sufficient |
| 16 GB      | 8     | 1 GB        | 8               | RAM at limit |
| 16 GB      | 8     | 2 GB        | **4**           | **Memory constrained** |
| 8 GB       | 16    | 500 MB      | **8**           | **Memory constrained** |
| 4 GB       | 8     | 500 MB      | **4**           | **Memory constrained** |
| 32 GB      | 4     | 2 GB        | 4               | Cores are bottleneck |

## Why This Matters

Without memory-aware optimization, spawning too many workers causes:

1. **System Swapping**: Performance drops dramatically as system swaps to disk
2. **OOM Killer**: Operating system kills processes to free memory
3. **System Instability**: Can crash or freeze the system
4. **Worse Performance**: Paradoxically slower than serial execution

## Real-World Example: Image Processing

```python
from amorsize import optimize
from multiprocessing import Pool

def process_4k_image(image_path):
    """
    Process a 4K image (3840x2160).
    Requires ~100MB temporary buffer during processing.
    """
    # Load image (100MB)
    img = load_image(image_path)
    
    # Apply filters (needs temporary buffers)
    img = apply_filters(img)
    
    # Save result
    save_image(img, output_path)
    return output_path

# 1000 images to process
image_paths = [f"img_{i}.jpg" for i in range(1000)]

# Optimize
result = optimize(process_4k_image, image_paths)

# On 8-core system with 8GB RAM:
# Each task needs ~100MB
# Available RAM / Task memory = 8GB / 100MB = 80 tasks
# But we need overhead, so maybe 40-50 concurrent
# Since we have chunks: 8 cores is fine as chunks are processed serially per worker
# Result: Might recommend 6-8 workers (not necessarily all 8)

# Apply recommendations
with Pool(processes=result.n_jobs) as pool:
    results = pool.map(process_4k_image, image_paths, 
                       chunksize=result.chunksize)
```

## Interpreting Results

When you run these examples:

- **n_jobs = max_cores**: System has enough resources
- **1 < n_jobs < max_cores**: **Memory constraint or overhead optimization**
- **n_jobs = 1**: Serial is better (function too fast, dataset too small, or unpicklable)

## Notes

The exact values you see will depend on:
- Your system's available RAM
- Number of physical cores
- Current system load
- Other running processes

The examples are designed to demonstrate the **concept** and **calculation logic** rather than produce specific numbers on every system.

## Key Takeaway

Amorsize doesn't just blindly use all cores. It intelligently determines the **truly optimal** number of workers by considering:

- ✅ Physical cores available
- ✅ Memory constraints
- ✅ Dataset characteristics
- ✅ Function execution time
- ✅ Overhead vs benefit

This prevents common parallelization pitfalls and ensures reliable, efficient execution!
