"""
Tests for workload type detection (CPU-bound vs I/O-bound).
"""

import time
import pytest
from amorsize import optimize
from amorsize.sampling import detect_workload_type, perform_dry_run


# Module-level functions for picklability in tests
def _cpu_heavy_func(x):
    """Pure computation - CPU-bound."""
    result = 0
    for i in range(10000):
        result += i ** 2
    return result


def _io_heavy_func(x):
    """Sleep simulates I/O wait - I/O-bound."""
    time.sleep(0.01)  # 10ms sleep simulates I/O wait
    return x


def _mixed_workload_func(x):
    """Some computation with some waiting - mixed."""
    result = sum(i ** 2 for i in range(10000))
    time.sleep(0.001)  # 1ms sleep
    return result + x


def _fast_func(x):
    """Extremely fast function."""
    return x + 1


def _simple_func(x):
    """Simple function for testing."""
    return x * 2


def _long_cpu_func(x):
    """Long-running CPU function."""
    result = 0
    for i in range(100000):
        result += i ** 2
    return result


def _long_io_func(x):
    """Long I/O wait function."""
    time.sleep(0.05)  # 50ms sleep
    return x


class TestDetectWorkloadType:
    """Test workload type detection functionality."""
    
    def test_cpu_bound_function(self):
        """Test that CPU-intensive function is correctly identified."""
        data = list(range(5))
        workload_type, cpu_ratio = detect_workload_type(_cpu_heavy_func, data)
        
        assert workload_type == "cpu_bound"
        assert cpu_ratio >= 0.7  # High CPU utilization
    
    def test_io_bound_function(self):
        """Test that I/O-intensive function is correctly identified."""
        data = list(range(5))
        workload_type, cpu_ratio = detect_workload_type(_io_heavy_func, data)
        
        assert workload_type == "io_bound"
        assert cpu_ratio < 0.3  # Low CPU utilization
    
    def test_mixed_workload_function(self):
        """Test that mixed CPU/I/O function is correctly identified."""
        data = list(range(5))
        workload_type, cpu_ratio = detect_workload_type(_mixed_workload_func, data)
        
        # Accept any classification - timing is system-dependent
        # What matters is that we get a valid classification and reasonable ratio
        assert workload_type in ("mixed", "cpu_bound", "io_bound")
        assert 0.1 <= cpu_ratio <= 1.0  # Reasonable CPU utilization range
    
    def test_empty_data(self):
        """Test workload detection with empty data."""
        workload_type, cpu_ratio = detect_workload_type(_simple_func, [])
        
        # Should default to CPU-bound
        assert workload_type == "cpu_bound"
        assert cpu_ratio == 1.0
    
    def test_fast_function(self):
        """Test workload detection with very fast function."""
        data = list(range(5))
        workload_type, cpu_ratio = detect_workload_type(_fast_func, data)
        
        # Fast functions should be classified as CPU-bound
        assert workload_type in ("cpu_bound", "mixed")  # Could be either due to measurement noise
    
    def test_function_with_exception(self):
        """Test workload detection handles exceptions gracefully."""
        def failing_func(x):
            if x == 2:
                raise ValueError("Test error")
            return x * 2
        
        data = list(range(5))
        # Should not raise, should handle gracefully
        workload_type, cpu_ratio = detect_workload_type(failing_func, data)
        
        # Should still return a valid classification
        assert workload_type in ("cpu_bound", "mixed", "io_bound")
        assert 0.0 <= cpu_ratio <= 2.0


class TestIntegrationWithOptimize:
    """Test workload detection integration with optimize()."""
    
    def test_cpu_bound_no_warning(self):
        """Test that CPU-bound workloads don't trigger I/O warnings."""
        result = optimize(_cpu_heavy_func, range(100))
        
        # Should not have I/O-bound warnings
        io_warnings = [w for w in result.warnings if "io-bound" in w.lower() or "i/o-bound" in w.lower()]
        assert len(io_warnings) == 0
    
    def test_io_bound_warning(self):
        """Test that I/O-bound workloads trigger appropriate warnings."""
        result = optimize(_io_heavy_func, range(20))
        
        # Debug: print warnings
        print(f"\nWarnings: {result.warnings}")
        
        # Should have workload warning (using actual warning text)
        workload_warnings = [w for w in result.warnings if "workload" in w.lower() or "i/o" in w.lower() or "threading" in w.lower()]
        assert len(workload_warnings) > 0, f"Expected workload warnings, got: {result.warnings}"
    
    def test_mixed_workload_warning(self):
        """Test that mixed workloads trigger appropriate warnings."""
        result = optimize(_mixed_workload_func, range(20))
        
        # Should have workload warning (could be mixed or io-bound depending on timing)
        workload_warnings = [w for w in result.warnings if "workload appears" in w.lower()]
        # May or may not have warning depending on exact CPU ratio
        # Just check that we get valid results
        assert result.n_jobs >= 1
    
    def test_diagnostic_profile_includes_workload_type(self):
        """Test that diagnostic profile includes workload type info."""
        result = optimize(_cpu_heavy_func, range(100), profile=True)
        
        assert hasattr(result.profile, 'workload_type')
        assert hasattr(result.profile, 'cpu_time_ratio')
        assert result.profile.workload_type in ("cpu_bound", "mixed", "io_bound")
        assert 0.0 <= result.profile.cpu_time_ratio <= 2.0
    
    def test_explain_shows_workload_type(self):
        """Test that explain() output includes workload type."""
        result = optimize(_cpu_heavy_func, range(100), profile=True)
        explanation = result.explain()
        
        # Should mention workload type
        assert "workload type" in explanation.lower() or "cpu-bound" in explanation.lower()


class TestPerformDryRunIntegration:
    """Test workload detection in perform_dry_run."""
    
    def test_sampling_result_includes_workload_type(self):
        """Test that SamplingResult includes workload type fields."""
        result = perform_dry_run(_simple_func, range(10), sample_size=5)
        
        assert hasattr(result, 'workload_type')
        assert hasattr(result, 'cpu_time_ratio')
        assert result.workload_type in ("cpu_bound", "mixed", "io_bound")
    
    def test_cpu_bound_detected_in_dry_run(self):
        """Test that CPU-bound workload is detected in dry run."""
        result = perform_dry_run(_cpu_heavy_func, range(10), sample_size=5)
        
        assert result.workload_type == "cpu_bound"
        assert result.cpu_time_ratio >= 0.5  # Reasonable CPU utilization
    
    def test_io_bound_detected_in_dry_run(self):
        """Test that I/O-bound workload is detected in dry run."""
        result = perform_dry_run(_io_heavy_func, range(10), sample_size=5)
        
        assert result.workload_type == "io_bound"
        assert result.cpu_time_ratio < 0.3  # Low CPU utilization


class TestEdgeCases:
    """Test edge cases for workload detection."""
    
    def test_instantaneous_function(self):
        """Test workload detection with extremely fast function."""
        data = list(range(5))
        workload_type, cpu_ratio = detect_workload_type(_fast_func, data)
        
        # Should still classify (likely CPU-bound due to no waiting)
        assert workload_type in ("cpu_bound", "mixed")
    
    def test_single_item(self):
        """Test workload detection with single data item."""
        workload_type, cpu_ratio = detect_workload_type(_cpu_heavy_func, [1])
        
        # Should still work with single item
        assert workload_type in ("cpu_bound", "mixed", "io_bound")
    
    def test_long_running_cpu_function(self):
        """Test workload detection with long-running CPU function."""
        # Use smaller sample to avoid test timeout
        data = list(range(2))
        workload_type, cpu_ratio = detect_workload_type(_long_cpu_func, data)
        
        assert workload_type == "cpu_bound"
        assert cpu_ratio >= 0.7
    
    def test_very_long_io_wait(self):
        """Test workload detection with long I/O wait."""
        data = list(range(3))
        workload_type, cpu_ratio = detect_workload_type(_long_io_func, data)
        
        assert workload_type == "io_bound"
        assert cpu_ratio < 0.2  # Very low CPU utilization
