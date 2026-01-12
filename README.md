# Amorsize

**Dynamic Parallelism Optimizer & Overhead Calculator**

Amorsize analyzes your Python functions and data to determine the optimal parallelization parameters (`n_jobs` and `chunksize`), preventing "Negative Scaling" where parallelism becomes slower than serial execution.

## 🚀 New to Amorsize?

**[📖 Start Here: 5-Minute Getting Started Guide](docs/GETTING_STARTED.md)**

Learn the basics in 5 minutes with practical examples for data processing, ML, and web scraping!

**[🍳 Performance Cookbook](docs/PERFORMANCE_COOKBOOK.md)** ⭐ - Quick recipes and decision trees for common scenarios!

**[📚 Complete Documentation Index](docs/README.md)** - Find guides for your specific needs (web services, data processing, ML, troubleshooting, and more)

**[💻 Try Interactive Notebooks](examples/notebooks/)** - Hands-on Jupyter tutorials with visualizations!

---

## Why Amorsize?

**The Problem:** Blindly using `multiprocessing.Pool` with `n_jobs=-1` can make your code *slower* due to overhead from process spawning, memory copying, and inter-process communication.

**The Solution:** Amorsize performs intelligent analysis to tell you:
- ✅ Whether parallelization will help (or hurt)
- ✅ The optimal number of workers for your system
- ✅ The ideal chunk size for your workload
- ✅ Expected speedup vs serial execution

## Features

### Core Optimization
- 🚀 **Automatic Optimization**: Analyzes function+data and recommends optimal parameters
- 🔍 **Intelligent Sampling**: Quick dry-run analysis without executing full workload
- 💾 **Memory-Aware**: Prevents OOM by considering RAM constraints
- 🖥️ **OS-Aware**: Adjusts for Linux (`fork`) vs Windows/macOS (`spawn`) overhead
- ⚡ **CPU Detection**: Uses physical cores (not hyperthreaded) for best performance
- 🛡️ **Safety Checks**: Validates function picklability and handles edge cases gracefully

### Execution & Reliability
- 🔄 **One-Line Execution**: `execute()` combines optimization and execution seamlessly
- 🔁 **Retry Logic**: Exponential backoff for handling transient failures (network, rate limits)
- 🔴 **Circuit Breaker**: Prevent cascade failures with automatic failure detection and recovery
- 💾 **Checkpoint/Resume**: Save progress and resume from failures for long-running workloads
- 📮 **Dead Letter Queue**: Collect permanently failed items for inspection, replay, and auditing
- 📦 **Batch Processing**: Memory-safe processing for workloads with large return objects
- 🌊 **Streaming Optimization**: imap/imap_unordered helper for continuous data streams

### Monitoring & Analysis
- 📊 **Diagnostic Profiling**: Deep insights into optimization decisions and trade-offs
- ✅ **Benchmark Validation**: Empirically verify optimizer predictions with actual performance
- 🎯 **CLI Interface**: Analyze functions from command line without writing code
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

### Run the Quickstart Example

After installing, try the interactive example to see Amorsize in action:
```bash
python quickstart_example.py
```

This will demonstrate automatic optimization in ~30 seconds with clear explanations of what's happening!

### Verify Installation

Verify everything works correctly:
```bash
python scripts/verify_installation.py
```

This runs 6 quick checks (~5 seconds) to ensure all core features are functional.

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

### Option 8: Retry Logic for Production Reliability

Handle transient failures (network issues, rate limiting, temporary unavailability) with automatic retry and exponential backoff:

```python
from amorsize import execute, with_retry, RetryPolicy

# Apply retry to individual functions
@with_retry(max_retries=3, initial_delay=0.1)
def fetch_from_api(item_id):
    """Function that may fail transiently."""
    response = requests.get(f"https://api.example.com/{item_id}")
    return response.json()

# Process with automatic parallelization + retry
results = execute(fetch_from_api, item_ids, verbose=True)

# Custom retry policy for production
policy = RetryPolicy(
    max_retries=5,
    initial_delay=0.5,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,  # Prevent thundering herd
    retry_on_exceptions=(ConnectionError, TimeoutError),
    on_retry=lambda exc, attempt, delay: logger.warning(
        f"Retry {attempt} after {delay:.2f}s: {exc}"
    )
)

@with_retry(policy=policy)
def production_function(x):
    return expensive_api_call(x)

results = execute(production_function, data)
```

**Key features:**
- ✅ Exponential backoff (delays: 0.1s → 0.2s → 0.4s → 0.8s...)
- ✅ Jitter to prevent thundering herd effect
- ✅ Selective retry on specific exception types
- ✅ Callback support for logging and monitoring
- ✅ Works seamlessly with parallel execution
- ✅ Zero external dependencies

See [Retry Logic Guide](examples/retry_logic_demo.py) for complete examples.

### Option 9: Circuit Breaker for Preventing Cascade Failures

Protect your system from cascade failures when services are unavailable with automatic circuit breaker pattern:

```python
from amorsize import execute, with_circuit_breaker, CircuitBreakerPolicy

# Apply circuit breaker to protect against failing services
@with_circuit_breaker()
def call_external_service(item):
    """Service that may fail persistently."""
    response = requests.post("https://external-api.com", json=item)
    return response.json()

# Process with automatic parallelization + circuit breaker
results = execute(call_external_service, items, verbose=True)

# Custom circuit breaker policy for production
policy = CircuitBreakerPolicy(
    failure_threshold=5,      # Open circuit after 5 failures
    success_threshold=2,      # Close after 2 successes
    timeout=60.0,             # Try recovery after 60s
    expected_exceptions=(ConnectionError, TimeoutError),
    on_open=lambda count, exc: logger.error(
        f"Circuit opened after {count} failures: {exc}"
    ),
    on_close=lambda: logger.info("Circuit closed - service recovered")
)

@with_circuit_breaker(policy)
def protected_service(x):
    return external_api_call(x)

results = execute(protected_service, data)
```

**Key features:**
- ✅ Automatic failure detection and circuit opening
- ✅ Periodic recovery testing (HALF_OPEN state)
- ✅ Prevents overwhelming failing services
- ✅ Selective exception handling
- ✅ Shared circuits across multiple functions
- ✅ Integration with retry logic for layered protection
- ✅ Zero external dependencies

**Circuit Breaker States:**
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service failing, requests blocked immediately
- **HALF_OPEN**: Testing recovery, limited requests allowed

**Combine with Retry for Robust Error Handling:**
```python
from amorsize import with_retry, with_circuit_breaker, RetryPolicy, CircuitBreakerPolicy

breaker = CircuitBreaker(CircuitBreakerPolicy(failure_threshold=5))

# Retry handles transient failures, circuit breaker handles persistent failures
@with_circuit_breaker(breaker)
@with_retry(policy=RetryPolicy(max_retries=2))
def robust_api_call(item):
    return api_call(item)

results = execute(robust_api_call, data)
```

See [Circuit Breaker Guide](examples/circuit_breaker_demo.py) for complete examples.

### Option 10: Checkpoint/Resume for Long-Running Workloads

Save progress during execution and resume from failures without losing work:

```python
from amorsize import CheckpointManager, CheckpointPolicy, get_pending_items, merge_results

# Configure checkpointing
policy = CheckpointPolicy(
    checkpoint_dir="./checkpoints",
    checkpoint_interval=100,  # Checkpoint every 100 items
    save_format="pickle",     # or "json" for human-readable
    keep_history=2,           # Keep 2 old versions
    auto_cleanup=True         # Delete on success
)

manager = CheckpointManager(policy)
checkpoint_name = "my_long_task"

def expensive_computation(x):
    """Long-running computation that might fail."""
    # ... expensive work ...
    return result

# First run (may fail partway through)
data = list(range(10000))
checkpoint_state = None
completed_indices = []
results = []

try:
    for i, item in enumerate(data):
        result = expensive_computation(item)
        completed_indices.append(i)
        results.append(result)
        
        # Checkpoint periodically
        if (i + 1) % 100 == 0:
            from amorsize import CheckpointState
            import time
            
            state = CheckpointState(
                completed_indices=completed_indices.copy(),
                results=results.copy(),
                total_items=len(data),
                checkpoint_time=time.time(),
                n_jobs=4,
                chunksize=10,
                metadata={"phase": "processing"}
            )
            manager.save_checkpoint(checkpoint_name, state)
except Exception as e:
    print(f"Failed after {len(completed_indices)} items")

# Second run (resume from checkpoint)
checkpoint_state = manager.load_checkpoint(checkpoint_name)

if checkpoint_state:
    # Get only the pending items
    pending_indices, pending_items = get_pending_items(data, checkpoint_state)
    
    # Process only what's left
    new_results = [expensive_computation(item) for item in pending_items]
    
    # Merge with checkpointed results
    final_results = merge_results(
        new_results, pending_indices, checkpoint_state, len(data)
    )
    
    # Success - cleanup checkpoint
    manager.delete_checkpoint(checkpoint_name)
```

**Key features:**
- ✅ Save progress during execution
- ✅ Resume from last checkpoint on failure
- ✅ JSON (readable) or Pickle (efficient) formats
- ✅ Automatic versioning and history management
- ✅ Thread-safe concurrent operations
- ✅ Zero external dependencies

**Use cases:**
- Long-running batch jobs (hours/days of computation)
- Expensive API calls or ML inference
- Unreliable environments (spot instances, network issues)
- Development/debugging with iterative workflows

**JSON vs Pickle:**
- **JSON**: Human-readable, limited to JSON-serializable objects, ~2x slower
- **Pickle**: Binary format, supports all Python objects, faster and more compact

See [Checkpoint Guide](examples/checkpoint_demo.py) for complete examples.

---

### Option 11: Dead Letter Queue for Failed Item Management

When items fail permanently even after retries, use a Dead Letter Queue to collect, inspect, and potentially replay them:

```python
from amorsize import DeadLetterQueue, DLQPolicy, DLQFormat, replay_failed_items

# Configure DLQ
policy = DLQPolicy(
    directory="./.dlq",           # Storage directory
    format=DLQFormat.JSON,        # or DLQFormat.PICKLE
    max_entries=10000,            # Size limit (0 = unlimited)
    include_traceback=True,       # Full stack traces
    auto_persist=True             # Auto-save to disk
)

dlq = DeadLetterQueue(policy)

def process_with_dlq(items, max_retries=3):
    """Process items with retry logic and DLQ for permanent failures."""
    results = []
    
    for item in items:
        for attempt in range(max_retries):
            try:
                result = risky_operation(item)
                results.append(result)
                break  # Success
            except Exception as e:
                if attempt == max_retries - 1:
                    # Final retry failed - add to DLQ
                    dlq.add(
                        item=item,
                        error=e,
                        retry_count=max_retries,
                        metadata={"source": "process_batch", "item_id": item.id}
                    )
                    print(f"Item {item} added to DLQ after {max_retries} retries")
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
    
    return results

# Process items
items = get_data()
results = process_with_dlq(items)

# Inspect failures
summary = dlq.get_summary()
print(f"Failed items: {summary['total_entries']}")
print(f"Error types: {summary['error_types']}")
print(f"Avg retries: {summary['avg_retry_count']}")

# Examine individual failures
for entry in dlq.get_entries():
    print(f"Item: {entry.item}")
    print(f"Error: {entry.error_type} - {entry.error_message}")
    print(f"Timestamp: {entry.timestamp}")
    if entry.traceback:
        print(f"Traceback:\n{entry.traceback}")

# After fixing the issue, replay failed items
print("Replaying failed items...")
recovered_results, still_failed = replay_failed_items(dlq, risky_operation)
print(f"Recovered: {len(recovered_results)}, Still failing: {len(still_failed)}")

# DLQ is automatically persisted to disk (if auto_persist=True)
# Load in a new session:
dlq2 = DeadLetterQueue(policy)
dlq2.load()  # Loads from disk
print(f"Loaded {dlq2.size()} failures from previous session")
```

**Key features:**
- ✅ Collect permanently failed items with full error context
- ✅ Inspect failures for debugging and monitoring
- ✅ Replay items after fixing issues
- ✅ Persist to disk for auditing across sessions
- ✅ Automatic size limiting to prevent unbounded growth
- ✅ Thread-safe concurrent access
- ✅ JSON (readable) or Pickle (efficient) formats
- ✅ Integration with retry and circuit breaker patterns

**Use cases:**
- API processing with occasional permanent failures
- ETL pipelines where some records are malformed
- Batch jobs with transient vs permanent errors
- Monitoring and alerting on failure patterns
- Audit trails for compliance and debugging

**DLQ complements existing fault tolerance:**
- **Retry**: Handles transient failures (network glitches, timeouts)
- **Circuit Breaker**: Prevents cascade failures (service outages)
- **Checkpoint**: Recovers from process crashes (resume from last save)
- **DLQ**: Manages permanent failures (bad data, validation errors)

See [DLQ Guide](examples/dead_letter_queue_demo.py) for complete examples.

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

## Best Practices

New to parallelization or want to optimize your usage? Check the [Best Practices Guide](docs/BEST_PRACTICES.md):

- ✅ When to use Amorsize (and when not to)
- ✅ Function design patterns for optimal parallelization
- ✅ Data preparation strategies
- ✅ Memory management techniques
- ✅ Real-world case studies with before/after results
- ✅ Performance optimization patterns
- ✅ Common pitfalls to avoid

Learn proven patterns for getting the most out of multiprocessing in Python.

## Performance Tuning

Want to squeeze every bit of performance from your parallelization? Check the [Performance Tuning Guide](docs/PERFORMANCE_TUNING.md):

- 🔍 **Cost Model Deep-Dive:** Understand spawn, IPC, chunking, and cache overhead
- ⚙️ **target_chunk_duration Tuning:** When and how to adjust the key parameter
- 🖥️ **Hardware-Specific Optimization:** Laptops, workstations, HPC, cloud instances
- 📊 **Workload Profiling:** Classify and optimize CPU-bound vs I/O-bound tasks
- 🎛️ **Advanced Configuration:** Memory safety, load-aware workers, caching strategies
- ✅ **Benchmarking & Validation:** Verify predictions match reality
- 🐧 **System-Specific Optimizations:** Linux, Windows, macOS, Docker, NUMA systems
- 🚀 **Extreme Performance Scenarios:** Millions of tasks, NUMA awareness, streaming

Master the internals to achieve optimal parallelization for your specific workload and hardware.

## Testing & Quality

Amorsize maintains high code quality through comprehensive testing:

- **2300+ unit tests** across all modules
- **Property-based testing** with Hypothesis (1000+ automatically generated test cases)
- **Mutation testing** infrastructure to validate test effectiveness
- **Cross-platform CI** (Ubuntu, Windows, macOS × Python 3.7-3.13)
- **Performance regression testing** to catch slowdowns

### Run Mutation Testing

Mutation testing validates that tests actually catch bugs (not just exercise code):

```bash
# Install mutation testing tool
pip install mutmut

# Quick test on core module
python scripts/run_mutation_test.py --module optimizer --quick

# Full mutation testing (slow, ~30-60 minutes)
python scripts/run_mutation_test.py --all
```

See [Mutation Testing Guide](docs/MUTATION_TESTING.md) for detailed documentation.

## Troubleshooting

Having issues? Check the comprehensive [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for solutions to common problems:

- Function/data pickling errors
- Memory constraints
- No speedup from parallelization
- Windows/macOS spawn issues
- Docker/container memory detection
- And much more...

The guide includes detailed explanations, code examples, and diagnostic tools to help resolve any issues quickly.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Design Document

See [Writeup.md](Writeup.md) for the complete design specification and implementation checklist.
