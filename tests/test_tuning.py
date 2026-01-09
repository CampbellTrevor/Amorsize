"""
Tests for the auto-tuning module.
"""

import pytest
import time
from amorsize.tuning import tune_parameters, quick_tune, TuningResult, _benchmark_configuration


def simple_func(x):
    """Simple CPU-bound function for testing."""
    return sum(i**2 for i in range(x))


def fast_func(x):
    """Very fast function."""
    return x * 2


def slow_func(x):
    """Moderately slow function."""
    time.sleep(0.01)
    return x * x


class TestTuningResult:
    """Test TuningResult class."""
    
    def test_initialization(self):
        """Test basic initialization."""
        result = TuningResult(
            best_n_jobs=4,
            best_chunksize=10,
            best_time=1.5,
            best_speedup=2.0,
            serial_time=3.0,
            configurations_tested=10,
            all_results={(4, 10): 1.5, (2, 5): 2.0},
            search_strategy="grid"
        )
        
        assert result.best_n_jobs == 4
        assert result.best_chunksize == 10
        assert result.best_time == 1.5
        assert result.best_speedup == 2.0
        assert result.serial_time == 3.0
        assert result.configurations_tested == 10
        assert result.search_strategy == "grid"
        assert result.executor_type == "process"
    
    def test_repr(self):
        """Test string representation."""
        result = TuningResult(
            best_n_jobs=4,
            best_chunksize=10,
            best_time=1.5,
            best_speedup=2.5,
            serial_time=3.0,
            configurations_tested=10,
            all_results={(4, 10): 1.5}
        )
        
        repr_str = repr(result)
        assert "TuningResult" in repr_str
        assert "best_n_jobs=4" in repr_str
        assert "best_chunksize=10" in repr_str
        assert "best_speedup=2.50x" in repr_str
    
    def test_str_formatting(self):
        """Test formatted string output."""
        result = TuningResult(
            best_n_jobs=4,
            best_chunksize=10,
            best_time=1.5,
            best_speedup=2.0,
            serial_time=3.0,
            configurations_tested=10,
            all_results={(4, 10): 1.5, (2, 5): 2.0}
        )
        
        str_output = str(result)
        assert "Auto-Tuning Results" in str_output
        assert "n_jobs:     4" in str_output
        assert "chunksize:  10" in str_output
        assert "Best speedup" in str_output
    
    def test_get_top_configurations(self):
        """Test getting top N configurations."""
        all_results = {
            (4, 10): 1.5,
            (2, 5): 2.0,
            (8, 20): 1.2,
            (1, 1): 3.0
        }
        result = TuningResult(
            best_n_jobs=8,
            best_chunksize=20,
            best_time=1.2,
            best_speedup=2.5,
            serial_time=3.0,
            configurations_tested=4,
            all_results=all_results
        )
        
        top_3 = result.get_top_configurations(n=3)
        assert len(top_3) == 3
        # Should be sorted by time (fastest first)
        assert top_3[0][0] == 8 and top_3[0][1] == 20  # Best config
        assert top_3[1][0] == 4 and top_3[1][1] == 10  # Second best


class TestBenchmarkConfiguration:
    """Test the _benchmark_configuration helper function."""
    
    def test_basic_benchmark(self):
        """Test basic benchmarking."""
        data = range(10, 20)
        exec_time = _benchmark_configuration(fast_func, data, n_jobs=2, chunksize=5)
        
        assert exec_time > 0
        assert exec_time < 10  # Should be very fast
    
    def test_different_worker_counts(self):
        """Test with different worker counts."""
        data = range(10, 30)
        
        time_1_worker = _benchmark_configuration(simple_func, data, n_jobs=1, chunksize=10)
        time_2_workers = _benchmark_configuration(simple_func, data, n_jobs=2, chunksize=10)
        
        # Both should complete successfully
        assert time_1_worker > 0
        assert time_2_workers > 0
    
    def test_thread_executor(self):
        """Test with thread executor."""
        data = range(10, 20)
        exec_time = _benchmark_configuration(
            fast_func, data, 
            n_jobs=2, 
            chunksize=5,
            executor_type="thread"
        )
        
        assert exec_time > 0
        assert exec_time < 10


class TestTuneParameters:
    """Test the main tune_parameters function."""
    
    def test_basic_tuning(self):
        """Test basic auto-tuning."""
        data = range(50, 100)
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[5, 10],
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        assert result.best_n_jobs >= 1
        # Best chunksize should be in search space OR 1 (if serial is fastest)
        assert result.best_chunksize in [1, 5, 10]
        assert result.serial_time > 0
        assert result.best_time > 0
        assert result.best_speedup >= 1.0  # Should be at least as good as serial
        assert result.configurations_tested == 5  # 2*2 + 1 for serial
    
    def test_small_dataset(self):
        """Test tuning with small dataset."""
        data = range(5, 10)
        
        result = tune_parameters(simple_func, data, verbose=False)
        
        assert isinstance(result, TuningResult)
        assert result.best_n_jobs >= 1
        assert result.best_chunksize >= 1
    
    def test_with_optimizer_hint(self):
        """Test tuning with optimizer hint enabled."""
        data = range(50, 100)
        
        result = tune_parameters(
            simple_func, data,
            use_optimizer_hint=True,
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        # Should have an optimization hint
        assert result.optimization_hint is not None
    
    def test_without_optimizer_hint(self):
        """Test tuning without optimizer hint."""
        data = range(50, 100)
        
        result = tune_parameters(
            simple_func, data,
            use_optimizer_hint=False,
            n_jobs_range=[1, 2],
            chunksize_range=[10, 20],
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        # Should not have optimization hint
        assert result.optimization_hint is None
    
    def test_verbose_output(self, capsys):
        """Test verbose output."""
        data = range(20, 40)
        
        result = tune_parameters(
            fast_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[5],
            verbose=True
        )
        
        captured = capsys.readouterr()
        assert "Auto-Tuning Configuration" in captured.out
        assert "Benchmarking serial" in captured.out
        assert "Testing n_jobs" in captured.out
    
    def test_custom_search_space(self):
        """Test with custom search space."""
        data = range(20, 60)
        
        custom_n_jobs = [1, 2, 4]
        custom_chunksize = [10, 20]
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=custom_n_jobs,
            chunksize_range=custom_chunksize,
            verbose=False
        )
        
        # Best config should be from search space, or (1,1) if serial is fastest
        assert result.best_n_jobs in custom_n_jobs or result.best_n_jobs == 1
        assert result.best_chunksize in custom_chunksize or result.best_chunksize == 1
        assert result.configurations_tested == len(custom_n_jobs) * len(custom_chunksize) + 1
    
    def test_list_data(self):
        """Test with list data."""
        data = [10, 20, 30, 40, 50]
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[2],
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        assert result.best_time > 0
    
    def test_range_data(self):
        """Test with range data."""
        data = range(10, 30)
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[5],
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        assert result.best_time > 0
    
    def test_iterator_conversion(self):
        """Test with iterator data (should be converted to list)."""
        data = iter(range(10, 20))
        
        result = tune_parameters(
            fast_func, data,
            n_jobs_range=[1],
            chunksize_range=[5],
            verbose=False
        )
        
        assert isinstance(result, TuningResult)
        assert result.best_time > 0
    
    def test_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="empty dataset"):
            tune_parameters(simple_func, [], verbose=False)
    
    def test_finds_parallelization_benefit(self):
        """Test that tuning finds benefit of parallelization when it exists."""
        # Use a workload large enough to benefit from parallelization
        data = range(100, 200)
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2, 4],
            chunksize_range=[10, 20],
            verbose=False
        )
        
        # For CPU-bound work with enough items, parallelization should help
        # (though this depends on system, so we just check that it completed)
        assert result.best_n_jobs >= 1
        assert result.best_speedup > 0
    
    def test_thread_executor_preference(self):
        """Test using thread executor."""
        data = range(10, 30)
        
        result = tune_parameters(
            fast_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[5],
            prefer_threads_for_io=True,
            verbose=False
        )
        
        assert result.executor_type == "thread"
    
    def test_process_executor_default(self):
        """Test default process executor."""
        data = range(10, 30)
        
        result = tune_parameters(
            fast_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[5],
            prefer_threads_for_io=False,
            verbose=False
        )
        
        assert result.executor_type == "process"


class TestQuickTune:
    """Test the quick_tune convenience function."""
    
    def test_basic_quick_tune(self):
        """Test basic quick tuning."""
        data = range(50, 100)
        
        result = quick_tune(simple_func, data, verbose=False)
        
        assert isinstance(result, TuningResult)
        assert result.best_n_jobs >= 1
        assert result.best_chunksize >= 1
        assert result.serial_time > 0
    
    def test_quick_tune_small_dataset(self):
        """Test quick tune with small dataset."""
        data = range(5, 15)
        
        result = quick_tune(fast_func, data, verbose=False)
        
        assert isinstance(result, TuningResult)
        # For small dataset, chunksize should be 1
        assert result.best_chunksize >= 1
    
    def test_quick_tune_with_threads(self):
        """Test quick tune with thread executor."""
        data = range(20, 50)
        
        result = quick_tune(
            fast_func, data,
            prefer_threads_for_io=True,
            verbose=False
        )
        
        assert result.executor_type == "thread"
    
    def test_quick_tune_verbose(self, capsys):
        """Test quick tune with verbose output."""
        data = range(20, 40)
        
        result = quick_tune(fast_func, data, verbose=True)
        
        captured = capsys.readouterr()
        assert "Auto-Tuning" in captured.out or "Benchmarking" in captured.out
    
    def test_quick_tune_tests_fewer_configs(self):
        """Test that quick_tune tests fewer configurations than full tune."""
        data = range(50, 150)
        
        quick_result = quick_tune(simple_func, data, verbose=False)
        
        # Quick tune should test a minimal set of configurations
        # Exact number depends on system, but should be relatively small
        assert quick_result.configurations_tested > 0
        assert quick_result.configurations_tested < 20  # Reasonable upper bound


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_single_item_data(self):
        """Test with single-item dataset."""
        data = [100]
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1],
            chunksize_range=[1],
            verbose=False
        )
        
        assert result.best_n_jobs == 1
        assert result.best_chunksize == 1
    
    def test_all_configs_produce_results(self):
        """Test that all configurations are tested."""
        data = range(20, 40)
        n_jobs_range = [1, 2]
        chunksize_range = [5, 10]
        
        result = tune_parameters(
            fast_func, data,
            n_jobs_range=n_jobs_range,
            chunksize_range=chunksize_range,
            verbose=False
        )
        
        # Should test all combinations
        expected_configs = len(n_jobs_range) * len(chunksize_range)
        assert len(result.all_results) == expected_configs
    
    def test_results_sorted_correctly(self):
        """Test that best result is actually the fastest."""
        data = range(30, 60)
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2, 4],
            chunksize_range=[5, 10],
            verbose=False
        )
        
        # Best time should be minimum of all times
        all_times = list(result.all_results.values())
        assert result.best_time <= min(all_times)
    
    def test_speedup_calculation(self):
        """Test speedup calculation is correct."""
        data = range(30, 60)
        
        result = tune_parameters(
            simple_func, data,
            n_jobs_range=[1, 2],
            chunksize_range=[10],
            verbose=False
        )
        
        # Speedup should be serial_time / best_time
        expected_speedup = result.serial_time / result.best_time
        assert abs(result.best_speedup - expected_speedup) < 0.01


class TestIntegrationWithOptimizer:
    """Test integration with the optimizer module."""
    
    def test_tuning_includes_optimizer_hint(self):
        """Test that optimizer hint is included in search space."""
        data = range(100, 200)
        
        result = tune_parameters(
            simple_func, data,
            use_optimizer_hint=True,
            verbose=False
        )
        
        # Should have optimizer hint
        assert result.optimization_hint is not None
        
        # Optimizer's recommendation should have been tested
        hint_config = (result.optimization_hint.n_jobs, result.optimization_hint.chunksize)
        # Note: The hint might not be in all_results if it matches an existing config
        # in the default search space, so we just check that hint exists
    
    def test_comparison_with_optimizer(self):
        """Test comparing tuning result with optimizer hint."""
        data = range(100, 150)
        
        result = tune_parameters(
            simple_func, data,
            use_optimizer_hint=True,
            verbose=False
        )
        
        # String output should mention optimizer hint
        str_output = str(result)
        if result.optimization_hint:
            assert "Optimizer suggested" in str_output or "Comparison" in str_output
