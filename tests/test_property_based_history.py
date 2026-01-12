"""
Property-based tests for the history module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the optimization history tracking system across a wide range of inputs and scenarios.
"""

import hashlib
import json
import os
import shutil
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume

from amorsize.comparison import ComparisonConfig, ComparisonResult
from amorsize.history import (
    HistoryEntry,
    get_system_fingerprint,
    _generate_id,
    get_history_dir,
    save_result,
    load_result,
    list_results,
    delete_result,
    compare_entries,
    clear_history,
)


# Custom strategies for generating test data

@st.composite
def valid_name(draw):
    """Generate valid result names."""
    return draw(st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_categories=('Cs',)),
        min_size=1,
        max_size=100
    ))


@st.composite
def valid_function_name(draw):
    """Generate valid function names."""
    return draw(st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),  # lowercase letters
        min_size=1,
        max_size=50
    ))


@st.composite
def valid_data_size(draw):
    """Generate valid data sizes."""
    return draw(st.integers(min_value=0, max_value=100000))


@st.composite
def valid_timestamp(draw):
    """Generate valid ISO 8601 timestamp strings."""
    # Generate a datetime within reasonable range
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Avoid month-end complexity
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))
    
    dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return dt.replace(tzinfo=None).isoformat() + "Z"


@st.composite
def valid_metadata(draw):
    """Generate valid metadata dictionaries."""
    return draw(st.one_of(
        st.none(),
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()),
            max_size=10
        )
    ))


@st.composite
def valid_comparison_config(draw):
    """Generate a valid ComparisonConfig."""
    name = draw(st.text(min_size=1, max_size=50))
    n_jobs = draw(st.integers(min_value=1, max_value=32))
    chunksize = draw(st.integers(min_value=1, max_value=1000))
    executor_type = draw(st.sampled_from(["process", "thread"]))
    
    return ComparisonConfig(
        name=name,
        n_jobs=n_jobs,
        chunksize=chunksize,
        executor_type=executor_type
    )


@st.composite
def valid_comparison_result(draw):
    """Generate a valid ComparisonResult."""
    num_configs = draw(st.integers(min_value=1, max_value=5))
    configs = [draw(valid_comparison_config()) for _ in range(num_configs)]
    
    # Generate execution times (all positive)
    execution_times = [
        draw(st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False))
        for _ in range(num_configs)
    ]
    
    # Calculate speedups relative to first config
    baseline_time = execution_times[0]
    speedups = [baseline_time / time if time > 0 else 1.0 for time in execution_times]
    
    # Best config is the one with fastest time
    best_config_index = execution_times.index(min(execution_times))
    
    recommendations = draw(st.lists(st.text(min_size=1, max_size=100), max_size=5))
    
    return ComparisonResult(
        configs=configs,
        execution_times=execution_times,
        speedups=speedups,
        best_config_index=best_config_index,
        recommendations=recommendations
    )


@st.composite
def valid_system_info(draw):
    """Generate a valid system info dictionary."""
    # Generate Python version manually instead of using regex
    major = 3
    minor = draw(st.integers(min_value=7, max_value=13))
    patch = draw(st.integers(min_value=0, max_value=20))
    python_version = f"{major}.{minor}.{patch}"
    
    return {
        "platform": draw(st.text(min_size=1, max_size=50)),
        "system": draw(st.sampled_from(["Linux", "Windows", "Darwin"])),
        "machine": draw(st.sampled_from(["x86_64", "amd64", "arm64"])),
        "processor": draw(st.text(min_size=1, max_size=50)),
        "python_version": python_version,
        "physical_cores": draw(st.integers(min_value=1, max_value=128)),
        "available_memory_gb": draw(st.floats(min_value=0.5, max_value=1024.0, allow_nan=False, allow_infinity=False)),
        "multiprocessing_start_method": draw(st.sampled_from(["fork", "spawn", "forkserver"]))
    }


# Fixtures for temporary history directories

@pytest.fixture
def temp_history_dir(monkeypatch):
    """Create a temporary history directory for testing."""
    temp_dir = tempfile.mkdtemp()
    history_path = Path(temp_dir) / ".amorsize" / "history"
    history_path.mkdir(parents=True, exist_ok=True)
    
    # Monkey-patch get_history_dir to use temp directory
    monkeypatch.setattr("amorsize.history.get_history_dir", lambda: history_path)
    
    yield history_path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestHistoryEntryInvariants:
    """Test HistoryEntry class invariants and serialization."""

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
        function_name=valid_function_name(),
        data_size=valid_data_size(),
        system_info=valid_system_info(),
        metadata=valid_metadata(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_history_entry_stores_all_fields(
        self, result, name, function_name, data_size, system_info, metadata
    ):
        """Test that HistoryEntry correctly stores all provided fields."""
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        entry_id = _generate_id(name, timestamp)
        
        entry = HistoryEntry(
            id=entry_id,
            name=name,
            timestamp=timestamp,
            result=result,
            function_name=function_name,
            data_size=data_size,
            system_info=system_info,
            metadata=metadata
        )
        
        # All fields should match
        assert entry.id == entry_id
        assert entry.name == name
        assert entry.timestamp == timestamp
        assert entry.result == result
        assert entry.function_name == function_name
        assert entry.data_size == data_size
        assert entry.system_info == system_info
        assert entry.metadata == (metadata or {})

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
        function_name=valid_function_name(),
        data_size=valid_data_size(),
        system_info=valid_system_info(),
        metadata=valid_metadata(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_history_entry_serialization_roundtrip(
        self, result, name, function_name, data_size, system_info, metadata
    ):
        """Test that HistoryEntry can be serialized to dict and back without loss."""
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        entry_id = _generate_id(name, timestamp)
        
        original = HistoryEntry(
            id=entry_id,
            name=name,
            timestamp=timestamp,
            result=result,
            function_name=function_name,
            data_size=data_size,
            system_info=system_info,
            metadata=metadata
        )
        
        # Serialize to dict and back
        data = original.to_dict()
        restored = HistoryEntry.from_dict(data)
        
        # All fields should match
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.timestamp == original.timestamp
        assert restored.function_name == original.function_name
        assert restored.data_size == original.data_size
        assert restored.system_info == original.system_info
        assert restored.metadata == original.metadata
        
        # Result should have same structure
        assert len(restored.result.configs) == len(original.result.configs)
        assert restored.result.execution_times == original.result.execution_times
        assert restored.result.speedups == original.result.speedups
        assert restored.result.best_config_index == original.result.best_config_index

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
        function_name=valid_function_name(),
        data_size=valid_data_size(),
        system_info=valid_system_info(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_history_entry_handles_missing_metadata(
        self, result, name, function_name, data_size, system_info
    ):
        """Test that HistoryEntry handles missing metadata gracefully."""
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        entry_id = _generate_id(name, timestamp)
        
        entry = HistoryEntry(
            id=entry_id,
            name=name,
            timestamp=timestamp,
            result=result,
            function_name=function_name,
            data_size=data_size,
            system_info=system_info,
            metadata=None
        )
        
        # Metadata should be empty dict
        assert entry.metadata == {}
        
        # Serialization should work
        data = entry.to_dict()
        assert "metadata" in data
        assert data["metadata"] == {}

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
        function_name=valid_function_name(),
        data_size=valid_data_size(),
        system_info=valid_system_info(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_history_entry_to_dict_is_json_serializable(
        self, result, name, function_name, data_size, system_info
    ):
        """Test that to_dict produces JSON-serializable output."""
        timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        entry_id = _generate_id(name, timestamp)
        
        entry = HistoryEntry(
            id=entry_id,
            name=name,
            timestamp=timestamp,
            result=result,
            function_name=function_name,
            data_size=data_size,
            system_info=system_info,
            metadata={"key": "value", "number": 42}
        )
        
        data = entry.to_dict()
        
        # Should be JSON serializable
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["id"] == entry_id
        assert parsed["name"] == name


class TestIDGeneration:
    """Test ID generation properties."""

    @given(
        name=valid_name(),
        timestamp=valid_timestamp(),
    )
    @settings(max_examples=100, deadline=None)
    def test_generate_id_returns_12_char_string(self, name, timestamp):
        """Test that _generate_id always returns a 12-character string."""
        entry_id = _generate_id(name, timestamp)
        
        assert isinstance(entry_id, str)
        assert len(entry_id) == 12
        # Should be hex characters (SHA256 hash truncated)
        assert all(c in "0123456789abcdef" for c in entry_id)

    @given(
        name=valid_name(),
        timestamp=valid_timestamp(),
    )
    @settings(max_examples=100, deadline=None)
    def test_generate_id_is_deterministic(self, name, timestamp):
        """Test that _generate_id produces same ID for same inputs."""
        id1 = _generate_id(name, timestamp)
        id2 = _generate_id(name, timestamp)
        
        assert id1 == id2

    @given(
        name1=valid_name(),
        name2=valid_name(),
        timestamp=valid_timestamp(),
    )
    @settings(max_examples=100, deadline=None)
    def test_generate_id_different_names_produce_different_ids(
        self, name1, name2, timestamp
    ):
        """Test that different names produce different IDs."""
        assume(name1 != name2)
        
        id1 = _generate_id(name1, timestamp)
        id2 = _generate_id(name2, timestamp)
        
        assert id1 != id2


class TestSystemFingerprint:
    """Test system fingerprint generation properties."""

    @settings(max_examples=10, deadline=None)
    @given(st.just(None))  # No input needed, but hypothesis requires at least one strategy
    def test_system_fingerprint_returns_dict(self, _):
        """Test that get_system_fingerprint returns a dictionary."""
        fingerprint = get_system_fingerprint()
        
        assert isinstance(fingerprint, dict)

    @settings(max_examples=10, deadline=None)
    @given(st.just(None))
    def test_system_fingerprint_contains_required_keys(self, _):
        """Test that system fingerprint contains all required keys."""
        fingerprint = get_system_fingerprint()
        
        required_keys = {
            "platform", "system", "machine", "processor",
            "python_version", "physical_cores", "available_memory_gb",
            "multiprocessing_start_method"
        }
        
        assert set(fingerprint.keys()) == required_keys

    @settings(max_examples=10, deadline=None)
    @given(st.just(None))
    def test_system_fingerprint_has_correct_types(self, _):
        """Test that system fingerprint fields have correct types."""
        fingerprint = get_system_fingerprint()
        
        assert isinstance(fingerprint["platform"], str)
        assert isinstance(fingerprint["system"], str)
        assert isinstance(fingerprint["machine"], str)
        assert isinstance(fingerprint["processor"], str)
        assert isinstance(fingerprint["python_version"], str)
        assert isinstance(fingerprint["physical_cores"], int)
        assert isinstance(fingerprint["available_memory_gb"], (int, float))
        assert isinstance(fingerprint["multiprocessing_start_method"], str)
        
        # Non-negative values
        assert fingerprint["physical_cores"] > 0
        assert fingerprint["available_memory_gb"] >= 0


class TestSaveAndLoadOperations:
    """Test save and load operations with various inputs."""

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
        function_name=valid_function_name(),
        data_size=valid_data_size(),
        metadata=valid_metadata(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_and_load_preserves_data(
        self, temp_history_dir, result, name, function_name, data_size, metadata
    ):
        """Test that saving and loading a result preserves all data."""
        # Save result
        entry_id = save_result(
            result=result,
            name=name,
            function_name=function_name,
            data_size=data_size,
            metadata=metadata
        )
        
        # Load result
        loaded = load_result(entry_id)
        
        assert loaded is not None
        assert loaded.id == entry_id
        assert loaded.name == name
        assert loaded.function_name == function_name
        assert loaded.data_size == data_size
        assert loaded.metadata == (metadata or {})
        
        # Result should match
        assert len(loaded.result.configs) == len(result.configs)
        assert loaded.result.execution_times == result.execution_times

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_returns_valid_id(self, temp_history_dir, result, name):
        """Test that save_result returns a valid ID."""
        entry_id = save_result(result=result, name=name)
        
        assert isinstance(entry_id, str)
        assert len(entry_id) == 12
        assert all(c in "0123456789abcdef" for c in entry_id)

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_creates_json_file(self, temp_history_dir, result, name):
        """Test that save_result creates a JSON file."""
        entry_id = save_result(result=result, name=name)
        
        filepath = temp_history_dir / f"{entry_id}.json"
        assert filepath.exists()
        assert filepath.is_file()
        
        # Should be valid JSON
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
        assert data["id"] == entry_id

    @given(entry_id=st.text(min_size=12, max_size=12))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_load_nonexistent_returns_none(self, temp_history_dir, entry_id):
        """Test that loading a nonexistent entry returns None."""
        loaded = load_result(entry_id)
        assert loaded is None


class TestListOperations:
    """Test list_results operations with various filters and limits."""

    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_list_results_empty_directory(self, temp_history_dir, _):
        """Test that list_results returns empty list for empty directory."""
        results = list_results()
        assert results == []

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_results_finds_saved_entry(self, temp_history_dir, result, name):
        """Test that list_results finds a saved entry."""
        entry_id = save_result(result=result, name=name)
        
        results = list_results()
        
        assert len(results) >= 1
        assert any(entry.id == entry_id for entry in results)

    @given(
        results=st.lists(
            st.tuples(valid_comparison_result(), valid_name()),
            min_size=2,
            max_size=5
        )
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_results_sorting(self, temp_history_dir, results):
        """Test that list_results sorts by timestamp (newest first)."""
        # Clear any existing files first
        clear_history()
        
        entry_ids = []
        for result, name in results:
            time.sleep(0.01)  # Ensure different timestamps
            entry_id = save_result(result=result, name=name)
            entry_ids.append(entry_id)
        
        listed = list_results()
        
        # Should be in reverse chronological order
        assert len(listed) == len(entry_ids)
        
        # Timestamps should be in descending order
        for i in range(len(listed) - 1):
            assert listed[i].timestamp >= listed[i + 1].timestamp

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
        limit=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_results_respects_limit(self, temp_history_dir, result, name, limit):
        """Test that list_results respects the limit parameter."""
        # Save multiple entries
        num_entries = limit + 2
        for i in range(num_entries):
            save_result(result=result, name=f"{name}_{i}")
        
        results = list_results(limit=limit)
        
        assert len(results) <= limit

    @given(
        results=st.lists(
            st.tuples(valid_comparison_result(), valid_name()),
            min_size=3,
            max_size=5
        ),
        filter_str=st.text(min_size=1, max_size=10),
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_results_name_filter(self, temp_history_dir, results, filter_str):
        """Test that list_results filters by name correctly."""
        # Save entries with and without filter string
        for result, base_name in results:
            save_result(result=result, name=f"{base_name}_{filter_str}_test")
            save_result(result=result, name=f"{base_name}_other")
        
        filtered = list_results(name_filter=filter_str)
        
        # All returned entries should contain filter string
        for entry in filtered:
            assert filter_str.lower() in entry.name.lower()


class TestDeleteOperations:
    """Test delete operations."""

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_delete_removes_entry(self, temp_history_dir, result, name):
        """Test that delete_result removes the entry."""
        entry_id = save_result(result=result, name=name)
        
        # Entry should exist
        assert load_result(entry_id) is not None
        
        # Delete it
        deleted = delete_result(entry_id)
        assert deleted is True
        
        # Should no longer exist
        assert load_result(entry_id) is None

    @given(entry_id=st.text(min_size=12, max_size=12))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_delete_nonexistent_returns_false(self, temp_history_dir, entry_id):
        """Test that deleting a nonexistent entry returns False."""
        deleted = delete_result(entry_id)
        assert deleted is False

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_delete_is_idempotent(self, temp_history_dir, result, name):
        """Test that delete_result is idempotent."""
        entry_id = save_result(result=result, name=name)
        
        # First delete should succeed
        assert delete_result(entry_id) is True
        
        # Second delete should fail (already gone)
        assert delete_result(entry_id) is False


class TestCompareOperations:
    """Test compare_entries operations."""

    @given(
        result1=valid_comparison_result(),
        result2=valid_comparison_result(),
        name1=valid_name(),
        name2=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_compare_entries_returns_comparison_dict(
        self, temp_history_dir, result1, result2, name1, name2
    ):
        """Test that compare_entries returns a comparison dictionary."""
        assume(name1 != name2)
        
        entry_id1 = save_result(result=result1, name=name1)
        entry_id2 = save_result(result=result2, name=name2)
        
        comparison = compare_entries(entry_id1, entry_id2)
        
        assert comparison is not None
        assert isinstance(comparison, dict)
        assert "entry1" in comparison
        assert "entry2" in comparison
        assert "comparison" in comparison

    @given(
        result1=valid_comparison_result(),
        result2=valid_comparison_result(),
        name1=valid_name(),
        name2=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_compare_entries_calculates_deltas(
        self, temp_history_dir, result1, result2, name1, name2
    ):
        """Test that compare_entries correctly calculates deltas."""
        assume(name1 != name2)
        
        entry_id1 = save_result(result=result1, name=name1)
        entry_id2 = save_result(result=result2, name=name2)
        
        comparison = compare_entries(entry_id1, entry_id2)
        
        # Extract best times from results
        best_time1 = min(result1.execution_times)
        best_time2 = min(result2.execution_times)
        
        # Check delta calculations
        assert "speedup_delta" in comparison["comparison"]
        assert "time_delta_seconds" in comparison["comparison"]
        assert "time_delta_percent" in comparison["comparison"]
        
        # Time delta should match
        expected_time_delta = best_time2 - best_time1
        assert abs(comparison["comparison"]["time_delta_seconds"] - expected_time_delta) < 0.001

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
        nonexistent_id=st.text(min_size=12, max_size=12),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_compare_entries_with_nonexistent_returns_none(
        self, temp_history_dir, result, name, nonexistent_id
    ):
        """Test that compare_entries returns None if either entry doesn't exist."""
        entry_id = save_result(result=result, name=name)
        
        comparison1 = compare_entries(entry_id, nonexistent_id)
        comparison2 = compare_entries(nonexistent_id, entry_id)
        
        assert comparison1 is None
        assert comparison2 is None

    @given(
        result1=valid_comparison_result(),
        result2=valid_comparison_result(),
        name1=valid_name(),
        name2=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_compare_entries_detects_regression(
        self, temp_history_dir, result1, result2, name1, name2
    ):
        """Test that compare_entries detects performance regressions."""
        assume(name1 != name2)
        
        entry_id1 = save_result(result=result1, name=name1)
        entry_id2 = save_result(result=result2, name=name2)
        
        comparison = compare_entries(entry_id1, entry_id2)
        
        # Check regression flag
        assert "is_regression" in comparison["comparison"]
        assert isinstance(comparison["comparison"]["is_regression"], bool)
        
        # Regression should be true if time2 > time1
        best_time1 = min(result1.execution_times)
        best_time2 = min(result2.execution_times)
        expected_regression = best_time2 > best_time1
        
        assert comparison["comparison"]["is_regression"] == expected_regression


class TestClearOperations:
    """Test clear_history operations."""

    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_clear_history_empty_returns_zero(self, temp_history_dir, _):
        """Test that clear_history returns 0 for empty directory."""
        count = clear_history()
        assert count == 0

    @given(
        results=st.lists(
            st.tuples(valid_comparison_result(), valid_name()),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_clear_history_removes_all_entries(self, temp_history_dir, results):
        """Test that clear_history removes all entries."""
        # Save multiple entries
        for result, name in results:
            save_result(result=result, name=name)
        
        # Verify entries exist
        before_count = len(list_results())
        assert before_count == len(results)
        
        # Clear history
        cleared = clear_history()
        assert cleared == len(results)
        
        # Verify all entries are gone
        after_count = len(list_results())
        assert after_count == 0

    @given(
        results=st.lists(
            st.tuples(valid_comparison_result(), valid_name()),
            min_size=2,
            max_size=5
        )
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_clear_history_returns_correct_count(self, temp_history_dir, results):
        """Test that clear_history returns the correct count of deleted entries."""
        # Save entries
        for result, name in results:
            save_result(result=result, name=name)
        
        # Clear and check count
        count = clear_history()
        assert count == len(results)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @given(result=valid_comparison_result())
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_with_empty_name(self, temp_history_dir, result):
        """Test saving with minimal name (1 character)."""
        # Hypothesis ensures min_size=1, so we test with that
        entry_id = save_result(result=result, name="a")
        
        loaded = load_result(entry_id)
        assert loaded is not None
        assert loaded.name == "a"

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_with_zero_data_size(self, temp_history_dir, result, name):
        """Test saving with zero data size."""
        entry_id = save_result(result=result, name=name, data_size=0)
        
        loaded = load_result(entry_id)
        assert loaded is not None
        assert loaded.data_size == 0

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_with_large_data_size(self, temp_history_dir, result, name):
        """Test saving with very large data size."""
        large_size = 10**9  # 1 billion
        entry_id = save_result(result=result, name=name, data_size=large_size)
        
        loaded = load_result(entry_id)
        assert loaded is not None
        assert loaded.data_size == large_size

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_with_empty_metadata(self, temp_history_dir, result, name):
        """Test saving with empty metadata dictionary."""
        entry_id = save_result(result=result, name=name, metadata={})
        
        loaded = load_result(entry_id)
        assert loaded is not None
        assert loaded.metadata == {}


class TestThreadSafety:
    """Test thread safety of history operations."""

    @given(
        results=st.lists(
            st.tuples(valid_comparison_result(), valid_name()),
            min_size=5,
            max_size=10
        )
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_concurrent_saves(self, temp_history_dir, results):
        """Test that concurrent saves don't corrupt data."""
        entry_ids = []
        errors = []
        
        def save_entry(result, name):
            try:
                entry_id = save_result(result=result, name=name)
                entry_ids.append(entry_id)
            except Exception as e:
                errors.append(e)
        
        # Save entries concurrently
        threads = []
        for result, name in results:
            thread = threading.Thread(target=save_entry, args=(result, name))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0
        
        # All entries should be saved
        assert len(entry_ids) == len(results)
        
        # All entries should be loadable
        for entry_id in entry_ids:
            loaded = load_result(entry_id)
            assert loaded is not None


class TestIntegrationProperties:
    """Test integration scenarios and full lifecycle."""

    @given(
        results=st.lists(
            st.tuples(valid_comparison_result(), valid_name(), valid_function_name()),
            min_size=2,
            max_size=5
        )
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_full_lifecycle(self, temp_history_dir, results):
        """Test full lifecycle: save, list, load, compare, delete."""
        entry_ids = []
        
        # Save all results
        for result, name, func_name in results:
            entry_id = save_result(
                result=result,
                name=name,
                function_name=func_name,
                data_size=len(results) * 100
            )
            entry_ids.append(entry_id)
        
        # List should find all entries
        listed = list_results()
        assert len(listed) >= len(entry_ids)
        
        # Load each entry
        for entry_id in entry_ids:
            loaded = load_result(entry_id)
            assert loaded is not None
        
        # Compare first two entries
        if len(entry_ids) >= 2:
            comparison = compare_entries(entry_ids[0], entry_ids[1])
            assert comparison is not None
        
        # Delete all entries
        for entry_id in entry_ids:
            deleted = delete_result(entry_id)
            assert deleted is True
        
        # Clear any remaining
        clear_history()
        
        # Should be empty now
        assert len(list_results()) == 0

    @given(
        result=valid_comparison_result(),
        name=valid_name(),
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_save_load_preserves_result_structure(self, temp_history_dir, result, name):
        """Test that saving and loading preserves ComparisonResult structure."""
        entry_id = save_result(result=result, name=name)
        loaded = load_result(entry_id)
        
        assert loaded is not None
        
        # Check result structure is preserved
        original_result = result
        loaded_result = loaded.result
        
        # Same number of configs
        assert len(loaded_result.configs) == len(original_result.configs)
        
        # Same execution times
        assert len(loaded_result.execution_times) == len(original_result.execution_times)
        for i in range(len(original_result.execution_times)):
            assert abs(loaded_result.execution_times[i] - original_result.execution_times[i]) < 0.001
        
        # Same speedups
        assert len(loaded_result.speedups) == len(original_result.speedups)
        
        # Same best config index
        assert loaded_result.best_config_index == original_result.best_config_index
        
        # Config details preserved
        for i in range(len(original_result.configs)):
            orig_config = original_result.configs[i]
            loaded_config = loaded_result.configs[i]
            
            assert loaded_config.name == orig_config.name
            assert loaded_config.n_jobs == orig_config.n_jobs
            assert loaded_config.chunksize == orig_config.chunksize
            assert loaded_config.executor_type == orig_config.executor_type
