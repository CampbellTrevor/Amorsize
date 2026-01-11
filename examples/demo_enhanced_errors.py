"""
Demonstration of Enhanced Error Messages in Amorsize

This script showcases the improved error messaging and actionable guidance
that helps users quickly understand and fix common optimization issues.
"""

from amorsize import optimize
import sys
from io import StringIO


def demo_section(title):
    """Print a section header."""
    print("\n" + "="*80)
    print(f"DEMO: {title}")
    print("="*80 + "\n")


def demo_lambda_error():
    """Demonstrate enhanced error message for lambda function."""
    demo_section("Lambda Function (Not Picklable)")
    
    # This will fail because lambda functions cannot be pickled
    func = lambda x: x ** 2
    data = range(100)
    
    result = optimize(func, data, verbose=True)
    
    print("\nResult:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  reason: {result.reason}")
    print("\nEnhanced Error Guidance:")
    if result.warnings:
        print(result.warnings[0][:500] + "...")


def demo_very_fast_function():
    """Demonstrate enhanced error message for function too fast to benefit."""
    demo_section("Very Fast Function (No Parallelization Benefit)")
    
    def tiny_func(x):
        """Extremely fast function - overhead exceeds benefit."""
        return x + 1
    
    data = range(10)
    
    result = optimize(tiny_func, data, verbose=True)
    
    print("\nResult:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  reason: {result.reason}")


def demo_sampling_error():
    """Demonstrate enhanced error message for function that raises errors."""
    demo_section("Function That Raises Errors During Sampling")
    
    def broken_func(x):
        """This function raises an error."""
        raise ValueError(f"Cannot process {x}")
    
    data = range(10)
    
    result = optimize(broken_func, data, verbose=True)
    
    print("\nResult:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  reason: {result.reason}")


def demo_successful_optimization():
    """Demonstrate successful optimization with good function."""
    demo_section("Successful Optimization (Good Function & Data)")
    
    def good_func(x):
        """Sufficiently expensive function that benefits from parallelization."""
        result = 0
        for i in range(1000):
            result += x ** 2
        return result
    
    data = range(100)
    
    result = optimize(good_func, data, verbose=True)
    
    print("\nResult:")
    print(f"  n_jobs: {result.n_jobs}")
    print(f"  chunksize: {result.chunksize}")
    print(f"  estimated_speedup: {result.estimated_speedup:.2f}x")
    print(f"  reason: {result.reason}")


def main():
    """Run all demonstrations."""
    print("\n" + "#"*80)
    print("# AMORSIZE: ENHANCED ERROR MESSAGES DEMONSTRATION")
    print("# Iteration 133: UX & Robustness Enhancement")
    print("#"*80)
    
    print("\nThis demonstration shows how Amorsize provides clear, actionable")
    print("guidance when optimization fails or encounters issues.")
    print("\nPress Enter to continue through each demo...")
    
    # Demo 1: Lambda error
    input("\nPress Enter for Demo 1...")
    demo_lambda_error()
    
    # Demo 2: Very fast function
    input("\nPress Enter for Demo 2...")
    demo_very_fast_function()
    
    # Demo 3: Sampling error
    input("\nPress Enter for Demo 3...")
    demo_sampling_error()
    
    # Demo 4: Successful optimization
    input("\nPress Enter for Demo 4...")
    demo_successful_optimization()
    
    print("\n" + "#"*80)
    print("# DEMONSTRATION COMPLETE")
    print("#"*80)
    print("\nKey Improvements:")
    print("  ✓ Clear explanation of what went wrong")
    print("  ✓ Common causes listed with examples")
    print("  ✓ Concrete solutions with code snippets")
    print("  ✓ Before/after examples (❌ vs ✅)")
    print("  ✓ Actionable guidance, not just error messages")
    print("\nThese enhancements help users quickly:")
    print("  1. Understand why optimization failed")
    print("  2. Learn common pitfalls to avoid")
    print("  3. Fix issues with copy-paste ready solutions")
    print("  4. Make better architectural decisions")


if __name__ == '__main__':
    # Run in non-interactive mode if requested
    if '--non-interactive' in sys.argv:
        print("Running in non-interactive mode...")
        # Just run demo 4 (successful case) to verify everything works
        demo_successful_optimization()
    else:
        main()
