"""
Tests for ML training data versioning and migration.

This module tests version detection, migration utilities, and backward
compatibility of ML training data as the format evolves across iterations.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from amorsize.ml_prediction import (
    get_ml_training_data_version,
    load_ml_training_data,
    update_model_from_execution,
    _migrate_training_data,
    _migrate_training_data_v1_to_v2,
    ML_TRAINING_DATA_VERSION
)


class TestVersionConstant:
    """Test that version constant is properly defined."""
    
    def test_version_is_integer(self):
        """Test that version is an integer."""
        version = get_ml_training_data_version()
        assert isinstance(version, int)
    
    def test_version_is_positive(self):
        """Test that version is positive."""
        version = get_ml_training_data_version()
        assert version > 0
    
    def test_version_matches_constant(self):
        """Test that function returns the module constant."""
        version = get_ml_training_data_version()
        assert version == ML_TRAINING_DATA_VERSION


class TestMigrationV1ToV2:
    """Test migration from version 1 to version 2."""
    
    def test_v1_to_v2_adds_version_field(self):
        """Test that v1→v2 migration adds version field."""
        # Create v1 format data (no version field)
        v1_data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 16000000000,
                'start_method': 'spawn'
            },
            'n_jobs': 4,
            'chunksize': 50,
            'speedup': 3.2,
            'timestamp': 1234567890.0
        }
        
        # Migrate to v2
        v2_data = _migrate_training_data_v1_to_v2(v1_data)
        
        # Check version field was added
        assert 'version' in v2_data
        assert v2_data['version'] == 2
    
    def test_v1_to_v2_preserves_all_fields(self):
        """Test that v1→v2 migration preserves all original fields."""
        # Create v1 format data with many fields
        v1_data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 16000000000,
                'start_method': 'spawn',
                'pickle_size': 1024,
                'coefficient_of_variation': 0.3,
                'function_complexity': 50
            },
            'n_jobs': 4,
            'chunksize': 50,
            'speedup': 3.2,
            'timestamp': 1234567890.0,
            'buffer_size': 12,
            'use_ordered': True,
            'is_streaming': True,
            'system_fingerprint': {
                'system_id': 'test-system',
                'physical_cores': 8,
                'l3_cache_mb': 16.0,
                'memory_bandwidth_gb_s': 50.0,
                'numa_nodes': 1,
                'start_method': 'spawn'
            },
            'adaptive_chunking_enabled': True,
            'adaptation_rate': 0.3,
            'min_chunksize': 10,
            'max_chunksize': 100
        }
        
        # Migrate to v2
        v2_data = _migrate_training_data_v1_to_v2(v1_data)
        
        # Check all original fields preserved
        for key, value in v1_data.items():
            assert key in v2_data
            assert v2_data[key] == value
    
    def test_v1_to_v2_does_not_modify_input(self):
        """Test that v1→v2 migration does not modify input data."""
        # Create v1 format data
        v1_data = {
            'features': {'data_size': 1000},
            'n_jobs': 4,
            'chunksize': 50,
            'speedup': 3.2
        }
        v1_data_copy = v1_data.copy()
        
        # Migrate to v2
        _migrate_training_data_v1_to_v2(v1_data)
        
        # Check input was not modified
        assert v1_data == v1_data_copy
        assert 'version' not in v1_data


class TestGeneralMigration:
    """Test general migration utility function."""
    
    def test_detect_v1_format(self):
        """Test that v1 format is correctly detected (no version field)."""
        v1_data = {
            'features': {'data_size': 1000},
            'n_jobs': 4,
            'chunksize': 50
        }
        
        migrated = _migrate_training_data(v1_data)
        
        # Should have been migrated to current version
        assert migrated['version'] == ML_TRAINING_DATA_VERSION
    
    def test_detect_v2_format(self):
        """Test that v2 format is correctly detected."""
        v2_data = {
            'version': 2,
            'features': {'data_size': 1000},
            'n_jobs': 4,
            'chunksize': 50
        }
        
        migrated = _migrate_training_data(v2_data)
        
        # Should remain unchanged if already at current version
        if ML_TRAINING_DATA_VERSION == 2:
            assert migrated == v2_data
    
    def test_already_current_version_no_change(self):
        """Test that data at current version is not modified."""
        current_data = {
            'version': ML_TRAINING_DATA_VERSION,
            'features': {'data_size': 1000},
            'n_jobs': 4,
            'chunksize': 50
        }
        
        migrated = _migrate_training_data(current_data)
        
        # Should be unchanged
        assert migrated == current_data
    
    def test_verbose_mode_prints_migration_info(self, capsys):
        """Test that verbose mode prints migration information."""
        v1_data = {
            'features': {'data_size': 1000},
            'n_jobs': 4,
            'chunksize': 50
        }
        
        _migrate_training_data(v1_data, verbose=True)
        
        captured = capsys.readouterr()
        assert 'Migrating' in captured.out or 'Migration' in captured.out


class TestSaveWithVersion:
    """Test that new training data is saved with version field."""
    
    def test_update_model_saves_with_version(self):
        """Test that update_model_from_execution saves version field."""
        # Create a simple test function
        def test_func(x):
            return x * 2
        
        # Create temporary cache directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the cache directory
            import amorsize.ml_prediction as ml_module
            original_get_cache = ml_module._get_ml_cache_dir
            ml_module._get_ml_cache_dir = lambda: Path(tmpdir)
            
            try:
                # Update model with execution results
                success = update_model_from_execution(
                    func=test_func,
                    data_size=1000,
                    estimated_item_time=0.01,
                    actual_n_jobs=4,
                    actual_chunksize=50,
                    actual_speedup=3.2,
                    verbose=False
                )
                
                assert success
                
                # Find and load the saved file
                cache_files = list(Path(tmpdir).glob('ml_training_*.json'))
                assert len(cache_files) == 1
                
                with open(cache_files[0], 'r') as f:
                    saved_data = json.load(f)
                
                # Check version field is present and correct
                assert 'version' in saved_data
                assert saved_data['version'] == ML_TRAINING_DATA_VERSION
                
            finally:
                # Restore original function
                ml_module._get_ml_cache_dir = original_get_cache


class TestBackwardCompatibility:
    """Test backward compatibility with old training data."""
    
    def test_load_old_v1_data(self):
        """Test that old v1 data can be loaded and migrated automatically."""
        # Create a v1 format training file
        v1_data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 16000000000,
                'start_method': 'spawn',
                'pickle_size': 1024,
                'coefficient_of_variation': 0.3,
                'function_complexity': 50
            },
            'n_jobs': 4,
            'chunksize': 50,
            'speedup': 3.2,
            'timestamp': 1234567890.0,
            'function_signature': 'test_func_abc123'
        }
        
        # Create temporary cache directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create v1 format file
            cache_file = Path(tmpdir) / 'ml_training_test_abc123_1234567890.json'
            with open(cache_file, 'w') as f:
                json.dump(v1_data, f)
            
            # Patch the cache directory
            import amorsize.ml_prediction as ml_module
            original_get_cache = ml_module._get_ml_cache_dir
            ml_module._get_ml_cache_dir = lambda: Path(tmpdir)
            
            try:
                # Load training data (should auto-migrate)
                training_data = load_ml_training_data(
                    enable_cross_system=False,
                    verbose=False
                )
                
                # Should successfully load despite old format
                assert len(training_data) == 1
                assert training_data[0].n_jobs == 4
                assert training_data[0].chunksize == 50
                assert training_data[0].speedup == 3.2
                
            finally:
                # Restore original function
                ml_module._get_ml_cache_dir = original_get_cache
    
    def test_mixed_version_data(self):
        """Test loading cache with mixed v1 and v2 data."""
        # Create both v1 and v2 format training files
        v1_data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 16000000000,
                'start_method': 'spawn'
            },
            'n_jobs': 4,
            'chunksize': 50,
            'speedup': 3.2,
            'timestamp': 1234567890.0,
            'function_signature': 'test_func_v1'
        }
        
        v2_data = {
            'version': 2,
            'features': {
                'data_size': 2000,
                'estimated_item_time': 0.02,
                'physical_cores': 8,
                'available_memory': 16000000000,
                'start_method': 'spawn'
            },
            'n_jobs': 8,
            'chunksize': 100,
            'speedup': 6.5,
            'timestamp': 1234567891.0,
            'function_signature': 'test_func_v2'
        }
        
        # Create temporary cache directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create both files
            v1_file = Path(tmpdir) / 'ml_training_test_v1_1234567890.json'
            v2_file = Path(tmpdir) / 'ml_training_test_v2_1234567891.json'
            
            with open(v1_file, 'w') as f:
                json.dump(v1_data, f)
            with open(v2_file, 'w') as f:
                json.dump(v2_data, f)
            
            # Patch the cache directory
            import amorsize.ml_prediction as ml_module
            original_get_cache = ml_module._get_ml_cache_dir
            ml_module._get_ml_cache_dir = lambda: Path(tmpdir)
            
            try:
                # Load training data (should handle both formats)
                training_data = load_ml_training_data(
                    enable_cross_system=False,
                    verbose=False
                )
                
                # Should load both samples
                assert len(training_data) == 2
                
                # Check both were loaded correctly
                n_jobs_values = {sample.n_jobs for sample in training_data}
                assert 4 in n_jobs_values  # v1 sample
                assert 8 in n_jobs_values  # v2 sample
                
            finally:
                # Restore original function
                ml_module._get_ml_cache_dir = original_get_cache


class TestEdgeCases:
    """Test edge cases in version handling."""
    
    def test_corrupted_version_field(self):
        """Test handling of corrupted version field."""
        # Create data with invalid version
        bad_data = {
            'version': 'invalid',  # Should be int
            'features': {'data_size': 1000},
            'n_jobs': 4
        }
        
        # Should handle gracefully (treat as v1)
        try:
            migrated = _migrate_training_data(bad_data)
            # If it doesn't raise, check it was handled
            assert 'version' in migrated
        except (TypeError, ValueError):
            # Acceptable to raise an error for invalid data
            pass
    
    def test_future_version_warning(self):
        """Test handling of future version numbers."""
        # Create data with future version
        future_data = {
            'version': 999,
            'features': {'data_size': 1000},
            'n_jobs': 4
        }
        
        # Should not attempt to migrate (already "newer")
        migrated = _migrate_training_data(future_data)
        assert migrated['version'] == 999


class TestIntegration:
    """Integration tests for versioning in real workflows."""
    
    def test_version_roundtrip(self):
        """Test that data can be saved and loaded with version."""
        def test_func(x):
            return x * 2
        
        with tempfile.TemporaryDirectory() as tmpdir:
            import amorsize.ml_prediction as ml_module
            original_get_cache = ml_module._get_ml_cache_dir
            ml_module._get_ml_cache_dir = lambda: Path(tmpdir)
            
            try:
                # Save training data
                success = update_model_from_execution(
                    func=test_func,
                    data_size=1000,
                    estimated_item_time=0.01,
                    actual_n_jobs=4,
                    actual_chunksize=50,
                    actual_speedup=3.2
                )
                assert success
                
                # Load it back
                training_data = load_ml_training_data(
                    enable_cross_system=False,
                    verbose=False
                )
                
                # Should have loaded successfully
                assert len(training_data) >= 1
                
            finally:
                ml_module._get_ml_cache_dir = original_get_cache
