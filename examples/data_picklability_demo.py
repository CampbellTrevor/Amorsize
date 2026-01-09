"""
Data Picklability Detection Example

This example demonstrates the safety check that detects unpicklable data items
before recommending parallelization, preventing runtime failures in multiprocessing.Pool.map().

Common unpicklable objects include:
- Thread locks (threading.Lock())
- File handles (open files)
- Database connections
- Network sockets
- Lambdas and local functions in data structures
"""

import threading
from amorsize import optimize


def process_item(x):
    """A simple function that processes dict items."""
    if isinstance(x, dict):
        return x.get("id", 0) * 2
    return x * 2


# Example 1: Picklable Data (Normal Case)
print("=" * 70)
print("Example 1: Normal Case with Picklable Data")
print("=" * 70)

good_data = [
    {"id": 1, "value": 100},
    {"id": 2, "value": 200},
    {"id": 3, "value": 300},
    {"id": 4, "value": 400},
    {"id": 5, "value": 500}
]

result = optimize(process_item, good_data, sample_size=3, verbose=True)
print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
print(f"Reason: {result.reason}")
print()


# Example 2: Unpicklable Data - Thread Lock
print("=" * 70)
print("Example 2: Unpicklable Data (Thread Lock)")
print("=" * 70)

# This is a common mistake: including thread synchronization objects in data
lock = threading.Lock()
bad_data_lock = [
    {"id": 1, "lock": lock},  # Thread locks cannot be pickled
    {"id": 2, "lock": lock},
    {"id": 3, "lock": lock}
]

result = optimize(process_item, bad_data_lock, sample_size=2, verbose=True)
print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
print(f"Reason: {result.reason}")
print(f"Warnings: {result.warnings}")
print()


# Example 3: Unpicklable Data with Profiling
print("=" * 70)
print("Example 3: Detailed Diagnostics with Profiling")
print("=" * 70)

# Using profiling to get detailed explanation
event = threading.Event()
bad_data_event = [1, 2, event, 4, 5, 6, 7, 8, 9, 10]

result = optimize(process_item, bad_data_event, sample_size=5, profile=True)
print(result.explain())
print()


# Example 4: Unpicklable Data - Lambda in Structure
print("=" * 70)
print("Example 4: Lambda Functions in Data (Common Mistake)")
print("=" * 70)

# This is another common mistake: including lambdas in data structures
lambda_func = lambda x: x * 2
bad_data_lambda = [
    {"id": 1, "transform": lambda_func},  # Lambdas cannot be pickled
    {"id": 2, "transform": lambda_func},
    {"id": 3, "transform": lambda_func}
]

result = optimize(process_item, bad_data_lambda, sample_size=2)
print(f"Result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
print(f"Reason: {result.reason}")
print()


# Example 5: File Handles (Another Common Mistake)
print("=" * 70)
print("Example 5: File Handles in Data")
print("=" * 70)

import tempfile

# Creating a file handle in the data is a common mistake
with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
    bad_data_file = [1, 2, f, 4, 5]  # File handles cannot be pickled
    
    result = optimize(process_item, bad_data_file, sample_size=3)
    print(f"Result: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Reason: {result.reason}")
print()


# Example 6: Best Practice - Check Before Production Use
print("=" * 70)
print("Example 6: Best Practice - Pre-flight Check")
print("=" * 70)

print("Always test your data structure with amorsize before production use!")
print("The optimizer will catch pickling issues early, before they cause")
print("runtime failures in multiprocessing.Pool.map().\n")

# Test with a small sample first
test_data = [
    {"id": 1, "data": "test"},
    {"id": 2, "data": "test"},
    {"id": 3, "data": "test"}
]

result = optimize(process_item, test_data, sample_size=2)
if "not picklable" in result.reason.lower():
    print("❌ ERROR: Data contains unpicklable objects!")
    print(f"   {result.reason}")
    print("\nRecommendations:")
    for warning in result.warnings:
        print(f"   - {warning}")
else:
    print("✓ Data is picklable - safe to use with multiprocessing!")
    print(f"   Recommended: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
print()


# Example 7: Solutions for Unpicklable Data
print("=" * 70)
print("Example 7: Solutions for Unpicklable Data")
print("=" * 70)

print("""
If you encounter unpicklable data, here are your options:

1. **Restructure your data**: Remove unpicklable objects
   Bad:  data = [{"id": 1, "lock": threading.Lock()}]
   Good: data = [{"id": 1}]  # Pass IDs, create locks in worker

2. **Use dill or cloudpickle**: More flexible serialization
   >>> import dill
   >>> # Use dill with multiprocessing instead of pickle

3. **Use multiprocessing.Manager**: For shared state
   >>> manager = multiprocessing.Manager()
   >>> shared_lock = manager.Lock()

4. **Serial execution**: Sometimes the safest choice
   >>> result = optimize(func, data)
   >>> if result.n_jobs == 1:
   >>>     # Just use a regular for loop
   >>>     results = [func(item) for item in data]

The optimizer will detect these issues early and recommend serial
execution rather than causing mysterious failures at runtime!
""")
