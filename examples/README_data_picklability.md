# Data Picklability Detection

## Overview

Amorsize now includes automatic detection of unpicklable data items, preventing runtime failures in `multiprocessing.Pool.map()`. This safety feature checks whether your data can be serialized before recommending parallelization.

## The Problem

Python's `multiprocessing` module requires that data be **picklable** (serializable) to send it between processes. Many Python objects cannot be pickled, including:

- **Thread synchronization objects**: `threading.Lock()`, `threading.Event()`, `threading.Semaphore()`
- **File handles**: Open file objects from `open()` or `tempfile`
- **Database connections**: Active database connection objects
- **Network sockets**: Socket objects
- **Lambda functions**: When embedded in data structures
- **Local functions with closures**: Functions defined inside other functions

Without detection, the optimizer might recommend parallelization that will fail at runtime with cryptic errors like:
```
TypeError: cannot pickle '_thread.lock' object
```

## The Solution

Amorsize now checks your data items during the dry run sampling phase. If any item cannot be pickled, the optimizer:

1. **Rejects parallelization** - Returns `n_jobs=1` for safe serial execution
2. **Identifies the problem** - Shows which data item index failed
3. **Explains the issue** - Clear error message about pickling
4. **Provides recommendations** - Suggests solutions like dill/cloudpickle

## Usage Examples

### Example 1: Detecting Thread Locks in Data

```python
import threading
from amorsize import optimize

def process_item(x):
    return x.get("id", 0) * 2

# Common mistake: including thread locks in data
lock = threading.Lock()
data = [
    {"id": 1, "lock": lock},  # This cannot be pickled!
    {"id": 2, "lock": lock},
    {"id": 3, "lock": lock}
]

result = optimize(process_item, data, sample_size=2)
print(result.reason)
# Output: "Data items are not picklable - Data item at index 0 is not picklable: TypeError"

print(result.warnings)
# Output: ["Data item at index 0 is not picklable: TypeError. Use serial execution."]
```

### Example 2: Detecting File Handles

```python
import tempfile
from amorsize import optimize

def process_item(x):
    if isinstance(x, int):
        return x * 2
    return 0

# Common mistake: including file handles in data
with tempfile.NamedTemporaryFile() as f:
    data = [1, 2, f, 4, 5]  # File handle cannot be pickled!
    
    result = optimize(process_item, data, sample_size=3)
    print(f"n_jobs={result.n_jobs}")  # Will be 1 (serial execution)
```

### Example 3: Using Profiling for Details

```python
import threading
from amorsize import optimize

def process_data(x):
    return x * 2 if isinstance(x, int) else 0

event = threading.Event()
data = [1, 2, event, 4, 5, 6, 7, 8, 9, 10]

result = optimize(process_data, data, sample_size=5, profile=True)
print(result.explain())
```

Output includes:
```
[5] REJECTION REASONS
----------------------------------------------------------------------
  ✗ Data items are not picklable - multiprocessing requires picklable data

[6] RECOMMENDATIONS
----------------------------------------------------------------------
  💡 Ensure data items don't contain thread locks, file handles, or other unpicklable objects
  💡 Consider using dill or cloudpickle for more flexible serialization
```

## How It Works

1. **During Sampling**: After extracting sample data items, each item is tested with `pickle.dumps()`
2. **Early Detection**: Happens before any dry run execution attempts
3. **Precise Reporting**: Identifies the exact index of the first unpicklable item
4. **Safe Fallback**: Returns serial execution parameters (`n_jobs=1`) to prevent runtime failures

## Solutions for Unpicklable Data

If you encounter unpicklable data, consider these solutions:

### Solution 1: Restructure Your Data

Remove unpicklable objects from your data structure:

```python
# Bad: Embedding locks in data
bad_data = [{"id": 1, "lock": threading.Lock()}]

# Good: Pass IDs only, create locks in worker if needed
good_data = [{"id": 1}]
```

### Solution 2: Use dill or cloudpickle

These libraries can pickle more object types:

```python
import dill
# Use dill for more flexible pickling
# (Note: Amorsize uses standard pickle, but you can use dill with Pool)
```

### Solution 3: Use multiprocessing.Manager

For shared state across processes:

```python
from multiprocessing import Manager

manager = Manager()
shared_lock = manager.Lock()
# This lock can be shared across processes
```

### Solution 4: Accept Serial Execution

Sometimes serial execution is the right choice:

```python
result = optimize(func, data)
if result.n_jobs == 1:
    # Just use a regular for loop
    results = [func(item) for item in data]
```

## Technical Details

### API Changes

**New in `SamplingResult` class:**
- `data_items_picklable: bool` - Whether all data items are picklable
- `unpicklable_data_index: Optional[int]` - Index of first unpicklable item
- `data_pickle_error: Optional[Exception]` - The pickling exception raised

**New function in `sampling.py`:**
```python
def check_data_picklability(data_items: List[Any]) -> Tuple[bool, Optional[int], Optional[Exception]]:
    """Check if data items can be pickled for multiprocessing."""
```

**Enhanced `optimize()` function:**
- Checks data picklability after sampling
- Returns `n_jobs=1` if data is unpicklable
- Provides clear error messages and recommendations

### Compatibility

- ✅ Backward compatible - existing code works unchanged
- ✅ Zero overhead when data is picklable
- ✅ Works with all data types (lists, generators, etc.)
- ✅ Integrates with diagnostic profiling mode

## Testing

Run the example to see the feature in action:

```bash
python examples/data_picklability_demo.py
```

Run the test suite:

```bash
pytest tests/test_data_picklability.py -v
```

## Benefits

1. **Prevents Silent Failures**: Catches pickling issues before runtime
2. **Clear Error Messages**: Tells you exactly what's wrong and where
3. **Actionable Guidance**: Suggests concrete solutions
4. **Fail-Safe Protocol**: Falls back to serial execution when needed
5. **Better DX**: Saves debugging time and frustration

## See Also

- [Examples README](README.md) - Overview of all examples
- [Generator Safety](README_generator_safety.md) - How Amorsize handles generators
- [Diagnostic Profiling](README_diagnostic_profiling.md) - Detailed optimization analysis
