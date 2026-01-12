"""
Property-based tests for bottleneck_analysis module using Hypothesis.

These tests use property-based testing to automatically generate thousands of
edge cases and verify that the bottleneck analysis behaves correctly across
a wide range of inputs.
"""

import pytest
from hypothesis import given, assume, settings, strategies as st
from amorsize.bottleneck_analysis import (
    BottleneckAnalysis,
    BottleneckType,
    analyze_bottlenecks,
    format_bottleneck_report,
    SPAWN_OVERHEAD_THRESHOLD,
    IPC_OVERHEAD_THRESHOLD,
    CHUNKING_OVERHEAD_THRESHOLD,
    MEMORY_USAGE_THRESHOLD,
    MIN_COMPUTATION_TIME_PER_ITEM,
    MIN_TOTAL_WORKLOAD_TIME,
    HETEROGENEOUS_CV_THRESHOLD,
)

# Memory size constants for readability
MB = 1024**2
GB = 1024**3
TB = 1024**4

# Floating point tolerance for percentage sums
PERCENTAGE_SUM_TOLERANCE = 2.0  # Allow 2% error for floating point rounding


# Custom strategies for bottleneck analysis parameters
@st.composite
def bottleneck_params(draw):
    """Generate valid parameters for bottleneck analysis."""
    n_jobs = draw(st.integers(min_value=1, max_value=64))
    chunksize = draw(st.integers(min_value=1, max_value=1000))
    total_items = draw(st.integers(min_value=1, max_value=100000))
    avg_execution_time = draw(st.floats(min_value=0.0, max_value=10.0))
    spawn_cost = draw(st.floats(min_value=0.0, max_value=5.0))
    ipc_overhead = draw(st.floats(min_value=0.0, max_value=5.0))
    chunking_overhead = draw(st.floats(min_value=0.0, max_value=2.0))
    estimated_speedup = draw(st.floats(min_value=1.0, max_value=64.0))
    physical_cores = draw(st.integers(min_value=1, max_value=128))
    available_memory = draw(st.integers(min_value=MB, max_value=TB))
    estimated_memory_per_job = draw(st.integers(min_value=0, max_value=10 * GB))
    coefficient_of_variation = draw(st.floats(min_value=0.0, max_value=3.0))
    
    return {
        'n_jobs': n_jobs,
        'chunksize': chunksize,
        'total_items': total_items,
        'avg_execution_time': avg_execution_time,
        'spawn_cost': spawn_cost,
        'ipc_overhead': ipc_overhead,
        'chunking_overhead': chunking_overhead,
        'estimated_speedup': estimated_speedup,
        'physical_cores': physical_cores,
        'available_memory': available_memory,
        'estimated_memory_per_job': estimated_memory_per_job,
        'coefficient_of_variation': coefficient_of_variation,
    }


@st.composite
def bottleneck_analysis_result(draw):
    """Generate valid BottleneckAnalysis objects."""
    primary_bottleneck = draw(st.sampled_from(list(BottleneckType)))
    bottleneck_severity = draw(st.floats(min_value=0.0, max_value=1.0))
    
    # Generate contributing factors (list of tuples)
    num_factors = draw(st.integers(min_value=0, max_value=5))
    contributing_factors = []
    for _ in range(num_factors):
        factor_type = draw(st.sampled_from(list(BottleneckType)))
        factor_severity = draw(st.floats(min_value=0.0, max_value=1.0))
        contributing_factors.append((factor_type, factor_severity))
    
    # Generate recommendations
    num_recommendations = draw(st.integers(min_value=0, max_value=10))
    recommendations = [draw(st.text(min_size=10, max_size=200)) for _ in range(num_recommendations)]
    
    # Generate overhead breakdown
    overhead_breakdown = {}
    if draw(st.booleans()):
        computation = draw(st.floats(min_value=0.0, max_value=100.0))
        spawn = draw(st.floats(min_value=0.0, max_value=100.0 - computation))
        ipc = draw(st.floats(min_value=0.0, max_value=100.0 - computation - spawn))
        chunking = 100.0 - computation - spawn - ipc
        overhead_breakdown = {
            'computation': computation,
            'spawn': spawn,
            'ipc': ipc,
            'chunking': max(0.0, chunking)
        }
    
    efficiency_score = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return BottleneckAnalysis(
        primary_bottleneck=primary_bottleneck,
        bottleneck_severity=bottleneck_severity,
        contributing_factors=contributing_factors,
        recommendations=recommendations,
        overhead_breakdown=overhead_breakdown,
        efficiency_score=efficiency_score
    )


class TestBottleneckAnalysisInvariants:
    """Test invariants of BottleneckAnalysis objects."""
    
    @given(bottleneck_analysis_result())
    def test_bottleneck_analysis_structure(self, analysis):
        """BottleneckAnalysis objects should have valid structure."""
        assert isinstance(analysis, BottleneckAnalysis)
        assert isinstance(analysis.primary_bottleneck, BottleneckType)
        assert isinstance(analysis.bottleneck_severity, float)
        assert isinstance(analysis.contributing_factors, list)
        assert isinstance(analysis.recommendations, list)
        assert isinstance(analysis.overhead_breakdown, dict)
        assert isinstance(analysis.efficiency_score, float)
    
    @given(bottleneck_analysis_result())
    def test_severity_bounds(self, analysis):
        """Severity should be between 0 and 1."""
        assert 0.0 <= analysis.bottleneck_severity <= 1.0
        for _, severity in analysis.contributing_factors:
            assert 0.0 <= severity <= 1.0
    
    @given(bottleneck_analysis_result())
    def test_efficiency_score_bounds(self, analysis):
        """Efficiency score should be between 0 and 1."""
        assert 0.0 <= analysis.efficiency_score <= 1.0
    
    @given(bottleneck_analysis_result())
    def test_contributing_factors_structure(self, analysis):
        """Contributing factors should be list of tuples."""
        for factor in analysis.contributing_factors:
            assert isinstance(factor, tuple)
            assert len(factor) == 2
            assert isinstance(factor[0], BottleneckType)
            assert isinstance(factor[1], float)


class TestAnalyzeBottlenecksBasicProperties:
    """Test basic properties of analyze_bottlenecks function."""
    
    @given(bottleneck_params())
    def test_returns_bottleneck_analysis(self, params):
        """analyze_bottlenecks should return a BottleneckAnalysis object."""
        analysis = analyze_bottlenecks(**params)
        assert isinstance(analysis, BottleneckAnalysis)
    
    @given(bottleneck_params())
    def test_efficiency_score_in_valid_range(self, params):
        """Efficiency score should always be between 0 and 1."""
        analysis = analyze_bottlenecks(**params)
        assert 0.0 <= analysis.efficiency_score <= 1.0
    
    @given(bottleneck_params())
    def test_bottleneck_severity_in_valid_range(self, params):
        """Bottleneck severity should be between 0 and 1."""
        analysis = analyze_bottlenecks(**params)
        assert 0.0 <= analysis.bottleneck_severity <= 1.0
    
    @given(bottleneck_params())
    def test_recommendations_are_strings(self, params):
        """All recommendations should be non-empty strings."""
        analysis = analyze_bottlenecks(**params)
        assert isinstance(analysis.recommendations, list)
        for rec in analysis.recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0
    
    @given(bottleneck_params())
    def test_overhead_breakdown_percentages(self, params):
        """Overhead breakdown percentages should sum to ~100%."""
        analysis = analyze_bottlenecks(**params)
        if analysis.overhead_breakdown:
            total = sum(analysis.overhead_breakdown.values())
            # Allow some floating point error
            assert 100.0 - PERCENTAGE_SUM_TOLERANCE <= total <= 100.0 + PERCENTAGE_SUM_TOLERANCE or total == 0.0


class TestSpawnOverheadDetection:
    """Test detection of spawn overhead bottleneck."""
    
    @given(
        n_jobs=st.integers(min_value=2, max_value=16),
        chunksize=st.integers(min_value=1, max_value=100),
        total_items=st.integers(min_value=100, max_value=1000),
        avg_execution_time=st.floats(min_value=0.01, max_value=0.1),
        physical_cores=st.integers(min_value=2, max_value=32),
    )
    def test_high_spawn_cost_detected(self, n_jobs, chunksize, total_items, avg_execution_time, physical_cores):
        """High spawn cost should be detected as bottleneck."""
        # Set spawn cost to be very high relative to computation
        total_serial_time = avg_execution_time * total_items
        parallel_compute_time = total_serial_time / n_jobs
        # Make spawn cost at least 30% of parallel time (above 20% threshold)
        spawn_cost = max(0.3 * parallel_compute_time, 0.1)
        
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=avg_execution_time,
            spawn_cost=spawn_cost,
            ipc_overhead=0.01,
            chunking_overhead=0.01,
            estimated_speedup=2.0,
            physical_cores=physical_cores,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
        )
        
        # Spawn overhead should be either primary or contributing bottleneck
        is_primary = analysis.primary_bottleneck == BottleneckType.SPAWN_OVERHEAD
        is_contributing = any(b[0] == BottleneckType.SPAWN_OVERHEAD for b in analysis.contributing_factors)
        assert is_primary or is_contributing
    
    @given(bottleneck_params())
    def test_spawn_overhead_recommendation_format(self, params):
        """Spawn overhead recommendation should contain useful advice."""
        # Force high spawn cost
        params['spawn_cost'] = 1.0
        params['ipc_overhead'] = 0.01
        params['chunking_overhead'] = 0.01
        
        analysis = analyze_bottlenecks(**params)
        
        # If spawn overhead is detected, check recommendation
        if analysis.primary_bottleneck == BottleneckType.SPAWN_OVERHEAD:
            spawn_recs = [r for r in analysis.recommendations if 'spawn' in r.lower()]
            assert len(spawn_recs) > 0
            # Should mention fork or forkserver
            assert any('fork' in r.lower() for r in spawn_recs)


class TestIPCOverheadDetection:
    """Test detection of IPC overhead bottleneck."""
    
    @given(
        n_jobs=st.integers(min_value=2, max_value=16),
        chunksize=st.integers(min_value=10, max_value=100),
        total_items=st.integers(min_value=100, max_value=1000),
        avg_execution_time=st.floats(min_value=0.01, max_value=0.1),
        physical_cores=st.integers(min_value=2, max_value=32),
    )
    def test_high_ipc_overhead_detected(self, n_jobs, chunksize, total_items, avg_execution_time, physical_cores):
        """High IPC overhead should be detected as bottleneck."""
        # Set IPC overhead to be very high
        total_serial_time = avg_execution_time * total_items
        parallel_compute_time = total_serial_time / n_jobs
        # Make IPC overhead at least 20% of parallel time (above 15% threshold)
        ipc_overhead = max(0.2 * parallel_compute_time, 0.1)
        
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=avg_execution_time,
            spawn_cost=0.01,
            ipc_overhead=ipc_overhead,
            chunking_overhead=0.01,
            estimated_speedup=2.0,
            physical_cores=physical_cores,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
        )
        
        # IPC overhead should be either primary or contributing bottleneck
        is_primary = analysis.primary_bottleneck == BottleneckType.IPC_OVERHEAD
        is_contributing = any(b[0] == BottleneckType.IPC_OVERHEAD for b in analysis.contributing_factors)
        assert is_primary or is_contributing
    
    @given(bottleneck_params())
    def test_ipc_overhead_recommendation_format(self, params):
        """IPC overhead recommendation should contain useful advice."""
        # Force high IPC overhead
        params['ipc_overhead'] = 1.0
        params['spawn_cost'] = 0.01
        params['chunking_overhead'] = 0.01
        
        analysis = analyze_bottlenecks(**params)
        
        # If IPC overhead is detected, check recommendation
        if analysis.primary_bottleneck == BottleneckType.IPC_OVERHEAD:
            ipc_recs = [r for r in analysis.recommendations if 'ipc' in r.lower() or 'serialization' in r.lower()]
            assert len(ipc_recs) > 0


class TestChunkingOverheadDetection:
    """Test detection of chunking overhead bottleneck."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=16),
        total_items=st.integers(min_value=1000, max_value=10000),
        avg_execution_time=st.floats(min_value=0.001, max_value=0.01),
        physical_cores=st.integers(min_value=1, max_value=32),
    )
    def test_high_chunking_overhead_detected(self, n_jobs, total_items, avg_execution_time, physical_cores):
        """High chunking overhead should be detected as bottleneck."""
        chunksize = 1  # Very small chunks = high overhead
        total_serial_time = avg_execution_time * total_items
        parallel_compute_time = total_serial_time / n_jobs
        chunking_overhead = parallel_compute_time * 0.2  # 20% of parallel time (above threshold)
        
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=avg_execution_time,
            spawn_cost=0.01,
            ipc_overhead=0.01,
            chunking_overhead=chunking_overhead,
            estimated_speedup=2.0,
            physical_cores=physical_cores,
            available_memory=8 * 1024**3,
            estimated_memory_per_job=100 * 1024**2,
        )
        
        # Chunking overhead should be either primary or contributing bottleneck
        is_primary = analysis.primary_bottleneck == BottleneckType.CHUNKING_OVERHEAD
        is_contributing = any(b[0] == BottleneckType.CHUNKING_OVERHEAD for b in analysis.contributing_factors)
        assert is_primary or is_contributing


class TestMemoryConstraintDetection:
    """Test detection of memory constraint bottleneck."""
    
    @given(
        physical_cores=st.integers(min_value=8, max_value=32),
        chunksize=st.integers(min_value=10, max_value=100),
        total_items=st.integers(min_value=100, max_value=1000),
        avg_execution_time=st.floats(min_value=0.01, max_value=0.1),
    )
    def test_memory_constraint_detected(self, physical_cores, chunksize, total_items, avg_execution_time):
        """Memory constraints should be detected when n_jobs < physical_cores."""
        n_jobs = 4  # Less than physical cores
        available_memory = 4 * 1024**3  # 4 GB
        estimated_memory_per_job = 900 * 1024**2  # 900 MB per job (tight memory)
        memory_usage_ratio = (n_jobs * estimated_memory_per_job) / available_memory
        
        # Only test when memory usage is high enough
        assume(memory_usage_ratio > MEMORY_USAGE_THRESHOLD)
        
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=avg_execution_time,
            spawn_cost=0.01,
            ipc_overhead=0.01,
            chunking_overhead=0.01,
            estimated_speedup=3.5,
            physical_cores=physical_cores,
            available_memory=available_memory,
            estimated_memory_per_job=estimated_memory_per_job,
        )
        
        # Memory constraint should be either primary or contributing bottleneck
        is_primary = analysis.primary_bottleneck == BottleneckType.MEMORY_CONSTRAINT
        is_contributing = any(b[0] == BottleneckType.MEMORY_CONSTRAINT for b in analysis.contributing_factors)
        assert is_primary or is_contributing


class TestWorkloadTooSmallDetection:
    """Test detection of workload too small bottleneck."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=8),
        chunksize=st.integers(min_value=1, max_value=10),
        physical_cores=st.integers(min_value=1, max_value=16),
    )
    def test_small_workload_detected(self, n_jobs, chunksize, physical_cores):
        """Small workloads should be detected as bottleneck."""
        # Create small workload (< 1 second total)
        total_items = 50
        avg_execution_time = 0.01  # 50 * 0.01 = 0.5s total
        
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=avg_execution_time,
            spawn_cost=0.05,
            ipc_overhead=0.05,
            chunking_overhead=0.02,
            estimated_speedup=1.5,
            physical_cores=physical_cores,
            available_memory=8 * GB,
            estimated_memory_per_job=100 * MB,
        )
        
        # Workload too small should be either primary or contributing bottleneck
        is_primary = analysis.primary_bottleneck == BottleneckType.WORKLOAD_TOO_SMALL
        is_contributing = any(b[0] == BottleneckType.WORKLOAD_TOO_SMALL for b in analysis.contributing_factors)
        assert is_primary or is_contributing


class TestInsufficientComputationDetection:
    """Test detection of insufficient computation bottleneck."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=8),
        chunksize=st.integers(min_value=10, max_value=100),
        total_items=st.integers(min_value=1000, max_value=10000),
        physical_cores=st.integers(min_value=1, max_value=16),
    )
    def test_insufficient_computation_detected(self, n_jobs, chunksize, total_items, physical_cores):
        """Very fast tasks should be detected as insufficient computation."""
        avg_execution_time = 0.0001  # 0.1ms per item - very fast
        
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=avg_execution_time,
            spawn_cost=0.05,
            ipc_overhead=0.05,
            chunking_overhead=0.02,
            estimated_speedup=2.0,
            physical_cores=physical_cores,
            available_memory=8 * GB,
            estimated_memory_per_job=100 * MB,
        )
        
        # Insufficient computation should be either primary or contributing bottleneck
        is_primary = analysis.primary_bottleneck == BottleneckType.INSUFFICIENT_COMPUTATION
        is_contributing = any(b[0] == BottleneckType.INSUFFICIENT_COMPUTATION for b in analysis.contributing_factors)
        assert is_primary or is_contributing


class TestHeterogeneousWorkloadDetection:
    """Test detection of heterogeneous workload bottleneck."""
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=8),
        chunksize=st.integers(min_value=10, max_value=100),
        total_items=st.integers(min_value=100, max_value=1000),
        avg_execution_time=st.floats(min_value=0.01, max_value=0.1),
        physical_cores=st.integers(min_value=1, max_value=16),
    )
    def test_heterogeneous_workload_detected(self, n_jobs, chunksize, total_items, avg_execution_time, physical_cores):
        """High coefficient of variation should be detected as heterogeneous workload."""
        coefficient_of_variation = 0.8  # High variability
        
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=avg_execution_time,
            spawn_cost=0.05,
            ipc_overhead=0.05,
            chunking_overhead=0.02,
            estimated_speedup=3.0,
            physical_cores=physical_cores,
            available_memory=8 * GB,
            estimated_memory_per_job=100 * MB,
            coefficient_of_variation=coefficient_of_variation,
        )
        
        # Heterogeneous workload should be either primary or contributing bottleneck
        is_primary = analysis.primary_bottleneck == BottleneckType.HETEROGENEOUS_WORKLOAD
        is_contributing = any(b[0] == BottleneckType.HETEROGENEOUS_WORKLOAD for b in analysis.contributing_factors)
        assert is_primary or is_contributing
    
    @given(bottleneck_params())
    def test_low_cv_no_heterogeneous_detection(self, params):
        """Low coefficient of variation should not trigger heterogeneous detection."""
        params['coefficient_of_variation'] = 0.1  # Low variability
        
        analysis = analyze_bottlenecks(**params)
        
        # Heterogeneous workload should not be detected
        is_primary = analysis.primary_bottleneck == BottleneckType.HETEROGENEOUS_WORKLOAD
        is_contributing = any(b[0] == BottleneckType.HETEROGENEOUS_WORKLOAD for b in analysis.contributing_factors)
        assert not (is_primary or is_contributing)


class TestPrimaryBottleneckSelection:
    """Test that primary bottleneck is always the most severe."""
    
    @given(bottleneck_params())
    def test_primary_is_most_severe(self, params):
        """Primary bottleneck should have highest severity among all bottlenecks."""
        analysis = analyze_bottlenecks(**params)
        
        if analysis.primary_bottleneck != BottleneckType.NONE:
            # Primary bottleneck severity should be >= all contributing factors
            for _, severity in analysis.contributing_factors:
                assert analysis.bottleneck_severity >= severity
    
    @given(bottleneck_params())
    def test_no_bottleneck_when_efficient(self, params):
        """High efficiency should result in no bottleneck or positive recommendations."""
        # Force high efficiency conditions
        n_jobs = min(params['n_jobs'], params['physical_cores'])
        params['n_jobs'] = max(2, n_jobs)  # At least 2 jobs
        params['physical_cores'] = max(2, params['physical_cores'])  # At least 2 cores
        params['estimated_speedup'] = float(min(params['n_jobs'], params['physical_cores'])) * 0.95
        params['spawn_cost'] = 0.001
        params['ipc_overhead'] = 0.001
        params['chunking_overhead'] = 0.001
        params['avg_execution_time'] = 0.1
        params['total_items'] = 1000
        params['coefficient_of_variation'] = 0.1
        params['estimated_memory_per_job'] = 100 * MB
        params['available_memory'] = 8 * GB
        
        analysis = analyze_bottlenecks(**params)
        
        # Should have high efficiency
        if analysis.efficiency_score > 0.8:
            # Should have at least one recommendation
            assert len(analysis.recommendations) > 0
            # May still have contributing factors, but should note excellence or be good
            assert any('excellent' in rec.lower() or 'good' in rec.lower() or '✅' in rec
                      for rec in analysis.recommendations)


class TestOverheadBreakdownProperties:
    """Test overhead breakdown calculation properties."""
    
    @given(bottleneck_params())
    def test_overhead_breakdown_components(self, params):
        """Overhead breakdown should contain all expected components."""
        analysis = analyze_bottlenecks(**params)
        
        if analysis.overhead_breakdown:
            assert 'computation' in analysis.overhead_breakdown
            assert 'spawn' in analysis.overhead_breakdown
            assert 'ipc' in analysis.overhead_breakdown
            assert 'chunking' in analysis.overhead_breakdown
    
    @given(bottleneck_params())
    def test_overhead_breakdown_non_negative(self, params):
        """All overhead breakdown percentages should be non-negative."""
        analysis = analyze_bottlenecks(**params)
        
        for component, percentage in analysis.overhead_breakdown.items():
            assert percentage >= 0.0
    
    @given(bottleneck_params())
    def test_overhead_breakdown_reasonable_range(self, params):
        """Each overhead breakdown component should be <= 100%."""
        analysis = analyze_bottlenecks(**params)
        
        for component, percentage in analysis.overhead_breakdown.items():
            assert percentage <= 100.0


class TestFormatBottleneckReport:
    """Test bottleneck report formatting."""
    
    @given(bottleneck_analysis_result())
    def test_report_is_string(self, analysis):
        """format_bottleneck_report should return a string."""
        report = format_bottleneck_report(analysis)
        assert isinstance(report, str)
    
    @given(bottleneck_analysis_result())
    def test_report_contains_header(self, analysis):
        """Report should contain the header."""
        report = format_bottleneck_report(analysis)
        assert "PERFORMANCE BOTTLENECK ANALYSIS" in report
    
    @given(bottleneck_analysis_result())
    def test_report_contains_efficiency(self, analysis):
        """Report should display efficiency score."""
        report = format_bottleneck_report(analysis)
        assert "Overall Efficiency" in report
        efficiency_str = f"{analysis.efficiency_score*100:.1f}%"
        assert efficiency_str in report
    
    @given(bottleneck_analysis_result())
    def test_report_contains_recommendations(self, analysis):
        """Report should include recommendations section if present."""
        report = format_bottleneck_report(analysis)
        if analysis.recommendations:
            assert "RECOMMENDATIONS:" in report
    
    @given(bottleneck_analysis_result())
    def test_report_length_reasonable(self, analysis):
        """Report should be a reasonable length."""
        report = format_bottleneck_report(analysis)
        # Should have some content
        assert len(report) > 100
        # But not be excessively long
        assert len(report) < 50000


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_all_zeros(self):
        """Test with minimal valid values."""
        analysis = analyze_bottlenecks(
            n_jobs=1,  # Minimum valid n_jobs
            chunksize=1,
            total_items=1,  # Minimum valid items
            avg_execution_time=0.0,
            spawn_cost=0.0,
            ipc_overhead=0.0,
            chunking_overhead=0.0,
            estimated_speedup=1.0,
            physical_cores=1,
            available_memory=GB,
            estimated_memory_per_job=0,
        )
        
        assert isinstance(analysis, BottleneckAnalysis)
        assert 0.0 <= analysis.efficiency_score <= 1.0
        assert 0.0 <= analysis.bottleneck_severity <= 1.0
    
    @given(
        n_jobs=st.integers(min_value=1, max_value=1000),
        physical_cores=st.integers(min_value=1, max_value=128),
        available_memory=st.integers(min_value=1024**2, max_value=1024**4),
    )
    def test_extreme_values(self, n_jobs, physical_cores, available_memory):
        """Test with extreme parameter values."""
        analysis = analyze_bottlenecks(
            n_jobs=n_jobs,
            chunksize=1,
            total_items=1000000,
            avg_execution_time=10.0,
            spawn_cost=100.0,
            ipc_overhead=200.0,
            chunking_overhead=50.0,
            estimated_speedup=1.01,
            physical_cores=physical_cores,
            available_memory=available_memory,
            estimated_memory_per_job=available_memory * 2,  # More than available!
        )
        
        # Should not crash
        assert isinstance(analysis, BottleneckAnalysis)
        assert analysis.bottleneck_severity >= 0.0
    
    @given(
        chunksize=st.integers(min_value=1, max_value=10),
        total_items=st.integers(min_value=1, max_value=100),
    )
    def test_single_worker(self, chunksize, total_items):
        """Test with single worker (no parallelism)."""
        analysis = analyze_bottlenecks(
            n_jobs=1,
            chunksize=chunksize,
            total_items=total_items,
            avg_execution_time=0.01,
            spawn_cost=0.0,
            ipc_overhead=0.0,
            chunking_overhead=0.0,
            estimated_speedup=1.0,
            physical_cores=1,
            available_memory=GB,
            estimated_memory_per_job=100 * MB,
        )
        
        assert isinstance(analysis, BottleneckAnalysis)
        # Efficiency should be perfect for single worker
        assert analysis.efficiency_score == 1.0


class TestIntegrationProperties:
    """Test integration between different components."""
    
    @given(bottleneck_params())
    def test_complete_analysis_workflow(self, params):
        """Test complete analysis and formatting workflow."""
        # Run analysis
        analysis = analyze_bottlenecks(**params)
        
        # Verify analysis structure
        assert isinstance(analysis, BottleneckAnalysis)
        assert isinstance(analysis.primary_bottleneck, BottleneckType)
        
        # Format report
        report = format_bottleneck_report(analysis)
        
        # Verify report structure
        assert isinstance(report, str)
        assert len(report) > 0
        assert "PERFORMANCE BOTTLENECK ANALYSIS" in report
    
    @given(bottleneck_params())
    def test_recommendations_match_bottlenecks(self, params):
        """Recommendations should be relevant to detected bottlenecks."""
        analysis = analyze_bottlenecks(**params)
        
        if analysis.primary_bottleneck != BottleneckType.NONE:
            # Should have at least one recommendation
            assert len(analysis.recommendations) > 0
            
            # Recommendation should be relevant to the bottleneck
            bottleneck_name = analysis.primary_bottleneck.value
            all_recs = " ".join(analysis.recommendations).lower()
            
            # For certain bottlenecks, check for specific keywords
            if analysis.primary_bottleneck == BottleneckType.SPAWN_OVERHEAD:
                assert 'spawn' in all_recs or 'fork' in all_recs
            elif analysis.primary_bottleneck == BottleneckType.MEMORY_CONSTRAINT:
                assert 'memory' in all_recs or 'ram' in all_recs
