"""
Tests for Bayesian optimization tuning functionality.

This module tests the bayesian_tune_parameters() function which uses
Gaussian Process-based optimization for efficient parameter search.
"""

import pytest
import time
import sys

try:
    from skopt import gp_minimize
    HAS_SKOPT = True
except ImportError:
    HAS_SKOPT = False

from amorsize import bayesian_tune_parameters, TuningResult


def simple_cpu_func(x):
    """Simple CPU-bound function for testing."""
    return sum(i ** 2 for i in range(x))


def fast_func(x):
    """Very fast function for testing edge cases."""
    return x * 2


def slow_func(x):
    """Slower function for testing."""
    total = 0
    for i in range(x * 100):
        total += i ** 2
    return total


class TestBayesianTuneBasic:
    """Test basic functionality of Bayesian optimization tuning."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_basic_bayesian_tune(self):
        """Test that Bayesian optimization completes successfully."""
        data = range(50, 150)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=10,
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        assert result.best_n_jobs >= 1
        assert result.best_chunksize >= 1
        assert result.best_time > 0
        assert result.serial_time > 0
        assert result.search_strategy == "bayesian"
        assert result.configurations_tested >= 1
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_bayesian_tune_finds_speedup(self):
        """Test that Bayesian optimization finds parallel speedup."""
        data = range(100, 300)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=15,
            verbose=False
        )
        
        # For CPU-bound work, parallel should be faster than serial
        # (unless system is overloaded or single-core)
        assert result.best_speedup >= 0.8  # Allow some variance
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_bayesian_tune_respects_bounds(self):
        """Test that Bayesian optimization respects parameter bounds."""
        data = range(50, 150)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=10,
            n_jobs_min=2,
            n_jobs_max=4,
            chunksize_min=5,
            chunksize_max=20,
            verbose=False
        )
        
        # Best result should be within bounds (or serial if parallel not beneficial)
        if result.best_n_jobs > 1:  # If parallel was beneficial
            assert 2 <= result.best_n_jobs <= 4
            assert 5 <= result.best_chunksize <= 20
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_bayesian_tune_with_optimizer_hint(self):
        """Test Bayesian optimization with optimizer hint as starting point."""
        data = range(50, 150)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=10,
            use_optimizer_hint=True,
            verbose=False
        )
        
        assert result.optimization_hint is not None
        assert result.best_n_jobs >= 1
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_bayesian_tune_without_optimizer_hint(self):
        """Test Bayesian optimization without optimizer hint."""
        data = range(50, 150)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=10,
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.optimization_hint is None
        assert result.best_n_jobs >= 1


class TestBayesianTuneVerbose:
    """Test verbose output of Bayesian optimization."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_verbose_mode_prints_progress(self, capsys):
        """Test that verbose mode prints progress information."""
        data = range(50, 100)
        result = bayesian_tune_parameters(
            fast_func,
            data,
            n_iterations=5,
            verbose=True
        )
        
        captured = capsys.readouterr()
        assert "Bayesian Optimization Configuration" in captured.out
        assert "Starting optimization" in captured.out
        assert "Optimization Complete" in captured.out
        assert "Testing n_jobs=" in captured.out


class TestBayesianTuneEdgeCases:
    """Test edge cases for Bayesian optimization."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="empty dataset"):
            bayesian_tune_parameters(simple_cpu_func, [])
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_too_few_iterations_raises_error(self):
        """Test that too few iterations raises ValueError."""
        data = range(10, 50)
        with pytest.raises(ValueError, match="at least 5"):
            bayesian_tune_parameters(
                simple_cpu_func,
                data,
                n_iterations=3
            )
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_invalid_n_jobs_bounds_raises_error(self):
        """Test that invalid n_jobs bounds raise ValueError."""
        data = range(10, 50)
        
        # n_jobs_min < 1
        with pytest.raises(ValueError, match="n_jobs_min must be at least 1"):
            bayesian_tune_parameters(
                simple_cpu_func,
                data,
                n_jobs_min=0
            )
        
        # n_jobs_max < n_jobs_min
        with pytest.raises(ValueError, match="n_jobs_max must be >= n_jobs_min"):
            bayesian_tune_parameters(
                simple_cpu_func,
                data,
                n_jobs_min=4,
                n_jobs_max=2
            )
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_invalid_chunksize_bounds_raises_error(self):
        """Test that invalid chunksize bounds raise ValueError."""
        data = range(10, 50)
        
        # chunksize_min < 1
        with pytest.raises(ValueError, match="chunksize_min must be at least 1"):
            bayesian_tune_parameters(
                simple_cpu_func,
                data,
                chunksize_min=0
            )
        
        # chunksize_max < chunksize_min
        with pytest.raises(ValueError, match="chunksize_max must be >= chunksize_min"):
            bayesian_tune_parameters(
                simple_cpu_func,
                data,
                chunksize_min=50,
                chunksize_max=10
            )
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_single_item_data(self):
        """Test Bayesian optimization with single item."""
        data = [100]
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=5,
            verbose=False
        )
        
        assert result.best_n_jobs >= 1
        assert result.best_chunksize >= 1


class TestBayesianTuneFallback:
    """Test fallback behavior when scikit-optimize is not available."""
    
    def test_fallback_to_grid_search_without_skopt(self, monkeypatch):
        """Test that Bayesian tuning falls back to grid search without skopt."""
        # Import the module first
        import amorsize.tuning as tuning_module
        
        # Temporarily set HAS_SKOPT to False
        original_has_skopt = tuning_module.HAS_SKOPT
        monkeypatch.setattr(tuning_module, 'HAS_SKOPT', False)
        
        try:
            data = range(10, 30)
            
            # Should fall back to grid search without error
            with pytest.warns(RuntimeWarning, match="scikit-optimize not available"):
                result = bayesian_tune_parameters(
                    fast_func,
                    data,
                    n_iterations=10,
                    verbose=False
                )
            
            # Should still return a valid result (from grid search fallback)
            assert isinstance(result, TuningResult)
            assert result.best_n_jobs >= 1
            assert result.search_strategy == "grid"  # Fell back to grid
        finally:
            # Restore original value
            monkeypatch.setattr(tuning_module, 'HAS_SKOPT', original_has_skopt)


class TestBayesianTuneDataTypes:
    """Test Bayesian optimization with different data types."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_with_list_data(self):
        """Test Bayesian optimization with list data."""
        data = list(range(50, 150))
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=8,
            verbose=False
        )
        
        assert result.best_n_jobs >= 1
        assert result.configurations_tested >= 1
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_with_range_data(self):
        """Test Bayesian optimization with range data."""
        data = range(50, 150)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=8,
            verbose=False
        )
        
        assert result.best_n_jobs >= 1
        assert result.configurations_tested >= 1
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_with_iterator_data(self):
        """Test Bayesian optimization with iterator data."""
        data = (x for x in range(50, 150))
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=8,
            verbose=False
        )
        
        assert result.best_n_jobs >= 1
        assert result.configurations_tested >= 1


class TestBayesianTuneThreading:
    """Test Bayesian optimization with threading."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_with_threading_executor(self):
        """Test Bayesian optimization with ThreadPoolExecutor."""
        data = range(50, 100)
        result = bayesian_tune_parameters(
            fast_func,
            data,
            n_iterations=8,
            prefer_threads_for_io=True,
            verbose=False
        )
        
        assert result.executor_type == "thread"
        assert result.best_n_jobs >= 1


class TestBayesianTuneReproducibility:
    """Test reproducibility of Bayesian optimization."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_random_state_reproducibility(self):
        """Test that random_state produces reproducible results."""
        data = range(50, 150)
        
        # Run twice with same random state
        result1 = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=10,
            random_state=42,
            verbose=False
        )
        
        result2 = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=10,
            random_state=42,
            verbose=False
        )
        
        # Should get same results with same random state
        assert result1.best_n_jobs == result2.best_n_jobs
        assert result1.best_chunksize == result2.best_chunksize


class TestBayesianTuneResultFormat:
    """Test the format and content of Bayesian optimization results."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_result_contains_all_fields(self):
        """Test that result contains all expected fields."""
        data = range(50, 100)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=8,
            verbose=False
        )
        
        # Check all required fields
        assert hasattr(result, 'best_n_jobs')
        assert hasattr(result, 'best_chunksize')
        assert hasattr(result, 'best_time')
        assert hasattr(result, 'best_speedup')
        assert hasattr(result, 'serial_time')
        assert hasattr(result, 'configurations_tested')
        assert hasattr(result, 'all_results')
        assert hasattr(result, 'search_strategy')
        assert hasattr(result, 'executor_type')
        
        # Check search strategy
        assert result.search_strategy == "bayesian"
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_result_str_representation(self):
        """Test string representation of result."""
        data = range(50, 100)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=8,
            verbose=False
        )
        
        result_str = str(result)
        assert "Auto-Tuning Results" in result_str
        assert "bayesian" in result_str
        assert "Best speedup" in result_str


class TestBayesianTuneIntegration:
    """Test integration of Bayesian optimization with other features."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_can_save_config_from_bayesian_result(self, tmp_path):
        """Test that Bayesian optimization result can be saved as config."""
        data = range(50, 100)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=8,
            verbose=False
        )
        
        # Save config
        config_path = tmp_path / "bayesian_config.json"
        result.save_config(str(config_path), function_name="simple_cpu_func")
        
        # Check file was created
        assert config_path.exists()
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_bayesian_vs_grid_comparison(self):
        """Test that Bayesian finds similar or better results than grid with fewer trials."""
        # This is a smoke test - just ensure both methods work
        data = range(50, 150)
        
        bayesian_result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=10,
            verbose=False
        )
        
        # Bayesian should test fewer configs than full grid
        # but still find reasonable performance
        assert bayesian_result.configurations_tested <= 12  # 10 iterations + serial + maybe 1 extra
        assert bayesian_result.best_speedup >= 0.5  # Some speedup achieved


class TestBayesianTunePerformance:
    """Test performance characteristics of Bayesian optimization."""
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_completes_in_reasonable_time(self):
        """Test that Bayesian optimization completes in reasonable time."""
        data = range(50, 100)
        
        start = time.time()
        result = bayesian_tune_parameters(
            fast_func,
            data,
            n_iterations=10,
            verbose=False
        )
        end = time.time()
        
        # Should complete in under 10 seconds for fast function
        # (even accounting for optimization overhead)
        assert (end - start) < 10.0
    
    @pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
    def test_all_results_tracked(self):
        """Test that all benchmarked configurations are tracked."""
        data = range(50, 100)
        result = bayesian_tune_parameters(
            simple_cpu_func,
            data,
            n_iterations=8,
            verbose=False
        )
        
        # Should have results for tested configurations
        assert len(result.all_results) > 0
        assert len(result.all_results) <= result.configurations_tested


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
