"""
Historical Tracking Demo

This demo shows how to use the historical tracking feature to save,
query, and compare optimization results over time.
"""

import math
from amorsize import (
    compare_strategies, ComparisonConfig,
    save_result, load_result, list_results, compare_entries, clear_history
)


def demo_function(x):
    """Simple CPU-bound function for demonstration."""
    return math.factorial(x % 20)


def demo_1_save_results():
    """Demo 1: Saving comparison results to history."""
    print("=" * 70)
    print("DEMO 1: Saving Results to History")
    print("=" * 70)
    
    # Create test data
    data = list(range(100))
    
    # Define strategies to compare
    configs = [
        ComparisonConfig("Serial", 1),
        ComparisonConfig("4 workers", 4, 25),
        ComparisonConfig("8 workers", 8, 10)
    ]
    
    print("\nRunning comparison...")
    result = compare_strategies(demo_function, data, configs, verbose=False)
    
    print("\nComparison complete!")
    print(result)
    
    # Save to history
    print("\nSaving to history...")
    entry_id = save_result(
        result,
        name="demo-baseline-v1.0",
        function_name="demo_function",
        data_size=len(data),
        metadata={
            "version": "1.0",
            "environment": "demo",
            "notes": "Baseline measurement for demo"
        }
    )
    
    print(f"✓ Saved as 'demo-baseline-v1.0' (ID: {entry_id})")
    
    return entry_id


def demo_2_list_results():
    """Demo 2: Listing historical results."""
    print("\n" + "=" * 70)
    print("DEMO 2: Listing Historical Results")
    print("=" * 70)
    
    entries = list_results()
    
    if not entries:
        print("\nNo history entries found.")
        return
    
    print(f"\nFound {len(entries)} history entries:")
    print()
    print(f"{'ID':<14} {'Name':<30} {'Best Strategy':<25}")
    print("-" * 70)
    
    for entry in entries[:10]:  # Show first 10
        best_strategy = entry.result.best_config.name
        print(f"{entry.id:<14} {entry.name:<30} {best_strategy:<25}")
    
    if len(entries) > 10:
        print(f"\n... and {len(entries) - 10} more")


def demo_3_show_details(entry_id):
    """Demo 3: Showing detailed information about a result."""
    print("\n" + "=" * 70)
    print("DEMO 3: Showing Result Details")
    print("=" * 70)
    
    entry = load_result(entry_id)
    
    if entry is None:
        print(f"\nError: Entry '{entry_id}' not found")
        return
    
    print(f"\nEntry ID:   {entry.id}")
    print(f"Name:       {entry.name}")
    print(f"Timestamp:  {entry.timestamp}")
    print(f"Function:   {entry.function_name}")
    print(f"Data size:  {entry.data_size}")
    
    print("\nSystem Information:")
    print(f"  Platform:       {entry.system_info.get('platform', 'N/A')}")
    print(f"  Physical cores: {entry.system_info.get('physical_cores', 'N/A')}")
    print(f"  Memory:         {entry.system_info.get('available_memory_gb', 0):.2f} GB")
    
    print("\nMetadata:")
    for key, value in entry.metadata.items():
        print(f"  {key}: {value}")
    
    print("\nResults:")
    print(f"  Best strategy:  {entry.result.best_config.name}")
    print(f"  Best time:      {entry.result.best_time:.4f}s")
    print(f"  Best speedup:   {entry.result.speedups[entry.result.best_config_index]:.2f}x")
    
    print("\nAll Strategies:")
    print(f"{'Name':<25} {'Workers':<10} {'Chunk':<10} {'Time (s)':<12} {'Speedup':<10}")
    print("-" * 70)
    for i, config in enumerate(entry.result.configs):
        print(f"{config.name:<25} {config.n_jobs:<10} {config.chunksize:<10} "
              f"{entry.result.execution_times[i]:<12.4f} {entry.result.speedups[i]:<10.2f}x")


def demo_4_compare_results(entry_id1):
    """Demo 4: Creating and comparing a second result."""
    print("\n" + "=" * 70)
    print("DEMO 4: Comparing Two Results")
    print("=" * 70)
    
    # Create a slightly different result to compare
    data = list(range(100))
    configs = [
        ComparisonConfig("Serial", 1),
        ComparisonConfig("6 workers", 6, 15)
    ]
    
    print("\nRunning second comparison...")
    result2 = compare_strategies(demo_function, data, configs, verbose=False)
    
    # Save second result
    entry_id2 = save_result(
        result2,
        name="demo-optimized-v1.1",
        function_name="demo_function",
        data_size=len(data),
        metadata={
            "version": "1.1",
            "environment": "demo",
            "notes": "Optimized configuration"
        }
    )
    
    print(f"✓ Saved as 'demo-optimized-v1.1' (ID: {entry_id2})")
    
    # Compare the two results
    print("\nComparing results...")
    comparison = compare_entries(entry_id1, entry_id2)
    
    if comparison is None:
        print("Error: Could not compare entries")
        return
    
    e1 = comparison["entry1"]
    e2 = comparison["entry2"]
    comp = comparison["comparison"]
    
    print(f"\nEntry 1: {e1['name']}")
    print(f"  Best strategy: {e1['best_strategy']}")
    print(f"  Speedup:       {e1['speedup']:.2f}x")
    print(f"  Time:          {e1['execution_time']:.4f}s")
    
    print(f"\nEntry 2: {e2['name']}")
    print(f"  Best strategy: {e2['best_strategy']}")
    print(f"  Speedup:       {e2['speedup']:.2f}x")
    print(f"  Time:          {e2['execution_time']:.4f}s")
    
    print("\nComparison:")
    print(f"  Time delta:    {comp['time_delta_seconds']:+.4f}s ({comp['time_delta_percent']:+.1f}%)")
    print(f"  Speedup delta: {comp['speedup_delta']:+.2f}x")
    print(f"  Same system:   {'Yes' if comp['same_system'] else 'No'}")
    
    if comp['is_regression']:
        print(f"  ⚠ REGRESSION DETECTED: Entry 2 is slower")
    else:
        print(f"  ✓ Performance improved or stable")


def demo_5_cleanup():
    """Demo 5: Cleaning up demo entries."""
    print("\n" + "=" * 70)
    print("DEMO 5: Cleanup")
    print("=" * 70)
    
    # List demo entries
    demo_entries = list_results(name_filter="demo-")
    
    print(f"\nFound {len(demo_entries)} demo entries")
    
    if demo_entries:
        print("\nDeleting demo entries...")
        for entry in demo_entries:
            from amorsize import delete_result
            delete_result(entry.id)
            print(f"  ✓ Deleted {entry.name} ({entry.id})")
    
    print("\nCleanup complete!")


def main():
    """Run all demos."""
    print("\n")
    print("*" * 70)
    print(" Historical Tracking Demo".center(70))
    print("*" * 70)
    
    # Demo 1: Save results
    entry_id = demo_1_save_results()
    
    # Demo 2: List results
    demo_2_list_results()
    
    # Demo 3: Show details
    demo_3_show_details(entry_id)
    
    # Demo 4: Compare results
    demo_4_compare_results(entry_id)
    
    # Demo 5: Cleanup
    demo_5_cleanup()
    
    print("\n" + "*" * 70)
    print(" Demo Complete!".center(70))
    print("*" * 70)
    print("\nFor more information, see examples/README_history.md")
    print()


if __name__ == "__main__":
    main()
