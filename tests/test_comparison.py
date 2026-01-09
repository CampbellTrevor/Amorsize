"""
Tests for the comparison mode module.
"""

import pytest
import time
from amorsize import compare_strategies, compare_with_optimizer, ComparisonConfig, ComparisonResult


# Module-level functions for testing (must be picklable for multiprocessing)
def simple_func(x):
    """Simple function for testing."""
    return x ** 2


def slow_func(x):
    """Slow function for testing parallelization."""
    result = 0
    for i in range(1000):
        result += x ** 2
    return result


def cpu_intensive(x):
    """CPU-intensive function for integration tests."""
    result = 0
    for i in range(500):
        result += x ** 2
    return result


def medium_func(x):
    """Medium-complexity function for testing."""
    result = 0
    for i in range(300):
        result += x ** 2
    return result


def io_bound_func(x):
    """Simulated I/O-bound function."""
    time.sleep(0.001)
    return x * 2


class TestComparisonConfig:
    """Tests for ComparisonConfig class."""
    
    def test_comparison_config_creation(self):
        """Test that ComparisonConfig can be created with all fields."""
        config = ComparisonConfig("Test", n_jobs=2, chunksize=10, executor_type="process")
        
        assert config.name == "Test"
        assert config.n_jobs == 2
        assert config.chunksize == 10
        assert config.executor_type == "process"
    
    def test_comparison_config_repr(self):
        """Test ComparisonConfig string representation."""
        config = ComparisonConfig("Test", n_jobs=2, chunksize=10, executor_type="process")
        repr_str = repr(config)
        
        assert "Test" in repr_str
        assert "n_jobs=2" in repr_str
        assert "chunksize=10" in repr_str
    
    def test_comparison_config_str(self):
        """Test ComparisonConfig readable string."""
        config = ComparisonConfig("Test", n_jobs=2, chunksize=10, executor_type="process")
        str_result = str(config)
        
        assert "Test" in str_result
        assert "2" in str_result
        assert "process" in str_result
    
    def test_comparison_config_serial(self):
        """Test ComparisonConfig for serial execution."""
        config = ComparisonConfig("Serial", n_jobs=1)
        str_result = str(config)
        
        assert "Serial" in str_result
        assert "Serial execution" in str_result
    
    def test_comparison_config_validation_n_jobs(self):
        """Test that invalid n_jobs raises error."""
        with pytest.raises(ValueError, match="n_jobs must be"):
            ComparisonConfig("Invalid", n_jobs=0)
        
        with pytest.raises(ValueError, match="n_jobs must be"):
            ComparisonConfig("Invalid", n_jobs=-1)
    
    def test_comparison_config_validation_chunksize(self):
        """Test that invalid chunksize raises error."""
        with pytest.raises(ValueError, match="chunksize must be"):
            ComparisonConfig("Invalid", n_jobs=2, chunksize=0)
        
        with pytest.raises(ValueError, match="chunksize must be"):
            ComparisonConfig("Invalid", n_jobs=2, chunksize=-5)
    
    def test_comparison_config_validation_executor_type(self):
        """Test that invalid executor_type raises error."""
        with pytest.raises(ValueError, match="executor_type must be"):
            ComparisonConfig("Invalid", n_jobs=2, executor_type="invalid")


class TestComparisonResult:
    """Tests for ComparisonResult class."""
    
    def test_comparison_result_creation(self):
        """Test that ComparisonResult can be created with all fields."""
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=50)
        ]
        times = [2.0, 1.0]
        speedups = [1.0, 2.0]
        
        result = ComparisonResult(
            configs=configs,
            execution_times=times,
            speedups=speedups,
            best_config_index=1,
            recommendations=["Test recommendation"]
        )
        
        assert len(result.configs) == 2
        assert result.best_config_index == 1
        assert result.best_config.name == "2 Workers"
        assert result.best_time == 1.0
        assert len(result.recommendations) == 1
    
    def test_comparison_result_repr(self):
        """Test ComparisonResult string representation."""
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=50)
        ]
        times = [2.0, 1.0]
        speedups = [1.0, 2.0]
        
        result = ComparisonResult(
            configs=configs,
            execution_times=times,
            speedups=speedups,
            best_config_index=1
        )
        
        repr_str = repr(result)
        assert "2 Workers" in repr_str
        assert "1.0000s" in repr_str
        assert "2.00x" in repr_str
    
    def test_comparison_result_str(self):
        """Test ComparisonResult full string output."""
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=50),
            ComparisonConfig("4 Workers", n_jobs=4, chunksize=25)
        ]
        times = [2.0, 1.0, 1.5]
        speedups = [1.0, 2.0, 1.33]
        
        result = ComparisonResult(
            configs=configs,
            execution_times=times,
            speedups=speedups,
            best_config_index=1,
            recommendations=["Consider larger dataset"]
        )
        
        str_result = str(result)
        assert "Strategy Comparison Results" in str_result
        assert "Serial" in str_result
        assert "2 Workers" in str_result
        assert "4 Workers" in str_result
        assert "FASTEST" in str_result
        assert "Consider larger dataset" in str_result
    
    def test_get_sorted_configs(self):
        """Test that get_sorted_configs returns configs sorted by time."""
        configs = [
            ComparisonConfig("Slow", n_jobs=1),
            ComparisonConfig("Fast", n_jobs=2, chunksize=50),
            ComparisonConfig("Medium", n_jobs=4, chunksize=25)
        ]
        times = [3.0, 1.0, 2.0]
        speedups = [1.0, 3.0, 1.5]
        
        result = ComparisonResult(
            configs=configs,
            execution_times=times,
            speedups=speedups,
            best_config_index=1
        )
        
        sorted_results = result.get_sorted_configs()
        
        # Should be sorted: Fast (1.0), Medium (2.0), Slow (3.0)
        assert len(sorted_results) == 3
        assert sorted_results[0][0].name == "Fast"
        assert sorted_results[1][0].name == "Medium"
        assert sorted_results[2][0].name == "Slow"


class TestCompareStrategies:
    """Tests for compare_strategies function."""
    
    def test_compare_strategies_basic(self):
        """Test basic strategy comparison."""
        data = range(100)
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=50)
        ]
        
        result = compare_strategies(simple_func, data, configs, verbose=False)
        
        assert isinstance(result, ComparisonResult)
        assert len(result.configs) == 2
        assert len(result.execution_times) == 2
        assert len(result.speedups) == 2
        assert result.best_config_index in [0, 1]
        assert result.best_config in configs
    
    def test_compare_strategies_multiple_configs(self):
        """Test comparison with multiple configurations."""
        data = range(50)
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=25),
            ComparisonConfig("4 Workers", n_jobs=4, chunksize=13)
        ]
        
        result = compare_strategies(func=slow_func, data=data, configs=configs, verbose=False)
        
        assert len(result.configs) == 3
        assert len(result.execution_times) == 3
        assert len(result.speedups) == 3
        assert result.best_config_index >= 0
        
        # Speedup should be calculated relative to first (serial) config
        baseline_time = result.execution_times[0]
        for i, (time, speedup) in enumerate(zip(result.execution_times, result.speedups)):
            expected_speedup = baseline_time / time if time > 0 else 1.0
            assert abs(speedup - expected_speedup) < 0.01
    
    def test_compare_strategies_with_max_items(self):
        """Test comparison with max_items limit."""
        data = range(1000)
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=50)
        ]
        
        result = compare_strategies(simple_func, data, configs, max_items=100, verbose=False)
        
        assert isinstance(result, ComparisonResult)
        # Should have benchmarked only 100 items
        assert len(result.execution_times) == 2
    
    def test_compare_strategies_threading(self):
        """Test comparison with threading executor."""
        data = range(20)
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Thread", n_jobs=2, executor_type="thread")
        ]
        
        result = compare_strategies(func=io_bound_func, data=data, configs=configs, verbose=False)
        
        assert isinstance(result, ComparisonResult)
        assert len(result.configs) == 2
        # Threading should work for I/O-bound tasks
        assert all(t > 0 for t in result.execution_times)
    
    def test_compare_strategies_mixed_executors(self):
        """Test comparison with both process and thread executors."""
        data = range(50)
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("Process", n_jobs=2, chunksize=25, executor_type="process"),
            ComparisonConfig("Thread", n_jobs=2, executor_type="thread")
        ]
        
        result = compare_strategies(simple_func, data, configs, verbose=False)
        
        assert len(result.configs) == 3
        assert len(result.execution_times) == 3
        # Should have recommendations about executor types
        assert len(result.recommendations) > 0
    
    def test_compare_strategies_validation_empty_configs(self):
        """Test that empty configs list raises error."""
        data = range(10)
        
        with pytest.raises(ValueError, match="configs cannot be empty"):
            compare_strategies(simple_func, data, [], verbose=False)
    
    def test_compare_strategies_validation_empty_data(self):
        """Test that empty data raises error."""
        data = []
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        with pytest.raises(ValueError, match="data cannot be empty"):
            compare_strategies(simple_func, data, configs, verbose=False)
    
    def test_compare_strategies_validation_timeout(self):
        """Test that invalid timeout raises error."""
        data = range(10)
        configs = [ComparisonConfig("Serial", n_jobs=1)]
        
        with pytest.raises(ValueError, match="timeout must be positive"):
            compare_strategies(simple_func, data, configs, timeout=-1, verbose=False)
    
    def test_compare_strategies_verbose_output(self, capsys):
        """Test that verbose mode prints output."""
        data = range(50)
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=25)
        ]
        
        result = compare_strategies(simple_func, data, configs, verbose=True)
        
        captured = capsys.readouterr()
        assert "Comparing" in captured.out
        assert "Testing:" in captured.out
        assert "Execution time:" in captured.out
    
    def test_compare_strategies_recommendations_serial_best(self):
        """Test recommendations when serial is fastest."""
        data = range(10)
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=5)
        ]
        
        result = compare_strategies(func=simple_func, data=data, configs=configs, verbose=False)
        
        # For very fast functions on small data, serial is likely best
        if result.best_config_index == 0:
            # Check for serial-specific recommendations
            assert any("Serial execution is fastest" in rec for rec in result.recommendations)


class TestCompareWithOptimizer:
    """Tests for compare_with_optimizer function."""
    
    def test_compare_with_optimizer_basic(self):
        """Test basic optimizer comparison."""
        def func(x):
            return x ** 2
        
        data = range(100)
        
        result, opt = compare_with_optimizer(func, data, verbose=False)
        
        assert isinstance(result, ComparisonResult)
        # Should have at least 2 configs: Serial + Optimizer
        assert len(result.configs) >= 2
        assert result.configs[0].name == "Serial"
        assert result.configs[1].name == "Optimizer"
        
        # Check that optimizer config matches optimization result
        optimizer_config = result.configs[1]
        assert optimizer_config.n_jobs == opt.n_jobs
        assert optimizer_config.chunksize == opt.chunksize
    
    def test_compare_with_optimizer_additional_configs(self):
        """Test optimizer comparison with additional configs."""
        data = range(50)
        additional = [
            ComparisonConfig("4 Workers", n_jobs=4, chunksize=13),
            ComparisonConfig("8 Workers", n_jobs=8, chunksize=7)
        ]
        
        result, opt = compare_with_optimizer(
            func=slow_func,
            data=data,
            additional_configs=additional,
            verbose=False
        )
        
        # Should have: Serial + Optimizer + 2 additional = 4 configs
        assert len(result.configs) == 4
        assert result.configs[0].name == "Serial"
        assert result.configs[1].name == "Optimizer"
        assert result.configs[2].name == "4 Workers"
        assert result.configs[3].name == "8 Workers"
    
    def test_compare_with_optimizer_verbose(self, capsys):
        """Test verbose output for optimizer comparison."""
        data = range(50)
        
        result, opt = compare_with_optimizer(simple_func, data, verbose=True)
        
        captured = capsys.readouterr()
        assert "Computing optimizer recommendation" in captured.out
        assert "Optimizer recommends" in captured.out
        assert "Predicted speedup" in captured.out
        assert "Comparing" in captured.out
    
    def test_compare_with_optimizer_max_items(self):
        """Test optimizer comparison with max_items limit."""
        data = range(1000)
        
        result, opt = compare_with_optimizer(simple_func, data, max_items=100, verbose=False)
        
        assert isinstance(result, ComparisonResult)
        # Benchmarking should be limited to 100 items
        assert len(result.configs) >= 2


class TestIntegration:
    """Integration tests for comparison mode."""
    
    def test_end_to_end_cpu_bound(self):
        """Test complete workflow for CPU-bound function."""
        data = range(50)
        
        # Compare several strategies
        configs = [
            ComparisonConfig("Serial", n_jobs=1),
            ComparisonConfig("2 Workers", n_jobs=2, chunksize=25),
            ComparisonConfig("4 Workers", n_jobs=4, chunksize=13)
        ]
        
        result = compare_strategies(cpu_intensive, data, configs, verbose=False)
        
        # Should complete successfully
        assert result.best_config is not None
        assert result.best_time > 0
        assert len(result.recommendations) > 0
        
        # Get sorted results
        sorted_results = result.get_sorted_configs()
        assert len(sorted_results) == 3
        # Fastest should be first
        assert sorted_results[0][1] <= sorted_results[1][1]
        assert sorted_results[1][1] <= sorted_results[2][1]
    
    def test_end_to_end_with_optimizer(self):
        """Test complete workflow comparing optimizer against alternatives."""
        def func(x):
            result = 0
            for i in range(300):
                result += x ** 2
            return result
        
        data = range(40)
        
        # Compare optimizer against fixed configs
        additional = [
            ComparisonConfig("Fixed 2", n_jobs=2, chunksize=20),
            ComparisonConfig("Fixed 4", n_jobs=4, chunksize=10)
        ]
        
        result, opt = compare_with_optimizer(
            medium_func, data,
            additional_configs=additional,
            verbose=False
        )
        
        # Should have optimizer recommendation
        assert opt.n_jobs >= 1
        assert opt.chunksize >= 1
        
        # Should have comparison results
        assert len(result.configs) == 4  # Serial + Optimizer + 2 additional
        assert result.best_config is not None
        
        # Optimizer should be reasonably competitive
        optimizer_idx = 1  # Second config is optimizer
        optimizer_time = result.execution_times[optimizer_idx]
        best_time = result.best_time
        
        # Optimizer should be within 2x of best (generous threshold for test stability)
        assert optimizer_time <= best_time * 2.0
