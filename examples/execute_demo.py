"""
Demonstration of the execute() convenience function.

This example shows how to use execute() to optimize and run parallel workloads
in a single function call, without manually managing multiprocessing.Pool.
"""

from amorsize import execute, optimize
import time


# Example 1: Basic Usage - Simplest Form
print("=" * 70)
print("Example 1: Basic Usage")
print("=" * 70)

def expensive_function(x):
    """Simulate expensive computation."""
    result = 0
    for i in range(1000):
        result += x ** 2 + i
    return result

# Traditional approach requires multiple steps:
# 1. opt_result = optimize(func, data)
# 2. with Pool(opt_result.n_jobs) as pool:
# 3.     results = pool.map(func, opt_result.data, chunksize=opt_result.chunksize)

# With execute(), it's just one line:
data = range(100)
results = execute(expensive_function, data)

print(f"Processed {len(results)} items")
print(f"First result: {results[0]}")
print(f"Last result: {results[-1]}")
print()


# Example 2: With Verbose Output
print("=" * 70)
print("Example 2: With Verbose Output")
print("=" * 70)

data = range(50)
results = execute(expensive_function, data, verbose=True)
print(f"\nGot {len(results)} results")
print()


# Example 3: Getting Optimization Details
print("=" * 70)
print("Example 3: Getting Optimization Details")
print("=" * 70)

data = list(range(80))
results, opt_result = execute(
    expensive_function,
    data,
    return_optimization_result=True
)

print(f"Used n_jobs={opt_result.n_jobs}, chunksize={opt_result.chunksize}")
print(f"Estimated speedup: {opt_result.estimated_speedup}")
print(f"Reason: {opt_result.reason}")
if opt_result.warnings:
    print("Warnings:")
    for warning in opt_result.warnings:
        print(f"  - {warning}")
print()


# Example 4: With Diagnostic Profiling
print("=" * 70)
print("Example 4: With Diagnostic Profiling")
print("=" * 70)

data = list(range(100))
results, opt_result = execute(
    expensive_function,
    data,
    profile=True,
    return_optimization_result=True
)

print(opt_result.explain())
print()


# Example 5: With Progress Callbacks
print("=" * 70)
print("Example 5: With Progress Callbacks")
print("=" * 70)

def progress_bar(phase: str, progress: float):
    """Simple progress bar callback."""
    bar_length = 40
    filled = int(bar_length * progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r[{bar}] {progress*100:5.1f}% - {phase}", end="", flush=True)

data = list(range(150))
results = execute(
    expensive_function,
    data,
    progress_callback=progress_bar
)
print(f"\n\nProcessed {len(results)} items with progress tracking")
print()


# Example 6: Comparison with Manual Pool Management
print("=" * 70)
print("Example 6: Comparison - execute() vs Manual Pool")
print("=" * 70)

from multiprocessing import Pool

data = list(range(100))

# Approach 1: Using execute() - Simple and clean
print("Approach 1: Using execute()")
start = time.time()
results_execute = execute(expensive_function, data)
time_execute = time.time() - start
print(f"  Time: {time_execute:.3f}s")
print(f"  Code: 1 line")
print()

# Approach 2: Manual optimization + Pool - More verbose
print("Approach 2: Manual optimize() + Pool")
start = time.time()
opt_result = optimize(expensive_function, data)
if opt_result.n_jobs == 1:
    results_manual = [expensive_function(x) for x in opt_result.data]
else:
    with Pool(opt_result.n_jobs) as pool:
        results_manual = pool.map(
            expensive_function,
            opt_result.data,
            chunksize=opt_result.chunksize
        )
time_manual = time.time() - start
print(f"  Time: {time_manual:.3f}s")
print(f"  Code: 7+ lines")
print()

# Verify results are identical
assert results_execute == results_manual
print("✓ Both approaches produce identical results")
print(f"✓ execute() saves {(time_manual - time_execute) * 1000:.1f}ms in execution overhead")
print()


# Example 7: Real-World Use Case - Data Processing Pipeline
print("=" * 70)
print("Example 7: Real-World Use Case - Data Processing")
print("=" * 70)

def process_record(record):
    """Simulate processing a data record."""
    # Simulate data validation
    if not isinstance(record, dict):
        record = {"id": record, "value": record}
    
    # Simulate expensive computation
    result = 0
    for i in range(500):
        result += record["value"] ** 2 + i
    
    return {
        "id": record["id"],
        "processed_value": result,
        "timestamp": time.time()
    }

# Generate sample data
raw_data = [{"id": i, "value": i * 10} for i in range(200)]

print("Processing 200 records...")
start = time.time()
processed_records = execute(
    process_record,
    raw_data,
    verbose=False
)
elapsed = time.time() - start

print(f"✓ Processed {len(processed_records)} records in {elapsed:.3f}s")
print(f"  First record: ID={processed_records[0]['id']}, Value={processed_records[0]['processed_value']}")
print(f"  Last record: ID={processed_records[-1]['id']}, Value={processed_records[-1]['processed_value']}")
print(f"  Throughput: {len(processed_records) / elapsed:.1f} records/sec")
print()


# Example 8: When to Use execute() vs optimize()
print("=" * 70)
print("Example 8: When to Use execute() vs optimize()")
print("=" * 70)

print("Use execute() when:")
print("  ✓ You want a simple, one-line solution")
print("  ✓ You don't need to reuse the Pool")
print("  ✓ You want automatic Pool management")
print("  ✓ You're writing quick scripts or prototypes")
print()

print("Use optimize() when:")
print("  ✓ You want to reuse a Pool for multiple operations")
print("  ✓ You need fine-grained control over Pool lifetime")
print("  ✓ You're using imap/imap_unordered for streaming")
print("  ✓ You need to inspect parameters before execution")
print()


# Example 9: Error Handling
print("=" * 70)
print("Example 9: Error Handling")
print("=" * 70)

# execute() validates parameters just like optimize()
try:
    execute(None, [1, 2, 3])  # Invalid function
except ValueError as e:
    print(f"✓ Caught validation error: {e}")

try:
    execute(expensive_function, None)  # Invalid data
except ValueError as e:
    print(f"✓ Caught validation error: {e}")

try:
    execute(expensive_function, [1, 2, 3], sample_size=-1)  # Invalid sample_size
except ValueError as e:
    print(f"✓ Caught validation error: {e}")

print()


# Example 10: Performance Comparison for Different Workloads
print("=" * 70)
print("Example 10: execute() with Different Workload Sizes")
print("=" * 70)

def benchmark_workload(workload_size, func_name):
    """Benchmark execute() with different data sizes."""
    data = range(workload_size)
    start = time.time()
    results, opt_result = execute(
        expensive_function,
        data,
        return_optimization_result=True
    )
    elapsed = time.time() - start
    
    print(f"{func_name:30s}: {len(results):5d} items, "
          f"{opt_result.n_jobs} workers, "
          f"chunksize {opt_result.chunksize:3d}, "
          f"{elapsed:.3f}s, "
          f"{opt_result.estimated_speedup} speedup")

benchmark_workload(10, "Small workload")
benchmark_workload(50, "Medium workload")
benchmark_workload(200, "Large workload")
print()

print("=" * 70)
print("Summary: execute() provides a clean, simple API for optimized")
print("parallel execution without the boilerplate of Pool management.")
print("=" * 70)
