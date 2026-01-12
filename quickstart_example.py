#!/usr/bin/env python3
"""
Amorsize Quick Start Example - Get started in 30 seconds!

This script demonstrates the core value proposition of Amorsize:
automatically finding the optimal parallelization parameters for your workload.

Run this file directly to see Amorsize in action:
    python quickstart_example.py
"""

import time
from amorsize import optimize, execute


def cpu_intensive_task(n):
    """
    Simulate a CPU-intensive task (e.g., data processing, computation).
    
    In real applications, this could be:
    - Image processing
    - Data transformation
    - Feature extraction
    - Mathematical computations
    """
    # Simulate more substantial work
    result = 0
    for i in range(n * 1000):  # More iterations for realistic timing
        result += i ** 2
    return result


def main():
    print("=" * 70)
    print("  Amorsize Quick Start - Automatic Parallelization Optimization")
    print("=" * 70)
    print()
    
    # Define our workload
    data = range(100, 200)  # 100 items to process
    print(f"📊 Workload: Processing {len(list(data))} items with cpu_intensive_task()")
    print()
    
    # Re-create data as range objects can't be reused after consumption
    data = range(100, 200)
    
    # ========================================================================
    # Option 1: Get Recommendations (analyze without executing)
    # ========================================================================
    print("🔍 Option 1: Analyze and get recommendations")
    print("-" * 70)
    
    result = optimize(cpu_intensive_task, data)
    
    print(f"✅ Recommended configuration:")
    print(f"   • Workers (n_jobs):  {result.n_jobs}")
    print(f"   • Chunk size:        {result.chunksize}")
    print(f"   • Expected speedup:  {result.estimated_speedup:.2f}x")
    print(f"   • Decision:          {result.reason}")
    print()
    
    # Check if parallelization is beneficial (n_jobs > 1)
    if result.n_jobs == 1:
        print("⚠️  Parallelization not recommended for this workload")
        print(f"   Reason: {result.reason}")
        print("\nTip: Try a larger dataset or slower function for parallel benefits")
        return
    
    # ========================================================================
    # Option 2: Optimize and Execute (one-liner!)
    # ========================================================================
    print("🚀 Option 2: Optimize AND execute in one call")
    print("-" * 70)
    
    print(f"⏱️  Executing with {result.n_jobs} workers, chunksize={result.chunksize}...")
    start_time = time.time()
    
    # Execute with automatically optimized parameters
    results = execute(
        func=cpu_intensive_task,
        data=data,
        verbose=False  # Set to True to see progress
    )
    
    execution_time = time.time() - start_time
    
    print(f"✅ Completed in {execution_time:.3f}s")
    print(f"   • Processed: {len(results)} items")
    print(f"   • Configuration: {result.n_jobs} workers, chunksize {result.chunksize}")
    print()
    
    # ========================================================================
    # Understanding the Output
    # ========================================================================
    print("📖 What just happened?")
    print("-" * 70)
    print("1. Amorsize analyzed your function + data with a quick dry-run")
    if result.profile:
        print("2. It measured:")
        print(f"   • Execution time per item: ~{result.profile.avg_execution_time*1000:.2f}ms")
        print(f"   • Pickle overhead: ~{result.profile.avg_pickle_time*1000:.3f}ms")
        print(f"   • Memory usage: {result.profile.return_size_bytes} bytes per result")
        print("3. It calculated optimal parameters based on your system:")
        print(f"   • Physical cores: {result.profile.physical_cores}")
        print(f"   • Available memory: {result.profile.available_memory / (1024**3):.1f}GB")
        print(f"   • Start method: {result.profile.multiprocessing_start_method}")
    else:
        print("2. It calculated optimal parameters based on your system")
    print("3. It recommended the config that maximizes speedup!")
    print()
    
    # ========================================================================
    # Next Steps
    # ========================================================================
    print("🎯 Next Steps:")
    print("-" * 70)
    print("• Use optimize() to analyze your own functions")
    print("• Use execute() for one-line optimization + execution")
    print("• Add verbose=True to see detailed analysis")
    print("• Check out docs/GETTING_STARTED.md for more examples")
    print("• Try python -m amorsize --help for CLI usage")
    print()
    
    print("=" * 70)
    print("  ✨ Successfully demonstrated Amorsize! ✨")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf you're seeing import errors, make sure Amorsize is installed:")
        print("  pip install -e .")
        raise
