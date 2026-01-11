"""
Tests for cloud-native monitoring integrations.

This module tests AWS CloudWatch, Azure Monitor, GCP Cloud Monitoring,
and OpenTelemetry integrations for Amorsize execution monitoring.
"""

import sys
import threading
import time
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from amorsize.hooks import HookContext, HookEvent, HookManager
from amorsize.monitoring import (
    AzureMonitorMetrics,
    CloudWatchMetrics,
    GCPMonitoringMetrics,
    OpenTelemetryTracer,
    create_azure_monitor_hook,
    create_cloudwatch_hook,
    create_gcp_monitoring_hook,
    create_opentelemetry_hook,
)


# ============================================================================
# AWS CloudWatch Tests
# ============================================================================


class TestCloudWatchMetrics:
    """Tests for AWS CloudWatch integration."""
    
    def _setup_mock_cloudwatch(self):
        """
        Helper method to set up a mocked CloudWatchMetrics instance.
        
        Returns:
            Tuple of (metrics, mock_client) where:
            - metrics: CloudWatchMetrics instance with mocked boto3
            - mock_client: MagicMock for the CloudWatch client
        """
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        metrics = CloudWatchMetrics()
        metrics._boto3 = mock_boto3
        metrics._has_boto3 = True
        
        return metrics, mock_client
    
    def test_cloudwatch_init_without_boto3(self):
        """Test CloudWatch initialization when boto3 is not installed."""
        with patch.dict(sys.modules, {'boto3': None}):
            metrics = CloudWatchMetrics()
            assert metrics._has_boto3 is False
            assert metrics._client is None
    
    def test_cloudwatch_init_with_config(self):
        """Test CloudWatch initialization with custom configuration."""
        metrics = CloudWatchMetrics(
            namespace="MyApp",
            region_name="us-west-2",
            dimensions={"Environment": "Production"},
        )
        assert metrics.namespace == "MyApp"
        assert metrics.region_name == "us-west-2"
        assert metrics.dimensions == {"Environment": "Production"}
    
    def test_cloudwatch_update_pre_execute(self):
        """Test CloudWatch metrics on PRE_EXECUTE event."""
        metrics, mock_client = self._setup_mock_cloudwatch()
        
        # Create context
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
            n_jobs=4,
        )
        
        # Update metrics
        metrics.update_from_context(ctx)
        
        # Verify put_metric_data was called
        assert mock_client.put_metric_data.call_count >= 2
    
    def test_cloudwatch_update_post_execute(self):
        """Test CloudWatch metrics on POST_EXECUTE event."""
        metrics, mock_client = self._setup_mock_cloudwatch()
        
        # Create context
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            timestamp=time.time(),
            elapsed_time=5.2,
            total_items=1000,
            throughput_items_per_sec=192.3,
        )
        
        # Update metrics
        metrics.update_from_context(ctx)
        
        # Verify put_metric_data was called
        assert mock_client.put_metric_data.call_count >= 4
    
    def test_cloudwatch_update_on_error(self):
        """Test CloudWatch metrics on ON_ERROR event."""
        metrics, mock_client = self._setup_mock_cloudwatch()
        
        # Create context
        ctx = HookContext(
            event=HookEvent.ON_ERROR,
            timestamp=time.time(),
            error_message="Test error",
        )
        
        # Update metrics
        metrics.update_from_context(ctx)
        
        # Verify put_metric_data was called
        assert mock_client.put_metric_data.call_count >= 1
    
    def test_cloudwatch_update_on_progress(self):
        """Test CloudWatch metrics on ON_PROGRESS event."""
        metrics, mock_client = self._setup_mock_cloudwatch()
        
        # Create context
        ctx = HookContext(
            event=HookEvent.ON_PROGRESS,
            timestamp=time.time(),
            percent_complete=50.0,
            throughput_items_per_sec=200.0,
        )
        
        # Update metrics
        metrics.update_from_context(ctx)
        
        # Verify put_metric_data was called
        assert mock_client.put_metric_data.call_count >= 2
    
    def test_cloudwatch_update_on_chunk_complete(self):
        """Test CloudWatch metrics on ON_CHUNK_COMPLETE event."""
        metrics, mock_client = self._setup_mock_cloudwatch()
        
        # Create context
        ctx = HookContext(
            event=HookEvent.ON_CHUNK_COMPLETE,
            timestamp=time.time(),
            chunk_id=1,
            chunk_size=100,
            chunk_time=0.5,
        )
        
        # Update metrics
        metrics.update_from_context(ctx)
        
        # Verify put_metric_data was called
        assert mock_client.put_metric_data.call_count >= 1
    
    def test_cloudwatch_error_isolation(self):
        """Test that CloudWatch errors don't crash execution."""
        # Create mocked CloudWatch with error-raising client
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_client.put_metric_data.side_effect = Exception("Network error")
        mock_boto3.client.return_value = mock_client
        
        metrics = CloudWatchMetrics()
        metrics._boto3 = mock_boto3
        metrics._has_boto3 = True
        
        # Create context
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
            n_jobs=4,
        )
        
        # Should not raise exception
        metrics.update_from_context(ctx)


class TestCreateCloudWatchHook:
    """Tests for create_cloudwatch_hook function."""
    
    def test_create_cloudwatch_hook_returns_hook_manager(self):
        """Test that create_cloudwatch_hook returns a HookManager."""
        hooks = create_cloudwatch_hook()
        assert isinstance(hooks, HookManager)
    
    def test_create_cloudwatch_hook_registers_events(self):
        """Test that create_cloudwatch_hook registers all relevant events."""
        hooks = create_cloudwatch_hook()
        
        # Check that hooks are registered for key events
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert HookEvent.ON_ERROR in hooks._hooks
        assert HookEvent.ON_PROGRESS in hooks._hooks
        assert HookEvent.ON_CHUNK_COMPLETE in hooks._hooks
    
    def test_create_cloudwatch_hook_with_config(self):
        """Test create_cloudwatch_hook with custom configuration."""
        hooks = create_cloudwatch_hook(
            namespace="MyApp",
            region_name="us-west-2",
            dimensions={"Env": "Prod"},
        )
        assert isinstance(hooks, HookManager)


# ============================================================================
# Azure Monitor Tests
# ============================================================================


class TestAzureMonitorMetrics:
    """Tests for Azure Monitor integration."""
    
    def test_azure_monitor_init_without_package(self):
        """Test Azure Monitor initialization when package is not installed."""
        with patch.dict(sys.modules, {'azure.monitor.opentelemetry': None}):
            metrics = AzureMonitorMetrics(connection_string="test")
            assert metrics._has_azure_monitor is False
    
    def test_azure_monitor_init_with_connection_string(self):
        """Test Azure Monitor initialization with connection string."""
        metrics = AzureMonitorMetrics(
            connection_string="InstrumentationKey=test;IngestionEndpoint=https://test.com"
        )
        assert metrics.connection_string is not None
    
    def test_azure_monitor_init_with_instrumentation_key(self):
        """Test Azure Monitor initialization with instrumentation key."""
        metrics = AzureMonitorMetrics(instrumentation_key="test-key")
        assert metrics.instrumentation_key == "test-key"
    
    def test_azure_monitor_update_pre_execute(self):
        """Test Azure Monitor metrics on PRE_EXECUTE event."""
        metrics = AzureMonitorMetrics(connection_string="test")
        
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
            n_jobs=4,
        )
        
        # Should not raise exception
        metrics.update_from_context(ctx)
    
    def test_azure_monitor_update_post_execute(self):
        """Test Azure Monitor metrics on POST_EXECUTE event."""
        metrics = AzureMonitorMetrics(connection_string="test")
        
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            timestamp=time.time(),
            elapsed_time=5.2,
            total_items=1000,
        )
        
        # Should not raise exception
        metrics.update_from_context(ctx)
    
    def test_azure_monitor_error_isolation(self):
        """Test that Azure Monitor errors don't crash execution."""
        metrics = AzureMonitorMetrics(connection_string="test")
        metrics._has_azure_monitor = True
        metrics._send_event = MagicMock(side_effect=Exception("Network error"))
        
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
        )
        
        # Should not raise exception
        metrics.update_from_context(ctx)


class TestCreateAzureMonitorHook:
    """Tests for create_azure_monitor_hook function."""
    
    def test_create_azure_monitor_hook_returns_hook_manager(self):
        """Test that create_azure_monitor_hook returns a HookManager."""
        hooks = create_azure_monitor_hook(connection_string="test")
        assert isinstance(hooks, HookManager)
    
    def test_create_azure_monitor_hook_registers_events(self):
        """Test that create_azure_monitor_hook registers all relevant events."""
        hooks = create_azure_monitor_hook(connection_string="test")
        
        # Check that hooks are registered for key events
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert HookEvent.ON_ERROR in hooks._hooks


# ============================================================================
# GCP Monitoring Tests
# ============================================================================


class TestGCPMonitoringMetrics:
    """Tests for GCP Monitoring integration."""
    
    def test_gcp_monitoring_init_without_package(self):
        """Test GCP Monitoring initialization when package is not installed."""
        with patch.dict(sys.modules, {'google.cloud.monitoring_v3': None}):
            metrics = GCPMonitoringMetrics(project_id="test-project")
            assert metrics._has_gcp_monitoring is False
    
    def test_gcp_monitoring_init_with_config(self):
        """Test GCP Monitoring initialization with configuration."""
        metrics = GCPMonitoringMetrics(
            project_id="test-project",
            metric_prefix="custom.googleapis.com/myapp",
        )
        assert metrics.project_id == "test-project"
        assert metrics.metric_prefix == "custom.googleapis.com/myapp"
    
    def test_gcp_monitoring_update_pre_execute(self):
        """Test GCP Monitoring metrics on PRE_EXECUTE event."""
        metrics = GCPMonitoringMetrics(project_id="test")
        
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
            n_jobs=4,
        )
        
        # Should not raise exception
        metrics.update_from_context(ctx)
    
    def test_gcp_monitoring_update_post_execute(self):
        """Test GCP Monitoring metrics on POST_EXECUTE event."""
        metrics = GCPMonitoringMetrics(project_id="test")
        
        ctx = HookContext(
            event=HookEvent.POST_EXECUTE,
            timestamp=time.time(),
            elapsed_time=5.2,
            total_items=1000,
        )
        
        # Should not raise exception
        metrics.update_from_context(ctx)
    
    def test_gcp_monitoring_error_isolation(self):
        """Test that GCP Monitoring errors don't crash execution."""
        metrics = GCPMonitoringMetrics(project_id="test")
        metrics._has_gcp_monitoring = True
        
        # Mock client to raise error
        mock_client = MagicMock()
        mock_client.create_time_series.side_effect = Exception("Network error")
        metrics._client = mock_client
        
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
        )
        
        # Should not raise exception
        metrics.update_from_context(ctx)


class TestCreateGCPMonitoringHook:
    """Tests for create_gcp_monitoring_hook function."""
    
    def test_create_gcp_monitoring_hook_returns_hook_manager(self):
        """Test that create_gcp_monitoring_hook returns a HookManager."""
        hooks = create_gcp_monitoring_hook(project_id="test")
        assert isinstance(hooks, HookManager)
    
    def test_create_gcp_monitoring_hook_registers_events(self):
        """Test that create_gcp_monitoring_hook registers all relevant events."""
        hooks = create_gcp_monitoring_hook(project_id="test")
        
        # Check that hooks are registered for key events
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert HookEvent.ON_ERROR in hooks._hooks


# ============================================================================
# OpenTelemetry Tests
# ============================================================================


class TestOpenTelemetryTracer:
    """Tests for OpenTelemetry integration."""
    
    def test_opentelemetry_init_without_package(self):
        """Test OpenTelemetry initialization when package is not installed."""
        with patch.dict(sys.modules, {'opentelemetry': None}):
            tracer = OpenTelemetryTracer()
            assert tracer._has_opentelemetry is False
    
    def test_opentelemetry_init_with_config(self):
        """Test OpenTelemetry initialization with configuration."""
        tracer = OpenTelemetryTracer(
            service_name="my-service",
            exporter_endpoint="http://localhost:4318",
        )
        assert tracer.service_name == "my-service"
        assert tracer.exporter_endpoint == "http://localhost:4318"
    
    def test_opentelemetry_update_pre_execute(self):
        """Test OpenTelemetry span on PRE_EXECUTE event."""
        tracer = OpenTelemetryTracer()
        
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
            n_jobs=4,
            chunksize=100,
            total_items=1000,
        )
        
        # Should not raise exception
        tracer.update_from_context(ctx)
    
    def test_opentelemetry_update_post_execute(self):
        """Test OpenTelemetry span on POST_EXECUTE event."""
        tracer = OpenTelemetryTracer()
        
        # Start span
        ctx_pre = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
        )
        tracer.update_from_context(ctx_pre)
        
        # End span
        ctx_post = HookContext(
            event=HookEvent.POST_EXECUTE,
            timestamp=time.time(),
            elapsed_time=5.2,
            throughput_items_per_sec=192.3,
        )
        tracer.update_from_context(ctx_post)
    
    def test_opentelemetry_update_on_error(self):
        """Test OpenTelemetry span on ON_ERROR event."""
        tracer = OpenTelemetryTracer()
        
        # Start span
        ctx_pre = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
        )
        tracer.update_from_context(ctx_pre)
        
        # Record error
        ctx_error = HookContext(
            event=HookEvent.ON_ERROR,
            timestamp=time.time(),
            error_message="Test error",
        )
        tracer.update_from_context(ctx_error)
    
    def test_opentelemetry_update_on_progress(self):
        """Test OpenTelemetry span event on ON_PROGRESS."""
        tracer = OpenTelemetryTracer()
        
        # Start span
        ctx_pre = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
        )
        tracer.update_from_context(ctx_pre)
        
        # Add progress event
        ctx_progress = HookContext(
            event=HookEvent.ON_PROGRESS,
            timestamp=time.time(),
            percent_complete=50.0,
            items_completed=500,
        )
        tracer.update_from_context(ctx_progress)
    
    def test_opentelemetry_update_on_chunk_complete(self):
        """Test OpenTelemetry span event on ON_CHUNK_COMPLETE."""
        tracer = OpenTelemetryTracer()
        
        # Start span
        ctx_pre = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
        )
        tracer.update_from_context(ctx_pre)
        
        # Add chunk completion event
        ctx_chunk = HookContext(
            event=HookEvent.ON_CHUNK_COMPLETE,
            timestamp=time.time(),
            chunk_id=1,
            chunk_size=100,
            chunk_time=0.5,
        )
        tracer.update_from_context(ctx_chunk)
    
    def test_opentelemetry_error_isolation(self):
        """Test that OpenTelemetry errors don't crash execution."""
        tracer = OpenTelemetryTracer()
        tracer._has_opentelemetry = True
        tracer._tracer = MagicMock()
        tracer._tracer.start_span.side_effect = Exception("Tracing error")
        
        ctx = HookContext(
            event=HookEvent.PRE_EXECUTE,
            timestamp=time.time(),
        )
        
        # Should not raise exception
        tracer.update_from_context(ctx)


class TestCreateOpenTelemetryHook:
    """Tests for create_opentelemetry_hook function."""
    
    def test_create_opentelemetry_hook_returns_hook_manager(self):
        """Test that create_opentelemetry_hook returns a HookManager."""
        hooks = create_opentelemetry_hook()
        assert isinstance(hooks, HookManager)
    
    def test_create_opentelemetry_hook_registers_events(self):
        """Test that create_opentelemetry_hook registers all relevant events."""
        hooks = create_opentelemetry_hook()
        
        # Check that hooks are registered for key events
        assert HookEvent.PRE_EXECUTE in hooks._hooks
        assert HookEvent.POST_EXECUTE in hooks._hooks
        assert HookEvent.ON_ERROR in hooks._hooks
        assert HookEvent.ON_PROGRESS in hooks._hooks
        assert HookEvent.ON_CHUNK_COMPLETE in hooks._hooks
    
    def test_create_opentelemetry_hook_with_config(self):
        """Test create_opentelemetry_hook with custom configuration."""
        hooks = create_opentelemetry_hook(
            service_name="my-service",
            exporter_endpoint="http://localhost:4318",
        )
        assert isinstance(hooks, HookManager)


# ============================================================================
# Integration Tests
# ============================================================================


class TestCloudIntegrationCompatibility:
    """Tests for compatibility between cloud integrations."""
    
    def test_all_cloud_hooks_can_coexist(self):
        """Test that multiple cloud hooks can be used together."""
        # Create all hooks
        cloudwatch_hooks = create_cloudwatch_hook()
        azure_hooks = create_azure_monitor_hook(connection_string="test")
        gcp_hooks = create_gcp_monitoring_hook(project_id="test")
        otel_hooks = create_opentelemetry_hook()
        
        # All should be HookManager instances
        assert isinstance(cloudwatch_hooks, HookManager)
        assert isinstance(azure_hooks, HookManager)
        assert isinstance(gcp_hooks, HookManager)
        assert isinstance(otel_hooks, HookManager)
    
    def test_cloud_hooks_thread_safety(self):
        """Test that cloud hooks are thread-safe."""
        hooks = create_cloudwatch_hook()
        
        def trigger_hook():
            ctx = HookContext(
                event=HookEvent.PRE_EXECUTE,
                timestamp=time.time(),
                n_jobs=4,
            )
            hooks.trigger(HookEvent.PRE_EXECUTE, ctx)
        
        # Create multiple threads
        threads = [threading.Thread(target=trigger_hook) for _ in range(10)]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Should complete without errors


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing monitoring."""
    
    def test_cloud_hooks_dont_break_existing_code(self):
        """Test that adding cloud hooks doesn't break existing functionality."""
        # Import existing monitoring functions
        from amorsize.monitoring import (
            create_prometheus_hook,
            create_statsd_hook,
            create_webhook_hook,
        )
        
        # All should still work
        prom_hooks = create_prometheus_hook()
        statsd_hooks = create_statsd_hook()
        webhook_hooks = create_webhook_hook(url="http://example.com")
        
        assert isinstance(prom_hooks, HookManager)
        assert isinstance(statsd_hooks, HookManager)
        assert isinstance(webhook_hooks, HookManager)
    
    def test_cloud_hooks_available_in_main_module(self):
        """Test that cloud hooks are available from main amorsize module."""
        from amorsize import (
            create_azure_monitor_hook,
            create_cloudwatch_hook,
            create_gcp_monitoring_hook,
            create_opentelemetry_hook,
        )
        
        # All should be callable
        assert callable(create_cloudwatch_hook)
        assert callable(create_azure_monitor_hook)
        assert callable(create_gcp_monitoring_hook)
        assert callable(create_opentelemetry_hook)
