# Configuration Export/Import Guide

Save and reuse optimal parallelization configurations across runs and share them between team members.

## Table of Contents
- [Quick Start](#quick-start)
- [Overview](#overview)
- [Python API](#python-api)
- [CLI Usage](#cli-usage)
- [Configuration Format](#configuration-format)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Save a configuration from optimization:
```python
from amorsize import optimize

def expensive_func(x):
    return sum(i**2 for i in range(x))

result = optimize(expensive_func, range(1000))
result.save_config('production.json', function_name='expensive_func')
```

### Load and use a configuration:
```python
from amorsize import load_config
from multiprocessing import Pool

config = load_config('production.json')
print(f"Using n_jobs={config.n_jobs}, chunksize={config.chunksize}")

with Pool(config.n_jobs) as pool:
    results = pool.map(expensive_func, data, chunksize=config.chunksize)
```

## Overview

The configuration export/import system allows you to:

1. **Save Optimizations**: Store optimal `n_jobs` and `chunksize` parameters discovered through `optimize()` or `tune_parameters()`
2. **Reuse Configurations**: Apply saved configurations to future runs without re-optimizing
3. **Share Settings**: Distribute configurations across team members or deployment environments
4. **Track Metadata**: Preserve system information, timestamps, and notes for context

### When to Use Configurations

✅ **Use saved configurations when:**
- You're running the same workload repeatedly with similar data sizes
- You want consistent performance in production
- You've empirically validated optimal parameters through tuning
- You're deploying to similar hardware configurations
- You want to skip optimization overhead

❌ **Don't use saved configurations when:**
- Hardware or data characteristics have changed significantly
- You're processing drastically different data sizes
- System resources (CPU, memory) are different from where config was generated
- You need adaptive parameter selection

## Python API

### Saving Configurations

#### From OptimizationResult
```python
from amorsize import optimize

result = optimize(my_func, data, profile=True)
result.save_config(
    'my_config.json',
    function_name='my_func',
    notes='Optimized for medium datasets (1K-10K items)',
    overwrite=False  # Prevents accidental overwrite
)
```

#### From TuningResult
```python
from amorsize import tune_parameters

result = tune_parameters(my_func, data)
result.save_config(
    'tuned_config.json',
    function_name='my_func',
    notes='Empirically tuned - best of 45 configurations'
)
```

#### Manual Configuration Creation
```python
from amorsize import ConfigData, save_config

config = ConfigData(
    n_jobs=4,
    chunksize=100,
    executor_type='process',
    estimated_speedup=3.5,
    function_name='batch_processor',
    notes='Hand-tuned for production workload'
)

save_config(config, 'manual_config.json')
```

### Loading Configurations

#### Basic Loading
```python
from amorsize import load_config

config = load_config('my_config.json')
print(config)
# Configuration (optimize):
#   n_jobs:           4
#   chunksize:        100
#   executor_type:    process
#   estimated_speedup: 3.50x
#   function:         my_func
#   ...
```

#### Using Loaded Configuration
```python
from amorsize import load_config
from multiprocessing import Pool

config = load_config('production.json')

# Apply to multiprocessing.Pool
with Pool(config.n_jobs) as pool:
    results = pool.map(func, data, chunksize=config.chunksize)
```

#### Using with ThreadPoolExecutor
```python
from amorsize import load_config
from concurrent.futures import ThreadPoolExecutor

config = load_config('io_workload.json')

if config.executor_type == 'thread':
    with ThreadPoolExecutor(max_workers=config.n_jobs) as executor:
        results = list(executor.map(func, data))
```

### Configuration Management

#### List Available Configurations
```python
from amorsize import list_configs

# List configs in current directory
configs = list_configs('.')
for config_path in configs:
    config = load_config(config_path)
    print(f"{config_path.name}: {config.n_jobs} workers, {config.chunksize} chunksize")
```

#### Use Default Config Directory
```python
from amorsize import get_default_config_dir, save_config, load_config

# Get default directory (~/.amorsize/configs)
config_dir = get_default_config_dir()
print(f"Configs stored in: {config_dir}")

# Save to default location
result.save_config(config_dir / 'my_app.json')

# Load from default location
config = load_config(config_dir / 'my_app.json')
```

## CLI Usage

### Save Configuration from Optimize

```bash
# Analyze and save configuration
python -m amorsize optimize mymodule.func --data-range 1000 \
    --save-config production_config.json
```

### Save Configuration from Tuning

```bash
# Auto-tune and save best configuration
python -m amorsize tune mymodule.func --data-range 1000 \
    --quick \
    --save-config tuned_config.json
```

### Execute with Loaded Configuration

```bash
# Skip optimization and use saved config
python -m amorsize execute mymodule.func --data-range 5000 \
    --load-config production_config.json
```

This is much faster than normal execution because it skips the optimization phase entirely.

### Complete Workflow Example

```bash
# Step 1: Find optimal parameters (one-time setup)
python -m amorsize optimize data_processor.process --data-range 10000 \
    --profile \
    --save-config processor_config.json

# Step 2: Use configuration in production (repeated)
python -m amorsize execute data_processor.process \
    --data-file production_data.txt \
    --load-config processor_config.json
```

## Configuration Format

Configurations are stored as JSON (or YAML with PyYAML installed):

### JSON Format
```json
{
  "n_jobs": 4,
  "chunksize": 100,
  "executor_type": "process",
  "estimated_speedup": 3.5,
  "function_name": "expensive_func",
  "data_size": 1000,
  "avg_execution_time": 0.001,
  "notes": "Optimized for production workload",
  "source": "optimize",
  "system_info": {
    "platform": "Linux",
    "python_version": "3.10.0",
    "physical_cores": 8,
    "available_memory": 16777216000,
    "start_method": "fork"
  },
  "timestamp": "2026-01-09T12:00:00.000000",
  "amorsize_version": "0.1.0"
}
```

### YAML Format
```yaml
n_jobs: 4
chunksize: 100
executor_type: process
estimated_speedup: 3.5
function_name: expensive_func
notes: Production configuration
source: tune
system_info:
  platform: Linux
  physical_cores: 8
timestamp: '2026-01-09T12:00:00.000000'
```

### Field Descriptions

- **n_jobs**: Number of parallel workers
- **chunksize**: Items per chunk for task distribution
- **executor_type**: `'process'` or `'thread'`
- **estimated_speedup**: Expected speedup over serial execution
- **function_name**: Name of the function (for documentation)
- **data_size**: Number of items used during optimization (if available)
- **avg_execution_time**: Average time per item in seconds (if available)
- **notes**: User-provided notes
- **source**: How config was generated (`'optimize'`, `'tune'`, or `'manual'`)
- **system_info**: Hardware/OS details from when config was created
- **timestamp**: When configuration was created
- **amorsize_version**: Version of Amorsize used

## Use Cases

### 1. Production Deployment

Optimize once during development, deploy configuration to production:

```python
# Development: Find optimal parameters
from amorsize import optimize

result = optimize(process_batch, sample_data, profile=True)
result.save_config('configs/production.json', 
                  function_name='process_batch',
                  notes='Optimized for 10K item batches')

# Production: Use saved configuration
from amorsize import load_config
from multiprocessing import Pool

config = load_config('configs/production.json')
with Pool(config.n_jobs) as pool:
    results = pool.map(process_batch, production_data, 
                      chunksize=config.chunksize)
```

### 2. Team Collaboration

Share optimal configurations across team members:

```bash
# Team member A: Finds optimal configuration
python -m amorsize tune image_processor.transform --data-range 1000 \
    --save-config shared/image_transform.json

# Commit to repo
git add shared/image_transform.json
git commit -m "Add optimal config for image processing"

# Team member B: Uses shared configuration
git pull
python -m amorsize execute image_processor.transform \
    --data-file images.txt \
    --load-config shared/image_transform.json
```

### 3. Multi-Environment Deployment

Create environment-specific configurations:

```python
# configs/development.json - Optimize for fast iteration
{
  "n_jobs": 2,
  "chunksize": 50,
  "notes": "Development - fast startup, good debuggability"
}

# configs/staging.json - Balanced performance
{
  "n_jobs": 4,
  "chunksize": 100,
  "notes": "Staging - production-like performance"
}

# configs/production.json - Maximum throughput
{
  "n_jobs": 16,
  "chunksize": 500,
  "notes": "Production - optimized for throughput"
}
```

Load based on environment:
```python
import os
from amorsize import load_config

env = os.getenv('ENV', 'development')
config = load_config(f'configs/{env}.json')
```

### 4. Workload-Specific Configurations

Different configurations for different workload types:

```python
# Small batches (< 1000 items)
result_small = optimize(func, small_data)
result_small.save_config('configs/small_batch.json')

# Large batches (> 10000 items)
result_large = optimize(func, large_data)
result_large.save_config('configs/large_batch.json')

# Use appropriate config based on data size
data_size = len(data)
if data_size < 1000:
    config = load_config('configs/small_batch.json')
else:
    config = load_config('configs/large_batch.json')
```

### 5. A/B Testing Performance

Compare configurations empirically:

```python
from amorsize import load_config, validate_optimization

config_a = load_config('config_a.json')
config_b = load_config('config_b.json')

# Test configuration A
result_a = validate_optimization(func, test_data, 
                                 n_jobs=config_a.n_jobs,
                                 chunksize=config_a.chunksize)

# Test configuration B
result_b = validate_optimization(func, test_data,
                                 n_jobs=config_b.n_jobs,
                                 chunksize=config_b.chunksize)

print(f"Config A: {result_a.actual_speedup:.2f}x")
print(f"Config B: {result_b.actual_speedup:.2f}x")
```

## Best Practices

### 1. Include Descriptive Notes

```python
result.save_config('config.json',
    function_name='batch_processor',
    notes='Optimized for 5K-10K item batches on 8-core machines. '
          'Validated with 95% CPU-bound workload. '
          'Expected speedup: 6.5x over serial.'
)
```

### 2. Validate Configurations on Target Hardware

```python
from amorsize import load_config, validate_optimization

# Load configuration optimized on different hardware
config = load_config('shared_config.json')

# Validate it works well on this system
result = validate_optimization(
    func, sample_data,
    n_jobs=config.n_jobs,
    chunksize=config.chunksize,
    verbose=True
)

if result.accuracy_percent < 90:
    print("Warning: Configuration may not be optimal for this system")
    print(f"Predicted: {config.estimated_speedup:.2f}x")
    print(f"Actual: {result.actual_speedup:.2f}x")
```

### 3. Version Control Configurations

Store configurations in version control alongside code:

```
project/
├── src/
│   └── processors.py
├── configs/
│   ├── development.json
│   ├── staging.json
│   └── production.json
└── README.md
```

### 4. Document System Requirements

```python
# In your configuration notes
result.save_config('config.json',
    notes='''
    System Requirements:
    - 8+ physical CPU cores
    - 16+ GB RAM
    - Python 3.8+
    - Linux (fork start method)
    
    Workload Characteristics:
    - CPU-bound computation
    - 5K-10K items per batch
    - ~1ms per item
    '''
)
```

### 5. Regular Re-validation

```python
# Periodically re-run optimization to check if config is still optimal
from amorsize import optimize, load_config

current_config = load_config('production.json')
fresh_result = optimize(func, representative_data)

if abs(fresh_result.n_jobs - current_config.n_jobs) > 2:
    print("Warning: Optimal n_jobs has changed significantly")
    print(f"Current config: {current_config.n_jobs}")
    print(f"New optimal: {fresh_result.n_jobs}")
```

## Troubleshooting

### Configuration Not Found

```python
from pathlib import Path
from amorsize import load_config

config_path = Path('my_config.json')
if not config_path.exists():
    print(f"Configuration not found: {config_path}")
    print(f"Available configs: {list(Path('.').glob('*.json'))}")
else:
    config = load_config(config_path)
```

### Invalid Configuration File

```python
from amorsize import load_config

try:
    config = load_config('broken_config.json')
except ValueError as e:
    print(f"Invalid configuration: {e}")
    # Fall back to optimization
    from amorsize import optimize
    config = optimize(func, data)
```

### System Mismatch Warning

When a configuration was created on different hardware:

```python
config = load_config('external_config.json')

# Check system compatibility
import platform
from amorsize import get_physical_cores

if platform.system() != config.system_info.get('platform'):
    print(f"Warning: Config from {config.system_info['platform']}, "
          f"running on {platform.system()}")

if get_physical_cores() != config.system_info.get('physical_cores'):
    print(f"Warning: Config optimized for "
          f"{config.system_info['physical_cores']} cores, "
          f"this system has {get_physical_cores()} cores")
```

### Overwrite Protection

```python
from amorsize import save_config, ConfigData

config = ConfigData(n_jobs=4, chunksize=100)

try:
    save_config(config, 'existing_config.json', overwrite=False)
except FileExistsError:
    print("Configuration already exists")
    # Either use a different name or set overwrite=True
    save_config(config, 'existing_config.json', overwrite=True)
```

### YAML Support

YAML requires PyYAML to be installed:

```bash
pip install pyyaml
```

```python
from amorsize import save_config, ConfigData

config = ConfigData(n_jobs=4, chunksize=100)

try:
    save_config(config, 'config.yaml', format='yaml')
except ImportError:
    print("YAML support requires PyYAML: pip install pyyaml")
    # Fall back to JSON
    save_config(config, 'config.json', format='json')
```

## See Also

- [Optimizer Guide](README.md) - Understanding how parameters are determined
- [Tuning Guide](README_tuning.md) - Auto-tuning for empirical optimization
- [History Guide](README_history.md) - Tracking results over time
- [CLI Guide](README_cli.md) - Command-line usage
