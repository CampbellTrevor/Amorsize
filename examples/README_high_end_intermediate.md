# Intermediate n_jobs for High-End Systems

## Overview

This example demonstrates how to achieve intermediate `n_jobs` values (between 1 and maximum cores) on high-end systems with many cores and large amounts of RAM.

## The Challenge

On high-resource systems (e.g., 96 cores, 700GB RAM), typical workloads don't trigger memory constraints because the system has abundant resources. This is actually **correct behavior** - the system should use all available cores when memory is not a limiting factor.

However, for demonstration and real-world scenarios involving truly memory-intensive tasks, this example shows when and how intermediate values occur.

## The Math

Amorsize calculates the maximum workers based on memory constraints:

```
max_workers = min(physical_cores, usable_ram / memory_per_task)
```

Where `usable_ram = available_ram * 0.8` (leaving 20% headroom for the system).

### For a 96-core, 700GB RAM system:

```
usable_ram = 700GB * 0.8 = 560GB
```

To get intermediate n_jobs (less than 96 workers), we need:

```
memory_per_task > usable_ram / 96
memory_per_task > 560GB / 96
memory_per_task > 5.83GB
```

Therefore, tasks using **6GB or more** of memory will trigger intermediate n_jobs values on this system.

## Example Scenarios

### Scenario 1: Huge Memory Task (~6GB/task)
```
Calculation: 560GB / 6GB ≈ 93 workers
Result: Recommends 93 workers (not all 96)
```

### Scenario 2: Very Huge Memory Task (~12GB/task)
```
Calculation: 560GB / 12GB ≈ 46 workers
Result: Recommends 46 workers (about half the cores)
```

### Scenario 3: Extreme Memory Task (~24GB/task)
```
Calculation: 560GB / 24GB ≈ 23 workers
Result: Recommends 23 workers (about 1/4 of cores)
```

### Scenario 4: Super Extreme Memory Task (~48GB/task)
```
Calculation: 560GB / 48GB ≈ 11 workers
Result: Recommends 11 workers (about 1/9 of cores)
```

## Running the Example

```bash
python examples/high_end_system_intermediate.py
```

**Note:** This example uses `sample_size=2` for faster demonstration. In production, the default `sample_size=5` is recommended.

## Real-World Applications

Tasks that commonly require 6GB+ of memory per worker include:

1. **Scientific Computing**
   - Large matrix operations (10K x 10K matrices)
   - Genomic sequence analysis
   - Climate modeling with high-resolution grids

2. **Machine Learning**
   - Training large neural networks
   - Processing high-resolution images (8K+)
   - Large-scale feature extraction

3. **Data Processing**
   - Processing massive DataFrames (billions of rows)
   - Video processing with multiple frame buffers
   - 3D rendering with high-poly models

4. **Database Operations**
   - In-memory database queries with large result sets
   - Data warehouse operations
   - Large-scale ETL transformations

## Why This Matters

Without Amorsize's memory-aware optimization:

- **Spawning 96 workers** with 12GB tasks = 1,152GB required
- **System only has 700GB** → OOM killer would terminate processes
- **Result:** System instability, crashed processes, poor performance

With Amorsize's optimization:

- **Spawning 46 workers** with 12GB tasks = 552GB required
- **System has 560GB usable** → Safe operation
- **Result:** Stable, optimal performance without crashes

## Key Takeaway

Amorsize's intermediate n_jobs feature is **system-dependent by design**:

- **Low-resource systems** (4 cores, 4GB RAM): 100MB tasks trigger constraints
- **High-resource systems** (96 cores, 700GB RAM): 6GB+ tasks trigger constraints

This adaptive behavior ensures optimal performance while preventing resource exhaustion across all system configurations.
