"""
Tests for the installation verification script.

These tests ensure the verification script itself works correctly.
"""

import subprocess
import sys
from pathlib import Path


def test_verification_script_exists():
    """Test that the verification script exists."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_installation.py"
    assert script_path.exists(), f"Verification script not found at {script_path}"
    assert script_path.is_file(), f"{script_path} is not a file"


def test_verification_script_is_executable():
    """Test that the verification script can be executed."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_installation.py"
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Should exit with 0 (success) or 1 (failure), not crash
    assert result.returncode in [0, 1], f"Script crashed with code {result.returncode}"
    
    # Should produce output
    assert len(result.stdout) > 0, "Script produced no output"
    
    # Should contain expected header
    assert "Amorsize Installation Verification" in result.stdout


def test_verification_script_checks_import():
    """Test that the script checks amorsize import."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_installation.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Should mention import check
    assert "Import amorsize" in result.stdout


def test_verification_script_checks_optimize():
    """Test that the script checks optimize() function."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_installation.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Should mention optimize check
    assert "optimize() function" in result.stdout


def test_verification_script_success_message():
    """Test that script shows success message when all checks pass."""
    script_path = Path(__file__).parent.parent / "scripts" / "verify_installation.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # If amorsize is properly installed (which it should be for tests),
    # all checks should pass
    if result.returncode == 0:
        assert "All" in result.stdout and "checks passed" in result.stdout
        assert "ready to use" in result.stdout
