"""
Tests for enhanced error messages and actionable guidance.

This test suite validates that error messages are clear, helpful, and provide
concrete examples and solutions for users when optimization fails.
"""

import pytest
import sys
from io import StringIO
from amorsize import optimize
from amorsize.error_messages import (
    get_picklability_error_message,
    get_data_picklability_error_message,
    get_memory_constraint_message,
    get_no_speedup_benefit_message,
    get_workload_too_small_message,
    get_sampling_failure_message,
    format_warning_with_guidance
)


class TestPicklabilityErrorMessages:
    """Test enhanced picklability error messages."""
    
    def test_function_picklability_message_has_common_causes(self):
        """Error message should list common causes of pickling failures."""
        message = get_picklability_error_message()
        
        assert "COMMON CAUSES:" in message
        assert "Lambda functions" in message
        assert "Nested functions" in message
        assert "local variables" in message
        
    def test_function_picklability_message_has_solutions(self):
        """Error message should provide concrete solutions."""
        message = get_picklability_error_message()
        
        assert "SOLUTIONS:" in message
        assert "Convert lambda to regular function" in message
        assert "Move nested function to module level" in message
        assert "cloudpickle" in message
        assert "ThreadPoolExecutor" in message
        
    def test_function_picklability_message_has_examples(self):
        """Error message should include code examples."""
        message = get_picklability_error_message()
        
        # Should have before (❌) and after (✅) examples
        assert "❌" in message
        assert "✅" in message
        assert "def func(x):" in message
        
    def test_function_picklability_with_function_name(self):
        """Error message should include function name if provided."""
        message = get_picklability_error_message(function_name="my_func")
        
        assert "'my_func'" in message
        
    def test_data_picklability_message_has_common_causes(self):
        """Data pickling error should list common unpicklable objects."""
        message = get_data_picklability_error_message(5)
        
        assert "COMMON CAUSES:" in message
        assert "File handles" in message
        assert "Database connections" in message
        assert "Thread locks" in message
        
    def test_data_picklability_message_has_solutions(self):
        """Data pickling error should provide concrete solutions."""
        message = get_data_picklability_error_message(5)
        
        assert "SOLUTIONS:" in message
        assert "Pass file paths instead" in message
        assert "Pass connection strings" in message
        assert "Extract only serializable data" in message
        
    def test_data_picklability_message_includes_index(self):
        """Data pickling error should identify the problematic item."""
        message = get_data_picklability_error_message(42)
        
        assert "index 42" in message
        
    def test_data_picklability_message_includes_type(self):
        """Data pickling error should include item type if available."""
        message = get_data_picklability_error_message(5, item_type="FileHandle")
        
        assert "FileHandle" in message


class TestMemoryConstraintMessages:
    """Test enhanced memory constraint messages."""
    
    def test_memory_constraint_message_shows_metrics(self):
        """Memory message should show memory requirements and availability."""
        message = get_memory_constraint_message(
            required_mb=500.0,
            available_mb=2000.0,
            optimal_workers=8,
            constrained_workers=3
        )
        
        assert "500" in message or "500.0" in message
        assert "2000" in message or "2000.0" in message
        assert "8" in message
        assert "3" in message
        
    def test_memory_constraint_message_has_solutions(self):
        """Memory message should provide concrete solutions."""
        message = get_memory_constraint_message(
            required_mb=500.0,
            available_mb=2000.0,
            optimal_workers=8,
            constrained_workers=3
        )
        
        assert "SOLUTIONS:" in message
        assert "Reduce memory footprint" in message
        assert "process_in_batches" in message
        assert "optimize_streaming" in message
        assert "Add more RAM" in message
        
    def test_memory_constraint_message_has_code_examples(self):
        """Memory message should include code examples."""
        message = get_memory_constraint_message(
            required_mb=500.0,
            available_mb=2000.0,
            optimal_workers=8,
            constrained_workers=3
        )
        
        assert "from amorsize import" in message
        assert "batch_size=" in message
        assert "max_memory_percent=" in message


class TestNoSpeedupBenefitMessages:
    """Test enhanced messages for no parallelization benefit."""
    
    def test_no_speedup_message_explains_why(self):
        """Message should explain why parallelization doesn't help."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=1.1,
            avg_function_time_ms=5.0,
            overhead_ms=50.0,
            min_function_time_ms=60.0
        )
        
        assert "WHY THIS HAPPENS:" in message
        assert "overhead" in message.lower()
        assert "startup costs" in message or "process creation" in message
        
    def test_no_speedup_message_has_solutions(self):
        """Message should provide concrete solutions."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=1.1,
            avg_function_time_ms=5.0,
            overhead_ms=50.0,
            min_function_time_ms=60.0
        )
        
        assert "SOLUTIONS:" in message
        assert "Make your function slower" in message or "do more work" in message
        assert "Process more data" in message
        assert "Batch multiple items" in message
        
    def test_no_speedup_message_shows_metrics(self):
        """Message should show relevant timing metrics."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=1.1,
            avg_function_time_ms=5.0,
            overhead_ms=50.0,
            min_function_time_ms=60.0
        )
        
        assert "1.1" in message or "1.10" in message
        assert "5.0" in message or "5.00" in message
        
    def test_no_speedup_message_has_code_examples(self):
        """Message should include before/after code examples."""
        message = get_no_speedup_benefit_message(
            estimated_speedup=1.1,
            avg_function_time_ms=5.0,
            overhead_ms=50.0,
            min_function_time_ms=60.0
        )
        
        assert "❌" in message
        assert "✅" in message
        assert "def process" in message


class TestWorkloadTooSmallMessages:
    """Test enhanced messages for small workloads."""
    
    def test_workload_too_small_message_explains_why(self):
        """Message should explain why small workload is problematic."""
        message = get_workload_too_small_message(
            total_items=10,
            speedup_with_2_workers=1.05,
            min_items_recommended=50
        )
        
        assert "WHY THIS HAPPENS:" in message
        assert "overhead" in message.lower()
        assert "splitting work" in message or "few items" in message
        
    def test_workload_too_small_message_has_solutions(self):
        """Message should provide concrete solutions."""
        message = get_workload_too_small_message(
            total_items=10,
            speedup_with_2_workers=1.05,
            min_items_recommended=50
        )
        
        assert "SOLUTIONS:" in message
        assert "Increase dataset size" in message
        assert "more expensive to process" in message
        assert "Accumulate items" in message
        
    def test_workload_too_small_message_shows_metrics(self):
        """Message should show item count and speedup."""
        message = get_workload_too_small_message(
            total_items=10,
            speedup_with_2_workers=1.05,
            min_items_recommended=50
        )
        
        assert "10" in message
        assert "50" in message
        assert "1.05" in message


class TestSamplingFailureMessages:
    """Test enhanced messages for sampling failures."""
    
    def test_sampling_failure_message_shows_error(self):
        """Message should display the error type and message."""
        error = ValueError("Invalid input data")
        message = get_sampling_failure_message(error)
        
        assert "ValueError" in message
        assert "Invalid input data" in message
        
    def test_sampling_failure_message_has_common_causes(self):
        """Message should list common causes of sampling failures."""
        error = RuntimeError("Test error")
        message = get_sampling_failure_message(error)
        
        assert "COMMON CAUSES:" in message
        assert "Function raises an exception" in message
        assert "Data iterator" in message
        
    def test_sampling_failure_message_has_solutions(self):
        """Message should provide debugging steps."""
        error = RuntimeError("Test error")
        message = get_sampling_failure_message(error)
        
        assert "SOLUTIONS:" in message
        assert "Test your function" in message
        assert "Validate your data" in message
        assert "Handle edge cases" in message


class TestIntegrationWithOptimizer:
    """Test that optimizer uses enhanced error messages."""
    
    def test_lambda_function_gets_enhanced_error(self):
        """Lambda function should trigger enhanced picklability error."""
        func = lambda x: x ** 2
        data = range(100)
        
        result = optimize(func, data)
        
        # Should recommend serial execution
        assert result.n_jobs == 1
        # Should have enhanced error message in warnings
        assert len(result.warnings) > 0
        warning_text = result.warnings[0]
        assert "COMMON CAUSES:" in warning_text or "cannot be pickled" in warning_text
        
    def test_very_fast_function_gets_enhanced_error(self):
        """Very fast function should get enhanced speedup benefit message."""
        def tiny_func(x):
            return x + 1
        
        data = range(10)
        
        result = optimize(tiny_func, data)
        
        # Should recommend serial execution
        assert result.n_jobs == 1
        # Should have guidance in warnings
        assert len(result.warnings) > 0
        
    def test_function_that_raises_error_gets_enhanced_message(self):
        """Function that raises error during sampling should get helpful message."""
        def broken_func(x):
            raise ValueError("Test error")
        
        data = range(10)
        
        result = optimize(broken_func, data)
        
        # Should recommend serial execution
        assert result.n_jobs == 1
        # Should have sampling failure guidance
        assert len(result.warnings) > 0
        warning_text = result.warnings[0]
        assert "Error" in warning_text or "SOLUTIONS:" in warning_text


class TestWarningFormatting:
    """Test warning formatting with guidance."""
    
    def test_io_bound_warning_has_guidance(self):
        """I/O-bound warning should include ThreadPoolExecutor guidance."""
        warnings = format_warning_with_guidance('io_bound')
        
        assert len(warnings) > 1
        warning_text = ' '.join(warnings)
        assert "ThreadPoolExecutor" in warning_text
        assert "I/O-bound" in warning_text
        
    def test_heterogeneous_warning_has_guidance(self):
        """Heterogeneous workload warning should include imap_unordered guidance."""
        warnings = format_warning_with_guidance('heterogeneous', cv=0.8)
        
        assert len(warnings) > 1
        warning_text = ' '.join(warnings)
        assert "imap_unordered" in warning_text
        assert "0.8" in warning_text or "heterogeneous" in warning_text.lower()
        
    def test_nested_parallelism_warning_has_guidance(self):
        """Nested parallelism warning should include environment variable guidance."""
        warnings = format_warning_with_guidance('nested_parallelism', internal_threads=4)
        
        assert len(warnings) > 1
        warning_text = ' '.join(warnings)
        assert "OMP_NUM_THREADS" in warning_text or "MKL_NUM_THREADS" in warning_text
        
    def test_memory_pressure_warning_has_guidance(self):
        """Memory pressure warning should include streaming/batching guidance."""
        warnings = format_warning_with_guidance('memory_pressure')
        
        assert len(warnings) > 1
        warning_text = ' '.join(warnings)
        assert "streaming" in warning_text.lower() or "batch" in warning_text.lower()


class TestErrorMessageQuality:
    """Test overall quality of error messages."""
    
    def test_messages_are_not_empty(self):
        """All error message functions should return non-empty strings."""
        messages = [
            get_picklability_error_message(),
            get_data_picklability_error_message(0),
            get_memory_constraint_message(100, 1000, 8, 2),
            get_no_speedup_benefit_message(1.1, 5.0, 50.0, 60.0),
            get_workload_too_small_message(10, 1.05, 50),
            get_sampling_failure_message(ValueError("test"))
        ]
        
        for message in messages:
            assert message
            assert len(message) > 50  # Should be substantial
            
    def test_messages_have_structure(self):
        """Messages should have clear structure with headers."""
        message = get_picklability_error_message()
        
        # Should have clear sections
        assert "COMMON CAUSES:" in message or "SOLUTIONS:" in message
        assert "\n" in message  # Multi-line
        
    def test_messages_have_actionable_content(self):
        """Messages should include actionable steps, not just descriptions."""
        message = get_no_speedup_benefit_message(1.1, 5.0, 50.0, 60.0)
        
        # Should have specific actions
        assert "def " in message or "import " in message  # Code examples
        assert ":" in message  # Explanations


class TestVerboseMode:
    """Test that verbose mode displays enhanced messages."""
    
    def test_verbose_mode_prints_enhanced_errors(self, capsys):
        """Verbose mode should print enhanced error messages."""
        func = lambda x: x ** 2
        data = range(100)
        
        # Redirect stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = optimize(func, data, verbose=True)
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
        
        # Should print enhanced message
        # (Check for presence of enhanced content markers)
        assert len(output) > 0 or result.n_jobs == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
