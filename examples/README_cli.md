# Amorsize CLI Interface

The Amorsize CLI provides a command-line interface for analyzing and executing parallelized Python functions without writing code.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [optimize](#optimize-command)
  - [execute](#execute-command)
- [Data Sources](#data-sources)
- [Output Formats](#output-formats)
- [Options](#options)
- [Examples](#examples)
- [Use Cases](#use-cases)

## Installation

The CLI is included with Amorsize. No additional installation required:

```bash
pip install -e .
```

## Quick Start

```bash
# Analyze a function for optimal parallelization
python -m amorsize optimize math.sqrt --data-range 1000

# Execute a function with automatic optimization
python -m amorsize execute mymodule.process --data-range 100

# Get JSON output for scripting
python -m amorsize optimize math.factorial --data-range 100 --json
```

## Commands

### optimize Command

Analyze a function and recommend optimal parallelization parameters without executing it.

**Syntax:**
```bash
python -m amorsize optimize <function> <data-source> [options]
```

**Output:**
- Recommended `n_jobs` (number of workers)
- Recommended `chunksize` (items per chunk)
- Estimated speedup vs serial execution
- Explanation of decision
- Warnings (if any)

**Example:**
```bash
python -m amorsize optimize math.sqrt --data-range 1000
```

**Output:**
```
======================================================================
OPTIMIZATION ANALYSIS
======================================================================

Recommendation:
  n_jobs:            1
  chunksize:         1
  estimated_speedup: 1.00x

Reason:
  Function is too fast (< 1ms) - parallelization overhead would dominate
```

### execute Command

Optimize and execute a function on data, returning the results.

**Syntax:**
```bash
python -m amorsize execute <function> <data-source> [options]
```

**Output:**
- Execution results (sample shown)
- Optimization details (n_jobs, chunksize, speedup)

**Example:**
```bash
python -m amorsize execute mymodule.square --data-range 10 --json
```

**Output:**
```json
{
  "mode": "execute",
  "results_count": 10,
  "sample_results": [0, 1, 4, 9, 16, 25, 36, 49, 64, 81],
  "optimization": {
    "n_jobs": 1,
    "chunksize": 1,
    "estimated_speedup": 1.0,
    "reason": "Function is too fast..."
  }
}
```

## Data Sources

The CLI supports three ways to provide input data:

### 1. Range (--data-range N)

Generate a range of integers from 0 to N-1.

```bash
python -m amorsize optimize math.sqrt --data-range 1000
# Data: [0, 1, 2, ..., 999]
```

**Use case:** Testing, benchmarking, numeric computations

### 2. File (--data-file FILE)

Read data from a file, one item per line.

```bash
# Create data file
echo -e "1\n2\n3\n4\n5" > numbers.txt

# Use it
python -m amorsize execute mymodule.process --data-file numbers.txt
```

**Use case:** Processing lists of IDs, URLs, file paths, records

### 3. Stdin (--data-stdin)

Read data from standard input for Unix pipelines.

```bash
cat urls.txt | python -m amorsize execute mymodule.fetch --data-stdin

# Or from command output
find . -name "*.log" | python -m amorsize execute mymodule.analyze --data-stdin
```

**Use case:** Shell scripts, pipelines, automation

## Output Formats

### Human-Readable (Default)

Formatted, easy-to-read output with sections and labels.

```bash
python -m amorsize optimize math.sqrt --data-range 1000
```

### JSON (--json)

Machine-readable JSON for scripting and automation.

```bash
python -m amorsize optimize math.sqrt --data-range 1000 --json
```

**Parse with jq:**
```bash
# Extract n_jobs
n_jobs=$(python -m amorsize optimize math.sqrt --data-range 1000 --json | jq '.n_jobs')

# Check if parallelization recommended
speedup=$(python -m amorsize optimize mymodule.func --data-range 100 --json | jq '.estimated_speedup')
if (( $(echo "$speedup > 1.5" | bc -l) )); then
    echo "Parallelization recommended!"
fi
```

## Options

### Optimization Parameters

- `--sample-size N` - Number of items to sample (default: 5)
- `--target-chunk-duration SECONDS` - Target duration per chunk (default: 0.2)

### Output Control

- `--json` - Output as JSON instead of human-readable
- `--verbose, -v` - Show detailed progress and decision-making
- `--profile, -p` - Show comprehensive diagnostic profile

### Benchmarking Control

- `--no-spawn-benchmark` - Use OS-based spawn cost estimate (faster but less accurate)
- `--no-chunking-benchmark` - Use default chunking overhead estimate
- `--no-auto-adjust` - Disable automatic n_jobs adjustment for nested parallelism

### Help

- `--help, -h` - Show help message
- `--version` - Show version number

## Examples

### 1. Basic Analysis

Analyze if a function should be parallelized:

```bash
python -m amorsize optimize math.factorial --data-range 100
```

### 2. Execute with File Input

Process data from a file:

```bash
# Create input file
echo -e "apple\nbanana\ncherry" > fruits.txt

# Process it
python -m amorsize execute mymodule.process_fruit --data-file fruits.txt
```

### 3. Pipeline Integration

Use in Unix pipelines:

```bash
# Find and process log files
find /var/log -name "*.log" | \
  python -m amorsize execute mymodule.analyze_log --data-stdin --json
```

### 4. Detailed Profiling

Get comprehensive analysis:

```bash
python -m amorsize optimize mymodule.expensive_func \
  --data-range 1000 \
  --profile \
  --verbose
```

**Shows:**
- Workload analysis (execution time, overhead)
- System resources (cores, spawn cost)
- Optimization decision (n_jobs, chunksize)
- Performance prediction (speedup, efficiency)
- Overhead breakdown (spawn %, IPC %, chunking %)

### 5. JSON for CI/CD

Use in automated testing or deployment:

```bash
# Save optimization report
python -m amorsize optimize myapp.process \
  --data-range 10000 \
  --profile \
  --json > optimization_report.json

# Check if parallelization worthwhile
if [ $(cat optimization_report.json | jq '.n_jobs') -gt 1 ]; then
    echo "Deploy with parallelization enabled"
else
    echo "Deploy in serial mode"
fi
```

### 6. Custom Parameters

Fine-tune the analysis:

```bash
python -m amorsize optimize mymodule.func \
  --data-range 1000 \
  --sample-size 10 \
  --target-chunk-duration 0.5 \
  --verbose
```

### 7. Fast Analysis

Skip benchmarks for quicker results:

```bash
python -m amorsize optimize mymodule.func \
  --data-range 1000 \
  --no-spawn-benchmark \
  --no-chunking-benchmark
```

**Note:** This uses OS-based estimates instead of measurements. Results are less accurate but ~25ms faster.

### 8. Function from Different Module

Use functions from any installed module:

```bash
# Standard library
python -m amorsize optimize math.sqrt --data-range 1000

# Your module (dot notation)
python -m amorsize optimize mypackage.mymodule.myfunction --data-range 100

# Your module (colon notation)
python -m amorsize optimize mypackage.mymodule:myfunction --data-range 100
```

## Use Cases

### 1. Quick Performance Testing

Test if a function is worth parallelizing without writing code:

```bash
python -m amorsize optimize mymodule.new_algorithm --data-range 10000 --profile
```

### 2. Shell Script Integration

Use optimal parallelization in shell scripts:

```bash
#!/bin/bash
# Analyze and save parameters
python -m amorsize optimize mymodule.process --data-range 1000 --json > params.json

# Extract parameters
n_jobs=$(cat params.json | jq '.n_jobs')
chunksize=$(cat params.json | jq '.chunksize')

echo "Using n_jobs=$n_jobs, chunksize=$chunksize"

# Run your Python script with these parameters
python my_script.py --n-jobs $n_jobs --chunksize $chunksize
```

### 3. Data Pipeline Processing

Process files in a pipeline:

```bash
# Process all CSV files in a directory
find data/ -name "*.csv" | \
  python -m amorsize execute myapp.process_csv --data-stdin --verbose
```

### 4. Benchmarking Tool

Compare different implementations:

```bash
# Test implementation A
python -m amorsize optimize mymodule.algorithm_a --data-range 1000 --json > report_a.json

# Test implementation B
python -m amorsize optimize mymodule.algorithm_b --data-range 1000 --json > report_b.json

# Compare speedups
speedup_a=$(cat report_a.json | jq '.estimated_speedup')
speedup_b=$(cat report_b.json | jq '.estimated_speedup')
echo "Algorithm A speedup: $speedup_a"
echo "Algorithm B speedup: $speedup_b"
```

### 5. CI/CD Integration

Add parallelization analysis to CI pipeline:

```yaml
# .gitlab-ci.yml
test_parallelization:
  script:
    - python -m amorsize optimize myapp.critical_function --data-range 10000 --json > report.json
    - |
      if [ $(cat report.json | jq '.estimated_speedup') -lt 1.5 ]; then
        echo "Warning: Parallelization provides minimal benefit"
      fi
  artifacts:
    paths:
      - report.json
```

### 6. Documentation Generation

Generate performance documentation:

```bash
# Analyze all critical functions
for func in process_image analyze_data compute_result; do
  echo "Analyzing $func..."
  python -m amorsize optimize myapp.$func \
    --data-range 1000 \
    --profile > docs/performance_$func.txt
done
```

### 7. Educational Tool

Learn about parallelization overhead:

```bash
# Compare fast vs slow functions
python -m amorsize optimize math.sqrt --data-range 1000 --profile --verbose
python -m amorsize optimize math.factorial --data-range 100 --profile --verbose
```

**Shows:**
- Why fast functions shouldn't be parallelized
- How overhead affects decision
- Break-even points for parallelization

## Function Loading

The CLI can load functions from any installed Python module using two notations:

**Dot notation:**
```bash
python -m amorsize optimize module.submodule.function --data-range 100
```

**Colon notation:**
```bash
python -m amorsize optimize module.submodule:function --data-range 100
```

**Requirements:**
- Module must be importable (installed or in PYTHONPATH)
- Function must be picklable (module-level, not nested)
- Function must accept a single argument

## Tips and Best Practices

### 1. Start with Small Samples

Use smaller `--sample-size` for quick initial analysis:

```bash
python -m amorsize optimize mymodule.func --data-range 10000 --sample-size 3
```

### 2. Use JSON for Automation

Always use `--json` when scripting:

```bash
result=$(python -m amorsize optimize mymodule.func --data-range 1000 --json)
n_jobs=$(echo $result | jq '.n_jobs')
```

### 3. Profile Unexpected Results

If results are unexpected, use `--profile --verbose`:

```bash
python -m amorsize optimize mymodule.func --data-range 1000 --profile --verbose
```

This shows the complete decision-making process.

### 4. Test with Representative Data

Use `--data-file` with representative sample data:

```bash
# Create sample of real data
head -n 100 production_data.csv > sample.csv

# Analyze
python -m amorsize optimize mymodule.process --data-file sample.csv --profile
```

### 5. Disable Benchmarks for Quick Tests

When iterating quickly:

```bash
python -m amorsize optimize mymodule.func \
  --data-range 1000 \
  --no-spawn-benchmark \
  --no-chunking-benchmark
```

### 6. Check for Nested Parallelism

If using NumPy, SciPy, PyTorch, etc., let auto-adjustment work:

```bash
# Auto-adjustment enabled by default
python -m amorsize optimize mymodule.numpy_func --data-range 1000 --verbose
```

Look for messages about detected nested parallelism.

## Troubleshooting

### Function Not Found

**Error:** `Module 'mymodule' has no function 'myfunc'`

**Solutions:**
- Verify function name: `python -c "import mymodule; print(dir(mymodule))"`
- Check module is importable: `python -c "import mymodule"`
- Use correct notation: `module.function` or `module:function`

### Import Error

**Error:** `Cannot import module 'mymodule'`

**Solutions:**
- Install module: `pip install mymodule`
- Check PYTHONPATH: `export PYTHONPATH=/path/to/module:$PYTHONPATH`
- Run from correct directory: `cd /project/root && python -m amorsize ...`

### Function Not Callable

**Error:** `'mymodule.thing' is not a callable function`

**Solution:**
- Verify it's a function: `python -c "import mymodule; print(callable(mymodule.thing))"`
- Don't use constants or classes directly

### Data File Issues

**Error:** `Cannot read data file 'data.txt'`

**Solutions:**
- Check file exists: `ls -l data.txt`
- Check permissions: `chmod +r data.txt`
- Use absolute path: `--data-file /full/path/to/data.txt`

## See Also

- [Main README](../README.md) - Library overview and Python API
- [Examples](../examples/) - More code examples
- [CLI Examples](cli_examples.py) - Comprehensive CLI examples

## Feedback

Have suggestions for CLI improvements? Open an issue or pull request!

