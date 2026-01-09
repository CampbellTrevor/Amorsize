"""
Tests for input validation in the optimizer module.

This test suite validates that the optimize() function properly validates
its input parameters and provides clear error messages for invalid inputs.
"""

import pytest
from amorsize import optimize


def simple_function(x):
    """A simple test function."""
    return x * 2


class TestFuncValidation:
    """Tests for func parameter validation."""
    
    def test_func_none_raises_error(self):
        """Test that None func raises ValueError."""
        with pytest.raises(ValueError, match="func parameter cannot be None"):
            optimize(None, [1, 2, 3])
    
    def test_func_not_callable_raises_error(self):
        """Test that non-callable func raises ValueError."""
        with pytest.raises(ValueError, match="func parameter must be callable"):
            optimize(123, [1, 2, 3])
    
    def test_func_string_raises_error(self):
        """Test that string func raises ValueError."""
        with pytest.raises(ValueError, match="func parameter must be callable"):
            optimize("not_a_function", [1, 2, 3])
    
    def test_func_list_raises_error(self):
        """Test that list func raises ValueError."""
        with pytest.raises(ValueError, match="func parameter must be callable"):
            optimize([1, 2, 3], [1, 2, 3])


class TestDataValidation:
    """Tests for data parameter validation."""
    
    def test_data_none_raises_error(self):
        """Test that None data raises ValueError."""
        with pytest.raises(ValueError, match="data parameter cannot be None"):
            optimize(simple_function, None)
    
    def test_data_not_iterable_raises_error(self):
        """Test that non-iterable data raises ValueError."""
        with pytest.raises(ValueError, match="data parameter must be iterable"):
            optimize(simple_function, 123)
    
    def test_data_string_is_valid(self):
        """Test that string data is accepted (strings are iterable)."""
        # Strings are iterable, so this should work
        result = optimize(simple_function, "abc")
        assert result is not None
        assert result.n_jobs >= 1


class TestSampleSizeValidation:
    """Tests for sample_size parameter validation."""
    
    def test_sample_size_negative_raises_error(self):
        """Test that negative sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size must be positive"):
            optimize(simple_function, [1, 2, 3], sample_size=-1)
    
    def test_sample_size_zero_raises_error(self):
        """Test that zero sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size must be positive"):
            optimize(simple_function, [1, 2, 3], sample_size=0)
    
    def test_sample_size_too_large_raises_error(self):
        """Test that unreasonably large sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size is unreasonably large"):
            optimize(simple_function, [1, 2, 3], sample_size=100000)
    
    def test_sample_size_not_integer_raises_error(self):
        """Test that non-integer sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size must be an integer"):
            optimize(simple_function, [1, 2, 3], sample_size=5.5)
    
    def test_sample_size_string_raises_error(self):
        """Test that string sample_size raises ValueError."""
        with pytest.raises(ValueError, match="sample_size must be an integer"):
            optimize(simple_function, [1, 2, 3], sample_size="5")
    
    def test_sample_size_valid_edge_cases(self):
        """Test that valid edge case sample_sizes work."""
        # Minimum valid: 1
        result = optimize(simple_function, [1, 2, 3], sample_size=1)
        assert result is not None
        
        # Maximum valid: 10000
        result = optimize(simple_function, range(10000), sample_size=10000)
        assert result is not None
        
        # Typical valid: 5 (default)
        result = optimize(simple_function, [1, 2, 3], sample_size=5)
        assert result is not None


class TestTargetChunkDurationValidation:
    """Tests for target_chunk_duration parameter validation."""
    
    def test_target_chunk_duration_negative_raises_error(self):
        """Test that negative target_chunk_duration raises ValueError."""
        with pytest.raises(ValueError, match="target_chunk_duration must be positive"):
            optimize(simple_function, [1, 2, 3], target_chunk_duration=-0.1)
    
    def test_target_chunk_duration_zero_raises_error(self):
        """Test that zero target_chunk_duration raises ValueError."""
        with pytest.raises(ValueError, match="target_chunk_duration must be positive"):
            optimize(simple_function, [1, 2, 3], target_chunk_duration=0)
    
    def test_target_chunk_duration_too_large_raises_error(self):
        """Test that unreasonably large target_chunk_duration raises ValueError."""
        with pytest.raises(ValueError, match="target_chunk_duration is unreasonably large"):
            optimize(simple_function, [1, 2, 3], target_chunk_duration=10000)
    
    def test_target_chunk_duration_not_number_raises_error(self):
        """Test that non-numeric target_chunk_duration raises ValueError."""
        with pytest.raises(ValueError, match="target_chunk_duration must be a number"):
            optimize(simple_function, [1, 2, 3], target_chunk_duration="0.2")
    
    def test_target_chunk_duration_valid_edge_cases(self):
        """Test that valid edge case target_chunk_durations work."""
        # Very small valid
        result = optimize(simple_function, [1, 2, 3], target_chunk_duration=0.001)
        assert result is not None
        
        # Maximum valid: 3600
        result = optimize(simple_function, [1, 2, 3], target_chunk_duration=3600)
        assert result is not None
        
        # Typical valid: 0.2 (default)
        result = optimize(simple_function, [1, 2, 3], target_chunk_duration=0.2)
        assert result is not None
        
        # Integer valid
        result = optimize(simple_function, [1, 2, 3], target_chunk_duration=1)
        assert result is not None


class TestBooleanParametersValidation:
    """Tests for boolean parameter validation."""
    
    def test_verbose_not_boolean_raises_error(self):
        """Test that non-boolean verbose raises ValueError."""
        with pytest.raises(ValueError, match="verbose must be a boolean"):
            optimize(simple_function, [1, 2, 3], verbose=1)
    
    def test_use_spawn_benchmark_not_boolean_raises_error(self):
        """Test that non-boolean use_spawn_benchmark raises ValueError."""
        with pytest.raises(ValueError, match="use_spawn_benchmark must be a boolean"):
            optimize(simple_function, [1, 2, 3], use_spawn_benchmark="true")
    
    def test_use_chunking_benchmark_not_boolean_raises_error(self):
        """Test that non-boolean use_chunking_benchmark raises ValueError."""
        with pytest.raises(ValueError, match="use_chunking_benchmark must be a boolean"):
            optimize(simple_function, [1, 2, 3], use_chunking_benchmark=0)
    
    def test_profile_not_boolean_raises_error(self):
        """Test that non-boolean profile raises ValueError."""
        with pytest.raises(ValueError, match="profile must be a boolean"):
            optimize(simple_function, [1, 2, 3], profile="false")
    
    def test_valid_boolean_combinations(self):
        """Test that all valid boolean combinations work."""
        # All False
        result = optimize(
            simple_function, [1, 2, 3],
            verbose=False,
            use_spawn_benchmark=False,
            use_chunking_benchmark=False,
            profile=False
        )
        assert result is not None
        
        # All True
        result = optimize(
            simple_function, [1, 2, 3],
            verbose=True,
            use_spawn_benchmark=True,
            use_chunking_benchmark=True,
            profile=True
        )
        assert result is not None


class TestRealWorldEdgeCases:
    """Tests for real-world edge cases that could occur."""
    
    def test_empty_list_is_valid(self):
        """Test that empty list is handled gracefully (not a validation error)."""
        # Empty data is valid input, should be handled by the optimizer logic
        result = optimize(simple_function, [])
        assert result is not None
        assert result.n_jobs == 1  # Should fall back to serial
    
    def test_very_small_data_is_valid(self):
        """Test that very small datasets work."""
        result = optimize(simple_function, [1])
        assert result is not None
    
    def test_generator_is_valid(self):
        """Test that generators are valid data."""
        def gen():
            yield 1
            yield 2
            yield 3
        
        result = optimize(simple_function, gen())
        assert result is not None
    
    def test_range_is_valid(self):
        """Test that range objects are valid data."""
        result = optimize(simple_function, range(100))
        assert result is not None
    
    def test_lambda_function_is_valid(self):
        """Test that lambda functions are valid (even if not picklable)."""
        # Lambda should pass validation but may fail picklability check
        result = optimize(lambda x: x * 2, [1, 2, 3])
        assert result is not None
        # Lambda won't be picklable, so should return n_jobs=1
        assert result.n_jobs == 1


class TestCombinedInvalidParameters:
    """Tests for multiple invalid parameters."""
    
    def test_multiple_invalid_parameters_reports_first_error(self):
        """Test that when multiple parameters are invalid, first error is reported."""
        # func and data both invalid - should report func error first
        with pytest.raises(ValueError, match="func parameter"):
            optimize(None, None, sample_size=-1)


class TestValidationDoesNotAffectExistingBehavior:
    """Tests to ensure validation doesn't break existing functionality."""
    
    def test_default_parameters_work(self):
        """Test that default parameters pass validation."""
        result = optimize(simple_function, [1, 2, 3])
        assert result is not None
    
    def test_typical_use_case_works(self):
        """Test that typical use case passes validation."""
        def compute_expensive(x):
            result = 0
            for i in range(1000):
                result += x ** 2
            return result
        
        result = optimize(
            compute_expensive,
            range(100),
            sample_size=5,
            target_chunk_duration=0.2,
            verbose=False
        )
        assert result is not None
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
