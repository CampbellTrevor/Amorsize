"""
Bottleneck analysis module for identifying performance limiters.

This module analyzes optimization results to identify what's preventing
better parallelization performance and provides actionable recommendations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    SPAWN_OVERHEAD = "spawn_overhead"
    IPC_OVERHEAD = "ipc_overhead"
    CHUNKING_OVERHEAD = "chunking_overhead"
    MEMORY_CONSTRAINT = "memory_constraint"
    WORKLOAD_TOO_SMALL = "workload_too_small"
    INSUFFICIENT_COMPUTATION = "insufficient_computation"
    DATA_SIZE = "data_size"
    HETEROGENEOUS_WORKLOAD = "heterogeneous_workload"
    NONE = "none"


@dataclass
class BottleneckAnalysis:
    """
    Results of bottleneck analysis.
    
    Attributes:
        primary_bottleneck: The most significant performance limiter
        bottleneck_severity: Score from 0-1 indicating how much this bottleneck hurts performance
        contributing_factors: List of secondary bottlenecks
        recommendations: List of actionable recommendations to address bottlenecks
        overhead_breakdown: Percentage breakdown of overhead sources
        efficiency_score: Overall parallelization efficiency (0-1)
    """
    primary_bottleneck: BottleneckType
    bottleneck_severity: float
    contributing_factors: List[Tuple[BottleneckType, float]]
    recommendations: List[str]
    overhead_breakdown: Dict[str, float]
    efficiency_score: float


def analyze_bottlenecks(
    n_jobs: int,
    chunksize: int,
    total_items: int,
    avg_execution_time: float,
    spawn_cost: float,
    ipc_overhead: float,
    chunking_overhead: float,
    estimated_speedup: float,
    physical_cores: int,
    available_memory: int,
    estimated_memory_per_job: int,
    coefficient_of_variation: float = 0.0
) -> BottleneckAnalysis:
    """
    Analyze optimization results to identify performance bottlenecks.
    
    Args:
        n_jobs: Number of parallel workers
        chunksize: Chunk size for task distribution
        total_items: Total number of items to process
        avg_execution_time: Average time per item (seconds)
        spawn_cost: Process spawn overhead (seconds)
        ipc_overhead: Inter-process communication overhead (seconds)
        chunking_overhead: Task distribution overhead (seconds)
        estimated_speedup: Expected speedup factor
        physical_cores: Number of physical CPU cores
        available_memory: Available system memory (bytes)
        estimated_memory_per_job: Memory needed per worker (bytes)
        coefficient_of_variation: Workload variability (0 = uniform, >0.5 = heterogeneous)
    
    Returns:
        BottleneckAnalysis with identified bottlenecks and recommendations
    """
    recommendations = []
    bottlenecks = []
    
    # Calculate total execution time components
    total_serial_time = avg_execution_time * total_items
    parallel_compute_time = total_serial_time / n_jobs if n_jobs > 0 else total_serial_time
    total_overhead = spawn_cost + ipc_overhead + chunking_overhead
    
    # Calculate efficiency score (actual speedup / theoretical maximum)
    theoretical_max_speedup = min(n_jobs, physical_cores)
    efficiency_score = estimated_speedup / theoretical_max_speedup if theoretical_max_speedup > 0 else 0.0
    efficiency_score = min(1.0, max(0.0, efficiency_score))
    
    # Overhead breakdown percentages
    total_parallel_time = parallel_compute_time + total_overhead
    overhead_breakdown = {}
    if total_parallel_time > 0:
        overhead_breakdown['computation'] = (parallel_compute_time / total_parallel_time) * 100
        overhead_breakdown['spawn'] = (spawn_cost / total_parallel_time) * 100
        overhead_breakdown['ipc'] = (ipc_overhead / total_parallel_time) * 100
        overhead_breakdown['chunking'] = (chunking_overhead / total_parallel_time) * 100
    
    # 1. Check for spawn overhead bottleneck
    if total_parallel_time > 0 and spawn_cost / total_parallel_time > 0.2:
        severity = spawn_cost / total_parallel_time
        bottlenecks.append((BottleneckType.SPAWN_OVERHEAD, severity))
        recommendations.append(
            "Spawn overhead is significant. Consider:\n"
            f"  • Using 'fork' or 'forkserver' start method (current spawn cost: {spawn_cost:.3f}s)\n"
            "  • Increasing workload per item to amortize spawn costs\n"
            "  • Using a persistent pool with PoolManager for repeated operations"
        )
    
    # 2. Check for IPC overhead bottleneck
    if total_parallel_time > 0 and ipc_overhead / total_parallel_time > 0.15:
        severity = ipc_overhead / total_parallel_time
        bottlenecks.append((BottleneckType.IPC_OVERHEAD, severity))
        recommendations.append(
            "IPC/serialization overhead is significant. Consider:\n"
            "  • Reducing data size passed to workers\n"
            "  • Using more efficient data structures (arrays instead of objects)\n"
            "  • Processing data in larger chunks to amortize pickling costs"
        )
    
    # 3. Check for chunking overhead bottleneck
    num_chunks = (total_items + chunksize - 1) // chunksize if chunksize > 0 else total_items
    if total_parallel_time > 0 and chunking_overhead / total_parallel_time > 0.1:
        severity = chunking_overhead / total_parallel_time
        bottlenecks.append((BottleneckType.CHUNKING_OVERHEAD, severity))
        recommendations.append(
            f"Task distribution overhead is significant ({num_chunks} chunks). Consider:\n"
            f"  • Increasing chunksize from {chunksize} to {chunksize * 2} or more\n"
            "  • Using batch processing for very large datasets"
        )
    
    # 4. Check for memory constraint bottleneck
    memory_usage_ratio = (n_jobs * estimated_memory_per_job) / available_memory if available_memory > 0 else 0
    if n_jobs < physical_cores and memory_usage_ratio > 0.7:
        severity = min(1.0, memory_usage_ratio)
        bottlenecks.append((BottleneckType.MEMORY_CONSTRAINT, severity))
        recommendations.append(
            f"Memory constraints limiting workers (using {n_jobs}/{physical_cores} cores). Consider:\n"
            "  • Processing data in smaller batches\n"
            "  • Reducing memory footprint of your function\n"
            f"  • Adding more RAM (current: {available_memory / (1024**3):.1f} GB)"
        )
    
    # 5. Check for insufficient computation per item
    if avg_execution_time > 0 and avg_execution_time < 0.001:  # < 1ms per item
        severity = 1.0 - min(1.0, avg_execution_time / 0.001)
        bottlenecks.append((BottleneckType.INSUFFICIENT_COMPUTATION, severity))
        recommendations.append(
            f"Each item takes only {avg_execution_time*1000:.3f}ms. Overhead dominates. Consider:\n"
            "  • Increasing computation per item\n"
            "  • Batching multiple items together before processing\n"
            "  • Using serial execution for such lightweight tasks"
        )
    
    # 6. Check for small workload bottleneck
    if total_serial_time > 0 and total_serial_time < 1.0:  # Less than 1 second of work
        severity = 1.0 - min(1.0, total_serial_time)
        bottlenecks.append((BottleneckType.WORKLOAD_TOO_SMALL, severity))
        recommendations.append(
            f"Total workload is small ({total_serial_time:.3f}s). Consider:\n"
            "  • Accumulating more data before processing\n"
            f"  • Increasing dataset size from {total_items} items\n"
            "  • Using serial execution for such small workloads"
        )
    
    # 7. Check for heterogeneous workload
    if coefficient_of_variation > 0.5:
        severity = min(1.0, coefficient_of_variation)
        bottlenecks.append((BottleneckType.HETEROGENEOUS_WORKLOAD, severity))
        recommendations.append(
            f"Workload is heterogeneous (CV={coefficient_of_variation:.2f}). Consider:\n"
            "  • Using dynamic chunking with smaller chunks\n"
            "  • Sorting items by expected execution time\n"
            "  • Using imap_unordered for better load balancing"
        )
    
    # Determine primary bottleneck (highest severity)
    if bottlenecks:
        bottlenecks.sort(key=lambda x: x[1], reverse=True)
        primary_bottleneck = bottlenecks[0][0]
        bottleneck_severity = bottlenecks[0][1]
        contributing_factors = bottlenecks[1:] if len(bottlenecks) > 1 else []
    else:
        primary_bottleneck = BottleneckType.NONE
        bottleneck_severity = 0.0
        contributing_factors = []
        if efficiency_score > 0.8:
            recommendations.append("✅ Excellent parallelization efficiency! No significant bottlenecks detected.")
        elif efficiency_score > 0.5:
            recommendations.append("Good parallelization efficiency. Minor optimizations possible.")
    
    return BottleneckAnalysis(
        primary_bottleneck=primary_bottleneck,
        bottleneck_severity=bottleneck_severity,
        contributing_factors=contributing_factors,
        recommendations=recommendations,
        overhead_breakdown=overhead_breakdown,
        efficiency_score=efficiency_score
    )


def format_bottleneck_report(analysis: BottleneckAnalysis) -> str:
    """
    Format bottleneck analysis into a human-readable report.
    
    Args:
        analysis: BottleneckAnalysis result
    
    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("PERFORMANCE BOTTLENECK ANALYSIS")
    lines.append("=" * 70)
    
    # Efficiency score
    lines.append(f"\nOverall Efficiency: {analysis.efficiency_score*100:.1f}%")
    if analysis.efficiency_score > 0.8:
        lines.append("Status: ✅ Excellent")
    elif analysis.efficiency_score > 0.6:
        lines.append("Status: ✓ Good")
    elif analysis.efficiency_score > 0.4:
        lines.append("Status: ⚠ Fair")
    else:
        lines.append("Status: ⚠ Poor")
    
    # Primary bottleneck
    if analysis.primary_bottleneck != BottleneckType.NONE:
        lines.append(f"\nPrimary Bottleneck: {analysis.primary_bottleneck.value.replace('_', ' ').title()}")
        lines.append(f"Severity: {analysis.bottleneck_severity*100:.1f}%")
        
        # Contributing factors
        if analysis.contributing_factors:
            lines.append("\nContributing Factors:")
            for bottleneck, severity in analysis.contributing_factors[:3]:  # Top 3
                lines.append(f"  • {bottleneck.value.replace('_', ' ').title()}: {severity*100:.1f}%")
    
    # Overhead breakdown
    if analysis.overhead_breakdown:
        lines.append("\nTime Distribution:")
        for component, percentage in sorted(analysis.overhead_breakdown.items(), key=lambda x: x[1], reverse=True):
            bar_length = int(percentage / 2)  # Scale to 50 chars max
            bar = "█" * bar_length
            lines.append(f"  {component.capitalize():12s} [{bar:<50s}] {percentage:5.1f}%")
    
    # Recommendations
    if analysis.recommendations:
        lines.append("\nRECOMMENDATIONS:")
        lines.append("-" * 70)
        for i, rec in enumerate(analysis.recommendations, 1):
            lines.append(f"\n{i}. {rec}")
    
    lines.append("\n" + "=" * 70)
    return "\n".join(lines)
