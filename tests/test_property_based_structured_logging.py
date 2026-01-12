"""
Property-based tests for structured logging module.

These tests use the Hypothesis library to automatically generate and test thousands
of edge cases for the structured_logging module, including StructuredLogger creation,
configuration, enable/disable functionality, logging methods, JSON formatting, and
thread safety.
"""

import json
import os
import sys
import tempfile
import time
from io import StringIO
from threading import Thread, Barrier
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, settings, assume

from amorsize.structured_logging import (
    StructuredLogger,
    JSONFormatter,
    LogLevel,
    get_logger,
    configure_logging,
)


# ============================================================================
# Custom Strategies
# ============================================================================

@st.composite
def valid_log_level(draw):
    """Generate valid log level strings."""
    return draw(st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR"]))


@st.composite
def valid_output_destination(draw):
    """Generate valid output destinations."""
    return draw(st.sampled_from(["stderr", "stdout"]))


@st.composite
def valid_logger_name(draw):
    """Generate valid logger names."""
    return draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        categories=('Lu', 'Ll', 'Nd'),
        include_characters='_-.'
    )))


@st.composite
def valid_function_name(draw):
    """Generate valid function names (Python identifiers)."""
    # Start with letter or underscore
    first = draw(st.sampled_from('abcdefghijklmnopqrstuvwxyz_'))
    # Rest can be letters, digits, or underscores
    rest = draw(st.text(
        alphabet=st.characters(categories=('Ll', 'Nd'), include_characters='_'),
        max_size=30
    ))
    return first + rest


@st.composite
def valid_data_size(draw):
    """Generate valid data sizes (positive integers)."""
    return draw(st.integers(min_value=1, max_value=1000000))


@st.composite
def valid_n_jobs(draw):
    """Generate valid n_jobs values."""
    return draw(st.integers(min_value=1, max_value=128))


@st.composite
def valid_chunksize(draw):
    """Generate valid chunksize values."""
    return draw(st.integers(min_value=1, max_value=10000))


@st.composite
def valid_speedup(draw):
    """Generate valid speedup values."""
    return draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_executor_type(draw):
    """Generate valid executor types."""
    return draw(st.sampled_from(["process", "thread", "serial"]))


@st.composite
def valid_sample_count(draw):
    """Generate valid sample counts."""
    return draw(st.integers(min_value=1, max_value=100))


@st.composite
def valid_avg_time(draw):
    """Generate valid average execution times."""
    return draw(st.floats(min_value=0.0001, max_value=10.0, allow_nan=False, allow_infinity=False))


@st.composite
def valid_workload_type(draw):
    """Generate valid workload types."""
    return draw(st.sampled_from(["cpu_bound", "io_bound", "mixed", "unknown"]))


@st.composite
def valid_physical_cores(draw):
    """Generate valid physical core counts."""
    return draw(st.integers(min_value=1, max_value=128))


@st.composite
def valid_logical_cores(draw):
    """Generate valid logical core counts."""
    physical = draw(valid_physical_cores())
    # Logical cores must be >= physical cores
    return draw(st.integers(min_value=physical, max_value=physical * 2))


@st.composite
def valid_memory_bytes(draw):
    """Generate valid memory byte values."""
    # 1GB to 1TB
    return draw(st.integers(min_value=1024**3, max_value=1024**4))


@st.composite
def valid_start_method(draw):
    """Generate valid multiprocessing start methods."""
    return draw(st.sampled_from(["fork", "spawn", "forkserver"]))


@st.composite
def valid_reason_string(draw):
    """Generate valid reason strings."""
    return draw(st.text(min_size=1, max_size=200, alphabet=st.characters(
        exclude_categories=('Cc', 'Cs'),  # Exclude control characters
        exclude_characters='\x00\n\r\t'
    )))


@st.composite
def valid_constraint_type(draw):
    """Generate valid constraint types."""
    return draw(st.sampled_from([
        "memory", "cpu", "picklability", "workload_size", "execution_time"
    ]))


@st.composite
def valid_error_type(draw):
    """Generate valid error types."""
    return draw(st.sampled_from([
        "ValueError", "TypeError", "RuntimeError", "ImportError",
        "AttributeError", "PicklingError", "MemoryError"
    ]))


@st.composite
def valid_metrics_dict(draw):
    """Generate valid metrics dictionaries."""
    num_metrics = draw(st.integers(min_value=1, max_value=10))
    metrics = {}
    for _ in range(num_metrics):
        key = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
            categories=('Ll', 'Nd'),
            include_characters='_'
        )))
        value = draw(st.one_of(
            st.integers(min_value=0, max_value=1000000),
            st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.text(max_size=50)
        ))
        metrics[key] = value
    return metrics


# ============================================================================
# Property-Based Test Classes
# ============================================================================


class TestStructuredLoggerInvariants:
    """Test StructuredLogger initialization and basic invariants."""

    @given(valid_logger_name(), valid_log_level())
    @settings(max_examples=50)
    def test_logger_initialization(self, name, level):
        """Property: Logger can be initialized with any valid name and level."""
        logger = StructuredLogger(name=name, level=level)
        assert logger is not None
        assert logger.logger.name == name
        assert not logger.enabled  # Should be disabled by default

    @given(valid_logger_name())
    @settings(max_examples=50)
    def test_logger_default_level(self, name):
        """Property: Default log level is INFO."""
        logger = StructuredLogger(name=name)
        # Python logging.INFO = 20
        assert logger.logger.level == 20

    @given(valid_logger_name())
    @settings(max_examples=50)
    def test_logger_disabled_by_default(self, name):
        """Property: Logger is always disabled by default."""
        logger = StructuredLogger(name=name)
        assert not logger.enabled


class TestLoggerEnableDisable:
    """Test enable/disable functionality."""

    @given(valid_output_destination(), valid_log_level())
    @settings(max_examples=50)
    def test_enable_sets_enabled_flag(self, output, level):
        """Property: Enabling logger sets enabled flag to True."""
        logger = StructuredLogger()
        logger.enable(output=output, level=level)
        assert logger.enabled
        logger.disable()

    @given(valid_output_destination(), valid_log_level())
    @settings(max_examples=50)
    def test_disable_clears_enabled_flag(self, output, level):
        """Property: Disabling logger sets enabled flag to False."""
        logger = StructuredLogger()
        logger.enable(output=output, level=level)
        logger.disable()
        assert not logger.enabled

    @given(valid_output_destination(), valid_log_level(), st.booleans())
    @settings(max_examples=50)
    def test_enable_with_format_json(self, output, level, format_json):
        """Property: Logger can be enabled with any format_json value."""
        logger = StructuredLogger()
        logger.enable(output=output, level=level, format_json=format_json)
        assert logger.enabled
        assert len(logger.logger.handlers) > 0
        logger.disable()

    def test_enable_disable_clears_handlers(self):
        """Property: Disabling logger clears all handlers."""
        logger = StructuredLogger()
        logger.enable(output="stderr", level="INFO")
        assert len(logger.logger.handlers) > 0
        logger.disable()
        assert len(logger.logger.handlers) == 0


class TestLogLevelValidation:
    """Test log level validation and filtering."""

    @given(valid_log_level())
    @settings(max_examples=50)
    def test_set_level_accepts_valid_levels(self, level):
        """Property: _set_level accepts all valid log levels."""
        logger = StructuredLogger()
        logger._set_level(level)
        # Should not raise exception

    @given(valid_output_destination())
    @settings(max_examples=50)
    def test_enable_respects_log_level(self, output):
        """Property: Enabling at WARNING level doesn't log INFO messages."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output=output, level="WARNING")
            logger.log_optimization_start("test", 100)
            output_text = sys.stderr.getvalue()
            
            # INFO level messages should not be logged at WARNING level
            assert output_text == ""
        finally:
            sys.stderr = old_stderr
            logger.disable()


class TestLoggingMethods:
    """Test individual logging methods."""

    @given(valid_function_name(), valid_data_size())
    @settings(max_examples=50)
    def test_log_optimization_start_structure(self, func_name, data_size):
        """Property: log_optimization_start creates valid JSON with correct fields."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            logger.log_optimization_start(func_name=func_name, data_size=data_size)
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["event"] == "optimization_start"
                assert data["function"] == func_name
                assert data["data_size"] == data_size
                assert "timestamp" in data
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(
        valid_n_jobs(),
        valid_chunksize(),
        valid_speedup(),
        valid_executor_type(),
        st.booleans()
    )
    @settings(max_examples=50)
    def test_log_optimization_complete_structure(self, n_jobs, chunksize, speedup, executor_type, cache_hit):
        """Property: log_optimization_complete creates valid JSON with correct fields."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            logger.log_optimization_complete(
                n_jobs=n_jobs,
                chunksize=chunksize,
                speedup=speedup,
                executor_type=executor_type,
                cache_hit=cache_hit
            )
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["event"] == "optimization_complete"
                assert data["n_jobs"] == n_jobs
                assert data["chunksize"] == chunksize
                assert data["estimated_speedup"] == speedup
                assert data["executor_type"] == executor_type
                assert data["cache_hit"] == cache_hit
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(
        valid_sample_count(),
        valid_avg_time(),
        st.booleans(),
        valid_workload_type()
    )
    @settings(max_examples=50)
    def test_log_sampling_complete_structure(self, sample_count, avg_time, is_picklable, workload_type):
        """Property: log_sampling_complete creates valid JSON with correct fields."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            logger.log_sampling_complete(
                sample_count=sample_count,
                avg_time=avg_time,
                is_picklable=is_picklable,
                workload_type=workload_type
            )
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["event"] == "sampling_complete"
                assert data["sample_count"] == sample_count
                assert data["avg_execution_time_seconds"] == avg_time
                assert data["is_picklable"] == is_picklable
                assert data["workload_type"] == workload_type
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(
        valid_physical_cores(),
        valid_memory_bytes(),
        valid_start_method()
    )
    @settings(max_examples=50)
    def test_log_system_info_structure(self, physical_cores, memory_bytes, start_method):
        """Property: log_system_info creates valid JSON with correct fields."""
        logger = StructuredLogger()
        logical_cores = physical_cores * 2  # Ensure logical >= physical
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="DEBUG")
            logger.log_system_info(
                physical_cores=physical_cores,
                logical_cores=logical_cores,
                available_memory_bytes=memory_bytes,
                start_method=start_method
            )
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["event"] == "system_info"
                assert data["physical_cores"] == physical_cores
                assert data["logical_cores"] == logical_cores
                assert data["available_memory_bytes"] == memory_bytes
                assert data["multiprocessing_start_method"] == start_method
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(valid_reason_string(), valid_metrics_dict())
    @settings(max_examples=50)
    def test_log_rejection_structure(self, reason, details):
        """Property: log_rejection creates valid JSON with correct fields."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="WARNING")
            logger.log_rejection(reason=reason, details=details)
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["event"] == "parallelization_rejected"
                assert data["reason"] == reason
                # Check that details are included
                for key in details:
                    assert key in data
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(valid_constraint_type(), valid_reason_string(), valid_metrics_dict())
    @settings(max_examples=50)
    def test_log_constraint_structure(self, constraint_type, message, details):
        """Property: log_constraint creates valid JSON with correct fields."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="WARNING")
            logger.log_constraint(
                constraint_type=constraint_type,
                message=message,
                details=details
            )
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["event"] == "optimization_constraint"
                assert data["constraint_type"] == constraint_type
                assert data["message"] == message
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(valid_error_type(), valid_reason_string(), valid_metrics_dict())
    @settings(max_examples=50)
    def test_log_error_structure(self, error_type, message, details):
        """Property: log_error creates valid JSON with correct fields."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="ERROR")
            logger.log_error(
                error_type=error_type,
                message=message,
                details=details
            )
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["event"] == "error"
                assert data["error_type"] == error_type
                assert data["message"] == message
        finally:
            sys.stderr = old_stderr
            logger.disable()


class TestJSONFormatterProperties:
    """Test JSON formatter properties."""

    @given(valid_function_name(), valid_data_size())
    @settings(max_examples=50)
    def test_json_formatter_produces_valid_json(self, func_name, data_size):
        """Property: JSON formatter always produces valid JSON."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", format_json=True, level="INFO")
            logger.log_optimization_start(func_name=func_name, data_size=data_size)
            output = sys.stderr.getvalue()
            
            if output:
                # Should be valid JSON
                data = json.loads(output.strip().split('\n')[0])
                assert isinstance(data, dict)
                assert "timestamp" in data
                assert "level" in data
                assert "event" in data
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(valid_function_name())
    @settings(max_examples=50)
    def test_json_formatter_includes_logger_name(self, func_name):
        """Property: JSON formatter includes logger name."""
        logger = StructuredLogger(name="test_logger")
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", format_json=True, level="INFO")
            logger.log_optimization_start(func_name=func_name, data_size=100)
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["logger"] == "test_logger"
        finally:
            sys.stderr = old_stderr
            logger.disable()


class TestLoggingDisabledBehavior:
    """Test that logging disabled produces no output."""

    @given(valid_function_name(), valid_data_size())
    @settings(max_examples=50)
    def test_disabled_logging_produces_no_output(self, func_name, data_size):
        """Property: Disabled logging produces no output."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            # Logger is disabled by default
            logger.log_optimization_start(func_name=func_name, data_size=data_size)
            output = sys.stderr.getvalue()
            
            # Should have no output
            assert output == ""
        finally:
            sys.stderr = old_stderr

    @given(
        valid_n_jobs(),
        valid_chunksize(),
        valid_speedup(),
        valid_executor_type()
    )
    @settings(max_examples=50)
    def test_all_methods_respect_disabled_flag(self, n_jobs, chunksize, speedup, executor_type):
        """Property: All logging methods respect disabled flag."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            # Call various logging methods while disabled
            logger.log_optimization_start("test", 100)
            logger.log_optimization_complete(n_jobs, chunksize, speedup, executor_type, False)
            logger.log_sampling_complete(5, 0.01, True, "cpu_bound")
            logger.log_rejection("reason", {})
            logger.log_error("error", "message", {})
            
            output = sys.stderr.getvalue()
            
            # Should have no output
            assert output == ""
        finally:
            sys.stderr = old_stderr


class TestFileOutputProperties:
    """Test file output properties."""

    @given(valid_function_name(), valid_data_size())
    @settings(max_examples=30)
    def test_file_output_creates_file(self, func_name, data_size):
        """Property: File output creates file with content."""
        logger = StructuredLogger()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            logger.enable(output=log_file, level="INFO")
            logger.log_optimization_start(func_name=func_name, data_size=data_size)
            logger.disable()
            
            # File should exist
            assert os.path.exists(log_file)
            
            # File should have content
            with open(log_file, 'r') as f:
                content = f.read()
            assert content != ""
            assert "optimization_start" in content
        finally:
            if os.path.exists(log_file):
                os.remove(log_file)

    @given(valid_n_jobs(), valid_chunksize())
    @settings(max_examples=30)
    def test_file_output_preserves_json_structure(self, n_jobs, chunksize):
        """Property: File output contains valid JSON."""
        logger = StructuredLogger()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            logger.enable(output=log_file, format_json=True, level="INFO")
            logger.log_optimization_complete(
                n_jobs=n_jobs,
                chunksize=chunksize,
                speedup=2.5,
                executor_type="process",
                cache_hit=False
            )
            logger.disable()
            
            # Read and parse JSON
            with open(log_file, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            for line in lines:
                data = json.loads(line)
                assert isinstance(data, dict)
                assert "event" in data
        finally:
            if os.path.exists(log_file):
                os.remove(log_file)


class TestThreadSafetyProperties:
    """Test thread safety of logging operations."""

    @given(st.integers(min_value=2, max_value=5))
    @settings(max_examples=20, deadline=5000)
    def test_concurrent_logging_safe(self, num_threads):
        """Property: Concurrent logging from multiple threads is safe."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        barrier = Barrier(num_threads)
        
        def log_from_thread(thread_id):
            barrier.wait()  # Synchronize all threads
            logger.log_optimization_start(f"func_{thread_id}", thread_id * 100)
        
        try:
            logger.enable(output="stderr", level="INFO")
            
            threads = []
            for i in range(num_threads):
                t = Thread(target=log_from_thread, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            output = sys.stderr.getvalue()
            
            # Should have output from all threads
            # Count the number of log entries
            if output:
                lines = [line for line in output.strip().split('\n') if line]
                assert len(lines) == num_threads
        finally:
            sys.stderr = old_stderr
            logger.disable()


class TestConfigureLoggingProperties:
    """Test configure_logging API properties."""

    @given(valid_output_destination(), valid_log_level())
    @settings(max_examples=50)
    def test_configure_logging_enables_logger(self, output, level):
        """Property: configure_logging(enabled=True) enables the logger."""
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            configure_logging(enabled=True, output=output, level=level)
            logger = get_logger()
            assert logger.enabled
        finally:
            sys.stderr = old_stderr
            configure_logging(enabled=False)

    def test_configure_logging_disables_logger(self):
        """Property: configure_logging(enabled=False) disables the logger."""
        configure_logging(enabled=False)
        logger = get_logger()
        assert not logger.enabled

    @given(valid_log_level())
    @settings(max_examples=50)
    def test_configure_logging_sets_level(self, level):
        """Property: configure_logging sets the log level."""
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            configure_logging(enabled=True, output="stderr", level=level)
            logger = get_logger()
            assert logger.enabled
            # Verify level is set correctly
            level_map = {
                "DEBUG": 10,
                "INFO": 20,
                "WARNING": 30,
                "ERROR": 40
            }
            assert logger.logger.level == level_map[level]
        finally:
            sys.stderr = old_stderr
            configure_logging(enabled=False)


class TestEdgeCasesProperties:
    """Test edge cases and boundary conditions."""

    @given(st.text(max_size=0))
    @settings(max_examples=30)
    def test_empty_function_name(self, empty_str):
        """Property: Empty function name defaults to 'unknown'."""
        assume(empty_str == "")
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            logger.log_optimization_start(func_name=empty_str, data_size=100)
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                # Empty string or None defaults to "unknown"
                assert data["function"] == "unknown"
        finally:
            sys.stderr = old_stderr
            logger.disable()

    def test_zero_data_size(self):
        """Property: Zero data size is handled gracefully."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            logger.log_optimization_start(func_name="test", data_size=0)
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["data_size"] == 0
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(st.floats(min_value=0.0, max_value=0.0))
    @settings(max_examples=30)
    def test_zero_speedup(self, zero_speedup):
        """Property: Zero speedup is handled gracefully."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            logger.log_optimization_complete(
                n_jobs=1,
                chunksize=1,
                speedup=zero_speedup,
                executor_type="serial",
                cache_hit=False
            )
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["estimated_speedup"] == zero_speedup
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(st.dictionaries(st.text(max_size=50), st.integers()))
    @settings(max_examples=30)
    def test_large_details_dict(self, large_dict):
        """Property: Large details dictionaries are handled gracefully."""
        assume(len(large_dict) <= 100)  # Reasonable limit
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="WARNING")
            logger.log_rejection("test_reason", details=large_dict)
            output = sys.stderr.getvalue()
            
            if output:
                data = json.loads(output.strip().split('\n')[0])
                assert data["reason"] == "test_reason"
        finally:
            sys.stderr = old_stderr
            logger.disable()


class TestIntegrationProperties:
    """Test integration properties with full workflow."""

    @given(
        valid_function_name(),
        valid_data_size(),
        valid_n_jobs(),
        valid_chunksize(),
        valid_speedup()
    )
    @settings(max_examples=30)
    def test_full_logging_workflow(self, func_name, data_size, n_jobs, chunksize, speedup):
        """Property: Full logging workflow produces sequential events."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            
            # Simulate full optimization workflow
            logger.log_optimization_start(func_name=func_name, data_size=data_size)
            logger.log_sampling_complete(5, 0.01, True, "cpu_bound")
            logger.log_optimization_complete(
                n_jobs=n_jobs,
                chunksize=chunksize,
                speedup=speedup,
                executor_type="process",
                cache_hit=False
            )
            
            output = sys.stderr.getvalue()
            
            # Should have all three events
            lines = [line for line in output.strip().split('\n') if line]
            assert len(lines) >= 3
            
            # Parse and verify events
            events = [json.loads(line)["event"] for line in lines]
            assert "optimization_start" in events
            assert "sampling_complete" in events
            assert "optimization_complete" in events
        finally:
            sys.stderr = old_stderr
            logger.disable()

    @given(valid_function_name(), valid_reason_string())
    @settings(max_examples=30)
    def test_rejection_workflow(self, func_name, reason):
        """Property: Rejection workflow produces appropriate events."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            
            # Simulate rejection workflow
            logger.log_optimization_start(func_name=func_name, data_size=100)
            logger.log_rejection(reason=reason, details={"detail": "value"})
            
            output = sys.stderr.getvalue()
            
            # Should have both events
            lines = [line for line in output.strip().split('\n') if line]
            assert len(lines) >= 2
            
            # Parse and verify events
            events = [json.loads(line)["event"] for line in lines]
            assert "optimization_start" in events
            assert "parallelization_rejected" in events
        finally:
            sys.stderr = old_stderr
            logger.disable()
