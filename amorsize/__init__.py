"""
Amorsize: Dynamic Parallelism Optimizer & Overhead Calculator

A Python utility that analyzes the cost-benefit ratio of parallelization
and returns optimal n_jobs and chunksize parameters.
"""

from .adaptive_chunking import AdaptiveChunkingPool, create_adaptive_pool
from .batch import estimate_safe_batch_size, process_in_batches
from .benchmark import BenchmarkResult, quick_validate, validate_optimization
from .cache import (
    CacheStats,
    CacheValidationResult,
    clear_benchmark_cache,
    clear_cache,
    export_cache,
    get_benchmark_cache_stats,
    get_cache_dir,
    get_cache_stats,
    import_cache,
    prewarm_cache,
    prune_expired_cache,
    repair_cache,
    validate_cache,
    validate_cache_entry,
)
from .comparison import (
    ComparisonConfig,
    ComparisonResult,
    compare_strategies,
    compare_with_optimizer,
)
from .config import (
    ConfigData,
    get_default_config_dir,
    list_configs,
    load_config,
    save_config,
)
from .cost_model import (
    CacheInfo,
    MemoryBandwidthInfo,
    NUMAInfo,
    SystemTopology,
    calculate_advanced_amdahl_speedup,
    detect_system_topology,
)
from .executor import execute
from .history import (
    HistoryEntry,
    clear_history,
    compare_entries,
    delete_result,
    list_results,
    load_result,
    save_result,
)
from .hooks import (
    HookContext,
    HookEvent,
    HookManager,
    create_error_hook,
    create_progress_hook,
    create_throughput_hook,
    create_timing_hook,
)
from .optimizer import DiagnosticProfile, OptimizationResult, optimize
from .performance import (
    PerformanceResult,
    WorkloadSpec,
    compare_performance_results,
    get_standard_workloads,
    run_performance_benchmark,
    run_performance_suite,
)
from .pool_manager import (
    PoolManager,
    get_global_pool_manager,
    managed_pool,
    shutdown_global_pool_manager,
)
from .streaming import StreamingOptimizationResult, optimize_streaming
from .structured_logging import configure_logging
from .tuning import TuningResult, bayesian_tune_parameters, quick_tune, tune_parameters
from .validation import ValidationResult, validate_system
from .visualization import (
    check_matplotlib,
    plot_comparison_times,
    plot_overhead_breakdown,
    plot_scaling_curve,
    plot_speedup_comparison,
    visualize_comparison_result,
)
from .watch import WatchMonitor, WatchSnapshot, watch

# Monitoring integrations (optional, no extra dependencies)
try:
    from .monitoring import (
        PrometheusMetrics,
        StatsDClient,
        create_multi_monitoring_hook,
        create_prometheus_hook,
        create_statsd_hook,
        create_webhook_hook,
    )
    _has_monitoring = True
except ImportError:
    _has_monitoring = False
    # Stubs for when monitoring module is not available
    def create_prometheus_hook(*args, **kwargs):
        raise ImportError("Monitoring module not available")
    def create_statsd_hook(*args, **kwargs):
        raise ImportError("Monitoring module not available")
    def create_webhook_hook(*args, **kwargs):
        raise ImportError("Monitoring module not available")
    def create_multi_monitoring_hook(*args, **kwargs):
        raise ImportError("Monitoring module not available")
    PrometheusMetrics = None
    StatsDClient = None

# ML prediction functions (optional feature)
try:
    from .ml_prediction import (
        CROSS_SYSTEM_WEIGHT,
        DEFAULT_CONFIDENCE_THRESHOLD,
        DEFAULT_K_VALUE,
        ENABLE_ENSEMBLE_PREDICTION,
        ENABLE_K_TUNING,
        K_RANGE_MAX,
        K_RANGE_MIN,
        MAX_CLUSTERS,
        MIN_CLUSTERING_SAMPLES,
        MIN_SAMPLES_FOR_ENSEMBLE,
        MIN_SAMPLES_FOR_K_TUNING,
        MIN_SYSTEM_SIMILARITY,
        MIN_TRAINING_SAMPLES,
        CalibrationData,
        PredictionResult,
        StreamingPredictionResult,
        SystemFingerprint,
        WorkloadCluster,
        get_calibration_stats,
        get_ml_training_data_version,
        load_ml_training_data,
        predict_parameters,
        predict_streaming_parameters,
        track_prediction_accuracy,
        update_model_from_execution,
        update_model_from_streaming_execution,
    )
    _has_ml_prediction = True
except ImportError:
    _has_ml_prediction = False
    # Stubs for when ML module is not available
    def predict_parameters(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    def predict_streaming_parameters(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    def update_model_from_execution(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    def update_model_from_streaming_execution(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    def track_prediction_accuracy(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    def get_calibration_stats(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    def load_ml_training_data(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    def get_ml_training_data_version(*args, **kwargs):
        raise ImportError("ML prediction module not available")
    PredictionResult = None
    StreamingPredictionResult = None
    CalibrationData = None
    SystemFingerprint = None
    WorkloadCluster = None
    MIN_TRAINING_SAMPLES = 3
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    MIN_SYSTEM_SIMILARITY = 0.8
    CROSS_SYSTEM_WEIGHT = 0.7
    MIN_CLUSTERING_SAMPLES = 10
    MAX_CLUSTERS = 5
    ENABLE_K_TUNING = True
    K_RANGE_MIN = 3
    K_RANGE_MAX = 15
    MIN_SAMPLES_FOR_K_TUNING = 20
    DEFAULT_K_VALUE = 5
    ENABLE_ENSEMBLE_PREDICTION = True
    MIN_SAMPLES_FOR_ENSEMBLE = 15

# ML training data pruning functions (optional feature, requires ml_prediction)
try:
    from .ml_pruning import DEFAULT_SIMILARITY_THRESHOLD as PRUNING_SIMILARITY_THRESHOLD
    from .ml_pruning import (
        MIN_SAMPLES_FOR_PRUNING,
        TARGET_PRUNING_RATIO,
        PruningResult,
        auto_prune_training_data,
        prune_training_data,
    )
    _has_ml_pruning = True
except ImportError:
    _has_ml_pruning = False
    # Stubs for when ML pruning is not available
    def prune_training_data(*args, **kwargs):
        raise ImportError("ML pruning module not available")
    def auto_prune_training_data(*args, **kwargs):
        raise ImportError("ML pruning module not available")
    PruningResult = None
    PRUNING_SIMILARITY_THRESHOLD = 0.5
    MIN_SAMPLES_FOR_PRUNING = 50
    TARGET_PRUNING_RATIO = 0.35

# Distributed cache functions (optional, requires redis-py)
try:
    from .distributed_cache import (
        clear_distributed_cache,
        configure_distributed_cache,
        disable_distributed_cache,
        get_distributed_cache_stats,
        is_distributed_cache_enabled,
        prewarm_distributed_cache,
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
    "predict_streaming_parameters",
    "update_model_from_execution",
    "update_model_from_streaming_execution",
    "load_ml_training_data",
    "get_ml_training_data_version",
    "track_prediction_accuracy",
    "get_calibration_stats",
    "PredictionResult",
    "StreamingPredictionResult",
    "CalibrationData",
    "SystemFingerprint",
    "WorkloadCluster",
    "MIN_TRAINING_SAMPLES",
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "MIN_SYSTEM_SIMILARITY",
    "CROSS_SYSTEM_WEIGHT",
    "MIN_CLUSTERING_SAMPLES",
    "MAX_CLUSTERS",
    "ENABLE_K_TUNING",
    "K_RANGE_MIN",
    "K_RANGE_MAX",
    "MIN_SAMPLES_FOR_K_TUNING",
    "DEFAULT_K_VALUE",
    "ENABLE_ENSEMBLE_PREDICTION",
    "MIN_SAMPLES_FOR_ENSEMBLE",
    "prune_training_data",
    "auto_prune_training_data",
    "PruningResult",
    "PRUNING_SIMILARITY_THRESHOLD",
    "MIN_SAMPLES_FOR_PRUNING",
    "TARGET_PRUNING_RATIO",
    "AdaptiveChunkingPool",
    "create_adaptive_pool",
    "PoolManager",
    "get_global_pool_manager",
    "managed_pool",
    "shutdown_global_pool_manager",
    "detect_system_topology",
    "calculate_advanced_amdahl_speedup",
    "CacheInfo",
    "NUMAInfo",
    "MemoryBandwidthInfo",
    "SystemTopology",
    "watch",
    "WatchMonitor",
    "WatchSnapshot",
    "HookManager",
    "HookEvent",
    "HookContext",
    "create_progress_hook",
    "create_timing_hook",
    "create_throughput_hook",
    "create_error_hook",
    "create_prometheus_hook",
    "create_statsd_hook",
    "create_webhook_hook",
    "create_multi_monitoring_hook",
    "PrometheusMetrics",
    "StatsDClient",
]
