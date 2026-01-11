"""
Structured logging module for production observability.

This module provides JSON-formatted structured logging for Amorsize,
enabling integration with log aggregation systems (ELK, Splunk, Datadog, etc.)
and machine-readable log analysis.

Design Principles:
- Minimal performance overhead (lazy evaluation, disabled by default)
- Optional (maintains backward compatibility)
- JSON-formatted for parsing by log aggregation systems
- Captures key optimization decisions and performance metrics
- Thread-safe and multiprocessing-safe
"""

import json
import logging
import sys
import time
from enum import Enum
from typing import Any, Dict, Optional


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class StructuredLogger:
    """
    Structured logger for Amorsize optimization events.

    Provides JSON-formatted logging with structured data for key
    optimization decisions, system information, and performance metrics.

    Thread-safe: Uses Python's logging module which is thread-safe.
    Multiprocessing-safe: Each process gets its own logger instance.
    """

    def __init__(self, name: str = "amorsize", level: str = "INFO"):
        """
        Initialize structured logger.

        Args:
            name: Logger name (default: "amorsize")
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger(name)
        self.enabled = False  # Disabled by default for backward compatibility

        # Set log level
        self._set_level(level)

    def _set_level(self, level: str):
        """Set the log level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))

    def enable(self, output: str = "stderr", format_json: bool = True, level: str = "INFO"):
        """
        Enable structured logging.

        Args:
            output: Output destination ("stderr", "stdout", or file path)
            format_json: If True, use JSON formatting (default: True)
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.enabled = True
        self._set_level(level)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add handler based on output destination
        handler: logging.Handler
        if output == "stderr":
            handler = logging.StreamHandler(sys.stderr)
        elif output == "stdout":
            handler = logging.StreamHandler(sys.stdout)
        else:
            # File output
            handler = logging.FileHandler(output)

        # Set formatter
        if format_json:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))

        self.logger.addHandler(handler)

    def disable(self):
        """Disable structured logging."""
        self.enabled = False
        self.logger.handlers.clear()

    def _log(self, level: LogLevel, event: str, data: Optional[Dict[str, Any]] = None):
        """
        Internal logging method with lazy evaluation.

        Args:
            level: Log level
            event: Event name/description
            data: Additional structured data
        """
        if not self.enabled:
            return

        # Build structured log entry
        log_entry = {
            "timestamp": time.time(),
            "event": event,
        }

        if data:
            log_entry.update(data)

        # Log at appropriate level
        level_method = getattr(self.logger, level.value.lower())
        level_method(json.dumps(log_entry))

    def log_optimization_start(self, func_name: Optional[str] = None, data_size: Optional[int] = None):
        """Log the start of an optimization."""
        self._log(LogLevel.INFO, "optimization_start", {
            "function": func_name or "unknown",
            "data_size": data_size
        })

    def log_optimization_complete(self, n_jobs: int, chunksize: int, speedup: float,
                                   executor_type: str, cache_hit: bool = False):
        """Log successful optimization completion."""
        self._log(LogLevel.INFO, "optimization_complete", {
            "n_jobs": n_jobs,
            "chunksize": chunksize,
            "estimated_speedup": speedup,
            "executor_type": executor_type,
            "cache_hit": cache_hit
        })

    def log_sampling_complete(self, sample_count: int, avg_time: float,
                              is_picklable: bool, workload_type: str):
        """Log completion of dry run sampling."""
        self._log(LogLevel.INFO, "sampling_complete", {
            "sample_count": sample_count,
            "avg_execution_time_seconds": avg_time,
            "is_picklable": is_picklable,
            "workload_type": workload_type
        })

    def log_system_info(self, physical_cores: int, logical_cores: int,
                        available_memory_bytes: int, start_method: str):
        """Log system information."""
        self._log(LogLevel.DEBUG, "system_info", {
            "physical_cores": physical_cores,
            "logical_cores": logical_cores,
            "available_memory_bytes": available_memory_bytes,
            "available_memory_gb": available_memory_bytes / (1024**3),
            "multiprocessing_start_method": start_method
        })

    def log_rejection(self, reason: str, details: Optional[Dict[str, Any]] = None):
        """Log parallelization rejection."""
        log_data = {"reason": reason}
        if details:
            log_data.update(details)
        self._log(LogLevel.WARNING, "parallelization_rejected", log_data)

    def log_constraint(self, constraint_type: str, message: str,
                       details: Optional[Dict[str, Any]] = None):
        """Log optimization constraint."""
        log_data = {
            "constraint_type": constraint_type,
            "message": message
        }
        if details:
            log_data.update(details)
        self._log(LogLevel.WARNING, "optimization_constraint", log_data)

    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics."""
        self._log(LogLevel.DEBUG, "performance_metrics", metrics)

    def log_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log an error."""
        log_data = {
            "error_type": error_type,
            "message": message
        }
        if details:
            log_data.update(details)
        self._log(LogLevel.ERROR, "error", log_data)


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON.

    This enables easy parsing by log aggregation systems and
    structured log analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # The message itself should already be JSON from _log method
        # But we add standard logging fields
        try:
            # Try to parse the message as JSON
            message_data = json.loads(record.getMessage())
        except (json.JSONDecodeError, ValueError):
            # If it's not JSON, treat it as a plain message
            message_data = {"message": record.getMessage()}

        log_entry = {
            "timestamp": record.created,
            "level": record.levelname,
            "logger": record.name,
            **message_data
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger() -> StructuredLogger:
    """
    Get the global structured logger instance.

    Returns:
        The global StructuredLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger()
    return _global_logger


def configure_logging(enabled: bool = True, output: str = "stderr",
                      format_json: bool = True, level: str = "INFO"):
    """
    Configure structured logging for Amorsize.

    Args:
        enabled: Enable or disable structured logging (default: True)
        output: Output destination - "stderr", "stdout", or file path (default: "stderr")
        format_json: Use JSON formatting (default: True)
        level: Log level - "DEBUG", "INFO", "WARNING", "ERROR" (default: "INFO")

    Example:
        >>> from amorsize import configure_logging
        >>> configure_logging(enabled=True, output="stderr", level="INFO")
        >>> # Now all optimizations will log structured events
        >>> result = optimize(my_func, data)

    Production Example:
        >>> # Log to file in JSON format for log aggregation
        >>> configure_logging(enabled=True, output="/var/log/amorsize.log", level="INFO")

    Disable Example:
        >>> # Disable logging (default behavior)
        >>> configure_logging(enabled=False)
    """
    logger = get_logger()

    if enabled:
        logger.enable(output=output, format_json=format_json, level=level)
    else:
        logger.disable()
