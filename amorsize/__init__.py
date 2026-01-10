"""
Amorsize: Dynamic Parallelism Optimizer & Overhead Calculator

A Python utility that analyzes the cost-benefit ratio of parallelization
and returns optimal n_jobs and chunksize parameters.
"""

from .optimizer import optimize, DiagnosticProfile, OptimizationResult
from .executor import execute
from .batch import process_in_batches, estimate_safe_batch_size
from .streaming import optimize_streaming, StreamingOptimizationResult
from .benchmark import validate_optimization, quick_validate, BenchmarkResult
from .validation import validate_system, ValidationResult
from .comparison import compare_strategies, compare_with_optimizer, ComparisonConfig, ComparisonResult
from .visualization import (
    plot_comparison_times,
    plot_speedup_comparison,
    plot_overhead_breakdown,
    plot_scaling_curve,
    visualize_comparison_result,
    check_matplotlib
)
from .history import (
    save_result,
    load_result,
    list_results,
    delete_result,
    compare_entries,
    clear_history,
    HistoryEntry
)
from .tuning import (
    tune_parameters,
    quick_tune,
    bayesian_tune_parameters,
    TuningResult
)
from .config import (
    save_config,
    load_config,
    list_configs,
    get_default_config_dir,
    ConfigData
)

__version__ = "0.1.0"
__all__ = [
    "optimize",
    "execute", 
    "process_in_batches",
    "estimate_safe_batch_size",
    "optimize_streaming",
    "validate_optimization",
    "quick_validate",
    "validate_system",
    "compare_strategies",
    "compare_with_optimizer",
    "plot_comparison_times",
    "plot_speedup_comparison",
    "plot_overhead_breakdown",
    "plot_scaling_curve",
    "visualize_comparison_result",
    "check_matplotlib",
    "save_result",
    "load_result",
    "list_results",
    "delete_result",
    "compare_entries",
    "clear_history",
    "tune_parameters",
    "quick_tune",
    "bayesian_tune_parameters",
    "save_config",
    "load_config",
    "list_configs",
    "get_default_config_dir",
    "OptimizationResult",
    "DiagnosticProfile",
    "StreamingOptimizationResult",
    "BenchmarkResult",
    "ValidationResult",
    "ComparisonConfig",
    "ComparisonResult",
    "HistoryEntry",
    "TuningResult",
    "ConfigData"
]
