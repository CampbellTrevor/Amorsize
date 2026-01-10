"""Tests for function profiling with cProfile integration."""

import os
import tempfile
from amorsize import optimize


def simple_function(x):
    """Simple test function."""
    return x * 2


def nested_function_calls(x):
    """Function with nested calls to test profiling depth."""
    def helper1(val):
        return val + 1
    
    def helper2(val):
        return helper1(val) * 2
    
    result = 0
    for _ in range(100):
        result += helper2(x)
    return result


def test_profiling_disabled_by_default():
    """Test that function profiling is disabled by default."""
    data = range(10)
    result = optimize(simple_function, data, sample_size=3)
    
    # Function profiler should be None when disabled
    assert result.function_profiler_stats is None


def test_profiling_enabled():
    """Test that function profiling works when enabled."""
    data = range(10)
    result = optimize(
        simple_function,
        data,
        sample_size=3,
        enable_function_profiling=True
    )
    
    # Function profiler should have stats when enabled
    assert result.function_profiler_stats is not None
    
    # Stats should have the expected attributes
    assert hasattr(result.function_profiler_stats, 'total_calls')
    assert hasattr(result.function_profiler_stats, 'prim_calls')


def test_show_function_profile_when_disabled():
    """Test showing profile when profiling is disabled."""
    data = range(10)
    result = optimize(simple_function, data, sample_size=3)
    
    # Should print message indicating profiling wasn't enabled
    # This is a manual verification test - just ensure it doesn't crash
    result.show_function_profile()


def test_show_function_profile_when_enabled(capsys):
    """Test showing profile when profiling is enabled."""
    data = range(10)
    result = optimize(
        nested_function_calls,
        data,
        sample_size=3,
        enable_function_profiling=True
    )
    
    # Should display profile stats
    result.show_function_profile(limit=10)
    
    # Capture output
    captured = capsys.readouterr()
    
    # Should contain profiling output
    assert "FUNCTION PERFORMANCE PROFILE" in captured.out
    assert "ncalls" in captured.out or "cumulative" in captured.out


def test_save_function_profile():
    """Test saving profile to file."""
    data = range(10)
    result = optimize(
        nested_function_calls,
        data,
        sample_size=3,
        enable_function_profiling=True
    )
    
    # Save profile to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        filepath = f.name
    
    try:
        result.save_function_profile(filepath, limit=20)
        
        # Verify file was created and contains content
        assert os.path.exists(filepath)
        
        with open(filepath, 'r') as f:
            content = f.read()
            assert "FUNCTION PERFORMANCE PROFILE" in content
            assert len(content) > 100  # Should have substantial content
    finally:
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)


def test_save_function_profile_when_disabled():
    """Test that saving profile raises error when profiling is disabled."""
    data = range(10)
    result = optimize(simple_function, data, sample_size=3)
    
    # Should raise ValueError when trying to save without profiling enabled
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        filepath = f.name
    
    try:
        # This should raise an error
        try:
            result.save_function_profile(filepath)
            assert False, "Expected ValueError but none was raised"
        except ValueError as e:
            assert "not enabled" in str(e).lower()
    finally:
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)


def test_profiling_with_different_sort_keys():
    """Test profiling with different sort options."""
    data = range(10)
    result = optimize(
        nested_function_calls,
        data,
        sample_size=3,
        enable_function_profiling=True
    )
    
    # Test different sort keys - should not crash
    result.show_function_profile(sort_by='cumulative', limit=5)
    result.show_function_profile(sort_by='time', limit=5)
    result.show_function_profile(sort_by='calls', limit=5)


def test_profiling_parameter_validation():
    """Test that enable_function_profiling parameter is validated."""
    data = range(10)
    
    # Should accept boolean values
    result1 = optimize(simple_function, data, sample_size=3, enable_function_profiling=True)
    assert result1.function_profiler_stats is not None
    
    result2 = optimize(simple_function, data, sample_size=3, enable_function_profiling=False)
    assert result2.function_profiler_stats is None
    
    # Should reject non-boolean values
    try:
        optimize(simple_function, data, sample_size=3, enable_function_profiling="yes")
        assert False, "Expected ValueError for non-boolean parameter"
    except ValueError as e:
        assert "enable_function_profiling must be a boolean" in str(e)


def test_profiling_with_verbose():
    """Test that profiling works alongside verbose mode."""
    data = range(10)
    result = optimize(
        nested_function_calls,
        data,
        sample_size=3,
        enable_function_profiling=True,
        verbose=True
    )
    
    # Both should work together
    assert result.function_profiler_stats is not None
    assert result.n_jobs >= 1


def test_profiling_with_diagnostic_profile():
    """Test that function profiling works alongside diagnostic profiling."""
    data = range(100)
    result = optimize(
        nested_function_calls,
        data,
        sample_size=3,
        enable_function_profiling=True,
        profile=True  # Diagnostic profiling
    )
    
    # Both should be available
    assert result.function_profiler_stats is not None
    assert result.profile is not None
    
    # Can access both reports
    result.show_function_profile(limit=5)
    diag_report = result.explain()
    assert len(diag_report) > 100
