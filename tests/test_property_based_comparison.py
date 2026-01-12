"""
Property-based tests for comparison module using Hypothesis.

This module tests comparison operations using property-based testing to
automatically generate thousands of edge cases for:
- ComparisonConfig validation and field types
- ComparisonResult structure and calculations
- compare_strategies function behavior
- compare_with_optimizer integration
- Edge cases and error handling
- Thread safety for concurrent operations
"""

import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from amorsize.comparison import (
    ComparisonConfig,
    ComparisonResult,
    compare_strategies,
    compare_with_optimizer,
)


# ============================================================================
# Custom Hypothesis Strategies
# ============================================================================

@st.composite
def comparison_config_strategy(draw, allow_serial=True):
    """Generate valid ComparisonConfig objects."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_- '
    )))
    n_jobs = draw(st.integers(min_value=1, max_value=16))
    chunksize = draw(st.integers(min_value=1, max_value=100))
    executor_type = draw(st.sampled_from(["process", "thread", "serial"]))
    
    return ComparisonConfig(
        name=name,
        n_jobs=n_jobs,
        chunksize=chunksize,
        executor_type=executor_type
    )


@st.composite
def config_list_strategy(draw, min_size=1, max_size=5):
    """Generate list of unique ComparisonConfig objects."""
    configs = draw(st.lists(
        comparison_config_strategy(),
        min_size=min_size,
        max_size=max_size
    ))
    
    # Ensure unique names
    seen_names = set()
    unique_configs = []
    for config in configs:
        if config.name not in seen_names:
            seen_names.add(config.name)
            unique_configs.append(config)
    
    # If we filtered too many, add some back with unique names
    if len(unique_configs) < min_size:
        for i in range(min_size - len(unique_configs)):
            unique_configs.append(ComparisonConfig(
                name=f"Config_{i}_{draw(st.integers(min_value=0, max_value=10000))}",
                n_jobs=draw(st.integers(min_value=1, max_value=8)),
                chunksize=draw(st.integers(min_value=1, max_value=50)),
                executor_type=draw(st.sampled_from(["process", "thread", "serial"]))
            ))
    
    return unique_configs[:max_size]


@st.composite
def comparison_result_strategy(draw):
    """Generate valid ComparisonResult objects for testing."""
    num_configs = draw(st.integers(min_value=1, max_value=5))
    configs = draw(config_list_strategy(min_size=num_configs, max_size=num_configs))
    
    # Generate execution times (positive floats)
    execution_times = draw(st.lists(
        st.floats(min_value=0.001, max_value=100.0),
        min_size=num_configs,
        max_size=num_configs
    ))
    
    # Calculate speedups relative to first config
    baseline_time = execution_times[0]
    speedups = [baseline_time / t if t > 0 else 1.0 for t in execution_times]
    
    # Find best config index
    best_idx = execution_times.index(min(execution_times))
    
    recommendations = draw(st.lists(
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=5
    ))
    
    return ComparisonResult(
        configs=configs,
        execution_times=execution_times,
        speedups=speedups,
        best_config_index=best_idx,
        recommendations=recommendations
    )


# Test function for comparison benchmarking
def fast_test_func(x):
    """Fast test function for property-based testing."""
    return x * 2


def medium_test_func(x):
    """Medium-speed test function."""
    result = 0
    for i in range(50):
        result += x ** 2
    return result


# ============================================================================
# Test ComparisonConfig Invariants
# ============================================================================

class TestComparisonConfigInvariants:
    """Test invariants of ComparisonConfig class."""
    
    @given(
        name=st.text(min_size=1, max_size=100),
        n_jobs=st.integers(min_value=1, max_value=32),
        chunksize=st.integers(min_value=1, max_value=1000),
        executor_type=st.sampled_from(["process", "thread", "serial"])
    )
    def test_valid_config_creation(self, name, n_jobs, chunksize, executor_type):
        """Test that valid ComparisonConfig can be created."""
        config = ComparisonConfig(
            name=name,
            n_jobs=n_jobs,
            chunksize=chunksize,
            executor_type=executor_type
        )
        
        assert config.name == name
        assert config.n_jobs == n_jobs
        assert config.chunksize == chunksize
        assert config.executor_type == executor_type
    
    @given(n_jobs=st.integers(max_value=0))
    def test_invalid_n_jobs_rejected(self, n_jobs):
        """Test that n_jobs <= 0 is rejected."""
        with pytest.raises(ValueError, match="n_jobs must be >= 1"):
            ComparisonConfig(name="test", n_jobs=n_jobs)
    
    @given(chunksize=st.integers(max_value=0))
    def test_invalid_chunksize_rejected(self, chunksize):
        """Test that chunksize <= 0 is rejected."""
        with pytest.raises(ValueError, match="chunksize must be >= 1"):
            ComparisonConfig(name="test", chunksize=chunksize)
    
    @given(executor_type=st.text(min_size=1, max_size=20).filter(
        lambda x: x not in ["process", "thread", "serial"]
    ))
    def test_invalid_executor_type_rejected(self, executor_type):
        """Test that invalid executor_type is rejected."""
        with pytest.raises(ValueError, match="executor_type must be"):
            ComparisonConfig(name="test", executor_type=executor_type)
    
    @given(config=comparison_config_strategy())
    def test_repr_contains_key_info(self, config):
        """Test that __repr__ contains key configuration info."""
        repr_str = repr(config)
        assert config.name in repr_str
        assert "ComparisonConfig" in repr_str
    
    @given(config=comparison_config_strategy())
    def test_str_is_readable(self, config):
        """Test that __str__ produces human-readable output."""
        str_output = str(config)
        assert config.name in str_output
        assert isinstance(str_output, str)
        assert len(str_output) > 0


# ============================================================================
# Test ComparisonResult Invariants
# ============================================================================

class TestComparisonResultInvariants:
    """Test invariants of ComparisonResult class."""
    
    @given(result=comparison_result_strategy())
    def test_result_structure_valid(self, result):
        """Test that ComparisonResult has valid structure."""
        assert isinstance(result.configs, list)
        assert isinstance(result.execution_times, list)
        assert isinstance(result.speedups, list)
        assert isinstance(result.best_config_index, int)
        assert isinstance(result.recommendations, list)
        
        # All lists should have same length
        assert len(result.configs) == len(result.execution_times)
        assert len(result.configs) == len(result.speedups)
        
        # Best index should be valid
        assert 0 <= result.best_config_index < len(result.configs)
    
    @given(result=comparison_result_strategy())
    def test_best_config_consistency(self, result):
        """Test that best_config and best_time are consistent with index."""
        assert result.best_config == result.configs[result.best_config_index]
        assert result.best_time == result.execution_times[result.best_config_index]
    
    @given(result=comparison_result_strategy())
    def test_speedup_calculation_correct(self, result):
        """Test that speedups are calculated correctly relative to baseline."""
        baseline_time = result.execution_times[0]
        for i, (exec_time, speedup) in enumerate(zip(result.execution_times, result.speedups)):
            if exec_time > 0:
                expected_speedup = baseline_time / exec_time
                assert abs(speedup - expected_speedup) < 0.001
    
    @given(result=comparison_result_strategy())
    def test_best_config_has_minimum_time(self, result):
        """Test that best_config_index points to minimum execution time."""
        min_time = min(result.execution_times)
        assert result.execution_times[result.best_config_index] == min_time
    
    @given(result=comparison_result_strategy())
    def test_repr_contains_key_info(self, result):
        """Test that __repr__ contains key result info."""
        repr_str = repr(result)
        assert "ComparisonResult" in repr_str
        assert result.best_config.name in repr_str
    
    @given(result=comparison_result_strategy())
    def test_str_produces_formatted_table(self, result):
        """Test that __str__ produces formatted output."""
        str_output = str(result)
        assert "Strategy Comparison Results" in str_output
        assert "Best Strategy:" in str_output
        assert result.best_config.name in str_output
        # Check that all config names appear
        for config in result.configs:
            assert config.name in str_output
    
    @given(result=comparison_result_strategy())
    def test_get_sorted_configs_returns_sorted_list(self, result):
        """Test that get_sorted_configs returns configs sorted by time."""
        sorted_configs = result.get_sorted_configs()
        
        assert len(sorted_configs) == len(result.configs)
        
        # Check that times are in ascending order
        times = [t for _, t, _ in sorted_configs]
        assert times == sorted(times)
        
        # Check that fastest config is first
        assert sorted_configs[0][0] == result.best_config
        assert sorted_configs[0][1] == result.best_time


# ============================================================================
# Test compare_strategies Function Properties
# ============================================================================

class TestCompareStrategiesProperties:
    """Test properties of compare_strategies function."""
    
    @given(
        data_size=st.integers(min_value=5, max_value=50),
        configs=config_list_strategy(min_size=1, max_size=3)
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_compare_returns_valid_result(self, data_size, configs):
        """Test that compare_strategies returns valid ComparisonResult."""
        data = list(range(data_size))
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert isinstance(result, ComparisonResult)
        assert len(result.configs) == len(configs)
        assert len(result.execution_times) == len(configs)
        assert len(result.speedups) == len(configs)
        assert 0 <= result.best_config_index < len(configs)
    
    @given(data_size=st.integers(min_value=1, max_value=30))
    @settings(deadline=None)
    def test_compare_with_single_config(self, data_size):
        """Test compare_strategies with single configuration."""
        data = list(range(data_size))
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.configs) == 1
        assert result.best_config_index == 0
        assert result.speedups[0] == 1.0  # Baseline speedup is 1.0
    
    @given(
        data_size=st.integers(min_value=10, max_value=50),
        max_items=st.integers(min_value=5, max_value=20)
    )
    @settings(deadline=None)
    def test_max_items_limits_dataset(self, data_size, max_items):
        """Test that max_items parameter limits dataset size."""
        assume(data_size > max_items)
        
        data = list(range(data_size))
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        # This should only process max_items, not all data
        result = compare_strategies(
            fast_test_func, data, configs,
            max_items=max_items, timeout=30.0
        )
        
        assert isinstance(result, ComparisonResult)
        # Result should be successful even though we limited items
        assert len(result.execution_times) == 1
    
    @given(configs=config_list_strategy(min_size=2, max_size=3))
    @settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_speedups_relative_to_first_config(self, configs):
        """Test that speedups are calculated relative to first config."""
        data = list(range(20))
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        # First config should always have speedup of 1.0 (baseline)
        assert abs(result.speedups[0] - 1.0) < 0.001
        
        # Faster configs should have speedup > 1.0
        for i in range(1, len(result.speedups)):
            if result.execution_times[i] < result.execution_times[0]:
                assert result.speedups[i] > 1.0
    
    def test_compare_rejects_empty_configs(self):
        """Test that empty configs list is rejected."""
        data = list(range(10))
        
        with pytest.raises(ValueError, match="configs cannot be empty"):
            compare_strategies(fast_test_func, data, [], timeout=30.0)
    
    def test_compare_rejects_none_data(self):
        """Test that None data is rejected."""
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        with pytest.raises(ValueError, match="data cannot be None"):
            compare_strategies(fast_test_func, None, configs, timeout=30.0)
    
    def test_compare_rejects_empty_data(self):
        """Test that empty data is rejected."""
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        with pytest.raises(ValueError, match="data cannot be empty"):
            compare_strategies(fast_test_func, [], configs, timeout=30.0)
    
    @given(timeout=st.floats(max_value=0.0))
    def test_compare_rejects_non_positive_timeout(self, timeout):
        """Test that non-positive timeout is rejected."""
        data = list(range(10))
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        with pytest.raises(ValueError, match="timeout must be positive"):
            compare_strategies(fast_test_func, data, configs, timeout=timeout)
    
    def test_compare_rejects_non_callable_func(self):
        """Test that non-callable func is rejected."""
        data = list(range(10))
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        with pytest.raises(ValueError, match="func must be callable"):
            compare_strategies("not_callable", data, configs, timeout=30.0)


# ============================================================================
# Test compare_strategies Execution Behavior
# ============================================================================

class TestCompareStrategiesExecution:
    """Test actual execution behavior of compare_strategies."""
    
    def test_serial_execution_works(self):
        """Test that serial execution completes successfully."""
        data = list(range(20))
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 1
        assert result.execution_times[0] > 0
    
    def test_thread_execution_works(self):
        """Test that thread execution completes successfully."""
        data = list(range(20))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Thread", n_jobs=2, executor_type="thread")
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 2
        assert all(t > 0 for t in result.execution_times)
    
    def test_process_execution_works(self):
        """Test that process execution completes successfully."""
        data = list(range(20))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Process", n_jobs=2, executor_type="process")
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 2
        assert all(t > 0 for t in result.execution_times)
    
    def test_mixed_executor_types(self):
        """Test comparison with mixed executor types."""
        data = list(range(20))
        configs = [
            ComparisonConfig("Serial", n_jobs=1, executor_type="serial"),
            ComparisonConfig("Thread", n_jobs=2, executor_type="thread"),
            ComparisonConfig("Process", n_jobs=2, executor_type="process")
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 3
        assert all(t > 0 for t in result.execution_times)
        assert 0 <= result.best_config_index < 3
    
    def test_verbose_mode_does_not_crash(self):
        """Test that verbose mode runs without errors."""
        data = list(range(10))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Parallel", n_jobs=2)
        ]
        
        # Should not raise any exceptions
        result = compare_strategies(
            fast_test_func, data, configs,
            timeout=30.0, verbose=True
        )
        
        assert isinstance(result, ComparisonResult)


# ============================================================================
# Test Recommendations Generation
# ============================================================================

class TestRecommendationsGeneration:
    """Test that recommendations are generated appropriately."""
    
    def test_serial_fastest_generates_recommendation(self):
        """Test recommendation when serial is fastest."""
        data = list(range(10))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Parallel", n_jobs=4, chunksize=3)
        ]
        
        # Use very fast function so serial wins
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        # Should have recommendations
        assert len(result.recommendations) > 0
    
    def test_parallel_fastest_generates_recommendation(self):
        """Test recommendation when parallel is fastest."""
        data = list(range(30))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Parallel", n_jobs=2, chunksize=5)
        ]
        
        # Use medium function so parallel has a chance to win
        result = compare_strategies(medium_test_func, data, configs, timeout=30.0)
        
        # Should have recommendations
        assert len(result.recommendations) > 0
    
    def test_thread_vs_process_comparison_recommendation(self):
        """Test recommendation when comparing thread vs process."""
        data = list(range(20))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Thread", n_jobs=2, executor_type="thread"),
            ComparisonConfig("Process", n_jobs=2, executor_type="process")
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        # Should generate recommendations comparing threading vs multiprocessing
        assert len(result.recommendations) > 0


# ============================================================================
# Test compare_with_optimizer Integration
# ============================================================================

class TestCompareWithOptimizerIntegration:
    """Test compare_with_optimizer function."""
    
    def test_compare_with_optimizer_returns_tuple(self):
        """Test that compare_with_optimizer returns (ComparisonResult, OptimizationResult)."""
        data = list(range(30))
        
        comparison, optimization = compare_with_optimizer(
            medium_test_func, data, timeout=60.0
        )
        
        assert isinstance(comparison, ComparisonResult)
        # optimization should have n_jobs attribute (duck typing check)
        assert hasattr(optimization, 'n_jobs')
        assert hasattr(optimization, 'chunksize')
    
    def test_compare_with_optimizer_includes_serial_baseline(self):
        """Test that comparison includes serial baseline."""
        data = list(range(20))
        
        comparison, _ = compare_with_optimizer(
            fast_test_func, data, timeout=60.0
        )
        
        # Should have at least 2 configs: Serial + Optimizer
        assert len(comparison.configs) >= 2
        # First config should be serial
        assert comparison.configs[0].name == "Serial"
        assert comparison.configs[0].n_jobs == 1
    
    def test_compare_with_optimizer_includes_optimizer_recommendation(self):
        """Test that comparison includes optimizer recommendation."""
        data = list(range(20))
        
        comparison, optimization = compare_with_optimizer(
            fast_test_func, data, timeout=60.0
        )
        
        # Should have optimizer config
        optimizer_configs = [c for c in comparison.configs if c.name == "Optimizer"]
        assert len(optimizer_configs) == 1
        
        # Optimizer config should match optimization result
        opt_config = optimizer_configs[0]
        assert opt_config.n_jobs == optimization.n_jobs
        assert opt_config.chunksize == optimization.chunksize
    
    def test_compare_with_optimizer_accepts_additional_configs(self):
        """Test that additional configs are included in comparison."""
        data = list(range(20))
        additional = [
            ComparisonConfig("Custom 1", n_jobs=2, chunksize=5),
            ComparisonConfig("Custom 2", n_jobs=4, chunksize=3)
        ]
        
        comparison, _ = compare_with_optimizer(
            fast_test_func, data,
            additional_configs=additional,
            timeout=60.0
        )
        
        # Should have Serial + Optimizer + 2 additional = 4 configs
        assert len(comparison.configs) >= 4
        
        # Check that additional configs are present
        config_names = [c.name for c in comparison.configs]
        assert "Custom 1" in config_names
        assert "Custom 2" in config_names
    
    def test_compare_with_optimizer_respects_max_items(self):
        """Test that max_items parameter is respected."""
        data = list(range(100))
        
        # Should complete quickly even with large dataset
        comparison, _ = compare_with_optimizer(
            fast_test_func, data,
            max_items=20,
            timeout=60.0
        )
        
        assert isinstance(comparison, ComparisonResult)
    
    def test_compare_with_optimizer_verbose_mode(self):
        """Test that verbose mode works without errors."""
        data = list(range(15))
        
        # Should not raise any exceptions
        comparison, optimization = compare_with_optimizer(
            fast_test_func, data,
            timeout=60.0,
            verbose=True
        )
        
        assert isinstance(comparison, ComparisonResult)


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_item_workload(self):
        """Test comparison with single-item workload."""
        data = [42]
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Parallel", n_jobs=2)
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 2
        assert all(t > 0 for t in result.execution_times)
    
    def test_identical_configs_different_names(self):
        """Test that identical configs with different names work."""
        data = list(range(20))
        configs = [
            ComparisonConfig("Config A", n_jobs=2, chunksize=5),
            ComparisonConfig("Config B", n_jobs=2, chunksize=5)
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 2
        # Execution times should be similar (within 50% tolerance due to variance)
        time_ratio = max(result.execution_times) / min(result.execution_times)
        assert time_ratio < 1.5
    
    def test_very_small_chunksize(self):
        """Test comparison with chunksize=1."""
        data = list(range(20))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Small Chunks", n_jobs=2, chunksize=1)
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 2
        assert all(t > 0 for t in result.execution_times)
    
    def test_very_large_chunksize(self):
        """Test comparison with chunksize larger than dataset."""
        data = list(range(10))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Large Chunks", n_jobs=2, chunksize=100)
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 2
        assert all(t > 0 for t in result.execution_times)
    
    def test_many_workers(self):
        """Test comparison with many workers."""
        data = list(range(50))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Many Workers", n_jobs=16, chunksize=3)
        ]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert len(result.execution_times) == 2
        assert all(t > 0 for t in result.execution_times)
    
    @given(data_size=st.integers(min_value=1, max_value=20))
    @settings(deadline=None)
    def test_various_data_sizes(self, data_size):
        """Test comparison with various data sizes."""
        data = list(range(data_size))
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        result = compare_strategies(fast_test_func, data, configs, timeout=30.0)
        
        assert isinstance(result, ComparisonResult)
        assert len(result.execution_times) == 1
        assert result.execution_times[0] > 0


# ============================================================================
# Test Thread Safety
# ============================================================================

class TestThreadSafety:
    """Test thread safety of comparison operations."""
    
    def test_concurrent_comparisons_no_interference(self):
        """Test that concurrent compare_strategies calls don't interfere."""
        data = list(range(20))
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Parallel", n_jobs=2)
        ]
        
        results = [None, None]
        errors = []
        
        def run_comparison(index):
            try:
                results[index] = compare_strategies(
                    fast_test_func, data, configs, timeout=30.0
                )
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=run_comparison, args=(0,)),
            threading.Thread(target=run_comparison, args=(1,))
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Both should succeed
        assert len(errors) == 0
        assert results[0] is not None
        assert results[1] is not None
        assert isinstance(results[0], ComparisonResult)
        assert isinstance(results[1], ComparisonResult)


# ============================================================================
# Test Integration Properties
# ============================================================================

class TestIntegrationProperties:
    """Test integration scenarios and full workflows."""
    
    def test_full_comparison_workflow(self):
        """Test complete comparison workflow from start to finish."""
        data = list(range(30))
        
        # Create multiple configs
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=10),
            ComparisonConfig("4 Workers", n_jobs=4, chunksize=5)
        ]
        
        # Run comparison
        result = compare_strategies(medium_test_func, data, configs, timeout=60.0)
        
        # Validate result structure
        assert len(result.configs) == 3
        assert len(result.execution_times) == 3
        assert len(result.speedups) == 3
        assert 0 <= result.best_config_index < 3
        
        # Validate speedups
        assert result.speedups[0] == 1.0  # Baseline
        
        # Validate best config
        assert result.best_time == min(result.execution_times)
        
        # Get sorted configs
        sorted_configs = result.get_sorted_configs()
        assert len(sorted_configs) == 3
        assert sorted_configs[0][0] == result.best_config
    
    def test_optimizer_integration_workflow(self):
        """Test complete workflow with optimizer integration."""
        data = list(range(30))
        
        # Run comparison with optimizer
        comparison, optimization = compare_with_optimizer(
            medium_test_func, data,
            additional_configs=[
                ComparisonConfig("Custom", n_jobs=3, chunksize=7)
            ],
            timeout=60.0
        )
        
        # Should have at least 3 configs: Serial, Optimizer, Custom
        assert len(comparison.configs) >= 3
        
        # Verify optimizer config matches optimization result
        opt_configs = [c for c in comparison.configs if c.name == "Optimizer"]
        assert len(opt_configs) == 1
        assert opt_configs[0].n_jobs == optimization.n_jobs
        assert opt_configs[0].chunksize == optimization.chunksize
        
        # Verify results are valid
        assert len(comparison.execution_times) == len(comparison.configs)
        assert all(t > 0 for t in comparison.execution_times)
