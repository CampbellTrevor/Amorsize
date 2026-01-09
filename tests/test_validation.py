"""
Tests for the system validation module.
"""

import pytest
from amorsize.validation import (
    validate_spawn_cost_measurement,
    validate_chunking_overhead_measurement,
    validate_pickle_overhead_measurement,
    validate_system_resources,
    validate_multiprocessing_basic,
    validate_system,
    ValidationResult
)


class TestValidationResult:
    """Tests for ValidationResult class."""
    
    def test_initialization(self):
        """Test that ValidationResult initializes correctly."""
        result = ValidationResult()
        assert result.checks_passed == 0
        assert result.checks_failed == 0
        assert result.warnings == []
        assert result.errors == []
        assert result.details == {}
        assert result.overall_health == "unknown"
    
    def test_add_check_passed(self):
        """Test adding a passed check."""
        result = ValidationResult()
        result.add_check("test_check", True, {"value": 42})
        assert result.checks_passed == 1
        assert result.checks_failed == 0
        assert result.details["test_check"] == {"value": 42}
    
    def test_add_check_failed(self):
        """Test adding a failed check."""
        result = ValidationResult()
        result.add_check("test_check", False, {"error": "failed"})
        assert result.checks_passed == 0
        assert result.checks_failed == 1
        assert result.details["test_check"] == {"error": "failed"}
    
    def test_add_warning(self):
        """Test adding a warning."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"
    
    def test_add_error(self):
        """Test adding an error."""
        result = ValidationResult()
        result.add_error("Test error")
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"
    
    def test_compute_health_excellent(self):
        """Test health computation for excellent system."""
        result = ValidationResult()
        result.add_check("check1", True)
        result.add_check("check2", True)
        result.add_check("check3", True)
        result.add_check("check4", True)
        result.add_check("check5", True)
        result.compute_health()
        assert result.overall_health == "excellent"
    
    def test_compute_health_good(self):
        """Test health computation for good system."""
        result = ValidationResult()
        result.add_check("check1", True)
        result.add_check("check2", True)
        result.add_check("check3", True)
        result.add_check("check4", True)
        result.add_check("check5", False)
        result.compute_health()
        assert result.overall_health == "good"
    
    def test_compute_health_poor(self):
        """Test health computation for poor system."""
        result = ValidationResult()
        result.add_check("check1", True)
        result.add_check("check2", True)
        result.add_check("check3", True)
        result.add_check("check4", False)
        result.add_check("check5", False)
        result.compute_health()
        # 60% pass rate -> poor
        assert result.overall_health == "poor"
    
    def test_compute_health_critical(self):
        """Test health computation for critical system."""
        result = ValidationResult()
        result.add_check("check1", False)
        result.add_check("check2", False)
        result.add_check("check3", False)
        result.add_check("check4", False)
        result.add_check("check5", False)
        result.compute_health()
        assert result.overall_health == "critical"
    
    def test_str_formatting(self):
        """Test string formatting of results."""
        result = ValidationResult()
        result.add_check("test", True, {"value": 42})
        result.add_warning("Test warning")
        result.add_error("Test error")
        result.compute_health()
        
        output = str(result)
        assert "AMORSIZE SYSTEM VALIDATION REPORT" in output
        assert "Overall Health:" in output
        assert "Test warning" in output
        assert "Test error" in output


class TestSpawnCostValidation:
    """Tests for spawn cost measurement validation."""
    
    def test_spawn_cost_validation_succeeds(self):
        """Test that spawn cost validation succeeds."""
        passed, details = validate_spawn_cost_measurement(verbose=False)
        
        # Should pass (or at least not crash)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
        
        # Should have key measurements
        assert 'measured_spawn_cost' in details
        assert 'os_estimate' in details
        assert 'start_method' in details
    
    def test_spawn_cost_verbose_mode(self):
        """Test spawn cost validation in verbose mode."""
        passed, details = validate_spawn_cost_measurement(verbose=True)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)


class TestChunkingOverheadValidation:
    """Tests for chunking overhead measurement validation."""
    
    def test_chunking_overhead_validation_succeeds(self):
        """Test that chunking overhead validation succeeds."""
        passed, details = validate_chunking_overhead_measurement(verbose=False)
        
        # Should pass
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
        
        # Should have key measurements
        assert 'measured_overhead' in details
    
    def test_chunking_overhead_verbose_mode(self):
        """Test chunking overhead validation in verbose mode."""
        passed, details = validate_chunking_overhead_measurement(verbose=True)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)


class TestPickleOverheadValidation:
    """Tests for pickle overhead measurement validation."""
    
    def test_pickle_overhead_validation_succeeds(self):
        """Test that pickle overhead validation succeeds."""
        passed, details = validate_pickle_overhead_measurement(verbose=False)
        
        # Should pass
        assert passed is True
        assert isinstance(details, dict)
        
        # Should have measurements for various data types
        assert 'small_int_pickle_time' in details
        assert 'small_string_pickle_time' in details
        assert 'small_list_pickle_time' in details
        assert 'medium_list_pickle_time' in details
    
    def test_pickle_overhead_verbose_mode(self):
        """Test pickle overhead validation in verbose mode."""
        passed, details = validate_pickle_overhead_measurement(verbose=True)
        assert passed is True
        assert isinstance(details, dict)


class TestSystemResourcesValidation:
    """Tests for system resource detection validation."""
    
    def test_system_resources_validation_succeeds(self):
        """Test that system resource validation succeeds."""
        passed, details = validate_system_resources(verbose=False)
        
        # Should pass
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
        
        # Should have key system information
        assert 'physical_cores' in details
        assert 'available_memory' in details
        assert 'multiprocessing_start_method' in details
        
        # Values should be reasonable
        cores = details['physical_cores']
        assert isinstance(cores, int)
        assert 1 <= cores <= 256
    
    def test_system_resources_verbose_mode(self):
        """Test system resources validation in verbose mode."""
        passed, details = validate_system_resources(verbose=True)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)


class TestMultiprocessingBasicValidation:
    """Tests for basic multiprocessing functionality validation."""
    
    def test_multiprocessing_basic_validation_succeeds(self):
        """Test that basic multiprocessing validation succeeds."""
        passed, details = validate_multiprocessing_basic(verbose=False)
        
        # Should pass (multiprocessing should work)
        assert passed is True
        assert isinstance(details, dict)
        
        # Should have execution details
        assert 'execution_time' in details
        assert 'workers' in details
        assert 'data_size' in details
        assert 'result' in details
    
    def test_multiprocessing_basic_verbose_mode(self):
        """Test multiprocessing basic validation in verbose mode."""
        passed, details = validate_multiprocessing_basic(verbose=True)
        assert passed is True
        assert isinstance(details, dict)


class TestSystemValidation:
    """Tests for complete system validation."""
    
    def test_validate_system_succeeds(self):
        """Test that complete system validation succeeds."""
        result = validate_system(verbose=False)
        
        # Should return ValidationResult
        assert isinstance(result, ValidationResult)
        
        # Should have run all checks
        total_checks = result.checks_passed + result.checks_failed
        assert total_checks == 5  # 5 validation checks
        
        # Should have computed health
        assert result.overall_health in ["excellent", "good", "poor", "critical"]
        
        # Most systems should pass most checks
        assert result.checks_passed >= 3
    
    def test_validate_system_verbose_mode(self):
        """Test system validation in verbose mode."""
        result = validate_system(verbose=True)
        assert isinstance(result, ValidationResult)
    
    def test_validate_system_has_all_checks(self):
        """Test that all expected checks are present."""
        result = validate_system(verbose=False)
        
        # All 5 checks should be in details
        expected_checks = [
            'multiprocessing_basic',
            'system_resources',
            'spawn_cost_measurement',
            'chunking_overhead_measurement',
            'pickle_overhead_measurement'
        ]
        
        for check in expected_checks:
            assert check in result.details, f"Missing check: {check}"
    
    def test_validate_system_report_format(self):
        """Test that validation report is properly formatted."""
        result = validate_system(verbose=False)
        report = str(result)
        
        # Check key sections are present
        assert "AMORSIZE SYSTEM VALIDATION REPORT" in report
        assert "Overall Health:" in report
        assert "Checks Passed:" in report
        assert "DETAILS:" in report
    
    def test_validate_system_returns_consistent_results(self):
        """Test that validation returns consistent results across runs."""
        result1 = validate_system(verbose=False)
        result2 = validate_system(verbose=False)
        
        # Both should have same number of total checks
        total1 = result1.checks_passed + result1.checks_failed
        total2 = result2.checks_passed + result2.checks_failed
        assert total1 == total2
        
        # Health should be similar (within one level)
        health_levels = ["critical", "poor", "good", "excellent"]
        idx1 = health_levels.index(result1.overall_health)
        idx2 = health_levels.index(result2.overall_health)
        assert abs(idx1 - idx2) <= 1  # At most one level difference


class TestValidationIntegration:
    """Integration tests for validation module."""
    
    def test_validation_can_be_imported(self):
        """Test that validation can be imported from main package."""
        from amorsize import validate_system, ValidationResult
        assert callable(validate_system)
        assert ValidationResult is not None
    
    def test_validation_works_end_to_end(self):
        """Test validation works end-to-end."""
        from amorsize import validate_system
        
        result = validate_system(verbose=False)
        
        # Should complete without errors
        assert isinstance(result, ValidationResult)
        assert result.checks_passed + result.checks_failed > 0
        
        # Should be able to print result
        report = str(result)
        assert len(report) > 0
    
    def test_validation_result_can_be_used_programmatically(self):
        """Test that validation results can be used programmatically."""
        from amorsize import validate_system
        
        result = validate_system(verbose=False)
        
        # Should be able to check health
        if result.overall_health in ["good", "excellent"]:
            # System is healthy
            assert result.checks_passed >= 4
        
        # Should be able to access details
        assert isinstance(result.details, dict)
        
        # Should be able to check for specific issues
        if result.errors:
            assert isinstance(result.errors, list)
            assert all(isinstance(e, str) for e in result.errors)
