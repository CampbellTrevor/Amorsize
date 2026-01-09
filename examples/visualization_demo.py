"""
Visualization Demo - Amorsize

This example demonstrates how to use Amorsize's visualization features
to generate charts and plots from comparison results.

Visualization features include:
- Bar charts of execution times
- Speedup comparison charts
- Overhead breakdown plots
- Scaling curve analysis
"""

import os
import tempfile

# Import comparison and visualization functions
from amorsize import (
    compare_strategies,
    compare_with_optimizer,
    visualize_comparison_result,
    check_matplotlib,
    ComparisonConfig
)


def expensive_computation(x):
    """
    A moderately expensive computation for demonstration.
    
    This function performs enough work to benefit from parallelization
    without being so slow that the demo takes too long to run.
    """
    result = 0
    for i in range(1000):
        result += x ** 2 + i
    return result


def demo_basic_visualization():
    """
    Demo 1: Basic visualization of comparison results.
    
    This shows how to:
    1. Compare multiple parallelization strategies
    2. Generate visualizations automatically
    """
    print("=" * 70)
    print("Demo 1: Basic Visualization")
    print("=" * 70)
    
    # Check if matplotlib is available
    if not check_matplotlib():
        print("⚠️  Matplotlib is not installed. Install it with:")
        print("   pip install matplotlib")
        print("\nContinuing with text-only output...")
        print()
    
    # Create test data
    data = range(500)
    
    # Define strategies to compare
    configs = [
        ComparisonConfig("Serial", n_jobs=1),
        ComparisonConfig("2 workers", n_jobs=2, chunksize=50),
        ComparisonConfig("4 workers", n_jobs=4, chunksize=25),
        ComparisonConfig("8 workers", n_jobs=8, chunksize=15)
    ]
    
    print("Comparing 4 parallelization strategies...")
    print()
    
    # Run comparison
    result = compare_strategies(
        expensive_computation,
        data,
        configs,
        verbose=False
    )
    
    # Display results
    print(result)
    print()
    
    # Generate visualizations
    if check_matplotlib():
        output_dir = tempfile.mkdtemp(prefix="amorsize_demo_")
        print(f"Generating visualizations in: {output_dir}")
        
        plot_paths = visualize_comparison_result(
            result,
            output_dir=output_dir
        )
        
        if plot_paths:
            print("\n✓ Visualizations created:")
            for plot_type, path in plot_paths.items():
                if path and os.path.exists(path):
                    size_kb = os.path.getsize(path) / 1024
                    print(f"  - {plot_type}: {path} ({size_kb:.1f} KB)")
        
        print(f"\n💡 Open the files in {output_dir} to view the charts!")
    
    print()


def demo_visualization_with_optimizer():
    """
    Demo 2: Compare custom strategies against optimizer recommendation.
    
    This shows how to:
    1. Include the optimizer's recommendation
    2. Compare it against manual configurations
    3. Visualize the results
    """
    print("=" * 70)
    print("Demo 2: Visualization with Optimizer")
    print("=" * 70)
    
    if not check_matplotlib():
        print("⚠️  Matplotlib is not installed. Skipping visualization demo.")
        return
    
    # Create test data
    data = range(1000)
    
    # Define manual strategies
    manual_configs = [
        ComparisonConfig("Conservative", n_jobs=2, chunksize=100),
        ComparisonConfig("Aggressive", n_jobs=8, chunksize=10)
    ]
    
    print("Comparing optimizer vs manual configurations...")
    print()
    
    # Run comparison with optimizer
    # compare_with_optimizer returns (ComparisonResult, OptimizationResult)
    comparison_result, opt_result = compare_with_optimizer(
        expensive_computation,
        data,
        additional_configs=manual_configs,
        verbose=False
    )
    
    # Display results
    print(comparison_result)
    print()
    
    # Generate visualizations
    output_dir = tempfile.mkdtemp(prefix="amorsize_optimizer_")
    print(f"Generating visualizations in: {output_dir}")
    
    plot_paths = visualize_comparison_result(
        comparison_result,
        output_dir=output_dir
    )
    
    if plot_paths:
        print("\n✓ Visualizations created:")
        for plot_type, path in plot_paths.items():
            if path and os.path.exists(path):
                print(f"  - {plot_type}: {path}")
    
    print(f"\n💡 Open the files in {output_dir} to view the charts!")
    print()


def demo_custom_plots():
    """
    Demo 3: Create custom visualization plots.
    
    This shows how to:
    1. Use individual plotting functions
    2. Customize plot appearance
    3. Save to specific locations
    """
    print("=" * 70)
    print("Demo 3: Custom Plot Generation")
    print("=" * 70)
    
    if not check_matplotlib():
        print("⚠️  Matplotlib is not installed. Skipping visualization demo.")
        return
    
    from amorsize import plot_comparison_times, plot_speedup_comparison
    
    # Create example data
    config_names = ["Serial", "2 workers", "4 workers", "8 workers", "16 workers"]
    execution_times = [10.0, 5.5, 3.2, 2.1, 1.8]
    speedups = [1.0, 1.82, 3.13, 4.76, 5.56]
    
    output_dir = tempfile.mkdtemp(prefix="amorsize_custom_")
    print(f"Creating custom plots in: {output_dir}")
    print()
    
    # Create execution times plot
    times_path = os.path.join(output_dir, "custom_times.png")
    plot_comparison_times(
        config_names,
        execution_times,
        output_path=times_path,
        title="Custom Title: Execution Time Comparison",
        figsize=(12, 7),
        show_values=True
    )
    print(f"✓ Created: {times_path}")
    
    # Create speedup plot
    speedup_path = os.path.join(output_dir, "custom_speedup.png")
    plot_speedup_comparison(
        config_names,
        speedups,
        output_path=speedup_path,
        title="Custom Title: Speedup Analysis",
        figsize=(12, 7),
        show_values=True
    )
    print(f"✓ Created: {speedup_path}")
    
    print(f"\n💡 Open the files in {output_dir} to view the charts!")
    print()


def demo_cli_visualization():
    """
    Demo 4: CLI visualization examples.
    
    This shows the command-line interface for generating visualizations.
    """
    print("=" * 70)
    print("Demo 4: CLI Visualization Commands")
    print("=" * 70)
    print()
    print("You can generate visualizations from the command line:")
    print()
    print("# Basic comparison with visualization")
    print("python -m amorsize compare math.factorial \\")
    print("    --data-range 100 \\")
    print("    --configs '2,20' '4,10' '8,5' \\")
    print("    --visualize ./output")
    print()
    print("# Compare with optimizer recommendation")
    print("python -m amorsize compare mymodule.process_data \\")
    print("    --data-range 500 \\")
    print("    --include-optimizer \\")
    print("    --configs 'Manual:4,25' \\")
    print("    --visualize ./comparison_plots")
    print()
    print("# Verbose output with visualization")
    print("python -m amorsize compare math.sqrt \\")
    print("    --data-range 1000 \\")
    print("    --configs '2,50' '4,25' \\")
    print("    --verbose \\")
    print("    --visualize ./plots")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║         Amorsize Visualization Features Demo                     ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Run all demos
    demo_basic_visualization()
    print()
    
    demo_visualization_with_optimizer()
    print()
    
    demo_custom_plots()
    print()
    
    demo_cli_visualization()
    print()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key Features:")
    print("  ✓ Automatic chart generation from comparison results")
    print("  ✓ Bar charts for execution time comparison")
    print("  ✓ Speedup visualization with color coding")
    print("  ✓ CLI integration with --visualize flag")
    print("  ✓ Graceful fallback when matplotlib is not installed")
    print()
    print("To use visualization features, install matplotlib:")
    print("  pip install matplotlib")
    print()
