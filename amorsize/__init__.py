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
    "OptimizationResult",
    "DiagnosticProfile",
    "StreamingOptimizationResult",
    "BenchmarkResult",
    "ValidationResult",
    "ComparisonConfig",
    "ComparisonResult"
]
