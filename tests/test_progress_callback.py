"""
Tests for progress callback functionality in optimize().
"""

import pytest
from amorsize import optimize


class TestProgressCallback:
    """Test progress callback feature."""
    
    def test_callback_receives_progress_updates(self):
        """Verify callback is invoked with progress updates."""
        received_phases = []
        received_progress = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
            received_progress.append(progress)
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(simple_func, data, progress_callback=callback)
        
        # Should have received multiple callbacks
        assert len(received_phases) > 0
        assert len(received_progress) > 0
        assert len(received_phases) == len(received_progress)
        
        # First callback should be start (0.0)
        assert received_progress[0] == 0.0
        assert "Start" in received_phases[0] or "start" in received_phases[0]
        
        # Last callback should be complete (1.0)
        assert received_progress[-1] == 1.0
        assert "complete" in received_phases[-1].lower()
        
        # Progress should be monotonically increasing
        for i in range(1, len(received_progress)):
            assert received_progress[i] >= received_progress[i-1]
    
    def test_callback_phases_are_descriptive(self):
        """Verify callback phases describe what's happening."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        optimize(simple_func, data, progress_callback=callback)
        
        # Should include key phases
        phase_text = " ".join(received_phases).lower()
        assert "start" in phase_text or "begin" in phase_text
        assert "sampl" in phase_text  # sampling/sample
        assert "complete" in phase_text or "finish" in phase_text
    
    def test_callback_none_does_not_break(self):
        """Verify optimize works when callback is None (default)."""
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(simple_func, data, progress_callback=None)
        
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_callback_with_slow_function(self):
        """Verify callback works with slow functions."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def slow_func(x):
            total = 0
            for i in range(10000):
                total += x ** 2
            return total
        
        data = list(range(50))
        result = optimize(slow_func, data, progress_callback=callback)
        
        # Should still receive callbacks
        assert len(received_phases) > 0
        assert result.n_jobs >= 1
    
    def test_callback_with_fast_function(self):
        """Verify callback works with fast functions (that get rejected)."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def fast_func(x):
            return x + 1
        
        data = list(range(100))
        result = optimize(fast_func, data, progress_callback=callback)
        
        # Should still receive callbacks even if parallelization rejected
        assert len(received_phases) > 0
        # Fast function should be rejected
        assert result.n_jobs == 1
    
    def test_callback_with_generator(self):
        """Verify callback works with generator inputs."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def simple_func(x):
            return x * 2
        
        data = (x for x in range(100))
        result = optimize(simple_func, data, progress_callback=callback)
        
        # Should receive callbacks
        assert len(received_phases) > 0
        # Generator data should be preserved
        assert result.data is not None
    
    def test_callback_error_does_not_break_optimization(self):
        """Verify optimization continues even if callback raises error."""
        def bad_callback(phase: str, progress: float):
            # Intentionally raise error
            raise RuntimeError("Callback error!")
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        
        # Should not raise error - callback errors are silently caught
        result = optimize(simple_func, data, progress_callback=bad_callback)
        
        # Optimization should complete successfully
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_callback_with_verbose_mode(self):
        """Verify callback works alongside verbose output."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(simple_func, data, verbose=True, progress_callback=callback)
        
        # Should receive callbacks
        assert len(received_phases) > 0
        assert result.n_jobs >= 1
    
    def test_callback_with_profile_mode(self):
        """Verify callback works with diagnostic profiling."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(simple_func, data, profile=True, progress_callback=callback)
        
        # Should receive callbacks
        assert len(received_phases) > 0
        # Profile should be populated
        assert result.profile is not None
    
    def test_progress_values_are_valid(self):
        """Verify all progress values are in range [0.0, 1.0]."""
        received_progress = []
        
        def callback(phase: str, progress: float):
            received_progress.append(progress)
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        optimize(simple_func, data, progress_callback=callback)
        
        # All progress values should be valid
        for progress in received_progress:
            assert 0.0 <= progress <= 1.0
            assert isinstance(progress, (int, float))
    
    def test_callback_with_empty_data(self):
        """Verify callback works with empty data."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def simple_func(x):
            return x * 2
        
        data = []
        result = optimize(simple_func, data, progress_callback=callback)
        
        # Should receive some callbacks even with empty data
        assert len(received_phases) > 0
        # Empty data should use serial execution
        assert result.n_jobs == 1


class TestProgressCallbackValidation:
    """Test validation of progress_callback parameter."""
    
    def test_callback_must_be_callable_or_none(self):
        """Verify callback must be callable or None."""
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        
        # None should work
        result = optimize(simple_func, data, progress_callback=None)
        assert result.n_jobs >= 1
        
        # Callable should work
        def callback(phase, progress):
            pass
        result = optimize(simple_func, data, progress_callback=callback)
        assert result.n_jobs >= 1
    
    def test_callback_invalid_type_raises_error(self):
        """Verify non-callable non-None callback raises ValueError."""
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        
        # String should fail
        with pytest.raises(ValueError) as exc_info:
            optimize(simple_func, data, progress_callback="not callable")
        assert "progress_callback" in str(exc_info.value).lower()
        assert "callable" in str(exc_info.value).lower()
        
        # Integer should fail
        with pytest.raises(ValueError) as exc_info:
            optimize(simple_func, data, progress_callback=42)
        assert "progress_callback" in str(exc_info.value).lower()
    
    def test_lambda_callback_works(self):
        """Verify lambda functions work as callbacks."""
        results = []
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(
            simple_func, 
            data, 
            progress_callback=lambda phase, progress: results.append((phase, progress))
        )
        
        # Should have captured callbacks
        assert len(results) > 0
        assert result.n_jobs >= 1


class TestProgressCallbackIntegration:
    """Test progress callback integration with other features."""
    
    def test_callback_all_execution_paths(self):
        """Verify callback is invoked on all execution paths."""
        # Test rejection due to fast function
        received_phases_fast = []
        
        def callback_fast(phase: str, progress: float):
            received_phases_fast.append(phase)
        
        def very_fast_func(x):
            return x
        
        result = optimize(very_fast_func, range(100), progress_callback=callback_fast)
        assert len(received_phases_fast) > 0  # Should get callbacks even on rejection
        
        # Test successful parallelization
        received_phases_slow = []
        
        def callback_slow(phase: str, progress: float):
            received_phases_slow.append(phase)
        
        def slow_func(x):
            total = 0
            for i in range(10000):
                total += x ** 2
            return total
        
        result = optimize(slow_func, range(50), progress_callback=callback_slow)
        assert len(received_phases_slow) > 0
    
    def test_callback_with_all_parameters(self):
        """Verify callback works with all optimize parameters set."""
        received_phases = []
        
        def callback(phase: str, progress: float):
            received_phases.append(phase)
        
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        result = optimize(
            simple_func,
            data,
            sample_size=10,
            target_chunk_duration=0.5,
            verbose=True,
            use_spawn_benchmark=True,
            use_chunking_benchmark=True,
            profile=True,
            auto_adjust_for_nested_parallelism=True,
            progress_callback=callback
        )
        
        # Should receive callbacks
        assert len(received_phases) > 0
        assert result.n_jobs >= 1
        assert result.profile is not None
