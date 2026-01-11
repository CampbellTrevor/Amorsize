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
from .performance import (
    run_performance_benchmark,
    run_performance_suite,
    compare_performance_results,
    get_standard_workloads,
    WorkloadSpec,
    PerformanceResult
)
from .cache import (
    clear_cache,
    prune_expired_cache,
    get_cache_dir,
    clear_benchmark_cache,
    get_cache_stats,
    get_benchmark_cache_stats,
    CacheStats,
    prewarm_cache,
    export_cache,
    import_cache,
    validate_cache_entry,
    validate_cache,
    repair_cache,
    CacheValidationResult
)
from .structured_logging import configure_logging

# ML prediction functions (optional feature)
try:
    from .ml_prediction import (
        predict_parameters,
        PredictionResult,
        MIN_TRAINING_SAMPLES,
        DEFAULT_CONFIDENCE_THRESHOLD
    )
    _has_ml_prediction = True
except ImportError:
    _has_ml_prediction = False
    # Stubs for when ML module is not available
    def predict_parameters(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    PredictionResult = None
    MIN_TRAINING_SAMPLES = 3
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7

# Distributed cache functions (optional, requires redis-py)
try:
    from .distributed_cache import (
        configure_distributed_cache,
        disable_distributed_cache,
        is_distributed_cache_enabled,
        clear_distributed_cache,
        get_distributed_cache_stats,
        prewarm_distributed_cache
    )
    _has_distributed_cache = True
except ImportError:
    _has_distributed_cache = False
    # Create stub functions that warn when called
    def configure_distributed_cache(*args, **kwargs):
        raise ImportError("Distributed caching requires redis-py. Install with: pip install redis")
    def disable_distributed_cache():
        pass
    def is_distributed_cache_enabled():
        return False
    def clear_distributed_cache(*args, **kwargs):
        return 0
    def get_distributed_cache_stats():
        return {"enabled": False}
    def prewarm_distributed_cache(*args, **kwargs):
        raise ImportError("Distributed caching requires redis-py. Install with: pip install redis")

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
    "run_performance_benchmark",
    "run_performance_suite",
    "compare_performance_results",
    "get_standard_workloads",
    "clear_cache",
    "prune_expired_cache",
    "get_cache_dir",
    "clear_benchmark_cache",
    "get_cache_stats",
    "get_benchmark_cache_stats",
    "CacheStats",
    "prewarm_cache",
    "export_cache",
    "import_cache",
    "validate_cache_entry",
    "validate_cache",
    "repair_cache",
    "configure_distributed_cache",
    "disable_distributed_cache",
    "is_distributed_cache_enabled",
    "clear_distributed_cache",
    "get_distributed_cache_stats",
    "prewarm_distributed_cache",
    "OptimizationResult",
    "DiagnosticProfile",
    "StreamingOptimizationResult",
    "BenchmarkResult",
    "ValidationResult",
    "ComparisonConfig",
    "ComparisonResult",
    "HistoryEntry",
    "TuningResult",
    "ConfigData",
    "WorkloadSpec",
    "PerformanceResult",
    "CacheValidationResult",
    "configure_logging",
    "predict_parameters",
    "PredictionResult",
    "MIN_TRAINING_SAMPLES",
    "DEFAULT_CONFIDENCE_THRESHOLD"
]
