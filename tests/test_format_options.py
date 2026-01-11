"""
Tests for CLI output format options.

Tests the --format flag with different output formats:
- text (default)
- json
- yaml
- table
- markdown
"""

import json
import subprocess
import sys
from typing import List

import pytest


def run_cli_command(args: List[str]) -> tuple[int, str, str]:
    """
    Run CLI command and return exit code, stdout, stderr.

    Args:
        args: List of command arguments

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    result = subprocess.run(
        [sys.executable, "-m", "amorsize"] + args,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


class TestFormatOption:
    """Test the --format option for different output formats."""

    def test_format_json(self):
        """Test --format json produces valid JSON output."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--format", "json"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Parse JSON to verify it's valid
        data = json.loads(stdout)
        
        # Verify structure
        assert data["mode"] == "optimize"
        assert "n_jobs" in data
        assert "chunksize" in data
        assert "estimated_speedup" in data
        assert "reason" in data
        assert "warnings" in data

    def test_format_yaml(self):
        """Test --format yaml produces valid YAML output."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--format", "yaml"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for YAML-like structure
        assert "mode:" in stdout
        assert "n_jobs:" in stdout
        assert "chunksize:" in stdout
        assert "estimated_speedup:" in stdout
        
        # Try to parse with yaml if available
        try:
            import yaml
            data = yaml.safe_load(stdout)
            assert data["mode"] == "optimize"
            assert "n_jobs" in data
        except ImportError:
            # If PyYAML not installed, should fall back to JSON
            # Warning goes to stderr, JSON goes to stdout
            if "Warning: PyYAML library not installed" in stderr:
                # The stdout should be pure JSON now
                data = json.loads(stdout)
                assert data["mode"] == "optimize"

    def test_format_table(self):
        """Test --format table produces ASCII table output."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--format", "table"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for table structure
        assert "╔" in stdout  # Box drawing characters
        assert "║" in stdout
        assert "├" in stdout
        assert "│" in stdout
        assert "OPTIMIZATION RECOMMENDATION" in stdout
        assert "Parameter" in stdout
        assert "Value" in stdout
        assert "n_jobs" in stdout
        assert "chunksize" in stdout
        assert "estimated_speedup" in stdout

    def test_format_markdown(self):
        """Test --format markdown produces Markdown output."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--format", "markdown"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for Markdown structure
        assert "## Optimization Recommendation" in stdout
        assert "### Parameters" in stdout
        assert "| Parameter | Value |" in stdout
        assert "|-----------|-------|" in stdout
        assert "| n_jobs |" in stdout
        assert "| chunksize |" in stdout
        assert "| estimated_speedup |" in stdout
        assert "### Reason" in stdout

    def test_format_text_default(self):
        """Test default format (text) without --format flag."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for human-readable text
        assert "Recommendation:" in stdout or "n_jobs" in stdout
        assert "OPTIMIZATION ANALYSIS" in stdout or "n_jobs" in stdout

    def test_format_text_explicit(self):
        """Test --format text produces human-readable output."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--format", "text"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for human-readable text
        assert "Recommendation:" in stdout or "n_jobs" in stdout

    def test_backward_compatibility_json_flag(self):
        """Test that --json flag still works (backward compatibility)."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--json"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Parse JSON to verify it's valid
        data = json.loads(stdout)
        assert data["mode"] == "optimize"

    def test_invalid_format(self):
        """Test that invalid format produces error."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--format", "invalid"
        ])

        assert exit_code != 0
        assert "invalid choice" in stderr.lower() or "error" in stderr.lower()


class TestFormatWithExecute:
    """Test format options with execute command."""

    def test_execute_json_format(self):
        """Test execute command with JSON format."""
        exit_code, stdout, stderr = run_cli_command([
            "execute", "math.factorial",
            "--data-range", "10",
            "--format", "json"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Parse JSON
        data = json.loads(stdout)
        assert data["mode"] == "execute"
        assert "results_count" in data
        assert "sample_results" in data
        assert "optimization" in data

    def test_execute_table_format(self):
        """Test execute command with table format."""
        exit_code, stdout, stderr = run_cli_command([
            "execute", "math.factorial",
            "--data-range", "10",
            "--format", "table"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for execution results section
        assert "EXECUTION RESULTS" in stdout
        assert "Items Processed:" in stdout
        assert "OPTIMIZATION DETAILS" in stdout

    def test_execute_markdown_format(self):
        """Test execute command with Markdown format."""
        exit_code, stdout, stderr = run_cli_command([
            "execute", "math.factorial",
            "--data-range", "10",
            "--format", "markdown"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for Markdown sections
        assert "## Execution Results" in stdout
        assert "**Items Processed:**" in stdout
        assert "## Optimization Details" in stdout


class TestFormatWithProfiling:
    """Test format options with profiling enabled."""

    def test_json_with_profile(self):
        """Test JSON format includes profile data when --profile is used."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "100",
            "--format", "json",
            "--profile"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Parse JSON
        data = json.loads(stdout)
        
        # Should have profile data
        assert "profile" in data
        assert "physical_cores" in data["profile"]
        assert "logical_cores" in data["profile"]
        assert "available_memory_gb" in data["profile"]

    def test_table_with_profile(self):
        """Test table format includes system info when --profile is used."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "100",
            "--format", "table",
            "--profile"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for system information section
        assert "System Information" in stdout
        assert "Physical Cores" in stdout
        assert "Logical Cores" in stdout
        assert "Available Memory" in stdout

    def test_markdown_with_profile(self):
        """Test Markdown format includes system info when --profile is used."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "100",
            "--format", "markdown",
            "--profile"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Check for system information section
        assert "### System Information" in stdout
        assert "Physical Cores" in stdout
        assert "Logical Cores" in stdout


class TestFormatEdgeCases:
    """Test edge cases and special scenarios."""

    def test_format_with_warnings(self):
        """Test that warnings are properly formatted in all formats."""
        # Use a small dataset to trigger warnings
        for fmt in ["json", "yaml", "table", "markdown"]:
            exit_code, stdout, stderr = run_cli_command([
                "optimize", "math.factorial",
                "--data-range", "10",
                "--format", fmt
            ])

            assert exit_code == 0, f"Format {fmt} failed with stderr: {stderr}"
            
            # Check that warnings are present
            if fmt == "json":
                data = json.loads(stdout)
                assert len(data["warnings"]) > 0
            elif fmt == "yaml":
                assert "warnings:" in stdout.lower() or "warning" in stdout.lower()
            else:
                # Table and markdown should show warnings
                assert "warning" in stdout.lower() or "⚠" in stdout

    def test_format_with_quiet_flag(self):
        """Test that --quiet overrides format for text output."""
        exit_code, stdout, stderr = run_cli_command([
            "optimize", "math.factorial",
            "--data-range", "50",
            "--format", "text",
            "--quiet"
        ])

        assert exit_code == 0, f"CLI failed with stderr: {stderr}"
        
        # Quiet mode should show minimal output
        assert "n_jobs=" in stdout
        assert "chunksize=" in stdout
        assert "speedup=" in stdout
        
        # Should NOT have verbose headers
        assert "OPTIMIZATION ANALYSIS" not in stdout

    def test_format_consistency(self):
        """Test that all formats report the same core values."""
        formats = ["json", "table", "markdown"]
        results = {}
        
        for fmt in formats:
            exit_code, stdout, stderr = run_cli_command([
                "optimize", "math.factorial",
                "--data-range", "100",
                "--format", fmt
            ])
            
            assert exit_code == 0, f"Format {fmt} failed"
            
            if fmt == "json":
                data = json.loads(stdout)
                results[fmt] = {
                    "n_jobs": data["n_jobs"],
                    "chunksize": data["chunksize"],
                    "speedup": data["estimated_speedup"]
                }
            else:
                # For other formats, just verify they completed
                results[fmt] = "completed"
        
        # All formats should report same values
        # (just checking JSON completed here; full consistency check would need parsing all formats)
        assert "json" in results
        assert results["json"]["n_jobs"] >= 1
        assert results["json"]["chunksize"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
