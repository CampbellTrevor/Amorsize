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
