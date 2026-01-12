"""
Tests for the visualization module.

These tests verify that visualization functions work correctly with and
without matplotlib installed. Tests use mocking to avoid actually
generating image files during test runs.
"""

import pytest
import os
import tempfile
from pathlib import Path

# Import the module to test
from amorsize import visualization
from amorsize.comparison import ComparisonConfig, ComparisonResult


# Module-level function for picklability in tests
def _test_square(x):
    """Helper function for integration test (must be module-level for pickling)."""
    return x ** 2


class TestMatplotlibDetection:
    """Test matplotlib availability detection."""
    
    def test_check_matplotlib_returns_bool(self):
        """check_matplotlib() should return a boolean."""
        result = visualization.check_matplotlib()
        assert isinstance(result, bool)
    
    def test_has_matplotlib_constant_matches_check(self):
        """HAS_MATPLOTLIB constant should match check_matplotlib() result."""
        assert visualization.HAS_MATPLOTLIB == visualization.check_matplotlib()


class TestVisualizationWithoutMatplotlib:
    """Test visualization behavior when matplotlib is not available."""
    
    def test_require_matplotlib_decorator_raises_import_error(self):
        """Functions should raise ImportError if matplotlib is missing."""
        # Skip if matplotlib is actually available
        if visualization.HAS_MATPLOTLIB:
            pytest.skip("matplotlib is installed")
        
        with pytest.raises(ImportError, match="Matplotlib is required"):
            visualization.plot_comparison_times(["A", "B"], [1.0, 2.0])
    
    def test_visualize_comparison_result_warns_without_matplotlib(self):
        """visualize_comparison_result should warn if matplotlib is missing."""
        # Skip if matplotlib is actually available
        if visualization.HAS_MATPLOTLIB:
            pytest.skip("matplotlib is installed")
        
        # Create a dummy comparison result
        configs = [
            ComparisonConfig("Serial", 1, 1, "serial"),
            ComparisonConfig("Parallel", 4, 10, "process")
        ]
        result = ComparisonResult(
            configs=configs,
            execution_times=[10.0, 3.0],
            speedups=[1.0, 3.33],
            best_config_index=1
        )
        
        with pytest.warns(UserWarning, match="Matplotlib is not available"):
            plot_paths = visualization.visualize_comparison_result(result)
        
        assert plot_paths == {}


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotComparisonTimes:
    """Test plot_comparison_times function."""
    
    def test_basic_usage(self):
        """Should generate a plot with basic inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_times.png")
            
            config_names = ["Serial", "4 workers", "8 workers"]
            execution_times = [10.0, 3.2, 2.1]
            
            result_path = visualization.plot_comparison_times(
                config_names,
                execution_times,
                output_path=output_path
            )
            
            assert result_path == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_default_output_path(self):
        """Should use default filename if output_path is None."""
        config_names = ["A", "B"]
        execution_times = [5.0, 3.0]
        
        result_path = visualization.plot_comparison_times(
            config_names,
            execution_times,
            output_path=None
        )
        
        assert result_path == "amorsize_comparison_times.png"
        # Clean up
        if os.path.exists(result_path):
            os.remove(result_path)
    
    def test_empty_configs_raises_error(self):
        """Should raise ValueError for empty configs."""
        with pytest.raises(ValueError, match="At least one configuration"):
            visualization.plot_comparison_times([], [])
    
    def test_mismatched_lengths_raises_error(self):
        """Should raise ValueError if lengths don't match."""
        with pytest.raises(ValueError, match="must have same length"):
            visualization.plot_comparison_times(
                ["A", "B"],
                [1.0, 2.0, 3.0]  # Wrong length
            )
    
    def test_custom_title_and_figsize(self):
        """Should accept custom title and figsize."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "custom.png")
            
            result_path = visualization.plot_comparison_times(
                ["A", "B"],
                [1.0, 2.0],
                output_path=output_path,
                title="Custom Title",
                figsize=(12, 8)
            )
            
            assert os.path.exists(result_path)
    
    def test_show_values_parameter(self):
        """Should work with show_values=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "no_values.png")
            
            result_path = visualization.plot_comparison_times(
                ["A", "B"],
                [1.0, 2.0],
                output_path=output_path,
                show_values=False
            )
            
            assert os.path.exists(result_path)


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotSpeedupComparison:
    """Test plot_speedup_comparison function."""
    
    def test_basic_usage(self):
        """Should generate a speedup plot with basic inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_speedup.png")
            
            config_names = ["Serial", "4 workers", "8 workers"]
            speedups = [1.0, 3.1, 4.8]
            
            result_path = visualization.plot_speedup_comparison(
                config_names,
                speedups,
                output_path=output_path
            )
            
            assert result_path == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_speedup_coloring(self):
        """Should handle different speedup ranges (affects colors)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "speedup_colors.png")
            
            # Test all color ranges: < 1.0 (red), < 1.2 (orange), < 2.0 (yellow), >= 2.0 (green)
            config_names = ["Slow", "Marginal", "Moderate", "Fast"]
            speedups = [0.8, 1.1, 1.5, 3.0]
            
            result_path = visualization.plot_speedup_comparison(
                config_names,
                speedups,
                output_path=output_path
            )
            
            assert os.path.exists(result_path)
    
    def test_empty_configs_raises_error(self):
        """Should raise ValueError for empty configs."""
        with pytest.raises(ValueError, match="At least one configuration"):
            visualization.plot_speedup_comparison([], [])
    
    def test_mismatched_lengths_raises_error(self):
        """Should raise ValueError if lengths don't match."""
        with pytest.raises(ValueError, match="must have same length"):
            visualization.plot_speedup_comparison(
                ["A", "B"],
                [1.0, 2.0, 3.0]  # Wrong length
            )
    
    def test_custom_baseline_name(self):
        """Should accept custom baseline name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "custom_baseline.png")
            
            result_path = visualization.plot_speedup_comparison(
                ["A", "B"],
                [1.0, 2.0],
                output_path=output_path,
                baseline_name="Custom Baseline"
            )
            
            assert os.path.exists(result_path)


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotOverheadBreakdown:
    """Test plot_overhead_breakdown function."""
    
    def test_basic_usage(self):
        """Should generate an overhead breakdown plot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_overhead.png")
            
            n_workers_list = [1, 2, 4, 8]
            compute_times = [10.0, 5.0, 2.5, 1.3]
            spawn_overheads = [0.0, 0.03, 0.06, 0.12]
            ipc_overheads = [0.0, 0.05, 0.10, 0.20]
            chunking_overheads = [0.0, 0.02, 0.04, 0.08]
            
            result_path = visualization.plot_overhead_breakdown(
                n_workers_list,
                compute_times,
                spawn_overheads,
                ipc_overheads,
                chunking_overheads,
                output_path=output_path
            )
            
            assert result_path == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_empty_data_raises_error(self):
        """Should raise ValueError for empty data."""
        with pytest.raises(ValueError, match="At least one data point"):
            visualization.plot_overhead_breakdown([], [], [], [], [])
    
    def test_mismatched_lengths_raises_error(self):
        """Should raise ValueError if lengths don't match."""
        with pytest.raises(ValueError, match="must have the same length"):
            visualization.plot_overhead_breakdown(
                [1, 2],
                [1.0, 2.0],
                [0.1],  # Wrong length
                [0.2, 0.3],
                [0.1, 0.2]
            )


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestPlotScalingCurve:
    """Test plot_scaling_curve function."""
    
    def test_basic_usage(self):
        """Should generate a scaling curve plot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_scaling.png")
            
            n_workers_list = [1, 2, 4, 8, 16]
            execution_times = [10.0, 5.5, 3.2, 2.0, 1.5]
            
            result_path = visualization.plot_scaling_curve(
                n_workers_list,
                execution_times,
                output_path=output_path
            )
            
            assert result_path == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
    
    def test_with_theoretical_speedups(self):
        """Should include theoretical speedup curve if provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_with_theory.png")
            
            n_workers_list = [1, 2, 4, 8]
            execution_times = [10.0, 5.5, 3.2, 2.0]
            theoretical = [10.0, 5.0, 2.5, 1.25]
            
            result_path = visualization.plot_scaling_curve(
                n_workers_list,
                execution_times,
                theoretical_speedups=theoretical,
                output_path=output_path
            )
            
            assert os.path.exists(result_path)
    
    def test_mismatched_theoretical_length_warns(self):
        """Should warn if theoretical speedups length doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "scaling_mismatch.png")
            
            with pytest.warns(UserWarning, match="length doesn't match"):
                result_path = visualization.plot_scaling_curve(
                    [1, 2, 4],
                    [10.0, 5.5, 3.2],
                    theoretical_speedups=[10.0, 5.0],  # Wrong length
                    output_path=output_path
                )
            
            assert os.path.exists(result_path)
    
    def test_empty_data_raises_error(self):
        """Should raise ValueError for empty data."""
        with pytest.raises(ValueError, match="At least one data point"):
            visualization.plot_scaling_curve([], [])
    
    def test_mismatched_lengths_raises_error(self):
        """Should raise ValueError if lengths don't match."""
        with pytest.raises(ValueError, match="must have same length"):
            visualization.plot_scaling_curve(
                [1, 2],
                [1.0, 2.0, 3.0]  # Wrong length
            )


@pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
class TestVisualizeComparisonResult:
    """Test visualize_comparison_result function."""
    
    def test_basic_usage(self):
        """Should generate all plots for a comparison result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a comparison result
            configs = [
                ComparisonConfig("Serial", 1, 1, "serial"),
                ComparisonConfig("2 workers", 2, 20, "process"),
                ComparisonConfig("4 workers", 4, 10, "process")
            ]
            result = ComparisonResult(
                configs=configs,
                execution_times=[10.0, 5.5, 3.2],
                speedups=[1.0, 1.82, 3.13],
                best_config_index=2
            )
            
            plot_paths = visualization.visualize_comparison_result(
                result,
                output_dir=tmpdir
            )
            
            # Should generate 'times' and 'speedups' plots
            assert 'times' in plot_paths
            assert 'speedups' in plot_paths
            
            # Check files exist
            if plot_paths['times']:
                assert os.path.exists(plot_paths['times'])
            if plot_paths['speedups']:
                assert os.path.exists(plot_paths['speedups'])
    
    def test_creates_output_directory(self):
        """Should create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "nested", "output")
            
            configs = [
                ComparisonConfig("A", 1),
                ComparisonConfig("B", 2)
            ]
            result = ComparisonResult(
                configs=configs,
                execution_times=[5.0, 3.0],
                speedups=[1.0, 1.67],
                best_config_index=1
            )
            
            plot_paths = visualization.visualize_comparison_result(
                result,
                output_dir=nested_dir
            )
            
            assert os.path.exists(nested_dir)
            assert len(plot_paths) > 0
    
    def test_custom_plot_selection(self):
        """Should allow selecting specific plots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = [
                ComparisonConfig("A", 1),
                ComparisonConfig("B", 2)
            ]
            result = ComparisonResult(
                configs=configs,
                execution_times=[5.0, 3.0],
                speedups=[1.0, 1.67],
                best_config_index=1
            )
            
            # Only generate 'times' plot
            plot_paths = visualization.visualize_comparison_result(
                result,
                output_dir=tmpdir,
                plots=['times']
            )
            
            assert 'times' in plot_paths
            assert 'speedups' not in plot_paths
    
    def test_all_plots_option(self):
        """Should generate all plots when 'all' is specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = [
                ComparisonConfig("A", 1),
                ComparisonConfig("B", 2)
            ]
            result = ComparisonResult(
                configs=configs,
                execution_times=[5.0, 3.0],
                speedups=[1.0, 1.67],
                best_config_index=1
            )
            
            plot_paths = visualization.visualize_comparison_result(
                result,
                output_dir=tmpdir,
                plots=['all']
            )
            
            # Should have both plots
            assert 'times' in plot_paths
            assert 'speedups' in plot_paths


class TestIntegration:
    """Integration tests for visualization with comparison module."""
    
    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_end_to_end_workflow(self):
        """Test complete workflow from comparison to visualization."""
        from amorsize import compare_strategies
        
        data = range(100)
        
        configs = [
            ComparisonConfig("Serial", 1, 1, "serial"),
            ComparisonConfig("Parallel", 2, 10, "process")
        ]
        
        # Run comparison with module-level function (picklable)
        result = compare_strategies(_test_square, data, configs, verbose=False)
        
        # Generate visualizations
        with tempfile.TemporaryDirectory() as tmpdir:
            plot_paths = visualization.visualize_comparison_result(
                result,
                output_dir=tmpdir
            )
            
            # Verify plots were created
            assert len(plot_paths) > 0
            for path in plot_paths.values():
                if path:
                    assert os.path.exists(path)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_single_config_visualization(self):
        """Should handle visualization with single config (no comparison)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "single.png")
            
            # Single config - just test it doesn't crash
            result_path = visualization.plot_comparison_times(
                ["Only Config"],
                [5.0],
                output_path=output_path
            )
            
            assert os.path.exists(result_path)
    
    @pytest.mark.skipif(not visualization.HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_very_long_config_names(self):
        """Should handle very long configuration names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "long_names.png")
            
            long_names = [
                "This is an extremely long configuration name that might cause layout issues",
                "Another very long name for testing purposes"
            ]
            
            result_path = visualization.plot_comparison_times(
                long_names,
                [5.0, 3.0],
                output_path=output_path
            )
            
            assert os.path.exists(result_path)
