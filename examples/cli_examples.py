"""
CLI Examples for Amorsize

This module demonstrates various ways to use the Amorsize CLI.
"""

import subprocess
import sys
import tempfile
from pathlib import Path


def example_1_basic_optimize():
    """Example 1: Basic optimization analysis."""
    print("="*70)
    print("Example 1: Basic Optimization Analysis")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize optimize math.sqrt --data-range 1000")
    print("\nDescription:")
    print("  Analyze whether parallelizing math.sqrt on 1000 items is worthwhile")
    print()


def example_2_json_output():
    """Example 2: JSON output for scripting."""
    print("="*70)
    print("Example 2: JSON Output for Scripting")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize optimize math.factorial --data-range 100 --json")
    print("\nDescription:")
    print("  Get machine-readable JSON output for use in scripts or CI/CD")
    print("\nUse case:")
    print("  # Parse with jq in shell scripts")
    print("  n_jobs=$(python -m amorsize optimize math.factorial --data-range 100 --json | jq '.n_jobs')")
    print()


def example_3_detailed_profile():
    """Example 3: Detailed diagnostic profiling."""
    print("="*70)
    print("Example 3: Detailed Diagnostic Profiling")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize optimize mymodule.process --data-range 500 --profile")
    print("\nDescription:")
    print("  Get comprehensive breakdown of overhead sources and decision rationale")
    print("\nShows:")
    print("  - Workload analysis (execution time, pickle overhead)")
    print("  - System resources (cores, spawn cost)")
    print("  - Optimization decision (n_jobs, chunksize)")
    print("  - Performance prediction (speedup, efficiency)")
    print("  - Overhead breakdown (spawn, IPC, chunking %)")
    print()


def example_4_execute_from_file():
    """Example 4: Execute function on data from file."""
    print("="*70)
    print("Example 4: Execute Function on Data from File")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize execute mymodule.process_record --data-file records.txt")
    print("\nDescription:")
    print("  Optimize and execute function on data read from a file")
    print("  Each line in the file is one data item")
    print("\nUse case:")
    print("  Process a list of IDs, URLs, or records stored in a text file")
    print()


def example_5_stdin_pipeline():
    """Example 5: Read data from stdin for pipelines."""
    print("="*70)
    print("Example 5: Read Data from Stdin for Pipelines")
    print("="*70)
    print("\nCommand:")
    print("  cat urls.txt | python -m amorsize execute mymodule.fetch_url --data-stdin")
    print("\nDescription:")
    print("  Read data from stdin for integration into Unix pipelines")
    print("\nUse case:")
    print("  # Process output from other commands")
    print("  find . -name '*.log' | python -m amorsize execute mymodule.analyze_log --data-stdin")
    print()


def example_6_verbose_debugging():
    """Example 6: Verbose mode for debugging."""
    print("="*70)
    print("Example 6: Verbose Mode for Debugging")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize optimize mymodule.func --data-range 100 --verbose")
    print("\nDescription:")
    print("  Enable verbose output to see detailed decision-making process")
    print("\nShows:")
    print("  - Sampling progress")
    print("  - System detection results")
    print("  - Overhead measurements")
    print("  - Decision checkpoints")
    print()


def example_7_custom_parameters():
    """Example 7: Custom optimization parameters."""
    print("="*70)
    print("Example 7: Custom Optimization Parameters")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize optimize mymodule.func \\")
    print("    --data-range 1000 \\")
    print("    --sample-size 10 \\")
    print("    --target-chunk-duration 0.5")
    print("\nDescription:")
    print("  Customize sampling and chunking parameters")
    print("\nParameters:")
    print("  --sample-size: Number of items to sample (default: 5)")
    print("  --target-chunk-duration: Target seconds per chunk (default: 0.2)")
    print()


def example_8_disable_benchmarks():
    """Example 8: Disable benchmarks for faster analysis."""
    print("="*70)
    print("Example 8: Disable Benchmarks for Faster Analysis")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize optimize mymodule.func \\")
    print("    --data-range 1000 \\")
    print("    --no-spawn-benchmark \\")
    print("    --no-chunking-benchmark")
    print("\nDescription:")
    print("  Skip spawn/chunking overhead measurements and use OS-based estimates")
    print("  Reduces analysis time by ~25ms but may be less accurate")
    print("\nUse case:")
    print("  Quick analysis when exact overhead isn't critical")
    print()


def example_9_nested_parallelism():
    """Example 9: Disable auto-adjustment for nested parallelism."""
    print("="*70)
    print("Example 9: Control Nested Parallelism Auto-Adjustment")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize optimize mymodule.numpy_func \\")
    print("    --data-range 1000 \\")
    print("    --no-auto-adjust")
    print("\nDescription:")
    print("  Disable automatic n_jobs reduction for detected nested parallelism")
    print("  Useful when you've already set thread limits via environment variables")
    print("\nNote:")
    print("  By default, Amorsize detects nested parallelism (NumPy, PyTorch, etc.)")
    print("  and automatically adjusts n_jobs to prevent thread oversubscription")
    print()


def example_10_real_world_use_case():
    """Example 10: Real-world use case - image processing."""
    print("="*70)
    print("Example 10: Real-World Use Case - Image Processing")
    print("="*70)
    print("\nScenario:")
    print("  Process 1000 images with a resize function")
    print("\nStep 1: Analyze optimal parameters")
    print("  python -m amorsize optimize myapp.resize_image \\")
    print("    --data-file image_list.txt \\")
    print("    --profile \\")
    print("    --json > optimization_report.json")
    print("\nStep 2: Use in production code")
    print("  from amorsize import optimize")
    print("  result = optimize(resize_image, image_paths)")
    print("  # Use result.n_jobs and result.chunksize")
    print("\nOr: Execute directly")
    print("  python -m amorsize execute myapp.resize_image \\")
    print("    --data-file image_list.txt \\")
    print("    --verbose")
    print()


def example_11_system_validation():
    """Example 11: System validation."""
    print("="*70)
    print("Example 11: System Validation")
    print("="*70)
    print("\nCommand:")
    print("  python -m amorsize validate")
    print("\nDescription:")
    print("  Validate that Amorsize measurements are working correctly on your system")
    print("\nShows:")
    print("  - Multiprocessing basic functionality test")
    print("  - System resources (cores, memory, start method)")
    print("  - Spawn cost measurement accuracy")
    print("  - Chunking overhead measurement")
    print("  - Pickle overhead for various data types")
    print("\nUse cases:")
    print("  # Post-installation health check")
    print("  python -m amorsize validate")
    print()
    print("  # CI/CD integration - fail if system unhealthy")
    print("  python -m amorsize validate && deploy.sh")
    print()
    print("  # Get JSON output for programmatic checks")
    print("  python -m amorsize validate --json")
    print()


def main():
    """Run all examples."""
    examples = [
        example_1_basic_optimize,
        example_2_json_output,
        example_3_detailed_profile,
        example_4_execute_from_file,
        example_5_stdin_pipeline,
        example_6_verbose_debugging,
        example_7_custom_parameters,
        example_8_disable_benchmarks,
        example_9_nested_parallelism,
        example_10_real_world_use_case,
        example_11_system_validation,
    ]
    
    print("\n" + "="*70)
    print("AMORSIZE CLI EXAMPLES")
    print("="*70)
    print("\nThis file demonstrates various ways to use the Amorsize CLI.")
    print("Run any example command to see it in action!\n")
    
    for example in examples:
        example()
        print()


if __name__ == "__main__":
    main()

