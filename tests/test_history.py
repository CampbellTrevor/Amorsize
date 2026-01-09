"""
Tests for the history module.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from amorsize.history import (
    save_result, load_result, list_results, delete_result,
    compare_entries, clear_history, get_history_dir,
    get_system_fingerprint, HistoryEntry
)
from amorsize.comparison import ComparisonResult, ComparisonConfig


@pytest.fixture
def temp_history_dir(tmp_path):
    """Create a temporary history directory for tests."""
    history_dir = tmp_path / ".amorsize" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch get_history_dir to return our temp directory
    with patch('amorsize.history.get_history_dir', return_value=history_dir):
        yield history_dir
    
    # Cleanup
    if history_dir.exists():
        shutil.rmtree(history_dir.parent)


@pytest.fixture
def sample_comparison_result():
    """Create a sample ComparisonResult for testing."""
    configs = [
        ComparisonConfig("Serial", 1, 1, "serial"),
        ComparisonConfig("Parallel", 4, 25, "process"),
        ComparisonConfig("Optimal", 8, 10, "process")
    ]
    
    execution_times = [10.0, 3.0, 2.5]
    speedups = [1.0, 3.33, 4.0]
    best_config_index = 2  # Optimal is fastest
    recommendations = ["Use 8 workers for best performance"]
    
    return ComparisonResult(
        configs=configs,
        execution_times=execution_times,
        speedups=speedups,
        best_config_index=best_config_index,
        recommendations=recommendations
    )


def test_get_system_fingerprint():
    """Test system fingerprint generation."""
    fingerprint = get_system_fingerprint()
    
    # Check all required fields are present
    assert "platform" in fingerprint
    assert "system" in fingerprint
    assert "machine" in fingerprint
    assert "python_version" in fingerprint
    assert "physical_cores" in fingerprint
    assert "available_memory_gb" in fingerprint
    assert "multiprocessing_start_method" in fingerprint
    
    # Check types
    assert isinstance(fingerprint["physical_cores"], int)
    assert isinstance(fingerprint["available_memory_gb"], float)
    assert fingerprint["physical_cores"] > 0
    assert fingerprint["available_memory_gb"] > 0


def test_save_and_load_result(temp_history_dir, sample_comparison_result):
    """Test saving and loading a result."""
    # Save result
    entry_id = save_result(sample_comparison_result, "test-run-1", "test_function", 1000)
    
    # Check ID format
    assert isinstance(entry_id, str)
    assert len(entry_id) == 12  # SHA256 truncated to 12 chars
    
    # Check file was created
    assert (temp_history_dir / f"{entry_id}.json").exists()
    
    # Load result
    entry = load_result(entry_id)
    
    # Verify loaded data
    assert entry is not None
    assert entry.id == entry_id
    assert entry.name == "test-run-1"
    assert entry.function_name == "test_function"
    assert entry.data_size == 1000
    assert len(entry.result.configs) == 3
    assert entry.result.best_config.name == "Optimal"


def test_load_nonexistent_result(temp_history_dir):
    """Test loading a result that doesn't exist."""
    entry = load_result("nonexistent123")
    assert entry is None


def test_save_result_with_metadata(temp_history_dir, sample_comparison_result):
    """Test saving a result with custom metadata."""
    metadata = {
        "version": "1.0",
        "environment": "production",
        "notes": "Baseline measurement"
    }
    
    entry_id = save_result(sample_comparison_result, "baseline", "test_func", 500, metadata=metadata)
    entry = load_result(entry_id)
    
    assert entry.metadata == metadata
    assert entry.metadata["version"] == "1.0"
    assert entry.metadata["environment"] == "production"


def test_list_results_empty(temp_history_dir):
    """Test listing results when none exist."""
    entries = list_results()
    assert entries == []


def test_list_results_multiple(temp_history_dir, sample_comparison_result):
    """Test listing multiple results."""
    # Save multiple results
    id1 = save_result(sample_comparison_result, "baseline-v1", "func1", 100)
    id2 = save_result(sample_comparison_result, "optimized-v1", "func2", 200)
    id3 = save_result(sample_comparison_result, "baseline-v2", "func3", 300)
    
    # List all results
    entries = list_results()
    
    assert len(entries) == 3
    assert all(isinstance(e, HistoryEntry) for e in entries)
    
    # Results should be sorted by timestamp (newest first)
    # All were created at nearly the same time, so just check they're present
    ids = {e.id for e in entries}
    assert id1 in ids
    assert id2 in ids
    assert id3 in ids


def test_list_results_with_filter(temp_history_dir, sample_comparison_result):
    """Test filtering results by name."""
    # Save results with different names
    save_result(sample_comparison_result, "baseline-v1", "func", 100)
    save_result(sample_comparison_result, "optimized-v1", "func", 100)
    save_result(sample_comparison_result, "baseline-v2", "func", 100)
    
    # Filter for "baseline"
    entries = list_results(name_filter="baseline")
    
    assert len(entries) == 2
    assert all("baseline" in e.name.lower() for e in entries)


def test_list_results_with_limit(temp_history_dir, sample_comparison_result):
    """Test limiting number of results returned."""
    # Save multiple results
    for i in range(5):
        save_result(sample_comparison_result, f"run-{i}", "func", 100)
    
    # Limit to 3
    entries = list_results(limit=3)
    
    assert len(entries) == 3


def test_delete_result(temp_history_dir, sample_comparison_result):
    """Test deleting a result."""
    # Save result
    entry_id = save_result(sample_comparison_result, "to-delete", "func", 100)
    
    # Verify it exists
    assert load_result(entry_id) is not None
    
    # Delete it
    assert delete_result(entry_id) is True
    
    # Verify it's gone
    assert load_result(entry_id) is None


def test_delete_nonexistent_result(temp_history_dir):
    """Test deleting a result that doesn't exist."""
    assert delete_result("nonexistent123") is False


def test_compare_entries(temp_history_dir):
    """Test comparing two historical results."""
    # Create two different results
    configs1 = [
        ComparisonConfig("Serial", 1, 1, "serial"),
        ComparisonConfig("Parallel", 4, 25, "process")
    ]
    result1 = ComparisonResult(
        configs=configs1,
        execution_times=[10.0, 3.0],
        speedups=[1.0, 3.33],
        best_config_index=1
    )
    
    configs2 = [
        ComparisonConfig("Serial", 1, 1, "serial"),
        ComparisonConfig("Parallel", 4, 25, "process")
    ]
    result2 = ComparisonResult(
        configs=configs2,
        execution_times=[10.0, 2.5],
        speedups=[1.0, 4.0],
        best_config_index=1
    )
    
    # Save both
    id1 = save_result(result1, "v1", "test_func", 1000)
    id2 = save_result(result2, "v2", "test_func", 1000)
    
    # Compare
    comparison = compare_entries(id1, id2)
    
    assert comparison is not None
    assert comparison["entry1"]["id"] == id1
    assert comparison["entry2"]["id"] == id2
    
    # v2 is faster (2.5s vs 3.0s)
    assert comparison["comparison"]["time_delta_seconds"] < 0
    assert comparison["comparison"]["is_regression"] is False
    
    # Speedup improved (4.0x vs 3.33x)
    assert comparison["comparison"]["speedup_delta"] > 0


def test_compare_entries_nonexistent(temp_history_dir):
    """Test comparing entries when one doesn't exist."""
    comparison = compare_entries("nonexistent1", "nonexistent2")
    assert comparison is None


def test_compare_entries_regression(temp_history_dir):
    """Test detecting performance regression."""
    # Create result with good performance
    configs1 = [
        ComparisonConfig("Serial", 1, 1, "serial"),
        ComparisonConfig("Parallel", 4, 25, "process")
    ]
    result1 = ComparisonResult(
        configs=configs1,
        execution_times=[10.0, 2.0],
        speedups=[1.0, 5.0],
        best_config_index=1
    )
    
    # Create result with worse performance (regression)
    configs2 = [
        ComparisonConfig("Serial", 1, 1, "serial"),
        ComparisonConfig("Parallel", 4, 25, "process")
    ]
    result2 = ComparisonResult(
        configs=configs2,
        execution_times=[10.0, 4.0],
        speedups=[1.0, 2.5],
        best_config_index=1
    )
    
    # Save both
    id1 = save_result(result1, "good", "test_func", 1000)
    id2 = save_result(result2, "regressed", "test_func", 1000)
    
    # Compare
    comparison = compare_entries(id1, id2)
    
    # Should detect regression (slower execution)
    assert comparison["comparison"]["is_regression"] is True
    assert comparison["comparison"]["time_delta_seconds"] > 0


def test_clear_history(temp_history_dir, sample_comparison_result):
    """Test clearing all history entries."""
    # Save multiple results
    save_result(sample_comparison_result, "entry1", "func", 100)
    save_result(sample_comparison_result, "entry2", "func", 100)
    save_result(sample_comparison_result, "entry3", "func", 100)
    
    # Verify they exist
    assert len(list_results()) == 3
    
    # Clear history
    count = clear_history()
    
    # Verify all cleared
    assert count == 3
    assert len(list_results()) == 0


def test_clear_history_empty(temp_history_dir):
    """Test clearing history when it's already empty."""
    count = clear_history()
    assert count == 0


def test_history_entry_serialization(sample_comparison_result):
    """Test HistoryEntry serialization and deserialization."""
    # Create entry
    entry = HistoryEntry(
        id="test123",
        name="test-entry",
        timestamp="2024-01-01T12:00:00Z",
        result=sample_comparison_result,
        function_name="test_function",
        data_size=1000,
        system_info={"platform": "Linux", "cores": 8},
        metadata={"version": "1.0"}
    )
    
    # Serialize to dict
    data = entry.to_dict()
    
    # Check structure
    assert data["id"] == "test123"
    assert data["name"] == "test-entry"
    assert data["timestamp"] == "2024-01-01T12:00:00Z"
    assert data["function_name"] == "test_function"
    assert data["data_size"] == 1000
    assert "result" in data
    assert "system_info" in data
    assert "metadata" in data
    
    # Deserialize
    restored = HistoryEntry.from_dict(data)
    
    # Verify restoration
    assert restored.id == entry.id
    assert restored.name == entry.name
    assert restored.timestamp == entry.timestamp
    assert restored.function_name == entry.function_name
    assert restored.data_size == entry.data_size
    assert len(restored.result.configs) == len(entry.result.configs)


def test_save_result_json_format(temp_history_dir, sample_comparison_result):
    """Test that saved files are valid JSON and can be read manually."""
    entry_id = save_result(sample_comparison_result, "json-test", "test_func", 500)
    
    # Read the JSON file directly
    filepath = temp_history_dir / f"{entry_id}.json"
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Verify structure
    assert "id" in data
    assert "name" in data
    assert "timestamp" in data
    assert "function_name" in data
    assert "data_size" in data
    assert "result" in data
    assert "system_info" in data
    
    # Verify result structure
    result = data["result"]
    assert "configs" in result
    assert "execution_times" in result
    assert "speedups" in result
    assert "best_config_index" in result


def test_malformed_json_file(temp_history_dir):
    """Test that malformed JSON files are skipped gracefully."""
    # Create a malformed JSON file
    bad_file = temp_history_dir / "bad123.json"
    with open(bad_file, 'w') as f:
        f.write("{invalid json")
    
    # list_results should skip it and not crash
    entries = list_results()
    assert entries == []


def test_list_results_sorting(temp_history_dir, sample_comparison_result):
    """Test that results are sorted by timestamp (newest first)."""
    import time
    
    # Save results with slight time delays to ensure different timestamps
    id1 = save_result(sample_comparison_result, "first", "func", 100)
    time.sleep(0.01)
    id2 = save_result(sample_comparison_result, "second", "func", 100)
    time.sleep(0.01)
    id3 = save_result(sample_comparison_result, "third", "func", 100)
    
    # List results
    entries = list_results()
    
    # Should be in reverse chronological order
    assert entries[0].id == id3  # newest
    assert entries[1].id == id2
    assert entries[2].id == id1  # oldest


def test_history_entry_with_empty_metadata(temp_history_dir, sample_comparison_result):
    """Test saving result without metadata."""
    entry_id = save_result(sample_comparison_result, "no-metadata", "func", 100)
    entry = load_result(entry_id)
    
    assert entry.metadata == {}


def test_compare_entries_same_system_detection(temp_history_dir):
    """Test detection of whether entries are from the same system."""
    # This test uses the actual system, so both entries will be from same system
    configs = [
        ComparisonConfig("Serial", 1, 1, "serial"),
        ComparisonConfig("Parallel", 4, 25, "process")
    ]
    result = ComparisonResult(
        configs=configs,
        execution_times=[10.0, 3.0],
        speedups=[1.0, 3.33],
        best_config_index=1
    )
    
    id1 = save_result(result, "entry1", "test_func", 1000)
    id2 = save_result(result, "entry2", "test_func", 1000)
    
    comparison = compare_entries(id1, id2)
    
    # Both from same system
    assert comparison["comparison"]["same_system"] is True
