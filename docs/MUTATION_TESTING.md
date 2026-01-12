# Mutation Testing Guide

## Overview

Mutation testing is a powerful technique for evaluating the quality of your test suite. Instead of just measuring code coverage (which lines are executed), mutation testing verifies that your tests actually **catch bugs**.

### How It Works

1. **Mutate**: The tool introduces small bugs (mutations) into your code
   - Change `==` to `!=`
   - Change `+` to `-`
   - Remove `return` statements
   - Flip boolean conditions
   - And many more...

2. **Test**: Run your test suite against each mutation

3. **Verify**: Check if tests caught the bug
   - **Killed**: Tests failed ✅ (Good! Your tests caught the bug)
   - **Survived**: Tests passed ❌ (Bad! Your tests didn't catch the bug)
   - **Timeout**: Tests hung (Code may have infinite loop)

### Mutation Score

The mutation score is the percentage of mutations that were killed by your tests:

```
Mutation Score = (Killed Mutations / Total Mutations) × 100%
```

A high mutation score (>80%) indicates high-quality tests that actually catch bugs.

## Installation

```bash
pip install mutmut
```

## Quick Start

### Run Mutation Testing on a Single File

Test one module to see mutation testing in action:

```bash
# Test the optimizer module (core logic)
mutmut run --paths-to-mutate amorsize/optimizer.py

# View results
mutmut results

# Show details of a survived mutation
mutmut show 1
```

### Run Full Mutation Test Suite

Run mutation testing on all core modules (takes 30-60 minutes):

```bash
# Run mutation testing on core modules
mutmut run --paths-to-mutate amorsize/ \
           --exclude '*/__init__.py' \
           --exclude '*/__main__.py' \
           --exclude '*/dashboards.py'

# Generate HTML report
mutmut html

# Open report in browser
open html/index.html
```

### Quick Validation (Smoke Test)

Run mutation testing on just one critical function to validate setup:

```bash
# Test a specific function
mutmut run --paths-to-mutate amorsize/optimizer.py::optimize

# This should complete in 2-3 minutes
```

## Configuration

Amorsize includes a `.mutmut-config.py` file with optimized settings:

- **Paths to mutate**: `amorsize/` (core library only, not tests)
- **Test command**: `python -m pytest tests/ -x --tb=short -q`
- **Excluded files**: `__init__.py`, `__main__.py`, `dashboards.py`
- **Priority paths**: Core modules tested first

## Understanding Results

### Example Output

```
╒════════════════════════════════════════════════╕
│ Mutation testing                               │
├────────────────────────────────────────────────┤
│ Total: 500                                     │
│ Killed: 425 (85.0%)                            │
│ Survived: 45 (9.0%)                            │
│ Timeout: 10 (2.0%)                             │
│ Suspicious: 20 (4.0%)                          │
╘════════════════════════════════════════════════╛
```

**Interpretation:**
- **85% mutation score**: Excellent! Most mutations are caught
- **9% survived**: These indicate gaps in test coverage
- **2% timeout**: Mutations may have created infinite loops
- **4% suspicious**: Unclear results, needs investigation

### What to Focus On

1. **Survived mutations**: These represent **real gaps in your tests**
   - Review the mutation with `mutmut show <id>`
   - Understand why tests didn't catch it
   - Add a test to catch this class of bugs

2. **Suspicious mutations**: May indicate flaky tests
   - Investigate with `mutmut show <id>`
   - Fix flaky tests or mark as expected

3. **Timeouts**: Often indicate infinite loops created by mutations
   - Usually not actionable (mutation created invalid code)
   - Focus on survived mutations instead

## Best Practices

### 1. Start with Core Modules

Focus mutation testing on business-critical code:

```bash
# Core optimization logic (highest priority)
mutmut run --paths-to-mutate amorsize/optimizer.py

# Sampling and measurement
mutmut run --paths-to-mutate amorsize/sampling.py

# System detection
mutmut run --paths-to-mutate amorsize/system_info.py
```

### 2. Set Realistic Goals

- **Starter goal**: 70% mutation score
- **Good goal**: 80% mutation score
- **Excellent goal**: 90% mutation score
- **Perfection**: 100% mutation score (often impractical)

### 3. Iterate Incrementally

Don't try to kill all mutations at once:

1. Run mutation testing on one module
2. Review survived mutations
3. Add tests to kill the most important ones
4. Re-run to verify improvement
5. Move to next module

### 4. Focus on High-Value Mutations

Not all survived mutations are equally important:

**High Priority** (fix these first):
- Mutations in core logic (`optimizer.py`, `cost_model.py`)
- Mutations in safety checks (`sampling.py` picklability)
- Mutations in boundary conditions (off-by-one errors)

**Lower Priority** (can defer):
- Mutations in error messages (cosmetic)
- Mutations in optional features (monitoring, dashboards)
- Mutations in fallback branches (edge cases)

### 5. Use Mutation Testing to Guide Test Writing

When you find a survived mutation:

```python
# Example: mutmut found that changing > to >= doesn't fail tests

# Original code
if chunksize > 1:
    return chunksize

# Mutated code (tests still passed!)
if chunksize >= 1:
    return chunksize

# This indicates a gap: add a test for the boundary condition
def test_chunksize_boundary():
    """Test that chunksize=1 is handled correctly."""
    result = optimize(func, [1, 2, 3])
    assert result.chunksize == 1  # Verify behavior at boundary
```

## Performance Tips

Mutation testing is **CPU-intensive** (runs tests hundreds of times):

### Speed Up Mutation Testing

1. **Use fast test subset**:
   ```bash
   # Only run fast unit tests, skip slow integration tests
   mutmut run --test-command "pytest tests/ -m 'not slow' -x -q"
   ```

2. **Use parallel execution** (if you have mutmut 2.0+):
   ```bash
   mutmut run --use-parallel
   ```

3. **Focus on one module at a time**:
   ```bash
   mutmut run --paths-to-mutate amorsize/optimizer.py
   ```

4. **Use caching** (mutmut caches results):
   ```bash
   # First run is slow, subsequent runs skip unchanged code
   mutmut run
   ```

5. **Run incrementally**:
   ```bash
   # Run 50 mutations, review, then continue
   mutmut run --max-mutations 50
   ```

### Expected Runtime

On modern hardware (4 cores, 16GB RAM):
- **Single file** (optimizer.py): 5-10 minutes
- **Core modules** (5 files): 30-60 minutes  
- **Full suite** (all 30+ files): 2-4 hours

Use `--use-parallel` to leverage multiple cores and reduce time.

## CI/CD Integration

Add mutation testing to your CI pipeline (optional, not required):

### GitHub Actions Example

```yaml
name: Mutation Testing

on:
  # Run on main branch merges (not every PR, too slow)
  push:
    branches: [main]
  
  # Allow manual trigger
  workflow_dispatch:

jobs:
  mutation-test:
    name: Mutation Testing
    runs-on: ubuntu-latest
    timeout-minutes: 120  # 2 hours max
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
        pip install mutmut
    
    - name: Run mutation testing (core modules only)
      run: |
        mutmut run --paths-to-mutate amorsize/optimizer.py,amorsize/sampling.py,amorsize/system_info.py
    
    - name: Generate report
      if: always()
      run: |
        mutmut results
        mutmut html
    
    - name: Upload report
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: mutation-report
        path: html/
```

### When to Run Mutation Testing

**Recommended:**
- **Weekly**: Run on core modules to catch regressions
- **Before releases**: Full mutation testing on all code
- **After major changes**: Verify tests still catch bugs

**Not recommended:**
- On every PR (too slow, CI bottleneck)
- On every commit (impractical runtime)

## Troubleshooting

### "No mutations found"

```bash
# Check that mutmut can find your code
mutmut run --paths-to-mutate amorsize/optimizer.py --verbose
```

**Solution**: Ensure path is correct and file exists.

### "All mutations timed out"

Tests may be hanging on mutations. Check test timeout settings:

```bash
# Add pytest timeout
pip install pytest-timeout
pytest --timeout=30 tests/
```

### "Mutation score is very low (<50%)"

This indicates significant gaps in test coverage. Focus on:
1. Adding tests for boundary conditions
2. Testing error handling paths
3. Verifying return values (not just no exceptions)

### "Mutation testing is too slow"

1. Use `--use-parallel` flag
2. Test one module at a time
3. Run on faster hardware
4. Use test subset (skip slow tests)

## Resources

- **Mutmut Documentation**: https://mutmut.readthedocs.io/
- **Mutation Testing Introduction**: https://en.wikipedia.org/wiki/Mutation_testing
- **Research Paper**: Just, R., Jalali, D., Inozemtseva, L., Ernst, M. D., Holmes, R., & Fraser, G. (2014). "Are Mutants a Valid Substitute for Real Faults in Software Testing?" *Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering (FSE 2014)*, pp. 654-665. DOI: 10.1145/2635868.2635929

## Example Workflow

### Step-by-Step: Improve Mutation Score

1. **Baseline**: Run mutation testing
   ```bash
   mutmut run --paths-to-mutate amorsize/optimizer.py
   mutmut results
   # Output: Killed: 120/150 (80%)
   ```

2. **Analyze**: Find survived mutations
   ```bash
   mutmut show 1
   # Shows: Changed `>` to `>=` in line 42
   # Test still passed - missing boundary test!
   ```

3. **Fix**: Add test to kill the mutation
   ```python
   def test_boundary_condition():
       result = optimize(func, [1])
       assert result.chunksize == 1
   ```

4. **Verify**: Re-run mutation testing
   ```bash
   mutmut run --paths-to-mutate amorsize/optimizer.py
   mutmut results
   # Output: Killed: 121/150 (80.7%) - Improved!
   ```

5. **Repeat**: Continue until satisfied with score

## Summary

Mutation testing is a powerful tool for validating test quality:

- ✅ **Use it**: To find gaps in your test suite
- ✅ **Focus**: On core business logic first
- ✅ **Iterate**: Improve incrementally, not all at once
- ✅ **Prioritize**: High-value mutations over perfection
- ❌ **Don't overdo it**: 100% mutation score is often impractical

**Goal**: Catch bugs before they reach production by ensuring your tests are actually effective at detecting real problems.
