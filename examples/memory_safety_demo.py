#!/usr/bin/env python
"""
Demonstration of Large Return Object Detection and Memory Safety

This script shows how Amorsize now detects and warns about large return
objects that could cause Out-Of-Memory (OOM) kills.
"""

from amorsize import optimize
from amorsize.system_info import get_available_memory


def create_large_image(x):
    """Simulate processing that returns large objects (e.g., images)."""
    # Return a 10MB string (simulating a large image)
    return "x" * (10 * 1024 * 1024)


def create_small_result(x):
    """Simulate processing that returns small objects."""
    return x * 2


def main():
    print("=" * 70)
    print("Amorsize: Large Return Object Detection Demo")
    print("=" * 70)
    
    # Show available memory
    available_memory = get_available_memory()
    print(f"\nSystem available memory: {available_memory / (1024**3):.2f} GB")
    print(f"Safety threshold (50%): {available_memory * 0.5 / (1024**3):.2f} GB")
    
    # Example 1: Small return objects (no warning)
    print("\n" + "-" * 70)
    print("Example 1: Small return objects (safe)")
    print("-" * 70)
    
    data = range(1000)
    result = optimize(create_small_result, data, verbose=True)
    
    print(f"\nResult: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    print(f"Warnings: {result.warnings if result.warnings else 'None'}")
    
    # Example 2: Large return objects (triggers warning)
    print("\n" + "-" * 70)
    print("Example 2: Large return objects (memory safety warning)")
    print("-" * 70)
    
    # Calculate how many items needed to trigger warning
    memory_threshold = available_memory * 0.5
    large_object_size = 10 * 1024 * 1024  # 10MB
    items_for_warning = int(memory_threshold / large_object_size) + 50
    
    print(f"Processing {items_for_warning} items, each returning ~10MB...")
    print(f"Expected memory accumulation: {items_for_warning * large_object_size / (1024**3):.2f} GB")
    
    data_large = range(items_for_warning)
    result_large = optimize(create_large_image, data_large, verbose=True)
    
    print(f"\nResult: n_jobs={result_large.n_jobs}, chunksize={result_large.chunksize}")
    print(f"\nWarnings detected:")
    for i, warning in enumerate(result_large.warnings, 1):
        print(f"  {i}. {warning}")
    
    # Key takeaway
    print("\n" + "=" * 70)
    print("KEY TAKEAWAY")
    print("=" * 70)
    print("""
Amorsize now proactively warns you when parallelization would accumulate
too much memory, potentially causing OOM kills. The warning includes:

1. Estimated memory consumption
2. Available memory on your system
3. Actionable advice (use imap_unordered() or batch processing)

This prevents silent catastrophic failures in production!
    """)


if __name__ == "__main__":
    main()
