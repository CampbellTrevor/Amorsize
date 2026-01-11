#!/usr/bin/env python3
"""
Demo: Output Format Options

This demo showcases the different output formats available in Amorsize CLI:
- text (default, human-readable)
- json (machine-readable, for scripts/CI)
- yaml (readable structured format)
- table (ASCII table format)
- markdown (for documentation)

Run this script to see examples of all output formats.
"""

import subprocess
import sys


def run_example(description: str, command: list):
    """Run a command and display its output."""
    print("\n" + "=" * 80)
    print(f"  {description}")
    print("=" * 80)
    print(f"\nCommand: {' '.join(command)}\n")
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"Error (exit code {result.returncode}):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    print()


def main():
    """Run examples demonstrating all format options."""
    print("=" * 80)
    print("  AMORSIZE OUTPUT FORMAT OPTIONS DEMO")
    print("=" * 80)
    print("\nThis demo shows how different output formats display the same optimization")
    print("results. All examples use the same function (math.factorial) and data.")
    print("\n" + "=" * 80)
    
    # Example 1: Text format (default)
    run_example(
        "Example 1: Text Format (Default - Human-Readable)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100"]
    )
    
    # Example 2: Quiet text format
    run_example(
        "Example 2: Text Format with --quiet (Minimal Output)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100", "--quiet"]
    )
    
    # Example 3: JSON format
    run_example(
        "Example 3: JSON Format (Machine-Readable, for CI/CD & Scripts)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100", "--format", "json"]
    )
    
    # Example 4: YAML format
    run_example(
        "Example 4: YAML Format (Readable Structured Data)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100", "--format", "yaml"]
    )
    
    # Example 5: Table format
    run_example(
        "Example 5: Table Format (ASCII Table)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100", "--format", "table"]
    )
    
    # Example 6: Markdown format
    run_example(
        "Example 6: Markdown Format (For Documentation)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100", "--format", "markdown"]
    )
    
    # Example 7: Table with profiling
    run_example(
        "Example 7: Table Format with Profiling (Shows System Info)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100", "--format", "table", "--profile"]
    )
    
    # Example 8: JSON with profiling
    run_example(
        "Example 8: JSON Format with Profiling (Complete Data)",
        ["python", "-m", "amorsize", "optimize", "math.factorial", "--data-range", "100", "--format", "json", "--profile"]
    )
    
    # Summary
    print("=" * 80)
    print("  SUMMARY OF FORMAT OPTIONS")
    print("=" * 80)
    print("""
Format Options:
  --format text      : Human-readable output with colors (default)
  --format json      : JSON format for scripts and CI/CD pipelines
  --format yaml      : YAML format (requires PyYAML: pip install pyyaml)
  --format table     : ASCII table format for clear structure
  --format markdown  : Markdown format for documentation

Additional Flags:
  --quiet            : Minimal text output (just the recommendation)
  --profile          : Include detailed profiling data
  --explain          : Add user-friendly explanation (text format only)
  --tips             : Show optimization tips (text format only)
  --show-overhead    : Show overhead breakdown (text format only)

Use Cases:
  • CI/CD Pipelines     → Use --format json for parsing
  • Documentation       → Use --format markdown
  • Interactive Use     → Use --format text (default)
  • Quick Checks        → Use --format text --quiet
  • Config Files        → Use --format yaml
  • Reports             → Use --format table

Backward Compatibility:
  • --json flag still works (equivalent to --format json)
    """)


if __name__ == "__main__":
    main()
