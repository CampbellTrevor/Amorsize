"""
Integration tests for bottleneck analysis with optimizer.
"""

import pytest
from amorsize import optimize, BottleneckType


def slow_function(x):
    """A simple test function with some computation."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def fast_function(x):
    """A very fast function to demonstrate overhead bottleneck."""
    return x * 2


class TestBottleneckAnalysisIntegration:
    """Integration tests for bottleneck analysis with optimize()."""

    def test_analyze_bottlenecks_method_exists(self):
        """Test that optimize result has analyze_bottlenecks method."""
        result = optimize(slow_function, range(100), profile=True)
        assert hasattr(result, 'analyze_bottlenecks')
        assert callable(result.analyze_bottlenecks)

    def test_analyze_bottlenecks_without_profile_raises_error(self):
        """Test that analyze_bottlenecks requires profile=True."""
        result = optimize(slow_function, range(100), profile=False)
        
        with pytest.raises(ValueError) as exc_info:
            result.analyze_bottlenecks()
        
        assert "diagnostic profiling" in str(exc_info.value).lower()
        assert "profile=True" in str(exc_info.value)

    def test_analyze_bottlenecks_returns_formatted_report(self):
        """Test that analyze_bottlenecks returns a formatted report."""
        result = optimize(slow_function, range(1000), profile=True)
        report = result.analyze_bottlenecks()
        
        # Check report structure
        assert isinstance(report, str)
        assert "PERFORMANCE BOTTLENECK ANALYSIS" in report
        assert "Overall Efficiency" in report
        assert "RECOMMENDATIONS" in report or "Excellent" in report

    def test_bottleneck_report_shows_efficiency_score(self):
        """Test that report includes efficiency score."""
        result = optimize(slow_function, range(1000), profile=True)
        report = result.analyze_bottlenecks()
        
        # Should have efficiency percentage
        assert "%" in report
        assert "Efficiency" in report

    def test_bottleneck_report_shows_overhead_breakdown(self):
        """Test that report includes overhead breakdown."""
        result = optimize(slow_function, range(1000), profile=True)
        report = result.analyze_bottlenecks()
        
        # Should show time distribution
        assert "Time Distribution" in report or "overhead" in report.lower()

    def test_fast_function_shows_overhead_bottleneck(self):
        """Test that very fast functions are identified as having overhead issues."""
        result = optimize(fast_function, range(100), profile=True)
        report = result.analyze_bottlenecks()
        
        # Fast function should have some bottleneck identified
        # (spawn, IPC, chunking, or insufficient computation)
        assert "Bottleneck" in report or "overhead" in report.lower() or "Excellent" in report

    def test_bottleneck_report_provides_recommendations(self):
        """Test that report includes actionable recommendations."""
        result = optimize(slow_function, range(100), profile=True)
        report = result.analyze_bottlenecks()
        
        # Should have recommendations section (even if just "Excellent")
        assert "RECOMMENDATIONS" in report or "excellent" in report.lower()

    def test_bottleneck_analysis_with_large_workload(self):
        """Test bottleneck analysis with a large workload."""
        result = optimize(slow_function, range(10000), profile=True)
        report = result.analyze_bottlenecks()
        
        # Should successfully analyze and report
        assert len(report) > 100  # Should be a substantial report
        assert "=" in report  # Has formatting

    def test_bottleneck_analysis_with_small_workload(self):
        """Test bottleneck analysis with a small workload."""
        result = optimize(slow_function, range(10), profile=True)
        report = result.analyze_bottlenecks()
        
        # Should identify small workload issues
        assert "small" in report.lower() or "Excellent" in report

    def test_import_bottleneck_classes_from_amorsize(self):
        """Test that bottleneck analysis classes can be imported."""
        from amorsize import BottleneckAnalysis, BottleneckType, analyze_bottlenecks, format_bottleneck_report
        
        assert BottleneckAnalysis is not None
        assert BottleneckType is not None
        assert callable(analyze_bottlenecks)
        assert callable(format_bottleneck_report)

    def test_direct_bottleneck_analysis_function(self):
        """Test using analyze_bottlenecks directly."""
        from amorsize import analyze_bottlenecks
        
        analysis = analyze_bottlenecks(
            n_jobs=4,
            chunksize=50,
            total_items=1000,
            avg_execution_time=0.01,
            spawn_cost=0.05,
            ipc_overhead=0.1,
            chunking_overhead=0.02,
            estimated_speedup=3.5,
            physical_cores=4,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
            coefficient_of_variation=0.1
        )
        
        assert analysis is not None
        assert hasattr(analysis, 'primary_bottleneck')
        assert hasattr(analysis, 'efficiency_score')
        assert hasattr(analysis, 'recommendations')

    def test_bottleneck_enum_values(self):
        """Test BottleneckType enum values."""
        assert BottleneckType.SPAWN_OVERHEAD is not None
        assert BottleneckType.IPC_OVERHEAD is not None
        assert BottleneckType.MEMORY_CONSTRAINT is not None
        assert BottleneckType.WORKLOAD_TOO_SMALL is not None
        assert BottleneckType.NONE is not None


class TestBottleneckAnalysisEdgeCases:
    """Test edge cases for bottleneck analysis integration."""

    def test_serial_execution_recommendation(self):
        """Test bottleneck analysis when serial execution is recommended."""
        result = optimize(fast_function, range(10), profile=True)
        
        # Should work even when n_jobs=1
        report = result.analyze_bottlenecks()
        assert isinstance(report, str)
        assert len(report) > 0

    def test_memory_constrained_scenario(self):
        """Test bottleneck analysis with memory constraints."""
        def memory_intensive_func(x):
            # Simulate memory-intensive operation
            return [x] * 1000
        
        result = optimize(memory_intensive_func, range(100), profile=True)
        report = result.analyze_bottlenecks()
        
        # Should identify memory-related issues or show good performance
        assert "memory" in report.lower() or "efficiency" in report.lower()

    def test_heterogeneous_workload(self):
        """Test bottleneck analysis with heterogeneous workload."""
        def variable_func(x):
            # Variable execution time based on input
            iterations = (x % 10) * 100
            result = 0
            for i in range(iterations):
                result += x
            return result
        
        result = optimize(variable_func, range(100), profile=True)
        report = result.analyze_bottlenecks()
        
        # Should work with heterogeneous workloads
        assert isinstance(report, str)
        assert len(report) > 0
