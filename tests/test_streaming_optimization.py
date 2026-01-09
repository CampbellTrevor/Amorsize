"""
Test suite for streaming optimization functionality.

Tests the optimize_streaming() function for imap/imap_unordered workloads.
"""

import pytest
import time
import threading
from amorsize import optimize_streaming, StreamingOptimizationResult


# Test functions
def fast_function(x):
    """Very fast function (< 1ms)."""
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


def large_return_function(x):
    """Function with large return value."""
    return [x] * 10000  # ~80KB return


def variable_time_function(x):
    """Function with variable execution time."""
    time.sleep(0.001 * (x % 10))
    return x


class UnpicklableObject:
    """Object that cannot be pickled."""
    def __init__(self):
        self.lock = threading.Lock()


def unpicklable_function(x):
    """Function that returns unpicklable object."""
    return UnpicklableObject()


# ============================================================================
# Basic Functionality Tests
# ============================================================================

class TestBasicStreamingOptimization:
    """Test basic streaming optimization functionality."""
    
    def test_optimize_streaming_basic(self):
        """Test basic streaming optimization."""
        data = list(range(1000))
        result = optimize_streaming(expensive_function, data, sample_size=5)
        
        assert isinstance(result, StreamingOptimizationResult)
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert isinstance(result.use_ordered, bool)
        assert isinstance(result.estimated_speedup, float)
        assert result.estimated_speedup >= 1.0
    
    def test_streaming_returns_correct_attributes(self):
        """Test that result contains all expected attributes."""
        data = list(range(100))
        result = optimize_streaming(slow_function, data)
        
        assert hasattr(result, 'n_jobs')
        assert hasattr(result, 'chunksize')
        assert hasattr(result, 'use_ordered')
        assert hasattr(result, 'reason')
        assert hasattr(result, 'estimated_speedup')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'data')
        assert hasattr(result, 'profile')
    
    def test_streaming_repr_and_str(self):
        """Test string representations."""
        data = list(range(50))
        result = optimize_streaming(slow_function, data)
        
        repr_str = repr(result)
        str_str = str(result)
        
        assert 'StreamingOptimizationResult' in repr_str
        assert 'n_jobs' in repr_str
        assert 'Recommended' in str_str
        assert 'imap' in str_str or 'imap_unordered' in str_str
    
    def test_streaming_verbose_output(self, capsys):
        """Test verbose mode produces output."""
        data = list(range(50))
        result = optimize_streaming(slow_function, data, verbose=True)
        
        captured = capsys.readouterr()
        assert 'STREAMING OPTIMIZATION' in captured.out
        assert 'Sampling function' in captured.out
        assert 'OPTIMIZATION RESULTS' in captured.out
    
    def test_streaming_with_profile(self):
        """Test streaming optimization with profiling enabled."""
        data = list(range(100))
        result = optimize_streaming(slow_function, data, profile=True)
        
        assert result.profile is not None
        assert hasattr(result.profile, 'avg_execution_time')
        assert hasattr(result.profile, 'physical_cores')
        assert hasattr(result.profile, 'estimated_speedup')
        
        # Test explain() method
        explanation = result.explain()
        assert 'DIAGNOSTIC PROFILE' in explanation
        assert 'WORKLOAD ANALYSIS' in explanation


# ============================================================================
# Ordered vs Unordered Decision Tests
# ============================================================================

class TestOrderedVsUnordered:
    """Test imap vs imap_unordered decision logic."""
    
    def test_prefer_ordered_true(self):
        """Test explicit preference for ordered."""
        data = list(range(100))
        result = optimize_streaming(slow_function, data, prefer_ordered=True)
        
        # Should respect preference even if speedup is low
        assert result.use_ordered is True
        assert 'imap' in str(result)
    
    def test_prefer_ordered_false(self):
        """Test explicit preference for unordered."""
        data = list(range(100))
        result = optimize_streaming(slow_function, data, prefer_ordered=False)
        
        assert result.use_ordered is False
        assert 'imap_unordered' in str(result)
    
    def test_auto_decide_ordered_vs_unordered(self):
        """Test automatic decision between ordered and unordered."""
        data = list(range(100))
        result = optimize_streaming(slow_function, data, prefer_ordered=None)
        
        # Should automatically choose based on overhead
        assert isinstance(result.use_ordered, bool)
        assert result.n_jobs >= 1


# ============================================================================
# Parameter Validation Tests
# ============================================================================

class TestStreamingParameterValidation:
    """Test parameter validation."""
    
    def test_invalid_func(self):
        """Test with non-callable func."""
        with pytest.raises(ValueError, match="must be a callable"):
            optimize_streaming("not_a_function", [1, 2, 3])
    
    def test_invalid_data_none(self):
        """Test with None data."""
        with pytest.raises(ValueError, match="cannot be None"):
            optimize_streaming(fast_function, None)
    
    def test_invalid_sample_size_type(self):
        """Test with invalid sample_size type."""
        with pytest.raises(ValueError, match="must be int"):
            optimize_streaming(fast_function, [1, 2, 3], sample_size="5")
    
    def test_invalid_sample_size_negative(self):
        """Test with negative sample_size."""
        with pytest.raises(ValueError, match="must be >= 1"):
            optimize_streaming(fast_function, [1, 2, 3], sample_size=0)
    
    def test_invalid_sample_size_too_large(self):
        """Test with too large sample_size."""
        with pytest.raises(ValueError, match="must be <= 10000"):
            optimize_streaming(fast_function, [1, 2, 3], sample_size=20000)
    
    def test_invalid_target_chunk_duration_type(self):
        """Test with invalid target_chunk_duration type."""
        with pytest.raises(ValueError, match="must be numeric"):
            optimize_streaming(fast_function, [1, 2, 3], target_chunk_duration="0.5")
    
    def test_invalid_target_chunk_duration_negative(self):
        """Test with negative target_chunk_duration."""
        with pytest.raises(ValueError, match="must be > 0"):
            optimize_streaming(fast_function, [1, 2, 3], target_chunk_duration=-1.0)
    
    def test_invalid_prefer_ordered_type(self):
        """Test with invalid prefer_ordered type."""
        with pytest.raises(ValueError, match="must be bool or None"):
            optimize_streaming(fast_function, [1, 2, 3], prefer_ordered="True")
    
    def test_invalid_buffer_size_type(self):
        """Test with invalid buffer_size type."""
        with pytest.raises(ValueError, match="must be int or None"):
            optimize_streaming(fast_function, [1, 2, 3], buffer_size="10")
    
    def test_invalid_buffer_size_negative(self):
        """Test with negative buffer_size."""
        with pytest.raises(ValueError, match="must be >= 1"):
            optimize_streaming(fast_function, [1, 2, 3], buffer_size=0)


# ============================================================================
# Generator Handling Tests
# ============================================================================

class TestStreamingGeneratorHandling:
    """Test generator handling in streaming optimization."""
    
    def test_streaming_with_generator(self):
        """Test streaming optimization with generator."""
        def gen():
            for i in range(100):
                yield i
        
        result = optimize_streaming(slow_function, gen(), sample_size=5)
        
        assert result.n_jobs >= 1
        assert result.data is not None
        # Verify data is an iterator
        assert hasattr(result.data, '__iter__')
    
    def test_generator_data_preserved(self):
        """Test that generator data is preserved."""
        def gen():
            for i in range(50):
                yield i
        
        data_gen = gen()
        result = optimize_streaming(slow_function, data_gen, sample_size=5)
        
        # Should be able to iterate through all items
        items = list(result.data)
        assert len(items) == 50
        assert items == list(range(50))


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================

class TestStreamingEdgeCases:
    """Test edge cases and error handling."""
    
    def test_very_fast_function(self):
        """Test with very fast function (should reject parallelization)."""
        data = list(range(1000))
        result = optimize_streaming(fast_function, data, sample_size=5)
        
        # Fast function should be rejected for parallelization
        assert result.n_jobs == 1
        assert 'too fast' in result.reason.lower() or 'serial' in result.reason.lower()
    
    def test_empty_data(self):
        """Test with empty data list."""
        data = []
        result = optimize_streaming(slow_function, data, sample_size=5)
        
        # Should handle gracefully
        assert result.n_jobs == 1
        assert 'error' in result.reason.lower() or 'empty' in result.reason.lower()
    
    def test_single_item_data(self):
        """Test with single item."""
        data = [42]
        result = optimize_streaming(expensive_function, data, sample_size=1)
        
        # Should work but likely recommend serial
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_unpicklable_function(self):
        """Test with unpicklable function (lambda)."""
        data = list(range(50))
        result = optimize_streaming(lambda x: x * 2, data)
        
        # Should reject parallelization
        assert result.n_jobs == 1
        assert 'picklable' in result.reason.lower()
    
    def test_unpicklable_data_items(self):
        """Test with unpicklable data items."""
        data = [1, 2, threading.Lock(), 4, 5]
        result = optimize_streaming(fast_function, data)
        
        # Should detect issue and reject parallelization
        assert result.n_jobs == 1
        # May get sampling error or picklability detection
        assert 'error' in result.reason.lower() or 'picklable' in result.reason.lower()


# ============================================================================
# Heterogeneous Workload Tests
# ============================================================================

class TestStreamingHeterogeneousWorkloads:
    """Test streaming optimization with heterogeneous workloads."""
    
    def test_variable_execution_time(self):
        """Test with variable execution times."""
        data = list(range(100))
        result = optimize_streaming(
            variable_time_function, 
            data,
            sample_size=10,
            profile=True
        )
        
        # Should detect heterogeneous workload
        assert result.profile is not None
        assert result.profile.coefficient_of_variation > 0
        
        # May adapt chunksize for better load balancing
        assert result.chunksize >= 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestStreamingIntegration:
    """Integration tests for streaming optimization."""
    
    def test_streaming_with_all_features(self):
        """Test streaming with all features enabled."""
        data = list(range(200))
        result = optimize_streaming(
            slow_function,
            data,
            sample_size=10,
            target_chunk_duration=0.5,
            prefer_ordered=None,
            verbose=False,
            use_spawn_benchmark=True,
            use_chunking_benchmark=True,
            profile=True
        )
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        assert result.profile is not None
        assert isinstance(result.use_ordered, bool)
    
    def test_streaming_vs_regular_optimize(self):
        """Test that streaming optimization differs from regular optimize."""
        from amorsize import optimize
        
        # Function with large return values
        data = list(range(100))
        
        # Regular optimize (considers result memory)
        regular_result = optimize(large_return_function, data, sample_size=5)
        
        # Streaming optimize (no result memory consideration)
        streaming_result = optimize_streaming(large_return_function, data, sample_size=5)
        
        # Both should work, but may have different recommendations
        assert isinstance(regular_result.n_jobs, int)
        assert isinstance(streaming_result.n_jobs, int)
        
        # Streaming should not have memory warnings
        # (or at least different characteristics)
        assert streaming_result.chunksize >= 1


# ============================================================================
# Performance Characteristics Tests
# ============================================================================

class TestStreamingPerformanceCharacteristics:
    """Test performance characteristics of streaming optimization."""
    
    def test_streaming_optimization_speed(self):
        """Test that streaming optimization completes quickly."""
        import time
        
        data = list(range(1000))
        
        start = time.perf_counter()
        result = optimize_streaming(
            slow_function,
            data,
            sample_size=5,
            use_spawn_benchmark=False,  # Skip benchmarks for speed
            use_chunking_benchmark=False
        )
        end = time.perf_counter()
        
        elapsed = end - start
        
        # Should complete in < 1 second (mostly sampling time)
        assert elapsed < 1.0
        assert result.n_jobs >= 1
    
    def test_explain_method_works(self):
        """Test that explain() method produces useful output."""
        data = list(range(100))
        result = optimize_streaming(slow_function, data, profile=True)
        
        explanation = result.explain()
        
        # Should be a detailed multi-line explanation
        assert len(explanation) > 100
        assert '\n' in explanation
