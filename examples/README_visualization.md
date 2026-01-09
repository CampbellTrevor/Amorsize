# Visualization Support

Amorsize includes powerful visualization capabilities to help you understand parallelization performance at a glance. Generate professional charts and plots from comparison results.

## Features

- 📊 **Execution Time Bar Charts** - Compare execution times across strategies
- ⚡ **Speedup Visualizations** - See performance improvements relative to baseline
- 🎨 **Color-Coded Results** - Automatic highlighting of best/worst performers
- 🔧 **Customizable Plots** - Control size, labels, colors, and more
- 💻 **CLI Integration** - Generate visualizations from command line
- ✨ **Graceful Fallback** - Works without matplotlib (text-only output)

## Installation

Visualization features require matplotlib (version 3.0 or higher recommended):

```bash
pip install "matplotlib>=3.0"
```

Or install with the full Amorsize package:

```bash
pip install -e ".[full]"
```

## Quick Start

### Option 1: Automatic Visualization (Recommended)

Use `visualize_comparison_result()` to automatically generate all charts:

```python
from amorsize import compare_strategies, visualize_comparison_result, ComparisonConfig

def expensive_func(x):
    return sum(i**2 for i in range(x))

data = range(100, 500)

# Define strategies to compare
configs = [
    ComparisonConfig("Serial", 1),
    ComparisonConfig("2 workers", 2, 50),
    ComparisonConfig("4 workers", 4, 25)
]

# Run comparison
result = compare_strategies(expensive_func, data, configs)

# Generate visualizations
plot_paths = visualize_comparison_result(
    result,
    output_dir="./plots"
)

# Print locations of generated plots
for plot_type, path in plot_paths.items():
    print(f"{plot_type}: {path}")
```

### Option 2: CLI with --visualize Flag

Generate visualizations directly from command line:

```bash
# Compare strategies and generate plots
python -m amorsize compare math.factorial \
    --data-range 100 \
    --configs "2,20" "4,10" "8,5" \
    --visualize ./output

# Compare with optimizer recommendation
python -m amorsize compare mymodule.process \
    --data-range 500 \
    --include-optimizer \
    --configs "Manual:4,25" \
    --visualize ./comparison_plots
```

### Option 3: Individual Plotting Functions

Create custom plots with fine-grained control:

```python
from amorsize import plot_comparison_times, plot_speedup_comparison

# Your comparison data
config_names = ["Serial", "2 workers", "4 workers", "8 workers"]
execution_times = [10.0, 5.5, 3.2, 2.1]
speedups = [1.0, 1.82, 3.13, 4.76]

# Create execution time chart
plot_comparison_times(
    config_names,
    execution_times,
    output_path="times.png",
    title="Execution Time Comparison",
    figsize=(12, 7)
)

# Create speedup chart
plot_speedup_comparison(
    config_names,
    speedups,
    output_path="speedups.png",
    title="Speedup Analysis"
)
```

## API Reference

### `visualize_comparison_result(result, output_dir=None, plots=None)`

Generate all visualization plots for a comparison result.

**Parameters:**
- `result` (ComparisonResult): Result from `compare_strategies()` or `compare_with_optimizer()`
- `output_dir` (str, optional): Directory to save plots (default: current directory)
- `plots` (list, optional): List of plot types to generate: `['times', 'speedups', 'all']` (default: all)

**Returns:**
- Dictionary mapping plot type to file path

**Example:**
```python
result = compare_strategies(func, data, configs)
paths = visualize_comparison_result(result, output_dir="./analysis")
# paths = {'times': './analysis/comparison_times.png', 'speedups': './analysis/speedup_comparison.png'}
```

---

### `plot_comparison_times(config_names, execution_times, output_path=None, ...)`

Create a bar chart comparing execution times.

**Parameters:**
- `config_names` (list[str]): Names of configurations
- `execution_times` (list[float]): Execution times in seconds
- `output_path` (str, optional): Path to save plot (default: `amorsize_comparison_times.png`)
- `title` (str): Chart title
- `figsize` (tuple): Figure size (width, height) in inches
- `show_values` (bool): Display values on bars (default: True)

**Returns:**
- Path to saved plot file

**Features:**
- Fastest configuration highlighted in green
- Values displayed on bars
- Automatic rotation for long labels

**Example:**
```python
plot_comparison_times(
    ["Serial", "Parallel"],
    [10.0, 3.2],
    output_path="comparison.png",
    title="My Analysis",
    figsize=(10, 6)
)
```

---

### `plot_speedup_comparison(config_names, speedups, output_path=None, ...)`

Create a bar chart comparing speedup factors.

**Parameters:**
- `config_names` (list[str]): Names of configurations
- `speedups` (list[float]): Speedup factors (e.g., 2.5 means 2.5x faster than baseline)
- `output_path` (str, optional): Path to save plot (default: `amorsize_speedup_comparison.png`)
- `title` (str): Chart title
- `figsize` (tuple): Figure size (width, height) in inches
- `show_values` (bool): Display values on bars (default: True)
- `baseline_name` (str): Name of baseline configuration (default: "Serial")

**Returns:**
- Path to saved plot file

**Features:**
- Color-coded by speedup: Red (<1.0), Orange (1.0-1.2), Yellow (1.2-2.0), Green (>2.0)
- Baseline reference line at 1.0x
- Values displayed on bars

**Example:**
```python
plot_speedup_comparison(
    ["Serial", "4 workers", "8 workers"],
    [1.0, 3.1, 4.8],
    output_path="speedup.png",
    baseline_name="Baseline"
)
```

---

### `plot_overhead_breakdown(n_workers_list, compute_times, spawn_overheads, ...)`

Create a stacked bar chart showing overhead breakdown by worker count.

**Parameters:**
- `n_workers_list` (list[int]): Worker counts
- `compute_times` (list[float]): Pure computation times
- `spawn_overheads` (list[float]): Process spawn overhead times
- `ipc_overheads` (list[float]): Inter-process communication overhead times
- `chunking_overheads` (list[float]): Task chunking overhead times
- `output_path` (str, optional): Path to save plot (default: `amorsize_overhead_breakdown.png`)
- `title` (str): Chart title
- `figsize` (tuple): Figure size (width, height) in inches

**Returns:**
- Path to saved plot file

**Features:**
- Stacked bars showing overhead components
- Color-coded layers: Compute (blue), Spawn (orange), IPC (red), Chunking (purple)
- Legend for easy interpretation

**Example:**
```python
plot_overhead_breakdown(
    [1, 2, 4, 8],
    [10.0, 5.0, 2.5, 1.3],
    [0.0, 0.03, 0.06, 0.12],
    [0.0, 0.05, 0.10, 0.20],
    [0.0, 0.02, 0.04, 0.08],
    output_path="overhead.png"
)
```

---

### `plot_scaling_curve(n_workers_list, execution_times, theoretical_speedups=None, ...)`

Create a line plot showing how execution time scales with worker count.

**Parameters:**
- `n_workers_list` (list[int]): Worker counts
- `execution_times` (list[float]): Execution times for each worker count
- `theoretical_speedups` (list[float], optional): Theoretical speedup curve (Amdahl's Law)
- `output_path` (str, optional): Path to save plot (default: `amorsize_scaling_curve.png`)
- `title` (str): Chart title
- `figsize` (tuple): Figure size (width, height) in inches

**Returns:**
- Path to saved plot file

**Features:**
- Actual performance vs theoretical maximum
- Automatic log scale for large ranges
- Grid for easy reading

**Example:**
```python
plot_scaling_curve(
    [1, 2, 4, 8, 16],
    [10.0, 5.5, 3.2, 2.0, 1.5],
    theoretical_speedups=[10.0, 5.0, 2.5, 1.25, 0.625],
    output_path="scaling.png"
)
```

---

### `check_matplotlib()`

Check if matplotlib is available.

**Returns:**
- `True` if matplotlib is installed, `False` otherwise

**Example:**
```python
from amorsize import check_matplotlib

if check_matplotlib():
    print("Visualization features available!")
else:
    print("Install matplotlib: pip install matplotlib")
```

## Chart Examples

### Execution Time Comparison
Shows absolute execution times for each strategy. The fastest configuration is highlighted in green.

```python
visualize_comparison_result(result, output_dir="./charts", plots=['times'])
```

**What to look for:**
- ✅ Green bar = fastest strategy
- 📊 Bar height = execution time (lower is better)
- 🔍 Compare relative differences

### Speedup Visualization
Shows speedup relative to baseline (usually serial). Color-coded by performance:
- 🔴 Red: Slower than baseline (<1.0x)
- 🟠 Orange: Marginal improvement (1.0-1.2x)
- 🟡 Yellow: Moderate improvement (1.2-2.0x)
- 🟢 Green: Good improvement (>2.0x)

```python
visualize_comparison_result(result, output_dir="./charts", plots=['speedups'])
```

**What to look for:**
- ✅ Green bars = good parallelization
- ⚠️ Orange/Red bars = overhead dominates
- 📈 Higher bars = better speedup

## CLI Examples

### Basic Usage
```bash
python -m amorsize compare math.sqrt \
    --data-range 1000 \
    --configs "2,50" "4,25" "8,10" \
    --visualize ./output
```

### With Optimizer
```bash
python -m amorsize compare mymodule.process \
    --data-range 500 \
    --include-optimizer \
    --configs "Manual:4,20" \
    --visualize ./analysis
```

### Verbose Output
```bash
python -m amorsize compare math.factorial \
    --data-range 100 \
    --configs "2,20" "4,10" \
    --verbose \
    --visualize ./plots
```

## Integration with Existing Code

If you already have comparison code, add visualization with one line:

```python
# Existing code
result = compare_strategies(func, data, configs)
print(result)

# Add visualization
from amorsize import visualize_comparison_result
visualize_comparison_result(result, output_dir="./plots")
```

## Troubleshooting

### "Matplotlib is not available"

Install matplotlib:
```bash
pip install matplotlib
```

### Plots not generated

Check that the output directory is writable:
```python
import os
os.makedirs("./output", exist_ok=True)
paths = visualize_comparison_result(result, output_dir="./output")
```

### Plots look wrong

Adjust figure size:
```python
plot_comparison_times(
    names, times,
    figsize=(16, 10)  # Larger plot
)
```

### Long labels cut off

Use automatic layout:
```python
# Already handled automatically with plt.tight_layout()
# But you can increase figure width if needed
plot_comparison_times(names, times, figsize=(14, 6))
```

## Best Practices

1. **Always check matplotlib availability** before generating plots:
   ```python
   if check_matplotlib():
       visualize_comparison_result(result)
   ```

2. **Use meaningful configuration names** for better chart readability:
   ```python
   ComparisonConfig("Conservative (2 workers)", 2, 50)
   ```

3. **Generate visualizations in dedicated directories**:
   ```python
   visualize_comparison_result(result, output_dir="./analysis/run_001")
   ```

4. **Keep plot counts manageable** - comparing 3-5 strategies works best for readability

5. **Use verbose mode** to see progress when generating plots:
   ```bash
   python -m amorsize compare ... --visualize ./plots --verbose
   ```

## Examples

See `examples/visualization_demo.py` for comprehensive examples of all visualization features.

## Related Documentation

- [Comparison Mode](README_comparison_mode.md) - Strategy comparison basics
- [CLI Documentation](README_cli.md) - Command-line interface
- [Benchmark Validation](README_benchmark_validation.md) - Verify optimizer accuracy

## Summary

Visualization makes it easy to:
- ✅ Quickly identify the best parallelization strategy
- ✅ Understand performance trade-offs at a glance
- ✅ Share results with stakeholders using professional charts
- ✅ Document optimization decisions with visual evidence

Generate your first visualization:
```python
from amorsize import compare_strategies, visualize_comparison_result, ComparisonConfig

result = compare_strategies(my_func, my_data, [
    ComparisonConfig("Serial", 1),
    ComparisonConfig("Parallel", 4, 25)
])

visualize_comparison_result(result, output_dir="./plots")
```
