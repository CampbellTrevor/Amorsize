"""
Tests for real-time system load adjustment functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from amorsize.system_info import (
    get_current_cpu_load,
    get_memory_pressure,
    calculate_load_aware_workers,
    get_physical_cores,
    HAS_PSUTIL
)


class TestGetCurrentCPULoad:
    """Tests for get_current_cpu_load() function."""
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_returns_float_between_0_and_100(self):
        """Test that CPU load is a percentage in valid range."""
        cpu_load = get_current_cpu_load()
        assert isinstance(cpu_load, float)
        assert 0.0 <= cpu_load <= 100.0
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_custom_interval(self):
        """Test that custom interval parameter works."""
        cpu_load = get_current_cpu_load(interval=0.05)
        assert isinstance(cpu_load, float)
        assert 0.0 <= cpu_load <= 100.0
    
    def test_returns_zero_without_psutil(self):
        """Test fallback behavior when psutil is not available."""
        with patch('amorsize.system_info.HAS_PSUTIL', False):
            cpu_load = get_current_cpu_load()
            assert cpu_load == 0.0
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_handles_psutil_errors(self):
        """Test graceful handling of psutil errors."""
        with patch('psutil.cpu_percent', side_effect=OSError("Mocked error")):
            cpu_load = get_current_cpu_load()
            assert cpu_load == 0.0


class TestGetMemoryPressure:
    """Tests for get_memory_pressure() function."""
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_returns_float_between_0_and_100(self):
        """Test that memory pressure is a percentage in valid range."""
        memory_pressure = get_memory_pressure()
        assert isinstance(memory_pressure, float)
        assert 0.0 <= memory_pressure <= 100.0
    
    def test_returns_zero_without_psutil(self):
        """Test fallback behavior when psutil is not available."""
        with patch('amorsize.system_info.HAS_PSUTIL', False):
            memory_pressure = get_memory_pressure()
            assert memory_pressure == 0.0
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available")
    def test_handles_psutil_errors(self):
        """Test graceful handling of psutil errors."""
        mock_vm = MagicMock()
        mock_vm.percent = None  # Simulate error
        with patch('psutil.virtual_memory', side_effect=OSError("Mocked error")):
            memory_pressure = get_memory_pressure()
            assert memory_pressure == 0.0


class TestCalculateLoadAwareWorkers:
    """Tests for calculate_load_aware_workers() function."""
    
    def test_no_adjustment_when_load_below_threshold(self):
        """Test that no adjustment is made when system load is below thresholds."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=50.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=50.0):
            
            workers = calculate_load_aware_workers(8, 1024*1024*1024)
            assert workers == 8  # No reduction
    
    def test_cpu_adjustment_when_above_threshold(self):
        """Test worker reduction when CPU load is above threshold."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=80.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=50.0):
            
            workers = calculate_load_aware_workers(8, 1024*1024*1024)
            assert workers < 8  # Should be reduced
            assert workers >= 1  # But at least 1
    
    def test_memory_adjustment_when_above_threshold(self):
        """Test worker reduction when memory pressure is above threshold."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=50.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=85.0):
            
            workers = calculate_load_aware_workers(8, 1024*1024*1024)
            assert workers < 8  # Should be reduced
            assert workers >= 1  # But at least 1
    
    def test_both_adjustments_when_both_above_threshold(self):
        """Test that the most conservative adjustment is applied."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=80.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=85.0):
            
            workers = calculate_load_aware_workers(8, 1024*1024*1024)
            assert workers < 8  # Should be reduced
            assert workers >= 1  # But at least 1
    
    def test_aggressive_reduction_mode(self):
        """Test aggressive reduction mode."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=95.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=95.0):
            
            # Conservative mode (default)
            workers_conservative = calculate_load_aware_workers(
                8, 1024*1024*1024, aggressive_reduction=False
            )
            
            # Aggressive mode
            workers_aggressive = calculate_load_aware_workers(
                8, 1024*1024*1024, aggressive_reduction=True
            )
            
            # Aggressive should reduce more
            assert workers_aggressive <= workers_conservative
            assert workers_aggressive >= 1
    
    def test_custom_thresholds(self):
        """Test custom CPU and memory thresholds."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=60.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=60.0):
            
            # With default thresholds (70%, 75%), no adjustment
            workers_default = calculate_load_aware_workers(8, 1024*1024*1024)
            assert workers_default == 8
            
            # With lower thresholds (50%, 50%), should adjust
            workers_custom = calculate_load_aware_workers(
                8, 1024*1024*1024, cpu_threshold=50.0, memory_threshold=50.0
            )
            assert workers_custom < 8
    
    def test_minimum_one_worker(self):
        """Test that at least 1 worker is always returned."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=1), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=99.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=99.0):
            
            workers = calculate_load_aware_workers(8, 1024*1024*1024)
            assert workers >= 1
    
    def test_respects_base_worker_constraints(self):
        """Test that load-aware calculation respects base constraints."""
        # If base calculation gives 2 workers (e.g., due to memory), 
        # load-aware should not exceed that
        with patch('amorsize.system_info.calculate_max_workers', return_value=2), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=10.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=10.0):
            
            workers = calculate_load_aware_workers(8, 10*1024*1024*1024)
            assert workers <= 2
    
    def test_very_high_cpu_load(self):
        """Test behavior with very high CPU load (>90%)."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=95.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=50.0):
            
            workers = calculate_load_aware_workers(8, 1024*1024*1024)
            # Should be significantly reduced for very high load
            assert workers <= 4  # Should be at most half
            assert workers >= 1
    
    def test_very_high_memory_pressure(self):
        """Test behavior with very high memory pressure (>90%)."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=50.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=95.0):
            
            workers = calculate_load_aware_workers(8, 1024*1024*1024)
            # Should be significantly reduced for very high pressure
            assert workers <= 4  # Should be at most half
            assert workers >= 1
    
    def test_threshold_edge_case_100_percent(self):
        """Test that 100% thresholds don't cause division by zero."""
        with patch('amorsize.system_info.calculate_max_workers', return_value=8), \
             patch('amorsize.system_info.get_current_cpu_load', return_value=95.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=95.0):
            
            # Should not raise ZeroDivisionError
            workers = calculate_load_aware_workers(
                8, 1024*1024*1024, cpu_threshold=100.0, memory_threshold=100.0
            )
            assert workers >= 1  # Should still return valid result
            assert workers <= 8


class TestLoadAwareIntegration:
    """Integration tests for load-aware functionality with optimizer."""
    
    def test_optimize_with_load_awareness_disabled(self):
        """Test that optimize works with load awareness disabled (default)."""
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(simple_func, data, adjust_for_system_load=False)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil required for load awareness")
    def test_optimize_with_load_awareness_enabled(self):
        """Test that optimize works with load awareness enabled."""
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(simple_func, data, adjust_for_system_load=True)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil required for load awareness")
    def test_load_awareness_reduces_workers_under_high_load(self):
        """Test that load awareness reduces workers when system is loaded."""
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        
        # Simulate high system load
        with patch('amorsize.system_info.get_current_cpu_load', return_value=90.0), \
             patch('amorsize.system_info.get_memory_pressure', return_value=90.0):
            
            result_with_load = optimize(simple_func, data, adjust_for_system_load=True)
            result_without_load = optimize(simple_func, data, adjust_for_system_load=False)
            
            # With load awareness, should use fewer workers
            assert result_with_load.n_jobs <= result_without_load.n_jobs
    
    def test_parameter_validation(self):
        """Test that adjust_for_system_load parameter is properly validated."""
        from amorsize import optimize
        
        def simple_func(x):
            return x * 2
        
        data = list(range(10))
        
        # Valid boolean values should work
        result = optimize(simple_func, data, adjust_for_system_load=True)
        assert result.n_jobs >= 1
        
        result = optimize(simple_func, data, adjust_for_system_load=False)
        assert result.n_jobs >= 1
        
        # Invalid type should raise ValueError
        with pytest.raises(ValueError, match="adjust_for_system_load must be a boolean"):
            optimize(simple_func, data, adjust_for_system_load="invalid")
        
        with pytest.raises(ValueError, match="adjust_for_system_load must be a boolean"):
            optimize(simple_func, data, adjust_for_system_load=1)
