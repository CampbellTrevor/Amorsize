"""
Nested Parallelism Detection Demo

This example demonstrates the nested parallelism detection feature,
which warns users when their function already uses internal threading/parallelism.

Nested parallelism can cause:
- Thread oversubscription (too many threads competing for CPU cores)
- Severe performance degradation (parallel code slower than serial)
- Resource contention and system instability
- Potential deadlocks (especially with nested Pool usage)
"""

import threading
import time
import os
from amorsize import optimize


# ============================================================
# Example 1: Simple Function (No Nested Parallelism)
# ============================================================

def simple_computation(x):
    """Pure Python computation with no internal parallelism."""
    result = 0
    for i in range(10000):
        result += x ** 2
    return result


print("=" * 70)
print("Example 1: Simple Function (No Nested Parallelism)")
print("=" * 70)

data = list(range(100))
result = optimize(simple_computation, data, sample_size=5, verbose=True)

print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
print(f"Warnings: {len(result.warnings)}")
for warning in result.warnings:
    print(f"  - {warning}")


# ============================================================
# Example 2: Threaded Function (Nested Parallelism Detected)
# ============================================================

def threaded_computation(x):
    """Function that creates threads internally."""
    result = [0]
    
    def worker():
        for i in range(10000):
            result[0] += x ** 2
    
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    
    return result[0]


print("\n" + "=" * 70)
print("Example 2: Threaded Function (Nested Parallelism Detected)")
print("=" * 70)

data = list(range(100))
result = optimize(threaded_computation, data, sample_size=5, verbose=True)

print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
print(f"Warnings: {len(result.warnings)}")
for warning in result.warnings:
    print(f"  - {warning}")


# ============================================================
# Example 3: Multi-Threaded Function (More Severe Case)
# ============================================================

def multi_threaded_computation(x):
    """Function that creates multiple threads."""
    results = [0] * 4
    threads = []
    
    def worker(idx):
        for i in range(2500):
            results[idx] += x ** 2
    
    for i in range(4):
        thread = threading.Thread(target=worker, args=(i,))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    return sum(results)


print("\n" + "=" * 70)
print("Example 3: Multi-Threaded Function (Severe Thread Oversubscription Risk)")
print("=" * 70)

data = list(range(100))
result = optimize(multi_threaded_computation, data, sample_size=5, verbose=True)

print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
print(f"Warnings: {len(result.warnings)}")
for warning in result.warnings:
    print(f"  - {warning}")


# ============================================================
# Example 4: Using Diagnostic Profile for Detailed Analysis
# ============================================================

print("\n" + "=" * 70)
print("Example 4: Diagnostic Profile with Nested Parallelism Info")
print("=" * 70)

data = list(range(50))
result = optimize(threaded_computation, data, sample_size=5, profile=True)

print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")

if result.profile:
    print("\nConstraints:")
    for constraint in result.profile.constraints:
        print(f"  - {constraint}")
    
    print("\nRecommendations:")
    for rec in result.profile.recommendations:
        print(f"  - {rec}")


# ============================================================
# Example 5: Simulating NumPy/MKL Scenario
# ============================================================

print("\n" + "=" * 70)
print("Example 5: Simulating NumPy/MKL with Thread Environment Variables")
print("=" * 70)

# Check current environment variables
from amorsize.sampling import check_parallel_environment_vars

env_vars = check_parallel_environment_vars()
print(f"Current parallel environment variables: {env_vars}")

if not env_vars:
    print("No thread limit environment variables set.")
    print("If using numpy/scipy with MKL or OpenBLAS, consider setting:")
    print("  export OMP_NUM_THREADS=1")
    print("  export MKL_NUM_THREADS=1")
    print("  export OPENBLAS_NUM_THREADS=1")


# ============================================================
# Example 6: Best Practices for Nested Parallelism
# ============================================================

print("\n" + "=" * 70)
print("Example 6: Best Practices for Handling Nested Parallelism")
print("=" * 70)

print("""
BEST PRACTICES:

1. **Detect Before Parallelizing**
   - Use optimize() with verbose=True to see warnings
   - Check result.warnings for nested parallelism alerts
   - Use profile=True for detailed analysis

2. **Limit Internal Threading**
   - Set environment variables BEFORE importing numpy/scipy:
     export OMP_NUM_THREADS=1
     export MKL_NUM_THREADS=1
     export OPENBLAS_NUM_THREADS=1
   
   - Or set in Python before imports:
     import os
     os.environ['OMP_NUM_THREADS'] = '1'
     os.environ['MKL_NUM_THREADS'] = '1'
     import numpy as np

3. **Adjust n_jobs for Internal Parallelism**
   - If function uses 4 threads internally, use n_jobs = cores / 4
   - Example: 16 cores, function uses 4 threads → n_jobs=4
   - This prevents 16 workers × 4 threads = 64 threads on 16 cores

4. **Choose the Right Parallelism Level**
   - Option A: Parallelize outer loop (multiprocessing), sequential inner
   - Option B: Sequential outer loop, parallelize inner (threading/numpy)
   - Don't mix both unless you know thread_count = cores

5. **Use Diagnostic Profiling**
   - Always check profile.constraints for parallelism warnings
   - Review profile.recommendations for specific guidance
   - Test performance with and without parallelization

6. **Monitor Thread Count**
   - Use tools like htop or top to watch thread count during execution
   - Expected: n_jobs workers × internal_threads per worker
   - If thread_count >> physical_cores, you have oversubscription
""")


# ============================================================
# Example 7: Safe Way to Use NumPy with Amorsize
# ============================================================

print("\n" + "=" * 70)
print("Example 7: Safe Pattern for NumPy/Scientific Libraries")
print("=" * 70)

print("""
SAFE PATTERN:

```python
import os

# Set thread limits BEFORE importing numpy
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
from amorsize import optimize

def process_array(data):
    # NumPy operations will use 1 thread
    return np.sum(data ** 2)

# Now safe to parallelize
data = [np.random.rand(1000) for _ in range(100)]
result = optimize(process_array, data)

# Use multiprocessing with single-threaded NumPy
from multiprocessing import Pool
with Pool(result.n_jobs) as pool:
    results = pool.map(process_array, data, chunksize=result.chunksize)
```

This gives you:
- {n_jobs} parallel workers (multiprocessing)
- Each worker uses 1 thread (NumPy/MKL)
- Total threads = n_jobs (optimal!)
- No oversubscription, maximum performance
""")


print("\n" + "=" * 70)
print("Demo Complete!")
print("=" * 70)
