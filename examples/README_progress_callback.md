# Progress Callbacks - Monitoring Optimization Progress

The `optimize()` function supports **progress callbacks** to monitor long-running optimization operations. This is particularly useful for:

- **GUI applications** that need to show progress bars
- **Command-line tools** that want to display status
- **Logging systems** that track optimization metrics
- **Long-running analyses** where users want feedback

## Basic Usage

```python
from amorsize import optimize

def progress_callback(phase: str, progress: float):
    """
    Called at key milestones during optimization.
    
    Args:
        phase: Descriptive string of current phase (e.g., "Sampling function")
        progress: Float from 0.0 (start) to 1.0 (complete)
    """
    print(f"{phase}: {progress*100:.0f}%")

def expensive_function(x):
    return sum(i ** 2 for i in range(10000)) + x

data = range(1000)
result = optimize(expensive_function, data, progress_callback=progress_callback)
```

## Callback Signature

```python
Callable[[str, float], None]
```

Your callback receives:
1. **phase** (str): Descriptive name of current phase
2. **progress** (float): Value from 0.0 to 1.0 indicating completion percentage

## Progress Phases

The callback is invoked at these key milestones:

| Phase | Progress | Description |
|-------|----------|-------------|
| "Starting optimization" | 0.0 | Optimization begins |
| "Sampling function" | 0.1 | About to sample function |
| "Sampling complete" | 0.3 | Sampling finished |
| "Analyzing system" | 0.5 | Gathering system info |
| "Calculating optimal parameters" | 0.7 | Computing chunksize/n_jobs |
| "Estimating speedup" | 0.9 | Final speedup calculation |
| "Optimization complete" | 1.0 | Done! |

## Examples

### Example 1: Simple Progress Bar

```python
def progress_bar(phase: str, progress: float):
    bar_length = 40
    filled = int(bar_length * progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r[{bar}] {progress*100:5.1f}%", end="", flush=True)

result = optimize(func, data, progress_callback=progress_bar)
print()  # New line after completion
```

Output:
```
[████████████████████████████████████████] 100.0%
```

### Example 2: Detailed Logging

```python
import time

start_time = time.time()

def detailed_logger(phase: str, progress: float):
    elapsed = time.time() - start_time
    print(f"[{elapsed:6.3f}s] {progress*100:5.1f}% - {phase}")

result = optimize(func, data, progress_callback=detailed_logger)
```

Output:
```
[ 0.000s]   0.0% - Starting optimization
[ 0.012s]  10.0% - Sampling function
[ 0.145s]  30.0% - Sampling complete
[ 0.167s]  50.0% - Analyzing system
[ 0.189s]  70.0% - Calculating optimal parameters
[ 0.201s]  90.0% - Estimating speedup
[ 0.215s] 100.0% - Optimization complete
```

### Example 3: GUI Integration

```python
class ProgressTracker:
    """Track progress for GUI updates."""
    
    def __init__(self, progress_bar_widget):
        self.widget = progress_bar_widget
    
    def update(self, phase: str, progress: float):
        # Update GUI progress bar
        self.widget.setValue(int(progress * 100))
        self.widget.setFormat(f"{phase} - %p%")

tracker = ProgressTracker(my_progress_bar)
result = optimize(func, data, progress_callback=tracker.update)
```

### Example 4: Percentage-Only Updates

```python
last_reported = -1

def percentage_only(phase: str, progress: float):
    global last_reported
    percentage = int(progress * 10) * 10  # Round to nearest 10%
    if percentage > last_reported:
        last_reported = percentage
        print(f"{percentage}% complete...")

result = optimize(func, data, progress_callback=percentage_only)
```

Output:
```
0% complete...
10% complete...
30% complete...
50% complete...
70% complete...
90% complete...
100% complete...
```

### Example 5: Lambda Callback

```python
# Quick one-liner for debugging
result = optimize(
    func, 
    data,
    progress_callback=lambda phase, pct: print(f"{pct*100:.0f}% - {phase}")
)
```

## Error Handling

**Callbacks are fail-safe**: If your callback raises an exception, it's silently caught and optimization continues normally. This ensures callback errors don't break your optimization.

```python
def potentially_buggy_callback(phase: str, progress: float):
    # Even if this crashes, optimize() will continue
    risky_operation()
    log_to_unreachable_server()

# Optimization will complete even if callback fails
result = optimize(func, data, progress_callback=potentially_buggy_callback)
```

### Best Practice: Add Your Own Error Handling

```python
class SafeCallback:
    def __init__(self):
        self.errors = []
    
    def __call__(self, phase: str, progress: float):
        try:
            # Your callback logic
            self.do_something(phase, progress)
        except Exception as e:
            self.errors.append(str(e))
            # Log but don't raise

callback = SafeCallback()
result = optimize(func, data, progress_callback=callback)

if callback.errors:
    print(f"Callback had {len(callback.errors)} errors")
```

## Integration with Other Features

### With Verbose Mode

```python
# Both verbose output AND callbacks
result = optimize(
    func, 
    data, 
    verbose=True,
    progress_callback=progress_bar
)
```

Verbose output and callbacks work independently - you'll see detailed text output plus progress updates.

### With Diagnostic Profiling

```python
# Track progress + get detailed analysis
result = optimize(
    func,
    data,
    profile=True,
    progress_callback=lambda phase, pct: print(f"{phase}: {pct*100:.0f}%")
)

# After completion, analyze with profile
print(result.explain())
```

### With All Parameters

```python
result = optimize(
    func,
    data,
    sample_size=10,
    target_chunk_duration=0.5,
    verbose=False,  # Can disable verbose if callback provides progress
    use_spawn_benchmark=True,
    use_chunking_benchmark=True,
    profile=True,
    auto_adjust_for_nested_parallelism=True,
    progress_callback=my_callback
)
```

## Use Cases

### 1. Long-Running Data Science Workflows

```python
def analyze_dataset(chunk):
    # Expensive ML or statistical analysis
    return process_data(chunk)

# Show progress while optimizing
with tqdm(desc="Optimizing", unit=" phase") as pbar:
    def update_pbar(phase, progress):
        pbar.n = progress
        pbar.set_description(phase)
        pbar.refresh()
    
    result = optimize(analyze_dataset, large_dataset, progress_callback=update_pbar)
```

### 2. Web API Progress Tracking

```python
from flask import jsonify

progress_state = {"phase": "", "progress": 0.0}

def update_progress(phase, progress):
    progress_state["phase"] = phase
    progress_state["progress"] = progress

@app.route('/api/optimize/status')
def get_status():
    return jsonify(progress_state)

# In another thread:
result = optimize(func, data, progress_callback=update_progress)
```

### 3. Automated Testing with Timeouts

```python
import time

class TimeoutCallback:
    def __init__(self, timeout_seconds):
        self.start_time = time.time()
        self.timeout = timeout_seconds
    
    def __call__(self, phase, progress):
        if time.time() - self.start_time > self.timeout:
            print(f"WARNING: Optimization taking longer than expected")
            # Could implement actual timeout logic here

callback = TimeoutCallback(timeout_seconds=60)
result = optimize(func, data, progress_callback=callback)
```

## Parameter Validation

The `progress_callback` parameter is validated:

```python
# Valid: None (default, no callbacks)
result = optimize(func, data, progress_callback=None)

# Valid: Any callable accepting (str, float)
result = optimize(func, data, progress_callback=my_function)

# Invalid: Non-callable, non-None values
result = optimize(func, data, progress_callback="not callable")
# Raises: ValueError: progress_callback must be callable or None
```

## Performance Impact

Progress callbacks have **minimal overhead**:

- **~0.1ms** per callback invocation (7 callbacks total)
- **~0.7ms total** for entire optimization
- Negligible compared to sampling and analysis time
- Safe to use even for performance-critical code

## Tips and Best Practices

1. **Keep callbacks fast**: Avoid expensive operations in callbacks
2. **Use buffering for I/O**: Don't write to files on every callback
3. **Handle errors gracefully**: Use try/except in your callbacks
4. **Test with fast functions**: Ensure callbacks work even when optimization is rejected
5. **Consider threading**: If callback does I/O, consider offloading to another thread

## Comparison with Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Progress Callback** | Real-time updates, flexible, minimal overhead | Requires callback implementation |
| **Verbose Mode** | Built-in, no setup | Fixed format, text-only, no programmatic access |
| **Polling** | Simple | Inefficient, requires shared state |
| **Logging** | Persistent record | Not real-time, requires log parsing |

## See Also

- [Basic Usage](../README.md) - Getting started with amorsize
- [Diagnostic Profiling](README_diagnostic_profiling.md) - Detailed analysis after optimization
- [Verbose Mode](README.md#verbose-output) - Built-in text output for debugging
