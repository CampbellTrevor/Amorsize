"""
Tests for cache validation and repair functionality.
"""

import json
import pytest
import time
from pathlib import Path

from amorsize import (
    optimize,
    validate_cache_entry,
    validate_cache,
    repair_cache,
    CacheValidationResult,
    clear_cache,
    get_cache_dir
)
from amorsize.cache import CacheEntry, save_cache_entry, compute_cache_key
from amorsize.system_info import get_physical_cores, get_available_memory, get_multiprocessing_start_method


def create_test_cache_entry(func_name="test_func"):
    """Helper function to create a valid cache entry for testing."""
    def test_func(x):
        return x ** 2
    
    cache_key = compute_cache_key(test_func, 100, 0.001)
    save_cache_entry(
        cache_key=cache_key,
        n_jobs=2,
        chunksize=100,
        executor_type="process",
        estimated_speedup=1.8,
        reason="Test entry",
        warnings=[]
    )
    return cache_key


class TestCacheValidationResult:
    """Tests for CacheValidationResult class."""
    
    def test_result_initialization(self):
        """Test CacheValidationResult initialization."""
        result = CacheValidationResult(
            is_valid=True,
            total_entries=10,
            valid_entries=9,
            invalid_entries=1,
            issues=["Entry expired"],
            health_score=95.0
        )
        
        assert result.is_valid is True
        assert result.total_entries == 10
        assert result.valid_entries == 9
        assert result.invalid_entries == 1
        assert len(result.issues) == 1
        assert result.health_score == 95.0
    
    def test_str_representation_healthy(self):
        """Test string representation of healthy cache."""
        result = CacheValidationResult(
            is_valid=True,
            total_entries=10,
            valid_entries=10,
            invalid_entries=0,
            issues=[],
            health_score=100.0
        )
        
        str_output = str(result)
        assert "=== Cache Validation Report ===" in str_output
        assert "Total entries examined: 10" in str_output
        assert "Valid entries: 10" in str_output
        assert "Health score: 100.0/100" in str_output
        assert "✓ HEALTHY" in str_output
    
    def test_str_representation_with_issues(self):
        """Test string representation with issues."""
        result = CacheValidationResult(
            is_valid=False,
            total_entries=10,
            valid_entries=7,
            invalid_entries=3,
            issues=["Entry expired", "System incompatible"],
            health_score=75.0
        )
        
        str_output = str(result)
        assert "✗ ISSUES FOUND" in str_output
        assert "Issues found:" in str_output
        assert "Entry expired" in str_output
        assert "System incompatible" in str_output
    
    def test_repr_representation(self):
        """Test repr representation."""
        result = CacheValidationResult(
            is_valid=True,
            total_entries=10,
            valid_entries=9,
            invalid_entries=1,
            issues=[],
            health_score=95.0
        )
        
        repr_output = repr(result)
        assert "CacheValidationResult" in repr_output
        assert "valid=9/10" in repr_output
        assert "health=95.0" in repr_output


class TestValidateCacheEntry:
    """Tests for validate_cache_entry function."""
    
    def test_validate_nonexistent_file(self, tmp_path):
        """Test validation of nonexistent file."""
        nonexistent = tmp_path / "nonexistent.json"
        is_valid, issues = validate_cache_entry(nonexistent)
        
        assert is_valid is False
        assert len(issues) == 1
        assert "does not exist" in issues[0].lower()
    
    def test_validate_invalid_json(self, tmp_path):
        """Test validation of file with invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        is_valid, issues = validate_cache_entry(invalid_file)
        
        assert is_valid is False
        assert any("invalid json" in issue.lower() for issue in issues)
    
    def test_validate_missing_fields(self, tmp_path):
        """Test validation with missing required fields."""
        incomplete_file = tmp_path / "incomplete.json"
        incomplete_file.write_text(json.dumps({
            "n_jobs": 2,
            "chunksize": 100
            # Missing other required fields
        }))
        
        is_valid, issues = validate_cache_entry(incomplete_file)
        
        assert is_valid is False
        assert any("missing required field" in issue.lower() for issue in issues)
    
    def test_validate_invalid_types(self, tmp_path):
        """Test validation with incorrect field types."""
        invalid_types_file = tmp_path / "invalid_types.json"
        invalid_types_file.write_text(json.dumps({
            "n_jobs": "two",  # Should be int
            "chunksize": 100,
            "executor_type": "process",
            "estimated_speedup": 1.5,
            "reason": "test",
            "warnings": [],
            "timestamp": time.time(),
            "system_info": {},
            "cache_version": 1
        }))
        
        is_valid, issues = validate_cache_entry(invalid_types_file)
        
        assert is_valid is False
        assert any("invalid type" in issue.lower() for issue in issues)
    
    def test_validate_invalid_values(self, tmp_path):
        """Test validation with invalid value ranges."""
        invalid_values_file = tmp_path / "invalid_values.json"
        invalid_values_file.write_text(json.dumps({
            "n_jobs": -1,  # Must be >= 1
            "chunksize": 0,  # Must be >= 1
            "executor_type": "invalid",  # Must be "process" or "thread"
            "estimated_speedup": -0.5,  # Must be >= 0
            "reason": "test",
            "warnings": [],
            "timestamp": time.time(),
            "system_info": {},
            "cache_version": 1
        }))
        
        is_valid, issues = validate_cache_entry(invalid_values_file)
        
        assert is_valid is False
        assert any("invalid n_jobs" in issue.lower() for issue in issues)
        assert any("invalid chunksize" in issue.lower() for issue in issues)
        assert any("invalid executor_type" in issue.lower() for issue in issues)
        assert any("invalid speedup" in issue.lower() for issue in issues)
    
    def test_validate_valid_entry(self, tmp_path):
        """Test validation of a valid cache entry."""
        valid_file = tmp_path / "valid.json"
        # Use actual system values to avoid false negatives from system differences
        current_cores = get_physical_cores()
        current_memory = get_available_memory()
        current_start_method = get_multiprocessing_start_method()
        
        valid_file.write_text(json.dumps({
            "n_jobs": 2,
            "chunksize": 100,
            "executor_type": "process",
            "estimated_speedup": 1.8,
            "reason": "Parallelization beneficial",
            "warnings": [],
            "timestamp": time.time(),
            "system_info": {
                "physical_cores": current_cores,
                "available_memory": current_memory,
                "start_method": current_start_method
            },
            "cache_version": 1
        }))
        
        is_valid, issues = validate_cache_entry(valid_file)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_expired_entry(self, tmp_path):
        """Test validation of expired entry."""
        expired_file = tmp_path / "expired.json"
        old_timestamp = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
        expired_file.write_text(json.dumps({
            "n_jobs": 2,
            "chunksize": 100,
            "executor_type": "process",
            "estimated_speedup": 1.8,
            "reason": "Parallelization beneficial",
            "warnings": [],
            "timestamp": old_timestamp,
            "system_info": {
                "physical_cores": 2,
                "available_memory": 1073741824,
                "start_method": "fork"
            },
            "cache_version": 1
        }))
        
        is_valid, issues = validate_cache_entry(expired_file, ttl_seconds=7*24*60*60)
        
        assert is_valid is False
        assert any("expired" in issue.lower() for issue in issues)


class TestValidateCache:
    """Tests for validate_cache function."""
    
    def test_validate_empty_cache(self):
        """Test validation of empty cache."""
        clear_cache()
        result = validate_cache()
        
        assert result.is_valid is True
        assert result.total_entries == 0
        assert result.valid_entries == 0
        assert result.invalid_entries == 0
        assert result.health_score == 100.0
        assert len(result.issues) == 0
    
    def test_validate_cache_with_valid_entries(self):
        """Test validation with only valid entries."""
        clear_cache()
        
        # Create valid cache entry
        create_test_cache_entry()
        
        result = validate_cache()
        
        assert result.is_valid is True
        assert result.total_entries >= 1
        assert result.valid_entries >= 1
        assert result.invalid_entries == 0
        assert result.health_score >= 90.0
    
    def test_validate_cache_with_corrupted_entry(self):
        """Test validation with corrupted entries."""
        clear_cache()
        
        # Create valid entry
        create_test_cache_entry()
        
        # Corrupt the cache file
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        cache_files[0].write_text("{ corrupted json }")
        
        result = validate_cache()
        
        assert result.is_valid is False or result.invalid_entries > 0
        assert result.total_entries >= 1
        assert result.invalid_entries >= 1
    
    def test_validate_cache_health_score_calculation(self):
        """Test health score calculation."""
        clear_cache()
        
        # Create valid entry
        create_test_cache_entry()
        
        result = validate_cache()
        
        # All entries should be valid
        assert result.health_score >= 90.0
        assert result.valid_entries == result.total_entries
    
    def test_validate_benchmark_cache(self):
        """Test validation of benchmark cache."""
        # Just test that it doesn't error
        result = validate_cache(cache_type="benchmark")
        
        assert isinstance(result, CacheValidationResult)
        assert result.health_score >= 0.0
        assert result.health_score <= 100.0
    
    def test_validate_invalid_cache_type(self):
        """Test validation with invalid cache type."""
        with pytest.raises(ValueError, match="Invalid cache_type"):
            validate_cache(cache_type="invalid")


class TestRepairCache:
    """Tests for repair_cache function."""
    
    def test_repair_empty_cache(self):
        """Test repairing empty cache."""
        clear_cache()
        result = repair_cache(dry_run=True)
        
        assert result["examined"] == 0
        assert result["deleted"] == 0
        assert result["kept"] == 0
    
    def test_repair_dry_run_mode(self):
        """Test repair in dry run mode."""
        clear_cache()
        
        # Create valid entry
        create_test_cache_entry()
        
        # Get cache files
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        
        # Corrupt it
        cache_files[0].write_text("{ corrupted }")
        
        # Dry run should not delete
        result = repair_cache(dry_run=True)
        
        assert result["examined"] >= 1
        assert result["deleted"] >= 1
        
        # File should still exist
        assert cache_files[0].exists()
    
    def test_repair_actual_deletion(self):
        """Test actual repair with deletion."""
        clear_cache()
        
        # Create valid entry
        create_test_cache_entry()
        
        # Get cache files
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        
        # Corrupt one
        corrupted_file = cache_files[0]
        corrupted_file.write_text("{ corrupted }")
        
        # Actually repair
        result = repair_cache(dry_run=False)
        
        assert result["examined"] >= 1
        assert result["deleted"] >= 1
        
        # Corrupted file should be deleted
        assert not corrupted_file.exists()
    
    def test_repair_keeps_valid_entries(self):
        """Test that repair keeps valid entries."""
        clear_cache()
        
        # Create valid entry
        create_test_cache_entry()
        
        # Repair (should keep all)
        result = repair_cache(dry_run=False)
        
        assert result["kept"] >= 1
        assert result["deleted"] == 0
    
    def test_repair_benchmark_cache(self):
        """Test repairing benchmark cache."""
        result = repair_cache(dry_run=True, cache_type="benchmark")
        
        assert isinstance(result, dict)
        assert "examined" in result
        assert "deleted" in result
        assert "kept" in result
    
    def test_repair_invalid_cache_type(self):
        """Test repair with invalid cache type."""
        with pytest.raises(ValueError, match="Invalid cache_type"):
            repair_cache(cache_type="invalid")


class TestCacheValidationIntegration:
    """Integration tests for cache validation."""
    
    def test_validate_then_repair_workflow(self):
        """Test complete validate -> repair workflow."""
        clear_cache()
        
        # Create cache entry
        create_test_cache_entry()
        
        # Get cache files
        cache_dir = get_cache_dir()
        cache_files = list(cache_dir.glob("*.json"))
        
        # Corrupt one
        cache_files[0].write_text("{ corrupted }")
        
        # Validate should show issues
        validation = validate_cache()
        assert validation.invalid_entries >= 1
        
        # Repair should fix it
        repair_result = repair_cache(dry_run=False)
        assert repair_result["deleted"] >= 1
        
        # Re-validate should be clean (might be empty if all were corrupted)
        validation_after = validate_cache()
        assert validation_after.health_score >= 90.0 or validation_after.total_entries == 0
    
    def test_cache_validation_after_import(self):
        """Test validation after importing cache."""
        clear_cache()
        
        # Create entry
        create_test_cache_entry()
        
        # Validate - should be healthy
        result = validate_cache()
        assert result.is_valid is True
        assert result.health_score >= 90.0


class TestCacheValidationEdgeCases:
    """Edge case tests for cache validation."""
    
    def test_validate_with_version_mismatch(self, tmp_path):
        """Test validation with cache version mismatch."""
        old_version_file = tmp_path / "old_version.json"
        old_version_file.write_text(json.dumps({
            "n_jobs": 2,
            "chunksize": 100,
            "executor_type": "process",
            "estimated_speedup": 1.8,
            "reason": "test",
            "warnings": [],
            "timestamp": time.time(),
            "system_info": {},
            "cache_version": 999  # Wrong version
        }))
        
        is_valid, issues = validate_cache_entry(old_version_file)
        
        assert is_valid is False
        assert any("version mismatch" in issue.lower() for issue in issues)
    
    def test_validate_with_custom_ttl(self):
        """Test validation with custom TTL."""
        clear_cache()
        
        # Create entry
        create_test_cache_entry()
        
        # Validate with very short TTL (should fail)
        result = validate_cache(ttl_seconds=0)
        
        # Entries should be marked as expired
        assert result.invalid_entries >= 1 or result.health_score < 100.0
    
    def test_validation_result_repr_empty(self):
        """Test repr with no entries."""
        result = CacheValidationResult(
            is_valid=True,
            total_entries=0,
            valid_entries=0,
            invalid_entries=0,
            issues=[],
            health_score=100.0
        )
        
        repr_str = repr(result)
        assert "0/0" in repr_str
        assert "100.0" in repr_str


class TestCacheValidationPublicAPI:
    """Tests for public API exports."""
    
    def test_validate_cache_entry_in_public_api(self):
        """Test that validate_cache_entry is exported."""
        from amorsize import validate_cache_entry
        assert callable(validate_cache_entry)
    
    def test_validate_cache_in_public_api(self):
        """Test that validate_cache is exported."""
        from amorsize import validate_cache
        assert callable(validate_cache)
    
    def test_repair_cache_in_public_api(self):
        """Test that repair_cache is exported."""
        from amorsize import repair_cache
        assert callable(repair_cache)
    
    def test_cache_validation_result_in_public_api(self):
        """Test that CacheValidationResult is exported."""
        from amorsize import CacheValidationResult
        assert CacheValidationResult is not None
    
    def test_functions_have_docstrings(self):
        """Test that validation functions have docstrings."""
        assert validate_cache_entry.__doc__ is not None
        assert validate_cache.__doc__ is not None
        assert repair_cache.__doc__ is not None
        assert len(validate_cache_entry.__doc__) > 50
        assert len(validate_cache.__doc__) > 50
        assert len(repair_cache.__doc__) > 50
