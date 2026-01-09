# Adaptive Chunking for Heterogeneous Workloads

## Overview

Amorsize now includes **adaptive chunking** that automatically detects workload heterogeneity (varying execution times) and adjusts the chunking strategy for optimal performance. This feature prevents worker idle time and improves load balancing when processing items with significantly different execution times.

## The Problem: Load Imbalance with Fixed Chunking

Traditional parallelization uses **fixed chunking**: all chunks contain the same number of items. This works well when all items take similar time to process (homogeneous workload). However, with heterogeneous workloads, fixed chunking can cause problems:

```
Worker 1: [fast, fast, SLOW, SLOW]  ← Bottleneck (finishes last)
Worker 2: [fast, fast, fast, fast]  ← Idle (waiting for Worker 1)
Worker 3: [fast, fast, fast, fast]  ← Idle (waiting for Worker 1)
Worker 4: [fast, fast, fast, fast]  ← Idle (waiting for Worker 1)
```

**Result**: Workers sit idle while one worker processes slow items, wasting parallelization potential.

## The Solution: Adaptive Chunking

Amorsize automatically:
1. **Measures variability** during sampling using Coefficient of Variation (CV)
2. **Detects heterogeneity** when CV > 0.5
3. **Reduces chunk size** to enable better load distribution
4. **Enables work-stealing** behavior through smaller chunks

With smaller chunks, workers can grab new work as they finish:

```
Worker 1: [fast, SLOW] [fast, SLOW]    ← Can grab more work when done
Worker 2: [fast, fast] [fast, fast]    ← Grabs next available chunk
Worker 3: [fast, SLOW] [fast]          ← Dynamic work distribution
Worker 4: [fast, fast] [SLOW]          ← Better load balance
```

**Result**: Better load balancing, less idle time, improved performance.

## How It Works

### Coefficient of Variation (CV)

CV is a normalized measure of variability:

```
CV = standard_deviation / mean
```

**Interpretation:**
- **CV < 0.3**: Homogeneous workload (consistent execution times)
- **CV 0.3-0.7**: Moderately heterogeneous 
- **CV > 0.7**: Highly heterogeneous (significant variance)

### Automatic Detection

During the dry run sampling phase, Amorsize:
1. Measures execution time for each sample
2. Calculates mean and standard deviation
3. Computes CV = std_dev / mean
4. Flags workload as heterogeneous if CV > 0.5

### Adaptive Chunk Sizing

For heterogeneous workloads:
- **Standard chunksize**: Based on target duration (default: 0.2s)
- **Adaptive reduction**: `chunksize *= max(0.25, 1.0 - CV * 0.5)`

**Examples:**
- CV = 0.3 (homogeneous): No reduction
- CV = 0.5 (moderately heterogeneous): 25% reduction
- CV = 1.0 (highly heterogeneous): 50% reduction
- CV = 1.5+ (extremely heterogeneous): 75% reduction

## Usage

### Basic Usage

```python
from amorsize import optimize

# Your function with varying execution times
def process_document(doc):
    # Some docs are short, others are long
    # Execution time varies significantly
    return analyze(doc)

# Mix of short and long documents
documents = load_documents()

# Amorsize automatically detects heterogeneity and adapts
result = optimize(process_document, documents)

# Use recommended parameters
with Pool(result.n_jobs) as pool:
    results = pool.map(process_document, result.data, chunksize=result.chunksize)
```

### With Diagnostic Profiling

```python
# Enable profiling to see workload analysis
result = optimize(process_document, documents, profile=True)

# Check workload characteristics
print(f"CV: {result.profile.coefficient_of_variation:.3f}")
print(f"Heterogeneous: {result.profile.is_heterogeneous}")
print(f"Recommended chunksize: {result.chunksize}")

# View detailed analysis
print(result.explain())
```

### Verbose Mode

```python
# See real-time analysis during optimization
result = optimize(process_document, documents, verbose=True)

# Output includes:
# - Workload variability: CV=0.85 (heterogeneous)
# - Heterogeneous workload detected (CV=0.85)
# - Reducing chunksize by 42% for better load balancing
```

## Real-World Examples

### Example 1: Document Processing

```python
def process_document(word_count):
    """Process documents of varying lengths."""
    # Longer documents take more time
    processing_time = word_count / 1000  # 1ms per 1000 words
    time.sleep(processing_time)
    return analyze_text(word_count)

# Mix of short (100 words) and long (5000 words) documents
documents = [100, 200, 5000, 150, 4000, 180, 3500, ...]

result = optimize(process_document, documents, profile=True)

# Output:
# CV=1.2 (highly heterogeneous)
# Chunksize reduced from 50 to 20 for load balancing
```

### Example 2: Image Processing

```python
def process_image(size_megapixels):
    """Process images of varying sizes."""
    # Larger images take more time
    processing_time = size_megapixels * 0.1  # 100ms per MP
    time.sleep(processing_time)
    return enhance_image(size_megapixels)

# Mix of small (1MP) and large (20MP) images  
images = [1.0, 2.0, 15.0, 1.5, 18.0, 2.5, 12.0, ...]

result = optimize(process_image, images, profile=True)

# Output:
# CV=0.9 (heterogeneous)
# Chunksize reduced from 30 to 15 for load balancing
```

### Example 3: Mixed Complexity Computation

```python
def compute(complexity):
    """Computation with varying complexity."""
    # Different complexity levels
    time.sleep(0.001 * complexity)
    return sum(i ** 2 for i in range(complexity))

# Mix of simple (complexity=10) and complex (complexity=1000) tasks
tasks = [10, 50, 1000, 20, 800, 30, 500, ...]

result = optimize(compute, tasks, profile=True)

# Output:
# CV=1.5 (extremely heterogeneous)
# Chunksize reduced from 100 to 25 for load balancing
```

## Benefits

### 1. **Automatic Detection**
- No manual analysis required
- Works with any workload type
- Adapts to your specific data

### 2. **Better Performance**
- Reduces worker idle time
- Improves load balancing
- Maximizes parallelization efficiency

### 3. **Transparent**
- CV metric shows workload variability
- Diagnostic profile explains decisions
- Verbose mode shows adaptation in action

### 4. **Zero Overhead**
- CV calculated during existing sampling
- No additional benchmarking
- Negligible performance impact

### 5. **Conservative**
- Only reduces chunks when beneficial
- Maintains standard chunking for homogeneous workloads
- Prevents over-aggressive reduction

## Technical Details

### CV Calculation

```python
# During dry run sampling
times = [t1, t2, t3, t4, t5]  # Measured execution times
mean = sum(times) / len(times)
variance = sum((t - mean)**2 for t in times) / len(times)
std_dev = variance ** 0.5
cv = std_dev / mean
```

### Adaptive Reduction Formula

```python
if cv > 0.5:  # Heterogeneous workload detected
    scale_factor = max(0.25, 1.0 - (cv * 0.5))
    chunksize = int(chunksize * scale_factor)
```

**Scale factor by CV:**
- CV = 0.5 → scale = 0.75 (25% reduction)
- CV = 1.0 → scale = 0.50 (50% reduction)
- CV = 1.5 → scale = 0.25 (75% reduction)
- CV = 2.0+ → scale = 0.25 (75% reduction, capped)

### Integration with Diagnostic Profile

```python
result = optimize(func, data, profile=True)

# Access workload characteristics
result.profile.coefficient_of_variation  # CV value
result.profile.is_heterogeneous          # Boolean flag (CV > 0.5)

# View in explanation
result.explain()
# Shows:
# Workload variability: CV=0.85 (heterogeneous)
# Heterogeneous workload (CV=0.85) - using smaller chunks for load balancing
```

## When to Expect Heterogeneity

### Common Scenarios:

1. **Document/Text Processing**
   - Short vs long documents
   - Simple vs complex content
   - Different languages

2. **Image/Video Processing**
   - Small vs large files
   - Low vs high resolution
   - Different formats/codecs

3. **Database Queries**
   - Simple vs complex queries
   - Small vs large result sets
   - Different table sizes

4. **API Calls**
   - Fast vs slow endpoints
   - Cached vs uncached data
   - Variable network latency

5. **Mathematical Computation**
   - Simple vs complex problems
   - Different input sizes
   - Varying convergence times

## Comparison: Fixed vs Adaptive Chunking

### Homogeneous Workload (CV < 0.3)

**Fixed Chunking:**
- ✓ Works well (consistent times)
- ✓ Efficient (fewer chunks)
- ✓ Low overhead

**Adaptive Chunking:**
- ✓ Maintains standard chunks
- ✓ No reduction applied
- ✓ Same performance as fixed

**Winner**: Tie (both work well)

### Heterogeneous Workload (CV > 0.5)

**Fixed Chunking:**
- ✗ Poor load balance
- ✗ Worker idle time
- ✗ Wasted parallelization

**Adaptive Chunking:**
- ✓ Better load balance
- ✓ Reduced idle time
- ✓ Improved efficiency

**Winner**: Adaptive (significant improvement)

## Best Practices

### 1. **Enable Profiling for Analysis**
```python
result = optimize(func, data, profile=True)
print(f"CV: {result.profile.coefficient_of_variation:.3f}")
```

### 2. **Use Verbose Mode for Debugging**
```python
result = optimize(func, data, verbose=True)
# See CV detection and adaptation in real-time
```

### 3. **Check Heterogeneity Flag**
```python
if result.profile.is_heterogeneous:
    print("Workload has varying execution times")
    print("Smaller chunks used for load balancing")
```

### 4. **Review Diagnostic Report**
```python
print(result.explain())
# Shows complete analysis including:
# - Workload variability (CV)
# - Chunking adaptations
# - Recommendations
```

### 5. **Trust the Adaptation**
- Amorsize automatically handles heterogeneity
- No manual chunk tuning needed
- Adaptation is conservative and safe

## Limitations

1. **Requires Sample Variance**: Needs at least 2 samples to calculate variance (default sample_size=5 is sufficient)

2. **Based on Sample**: CV is estimated from sample, may not reflect entire dataset perfectly (but typically representative)

3. **Conservative Threshold**: CV > 0.5 required to trigger adaptation (prevents false positives)

4. **Minimum Chunksize**: Will not reduce below 1 item per chunk (fundamental limit)

5. **Fixed Data Only**: Cannot determine size for generators (adaptation works, but without total item count)

## FAQ

**Q: Does this slow down optimization?**
A: No. CV is calculated during existing sampling with negligible overhead (< 0.1ms).

**Q: Can I disable adaptive chunking?**
A: Not directly, but it only activates for heterogeneous workloads (CV > 0.5). For homogeneous workloads, standard chunking is used automatically.

**Q: What if my sample isn't representative?**
A: Increase `sample_size` parameter for more accurate CV estimation. Default is 5, try 10-20 for critical workloads.

**Q: Does this work with generators?**
A: Yes! Adaptive chunking works with all data types (lists, ranges, generators).

**Q: How do I verify adaptation occurred?**
A: Use `profile=True` or `verbose=True` to see CV and adaptation messages.

## Summary

Adaptive chunking is a powerful feature that:
- ✓ Automatically detects workload heterogeneity
- ✓ Adjusts chunking for better load balancing
- ✓ Requires no manual intervention
- ✓ Improves performance for heterogeneous workloads
- ✓ Maintains efficiency for homogeneous workloads
- ✓ Provides transparent diagnostics

Just use `optimize()` as normal - Amorsize handles the rest!

## See Also

- `examples/adaptive_chunking_demo.py` - Comprehensive examples
- `tests/test_adaptive_chunking.py` - Test suite
- Diagnostic Profiling documentation
- Core optimization documentation
