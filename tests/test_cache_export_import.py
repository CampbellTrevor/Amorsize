"""
Tests for cache export/import functionality.
"""

import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path
import pytest

from amorsize import optimize, export_cache, import_cache, get_cache_dir, clear_cache
from amorsize.cache import CacheEntry, save_cache_entry, compute_cache_key, DEFAULT_TTL_SECONDS
from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method


def create_test_cache_entry(func, data_size=100, avg_time=0.001):
    """Helper to create and save a test cache entry."""
    cache_key = compute_cache_key(func, data_size, avg_time)
    save_cache_entry(
        cache_key=cache_key,
        n_jobs=2,
        chunksize=25,
        executor_type="process",
        estimated_speedup=1.8,
        reason="Test entry",
        warnings=[]
    )
    return cache_key


class TestExportCache:
    """Test cache export functionality."""
    
    def test_export_empty_cache(self, tmp_path):
        """Test exporting when cache is empty."""
        output_file = tmp_path / "export.json"
        count = export_cache(str(output_file))
        
        assert count == 0
        assert output_file.exists()
        
        # Verify file structure
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'version' in data
        assert 'export_timestamp' in data
        assert 'export_system' in data
        assert 'entries' in data
        assert len(data['entries']) == 0
    
    def test_export_with_entries(self, tmp_path):
        """Test exporting cache with valid entries."""
        # Create some cache entries manually
        def func1(x):
            return x * 2
        
        def func2(x):
            return x ** 2
        
        create_test_cache_entry(func1, 100, 0.001)
        create_test_cache_entry(func2, 200, 0.002)
        
        # Export cache
        output_file = tmp_path / "export.json"
        count = export_cache(str(output_file))
        
        assert count == 2
        assert output_file.exists()
        
        # Verify entries
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data['entries']) == 2
        for entry in data['entries']:
            assert 'cache_key' in entry
            assert 'n_jobs' in entry
            assert 'chunksize' in entry
            assert 'timestamp' in entry
            assert 'system_info' in entry
    
    def test_export_exclude_expired(self, tmp_path):
        """Test that expired entries are excluded by default."""
        def func(x):
            return x * 2
        
        # Create an entry manually with old timestamp (8 days old)
        cache_key = compute_cache_key(func, 100, 0.001)
        cache_dir = get_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        system_info = {
            "physical_cores": get_physical_cores(),
            "available_memory": get_available_memory(),
            "start_method": get_multiprocessing_start_method(),
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"
        }
        
        old_entry = CacheEntry(
            n_jobs=2,
            chunksize=25,
            executor_type="process",
            estimated_speedup=1.8,
            reason="Old entry",
            warnings=[],
            timestamp=time.time() - (8 * 24 * 60 * 60),  # 8 days ago
            system_info=system_info
        )
        
        # Write entry manually
        with open(cache_file, 'w') as f:
            json.dump(old_entry.to_dict(), f, indent=2)
        
        # Export should exclude expired entry by default
        output_file = tmp_path / "export.json"
        count = export_cache(str(output_file), include_expired=False)
        
        assert count == 0
        
        # Export with include_expired should include it
        count = export_cache(str(output_file), include_expired=True)
        assert count == 1
    
    def test_export_creates_directory(self, tmp_path):
        """Test that export creates parent directories if needed."""
        output_file = tmp_path / "nested" / "dir" / "export.json"
        count = export_cache(str(output_file))
        
        assert output_file.exists()
        assert output_file.parent.exists()


class TestImportCache:
    """Test cache import functionality."""
    
    def test_import_nonexistent_file(self, tmp_path):
        """Test importing from nonexistent file raises error."""
        nonexistent = tmp_path / "nonexistent.json"
        
        with pytest.raises(IOError, match="Import file not found"):
            import_cache(str(nonexistent))
    
    def test_import_invalid_json(self, tmp_path):
        """Test importing invalid JSON raises error."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("not valid json {")
        
        with pytest.raises(IOError, match="Invalid JSON"):
            import_cache(str(invalid_file))
    
    def test_import_invalid_format(self, tmp_path):
        """Test importing invalid format raises error."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            json.dump({"foo": "bar"}, f)
        
        with pytest.raises(IOError, match="Invalid export file format"):
            import_cache(str(invalid_file))
    
    def test_import_skip_strategy(self, tmp_path):
        """Test import with skip strategy (default)."""
        def func(x):
            return x * 2
        
        # Create cache entry
        create_test_cache_entry(func, 100, 0.001)
        
        # Export cache
        export_file = tmp_path / "export.json"
        export_count = export_cache(str(export_file))
        assert export_count == 1
        
        # Clear cache
        clear_cache()
        
        # Import with skip strategy
        imported, skipped, incompatible = import_cache(str(export_file), merge_strategy="skip")
        
        assert imported == 1
        assert skipped == 0
        assert incompatible == 0
        
        # Try importing again - should skip
        imported, skipped, incompatible = import_cache(str(export_file), merge_strategy="skip")
        
        assert imported == 0
        assert skipped == 1
        assert incompatible == 0
    
    def test_import_overwrite_strategy(self, tmp_path):
        """Test import with overwrite strategy."""
        def func(x):
            return x * 2
        
        # Create and export cache entry
        create_test_cache_entry(func, 100, 0.001)
        export_file = tmp_path / "export.json"
        export_cache(str(export_file))
        
        # Modify cache entry (simulate change)
        clear_cache()
        time.sleep(0.1)
        create_test_cache_entry(func, 100, 0.001)
        
        # Import with overwrite strategy
        imported, skipped, incompatible = import_cache(str(export_file), merge_strategy="overwrite")
        
        assert imported == 1
        assert skipped == 0
    
    def test_import_update_strategy(self, tmp_path):
        """Test import with update strategy."""
        def func(x):
            return x * 2
        
        # Create older cache entry manually and export
        cache_key = compute_cache_key(func, 100, 0.001)
        cache_dir = get_cache_dir()
        cache_file = cache_dir / f"{cache_key}.json"
        
        system_info = {
            "physical_cores": get_physical_cores(),
            "available_memory": get_available_memory(),
            "start_method": get_multiprocessing_start_method(),
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"
        }
        
        old_entry = CacheEntry(
            n_jobs=2,
            chunksize=25,
            executor_type="process",
            estimated_speedup=1.8,
            reason="Old entry",
            warnings=[],
            timestamp=time.time() - 100,  # Older timestamp
            system_info=system_info
        )
        
        # Write old entry manually
        with open(cache_file, 'w') as f:
            json.dump(old_entry.to_dict(), f, indent=2)
        
        # Export it
        export_file = tmp_path / "export.json"
        export_cache(str(export_file))
        
        # Create newer cache entry
        clear_cache()
        time.sleep(0.1)
        create_test_cache_entry(func, 100, 0.001)  # Newer timestamp
        
        # Import with update strategy - should skip (existing is newer)
        imported, skipped, incompatible = import_cache(str(export_file), merge_strategy="update")
        
        assert imported == 0
        assert skipped == 1
    
    def test_import_update_timestamps(self, tmp_path):
        """Test import with timestamp updates."""
        def func(x):
            return x * 2
        
        # Create and export cache entry
        create_test_cache_entry(func, 100, 0.001)
        export_file = tmp_path / "export.json"
        export_cache(str(export_file))
        
        # Note the original timestamp
        with open(export_file, 'r') as f:
            export_data = json.load(f)
        original_timestamp = export_data['entries'][0]['timestamp']
        
        # Clear cache
        clear_cache()
        
        # Wait a bit
        time.sleep(0.1)
        
        # Import with timestamp update
        current_time = time.time()
        imported, _, _ = import_cache(str(export_file), update_timestamps=True)
        
        assert imported == 1
        
        # Verify timestamp was updated
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) == 1
        
        with open(cache_files[0], 'r') as f:
            entry_data = json.load(f)
        
        new_timestamp = entry_data['timestamp']
        assert new_timestamp > original_timestamp
        assert abs(new_timestamp - current_time) < 1.0  # Within 1 second
    
    def test_import_invalid_merge_strategy(self, tmp_path):
        """Test that invalid merge strategy raises error."""
        export_file = tmp_path / "export.json"
        export_cache(str(export_file))
        
        with pytest.raises(ValueError, match="Invalid merge_strategy"):
            import_cache(str(export_file), merge_strategy="invalid")


class TestExportImportIntegration:
    """Test export/import integration scenarios."""
    
    def test_round_trip_export_import(self, tmp_path):
        """Test that export->import preserves cache entries."""
        def func(x):
            return x ** 2
        
        # Create cache entries
        create_test_cache_entry(func, 100, 0.001)
        create_test_cache_entry(func, 1000, 0.002)
        
        # Export cache
        export_file = tmp_path / "export.json"
        exported = export_cache(str(export_file))
        assert exported == 2
        
        # Clear cache
        clear_cache()
        
        # Import cache
        imported, skipped, incompatible = import_cache(str(export_file))
        assert imported == 2
        assert skipped == 0
        
        # Verify cache files exist
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) == 2
    
    def test_share_cache_between_functions(self, tmp_path):
        """Test sharing cache entries for different functions."""
        def func1(x):
            return x * 2
        
        def func2(x):
            return x ** 2
        
        # Create entries for func1
        create_test_cache_entry(func1, 100, 0.001)
        create_test_cache_entry(func1, 1000, 0.002)
        
        # Export func1's cache
        export_file = tmp_path / "func1_cache.json"
        exported = export_cache(str(export_file))
        assert exported == 2
        
        # Clear cache and create entries for func2
        clear_cache()
        create_test_cache_entry(func2, 200, 0.001)
        
        # Import func1's cache (should merge)
        imported, skipped, incompatible = import_cache(str(export_file))
        assert imported == 2
        
        # Verify all caches exist
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) == 3  # 2 from func1 + 1 from func2
    
    def test_version_control_workflow(self, tmp_path):
        """Test typical version control workflow."""
        def production_func(x):
            """Simulated production function."""
            total = 0
            for i in range(100):
                total += x ** 2
            return total
        
        # Developer 1: Optimize and export
        create_test_cache_entry(production_func, 1000, 0.01)
        export_file = tmp_path / "production_cache.json"
        export_cache(str(export_file))
        
        # Developer 2: Clear local cache and import
        clear_cache()
        imported, _, _ = import_cache(str(export_file))
        assert imported == 1
        
        # Verify cache exists
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) == 1


class TestExportImportEdgeCases:
    """Test edge cases and error handling."""
    
    def test_export_to_readonly_location(self):
        """Test exporting to read-only location raises error."""
        # Try to export to a location that should be read-only
        readonly_path = "/readonly/export.json"
        
        with pytest.raises(IOError, match="Failed to export cache"):
            export_cache(readonly_path)
    
    def test_import_with_compatibility_check(self, tmp_path):
        """Test that compatibility check filters incompatible entries."""
        def func(x):
            return x * 2
        
        # Create and export cache entry
        create_test_cache_entry(func, 100, 0.001)
        export_file = tmp_path / "export.json"
        export_cache(str(export_file))
        
        # Modify export to have incompatible system info
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        # Change core count to something different
        current_cores = data['export_system']['physical_cores']
        different_cores = current_cores + 10
        data['entries'][0]['system_info']['physical_cores'] = different_cores
        
        with open(export_file, 'w') as f:
            json.dump(data, f)
        
        # Clear cache
        clear_cache()
        
        # Import with compatibility check - should mark as incompatible
        imported, skipped, incompatible = import_cache(str(export_file), validate_compatibility=True)
        
        assert imported == 0
        assert incompatible == 1
        
        # Import without compatibility check - should import
        imported, skipped, incompatible = import_cache(str(export_file), validate_compatibility=False)
        
        assert imported == 1
        assert incompatible == 0
    
    def test_export_import_with_corrupted_entry(self, tmp_path):
        """Test that corrupted entries are skipped gracefully."""
        def func(x):
            return x * 2
        
        # Create cache entry
        create_test_cache_entry(func, 100, 0.001)
        
        # Corrupt a cache file
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        assert len(cache_files) == 1
        
        with open(cache_files[0], 'w') as f:
            f.write("corrupted data {")
        
        # Export should skip corrupted entry
        export_file = tmp_path / "export.json"
        count = export_cache(str(export_file))
        assert count == 0


class TestExportImportPublicAPI:
    """Test that export/import are properly exported in public API."""
    
    def test_export_import_in_public_api(self):
        """Test that export_cache and import_cache are importable."""
        from amorsize import export_cache, import_cache
        
        assert callable(export_cache)
        assert callable(import_cache)
    
    def test_functions_have_docstrings(self):
        """Test that functions have comprehensive docstrings."""
        from amorsize import export_cache, import_cache
        
        assert export_cache.__doc__ is not None
        assert len(export_cache.__doc__) > 100
        assert "portable" in export_cache.__doc__.lower()
        
        assert import_cache.__doc__ is not None
        assert len(import_cache.__doc__) > 100
        assert "merge" in import_cache.__doc__.lower()
