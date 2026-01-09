"""
System Validation Demo - Verify Amorsize Installation Health

This example demonstrates how to use the system validation tool to:
1. Verify that Amorsize is correctly installed
2. Check that all measurements are working
3. Validate system-specific calibration
4. Debug unexpected optimizer recommendations

The validation tool provides confidence that the optimizer's measurements
(spawn cost, chunking overhead, pickle overhead) are accurate on your system.
"""

from amorsize import validate_system


def example_1_basic_validation():
    """
    Example 1: Basic system validation.
    
    This is the simplest way to check your Amorsize installation.
    Run this after installing to ensure everything works correctly.
    """
    print("=" * 70)
    print("EXAMPLE 1: Basic System Validation")
    print("=" * 70)
    print()
    
    # Run validation
    result = validate_system(verbose=False)
    
    # Print report
    print(result)
    
    # Check health
    if result.overall_health in ["excellent", "good"]:
        print("✅ Your system is healthy! Amorsize should work correctly.")
    else:
        print("⚠️ Some issues detected. Check the report above.")
    
    print()


def example_2_verbose_validation():
    """
    Example 2: Verbose validation with progress output.
    
    Use verbose mode to see what's being tested in real-time.
    Useful for debugging or understanding what the validator does.
    """
    print("=" * 70)
    print("EXAMPLE 2: Verbose System Validation")
    print("=" * 70)
    print()
    
    # Run validation with verbose output
    result = validate_system(verbose=True)
    
    # Print summary
    print()
    print(f"Overall Health: {result.overall_health.upper()}")
    print(f"Checks Passed: {result.checks_passed}/{result.checks_passed + result.checks_failed}")
    
    print()


def example_3_programmatic_health_check():
    """
    Example 3: Programmatic health check.
    
    Use validation results programmatically in scripts or CI/CD pipelines.
    This example shows how to check system health and react accordingly.
    """
    print("=" * 70)
    print("EXAMPLE 3: Programmatic Health Check")
    print("=" * 70)
    print()
    
    # Run validation
    result = validate_system(verbose=False)
    
    # Check system health
    print(f"System Health: {result.overall_health}")
    print(f"Checks Passed: {result.checks_passed}/{result.checks_passed + result.checks_failed}")
    print()
    
    # React based on health
    if result.overall_health == "excellent":
        print("✅ System is in excellent condition!")
        print("   All measurements are working correctly.")
        print("   Optimizer recommendations should be highly accurate.")
    
    elif result.overall_health == "good":
        print("✓ System is in good condition.")
        print("  Minor issues detected, but optimizer should work well.")
        if result.warnings:
            print("  Warnings:")
            for warning in result.warnings:
                print(f"    • {warning}")
    
    elif result.overall_health == "poor":
        print("⚠️ System has some issues.")
        print("   Optimizer may not work optimally.")
        print("   Review the issues below:")
        for error in result.errors:
            print(f"    ❌ {error}")
    
    else:  # critical
        print("❌ Critical system issues detected!")
        print("   Amorsize may not function correctly.")
        print("   Critical errors:")
        for error in result.errors:
            print(f"    • {error}")
    
    print()


def example_4_inspect_specific_measurements():
    """
    Example 4: Inspect specific measurement details.
    
    Access detailed information about each validation check.
    Useful for understanding system-specific characteristics.
    """
    print("=" * 70)
    print("EXAMPLE 4: Inspect Specific Measurements")
    print("=" * 70)
    print()
    
    # Run validation
    result = validate_system(verbose=False)
    
    # Inspect spawn cost measurement
    print("Spawn Cost Measurement:")
    if 'spawn_cost_measurement' in result.details:
        spawn_details = result.details['spawn_cost_measurement']
        print(f"  Measured: {spawn_details.get('measured_spawn_cost', 'N/A')}")
        print(f"  OS Estimate: {spawn_details.get('os_estimate', 'N/A')}")
        print(f"  Start Method: {spawn_details.get('start_method', 'N/A')}")
        print(f"  Ratio: {spawn_details.get('measurement_vs_estimate', 'N/A')}")
    print()
    
    # Inspect chunking overhead
    print("Chunking Overhead Measurement:")
    if 'chunking_overhead_measurement' in result.details:
        chunk_details = result.details['chunking_overhead_measurement']
        print(f"  Measured: {chunk_details.get('measured_overhead', 'N/A')}")
    print()
    
    # Inspect system resources
    print("System Resources:")
    if 'system_resources' in result.details:
        sys_details = result.details['system_resources']
        print(f"  Physical Cores: {sys_details.get('physical_cores', 'N/A')}")
        print(f"  Available Memory: {sys_details.get('available_memory', 'N/A')}")
        print(f"  Start Method: {sys_details.get('multiprocessing_start_method', 'N/A')}")
    print()


def example_5_ci_cd_integration():
    """
    Example 5: CI/CD integration pattern.
    
    Use validation in continuous integration to catch system issues early.
    This pattern ensures consistent behavior across environments.
    """
    print("=" * 70)
    print("EXAMPLE 5: CI/CD Integration Pattern")
    print("=" * 70)
    print()
    
    # Run validation
    result = validate_system(verbose=False)
    
    # For CI/CD, we want to fail fast on critical issues
    if result.overall_health == "critical":
        print("❌ CI/CD CHECK FAILED: Critical system issues")
        print("Details:")
        print(result)
        # In real CI/CD, you would: sys.exit(1)
        print("(In CI/CD, this would exit with code 1)")
    else:
        print("✅ CI/CD CHECK PASSED: System validation successful")
        print(f"   Health: {result.overall_health}")
        print(f"   Passed: {result.checks_passed}/{result.checks_passed + result.checks_failed}")
    
    print()


def example_6_troubleshooting_guide():
    """
    Example 6: Troubleshooting guide based on validation results.
    
    Provides actionable advice based on common validation issues.
    """
    print("=" * 70)
    print("EXAMPLE 6: Troubleshooting Guide")
    print("=" * 70)
    print()
    
    # Run validation
    result = validate_system(verbose=False)
    
    print("Troubleshooting Analysis:")
    print()
    
    # Check for multiprocessing issues
    if 'multiprocessing_basic' in result.details:
        mp_details = result.details['multiprocessing_basic']
        if 'error' in mp_details:
            print("❌ Multiprocessing Not Working:")
            print(f"   Error: {mp_details['error']}")
            print("   Solutions:")
            print("   • Ensure your Python installation supports multiprocessing")
            print("   • Check if you're in a restricted environment (some containers/notebooks)")
            print("   • Try using 'spawn' or 'forkserver' start method")
            print()
        else:
            print("✅ Multiprocessing: Working correctly")
            print()
    
    # Check for measurement issues
    if 'spawn_cost_measurement' in result.details:
        spawn_details = result.details['spawn_cost_measurement']
        if 'warning' in spawn_details:
            print("⚠️ Spawn Cost Measurement Warning:")
            print(f"   {spawn_details['warning']}")
            print("   This is usually normal and indicates system-specific characteristics.")
            print("   Fork-based systems often measure lower than estimates.")
            print()
    
    # Check for resource detection issues
    if 'system_resources' in result.details:
        sys_details = result.details['system_resources']
        if 'warning' in sys_details or 'error' in sys_details:
            print("⚠️ Resource Detection Issue:")
            if 'warning' in sys_details:
                print(f"   Warning: {sys_details['warning']}")
            if 'error' in sys_details:
                print(f"   Error: {sys_details['error']}")
            print("   Solutions:")
            print("   • Install psutil for better resource detection: pip install psutil")
            print("   • Check system resource availability")
            print()
        else:
            print("✅ Resource Detection: Working correctly")
            cores = sys_details.get('physical_cores', 'N/A')
            memory = sys_details.get('available_memory', 'N/A')
            print(f"   Detected: {cores} cores, {memory} memory")
            print()
    
    # Overall recommendation
    if result.overall_health in ["excellent", "good"]:
        print("Overall: ✅ No troubleshooting needed. System is healthy!")
    else:
        print("Overall: ⚠️ Review the issues above and apply suggested solutions.")
    
    print()


def example_7_comparing_systems():
    """
    Example 7: Comparing system characteristics.
    
    Use validation to understand differences between development and production.
    This helps explain why optimizer recommendations might differ across environments.
    """
    print("=" * 70)
    print("EXAMPLE 7: System Characteristics Summary")
    print("=" * 70)
    print()
    
    # Run validation
    result = validate_system(verbose=False)
    
    print("System Profile:")
    print()
    
    # Extract key characteristics
    if 'system_resources' in result.details:
        sys_details = result.details['system_resources']
        print(f"Platform Characteristics:")
        print(f"  • Physical Cores: {sys_details.get('physical_cores', 'unknown')}")
        print(f"  • Available Memory: {sys_details.get('available_memory', 'unknown')}")
        print(f"  • Multiprocessing Start Method: {sys_details.get('multiprocessing_start_method', 'unknown')}")
        print()
    
    if 'spawn_cost_measurement' in result.details:
        spawn_details = result.details['spawn_cost_measurement']
        print(f"Performance Characteristics:")
        print(f"  • Worker Spawn Cost: {spawn_details.get('measured_spawn_cost', 'unknown')}")
        print(f"  • Start Method: {spawn_details.get('start_method', 'unknown')}")
        print()
    
    if 'chunking_overhead_measurement' in result.details:
        chunk_details = result.details['chunking_overhead_measurement']
        print(f"Task Distribution Characteristics:")
        print(f"  • Chunking Overhead: {chunk_details.get('measured_overhead', 'unknown')}")
        print()
    
    print("Use this information to understand why optimizer recommendations")
    print("may differ between your development and production environments.")
    print()


if __name__ == "__main__":
    import sys
    
    # Check for non-interactive mode
    non_interactive = "--no-pause" in sys.argv or "-n" in sys.argv
    
    # Run all examples
    example_1_basic_validation()
    if not non_interactive:
        input("Press Enter to continue to Example 2...\n")
    else:
        print("\n")
    
    example_2_verbose_validation()
    if not non_interactive:
        input("Press Enter to continue to Example 3...\n")
    else:
        print("\n")
    
    example_3_programmatic_health_check()
    if not non_interactive:
        input("Press Enter to continue to Example 4...\n")
    else:
        print("\n")
    
    example_4_inspect_specific_measurements()
    if not non_interactive:
        input("Press Enter to continue to Example 5...\n")
    else:
        print("\n")
    
    example_5_ci_cd_integration()
    if not non_interactive:
        input("Press Enter to continue to Example 6...\n")
    else:
        print("\n")
    
    example_6_troubleshooting_guide()
    if not non_interactive:
        input("Press Enter to continue to Example 7...\n")
    else:
        print("\n")
    
    example_7_comparing_systems()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    
    if non_interactive:
        print("\nRun without --no-pause flag for interactive mode with pauses between examples.")
