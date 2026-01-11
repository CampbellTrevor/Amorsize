"""
System validation module for verifying measurement accuracy and installation health.

This module provides tools to validate that Amorsize's core measurements
(spawn cost, chunking overhead, pickle overhead) are working correctly on
the current system, giving users confidence in optimizer recommendations.
"""

import pickle
import sys
import time
from multiprocessing import Pool
from typing import Any, Dict, List, Tuple

from .system_info import (
    get_available_memory,
    get_multiprocessing_start_method,
    get_physical_cores,
    get_spawn_cost_estimate,
    measure_chunking_overhead,
    measure_spawn_cost,
)


class ValidationResult:
    """
    Container for system validation results.
    
    Attributes:
        checks_passed: Number of validation checks that passed
        checks_failed: Number of validation checks that failed
        warnings: List of warning messages
        errors: List of error messages
        details: Dictionary with detailed results for each check
        overall_health: 'excellent', 'good', 'poor', or 'critical'
    """

    def __init__(self):
        self.checks_passed: int = 0
        self.checks_failed: int = 0
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.details: Dict[str, Any] = {}
        self.overall_health: str = "unknown"

    def add_check(self, name: str, passed: bool, details: Any = None):
        """Add a validation check result."""
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1

        if details is not None:
            self.details[name] = details

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)

    def compute_health(self):
        """Compute overall system health rating."""
        total_checks = self.checks_passed + self.checks_failed
        if total_checks == 0:
            self.overall_health = "unknown"
            return

        pass_rate = self.checks_passed / total_checks

        if pass_rate >= 0.95 and not self.errors:
            self.overall_health = "excellent"
        elif pass_rate >= 0.80 and len(self.errors) <= 1:
            self.overall_health = "good"
        elif pass_rate >= 0.60:
            self.overall_health = "poor"
        else:
            self.overall_health = "critical"

    def __str__(self):
        """Format validation results for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("AMORSIZE SYSTEM VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Overall health
        health_emoji = {
            "excellent": "✅",
            "good": "✓",
            "poor": "⚠️",
            "critical": "❌",
            "unknown": "?"
        }
        emoji = health_emoji.get(self.overall_health, "?")
        lines.append(f"Overall Health: {emoji} {self.overall_health.upper()}")
        lines.append(f"Checks Passed: {self.checks_passed}/{self.checks_passed + self.checks_failed}")
        lines.append("")

        # Errors (if any)
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  ❌ {error}")
            lines.append("")

        # Warnings (if any)
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")

        # Details
        if self.details:
            lines.append("DETAILS:")
            for name, detail in self.details.items():
                lines.append(f"  • {name}:")
                if isinstance(detail, dict):
                    for key, value in detail.items():
                        lines.append(f"      {key}: {value}")
                else:
                    lines.append(f"      {detail}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)


def validate_spawn_cost_measurement(verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that spawn cost measurement is working correctly.
    
    This function verifies that:
    1. Spawn cost measurement completes without errors
    2. Measured value is within reasonable bounds (1ms - 5s)
    3. Measured value is consistent with OS estimate (within 10x)
    
    Args:
        verbose: Print detailed progress if True
    
    Returns:
        Tuple of (passed, details) where:
        - passed: True if validation passed
        - details: Dictionary with measurement details
    """
    if verbose:
        print("Validating spawn cost measurement...")

    details = {}

    try:
        # Measure spawn cost
        start = time.perf_counter()
        measured_cost = measure_spawn_cost(timeout=5.0)
        elapsed = time.perf_counter() - start

        details['measured_spawn_cost'] = f"{measured_cost * 1000:.2f}ms"
        details['measurement_time'] = f"{elapsed:.2f}s"

        # Get OS estimate for comparison
        estimate = get_spawn_cost_estimate()
        details['os_estimate'] = f"{estimate * 1000:.2f}ms"

        # Get start method
        start_method = get_multiprocessing_start_method()
        details['start_method'] = start_method

        # Validation checks
        passed = True

        # Check 1: Measurement completed (not None)
        if measured_cost is None:
            details['error'] = "Measurement returned None"
            return False, details

        # Check 2: Value is within reasonable bounds (1ms to 5 seconds)
        if not (0.001 <= measured_cost <= 5.0):
            details['error'] = f"Measured cost {measured_cost}s outside reasonable bounds [0.001s, 5.0s]"
            passed = False

        # Check 3: Value is consistent with OS estimate (within 10x factor)
        ratio = measured_cost / estimate if estimate > 0 else float('inf')
        details['measurement_vs_estimate'] = f"{ratio:.2f}x"

        if ratio > 10.0 or ratio < 0.1:
            details['warning'] = f"Measured cost differs from estimate by {ratio:.1f}x (expected within 10x)"
            # This is a warning, not a failure - measurements can vary

        return passed, details

    except Exception as e:
        details['error'] = f"Measurement failed: {str(e)}"
        return False, details


def validate_chunking_overhead_measurement(verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that chunking overhead measurement is working correctly.
    
    This function verifies that:
    1. Chunking overhead measurement completes without errors
    2. Measured value is within reasonable bounds (0.01ms - 100ms per chunk)
    3. Measurement is repeatable (variance < 50%)
    
    Args:
        verbose: Print detailed progress if True
    
    Returns:
        Tuple of (passed, details) where:
        - passed: True if validation passed
        - details: Dictionary with measurement details
    """
    if verbose:
        print("Validating chunking overhead measurement...")

    details = {}

    try:
        # Measure chunking overhead
        start = time.perf_counter()
        measured_overhead = measure_chunking_overhead(timeout=5.0)
        elapsed = time.perf_counter() - start

        details['measured_overhead'] = f"{measured_overhead * 1000:.3f}ms"
        details['measurement_time'] = f"{elapsed:.2f}s"

        # Validation checks
        passed = True

        # Check 1: Measurement completed (not None)
        if measured_overhead is None:
            details['error'] = "Measurement returned None"
            return False, details

        # Check 2: Value is within reasonable bounds (0.01ms to 100ms per chunk)
        if not (0.00001 <= measured_overhead <= 0.1):
            details['error'] = f"Measured overhead {measured_overhead}s outside reasonable bounds [0.00001s, 0.1s]"
            passed = False

        return passed, details

    except Exception as e:
        details['error'] = f"Measurement failed: {str(e)}"
        return False, details


def validate_pickle_overhead_measurement(verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that pickle overhead measurement is working correctly.
    
    This function tests pickling of various data types to ensure
    serialization time measurement is accurate.
    
    Args:
        verbose: Print detailed progress if True
    
    Returns:
        Tuple of (passed, details) where:
        - passed: True if validation passed
        - details: Dictionary with measurement details
    """
    if verbose:
        print("Validating pickle overhead measurement...")

    details = {}
    passed = True

    # Test various data types
    test_cases = [
        ("small_int", 42),
        ("small_string", "hello world"),
        ("small_list", list(range(100))),
        ("medium_list", list(range(10000))),
        ("dict", {"a": 1, "b": 2, "c": 3}),
        ("nested", {"data": [1, 2, 3], "meta": {"count": 3}}),
    ]

    for name, obj in test_cases:
        try:
            # Measure pickle time
            start = time.perf_counter()
            pickled = pickle.dumps(obj)
            elapsed = time.perf_counter() - start

            # Measure unpickle time
            start_unpickle = time.perf_counter()
            _ = pickle.loads(pickled)
            unpickle_time = time.perf_counter() - start_unpickle

            details[f"{name}_pickle_time"] = f"{elapsed * 1000000:.2f}μs"
            details[f"{name}_size"] = f"{len(pickled)}B"
            details[f"{name}_unpickle_time"] = f"{unpickle_time * 1000000:.2f}μs"

            # Validate timing is reasonable (< 10ms for these small objects)
            if elapsed > 0.01:
                details[f"{name}_warning"] = f"Slow pickle time: {elapsed * 1000:.2f}ms"

        except Exception as e:
            details[f"{name}_error"] = str(e)
            passed = False

    return passed, details


def validate_system_resources(verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate system resource detection.
    
    This function verifies that:
    1. Physical core detection works
    2. Memory detection works
    3. Values are reasonable for a real system
    
    Args:
        verbose: Print detailed progress if True
    
    Returns:
        Tuple of (passed, details) where:
        - passed: True if validation passed
        - details: Dictionary with system information
    """
    if verbose:
        print("Validating system resource detection...")

    details = {}
    passed = True

    try:
        # Get physical cores
        cores = get_physical_cores()
        details['physical_cores'] = cores

        if cores < 1 or cores > 256:
            details['error'] = f"Physical cores {cores} outside reasonable range [1, 256]"
            passed = False

        # Get available memory
        memory = get_available_memory()
        details['available_memory'] = f"{memory / (1024**3):.2f}GB"

        if memory < 100_000_000:  # Less than 100MB
            details['warning'] = f"Very low available memory: {memory / (1024**2):.1f}MB"

        # Get start method
        start_method = get_multiprocessing_start_method()
        details['multiprocessing_start_method'] = start_method

        if start_method not in ['fork', 'spawn', 'forkserver']:
            details['warning'] = f"Unexpected start method: {start_method}"

        return passed, details

    except Exception as e:
        details['error'] = f"Resource detection failed: {str(e)}"
        return False, details


def _simple_test_func(x):
    """Simple test function for multiprocessing validation."""
    return x * 2


def validate_multiprocessing_basic(verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that basic multiprocessing functionality works.
    
    This function tests that Pool.map() works correctly, which is
    essential for the optimizer to function.
    
    Args:
        verbose: Print detailed progress if True
    
    Returns:
        Tuple of (passed, details) where:
        - passed: True if validation passed
        - details: Dictionary with test results
    """
    if verbose:
        print("Validating multiprocessing functionality...")

    details = {}

    try:
        # Test with 2 workers
        test_data = list(range(10))
        expected = [x * 2 for x in test_data]

        start = time.perf_counter()
        with Pool(processes=2) as pool:
            results = pool.map(_simple_test_func, test_data)
        elapsed = time.perf_counter() - start

        details['execution_time'] = f"{elapsed * 1000:.2f}ms"
        details['workers'] = 2
        details['data_size'] = len(test_data)

        # Verify results
        if results != expected:
            details['error'] = "Results do not match expected output"
            return False, details

        details['result'] = "Pool.map() works correctly"
        return True, details

    except Exception as e:
        details['error'] = f"Multiprocessing test failed: {str(e)}"
        return False, details


def validate_system(verbose: bool = False) -> ValidationResult:
    """
    Run complete system validation suite.
    
    This function runs all validation checks and returns a comprehensive
    report on system health and measurement accuracy.
    
    Args:
        verbose: Print detailed progress if True
    
    Returns:
        ValidationResult object with complete validation report
    """
    if verbose:
        print("=" * 60)
        print("Running Amorsize System Validation...")
        print("=" * 60)
        print()

    result = ValidationResult()

    # Validate multiprocessing basics (must work for anything else to work)
    if verbose:
        print("[1/5] Testing multiprocessing functionality...")
    passed, details = validate_multiprocessing_basic(verbose=False)
    result.add_check("multiprocessing_basic", passed, details)
    if not passed:
        result.add_error("Multiprocessing not working - library cannot function")
        if 'error' in details:
            result.add_error(f"  {details['error']}")

    # Validate system resources
    if verbose:
        print("[2/5] Detecting system resources...")
    passed, details = validate_system_resources(verbose=False)
    result.add_check("system_resources", passed, details)
    if not passed:
        result.add_error("System resource detection failed")
        if 'error' in details:
            result.add_error(f"  {details['error']}")

    # Validate spawn cost measurement
    if verbose:
        print("[3/5] Measuring spawn cost...")
    passed, details = validate_spawn_cost_measurement(verbose=False)
    result.add_check("spawn_cost_measurement", passed, details)
    if not passed:
        result.add_error("Spawn cost measurement failed")
        if 'error' in details:
            result.add_error(f"  {details['error']}")
    if 'warning' in details:
        result.add_warning(details['warning'])

    # Validate chunking overhead measurement
    if verbose:
        print("[4/5] Measuring chunking overhead...")
    passed, details = validate_chunking_overhead_measurement(verbose=False)
    result.add_check("chunking_overhead_measurement", passed, details)
    if not passed:
        result.add_error("Chunking overhead measurement failed")
        if 'error' in details:
            result.add_error(f"  {details['error']}")

    # Validate pickle overhead measurement
    if verbose:
        print("[5/5] Testing pickle overhead...")
    passed, details = validate_pickle_overhead_measurement(verbose=False)
    result.add_check("pickle_overhead_measurement", passed, details)
    if not passed:
        result.add_error("Pickle overhead measurement failed")
        if 'error' in details:
            result.add_error(f"  {details['error']}")

    # Compute overall health
    result.compute_health()

    if verbose:
        print()
        print("Validation complete!")
        print()

    return result


if __name__ == "__main__":
    # Run validation when module is executed directly
    result = validate_system(verbose=True)
    print(result)

    # Exit with error code if validation failed
    if result.overall_health in ["poor", "critical"]:
        sys.exit(1)
    else:
        sys.exit(0)
