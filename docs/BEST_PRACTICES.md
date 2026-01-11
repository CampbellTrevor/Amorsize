# Amorsize Best Practices Guide

This guide teaches you when and how to use Amorsize effectively for optimal parallelization performance. Follow these proven patterns to get the most out of multiprocessing in Python.

## Table of Contents

- [When to Use Amorsize](#when-to-use-amorsize)
- [When NOT to Parallelize](#when-not-to-parallelize)
- [Function Design Patterns](#function-design-patterns)
- [Data Preparation Strategies](#data-preparation-strategies)
- [Memory Management Techniques](#memory-management-techniques)
- [Performance Optimization Patterns](#performance-optimization-patterns)
- [Real-World Case Studies](#real-world-case-studies)
- [Common Pitfalls to Avoid](#common-pitfalls-to-avoid)
- [System-Specific Considerations](#system-specific-considerations)
- [Optimization Checklist](#optimization-checklist)

---

## When to Use Amorsize

### ✅ Good Use Cases

Amorsize excels when you have:

#### 1. **CPU-Intensive Computations**

Functions that perform heavy calculations without I/O blocking:

```python
from amorsize import optimize

def process_signal(signal_data):
    """CPU-intensive signal processing"""
    # FFT, filtering, convolutions
    fft = np.fft.fft(signal_data)
    filtered = apply_bandpass_filter(fft)
    return np.fft.ifft(filtered)

# Great candidate for parallelization
signals = load_signals()  # List of 1000 signals
result = optimize(process_signal, signals, verbose=True)
```

**Why it works:** Each signal is independent, computation is CPU-bound, minimal data transfer.

#### 2. **Independent Data Items**

Tasks where each item can be processed without depending on others:

```python
def analyze_customer(customer_id):
    """Calculate customer metrics"""
    purchases = get_purchases(customer_id)
    return {
        'ltv': calculate_lifetime_value(purchases),
        'churn_risk': predict_churn(purchases),
        'segment': classify_segment(purchases)
    }

customer_ids = range(100000)
result = optimize(analyze_customer, customer_ids)
```

**Why it works:** No shared state, no dependencies between customers.

#### 3. **Large Datasets with Uniform Processing**

Bulk operations on homogeneous data:

```python
def resize_image(image_path):
    """Resize and optimize image"""
    img = Image.open(image_path)
    img = img.resize((800, 600), Image.LANCZOS)
    return optimize_quality(img)

image_files = glob.glob("photos/*.jpg")  # 10,000 images
result = optimize(resize_image, image_files)
```

**Why it works:** Each image takes similar time, no coordination needed.

#### 4. **Embarrassingly Parallel Problems**

Monte Carlo simulations, parameter sweeps, A/B testing:

```python
def run_simulation(seed):
    """Monte Carlo simulation run"""
    np.random.seed(seed)
    market_prices = simulate_market(days=365)
    portfolio_value = calculate_returns(market_prices)
    return portfolio_value

# Run 10,000 independent simulations
seeds = range(10000)
result = optimize(run_simulation, seeds)
```

**Why it works:** Perfect independence, CPU-bound, minimal communication.

---

## When NOT to Parallelize

### ❌ Poor Use Cases

Avoid parallelization when:

#### 1. **Functions Are Too Fast (< 10ms)**

```python
# ❌ WRONG - Function too fast, overhead dominates
def simple_multiply(x):
    return x * 2

data = range(10000)
result = optimize(simple_multiply, data)
# Amorsize will recommend serial execution
```

**Why it fails:** Process spawning takes 15-200ms. For 1ms functions, overhead is 15-200x the work!

**Solution:** Batch multiple operations or use vectorization:

```python
# ✅ CORRECT - Use NumPy vectorization instead
import numpy as np
data = np.arange(10000)
result = data * 2  # 1000x faster than multiprocessing
```

#### 2. **Shared State or Sequential Dependencies**

```python
# ❌ WRONG - Each calculation depends on previous result
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Cannot parallelize sequential dependency chain
```

**Why it fails:** Parallelism requires independence. Sequential logic cannot be parallelized.

**Solution:** Redesign algorithm or use dynamic programming.

#### 3. **I/O-Bound Tasks (Database, Network, Disk)**

```python
# ❌ WRONG - I/O bound, not CPU bound
def fetch_user_data(user_id):
    time.sleep(0.1)  # Network call
    return requests.get(f"/api/users/{user_id}").json()

# multiprocessing adds overhead without benefit
```

**Why it fails:** I/O blocking doesn't benefit from multiprocessing. Use `asyncio` or threading instead.

**Solution:** Use async/await for I/O:

```python
# ✅ CORRECT - Use asyncio for I/O-bound tasks
import asyncio
import aiohttp

async def fetch_user_data(session, user_id):
    async with session.get(f"/api/users/{user_id}") as response:
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_user_data(session, uid) for uid in user_ids]
        results = await asyncio.gather(*tasks)
```

#### 4. **Small Datasets (< 100 items)**

```python
# ❌ WRONG - Dataset too small
data = range(50)
result = optimize(expensive_function, data)
# Likely recommends serial execution
```

**Why it fails:** Startup overhead (200ms) is large compared to total work time.

**Solution:** Only parallelize when you have enough work:

```python
# Rule of thumb: Total work time should be > 5 seconds
# For 50 items × 10ms each = 500ms → stay serial
# For 1000 items × 10ms each = 10s → parallelize
```

#### 5. **Functions with Large Return Values**

```python
# ❌ WRONG - Returns huge objects
def generate_large_dataframe(params):
    df = pd.DataFrame(np.random.rand(1_000_000, 100))
    return df  # 800MB object!

# Pickling and IPC overhead dominates
```

**Why it fails:** Each 800MB result must be serialized and transferred back. Bottleneck shifts to IPC.

**Solution:** Use batch processing or write directly to disk:

```python
# ✅ CORRECT - Process in batches
from amorsize import process_in_batches

results = process_in_batches(
    generate_large_dataframe,
    params_list,
    batch_size=10,  # Small batches to manage memory
    max_memory_percent=0.6
)
```

---

## Function Design Patterns

### Pattern 1: Pure Functions (Best Practice)

Design functions without side effects:

```python
# ✅ EXCELLENT - Pure function
def calculate_statistics(data: List[float]) -> Dict[str, float]:
    """Pure function: same input → same output, no side effects"""
    return {
        'mean': np.mean(data),
        'std': np.std(data),
        'median': np.median(data)
    }
```

**Benefits:**
- Easy to test
- Safe to parallelize
- No synchronization issues
- Predictable behavior

### Pattern 2: Minimal External Dependencies

Keep external imports inside functions when possible:

```python
# ✅ GOOD - Import inside function for Windows compatibility
def process_document(doc_path):
    import pandas as pd  # Import inside function
    import spacy
    
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(open(doc_path).read())
    return extract_entities(doc)
```

**Why:** On Windows/macOS (spawn), worker processes need to reimport modules. Module-level imports work, but function-level imports can help with pickling issues.

### Pattern 3: Parameter Injection (Avoid Closures)

Pass configuration as parameters, not closures:

```python
# ❌ WRONG - Closure captures external state
threshold = 0.8

def filter_items(item):
    return item.score > threshold  # Captures external variable

# ✅ CORRECT - Pass as parameter
def filter_items(item, threshold=0.8):
    return item.score > threshold

# OR use partial application
from functools import partial

filter_func = partial(filter_items, threshold=0.8)
result = optimize(filter_func, items)
```

### Pattern 4: Error Handling Within Function

Catch exceptions inside worker functions:

```python
# ✅ GOOD - Handle errors gracefully
def safe_process(item):
    try:
        return process(item)
    except ValueError as e:
        # Log error, return sentinel, or raise with context
        return {'error': str(e), 'item': item}

# Better debugging and resilience
result = optimize(safe_process, items)
```

### Pattern 5: Stateless Processing

Avoid maintaining state between calls:

```python
# ❌ WRONG - Maintains state
class Processor:
    def __init__(self):
        self.count = 0  # Mutable state
    
    def process(self, item):
        self.count += 1  # Won't work correctly in parallel!
        return item * self.count

# ✅ CORRECT - Stateless processing
class Processor:
    def __init__(self, multiplier):
        self.multiplier = multiplier  # Immutable configuration
    
    def process(self, item):
        return item * self.multiplier

processor = Processor(multiplier=10)
result = optimize(processor.process, items)
```

---

## Data Preparation Strategies

### Strategy 1: Pre-compute Expensive Lookups

Do expensive operations once before parallelization:

```python
# ✅ EFFICIENT - Pre-compute lookup table
lookup_table = build_expensive_lookup()  # Done once

def process_with_lookup(item):
    # Fast lookup, no recomputation
    key = extract_key(item)
    return lookup_table.get(key, default_value)

result = optimize(process_with_lookup, items)
```

### Strategy 2: Chunk Related Data Together

Group related items for better cache locality:

```python
# ✅ GOOD - Group by category for cache efficiency
items_by_category = defaultdict(list)
for item in all_items:
    items_by_category[item.category].append(item)

# Process each category together
for category, items in items_by_category.items():
    result = optimize(process_category, items)
```

### Strategy 3: Convert Generators to Lists (When Appropriate)

For small-medium datasets, materialize generators:

```python
# If dataset fits in memory
data_generator = read_from_database()

# ✅ OPTION 1 - Let Amorsize handle it
result = optimize(process_func, data_generator)
# Amorsize safely preserves data in result.data

# ✅ OPTION 2 - Materialize explicitly if you need data multiple times
data_list = list(data_generator)
result = optimize(process_func, data_list)
```

### Strategy 4: Filter Before Parallelization

Remove invalid data serially before parallel processing:

```python
# ✅ EFFICIENT - Filter once serially
valid_items = [item for item in all_items if is_valid(item)]

# Then parallelize expensive processing
result = optimize(expensive_process, valid_items)

# vs. filtering in each worker (wasteful)
```

### Strategy 5: Normalize Data Shapes

Ensure uniform processing times:

```python
# ✅ GOOD - Separate by processing time
small_items = [item for item in items if item.size < 1000]
large_items = [item for item in items if item.size >= 1000]

# Process separately with different strategies
result_small = optimize(process, small_items)
result_large = optimize(process, large_items, target_chunk_duration=1.0)
```

---

## Memory Management Techniques

### Technique 1: Estimate Memory Requirements

Calculate memory needs before processing:

```python
from amorsize import estimate_safe_batch_size

def memory_intensive_task(image_path):
    # Each image loads ~50MB
    img = load_image(image_path)
    return process(img)

# Estimate safe batch size
batch_size = estimate_safe_batch_size(
    sample_func=memory_intensive_task,
    sample_data=image_paths[:10],
    max_memory_percent=0.6  # Use max 60% of available RAM
)

print(f"Safe batch size: {batch_size}")
```

### Technique 2: Use Streaming for Large Results

Process and save incrementally:

```python
from amorsize import optimize_streaming

def process_and_save(item):
    result = expensive_computation(item)
    # Save immediately, return small summary
    save_to_disk(result, f"output_{item.id}.pkl")
    return {'id': item.id, 'status': 'success'}

# Streaming optimization for imap/imap_unordered
streaming_result = optimize_streaming(process_and_save, items)

with Pool(streaming_result.n_jobs) as pool:
    summaries = list(pool.imap_unordered(
        process_and_save,
        items,
        chunksize=streaming_result.chunksize
    ))
```

### Technique 3: Clear Memory in Workers

Explicitly free memory after processing:

```python
def process_with_cleanup(item):
    # Load large data
    large_data = load_large_dataset(item)
    
    # Process
    result = compute(large_data)
    
    # Explicitly cleanup before returning
    del large_data
    import gc
    gc.collect()
    
    return result
```

### Technique 4: Use Memory-Mapped Files for Huge Data

Share large read-only data efficiently:

```python
import numpy as np

# Create memory-mapped array (shared, read-only)
shared_data = np.memmap('large_data.dat', dtype='float32', mode='r', shape=(1000000, 1000))

def process_row(row_index):
    # Each worker accesses shared memory without copying
    row = shared_data[row_index]
    return compute(row)

row_indices = range(1000000)
result = optimize(process_row, row_indices)
```

### Technique 5: Monitor Memory Usage

Track memory consumption during development:

```python
from amorsize import validate_system

# Check system resources before processing
validation = validate_system()
print(f"Available memory: {validation.available_memory_gb:.1f} GB")
print(f"Physical cores: {validation.physical_cores}")

if validation.warnings:
    print("Warnings:", validation.warnings)
```

---

## Performance Optimization Patterns

### Pattern 1: Use Diagnostic Profiling

Understand optimization decisions:

```python
from amorsize import optimize

result = optimize(func, data, verbose=True, return_diagnostics=True)

# Examine diagnostic profile
profile = result.diagnostic_profile
print(f"Avg execution time: {profile.avg_execution_time:.6f}s")
print(f"Pickle overhead: {profile.avg_pickle_time:.6f}s")
print(f"Spawn cost: {profile.spawn_cost:.3f}s")
print(f"Estimated speedup: {profile.estimated_speedup:.2f}x")

# Identify bottlenecks
if profile.avg_pickle_time > profile.avg_execution_time:
    print("⚠️  Pickling is slower than execution! Consider reducing data size.")
```

### Pattern 2: Tune for Your Workload

Adjust parameters based on your use case:

```python
# For heterogeneous workloads (varying execution times)
result = optimize(
    func, data,
    target_chunk_duration=0.5,  # Smaller chunks for load balancing
    sample_size=50  # More samples for better estimates
)

# For homogeneous workloads (uniform execution times)
result = optimize(
    func, data,
    target_chunk_duration=2.0,  # Larger chunks reduce overhead
    sample_size=10  # Fewer samples needed
)
```

### Pattern 3: Validate Predictions with Benchmarking

Empirically verify optimizer recommendations:

```python
from amorsize import optimize, validate_optimization

# Get recommendations
result = optimize(func, data)

# Validate with actual execution
validation = validate_optimization(
    func, data,
    predicted_n_jobs=result.n_jobs,
    predicted_chunksize=result.chunksize,
    num_trials=3
)

print(f"Predicted speedup: {result.speedup:.2f}x")
print(f"Actual speedup: {validation.actual_speedup:.2f}x")
print(f"Prediction accuracy: {validation.accuracy:.1f}%")
```

### Pattern 4: Cache Results for Repeated Workloads

Reuse optimization results:

```python
from amorsize import optimize, save_config, load_config

# First run: optimize and save
result = optimize(func, data)
save_config("my_workload", result)

# Later runs: load cached configuration
config = load_config("my_workload")
with Pool(config.n_jobs) as pool:
    results = pool.map(func, data, chunksize=config.chunksize)
```

### Pattern 5: Use Comparison Mode for Algorithm Selection

Compare different approaches:

```python
from amorsize import compare_strategies, ComparisonConfig

# Compare serial, parallel, and parallel with batching
comparison = compare_strategies(
    func, data,
    config=ComparisonConfig(
        include_serial=True,
        include_parallel=True,
        include_batched=True,
        num_trials=3
    )
)

# Automatically selects best strategy
print(f"Best strategy: {comparison.best_strategy}")
print(f"Best time: {comparison.best_time:.2f}s")
```

---

## Real-World Case Studies

### Case Study 1: Image Processing Pipeline

**Scenario:** Resize and watermark 50,000 product images for e-commerce site.

**Initial Approach (Naive):**

```python
# ❌ SUBOPTIMAL - Simple parallelization
from multiprocessing import Pool

def process_image(path):
    img = Image.open(path)
    img = img.resize((800, 600))
    img = add_watermark(img)
    img.save(path.replace('.jpg', '_processed.jpg'))
    return path

with Pool(processes=8) as pool:
    pool.map(process_image, image_paths)
```

**Issues:**
- Used all 8 cores (4 physical, 8 logical with HT)
- Over-subscription caused context switching
- No memory management
- Crashed after 10,000 images (OOM)

**Optimized Approach:**

```python
# ✅ OPTIMIZED - Using Amorsize
from amorsize import process_in_batches

def process_image(path):
    img = Image.open(path)
    img = img.resize((800, 600))
    img = add_watermark(img)
    
    # Save immediately, return small result
    output_path = path.replace('.jpg', '_processed.jpg')
    img.save(output_path)
    
    # Return small object, not the image
    return {'path': output_path, 'status': 'success'}

# Auto-batch with memory management
results = process_in_batches(
    process_image,
    image_paths,
    max_memory_percent=0.6,
    verbose=True
)
```

**Results:**
- **Time:** 45 minutes → 12 minutes (3.75x speedup)
- **Memory:** 32GB peak → 8GB peak (4x reduction)
- **Cores Used:** 8 → 4 physical cores
- **Success Rate:** 100% (no OOM crashes)

**Key Learnings:**
1. Use physical cores, not hyperthreaded
2. Batch processing prevents OOM
3. Return small objects, save large ones
4. Let Amorsize calculate optimal parameters

---

### Case Study 2: Financial Monte Carlo Simulation

**Scenario:** Run 100,000 Monte Carlo simulations for portfolio risk analysis.

**Initial Approach:**

```python
# Took 8 hours on 16-core server
results = [run_simulation(seed) for seed in range(100000)]
```

**Optimized Approach:**

```python
from amorsize import optimize, execute

def run_simulation(seed):
    """Single Monte Carlo simulation"""
    np.random.seed(seed)
    prices = simulate_market(days=252, volatility=0.2)
    portfolio = calculate_portfolio_value(prices)
    return {
        'seed': seed,
        'final_value': portfolio[-1],
        'max_drawdown': calculate_drawdown(portfolio),
        'sharpe_ratio': calculate_sharpe(portfolio)
    }

# Optimize and execute
results = execute(run_simulation, range(100000), verbose=True)
```

**Results:**
- **Time:** 8 hours → 35 minutes (13.7x speedup)
- **Recommendations:** n_jobs=16, chunksize=250
- **Efficiency:** 85.6% (theoretical max: 16x)

**Key Learnings:**
1. Perfect embarrassingly parallel problem
2. Near-linear scaling (85% efficiency)
3. Chunking crucial for reducing overhead
4. `execute()` is simplest for pure compute

---

### Case Study 3: Web Scraping (Anti-Pattern)

**Scenario:** Scrape 10,000 product listings from e-commerce API.

**Attempted with Multiprocessing:**

```python
# ❌ WRONG TOOL - I/O bound, not CPU bound
def scrape_product(url):
    time.sleep(0.5)  # Network latency
    response = requests.get(url)
    return parse_product(response.text)

result = optimize(scrape_product, urls)
# Recommends serial! Parallelization doesn't help I/O
```

**Correct Approach (asyncio):**

```python
# ✅ CORRECT - Use async for I/O bound
import asyncio
import aiohttp

async def scrape_product(session, url):
    async with session.get(url) as response:
        text = await response.text()
        return parse_product(text)

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_product(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

**Results:**
- **multiprocessing:** 10,000 requests × 0.5s = 83 minutes
- **asyncio:** 10,000 requests / 100 concurrent = 50 seconds

**Key Learnings:**
1. Amorsize correctly recommends serial for I/O
2. Use `asyncio` or threading for I/O-bound tasks
3. Multiprocessing is for CPU-bound work only
4. Different problems need different tools

---

### Case Study 4: Data Science Feature Engineering

**Scenario:** Extract 500 features from 1 million text documents.

**Challenge:** Each document takes 50ms (25ms tokenization + 25ms feature extraction).

**Solution:**

```python
from amorsize import optimize
import pandas as pd

def extract_features(doc_id):
    """Extract NLP features from document"""
    text = load_document(doc_id)
    
    # Tokenization and feature extraction
    tokens = tokenize(text)
    features = {
        'word_count': len(tokens),
        'avg_word_length': np.mean([len(w) for w in tokens]),
        'sentiment': analyze_sentiment(text),
        'entities': extract_entities(text),
        'complexity': calculate_complexity(text)
    }
    
    return {'doc_id': doc_id, **features}

# Optimize parameters
result = optimize(extract_features, doc_ids, verbose=True)

# Execute
with Pool(result.n_jobs) as pool:
    features = pool.map(extract_features, doc_ids, chunksize=result.chunksize)

# Convert to DataFrame
df = pd.DataFrame(features)
```

**Results:**
- **Serial time estimate:** 1M × 50ms = 13.9 hours
- **Parallel time (16 cores):** 58 minutes (14.4x speedup)
- **Optimal settings:** n_jobs=16, chunksize=125

**Key Learnings:**
1. NLP processing is CPU-intensive
2. Independent documents = perfect parallelism
3. Chunking reduces function call overhead
4. Return structured data for DataFrame construction

---

## Common Pitfalls to Avoid

### Pitfall 1: Ignoring Amorsize Recommendations

```python
# ❌ DON'T DO THIS
result = optimize(func, data)
# Amorsize says: "Serial execution recommended"

# But you ignore it and parallelize anyway
with Pool(processes=8) as pool:
    results = pool.map(func, data)
# Result: Slower than serial!
```

**Lesson:** Trust the optimizer. If it recommends serial, parallelization will hurt performance.

---

### Pitfall 2: Using Consumed Generators

```python
# ❌ WRONG
data = (x for x in range(1000))
result = optimize(func, data)

# Generator is now consumed!
with Pool(result.n_jobs) as pool:
    results = pool.map(func, data)  # Empty generator!
```

**Solution:**

```python
# ✅ CORRECT
data = (x for x in range(1000))
result = optimize(func, data)

# Use result.data, which preserves the data
with Pool(result.n_jobs) as pool:
    results = pool.map(func, result.data, chunksize=result.chunksize)
```

---

### Pitfall 3: Over-subscribing Cores

```python
# ❌ WRONG - Using all logical cores with hyperthreading
import os
n_jobs = os.cpu_count()  # 16 logical cores (8 physical)

# Over-subscription causes thrashing
with Pool(processes=n_jobs) as pool:
    results = pool.map(func, data)
```

**Solution:**

```python
# ✅ CORRECT - Amorsize uses physical cores
result = optimize(func, data)  # Returns n_jobs=8 (physical cores)
```

---

### Pitfall 4: Not Handling Windows `__main__` Guard

```python
# ❌ WRONG - Missing __main__ guard on Windows
from amorsize import optimize

result = optimize(func, data)
# RuntimeError on Windows: "freeze_support" required
```

**Solution:**

```python
# ✅ CORRECT - Always use __main__ guard
if __name__ == "__main__":
    result = optimize(func, data)
```

---

### Pitfall 5: Parallelizing Setup/Teardown

```python
# ❌ WRONG - Setup in worker function
def process_with_setup(item):
    # This loads model 1000 times (once per item!)
    model = load_heavy_model()
    return model.predict(item)
```

**Solution:**

```python
# ✅ CORRECT - Setup once per worker
def initialize_worker():
    global model
    model = load_heavy_model()

def process(item):
    return model.predict(item)  # Reuses loaded model

with Pool(processes=result.n_jobs, initializer=initialize_worker) as pool:
    results = pool.map(process, items, chunksize=result.chunksize)
```

---

## System-Specific Considerations

### Linux (fork start method)

**Advantages:**
- Fast process spawning (~15ms)
- Copy-on-write memory sharing
- Best performance

**Considerations:**
- Safe for most use cases
- Watch for thread safety if using threads

```python
# Optimal on Linux
result = optimize(func, data)
# Typically recommends more workers due to low spawn cost
```

---

### Windows / macOS (spawn start method)

**Challenges:**
- Slow process spawning (~200ms)
- No copy-on-write
- Requires pickling everything

**Best Practices:**

```python
# Always use __main__ guard
if __name__ == "__main__":
    # Amorsize accounts for higher spawn cost
    result = optimize(func, data)
    # May recommend fewer workers or serial execution
```

**Tips:**
1. Ensure functions are defined at module level
2. Use `if __name__ == "__main__":` guard
3. Expect lower speedups due to spawn cost
4. Consider larger `target_chunk_duration` (e.g., 1.0s)

---

### Docker / Containers

**Challenges:**
- Memory limits may differ from host
- CPU limits via cgroups
- Swap may not be available

**Best Practices:**

```python
# Amorsize detects container limits automatically
from amorsize import validate_system

validation = validate_system()
print(f"Detected memory: {validation.available_memory_gb:.1f}GB")
print(f"Physical cores: {validation.physical_cores}")

# If detection fails, set manually
result = optimize(
    func, data,
    max_workers=4,  # Container CPU limit
)
```

**Tips:**
1. Set container memory limits explicitly: `docker run -m 4g`
2. Don't rely on swap in containers
3. Test optimization in target container
4. Consider using fewer workers than cores in container

---

### High-Performance Computing (HPC)

**Considerations:**
- Many physical cores (64+)
- NUMA architecture
- Batch job systems

**Best Practices:**

```python
# Use load-aware optimization for shared systems
from amorsize import optimize

result = optimize(
    func, data,
    respect_load=True,  # Reduce workers if system is busy
    verbose=True
)
```

**Tips:**
1. Be mindful of other users on shared HPC systems
2. Use SLURM environment variables for core detection
3. Consider NUMA-aware scheduling for large core counts
4. Profile on actual HPC hardware, not laptop

---

## Optimization Checklist

Use this checklist before deploying parallelized code:

### ☐ Design Phase
- [ ] Function is CPU-bound (not I/O-bound)
- [ ] Each data item is independent
- [ ] Function execution time > 10ms per item
- [ ] Dataset has > 100 items
- [ ] Function is picklable (no lambdas/closures)
- [ ] No shared state between calls
- [ ] Error handling inside function

### ☐ Implementation Phase
- [ ] Used `if __name__ == "__main__":` guard
- [ ] Ran `optimize()` to get recommendations
- [ ] Used `result.data` instead of original generator
- [ ] Applied recommended `n_jobs` and `chunksize`
- [ ] Added memory management for large returns
- [ ] Included verbose output for debugging

### ☐ Testing Phase
- [ ] Tested on target platform (Linux/Windows/Mac)
- [ ] Validated with `validate_optimization()`
- [ ] Checked memory usage under load
- [ ] Tested with production data size
- [ ] Verified speedup matches predictions
- [ ] Tested error handling paths

### ☐ Production Phase
- [ ] Monitored memory usage in production
- [ ] Logged optimization decisions
- [ ] Set up alerts for OOM conditions
- [ ] Documented optimization parameters
- [ ] Prepared rollback plan if issues arise

---

## Summary

**Key Takeaways:**

1. **Let Amorsize decide** - Trust optimizer recommendations
2. **CPU-bound only** - Don't parallelize I/O tasks
3. **Pure functions** - Avoid side effects and shared state
4. **Memory matters** - Use batching for large returns
5. **Validate predictions** - Benchmark on real hardware
6. **Platform-aware** - Test on target OS (Windows/Linux/Mac)
7. **Measure first** - Profile before and after optimization

**Quick Decision Guide:**

| Scenario | Recommendation |
|----------|----------------|
| Function < 10ms | Don't parallelize, use vectorization |
| Function 10-100ms | Run `optimize()`, may parallelize |
| Function > 100ms | Excellent candidate for parallelization |
| Dataset < 100 items | Likely stay serial |
| Dataset 100-10K items | Good parallelization opportunity |
| Dataset > 10K items | Excellent parallelization candidate |
| I/O-bound task | Use `asyncio` or threading, not multiprocessing |
| Large returns (>10MB) | Use `process_in_batches()` |
| Windows/macOS | Higher overhead, may need more work per item |

**Remember:** The best optimization is the one that's measured, validated, and works reliably in production.

For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

For API reference, see [README.md](../README.md).
