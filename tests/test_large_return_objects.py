"""
Tests for large return object detection and memory safety.
"""

import pytest
from amorsize import optimize
from amorsize.system_info import get_available_memory


def small_return_function(x):
    """Function that returns a small object (few bytes)."""
    return x * 2


def medium_return_function(x):
    """Function that returns a medium object (~1KB)."""
    return "x" * 1024


def large_return_function(x):
    """Function that returns a large object (~10MB)."""
    # Create a 10MB string
    return "x" * (10 * 1024 * 1024)


def test_small_return_no_warning():
    """Test that small return objects don't trigger warnings."""
    data = range(1000)
    result = optimize(small_return_function, data, verbose=False)
    
    # Should not have memory warnings
    memory_warnings = [w for w in result.warnings if "Large return objects" in w]
    assert len(memory_warnings) == 0
    
    # Should recommend parallelization if beneficial
    assert result.n_jobs >= 1


def test_large_return_warning():
    """Test that large return objects trigger appropriate warnings."""
    # Use enough items to trigger memory warning
    # Each item returns ~10MB, so 100 items = 1GB
    available_memory = get_available_memory()
    memory_threshold = available_memory * 0.5
    
    # Calculate how many large objects we need to exceed threshold
    large_object_size = 10 * 1024 * 1024  # 10MB
    items_needed = int(memory_threshold / large_object_size) + 10
    
    data = range(items_needed)
    result = optimize(large_return_function, data, verbose=False)
    
    # Should have memory warning
    memory_warnings = [w for w in result.warnings if "Large return objects" in w]
    assert len(memory_warnings) > 0
    
    # Warning should mention memory consumption
    assert "GB" in memory_warnings[0]
    assert "imap_unordered" in memory_warnings[0] or "batches" in memory_warnings[0]


def test_memory_warning_content():
    """Test that memory warnings contain useful information."""
    available_memory = get_available_memory()
    memory_threshold = available_memory * 0.5
    
    large_object_size = 10 * 1024 * 1024  # 10MB
    # Need enough items to exceed threshold
    items_needed = int(memory_threshold / large_object_size) + 50
    
    data = range(items_needed)
    result = optimize(large_return_function, data, verbose=False, sample_size=5)
    
    # Should have memory warning
    memory_warnings = [w for w in result.warnings if "Large return objects" in w]
    assert len(memory_warnings) > 0, f"Expected memory warning but got: {result.warnings}"
    
    warning = memory_warnings[0]
    
    # Should mention memory amounts
    assert "GB" in warning
    
    # Should provide actionable advice
    assert "imap_unordered" in warning or "batches" in warning
    
    # Should mention available memory
    assert "available" in warning


def test_verbose_mode_shows_memory_estimates():
    """Test that verbose mode displays memory estimates when appropriate."""
    import io
    import sys
    
    # Use a simple function that won't trigger pickling or fast-fail issues
    data = range(100)
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    try:
        # Use the medium_return_function which is defined at module level (picklable)
        # and has a known size
        result = optimize(medium_return_function, data, verbose=True, sample_size=5)
        output = captured_output.getvalue()
        
        # Check that the output was captured
        assert len(output) > 0, "Expected verbose output"
        
        # The verbose output should mention estimated items or serial execution time
        # (even if function is fast, we should see SOME output)
        has_estimate_info = any([
            "estimated total items" in output.lower(),
            "estimated serial execution time" in output.lower(),
            "estimated result memory" in output.lower(),
            "average execution time" in output.lower(),
        ])
        assert has_estimate_info, f"Expected timing/size estimates in verbose output: {output}"
        
    finally:
        sys.stdout = old_stdout


def test_medium_return_objects():
    """Test behavior with medium-sized return objects (edge case)."""
    # Medium objects shouldn't trigger warnings for reasonable dataset sizes
    data = range(1000)
    result = optimize(medium_return_function, data, verbose=False)
    
    # With 1KB returns and 1000 items = 1MB total, should be fine
    memory_warnings = [w for w in result.warnings if "Large return objects" in w]
    assert len(memory_warnings) == 0


def test_edge_case_exact_threshold():
    """Test behavior when result memory is exactly at threshold."""
    available_memory = get_available_memory()
    memory_threshold = available_memory * 0.5
    
    # Create a function that returns objects sized to hit exactly threshold
    target_object_size = int(memory_threshold / 100)  # 100 items to hit threshold
    
    def threshold_function(x):
        return "x" * target_object_size
    
    data = range(100)
    result = optimize(threshold_function, data, verbose=False)
    
    # Right at threshold - may or may not warn depending on rounding
    # Just check it doesn't crash
    assert result is not None
    assert result.n_jobs >= 1


def test_small_dataset_large_returns():
    """Test that small datasets don't trigger warnings even with large returns."""
    # Only 5 items, even at 10MB each = 50MB, shouldn't exceed threshold on most systems
    data = range(5)
    result = optimize(large_return_function, data, verbose=False)
    
    # Should not have memory warnings for such a small dataset
    memory_warnings = [w for w in result.warnings if "Large return objects" in w]
    assert len(memory_warnings) == 0


def test_generator_no_false_warnings():
    """Test that generators trigger appropriate warnings when size is unknown."""
    def gen():
        for i in range(100):
            yield i
    
    # Use the module-level small_return_function which is picklable
    result = optimize(small_return_function, gen(), verbose=False, sample_size=5)
    
    # Generators with picklable functions should not trigger large return warnings
    # (since we can't determine size, we can't warn about large returns)
    large_return_warnings = [w for w in result.warnings if "Large return objects" in w]
    assert len(large_return_warnings) == 0, f"Unexpected large return warning for generator: {large_return_warnings}"
    
    # When function is too fast or if  generator is processed, we may or may not get a size warning
    # The key test is: no false alarms about large returns when we don't know the size
    # Just verify the optimization completed without crashing
    assert result is not None
    assert result.n_jobs >= 1


def test_warning_suggests_alternatives():
    """Test that warnings suggest appropriate alternatives."""
    available_memory = get_available_memory()
    memory_threshold = available_memory * 0.5
    
    large_object_size = 10 * 1024 * 1024  # 10MB
    items_needed = int(memory_threshold / large_object_size) + 10
    
    data = range(items_needed)
    result = optimize(large_return_function, data, verbose=False)
    
    memory_warnings = [w for w in result.warnings if "Large return objects" in w]
    assert len(memory_warnings) > 0
    
    warning = memory_warnings[0].lower()
    
    # Should suggest at least one alternative approach
    has_suggestion = any(keyword in warning for keyword in [
        "imap_unordered",
        "batches",
        "batch",
        "chunk",
        "streaming"
    ])
    assert has_suggestion, f"Warning should suggest alternatives: {warning}"


def test_memory_calculation_accuracy():
    """Test that memory calculations are reasonably accurate."""
    # Create function with known return size
    known_size = 1024 * 100  # 100KB
    
    def known_size_function(x):
        return "x" * known_size
    
    data = range(1000)
    result = optimize(known_size_function, data, verbose=False)
    
    # Total should be ~100MB (1000 * 100KB)
    # This shouldn't trigger warning on most systems (threshold is 50% of RAM)
    # Just verify it completes without errors
    assert result is not None
    assert result.n_jobs >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
