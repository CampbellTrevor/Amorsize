"""
Tests for bottleneck analysis module.
"""

import pytest
from amorsize.bottleneck_analysis import (
    BottleneckAnalysis,
    BottleneckType,
    analyze_bottlenecks,
    format_bottleneck_report,
)


class TestBottleneckAnalysis:
    """Test suite for bottleneck analysis functionality."""

    def test_no_bottleneck_high_efficiency(self):
        """Test case with excellent parallelization efficiency."""
        analysis = analyze_bottlenecks(
            n_jobs=8,
            chunksize=50,
            total_items=1000,
            avg_execution_time=0.01,  # 10ms per item
            spawn_cost=0.05,  # 50ms total spawn
            ipc_overhead=0.1,  # 100ms IPC
            chunking_overhead=0.02,  # 20ms chunking
            estimated_speedup=7.5,  # Very good speedup
            physical_cores=8,
            available_memory=8 * 1024**3,  # 8 GB
            estimated_memory_per_job=100 * 1024**2,  # 100 MB per job
            coefficient_of_variation=0.1
        )
        
        assert analysis.efficiency_score > 0.8
        assert analysis.primary_bottleneck == BottleneckType.NONE
        assert analysis.bottleneck_severity == 0.0
        assert len(analysis.recommendations) > 0
        assert "Excellent" in analysis.recommendations[0] or "excellent" in analysis.recommendations[0]

    def test_spawn_overhead_bottleneck(self):
        """Test detection of spawn overhead as primary bottleneck."""
        analysis = analyze_bottlenecks(
            n_jobs=8,
            chunksize=50,
            total_items=100,
            avg_execution_time=0.001,  # 1ms per item - fast computation
            spawn_cost=0.5,  # 500ms spawn - HUGE overhead
            ipc_overhead=0.01,
            chunking_overhead=0.005,
            estimated_speedup=1.2,  # Poor speedup
            physical_cores=8,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        
        assert analysis.primary_bottleneck == BottleneckType.SPAWN_OVERHEAD
        assert analysis.bottleneck_severity > 0.2
        assert any("spawn" in rec.lower() for rec in analysis.recommendations)
        assert any("fork" in rec.lower() or "forkserver" in rec.lower() for rec in analysis.recommendations)

    def test_ipc_overhead_bottleneck(self):
        """Test detection of IPC/serialization overhead."""
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=100,
            total_items=1000,
            avg_execution_time=0.001,
            spawn_cost=0.02,
            ipc_overhead=0.8,  # Very high IPC overhead
            chunking_overhead=0.01,
            estimated_speedup=2.0,
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        
        assert analysis.primary_bottleneck == BottleneckType.IPC_OVERHEAD
        assert analysis.bottleneck_severity > 0.15
        assert any("ipc" in rec.lower() or "serialization" in rec.lower() for rec in analysis.recommendations)

    def test_memory_constraint_bottleneck(self):
        """Test detection of memory constraints limiting workers."""
        analysis = analyze_bottlenecks(
            n_jobs=4,  # Limited by memory
            chunksize=50,
            total_items=1000,
            avg_execution_time=0.01,
            spawn_cost=0.05,
            ipc_overhead=0.1,
            chunking_overhead=0.02,
            estimated_speedup=3.8,
            physical_cores=8,  # Have 8 cores but using only 4
            available_memory=4 * 1024**3,  # 4 GB
            estimated_memory_per_job=800 * 1024**2,  # 800 MB per job (tight!)
            coefficient_of_variation=0.1
        )
        
        assert analysis.primary_bottleneck == BottleneckType.MEMORY_CONSTRAINT
        assert any("memory" in rec.lower() for rec in analysis.recommendations)

    def test_workload_too_small_bottleneck(self):
        """Test detection of workload that's too small to parallelize."""
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=5,
            total_items=50,
            avg_execution_time=0.01,  # Total: 0.5s
            spawn_cost=0.1,
            ipc_overhead=0.05,
            chunking_overhead=0.02,
            estimated_speedup=1.5,
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        
        assert analysis.primary_bottleneck == BottleneckType.WORKLOAD_TOO_SMALL
        assert any("small" in rec.lower() or "accumulating" in rec.lower() for rec in analysis.recommendations)

    def test_insufficient_computation_bottleneck(self):
        """Test detection of tasks that are too lightweight."""
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=100,
            total_items=10000,
            avg_execution_time=0.0001,  # 0.1ms per item - too fast!
            spawn_cost=0.05,
            ipc_overhead=0.1,
            chunking_overhead=0.02,
            estimated_speedup=2.0,
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        
        assert analysis.primary_bottleneck == BottleneckType.INSUFFICIENT_COMPUTATION
        assert any("computation" in rec.lower() or "batching" in rec.lower() for rec in analysis.recommendations)

    def test_heterogeneous_workload_bottleneck(self):
        """Test detection of heterogeneous workloads."""
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=50,
            total_items=1000,
            avg_execution_time=0.01,
            spawn_cost=0.05,
            ipc_overhead=0.1,
            chunking_overhead=0.02,
            estimated_speedup=3.0,
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.8  # High variability
        )
        
        # Check if heterogeneous workload is identified
        is_in_contributing = any(b[0] == BottleneckType.HETEROGENEOUS_WORKLOAD 
                                 for b in analysis.contributing_factors)
        is_primary = analysis.primary_bottleneck == BottleneckType.HETEROGENEOUS_WORKLOAD
        assert is_in_contributing or is_primary, \
            "Heterogeneous workload should be identified as bottleneck"
        
        # Check for heterogeneous-related recommendations
        found_heterogeneous_rec = any("heterogeneous" in rec.lower() or "dynamic" in rec.lower() 
                                       for rec in analysis.recommendations)
        assert found_heterogeneous_rec, \
            "Should provide recommendations for heterogeneous workload"

    def test_chunking_overhead_bottleneck(self):
        """Test detection of excessive task distribution overhead."""
        analysis = analyze_bottlenecks(
            n_jobs=8,
            chunksize=1,  # Very small chunks = lots of overhead
            total_items=10000,
            avg_execution_time=0.001,
            spawn_cost=0.05,
            ipc_overhead=0.1,
            chunking_overhead=0.5,  # High chunking overhead
            estimated_speedup=4.0,
            physical_cores=8,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        
        assert analysis.primary_bottleneck == BottleneckType.CHUNKING_OVERHEAD
        assert any("chunk" in rec.lower() for rec in analysis.recommendations)

    def test_multiple_contributing_factors(self):
        """Test case with multiple bottlenecks."""
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=10,
            total_items=100,
            avg_execution_time=0.002,
            spawn_cost=0.2,  # Significant spawn
            ipc_overhead=0.15,  # Significant IPC
            chunking_overhead=0.08,  # Significant chunking
            estimated_speedup=1.5,
            physical_cores=8,
            available_memory=4 * 1024**3,
            estimated_memory_per_job=800 * 1024**2,  # Memory constraint
            coefficient_of_variation=0.6  # Some variability
        )
        
        # Should have multiple contributing factors
        assert len(analysis.contributing_factors) >= 1
        # Primary should be the most severe
        assert analysis.bottleneck_severity > 0

    def test_overhead_breakdown_percentages(self):
        """Test that overhead breakdown percentages are calculated correctly."""
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=50,
            total_items=1000,
            avg_execution_time=0.01,
            spawn_cost=0.1,
            ipc_overhead=0.2,
            chunking_overhead=0.05,
            estimated_speedup=3.5,
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        
        # Check that breakdown exists and sums to ~100%
        assert 'computation' in analysis.overhead_breakdown
        assert 'spawn' in analysis.overhead_breakdown
        assert 'ipc' in analysis.overhead_breakdown
        assert 'chunking' in analysis.overhead_breakdown
        
        total_percentage = sum(analysis.overhead_breakdown.values())
        assert 99 <= total_percentage <= 101  # Allow small rounding error

    def test_efficiency_score_calculation(self):
        """Test efficiency score is calculated correctly."""
        # Perfect efficiency
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=100,
            total_items=1000,
            avg_execution_time=0.1,
            spawn_cost=0.01,
            ipc_overhead=0.01,
            chunking_overhead=0.01,
            estimated_speedup=4.0,  # Perfect linear speedup
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        assert analysis.efficiency_score == 1.0
        
        # Poor efficiency
        analysis2 = analyze_bottlenecks(
            n_jobs=4,
            chunksize=10,
            total_items=100,
            avg_execution_time=0.001,
            spawn_cost=0.5,
            ipc_overhead=0.3,
            chunking_overhead=0.1,
            estimated_speedup=1.2,  # Very poor speedup
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        assert analysis2.efficiency_score < 0.5

    def test_format_bottleneck_report(self):
        """Test report formatting."""
        analysis = BottleneckAnalysis(
            primary_bottleneck=BottleneckType.SPAWN_OVERHEAD,
            bottleneck_severity=0.35,
            contributing_factors=[(BottleneckType.IPC_OVERHEAD, 0.15)],
            recommendations=["Use fork instead of spawn", "Increase workload per item"],
            overhead_breakdown={'computation': 50.0, 'spawn': 30.0, 'ipc': 15.0, 'chunking': 5.0},
            efficiency_score=0.65
        )
        
        report = format_bottleneck_report(analysis)
        
        # Check report structure
        assert "PERFORMANCE BOTTLENECK ANALYSIS" in report
        assert "Overall Efficiency: 65.0%" in report
        assert "Spawn Overhead" in report
        assert "Severity: 35.0%" in report
        assert "RECOMMENDATIONS:" in report
        assert "fork" in report.lower()

    def test_edge_case_zero_values(self):
        """Test handling of edge cases with zero values."""
        analysis = analyze_bottlenecks(
            n_jobs=0,
            chunksize=1,
            total_items=0,
            avg_execution_time=0.0,
            spawn_cost=0.0,
            ipc_overhead=0.0,
            chunking_overhead=0.0,
            estimated_speedup=1.0,
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=0,
            coefficient_of_variation=0.0
        )
        
        # Should not crash and should have sensible defaults
        assert isinstance(analysis, BottleneckAnalysis)
        assert 0.0 <= analysis.efficiency_score <= 1.0

    def test_edge_case_extreme_values(self):
        """Test handling of extreme values."""
        analysis = analyze_bottlenecks(
            n_jobs=1000,
            chunksize=1,
            total_items=1000000,
            avg_execution_time=10.0,
            spawn_cost=100.0,
            ipc_overhead=200.0,
            chunking_overhead=50.0,
            estimated_speedup=1.01,
            physical_cores=16,
            available_memory=1024**3,
            estimated_memory_per_job=10 * 1024**3,  # More than available!
            coefficient_of_variation=2.0
        )
        
        # Should not crash
        assert isinstance(analysis, BottleneckAnalysis)
        assert analysis.bottleneck_severity >= 0.0

    def test_recommendations_are_actionable(self):
        """Test that recommendations contain actionable advice."""
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=10,
            total_items=100,
            avg_execution_time=0.0005,
            spawn_cost=0.2,
            ipc_overhead=0.15,
            chunking_overhead=0.08,
            estimated_speedup=1.5,
            physical_cores=8,
            available_memory=4 * 1024**3,
            estimated_memory_per_job=900 * 1024**2,
            coefficient_of_variation=0.6
        )
        
        # All recommendations should be non-empty strings
        assert all(isinstance(rec, str) and len(rec) > 10 for rec in analysis.recommendations)
        
        # Should contain specific suggestions
        all_text = " ".join(analysis.recommendations).lower()
        # At least one of these actionable terms should appear
        actionable_terms = ['increase', 'reduce', 'use', 'consider', 'add', 'change']
        assert any(term in all_text for term in actionable_terms)


class TestBottleneckReportFormatting:
    """Test suite for report formatting."""

    def test_report_has_proper_structure(self):
        """Test that formatted report has expected sections."""
        analysis = BottleneckAnalysis(
            primary_bottleneck=BottleneckType.IPC_OVERHEAD,
            bottleneck_severity=0.25,
            contributing_factors=[],
            recommendations=["Optimize data structures"],
            overhead_breakdown={'computation': 60.0, 'spawn': 10.0, 'ipc': 25.0, 'chunking': 5.0},
            efficiency_score=0.75
        )
        
        report = format_bottleneck_report(analysis)
        lines = report.split('\n')
        
        # Check for section headers
        assert any("PERFORMANCE BOTTLENECK ANALYSIS" in line for line in lines)
        assert any("Overall Efficiency" in line for line in lines)
        assert any("Primary Bottleneck" in line for line in lines)
        assert any("Time Distribution" in line for line in lines)
        assert any("RECOMMENDATIONS" in line for line in lines)

    def test_report_visual_bars(self):
        """Test that report includes visual progress bars."""
        analysis = BottleneckAnalysis(
            primary_bottleneck=BottleneckType.NONE,
            bottleneck_severity=0.0,
            contributing_factors=[],
            recommendations=["All good!"],
            overhead_breakdown={'computation': 80.0, 'spawn': 10.0, 'ipc': 8.0, 'chunking': 2.0},
            efficiency_score=0.95
        )
        
        report = format_bottleneck_report(analysis)
        
        # Should contain progress bars (█ character)
        assert "█" in report

    def test_report_efficiency_status(self):
        """Test efficiency status indicators."""
        # Excellent
        analysis_excellent = BottleneckAnalysis(
            primary_bottleneck=BottleneckType.NONE,
            bottleneck_severity=0.0,
            contributing_factors=[],
            recommendations=[],
            overhead_breakdown={},
            efficiency_score=0.85
        )
        report = format_bottleneck_report(analysis_excellent)
        assert "✅ Excellent" in report or "Excellent" in report
        
        # Good
        analysis_good = BottleneckAnalysis(
            primary_bottleneck=BottleneckType.NONE,
            bottleneck_severity=0.0,
            contributing_factors=[],
            recommendations=[],
            overhead_breakdown={},
            efficiency_score=0.65
        )
        report = format_bottleneck_report(analysis_good)
        assert "Good" in report
        
        # Poor
        analysis_poor = BottleneckAnalysis(
            primary_bottleneck=BottleneckType.SPAWN_OVERHEAD,
            bottleneck_severity=0.5,
            contributing_factors=[],
            recommendations=[],
            overhead_breakdown={},
            efficiency_score=0.3
        )
        report = format_bottleneck_report(analysis_poor)
        assert "Poor" in report
