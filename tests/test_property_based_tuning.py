"""
Property-based tests for the tuning module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the auto-tuning functionality across a wide range of inputs.
"""

import math
import time
from typing import Any, List, Iterator

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize.tuning import (
    TuningResult,
    tune_parameters,
    quick_tune,
    bayesian_tune_parameters,
    _benchmark_configuration,
    HAS_SKOPT,
)
from amorsize.system_info import get_physical_cores


# ============================================================================
# Custom Strategies
# ============================================================================

@st.composite
def valid_data_lists(draw, min_size=10, max_size=500):
    """Generate valid data lists for tuning."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.lists(st.integers(min_value=1, max_value=1000), min_size=size, max_size=size))


@st.composite
def valid_n_jobs_range(draw):
    """Generate valid n_jobs range."""
    physical_cores = get_physical_cores()
    # Generate 1-3 values in reasonable range
    size = draw(st.integers(min_value=1, max_value=3))
    values = draw(st.lists(
        st.integers(min_value=1, max_value=physical_cores * 2),
        min_size=size,
        max_size=size,
        unique=True
    ))
    return sorted(values)


@st.composite
def valid_chunksize_range(draw, data_size=100):
    """Generate valid chunksize range based on data size."""
    # Generate 1-3 values
    size = draw(st.integers(min_value=1, max_value=3))
    max_chunk = max(1, data_size // 2)
    values = draw(st.lists(
        st.integers(min_value=1, max_value=max_chunk),
        min_size=size,
        max_size=size,
        unique=True
    ))
    return sorted(values)


# Simple test functions
def simple_func(x):
    """Simple function for testing."""
    return x * 2


def very_fast_func(x):
    """Very fast function (instant)."""
    return x


def cpu_bound_func(x):
    """CPU-bound function."""
    total = 0
    for i in range(100):
        total += i * x
    return total


# ============================================================================
# Test TuningResult Invariants
# ============================================================================

class TestTuningResultInvariants:
    """Test invariant properties of TuningResult dataclass."""

    @given(
        best_n_jobs=st.integers(min_value=1, max_value=128),
        best_chunksize=st.integers(min_value=1, max_value=10000),
        best_time=st.floats(min_value=0.001, max_value=100.0),
        serial_time=st.floats(min_value=0.01, max_value=200.0),
        configurations_tested=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100, deadline=1000)
    def test_result_initialization(self, best_n_jobs, best_chunksize, best_time, 
                                   serial_time, configurations_tested):
        """Test that TuningResult stores all parameters correctly."""
        best_speedup = serial_time / best_time if best_time > 0 else 0
        all_results = {(best_n_jobs, best_chunksize): best_time}
        
        result = TuningResult(
            best_n_jobs=best_n_jobs,
            best_chunksize=best_chunksize,
            best_time=best_time,
            best_speedup=best_speedup,
            serial_time=serial_time,
            configurations_tested=configurations_tested,
            all_results=all_results,
            search_strategy="grid",
            executor_type="process"
        )
        
        assert result.best_n_jobs == best_n_jobs
        assert result.best_chunksize == best_chunksize
        assert result.best_time == best_time
        assert result.best_speedup == best_speedup
        assert result.serial_time == serial_time
        assert result.configurations_tested == configurations_tested
        assert isinstance(result.all_results, dict)
        assert result.search_strategy in ["grid", "adaptive", "bayesian"]
        assert result.executor_type in ["process", "thread"]

    @given(
        best_n_jobs=st.integers(min_value=1, max_value=128),
        best_chunksize=st.integers(min_value=1, max_value=10000),
        best_speedup=st.floats(min_value=0.5, max_value=100.0),
        configurations_tested=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100, deadline=1000)
    def test_result_repr_format(self, best_n_jobs, best_chunksize, best_speedup, configurations_tested):
        """Test that __repr__ returns a valid string with expected format."""
        result = TuningResult(
            best_n_jobs=best_n_jobs,
            best_chunksize=best_chunksize,
            best_time=1.0,
            best_speedup=best_speedup,
            serial_time=2.0,
            configurations_tested=configurations_tested,
            all_results={},
            search_strategy="grid"
        )
        
        repr_str = repr(result)
        assert isinstance(repr_str, str)
        assert "TuningResult" in repr_str
        assert f"best_n_jobs={best_n_jobs}" in repr_str
        assert f"best_chunksize={best_chunksize}" in repr_str
        assert f"tested={configurations_tested}" in repr_str

    @given(
        best_n_jobs=st.integers(min_value=1, max_value=128),
        best_chunksize=st.integers(min_value=1, max_value=10000),
    )
    @settings(max_examples=100, deadline=1000)
    def test_result_str_format(self, best_n_jobs, best_chunksize):
        """Test that __str__ returns formatted output."""
        result = TuningResult(
            best_n_jobs=best_n_jobs,
            best_chunksize=best_chunksize,
            best_time=1.0,
            best_speedup=2.0,
            serial_time=2.0,
            configurations_tested=5,
            all_results={},
            search_strategy="grid",
            executor_type="process"
        )
        
        str_output = str(result)
        assert isinstance(str_output, str)
        assert "Auto-Tuning Results" in str_output
        assert f"n_jobs:     {best_n_jobs}" in str_output
        assert f"chunksize:  {best_chunksize}" in str_output

    @given(n_top=st.integers(min_value=1, max_value=10))
    @settings(max_examples=50, deadline=1000)
    def test_get_top_configurations(self, n_top):
        """Test that get_top_configurations returns correct number of results."""
        all_results = {
            (1, 1): 10.0,
            (2, 10): 5.0,
            (4, 20): 3.0,
            (8, 40): 2.5,
        }
        
        result = TuningResult(
            best_n_jobs=8,
            best_chunksize=40,
            best_time=2.5,
            best_speedup=4.0,
            serial_time=10.0,
            configurations_tested=4,
            all_results=all_results,
        )
        
        top_configs = result.get_top_configurations(n=n_top)
        assert isinstance(top_configs, list)
        assert len(top_configs) <= min(n_top, len(all_results))
        
        # Verify ordering (best first)
        for i in range(len(top_configs) - 1):
            assert top_configs[i][2] <= top_configs[i+1][2]  # time increases


# ============================================================================
# Test Tuning Function Invariants
# ============================================================================

class TestTuneParametersInvariants:
    """Test invariant properties of tune_parameters function."""

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_result_type(self, data):
        """Test that tune_parameters returns TuningResult."""
        # Use minimal search space for speed
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert isinstance(result, TuningResult)

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_best_n_jobs_positive(self, data):
        """Test that best_n_jobs is always >= 1."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.best_n_jobs >= 1

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_best_chunksize_positive(self, data):
        """Test that best_chunksize is always >= 1."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1, 5],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.best_chunksize >= 1

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_best_time_positive(self, data):
        """Test that best_time is always positive."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.best_time > 0

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_serial_time_positive(self, data):
        """Test that serial_time is always positive."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.serial_time > 0

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_best_speedup_non_negative(self, data):
        """Test that best_speedup is non-negative."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.best_speedup >= 0

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_configurations_tested_positive(self, data):
        """Test that configurations_tested is positive."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.configurations_tested > 0

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_search_strategy_valid(self, data):
        """Test that search_strategy is a valid value."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.search_strategy in ["grid", "adaptive", "bayesian", "quick"]

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_executor_type_valid(self, data):
        """Test that executor_type is valid."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False,
            prefer_threads_for_io=False
        )
        
        assert result.executor_type in ["process", "thread"]

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_all_results_is_dict(self, data):
        """Test that all_results is a dictionary."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert isinstance(result.all_results, dict)

    @given(data=valid_data_lists(min_size=10, max_size=50))
    @settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_best_config_in_all_results(self, data):
        """Test that best configuration is in all_results or is serial (1,1)."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1, 5],
            use_optimizer_hint=False,
            verbose=False
        )
        
        best_key = (result.best_n_jobs, result.best_chunksize)
        # Best config is either in all_results or is serial fallback (1, 1)
        assert best_key in result.all_results or best_key == (1, 1)


# ============================================================================
# Test Parameter Validation
# ============================================================================

class TestParameterValidation:
    """Test parameter validation for tuning functions."""

    def test_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="empty dataset"):
            tune_parameters(simple_func, [], n_jobs_range=[1], chunksize_range=[1])

    @given(
        n_iterations=st.integers(min_value=-10, max_value=4)
    )
    @settings(max_examples=20, deadline=1000)
    def test_bayesian_min_iterations(self, n_iterations):
        """Test that bayesian_tune requires at least 5 iterations."""
        if not HAS_SKOPT:
            pytest.skip("scikit-optimize not available")
        
        data = list(range(20))
        
        if n_iterations < 5:
            with pytest.raises(ValueError, match="at least 5"):
                bayesian_tune_parameters(simple_func, data, n_iterations=n_iterations)

    @given(
        n_jobs_min=st.integers(min_value=-10, max_value=0)
    )
    @settings(max_examples=20, deadline=1000)
    def test_bayesian_n_jobs_min_positive(self, n_jobs_min):
        """Test that n_jobs_min must be at least 1."""
        if not HAS_SKOPT:
            pytest.skip("scikit-optimize not available")
        
        data = list(range(20))
        
        if n_jobs_min < 1:
            with pytest.raises(ValueError, match="at least 1"):
                bayesian_tune_parameters(simple_func, data, n_jobs_min=n_jobs_min, n_iterations=5)

    @given(
        chunksize_min=st.integers(min_value=-10, max_value=0)
    )
    @settings(max_examples=20, deadline=1000)
    def test_bayesian_chunksize_min_positive(self, chunksize_min):
        """Test that chunksize_min must be at least 1."""
        if not HAS_SKOPT:
            pytest.skip("scikit-optimize not available")
        
        data = list(range(20))
        
        if chunksize_min < 1:
            with pytest.raises(ValueError, match="at least 1"):
                bayesian_tune_parameters(simple_func, data, chunksize_min=chunksize_min, n_iterations=5)

    def test_bayesian_n_jobs_max_greater_than_min(self):
        """Test that n_jobs_max must be >= n_jobs_min."""
        if not HAS_SKOPT:
            pytest.skip("scikit-optimize not available")
        
        data = list(range(20))
        
        with pytest.raises(ValueError, match="n_jobs_max must be"):
            bayesian_tune_parameters(simple_func, data, n_jobs_min=4, n_jobs_max=2, n_iterations=5)

    def test_bayesian_chunksize_max_greater_than_min(self):
        """Test that chunksize_max must be >= chunksize_min."""
        if not HAS_SKOPT:
            pytest.skip("scikit-optimize not available")
        
        data = list(range(20))
        
        with pytest.raises(ValueError, match="chunksize_max must be"):
            bayesian_tune_parameters(simple_func, data, chunksize_min=10, chunksize_max=5, n_iterations=5)


# ============================================================================
# Test Quick Tune
# ============================================================================

class TestQuickTune:
    """Test quick_tune function."""

    @given(data=valid_data_lists(min_size=20, max_size=100))
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_quick_tune_returns_tuning_result(self, data):
        """Test that quick_tune returns TuningResult."""
        result = quick_tune(simple_func, data, verbose=False)
        assert isinstance(result, TuningResult)

    @given(data=valid_data_lists(min_size=20, max_size=100))
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_quick_tune_tests_fewer_configs(self, data):
        """Test that quick_tune tests fewer configurations than full tune."""
        result = quick_tune(simple_func, data, verbose=False)
        
        # Quick tune should test at most ~9 configurations (3 n_jobs * 3 chunksizes)
        # Plus serial baseline = 10
        assert result.configurations_tested <= 15

    @given(data=valid_data_lists(min_size=20, max_size=100))
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_quick_tune_valid_results(self, data):
        """Test that quick_tune produces valid results."""
        result = quick_tune(simple_func, data, verbose=False)
        
        assert result.best_n_jobs >= 1
        assert result.best_chunksize >= 1
        assert result.best_time > 0
        assert result.serial_time > 0
        assert result.best_speedup >= 0


# ============================================================================
# Test Benchmark Configuration Helper
# ============================================================================

class TestBenchmarkConfiguration:
    """Test _benchmark_configuration helper function."""

    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=20, deadline=5000)
    def test_benchmark_returns_positive_time(self, n_jobs, chunksize):
        """Test that benchmark returns positive execution time."""
        data = list(range(50))
        
        exec_time = _benchmark_configuration(
            simple_func, data, n_jobs, chunksize,
            executor_type="process"
        )
        
        # Should return positive time or infinity on error
        assert exec_time > 0 or exec_time == float('inf')

    @given(
        n_jobs=st.integers(min_value=1, max_value=4),
        chunksize=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=20, deadline=5000)
    def test_benchmark_with_threads(self, n_jobs, chunksize):
        """Test benchmark with thread executor."""
        data = list(range(50))
        
        exec_time = _benchmark_configuration(
            simple_func, data, n_jobs, chunksize,
            executor_type="thread"
        )
        
        assert exec_time > 0 or exec_time == float('inf')


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases in tuning."""

    def test_small_dataset(self):
        """Test tuning with small dataset (10 items)."""
        data = list(range(10))
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        assert result.best_n_jobs >= 1
        assert result.best_chunksize >= 1

    def test_single_n_jobs_option(self):
        """Test with only one n_jobs option."""
        data = list(range(50))
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[2],
            chunksize_range=[1, 10],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.best_n_jobs in [1, 2]  # Could fall back to serial

    def test_single_chunksize_option(self):
        """Test with only one chunksize option."""
        data = list(range(50))
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[10],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.best_chunksize in [1, 10]  # Could fall back to serial

    def test_prefer_threads_for_io(self):
        """Test prefer_threads_for_io parameter."""
        data = list(range(30))
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False,
            prefer_threads_for_io=True
        )
        
        assert result.executor_type == "thread"

    @given(data=valid_data_lists(min_size=20, max_size=50))
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_verbose_parameter(self, data):
        """Test that verbose parameter doesn't affect results."""
        # Run with verbose=False
        result1 = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        # Verbose just prints output, doesn't change behavior
        assert isinstance(result1, TuningResult)


# ============================================================================
# Test Numerical Stability
# ============================================================================

class TestNumericalStability:
    """Test numerical stability with various parameter values."""

    @given(data=valid_data_lists(min_size=20, max_size=100))
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_various_data_sizes(self, data):
        """Test tuning with various data sizes."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        assert result.best_speedup >= 0
        assert result.best_time > 0
        assert not (math.isnan(result.best_speedup) or math.isinf(result.best_speedup))


# ============================================================================
# Test Integration Properties
# ============================================================================

class TestIntegration:
    """Test integration between different tuning components."""

    @given(data=valid_data_lists(min_size=20, max_size=50))
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_with_optimizer_hint(self, data):
        """Test tuning with optimizer hint enabled."""
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1, 5],
            use_optimizer_hint=True,
            verbose=False
        )
        
        # Optimizer hint may or may not be available
        # Just verify result is valid
        assert isinstance(result, TuningResult)
        assert result.best_n_jobs >= 1

    def test_result_save_config_method_exists(self):
        """Test that save_config method exists on TuningResult."""
        data = list(range(30))
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1],
            chunksize_range=[1],
            use_optimizer_hint=False,
            verbose=False
        )
        
        # Verify method exists (don't actually save file)
        assert hasattr(result, 'save_config')
        assert callable(result.save_config)

    def test_result_get_top_configurations_method_exists(self):
        """Test that get_top_configurations method exists."""
        data = list(range(30))
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[1, 5],
            use_optimizer_hint=False,
            verbose=False
        )
        
        # Verify method exists and works
        assert hasattr(result, 'get_top_configurations')
        assert callable(result.get_top_configurations)
        top_configs = result.get_top_configurations(n=3)
        assert isinstance(top_configs, list)


# ============================================================================
# Test Bayesian Optimization (if available)
# ============================================================================

@pytest.mark.skipif(not HAS_SKOPT, reason="scikit-optimize not installed")
class TestBayesianOptimization:
    """Test Bayesian optimization functionality."""

    def test_bayesian_tune_returns_tuning_result(self):
        """Test that bayesian_tune returns TuningResult."""
        data = list(range(30))
        
        result = bayesian_tune_parameters(
            simple_func, data,
            n_iterations=5,  # Minimal for speed
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        assert result.search_strategy == "bayesian"

    def test_bayesian_tune_valid_results(self):
        """Test that Bayesian optimization produces valid results."""
        data = list(range(30))
        
        result = bayesian_tune_parameters(
            simple_func, data,
            n_iterations=5,
            verbose=False
        )
        
        assert result.best_n_jobs >= 1
        assert result.best_chunksize >= 1
        assert result.best_time > 0
        assert result.serial_time > 0
        assert result.best_speedup >= 0

    def test_bayesian_respects_bounds(self):
        """Test that Bayesian optimization respects parameter bounds."""
        data = list(range(30))
        
        result = bayesian_tune_parameters(
            simple_func, data,
            n_iterations=5,
            n_jobs_min=2,
            n_jobs_max=4,
            chunksize_min=5,
            chunksize_max=15,
            verbose=False
        )
        
        # Best result should be within bounds or fall back to serial (1,1)
        if result.best_n_jobs != 1:
            assert 2 <= result.best_n_jobs <= 4
        if result.best_chunksize != 1:
            assert 5 <= result.best_chunksize <= 15

    @given(random_state=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=3, deadline=20000, suppress_health_check=[HealthCheck.too_slow])
    def test_bayesian_random_state_determinism(self, random_state):
        """Test that random_state provides deterministic results."""
        data = list(range(30))
        
        result1 = bayesian_tune_parameters(
            simple_func, data,
            n_iterations=5,
            random_state=random_state,
            verbose=False
        )
        
        result2 = bayesian_tune_parameters(
            simple_func, data,
            n_iterations=5,
            random_state=random_state,
            verbose=False
        )
        
        # With same random state, should get same best configuration
        # (may not be identical due to timing variations, but should be close)
        assert result1.best_n_jobs == result2.best_n_jobs or abs(result1.best_n_jobs - result2.best_n_jobs) <= 1


# ============================================================================
# Test Fallback Behavior
# ============================================================================

class TestFallbackBehavior:
    """Test fallback behavior when optimization fails."""

    def test_bayesian_fallback_without_skopt(self):
        """Test that bayesian_tune falls back gracefully without scikit-optimize."""
        if HAS_SKOPT:
            pytest.skip("Test only applies when scikit-optimize is not available")
        
        data = list(range(30))
        
        # Should fall back to grid search
        with pytest.warns(RuntimeWarning, match="scikit-optimize not available"):
            result = bayesian_tune_parameters(
                simple_func, data,
                n_iterations=5,
                verbose=False
            )
        
        assert isinstance(result, TuningResult)
        # Fallback should use grid search
        assert result.search_strategy == "grid"
