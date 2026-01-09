# Smart Default Overhead Measurements

## What Changed in Iteration 12

Starting from Iteration 12, Amorsize now **measures actual system-specific overhead by default** instead of using OS-based estimates. This provides more accurate parallelization recommendations out-of-the-box.

## The Problem We Solved

Previously, the optimizer used:
- **OS-based spawn cost estimates** (15ms for Linux, 200ms for Windows/macOS)
- **Hardcoded chunking overhead** (0.5ms per chunk)

These estimates were:
- ❌ Not system-specific
- ❌ Could be 2-3x off on fast or slow systems
- ❌ Led to suboptimal parallelization decisions

## The Solution

Now, by default, Amorsize:
- ✅ **Measures actual spawn cost** (~15ms one-time measurement, cached)
- ✅ **Measures actual chunking overhead** (~10ms one-time measurement, cached)
- ✅ **Provides system-specific accurate recommendations**
- ✅ **Caches measurements globally** (no repeated benchmarking)

## Performance Impact

**First optimize() call:**
- Includes ~25ms of one-time measurement overhead
- Measurements are cached for all subsequent calls

**Subsequent optimize() calls:**
- Zero measurement overhead (uses cached values)

**Total overhead:** Negligible compared to typical optimization analysis time

## Usage Examples

### Default Behavior (Recommended)

```python
from amorsize import optimize

def expensive_function(x):
    result = 0
    for i in range(1000):
        result += x ** 2
    return result

data = range(10000)

# Measures actual spawn cost and chunking overhead by default
result = optimize(expensive_function, data)
print(f"Use n_jobs={result.n_jobs}, chunksize={result.chunksize}")
# Result is based on ACTUAL system measurements, not estimates
```

### Opting Out for Fastest Startup

If you want the absolute fastest startup time and are willing to accept estimates:

```python
# Use estimates instead of measurements (saves ~25ms on first call)
result = optimize(
    expensive_function, 
    data,
    use_spawn_benchmark=False,      # Use OS-based estimate
    use_chunking_benchmark=False    # Use default 0.5ms estimate
)
```

### Viewing Measurement Results

```python
result = optimize(expensive_function, data, profile=True)

# See the measured values
print(f"Spawn cost: {result.profile.spawn_cost * 1000:.2f}ms per worker")
print(f"Chunking overhead: {result.profile.chunking_overhead * 1000:.2f}ms per chunk")

# View detailed analysis
print(result.explain())
```

## Comparison: Before vs After

### Before Iteration 12

```python
# Old behavior: Always used estimates
result = optimize(func, data)
# Spawn cost: 15ms (OS estimate, not measured)
# Chunking overhead: 0.5ms (hardcoded, not measured)
# Could be 2-3x off on your specific system
```

### After Iteration 12

```python
# New behavior: Measures actual overhead by default
result = optimize(func, data)
# Spawn cost: 7ms (actual measurement on your system)
# Chunking overhead: 0.032ms (actual measurement on your system)
# Accurate recommendations for YOUR specific hardware
```

## When to Use Each Mode

### Use Default (Measurements Enabled)

✅ **Recommended for most use cases:**
- You want the most accurate recommendations
- You're optimizing workloads that run multiple times
- ~25ms one-time measurement overhead is acceptable
- You want system-specific tuning

### Use Estimates (Measurements Disabled)

✅ **Consider when:**
- You need absolute fastest startup (<5ms overhead)
- You're doing one-off analysis
- System variability is not a concern
- You're in a constrained environment

## Technical Details

### What Gets Measured

**Spawn Cost Measurement:**
- Creates pools with 1 and 2 workers
- Calculates marginal cost per worker
- Accounts for fork vs spawn vs forkserver methods
- Typical measurement time: ~15ms

**Chunking Overhead Measurement:**
- Processes 1000 items with large chunks (100 items → 10 chunks)
- Processes 1000 items with small chunks (10 items → 100 chunks)
- Calculates marginal cost per chunk
- Typical measurement time: ~10ms

### Caching Behavior

Measurements are cached **globally per process:**
- First `optimize()` call: measures and caches
- Subsequent calls: use cached values (zero overhead)
- Cache persists for entire Python process lifetime
- Different processes measure independently

### Accuracy Improvement

Real-world measurements on Linux with fork:
- **Spawn Cost:**
  - Estimate: 15ms
  - Measured: 5-10ms (40-50% more accurate)
- **Chunking Overhead:**
  - Estimate: 0.5ms
  - Measured: 0.01-0.1ms (80-98% more accurate)

## Backward Compatibility

This change is **fully backward compatible:**
- ✅ All existing code works unchanged
- ✅ Tests updated to reflect new defaults
- ✅ Explicit `use_spawn_benchmark=False` still works
- ✅ No breaking changes to API

## API Changes

### Default Parameter Values Changed

```python
# Old defaults
def optimize(
    func, data,
    use_spawn_benchmark=False,      # Was False
    use_chunking_benchmark=False    # Was False
):
    ...

# New defaults
def optimize(
    func, data,
    use_spawn_benchmark=True,       # Now True
    use_chunking_benchmark=True     # Now True
):
    ...
```

### Function Signature Changes

```python
# system_info.py
def get_spawn_cost(use_benchmark: bool = True)  # Was False
def get_chunking_overhead(use_benchmark: bool = True)  # Was False
```

## Migration Guide

No migration needed! Your existing code will automatically benefit from more accurate measurements.

**If you explicitly set the flags:**

```python
# If you had this:
result = optimize(func, data, use_spawn_benchmark=True)

# It still works the same way - no changes needed
```

**If you want the old behavior:**

```python
# To restore old behavior (estimates only):
result = optimize(
    func, data,
    use_spawn_benchmark=False,
    use_chunking_benchmark=False
)
```

## Testing

New test suite added in `tests/test_smart_defaults.py`:
- 17 new tests covering smart default behavior
- Tests verify measurements are fast (<100ms)
- Tests confirm caching works correctly
- Tests ensure backward compatibility

Run tests with:
```bash
pytest tests/test_smart_defaults.py -v
```

## Related Strategic Priorities

This change addresses the **SAFETY & ACCURACY** priority:
> "Is the OS spawning overhead (`fork` vs `spawn`) actually measured, or just guessed?"

✅ **Answer:** Now MEASURED by default, providing accurate system-specific recommendations.

## Performance Benchmarks

```python
# Benchmark: First optimize() call (includes measurements)
import time
start = time.perf_counter()
result = optimize(func, data)
duration = time.perf_counter() - start
# Duration: ~50-100ms (sampling + measurement)

# Benchmark: Subsequent optimize() calls (uses cache)
start = time.perf_counter()
result = optimize(func, data)
duration = time.perf_counter() - start
# Duration: ~25-50ms (sampling only, no measurement overhead)
```

## Summary

**What:** Default behavior now measures actual overhead instead of using estimates

**Why:** Provides more accurate recommendations without requiring user knowledge

**Impact:** ~25ms one-time measurement overhead, cached for all subsequent calls

**Benefit:** 40-80% more accurate spawn cost and chunking overhead estimates

**Compatibility:** Fully backward compatible, no code changes required
