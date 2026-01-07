# Amorsize

**Dynamic Parallelism Optimizer & Overhead Calculator**

Amorsize is a Python utility that analyzes the cost-benefit ratio of parallelization and returns optimal `n_jobs` and `chunksize` parameters to minimize total execution time. It prevents "Negative Scaling" where parallelism becomes slower than serial execution.

## Features

- 🚀 **Automatic Optimization**: Determines optimal parallelization parameters
- 🔍 **Intelligent Analysis**: Performs heuristic dry-runs without executing full workload
- 💾 **Memory-Aware**: Considers RAM constraints when suggesting worker counts
- 🖥️ **OS-Aware**: Adjusts overhead estimates based on your operating system
- ⚡ **CPU Detection**: Uses physical cores (not hyperthreaded) for optimal performance
- 🛡️ **Safety Checks**: Validates function picklability and handles edge cases

## Installation

```bash
pip install -e .
```

For full functionality with physical core detection:

```bash
pip install -e ".[full]"
```

## Quick Start

```python
from amorsize import optimize

def expensive_function(x):
    """Your CPU-intensive function"""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result

# Generate data
data = range(10000)

# Get optimization recommendations
result = optimize(expensive_function, data, verbose=True)

print(result)
# Output:
# Recommended: n_jobs=8, chunksize=50
# Reason: Parallelization beneficial: 8 workers with chunks of 50
# Estimated speedup: 6.5x

# Use with multiprocessing
from multiprocessing import Pool

with Pool(processes=result.n_jobs) as pool:
    results = pool.map(expensive_function, data, chunksize=result.chunksize)
```

## How It Works

Amorsize follows a systematic approach based on Amdahl's Law:

### 1. Dry Run Sampling
- Executes function on a small sample (default: 5 items)
- Measures average execution time
- Measures return object size for IPC cost estimation
- Tracks peak memory usage

### 2. Overhead Estimation
- Calculates process spawn cost based on OS:
  - Linux: ~0.05s (uses `fork`)
  - Windows/macOS: ~0.2s (uses `spawn`)
- Estimates total execution time
- Performs "Fast Fail" if parallelization overhead would dominate

### 3. Optimization
- **Chunksize**: Targets 0.2s per chunk to amortize IPC overhead
- **Worker Count**: Uses physical cores, adjusted for memory constraints
- **Speedup Estimation**: Provides expected performance improvement

## API Reference

### `optimize(func, data, sample_size=5, target_chunk_duration=0.2, verbose=False)`

Analyzes a function and data to determine optimal parallelization parameters.

**Parameters:**
- `func` (Callable): Function to parallelize. Must accept a single argument.
- `data` (Iterable): Input data (list, generator, or iterator)
- `sample_size` (int): Number of items to sample for timing (default: 5)
- `target_chunk_duration` (float): Target duration per chunk in seconds (default: 0.2)
- `verbose` (bool): Print detailed analysis information (default: False)

**Returns:**
- `OptimizationResult`: Object containing:
  - `n_jobs`: Recommended number of workers
  - `chunksize`: Recommended chunk size
  - `reason`: Explanation of the recommendation
  - `estimated_speedup`: Expected performance improvement
  - `warnings`: List of any warnings or constraints

## Design Principles

### System Constraints
- **Physical vs Logical Cores**: Distinguishes between physical and hyperthreaded cores
- **OS Fork Methods**: Adjusts overhead based on `fork` (Linux) vs `spawn` (Windows/macOS)
- **Memory Ceiling**: Calculates `Max_Workers = min(CPU_Count, Available_RAM / Est_Job_RAM)`

### Workload Constraints
- **Serialization Cost**: Measures pickle size to account for IPC overhead
- **Task Granularity**: Optimizes chunksize to amortize per-task overhead
- **Fast Fail**: Skips parallelization for very fast or small workloads

## Examples

### Example 1: CPU-Bound Task

```python
import numpy as np
from amorsize import optimize

def matrix_operation(size):
    """Expensive matrix computation"""
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    return np.dot(a, b)

data = [100, 200, 300, 400, 500]
result = optimize(matrix_operation, data)
print(f"Use {result.n_jobs} workers with chunksize={result.chunksize}")
```

### Example 2: Generator Input

```python
from amorsize import optimize

def process_item(item):
    return item ** 2 + item ** 3

def data_generator():
    """Lazy data generation"""
    for i in range(100000):
        yield i

result = optimize(process_item, data_generator())
print(result)
```

### Example 3: Too Fast for Parallelization

```python
from amorsize import optimize

def simple_function(x):
    return x * 2

data = range(100)
result = optimize(simple_function, data, verbose=True)
# Will recommend n_jobs=1 due to overhead
```

## Requirements

- Python 3.7+
- Optional: `psutil` for accurate physical core detection

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Implementation Details

Based on the design document in `Writeup.md`, Amorsize implements:
- ✅ Generator handling with `itertools.islice`
- ✅ Picklability checking
- ✅ Physical core detection
- ✅ OS-specific overhead estimation
- ✅ Memory constraint calculation
- ✅ Optimal chunksize calculation
- ✅ Clear error propagation
