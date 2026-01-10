# Performance Benchmarks

This directory contains performance benchmark baselines and results for the Amorsize optimizer.

## Files

- **baseline.json** - Baseline performance results used for regression detection in CI
- **current.json** - Current benchmark results (generated during CI runs)

## Purpose

The performance testing framework runs standardized benchmark workloads to:

1. **Detect regressions** - Catch performance degradations before they reach production
2. **Track accuracy** - Monitor optimizer prediction accuracy over time
3. **Validate changes** - Ensure code changes don't negatively impact performance

## Baseline

The baseline was generated on the CI environment and represents the expected performance characteristics for that environment. The baseline is updated automatically when commits are merged to the main branch.

### Important Notes

- **CI Environment Constraints**: The CI environment may not achieve high absolute speedups due to limited CPU cores and system load. This is expected and normal.
- **Regression Detection**: The CI workflow focuses on detecting **regressions** (performance degrading compared to baseline) rather than absolute performance thresholds.
- **Threshold**: The CI uses a 15% tolerance threshold to account for normal system variability.

## Running Benchmarks Locally

To run the performance benchmarks locally:

```bash
# Run the full suite and save results
python -c "from amorsize import run_performance_suite; \
           results = run_performance_suite(run_validation=True, verbose=True, \
           save_results=True, results_path='benchmarks/my_results.json')"

# Compare against baseline
python -c "from amorsize import compare_performance_results; \
           from pathlib import Path; \
           comparison = compare_performance_results( \
               Path('benchmarks/baseline.json'), \
               Path('benchmarks/my_results.json'), \
               regression_threshold=0.10)"
```

## More Information

See [examples/README_performance_testing.md](../examples/README_performance_testing.md) for complete documentation on the performance testing framework.
