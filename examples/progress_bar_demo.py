"""
Demo: Progress Bar for Long-Running Optimizations

This example demonstrates the new --progress flag for the CLI,
which displays a progress bar during optimization of large datasets.

This is particularly useful for:
1. Large datasets (10,000+ items) where optimization takes 5-30 seconds
2. Understanding optimization progress in real-time
3. Confirming the system hasn't hung during long operations

Run this demo:
    python examples/progress_bar_demo.py
"""

import math
import subprocess
import sys
import time


def slow_function(x):
    """
    A deliberately slow function to demonstrate progress reporting.
    
    Simulates a CPU-intensive operation that takes ~5ms per item.
    """
    result = 0
    for i in range(5000):
        result += math.sin(x) * math.cos(x)
    return result


def fast_function(x):
    """A fast function for comparison."""
    return x ** 2


def demo_1_basic_progress():
    """Demo 1: Basic progress bar with small dataset."""
    print("=" * 70)
    print("DEMO 1: Basic Progress Bar (Small Dataset)")
    print("=" * 70)
    print("\nOptimizing with 1,000 items (should complete quickly)")
    print("Command: python -m amorsize optimize math.factorial --data-range 1000 --progress")
    print("\nPress Enter to run...")
    input()
    
    subprocess.run([
        sys.executable, "-m", "amorsize", "optimize",
        "math.factorial",
        "--data-range", "1000",
        "--progress"
    ])


def demo_2_large_dataset():
    """Demo 2: Progress bar with large dataset."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: Progress Bar with Large Dataset")
    print("=" * 70)
    print("\nOptimizing with 10,000 items (takes longer, progress helps)")
    print("Command: python -m amorsize optimize math.factorial --data-range 10000 --progress")
    print("\nPress Enter to run...")
    input()
    
    subprocess.run([
        sys.executable, "-m", "amorsize", "optimize",
        "math.factorial",
        "--data-range", "10000",
        "--progress"
    ])


def demo_3_progress_with_verbose():
    """Demo 3: Progress bar with verbose output."""
    print("\n\n" + "=" * 70)
    print("DEMO 3: Progress Bar with Verbose Mode")
    print("=" * 70)
    print("\nShows detailed phase names in progress bar")
    print("Command: python -m amorsize optimize math.sqrt --data-range 5000 --progress --verbose")
    print("\nPress Enter to run...")
    input()
    
    subprocess.run([
        sys.executable, "-m", "amorsize", "optimize",
        "math.sqrt",
        "--data-range", "5000",
        "--progress",
        "--verbose"
    ])


def demo_4_comparison():
    """Demo 4: Compare with and without progress bar."""
    print("\n\n" + "=" * 70)
    print("DEMO 4: Comparison - Without Progress vs With Progress")
    print("=" * 70)
    
    print("\n--- Without progress bar (standard output) ---")
    print("Command: python -m amorsize optimize math.factorial --data-range 5000")
    print("\nPress Enter to run...")
    input()
    
    subprocess.run([
        sys.executable, "-m", "amorsize", "optimize",
        "math.factorial",
        "--data-range", "5000"
    ])
    
    print("\n--- With progress bar (visual feedback) ---")
    print("Command: python -m amorsize optimize math.factorial --data-range 5000 --progress")
    print("\nPress Enter to run...")
    input()
    
    subprocess.run([
        sys.executable, "-m", "amorsize", "optimize",
        "math.factorial",
        "--data-range", "5000",
        "--progress"
    ])


def demo_5_execute_with_progress():
    """Demo 5: Progress bar with execute command."""
    print("\n\n" + "=" * 70)
    print("DEMO 5: Progress Bar with Execute Command")
    print("=" * 70)
    print("\nProgress bar works with 'execute' command too")
    print("Command: python -m amorsize execute math.sqrt --data-range 3000 --progress")
    print("\nPress Enter to run...")
    input()
    
    subprocess.run([
        sys.executable, "-m", "amorsize", "execute",
        "math.sqrt",
        "--data-range", "3000",
        "--progress"
    ])


def demo_6_quiet_mode():
    """Demo 6: Progress bar with quiet mode."""
    print("\n\n" + "=" * 70)
    print("DEMO 6: Progress Bar with Quiet Mode")
    print("=" * 70)
    print("\nProgress bar provides feedback even in quiet mode")
    print("Command: python -m amorsize optimize math.factorial --data-range 5000 --progress --quiet")
    print("\nPress Enter to run...")
    input()
    
    subprocess.run([
        sys.executable, "-m", "amorsize", "optimize",
        "math.factorial",
        "--data-range", "5000",
        "--progress",
        "--quiet"
    ])


def main():
    """Run all progress bar demos."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                  PROGRESS BAR DEMONSTRATION                        ║
║                                                                    ║
║  New Feature: Visual progress feedback for long optimizations     ║
║                                                                    ║
║  Use --progress flag to see optimization progress in real-time    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\nThis demo will show:")
    print("  1. Basic progress bar with small dataset")
    print("  2. Progress bar with large dataset (most useful)")
    print("  3. Progress bar with verbose phase descriptions")
    print("  4. Comparison: with vs without progress bar")
    print("  5. Progress bar with execute command")
    print("  6. Progress bar with quiet mode")
    
    print("\nWould you like to run all demos? (y/n): ", end="")
    response = input().strip().lower()
    
    if response != 'y':
        print("\nSkipping demos. You can run individual demos by uncommenting them in the script.")
        return
    
    try:
        demo_1_basic_progress()
        demo_2_large_dataset()
        demo_3_progress_with_verbose()
        demo_4_comparison()
        demo_5_execute_with_progress()
        demo_6_quiet_mode()
        
        print("\n\n" + "=" * 70)
        print("ALL DEMOS COMPLETE!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  • Use --progress for real-time feedback during optimization")
        print("  • Especially useful for large datasets (5,000+ items)")
        print("  • Combine with --verbose for detailed phase names")
        print("  • Works with both 'optimize' and 'execute' commands")
        print("  • Progress bar automatically disabled for non-TTY output")
        print("\nUsage:")
        print("  python -m amorsize optimize my_func --data-range 10000 --progress")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
