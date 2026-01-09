"""
Amorsize: Dynamic Parallelism Optimizer & Overhead Calculator

A Python utility that analyzes the cost-benefit ratio of parallelization
and returns optimal n_jobs and chunksize parameters.
"""

from .optimizer import optimize, DiagnosticProfile, OptimizationResult
from .executor import execute

__version__ = "0.1.0"
__all__ = ["optimize", "execute", "OptimizationResult", "DiagnosticProfile"]
