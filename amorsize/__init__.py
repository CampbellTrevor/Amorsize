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

__version__ = "0.1.0"
__all__ = [
    "optimize",
    "execute", 
    "process_in_batches",
    "estimate_safe_batch_size",
    "optimize_streaming",
    "validate_optimization",
    "quick_validate",
    "OptimizationResult",
    "DiagnosticProfile",
    "StreamingOptimizationResult",
    "BenchmarkResult"
]
