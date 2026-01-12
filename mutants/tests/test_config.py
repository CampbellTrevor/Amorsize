"""
Tests for configuration export/import functionality.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from amorsize import (
    save_config,
    load_config,
    list_configs,
    get_default_config_dir,
    ConfigData,
    optimize,
    tune_parameters
)


class TestConfigData:
    """Test ConfigData class."""
    
    def test_init_minimal(self):
        """Test ConfigData with minimal parameters."""
        config = ConfigData(n_jobs=4, chunksize=100)
        assert config.n_jobs == 4
        assert config.chunksize == 100
        assert config.executor_type == "process"
        assert config.estimated_speedup == 1.0
        assert config.source == "optimize"
        assert config.timestamp is not None
        assert config.system_info is not None
    
    def test_init_full(self):
        """Test ConfigData with all parameters."""
        config = ConfigData(
            n_jobs=8,
            chunksize=50,
            executor_type="thread",
            estimated_speedup=6.5,
            function_name="my_func",
            data_size=1000,
            avg_execution_time=0.001,
            notes="Test config",
            source="tune"
        )
        assert config.n_jobs == 8
        assert config.chunksize == 50
        assert config.executor_type == "thread"
        assert config.estimated_speedup == 6.5
        assert config.function_name == "my_func"
        assert config.data_size == 1000
        assert config.avg_execution_time == 0.001
        assert config.notes == "Test config"
        assert config.source == "tune"
    
    def test_to_dict(self):
        """Test converting ConfigData to dictionary."""
        config = ConfigData(n_jobs=4, chunksize=100)
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert data['n_jobs'] == 4
        assert data['chunksize'] == 100
        assert 'system_info' in data
        assert 'timestamp' in data
        assert 'amorsize_version' in data
    
    def test_from_dict(self):
        """Test creating ConfigData from dictionary."""
        data = {
            'n_jobs': 8,
            'chunksize': 50,
            'executor_type': 'thread',
            'estimated_speedup': 5.0
        }
        config = ConfigData.from_dict(data)
        
        assert config.n_jobs == 8
        assert config.chunksize == 50
        assert config.executor_type == 'thread'
        assert config.estimated_speedup == 5.0
    
    def test_round_trip(self):
        """Test to_dict -> from_dict preserves data."""
        original = ConfigData(
            n_jobs=4,
            chunksize=100,
            function_name="test_func",
            notes="Round trip test"
        )
        
        data = original.to_dict()
        restored = ConfigData.from_dict(data)
        
        assert restored.n_jobs == original.n_jobs
        assert restored.chunksize == original.chunksize
        assert restored.function_name == original.function_name
        assert restored.notes == original.notes
    
    def test_repr(self):
        """Test __repr__ method."""
        config = ConfigData(n_jobs=4, chunksize=100)
        repr_str = repr(config)
        
        assert 'ConfigData' in repr_str
        assert 'n_jobs=4' in repr_str
        assert 'chunksize=100' in repr_str
    
    def test_str(self):
        """Test __str__ method."""
        config = ConfigData(
            n_jobs=4,
            chunksize=100,
            function_name="my_func"
        )
        str_rep = str(config)
        
        assert 'Configuration' in str_rep
        assert 'n_jobs' in str_rep
        assert '4' in str_rep
        assert 'chunksize' in str_rep
        assert '100' in str_rep


class TestSaveLoadConfig:
    """Test save_config and load_config functions."""
    
    def test_save_and_load_json(self):
        """Test saving and loading JSON configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.json'
            
            config = ConfigData(n_jobs=4, chunksize=100)
            save_config(config, filepath)
            
            assert filepath.exists()
            
            loaded = load_config(filepath)
            assert loaded.n_jobs == 4
            assert loaded.chunksize == 100
    
    def test_save_and_load_yaml(self):
        """Test saving and loading YAML configuration."""
        pytest.importorskip("yaml")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_config.yaml'
            
            config = ConfigData(n_jobs=8, chunksize=50)
            save_config(config, filepath, format='yaml')
            
            assert filepath.exists()
            
            loaded = load_config(filepath, format='yaml')
            assert loaded.n_jobs == 8
            assert loaded.chunksize == 50
    
    def test_auto_format_detection_json(self):
        """Test automatic format detection for JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'config.json'
            
            config = ConfigData(n_jobs=2, chunksize=200)
            save_config(config, filepath, format='auto')
            
            loaded = load_config(filepath, format='auto')
            assert loaded.n_jobs == 2
            assert loaded.chunksize == 200
    
    def test_auto_format_detection_yaml(self):
        """Test automatic format detection for YAML."""
        pytest.importorskip("yaml")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'config.yml'
            
            config = ConfigData(n_jobs=3, chunksize=150)
            save_config(config, filepath, format='auto')
            
            loaded = load_config(filepath, format='auto')
            assert loaded.n_jobs == 3
            assert loaded.chunksize == 150
    
    def test_save_creates_parent_directory(self):
        """Test that save_config creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'subdir1' / 'subdir2' / 'config.json'
            
            config = ConfigData(n_jobs=4, chunksize=100)
            save_config(config, filepath)
            
            assert filepath.exists()
            assert filepath.parent.exists()
    
    def test_save_without_overwrite_raises_error(self):
        """Test that saving to existing file without overwrite raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'config.json'
            
            config = ConfigData(n_jobs=4, chunksize=100)
            save_config(config, filepath)
            
            # Try to save again without overwrite
            with pytest.raises(FileExistsError):
                save_config(config, filepath, overwrite=False)
    
    def test_save_with_overwrite_succeeds(self):
        """Test that overwrite=True allows replacing existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'config.json'
            
            config1 = ConfigData(n_jobs=4, chunksize=100)
            save_config(config1, filepath)
            
            config2 = ConfigData(n_jobs=8, chunksize=50)
            save_config(config2, filepath, overwrite=True)
            
            loaded = load_config(filepath)
            assert loaded.n_jobs == 8
            assert loaded.chunksize == 50
    
    def test_load_nonexistent_file_raises_error(self):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config('/nonexistent/path/config.json')
    
    def test_load_invalid_json_raises_error(self):
        """Test that loading invalid JSON raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'invalid.json'
            filepath.write_text('{ invalid json }')
            
            with pytest.raises(ValueError, match='Invalid JSON'):
                load_config(filepath)
    
    def test_load_missing_required_fields_raises_error(self):
        """Test that loading config without required fields raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'incomplete.json'
            # Missing 'chunksize' field
            filepath.write_text('{"n_jobs": 4}')
            
            with pytest.raises(ValueError, match='missing required fields'):
                load_config(filepath)
    
    def test_save_unsupported_format_raises_error(self):
        """Test that unsupported format raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'config.txt'
            config = ConfigData(n_jobs=4, chunksize=100)
            
            with pytest.raises(ValueError, match='Unsupported format'):
                save_config(config, filepath, format='xml')
    
    def test_save_yaml_without_pyyaml_raises_error(self):
        """Test that YAML save without PyYAML raises ImportError."""
        # This test is tricky - we need to mock the import failure
        # For now, we'll just document that this should raise ImportError
        pass


class TestListConfigs:
    """Test list_configs function."""
    
    def test_list_configs_empty_directory(self):
        """Test listing configs in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            configs = list_configs(tmpdir)
            assert configs == []
    
    def test_list_configs_nonexistent_directory(self):
        """Test listing configs in nonexistent directory."""
        configs = list_configs('/nonexistent/directory')
        assert configs == []
    
    def test_list_configs_finds_json_files(self):
        """Test that list_configs finds JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test config files
            config1 = ConfigData(n_jobs=4, chunksize=100)
            config2 = ConfigData(n_jobs=8, chunksize=50)
            
            save_config(config1, Path(tmpdir) / 'config1.json')
            save_config(config2, Path(tmpdir) / 'config2.json')
            
            configs = list_configs(tmpdir)
            assert len(configs) == 2
            assert all(str(p).endswith('.json') for p in configs)
    
    def test_list_configs_finds_yaml_files(self):
        """Test that list_configs finds YAML files."""
        pytest.importorskip("yaml")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ConfigData(n_jobs=4, chunksize=100)
            save_config(config, Path(tmpdir) / 'config.yaml', format='yaml')
            save_config(config, Path(tmpdir) / 'config.yml', format='yaml')
            
            configs = list_configs(tmpdir)
            assert len(configs) == 2
    
    def test_list_configs_sorted(self):
        """Test that list_configs returns sorted results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ConfigData(n_jobs=4, chunksize=100)
            
            # Create files in non-alphabetical order
            save_config(config, Path(tmpdir) / 'c.json')
            save_config(config, Path(tmpdir) / 'a.json')
            save_config(config, Path(tmpdir) / 'b.json')
            
            configs = list_configs(tmpdir)
            names = [p.name for p in configs]
            assert names == sorted(names)


class TestGetDefaultConfigDir:
    """Test get_default_config_dir function."""
    
    def test_get_default_config_dir_returns_path(self):
        """Test that get_default_config_dir returns a Path."""
        config_dir = get_default_config_dir()
        assert isinstance(config_dir, Path)
    
    def test_get_default_config_dir_creates_directory(self):
        """Test that get_default_config_dir creates the directory."""
        config_dir = get_default_config_dir()
        assert config_dir.exists()
        assert config_dir.is_dir()
    
    def test_get_default_config_dir_location(self):
        """Test that default config dir is in home directory."""
        config_dir = get_default_config_dir()
        assert '.amorsize' in str(config_dir)
        assert 'configs' in str(config_dir)


class TestOptimizationResultIntegration:
    """Test integration with OptimizationResult."""
    
    def test_optimization_result_save_config(self):
        """Test saving config from OptimizationResult."""
        def simple_func(x):
            return x * 2
        
        result = optimize(simple_func, range(100))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'opt_config.json'
            result.save_config(filepath, function_name='simple_func')
            
            assert filepath.exists()
            
            config = load_config(filepath)
            assert config.n_jobs == result.n_jobs
            assert config.chunksize == result.chunksize
            assert config.executor_type == result.executor_type
            assert config.function_name == 'simple_func'
            assert config.source == 'optimize'
    
    def test_optimization_result_save_config_with_notes(self):
        """Test saving config with notes."""
        def simple_func(x):
            return x * 2
        
        result = optimize(simple_func, range(50))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'config.json'
            result.save_config(
                filepath,
                function_name='simple_func',
                notes='Optimized for small datasets'
            )
            
            config = load_config(filepath)
            assert config.notes == 'Optimized for small datasets'


class TestTuningResultIntegration:
    """Test integration with TuningResult."""
    
    def test_tuning_result_save_config(self):
        """Test saving config from TuningResult."""
        def simple_func(x):
            return x * 2
        
        # Use quick_tune for faster testing
        from amorsize import quick_tune
        result = quick_tune(simple_func, range(50))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'tune_config.json'
            result.save_config(filepath, function_name='simple_func')
            
            assert filepath.exists()
            
            config = load_config(filepath)
            assert config.n_jobs == result.best_n_jobs
            assert config.chunksize == result.best_chunksize
            assert config.executor_type == result.executor_type
            assert config.function_name == 'simple_func'
            assert config.source == 'tune'


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_save_and_reuse_config(self):
        """Test saving a config and using it in another run."""
        def cpu_func(x):
            return sum(i**2 for i in range(x))
        
        # First run: optimize and save
        result1 = optimize(cpu_func, range(100, 200))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'cpu_config.json'
            result1.save_config(filepath, function_name='cpu_func')
            
            # Second run: load and verify we can use the config
            config = load_config(filepath)
            
            assert config.n_jobs > 0
            assert config.chunksize > 0
            
            # Could be used to initialize Pool with these parameters
            # with Pool(config.n_jobs) as pool:
            #     results = pool.map(cpu_func, data, chunksize=config.chunksize)
    
    def test_config_with_metadata(self):
        """Test that config preserves important metadata."""
        def test_func(x):
            return x * 2
        
        result = optimize(test_func, range(1000), profile=True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'config.json'
            result.save_config(
                filepath,
                function_name='test_func',
                notes='Production configuration for batch processing'
            )
            
            config = load_config(filepath)
            
            # Verify metadata
            assert config.system_info is not None
            assert 'platform' in config.system_info
            assert 'physical_cores' in config.system_info
            assert config.timestamp is not None
            assert config.notes == 'Production configuration for batch processing'
