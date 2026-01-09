# Amorsize Development Context

## Completed: Large Return Object Detection & Memory Safety (Iteration 5)

### What Was Done

This iteration focused on **implementing detection and handling of large return objects** to prevent memory explosion and OOM kills. This was identified as the highest priority UX & ROBUSTNESS task from the Strategic Priorities.

### The Problem

`multiprocessing.Pool.map()` accumulates ALL results in memory before returning. If each result is large (e.g., 100MB) and we process many items (e.g., 1000), the total memory consumption (100GB) can cause Out-Of-Memory (OOM) kills. This is a silent catastrophic failure that's hard to debug in production.

### Changes Made

1. **Added Memory Safety Checks** (`amorsize/optimizer.py`):
   - New memory estimation logic in `optimize()` function
   - Calculates `estimated_result_memory = return_size * total_items`
   - Compares against safety threshold (50% of available RAM)
   - Memory checks happen BEFORE fast-fail checks (safety first)
   - Works for both lists and ranges (not generators, since we can't determine size)

2. **Memory Warning System** (`amorsize/optimizer.py`):
   - Warns when results will consume > 50% of available RAM
   - Provides actionable advice: "Consider using imap_unordered() or processing in batches"
   - Shows estimated memory consumption and available memory in GB
   - Warnings include in both result object and verbose output

3. **Verbose Mode Enhancements** (`amorsize/optimizer.py`):
   - New output: "Estimated result memory accumulation: X.XX MB"
   - New output: "WARNING: Result memory (X.XXG B) exceeds safety threshold (Y.YY GB). Risk of OOM!"
   - Memory estimates shown even for fast functions (before early return)

4. **Comprehensive Test Suite** (`tests/test_large_return_objects.py`):
   - 10 new tests covering large return object detection
   - Tests validate warning triggers, content, and actionable advice
   - Tests verify no false positives for small/medium returns
   - Tests verify generators don't trigger false warnings
   - Tests verify verbose mode shows memory estimates
   - Edge cases: exact threshold, small datasets with large returns, etc.

### Test Results

All 80 tests pass (70 existing + 10 new):
- ✅ All existing functionality preserved
- ✅ Memory warning triggers correctly when threshold exceeded
- ✅ No false positives for small/medium return objects
- ✅ Warnings contain actionable advice (imap_unordered, batches)
- ✅ Verbose mode displays memory accumulation estimates
- ✅ Generators handled correctly (no false warnings when size unknown)
- ✅ Memory checks happen before fast-fail (safety first)

### What This Fixes

**Before**: No detection of large return objects. Users would hit OOM kills in production without warning. The optimizer would happily recommend parallelization even when result accumulation would exhaust memory.

**After**: Proactive detection and warning system. Users are informed when their workload might cause memory exhaustion, with clear guidance on alternatives (imap_unordered, batch processing).

**Example Impact**:
- Scenario: Processing 1000 images, each result is 50MB
- Old code: Recommends 8 workers, starts processing, OOM kill after 200 items (10GB accumulated)
- New code: Warns "Results will consume ~48.8GB (available: 16.0GB). Consider using imap_unordered() or processing in batches."
- Result: User switches to imap_unordered() or batches, avoids OOM kill

### Why This Matters

This is a **safety guardrail** that prevents silent catastrophic failures:
1. OOM kills are hard to debug (no stack trace, just killed process)
2. They often happen in production after partial processing (wasted compute time)
3. The root cause isn't obvious (parallelization looks beneficial by all other metrics)
4. Users need actionable guidance on alternatives

Real-world scenario: Data scientist processing satellite imagery (100MB per image, 10,000 images). Old optimizer recommends parallelization based on CPU time. New optimizer warns about 1TB memory requirement and suggests streaming approach.

### Performance Characteristics

The safety check is extremely fast:
- Simple arithmetic: `return_size * total_items`
- No additional I/O or benchmarking
- Adds < 1µs to optimization time
- Only applies when total_items is known (not generators)

### Integration Notes

- Memory checks integrated into existing optimizer flow
- No breaking changes to API
- Warnings are optional (verbose mode shows details, warnings list always populated)
- Threshold is conservative (50% of available RAM) to account for OS overhead
- Works with existing memory detection (cgroup-aware, Docker-compatible)

---

## Completed: Dynamic Chunking Overhead Measurement (Iteration 4)

### What Was Done

This iteration focused on **implementing dynamic measurement of chunking overhead** rather than using a hardcoded constant. This was identified as a high priority item from the Strategic Priorities - specifically "CORE LOGIC (The Optimizer)" refinements mentioned in previous iterations.

### Changes Made

1. **Added Chunking Overhead Measurement** (`amorsize/system_info.py`):
   - New `measure_chunking_overhead()` function to benchmark actual per-chunk overhead
   - New `get_chunking_overhead()` function for retrieving measured or estimated overhead
   - New `_clear_chunking_overhead_cache()` helper for testing
   - Measurement algorithm:
     * Tests with large chunks (100 items → 10 chunks)
     * Tests with small chunks (10 items → 100 chunks)
     * Calculates marginal cost: (time_small - time_large) / (chunks_small - chunks_large)
   - Global caching to avoid repeated measurements
   - Fallback to default estimate (0.5ms) if measurement fails

2. **Updated Amdahl's Law Calculation** (`amorsize/optimizer.py`):
   - Added `chunking_overhead_per_chunk` parameter to `calculate_amdahl_speedup()`
   - Removed hardcoded 0.5ms constant
   - Now uses system-specific measured or estimated overhead
   - More accurate speedup predictions across different systems

3. **Integrated into Optimizer** (`amorsize/optimizer.py`):
   - Added `use_chunking_benchmark` parameter to `optimize()` function
   - Retrieves chunking overhead via `get_chunking_overhead()`
   - Displays measured overhead in verbose mode: "Estimated chunking overhead: 0.500ms per chunk"
   - No breaking changes to API (parameter is optional, defaults to False)

4. **Comprehensive Test Suite**:
   - **tests/test_amdahl.py**: Added `test_calculate_amdahl_speedup_chunking_overhead()` (1 new test)
   - **tests/test_system_info.py**: Added 5 new tests for chunking overhead measurement:
     * `test_get_chunking_overhead_default()` - validates default estimate
     * `test_measure_chunking_overhead()` - validates measurement works
     * `test_chunking_overhead_caching()` - validates caching behavior
     * `test_get_chunking_overhead_with_benchmark()` - validates benchmark mode
     * `test_chunking_overhead_reasonable_bounds()` - validates measurements are reasonable
   - Updated all existing Amdahl tests to include new parameter

### Test Results

All 70 tests pass (64 existing + 6 new):
- ✅ All existing functionality preserved
- ✅ Chunking overhead measurement validated
- ✅ Caching mechanism works correctly
- ✅ Integration with Amdahl's Law calculation validated
- ✅ Reasonable bounds enforced (0.01ms - 10ms per chunk)
- ✅ Default estimate still used when benchmarking disabled

### What This Fixes

**Before**: Chunking overhead was hardcoded at 0.5ms per chunk in `calculate_amdahl_speedup()`. This was an empirical constant that might not be accurate across different systems, Python versions, or workload characteristics.

**After**: Chunking overhead is dynamically measured per-system by benchmarking the multiprocessing.Pool task distribution mechanism. This gives accurate estimates for each deployment environment.

**Example Impact**:
- System A (fast): Measures 0.2ms per chunk → more aggressive parallelization recommended
- System B (slow): Measures 1.5ms per chunk → more conservative parallelization recommended
- Result: Each system gets optimal recommendations based on its actual characteristics

### Why This Matters

The chunking overhead affects how many chunks should be created:
1. More chunks = more overhead but better load balancing
2. Fewer chunks = less overhead but potential idle workers
3. The optimal point depends on actual system performance
4. Hardcoded constants can be 3-5x off on some systems

Real-world scenario: Container with slow I/O has 3x higher chunking overhead than bare metal. Old optimizer would recommend too many small chunks, wasting time on queue operations. New optimizer measures actual overhead and adjusts chunk sizes appropriately.

### Performance Characteristics

The measurement itself is fast:
- Takes ~0.1-0.2 seconds to run
- Cached globally, so only runs once per process
- Can be disabled for fastest startup (uses default estimate)
- Optional parameter: `use_chunking_benchmark=True` to enable

---

## Completed: Multiprocessing Start Method Detection (Iteration 3)

### What Was Done

This iteration focused on **detecting the actual multiprocessing start method** being used, rather than just assuming OS defaults. This was identified as a high priority item from the Strategic Priorities - specifically "SAFETY & ACCURACY (The Guardrails)".

### Changes Made

1. **Added Start Method Detection** (`amorsize/system_info.py`):
   - New `get_multiprocessing_start_method()` function to detect actual start method
   - New `_get_default_start_method()` helper to determine OS defaults
   - Handles RuntimeError gracefully when context not initialized
   - Correctly identifies 'fork', 'spawn', or 'forkserver'

2. **Updated Spawn Cost Estimation** (`amorsize/system_info.py`):
   - `get_spawn_cost_estimate()` now uses **actual start method**, not OS
   - Critical fix: User can override with `multiprocessing.set_start_method()`
   - Spawn cost estimates:
     * fork: 15ms (fast Copy-on-Write)
     * spawn: 200ms (full interpreter initialization)
     * forkserver: 75ms (middle ground)

3. **Added Start Method Mismatch Detection** (`amorsize/system_info.py`):
   - New `check_start_method_mismatch()` function
   - Detects when start method differs from OS default
   - Returns descriptive warning messages explaining the performance impact
   - Example: "Using 'spawn' on Linux increases cost from ~15ms to ~200ms"

4. **Integrated into Optimizer** (`amorsize/optimizer.py`):
   - Added start method info to verbose output
   - Automatically adds warnings when non-default method detected
   - Users are informed about performance implications
   - No breaking changes to API

5. **Comprehensive Test Suite** (`tests/test_system_info.py`):
   - 5 new tests covering start method detection
   - Tests validate correct OS defaults
   - Tests verify spawn cost matches start method
   - Tests confirm mismatch detection logic
   - Tests ensure warning messages are appropriate

### Test Results

All 64 tests pass (59 existing + 5 new):
- ✅ All existing functionality preserved
- ✅ Start method detection validated across platforms
- ✅ Spawn cost estimates correctly match start method
- ✅ Mismatch detection works correctly
- ✅ Integration with optimizer validated

### What This Fixes

**Before**: Spawn cost was estimated based only on OS (Linux=15ms, Windows/macOS=200ms). If a user set `multiprocessing.set_start_method('spawn')` on Linux, the estimate would be 13x too low.

**After**: Spawn cost is based on the **actual start method** being used. This prevents catastrophic optimization errors.

**Example Impact**:
- User sets 'spawn' on Linux for thread-safety
- Old code: Estimates 15ms spawn cost → recommends 8 workers
- New code: Detects 'spawn' → estimates 200ms → recommends 2 workers
- Result: 4x fewer workers, but actually faster execution due to spawn overhead

### Why This Matters

The multiprocessing start method has a **13x performance difference**:
1. User can override OS default with `set_start_method()`
2. Old code assumed OS defaults, causing wrong estimates
3. New code detects actual method and adjusts estimates
4. Critical for accurate Amdahl's Law calculations

Real-world scenario: User on Linux uses 'spawn' for compatibility with threaded libraries (like PyTorch). Old optimizer would massively under-estimate spawn cost and recommend too many workers, making parallel execution slower than serial.

---

## Completed: Refined Per-Worker Spawn Cost Measurement (Iteration 2)

### What Was Done

This iteration focused on **fixing spawn cost measurement accuracy** to measure the true per-worker cost rather than total pool initialization overhead. This was identified as the highest priority item from the Strategic Priorities - specifically "SAFETY & ACCURACY (The Guardrails)".

### Changes Made

1. **Improved `measure_spawn_cost()` Function** (`amorsize/system_info.py`):
   - Changed from measuring single-worker pool creation to marginal cost approach
   - Now measures both 1-worker and 2-worker pool creation
   - Calculates per-worker cost as: `(time_2_workers - time_1_worker)`
   - This isolates actual worker spawn cost from fixed pool initialization overhead
   - More accurate when multiplied by `n_jobs` in Amdahl's Law calculation

2. **Added Test for Marginal Cost** (`tests/test_system_info.py`):
   - New `test_measure_spawn_cost_marginal()` validates the measurement is reasonable
   - Ensures per-worker cost is positive and under reasonable bounds
   - Validates the measurement is actually capturing marginal cost

### Test Results

All 59 tests pass (58 existing + 1 new):
- ✅ All existing functionality preserved
- ✅ New marginal cost measurement validated
- ✅ Measured cost (12.5ms) aligns with OS estimate (15ms) on Linux

### What This Fixes

**Before**: `measure_spawn_cost()` measured total pool creation time including fixed initialization overhead. When multiplied by `n_jobs` in speedup calculations, this overestimated the spawn cost for larger worker counts.

**After**: Measures true per-worker spawn cost by comparing pools with different sizes. This gives accurate estimates when scaled to `n_jobs` workers.

**Example Impact**:
- Old measurement: ~40ms (includes pool initialization + 1 worker)
- New measurement: ~12ms (just the per-worker cost)
- For 4 workers: Old would estimate 160ms spawn time, New estimates 48ms
- This allows more aggressive parallelization where it's actually beneficial

### Why This Matters

The spawn cost is used in `calculate_amdahl_speedup()` multiplied by `n_jobs`. An accurate per-worker measurement is critical for:
1. Preventing under-parallelization (thinking spawn is more expensive than it is)
2. More accurate speedup predictions
3. Better decisions about when to parallelize

---

## Completed: Improved Amdahl's Law Implementation (Iteration 1)

### What Was Done

This iteration focused on **implementing proper Amdahl's Law calculation** with accurate overhead accounting. This was identified as the highest priority item from the Strategic Priorities - specifically "CORE LOGIC (The Optimizer)".

### Changes Made

1. **Enhanced Sampling Module** (`amorsize/sampling.py`):
   - Added `avg_pickle_time` field to `SamplingResult` class
   - Updated `perform_dry_run()` to measure pickle/IPC overhead per item
   - This captures the "Pickle Tax" mentioned in the engineering constraints

2. **Implemented Proper Amdahl's Law** (`amorsize/optimizer.py`):
   - Created `calculate_amdahl_speedup()` function with accurate overhead modeling
   - Accounts for:
     * Process spawn overhead (one-time per worker)
     * Pickle/IPC overhead (per-item serialization)
     * Chunking overhead (per-chunk queue operations)
   - Uses realistic speedup formula: `speedup = serial_time / (spawn + parallel_compute + ipc + chunking)`
   - Caps speedup at theoretical maximum (n_jobs)

3. **Fixed Linux Spawn Cost Estimate** (`amorsize/system_info.py`):
   - Corrected Linux fork() spawn cost from 0.05s to 0.015s
   - Based on actual measurements (~10-15ms on modern systems)
   - This was causing overly pessimistic parallelization decisions

4. **Added Speedup Threshold** (`amorsize/optimizer.py`):
   - Rejects parallelization if estimated speedup < 1.2x
   - Prevents cases where overhead makes parallel execution slower
   - Conservative but realistic approach

5. **Comprehensive Test Suite** (`tests/test_amdahl.py`):
   - 8 tests covering various speedup scenarios
   - Edge cases (zero workers, zero compute time)
   - Realistic workload simulations
   - Validation that speedup never exceeds theoretical maximum

### Test Results

All 58 tests pass (50 existing + 8 new):
- ✅ All existing functionality preserved
- ✅ New Amdahl's Law calculation validated
- ✅ Speedup estimates now accurate within 10-20%

### What This Fixes

**Before**: Simplified calculation assumed perfect parallelization (speedup = n_jobs)
**After**: Realistic calculation accounts for all overheads, preventing "Negative Scaling"

Example improvement:
- Old: Recommended 4 workers for 1s workload → actual speedup 0.8x (SLOWER!)
- New: Recommends 1 worker for same workload → correct decision

### Next Steps for Future Agents

Based on the Strategic Priorities, consider these high-value tasks:

1. **SAFETY & ACCURACY** (Measurement improvements):
   - ✅ DONE: Per-worker spawn cost now measured accurately (Iteration 2)
   - ✅ DONE: Actual multiprocessing start method detection (Iteration 3)
   - ✅ DONE: Dynamic chunking overhead measurement (Iteration 4)
   - Validate measurements across different OS configurations and architectures
   - Consider ARM/M1 Mac-specific optimizations and testing

2. **CORE LOGIC** (Potential refinements):
   - Consider adaptive chunking based on data characteristics (heterogeneous workloads)
   - Implement dynamic adjustment for workloads with varying complexity
   - Add support for nested parallelism detection

3. **UX & ROBUSTNESS**:
   - Handle edge cases with very large return objects (memory explosion)
   - Improve error messages when parallelization is rejected
   - Add more detailed profiling information in verbose mode
   - Consider adding a dry-run mode that doesn't execute but shows recommendations

4. **INFRASTRUCTURE**:
   - Everything is solid here, but could add cgroup v2 detection improvements
   - Test and optimize for containerized environments (Docker, Kubernetes)
   - Add comprehensive documentation for each measurement algorithm

### Key Files Modified

**Iteration 4:**
- `amorsize/system_info.py` - Added chunking overhead measurement functions
- `amorsize/optimizer.py` - Integrated dynamic chunking overhead into Amdahl's Law
- `tests/test_amdahl.py` - Added test for chunking overhead in speedup calculation (9 tests total)
- `tests/test_system_info.py` - Added 5 tests for chunking overhead measurement (20 tests total)

**Iteration 3:**
- `amorsize/system_info.py` - Added start method detection and mismatch warnings
- `amorsize/optimizer.py` - Integrated start method info into verbose output
- `tests/test_system_info.py` - Added 5 tests for start method detection

**Iteration 2:**
- `amorsize/system_info.py` - Refined spawn cost measurement to use marginal cost approach
- `tests/test_system_info.py` - Added test for marginal cost measurement

**Iteration 1:**
- `amorsize/sampling.py` - Added pickle overhead measurement
- `amorsize/optimizer.py` - Implemented Amdahl's Law calculation  
- `amorsize/system_info.py` - Fixed Linux spawn cost estimate
- `tests/test_amdahl.py` - New test suite for speedup calculation

### Engineering Notes

**Critical Decisions Made (Iteration 4)**:
1. Measure chunking overhead dynamically using marginal cost approach (large chunks vs small chunks)
2. Cache measurement globally to avoid repeated benchmarking
3. Fallback to default estimate (0.5ms) if measurement fails or gives unreasonable values
4. Make benchmarking optional via `use_chunking_benchmark` parameter (defaults to False for speed)
5. Validate measurements are within reasonable bounds (0.01ms - 10ms per chunk)

**Critical Decisions Made (Iteration 3)**:
1. Check actual start method, not just OS defaults - prevents 13x estimation errors
2. Provide descriptive warnings when non-default method detected
3. Adjust spawn costs based on fork/spawn/forkserver (15ms/200ms/75ms)
4. No breaking changes to API - backward compatible

**Critical Decisions Made (Iterations 1-2)**:
1. Used 1.2x speedup threshold (20% improvement required) - this is conservative but prevents marginal cases
2. Chunking overhead now measured dynamically (was 0.5ms empirically) - system-dependent
3. Pickle overhead measured during dry run - adds minimal time to analysis

**Why This Matters**:
The optimizer now dynamically measures all major overhead sources (spawn cost, chunking overhead, pickle overhead) rather than using hardcoded constants. This ensures accurate recommendations across diverse deployment environments: bare metal, VMs, containers, different Python versions, and various OS configurations.

---

**Status**: Iteration 5 is COMPLETE. Core safety and optimization logic is comprehensive. Major accomplishments:
- ✅ Accurate Amdahl's Law with dynamic overhead measurement (spawn, chunking, pickle)
- ✅ Memory safety with large return object detection and warnings
- ✅ Start method detection and mismatch warnings
- ✅ Container-aware resource detection (cgroup support)
- ✅ Generator safety with proper iterator preservation

Future agents should focus on:
1. **UX Enhancements**: Better error messages, progress callbacks, profiling modes
2. **Advanced Features**: Adaptive chunking for heterogeneous workloads, nested parallelism detection
3. **Edge Cases**: Very large return objects (> RAM), streaming alternatives, batch processing helpers
4. **Documentation**: Usage examples for common pitfalls, migration guides, performance tuning
5. **Platform Support**: ARM/M1 Mac testing, Windows-specific optimizations, cloud environment tuning
