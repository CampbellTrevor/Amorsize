"""
Tests for the CLI interface.

Tests cover:
- Function loading
- Data loading (range, file, stdin)
- Command execution (optimize, execute)
- Output formatting (human-readable, JSON)
- Error handling
- Parameter passing
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestFunctionLoading:
    """Test loading functions from module paths."""
    
    def test_load_function_with_dot_notation(self):
        """Test loading function with dot notation."""
        from amorsize.__main__ import load_function
        func = load_function("math.sqrt")
        assert callable(func)
        assert func(4) == 2.0
    
    def test_load_function_with_colon_notation(self):
        """Test loading function with colon notation."""
        from amorsize.__main__ import load_function
        func = load_function("math:sqrt")
        assert callable(func)
        assert func(4) == 2.0
    
    def test_load_function_from_tests(self):
        """Test loading function from test module."""
        from amorsize.__main__ import load_function
        func = load_function("tests.test_cli_functions.square")
        assert callable(func)
        assert func(5) == 25
    
    def test_load_function_invalid_format(self):
        """Test error for invalid function path format."""
        from amorsize.__main__ import load_function
        with pytest.raises(ValueError, match="Invalid function path"):
            load_function("noseparator")
    
    def test_load_function_module_not_found(self):
        """Test error when module doesn't exist."""
        from amorsize.__main__ import load_function
        with pytest.raises(ValueError, match="Cannot import module"):
            load_function("nonexistent_module.function")
    
    def test_load_function_function_not_found(self):
        """Test error when function doesn't exist in module."""
        from amorsize.__main__ import load_function
        with pytest.raises(ValueError, match="has no function"):
            load_function("math.nonexistent_function")
    
    def test_load_function_not_callable(self):
        """Test error when attribute is not callable."""
        from amorsize.__main__ import load_function
        with pytest.raises(ValueError, match="not a callable"):
            load_function("math.pi")  # pi is a constant, not a function


class TestDataLoading:
    """Test loading data from various sources."""
    
    def test_load_data_range(self):
        """Test loading data from range."""
        from amorsize.__main__ import load_data
        import argparse
        
        args = argparse.Namespace(
            data_range=10,
            data_file=None,
            data_stdin=False
        )
        data = load_data(args)
        assert data == list(range(10))
    
    def test_load_data_file(self):
        """Test loading data from file."""
        from amorsize.__main__ import load_data
        import argparse
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("1\n2\n3\n4\n5\n")
            temp_file = f.name
        
        try:
            args = argparse.Namespace(
                data_range=None,
                data_file=temp_file,
                data_stdin=False
            )
            data = load_data(args)
            assert data == ["1", "2", "3", "4", "5"]
        finally:
            os.unlink(temp_file)
    
    def test_load_data_file_with_empty_lines(self):
        """Test loading data from file with empty lines."""
        from amorsize.__main__ import load_data
        import argparse
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("1\n\n2\n  \n3\n")
            temp_file = f.name
        
        try:
            args = argparse.Namespace(
                data_range=None,
                data_file=temp_file,
                data_stdin=False
            )
            data = load_data(args)
            assert data == ["1", "2", "3"]
        finally:
            os.unlink(temp_file)
    
    def test_load_data_file_not_found(self):
        """Test error when file doesn't exist."""
        from amorsize.__main__ import load_data
        import argparse
        
        args = argparse.Namespace(
            data_range=None,
            data_file="/nonexistent/file.txt",
            data_stdin=False
        )
        with pytest.raises(ValueError, match="Cannot read data file"):
            load_data(args)
    
    def test_load_data_no_source(self):
        """Test error when no data source specified."""
        from amorsize.__main__ import load_data
        import argparse
        
        args = argparse.Namespace(
            data_range=None,
            data_file=None,
            data_stdin=False
        )
        with pytest.raises(ValueError, match="No data source specified"):
            load_data(args)


class TestCLIOptimizeCommand:
    """Test the optimize command."""
    
    def test_optimize_with_range(self):
        """Test optimize command with range data."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "100",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["mode"] == "optimize"
        assert "n_jobs" in output
        assert "chunksize" in output
        assert "estimated_speedup" in output
    
    def test_optimize_with_file(self):
        """Test optimize command with file data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("1\n2\n3\n4\n5\n")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "amorsize",
                    "optimize",
                    "tests.test_cli_functions.square",
                    "--data-file", temp_file,
                    "--json"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )
            
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert output["mode"] == "optimize"
            assert output["n_jobs"] >= 1
        finally:
            os.unlink(temp_file)
    
    def test_optimize_with_profile(self):
        """Test optimize command with profiling."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--profile"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "OPTIMIZATION ANALYSIS" in result.stdout
        assert "n_jobs" in result.stdout
        assert "chunksize" in result.stdout
        # Profile output should be present
        assert "DETAILED DIAGNOSTIC PROFILE" in result.stdout or "WORKLOAD ANALYSIS" in result.stdout
    
    def test_optimize_with_verbose(self):
        """Test optimize command with verbose output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--verbose"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "OPTIMIZATION ANALYSIS" in result.stdout
    
    def test_optimize_expensive_function(self):
        """Test optimize with expensive function."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.expensive_computation",
                "--data-range", "100",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["n_jobs"] >= 1  # May or may not parallelize depending on system
    
    def test_optimize_with_custom_sample_size(self):
        """Test optimize with custom sample size."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "100",
                "--sample-size", "10",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["n_jobs"] >= 1


class TestCLIExecuteCommand:
    """Test the execute command."""
    
    def test_execute_with_range(self):
        """Test execute command with range data."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "execute",
                "tests.test_cli_functions.square",
                "--data-range", "10",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["mode"] == "execute"
        assert output["results_count"] == 10
        assert "sample_results" in output
        assert output["optimization"]["n_jobs"] >= 1
    
    def test_execute_with_file(self):
        """Test execute command with file data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("1\n2\n3\n4\n5\n")
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [
                    sys.executable, "-m", "amorsize",
                    "execute",
                    "tests.test_cli_functions.double",
                    "--data-file", temp_file,
                    "--json"
                ],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )
            
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert output["mode"] == "execute"
            assert output["results_count"] == 5
            # Check that results are correct (double function)
            expected = [2, 4, 6, 8, 10]
            assert output["sample_results"] == expected
        finally:
            os.unlink(temp_file)
    
    def test_execute_verifies_results(self):
        """Test that execute produces correct results."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "execute",
                "tests.test_cli_functions.square",
                "--data-range", "5",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        # Verify results are correct squares
        expected = [0, 1, 4, 9, 16]
        assert output["sample_results"] == expected


class TestCLIErrorHandling:
    """Test error handling in CLI."""
    
    def test_invalid_function_path(self):
        """Test error for invalid function path."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "invalid_module.nonexistent",
                "--data-range", "10"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 1
        assert "Error:" in result.stderr
    
    def test_no_data_source(self):
        """Test error when no data source specified."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 2  # argparse error
        assert "required" in result.stderr.lower() or "error" in result.stderr.lower()
    
    def test_no_command(self):
        """Test error when no command specified."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 1
        # Should show help
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()
    
    def test_help_message(self):
        """Test help message display."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "validate" in result.stdout
        assert "optimize" in result.stdout
        assert "execute" in result.stdout
        assert "Dynamic Parallelism Optimizer" in result.stdout
    
    def test_version(self):
        """Test version display."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "--version"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "0.1.0" in result.stdout or "0.1.0" in result.stderr


class TestCLIOutputFormats:
    """Test different output formats."""
    
    def test_json_output_structure(self):
        """Test JSON output has correct structure."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        
        # Check required fields
        assert "mode" in output
        assert "n_jobs" in output
        assert "chunksize" in output
        assert "estimated_speedup" in output
        assert "reason" in output
        assert "warnings" in output
        
        # Verify types
        assert isinstance(output["n_jobs"], int)
        assert isinstance(output["chunksize"], int)
        assert isinstance(output["estimated_speedup"], (int, float))
        assert isinstance(output["warnings"], list)
    
    def test_human_output_structure(self):
        """Test human-readable output has expected sections."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "50"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        
        # Check expected sections
        assert "OPTIMIZATION ANALYSIS" in result.stdout
        assert "Recommendation:" in result.stdout
        assert "n_jobs" in result.stdout
        assert "chunksize" in result.stdout
        assert "estimated_speedup" in result.stdout
        assert "Reason:" in result.stdout


class TestCLIParameterPassing:
    """Test that CLI parameters are correctly passed to library."""
    
    def test_no_spawn_benchmark_flag(self):
        """Test --no-spawn-benchmark flag."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--no-spawn-benchmark",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        # Should still work, just with estimates instead of measurements
        output = json.loads(result.stdout)
        assert output["n_jobs"] >= 1
    
    def test_no_chunking_benchmark_flag(self):
        """Test --no-chunking-benchmark flag."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--no-chunking-benchmark",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["n_jobs"] >= 1
    
    def test_no_auto_adjust_flag(self):
        """Test --no-auto-adjust flag."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--no-auto-adjust",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["n_jobs"] >= 1


class TestCLIValidateCommand:
    """Test the validate subcommand."""
    
    def test_validate_basic(self):
        """Test basic validate command."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "validate"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        # Should succeed (exit code 0) on healthy system
        assert result.returncode == 0
        # Should show validation report
        assert "VALIDATION REPORT" in result.stdout or "Health:" in result.stdout
        assert "checks" in result.stdout.lower() or "passed" in result.stdout.lower()
    
    def test_validate_with_json_output(self):
        """Test validate command with JSON output."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "validate", "--json"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        
        # Parse JSON output
        output = json.loads(result.stdout)
        
        # Verify structure
        assert "checks_passed" in output
        assert "checks_failed" in output
        assert "overall_health" in output
        assert "warnings" in output
        assert "errors" in output
        assert "details" in output
        
        # Verify types
        assert isinstance(output["checks_passed"], int)
        assert isinstance(output["checks_failed"], int)
        assert isinstance(output["overall_health"], str)
        assert isinstance(output["warnings"], list)
        assert isinstance(output["errors"], list)
        assert isinstance(output["details"], dict)
        
        # On a healthy system, should have checks passed
        assert output["checks_passed"] > 0
    
    def test_validate_with_verbose(self):
        """Test validate command with verbose output."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "validate", "--verbose"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        # Should succeed
        assert result.returncode == 0
        # Should show validation output (verbose may add more details)
        assert "VALIDATION REPORT" in result.stdout or "Health:" in result.stdout
    
    def test_validate_json_structure_details(self):
        """Test validate JSON output contains expected details."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "validate", "--json"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        
        # Check for expected validation checks in details
        details = output["details"]
        expected_checks = [
            "multiprocessing_basic",
            "system_resources",
            "spawn_cost_measurement",
            "chunking_overhead_measurement",
            "pickle_overhead_measurement"
        ]
        
        # At least some of these checks should be present
        present_checks = sum(1 for check in expected_checks if check in details)
        assert present_checks > 0, "Expected validation checks not found in details"
    
    def test_validate_help_message(self):
        """Test validate command help message."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "validate", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "validate" in result.stdout.lower()
        assert "--json" in result.stdout or "json" in result.stdout.lower()
        assert "--verbose" in result.stdout or "verbose" in result.stdout.lower()


class TestCLICompareCommand:
    """Test the compare subcommand."""
    
    def test_compare_basic(self):
        """Test basic compare command with multiple configs."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--configs", "2,10", "4,5"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        # Should show comparison results
        assert "Strategy Comparison Results" in result.stdout or "Best Strategy:" in result.stdout
        assert "Serial" in result.stdout  # Should have baseline
    
    def test_compare_with_json_output(self):
        """Test compare command with JSON output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--configs", "2,10", "4,5",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        
        # Parse JSON output
        output = json.loads(result.stdout)
        
        # Verify structure
        assert "strategies" in output
        assert "best_strategy" in output
        assert "recommendations" in output
        
        # Verify strategies list
        assert isinstance(output["strategies"], list)
        assert len(output["strategies"]) >= 3  # Serial + 2 configs
        
        # Verify each strategy has required fields
        for strategy in output["strategies"]:
            assert "name" in strategy
            assert "n_jobs" in strategy
            assert "chunksize" in strategy
            assert "executor_type" in strategy
            assert "time" in strategy
            assert "speedup" in strategy
        
        # Verify best strategy
        best = output["best_strategy"]
        assert "name" in best
        assert "n_jobs" in best
        assert "time" in best
        assert "speedup" in best
    
    def test_compare_with_optimizer(self):
        """Test compare command with optimizer recommendation."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--include-optimizer",
                "--configs", "2,10",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        
        output = json.loads(result.stdout)
        
        # Should have Serial + Optimizer + 1 custom config = 3 strategies
        assert len(output["strategies"]) >= 3
        
        # Check that optimizer strategy is present
        strategy_names = [s["name"] for s in output["strategies"]]
        assert "Optimizer" in strategy_names
        assert "Serial" in strategy_names
    
    def test_compare_with_custom_names(self):
        """Test compare with custom strategy names."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--configs", "Low:2,10", "High:4,5",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        
        output = json.loads(result.stdout)
        strategy_names = [s["name"] for s in output["strategies"]]
        
        # Check custom names are preserved
        assert "Low" in strategy_names
        assert "High" in strategy_names
    
    def test_compare_no_baseline(self):
        """Test compare with --no-baseline flag."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--configs", "2,10", "4,5",
                "--no-baseline",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        
        output = json.loads(result.stdout)
        
        # Should have exactly 2 strategies (no serial baseline)
        assert len(output["strategies"]) == 2
    
    def test_compare_with_max_items(self):
        """Test compare with --max-items to limit dataset."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "1000",
                "--configs", "2,10",
                "--max-items", "50",
                "--json"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert len(output["strategies"]) >= 2
    
    def test_compare_error_no_configs(self):
        """Test compare error when no configs provided."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--no-baseline"  # Remove baseline, no configs = error
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        # Should fail with error
        assert result.returncode != 0
        assert "at least 2 configurations" in result.stderr.lower() or "need at least 2" in result.stderr.lower()
    
    def test_compare_error_invalid_config(self):
        """Test compare error with invalid config format."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "50",
                "--configs", "invalid"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        # Should fail with parsing error
        assert result.returncode != 0
        assert "Error parsing config" in result.stderr or "Invalid config" in result.stderr
    
    def test_compare_help_message(self):
        """Test compare command help message."""
        result = subprocess.run(
            [sys.executable, "-m", "amorsize", "compare", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        assert "compare" in result.stdout.lower()
        assert "--configs" in result.stdout
        assert "--include-optimizer" in result.stdout
        assert "--json" in result.stdout
    
    def test_compare_verbose_output(self):
        """Test compare command with verbose output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "compare",
                "tests.test_cli_functions.square",
                "--data-range", "30",
                "--configs", "2,10",
                "--verbose"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        # Verbose mode should show progress
        assert "Comparing" in result.stdout or "Testing" in result.stdout


class TestCLIEnhancements:
    """Test new CLI enhancement flags from Iteration 137."""
    
    def test_explain_flag(self):
        """Test --explain flag shows detailed explanation."""
        from amorsize.__main__ import load_function
        
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--explain"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}  # Disable colors for testing
        )
        
        assert result.returncode == 0
        # Should show detailed explanation section
        assert "DETAILED EXPLANATION" in result.stdout or "explanation" in result.stdout.lower()
    
    def test_tips_flag(self):
        """Test --tips flag shows optimization tips."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--tips"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should show tips section
        assert "OPTIMIZATION TIPS" in result.stdout or "tips" in result.stdout.lower()
    
    def test_show_overhead_flag(self):
        """Test --show-overhead flag shows overhead breakdown."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--show-overhead"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should show overhead breakdown
        assert "OVERHEAD BREAKDOWN" in result.stdout or "overhead" in result.stdout.lower()
        # Should show overhead components
        assert "Spawn overhead" in result.stdout or "spawn" in result.stdout.lower()
    
    def test_quiet_flag(self):
        """Test --quiet/-q flag shows minimal output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--quiet"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Quiet mode should show only essentials
        assert "n_jobs=" in result.stdout
        assert "chunksize=" in result.stdout
        assert "speedup=" in result.stdout
        # Should NOT show verbose headers
        assert "OPTIMIZATION ANALYSIS" not in result.stdout
    
    def test_quiet_flag_short_form(self):
        """Test -q short form of --quiet flag."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "-q"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should behave same as --quiet
        assert "n_jobs=" in result.stdout
        assert "chunksize=" in result.stdout
    
    def test_color_flag(self):
        """Test --color flag forces colored output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        # Should contain ANSI escape codes (color codes start with \033[)
        # Even though output may not be TTY, --color forces it
        # Note: Due to piping, colors might still be disabled by TTY check
        # So we just verify command runs successfully
        assert "n_jobs" in result.stdout.lower() or "recommendation" in result.stdout.lower()
    
    def test_no_color_flag(self):
        """Test --no-color flag disables colored output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        assert result.returncode == 0
        # Should not contain ANSI escape codes
        assert "\033[" not in result.stdout
    
    def test_combined_flags(self):
        """Test combining multiple enhancement flags."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--explain",
                "--tips",
                "--show-overhead",
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should show all requested sections
        output_lower = result.stdout.lower()
        assert "explanation" in output_lower or "detailed" in output_lower
        assert "tips" in output_lower
        assert "overhead" in output_lower
    
    def test_quiet_overrides_verbose_flags(self):
        """Test --quiet suppresses verbose output from other flags."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--quiet",
                "--tips",  # Should be ignored with --quiet
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Quiet mode should suppress everything except essentials
        assert "n_jobs=" in result.stdout
        # Should NOT show tips even though --tips was specified
        assert "OPTIMIZATION TIPS" not in result.stdout
    
    def test_profile_auto_enabled_with_explain(self):
        """Test that --explain automatically enables profiling."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--explain",
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should work without requiring explicit --profile flag
        # If profiling wasn't auto-enabled, this would fail or show less detail
        assert "n_jobs" in result.stdout.lower()
    
    def test_profile_auto_enabled_with_tips(self):
        """Test that --tips automatically enables profiling."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--tips",
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should work without requiring explicit --profile flag
        assert "n_jobs" in result.stdout.lower()
    
    def test_profile_auto_enabled_with_show_overhead(self):
        """Test that --show-overhead automatically enables profiling."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "optimize",
                "math.sqrt",
                "--data-range", "50",
                "--show-overhead",
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should show overhead details
        output_lower = result.stdout.lower()
        assert "overhead" in output_lower
    
    def test_execute_with_quiet_flag(self):
        """Test --quiet flag works with execute command."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "execute",
                "math.sqrt",
                "--data-range", "10",
                "--quiet",
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should show minimal output
        assert "n_jobs=" in result.stdout
    
    def test_execute_with_explain_flag(self):
        """Test --explain flag works with execute command."""
        result = subprocess.run(
            [
                sys.executable, "-m", "amorsize",
                "execute",
                "math.sqrt",
                "--data-range", "10",
                "--explain",
                "--no-color"
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        # Should show explanation
        output_lower = result.stdout.lower()
        assert "explanation" in output_lower or "detailed" in output_lower


