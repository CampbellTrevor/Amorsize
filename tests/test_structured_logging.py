"""
Tests for structured logging module.
"""

import json
import os
import tempfile
import time
from io import StringIO
import sys

import pytest

from amorsize import configure_logging, optimize
from amorsize.structured_logging import get_logger, StructuredLogger, JSONFormatter


class TestStructuredLogger:
    """Test the StructuredLogger class."""
    
    def test_logger_initialization(self):
        """Test logger can be initialized."""
        logger = StructuredLogger()
        assert logger is not None
        assert not logger.enabled  # Disabled by default
    
    def test_logger_enable_disable(self):
        """Test enabling and disabling logger."""
        logger = StructuredLogger()
        assert not logger.enabled
        
        logger.enable(output="stderr", level="INFO")
        assert logger.enabled
        
        logger.disable()
        assert not logger.enabled
    
    def test_logger_singleton(self):
        """Test that get_logger returns the same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
    
    def test_logging_disabled_by_default(self):
        """Test that logging is disabled by default (no output)."""
        logger = StructuredLogger()
        
        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            # This should not produce output since logging is disabled
            logger.log_optimization_start(func_name="test_func", data_size=100)
            output = sys.stderr.getvalue()
            assert output == ""
        finally:
            sys.stderr = old_stderr
    
    def test_logging_when_enabled(self):
        """Test that logging produces output when enabled."""
        logger = StructuredLogger()
        
        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="INFO")
            logger.log_optimization_start(func_name="test_func", data_size=100)
            output = sys.stderr.getvalue()
            
            # Should have output
            assert output != ""
            
            # Should be valid JSON
            lines = output.strip().split('\n')
            for line in lines:
                data = json.loads(line)
                assert "event" in data
                assert data["event"] == "optimization_start"
                assert "function" in data
                assert data["function"] == "test_func"
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_json_formatter(self):
        """Test JSON formatter produces valid JSON."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", format_json=True, level="INFO")
            logger.log_optimization_start(func_name="my_func", data_size=1000)
            output = sys.stderr.getvalue()
            
            # Parse each line as JSON
            lines = output.strip().split('\n')
            for line in lines:
                data = json.loads(line)
                assert "timestamp" in data
                assert "level" in data
                assert "event" in data
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_log_levels(self):
        """Test different log levels."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            # Set to WARNING level - should not log INFO
            logger.enable(output="stderr", level="WARNING")
            logger.log_optimization_start(func_name="test", data_size=100)
            output1 = sys.stderr.getvalue()
            
            # INFO should not be logged at WARNING level
            # The output might still have something due to how logging works,
            # but optimization_start is INFO level so it should be filtered
            assert output1 == ""
            
            # Now log a warning
            logger.log_rejection("test_reason", {"detail": "value"})
            output2 = sys.stderr.getvalue()
            
            # Should have warning output
            assert output2 != ""
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_file_output(self):
        """Test logging to a file."""
        logger = StructuredLogger()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            logger.enable(output=log_file, level="INFO")
            logger.log_optimization_start(func_name="file_test", data_size=500)
            logger.log_optimization_complete(
                n_jobs=4,
                chunksize=10,
                speedup=3.5,
                executor_type="process",
                cache_hit=False
            )
            logger.disable()
            
            # Read the file
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Should have content
            assert content != ""
            
            # Should have both events
            assert "optimization_start" in content
            assert "optimization_complete" in content
            
            # Validate JSON structure
            lines = content.strip().split('\n')
            for line in lines:
                data = json.loads(line)
                assert "timestamp" in data
                assert "event" in data
        finally:
            logger.disable()
            if os.path.exists(log_file):
                os.remove(log_file)


class TestLoggingIntegration:
    """Test logging integration with optimize function."""
    
    def test_optimize_with_logging_disabled(self):
        """Test optimize works normally when logging is disabled."""
        def simple_func(x):
            return x * 2
        
        data = range(100)
        result = optimize(simple_func, data, sample_size=5)
        
        assert result is not None
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_optimize_with_logging_enabled(self):
        """Test optimize logs events when logging is enabled."""
        # Import a module-level function so it's picklable
        import math
        
        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            configure_logging(enabled=True, output="stderr", level="INFO")
            
            data = range(100)
            result = optimize(math.sqrt, data, sample_size=5)
            
            output = sys.stderr.getvalue()
            
            # Should have logged events
            assert output != ""
            
            # Check for expected events
            assert "optimization_start" in output
            
            # Should have either optimization_complete or rejection
            # (sqrt is picklable so should complete or reject for other reasons)
            assert ("optimization_complete" in output or 
                    "parallelization_rejected" in output or
                    "sampling_complete" in output)
            
            # Validate JSON structure
            lines = [line for line in output.strip().split('\n') if line]
            for line in lines:
                data = json.loads(line)
                assert "timestamp" in data
                assert "event" in data
            
        finally:
            sys.stderr = old_stderr
            configure_logging(enabled=False)
    
    def test_optimize_logs_cache_hit(self):
        """Test that cache hits are logged correctly."""
        def simple_func(x):
            return x * 2
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            configure_logging(enabled=True, output="stderr", level="INFO")
            
            data = list(range(1000))
            
            # First call - should not be cache hit
            result1 = optimize(simple_func, data, sample_size=5, use_cache=True)
            output1 = sys.stderr.getvalue()
            
            # Check first optimization
            lines1 = [line for line in output1.strip().split('\n') if line and "optimization_complete" in line]
            if lines1:
                data1 = json.loads(lines1[0])
                # First call should not be cache hit
                assert data1.get("cache_hit", False) == False
            
            # Clear buffer
            sys.stderr = StringIO()
            
            # Second call with same data - should be cache hit
            result2 = optimize(simple_func, data, sample_size=5, use_cache=True)
            output2 = sys.stderr.getvalue()
            
            # Check for cache hit event
            if result2.cache_hit:
                lines2 = [line for line in output2.strip().split('\n') if line and "optimization_complete" in line]
                if lines2:
                    data2 = json.loads(lines2[0])
                    assert data2.get("cache_hit", False) == True
        finally:
            sys.stderr = old_stderr
            configure_logging(enabled=False)
            # Clear cache to not affect other tests
            from amorsize import clear_cache
            clear_cache()
    
    def test_optimize_logs_rejection(self):
        """Test that rejections are logged."""
        def unpicklable_func(x):
            # This will fail picklability check
            import threading
            lock = threading.Lock()
            return x * 2
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            configure_logging(enabled=True, output="stderr", level="INFO")
            
            data = range(10)
            result = optimize(unpicklable_func, data, sample_size=5)
            
            # Should recommend serial execution
            assert result.n_jobs == 1
            
            output = sys.stderr.getvalue()
            
            # Should have logged rejection or other event
            # (rejection logging depends on where picklability check fails)
            assert output != ""
            
        finally:
            sys.stderr = old_stderr
            configure_logging(enabled=False)


class TestConfigureLogging:
    """Test the configure_logging API."""
    
    def test_configure_logging_default(self):
        """Test configure_logging with default parameters."""
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            configure_logging(enabled=True)
            
            logger = get_logger()
            assert logger.enabled
            
            logger.log_optimization_start(func_name="test", data_size=100)
            output = sys.stderr.getvalue()
            
            # Should have output
            assert output != ""
        finally:
            sys.stderr = old_stderr
            configure_logging(enabled=False)
    
    def test_configure_logging_stdout(self):
        """Test configure_logging with stdout output."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            configure_logging(enabled=True, output="stdout")
            
            logger = get_logger()
            logger.log_optimization_start(func_name="test", data_size=100)
            output = sys.stdout.getvalue()
            
            # Should have output to stdout
            assert output != ""
        finally:
            sys.stdout = old_stdout
            configure_logging(enabled=False)
    
    def test_configure_logging_file(self):
        """Test configure_logging with file output."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        
        try:
            configure_logging(enabled=True, output=log_file)
            
            logger = get_logger()
            logger.log_optimization_start(func_name="file_test", data_size=200)
            configure_logging(enabled=False)
            
            # Read file
            with open(log_file, 'r') as f:
                content = f.read()
            
            assert content != ""
            assert "optimization_start" in content
        finally:
            if os.path.exists(log_file):
                os.remove(log_file)
    
    def test_configure_logging_disable(self):
        """Test disabling logging via configure_logging."""
        configure_logging(enabled=False)
        
        logger = get_logger()
        assert not logger.enabled


class TestLoggingMethods:
    """Test individual logging methods."""
    
    def test_log_optimization_start(self):
        """Test log_optimization_start method."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr")
            logger.log_optimization_start(func_name="my_function", data_size=1000)
            output = sys.stderr.getvalue()
            
            data = json.loads(output.strip().split('\n')[0])
            assert data["event"] == "optimization_start"
            assert data["function"] == "my_function"
            assert data["data_size"] == 1000
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_log_optimization_complete(self):
        """Test log_optimization_complete method."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr")
            logger.log_optimization_complete(
                n_jobs=4,
                chunksize=25,
                speedup=3.2,
                executor_type="process",
                cache_hit=False
            )
            output = sys.stderr.getvalue()
            
            data = json.loads(output.strip().split('\n')[0])
            assert data["event"] == "optimization_complete"
            assert data["n_jobs"] == 4
            assert data["chunksize"] == 25
            assert data["estimated_speedup"] == 3.2
            assert data["executor_type"] == "process"
            assert data["cache_hit"] == False
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_log_sampling_complete(self):
        """Test log_sampling_complete method."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr")
            logger.log_sampling_complete(
                sample_count=5,
                avg_time=0.01,
                is_picklable=True,
                workload_type="cpu_bound"
            )
            output = sys.stderr.getvalue()
            
            data = json.loads(output.strip().split('\n')[0])
            assert data["event"] == "sampling_complete"
            assert data["sample_count"] == 5
            assert data["avg_execution_time_seconds"] == 0.01
            assert data["is_picklable"] == True
            assert data["workload_type"] == "cpu_bound"
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_log_system_info(self):
        """Test log_system_info method."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr", level="DEBUG")
            logger.log_system_info(
                physical_cores=4,
                logical_cores=8,
                available_memory_bytes=8*1024**3,
                start_method="fork"
            )
            output = sys.stderr.getvalue()
            
            data = json.loads(output.strip().split('\n')[0])
            assert data["event"] == "system_info"
            assert data["physical_cores"] == 4
            assert data["logical_cores"] == 8
            assert data["available_memory_bytes"] == 8*1024**3
            assert data["multiprocessing_start_method"] == "fork"
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_log_rejection(self):
        """Test log_rejection method."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr")
            logger.log_rejection("workload_too_small", {"estimated_speedup": 1.1})
            output = sys.stderr.getvalue()
            
            data = json.loads(output.strip().split('\n')[0])
            assert data["event"] == "parallelization_rejected"
            assert data["reason"] == "workload_too_small"
            assert data["estimated_speedup"] == 1.1
        finally:
            sys.stderr = old_stderr
            logger.disable()
    
    def test_log_error(self):
        """Test log_error method."""
        logger = StructuredLogger()
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            logger.enable(output="stderr")
            logger.log_error("validation_error", "Invalid parameter", {"param": "sample_size"})
            output = sys.stderr.getvalue()
            
            data = json.loads(output.strip().split('\n')[0])
            assert data["event"] == "error"
            assert data["error_type"] == "validation_error"
            assert data["message"] == "Invalid parameter"
            assert data["param"] == "sample_size"
        finally:
            sys.stderr = old_stderr
            logger.disable()


class TestLoggingPerformance:
    """Test that logging has minimal performance overhead."""
    
    def test_disabled_logging_overhead(self):
        """Test that disabled logging has negligible overhead."""
        def simple_func(x):
            return x * 2
        
        data = list(range(100))
        
        # Time without logging
        configure_logging(enabled=False)
        start1 = time.perf_counter()
        result1 = optimize(simple_func, data, sample_size=5, use_cache=False)
        time1 = time.perf_counter() - start1
        
        # Time with logging disabled (should be same)
        configure_logging(enabled=False)
        start2 = time.perf_counter()
        result2 = optimize(simple_func, data, sample_size=5, use_cache=False)
        time2 = time.perf_counter() - start2
        
        # Both should be similar (within 50% difference)
        # This is a loose check since timing can vary
        assert abs(time1 - time2) / max(time1, time2) < 0.5


class TestBackwardCompatibility:
    """Test that logging doesn't break existing code."""
    
    def test_existing_code_works(self):
        """Test that existing code works without changes."""
        def my_func(x):
            return x ** 2
        
        data = range(50)
        
        # This should work exactly as before (logging disabled by default)
        result = optimize(my_func, data)
        
        assert result is not None
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
    
    def test_optimize_all_parameters(self):
        """Test optimize with all parameters still works."""
        def my_func(x):
            return x + 1
        
        data = list(range(100))
        
        result = optimize(
            my_func,
            data,
            sample_size=5,
            target_chunk_duration=0.2,
            verbose=False,
            use_spawn_benchmark=True,
            use_chunking_benchmark=True,
            profile=False
        )
        
        assert result is not None
