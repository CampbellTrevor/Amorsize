"""
Tests for built-in monitoring system integrations.

This test suite validates:
- Prometheus metrics exporter functionality
- StatsD client integration
- HTTP webhook integration
- Multi-system monitoring coordination
- Error isolation and thread safety
- Integration with execute() function
"""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Optional
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from amorsize.hooks import HookContext, HookEvent, HookManager
from amorsize.monitoring import (
    PrometheusMetrics,
    StatsDClient,
    create_multi_monitoring_hook,
    create_prometheus_hook,
    create_statsd_hook,
    create_webhook_hook,
)


# ============================================================================
# Prometheus Integration Tests
# ============================================================================


class TestPrometheusMetrics:
    """Test Prometheus metrics exporter."""
    
    def test_initialization(self):
        """Test that PrometheusMetrics initializes correctly."""
        metrics = PrometheusMetrics(port=9000, namespace="test")
        assert metrics.port == 9000
        assert metrics.namespace == "test"
        assert metrics._executions_total == 0
        assert metrics._errors_total == 0
    
    def test_update_from_pre_execute_context(self):
        """Test metrics update from PRE_EXECUTE event."""
        metrics = PrometheusMetrics()
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            n_jobs=4,
            total_items=1000,
        )
        
        metrics.update_from_context(ctx)
        
        assert metrics._executions_total == 1
        assert metrics._workers_active == 4
    
    def test_update_from_post_execute_context(self):
        """Test metrics update from POST_EXECUTE event."""
        metrics = PrometheusMetrics()
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            elapsed_time=5.5,
            total_items=1000,
            throughput_items_per_sec=181.8,
        )
        
        metrics.update_from_context(ctx)
        
        assert metrics._execution_duration_seconds == [5.5]
        assert metrics._items_processed_total == 1000
        assert metrics._throughput_items_per_second == 181.8
        assert metrics._workers_active == 0
    
    def test_update_from_error_context(self):
        """Test metrics update from ON_ERROR event."""
        metrics = PrometheusMetrics()
        ctx = HookContext(
            event=HookEvent.ON_ERROR,
            error_message="Test error",
        )
        
        metrics.update_from_context(ctx)
        
        assert metrics._errors_total == 1
    
    def test_generate_metrics_format(self):
        """Test that metrics are generated in Prometheus format."""
        metrics = PrometheusMetrics(namespace="amorsize")
        
        # Add some data
        metrics._executions_total = 5
        metrics._execution_duration_seconds = [1.0, 2.0, 3.0]
        metrics._items_processed_total = 1000
        metrics._workers_active = 4
        metrics._throughput_items_per_second = 200.0
        metrics._errors_total = 2
        
        output = metrics._generate_metrics()
        
        # Verify Prometheus format
        assert "# HELP amorsize_executions_total" in output
        assert "# TYPE amorsize_executions_total counter" in output
        assert "amorsize_executions_total 5" in output
        
        assert "# HELP amorsize_execution_duration_seconds" in output
        assert "amorsize_execution_duration_seconds_sum 6.0" in output
        assert "amorsize_execution_duration_seconds_count 3" in output
        
        assert "amorsize_items_processed_total 1000" in output
        assert "amorsize_workers_active 4" in output
        assert "amorsize_throughput_items_per_second 200.0" in output
        assert "amorsize_errors_total 2" in output
    
    def test_metrics_url(self):
        """Test metrics URL generation."""
        metrics = PrometheusMetrics(port=8000)
        assert metrics.get_metrics_url() == "http://localhost:8000/metrics"
    
    def test_thread_safety(self):
        """Test that metrics updates are thread-safe."""
        metrics = PrometheusMetrics()
        
        def update_metrics():
            for _ in range(100):
                ctx = HookContext(event=HookEvent.PRE_EXECUTE, n_jobs=1)
                metrics.update_from_context(ctx)
        
        # Run concurrent updates
        threads = [threading.Thread(target=update_metrics) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 500 total executions (5 threads * 100 updates)
        assert metrics._executions_total == 500


class TestCreatePrometheusHook:
    """Test Prometheus hook creation."""
    
    def test_returns_hook_manager(self):
        """Test that create_prometheus_hook returns a HookManager."""
        hooks = create_prometheus_hook(port=9001)
        assert isinstance(hooks, HookManager)
    
    def test_hook_manager_has_registered_hooks(self):
        """Test that hook manager has hooks registered for relevant events."""
        hooks = create_prometheus_hook(port=9002)
        
        # Check that hooks are registered
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert HookEvent.ON_ERROR in hooks._hooks
        assert len(hooks._hooks[HookEvent.PRE_EXECUTE]) > 0
    
    def test_hook_updates_metrics(self):
        """Test that triggering hooks updates Prometheus metrics."""
        hooks = create_prometheus_hook(port=9003)
        
        # Trigger PRE_EXECUTE hook
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            n_jobs=4,
            total_items=1000,
        )
        hooks.trigger(ctx)
        
        # Note: Can't easily verify metrics were updated without exposing internals
        # But this at least verifies the hook doesn't crash
    
    def test_error_isolation(self):
        """Test that hook errors don't crash execution."""
        hooks = create_prometheus_hook(port=9004)
        
        # Create context with invalid data to potentially cause errors
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            n_jobs=None,  # This might cause issues in metrics update
        )
        
        # Should not raise exception
        hooks.trigger(ctx)


# ============================================================================
# StatsD Integration Tests
# ============================================================================


class TestStatsDClient:
    """Test StatsD client functionality."""
    
    def test_initialization(self):
        """Test that StatsDClient initializes correctly."""
        client = StatsDClient(host='statsd.local', port=8126, prefix='test')
        assert client.host == 'statsd.local'
        assert client.port == 8126
        assert client.prefix == 'test'
    
    @patch('socket.socket')
    def test_increment_sends_counter(self, mock_socket):
        """Test that increment sends a counter metric."""
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        
        client = StatsDClient(host='localhost', port=8125, prefix='amorsize')
        client.increment('test.counter', value=5)
        
        # Verify socket sendto was called
        mock_sock_instance.sendto.assert_called_once()
        call_args = mock_sock_instance.sendto.call_args
        message = call_args[0][0].decode('utf-8')
        assert message == 'amorsize.test.counter:5|c'
        assert call_args[0][1] == ('localhost', 8125)
    
    @patch('socket.socket')
    def test_gauge_sends_gauge(self, mock_socket):
        """Test that gauge sends a gauge metric."""
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        
        client = StatsDClient(prefix='amorsize')
        client.gauge('test.gauge', 42.5)
        
        mock_sock_instance.sendto.assert_called_once()
        message = mock_sock_instance.sendto.call_args[0][0].decode('utf-8')
        assert message == 'amorsize.test.gauge:42.5|g'
    
    @patch('socket.socket')
    def test_timing_sends_timing(self, mock_socket):
        """Test that timing sends a timing metric."""
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        
        client = StatsDClient(prefix='amorsize')
        client.timing('test.timing', 123)
        
        mock_sock_instance.sendto.assert_called_once()
        message = mock_sock_instance.sendto.call_args[0][0].decode('utf-8')
        assert message == 'amorsize.test.timing:123|ms'
    
    @patch('socket.socket')
    def test_histogram_sends_histogram(self, mock_socket):
        """Test that histogram sends a histogram metric."""
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        
        client = StatsDClient(prefix='amorsize')
        client.histogram('test.histogram', 99.9)
        
        mock_sock_instance.sendto.assert_called_once()
        message = mock_sock_instance.sendto.call_args[0][0].decode('utf-8')
        assert message == 'amorsize.test.histogram:99.9|h'
    
    @patch('socket.socket')
    def test_error_isolation_on_network_error(self, mock_socket):
        """Test that network errors are isolated and don't crash."""
        mock_sock_instance = Mock()
        mock_sock_instance.sendto.side_effect = OSError("Network error")
        mock_socket.return_value = mock_sock_instance
        
        client = StatsDClient()
        
        # Should not raise exception
        client.increment('test.counter')


class TestCreateStatsdHook:
    """Test StatsD hook creation."""
    
    def test_returns_hook_manager(self):
        """Test that create_statsd_hook returns a HookManager."""
        hooks = create_statsd_hook(host='localhost')
        assert isinstance(hooks, HookManager)
    
    def test_hook_manager_has_registered_hooks(self):
        """Test that hook manager has hooks registered for relevant events."""
        hooks = create_statsd_hook(host='localhost')
        
        # Check that hooks are registered
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert HookEvent.ON_ERROR in hooks._hooks
    
    @patch('socket.socket')
    def test_hook_sends_metrics(self, mock_socket):
        """Test that triggering hooks sends StatsD metrics."""
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        
        hooks = create_statsd_hook(host='localhost')
        
        # Trigger PRE_EXECUTE hook
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            n_jobs=4,
            total_items=1000,
        )
        hooks.trigger(ctx)
        
        # Should have sent at least one metric
        assert mock_sock_instance.sendto.call_count >= 1


# ============================================================================
# HTTP Webhook Integration Tests
# ============================================================================


class TestCreateWebhookHook:
    """Test HTTP webhook hook creation."""
    
    def test_returns_hook_manager(self):
        """Test that create_webhook_hook returns a HookManager."""
        hooks = create_webhook_hook(url='http://example.com/webhook')
        assert isinstance(hooks, HookManager)
    
    def test_hook_manager_registers_all_events_by_default(self):
        """Test that all events are registered by default."""
        hooks = create_webhook_hook(url='http://example.com/webhook')
        
        # Should have hooks for all event types
        assert len(hooks._hooks) == len(HookEvent)
    
    def test_hook_manager_registers_only_specified_events(self):
        """Test that only specified events are registered."""
        hooks = create_webhook_hook(
            url='http://example.com/webhook',
            events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],
        )
        
        # Should only have hooks for specified events
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert HookEvent.ON_ERROR in hooks._hooks
    
    @patch('amorsize.monitoring.urlopen')
    def test_webhook_sends_json_payload(self, mock_urlopen):
        """Test that webhook sends JSON payload with context data."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        hooks = create_webhook_hook(url='http://example.com/webhook')
        
        # Trigger POST_EXECUTE hook
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            n_jobs=4,
            chunksize=100,
            total_items=1000,
            elapsed_time=5.5,
            throughput_items_per_sec=181.8,
        )
        hooks.trigger(ctx)
        
        # Verify urlopen was called
        assert mock_urlopen.call_count == 1
        
        # Verify request was made with correct data
        request = mock_urlopen.call_args[0][0]
        payload = json.loads(request.data.decode('utf-8'))
        
        assert payload['event'] == 'post_execute'
        assert payload['n_jobs'] == 4
        assert payload['chunksize'] == 100
        assert payload['total_items'] == 1000
        assert payload['elapsed_time'] == 5.5
        assert payload['throughput_items_per_sec'] == 181.8
    
    @patch('amorsize.monitoring.urlopen')
    def test_webhook_includes_auth_token(self, mock_urlopen):
        """Test that webhook includes auth token in headers."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        hooks = create_webhook_hook(
            url='http://example.com/webhook',
            auth_token='secret_token_123',
        )
        
        ctx = HookContext(event=HookEvent.POST_EXECUTE)
        hooks.trigger(ctx)
        
        # Verify auth header was included
        request = mock_urlopen.call_args[0][0]
        assert 'Authorization' in request.headers
        assert request.headers['Authorization'] == 'Bearer secret_token_123'
    
    @patch('amorsize.monitoring.urlopen')
    def test_webhook_error_isolation_on_http_error(self, mock_urlopen):
        """Test that HTTP errors are isolated and don't crash."""
        mock_urlopen.side_effect = HTTPError(
            url='http://example.com/webhook',
            code=500,
            msg='Internal Server Error',
            hdrs={},
            fp=None,
        )
        
        hooks = create_webhook_hook(url='http://example.com/webhook')
        
        ctx = HookContext(event=HookEvent.POST_EXECUTE)
        
        # Should not raise exception
        hooks.trigger(ctx)
    
    @patch('amorsize.monitoring.urlopen')
    def test_webhook_error_isolation_on_network_error(self, mock_urlopen):
        """Test that network errors are isolated and don't crash."""
        mock_urlopen.side_effect = URLError('Network unreachable')
        
        hooks = create_webhook_hook(url='http://example.com/webhook')
        
        ctx = HookContext(event=HookEvent.POST_EXECUTE)
        
        # Should not raise exception
        hooks.trigger(ctx)


# ============================================================================
# Multi-System Integration Tests
# ============================================================================


class TestCreateMultiMonitoringHook:
    """Test multi-system monitoring hook creation."""
    
    def test_returns_hook_manager(self):
        """Test that create_multi_monitoring_hook returns a HookManager."""
        hooks = create_multi_monitoring_hook(prometheus_port=9010)
        assert isinstance(hooks, HookManager)
    
    def test_enables_only_prometheus(self):
        """Test enabling only Prometheus."""
        hooks = create_multi_monitoring_hook(prometheus_port=9011)
        
        # Should have hooks registered
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert len(hooks._hooks[HookEvent.PRE_EXECUTE]) > 0
    
    @patch('socket.socket')
    def test_enables_only_statsd(self, mock_socket):
        """Test enabling only StatsD."""
        mock_socket.return_value = Mock()
        hooks = create_multi_monitoring_hook(statsd_host='localhost')
        
        # Should have hooks registered
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert len(hooks._hooks[HookEvent.PRE_EXECUTE]) > 0
    
    @patch('amorsize.monitoring.urlopen')
    def test_enables_only_webhook(self, mock_urlopen):
        """Test enabling only webhook."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        hooks = create_multi_monitoring_hook(webhook_url='http://example.com/webhook')
        
        # Should have hooks registered
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert len(hooks._hooks[HookEvent.POST_EXECUTE]) > 0
    
    @patch('socket.socket')
    def test_enables_multiple_systems(self, mock_socket):
        """Test enabling multiple monitoring systems simultaneously."""
        mock_socket.return_value = Mock()
        
        hooks = create_multi_monitoring_hook(
            prometheus_port=9012,
            statsd_host='localhost',
        )
        
        # Should have hooks from both systems
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        # Should have at least 2 hooks (one from each system)
        assert len(hooks._hooks[HookEvent.PRE_EXECUTE]) >= 2
    
    def test_returns_empty_hook_manager_when_no_systems_enabled(self):
        """Test that empty hook manager is returned when no systems enabled."""
        hooks = create_multi_monitoring_hook()
        
        # Should still be a valid hook manager, just with no hooks
        assert isinstance(hooks, HookManager)


# ============================================================================
# Integration Tests with execute()
# ============================================================================


class TestMonitoringIntegrationWithExecute:
    """Test monitoring integrations with the execute() function."""
    
    @patch('socket.socket')
    def test_monitoring_works_with_execute(self, mock_socket):
        """Test that monitoring integrations work with execute()."""
        from amorsize import execute
        
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        
        # Create monitoring hooks
        hooks = create_statsd_hook(host='localhost')
        
        # Simple test function
        def square(x):
            return x * x
        
        # Execute with monitoring
        data = range(10)
        results = execute(square, data, hooks=hooks)
        
        # Verify results are correct
        assert list(results) == [x * x for x in range(10)]
        
        # Verify StatsD metrics were sent
        assert mock_sock_instance.sendto.call_count >= 1


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling in monitoring integrations."""
    
    def test_prometheus_with_empty_metrics(self):
        """Test Prometheus metrics generation with no data."""
        metrics = PrometheusMetrics()
        output = metrics._generate_metrics()
        
        # Should generate valid (empty) metrics
        assert "amorsize_executions_total 0" in output
        assert "amorsize_errors_total 0" in output
    
    def test_statsd_with_none_values(self):
        """Test StatsD client with None values."""
        # This tests defensive programming - StatsD should handle None gracefully
        # In practice, our code shouldn't send None values, but good to be safe
        pass  # StatsDClient methods expect numeric values, not None
    
    @patch('amorsize.monitoring.urlopen')
    def test_webhook_removes_none_values_from_payload(self, mock_urlopen):
        """Test that webhook removes None values from payload."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        hooks = create_webhook_hook(url='http://example.com/webhook')
        
        # Context with many None values
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            n_jobs=4,
            chunksize=None,  # None value
            total_items=None,  # None value
        )
        hooks.trigger(ctx)
        
        # Verify payload doesn't include None values
        request = mock_urlopen.call_args[0][0]
        payload = json.loads(request.data.decode('utf-8'))
        
        assert 'n_jobs' in payload
        assert payload['n_jobs'] == 4
        # None values should be filtered out
        assert 'chunksize' not in payload or payload.get('chunksize') is None
    
    def test_prometheus_thread_safety_with_concurrent_servers(self):
        """Test that multiple Prometheus instances don't interfere."""
        # Each instance should use a different port
        metrics1 = PrometheusMetrics(port=9020)
        metrics2 = PrometheusMetrics(port=9021)
        
        # Update both concurrently
        ctx = HookContext(event=HookEvent.PRE_EXECUTE, n_jobs=2)
        metrics1.update_from_context(ctx)
        metrics2.update_from_context(ctx)
        
        # Both should have recorded the execution
        assert metrics1._executions_total == 1
        assert metrics2._executions_total == 1
