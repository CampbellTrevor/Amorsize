#!/usr/bin/env python3
"""
Demo script for CLI enhancements in Iteration 137.

This script demonstrates the new CLI flags:
- --explain: User-friendly explanation of optimization decisions
- --tips: Actionable optimization tips and recommendations
- --show-overhead: Detailed overhead breakdown
- --quiet: Minimal output mode
- --color / --no-color: Terminal color control

Run this script to see examples of all new features.
"""

import subprocess
import time


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def run_command(description, command):
    """Run a command and display its output."""
    print(f"{description}")
    print(f"Command: {command}")
    print()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
    time.sleep(0.5)


def main():
    print_section("Amorsize CLI Enhancements Demo - Iteration 137")
    
    # Demo 1: Quiet mode
    print_section("1. Quiet Mode (--quiet)")
    print("Use --quiet for minimal output - just the essentials.")
    run_command(
        "Example:",
        "python3 -m amorsize optimize math.factorial --data-range 100 --quiet"
    )
    
    # Demo 2: Normal mode
    print_section("2. Normal Mode (default)")
    print("Standard output with recommendations and warnings.")
    run_command(
        "Example:",
        "python3 -m amorsize optimize math.factorial --data-range 100 --no-color"
    )
    
    # Demo 3: Tips flag
    print_section("3. Optimization Tips (--tips)")
    print("Get actionable optimization tips based on the analysis.")
    run_command(
        "Example:",
        "python3 -m amorsize optimize math.factorial --data-range 500 --tips --no-color"
    )
    
    # Demo 4: Explain flag  
    print_section("4. User-Friendly Explanation (--explain)")
    print("Get a detailed, user-friendly explanation of optimization decisions.")
    run_command(
        "Example:",
        "python3 -m amorsize optimize math.sqrt --data-range 5000 --explain --no-color"
    )
    
    # Demo 5: Show overhead flag
    print_section("5. Overhead Breakdown (--show-overhead)")
    print("See detailed breakdown of overhead components.")
    run_command(
        "Example:",
        "python3 -m amorsize optimize math.sqrt --data-range 5000 --show-overhead --no-color"
    )
    
    # Demo 6: Combined flags
    print_section("6. Combined Flags (--explain --tips --show-overhead)")
    print("Combine multiple flags for comprehensive analysis.")
    run_command(
        "Example:",
        "python3 -m amorsize optimize math.sqrt --data-range 5000 --explain --tips --show-overhead --no-color"
    )
    
    # Demo 7: Color support
    print_section("7. Color Support (--color / --no-color)")
    print("Colors are automatically enabled on TTYs, but can be forced:")
    print("  --color: Force colored output")
    print("  --no-color: Disable colored output")
    print("\nNote: This demo uses --no-color for consistent output.")
    print("Try running without --no-color to see colored output!")
    
    print_section("Demo Complete!")
    print("Key takeaways:")
    print("  • --quiet: Minimal output for scripts")
    print("  • --explain: User-friendly explanations")
    print("  • --tips: Actionable optimization tips")
    print("  • --show-overhead: Detailed overhead breakdown")
    print("  • --color/--no-color: Control colored output")
    print("\nFor more information, run:")
    print("  python3 -m amorsize optimize --help")
    print()


if __name__ == "__main__":
    main()
