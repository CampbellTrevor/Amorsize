# Performance Cookbook: Quick Reference Guide

**Quick recipes and decision trees for optimizing parallel workloads with Amorsize.**

This cookbook provides copy-paste solutions for common optimization scenarios. Each recipe is battle-tested and includes expected results.

---

## Table of Contents

1. [Decision Trees](#decision-trees)
   - [Should I Parallelize?](#should-i-parallelize)
   - [How Many Workers?](#how-many-workers)
   - [What Chunksize?](#what-chunksize)
2. [Quick Recipes](#quick-recipes)
   - [CPU-Bound Workload](#recipe-cpu-bound-workload)
   - [I/O-Bound Workload](#recipe-io-bound-workload)
   - [Memory-Constrained](#recipe-memory-constrained)
   - [Mixed Workload](#recipe-mixed-workload)
   - [Nested Parallelism](#recipe-nested-parallelism)
3. [Common Patterns](#common-patterns)
   - [Data Processing Pipeline](#pattern-data-processing-pipeline)
   - [API/Web Scraping](#pattern-api-web-scraping)
   - [Image/Video Processing](#pattern-image-video-processing)
   - [ML Feature Engineering](#pattern-ml-feature-engineering)
4. [Troubleshooting Flowcharts](#troubleshooting-flowcharts)
   - [Slower Than Expected](#flowchart-slower-than-expected)
   - [High Memory Usage](#flowchart-high-memory-usage)
   - [Inconsistent Performance](#flowchart-inconsistent-performance)
5. [Performance Checklist](#performance-checklist)

---

## Decision Trees

### Should I Parallelize?

```
START: Is parallelization worth it?
│
├─ Function takes < 1ms per item?
│  └─ ❌ NO: Overhead will dominate → Use serial execution
│
├─ Less than 10 items to process?
│  └─ ❌ NO: Not enough work → Use serial execution
│
├─ Function is I/O-bound (network, disk)?
│  ├─ Yes → ✅ Use threading (not Amorsize) or async
│  └─ No → Continue
│
├─ Function does significant computation (> 10ms per item)?
│  └─ Yes → ✅ YES: Amorsize will likely help
│
├─ Data is already in memory?
│  ├─ No (streaming) → ✅ Use optimize_streaming()
│  └─ Yes → ✅ Use optimize()
│
└─ Unsure? → Run quick_validate() to measure actual speedup
```

**Quick Check:**
```python
from amorsize import quick_validate

# Test if parallelization helps
result = quick_validate(my_function, my_data)
print(f"Speedup: {result.actual_speedup:.2f}x")
print(f"Accuracy: {result.accuracy_percent:.1f}%")
# If actual_speedup < 1.2x, don't parallelize
```

---

### How Many Workers?

```
START: How many workers should I use?
│
├─ CPU-bound workload?
│  └─ Use n_jobs = physical_cores (not logical)
│      └─ Amorsize default ✅
│
├─ Memory-constrained?
│  ├─ Each worker needs > 1GB RAM?
│  │  └─ Use n_jobs = available_memory / per_worker_memory
│  │      └─ Amorsize calculates automatically ✅
│  └─ Not constrained → Continue
│
├─ Shared system (others using CPU)?
│  └─ Use load_aware=True to adjust dynamically
│      └─ optimize(..., load_aware=True)
│
├─ Testing/development?
│  └─ Start with n_jobs=2 for fast iteration
│
└─ Not sure? → Let Amorsize decide (default behavior)
```

**Quick Recipe:**
```python
from amorsize import optimize

# Amorsize automatically selects optimal workers
result = optimize(my_function, my_data)
print(f"Selected: {result.n_jobs} workers")
print(f"Reason: {result.reason}")
```

---

### What Chunksize?

```
START: What chunksize should I use?
│
├─ Function is very fast (< 1ms)?
│  └─ Use large chunks (100-1000 items)
│      └─ Minimize overhead
│
├─ Function is slow (> 100ms)?
│  └─ Use small chunks (1-10 items)
│      └─ Better load balancing
│
├─ Workload is heterogeneous (variable time)?
│  └─ Use adaptive chunking
│      └─ from amorsize import create_adaptive_pool
│
├─ Not sure? → Let Amorsize calculate
│  └─ Target: 0.2s per chunk (optimal balance)
│
└─ Want different target duration?
   └─ optimize(..., target_chunk_duration=0.5)
```

**Quick Recipe:**
```python
from amorsize import optimize

# Fast functions: large chunks
result = optimize(fast_function, data, target_chunk_duration=0.1)

# Slow functions: small chunks  
result = optimize(slow_function, data, target_chunk_duration=0.5)

# Heterogeneous: adaptive
from amorsize import create_adaptive_pool
with create_adaptive_pool(max_workers=4) as pool:
    results = pool.map(variable_function, data)
```

---

## Quick Recipes

### Recipe: CPU-Bound Workload

**Scenario:** Heavy computation, each item takes 10-100ms

```python
from amorsize import optimize, execute

# Data processing function
def process_item(item):
    # CPU-intensive work (e.g., parsing, calculation)
    result = complex_computation(item)
    return result

# Get optimal parameters
data = load_data()  # List of items
result = optimize(process_item, data)

# Execute with optimal settings
results = execute(
    process_item,
    data,
    n_jobs=result.n_jobs,
    chunksize=result.chunksize
)

print(f"Processed {len(data)} items with {result.estimated_speedup:.2f}x speedup")
```

**Expected Results:**
- Speedup: 2-6x (depends on cores)
- CPU usage: 90-100%
- Memory: Stable
- Best for: Data transformation, parsing, computation

---

### Recipe: I/O-Bound Workload

**Scenario:** Network calls, file I/O, database queries

```python
from amorsize import optimize
import concurrent.futures

# I/O-bound function
def fetch_data(url):
    response = requests.get(url)
    return response.json()

urls = [f"https://api.example.com/data/{i}" for i in range(100)]

# ⚠️ For pure I/O, use threading instead of multiprocessing
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_data, urls))

# OR if there's CPU work after I/O:
def fetch_and_process(url):
    data = requests.get(url).json()  # I/O
    return heavy_computation(data)   # CPU

# Now Amorsize helps with the CPU part
result = optimize(fetch_and_process, urls)
```

**Expected Results:**
- Pure I/O: Use threading (10-20x speedup)
- Mixed I/O + CPU: Use Amorsize (2-8x speedup)
- CPU usage: 20-60%
- Network: Saturated

**Note:** Amorsize is optimized for CPU-bound work. For pure I/O, use `threading` or `asyncio`.

---

### Recipe: Memory-Constrained

**Scenario:** Each item generates large results (> 100MB)

```python
from amorsize import optimize, estimate_safe_batch_size

# Memory-intensive function
def process_image(image_path):
    image = load_large_image(image_path)  # 200MB
    processed = apply_filters(image)      # 200MB
    return processed

images = get_image_paths()  # 1000 images

# Amorsize automatically limits workers based on memory
result = optimize(process_image, images)
print(f"Workers: {result.n_jobs} (memory-limited)")

# Or use batching for extreme cases
batch_size = estimate_safe_batch_size(
    result_size_bytes=200 * 1024 * 1024  # 200MB per result
)

from amorsize import process_in_batches
for batch_results in process_in_batches(process_image, images, batch_size):
    save_results(batch_results)
    # Results cleared after each batch
```

**Expected Results:**
- Workers: Limited by RAM (2-4 workers typical)
- Memory: Stays below 80% of available
- Speedup: 1.5-3x (limited by memory)
- Best for: Image/video processing, large data structures

---

### Recipe: Mixed Workload

**Scenario:** Some items fast, some slow (heterogeneous)

```python
from amorsize import create_adaptive_pool

# Variable-time function
def process_item(item):
    if item.type == "simple":
        return fast_process(item)  # 10ms
    else:
        return slow_process(item)  # 500ms

data = load_mixed_data()  # Mix of simple and complex items

# Adaptive chunking adjusts automatically
with create_adaptive_pool(max_workers=4, target_chunk_duration=0.2) as pool:
    results = pool.map(process_item, data)
    
print("Adaptive chunking handled variable workload efficiently")
```

**Expected Results:**
- Speedup: 3-5x (better than fixed chunking)
- Load balancing: Excellent
- Worker utilization: 85-95%
- Best for: Mixed data types, unknown complexity

---

### Recipe: Nested Parallelism

**Scenario:** Your function already uses parallelism internally

```python
from amorsize import optimize

# Function that internally uses parallelism
def train_model(dataset):
    # PyTorch/TensorFlow uses multiple threads internally
    model.fit(dataset, n_jobs=-1)  # Uses all cores internally
    return model

datasets = load_datasets()  # Multiple datasets

# Amorsize detects nested parallelism and adjusts
result = optimize(train_model, datasets)

# Will use fewer workers to avoid oversubscription
print(f"Workers: {result.n_jobs} (adjusted for nested parallelism)")
print(f"Internal threads detected: {result.profile.nested_parallelism_detected}")
```

**Expected Results:**
- Workers: Reduced (e.g., 2 instead of 8)
- Total threads: physical_cores (not workers * internal_threads)
- CPU usage: 90-100% (fully utilized, not oversubscribed)
- Best for: ML training, numerical libraries (NumPy, SciPy)

---

## Common Patterns

### Pattern: Data Processing Pipeline

**Use Case:** CSV processing, data transformation, ETL

```python
from amorsize import optimize, execute
import pandas as pd

# Load data
df = pd.read_csv("large_dataset.csv")
rows = df.to_dict('records')  # Convert to list of dicts

# Define processing function
def process_row(row):
    # Clean data
    row['name'] = row['name'].strip().lower()
    
    # Calculations
    row['total'] = row['price'] * row['quantity']
    
    # Enrichment
    row['category'] = categorize(row)
    
    return row

# Optimize and execute
result = optimize(process_row, rows)
processed_rows = execute(
    process_row,
    rows,
    n_jobs=result.n_jobs,
    chunksize=result.chunksize
)

# Convert back to DataFrame
processed_df = pd.DataFrame(processed_rows)
```

**Performance Tips:**
- ✅ Break DataFrame into rows/chunks before parallelizing
- ✅ Use `to_dict('records')` for serialization
- ✅ Avoid passing large DataFrames to workers (pickle overhead)
- ✅ Consider `dask` for very large datasets (> 10GB)

---

### Pattern: API/Web Scraping

**Use Case:** Fetching data from multiple URLs

```python
import requests
from amorsize import optimize
import time

# Hybrid I/O + CPU function
def scrape_and_parse(url):
    # I/O-bound part
    response = requests.get(url, timeout=5)
    html = response.text
    
    # CPU-bound part (parsing)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract data
    data = {
        'title': soup.find('h1').text,
        'price': parse_price(soup),
        'description': soup.find('div', class_='desc').text
    }
    
    return data

urls = [f"https://example.com/product/{i}" for i in range(100)]

# Optimize (Amorsize handles CPU parsing)
result = optimize(scrape_and_parse, urls[:10])  # Sample first

# Execute with rate limiting
results = []
for url in urls:
    result_item = scrape_and_parse(url)
    results.append(result_item)
    time.sleep(0.1)  # Rate limiting
```

**Performance Tips:**
- ✅ Use connection pooling (`requests.Session()`)
- ✅ Add timeout to avoid hanging
- ✅ Implement retry logic for failures
- ✅ Respect rate limits (consider `from amorsize import with_retry`)
- ⚠️ For pure I/O, use `concurrent.futures.ThreadPoolExecutor`

---

### Pattern: Image/Video Processing

**Use Case:** Batch processing images

```python
from amorsize import optimize, process_in_batches
from PIL import Image

# Image processing function
def process_image(image_path):
    # Load image
    img = Image.open(image_path)
    
    # Resize
    img_resized = img.resize((800, 600))
    
    # Apply filters
    img_filtered = apply_filters(img_resized)
    
    # Save
    output_path = image_path.replace('input', 'output')
    img_filtered.save(output_path)
    
    return output_path

image_paths = glob.glob("input/*.jpg")  # 1000 images

# Optimize (accounts for memory)
result = optimize(process_image, image_paths[:50])  # Sample

# Process in batches to control memory
batch_size = 100
for batch in process_in_batches(
    process_image,
    image_paths,
    batch_size,
    n_jobs=result.n_jobs
):
    print(f"Processed batch of {len(batch)} images")
```

**Performance Tips:**
- ✅ Use batching for large image sets (controls memory)
- ✅ Pre-calculate optimal batch size with `estimate_safe_batch_size()`
- ✅ Consider image format (JPEG faster than PNG)
- ✅ Use PIL/Pillow-SIMD for faster processing
- ⚠️ Monitor memory usage (images can be large)

---

### Pattern: ML Feature Engineering

**Use Case:** Extracting features from data

```python
from amorsize import optimize, execute
import numpy as np

# Feature extraction function
def extract_features(data_point):
    features = {}
    
    # Statistical features
    features['mean'] = np.mean(data_point)
    features['std'] = np.std(data_point)
    features['max'] = np.max(data_point)
    
    # Domain-specific features
    features['custom_1'] = calculate_custom_feature_1(data_point)
    features['custom_2'] = calculate_custom_feature_2(data_point)
    
    return features

# Load data
data = load_training_data()  # List of data points

# Optimize and execute
result = optimize(extract_features, data[:100])  # Sample
features = execute(
    extract_features,
    data,
    n_jobs=result.n_jobs,
    chunksize=result.chunksize
)

# Convert to feature matrix
import pandas as pd
feature_df = pd.DataFrame(features)
```

**Performance Tips:**
- ✅ Use NumPy vectorized operations when possible
- ✅ Avoid loading large models in each worker (load once, share read-only)
- ✅ Cache expensive computations
- ✅ Consider using `joblib` for large numpy arrays (better serialization)

---

## Troubleshooting Flowcharts

### Flowchart: Slower Than Expected

```
START: Parallelization is slower than serial
│
├─ Check speedup estimate
│  └─ result.estimated_speedup < 1.2?
│      └─ ❌ Function too fast → Use serial
│
├─ Check overhead breakdown
│  └─ profile.overhead_spawn > 50%?
│      └─ ❌ Spawn cost dominates → Use more items per chunk
│
├─ Check pickle time
│  └─ profile.avg_pickle_time > profile.avg_execution_time?
│      └─ ❌ Serialization bottleneck → Simplify data or use shared memory
│
├─ Check worker utilization
│  └─ Workers idle most of time?
│      └─ ❌ Not enough work → Use fewer workers or larger chunks
│
├─ Check for nested parallelism
│  └─ profile.nested_parallelism_detected == True?
│      └─ ⚠️ Oversubscription → Reduce n_jobs or internal threads
│
└─ Check data size
    └─ Less than 100 items?
        └─ ❌ Not enough parallelism → Need more data or use serial
```

**Quick Debug:**
```python
from amorsize import optimize

result = optimize(my_function, my_data, verbose=True)

# Check diagnostics
print(f"Estimated speedup: {result.estimated_speedup:.2f}x")
print(f"Spawn overhead: {result.profile.overhead_spawn:.3f}s")
print(f"Pickle time: {result.profile.avg_pickle_time:.6f}s")
print(f"Execution time: {result.profile.avg_execution_time:.6f}s")
print(f"Reason: {result.reason}")

# If still slow, try serial
import time
start = time.time()
serial_results = [my_function(x) for x in my_data]
serial_time = time.time() - start
print(f"Serial time: {serial_time:.2f}s")
```

---

### Flowchart: High Memory Usage

```
START: Memory usage too high or OOM
│
├─ Check item size
│  └─ result.profile.peak_memory_bytes > 100MB per item?
│      └─ ⚠️ Large items → Use batching or reduce workers
│
├─ Check worker count
│  └─ n_jobs * item_size > available_memory?
│      └─ ❌ Too many workers → Reduce n_jobs
│
├─ Check return size
│  └─ profile.return_size_bytes > input size?
│      └─ ⚠️ Large results → Process in batches, don't accumulate
│
├─ Check for memory leaks
│  └─ Memory grows over time?
│      └─ ⚠️ Leak in function → Use `del` or process in smaller batches
│
└─ Use batching
    └─ from amorsize import process_in_batches
```

**Quick Fix:**
```python
from amorsize import optimize, process_in_batches, estimate_safe_batch_size

# Calculate safe batch size based on result size
batch_size = estimate_safe_batch_size(
    result_size_bytes=100 * 1024 * 1024,  # 100MB per result
    max_memory_percent=0.5  # Use 50% of available memory
)

# Process in batches
for batch_results in process_in_batches(
    my_function,
    my_data,
    batch_size,
    n_jobs=2  # Reduce workers
):
    process_batch_results(batch_results)
    # batch_results released after each iteration
```

---

### Flowchart: Inconsistent Performance

```
START: Performance varies between runs
│
├─ Check workload type
│  └─ profile.workload_type == "io_bound"?
│      └─ ⚠️ I/O variance → Use threading or implement retries
│
├─ Check coefficient of variation
│  └─ profile.coefficient_of_variation > 0.5?
│      └─ ⚠️ Heterogeneous workload → Use adaptive chunking
│
├─ Check system load
│  └─ High background CPU usage?
│      └─ ⚠️ Shared system → Use load_aware=True
│
├─ Check start method
│  └─ Windows or macOS (spawn)?
│      └─ ⚠️ Higher overhead → Increase chunksize
│
└─ Check sample size
    └─ Optimized with < 10 samples?
        └─ ⚠️ Poor estimate → Use larger sample_size
```

**Quick Fix:**
```python
from amorsize import optimize

# For heterogeneous workloads
from amorsize import create_adaptive_pool
with create_adaptive_pool(max_workers=4) as pool:
    results = pool.map(variable_function, data)

# For shared systems
result = optimize(my_function, my_data, load_aware=True)

# For better estimates
result = optimize(my_function, my_data, sample_size=100)  # Larger sample
```

---

## Performance Checklist

Before optimizing with Amorsize, verify:

### 1. Function Requirements
- [ ] Function is pickle-able (no lambdas, nested functions without `cloudpickle`)
- [ ] Function is pure (no side effects, thread-safe)
- [ ] Function takes reasonable time (> 1ms per item ideal)
- [ ] Function doesn't internally parallelize (or adjust n_jobs accordingly)

### 2. Data Requirements  
- [ ] Data is in memory (or use `optimize_streaming` for iterators)
- [ ] Data items are pickle-able
- [ ] Data size is reasonable (> 100 items ideal)
- [ ] Data doesn't require excessive memory (< 80% RAM total)

### 3. Performance Expectations
- [ ] Serial execution measured as baseline
- [ ] Expected speedup calculated (not > n_physical_cores)
- [ ] Overhead considered (spawn cost, pickle time)
- [ ] Memory constraints identified

### 4. System Considerations
- [ ] Available CPU cores known (`psutil.cpu_count(logical=False)`)
- [ ] Available memory known (`psutil.virtual_memory().available`)
- [ ] Other processes not heavily using CPU
- [ ] Start method appropriate (fork > forkserver > spawn for speed)

### 5. Validation
- [ ] Run `quick_validate()` to verify speedup
- [ ] Check `result.reason` for optimization decision
- [ ] Monitor actual resource usage during execution
- [ ] Compare wall-clock time with serial execution

---

## Quick Reference Card

### Common Commands

```python
# Basic optimization
from amorsize import optimize, execute
result = optimize(function, data)
results = execute(function, data, n_jobs=result.n_jobs, chunksize=result.chunksize)

# Quick validation
from amorsize import quick_validate
validation = quick_validate(function, data, n_jobs=4)

# Streaming data
from amorsize import optimize_streaming
result = optimize_streaming(function, data_generator())

# Adaptive chunking
from amorsize import create_adaptive_pool
with create_adaptive_pool(max_workers=4) as pool:
    results = pool.map(function, data)

# Memory-safe batching
from amorsize import process_in_batches, estimate_safe_batch_size
batch_size = estimate_safe_batch_size(result_size_bytes=50_000_000)
for batch in process_in_batches(function, data, batch_size):
    process(batch)

# Load-aware optimization
result = optimize(function, data, load_aware=True)

# Custom chunk duration
result = optimize(function, data, target_chunk_duration=0.5)
```

### Key Metrics

```python
result.n_jobs              # Optimal worker count
result.chunksize           # Optimal items per chunk
result.estimated_speedup   # Expected speedup vs serial
result.reason              # Why these parameters chosen

result.profile.avg_execution_time      # Function time per item
result.profile.avg_pickle_time         # Serialization time per item
result.profile.overhead_spawn          # Worker startup cost
result.profile.overhead_chunking       # Chunk management cost
result.profile.peak_memory_bytes       # Memory per item
result.profile.coefficient_of_variation  # Workload uniformity (< 0.3 good)
```

### When to Use What

| Scenario | Solution | Example |
|----------|----------|---------|
| CPU-bound, uniform workload | `optimize()` + `execute()` | Data processing, parsing |
| CPU-bound, variable workload | `create_adaptive_pool()` | Mixed complexity items |
| I/O-bound | `concurrent.futures.ThreadPoolExecutor` | API calls, file I/O |
| Memory-constrained | `process_in_batches()` | Image processing |
| Streaming data | `optimize_streaming()` | Real-time processing |
| Shared system | `optimize(..., load_aware=True)` | Multi-user environments |
| Nested parallelism | Automatic detection & adjustment | ML training, NumPy |

---

## Next Steps

After using this cookbook:

1. **For detailed explanations:** Read [BEST_PRACTICES.md](BEST_PRACTICES.md)
2. **For use case examples:** See [USE_CASE_*.md](README.md#documentation)
3. **For troubleshooting:** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. **For performance tuning:** Read [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md)
5. **For getting started:** Follow [GETTING_STARTED.md](GETTING_STARTED.md)

---

## Contributing

Found a useful recipe not in this cookbook? Please contribute!

1. Test your recipe thoroughly
2. Include expected results and performance tips
3. Add to the appropriate section
4. Submit a pull request

---

**Happy Optimizing! 🚀**
