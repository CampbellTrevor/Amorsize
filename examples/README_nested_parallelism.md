# Nested Parallelism Detection

## Overview

The **Nested Parallelism Detection** feature identifies when your function already uses internal threading or parallelism, which can cause severe performance degradation when combined with multiprocessing.

## The Problem

When you parallelize a function that already uses internal parallelism, you create **thread oversubscription**:

```
Without Detection:
  16 physical cores
  × 8 multiprocessing workers
  × 4 threads per worker (numpy/MKL)
  = 32 threads competing for 16 cores
  Result: ~40-60% slower than serial execution!

With Detection:
  Warning: "Nested parallelism detected"
  Recommendation: Set OMP_NUM_THREADS=1
  Result: Optimal performance
```

## What It Detects

### 1. **Thread Activity**
Monitors thread count before, during, and after function execution:
- Delta > 0: Function creates threads internally
- Example: Simple function = 0 threads, Threaded function = +4 threads

### 2. **Parallel Libraries**
Detects loaded parallel computing libraries:
- numpy (with MKL/OpenBLAS)
- scipy
- numba
- joblib
- multiprocessing.Pool (nested pools!)
- concurrent.futures
- tensorflow/pytorch
- dask

### 3. **Environment Variables**
Checks thread limit settings:
- `OMP_NUM_THREADS` (OpenMP)
- `MKL_NUM_THREADS` (Intel MKL)
- `OPENBLAS_NUM_THREADS` (OpenBLAS)
- `NUMEXPR_NUM_THREADS` (NumExpr)
- `VECLIB_MAXIMUM_THREADS` (macOS Accelerate)
- `NUMBA_NUM_THREADS` (Numba JIT)

## Usage

### Basic Detection

```python
from amorsize import optimize

def my_function(x):
    # Uses numpy/MKL internally
    return np.sum(x ** 2)

data = [np.random.rand(1000) for _ in range(100)]
result = optimize(my_function, data, verbose=True)

# Output:
# WARNING: Nested parallelism detected (thread count increased by 4)
# Detected libraries: numpy
# Consider setting thread limits (OMP_NUM_THREADS=1, MKL_NUM_THREADS=1)

print(result.warnings)
# ['Nested parallelism detected: Function uses internal threading/parallelism (thread count increased by 4). Detected libraries: numpy',
#  'Consider setting thread limits (e.g., OMP_NUM_THREADS=1, MKL_NUM_THREADS=1) to avoid thread oversubscription']
```

### With Diagnostic Profiling

```python
result = optimize(my_function, data, profile=True)

print(result.profile.constraints)
# ['Nested parallelism detected: Function uses internal threading/parallelism...']

print(result.profile.recommendations)
# ['Set environment variables to limit internal threading: OMP_NUM_THREADS=1, MKL_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1',
#  'Or reduce n_jobs to account for internal parallelism (e.g., use n_jobs=cores/internal_threads)']
```

## Solutions

### Solution 1: Limit Internal Threading (Recommended)

**Before importing numpy/scipy:**

```python
import os

# Set thread limits BEFORE imports
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# Now import and use
import numpy as np
from amorsize import optimize

def process(x):
    return np.sum(x ** 2)  # Uses 1 thread

data = [np.random.rand(1000) for _ in range(100)]
result = optimize(process, data)
# No warnings! Safe to use recommended n_jobs
```

**Or in shell before running script:**

```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
python your_script.py
```

### Solution 2: Adjust n_jobs

If you want to keep internal parallelism:

```python
# Function uses 4 threads internally
result = optimize(my_function, data)

if 'nested parallelism' in str(result.warnings).lower():
    # Manually adjust n_jobs
    physical_cores = 16
    internal_threads = 4
    adjusted_n_jobs = physical_cores // internal_threads  # = 4
    
    # Use adjusted value
    from multiprocessing import Pool
    with Pool(adjusted_n_jobs) as pool:
        results = pool.map(my_function, data)
```

### Solution 3: Choose Parallelism Level

Pick ONE level of parallelism:

```python
# Option A: Parallelize outer loop (multiprocessing), sequential inner
os.environ['OMP_NUM_THREADS'] = '1'
import numpy as np

def process(x):
    return np.sum(x ** 2)  # Sequential numpy

result = optimize(process, data)  # Multiprocessing here
```

```python
# Option B: Sequential outer loop, parallelize inner (numpy)
def process_all(data):
    results = []
    for x in data:
        results.append(np.sum(x ** 2))  # Parallel numpy
    return results

# Don't use optimize/multiprocessing - let numpy handle it
results = process_all(data)
```

## Real-World Examples

### Example 1: NumPy/Pandas

```python
import os
os.environ['OMP_NUM_THREADS'] = '1'

import numpy as np
import pandas as pd
from amorsize import optimize

def analyze_data(df_chunk):
    # Pandas/NumPy operations (single-threaded now)
    return df_chunk.groupby('category').agg({'value': 'sum'})

chunks = np.array_split(large_dataframe, 100)
result = optimize(analyze_data, chunks)

# Safe: n_jobs workers × 1 thread each = n_jobs threads total
```

### Example 2: scikit-learn

```python
import os
os.environ['OMP_NUM_THREADS'] = '1'

from sklearn.ensemble import RandomForestClassifier
from amorsize import optimize

def train_model(params):
    # RandomForest uses single thread for BLAS operations
    model = RandomForestClassifier(**params, n_jobs=1)
    model.fit(X_train, y_train)
    return model.score(X_test, y_test)

param_grid = [{'n_estimators': n, 'max_depth': d} 
              for n in [10, 50, 100] for d in [5, 10, 15]]

result = optimize(train_model, param_grid)
# Safe: Each worker trains one model sequentially
```

### Example 3: Image Processing

```python
import os
os.environ['OMP_NUM_THREADS'] = '1'

import cv2  # OpenCV uses OpenMP
from amorsize import optimize

def process_image(image_path):
    img = cv2.imread(image_path)
    # OpenCV operations use 1 thread
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return edges

image_paths = ['img1.jpg', 'img2.jpg', ...]
result = optimize(process_image, image_paths)
# Safe: n_jobs workers processing images in parallel
```

## Technical Details

### Detection Algorithm

1. **Baseline Measurement**
   - Count threads before function execution
   - Typical: 1 main thread

2. **Execution Monitoring**
   - Execute function on sample data
   - Monitor peak thread count during execution
   - Count threads after execution

3. **Library Scanning**
   - Check sys.modules for parallel libraries
   - Check environment variables for thread limits

4. **Decision Logic**
   ```python
   if thread_delta > 0:
       # Explicit thread creation detected
       flag_nested_parallelism()
   elif parallel_libraries and not explicit_thread_limits:
       # Libraries present but not limited
       flag_nested_parallelism()
   ```

### Performance Impact

The detection adds minimal overhead:
- **Time**: ~1-2ms (single extra function call)
- **Memory**: Negligible (stores thread counts)
- **Accuracy**: High for thread creation, heuristic for libraries

### Limitations

1. **Fast Functions**: Very fast functions may complete before threads are detected
2. **Lazy Threading**: Some libraries create threads on first use, not immediately
3. **False Negatives**: Conservative detection may miss some cases
4. **False Positives**: Loading a library doesn't always mean it's used

## Best Practices

### ✅ DO:
- Set thread limits BEFORE importing numpy/scipy
- Check result.warnings for nested parallelism alerts
- Use profile=True for detailed analysis
- Test with and without parallelization
- Monitor actual thread count during execution

### ❌ DON'T:
- Ignore nested parallelism warnings
- Assume "more parallelism = faster"
- Mix multiprocessing + uncontrolled threading
- Skip performance testing
- Use nested multiprocessing.Pool

## Troubleshooting

### "No warnings but performance is bad"

**Check thread count manually:**
```bash
# Run your script
python script.py &

# Monitor threads (Linux)
watch -n 1 "ps -T -p $(pgrep -f script.py) | wc -l"

# If threads >> physical_cores, you have oversubscription
```

### "Warnings but I want internal parallelism"

**Calculate optimal n_jobs:**
```python
import os

physical_cores = int(os.cpu_count() / 2)  # Accounting for hyperthreading
internal_threads = 4  # Your function's thread usage

optimal_n_jobs = max(1, physical_cores // internal_threads)
print(f"Use n_jobs={optimal_n_jobs}")
```

### "Set env vars but still getting warnings"

**Verify they're actually set:**
```python
import os
print(os.environ.get('OMP_NUM_THREADS'))  # Should print '1'
print(os.environ.get('MKL_NUM_THREADS'))  # Should print '1'

# Must be set BEFORE importing numpy
import numpy as np
```

## Integration with Other Features

### With Diagnostic Profiling
```python
result = optimize(func, data, profile=True)
if result.profile.constraints:
    for c in result.profile.constraints:
        if 'nested' in c.lower():
            print(f"Parallelism issue: {c}")
```

### With Adaptive Chunking
Nested parallelism detection is independent of adaptive chunking:
- Heterogeneous workloads → smaller chunks
- Nested parallelism → warnings + recommendations
- Both can occur simultaneously

### With Memory Safety
Multiple safety checks work together:
- Memory constraints limit n_jobs
- Nested parallelism warns about thread oversubscription
- Both protect against resource exhaustion

## See Also

- [Smart Defaults](README_smart_defaults.md) - Automatic measurement configuration
- [Diagnostic Profiling](README_diagnostic_profiling.md) - Detailed analysis
- [Adaptive Chunking](README_adaptive_chunking.md) - Heterogeneous workload handling
- Main [README](../README.md) - General usage guide

## References

- [NumPy Performance Tips](https://numpy.org/doc/stable/reference/generated/numpy.set_num_threads.html)
- [Intel MKL Threading](https://www.intel.com/content/www/us/en/develop/documentation/onemkl-linux-developer-guide/top/managing-performance-and-memory/improving-performance-with-threading.html)
- [OpenMP Environment Variables](https://www.openmp.org/spec-html/5.0/openmpse50.html)
- [Python Multiprocessing Best Practices](https://docs.python.org/3/library/multiprocessing.html)
