"""
Visualization module for creating charts and plots of optimization results.

This module provides functions to generate visual representations of:
- Strategy comparison results (bar charts)
- Speedup curves (line plots)
- Overhead breakdowns (stacked bar charts)

The module gracefully handles missing matplotlib dependency.
"""

import warnings
from typing import List, Optional, Dict, Any
from pathlib import Path

# Try to import matplotlib, but don't fail if it's not available
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving files
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None


def check_matplotlib() -> bool:
    """
    Check if matplotlib is available.
    
    Returns:
        True if matplotlib is installed, False otherwise
    """
    return HAS_MATPLOTLIB


def require_matplotlib(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "Matplotlib is required for visualization features. "
                "Install it with: pip install matplotlib"
            )
        return func(*args, **kwargs)
    return wrapper


@require_matplotlib
def plot_comparison_times(
    config_names: List[str],
    execution_times: List[float],
    output_path: Optional[str] = None,
    title: str = "Strategy Comparison: Execution Times",
    figsize: tuple = (10, 6),
    show_values: bool = True
) -> Optional[str]:
    """
    Create a bar chart comparing execution times across strategies.
    
    Args:
        config_names: Names of configurations
        execution_times: Execution times for each config (seconds)
        output_path: Path to save the plot (if None, returns path to temp file)
        title: Chart title
        figsize: Figure size in inches (width, height)
        show_values: Whether to display values on bars
    
    Returns:
        Path to saved plot file, or None if saving failed
        
    Example:
        >>> names = ["Serial", "4 workers", "8 workers"]
        >>> times = [10.0, 3.2, 2.1]
        >>> plot_comparison_times(names, times, "comparison.png")
        'comparison.png'
    """
    if len(config_names) != len(execution_times):
        raise ValueError("config_names and execution_times must have same length")
    
    if not config_names:
        raise ValueError("At least one configuration is required")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create bar chart
    bars = ax.bar(range(len(config_names)), execution_times, color='steelblue', alpha=0.8)
    
    # Highlight the best (fastest) configuration
    best_idx = execution_times.index(min(execution_times))
    bars[best_idx].set_color('green')
    bars[best_idx].set_alpha(1.0)
    
    # Customize the plot
    ax.set_xlabel('Configuration', fontsize=12)
    ax.set_ylabel('Execution Time (seconds)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(config_names)))
    ax.set_xticklabels(config_names, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars if requested
    if show_values:
        for i, (bar, time) in enumerate(zip(bars, execution_times)):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{time:.2f}s',
                ha='center',
                va='bottom',
                fontsize=10
            )
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    if output_path is None:
        output_path = "amorsize_comparison_times.png"
    
    try:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    except Exception as e:
        warnings.warn(f"Failed to save plot to {output_path}: {e}")
        plt.close(fig)
        return None


@require_matplotlib
def plot_speedup_comparison(
    config_names: List[str],
    speedups: List[float],
    output_path: Optional[str] = None,
    title: str = "Strategy Comparison: Speedup vs Serial",
    figsize: tuple = (10, 6),
    show_values: bool = True,
    baseline_name: str = "Serial"
) -> Optional[str]:
    """
    Create a bar chart comparing speedups relative to baseline.
    
    Args:
        config_names: Names of configurations
        speedups: Speedup factors relative to serial (e.g., 2.5x means 2.5x faster)
        output_path: Path to save the plot (if None, returns path to temp file)
        title: Chart title
        figsize: Figure size in inches (width, height)
        show_values: Whether to display values on bars
        baseline_name: Name of the baseline configuration (usually "Serial")
    
    Returns:
        Path to saved plot file, or None if saving failed
        
    Example:
        >>> names = ["Serial", "4 workers", "8 workers"]
        >>> speedups = [1.0, 3.1, 4.8]
        >>> plot_speedup_comparison(names, speedups, "speedup.png")
        'speedup.png'
    """
    if len(config_names) != len(speedups):
        raise ValueError("config_names and speedups must have same length")
    
    if not config_names:
        raise ValueError("At least one configuration is required")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Color bars based on speedup value
    colors = []
    for speedup in speedups:
        if speedup < 1.0:
            colors.append('red')  # Slower than baseline
        elif speedup < 1.2:
            colors.append('orange')  # Marginal improvement
        elif speedup < 2.0:
            colors.append('yellow')  # Moderate improvement
        else:
            colors.append('green')  # Good improvement
    
    # Create bar chart
    bars = ax.bar(range(len(config_names)), speedups, color=colors, alpha=0.8)
    
    # Add horizontal line at 1.0x (baseline)
    ax.axhline(y=1.0, color='gray', linestyle='--', linewidth=2, label=f'{baseline_name} baseline')
    
    # Customize the plot
    ax.set_xlabel('Configuration', fontsize=12)
    ax.set_ylabel('Speedup (x)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(config_names)))
    ax.set_xticklabels(config_names, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.legend()
    
    # Add value labels on bars if requested
    if show_values:
        for i, (bar, speedup) in enumerate(zip(bars, speedups)):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{speedup:.2f}x',
                ha='center',
                va='bottom',
                fontsize=10
            )
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the figure
    if output_path is None:
        output_path = "amorsize_speedup_comparison.png"
    
    try:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    except Exception as e:
        warnings.warn(f"Failed to save plot to {output_path}: {e}")
        plt.close(fig)
        return None


@require_matplotlib
def plot_overhead_breakdown(
    n_workers_list: List[int],
    compute_times: List[float],
    spawn_overheads: List[float],
    ipc_overheads: List[float],
    chunking_overheads: List[float],
    output_path: Optional[str] = None,
    title: str = "Overhead Breakdown by Worker Count",
    figsize: tuple = (10, 6)
) -> Optional[str]:
    """
    Create a stacked bar chart showing overhead breakdown.
    
    Args:
        n_workers_list: List of worker counts
        compute_times: Pure computation times for each worker count
        spawn_overheads: Process spawn overhead times
        ipc_overheads: Inter-process communication overhead times
        chunking_overheads: Task chunking overhead times
        output_path: Path to save the plot (if None, returns path to temp file)
        title: Chart title
        figsize: Figure size in inches (width, height)
    
    Returns:
        Path to saved plot file, or None if saving failed
        
    Example:
        >>> workers = [1, 2, 4, 8]
        >>> compute = [10.0, 5.0, 2.5, 1.3]
        >>> spawn = [0.0, 0.03, 0.06, 0.12]
        >>> ipc = [0.0, 0.05, 0.10, 0.20]
        >>> chunk = [0.0, 0.02, 0.04, 0.08]
        >>> plot_overhead_breakdown(workers, compute, spawn, ipc, chunk, "overhead.png")
        'overhead.png'
    """
    if not (len(n_workers_list) == len(compute_times) == len(spawn_overheads) == 
            len(ipc_overheads) == len(chunking_overheads)):
        raise ValueError("All input lists must have the same length")
    
    if not n_workers_list:
        raise ValueError("At least one data point is required")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create stacked bar chart
    x_pos = range(len(n_workers_list))
    
    # Stack the bars (bottom to top: compute, spawn, ipc, chunking)
    bars1 = ax.bar(x_pos, compute_times, label='Computation', color='steelblue', alpha=0.8)
    bars2 = ax.bar(x_pos, spawn_overheads, bottom=compute_times, 
                   label='Spawn Overhead', color='orange', alpha=0.8)
    
    bottom2 = [c + s for c, s in zip(compute_times, spawn_overheads)]
    bars3 = ax.bar(x_pos, ipc_overheads, bottom=bottom2,
                   label='IPC Overhead', color='red', alpha=0.8)
    
    bottom3 = [b + i for b, i in zip(bottom2, ipc_overheads)]
    bars4 = ax.bar(x_pos, chunking_overheads, bottom=bottom3,
                   label='Chunking Overhead', color='purple', alpha=0.8)
    
    # Customize the plot
    ax.set_xlabel('Number of Workers', fontsize=12)
    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(n) for n in n_workers_list])
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    if output_path is None:
        output_path = "amorsize_overhead_breakdown.png"
    
    try:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    except Exception as e:
        warnings.warn(f"Failed to save plot to {output_path}: {e}")
        plt.close(fig)
        return None


@require_matplotlib
def plot_scaling_curve(
    n_workers_list: List[int],
    execution_times: List[float],
    theoretical_speedups: Optional[List[float]] = None,
    output_path: Optional[str] = None,
    title: str = "Scaling Performance",
    figsize: tuple = (10, 6)
) -> Optional[str]:
    """
    Create a line plot showing how execution time scales with worker count.
    
    Args:
        n_workers_list: List of worker counts
        execution_times: Execution times for each worker count
        theoretical_speedups: Optional theoretical speedup curve (Amdahl's Law)
        output_path: Path to save the plot (if None, returns path to temp file)
        title: Chart title
        figsize: Figure size in inches (width, height)
    
    Returns:
        Path to saved plot file, or None if saving failed
        
    Example:
        >>> workers = [1, 2, 4, 8, 16]
        >>> times = [10.0, 5.5, 3.2, 2.0, 1.5]
        >>> theoretical = [10.0, 5.0, 2.5, 1.25, 0.625]  # Ideal scaling
        >>> plot_scaling_curve(workers, times, theoretical, "scaling.png")
        'scaling.png'
    """
    if len(n_workers_list) != len(execution_times):
        raise ValueError("n_workers_list and execution_times must have same length")
    
    if not n_workers_list:
        raise ValueError("At least one data point is required")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot actual execution times
    ax.plot(n_workers_list, execution_times, marker='o', linewidth=2, 
            markersize=8, color='steelblue', label='Actual')
    
    # Plot theoretical speedup if provided
    if theoretical_speedups is not None:
        if len(theoretical_speedups) != len(n_workers_list):
            warnings.warn("theoretical_speedups length doesn't match n_workers_list, skipping")
        else:
            ax.plot(n_workers_list, theoretical_speedups, marker='s', linewidth=2,
                   markersize=6, color='green', linestyle='--', alpha=0.7,
                   label='Theoretical (Amdahl)')
    
    # Customize the plot
    ax.set_xlabel('Number of Workers', fontsize=12)
    ax.set_ylabel('Execution Time (seconds)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Use log scale if range is large
    if max(execution_times) / min(execution_times) > 10:
        ax.set_yscale('log')
        ax.set_ylabel('Execution Time (seconds, log scale)', fontsize=12)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the figure
    if output_path is None:
        output_path = "amorsize_scaling_curve.png"
    
    try:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    except Exception as e:
        warnings.warn(f"Failed to save plot to {output_path}: {e}")
        plt.close(fig)
        return None


def visualize_comparison_result(
    comparison_result,
    output_dir: Optional[str] = None,
    plots: Optional[List[str]] = None
) -> Dict[str, Optional[str]]:
    """
    Generate all visualization plots for a comparison result.
    
    Args:
        comparison_result: ComparisonResult object from compare_strategies()
        output_dir: Directory to save plots (if None, saves to current directory)
        plots: List of plot types to generate. Options: 'times', 'speedups', 'all'
               If None, generates all plots.
    
    Returns:
        Dictionary mapping plot type to file path (or None if generation failed)
        
    Example:
        >>> from amorsize.comparison import compare_strategies, ComparisonConfig
        >>> configs = [
        ...     ComparisonConfig("Serial", 1, 1, "serial"),
        ...     ComparisonConfig("4 workers", 4, 10, "process")
        ... ]
        >>> result = compare_strategies(my_func, data, configs)
        >>> paths = visualize_comparison_result(result, output_dir="./plots")
        >>> print(paths['times'])
        './plots/comparison_times.png'
    """
    if not HAS_MATPLOTLIB:
        warnings.warn(
            "Matplotlib is not available. Install it with: pip install matplotlib"
        )
        return {}
    
    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots
    
    # Prepare output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups
    
    # Generate plots
    result_paths = {}
    
    if 'times' in plot_types:
        if output_dir is not None:
            times_path = str(output_dir / "comparison_times.png")
        else:
            times_path = "comparison_times.png"
        
        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )
    
    if 'speedups' in plot_types:
        if output_dir is not None:
            speedups_path = str(output_dir / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"
        
        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )
    
    return result_paths
