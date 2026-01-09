# Execute: One-Line Optimized Parallel Execution

## Overview

The `execute()` function is a convenience wrapper that combines `optimize()` and `multiprocessing.Pool` in a single call. It eliminates boilerplate code and makes Amorsize immediately usable for common parallelization tasks.

## The Problem

Using `optimize()` requires manual Pool management:

```python
from multiprocessing import Pool
from amorsize import optimize

# Traditional approach - 7+ lines of boilerplate
opt_result = optimize(expensive_func, data)
if opt_result.n_jobs == 1:
    results = [expensive_func(x) for x in opt_result.data]
else:
    with Pool(opt_result.n_jobs) as pool:
        results = pool.map(
            expensive_func,
            opt_result.data,
            chunksize=opt_result.chunksize
        )
```

This is verbose and error-prone for simple use cases.

## The Solution

`execute()` does everything in one line:

```python
from amorsize import execute

# One-line approach - clean and simple
results = execute(expensive_func, data)
```

## Basic Usage

### Example 1: Simplest Form

```python
from amorsize import execute

def expensive_computation(x):
    result = 0
    for i in range(1000):
        result += x ** 2 + i
    return result

data = range(100)
results = execute(expensive_computation, data)
# Done! Results contains the output for all items
```

### Example 2: With Verbose Output

```python
results = execute(expensive_computation, data, verbose=True)
# Prints:
#   Analyzing function performance...
#   Executing with n_jobs=4, chunksize=25
#   Estimated speedup: 3.2x
#   Execution complete: processed 100 items
```

### Example 3: Getting Optimization Details

```python
results, opt_result = execute(
    expensive_computation,
    data,
    return_optimization_result=True
)

print(f"Used {opt_result.n_jobs} workers")
print(f"Chunksize: {opt_result.chunksize}")
print(f"Speedup: {opt_result.estimated_speedup}")
```

## Features

### Automatic Pool Management

`execute()` handles all Pool lifecycle management:
- Creates Pool with optimal number of workers
- Executes with optimal chunksize
- Closes Pool properly (even on errors)
- Uses direct execution for serial cases (n_jobs=1)

### Parameter Passing

`execute()` accepts all `optimize()` parameters:

```python
results = execute(
    func=my_function,
    data=my_data,
    sample_size=10,              # Sample 10 items for analysis
    target_chunk_duration=0.3,   # Target 0.3s per chunk
    verbose=True,                # Show progress
    use_spawn_benchmark=True,    # Measure spawn cost
    use_chunking_benchmark=True, # Measure chunking overhead
    profile=True,                # Enable profiling
    auto_adjust_for_nested_parallelism=True,  # Auto-adjust n_jobs
    progress_callback=callback   # Progress tracking
)
```

### Two Return Modes

**Default: Results Only**
```python
results = execute(func, data)
# Returns: List[Any]
```

**With Optimization Details**
```python
results, opt_result = execute(func, data, return_optimization_result=True)
# Returns: Tuple[List[Any], OptimizationResult]
```

## Advanced Usage

### With Progress Callbacks

```python
def progress_bar(phase, progress):
    bar_length = 40
    filled = int(bar_length * progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r[{bar}] {progress*100:5.1f}%", end="", flush=True)

results = execute(my_function, data, progress_callback=progress_bar)
```

### With Diagnostic Profiling

```python
results, opt_result = execute(
    my_function,
    data,
    profile=True,
    return_optimization_result=True
)

# Get detailed analysis
print(opt_result.explain())
```

Output:
```
[1] WORKLOAD ANALYSIS
  Function execution time:  5.96ms per item
  Pickle/IPC overhead:      5.4μs per item
  Return object size:       21B
  Total items to process:   500
  Estimated serial time:    2.981s

[2] SYSTEM RESOURCES
  Physical CPU cores:       4
  Process spawn cost:       12.5ms per worker
  Chunking overhead:        450μs per chunk

[3] OPTIMIZATION DECISION
  Max workers (CPU limit):  4
  Optimal chunksize:        33

[4] PERFORMANCE PREDICTION
  Theoretical max speedup:  4.00x
  Estimated actual speedup: 3.2x
  Parallel efficiency:      80.0%
```

### With Generators

`execute()` properly handles generators:

```python
def data_stream():
    """Generator that yields data."""
    for i in range(1000):
        yield i

# Works seamlessly with generators
results = execute(process_item, data_stream())
```

## When to Use execute() vs optimize()

### Use `execute()` when:
- ✅ You want a simple, one-line solution
- ✅ You don't need to reuse the Pool
- ✅ You want automatic Pool management
- ✅ You're writing quick scripts or prototypes
- ✅ You're processing a single dataset

### Use `optimize()` when:
- ✅ You want to reuse a Pool for multiple operations
- ✅ You need fine-grained control over Pool lifetime
- ✅ You're using `imap`/`imap_unordered` for streaming
- ✅ You need to inspect parameters before execution
- ✅ You're integrating with existing Pool-based code

## Real-World Examples

### Example 1: Data Processing Pipeline

```python
from amorsize import execute

def process_record(record):
    """Process a single data record."""
    # Validate
    validated = validate_record(record)
    # Transform
    transformed = transform_data(validated)
    # Enrich
    enriched = enrich_with_metadata(transformed)
    return enriched

# Process 10,000 records with optimal parallelization
raw_data = load_records_from_database()
processed_data = execute(process_record, raw_data, verbose=True)
save_to_database(processed_data)
```

### Example 2: Image Processing

```python
import PIL.Image

def process_image(filepath):
    """Apply filters to an image."""
    img = PIL.Image.open(filepath)
    img = img.resize((800, 600))
    img = img.filter(PIL.ImageFilter.SHARPEN)
    output_path = f"processed_{filepath}"
    img.save(output_path)
    return output_path

# Process all images in a directory
import glob
image_files = glob.glob("images/*.jpg")
processed_paths = execute(process_image, image_files, verbose=True)
print(f"Processed {len(processed_paths)} images")
```

### Example 3: Scientific Computing

```python
import numpy as np

def monte_carlo_simulation(seed):
    """Run Monte Carlo simulation with given seed."""
    np.random.seed(seed)
    samples = np.random.normal(0, 1, 1000000)
    return np.mean(samples), np.std(samples)

# Run 100 independent simulations
seeds = range(100)
results, opt_result = execute(
    monte_carlo_simulation,
    seeds,
    profile=True,
    return_optimization_result=True
)

means = [r[0] for r in results]
stds = [r[1] for r in results]
print(f"Average mean: {np.mean(means):.6f}")
print(f"Average std: {np.mean(stds):.6f}")
print(f"Speedup: {opt_result.estimated_speedup}")
```

### Example 4: Web Scraping

```python
import requests

def fetch_url(url):
    """Fetch and parse a URL."""
    response = requests.get(url, timeout=10)
    return {
        "url": url,
        "status": response.status_code,
        "content_length": len(response.content),
        "title": extract_title(response.text)
    }

# Scrape multiple URLs
urls = [f"https://example.com/page{i}" for i in range(100)]
results = execute(fetch_url, urls, verbose=True)
successful = [r for r in results if r["status"] == 200]
print(f"Successfully fetched {len(successful)}/{len(urls)} pages")
```

## Performance

`execute()` has the same performance as manually using `optimize()` + `Pool`:
- Only overhead is function call (< 0.1ms)
- Pool creation is identical
- Execution uses same optimal parameters
- All optimizations from Amorsize apply

Benchmark comparison:
```python
import time

# Approach 1: execute()
start = time.time()
results = execute(expensive_func, data)
time_execute = time.time() - start

# Approach 2: Manual optimize() + Pool
start = time.time()
opt = optimize(expensive_func, data)
with Pool(opt.n_jobs) as pool:
    results = pool.map(expensive_func, opt.data, chunksize=opt.chunksize)
time_manual = time.time() - start

# Difference: < 1ms
assert abs(time_execute - time_manual) < 0.001
```

## Error Handling

`execute()` validates parameters and provides clear error messages:

```python
# Invalid function
try:
    execute(None, [1, 2, 3])
except ValueError as e:
    print(e)  # "Invalid parameter: func must be callable, got NoneType"

# Invalid data
try:
    execute(my_func, None)
except ValueError as e:
    print(e)  # "Invalid parameter: data must be iterable, got NoneType"

# Invalid sample_size
try:
    execute(my_func, data, sample_size=-1)
except ValueError as e:
    print(e)  # "Invalid parameter: sample_size must be positive, got -1"
```

## Integration with Other Features

### Works with All Amorsize Features

```python
# Nested parallelism detection
import numpy as np

def numpy_computation(x):
    return np.sum(np.random.rand(1000) * x)

results = execute(numpy_computation, range(100), verbose=True)
# Output: "Auto-adjusting n_jobs to account for internal threads..."

# Memory safety warnings
def large_return_function(x):
    return np.zeros((1000, 1000))  # Large array

results = execute(large_return_function, range(100), verbose=True)
# Output: "WARNING: Result memory exceeds safety threshold..."

# Generator safety
def data_generator():
    for i in range(100):
        yield expensive_data(i)

results = execute(process_data, data_generator())
# Generators handled automatically - no data loss
```

## FAQ

**Q: Is execute() faster than optimize() + Pool?**  
A: No, they have identical performance. `execute()` just eliminates boilerplate.

**Q: Can I reuse the Pool across multiple execute() calls?**  
A: No, `execute()` creates a new Pool each time. Use `optimize()` if you need Pool reuse.

**Q: What if I need imap or imap_unordered?**  
A: Use `optimize()` directly for streaming operations. `execute()` uses `Pool.map()`.

**Q: Does execute() work with generators?**  
A: Yes! Generators are automatically handled with no data loss.

**Q: Can I get optimization details without the results?**  
A: Use `optimize()` if you only want parameters. `execute()` always executes.

**Q: What happens if the function fails?**  
A: Pool exceptions propagate normally. Use try/except to handle errors.

## API Reference

```python
def execute(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    verbose: bool = False,
    use_spawn_benchmark: bool = True,
    use_chunking_benchmark: bool = True,
    profile: bool = False,
    auto_adjust_for_nested_parallelism: bool = True,
    progress_callback: Optional[Callable[[str, float], None]] = None,
    return_optimization_result: bool = False
) -> Union[List[Any], Tuple[List[Any], OptimizationResult]]
```

**Parameters:**
- `func`: Function to parallelize (must be picklable)
- `data`: Iterable of input data
- `sample_size`: Number of items to sample (default: 5)
- `target_chunk_duration`: Target duration per chunk (default: 0.2s)
- `verbose`: Print detailed progress (default: False)
- `use_spawn_benchmark`: Measure spawn cost (default: True)
- `use_chunking_benchmark`: Measure chunking overhead (default: True)
- `profile`: Enable diagnostic profiling (default: False)
- `auto_adjust_for_nested_parallelism`: Auto-adjust n_jobs (default: True)
- `progress_callback`: Callback for progress updates (default: None)
- `return_optimization_result`: Return optimization details (default: False)

**Returns:**
- `List[Any]`: Results (default)
- `Tuple[List[Any], OptimizationResult]`: Results and optimization details (if `return_optimization_result=True`)

**Raises:**
- `ValueError`: If parameter validation fails

## Summary

`execute()` provides a clean, simple API for optimized parallel execution:

✅ **One line of code** vs 7+ lines with manual Pool management  
✅ **Automatic optimization** using all Amorsize features  
✅ **No boilerplate** - Pool lifecycle handled automatically  
✅ **Optional details** - Get optimization info when needed  
✅ **Full compatibility** - Works with all Amorsize features  
✅ **Zero overhead** - Same performance as manual approach  

For most use cases, `execute()` is the recommended way to use Amorsize.
