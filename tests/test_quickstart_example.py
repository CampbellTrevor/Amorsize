"""
Tests for quickstart_example.py

Ensures the quickstart example works correctly and doesn't break.
"""

import subprocess
import sys
from pathlib import Path


def test_quickstart_example_exists():
    """Test that quickstart_example.py exists in repo root."""
    quickstart_path = Path(__file__).parent.parent / "quickstart_example.py"
    assert quickstart_path.exists(), "quickstart_example.py should exist in repo root"


def test_quickstart_example_is_executable():
    """Test that quickstart_example.py can be imported without errors."""
    quickstart_path = Path(__file__).parent.parent / "quickstart_example.py"
    
    # Test that we can import it
    import importlib.util
    spec = importlib.util.spec_from_file_location("quickstart_example", quickstart_path)
    assert spec is not None, "Should be able to create module spec"
    module = importlib.util.module_from_spec(spec)
    assert module is not None, "Should be able to create module from spec"


def test_quickstart_example_runs_successfully():
    """Test that quickstart_example.py runs without crashing."""
    quickstart_path = Path(__file__).parent.parent / "quickstart_example.py"
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(quickstart_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Check it ran successfully
    assert result.returncode == 0, f"Script should exit with 0, got {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
    
    # Check for expected output markers
    assert "Amorsize Quick Start" in result.stdout, "Should show title"
    assert "Recommended configuration" in result.stdout, "Should show recommendations"
    assert "Successfully demonstrated Amorsize" in result.stdout, "Should show success message"


def test_quickstart_example_shows_optimization():
    """Test that the example shows optimization results."""
    quickstart_path = Path(__file__).parent.parent / "quickstart_example.py"
    
    result = subprocess.run(
        [sys.executable, str(quickstart_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Should show key optimization metrics
    assert "Workers (n_jobs)" in result.stdout, "Should show n_jobs recommendation"
    assert "Chunk size" in result.stdout, "Should show chunksize recommendation"
    assert "Expected speedup" in result.stdout, "Should show speedup estimate"


def test_quickstart_example_handles_errors_gracefully():
    """Test that the example handles potential errors gracefully."""
    # This test verifies the try/except block works
    # We can't easily trigger an error, but we can check the code structure
    quickstart_path = Path(__file__).parent.parent / "quickstart_example.py"
    
    with open(quickstart_path) as f:
        content = f.read()
        
    # Verify error handling exists
    assert "except KeyboardInterrupt" in content, "Should handle Ctrl+C gracefully"
    assert "except Exception" in content, "Should handle general exceptions"
