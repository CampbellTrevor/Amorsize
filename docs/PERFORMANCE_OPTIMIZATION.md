# Performance Optimization Methodology

## Overview

This document describes the systematic performance optimization methodology developed and applied in Amorsize, specifically in **Iterations 164-166** where we achieved **1475x**, **8.1x**, and **52.5x** speedups through targeted caching strategies.

The methodology follows a data-driven approach: **Profile → Identify → Optimize → Verify**. This ensures optimizations target real bottlenecks rather than guessing.

## Table of Contents

1. [The Four-Phase Cycle](#the-four-phase-cycle)
2. [Case Studies](#case-studies)
3. [Caching Strategies](#caching-strategies)
4. [Profiling Guide](#profiling-guide)
5. [Performance Results](#performance-results)

---

## The Four-Phase Cycle

### Phase 1: Profile

**Goal:** Identify actual hot paths through measurement, not guessing.

**Tools:**
- Python's `cProfile` for function-level profiling
- Custom profiling scripts for call frequency analysis
- Performance benchmarks with realistic workloads

**Key Metrics:**
- **Call frequency**: How many times is a function called per operation?
- **Per-call cost**: How long does each call take?
- **Total cost**: frequency × per-call cost
- **Potential savings**: What if we cached this?

**Example Profiling Script:**

```python
import cProfile
import pstats
import io

def profile_function(func, *args, **kwargs):
    """Profile a function and return statistics."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run function multiple times to see patterns
    for _ in range(10):
        result = func(*args, **kwargs)
    
    profiler.disable()
    
    # Analyze results
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)
    
    return s.getvalue()
```

### Phase 2: Identify

**Goal:** Find functions that are:
1. Called multiple times per operation (redundancy)
2. Doing the same work each time (constant result)
3. Have measurable cost (worth optimizing)

**Target Patterns:**
- **File I/O operations** → Highest speedup potential (1000x+)
- **System queries** → High speedup potential (10-100x)
- **Network operations** → Medium-high speedup potential (5-50x)
- **Platform detection** → Medium speedup potential (10-50x)

**Red Flags (Don't Cache):**
- Functions called once per operation
- Functions with unique inputs each time
- Functions already very fast (< 0.1 μs)
- Functions doing unique work (e.g., user computation)

### Phase 3: Optimize

**Goal:** Implement caching with minimal changes and zero regressions.

**Implementation Pattern:**

We use **double-checked locking** for thread-safe caching:

```python
import threading
from typing import Optional

# Global cache variables
_cached_value: Optional[ResultType] = None
_cache_lock = threading.Lock()

def get_expensive_value() -> ResultType:
    """Get value with caching.
    
    First call: Performs expensive operation
    Subsequent calls: Returns cached value (fast)
    
    Thread-safe using double-checked locking pattern.
    """
    global _cached_value
    
    # Quick check without lock (common case)
    if _cached_value is not None:
        return _cached_value
    
    # Lock-protected initialization
    with _cache_lock:
        # Double-check after acquiring lock
        if _cached_value is not None:
            return _cached_value
        
        # Perform expensive operation once
        _cached_value = _perform_expensive_operation()
        return _cached_value

def _clear_cache_for_testing() -> None:
    """Clear cache (for testing only)."""
    global _cached_value
    with _cache_lock:
        _cached_value = None
```

**For values that change over time, add TTL:**

```python
import time

_cached_value: Optional[ResultType] = None
_cache_timestamp: Optional[float] = None
_cache_lock = threading.Lock()
CACHE_TTL = 1.0  # 1 second

def get_value_with_ttl() -> ResultType:
    """Get value with TTL-based caching."""
    global _cached_value, _cache_timestamp
    
    current_time = time.time()
    
    # Check if cache is fresh
    if (_cached_value is not None and 
        _cache_timestamp is not None and 
        current_time - _cache_timestamp < CACHE_TTL):
        return _cached_value
    
    # Cache expired, refresh
    with _cache_lock:
        # Double-check after acquiring lock
        if (_cached_value is not None and 
            _cache_timestamp is not None and 
            current_time - _cache_timestamp < CACHE_TTL):
            return _cached_value
        
        _cached_value = _perform_operation()
        _cache_timestamp = current_time
        return _cached_value
```

### Phase 4: Verify

**Goal:** Ensure correctness and measure actual improvement.

**Verification Checklist:**

1. **Correctness:**
   - [ ] All existing tests pass (zero regressions)
   - [ ] Cache returns correct values
   - [ ] Thread safety verified
   - [ ] Cache clearing works (for testing)

2. **Performance:**
   - [ ] Measure speedup with benchmarks
   - [ ] Verify first-call cost is acceptable
   - [ ] Verify cached-call cost is minimal
   - [ ] Document actual measurements

3. **Quality:**
   - [ ] Code follows existing patterns
   - [ ] Comprehensive documentation added
   - [ ] Test coverage for all code paths
   - [ ] Security scan passes (CodeQL)

**Example Performance Test:**

```python
def test_caching_performance():
    """Verify caching provides speedup."""
    import time
    
    # Clear cache
    _clear_cache_for_testing()
    
    # Measure first call (uncached)
    start = time.perf_counter()
    result1 = get_expensive_value()
    first_call_time = time.perf_counter() - start
    
    # Measure subsequent calls (cached)
    times = []
    for _ in range(100):
        start = time.perf_counter()
        result = get_expensive_value()
        times.append(time.perf_counter() - start)
    
    cached_avg_time = sum(times) / len(times)
    speedup = first_call_time / cached_avg_time
    
    assert speedup > 10, f"Expected >10x speedup, got {speedup:.1f}x"
    assert result == result1, "Cached value must match original"
```

---

## Case Studies

### Case Study 1: Cache Directory Lookup (Iteration 164)

**Problem:** `get_cache_dir()` was called on every `optimize()` invocation, performing:
- Platform detection via `platform.system()`
- Environment variable lookups via `os.environ.get()`
- Path construction with `pathlib` operations
- Filesystem I/O with `mkdir(parents=True, exist_ok=True)`

**Profiling Results:**
- Called: 1x per `optimize()` call
- Cost: ~0.18ms per call
- Pattern: Returns same directory for entire program lifetime

**Solution:** Permanent caching (no TTL needed - path never changes)

**Implementation:**
```python
_cached_cache_dir: Optional[Path] = None
_cache_dir_lock = threading.Lock()

def get_cache_dir() -> Path:
    global _cached_cache_dir
    
    if _cached_cache_dir is not None:
        return _cached_cache_dir
    
    with _cache_dir_lock:
        if _cached_cache_dir is not None:
            return _cached_cache_dir
        
        # One-time initialization
        _cached_cache_dir = _compute_cache_dir()
        return _cached_cache_dir
```

**Results:**
- **First call:** 0.179ms (full initialization)
- **Cached calls:** 0.12μs (direct return)
- **Speedup:** **1475x** 🎯
- **Impact:** Eliminates ~0.18ms overhead for every `optimize()` call after the first
- **Regressions:** 0 (all 2215 tests passed)

**Key Lesson:** File I/O operations are prime caching candidates with highest speedup potential.

---

### Case Study 2: Redis Availability Check (Iteration 165)

**Problem:** `is_distributed_cache_enabled()` was called twice per `optimize()`:
- Once during `save_cache_entry()`
- Once during `load_cache_entry()`
- Each call performed `_redis_client.ping()` network operation
- Network latency overhead: 1-10ms depending on Redis location

**Profiling Results:**
- Called: 2x per `optimize()` call (when distributed caching configured)
- Cost: ~2.27μs per call (in test environment without actual network)
- Real-world cost: 1-10ms per call with network latency
- Pattern: Result rarely changes (only when Redis goes down/up)

**Solution:** TTL-based caching (1-second window) to balance performance and responsiveness

**Implementation:**
```python
_cached_redis_enabled: Optional[bool] = None
_redis_enabled_cache_timestamp: Optional[float] = None
_redis_enabled_cache_lock = threading.Lock()
REDIS_ENABLED_CACHE_TTL = 1.0  # 1 second

def is_distributed_cache_enabled() -> bool:
    global _cached_redis_enabled, _redis_enabled_cache_timestamp
    
    current_time = time.time()
    
    # Check if cache is fresh (within TTL)
    if (_cached_redis_enabled is not None and 
        _redis_enabled_cache_timestamp is not None and 
        current_time - _redis_enabled_cache_timestamp < REDIS_ENABLED_CACHE_TTL):
        return _cached_redis_enabled
    
    # Cache expired or not initialized
    with _redis_enabled_cache_lock:
        # Double-check after acquiring lock
        if (_cached_redis_enabled is not None and 
            _redis_enabled_cache_timestamp is not None and 
            current_time - _redis_enabled_cache_timestamp < REDIS_ENABLED_CACHE_TTL):
            return _cached_redis_enabled
        
        # Check Redis availability
        _cached_redis_enabled = _check_redis_ping()
        _redis_enabled_cache_timestamp = current_time
        return _cached_redis_enabled
```

**Results:**
- **First call:** 2.27μs (Redis check)
- **Cached calls:** 0.28μs (dictionary + time check)
- **Speedup:** **8.1x** 🎯
- **Real-world impact:** Eliminates redundant network pings for burst requests
- **Responsiveness:** Detects Redis state changes within 1 second
- **Regressions:** 0 (all 2215 tests passed)

**Key Lesson:** Network operations benefit from TTL-based caching to balance performance and state awareness.

---

### Case Study 3: Start Method Detection (Iteration 166)

**Problem:** `get_multiprocessing_start_method()` was called 4x per `optimize()`:
- Multiple components querying the same immutable system property
- Each call performed `multiprocessing.get_start_method()`
- Platform fallback detection via `_get_default_start_method()`

**Profiling Results:**
- Called: 4x per `optimize()` call
- Cost: ~4.71μs per call
- Total cost: 18.84μs per `optimize()`
- Pattern: Result is constant (set once at program startup, never changes)

**Solution:** Permanent caching (no TTL - value never changes)

**Implementation:**
```python
_CACHED_START_METHOD: Optional[str] = None
_start_method_lock = threading.Lock()

def get_multiprocessing_start_method() -> str:
    global _CACHED_START_METHOD
    
    if _CACHED_START_METHOD is not None:
        return _CACHED_START_METHOD
    
    with _start_method_lock:
        if _CACHED_START_METHOD is not None:
            return _CACHED_START_METHOD
        
        # One-time detection
        try:
            _CACHED_START_METHOD = multiprocessing.get_start_method()
        except RuntimeError:
            _CACHED_START_METHOD = _get_default_start_method()
        
        return _CACHED_START_METHOD
```

**Results:**
- **First call:** 4.71μs (query multiprocessing context)
- **Cached calls:** 0.09μs (dictionary lookup)
- **Speedup:** **52.5x** 🎯
- **Per-optimize() savings:** 13.86μs (from 18.84μs → 4.98μs)
- **Regressions:** 0 (all 2215+ tests passed)

**Key Lesson:** System properties set at startup are excellent permanent caching candidates.

---

## Caching Strategies

### Strategy 1: Permanent Cache (No TTL)

**When to use:**
- Value never changes during program execution
- System properties (platform, cores, Python version)
- Startup configuration (start method, cache directory)
- Immutable resources

**Advantages:**
- Maximum speedup (no TTL overhead)
- Simplest implementation
- Lowest memory footprint

**Example:**
```python
_cached_value: Optional[T] = None
_cache_lock = threading.Lock()

def get_value() -> T:
    global _cached_value
    if _cached_value is not None:
        return _cached_value
    with _cache_lock:
        if _cached_value is not None:
            return _cached_value
        _cached_value = _compute_value()
        return _cached_value
```

**Speedup Potential:** 10-1000x+ (depends on operation cost)

---

### Strategy 2: TTL-Based Cache

**When to use:**
- Value might change over time
- Network state (service availability)
- System state (memory usage, CPU load)
- Configuration that can be updated

**Advantages:**
- Balances performance and freshness
- Detects state changes reasonably quickly
- Suitable for production environments

**TTL Selection Guide:**
- **1 second:** Fast-changing state (memory, load, network)
- **5 seconds:** Moderate-changing state (configuration)
- **60 seconds:** Slow-changing state (system topology)

**Example:**
```python
_cached_value: Optional[T] = None
_cache_timestamp: Optional[float] = None
_cache_lock = threading.Lock()
CACHE_TTL = 1.0

def get_value() -> T:
    global _cached_value, _cache_timestamp
    current_time = time.time()
    
    if (_cached_value is not None and 
        _cache_timestamp is not None and 
        current_time - _cache_timestamp < CACHE_TTL):
        return _cached_value
    
    with _cache_lock:
        if (_cached_value is not None and 
            _cache_timestamp is not None and 
            current_time - _cache_timestamp < CACHE_TTL):
            return _cached_value
        
        _cached_value = _compute_value()
        _cache_timestamp = current_time
        return _cached_value
```

**Speedup Potential:** 5-100x (depends on TTL overhead vs operation cost)

---

### Strategy 3: No Caching

**When NOT to cache:**
- Function called once per operation (no redundancy)
- Unique inputs each time (no constant result)
- Already very fast (< 0.1μs, caching adds overhead)
- Doing unique user work (e.g., computation on user data)

**Examples:**
- `perform_dry_run()` - samples user function with unique data
- `calculate_amdahl_speedup()` - computes with unique parameters
- User-provided functions

---

## Profiling Guide

### Getting Started with Profiling

#### 1. Basic Profiling with cProfile

```python
import cProfile
import pstats

def profile_my_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    my_expensive_function()
    
    profiler.disable()
    
    # Print results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

#### 2. Profiling Multiple Calls

```python
def profile_repeated_calls():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Call multiple times to see patterns
    for _ in range(10):
        my_function()
    
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    
    # Analyze by cumulative time
    print("=== Top functions by cumulative time ===")
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    # Analyze by call count
    print("\n=== Top functions by call count ===")
    stats.sort_stats('ncalls')
    stats.print_stats(20)
```

#### 3. Analyzing Call Frequency

```python
def analyze_call_frequency():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run your function 10 times
    for _ in range(10):
        my_function()
    
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    
    # Get raw stats
    for func_key, (cc, nc, tt, ct, callers) in stats.stats.items():
        filename, line, func_name = func_key
        
        # Skip non-relevant functions
        if 'my_module' not in filename:
            continue
        
        # Calculate metrics
        calls_per_run = nc / 10
        avg_time_ms = (tt / nc * 1000) if nc > 0 else 0
        
        # Identify potential optimization targets
        if calls_per_run > 1.5:  # Called multiple times per run
            print(f"{func_name}: {calls_per_run:.1f} calls/run, {avg_time_ms:.3f}ms/call")
```

#### 4. Benchmarking Speedup

```python
import time

def benchmark_optimization():
    # Before optimization
    times_before = []
    for _ in range(100):
        start = time.perf_counter()
        result = unoptimized_function()
        times_before.append(time.perf_counter() - start)
    
    avg_before = sum(times_before) / len(times_before)
    
    # After optimization
    times_after = []
    for _ in range(100):
        start = time.perf_counter()
        result = optimized_function()
        times_after.append(time.perf_counter() - start)
    
    avg_after = sum(times_after) / len(times_after)
    
    speedup = avg_before / avg_after
    print(f"Before: {avg_before*1e6:.2f} μs")
    print(f"After: {avg_after*1e6:.2f} μs")
    print(f"Speedup: {speedup:.1f}x")
```

### Profiling Best Practices

1. **Profile realistic workloads** - Use representative data and operations
2. **Run multiple iterations** - First call may have one-time costs
3. **Focus on cumulative time** - Total impact matters more than individual calls
4. **Look for patterns** - Functions called repeatedly are prime candidates
5. **Measure actual speedup** - Verify improvement with benchmarks
6. **Consider thread safety** - Concurrent access needs proper locking
7. **Test thoroughly** - Ensure optimizations don't break functionality

---

## Performance Results

### Overall Impact (Iterations 164-166)

| Iteration | Optimization | Speedup | Impact |
|-----------|-------------|---------|--------|
| 164 | Cache Directory Lookup | **1475x** | Eliminated 0.18ms overhead per optimize() |
| 165 | Redis Availability Check | **8.1x** | Eliminated redundant network pings |
| 166 | Start Method Detection | **52.5x** | Saved 13.86μs per optimize() |

### Current Performance

**`optimize()` function performance:**
- Average time: **0.114ms** per call ✅
- This is excellent for a full optimization analysis
- 70-80% of time is now in `perform_dry_run` (unique work, not cacheable)
- Remaining operations are already cached or very fast

### Performance Hierarchy (by speedup potential)

1. **File I/O operations**: 100-1000x+ speedup
   - Example: Cache directory lookup (1475x)
   - Reason: Eliminates platform detection, mkdir, path operations

2. **System property queries**: 10-100x speedup
   - Example: Start method detection (52.5x)
   - Reason: Eliminates multiprocessing context queries

3. **Network operations with TTL**: 5-50x speedup
   - Example: Redis availability (8.1x)
   - Reason: Eliminates network latency, but TTL adds overhead

4. **Computations**: 2-10x speedup
   - Reason: Already fast, caching helps with repeated calculations

### Recommendations for Users

If you're using Amorsize and want to optimize your application:

1. **Profile first** - Don't guess at bottlenecks
2. **Use the profiling guide** above to identify hot paths
3. **Check if Amorsize is the bottleneck** - Usually it's not (0.114ms is fast!)
4. **Focus on your function execution time** - That's where most time is spent
5. **Consider caching your function results** - If calling same function with same data
6. **Use batch processing** - `process_in_batches()` for large datasets

---

## Conclusion

The systematic **Profile → Identify → Optimize → Verify** cycle has proven highly effective:

- **Data-driven**: Profiling identifies real bottlenecks
- **Minimal changes**: Each optimization is ~50-100 lines in one file
- **Zero regressions**: All existing tests continue to pass
- **Measurable impact**: Speedups range from 8x to 1475x
- **Repeatable**: Same pattern works for different optimizations

This methodology can be applied to any Python codebase seeking performance improvements through targeted caching strategies.

For questions or suggestions, please open an issue on GitHub.
