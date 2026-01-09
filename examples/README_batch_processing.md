# Batch Processing for Memory-Constrained Workloads

## Overview

When `optimize()` warns about excessive memory usage (e.g., "Result memory exceeds safety threshold"), you need a way to process your data without causing Out-Of-Memory (OOM) errors. The `process_in_batches()` function provides an automated solution that:

1. **Divides data into manageable batches**
2. **Optimizes each batch independently**
3. **Processes batches sequentially**
4. **Accumulates results without memory exhaustion**

This is the recommended approach for workloads where function results are large and would otherwise accumulate in RAM beyond safe limits.

## When to Use Batch Processing

Use `process_in_batches()` when:

✅ **Large Return Objects**: Function returns large results (images, dataframes, models)  
✅ **Memory Warnings**: `optimize()` warns about result memory exceeding thresholds  
✅ **OOM Risk**: Processing all data at once would exhaust available RAM  
✅ **Production Safety**: Need guaranteed memory-safe processing  
✅ **Large Datasets**: Processing thousands of items with non-trivial return sizes  

**Don't use batch processing when:**

❌ **Small Results**: Function returns tiny objects (ints, small strings)  
❌ **No Memory Constraints**: Plenty of RAM available for all results  
❌ **Streaming Needed**: Use `imap/imap_unordered` for true streaming instead  

## Quick Start

### Basic Usage

```python
from amorsize import process_in_batches

def expensive_func(x):
    return x ** 2

data = range(10000)

# Process in batches of 1000 items
results = process_in_batches(
    expensive_func,
    data,
    batch_size=1000,
    verbose=True
)

# results contains all 10,000 processed items
print(f"Processed {len(results)} items")
```

### Auto-calculated Batch Size

```python
from amorsize import process_in_batches

# Let the library calculate optimal batch size
results = process_in_batches(
    expensive_func,
    data,
    max_memory_percent=0.5,  # Use max 50% of available RAM
    verbose=True
)
```

## API Reference

### process_in_batches()

```python
def process_in_batches(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    batch_size: Optional[int] = None,
    max_memory_percent: float = 0.5,
    sample_size: int = 5,
    verbose: bool = False,
    **optimize_kwargs
) -> List[Any]
```

**Parameters:**

- **func**: Function to apply to each data item (must be picklable)
- **data**: Input data to process (list, range, iterator)
- **batch_size**: Number of items per batch (if None, auto-calculated)
- **max_memory_percent**: Maximum % of RAM to use per batch (default: 0.5)
- **sample_size**: Items to sample for optimization (default: 5)
- **verbose**: Print progress information (default: False)
- **optimize_kwargs**: Additional args passed to `optimize()` (e.g., `profile=True`)

**Returns:**

- List of all results concatenated from all batches

**Raises:**

- `ValueError`: If parameters are invalid

### estimate_safe_batch_size()

```python
def estimate_safe_batch_size(
    result_size_bytes: int,
    max_memory_percent: float = 0.5
) -> int
```

Helper function to manually calculate safe batch sizes.

**Parameters:**

- **result_size_bytes**: Size of a single result in bytes
- **max_memory_percent**: Maximum % of RAM to use (default: 0.5)

**Returns:**

- Safe batch size (number of items)

## Examples

### Example 1: Image Processing

```python
from amorsize import process_in_batches

def process_image(filepath):
    """Load and process image (returns large result)."""
    from PIL import Image
    img = Image.open(filepath)
    img = img.resize((1920, 1080))
    # Return processed image (large object)
    return img

image_files = glob.glob("images/*.jpg")  # 10,000 images

# Process safely in batches
results = process_in_batches(
    process_image,
    image_files,
    batch_size=100,  # 100 images at a time
    verbose=True
)

print(f"Processed {len(results)} images")
```

### Example 2: Database Records with Large Results

```python
def process_record(record):
    """Transform database record with expensive operations."""
    # Simulate expensive transformation
    transformed = {
        'id': record['id'],
        'features': extract_features(record),  # Returns large array
        'embeddings': calculate_embeddings(record),  # Returns large vector
        'metadata': enrich_metadata(record)
    }
    return transformed

records = load_from_database(limit=100000)

# Auto-calculate batch size based on memory
results = process_in_batches(
    process_record,
    records,
    max_memory_percent=0.3,  # Conservative: use max 30% RAM
    verbose=True
)
```

### Example 3: Manual Batch Size Estimation

```python
from amorsize import estimate_safe_batch_size

# You know each result is ~50MB
result_size = 50 * 1024 * 1024

# Calculate safe batch size
batch_size = estimate_safe_batch_size(
    result_size,
    max_memory_percent=0.5
)

print(f"Safe batch size: {batch_size} items")

# Use calculated batch size
results = process_in_batches(
    my_func,
    my_data,
    batch_size=batch_size,
    verbose=True
)
```

### Example 4: Handling Memory Warnings

```python
from amorsize import optimize, process_in_batches

# First, analyze the workload
opt_result = optimize(expensive_func, data, sample_size=5)

# Check for memory warnings
has_memory_warning = any('memory' in w.lower() for w in opt_result.warnings)

if has_memory_warning:
    print("⚠️  Memory warning detected - using batch processing")
    results = process_in_batches(
        expensive_func,
        data,
        batch_size=100,
        verbose=True
    )
else:
    print("✓ Safe to use normal Pool.map()")
    from multiprocessing import Pool
    with Pool(opt_result.n_jobs) as pool:
        results = pool.map(
            expensive_func,
            opt_result.data,
            chunksize=opt_result.chunksize
        )
```

### Example 5: Progress Tracking

```python
def my_progress_callback(phase, progress):
    print(f"{phase}: {progress*100:.0f}%")

results = process_in_batches(
    expensive_func,
    data,
    batch_size=500,
    progress_callback=my_progress_callback,  # Passed to optimize()
    verbose=True
)
```

### Example 6: With Profiling

```python
# Profile the first batch
results = process_in_batches(
    expensive_func,
    data,
    batch_size=1000,
    profile=True,  # Passed to optimize() for each batch
    verbose=True
)
```

## How It Works

### Memory-Safe Batching Algorithm

1. **Divide Data**: Split input data into batches of size `batch_size`
2. **Optimize Each Batch**: Run `optimize()` on each batch independently
3. **Process Batch**: Execute batch with optimal `n_jobs` and `chunksize`
4. **Accumulate Results**: Collect results in memory (bounded by batch size)
5. **Repeat**: Process next batch, releasing memory from previous batch

### Auto-calculation of Batch Size

When `batch_size=None`:

1. Sample first few items to estimate result size
2. Get available system memory
3. Calculate: `batch_size = (max_memory_percent * available_memory) / result_size`
4. Ensure: `batch_size >= 1` and `batch_size <= total_items`

**Formula:**
```
safe_batch_size = floor((max_memory_percent * available_RAM) / avg_result_size)
```

**Example:**
- Available RAM: 16 GB
- Max memory %: 50% (8 GB)
- Result size: 10 MB
- Safe batch size: 8000 MB / 10 MB = **800 items**

## Performance Characteristics

### Memory Usage

- **Peak Memory**: `batch_size * avg_result_size`
- **Controlled**: Never exceeds `max_memory_percent` of available RAM
- **Safe**: Prevents OOM kills

### Time Overhead

- **Optimization Overhead**: One `optimize()` call per batch (~10-50ms each)
- **Inter-batch Overhead**: Pool creation/destruction (~5-20ms per batch)
- **Total Overhead**: `num_batches * (optimization_time + pool_overhead)`

For 10,000 items with batch_size=1000:
- 10 batches
- ~10ms optimization per batch = 100ms
- ~10ms pool overhead per batch = 100ms  
- **Total overhead: ~200ms** (negligible for expensive functions)

### Scalability

| Dataset Size | Batch Size | Overhead | Notes |
|--------------|------------|----------|-------|
| 100 items | 100 (1 batch) | ~20ms | Minimal |
| 1,000 items | 100 (10 batches) | ~200ms | Low |
| 10,000 items | 500 (20 batches) | ~400ms | Acceptable |
| 100,000 items | 1000 (100 batches) | ~2s | Still reasonable |

## Best Practices

### 1. Choose Appropriate Batch Size

```python
# Too small: High overhead
results = process_in_batches(func, data, batch_size=10)  # 100 batches!

# Too large: Risk of OOM
results = process_in_batches(func, data, batch_size=100000)  # Might OOM!

# Just right: Balance memory and overhead
results = process_in_batches(func, data, batch_size=1000)  # Good balance
```

**Rule of thumb**: Aim for 10-100 batches for large datasets

### 2. Use Auto-calculation for Unknown Result Sizes

```python
# When you don't know result size
results = process_in_batches(
    func,
    data,
    max_memory_percent=0.5  # Let library calculate batch_size
)
```

### 3. Monitor Progress with verbose=True

```python
# See progress for long-running jobs
results = process_in_batches(
    expensive_func,
    large_dataset,
    batch_size=500,
    verbose=True  # Shows batch progress
)
```

### 4. Profile First Batch for Diagnostics

```python
# Understand optimization decisions
results = process_in_batches(
    func,
    data,
    batch_size=1000,
    profile=True,  # Only first batch is profiled
    verbose=True
)
```

### 5. Use Conservative Memory Limits in Production

```python
# Production: Be conservative
results = process_in_batches(
    func,
    data,
    max_memory_percent=0.3,  # Only use 30% RAM
    verbose=True
)

# Development: Can be more aggressive
results = process_in_batches(
    func,
    data,
    max_memory_percent=0.7,  # Use 70% RAM for speed
    verbose=False
)
```

## Limitations

### 1. Sequential Processing

- Batches are processed **sequentially**, not in parallel
- Each batch is internally parallelized (via `optimize()`)
- Can't parallelize across batches (would defeat memory safety)

### 2. Generator Materialization

```python
# Generators are converted to lists (required for batching)
data = (x for x in range(10000))
results = process_in_batches(func, data)  # Converts to list first
```

For true streaming, use `imap/imap_unordered` instead.

### 3. Result Accumulation

- Results are accumulated in memory after processing
- Total memory = sum of all batch results
- If even accumulated results are too large, write results to disk instead

**Alternative for very large outputs:**
```python
# Write results to disk instead of accumulating
for batch_idx in range(num_batches):
    batch_results = process_in_batches(
        func,
        data[batch_idx*batch_size:(batch_idx+1)*batch_size],
        batch_size=batch_size
    )
    save_to_disk(f"results_batch_{batch_idx}.pkl", batch_results)
```

## Comparison with Alternatives

| Approach | Memory Usage | Processing Speed | Use Case |
|----------|--------------|------------------|----------|
| `Pool.map()` | All results in RAM | Fast (one Pool) | Small results |
| `process_in_batches()` | Bounded by batch | Moderate (multiple Pools) | Large results, limited RAM |
| `imap/imap_unordered()` | One result at a time | Fast (streaming) | Streaming needed |
| Manual batching | Custom control | Varies | Complex requirements |

## Troubleshooting

### Problem: Batch size too small, high overhead

**Solution:** Increase batch_size or max_memory_percent

```python
# Before: Too many batches
results = process_in_batches(func, data, batch_size=10)  # 1000 batches!

# After: Fewer batches
results = process_in_batches(func, data, batch_size=500)  # 20 batches
```

### Problem: Still running out of memory

**Solution:** Reduce max_memory_percent or batch_size

```python
# More conservative
results = process_in_batches(
    func,
    data,
    max_memory_percent=0.2  # Only 20% RAM
)
```

### Problem: Very slow processing

**Solution:** Check if function is optimizing correctly

```python
# Add profiling to first batch
results = process_in_batches(
    func,
    data,
    batch_size=1000,
    profile=True,
    verbose=True
)
# Look at "Optimization: n_jobs=X" messages
```

### Problem: Generator consumed before processing

**Solution:** `process_in_batches()` automatically converts generators to lists

```python
# This is fine - handled automatically
data = (expensive_load(i) for i in range(10000))
results = process_in_batches(func, data, batch_size=500)
```

## Related Features

- **[optimize()](../README.md#optimize)**: Analyze optimal parallelization parameters
- **[execute()](README_execute.md)**: One-line optimize + execute
- **[Progress Callbacks](README_progress_callback.md)**: Track optimization progress
- **[Diagnostic Profiling](README_diagnostic_profiling.md)**: Deep analysis of decisions
- **[Large Return Object Detection](README.md#memory-safety)**: Automatic memory warnings

## Summary

`process_in_batches()` provides memory-safe processing for workloads with large return objects:

✅ **Automatic**: Auto-calculates safe batch sizes  
✅ **Safe**: Prevents OOM errors in production  
✅ **Optimized**: Each batch uses optimal parallelization  
✅ **Transparent**: Verbose mode shows progress  
✅ **Flexible**: Manual or automatic batch sizing  

**Key Takeaway**: When `optimize()` warns about memory, use `process_in_batches()` for safe, production-ready processing.
