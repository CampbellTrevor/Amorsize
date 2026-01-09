# Iteration 32 Summary: CLI Support for Comparison Mode

**Date**: 2026-01-09
**Objective**: Add command-line interface support for comparison mode
**Status**: ✅ Complete - All tests passing (542 total)

## Problem Statement

The comparison mode feature was implemented in Iteration 31, allowing users to benchmark and compare multiple parallelization strategies. However, it required writing Python code. Users needed a way to perform comparisons directly from the command line without writing scripts.

## Solution

Extended the CLI (`amorsize/__main__.py`) with a new `compare` subcommand that enables:
- Comparing multiple parallelization strategies from the command line
- Integration with the optimizer to include its recommendation
- Custom strategy names and executor types
- Both human-readable and JSON output formats
- Flexible dataset limiting and timeout controls

## Changes Made

### 1. Core Implementation (`amorsize/__main__.py`)

#### Added Functions:
- **`parse_strategy_config(config_str: str) -> ComparisonConfig`**
  - Parses CLI config strings: "n_jobs,chunksize" or "name:n_jobs,chunksize,executor"
  - Supports custom strategy names
  - Validates input format and values
  - Examples:
    - "2,50" → 2 workers, chunksize 50
    - "Custom:4,25,thread" → named config with thread executor

- **`cmd_compare(args: argparse.Namespace)`**
  - Main handler for compare subcommand
  - Loads function and data using existing CLI utilities
  - Parses user-provided strategy configs
  - Optionally includes optimizer recommendation
  - Runs comparison and formats output (human or JSON)
  - Error handling for invalid configs

#### Extended Argument Parser:
- Added `compare` subcommand with full argument set
- Strategy specification via `--configs`
- `--include-optimizer` flag for optimizer integration
- `--no-baseline` to skip serial baseline
- `--max-items` to limit benchmark size
- `--timeout` for benchmark time control
- Standard CLI flags: `--json`, `--verbose`
- Optimization parameters when using `--include-optimizer`

#### Updated Help Text:
- Added compare examples to main epilog
- Comprehensive help for compare subcommand

### 2. Test Suite (`tests/test_cli.py`)

Added comprehensive test class `TestCLICompareCommand` with 10 tests:

1. **`test_compare_basic`** - Basic comparison with multiple configs
2. **`test_compare_with_json_output`** - JSON output format validation
3. **`test_compare_with_optimizer`** - Optimizer integration
4. **`test_compare_with_custom_names`** - Custom strategy names
5. **`test_compare_no_baseline`** - Skip serial baseline
6. **`test_compare_with_max_items`** - Dataset limiting
7. **`test_compare_error_no_configs`** - Error handling: insufficient configs
8. **`test_compare_error_invalid_config`** - Error handling: malformed configs
9. **`test_compare_help_message`** - Help text validation
10. **`test_compare_verbose_output`** - Verbose mode output

All tests use subprocess to test actual CLI invocation, ensuring end-to-end functionality.

## Technical Highlights

### Config String Parsing
The parser supports flexible formats:
```bash
# Simple format (auto-generated name)
"2,50"              → "2 processes" with n_jobs=2, chunksize=50

# Named format
"Low:2,50"          → "Low" with n_jobs=2, chunksize=50

# Full format with executor
"Custom:4,25,thread" → "Custom" with n_jobs=4, chunksize=25, ThreadPoolExecutor
```

### Output Formats

**Human-Readable:**
```
=== Strategy Comparison Results ===

Strategy                       Time (s)     Speedup    Status         
----------------------------------------------------------------------
Serial                         0.0000       1.00x      ⭐ FASTEST      
2 processes                    0.0078       0.00x      ⚠️  Slower     
4 processes                    0.0062       0.00x      ⚠️  Slower     

Best Strategy: Serial
Best Time: 0.0000s
Best Speedup: 1.00x
```

**JSON:**
```json
{
  "strategies": [
    {
      "name": "Serial",
      "n_jobs": 1,
      "chunksize": 1,
      "executor_type": "process",
      "time": 0.0000174,
      "speedup": 1.0
    },
    ...
  ],
  "best_strategy": {
    "name": "Serial",
    "n_jobs": 1,
    ...
  },
  "recommendations": [...]
}
```

## Usage Examples

### Basic Comparison
```bash
python -m amorsize compare math.factorial --data-range 100 --configs "2,50" "4,25" "8,10"
```

### With Optimizer
```bash
python -m amorsize compare mymodule.func --data-range 500 --include-optimizer --configs "4,20"
```

### Custom Names and JSON
```bash
python -m amorsize compare math.sqrt --data-range 200 \
  --configs "Low:2,50" "High:8,10" \
  --json
```

### Limit Dataset Size
```bash
python -m amorsize compare bigfunc --data-range 10000 \
  --configs "2,100" "4,50" \
  --max-items 100
```

## Test Results

```
tests/test_cli.py::TestCLICompareCommand::test_compare_basic PASSED                    [ 10%]
tests/test_cli.py::TestCLICompareCommand::test_compare_with_json_output PASSED        [ 20%]
tests/test_cli.py::TestCLICompareCommand::test_compare_with_optimizer PASSED          [ 30%]
tests/test_cli.py::TestCLICompareCommand::test_compare_with_custom_names PASSED       [ 40%]
tests/test_cli.py::TestCLICompareCommand::test_compare_no_baseline PASSED             [ 50%]
tests/test_cli.py::TestCLICompareCommand::test_compare_with_max_items PASSED          [ 60%]
tests/test_cli.py::TestCLICompareCommand::test_compare_error_no_configs PASSED        [ 70%]
tests/test_cli.py::TestCLICompareCommand::test_compare_error_invalid_config PASSED    [ 80%]
tests/test_cli.py::TestCLICompareCommand::test_compare_help_message PASSED            [ 90%]
tests/test_cli.py::TestCLICompareCommand::test_compare_verbose_output PASSED          [100%]

10 passed in 0.76s
```

**Full Suite**: 542 passed in 14.29s (up from 532)

## Integration

The CLI compare feature integrates seamlessly with:
- **comparison.py**: Uses `compare_strategies()` and `ComparisonConfig` directly
- **optimizer.py**: Can include optimizer recommendation via `optimize()`
- **Existing CLI**: Follows same patterns as `optimize`, `execute`, and `validate` commands
- **Error handling**: Consistent error messages and exit codes

## Design Decisions

1. **Config String Format**: Chose comma-separated format for simplicity and consistency
2. **Always Include Baseline**: Serial baseline included by default (can be disabled)
3. **Optimizer Integration**: Optional via flag rather than always-on (for speed)
4. **JSON Structure**: Matches comparison.py output structure for consistency
5. **Error Messages**: Clear, actionable error messages for invalid configs

## Known Limitations

1. **No Config Files**: Must specify configs via command line (future: load from file)
2. **No Visualization**: Text/JSON output only (future: `--plot` flag)
3. **No History**: Results not saved automatically (future: historical tracking)

## Recommended Next Steps

1. **Visualization Support** (HIGH PRIORITY)
   - Add `--plot` flag to generate charts
   - Bar charts for execution times
   - Speedup curves
   - Integration with matplotlib/plotly

2. **Configuration Files**
   - Save/load configs from YAML/JSON
   - `--save-config` and `--load-config` flags

3. **Historical Tracking**
   - Save results to database
   - Compare across runs
   - Track performance over time

4. **Auto-Tuning**
   - `--auto-tune` flag for grid search
   - Iterative refinement
   - Converge on optimal config

## Conclusion

This iteration successfully delivered CLI support for comparison mode, making it easy for users to benchmark parallelization strategies from the command line. The implementation is clean, well-tested, and ready for production use.

**Key Metrics:**
- ✅ 10 new tests added (all passing)
- ✅ 542 total tests (up from 532)
- ✅ Zero breaking changes
- ✅ Full backward compatibility
- ✅ Complete documentation in help text

The foundation is now in place for advanced features like visualization, historical tracking, and auto-tuning.
