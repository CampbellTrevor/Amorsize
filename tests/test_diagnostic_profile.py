"""
Tests for diagnostic profiling functionality.
"""

import pytest
from amorsize import optimize
from amorsize.optimizer import DiagnosticProfile


def slow_function(x):
    """A moderately expensive function for testing."""
    result = 0
    for i in range(5000):
        result += x ** 2
    return result


def fast_function(x):
    """A very fast function for testing."""
    return x * 2


def large_return_function(x):
    """Function that returns a large object."""
    return [x] * 10000


class TestDiagnosticProfileClass:
    """Test the DiagnosticProfile class directly."""
    
    def test_diagnostic_profile_initialization(self):
        """Test that DiagnosticProfile initializes with sensible defaults."""
        diag = DiagnosticProfile()
        
        assert diag.avg_execution_time == 0.0
        assert diag.physical_cores == 1
        assert diag.optimal_chunksize == 1
        assert diag.estimated_speedup == 1.0
        assert diag.rejection_reasons == []
        assert diag.constraints == []
        assert diag.recommendations == []
    
    def test_format_time(self):
        """Test time formatting utility."""
        diag = DiagnosticProfile()
        
        assert "μs" in diag.format_time(0.0001)
        assert "ms" in diag.format_time(0.05)
        assert "s" in diag.format_time(2.5)
    
    def test_format_bytes(self):
        """Test bytes formatting utility."""
        diag = DiagnosticProfile()
        
        assert "B" in diag.format_bytes(100)
        assert "KB" in diag.format_bytes(2048)
        assert "MB" in diag.format_bytes(5 * 1024 * 1024)
        assert "GB" in diag.format_bytes(3 * 1024 * 1024 * 1024)
    
    def test_overhead_breakdown(self):
        """Test overhead breakdown calculation."""
        diag = DiagnosticProfile()
        diag.overhead_spawn = 0.1
        diag.overhead_ipc = 0.2
        diag.overhead_chunking = 0.3
        
        breakdown = diag.get_overhead_breakdown()
        
        assert "spawn" in breakdown
        assert "ipc" in breakdown
        assert "chunking" in breakdown
        
        # Check percentages add up to ~100
        total = breakdown["spawn"] + breakdown["ipc"] + breakdown["chunking"]
        assert abs(total - 100.0) < 0.1
    
    def test_overhead_breakdown_zero(self):
        """Test overhead breakdown with zero overhead."""
        diag = DiagnosticProfile()
        diag.overhead_spawn = 0.0
        diag.overhead_ipc = 0.0
        diag.overhead_chunking = 0.0
        
        breakdown = diag.get_overhead_breakdown()
        
        assert breakdown["spawn"] == 0.0
        assert breakdown["ipc"] == 0.0
        assert breakdown["chunking"] == 0.0
    
    def test_explain_decision_basic(self):
        """Test that explain_decision returns a formatted string."""
        diag = DiagnosticProfile()
        diag.avg_execution_time = 0.01
        diag.physical_cores = 4
        diag.estimated_speedup = 2.5
        
        explanation = diag.explain_decision()
        
        assert "AMORSIZE DIAGNOSTIC PROFILE" in explanation
        assert "WORKLOAD ANALYSIS" in explanation
        assert "SYSTEM RESOURCES" in explanation
        assert "OPTIMIZATION DECISION" in explanation
        assert isinstance(explanation, str)
        assert len(explanation) > 100


class TestOptimizeWithProfiling:
    """Test the optimize() function with profiling enabled."""
    
    def test_profile_disabled_by_default(self):
        """Test that profiling is disabled by default."""
        data = range(50)
        result = optimize(slow_function, data, sample_size=3)
        
        assert result.profile is None
    
    def test_profile_enabled(self):
        """Test that profiling can be enabled."""
        data = range(50)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        assert result.profile is not None
        assert isinstance(result.profile, DiagnosticProfile)
    
    def test_profile_captures_sampling_data(self):
        """Test that profile captures sampling results."""
        data = range(50)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        assert result.profile.avg_execution_time > 0
        assert result.profile.return_size_bytes > 0
        assert result.profile.sample_count == 3
        assert result.profile.is_picklable is True
    
    def test_profile_captures_system_info(self):
        """Test that profile captures system information."""
        data = range(50)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        assert result.profile.physical_cores > 0
        assert result.profile.logical_cores > 0
        assert result.profile.spawn_cost > 0
        assert result.profile.chunking_overhead > 0
        assert result.profile.available_memory > 0
        assert len(result.profile.multiprocessing_start_method) > 0
    
    def test_profile_captures_workload_characteristics(self):
        """Test that profile captures workload characteristics."""
        data = range(100)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        assert result.profile.total_items == 100
        assert result.profile.estimated_serial_time > 0
        assert result.profile.optimal_chunksize > 0
    
    def test_profile_captures_speedup_analysis(self):
        """Test that profile captures speedup analysis."""
        data = range(100)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        # Should have speedup analysis
        assert result.profile.theoretical_max_speedup >= 1.0
        assert result.profile.estimated_speedup >= 1.0
        assert 0.0 <= result.profile.speedup_efficiency <= 1.0
    
    def test_profile_with_fast_function_rejection(self):
        """Test that profile captures rejection reasons for fast functions."""
        data = range(100)
        result = optimize(fast_function, data, sample_size=3, profile=True)
        
        assert result.n_jobs == 1
        assert len(result.profile.rejection_reasons) > 0
        assert any("fast" in reason.lower() or "1ms" in reason 
                  for reason in result.profile.rejection_reasons)
    
    def test_profile_with_memory_constraints(self):
        """Test that profile captures memory constraints."""
        data = range(1000)
        result = optimize(large_return_function, data, sample_size=3, profile=True)
        
        # Should capture memory information
        assert result.profile.estimated_result_memory > 0
        
        # Might have memory constraint warnings
        if result.profile.estimated_result_memory > result.profile.available_memory * 0.5:
            assert len(result.profile.constraints) > 0 or len(result.profile.recommendations) > 0
    
    def test_profile_with_successful_parallelization(self):
        """Test profile when parallelization is recommended."""
        # Use large dataset and slow function to ensure parallelization
        data = range(500)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        # Depending on system, might recommend parallelization
        if result.n_jobs > 1:
            assert result.profile.estimated_speedup > 1.0
            assert result.profile.overhead_spawn >= 0
            assert result.profile.overhead_ipc >= 0
            assert result.profile.overhead_chunking >= 0
            assert result.profile.parallel_compute_time > 0
    
    def test_profile_overhead_breakdown(self):
        """Test that overhead breakdown is populated."""
        data = range(200)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        if result.n_jobs > 1:
            breakdown = result.profile.get_overhead_breakdown()
            assert "spawn" in breakdown
            assert "ipc" in breakdown
            assert "chunking" in breakdown


class TestExplainMethod:
    """Test the explain() method on OptimizationResult."""
    
    def test_explain_without_profile(self):
        """Test explain() when profiling is disabled."""
        data = range(50)
        result = optimize(slow_function, data, sample_size=3, profile=False)
        
        explanation = result.explain()
        assert "not enabled" in explanation.lower()
        assert "profile=True" in explanation
    
    def test_explain_with_profile(self):
        """Test explain() when profiling is enabled."""
        data = range(50)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        explanation = result.explain()
        
        # Should contain key sections
        assert "WORKLOAD ANALYSIS" in explanation
        assert "SYSTEM RESOURCES" in explanation
        assert "OPTIMIZATION DECISION" in explanation
        assert "Physical CPU cores" in explanation
        assert "Function execution time" in explanation
    
    def test_explain_shows_rejection_reasons(self):
        """Test that explain() shows rejection reasons."""
        data = range(50)
        result = optimize(fast_function, data, sample_size=3, profile=True)
        
        explanation = result.explain()
        
        # Fast function should be rejected
        if result.n_jobs == 1:
            assert "REJECTION REASONS" in explanation
    
    def test_explain_shows_recommendations(self):
        """Test that explain() shows recommendations when available."""
        data = range(200)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        explanation = result.explain()
        
        # Should have some recommendations
        if len(result.profile.recommendations) > 0:
            assert "RECOMMENDATIONS" in explanation
    
    def test_explain_is_comprehensive(self):
        """Test that explain() provides comprehensive information."""
        data = range(100)
        result = optimize(slow_function, data, sample_size=3, profile=True)
        
        explanation = result.explain()
        
        # Check for expected data points
        assert "execution time" in explanation.lower()
        assert "cores" in explanation.lower()
        assert "speedup" in explanation.lower() or "serial" in explanation.lower()
        assert len(explanation) > 500  # Should be detailed


class TestProfileWithGenerators:
    """Test profiling with generator inputs."""
    
    def test_profile_with_generator(self):
        """Test that profiling works with generators."""
        def gen():
            for i in range(100):
                yield i
        
        result = optimize(slow_function, gen(), sample_size=3, profile=True)
        
        assert result.profile is not None
        # Generators don't have known size
        assert result.profile.total_items == -1 or result.profile.total_items == 0
    
    def test_profile_generator_constraint(self):
        """Test that generator size constraint is noted."""
        def gen():
            for i in range(100):
                yield i
        
        result = optimize(slow_function, gen(), sample_size=3, profile=True)
        
        # Should have a constraint about unknown size
        if result.profile.total_items <= 0:
            constraints_text = " ".join(result.profile.constraints)
            assert "generator" in constraints_text.lower() or "unknown" in constraints_text.lower()


class TestProfileVerboseInteraction:
    """Test interaction between profile and verbose modes."""
    
    def test_profile_and_verbose_together(self):
        """Test that profile and verbose modes work together."""
        data = range(50)
        
        # Should not raise any errors
        result = optimize(slow_function, data, sample_size=3, 
                        profile=True, verbose=True)
        
        assert result.profile is not None
        assert result.profile.avg_execution_time > 0
    
    def test_profile_without_verbose(self):
        """Test that profile works without verbose mode."""
        data = range(50)
        
        result = optimize(slow_function, data, sample_size=3, 
                        profile=True, verbose=False)
        
        assert result.profile is not None
        # All diagnostic data should still be captured
        assert result.profile.physical_cores > 0
        assert result.profile.avg_execution_time > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
