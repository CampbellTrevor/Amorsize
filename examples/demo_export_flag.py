#!/usr/bin/env python3
"""
Demo script showcasing the --export flag functionality.

This script demonstrates how to export comprehensive diagnostic
information to files for later analysis, documentation, or sharing.
"""

import json
import math
import os
import subprocess
import sys
import tempfile


def demo_basic_json_export():
    """Demo: Basic JSON export without profiling."""
    print("=" * 70)
    print("DEMO 1: Basic JSON Export")
    print("=" * 70)
    print()
    
    # Use tempfile for cross-platform compatibility
    export_file = os.path.join(tempfile.gettempdir(), "amorsize_export_basic.json")
    
    print(f"Running: amorsize optimize math.sqrt --data-range 1000 --export {export_file}\n")
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'amorsize',
            'optimize', 'math.sqrt',
            '--data-range', '1000',
            '--export', export_file,
            '--quiet'
        ],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if os.path.exists(export_file):
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n✓ Diagnostics exported to: {export_file}")
        print(f"  File size: {os.path.getsize(export_file)} bytes")
        print(f"  Mode: {data['mode']}")
        print(f"  n_jobs: {data['n_jobs']}")
        print(f"  chunksize: {data['chunksize']}")
        print(f"  estimated_speedup: {data['estimated_speedup']}x")
        print()
        os.remove(export_file)


def demo_profile_json_export():
    """Demo: JSON export with comprehensive profiling data."""
    print("=" * 70)
    print("DEMO 2: Comprehensive Profile Export (JSON)")
    print("=" * 70)
    print()
    
    # Use tempfile for cross-platform compatibility
    export_file = os.path.join(tempfile.gettempdir(), "amorsize_export_profile.json")
    
    print(f"Running: amorsize optimize math.factorial --data-range 5000 --profile --export {export_file}\n")
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'amorsize',
            'optimize', 'math.factorial',
            '--data-range', '5000',
            '--profile',
            '--export', export_file,
            '--quiet'
        ],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if os.path.exists(export_file):
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n✓ Diagnostics with profile exported to: {export_file}")
        print(f"  File size: {os.path.getsize(export_file)} bytes")
        
        if 'profile' in data:
            profile = data['profile']
            print(f"\n  Profile data included:")
            print(f"    • Physical cores: {profile.get('physical_cores', 'N/A')}")
            print(f"    • Logical cores: {profile.get('logical_cores', 'N/A')}")
            print(f"    • Spawn cost: {profile.get('spawn_cost_ms', 'N/A')}ms")
            print(f"    • Available memory: {profile.get('available_memory_gb', 'N/A')} GB")
            print(f"    • Start method: {profile.get('start_method', 'N/A')}")
            print(f"    • Workload type: {profile.get('workload_type', 'N/A')}")
            print(f"    • Avg execution time: {profile.get('avg_execution_time_ms', 'N/A')}ms")
        print()
        os.remove(export_file)


def demo_yaml_export():
    """Demo: YAML export for human-readable output."""
    print("=" * 70)
    print("DEMO 3: YAML Export (Human-Readable Format)")
    print("=" * 70)
    print()
    
    # Use tempfile for cross-platform compatibility
    export_file = os.path.join(tempfile.gettempdir(), "amorsize_export.yaml")
    
    print(f"Running: amorsize optimize math.sqrt --data-range 2000 --export {export_file}\n")
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'amorsize',
            'optimize', 'math.sqrt',
            '--data-range', '2000',
            '--export', export_file,
            '--quiet'
        ],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if os.path.exists(export_file):
        with open(export_file, 'r') as f:
            content = f.read()
        
        print(f"\n✓ Diagnostics exported to: {export_file}")
        print(f"  File size: {os.path.getsize(export_file)} bytes")
        print(f"\n  Content preview (first 300 characters):")
        print("  " + "-" * 60)
        print("  " + "\n  ".join(content[:300].split('\n')))
        print("  " + "-" * 60)
        print()
        os.remove(export_file)


def demo_execute_with_export():
    """Demo: Export from execute command."""
    print("=" * 70)
    print("DEMO 4: Export with Execute Command")
    print("=" * 70)
    print()
    
    # Use tempfile for cross-platform compatibility
    export_file = os.path.join(tempfile.gettempdir(), "amorsize_execute_export.json")
    
    print(f"Running: amorsize execute math.sqrt --data-range 500 --export {export_file}\n")
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'amorsize',
            'execute', 'math.sqrt',
            '--data-range', '500',
            '--export', export_file,
            '--quiet'
        ],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if os.path.exists(export_file):
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n✓ Execution results exported to: {export_file}")
        print(f"  Optimization parameters:")
        print(f"    • n_jobs: {data.get('n_jobs', 'N/A')}")
        print(f"    • chunksize: {data.get('chunksize', 'N/A')}")
        print()
        os.remove(export_file)


def demo_verbose_export():
    """Demo: Export with verbose output."""
    print("=" * 70)
    print("DEMO 5: Export with Verbose Confirmation")
    print("=" * 70)
    print()
    
    # Use tempfile for cross-platform compatibility
    export_file = os.path.join(tempfile.gettempdir(), "amorsize_export_verbose.json")
    
    print(f"Running: amorsize optimize math.sqrt --data-range 1000 --export {export_file} --verbose\n")
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'amorsize',
            'optimize', 'math.sqrt',
            '--data-range', '1000',
            '--export', export_file,
            '--verbose'
        ],
        capture_output=True,
        text=True
    )
    
    # Show last 10 lines of output (including export confirmation)
    output_lines = result.stdout.split('\n')
    print('\n'.join(output_lines[-10:]))
    print()
    
    if os.path.exists(export_file):
        os.remove(export_file)


def demo_explicit_format():
    """Demo: Explicit export format specification."""
    print("=" * 70)
    print("DEMO 6: Explicit Export Format")
    print("=" * 70)
    print()
    
    # Use tempfile for cross-platform compatibility
    # Export YAML to .txt file using explicit format flag
    export_file = os.path.join(tempfile.gettempdir(), "amorsize_export.txt")
    
    print(f"Running: amorsize optimize math.factorial --data-range 1000")
    print(f"         --export {export_file} --export-format yaml\n")
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'amorsize',
            'optimize', 'math.factorial',
            '--data-range', '1000',
            '--export', export_file,
            '--export-format', 'yaml',
            '--quiet'
        ],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if os.path.exists(export_file):
        with open(export_file, 'r') as f:
            content = f.read()
        
        print(f"\n✓ YAML diagnostics exported to: {export_file}")
        print(f"  (Format explicitly specified as 'yaml')")
        print(f"  File extension: .txt")
        print(f"  Content format: YAML")
        print()
        os.remove(export_file)


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("AMORSIZE --export FLAG DEMO")
    print("=" * 70)
    print()
    print("This demo showcases the --export flag, which allows you to save")
    print("comprehensive diagnostic information to files for later analysis,")
    print("documentation, or sharing.")
    print()
    
    try:
        demo_basic_json_export()
        demo_profile_json_export()
        demo_yaml_export()
        demo_execute_with_export()
        demo_verbose_export()
        demo_explicit_format()
        
        print("=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print()
        print("Key Features:")
        print("  • Export to JSON or YAML format")
        print("  • Automatic format detection from file extension")
        print("  • Works with both 'optimize' and 'execute' commands")
        print("  • Include comprehensive profile data with --profile flag")
        print("  • Export confirmation with --verbose flag")
        print("  • Explicit format control with --export-format flag")
        print()
        print("Usage Examples:")
        print("  amorsize optimize func --data-range 1000 --export report.json")
        print("  amorsize optimize func --data-range 1000 --export report.yaml")
        print("  amorsize optimize func --data-range 1000 --profile --export full_report.json")
        print("  amorsize execute func --data-file data.txt --export results.json")
        print()
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
