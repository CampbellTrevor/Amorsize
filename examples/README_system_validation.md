# System Validation Tool

Comprehensive guide to Amorsize's system validation tool for verifying installation health and measurement accuracy.

## Overview

The system validation tool provides confidence that Amorsize's core measurements (spawn cost, chunking overhead, pickle overhead) are working correctly on your specific system. This is critical because:

1. **Spawn cost varies dramatically** - 15ms for fork vs 200ms for spawn
2. **Chunking overhead is system-dependent** - faster on bare metal, slower in containers
3. **Pickle overhead depends on Python version** - optimization improvements over time
4. **Users need confidence in recommendations** - validation proves measurements are accurate

## Quick Start

### Basic Usage

```python
from amorsize import validate_system

# Run validation
result = validate_system(verbose=True)

# Print report
print(result)

# Check health
if result.overall_health in ["excellent", "good"]:
    print("✅ System is healthy!")
else:
    print("⚠️ Some issues detected")
```

### Command Line

```bash
# Run validation from command line
python -m amorsize.validation

# Exit code:
#   0 - excellent or good health
#   1 - poor or critical health
```

## What Gets Validated

The validation tool runs 5 comprehensive checks:

### 1. Multiprocessing Basic Functionality
- Tests that `Pool.map()` works correctly
- Verifies results match expected output
- Essential for any parallelization to work

**What it checks:**
- ✅ Pool creation succeeds
- ✅ Workers execute functions correctly
- ✅ Results are returned properly

**Common issues:**
- Restricted environments (some Docker containers, notebooks)
- Missing multiprocessing support
- Start method incompatibilities

### 2. System Resource Detection
- Detects physical CPU cores
- Measures available memory
- Identifies multiprocessing start method

**What it checks:**
- ✅ Physical cores detected (1-256 range)
- ✅ Memory detection works
- ✅ Start method is valid (fork/spawn/forkserver)

**Common issues:**
- psutil not installed (reduced accuracy)
- Container resource limits not detected
- Unusual system configurations

### 3. Spawn Cost Measurement
- Measures actual per-worker spawn cost
- Compares against OS-based estimate
- Validates reasonable bounds (1ms - 5s)

**What it checks:**
- ✅ Measurement completes without errors
- ✅ Value is within reasonable bounds
- ✅ Consistent with OS estimate (within 10x)

**Expected values:**
- Fork (Linux): 1-20ms
- Spawn (Windows/macOS): 100-500ms
- Forkserver: 50-150ms

**Common issues:**
- High system load causes variance
- Containers have higher overhead
- Warm vs cold measurements differ

### 4. Chunking Overhead Measurement
- Measures per-chunk task distribution overhead
- Tests with different chunk sizes
- Validates reasonable bounds (0.01ms - 100ms)

**What it checks:**
- ✅ Measurement completes without errors
- ✅ Value is within reasonable bounds
- ✅ Measurement is stable

**Expected values:**
- Typical: 0.01-1ms per chunk
- Fast systems: < 0.1ms
- Slow systems: 1-10ms

**Common issues:**
- I/O-bound systems have higher overhead
- Network file systems slow down chunking
- Container overhead affects distribution

### 5. Pickle Overhead Measurement
- Tests pickling of various data types
- Measures serialization and deserialization time
- Validates reasonable performance

**What it checks:**
- ✅ Pickling works for common types
- ✅ Serialization time is reasonable
- ✅ Sizes match expectations

**Data types tested:**
- Integers, strings, lists, dicts
- Small and medium-sized objects
- Nested structures

## Understanding Results

### Health Ratings

**Excellent (95%+ pass rate, no errors):**
- ✅ All measurements working correctly
- ✅ System fully supported
- ✅ Optimizer recommendations will be highly accurate

**Good (80%+ pass rate, ≤1 error):**
- ✓ Core functionality working
- ✓ Minor issues detected
- ✓ Optimizer should work well

**Poor (60%+ pass rate):**
- ⚠️ Multiple issues detected
- ⚠️ Optimizer may not work optimally
- ⚠️ Review warnings and errors

**Critical (<60% pass rate):**
- ❌ Serious issues detected
- ❌ Library may not function correctly
- ❌ Installation or environment problems

### Reading the Report

```
============================================================
AMORSIZE SYSTEM VALIDATION REPORT
============================================================

Overall Health: ✅ EXCELLENT
Checks Passed: 5/5

WARNINGS:
  ⚠️  Measured cost differs from estimate by 0.1x (expected within 10x)

DETAILS:
  • multiprocessing_basic:
      execution_time: 12.27ms
      workers: 2
      data_size: 10
      result: Pool.map() works correctly
  • system_resources:
      physical_cores: 2
      available_memory: 1.00GB
      multiprocessing_start_method: fork
  • spawn_cost_measurement:
      measured_spawn_cost: 1.09ms
      measurement_time: 0.01s
      os_estimate: 15.00ms
      start_method: fork
      measurement_vs_estimate: 0.07x
      warning: Measured cost differs from estimate by 0.1x
  • chunking_overhead_measurement:
      measured_overhead: 0.052ms
      measurement_time: 0.01s
  • pickle_overhead_measurement:
      small_int_pickle_time: 5.89μs
      small_int_size: 5B
      ...
============================================================
```

## Programmatic Usage

### Access Validation Details

```python
from amorsize import validate_system

result = validate_system(verbose=False)

# Check overall health
print(f"Health: {result.overall_health}")
print(f"Passed: {result.checks_passed}/{result.checks_passed + result.checks_failed}")

# Check for specific issues
if result.errors:
    print("Errors detected:")
    for error in result.errors:
        print(f"  • {error}")

if result.warnings:
    print("Warnings:")
    for warning in result.warnings:
        print(f"  • {warning}")

# Access detailed measurements
spawn_cost = result.details['spawn_cost_measurement']
print(f"Spawn cost: {spawn_cost['measured_spawn_cost']}")

cores = result.details['system_resources']['physical_cores']
print(f"Physical cores: {cores}")
```

### CI/CD Integration

```python
import sys
from amorsize import validate_system

def ci_health_check():
    """Run validation in CI/CD pipeline."""
    result = validate_system(verbose=True)
    
    # Fail build on critical issues
    if result.overall_health == "critical":
        print("❌ Critical system issues - failing build")
        sys.exit(1)
    
    # Warn on poor health
    elif result.overall_health == "poor":
        print("⚠️ System health is poor - review warnings")
        # Continue but log warnings
    
    else:
        print("✅ System validation passed")
        sys.exit(0)

if __name__ == "__main__":
    ci_health_check()
```

### Conditional Behavior

```python
from amorsize import validate_system

result = validate_system(verbose=False)

# Adjust behavior based on system characteristics
if result.overall_health in ["excellent", "good"]:
    # Use optimizer with confidence
    from amorsize import optimize
    result = optimize(my_func, data)
else:
    # Fall back to conservative settings
    print("System issues detected - using serial execution")
    results = [my_func(x) for x in data]
```

## Troubleshooting

### Common Issues and Solutions

**Issue: "Multiprocessing not working"**
- **Cause:** Restricted environment (container, notebook, sandbox)
- **Solution:** 
  ```python
  import multiprocessing
  multiprocessing.set_start_method('spawn')  # Try different method
  ```
- **Alternative:** Use in less restricted environment

**Issue: "Spawn cost differs from estimate by 10x+"**
- **Cause:** System-specific characteristics (normal for fork on Linux)
- **Impact:** None - this is actually accurate measurement
- **Action:** No action needed - validation is working correctly

**Issue: "Very low available memory"**
- **Cause:** Container memory limits or system memory pressure
- **Solution:** 
  - Increase container memory limits
  - Use batch processing: `process_in_batches()`
  - Close other applications

**Issue: "Physical cores outside reasonable range"**
- **Cause:** Detection failure or unusual system
- **Solution:** 
  ```bash
  pip install psutil  # For better core detection
  ```
- **Fallback:** Manual specification in optimize()

### When Validation Fails

If validation consistently fails:

1. **Check Python version:** Requires Python 3.7+
2. **Check multiprocessing:** Some environments restrict it
3. **Install psutil:** `pip install psutil` for better detection
4. **Check permissions:** Container/sandbox restrictions
5. **Review logs:** Enable verbose mode for details

### Platform-Specific Notes

**Linux (fork start method):**
- Spawn cost will be very low (1-20ms)
- This is normal - fork is fast
- Measurement may be 10x lower than estimate

**Windows/macOS (spawn start method):**
- Spawn cost will be higher (100-500ms)
- This is normal - spawn is slow
- Factor this into workload decisions

**Containers (Docker, etc.):**
- Spawn cost may be 2-3x higher
- Chunking overhead may be higher
- Memory detection may not see host memory

## Best Practices

### When to Run Validation

**Always run after:**
- Fresh installation
- Python version upgrade
- Moving to new environment (dev → prod)
- Container/VM changes
- Deployment to cloud

**Run periodically:**
- CI/CD pipelines (catch regressions)
- After system updates
- When debugging unexpected behavior

### Integration Patterns

**Development:**
```python
# Run once during development to understand your system
from amorsize import validate_system
result = validate_system(verbose=True)
print(result)
```

**Testing:**
```python
# Include in test suite to catch environment issues
def test_amorsize_health():
    result = validate_system(verbose=False)
    assert result.overall_health in ["excellent", "good"]
```

**Production:**
```python
# Log validation results on startup
import logging
from amorsize import validate_system

result = validate_system(verbose=False)
if result.overall_health not in ["excellent", "good"]:
    logging.warning(f"Amorsize health: {result.overall_health}")
    for error in result.errors:
        logging.error(f"Amorsize: {error}")
```

## Advanced Usage

### Custom Validation

```python
from amorsize.validation import (
    validate_spawn_cost_measurement,
    validate_chunking_overhead_measurement,
    validate_system_resources
)

# Run individual checks
passed, details = validate_spawn_cost_measurement(verbose=True)
print(f"Spawn cost: {details['measured_spawn_cost']}")

passed, details = validate_system_resources(verbose=True)
print(f"Cores: {details['physical_cores']}")
```

### Benchmarking Across Systems

```python
import json
from amorsize import validate_system

# Collect validation results
result = validate_system(verbose=False)

# Export for comparison
system_profile = {
    "health": result.overall_health,
    "details": result.details,
    "checks_passed": result.checks_passed,
    "checks_failed": result.checks_failed
}

with open("system_profile.json", "w") as f:
    json.dump(system_profile, f, indent=2)
```

## Examples

See [system_validation_demo.py](system_validation_demo.py) for complete working examples:

1. **Basic Validation** - Simple health check
2. **Verbose Validation** - See progress in real-time
3. **Programmatic Health Check** - Use results in code
4. **Inspect Measurements** - Access detailed data
5. **CI/CD Integration** - Fail fast on issues
6. **Troubleshooting Guide** - Fix common problems
7. **System Comparison** - Understand environment differences

## Summary

The system validation tool provides:
- ✅ **Installation confidence** - Verify everything works
- ✅ **Measurement accuracy** - Validate system-specific calibration
- ✅ **Debugging aid** - Understand unexpected recommendations
- ✅ **CI/CD integration** - Catch environment issues early
- ✅ **Platform awareness** - Understand system characteristics

Use it whenever you install Amorsize or move to a new environment to ensure optimal performance.
