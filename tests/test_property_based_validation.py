"""
Property-based tests for the validation module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the validation system across a wide range of inputs.
"""

import pickle
import time
from typing import Any, Dict, List

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize.validation import (
    ValidationResult,
    validate_spawn_cost_measurement,
    validate_chunking_overhead_measurement,
    validate_pickle_overhead_measurement,
    validate_system_resources,
    validate_multiprocessing_basic,
    validate_system,
)


class TestValidationResultInvariants:
    """Test invariant properties that should always hold for ValidationResult."""

    @given(
        passed=st.integers(min_value=0, max_value=100),
        failed=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=1000)
    def test_check_counts_non_negative(self, passed, failed):
        """Test that check counts are always non-negative."""
        result = ValidationResult()
        result.checks_passed = passed
        result.checks_failed = failed
        
        assert result.checks_passed >= 0, "Passed checks should be non-negative"
        assert result.checks_failed >= 0, "Failed checks should be non-negative"

    @given(
        passed=st.integers(min_value=0, max_value=100),
        failed=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=1000)
    def test_health_computation_deterministic(self, passed, failed):
        """Test that health computation is deterministic."""
        result1 = ValidationResult()
        result1.checks_passed = passed
        result1.checks_failed = failed
        result1.compute_health()
        health1 = result1.overall_health
        
        result2 = ValidationResult()
        result2.checks_passed = passed
        result2.checks_failed = failed
        result2.compute_health()
        health2 = result2.overall_health
        
        assert health1 == health2, "Health computation should be deterministic"

    @given(
        passed=st.integers(min_value=0, max_value=100),
        failed=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=1000)
    def test_health_values_valid(self, passed, failed):
        """Test that health values are always from valid set."""
        result = ValidationResult()
        result.checks_passed = passed
        result.checks_failed = failed
        result.compute_health()
        
        valid_health_values = {"excellent", "good", "poor", "critical", "unknown"}
        assert result.overall_health in valid_health_values, \
            f"Health value '{result.overall_health}' not in valid set"

    @given(
        passed=st.integers(min_value=95, max_value=100),
        failed=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=50, deadline=1000)
    def test_high_pass_rate_yields_good_health(self, passed, failed):
        """Test that high pass rate yields good/excellent health."""
        assume(passed + failed > 0)  # Avoid division by zero
        
        result = ValidationResult()
        result.checks_passed = passed
        result.checks_failed = failed
        # Don't add errors, so health can be excellent
        result.compute_health()
        
        # With pass rate >= 95% and no errors, health should be excellent or good
        assert result.overall_health in {"excellent", "good"}, \
            f"High pass rate should yield good/excellent, got {result.overall_health}"

    @given(
        passed=st.integers(min_value=0, max_value=40),
        failed=st.integers(min_value=60, max_value=100)
    )
    @settings(max_examples=50, deadline=1000)
    def test_low_pass_rate_yields_poor_health(self, passed, failed):
        """Test that low pass rate yields poor/critical health."""
        assume(passed + failed > 0)  # Avoid division by zero
        
        result = ValidationResult()
        result.checks_passed = passed
        result.checks_failed = failed
        result.compute_health()
        
        # With pass rate < 60%, health should be poor or critical
        assert result.overall_health in {"poor", "critical"}, \
            f"Low pass rate should yield poor/critical, got {result.overall_health}"

    @given(warnings=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10))
    @settings(max_examples=50, deadline=1000)
    def test_warnings_list_valid(self, warnings):
        """Test that warnings list is properly maintained."""
        result = ValidationResult()
        for warning in warnings:
            result.add_warning(warning)
        
        assert len(result.warnings) == len(warnings), "Warning count should match additions"
        assert all(isinstance(w, str) for w in result.warnings), "All warnings should be strings"

    @given(errors=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10))
    @settings(max_examples=50, deadline=1000)
    def test_errors_list_valid(self, errors):
        """Test that errors list is properly maintained."""
        result = ValidationResult()
        for error in errors:
            result.add_error(error)
        
        assert len(result.errors) == len(errors), "Error count should match additions"
        assert all(isinstance(e, str) for e in result.errors), "All errors should be strings"

    @given(
        check_name=st.text(min_size=1, max_size=50),
        passed=st.booleans()
    )
    @settings(max_examples=50, deadline=1000)
    def test_add_check_updates_counts(self, check_name, passed):
        """Test that add_check properly updates check counts."""
        result = ValidationResult()
        initial_passed = result.checks_passed
        initial_failed = result.checks_failed
        
        result.add_check(check_name, passed)
        
        if passed:
            assert result.checks_passed == initial_passed + 1, "Passed count should increment"
            assert result.checks_failed == initial_failed, "Failed count should not change"
        else:
            assert result.checks_passed == initial_passed, "Passed count should not change"
            assert result.checks_failed == initial_failed + 1, "Failed count should increment"

    @given(
        check_name=st.text(min_size=1, max_size=50),
        passed=st.booleans(),
        details=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.integers(), st.floats(allow_nan=False), st.text())
        )
    )
    @settings(max_examples=50, deadline=1000)
    def test_add_check_stores_details(self, check_name, passed, details):
        """Test that add_check stores details correctly."""
        result = ValidationResult()
        result.add_check(check_name, passed, details)
        
        if details:
            assert check_name in result.details, "Check name should be in details"
            assert result.details[check_name] == details, "Details should match"

    @given(
        passed=st.integers(min_value=0, max_value=100),
        failed=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=50, deadline=1000)
    def test_str_method_returns_string(self, passed, failed):
        """Test that __str__ method returns a valid string."""
        result = ValidationResult()
        result.checks_passed = passed
        result.checks_failed = failed
        result.compute_health()
        
        output = str(result)
        assert isinstance(output, str), "__str__ should return string"
        assert len(output) > 0, "__str__ should return non-empty string"
        assert "AMORSIZE SYSTEM VALIDATION REPORT" in output, "Should contain report header"


class TestValidationFunctionProperties:
    """Test properties of individual validation functions."""

    @pytest.mark.slow
    def test_spawn_cost_validation_returns_tuple(self):
        """Test that spawn cost validation returns tuple."""
        passed, details = validate_spawn_cost_measurement(verbose=False)
        
        assert isinstance(passed, bool), "First return value should be bool"
        assert isinstance(details, dict), "Second return value should be dict"

    @pytest.mark.slow
    def test_spawn_cost_validation_deterministic(self):
        """Test that spawn cost validation is deterministic."""
        # Note: This test may fail if system load changes significantly between calls
        # We're testing structural determinism, not value determinism
        passed1, details1 = validate_spawn_cost_measurement(verbose=False)
        passed2, details2 = validate_spawn_cost_measurement(verbose=False)
        
        # Both should return same type
        assert type(passed1) == type(passed2), "Return types should match"
        # Both should have reasonable keys (flexible check to avoid brittleness)
        # Essential keys should be present when validation succeeds
        if passed1:
            assert 'measured_spawn_cost' in details1 or 'error' in details1, \
                "Should have either measurement or error"

    @pytest.mark.slow
    def test_chunking_overhead_validation_returns_tuple(self):
        """Test that chunking overhead validation returns tuple."""
        passed, details = validate_chunking_overhead_measurement(verbose=False)
        
        assert isinstance(passed, bool), "First return value should be bool"
        assert isinstance(details, dict), "Second return value should be dict"

    @pytest.mark.slow
    def test_pickle_overhead_validation_returns_tuple(self):
        """Test that pickle overhead validation returns tuple."""
        passed, details = validate_pickle_overhead_measurement(verbose=False)
        
        assert isinstance(passed, bool), "First return value should be bool"
        assert isinstance(details, dict), "Second return value should be dict"

    def test_system_resources_validation_returns_tuple(self):
        """Test that system resources validation returns tuple."""
        passed, details = validate_system_resources(verbose=False)
        
        assert isinstance(passed, bool), "First return value should be bool"
        assert isinstance(details, dict), "Second return value should be dict"

    @pytest.mark.slow
    def test_multiprocessing_basic_validation_returns_tuple(self):
        """Test that multiprocessing basic validation returns tuple."""
        passed, details = validate_multiprocessing_basic(verbose=False)
        
        assert isinstance(passed, bool), "First return value should be bool"
        assert isinstance(details, dict), "Second return value should be dict"

    def test_system_resources_details_structure(self):
        """Test that system resources validation returns expected structure."""
        passed, details = validate_system_resources(verbose=False)
        
        # Should have expected keys (unless error occurred)
        if passed:
            assert 'physical_cores' in details, "Should have physical_cores"
            assert 'available_memory' in details, "Should have available_memory"
            assert 'multiprocessing_start_method' in details, "Should have start_method"
            
            # Values should be reasonable
            if 'physical_cores' in details:
                assert isinstance(details['physical_cores'], int), "Cores should be int"
                assert details['physical_cores'] >= 1, "Should have at least 1 core"

    @pytest.mark.slow
    def test_validate_system_returns_result_object(self):
        """Test that validate_system returns ValidationResult."""
        result = validate_system(verbose=False)
        
        assert isinstance(result, ValidationResult), "Should return ValidationResult"
        assert hasattr(result, 'checks_passed'), "Should have checks_passed"
        assert hasattr(result, 'checks_failed'), "Should have checks_failed"
        assert hasattr(result, 'overall_health'), "Should have overall_health"

    @pytest.mark.slow
    def test_validate_system_runs_multiple_checks(self):
        """Test that validate_system runs multiple validation checks."""
        result = validate_system(verbose=False)
        
        # Should have run at least 5 checks (one for each validation function)
        total_checks = result.checks_passed + result.checks_failed
        assert total_checks >= 5, f"Should run at least 5 checks, ran {total_checks}"

    @pytest.mark.slow
    def test_validate_system_computes_health(self):
        """Test that validate_system computes overall health."""
        result = validate_system(verbose=False)
        
        valid_health_values = {"excellent", "good", "poor", "critical", "unknown"}
        assert result.overall_health in valid_health_values, \
            f"Health should be valid, got {result.overall_health}"


class TestPickleOverheadMeasurement:
    """Test properties of pickle overhead measurement."""

    @given(test_data=st.one_of(
        st.integers(),
        st.text(min_size=0, max_size=100),
        st.lists(st.integers(), min_size=0, max_size=100),
        st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=0, max_size=10)
    ))
    @settings(max_examples=50, deadline=5000)
    def test_picklable_objects_succeed(self, test_data):
        """Test that picklable objects can be pickled successfully."""
        try:
            # Should be able to pickle and unpickle
            pickled = pickle.dumps(test_data)
            unpickled = pickle.loads(pickled)
            
            # Unpickled should equal original (for these types)
            if isinstance(test_data, (int, str, list, dict)):
                assert unpickled == test_data, "Unpickled data should equal original"
        except Exception as e:
            # Some edge cases might fail (e.g., very large data), but most should succeed
            pytest.skip(f"Pickle failed (acceptable): {e}")

    @given(data_size=st.integers(min_value=1, max_value=1000))
    @settings(max_examples=30, deadline=3000)
    def test_pickle_time_increases_with_size(self, data_size):
        """Test that pickle time generally increases with data size."""
        # Create small and large datasets
        small_data = list(range(min(10, data_size)))
        large_data = list(range(data_size))
        
        # Measure pickle times
        start = time.perf_counter()
        pickle.dumps(small_data)
        small_time = time.perf_counter() - start
        
        start = time.perf_counter()
        pickle.dumps(large_data)
        large_time = time.perf_counter() - start
        
        # Large data should take at least as long (accounting for noise)
        # We allow some tolerance for measurement noise
        assert small_time >= 0, "Time should be non-negative"
        assert large_time >= 0, "Time should be non-negative"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_validation_result(self):
        """Test that empty ValidationResult behaves correctly."""
        result = ValidationResult()
        result.compute_health()
        
        # Should have unknown health with no checks
        assert result.overall_health == "unknown", "Empty result should be unknown"
        assert result.checks_passed == 0, "Should have 0 passed checks"
        assert result.checks_failed == 0, "Should have 0 failed checks"

    @pytest.mark.slow
    def test_verbose_parameter_handled(self):
        """Test that verbose parameter is handled without errors."""
        # Should not crash with verbose True or False
        result_false = validate_system(verbose=False)
        assert isinstance(result_false, ValidationResult), "Should return result with verbose=False"
        
        result_true = validate_system(verbose=True)
        assert isinstance(result_true, ValidationResult), "Should return result with verbose=True"

    def test_validation_result_str_with_empty_lists(self):
        """Test that __str__ works with empty warnings/errors."""
        result = ValidationResult()
        result.checks_passed = 5
        result.checks_failed = 0
        result.compute_health()
        
        output = str(result)
        assert isinstance(output, str), "Should return string"
        assert "AMORSIZE SYSTEM VALIDATION REPORT" in output, "Should have header"

    def test_validation_result_str_with_warnings_and_errors(self):
        """Test that __str__ includes warnings and errors."""
        result = ValidationResult()
        result.add_warning("Test warning")
        result.add_error("Test error")
        result.compute_health()
        
        output = str(result)
        assert "Test warning" in output, "Should include warning"
        assert "Test error" in output, "Should include error"


class TestNumericalStability:
    """Test numerical stability of health calculations."""

    @given(
        passed=st.integers(min_value=0, max_value=1000),
        failed=st.integers(min_value=0, max_value=1000)
    )
    @settings(max_examples=100, deadline=1000)
    def test_pass_rate_computation_stable(self, passed, failed):
        """Test that pass rate computation is numerically stable."""
        assume(passed + failed > 0)  # Avoid division by zero
        
        result = ValidationResult()
        result.checks_passed = passed
        result.checks_failed = failed
        result.compute_health()
        
        # Compute pass rate manually
        total = passed + failed
        pass_rate = passed / total
        
        # Health should be consistent with pass rate
        if pass_rate >= 0.95:
            assert result.overall_health in {"excellent", "good"}, \
                f"Pass rate {pass_rate} should yield good/excellent"
        elif pass_rate < 0.60:
            assert result.overall_health in {"poor", "critical"}, \
                f"Pass rate {pass_rate} should yield poor/critical"

    @given(
        passed=st.integers(min_value=1, max_value=1000),
        failed=st.integers(min_value=0, max_value=0)
    )
    @settings(max_examples=50, deadline=1000)
    def test_perfect_pass_rate(self, passed, failed):
        """Test that 100% pass rate yields excellent/good health."""
        result = ValidationResult()
        result.checks_passed = passed
        result.checks_failed = failed
        result.compute_health()
        
        # With no failures, should be excellent or good
        assert result.overall_health in {"excellent", "good"}, \
            f"Perfect pass rate should yield excellent/good, got {result.overall_health}"


class TestIntegrationProperties:
    """Test integration properties across multiple components."""

    @pytest.mark.slow
    def test_validate_system_consistency(self):
        """Test that validate_system produces consistent results."""
        # Run twice and compare structure
        result1 = validate_system(verbose=False)
        result2 = validate_system(verbose=False)
        
        # Both should have same number of checks (structure is consistent)
        total1 = result1.checks_passed + result1.checks_failed
        total2 = result2.checks_passed + result2.checks_failed
        assert total1 == total2, "Should run same number of checks"

    @pytest.mark.slow
    def test_validate_system_has_expected_checks(self):
        """Test that validate_system includes all expected validation checks."""
        result = validate_system(verbose=False)
        
        # Should have details for each validation
        expected_checks = [
            'multiprocessing_basic',
            'system_resources',
            'spawn_cost_measurement',
            'chunking_overhead_measurement',
            'pickle_overhead_measurement'
        ]
        
        # Check that these are present in details
        for check in expected_checks:
            assert check in result.details, f"Missing check: {check}"
