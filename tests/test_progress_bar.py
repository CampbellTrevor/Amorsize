"""
Tests for progress bar functionality.

Tests the new --progress CLI flag and create_progress_callback function.
"""

import io
import sys
from unittest.mock import patch

import pytest

from amorsize.__main__ import create_progress_callback


def test_create_progress_callback_basic():
    """Test that create_progress_callback returns a callable."""
    callback = create_progress_callback(verbose=False)
    assert callable(callback)


def test_progress_callback_non_tty():
    """Test that progress callback silently does nothing when not a TTY."""
    callback = create_progress_callback(verbose=False)
    
    # Mock stdout as non-TTY
    with patch('sys.stdout.isatty', return_value=False):
        # Should not raise any errors
        callback("Starting", 0.0)
        callback("Halfway", 0.5)
        callback("Complete", 1.0)


def test_progress_callback_tty_output():
    """Test progress callback output when TTY is available."""
    # Create a string buffer to capture output
    output = io.StringIO()
    
    callback = create_progress_callback(verbose=False)
    
    # Mock stdout as TTY and redirect writes
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write') as mock_write:
            with patch('sys.stdout.flush'):
                callback("Starting", 0.0)
                
                # Should have written progress bar
                assert mock_write.called
                call_args = mock_write.call_args[0][0]
                # Should contain bar characters and percentage
                assert '░' in call_args or '█' in call_args
                assert '0%' in call_args or '  0%' in call_args


def test_progress_callback_verbose_mode():
    """Test verbose mode shows phase descriptions."""
    callback = create_progress_callback(verbose=True)
    
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write') as mock_write:
            with patch('sys.stdout.flush'):
                callback("Sampling function", 0.5)
                
                # Should include phase description in verbose mode
                call_args = mock_write.call_args[0][0]
                assert 'Sampling function' in call_args
                assert '50%' in call_args


def test_progress_callback_completion():
    """Test that callback adds newline at completion."""
    callback = create_progress_callback(verbose=False)
    
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write') as mock_write:
            with patch('sys.stdout.flush'):
                callback("Complete", 1.0)
                
                # Should have written newline
                calls = [call[0][0] for call in mock_write.call_args_list]
                # Last call should be newline
                assert '\n' in calls[-1]


def test_progress_callback_progression():
    """Test progress values from 0 to 100%."""
    callback = create_progress_callback(verbose=False)
    
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write') as mock_write:
            with patch('sys.stdout.flush'):
                # Test various progress values
                for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    callback(f"Progress {progress}", progress)
                    
                    # Should have been called
                    assert mock_write.called
                    
                    # Reset mock for next iteration
                    mock_write.reset_mock()


def test_progress_callback_bar_filling():
    """Test that progress bar fills as progress increases."""
    callback = create_progress_callback(verbose=False)
    
    outputs = []
    
    def capture_write(text):
        """Capture written text."""
        outputs.append(text)
    
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write', side_effect=capture_write):
            with patch('sys.stdout.flush'):
                # Test at different progress levels
                callback("Start", 0.0)
                callback("Quarter", 0.25)
                callback("Half", 0.5)
                callback("ThreeQuarters", 0.75)
                callback("Complete", 1.0)
                
                # Should have written multiple times (at least 5 progress updates)
                assert len(outputs) >= 5
                
                # Check that we have progress bar output with filled blocks
                filled_counts = []
                for output in outputs:
                    if '█' in output or '░' in output:
                        filled_counts.append(output.count('█'))
                
                # Should have some progress bar outputs
                assert len(filled_counts) > 0
                
                # Generally, filled count should increase (may not be perfectly monotonic
                # due to output formatting, but first should be less than last)
                if len(filled_counts) >= 2:
                    assert filled_counts[0] <= filled_counts[-1]


def test_progress_callback_with_special_characters():
    """Test progress callback handles special phase names correctly."""
    callback = create_progress_callback(verbose=True)
    
    special_phases = [
        "Phase with spaces",
        "Phase-with-dashes",
        "Phase_with_underscores",
        "Phase (with parentheses)",
        "Phase with numbers 123",
    ]
    
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write'):
            with patch('sys.stdout.flush'):
                # Should not raise errors for any phase name
                for phase in special_phases:
                    callback(phase, 0.5)


def test_progress_callback_bounds():
    """Test progress callback handles edge cases for progress values."""
    callback = create_progress_callback(verbose=False)
    
    outputs = []
    
    def capture_write(text):
        """Capture written text."""
        outputs.append(text)
    
    with patch('sys.stdout.isatty', return_value=True):
        with patch('sys.stdout.write', side_effect=capture_write):
            with patch('sys.stdout.flush'):
                # Should handle values at boundaries
                callback("Minimum", 0.0)
                callback("Maximum", 1.0)
                
                # Clear outputs for next test
                outputs.clear()
                
                # Should handle values slightly outside bounds (shouldn't crash).
                # Note: In real usage, values should be 0.0-1.0, but we test robustness.
                # The implementation clamps these values to the valid range.
                callback("Below minimum", -0.1)  # Should be clamped to 0.0
                
                # Find the progress bar output (not newline)
                below_outputs = [o for o in outputs if '░' in o or '█' in o]
                assert len(below_outputs) > 0
                below_output = below_outputs[0]
                # Should show 0% not negative
                assert '  0%' in below_output or '0%' in below_output
                
                outputs.clear()
                
                callback("Above maximum", 1.1)   # Should be clamped to 1.0
                # Find the progress bar output (not newline)
                above_outputs = [o for o in outputs if '░' in o or '█' in o]
                assert len(above_outputs) > 0
                above_output = above_outputs[0]
                # Should show 100% not more
                assert '100%' in above_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
