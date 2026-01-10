# Amorsize

[![CI](https://github.com/CampbellTrevor/Amorsize/actions/workflows/ci.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/ci.yml)
[![Lint](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/lint.yml)
[![Build](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml/badge.svg)](https://github.com/CampbellTrevor/Amorsize/actions/workflows/build.yml)

**Dynamic Parallelism Optimizer & Overhead Calculator**

Amorsize analyzes your Python functions and data to determine the optimal parallelization parameters (`n_jobs` and `chunksize`), preventing "Negative Scaling" where parallelism becomes slower than serial execution.

## Why Amorsize?

**The Problem:** Blindly using `multiprocessing.Pool` with `n_jobs=-1` can make your code *slower* due to overhead from process spawning, memory copying, and inter-process communication.

**The Solution:** Amorsize performs intelligent analysis to tell you:
- ✅ Whether parallelization will help (or hurt)
- ✅ The optimal number of workers for your system
- ✅ The ideal chunk size for your workload
- ✅ Expected speedup vs serial execution

## Features

- 🚀 **Automatic Optimization**: Analyzes function+data and recommends optimal parameters
- 🔍 **Intelligent Sampling**: Quick dry-run analysis without executing full workload
- 💾 **Memory-Aware**: Prevents OOM by considering RAM constraints
- 🖥️ **OS-Aware**: Adjusts for Linux (`fork`) vs Windows/macOS (`spawn`) overhead
- ⚡ **CPU Detection**: Uses physical cores (not hyperthreaded) for best performance
- 🛡️ **Safety Checks**: Validates function picklability and handles edge cases gracefully
- 📦 **Batch Processing**: Memory-safe processing for workloads with large return objects
- 🌊 **Streaming Optimization**: imap/imap_unordered helper for continuous data streams
- 🎯 **CLI Interface**: Analyze functions from command line without writing code
- 🔄 **One-Line Execution**: `execute()` combines optimization and execution seamlessly
- 📊 **Diagnostic Profiling**: Deep insights into optimization decisions and trade-offs
- ✅ **Benchmark Validation**: Empirically verify optimizer predictions with actual performance
- 💾 **Configuration Export/Import**: Save and reuse optimal parameters across runs

## Installation

### From source (development)

```bash
git clone https://github.com/CampbellTrevor/Amorsize.git
cd Amorsize
pip install -e .
```

### With optional dependencies

For enhanced physical core detection:

```bash
pip install -e ".[full]"
```

### Requirements

- Python 3.7+
- Optional: `psutil` for accurate physical core detection (included in `[full]`)

## Quick Start

### Option 1: Command-Line Interface (Fastest to Try)

Analyze or execute functions without writing code:

```bash
# Analyze optimal parameters
python -m amorsize optimize math.factorial --data-range 100

# Execute with automatic optimization
python -m amorsize execute mymodule.process --data-range 1000 --json

# Get detailed profiling
python -m amorsize optimize mymodule.func --data-range 1000 --profile
```

See [CLI Documentation](examples/README_cli.md) for complete guide.

### Option 2: One-Line Execution (Recommended for Python)

```python
from amorsize import execute

def expensive_function(x):
    """Your CPU-intensive function"""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result

# Generate data
data = range(10000)

# Optimize and execute in one line!
results = execute(expensive_function, data, verbose=True)
# That's it! Results contains the output for all 10,000 items
```

### Option 3: Manual Pool Management

For more control, use `optimize()` to get parameters:

```python
from amorsize import optimize
from multiprocessing import Pool

# Get optimization recommendations
result = optimize(expensive_function, data, verbose=True)

print(result)
# Output:
# Recommended: n_jobs=8, chunksize=50
# Reason: Parallelization beneficial: 8 workers with chunks of 50
# Estimated speedup: 6.5x

# Use with multiprocessing
with Pool(processes=result.n_jobs) as pool:
    results = pool.map(expensive_function, result.data, chunksize=result.chunksize)
```

### Option 4: Batch Processing for Memory-Constrained Workloads

When processing functions that return large objects (images, dataframes, models), use batch processing to avoid memory exhaustion:

```python
from amorsize import process_in_batches

def process_image(filepath):
    """Load and process large image"""
    img = load_image(filepath)  # Returns large object
    return transform(img)  # Returns large result

image_files = list_images()  # 10,000 images

# Process safely in batches to prevent OOM
results = process_in_batches(
    process_image,
    image_files,
    batch_size=100,  # Process 100 at a time
    verbose=True
)
```

Or let Amorsize automatically calculate safe batch size:

```python
# Auto-calculate batch size based on available memory
results = process_in_batches(
    process_image,
    image_files,
    max_memory_percent=0.5,  # Use max 50% of RAM
    verbose=True
)
```

See [Batch Processing Guide](examples/README_batch_processing.md) for complete documentation.

### Option 5: Streaming Optimization for Large/Infinite Datasets

For very large datasets or infinite streams, use streaming optimization with `imap`/`imap_unordered`:

```python
from amorsize import optimize_streaming
from multiprocessing import Pool

def process_log_entry(entry):
    """Process log entry with expensive computation"""
    return analyze_and_extract(entry)

# Optimize for streaming (no memory accumulation)
result = optimize_streaming(process_log_entry, log_stream, verbose=True)

# Process with imap/imap_unordered
with Pool(result.n_jobs) as pool:
    if result.use_ordered:
        iterator = pool.imap(process_log_entry, result.data, chunksize=result.chunksize)
    else:
        iterator = pool.imap_unordered(process_log_entry, result.data, chunksize=result.chunksize)
    
    # Process results as they become available (no memory accumulation)
    for item in iterator:
        save_to_database(item)
```

**When to use streaming:**
- ✅ Very large datasets that don't fit in memory
- ✅ Infinite generators or data streams  
- ✅ Processing results incrementally
- ✅ Functions with large return objects

See [Streaming Optimization Guide](examples/README_streaming_optimization.md) for complete documentation.

### Option 6: Benchmark Validation (Verify Predictions)

Want to verify that optimizer recommendations are accurate for your specific system? Use benchmark validation:

```python
from amorsize import validate_optimization, quick_validate

def expensive_func(x):
    """Your computation."""
    return sum(i**2 for i in range(x))

data = range(100, 500)

# Validate optimizer predictions with actual benchmarks
result = validate_optimization(expensive_func, data, verbose=True)

print(result)
# Output:
# === Benchmark Validation Results ===
#
# Performance Measurements:
#   Serial execution time:   2.45s
#   Parallel execution time: 1.32s
#   Actual speedup:          1.85x
#   Predicted speedup:       1.78x
#
# Prediction Accuracy:
#   Accuracy:                96.2%
#   Error:                   +3.9%
#
# ✅ Excellent prediction accuracy!

# For large datasets, use quick validation
result = quick_validate(expensive_func, large_data, sample_size=100)
print(f"Accuracy: {result.accuracy_percent:.1f}%")
```

**When to use benchmark validation:**
- ✅ Before production deployment
- ✅ To verify optimizer accuracy for your system
- ✅ When accuracy is critical
- ✅ To understand system-specific factors

See [Benchmark Validation Guide](examples/README_benchmark_validation.md) for complete documentation.

### Option 7: Configuration Export/Import (Save and Reuse)

Save optimal configurations and reuse them across runs without re-optimizing:

```python
from amorsize import optimize, load_config
from multiprocessing import Pool

# One-time: Find and save optimal configuration
result = optimize(expensive_func, sample_data)
result.save_config('production_config.json', function_name='expensive_func')

# Future runs: Load and use saved configuration (fast!)
config = load_config('production_config.json')
with Pool(config.n_jobs) as pool:
    results = pool.map(expensive_func, data, chunksize=config.chunksize)
```

**CLI Usage:**
```bash
# Save configuration from optimization
python -m amorsize optimize mymodule.func --data-range 1000 \
    --save-config production.json

# Execute with saved config (skips optimization - much faster!)
python -m amorsize execute mymodule.func --data-range 10000 \
    --load-config production.json
```

**When to use saved configurations:**
- ✅ Running same workload repeatedly
- ✅ Deploying to production with consistent hardware
- ✅ Sharing optimal settings across team members
- ✅ Skipping optimization overhead for faster execution

See [Configuration Guide](examples/README_config.md) for complete documentation.

## How It Works

Amorsize uses a 3-step process based on Amdahl's Law:

1. **Dry Run Sampling**: Executes function on small sample (default: 5 items) to measure timing, memory, and serialization costs
2. **Overhead Estimation**: Calculates process spawn costs (OS-dependent) and performs fast-fail checks  
3. **Optimization**: Determines optimal `chunksize` (targets 0.2s/chunk) and `n_jobs` (physical cores, adjusted for memory)

Result: `n_jobs = min(physical_cores, available_RAM / estimated_job_RAM)`

## API Reference

### `optimize(func, data, sample_size=5, target_chunk_duration=0.2, verbose=False)`

Analyzes a function and data to determine optimal parallelization parameters.

**Parameters:**
- `func` (Callable): Function to parallelize (must accept single argument)
- `data` (Iterable): Input data (list, generator, or iterator)
- `sample_size` (int): Items to sample for timing (default: 5)
- `target_chunk_duration` (float): Target seconds per chunk (default: 0.2)
- `verbose` (bool): Print detailed analysis (default: False)

**Returns:**
- `OptimizationResult` with attributes:
  - `n_jobs`: Recommended number of workers
  - `chunksize`: Recommended chunk size
  - `reason`: Explanation of recommendation
  - `estimated_speedup`: Expected performance improvement
  - `warnings`: List of constraints or issues

## Examples & Use Cases

Amorsize includes comprehensive examples in the `examples/` directory:

- **Quick Start**: `basic_usage.py` - Simple examples for common use cases
- **Interactive**: `amorsize_quickstart.ipynb` - Jupyter notebook with drop-in template
- **Real-World**: `dns_entropy_analysis.py` - 120MB log file analysis for security
- **Memory-Constrained**: Multiple examples showing intermediate `n_jobs` values

See [examples/README.md](examples/README.md) for complete documentation.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

All 44 tests cover core functionality, edge cases, and expensive computational scenarios.

## How It Works

Amorsize uses a 3-step process based on Amdahl's Law:

1. **Dry Run Sampling**: Executes function on small sample (default: 5 items) to measure timing, memory, and serialization costs
2. **Overhead Estimation**: Calculates process spawn costs (OS-dependent) and performs fast-fail checks
3. **Optimization**: Determines optimal `chunksize` (targets 0.2s/chunk) and `n_jobs` (physical cores, adjusted for memory)

Result: `n_jobs = min(physical_cores, available_RAM / estimated_job_RAM)`

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Design Document

See [Writeup.md](Writeup.md) for the complete design specification and implementation checklist.
