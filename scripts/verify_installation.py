#!/usr/bin/env python
"""
Installation verification script for Amorsize.

This script performs a quick smoke test to verify that Amorsize is correctly
installed and all critical components are functioning properly.

Run this after installing Amorsize to ensure everything works:
    python scripts/verify_installation.py

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import sys
import time
from typing import List, Tuple


def print_header(text: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def print_result(check_name: str, passed: bool, details: str = "") -> None:
    """Print a check result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status:8} {check_name}")
    if details:
        print(f"         {details}")


def check_import() -> Tuple[bool, str]:
    """Check that amorsize can be imported."""
    try:
        import amorsize
        # Try to get version, but don't fail if not available
        version = getattr(amorsize, '__version__', None)
        if version is None:
            # Try alternate version locations
            try:
                from importlib.metadata import version
                version = version('amorsize')
            except Exception:
                version = 'unknown'
        return True, f"Version: {version}"
    except ImportError as e:
        return False, f"Import error: {e}"


def check_optimize_basic() -> Tuple[bool, str]:
    """Check that basic optimize() function works."""
    try:
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        result = optimize(simple_func, range(10), sample_size=3, verbose=False)
        
        if not hasattr(result, 'n_jobs') or not hasattr(result, 'chunksize'):
            return False, "Result missing required attributes"
        
        if result.n_jobs < 1:
            return False, f"Invalid n_jobs: {result.n_jobs}"
        
        if result.chunksize < 1:
            return False, f"Invalid chunksize: {result.chunksize}"
        
        return True, f"n_jobs={result.n_jobs}, chunksize={result.chunksize}"
    except Exception as e:
        return False, f"Error: {e}"


def check_system_info() -> Tuple[bool, str]:
    """Check that system information detection works."""
    try:
        from amorsize.system_info import (
            get_physical_cores,
            get_logical_cores,
            get_available_memory,
            get_multiprocessing_start_method
        )
        
        phys = get_physical_cores()
        log = get_logical_cores()
        mem = get_available_memory()
        method = get_multiprocessing_start_method()
        
        if phys < 1:
            return False, f"Invalid physical cores: {phys}"
        
        if log < 1:
            return False, f"Invalid logical cores: {log}"
        
        if mem < 1:
            return False, f"Invalid memory: {mem}"
        
        if method not in ['fork', 'spawn', 'forkserver']:
            return False, f"Invalid start method: {method}"
        
        mem_gb = mem / (1024**3)
        return True, f"cores={phys}/{log}, memory={mem_gb:.1f}GB, method={method}"
    except Exception as e:
        return False, f"Error: {e}"


def check_generator_safety() -> Tuple[bool, str]:
    """Check that generator handling preserves data."""
    try:
        from amorsize import optimize
        
        def gen_func(x):
            return x + 1
        
        # Create generator
        gen = (i for i in range(100))
        
        # Optimize with generator
        result = optimize(gen_func, gen, sample_size=5, verbose=False)
        
        # Check that result.data is available and has correct length
        if result.data is None:
            return False, "result.data is None"
        
        # Convert to list to check length
        data_list = list(result.data)
        if len(data_list) != 100:
            return False, f"Expected 100 items, got {len(data_list)}"
        
        return True, "Generator data preserved correctly"
    except Exception as e:
        return False, f"Error: {e}"


def check_pickle_measurement() -> Tuple[bool, str]:
    """Check that pickle time measurement works."""
    try:
        from amorsize.sampling import perform_dry_run
        import operator
        
        # Use a built-in operator which is guaranteed to be picklable
        # (Functions defined inside other functions are not picklable)
        test_func = operator.neg
        
        # Perform dry run
        result = perform_dry_run(
            test_func, 
            list(range(5)),
            sample_size=3,
            enable_memory_tracking=False,
            enable_function_profiling=False
        )
        
        # Verify pickle times were measured
        if result.avg_pickle_time < 0:
            return False, f"Invalid pickle time: {result.avg_pickle_time}"
        
        # Check that results are correct
        if result.sample_count != 3:
            return False, f"Expected 3 samples, got {result.sample_count}"
        
        return True, f"pickle_time={result.avg_pickle_time*1000:.3f}ms, samples={result.sample_count}"
    except Exception as e:
        return False, f"Error: {e}"


def check_execute() -> Tuple[bool, str]:
    """Check that execute() convenience function works."""
    try:
        from amorsize import execute
        
        def multiply(x):
            return x * 3
        
        data = list(range(10))
        results = execute(multiply, data)
        
        if len(results) != len(data):
            return False, f"Expected {len(data)} results, got {len(results)}"
        
        expected = [x * 3 for x in data]
        if results != expected:
            return False, "Results don't match expected values"
        
        return True, "Parallel execution successful"
    except Exception as e:
        return False, f"Error: {e}"


def run_all_checks() -> bool:
    """Run all verification checks."""
    print_header("Amorsize Installation Verification")
    print("This script checks that Amorsize is correctly installed and functional.")
    
    checks = [
        ("Import amorsize", check_import),
        ("Basic optimize() function", check_optimize_basic),
        ("System information detection", check_system_info),
        ("Generator data preservation", check_generator_safety),
        ("Pickle time measurement", check_pickle_measurement),
        ("Parallel execute() function", check_execute),
    ]
    
    results = []
    for check_name, check_func in checks:
        passed, details = check_func()
        print_result(check_name, passed, details)
        results.append(passed)
    
    # Summary
    print_header("Summary")
    passed_count = sum(results)
    total_count = len(results)
    
    if passed_count == total_count:
        print(f"✓ All {total_count} checks passed!")
        print("\nAmorsize is correctly installed and ready to use.")
        return True
    else:
        failed_count = total_count - passed_count
        print(f"✗ {failed_count} of {total_count} checks failed.")
        print("\nPlease check the error messages above and ensure Amorsize is")
        print("properly installed: pip install -e .")
        return False


def main() -> int:
    """Main entry point."""
    try:
        all_passed = run_all_checks()
        return 0 if all_passed else 1
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user.")
        return 130
    except Exception as e:
        print(f"\n\nUnexpected error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
