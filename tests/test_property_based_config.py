"""
Property-based tests for configuration export/import module.

These tests use the Hypothesis library to automatically generate and test thousands
of edge cases for the config module, including ConfigData creation, serialization,
file I/O, and integration with optimization results.
"""

import json
import tempfile
from pathlib import Path
from threading import Thread, Barrier
import pytest
from hypothesis import given, strategies as st, settings

from amorsize.config import (
    ConfigData,
    save_config,
    load_config,
    list_configs,
    get_default_config_dir,
    _capture_system_info,
)


# Custom strategies for config parameters
@st.composite
def valid_n_jobs(draw):
    """Generate valid n_jobs values (positive integers)."""
    return draw(st.integers(min_value=1, max_value=128))


@st.composite
def valid_chunksize(draw):
    """Generate valid chunksize values (positive integers)."""
    return draw(st.integers(min_value=1, max_value=10000))


@st.composite
def valid_executor_type(draw):
    """Generate valid executor types."""
    return draw(st.sampled_from(['process', 'thread']))


@st.composite
def valid_speedup(draw):
    """Generate valid speedup values (positive floats)."""
    return draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_data_size(draw):
    """Generate valid data sizes (positive integers or None)."""
    return draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1000000)))


@st.composite
def valid_execution_time(draw):
    """Generate valid execution times (positive floats or None)."""
    return draw(st.one_of(
        st.none(),
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    ))


@st.composite
def valid_source(draw):
    """Generate valid source values."""
    return draw(st.sampled_from(['optimize', 'tune', 'manual', 'benchmark', 'unknown']))


@st.composite
def valid_function_name(draw):
    """Generate valid function names (Python identifiers)."""
    return draw(st.one_of(
        st.none(),
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
                min_size=1, max_size=50).filter(lambda x: x[0] not in '0123456789')
    ))


@st.composite
def valid_notes(draw):
    """Generate valid notes (text or None)."""
    return draw(st.one_of(st.none(), st.text(min_size=0, max_size=500)))


@st.composite
def config_data_strategy(draw):
    """Generate valid ConfigData instances."""
    return ConfigData(
        n_jobs=draw(valid_n_jobs()),
        chunksize=draw(valid_chunksize()),
        executor_type=draw(valid_executor_type()),
        estimated_speedup=draw(valid_speedup()),
        function_name=draw(valid_function_name()),
        data_size=draw(valid_data_size()),
        avg_execution_time=draw(valid_execution_time()),
        notes=draw(valid_notes()),
        source=draw(valid_source())
    )


# Test Class 1: ConfigData Invariants
class TestConfigDataInvariants:
    """Test invariants that should hold for all ConfigData instances."""

    @given(config_data_strategy())
    def test_valid_creation(self, config):
        """ConfigData should be created with valid parameters."""
        assert isinstance(config, ConfigData)
        assert config.n_jobs > 0
        assert config.chunksize > 0
        assert config.executor_type in ['process', 'thread']
        assert config.estimated_speedup >= 0.0
        assert config.source in ['optimize', 'tune', 'manual', 'benchmark', 'unknown']

    @given(config_data_strategy())
    def test_system_info_populated(self, config):
        """System info should be auto-populated if not provided."""
        assert config.system_info is not None
        assert isinstance(config.system_info, dict)
        # Check required keys
        required_keys = ['platform', 'platform_version', 'python_version',
                        'physical_cores', 'available_memory', 'start_method']
        for key in required_keys:
            assert key in config.system_info

    @given(config_data_strategy())
    def test_timestamp_populated(self, config):
        """Timestamp should be auto-populated if not provided."""
        assert config.timestamp is not None
        assert isinstance(config.timestamp, str)
        # Should be valid ISO format (basic check - contains T and -)
        assert 'T' in config.timestamp or ' ' in config.timestamp
        assert '-' in config.timestamp

    @given(config_data_strategy())
    def test_repr_format(self, config):
        """__repr__ should return valid string representation."""
        repr_str = repr(config)
        assert isinstance(repr_str, str)
        assert 'ConfigData' in repr_str
        assert str(config.n_jobs) in repr_str
        assert str(config.chunksize) in repr_str
        assert config.executor_type in repr_str

    @given(config_data_strategy())
    def test_str_format(self, config):
        """__str__ should return human-readable string."""
        str_result = str(config)
        assert isinstance(str_result, str)
        assert 'n_jobs' in str_result
        assert 'chunksize' in str_result
        assert 'executor_type' in str_result
        assert str(config.n_jobs) in str_result
        assert str(config.chunksize) in str_result


# Test Class 2: Serialization Properties
class TestSerializationProperties:
    """Test serialization to/from dictionary."""

    @given(config_data_strategy())
    def test_to_dict_structure(self, config):
        """to_dict should return dict with all required fields."""
        data = config.to_dict()
        assert isinstance(data, dict)
        
        # Check required fields
        required_fields = ['n_jobs', 'chunksize', 'executor_type', 'estimated_speedup',
                          'source', 'system_info', 'timestamp', 'amorsize_version']
        for field in required_fields:
            assert field in data

    @given(config_data_strategy())
    def test_to_dict_preserves_values(self, config):
        """to_dict should preserve all field values."""
        data = config.to_dict()
        assert data['n_jobs'] == config.n_jobs
        assert data['chunksize'] == config.chunksize
        assert data['executor_type'] == config.executor_type
        assert data['estimated_speedup'] == config.estimated_speedup
        assert data['function_name'] == config.function_name
        assert data['data_size'] == config.data_size
        assert data['avg_execution_time'] == config.avg_execution_time
        assert data['notes'] == config.notes
        assert data['source'] == config.source

    @given(config_data_strategy())
    def test_serialization_roundtrip(self, config):
        """ConfigData -> dict -> ConfigData should preserve data."""
        data = config.to_dict()
        restored = ConfigData.from_dict(data)
        
        assert restored.n_jobs == config.n_jobs
        assert restored.chunksize == config.chunksize
        assert restored.executor_type == config.executor_type
        assert restored.estimated_speedup == config.estimated_speedup
        assert restored.function_name == config.function_name
        assert restored.data_size == config.data_size
        assert restored.avg_execution_time == config.avg_execution_time
        assert restored.notes == config.notes
        assert restored.source == config.source

    @given(config_data_strategy())
    def test_json_serializable(self, config):
        """to_dict output should be JSON-serializable."""
        data = config.to_dict()
        # Should not raise exception
        json_str = json.dumps(data)
        assert isinstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


# Test Class 3: File Save/Load Operations
class TestFileSaveLoadOperations:
    """Test save_config and load_config functions."""

    @given(config_data_strategy())
    def test_save_and_load_preserves_data(self, config):
        """Saving and loading should preserve configuration data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.json'
            
            save_config(config, filepath)
            loaded = load_config(filepath)
            
            assert loaded.n_jobs == config.n_jobs
            assert loaded.chunksize == config.chunksize
            assert loaded.executor_type == config.executor_type
            assert loaded.estimated_speedup == config.estimated_speedup
            assert loaded.function_name == config.function_name
            assert loaded.data_size == config.data_size

    @given(config_data_strategy())
    def test_save_creates_file(self, config):
        """save_config should create a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.json'
            
            save_config(config, filepath)
            
            assert filepath.exists()
            assert filepath.is_file()

    @given(config_data_strategy())
    def test_save_creates_parent_directories(self, config):
        """save_config should create parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'subdir' / 'nested' / 'test_config.json'
            
            save_config(config, filepath)
            
            assert filepath.exists()
            assert filepath.parent.exists()

    @given(config_data_strategy())
    def test_overwrite_flag(self, config):
        """overwrite flag should control file replacement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.json'
            
            # First save
            save_config(config, filepath)
            
            # Second save without overwrite should raise error
            with pytest.raises(FileExistsError):
                save_config(config, filepath, overwrite=False)
            
            # Second save with overwrite should succeed
            save_config(config, filepath, overwrite=True)

    @given(config_data_strategy())
    def test_load_nonexistent_raises_error(self, config):
        """Loading non-existent file should raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'nonexistent.json'
            
            with pytest.raises(FileNotFoundError):
                load_config(filepath)


# Test Class 4: Format Detection
class TestFormatDetection:
    """Test automatic format detection from file extensions."""

    @given(config_data_strategy())
    def test_json_format_explicit(self, config):
        """Explicitly specified JSON format should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.xyz'
            
            save_config(config, filepath, format='json')
            loaded = load_config(filepath, format='json')
            
            assert loaded.n_jobs == config.n_jobs

    @given(config_data_strategy())
    def test_json_format_auto_detection(self, config):
        """Auto-detection should work for .json extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.json'
            
            save_config(config, filepath, format='auto')
            loaded = load_config(filepath, format='auto')
            
            assert loaded.n_jobs == config.n_jobs

    @given(config_data_strategy())
    def test_unknown_extension_defaults_to_json(self, config):
        """Unknown extensions should default to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.xyz'
            
            save_config(config, filepath, format='auto')
            loaded = load_config(filepath, format='auto')
            
            assert loaded.n_jobs == config.n_jobs


# Test Class 5: List Configs Operation
class TestListConfigsOperation:
    """Test list_configs function."""

    @given(st.lists(config_data_strategy(), min_size=0, max_size=10))
    def test_list_finds_all_configs(self, configs):
        """list_configs should find all saved configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Save all configs
            for i, config in enumerate(configs):
                filepath = tmpdir_path / f'config_{i}.json'
                save_config(config, filepath)
            
            # List configs
            found = list_configs(tmpdir_path)
            
            assert len(found) == len(configs)

    def test_list_empty_directory(self):
        """list_configs should return empty list for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found = list_configs(tmpdir)
            assert found == []

    def test_list_nonexistent_directory(self):
        """list_configs should return empty list for non-existent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = Path(tmpdir) / 'nonexistent'
            found = list_configs(nonexistent)
            assert found == []

    @given(st.lists(config_data_strategy(), min_size=2, max_size=5))
    def test_list_returns_sorted_paths(self, configs):
        """list_configs should return sorted paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Save configs with random names
            names = ['z_config.json', 'a_config.json', 'm_config.json'][:len(configs)]
            for name, config in zip(names, configs):
                save_config(config, tmpdir_path / name)
            
            found = list_configs(tmpdir_path)
            
            # Should be sorted
            assert found == sorted(found)


# Test Class 6: Default Config Directory
class TestDefaultConfigDirectory:
    """Test get_default_config_dir function."""

    def test_returns_path(self):
        """get_default_config_dir should return a Path object."""
        result = get_default_config_dir()
        assert isinstance(result, Path)

    def test_creates_directory(self):
        """get_default_config_dir should create the directory."""
        result = get_default_config_dir()
        assert result.exists()
        assert result.is_dir()

    def test_consistent_location(self):
        """get_default_config_dir should return consistent location."""
        result1 = get_default_config_dir()
        result2 = get_default_config_dir()
        assert result1 == result2

    def test_in_home_directory(self):
        """Default config directory should be under home directory."""
        result = get_default_config_dir()
        assert Path.home() in result.parents or result == Path.home()


# Test Class 7: System Info Capture
class TestSystemInfoCapture:
    """Test _capture_system_info function."""

    def test_returns_dict(self):
        """_capture_system_info should return a dictionary."""
        info = _capture_system_info()
        assert isinstance(info, dict)

    def test_contains_required_keys(self):
        """_capture_system_info should contain all required keys."""
        info = _capture_system_info()
        required_keys = ['platform', 'platform_version', 'python_version',
                        'physical_cores', 'available_memory', 'start_method']
        for key in required_keys:
            assert key in info

    def test_platform_is_string(self):
        """Platform should be a string."""
        info = _capture_system_info()
        assert isinstance(info['platform'], str)
        assert len(info['platform']) > 0

    def test_physical_cores_is_int(self):
        """Physical cores should be an integer."""
        info = _capture_system_info()
        assert isinstance(info['physical_cores'], int)
        assert info['physical_cores'] > 0

    def test_available_memory_is_numeric(self):
        """Available memory should be a number (int or float)."""
        info = _capture_system_info()
        assert isinstance(info['available_memory'], (int, float))
        assert info['available_memory'] > 0


# Test Class 8: Edge Cases
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimal_n_jobs(self):
        """ConfigData should work with n_jobs=1."""
        config = ConfigData(n_jobs=1, chunksize=1)
        assert config.n_jobs == 1

    def test_minimal_chunksize(self):
        """ConfigData should work with chunksize=1."""
        config = ConfigData(n_jobs=1, chunksize=1)
        assert config.chunksize == 1

    def test_large_n_jobs(self):
        """ConfigData should work with large n_jobs."""
        config = ConfigData(n_jobs=1000, chunksize=1)
        assert config.n_jobs == 1000

    def test_large_chunksize(self):
        """ConfigData should work with large chunksize."""
        config = ConfigData(n_jobs=1, chunksize=1000000)
        assert config.chunksize == 1000000

    def test_zero_speedup(self):
        """ConfigData should work with zero speedup."""
        config = ConfigData(n_jobs=1, chunksize=1, estimated_speedup=0.0)
        assert config.estimated_speedup == 0.0

    def test_very_high_speedup(self):
        """ConfigData should work with very high speedup."""
        config = ConfigData(n_jobs=1, chunksize=1, estimated_speedup=1000.0)
        assert config.estimated_speedup == 1000.0

    def test_empty_function_name(self):
        """ConfigData should work with empty function name."""
        config = ConfigData(n_jobs=1, chunksize=1, function_name='')
        assert config.function_name == ''

    def test_long_notes(self):
        """ConfigData should work with long notes."""
        long_notes = 'x' * 10000
        config = ConfigData(n_jobs=1, chunksize=1, notes=long_notes)
        assert config.notes == long_notes

    def test_special_characters_in_notes(self):
        """ConfigData should work with special characters in notes."""
        special_notes = "Test\n\t\"'\\{}"
        config = ConfigData(n_jobs=1, chunksize=1, notes=special_notes)
        assert config.notes == special_notes

    @given(config_data_strategy())
    def test_save_load_with_special_filename(self, config):
        """Save/load should work with special characters in filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use only safe characters to avoid filesystem issues
            filepath = Path(tmpdir) / 'test_config_123-abc.json'
            
            save_config(config, filepath)
            loaded = load_config(filepath)
            
            assert loaded.n_jobs == config.n_jobs


# Test Class 9: Thread Safety
class TestThreadSafety:
    """Test thread safety of concurrent operations."""

    @given(st.lists(config_data_strategy(), min_size=2, max_size=5))
    @settings(max_examples=10, deadline=5000)  # Fewer examples for thread tests
    def test_concurrent_saves(self, configs):
        """Concurrent saves to different files should not interfere."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            barrier = Barrier(len(configs))
            errors = []
            
            def save_config_thread(config, index):
                try:
                    barrier.wait()  # Synchronize start
                    filepath = tmpdir_path / f'config_{index}.json'
                    save_config(config, filepath)
                except Exception as e:
                    errors.append(e)
            
            threads = [
                Thread(target=save_config_thread, args=(config, i))
                for i, config in enumerate(configs)
            ]
            
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            
            # No errors should occur
            assert len(errors) == 0
            
            # All files should exist
            for i in range(len(configs)):
                filepath = tmpdir_path / f'config_{i}.json'
                assert filepath.exists()


# Test Class 10: Invalid Input Handling
class TestInvalidInputHandling:
    """Test handling of invalid inputs."""

    def test_from_dict_missing_n_jobs(self):
        """from_dict should handle missing n_jobs."""
        data = {'chunksize': 100}
        with pytest.raises(KeyError):
            ConfigData.from_dict(data)

    def test_from_dict_missing_chunksize(self):
        """from_dict should handle missing chunksize."""
        data = {'n_jobs': 4}
        with pytest.raises(KeyError):
            ConfigData.from_dict(data)

    def test_load_invalid_json(self):
        """Loading invalid JSON should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'invalid.json'
            filepath.write_text('not valid json {')
            
            with pytest.raises(ValueError):
                load_config(filepath)

    def test_load_json_not_dict(self):
        """Loading JSON that's not a dict should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'list.json'
            filepath.write_text('[1, 2, 3]')
            
            with pytest.raises(ValueError):
                load_config(filepath)

    def test_load_missing_required_fields(self):
        """Loading config without required fields should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'incomplete.json'
            filepath.write_text('{"n_jobs": 4}')  # Missing chunksize
            
            with pytest.raises(ValueError):
                load_config(filepath)

    def test_save_unsupported_format(self):
        """Saving with unsupported format should raise ValueError."""
        config = ConfigData(n_jobs=4, chunksize=100)
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test.json'
            
            with pytest.raises(ValueError):
                save_config(config, filepath, format='xml')

    def test_load_unsupported_format(self):
        """Loading with unsupported format should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test.json'
            filepath.write_text('{"n_jobs": 4, "chunksize": 100}')
            
            with pytest.raises(ValueError):
                load_config(filepath, format='xml')


# Test Class 11: Integration Properties
class TestIntegrationProperties:
    """Test integration with other parts of the system."""

    @given(config_data_strategy())
    def test_full_save_load_lifecycle(self, config):
        """Full lifecycle: create -> save -> load -> verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'lifecycle_test.json'
            
            # Save
            save_config(config, filepath)
            
            # Load
            loaded = load_config(filepath)
            
            # Verify all fields
            assert loaded.n_jobs == config.n_jobs
            assert loaded.chunksize == config.chunksize
            assert loaded.executor_type == config.executor_type
            assert loaded.estimated_speedup == config.estimated_speedup
            assert loaded.function_name == config.function_name
            assert loaded.data_size == config.data_size
            assert loaded.avg_execution_time == config.avg_execution_time
            assert loaded.notes == config.notes
            assert loaded.source == config.source

    @given(st.lists(config_data_strategy(), min_size=1, max_size=5))
    def test_multiple_configs_in_directory(self, configs):
        """Multiple configs can coexist in same directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Save all configs
            for i, config in enumerate(configs):
                save_config(config, tmpdir_path / f'config_{i}.json')
            
            # List and verify count
            found = list_configs(tmpdir_path)
            assert len(found) == len(configs)
            
            # Load each and verify
            for i, config in enumerate(configs):
                loaded = load_config(tmpdir_path / f'config_{i}.json')
                assert loaded.n_jobs == config.n_jobs
                assert loaded.chunksize == config.chunksize


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
