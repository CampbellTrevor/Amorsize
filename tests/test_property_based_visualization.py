"""
Property-based tests for the visualization module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the visualization functions across a wide range of inputs. Tests handle
matplotlib's optional dependency gracefully.
"""

import os
import tempfile
from pathlib import Path
from typing import List
from unittest import mock

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize import visualization
from amorsize.comparison import ComparisonConfig, ComparisonResult


# Custom strategies for generating test data
@st.composite
def valid_config_names(draw, min_size=1, max_size=10):
    """Generate valid configuration name lists."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    # Configuration names can be any non-empty string
    names = draw(st.lists(
        st.text(min_size=1, max_size=50),
        min_size=size,
        max_size=size,
        unique=True
    ))
    return names


@st.composite
def valid_execution_times(draw, size):
    """Generate valid execution time lists (positive floats)."""
    # Execution times must be positive
    times = draw(st.lists(
        st.floats(min_value=0.001, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    return times


@st.composite
def valid_speedups(draw, size):
    """Generate valid speedup lists (positive floats, typically 0.1x to 100x)."""
    speedups = draw(st.lists(
        st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    return speedups


@st.composite
def valid_worker_counts(draw, min_size=1, max_size=10):
    """Generate valid worker count lists."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    # Worker counts must be positive integers
    workers = draw(st.lists(
        st.integers(min_value=1, max_value=128),
        min_size=size,
        max_size=size,
        unique=True
    ))
    return sorted(workers)  # Typically sorted for visualization


@st.composite
def valid_overhead_times(draw, size):
    """Generate valid overhead time lists (non-negative floats)."""
    # Overhead times can be zero or positive
    times = draw(st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    return times


@st.composite
def valid_figsize(draw):
    """Generate valid matplotlib figure sizes."""
    width = draw(st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False))
    height = draw(st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False))
    return (width, height)


@st.composite
def valid_comparison_result(draw):
    """Generate valid ComparisonResult objects."""
    size = draw(st.integers(min_value=1, max_value=10))
    
    config_names = draw(st.lists(
        st.text(min_size=1, max_size=30),
        min_size=size,
        max_size=size,
        unique=True
    ))
    
    execution_times = draw(st.lists(
        st.floats(min_value=0.001, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    
    speedups = draw(st.lists(
        st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    
    # Create ComparisonConfig objects
    configs = []
    for i, name in enumerate(config_names):
        n_jobs = draw(st.integers(min_value=1, max_value=32))
        chunksize = draw(st.integers(min_value=1, max_value=1000))
        method = draw(st.sampled_from(['serial', 'process', 'thread']))
        config = ComparisonConfig(name, n_jobs, chunksize, method)
        configs.append(config)
    
    best_idx = draw(st.integers(min_value=0, max_value=size-1))
    
    return ComparisonResult(
        configs=configs,
        execution_times=execution_times,
        speedups=speedups,
        best_config_index=best_idx
    )


class TestMatplotlibDetectionInvariants:
    """Test invariant properties of matplotlib detection."""

    @given(st.integers())
    @settings(max_examples=10)
    def test_check_matplotlib_always_returns_bool(self, _):
        """check_matplotlib() should always return a boolean."""
        result = visualization.check_matplotlib()
        assert isinstance(result, bool)

    @given(st.integers())
    @settings(max_examples=10)
    def test_has_matplotlib_constant_is_bool(self, _):
        """HAS_MATPLOTLIB constant should always be a boolean."""
        assert isinstance(visualization.HAS_MATPLOTLIB, bool)

    @given(st.integers())
    @settings(max_examples=10)
    def test_has_matplotlib_matches_check(self, _):
        """HAS_MATPLOTLIB constant should match check_matplotlib() result."""
        assert visualization.HAS_MATPLOTLIB == visualization.check_matplotlib()


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotComparisonTimesInvariants:
    """Test invariant properties of plot_comparison_times function."""

    @given(
        names=valid_config_names(min_size=1, max_size=5),
        data=st.data()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_path_on_success(self, names, data):
        """plot_comparison_times should return a path string on success."""
        times = data.draw(valid_execution_times(len(names)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_comparison_times(
                names,
                times,
                output_path=output_path
            )
            
            # Should return the output path
            assert result == output_path
            # File should exist
            assert os.path.exists(output_path)
            # File should have content
            assert os.path.getsize(output_path) > 0

    @given(
        names=valid_config_names(min_size=1, max_size=5),
        data=st.data(),
        show_values=st.booleans()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_respects_show_values_parameter(self, names, data, show_values):
        """plot_comparison_times should respect show_values parameter."""
        times = data.draw(valid_execution_times(len(names)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_comparison_times(
                names,
                times,
                output_path=output_path,
                show_values=show_values
            )
            
            # Should succeed regardless of show_values
            assert result == output_path
            assert os.path.exists(output_path)

    @given(
        names=valid_config_names(min_size=1, max_size=5),
        data=st.data(),
        figsize=valid_figsize()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_accepts_various_figsize_values(self, names, data, figsize):
        """plot_comparison_times should accept various figsize values."""
        times = data.draw(valid_execution_times(len(names)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_comparison_times(
                names,
                times,
                output_path=output_path,
                figsize=figsize
            )
            
            assert result == output_path
            assert os.path.exists(output_path)

    @given(
        names1=valid_config_names(min_size=2, max_size=3),
        names2=valid_config_names(min_size=2, max_size=3),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_input_length_mismatch_raises_error(self, names1, names2, data):
        """plot_comparison_times should raise ValueError when input lengths differ."""
        # Ensure different lengths
        assume(len(names1) != len(names2))
        
        times = data.draw(valid_execution_times(len(names2)))
        
        with pytest.raises(ValueError, match="must have same length"):
            visualization.plot_comparison_times(names1, times)

    @given(st.just([]))
    @settings(max_examples=5)
    def test_empty_input_raises_error(self, empty_list):
        """plot_comparison_times should raise ValueError for empty inputs."""
        with pytest.raises(ValueError, match="At least one configuration is required"):
            visualization.plot_comparison_times(empty_list, empty_list)

    @given(
        names=valid_config_names(min_size=1, max_size=5),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_default_output_path_when_none(self, names, data):
        """plot_comparison_times should use default path when output_path is None."""
        times = data.draw(valid_execution_times(len(names)))
        
        # Mock plt.savefig to avoid creating files
        with mock.patch('amorsize.visualization.plt.savefig') as mock_savefig:
            with mock.patch('amorsize.visualization.plt.close'):
                mock_savefig.return_value = None
                
                result = visualization.plot_comparison_times(
                    names,
                    times,
                    output_path=None
                )
                
                # Should return default filename
                assert result == "amorsize_comparison_times.png"
                # Should have called savefig with that path
                mock_savefig.assert_called_once()
                args, _ = mock_savefig.call_args
                assert args[0] == "amorsize_comparison_times.png"


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotSpeedupComparisonInvariants:
    """Test invariant properties of plot_speedup_comparison function."""

    @given(
        names=valid_config_names(min_size=1, max_size=5),
        data=st.data()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_path_on_success(self, names, data):
        """plot_speedup_comparison should return a path string on success."""
        speedups = data.draw(valid_speedups(len(names)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_speedup_comparison(
                names,
                speedups,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

    @given(
        names=valid_config_names(min_size=1, max_size=5),
        data=st.data(),
        show_values=st.booleans()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_respects_show_values_parameter(self, names, data, show_values):
        """plot_speedup_comparison should respect show_values parameter."""
        speedups = data.draw(valid_speedups(len(names)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_speedup_comparison(
                names,
                speedups,
                output_path=output_path,
                show_values=show_values
            )
            
            assert result == output_path
            assert os.path.exists(output_path)

    @given(
        names=valid_config_names(min_size=1, max_size=5),
        data=st.data(),
        baseline_name=st.text(min_size=1, max_size=20)
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_accepts_custom_baseline_name(self, names, data, baseline_name):
        """plot_speedup_comparison should accept custom baseline names."""
        speedups = data.draw(valid_speedups(len(names)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_speedup_comparison(
                names,
                speedups,
                output_path=output_path,
                baseline_name=baseline_name
            )
            
            assert result == output_path
            assert os.path.exists(output_path)

    @given(
        names1=valid_config_names(min_size=2, max_size=3),
        names2=valid_config_names(min_size=2, max_size=3),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_input_length_mismatch_raises_error(self, names1, names2, data):
        """plot_speedup_comparison should raise ValueError when input lengths differ."""
        assume(len(names1) != len(names2))
        
        speedups = data.draw(valid_speedups(len(names2)))
        
        with pytest.raises(ValueError, match="must have same length"):
            visualization.plot_speedup_comparison(names1, speedups)

    @given(st.just([]))
    @settings(max_examples=5)
    def test_empty_input_raises_error(self, empty_list):
        """plot_speedup_comparison should raise ValueError for empty inputs."""
        with pytest.raises(ValueError, match="At least one configuration is required"):
            visualization.plot_speedup_comparison(empty_list, empty_list)


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotOverheadBreakdownInvariants:
    """Test invariant properties of plot_overhead_breakdown function."""

    @given(
        workers=valid_worker_counts(min_size=1, max_size=5),
        data=st.data()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_path_on_success(self, workers, data):
        """plot_overhead_breakdown should return a path string on success."""
        size = len(workers)
        compute = data.draw(valid_overhead_times(size))
        spawn = data.draw(valid_overhead_times(size))
        ipc = data.draw(valid_overhead_times(size))
        chunking = data.draw(valid_overhead_times(size))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_overhead_breakdown(
                workers,
                compute,
                spawn,
                ipc,
                chunking,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

    @given(
        workers=valid_worker_counts(min_size=2, max_size=4),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_lists_must_have_same_length(self, workers, data):
        """plot_overhead_breakdown should raise ValueError if lists have different lengths."""
        size = len(workers)
        compute = data.draw(valid_overhead_times(size))
        spawn = data.draw(valid_overhead_times(size))
        ipc = data.draw(valid_overhead_times(size))
        # Make chunking have different length
        wrong_size = size + 1
        chunking = data.draw(valid_overhead_times(wrong_size))
        
        with pytest.raises(ValueError, match="must have the same length"):
            visualization.plot_overhead_breakdown(
                workers, compute, spawn, ipc, chunking
            )

    @given(st.just([]))
    @settings(max_examples=5)
    def test_empty_input_raises_error(self, empty_list):
        """plot_overhead_breakdown should raise ValueError for empty inputs."""
        with pytest.raises(ValueError, match="At least one data point is required"):
            visualization.plot_overhead_breakdown(
                empty_list, empty_list, empty_list, empty_list, empty_list
            )

    @given(
        workers=valid_worker_counts(min_size=1, max_size=5),
        data=st.data(),
        figsize=valid_figsize()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_accepts_various_figsize_values(self, workers, data, figsize):
        """plot_overhead_breakdown should accept various figsize values."""
        size = len(workers)
        compute = data.draw(valid_overhead_times(size))
        spawn = data.draw(valid_overhead_times(size))
        ipc = data.draw(valid_overhead_times(size))
        chunking = data.draw(valid_overhead_times(size))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_overhead_breakdown(
                workers,
                compute,
                spawn,
                ipc,
                chunking,
                output_path=output_path,
                figsize=figsize
            )
            
            assert result == output_path
            assert os.path.exists(output_path)


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotScalingCurveInvariants:
    """Test invariant properties of plot_scaling_curve function."""

    @given(
        workers=valid_worker_counts(min_size=1, max_size=5),
        data=st.data()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_path_on_success(self, workers, data):
        """plot_scaling_curve should return a path string on success."""
        times = data.draw(valid_execution_times(len(workers)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_scaling_curve(
                workers,
                times,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

    @given(
        workers=valid_worker_counts(min_size=1, max_size=5),
        data=st.data()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_accepts_theoretical_speedups(self, workers, data):
        """plot_scaling_curve should accept optional theoretical speedup data."""
        times = data.draw(valid_execution_times(len(workers)))
        theoretical = data.draw(valid_execution_times(len(workers)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_scaling_curve(
                workers,
                times,
                theoretical_speedups=theoretical,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)

    @given(
        workers1=valid_worker_counts(min_size=2, max_size=3),
        workers2=valid_worker_counts(min_size=2, max_size=3),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_input_length_mismatch_raises_error(self, workers1, workers2, data):
        """plot_scaling_curve should raise ValueError when input lengths differ."""
        assume(len(workers1) != len(workers2))
        
        times = data.draw(valid_execution_times(len(workers2)))
        
        with pytest.raises(ValueError, match="must have same length"):
            visualization.plot_scaling_curve(workers1, times)

    @given(st.just([]))
    @settings(max_examples=5)
    def test_empty_input_raises_error(self, empty_list):
        """plot_scaling_curve should raise ValueError for empty inputs."""
        with pytest.raises(ValueError, match="At least one data point is required"):
            visualization.plot_scaling_curve(empty_list, empty_list)

    @given(
        workers=valid_worker_counts(min_size=3, max_size=5),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_uses_log_scale_for_large_ranges(self, workers, data):
        """plot_scaling_curve should use log scale when time range is large."""
        # Create times with large range (>10x difference)
        min_time = data.draw(st.floats(min_value=0.01, max_value=0.1, allow_nan=False, allow_infinity=False))
        max_time = min_time * data.draw(st.floats(min_value=15.0, max_value=100.0, allow_nan=False, allow_infinity=False))
        
        # Generate times with this range
        times = [max_time]
        for _ in range(len(workers) - 1):
            time = data.draw(st.floats(min_value=min_time, max_value=max_time, allow_nan=False, allow_infinity=False))
            times.append(time)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_scaling_curve(
                workers,
                times,
                output_path=output_path
            )
            
            # Should still succeed (log scale is automatic)
            assert result == output_path
            assert os.path.exists(output_path)


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestVisualizeComparisonResultInvariants:
    """Test invariant properties of visualize_comparison_result function."""

    @given(comparison_result=valid_comparison_result())
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_dict_of_paths(self, comparison_result):
        """visualize_comparison_result should return dict mapping plot type to path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = visualization.visualize_comparison_result(
                comparison_result,
                output_dir=tmpdir
            )
            
            # Should return a dictionary
            assert isinstance(result, dict)
            
            # Should contain both 'times' and 'speedups' keys
            assert 'times' in result
            assert 'speedups' in result
            
            # Paths should exist if generation succeeded
            for plot_type, path in result.items():
                if path is not None:
                    assert os.path.exists(path)
                    assert os.path.getsize(path) > 0

    @given(
        comparison_result=valid_comparison_result(),
        plots=st.lists(st.sampled_from(['times', 'speedups', 'all']), min_size=1, max_size=3, unique=True)
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_respects_plots_parameter(self, comparison_result, plots):
        """visualize_comparison_result should respect plots parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = visualization.visualize_comparison_result(
                comparison_result,
                output_dir=tmpdir,
                plots=plots
            )
            
            # Should return a dictionary
            assert isinstance(result, dict)
            
            # If 'all' in plots, should have both types
            if 'all' in plots:
                assert 'times' in result or 'speedups' in result
            else:
                # Should only have requested types
                for plot_type in plots:
                    if plot_type in ['times', 'speedups']:
                        assert plot_type in result

    @given(comparison_result=valid_comparison_result())
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_creates_output_directory_if_needed(self, comparison_result):
        """visualize_comparison_result should create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested directory path that doesn't exist yet
            nested_dir = os.path.join(tmpdir, "nested", "subdir")
            
            result = visualization.visualize_comparison_result(
                comparison_result,
                output_dir=nested_dir
            )
            
            # Directory should have been created
            assert os.path.exists(nested_dir)
            
            # Should have generated plots
            assert isinstance(result, dict)
            assert len(result) > 0

    @given(comparison_result=valid_comparison_result())
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_uses_current_directory_when_none(self, comparison_result):
        """visualize_comparison_result should use current directory when output_dir is None."""
        # Mock the plotting functions to avoid creating files
        with mock.patch('amorsize.visualization.plot_comparison_times') as mock_times:
            with mock.patch('amorsize.visualization.plot_speedup_comparison') as mock_speedups:
                mock_times.return_value = "comparison_times.png"
                mock_speedups.return_value = "speedup_comparison.png"
                
                result = visualization.visualize_comparison_result(
                    comparison_result,
                    output_dir=None
                )
                
                # Should have called the plotting functions with simple filenames
                assert mock_times.called
                assert mock_speedups.called
                
                # Check that paths don't include directory separators
                times_call = mock_times.call_args
                speedups_call = mock_speedups.call_args
                
                # Extract output_path parameter
                assert 'output_path' in times_call.kwargs or len(times_call.args) > 2
                assert 'output_path' in speedups_call.kwargs or len(speedups_call.args) > 2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @given(st.integers())
    @settings(max_examples=10)
    def test_check_matplotlib_is_deterministic(self, _):
        """check_matplotlib() should return the same value on repeated calls."""
        first_call = visualization.check_matplotlib()
        second_call = visualization.check_matplotlib()
        assert first_call == second_call

    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    @given(
        names=st.just(["A"]),
        times=st.just([1.0])
    )
    @settings(max_examples=5)
    def test_single_data_point_works(self, names, times):
        """Visualization functions should work with a single data point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_comparison_times(
                names,
                times,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)

    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    @given(
        names=valid_config_names(min_size=2, max_size=5),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_identical_times_dont_break_plotting(self, names, data):
        """Visualization should handle identical execution times gracefully."""
        # All times are the same
        time_value = data.draw(st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False))
        times = [time_value] * len(names)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_comparison_times(
                names,
                times,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)


class TestNumericalStability:
    """Test numerical stability with various input ranges."""

    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    @given(
        names=valid_config_names(min_size=2, max_size=4),
        data=st.data()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_very_small_times(self, names, data):
        """Visualization should handle very small execution times."""
        # Generate very small times (microsecond range)
        times = data.draw(st.lists(
            st.floats(min_value=0.000001, max_value=0.001, allow_nan=False, allow_infinity=False),
            min_size=len(names),
            max_size=len(names)
        ))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_comparison_times(
                names,
                times,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)

    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    @given(
        names=valid_config_names(min_size=2, max_size=4),
        data=st.data()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_very_large_times(self, names, data):
        """Visualization should handle very large execution times."""
        # Generate very large times (hours range)
        times = data.draw(st.lists(
            st.floats(min_value=1000.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
            min_size=len(names),
            max_size=len(names)
        ))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            
            result = visualization.plot_comparison_times(
                names,
                times,
                output_path=output_path
            )
            
            assert result == output_path
            assert os.path.exists(output_path)


class TestIntegrationProperties:
    """Test integration properties across multiple functions."""

    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    @given(comparison_result=valid_comparison_result())
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_full_workflow_with_comparison_result(self, comparison_result):
        """Test the full visualization workflow with ComparisonResult."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate all plots
            result = visualization.visualize_comparison_result(
                comparison_result,
                output_dir=tmpdir
            )
            
            # Should have created both plot types
            assert isinstance(result, dict)
            assert len(result) >= 1  # At least one plot type
            
            # All returned paths should exist and have content
            for plot_type, path in result.items():
                if path is not None:
                    assert os.path.exists(path)
                    assert os.path.getsize(path) > 0
                    # Path should be in the output directory
                    assert tmpdir in path

    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    @given(
        names=valid_config_names(min_size=2, max_size=4),
        data=st.data()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_plots_can_be_created_consecutively(self, names, data):
        """Test that multiple plots can be created one after another."""
        times = data.draw(valid_execution_times(len(names)))
        speedups = data.draw(valid_speedups(len(names)))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first plot
            path1 = os.path.join(tmpdir, "plot1.png")
            result1 = visualization.plot_comparison_times(
                names,
                times,
                output_path=path1
            )
            
            # Create second plot
            path2 = os.path.join(tmpdir, "plot2.png")
            result2 = visualization.plot_speedup_comparison(
                names,
                speedups,
                output_path=path2
            )
            
            # Both should succeed
            assert result1 == path1
            assert result2 == path2
            assert os.path.exists(path1)
            assert os.path.exists(path2)
            
            # Files should have different content
            assert os.path.getsize(path1) > 0
            assert os.path.getsize(path2) > 0
