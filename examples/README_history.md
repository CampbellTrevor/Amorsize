# Historical Tracking

Track and compare optimization results over time to monitor performance trends and detect regressions.

## Overview

The historical tracking feature allows you to:
- 📊 Save comparison results with metadata
- 🔍 Query historical results by name or date
- 📈 Compare results across different runs or systems
- ⚠️ Detect performance regressions automatically
- 💾 Store results in JSON format for easy inspection

## Quick Start

### Saving Results

Use the `--save-result` flag with the `compare` command:

```bash
# Save a baseline measurement
python -m amorsize compare math.factorial \
    --data-range 100 \
    --configs "4,25" "8,10" \
    --save-result "baseline-v1.0"

# Output:
# === Strategy Comparison Results ===
# ...
# ✓ Result saved to history as 'baseline-v1.0' (ID: a1b2c3d4e5f6)
```

### Python API

```python
from amorsize import compare_strategies, ComparisonConfig, save_result

# Define strategies
configs = [
    ComparisonConfig("Serial", 1),
    ComparisonConfig("Parallel", 4, 25)
]

# Run comparison
result = compare_strategies(my_function, data, configs)

# Save to history
entry_id = save_result(result, "v1.0-baseline", "my_function", len(data))
print(f"Saved as {entry_id}")
```

## CLI Commands

### list - Show All Results

```bash
# List all saved results
python -m amorsize history list

# Output:
# Found 3 history entries:
#
# ID             Name                      Date                 Function
# ---------------------------------------------------------------------------------
# a1b2c3d4e5f6   baseline-v1.0             2024-01-09 10:30:45  factorial
# b2c3d4e5f6a7   optimized-v1.1            2024-01-09 11:15:20  factorial
# c3d4e5f6a7b8   baseline-v2.0             2024-01-09 14:22:33  factorial

# Filter by name
python -m amorsize history list --filter baseline

# Limit results
python -m amorsize history list --limit 5

# JSON output
python -m amorsize history list --json
```

### show - Display Details

```bash
# Show details of a specific result
python -m amorsize history show a1b2c3d4e5f6

# Output:
# ======================================================================
# History Entry: baseline-v1.0
# ======================================================================
# ID:        a1b2c3d4e5f6
# Timestamp: 2024-01-09T10:30:45Z
# Function:  factorial
# Data size: 100
#
# System Information:
#   Platform:       Linux-5.15.0-x86_64
#   Physical cores: 8
#   Memory:         15.52 GB
#   Start method:   fork
#
# Results:
#   Best strategy:  Parallel (8 workers)
#   Best time:      0.0234s
#   Best speedup:   4.27x
#
# Strategy                  Workers    Chunk      Time (s)     Speedup
# ----------------------------------------------------------------------
# Serial                    1          1          0.1000       1.00x
# Parallel (4 workers)      4          25         0.0312       3.21x
# Parallel (8 workers)      8          10         0.0234       4.27x
```

### compare - Compare Two Results

```bash
# Compare two historical results
python -m amorsize history compare a1b2c3d4e5f6 b2c3d4e5f6a7

# Output:
# ======================================================================
# History Comparison
# ======================================================================
#
# Entry 1: baseline-v1.0 (ID: a1b2c3d4e5f6)
#   Timestamp:     2024-01-09T10:30:45Z
#   Best strategy: Parallel (8 workers)
#   Speedup:       4.27x
#   Time:          0.0234s
#
# Entry 2: optimized-v1.1 (ID: b2c3d4e5f6a7)
#   Timestamp:     2024-01-09T11:15:20Z
#   Best strategy: Parallel (8 workers)
#   Speedup:       4.82x
#   Time:          0.0207s
#
# Comparison:
#   Time delta:    -0.0027s (-11.5%)
#   Speedup delta: +0.55x
#   Same system:   Yes
#   ✓ Performance improved or stable
```

### delete - Remove a Result

```bash
# Delete a specific result
python -m amorsize history delete a1b2c3d4e5f6

# Output:
# ✓ Deleted history entry 'a1b2c3d4e5f6'
```

### clear - Remove All Results

```bash
# Clear all history (with confirmation)
python -m amorsize history clear

# Output:
# Are you sure you want to delete ALL history entries? (yes/no): yes
# ✓ Deleted 3 history entries

# Skip confirmation
python -m amorsize history clear --yes
```

## Python API Reference

### save_result()

Save a comparison result to history.

```python
from amorsize import save_result

entry_id = save_result(
    result,                    # ComparisonResult object
    name="baseline-v1.0",      # User-friendly name
    function_name="my_func",   # Function that was tested
    data_size=1000,            # Size of dataset
    metadata={                 # Optional metadata
        "version": "1.0",
        "environment": "prod",
        "notes": "Baseline"
    }
)

print(f"Saved as {entry_id}")  # Returns unique ID
```

### load_result()

Load a specific result by ID.

```python
from amorsize import load_result

entry = load_result("a1b2c3d4e5f6")

if entry:
    print(f"Name: {entry.name}")
    print(f"Function: {entry.function_name}")
    print(f"Best: {entry.result.best_config.name}")
    print(f"Speedup: {entry.result.speedups[entry.result.best_config_index]:.2f}x")
```

### list_results()

List all saved results with optional filtering.

```python
from amorsize import list_results

# List all
entries = list_results()

# Filter by name
entries = list_results(name_filter="baseline")

# Limit results
entries = list_results(limit=10)

# Process results
for entry in entries:
    print(f"{entry.id}: {entry.name} - {entry.timestamp}")
```

### compare_entries()

Compare two historical results.

```python
from amorsize import compare_entries

comparison = compare_entries("a1b2c3d4e5f6", "b2c3d4e5f6a7")

if comparison:
    # Access comparison data
    entry1 = comparison["entry1"]
    entry2 = comparison["entry2"]
    comp = comparison["comparison"]
    
    print(f"Time delta: {comp['time_delta_seconds']:+.4f}s")
    print(f"Speedup delta: {comp['speedup_delta']:+.2f}x")
    
    if comp['is_regression']:
        print("⚠ REGRESSION DETECTED")
    else:
        print("✓ Performance improved or stable")
    
    if not comp['same_system']:
        print("Note: Results from different systems")
```

### delete_result()

Delete a specific result.

```python
from amorsize import delete_result

if delete_result("a1b2c3d4e5f6"):
    print("Deleted successfully")
else:
    print("Entry not found")
```

### clear_history()

Clear all history entries.

```python
from amorsize import clear_history

count = clear_history()
print(f"Deleted {count} entries")
```

## Storage Format

Results are stored as JSON files in `~/.amorsize/history/`.

### File Structure

```json
{
  "id": "a1b2c3d4e5f6",
  "name": "baseline-v1.0",
  "timestamp": "2024-01-09T10:30:45Z",
  "function_name": "factorial",
  "data_size": 100,
  "system_info": {
    "platform": "Linux-5.15.0-x86_64",
    "system": "Linux",
    "machine": "x86_64",
    "processor": "x86_64",
    "python_version": "3.10.0",
    "physical_cores": 8,
    "available_memory_gb": 15.52,
    "multiprocessing_start_method": "fork"
  },
  "metadata": {
    "version": "1.0",
    "environment": "production"
  },
  "result": {
    "configs": [
      {
        "name": "Serial",
        "n_jobs": 1,
        "chunksize": 1,
        "executor_type": "serial"
      },
      {
        "name": "Parallel",
        "n_jobs": 4,
        "chunksize": 25,
        "executor_type": "process"
      }
    ],
    "execution_times": [0.1000, 0.0312],
    "speedups": [1.0, 3.21],
    "best_config_index": 1,
    "recommendations": []
  }
}
```

## Use Cases

### 1. Track Performance Over Time

```bash
# Baseline measurement
python -m amorsize compare mymodule.process \
    --data-range 1000 \
    --configs "4,25" "8,10" \
    --save-result "v1.0"

# After optimizations
python -m amorsize compare mymodule.process \
    --data-range 1000 \
    --configs "4,25" "8,10" \
    --save-result "v1.1"

# Compare
python -m amorsize history compare <v1.0-id> <v1.1-id>
```

### 2. Monitor CI/CD Performance

```bash
# In CI pipeline
python -m amorsize compare tests.benchmark \
    --data-range 500 \
    --include-optimizer \
    --save-result "ci-${BUILD_NUMBER}"

# Check for regressions
python -m amorsize history list --filter ci --limit 2 --json | \
    jq -r '.[0].id, .[1].id' | \
    xargs python -m amorsize history compare
```

### 3. Cross-System Comparison

```bash
# On development machine
python -m amorsize compare mymodule.func \
    --data-range 1000 \
    --include-optimizer \
    --save-result "dev-laptop"

# On production server
python -m amorsize compare mymodule.func \
    --data-range 1000 \
    --include-optimizer \
    --save-result "prod-server"

# Compare
python -m amorsize history compare <dev-id> <prod-id>
```

### 4. A/B Testing Strategies

```python
from amorsize import compare_strategies, ComparisonConfig, save_result

# Strategy A: Conservative
configs_a = [ComparisonConfig("Conservative", 4, 50)]
result_a = compare_strategies(func, data, configs_a)
save_result(result_a, "strategy-A-conservative", "my_func", len(data))

# Strategy B: Aggressive
configs_b = [ComparisonConfig("Aggressive", 16, 10)]
result_b = compare_strategies(func, data, configs_b)
save_result(result_b, "strategy-B-aggressive", "my_func", len(data))

# Compare using history commands
```

## Best Practices

### 1. Use Descriptive Names

```python
# Good
save_result(result, "v2.1-optimized-memory-pool")

# Bad  
save_result(result, "test123")
```

### 2. Add Metadata

```python
save_result(result, "baseline", metadata={
    "version": "2.1.0",
    "commit": "abc123",
    "environment": "production",
    "notes": "After database optimization"
})
```

### 3. Regular Cleanup

```bash
# Keep only recent results
python -m amorsize history list --json | \
    jq -r '.[] | select(.timestamp < "2024-01-01") | .id' | \
    xargs -I {} python -m amorsize history delete {}
```

### 4. Export Important Results

```bash
# Backup important results
python -m amorsize history show a1b2c3d4e5f6 --json > baseline.json
```

## Troubleshooting

### History Directory

Results are stored in `~/.amorsize/history/`. To reset:

```bash
rm -rf ~/.amorsize/history
```

### JSON Files

History files are plain JSON and can be manually inspected or edited:

```bash
cat ~/.amorsize/history/a1b2c3d4e5f6.json | jq .
```

### Cross-System Warnings

When comparing results from different systems, the comparison will note that direct comparison may not be meaningful due to hardware differences.

## See Also

- [Comparison Mode](README_comparison_mode.md) - Multi-strategy comparison
- [Visualization](README_visualization.md) - Chart generation from results
- [Benchmark Validation](README_benchmark_validation.md) - Verify optimizer accuracy
