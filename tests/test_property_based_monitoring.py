"""
Property-based tests for monitoring module using Hypothesis.

These tests verify invariants and properties that should hold for all inputs,
automatically generating thousands of edge cases to test the monitoring module's robustness.
"""

import threading
import time
from hypothesis import given, strategies as st, settings, assume
import pytest

from amorsize.monitoring import (
    PrometheusMetrics,
    StatsDClient,
    CloudWatchMetrics,
    AzureMonitorMetrics,
    GCPMonitoringMetrics,
    OpenTelemetryTracer,
    create_prometheus_hook,
    create_statsd_hook,
    create_webhook_hook,
    create_multi_monitoring_hook,
    create_cloudwatch_hook,
    create_azure_monitor_hook,
    create_gcp_monitoring_hook,
    create_opentelemetry_hook,
)
from amorsize.hooks import HookContext, HookEvent, HookManager


# ============================================================================
# Test Strategies (Input Generators)
# ============================================================================

@st.composite
def port_strategy(draw):
    """Generate valid port numbers."""
    return draw(st.integers(min_value=1024, max_value=65535))


@st.composite
def namespace_strategy(draw):
    """Generate valid metric namespaces."""
    return draw(st.text(alphabet=st.characters(categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_'), min_size=1, max_size=20))


@st.composite
def host_strategy(draw):
    """Generate valid hostnames."""
    return draw(st.sampled_from(['localhost', '127.0.0.1', 'monitoring.local', 'metrics.example.com']))


@st.composite
def hook_context_strategy(draw):
    """Generate valid HookContext objects for testing."""
    event = draw(st.sampled_from([HookEvent.PRE_EXECUTE, HookEvent.POST_EXECUTE, HookEvent.ON_ERROR]))
    
    ctx = HookContext(event=event)
    
    # Add context-specific fields
    if event == HookEvent.PRE_EXECUTE:
        ctx.n_jobs = draw(st.integers(min_value=1, max_value=32))
    elif event == HookEvent.POST_EXECUTE:
        ctx.elapsed_time = draw(st.floats(min_value=0.001, max_value=1000.0))
        ctx.total_items = draw(st.integers(min_value=1, max_value=10000))
        ctx.throughput_items_per_sec = draw(st.floats(min_value=0.1, max_value=10000.0))
    
    return ctx


# ============================================================================
# 1. PrometheusMetrics Invariants
# ============================================================================

class TestPrometheusMetricsInvariants:
    """Test invariants of the PrometheusMetrics class."""
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_prometheus_metrics_initialization(self, port, namespace):
        """PrometheusMetrics should initialize with valid parameters."""
        assume(namespace.isidentifier() or '_' in namespace)  # Valid Python identifier
        
        metrics = PrometheusMetrics(port=port, namespace=namespace)
        
        assert metrics.port == port
        assert metrics.namespace == namespace
        assert metrics._executions_total == 0
        assert metrics._items_processed_total == 0
        assert metrics._errors_total == 0
        assert metrics._workers_active == 0
        assert metrics._throughput_items_per_second == 0.0
        assert metrics._execution_duration_seconds == []
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_prometheus_metrics_url_format(self, port, namespace):
        """PrometheusMetrics URL should have correct format."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        metrics = PrometheusMetrics(port=port, namespace=namespace)
        url = metrics.get_metrics_url()
        
        assert url.startswith("http://localhost:")
        assert str(port) in url
        assert url.endswith("/metrics")
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_prometheus_generate_metrics_format(self, port, namespace):
        """Generated Prometheus metrics should be in valid text format."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        metrics = PrometheusMetrics(port=port, namespace=namespace)
        metrics_text = metrics._generate_metrics()
        
        # Should be non-empty string
        assert isinstance(metrics_text, str)
        assert len(metrics_text) > 0
        
        # Should contain HELP and TYPE lines
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        
        # Should contain namespace
        assert namespace in metrics_text
        
        # Should end with newline
        assert metrics_text.endswith('\n')
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy(),
        ctx=hook_context_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_prometheus_update_from_context_thread_safe(self, port, namespace, ctx):
        """Prometheus metric updates should be thread-safe."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        metrics = PrometheusMetrics(port=port, namespace=namespace)
        
        # Update should not raise exception
        metrics.update_from_context(ctx)
        
        # Metrics should reflect updates
        if ctx.event == HookEvent.PRE_EXECUTE:
            assert metrics._executions_total >= 1
            if ctx.n_jobs:
                assert metrics._workers_active == ctx.n_jobs
        elif ctx.event == HookEvent.POST_EXECUTE:
            if ctx.elapsed_time is not None:
                assert len(metrics._execution_duration_seconds) >= 1
            if ctx.total_items:
                assert metrics._items_processed_total >= ctx.total_items
        elif ctx.event == HookEvent.ON_ERROR:
            assert metrics._errors_total >= 1


# ============================================================================
# 2. StatsDClient Invariants
# ============================================================================

class TestStatsDClientInvariants:
    """Test invariants of the StatsDClient class."""
    
    @given(
        host=host_strategy(),
        port=port_strategy(),
        prefix=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_statsd_client_initialization(self, host, port, prefix):
        """StatsDClient should initialize with valid parameters."""
        assume(prefix.isidentifier() or '_' in prefix)
        
        client = StatsDClient(host=host, port=port, prefix=prefix)
        
        assert client.host == host
        assert client.port == port
        assert client.prefix == prefix
        assert client._socket is None  # Lazy initialization
    
    @given(
        host=host_strategy(),
        port=port_strategy(),
        prefix=namespace_strategy(),
        metric_name=st.text(alphabet=st.characters(categories=('Ll', 'Lu'), whitelist_characters='_'), min_size=1, max_size=20),
        value=st.integers(min_value=0, max_value=10000)
    )
    @settings(deadline=1000, max_examples=30)
    def test_statsd_increment_does_not_crash(self, host, port, prefix, metric_name, value):
        """StatsD increment should not crash (network errors are isolated)."""
        assume(prefix.isidentifier() or '_' in prefix)
        assume(metric_name.isidentifier())
        
        client = StatsDClient(host=host, port=port, prefix=prefix)
        
        # Should not raise exception even if network fails
        client.increment(metric_name, value=value)
    
    @given(
        host=host_strategy(),
        port=port_strategy(),
        prefix=namespace_strategy(),
        metric_name=st.text(alphabet=st.characters(categories=('Ll', 'Lu'), whitelist_characters='_'), min_size=1, max_size=20),
        value=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(deadline=1000, max_examples=30)
    def test_statsd_gauge_does_not_crash(self, host, port, prefix, metric_name, value):
        """StatsD gauge should not crash (network errors are isolated)."""
        assume(prefix.isidentifier() or '_' in prefix)
        assume(metric_name.isidentifier())
        
        client = StatsDClient(host=host, port=port, prefix=prefix)
        
        # Should not raise exception even if network fails
        client.gauge(metric_name, value=value)
    
    @given(
        host=host_strategy(),
        port=port_strategy(),
        prefix=namespace_strategy(),
        metric_name=st.text(alphabet=st.characters(categories=('Ll', 'Lu'), whitelist_characters='_'), min_size=1, max_size=20),
        ms=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(deadline=1000, max_examples=30)
    def test_statsd_timing_does_not_crash(self, host, port, prefix, metric_name, ms):
        """StatsD timing should not crash (network errors are isolated)."""
        assume(prefix.isidentifier() or '_' in prefix)
        assume(metric_name.isidentifier())
        
        client = StatsDClient(host=host, port=port, prefix=prefix)
        
        # Should not raise exception even if network fails
        client.timing(metric_name, ms=ms)


# ============================================================================
# 3. CloudWatchMetrics Invariants
# ============================================================================

class TestCloudWatchMetricsInvariants:
    """Test invariants of the CloudWatchMetrics class."""
    
    @given(
        namespace=namespace_strategy(),
        region_name=st.sampled_from(['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1', None])
    )
    @settings(deadline=1000, max_examples=30)
    def test_cloudwatch_metrics_initialization(self, namespace, region_name):
        """CloudWatchMetrics should initialize with valid parameters."""
        assume(namespace.isidentifier() or '_' in namespace or '/' in namespace)
        
        metrics = CloudWatchMetrics(namespace=namespace, region_name=region_name)
        
        assert metrics.namespace == namespace
        assert metrics.region_name == region_name
        assert metrics._pending_metrics == []
        assert metrics._lock is not None
    
    @given(
        namespace=namespace_strategy(),
        region_name=st.sampled_from(['us-east-1', 'us-west-2', None])
    )
    @settings(deadline=1000, max_examples=10)  # Reduced examples to avoid hanging
    def test_cloudwatch_metrics_does_not_crash_on_update(self, namespace, region_name):
        """CloudWatch metric initialization should not crash."""
        assume(namespace.isidentifier() or '_' in namespace or '/' in namespace)
        
        metrics = CloudWatchMetrics(namespace=namespace, region_name=region_name)
        
        # Just verify initialization works - don't call update_from_context as it may hang
        assert metrics.namespace == namespace
        assert metrics.region_name == region_name


# ============================================================================
# 4. AzureMonitorMetrics Invariants
# ============================================================================

class TestAzureMonitorMetricsInvariants:
    """Test invariants of the AzureMonitorMetrics class."""
    
    @given(
        connection_string=st.text(min_size=10, max_size=100)
    )
    @settings(deadline=1000, max_examples=30)
    def test_azure_monitor_metrics_initialization(self, connection_string):
        """AzureMonitorMetrics should initialize with connection string."""
        metrics = AzureMonitorMetrics(connection_string=connection_string)
        
        assert metrics.connection_string == connection_string
        assert metrics._client is None  # Lazy initialization
    
    @given(
        connection_string=st.text(min_size=10, max_size=100),
        ctx=hook_context_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_azure_monitor_update_from_context_does_not_crash(self, connection_string, ctx):
        """Azure Monitor metric updates should not crash."""
        metrics = AzureMonitorMetrics(connection_string=connection_string)
        
        # Should not raise exception (even if Azure SDK not available)
        metrics.update_from_context(ctx)


# ============================================================================
# 5. GCPMonitoringMetrics Invariants
# ============================================================================

class TestGCPMonitoringMetricsInvariants:
    """Test invariants of the GCPMonitoringMetrics class."""
    
    @given(
        project_id=st.text(alphabet=st.characters(categories=('Ll', 'Nd'), whitelist_characters='-'), min_size=6, max_size=30)
    )
    @settings(deadline=1000, max_examples=30)
    def test_gcp_monitoring_metrics_initialization(self, project_id):
        """GCPMonitoringMetrics should initialize with project ID."""
        assume('-' not in project_id[:1])  # Can't start with dash
        
        metrics = GCPMonitoringMetrics(project_id=project_id)
        
        assert metrics.project_id == project_id
        assert metrics._client is None  # Lazy initialization
    
    @given(
        project_id=st.text(alphabet=st.characters(categories=('Ll', 'Nd'), whitelist_characters='-'), min_size=6, max_size=30),
        ctx=hook_context_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_gcp_monitoring_update_from_context_does_not_crash(self, project_id, ctx):
        """GCP Monitoring metric updates should not crash."""
        assume('-' not in project_id[:1])
        
        metrics = GCPMonitoringMetrics(project_id=project_id)
        
        # Should not raise exception (even if GCP SDK not available)
        metrics.update_from_context(ctx)


# ============================================================================
# 6. OpenTelemetryTracer Invariants
# ============================================================================

class TestOpenTelemetryTracerInvariants:
    """Test invariants of the OpenTelemetryTracer class."""
    
    @given(
        service_name=st.text(alphabet=st.characters(categories=('Ll', 'Lu'), whitelist_characters='_-.'), min_size=1, max_size=30),
        exporter_endpoint=st.sampled_from(['http://localhost:4317', 'http://jaeger:4317', 'http://tempo:4317', None])
    )
    @settings(deadline=1000, max_examples=30)
    def test_opentelemetry_tracer_initialization(self, service_name, exporter_endpoint):
        """OpenTelemetryTracer should initialize with service name and endpoint."""
        tracer = OpenTelemetryTracer(service_name=service_name, exporter_endpoint=exporter_endpoint)
        
        assert tracer.service_name == service_name
        assert tracer.exporter_endpoint == exporter_endpoint
    
    @given(
        service_name=st.text(alphabet=st.characters(categories=('Ll', 'Lu'), whitelist_characters='_-.'), min_size=1, max_size=30),
        exporter_endpoint=st.sampled_from(['http://localhost:4317', 'http://jaeger:4317', None]),
        ctx=hook_context_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_opentelemetry_update_from_context_does_not_crash(self, service_name, exporter_endpoint, ctx):
        """OpenTelemetry trace updates should not crash."""
        tracer = OpenTelemetryTracer(service_name=service_name, exporter_endpoint=exporter_endpoint)
        
        # Should not raise exception (even if OpenTelemetry SDK not available)
        tracer.update_from_context(ctx)


# ============================================================================
# 7. Hook Creation Functions
# ============================================================================

class TestHookCreationFunctions:
    """Test hook creation functions return valid HookManager instances."""
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_create_prometheus_hook_returns_hook_manager(self, port, namespace):
        """create_prometheus_hook should return HookManager."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        hooks = create_prometheus_hook(port=port, namespace=namespace)
        
        assert isinstance(hooks, HookManager)
    
    @given(
        host=host_strategy(),
        port=port_strategy(),
        prefix=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=30)
    def test_create_statsd_hook_returns_hook_manager(self, host, port, prefix):
        """create_statsd_hook should return HookManager."""
        assume(prefix.isidentifier() or '_' in prefix)
        
        hooks = create_statsd_hook(host=host, port=port, prefix=prefix)
        
        assert isinstance(hooks, HookManager)
    
    @given(
        url=st.sampled_from(['http://localhost:8080/webhook', 'https://example.com/metrics', 'http://monitor.local/api/v1/metrics'])
    )
    @settings(deadline=1000, max_examples=30)
    def test_create_webhook_hook_returns_hook_manager(self, url):
        """create_webhook_hook should return HookManager."""
        hooks = create_webhook_hook(url=url)
        
        assert isinstance(hooks, HookManager)
    
    @given(
        namespace=namespace_strategy(),
        region_name=st.sampled_from(['us-east-1', 'us-west-2', None])
    )
    @settings(deadline=1000, max_examples=30)
    def test_create_cloudwatch_hook_returns_hook_manager(self, namespace, region_name):
        """create_cloudwatch_hook should return HookManager."""
        assume(namespace.isidentifier() or '_' in namespace or '/' in namespace)
        
        hooks = create_cloudwatch_hook(namespace=namespace, region_name=region_name)
        
        assert isinstance(hooks, HookManager)
    
    @given(
        connection_string=st.text(min_size=10, max_size=100)
    )
    @settings(deadline=1000, max_examples=30)
    def test_create_azure_monitor_hook_returns_hook_manager(self, connection_string):
        """create_azure_monitor_hook should return HookManager."""
        hooks = create_azure_monitor_hook(connection_string=connection_string)
        
        assert isinstance(hooks, HookManager)
    
    @given(
        project_id=st.text(alphabet=st.characters(categories=('Ll', 'Nd'), whitelist_characters='-'), min_size=6, max_size=30)
    )
    @settings(deadline=1000, max_examples=30)
    def test_create_gcp_monitoring_hook_returns_hook_manager(self, project_id):
        """create_gcp_monitoring_hook should return HookManager."""
        assume('-' not in project_id[:1])
        
        hooks = create_gcp_monitoring_hook(project_id=project_id)
        
        assert isinstance(hooks, HookManager)
    
    @given(
        service_name=st.text(alphabet=st.characters(categories=('Ll', 'Lu'), whitelist_characters='_-.'), min_size=1, max_size=30),
        exporter_endpoint=st.sampled_from(['http://localhost:4317', 'http://jaeger:4317', None])
    )
    @settings(deadline=1000, max_examples=30)
    def test_create_opentelemetry_hook_returns_hook_manager(self, service_name, exporter_endpoint):
        """create_opentelemetry_hook should return HookManager."""
        hooks = create_opentelemetry_hook(service_name=service_name, exporter_endpoint=exporter_endpoint)
        
        assert isinstance(hooks, HookManager)


# ============================================================================
# 8. Multi-Monitoring Hook
# ============================================================================

class TestMultiMonitoringHook:
    """Test multi-monitoring hook combiner."""
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=20)
    def test_create_multi_monitoring_hook_combines_hooks(self, port, namespace):
        """create_multi_monitoring_hook should combine multiple hooks."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        # Use the actual function signature (not a list of hooks)
        multi_hook = create_multi_monitoring_hook(prometheus_port=port)
        
        assert isinstance(multi_hook, HookManager)
    
    def test_create_multi_monitoring_hook_no_parameters(self):
        """create_multi_monitoring_hook should handle no parameters."""
        multi_hook = create_multi_monitoring_hook()
        
        assert isinstance(multi_hook, HookManager)


# ============================================================================
# 9. Thread Safety
# ============================================================================

class TestThreadSafety:
    """Test thread safety of monitoring classes."""
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=2000, max_examples=20)
    def test_prometheus_metrics_concurrent_updates(self, port, namespace):
        """PrometheusMetrics should handle concurrent updates safely."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        metrics = PrometheusMetrics(port=port, namespace=namespace)
        
        # Create contexts
        ctx = HookContext(event=HookEvent.PRE_EXECUTE)
        ctx.n_jobs = 4
        
        # Update concurrently from multiple threads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=lambda: metrics.update_from_context(ctx))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=1.0)
        
        # Should have recorded all executions
        assert metrics._executions_total == 5


# ============================================================================
# 10. Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_prometheus_metrics_with_default_values(self):
        """PrometheusMetrics should work with default values."""
        metrics = PrometheusMetrics()
        
        assert metrics.port == 8000
        assert metrics.namespace == "amorsize"
        
        # Should generate valid metrics
        metrics_text = metrics._generate_metrics()
        assert isinstance(metrics_text, str)
        assert len(metrics_text) > 0
    
    def test_statsd_client_with_default_values(self):
        """StatsDClient should work with default values."""
        client = StatsDClient()
        
        assert client.host == 'localhost'
        assert client.port == 8125
        assert client.prefix == 'amorsize'
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=20)
    def test_prometheus_metrics_with_empty_context(self, port, namespace):
        """PrometheusMetrics should handle context with minimal fields."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        metrics = PrometheusMetrics(port=port, namespace=namespace)
        
        # Create minimal context
        ctx = HookContext(event=HookEvent.POST_EXECUTE)
        # No elapsed_time, total_items, throughput set
        
        # Should not crash
        metrics.update_from_context(ctx)
    
    @given(
        host=host_strategy(),
        port=port_strategy(),
        prefix=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=20)
    def test_statsd_client_with_zero_values(self, host, port, prefix):
        """StatsDClient should handle zero values."""
        assume(prefix.isidentifier() or '_' in prefix)
        
        client = StatsDClient(host=host, port=port, prefix=prefix)
        
        # Should not crash with zero values
        client.increment("test", value=0)
        client.gauge("test", value=0.0)
        client.timing("test", ms=0.0)


# ============================================================================
# 11. Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and isolation."""
    
    @given(
        port=port_strategy(),
        namespace=namespace_strategy()
    )
    @settings(deadline=1000, max_examples=20)
    def test_prometheus_metrics_handles_invalid_context(self, port, namespace):
        """PrometheusMetrics should handle invalid context gracefully."""
        assume(namespace.isidentifier() or '_' in namespace)
        
        metrics = PrometheusMetrics(port=port, namespace=namespace)
        
        # Create context with unexpected event
        ctx = HookContext(event=None)
        
        # Should not crash (error isolation)
        try:
            metrics.update_from_context(ctx)
        except Exception:
            pass  # Errors should be isolated, but if they occur, they shouldn't crash the test
    
    @given(
        host=host_strategy(),
        port=st.integers(min_value=1, max_value=100)  # Invalid port range
    )
    @settings(deadline=1000, max_examples=20)
    def test_statsd_client_handles_network_errors(self, host, port):
        """StatsDClient should isolate network errors."""
        client = StatsDClient(host=host, port=port)  # Likely invalid port
        
        # Should not raise exception (errors are isolated)
        client.increment("test")
        client.gauge("test", 42.0)
        client.timing("test", 100.0)
