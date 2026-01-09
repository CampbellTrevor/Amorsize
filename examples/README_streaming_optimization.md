# Streaming Optimization Guide

## Overview

The `optimize_streaming()` function optimizes parameters for **streaming workloads** using `imap` or `imap_unordered`. This is ideal when you need to:

- Process results incrementally without accumulating all results in memory
- Handle very large datasets that don't fit in memory
- Process infinite generators or data streams
- Avoid memory exhaustion from large return objects

## When to Use Streaming vs Batch vs Map

| Approach | Best For | Memory Impact | Processing Style |
|----------|----------|---------------|------------------|
| `optimize() + Pool.map()` | Moderate datasets, need all results at once | **High**: Accumulates all results | Bulk operation |
| `process_in_batches()` | Very large datasets, batch processing | **Medium**: One batch at a time | Sequential batches |
| `optimize_streaming() + imap` | Large/infinite datasets, continuous processing | **Low**: One result at a time | Incremental streaming |

## Basic Usage

```python
from amorsize import optimize_streaming
from multiprocessing import Pool

def expensive_function(x):
    # Your CPU-intensive function
    result = heavy_computation(x)
    return result

# Large dataset
data = range(10000)

# Optimize for streaming
result = optimize_streaming(expensive_function, data, verbose=True)

# Use with imap/imap_unordered
with Pool(result.n_jobs) as pool:
    if result.use_ordered:
        iterator = pool.imap(expensive_function, result.data, chunksize=result.chunksize)
    else:
        iterator = pool.imap_unordered(expensive_function, result.data, chunksize=result.chunksize)
    
    # Process results as they become available
    for item in iterator:
        process_result(item)  # No memory accumulation!
```

## API Reference

### optimize_streaming()

```python
from amorsize import optimize_streaming

result = optimize_streaming(
    func,                              # Function to optimize (must be picklable)
    data,                              # Input data (list, generator, iterator)
    sample_size=5,                     # Items to sample for analysis
    target_chunk_duration=0.2,         # Target seconds per chunk
    prefer_ordered=None,               # True=imap, False=imap_unordered, None=auto
    buffer_size=None,                  # Result buffer size (advanced)
    verbose=False,                     # Print detailed analysis
    use_spawn_benchmark=True,          # Measure actual spawn cost
    use_chunking_benchmark=True,       # Measure actual chunking overhead
    profile=False                      # Enable diagnostic profiling
)
```

**Returns:** `StreamingOptimizationResult` with:
- `n_jobs`: Number of worker processes
- `chunksize`: Items per chunk for imap/imap_unordered
- `use_ordered`: True for imap(), False for imap_unordered()
- `reason`: Explanation of recommendation
- `estimated_speedup`: Expected performance improvement
- `warnings`: List of potential issues
- `data`: Reconstructed data (for generators)
- `profile`: Diagnostic profile (if enabled)

## Key Differences from optimize()

| Feature | optimize() | optimize_streaming() |
|---------|-----------|---------------------|
| **Memory consideration** | Considers result memory accumulation | **No result memory consideration** |
| **Use case** | Pool.map() (all results at once) | imap/imap_unordered (incremental) |
| **Return type** | OptimizationResult | StreamingOptimizationResult |
| **Ordered vs unordered** | Not applicable | Provides guidance |
| **Infinite datasets** | Not suitable | **Suitable** |

## Examples

### Example 1: Basic Streaming

```python
from amorsize import optimize_streaming
from multiprocessing import Pool

def process_item(x):
    # Expensive computation with large return value
    return expensive_operation(x)

# Large dataset
data = range(10000)

# Optimize for streaming
result = optimize_streaming(process_item, data, verbose=True)

# Process with streaming
with Pool(result.n_jobs) as pool:
    if result.use_ordered:
        iterator = pool.imap(process_item, result.data, chunksize=result.chunksize)
    else:
        iterator = pool.imap_unordered(process_item, result.data, chunksize=result.chunksize)
    
    for item in iterator:
        save_to_database(item)  # Process immediately, no accumulation
```

### Example 2: Infinite Data Stream

```python
def data_generator():
    """Infinite data stream."""
    while True:
        yield fetch_from_api()

# Optimize for streaming (generator is consumed for sampling)
result = optimize_streaming(process_item, data_generator(), sample_size=10)

# Process infinite stream
# IMPORTANT: Use result.data (reconstructed generator), not original
with Pool(result.n_jobs) as pool:
    iterator = pool.imap_unordered(
        process_item,
        result.data,  # Use result.data, not original generator!
        chunksize=result.chunksize
    )
    
    for item in iterator:
        handle_result(item)
        # Process continuously, never accumulates in memory
```

**Note:** For generators, always use `result.data` instead of the original generator. The sampling process consumes items from the generator, but `result.data` contains the reconstructed stream with all items intact.

### Example 3: Ordered vs Unordered

```python
# Force ordered results (imap)
result_ordered = optimize_streaming(
    process_item,
    data,
    prefer_ordered=True  # Results arrive in order
)

# Force unordered results (imap_unordered)
result_unordered = optimize_streaming(
    process_item,
    data,
    prefer_ordered=False  # Results arrive as completed (10-20% faster)
)

# Auto-decide based on overhead (recommended)
result_auto = optimize_streaming(
    process_item,
    data,
    prefer_ordered=None  # Automatically chooses based on analysis
)
```

### Example 4: Progress Tracking

```python
from amorsize import optimize_streaming
from multiprocessing import Pool

data = list(range(1000))
total = len(data)

result = optimize_streaming(process_item, data)

with Pool(result.n_jobs) as pool:
    iterator = pool.imap_unordered(
        process_item,
        data,
        chunksize=result.chunksize
    )
    
    processed = 0
    for item in iterator:
        processed += 1
        if processed % 100 == 0:
            print(f"Progress: {processed}/{total} ({processed/total*100:.0f}%)")
```

### Example 5: Diagnostic Profiling

```python
# Enable detailed profiling
result = optimize_streaming(
    process_item,
    data,
    sample_size=10,
    profile=True,
    verbose=True
)

# View detailed explanation
print(result.explain())

# Access structured profile data
if result.profile:
    print(f"Avg execution time: {result.profile.avg_execution_time:.3f}s")
    print(f"Physical cores: {result.profile.physical_cores}")
    print(f"Speedup: {result.profile.estimated_speedup:.2f}x")
```

## Ordered vs Unordered Decision

### imap() - Ordered Results

**Use when:**
- ✅ Result order matters for your application
- ✅ Need to maintain 1:1 correspondence with input order
- ✅ Overhead is minimal (< 20% of execution time)

**Characteristics:**
- Results arrive in input order
- Slightly slower (~10-20% overhead compared to unordered)
- Better for UX when order matters

### imap_unordered() - Unordered Results

**Use when:**
- ✅ Result order doesn't matter
- ✅ Want maximum performance
- ✅ Processing independent items (logs, images, etc.)

**Characteristics:**
- Results arrive as they complete (out of order)
- ~10-20% faster than ordered
- Best for maximum throughput

### Auto-Decision (prefer_ordered=None)

The optimizer automatically chooses based on overhead analysis:
- **High overhead (>20%)** → Use imap_unordered() for better performance
- **Low overhead (<20%)** → Use imap() for better UX

## Memory Safety

Streaming optimization is **memory-safe by design**:

- ✅ No result memory accumulation (processes one at a time)
- ✅ Suitable for functions with large return values
- ✅ Works with infinite or very large datasets
- ✅ No memory warnings (unlike optimize() with large results)

Example:
```python
def process_image(path):
    img = load_image(path)  # 50MB image
    return transform(img)    # 50MB result

# With optimize() + Pool.map()
# Problem: 1000 images × 50MB = 50GB accumulated in memory! 💥

# With optimize_streaming() + imap_unordered()
# Solution: Process one at a time, peak memory = 50MB ✅
result = optimize_streaming(process_image, image_paths)
with Pool(result.n_jobs) as pool:
    for processed_img in pool.imap_unordered(process_image, result.data, result.chunksize):
        save_image(processed_img)  # Save immediately, no accumulation
```

## Integration with Other Features

### With Nested Parallelism Detection

```python
# Auto-adjusts n_jobs if function uses internal threading
result = optimize_streaming(numpy_heavy_function, data, verbose=True)
# Output: "Adjusting n_jobs from 8 to 2 to avoid oversubscription (4 threads per worker)"
```

### With Heterogeneous Workloads

```python
# Automatically adapts chunksize for variable execution times
result = optimize_streaming(
    variable_time_function,
    data,
    sample_size=10,  # Larger sample to detect variability
    profile=True
)
# Smaller chunks for better load balancing when CV > 0.5
```

### With Generators

```python
def data_generator():
    for i in range(10000):
        yield i

# Generator is safely preserved
result = optimize_streaming(process_item, data_generator())

# Use result.data (reconstructed generator) not original
with Pool(result.n_jobs) as pool:
    for item in pool.imap(process_item, result.data, result.chunksize):
        handle(item)
```

## Performance Characteristics

| Metric | Impact |
|--------|--------|
| **Optimization time** | ~50-200ms (includes sampling and benchmarking) |
| **Memory overhead** | Minimal (no result accumulation) |
| **Throughput** | Near-optimal (accounts for all overhead sources) |
| **Speedup accuracy** | Within 10-20% of actual (Amdahl's Law with overhead) |

## Best Practices

### ✅ Do

- Use streaming for large datasets or infinite streams
- Use streaming when results are large (images, models, dataframes)
- Process results immediately (save to database, write to file, etc.)
- Enable verbose mode during development to understand decisions
- Use profile=True to validate optimization decisions

### ❌ Don't

- Don't use streaming if you need all results at once
- Don't accumulate results in a list (defeats the purpose)
- Don't use for very small datasets (< 100 items)
- Don't use for very fast functions (< 1ms per item)

## Troubleshooting

### "Insufficient speedup" - Recommends serial execution

**Cause:** Function is too fast, overhead dominates execution time.

**Solution:**
- Use serial execution for very fast functions
- Or batch multiple operations into a single function call
- Or use regular optimize() if dataset is moderate size

### "Nested parallelism detected"

**Cause:** Function uses internal threading (NumPy, PyTorch, etc.)

**Solution:**
- Set environment variables to limit internal threads:
  ```python
  import os
  os.environ['OMP_NUM_THREADS'] = '1'
  os.environ['MKL_NUM_THREADS'] = '1'
  ```
- Or accept reduced n_jobs (optimizer auto-adjusts)

### Memory still accumulating

**Cause:** Accumulating results instead of processing immediately.

**Solution:**
```python
# ❌ Wrong - accumulates in memory
results = []
for item in iterator:
    results.append(item)  # Memory accumulation!

# ✅ Correct - process immediately
for item in iterator:
    save_to_database(item)  # No accumulation
```

## Comparison Table

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Small dataset (< 1000 items) | `optimize() + Pool.map()` | Simple, results fit in memory |
| Large dataset, moderate results | `optimize() + Pool.map()` | Efficient bulk processing |
| Large dataset, large results | `optimize_streaming() + imap` | Avoid memory exhaustion |
| Infinite or streaming data | `optimize_streaming() + imap` | Only option for continuous streams |
| Very large dataset, need safety | `process_in_batches()` | Memory-safe batch processing |
| Need all results at once | `optimize() + Pool.map()` | Bulk processing, all in memory |
| Process results immediately | `optimize_streaming() + imap` | Incremental, no accumulation |

## See Also

- [Basic Usage Examples](basic_usage.py)
- [Batch Processing Guide](README_batch_processing.md)
- [Diagnostic Profiling Guide](README_diagnostic_profiling.md)
- [Streaming Demo](streaming_optimization_demo.py)
