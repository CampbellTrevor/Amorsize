# Contributing to Amorsize

Thank you for your interest in contributing to Amorsize! This guide will help you understand the project architecture, development workflow, and quality standards.

## Table of Contents
- [Project Overview](#project-overview)
- [Architecture & Design Principles](#architecture--design-principles)
- [Development Setup](#development-setup)
- [Testing Strategy](#testing-strategy)
- [Code Quality Standards](#code-quality-standards)
- [Adding New Features](#adding-new-features)
- [CI/CD Pipeline](#cicd-pipeline)
- [Release Process](#release-process)

## Project Overview

Amorsize is a Python library that optimizes parallelization parameters (`n_jobs` and `chunksize`) for multiprocessing operations. It prevents "negative scaling" where parallelism becomes slower than serial execution due to overhead.

### Core Mission
Provide intelligent, automatic optimization of parallel workloads by:
1. Measuring function execution characteristics
2. Detecting system capabilities (CPU, memory, OS)
3. Calculating overhead costs (spawn, pickle, chunking)
4. Applying Amdahl's Law to predict speedup
5. Recommending optimal parameters

### Key Constraints (THE ENGINEERING CONTRACT)
These are **non-negotiable** design principles:

1. **The "Pickle Tax"**: Always measure serialization time during dry runs
2. **Iterator Preservation**: NEVER consume a generator without restoring it via `itertools.chain`
3. **OS Agnosticism**: Support Linux (`fork`), Windows (`spawn`), and macOS properly
4. **Safety First**: Return `n_jobs=1` (serial) on ANY error rather than crashing
5. **Fail-Safe**: All edge cases must degrade gracefully

## Architecture & Design Principles

### Module Organization

```
amorsize/
├── __init__.py           # Public API exports
├── optimizer.py          # Main optimize() function & Amdahl's Law
├── system_info.py        # Hardware detection (cores, memory, spawn cost)
├── sampling.py           # Dry run execution & measurement
├── executor.py           # Convenience execute() wrapper
├── validation.py         # System validation utilities
├── batch.py              # Batch processing for large result sets
├── streaming.py          # Streaming optimization (imap/imap_unordered)
├── benchmark.py          # Empirical validation of predictions
├── comparison.py         # Strategy comparison utilities
├── tuning.py             # Parameter tuning (grid search, Bayesian)
├── history.py            # Result persistence & comparison
├── config.py             # Configuration export/import
├── performance.py        # Performance regression testing
└── visualization.py      # Plotting utilities (optional matplotlib)
```

### Design Patterns

#### 1. **Layered Error Handling**
Every function has multiple fallback strategies:
```python
# Example: Physical core detection
1. Try psutil (most reliable)
2. Try /proc/cpuinfo parsing (Linux, no deps)
3. Try lscpu command (Linux fallback)
4. Use logical_cores / 2 (conservative estimate)
5. Return 1 (absolute fallback)
```

#### 2. **Measurement with Validation**
All benchmarks validate measurement quality:
```python
def measure_spawn_cost():
    # Measure
    marginal_cost = time_2_workers - time_1_worker
    
    # Validate with 4 quality checks:
    # 1. Reasonable range based on start method
    # 2. Signal strength (clear difference)
    # 3. Consistency with expectations
    # 4. Overhead fraction sanity check
    
    # Fallback to estimate if any check fails
```

#### 3. **Generator Safety Protocol**
```python
# ALWAYS follow this pattern for iterators:
sample, remaining_data, is_gen = safe_slice_data(data, sample_size)
if is_gen:
    # Reconstruct with itertools.chain
    reconstructed_data = itertools.chain(sample, remaining_data)
else:
    # Lists are unchanged
    reconstructed_data = data
```

#### 4. **Optional Dependencies**
Heavy imports are lazy-loaded:
```python
# BAD - loads at module level
import matplotlib.pyplot as plt

# GOOD - lazy import
def plot_something():
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("Install matplotlib: pip install amorsize[viz]")
```

### Data Flow

```
User calls optimize(func, data)
    ↓
1. Validate parameters (raise ValueError on invalid input)
    ↓
2. Perform dry run sampling (sampling.py)
   - Check function picklability
   - Check data picklability
   - Measure execution time
   - Measure pickle time (THE PICKLE TAX)
   - Detect workload type (CPU/IO)
   - Detect nested parallelism
   - Preserve iterator (chain sample + remaining)
    ↓
3. Get system information (system_info.py)
   - Physical cores (not hyperthreaded)
   - Available memory (cgroup-aware for Docker)
   - Spawn cost (measured or estimated)
   - Chunking overhead (measured or estimated)
    ↓
4. Calculate optimal parameters (optimizer.py)
   - Target chunk duration (default 0.2s)
   - Apply Amdahl's Law with overhead accounting
   - Memory-aware worker limits
   - Nested parallelism adjustments
    ↓
5. Return OptimizationResult
   - n_jobs, chunksize, executor_type
   - estimated_speedup, warnings
   - data (reconstructed for generators)
   - profile (optional diagnostic info)
```

## Development Setup

### Prerequisites
- Python 3.7+ (tested on 3.7-3.13)
- Git
- pip

### Installation

```bash
# Clone repository
git clone https://github.com/CampbellTrevor/Amorsize.git
cd Amorsize

# Install in development mode with all dependencies
pip install -e ".[full,dev]"

# Run tests to verify setup
pytest tests/ -v
```

### Development Dependencies
```
# Core
psutil                    # Enhanced physical core detection

# Development
pytest>=6.0              # Test framework
pytest-cov               # Coverage reporting
black                    # Code formatting
flake8                   # Linting
mypy                     # Type checking (future)

# Optional
matplotlib               # Visualization
scikit-optimize          # Bayesian optimization
```

## Testing Strategy

### Test Organization

```
tests/
├── test_optimizer.py              # Core optimization logic
├── test_system_info.py            # Hardware detection
├── test_sampling.py               # Dry run & measurement
├── test_amdahl.py                 # Amdahl's Law calculations
├── test_spawn_cost_measurement.py # Spawn cost validation
├── test_chunking_overhead_measurement.py
├── test_generator_safety.py       # Iterator preservation
├── test_input_validation.py       # Parameter validation
├── test_data_picklability.py      # Pickle checks
├── test_nested_parallelism.py     # Nested parallelism detection
├── test_workload_detection.py     # CPU/IO classification
├── test_integration.py            # End-to-end scenarios
├── test_performance.py            # Performance regression
└── ...                            # Feature-specific tests
```

### Test Categories

#### 1. **Unit Tests** (Fast, Isolated)
Test individual functions with mocked dependencies:
```python
def test_calculate_amdahl_speedup_basic():
    speedup = calculate_amdahl_speedup(
        total_compute_time=10.0,
        pickle_overhead_per_item=0.001,
        spawn_cost_per_worker=0.1,
        chunking_overhead_per_chunk=0.0005,
        n_jobs=4,
        chunksize=10,
        total_items=100
    )
    assert 1.0 < speedup < 4.0  # Speedup with overhead
```

#### 2. **Integration Tests** (Realistic Workflows)
Test complete user scenarios:
```python
def test_optimize_complete_workflow():
    def cpu_bound_func(x):
        return sum(i**2 for i in range(1000))
    
    data = range(100)
    result = optimize(cpu_bound_func, data)
    
    assert result.n_jobs > 1
    assert result.chunksize > 1
    assert result.data == list(data)  # Preserved
```

#### 3. **Edge Case Tests** (Robustness)
Test failure modes and boundary conditions:
```python
def test_empty_data():
    result = optimize(lambda x: x, [])
    assert result.n_jobs == 1  # Safe fallback

def test_unpicklable_function():
    result = optimize(lambda x: x, range(100))
    assert result.n_jobs == 1
    assert "not picklable" in result.reason
```

#### 4. **Performance Tests** (Regression Detection)
Validate optimizer predictions:
```python
def test_optimization_actually_faster():
    result = optimize(expensive_func, large_data)
    if result.n_jobs > 1:
        # Verify parallel is actually faster
        serial_time = measure_serial(expensive_func, data)
        parallel_time = measure_parallel(
            expensive_func, data,
            n_jobs=result.n_jobs,
            chunksize=result.chunksize
        )
        assert parallel_time < serial_time
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_optimizer.py -v

# Run with coverage
pytest tests/ --cov=amorsize --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest tests/ -m "not slow"

# Run in parallel (faster)
pytest tests/ -n auto
```

### Testing Environment Variables

```bash
# Disable nested parallelism detection in tests
export AMORSIZE_TESTING=1

# Set multiprocessing start method for testing
export AMORSIZE_START_METHOD=spawn
```

## Code Quality Standards

### Style Guide
- Follow PEP 8 (enforced by flake8)
- Use type hints for all public functions
- Maximum line length: 100 characters
- Docstrings: Google style format

### Documentation Requirements
Every public function must have:
```python
def my_function(arg1: int, arg2: str) -> bool:
    """
    One-line summary (imperative mood).
    
    Detailed explanation of what the function does,
    including algorithm details if complex.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When and why this is raised
        
    Example:
        >>> my_function(42, "hello")
        True
    """
```

### Error Handling
```python
# GOOD: Specific errors with helpful messages
if not callable(func):
    raise ValueError(
        f"func must be callable, got {type(func).__name__}"
    )

# BAD: Generic errors
if not callable(func):
    raise Exception("Bad function")
```

### Performance Considerations
1. **Cache expensive operations**: Spawn cost, chunking overhead
2. **Lazy imports**: Don't load matplotlib unless needed
3. **Early exits**: Check fast failure conditions first
4. **Minimize dry run samples**: Default sample_size=5

### Commit Message Format
```
Short summary (50 chars or less)

More detailed explanation if needed. Explain WHAT changed
and WHY, not HOW (code shows how).

- Bullet points for multiple changes
- Reference issues: Fixes #123
- Break changes: BREAKING: old API removed
```

## Adding New Features

### Process

1. **Discuss First**: Open an issue to discuss the feature
2. **Design Document**: For large features, write a design doc
3. **Tests First**: Write tests before implementation (TDD)
4. **Incremental**: Small, reviewable PRs
5. **Documentation**: Update docs and examples
6. **Benchmark**: Verify no performance regression

### Feature Checklist

- [ ] Tests written (unit + integration)
- [ ] All tests passing (689+ tests)
- [ ] Documentation updated (docstrings + examples)
- [ ] No performance regression (benchmark suite)
- [ ] Error handling implemented
- [ ] Edge cases covered
- [ ] Type hints added
- [ ] Example code provided
- [ ] CHANGELOG.md updated

### Example: Adding a New Optimization Strategy

```python
# 1. Add core logic (amorsize/optimizer.py)
def calculate_my_strategy(...):
    """Docstring with details."""
    # Implementation
    pass

# 2. Add tests (tests/test_my_strategy.py)
def test_my_strategy_basic():
    result = calculate_my_strategy(...)
    assert result > 0

def test_my_strategy_edge_cases():
    # Empty input
    # Negative values
    # etc.
    pass

# 3. Integrate into optimize()
def optimize(...):
    # ...
    if use_my_strategy:
        result = calculate_my_strategy(...)
    # ...

# 4. Add example (examples/README_my_strategy.md)
# 5. Update CHANGELOG.md
# 6. Run benchmarks: python -m amorsize benchmark ...
```

## CI/CD Pipeline

### Workflows

1. **test.yml**: Runs on every push/PR
   - Matrix: Python 3.7-3.13 × Ubuntu/Windows/macOS
   - 689+ tests must pass
   - Skips expensive tests on PR

2. **lint.yml**: Code quality checks
   - flake8 linting
   - Import order validation
   - Docstring coverage check

3. **build.yml**: Package building
   - Build source distribution
   - Build wheel
   - Validate manifest
   - Check with twine

4. **performance.yml**: Regression testing
   - 5 standardized workloads
   - Compare against baseline
   - Fail if >10% slower
   - Update baseline on main branch

5. **publish.yml**: PyPI publication
   - Triggered by version tags (v*.*.*)
   - Validates, builds, publishes
   - Creates GitHub release
   - Verifies installation

### Running CI Locally

```bash
# Run lint checks
flake8 amorsize/ tests/

# Run full test matrix (requires tox)
tox

# Run build validation
python -m build
twine check dist/*
check-manifest

# Run performance benchmarks
python -m pytest tests/test_performance.py -v
```

## Release Process

### Version Numbering
Follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Steps

1. **Update Version**
   ```python
   # amorsize/__init__.py
   __version__ = "0.2.0"
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [0.2.0] - 2026-01-15
   
   ### Added
   - New feature X
   
   ### Fixed
   - Bug Y
   ```

3. **Run Full Test Suite**
   ```bash
   pytest tests/ -v
   python -m amorsize benchmark --validate
   ```

4. **Build and Validate**
   ```bash
   python -m build
   twine check dist/*
   ```

5. **Tag Release**
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

6. **Automated Publication**
   - CI automatically publishes to PyPI
   - Creates GitHub release with notes
   - Verifies installation

### Post-Release

1. Monitor PyPI for issues
2. Update documentation site
3. Announce on GitHub Discussions
4. Monitor issue tracker

## Development Tips

### Debugging
```python
# Enable verbose mode
result = optimize(func, data, verbose=True)

# Get diagnostic profile
result = optimize(func, data, profile=True)
print(result.explain())

# Profile function internals
result = optimize(func, data, enable_function_profiling=True)
result.show_function_profile()
```

### Testing Multiprocessing
```python
# Test with different start methods
import multiprocessing as mp
mp.set_start_method('spawn', force=True)

# Avoid fork bombs in tests
if __name__ == '__main__':
    # Multiprocessing code here
    pass
```

### Memory Profiling
```python
import tracemalloc
tracemalloc.start()
# ... code ...
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
```

## Getting Help

- **Documentation**: See `examples/` directory
- **Issues**: Open GitHub issue with minimal reproducer
- **Discussions**: GitHub Discussions for questions
- **Email**: Check README.md for contact

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to build great software together.

---

**Happy Contributing!** 🚀

If you have questions about this guide, please open an issue.
