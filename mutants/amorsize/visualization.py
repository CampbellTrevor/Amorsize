"""
Visualization module for creating charts and plots of optimization results.

This module provides functions to generate visual representations of:
- Strategy comparison results (bar charts)
- Speedup curves (line plots)
- Overhead breakdowns (stacked bar charts)

The module gracefully handles missing matplotlib dependency.
"""

import warnings
from pathlib import Path
from typing import Dict, List, Optional

# Try to import matplotlib, but don't fail if it's not available
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving files
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


def check_matplotlib() -> bool:
    """
    Check if matplotlib is available.

    Returns:
        True if matplotlib is installed, False otherwise
    """
    return HAS_MATPLOTLIB


def x_require_matplotlib__mutmut_orig(func):
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


def x_require_matplotlib__mutmut_1(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if HAS_MATPLOTLIB:
            raise ImportError(
                "Matplotlib is required for visualization features. "
                "Install it with: pip install matplotlib"
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_2(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                None
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_3(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "XXMatplotlib is required for visualization features. XX"
                "Install it with: pip install matplotlib"
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_4(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "matplotlib is required for visualization features. "
                "Install it with: pip install matplotlib"
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_5(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "MATPLOTLIB IS REQUIRED FOR VISUALIZATION FEATURES. "
                "Install it with: pip install matplotlib"
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_6(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "Matplotlib is required for visualization features. "
                "XXInstall it with: pip install matplotlibXX"
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_7(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "Matplotlib is required for visualization features. "
                "install it with: pip install matplotlib"
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_8(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "Matplotlib is required for visualization features. "
                "INSTALL IT WITH: PIP INSTALL MATPLOTLIB"
            )
        return func(*args, **kwargs)
    return wrapper


def x_require_matplotlib__mutmut_9(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "Matplotlib is required for visualization features. "
                "Install it with: pip install matplotlib"
            )
        return func(**kwargs)
    return wrapper


def x_require_matplotlib__mutmut_10(func):
    """
    Decorator to ensure matplotlib is available before calling visualization functions.
    """
    def wrapper(*args, **kwargs):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "Matplotlib is required for visualization features. "
                "Install it with: pip install matplotlib"
            )
        return func(*args, )
    return wrapper

x_require_matplotlib__mutmut_mutants : ClassVar[MutantDict] = {
'x_require_matplotlib__mutmut_1': x_require_matplotlib__mutmut_1, 
    'x_require_matplotlib__mutmut_2': x_require_matplotlib__mutmut_2, 
    'x_require_matplotlib__mutmut_3': x_require_matplotlib__mutmut_3, 
    'x_require_matplotlib__mutmut_4': x_require_matplotlib__mutmut_4, 
    'x_require_matplotlib__mutmut_5': x_require_matplotlib__mutmut_5, 
    'x_require_matplotlib__mutmut_6': x_require_matplotlib__mutmut_6, 
    'x_require_matplotlib__mutmut_7': x_require_matplotlib__mutmut_7, 
    'x_require_matplotlib__mutmut_8': x_require_matplotlib__mutmut_8, 
    'x_require_matplotlib__mutmut_9': x_require_matplotlib__mutmut_9, 
    'x_require_matplotlib__mutmut_10': x_require_matplotlib__mutmut_10
}

def require_matplotlib(*args, **kwargs):
    result = _mutmut_trampoline(x_require_matplotlib__mutmut_orig, x_require_matplotlib__mutmut_mutants, args, kwargs)
    return result 

require_matplotlib.__signature__ = _mutmut_signature(x_require_matplotlib__mutmut_orig)
x_require_matplotlib__mutmut_orig.__name__ = 'x_require_matplotlib'


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
    ax.bar(x_pos, compute_times, label='Computation', color='steelblue', alpha=0.8)
    ax.bar(x_pos, spawn_overheads, bottom=compute_times,
           label='Spawn Overhead', color='orange', alpha=0.8)

    bottom2 = [c + s for c, s in zip(compute_times, spawn_overheads)]
    ax.bar(x_pos, ipc_overheads, bottom=bottom2,
           label='IPC Overhead', color='red', alpha=0.8)

    bottom3 = [b + i for b, i in zip(bottom2, ipc_overheads)]
    ax.bar(x_pos, chunking_overheads, bottom=bottom3,
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


def x_visualize_comparison_result__mutmut_orig(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_1(
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
    if HAS_MATPLOTLIB:
        warnings.warn(
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_2(
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
            None,
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_3(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            None
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_4(
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
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_5(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_6(
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
            "XXMatplotlib is not available. Install it with: pip install matplotlibXX",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_7(
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
            "matplotlib is not available. install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_8(
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
            "MATPLOTLIB IS NOT AVAILABLE. INSTALL IT WITH: PIP INSTALL MATPLOTLIB",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_9(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None and 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_10(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is not None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_11(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'XXallXX' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_12(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'ALL' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_13(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' not in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_14(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = None
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_15(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['XXtimesXX', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_16(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['TIMES', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_17(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'XXspeedupsXX']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_18(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'SPEEDUPS']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_19(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = None

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_20(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = ""
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_21(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_22(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = None
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_23(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(None)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_24(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=None, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_25(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=None)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_26(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_27(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, )

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_28(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=False, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_29(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=False)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_30(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = None
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_31(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = None
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_32(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = None

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_33(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = None

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_34(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'XXtimesXX' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_35(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'TIMES' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_36(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' not in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_37(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_38(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = None
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_39(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(None)
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_40(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path * "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_41(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "XXcomparison_times.pngXX")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_42(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "COMPARISON_TIMES.PNG")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_43(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = None

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_44(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "XXcomparison_times.pngXX"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_45(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "COMPARISON_TIMES.PNG"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_46(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = None

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_47(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['XXtimesXX'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_48(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['TIMES'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_49(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            None,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_50(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            None,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_51(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=None
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_52(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_53(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_54(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_55(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'XXspeedupsXX' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_56(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'SPEEDUPS' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_57(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' not in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_58(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_59(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = None
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_60(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(None)
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_61(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path * "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_62(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "XXspeedup_comparison.pngXX")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_63(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "SPEEDUP_COMPARISON.PNG")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_64(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = None

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_65(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "XXspeedup_comparison.pngXX"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_66(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "SPEEDUP_COMPARISON.PNG"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_67(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = None

    return result_paths


def x_visualize_comparison_result__mutmut_68(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['XXspeedupsXX'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_69(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['SPEEDUPS'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_70(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            None,
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_71(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            None,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_72(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            output_path=None
        )

    return result_paths


def x_visualize_comparison_result__mutmut_73(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            speedups,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_74(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            output_path=speedups_path
        )

    return result_paths


def x_visualize_comparison_result__mutmut_75(
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
            "Matplotlib is not available. Install it with: pip install matplotlib",
            UserWarning
        )
        return {}

    # Determine which plots to generate
    if plots is None or 'all' in plots:
        plot_types = ['times', 'speedups']
    else:
        plot_types = plots

    # Prepare output directory
    output_dir_path: Optional[Path] = None
    if output_dir is not None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

    # Extract data from comparison result
    config_names = [config.name for config in comparison_result.configs]
    execution_times = comparison_result.execution_times
    speedups = comparison_result.speedups

    # Generate plots
    result_paths = {}

    if 'times' in plot_types:
        if output_dir_path is not None:
            times_path = str(output_dir_path / "comparison_times.png")
        else:
            times_path = "comparison_times.png"

        result_paths['times'] = plot_comparison_times(
            config_names,
            execution_times,
            output_path=times_path
        )

    if 'speedups' in plot_types:
        if output_dir_path is not None:
            speedups_path = str(output_dir_path / "speedup_comparison.png")
        else:
            speedups_path = "speedup_comparison.png"

        result_paths['speedups'] = plot_speedup_comparison(
            config_names,
            speedups,
            )

    return result_paths

x_visualize_comparison_result__mutmut_mutants : ClassVar[MutantDict] = {
'x_visualize_comparison_result__mutmut_1': x_visualize_comparison_result__mutmut_1, 
    'x_visualize_comparison_result__mutmut_2': x_visualize_comparison_result__mutmut_2, 
    'x_visualize_comparison_result__mutmut_3': x_visualize_comparison_result__mutmut_3, 
    'x_visualize_comparison_result__mutmut_4': x_visualize_comparison_result__mutmut_4, 
    'x_visualize_comparison_result__mutmut_5': x_visualize_comparison_result__mutmut_5, 
    'x_visualize_comparison_result__mutmut_6': x_visualize_comparison_result__mutmut_6, 
    'x_visualize_comparison_result__mutmut_7': x_visualize_comparison_result__mutmut_7, 
    'x_visualize_comparison_result__mutmut_8': x_visualize_comparison_result__mutmut_8, 
    'x_visualize_comparison_result__mutmut_9': x_visualize_comparison_result__mutmut_9, 
    'x_visualize_comparison_result__mutmut_10': x_visualize_comparison_result__mutmut_10, 
    'x_visualize_comparison_result__mutmut_11': x_visualize_comparison_result__mutmut_11, 
    'x_visualize_comparison_result__mutmut_12': x_visualize_comparison_result__mutmut_12, 
    'x_visualize_comparison_result__mutmut_13': x_visualize_comparison_result__mutmut_13, 
    'x_visualize_comparison_result__mutmut_14': x_visualize_comparison_result__mutmut_14, 
    'x_visualize_comparison_result__mutmut_15': x_visualize_comparison_result__mutmut_15, 
    'x_visualize_comparison_result__mutmut_16': x_visualize_comparison_result__mutmut_16, 
    'x_visualize_comparison_result__mutmut_17': x_visualize_comparison_result__mutmut_17, 
    'x_visualize_comparison_result__mutmut_18': x_visualize_comparison_result__mutmut_18, 
    'x_visualize_comparison_result__mutmut_19': x_visualize_comparison_result__mutmut_19, 
    'x_visualize_comparison_result__mutmut_20': x_visualize_comparison_result__mutmut_20, 
    'x_visualize_comparison_result__mutmut_21': x_visualize_comparison_result__mutmut_21, 
    'x_visualize_comparison_result__mutmut_22': x_visualize_comparison_result__mutmut_22, 
    'x_visualize_comparison_result__mutmut_23': x_visualize_comparison_result__mutmut_23, 
    'x_visualize_comparison_result__mutmut_24': x_visualize_comparison_result__mutmut_24, 
    'x_visualize_comparison_result__mutmut_25': x_visualize_comparison_result__mutmut_25, 
    'x_visualize_comparison_result__mutmut_26': x_visualize_comparison_result__mutmut_26, 
    'x_visualize_comparison_result__mutmut_27': x_visualize_comparison_result__mutmut_27, 
    'x_visualize_comparison_result__mutmut_28': x_visualize_comparison_result__mutmut_28, 
    'x_visualize_comparison_result__mutmut_29': x_visualize_comparison_result__mutmut_29, 
    'x_visualize_comparison_result__mutmut_30': x_visualize_comparison_result__mutmut_30, 
    'x_visualize_comparison_result__mutmut_31': x_visualize_comparison_result__mutmut_31, 
    'x_visualize_comparison_result__mutmut_32': x_visualize_comparison_result__mutmut_32, 
    'x_visualize_comparison_result__mutmut_33': x_visualize_comparison_result__mutmut_33, 
    'x_visualize_comparison_result__mutmut_34': x_visualize_comparison_result__mutmut_34, 
    'x_visualize_comparison_result__mutmut_35': x_visualize_comparison_result__mutmut_35, 
    'x_visualize_comparison_result__mutmut_36': x_visualize_comparison_result__mutmut_36, 
    'x_visualize_comparison_result__mutmut_37': x_visualize_comparison_result__mutmut_37, 
    'x_visualize_comparison_result__mutmut_38': x_visualize_comparison_result__mutmut_38, 
    'x_visualize_comparison_result__mutmut_39': x_visualize_comparison_result__mutmut_39, 
    'x_visualize_comparison_result__mutmut_40': x_visualize_comparison_result__mutmut_40, 
    'x_visualize_comparison_result__mutmut_41': x_visualize_comparison_result__mutmut_41, 
    'x_visualize_comparison_result__mutmut_42': x_visualize_comparison_result__mutmut_42, 
    'x_visualize_comparison_result__mutmut_43': x_visualize_comparison_result__mutmut_43, 
    'x_visualize_comparison_result__mutmut_44': x_visualize_comparison_result__mutmut_44, 
    'x_visualize_comparison_result__mutmut_45': x_visualize_comparison_result__mutmut_45, 
    'x_visualize_comparison_result__mutmut_46': x_visualize_comparison_result__mutmut_46, 
    'x_visualize_comparison_result__mutmut_47': x_visualize_comparison_result__mutmut_47, 
    'x_visualize_comparison_result__mutmut_48': x_visualize_comparison_result__mutmut_48, 
    'x_visualize_comparison_result__mutmut_49': x_visualize_comparison_result__mutmut_49, 
    'x_visualize_comparison_result__mutmut_50': x_visualize_comparison_result__mutmut_50, 
    'x_visualize_comparison_result__mutmut_51': x_visualize_comparison_result__mutmut_51, 
    'x_visualize_comparison_result__mutmut_52': x_visualize_comparison_result__mutmut_52, 
    'x_visualize_comparison_result__mutmut_53': x_visualize_comparison_result__mutmut_53, 
    'x_visualize_comparison_result__mutmut_54': x_visualize_comparison_result__mutmut_54, 
    'x_visualize_comparison_result__mutmut_55': x_visualize_comparison_result__mutmut_55, 
    'x_visualize_comparison_result__mutmut_56': x_visualize_comparison_result__mutmut_56, 
    'x_visualize_comparison_result__mutmut_57': x_visualize_comparison_result__mutmut_57, 
    'x_visualize_comparison_result__mutmut_58': x_visualize_comparison_result__mutmut_58, 
    'x_visualize_comparison_result__mutmut_59': x_visualize_comparison_result__mutmut_59, 
    'x_visualize_comparison_result__mutmut_60': x_visualize_comparison_result__mutmut_60, 
    'x_visualize_comparison_result__mutmut_61': x_visualize_comparison_result__mutmut_61, 
    'x_visualize_comparison_result__mutmut_62': x_visualize_comparison_result__mutmut_62, 
    'x_visualize_comparison_result__mutmut_63': x_visualize_comparison_result__mutmut_63, 
    'x_visualize_comparison_result__mutmut_64': x_visualize_comparison_result__mutmut_64, 
    'x_visualize_comparison_result__mutmut_65': x_visualize_comparison_result__mutmut_65, 
    'x_visualize_comparison_result__mutmut_66': x_visualize_comparison_result__mutmut_66, 
    'x_visualize_comparison_result__mutmut_67': x_visualize_comparison_result__mutmut_67, 
    'x_visualize_comparison_result__mutmut_68': x_visualize_comparison_result__mutmut_68, 
    'x_visualize_comparison_result__mutmut_69': x_visualize_comparison_result__mutmut_69, 
    'x_visualize_comparison_result__mutmut_70': x_visualize_comparison_result__mutmut_70, 
    'x_visualize_comparison_result__mutmut_71': x_visualize_comparison_result__mutmut_71, 
    'x_visualize_comparison_result__mutmut_72': x_visualize_comparison_result__mutmut_72, 
    'x_visualize_comparison_result__mutmut_73': x_visualize_comparison_result__mutmut_73, 
    'x_visualize_comparison_result__mutmut_74': x_visualize_comparison_result__mutmut_74, 
    'x_visualize_comparison_result__mutmut_75': x_visualize_comparison_result__mutmut_75
}

def visualize_comparison_result(*args, **kwargs):
    result = _mutmut_trampoline(x_visualize_comparison_result__mutmut_orig, x_visualize_comparison_result__mutmut_mutants, args, kwargs)
    return result 

visualize_comparison_result.__signature__ = _mutmut_signature(x_visualize_comparison_result__mutmut_orig)
x_visualize_comparison_result__mutmut_orig.__name__ = 'x_visualize_comparison_result'
