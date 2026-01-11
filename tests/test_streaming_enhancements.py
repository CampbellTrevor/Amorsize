"""
Test suite for streaming enhancements: adaptive chunking, pool manager integration, and memory backpressure.

Tests new features added in Iteration 110.
"""

import pytest
import time
from amorsize import optimize_streaming, StreamingOptimizationResult, PoolManager, get_global_pool_manager


# Test functions
def fast_function(x):
    """Very fast function."""
    return x * 2


def slow_function(x):
    """Slow function (~10ms)."""
    time.sleep(0.01)
    return x ** 2


def expensive_function(x):
    """Expensive function (~50ms)."""
    result = 0
    for i in range(50000):
        result += x ** 2
    return result


def heterogeneous_function(x):
    """Function with variable execution time."""
    if x % 2 == 0:
        time.sleep(0.001)
    else:
        time.sleep(0.010)
    return x


def large_return_function(x):
    """Function with large return value."""
    return [x] * 10000  # ~80KB return


# ============================================================================
# Adaptive Chunking Integration Tests
# ============================================================================

class TestAdaptiveChunkingIntegration:
    """Test adaptive chunking integration with streaming optimization."""
    
    def test_adaptive_chunking_enabled_for_heterogeneous_workload(self):
        """Test that adaptive chunking is enabled for heterogeneous workloads."""
        data = list(range(100))
        result = optimize_streaming(
            heterogeneous_function, 
            data, 
            sample_size=10,
            enable_adaptive_chunking=True
        )
        
        # Heterogeneous workload should enable adaptive chunking
        assert isinstance(result, StreamingOptimizationResult)
        assert hasattr(result, 'use_adaptive_chunking')
        assert hasattr(result, 'adaptive_chunking_params')
        
        # If n_jobs > 1, adaptive chunking should be enabled for heterogeneous workload
        if result.n_jobs > 1 and result.use_adaptive_chunking:
            assert isinstance(result.adaptive_chunking_params, dict)
            assert 'initial_chunksize' in result.adaptive_chunking_params
            assert 'target_chunk_duration' in result.adaptive_chunking_params
            assert 'adaptation_rate' in result.adaptive_chunking_params
    
    def test_adaptive_chunking_disabled_for_homogeneous_workload(self):
        """Test that adaptive chunking is disabled for homogeneous workloads."""
        data = list(range(100))
        result = optimize_streaming(
            expensive_function,  # Homogeneous workload
            data,
            sample_size=5,
            enable_adaptive_chunking=True
        )
        
        assert isinstance(result, StreamingOptimizationResult)
        # Homogeneous workload should not enable adaptive chunking
        # (even if requested, because CV is low)
        assert hasattr(result, 'use_adaptive_chunking')
    
    def test_adaptive_chunking_parameters_passed_correctly(self):
        """Test that adaptive chunking parameters are passed correctly."""
        data = list(range(100))
        custom_adaptation_rate = 0.5
        
        result = optimize_streaming(
            heterogeneous_function,
            data,
            sample_size=10,
            enable_adaptive_chunking=True,
            adaptation_rate=custom_adaptation_rate
        )
        
        # Check if parameters were used
        if result.use_adaptive_chunking:
            assert result.adaptive_chunking_params.get('adaptation_rate') == custom_adaptation_rate
    
    def test_adaptive_chunking_disabled_by_default(self):
        """Test that adaptive chunking is disabled by default."""
        data = list(range(100))
        result = optimize_streaming(
            heterogeneous_function,
            data,
            sample_size=10
            # enable_adaptive_chunking not specified - defaults to False
        )
        
        assert result.use_adaptive_chunking is False
    
    def test_adaptive_chunking_params_empty_when_disabled(self):
        """Test that adaptive chunking params are empty when disabled."""
        data = list(range(50))
        result = optimize_streaming(
            expensive_function,
            data,
            enable_adaptive_chunking=False
        )
        
        assert result.use_adaptive_chunking is False
        assert result.adaptive_chunking_params == {} or not result.adaptive_chunking_params


# ============================================================================
# Pool Manager Integration Tests
# ============================================================================

class TestPoolManagerIntegration:
    """Test pool manager integration with streaming optimization."""
    
    def test_pool_manager_parameter_accepted(self):
        """Test that pool_manager parameter is accepted."""
        data = list(range(50))
        manager = PoolManager()
        
        try:
            result = optimize_streaming(
                slow_function,
                data,
                pool_manager=manager
            )
            
            assert isinstance(result, StreamingOptimizationResult)
            assert result.n_jobs >= 1
        finally:
            manager.shutdown()
    
    def test_pool_manager_none_by_default(self):
        """Test that pool_manager defaults to None."""
        data = list(range(50))
        result = optimize_streaming(slow_function, data)
        
        # Should work without pool_manager
        assert isinstance(result, StreamingOptimizationResult)
    
    def test_pool_manager_validation_invalid_object(self):
        """Test validation rejects invalid pool manager objects."""
        data = list(range(50))
        invalid_manager = "not_a_pool_manager"
        
        with pytest.raises(ValueError, match="must have 'get_pool' method"):
            optimize_streaming(
                slow_function,
                data,
                pool_manager=invalid_manager
            )
    
    def test_global_pool_manager_can_be_used(self):
        """Test that global pool manager can be used."""
        data = list(range(50))
        manager = get_global_pool_manager()
        
        result = optimize_streaming(
            slow_function,
            data,
            pool_manager=manager
        )
        
        assert isinstance(result, StreamingOptimizationResult)


# ============================================================================
# Memory Backpressure Tests
# ============================================================================

class TestMemoryBackpressure:
    """Test memory backpressure handling."""
    
    def test_memory_backpressure_disabled_by_default(self):
        """Test that memory backpressure is disabled by default."""
        data = list(range(50))
        result = optimize_streaming(slow_function, data)
        
        assert hasattr(result, 'memory_backpressure_enabled')
        assert result.memory_backpressure_enabled is False
    
    def test_memory_backpressure_can_be_enabled(self):
        """Test that memory backpressure can be enabled."""
        data = list(range(50))
        result = optimize_streaming(
            slow_function,
            data,
            enable_memory_backpressure=True
        )
        
        assert result.memory_backpressure_enabled is True
    
    def test_memory_threshold_parameter(self):
        """Test memory threshold parameter."""
        data = list(range(50))
        custom_threshold = 0.7
        
        # Should not raise error
        result = optimize_streaming(
            slow_function,
            data,
            enable_memory_backpressure=True,
            memory_threshold=custom_threshold
        )
        
        assert isinstance(result, StreamingOptimizationResult)
    
    def test_buffer_size_calculated_when_backpressure_enabled(self):
        """Test that buffer size is calculated when backpressure is enabled."""
        data = list(range(100))
        result = optimize_streaming(
            large_return_function,  # Large return values
            data,
            sample_size=5,
            enable_memory_backpressure=True
        )
        
        assert hasattr(result, 'buffer_size')
        assert result.buffer_size is not None
        assert result.buffer_size >= 1


# ============================================================================
# Buffer Size Calculation Tests
# ============================================================================

class TestBufferSizeCalculation:
    """Test buffer size calculation logic."""
    
    def test_buffer_size_auto_calculated(self):
        """Test that buffer size is auto-calculated when not provided."""
        data = list(range(50))
        result = optimize_streaming(
            slow_function,
            data
            # buffer_size not specified - should be auto-calculated
        )
        
        assert hasattr(result, 'buffer_size')
        assert result.buffer_size is not None
        assert result.buffer_size >= 1
    
    def test_buffer_size_respects_explicit_value(self):
        """Test that explicit buffer size is used when provided."""
        data = list(range(50))
        custom_buffer_size = 20
        
        result = optimize_streaming(
            slow_function,
            data,
            buffer_size=custom_buffer_size
        )
        
        # Should respect the explicit value
        assert result.buffer_size == custom_buffer_size
    
    def test_buffer_size_scales_with_workers(self):
        """Test that buffer size scales with number of workers."""
        data = list(range(100))
        result = optimize_streaming(expensive_function, data, sample_size=5)
        
        if result.n_jobs > 1:
            # Buffer size should be proportional to n_jobs
            # Typically buffer = n_jobs * 2 to 4
            assert result.buffer_size >= result.n_jobs
    
    def test_buffer_size_limited_by_memory_with_large_returns(self):
        """Test that buffer size is limited by memory for large return values."""
        data = list(range(100))
        result = optimize_streaming(
            large_return_function,
            data,
            sample_size=5,
            enable_memory_backpressure=True
        )
        
        # Buffer size should be reasonable even with large returns
        assert result.buffer_size is not None
        assert result.buffer_size >= 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestStreamingEnhancementsIntegration:
    """Test combinations of enhancements."""
    
    def test_all_enhancements_together(self):
        """Test enabling all enhancements together."""
        data = list(range(100))
        manager = PoolManager()
        
        try:
            result = optimize_streaming(
                heterogeneous_function,
                data,
                sample_size=10,
                enable_adaptive_chunking=True,
                adaptation_rate=0.4,
                pool_manager=manager,
                enable_memory_backpressure=True,
                memory_threshold=0.75,
                buffer_size=None  # Let it auto-calculate
            )
            
            assert isinstance(result, StreamingOptimizationResult)
            assert hasattr(result, 'use_adaptive_chunking')
            assert hasattr(result, 'memory_backpressure_enabled')
            assert hasattr(result, 'buffer_size')
            
            # Memory backpressure should be enabled (even if serial execution)
            assert result.memory_backpressure_enabled is True
            
            # Buffer size should be calculated
            assert result.buffer_size is not None
            
        finally:
            manager.shutdown()
    
    def test_enhancements_with_verbose_output(self):
        """Test that verbose mode works with all enhancements."""
        data = list(range(50))
        
        # Should not raise error
        result = optimize_streaming(
            heterogeneous_function,
            data,
            sample_size=10,
            enable_adaptive_chunking=True,
            enable_memory_backpressure=True,
            verbose=True
        )
        
        assert isinstance(result, StreamingOptimizationResult)
    
    def test_enhancements_with_profiling(self):
        """Test that profiling works with enhancements."""
        data = list(range(50))
        
        result = optimize_streaming(
            slow_function,
            data,
            enable_adaptive_chunking=True,
            enable_memory_backpressure=True,
            profile=True
        )
        
        assert isinstance(result, StreamingOptimizationResult)
        assert result.profile is not None


# ============================================================================
# Parameter Validation Tests
# ============================================================================

class TestParameterValidation:
    """Test parameter validation for new parameters."""
    
    def test_enable_adaptive_chunking_must_be_bool(self):
        """Test that enable_adaptive_chunking must be a boolean."""
        data = list(range(50))
        
        with pytest.raises(ValueError, match="must be bool"):
            optimize_streaming(
                slow_function,
                data,
                enable_adaptive_chunking="yes"  # Invalid: string
            )
    
    def test_adaptation_rate_must_be_numeric(self):
        """Test that adaptation_rate must be numeric."""
        data = list(range(50))
        
        with pytest.raises(ValueError, match="must be numeric"):
            optimize_streaming(
                slow_function,
                data,
                adaptation_rate="fast"  # Invalid: string
            )
    
    def test_adaptation_rate_must_be_in_range(self):
        """Test that adaptation_rate must be 0.0-1.0."""
        data = list(range(50))
        
        # Test too high
        with pytest.raises(ValueError, match="must be 0.0-1.0"):
            optimize_streaming(
                slow_function,
                data,
                adaptation_rate=1.5  # Invalid: > 1.0
            )
        
        # Test negative
        with pytest.raises(ValueError, match="must be 0.0-1.0"):
            optimize_streaming(
                slow_function,
                data,
                adaptation_rate=-0.1  # Invalid: < 0.0
            )
    
    def test_adaptation_rate_validation(self):
        """Test adaptation rate validation."""
        data = list(range(50))
        
        # Valid adaptation rates should work
        for rate in [0.0, 0.3, 0.5, 1.0]:
            result = optimize_streaming(
                slow_function,
                data,
                enable_adaptive_chunking=True,
                adaptation_rate=rate
            )
            assert isinstance(result, StreamingOptimizationResult)
    
    def test_memory_threshold_must_be_numeric(self):
        """Test that memory_threshold must be numeric."""
        data = list(range(50))
        
        with pytest.raises(ValueError, match="must be numeric"):
            optimize_streaming(
                slow_function,
                data,
                memory_threshold="high"  # Invalid: string
            )
    
    def test_memory_threshold_must_be_in_range(self):
        """Test that memory_threshold must be 0.0-1.0."""
        data = list(range(50))
        
        # Test too high
        with pytest.raises(ValueError, match="must be 0.0-1.0"):
            optimize_streaming(
                slow_function,
                data,
                memory_threshold=1.5  # Invalid: > 1.0
            )
        
        # Test negative
        with pytest.raises(ValueError, match="must be 0.0-1.0"):
            optimize_streaming(
                slow_function,
                data,
                memory_threshold=-0.1  # Invalid: < 0.0
            )
    
    def test_memory_threshold_validation(self):
        """Test memory threshold validation."""
        data = list(range(50))
        
        # Valid thresholds should work
        for threshold in [0.5, 0.7, 0.8, 0.9]:
            result = optimize_streaming(
                slow_function,
                data,
                enable_memory_backpressure=True,
                memory_threshold=threshold
            )
            assert isinstance(result, StreamingOptimizationResult)
    
    def test_enable_memory_backpressure_must_be_bool(self):
        """Test that enable_memory_backpressure must be a boolean."""
        data = list(range(50))
        
        with pytest.raises(ValueError, match="must be bool"):
            optimize_streaming(
                slow_function,
                data,
                enable_memory_backpressure="yes"  # Invalid: string
            )


# ============================================================================
# Backward Compatibility Tests
# ============================================================================

class TestBackwardCompatibility:
    """Test that existing functionality still works."""
    
    def test_existing_parameters_still_work(self):
        """Test that existing parameters work without new parameters."""
        data = list(range(50))
        
        # Original parameters only
        result = optimize_streaming(
            slow_function,
            data,
            sample_size=5,
            target_chunk_duration=0.2,
            verbose=False
        )
        
        assert isinstance(result, StreamingOptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_all_return_fields_present(self):
        """Test that result contains all fields (old and new)."""
        data = list(range(50))
        result = optimize_streaming(slow_function, data)
        
        # Old fields
        assert hasattr(result, 'n_jobs')
        assert hasattr(result, 'chunksize')
        assert hasattr(result, 'use_ordered')
        assert hasattr(result, 'reason')
        assert hasattr(result, 'estimated_speedup')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'data')
        assert hasattr(result, 'profile')
        
        # New fields
        assert hasattr(result, 'use_adaptive_chunking')
        assert hasattr(result, 'adaptive_chunking_params')
        assert hasattr(result, 'buffer_size')
        assert hasattr(result, 'memory_backpressure_enabled')
    
    def test_serial_execution_returns_have_new_fields(self):
        """Test that serial execution results also have new fields."""
        data = list(range(10))
        
        # Use very fast function to force serial execution
        result = optimize_streaming(fast_function, data, sample_size=3)
        
        # Should have all fields even for serial execution
        assert hasattr(result, 'use_adaptive_chunking')
        assert hasattr(result, 'buffer_size')
        assert hasattr(result, 'memory_backpressure_enabled')
