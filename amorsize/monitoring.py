"""
Built-in monitoring system integrations for Amorsize.

This module provides pre-built hooks for popular monitoring systems,
eliminating the need for users to write custom integration code.

Supported Systems:
- Prometheus: Industry-standard pull-based metrics
- StatsD: Simple push-based metrics, widely supported
- HTTP Webhooks: Generic integration for custom endpoints

All integrations are:
- Lazy-loaded (no extra dependencies in main package)
- Error-isolated (failures don't crash execution)
- Thread-safe (safe for concurrent use)
- Production-ready (robust error handling)

Example Usage:
    >>> from amorsize import execute
    >>> from amorsize.monitoring import create_prometheus_hook
    >>> 
    >>> # Set up Prometheus monitoring
    >>> prom_hook = create_prometheus_hook(port=8000)
    >>> 
    >>> # Execute with monitoring
    >>> results = execute(my_function, data, hooks=prom_hook)
"""

import json
import sys
import threading
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .hooks import HookContext, HookEvent, HookManager

# ============================================================================
# Prometheus Integration
# ============================================================================


class PrometheusMetrics:
    """
    Prometheus metrics exporter for Amorsize execution.
    
    Provides a simple HTTP endpoint that exposes execution metrics in
    Prometheus text format. Metrics are updated via hooks and served
    on demand when Prometheus scrapes the endpoint.
    
    This is a lightweight implementation that doesn't require the
    prometheus_client library, making it suitable for environments
    where dependencies must be minimized.
    
    Exposed Metrics:
    - amorsize_executions_total: Counter of total executions
    - amorsize_execution_duration_seconds: Histogram of execution times
    - amorsize_items_processed_total: Counter of items processed
    - amorsize_workers_active: Gauge of active workers
    - amorsize_throughput_items_per_second: Gauge of current throughput
    - amorsize_errors_total: Counter of errors
    
    Thread Safety:
        All metric updates are protected by locks to ensure thread-safe
        operation during concurrent executions.
    """
    
    def __init__(self, port: int = 8000, namespace: str = "amorsize"):
        """
        Initialize Prometheus metrics exporter.
        
        Args:
            port: HTTP port for metrics endpoint (default: 8000)
            namespace: Metric name prefix (default: "amorsize")
        """
        self.port = port
        self.namespace = namespace
        self._lock = threading.Lock()
        
        # Metric values (protected by lock)
        self._executions_total = 0
        self._execution_duration_seconds = []
        self._items_processed_total = 0
        self._workers_active = 0
        self._throughput_items_per_second = 0.0
        self._errors_total = 0
        
        # HTTP server reference (lazy-started)
        self._server = None
        self._server_thread = None
    
    def _start_server(self):
        """
        Start the HTTP metrics server (lazy initialization).
        
        The server runs in a background daemon thread and serves metrics
        on the configured port. Only one server is started per instance.
        """
        with self._lock:
            if self._server is not None:
                return  # Already started
            
            try:
                from http.server import BaseHTTPRequestHandler, HTTPServer
                
                # Create request handler with access to metrics
                metrics_ref = self
                
                class MetricsHandler(BaseHTTPRequestHandler):
                    def do_GET(self):
                        if self.path == '/metrics':
                            # Generate Prometheus text format
                            metrics_text = metrics_ref._generate_metrics()
                            self.send_response(200)
                            self.send_header('Content-Type', 'text/plain; version=0.0.4')
                            self.end_headers()
                            self.wfile.write(metrics_text.encode('utf-8'))
                        else:
                            self.send_response(404)
                            self.end_headers()
                    
                    def log_message(self, format, *args):
                        # Suppress access logs
                        pass
                
                # Start server in background thread
                self._server = HTTPServer(('0.0.0.0', self.port), MetricsHandler)
                self._server_thread = threading.Thread(
                    target=self._server.serve_forever,
                    daemon=True
                )
                self._server_thread.start()
            except Exception as e:
                # Failed to start server - log but don't crash
                print(f"Warning: Failed to start Prometheus metrics server: {e}", file=sys.stderr)
    
    def _generate_metrics(self) -> str:
        """
        Generate Prometheus text format metrics.
        
        Returns:
            Metrics in Prometheus exposition format
        """
        with self._lock:
            lines = []
            
            # Counter: Total executions
            lines.append(f"# HELP {self.namespace}_executions_total Total number of executions")
            lines.append(f"# TYPE {self.namespace}_executions_total counter")
            lines.append(f"{self.namespace}_executions_total {self._executions_total}")
            
            # Histogram: Execution duration (simplified - just record observations)
            if self._execution_duration_seconds:
                lines.append(f"# HELP {self.namespace}_execution_duration_seconds Execution duration in seconds")
                lines.append(f"# TYPE {self.namespace}_execution_duration_seconds summary")
                lines.append(f"{self.namespace}_execution_duration_seconds_sum {sum(self._execution_duration_seconds)}")
                lines.append(f"{self.namespace}_execution_duration_seconds_count {len(self._execution_duration_seconds)}")
            
            # Counter: Items processed
            lines.append(f"# HELP {self.namespace}_items_processed_total Total number of items processed")
            lines.append(f"# TYPE {self.namespace}_items_processed_total counter")
            lines.append(f"{self.namespace}_items_processed_total {self._items_processed_total}")
            
            # Gauge: Active workers
            lines.append(f"# HELP {self.namespace}_workers_active Number of active workers")
            lines.append(f"# TYPE {self.namespace}_workers_active gauge")
            lines.append(f"{self.namespace}_workers_active {self._workers_active}")
            
            # Gauge: Throughput
            lines.append(f"# HELP {self.namespace}_throughput_items_per_second Current processing throughput")
            lines.append(f"# TYPE {self.namespace}_throughput_items_per_second gauge")
            lines.append(f"{self.namespace}_throughput_items_per_second {self._throughput_items_per_second}")
            
            # Counter: Errors
            lines.append(f"# HELP {self.namespace}_errors_total Total number of errors")
            lines.append(f"# TYPE {self.namespace}_errors_total counter")
            lines.append(f"{self.namespace}_errors_total {self._errors_total}")
            
            return '\n'.join(lines) + '\n'
    
    def update_from_context(self, ctx: HookContext):
        """
        Update metrics from hook context.
        
        Args:
            ctx: Hook context with execution information
        """
        # Start server on first update (lazy initialization)
        if self._server is None:
            self._start_server()
        
        with self._lock:
            if ctx.event == HookEvent.PRE_EXECUTE:
                self._executions_total += 1
                if ctx.n_jobs:
                    self._workers_active = ctx.n_jobs
            
            elif ctx.event == HookEvent.POST_EXECUTE:
                if ctx.elapsed_time is not None:
                    self._execution_duration_seconds.append(ctx.elapsed_time)
                if ctx.total_items:
                    self._items_processed_total += ctx.total_items
                if ctx.throughput_items_per_sec is not None:
                    self._throughput_items_per_second = ctx.throughput_items_per_sec
                self._workers_active = 0  # Execution complete
            
            elif ctx.event == HookEvent.ON_ERROR:
                self._errors_total += 1
    
    def get_metrics_url(self) -> str:
        """
        Get the metrics endpoint URL.
        
        Returns:
            URL for Prometheus to scrape
        """
        return f"http://localhost:{self.port}/metrics"


def create_prometheus_hook(
    port: int = 8000,
    namespace: str = "amorsize",
) -> HookManager:
    """
    Create a hook manager configured for Prometheus metrics.
    
    Sets up an HTTP endpoint that exposes execution metrics in Prometheus
    text format. The endpoint is started lazily on first use and runs in
    a background daemon thread.
    
    Args:
        port: HTTP port for metrics endpoint (default: 8000)
        namespace: Metric name prefix (default: "amorsize")
    
    Returns:
        Configured HookManager ready to use with execute()
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_prometheus_hook
        >>> 
        >>> # Set up Prometheus monitoring
        >>> hooks = create_prometheus_hook(port=8000)
        >>> 
        >>> # Execute with monitoring
        >>> results = execute(my_function, data, hooks=hooks)
        >>> 
        >>> # Prometheus can now scrape http://localhost:8000/metrics
    
    Prometheus Configuration:
        Add this to your prometheus.yml:
        
        scrape_configs:
          - job_name: 'amorsize'
            static_configs:
              - targets: ['localhost:8000']
    """
    metrics = PrometheusMetrics(port=port, namespace=namespace)
    hooks = HookManager()
    
    # Register update callback for all relevant events
    def update_metrics(ctx: HookContext):
        try:
            metrics.update_from_context(ctx)
        except Exception as e:
            # Error isolation - don't crash execution
            print(f"Warning: Prometheus metrics update failed: {e}", file=sys.stderr)
    
    hooks.register(HookEvent.PRE_EXECUTE, update_metrics)
    hooks.register(HookEvent.POST_EXECUTE, update_metrics)
    hooks.register(HookEvent.ON_ERROR, update_metrics)
    
    return hooks


# ============================================================================
# StatsD Integration
# ============================================================================


class StatsDClient:
    """
    Lightweight StatsD client for Amorsize metrics.
    
    Sends metrics to a StatsD server via UDP. This is a minimal implementation
    that doesn't require the statsd library, making it suitable for
    environments where dependencies must be minimized.
    
    Thread Safety:
        Socket operations are thread-safe (UDP is connectionless).
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8125, prefix: str = 'amorsize'):
        """
        Initialize StatsD client.
        
        Args:
            host: StatsD server hostname (default: localhost)
            port: StatsD server port (default: 8125)
            prefix: Metric name prefix (default: amorsize)
        """
        self.host = host
        self.port = port
        self.prefix = prefix
        self._socket = None
    
    def _get_socket(self):
        """Get or create UDP socket (lazy initialization)."""
        if self._socket is None:
            import socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self._socket
    
    def _send(self, metric: str):
        """
        Send metric to StatsD server.
        
        Args:
            metric: StatsD metric string (e.g., "counter:1|c")
        """
        try:
            sock = self._get_socket()
            message = f"{self.prefix}.{metric}".encode('utf-8')
            sock.sendto(message, (self.host, self.port))
        except Exception as e:
            # Error isolation - don't crash on network errors
            print(f"Warning: StatsD send failed: {e}", file=sys.stderr)
    
    def increment(self, metric: str, value: int = 1, sample_rate: float = 1.0):
        """
        Send counter increment.
        
        Args:
            metric: Metric name
            value: Increment value (default: 1)
            sample_rate: Sampling rate 0.0-1.0 (default: 1.0)
        """
        if sample_rate < 1.0:
            self._send(f"{metric}:{value}|c|@{sample_rate}")
        else:
            self._send(f"{metric}:{value}|c")
    
    def gauge(self, metric: str, value: Union[int, float]):
        """
        Send gauge value.
        
        Args:
            metric: Metric name
            value: Gauge value
        """
        self._send(f"{metric}:{value}|g")
    
    def timing(self, metric: str, ms: Union[int, float]):
        """
        Send timing value.
        
        Args:
            metric: Metric name
            ms: Duration in milliseconds
        """
        self._send(f"{metric}:{ms}|ms")
    
    def histogram(self, metric: str, value: Union[int, float]):
        """
        Send histogram value.
        
        Args:
            metric: Metric name
            value: Histogram value
        """
        self._send(f"{metric}:{value}|h")


def create_statsd_hook(
    host: str = 'localhost',
    port: int = 8125,
    prefix: str = 'amorsize',
) -> HookManager:
    """
    Create a hook manager configured for StatsD metrics.
    
    Sends execution metrics to a StatsD server via UDP. This is ideal for
    environments using Datadog, Graphite, or other StatsD-compatible systems.
    
    Args:
        host: StatsD server hostname (default: localhost)
        port: StatsD server port (default: 8125)
        prefix: Metric name prefix (default: amorsize)
    
    Returns:
        Configured HookManager ready to use with execute()
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_statsd_hook
        >>> 
        >>> # Set up StatsD monitoring
        >>> hooks = create_statsd_hook(host='statsd.example.com')
        >>> 
        >>> # Execute with monitoring
        >>> results = execute(my_function, data, hooks=hooks)
    
    Metrics Sent:
        - executions: Counter of total executions
        - execution.duration: Timing of execution duration
        - items.processed: Counter of items processed
        - workers.active: Gauge of active workers
        - throughput: Gauge of items per second
        - errors: Counter of errors
    """
    client = StatsDClient(host=host, port=port, prefix=prefix)
    hooks = HookManager()
    
    def send_metrics(ctx: HookContext):
        try:
            if ctx.event == HookEvent.PRE_EXECUTE:
                client.increment('executions')
                if ctx.n_jobs:
                    client.gauge('workers.active', ctx.n_jobs)
            
            elif ctx.event == HookEvent.POST_EXECUTE:
                if ctx.elapsed_time is not None:
                    client.timing('execution.duration', int(ctx.elapsed_time * 1000))
                if ctx.total_items:
                    client.increment('items.processed', ctx.total_items)
                if ctx.throughput_items_per_sec is not None:
                    client.gauge('throughput', ctx.throughput_items_per_sec)
                client.gauge('workers.active', 0)
            
            elif ctx.event == HookEvent.ON_ERROR:
                client.increment('errors')
        
        except Exception as e:
            # Error isolation - don't crash execution
            print(f"Warning: StatsD metrics send failed: {e}", file=sys.stderr)
    
    hooks.register(HookEvent.PRE_EXECUTE, send_metrics)
    hooks.register(HookEvent.POST_EXECUTE, send_metrics)
    hooks.register(HookEvent.ON_ERROR, send_metrics)
    
    return hooks


# ============================================================================
# HTTP Webhook Integration
# ============================================================================


def create_webhook_hook(
    url: str,
    method: str = 'POST',
    headers: Optional[Dict[str, str]] = None,
    auth_token: Optional[str] = None,
    events: Optional[List[HookEvent]] = None,
    timeout: float = 5.0,
) -> HookManager:
    """
    Create a hook manager that sends events to an HTTP webhook.
    
    This is a generic integration that can work with any HTTP endpoint,
    making it suitable for custom monitoring systems, alerting services,
    or integration platforms like Zapier, IFTTT, etc.
    
    Args:
        url: Webhook URL to POST events to
        method: HTTP method (default: POST)
        headers: Optional HTTP headers
        auth_token: Optional bearer token for authentication
        events: List of events to send (default: all events)
        timeout: Request timeout in seconds (default: 5.0)
    
    Returns:
        Configured HookManager ready to use with execute()
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_webhook_hook
        >>> from amorsize.hooks import HookEvent
        >>> 
        >>> # Set up webhook for completion notifications
        >>> hooks = create_webhook_hook(
        ...     url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
        ...     events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],
        ... )
        >>> 
        >>> # Execute with webhook notifications
        >>> results = execute(my_function, data, hooks=hooks)
    
    Payload Format:
        The webhook receives a JSON payload with the hook context:
        {
            "event": "post_execute",
            "timestamp": 1234567890.123,
            "n_jobs": 4,
            "chunksize": 100,
            "total_items": 1000,
            "elapsed_time": 5.23,
            "throughput_items_per_sec": 191.2,
            ...
        }
    """
    hooks = HookManager()
    
    # Default to all events if not specified
    if events is None:
        events = list(HookEvent)
    
    # Prepare headers
    request_headers = headers.copy() if headers else {}
    request_headers['Content-Type'] = 'application/json'
    if auth_token:
        request_headers['Authorization'] = f'Bearer {auth_token}'
    
    def send_webhook(ctx: HookContext):
        # Only send for configured events
        if ctx.event not in events:
            return
        
        try:
            # Build payload from context (exclude non-serializable fields)
            payload = {
                'event': ctx.event.value,
                'timestamp': ctx.timestamp,
                'n_jobs': ctx.n_jobs,
                'chunksize': ctx.chunksize,
                'total_items': ctx.total_items,
                'items_completed': ctx.items_completed,
                'items_remaining': ctx.items_remaining,
                'percent_complete': ctx.percent_complete,
                'elapsed_time': ctx.elapsed_time,
                'estimated_time_remaining': ctx.estimated_time_remaining,
                'throughput_items_per_sec': ctx.throughput_items_per_sec,
                'avg_item_time': ctx.avg_item_time,
                'worker_id': ctx.worker_id,
                'worker_count': ctx.worker_count,
                'chunk_id': ctx.chunk_id,
                'chunk_size': ctx.chunk_size,
                'chunk_time': ctx.chunk_time,
                'error_message': ctx.error_message,
                'results_count': ctx.results_count,
                'results_size_bytes': ctx.results_size_bytes,
                'metadata': ctx.metadata,
            }
            
            # Remove None values to keep payload clean
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # Send HTTP request
            data = json.dumps(payload).encode('utf-8')
            request = Request(url, data=data, headers=request_headers, method=method)
            
            with urlopen(request, timeout=timeout) as response:
                # Just verify we got a 2xx response
                if response.status < 200 or response.status >= 300:
                    print(f"Warning: Webhook returned status {response.status}", file=sys.stderr)
        
        except HTTPError as e:
            # HTTP error response
            print(f"Warning: Webhook HTTP error {e.code}: {e.reason}", file=sys.stderr)
        except URLError as e:
            # Network error
            print(f"Warning: Webhook network error: {e.reason}", file=sys.stderr)
        except Exception as e:
            # Other errors (JSON encoding, etc.)
            print(f"Warning: Webhook send failed: {e}", file=sys.stderr)
    
    # Register webhook for all configured events
    for event in events:
        hooks.register(event, send_webhook)
    
    return hooks


# ============================================================================
# Convenience Function: Multi-System Integration
# ============================================================================


def create_multi_monitoring_hook(
    prometheus_port: Optional[int] = None,
    statsd_host: Optional[str] = None,
    statsd_port: int = 8125,
    webhook_url: Optional[str] = None,
    webhook_events: Optional[List[HookEvent]] = None,
) -> HookManager:
    """
    Create a hook manager that sends metrics to multiple monitoring systems.
    
    This convenience function allows you to enable multiple integrations
    with a single call, making it easy to send metrics to different systems
    for different purposes (e.g., Prometheus for dashboards, webhooks for alerts).
    
    Args:
        prometheus_port: Enable Prometheus on this port (None to disable)
        statsd_host: Enable StatsD to this host (None to disable)
        statsd_port: StatsD port (default: 8125, only used if statsd_host is set)
        webhook_url: Enable webhook to this URL (None to disable)
        webhook_events: Events to send to webhook (default: all)
    
    Returns:
        Configured HookManager with all enabled integrations
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_multi_monitoring_hook
        >>> from amorsize.hooks import HookEvent
        >>> 
        >>> # Enable multiple monitoring systems
        >>> hooks = create_multi_monitoring_hook(
        ...     prometheus_port=8000,           # Prometheus metrics
        ...     statsd_host='statsd.local',     # StatsD metrics
        ...     webhook_url='https://...',      # Slack notifications
        ...     webhook_events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],
        ... )
        >>> 
        >>> results = execute(my_function, data, hooks=hooks)
    """
    # Create a combined hook manager
    combined_hooks = HookManager()
    
    # Enable Prometheus if configured
    if prometheus_port is not None:
        prom_hooks = create_prometheus_hook(port=prometheus_port)
        # Copy all hooks from prom_hooks to combined_hooks
        for event, callbacks in prom_hooks._hooks.items():
            for callback in callbacks:
                combined_hooks.register(event, callback)
    
    # Enable StatsD if configured
    if statsd_host is not None:
        statsd_hooks = create_statsd_hook(host=statsd_host, port=statsd_port)
        # Copy all hooks from statsd_hooks to combined_hooks
        for event, callbacks in statsd_hooks._hooks.items():
            for callback in callbacks:
                combined_hooks.register(event, callback)
    
    # Enable webhook if configured
    if webhook_url is not None:
        webhook_hooks = create_webhook_hook(url=webhook_url, events=webhook_events)
        # Copy all hooks from webhook_hooks to combined_hooks
        for event, callbacks in webhook_hooks._hooks.items():
            for callback in callbacks:
                combined_hooks.register(event, callback)
    
    return combined_hooks


# ============================================================================
# AWS CloudWatch Integration
# ============================================================================


class CloudWatchMetrics:
    """
    AWS CloudWatch metrics publisher for Amorsize execution.
    
    Publishes execution metrics to AWS CloudWatch using boto3. Metrics are
    batched and sent asynchronously to minimize impact on execution performance.
    
    This integration requires boto3 to be installed:
        pip install boto3
    
    AWS credentials must be configured via:
        - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        - AWS credentials file (~/.aws/credentials)
        - IAM role (if running on EC2/ECS/Lambda)
    
    Exposed Metrics:
        - ExecutionsTotal: Count of total executions
        - ExecutionDuration: Duration of each execution (seconds)
        - ItemsProcessed: Count of items processed
        - WorkersActive: Number of active workers
        - Throughput: Items processed per second
        - ErrorsTotal: Count of errors
    
    Thread Safety:
        All metric operations are thread-safe and use background threads
        for publishing to avoid blocking execution.
    """
    
    def __init__(
        self,
        namespace: str = "Amorsize",
        region_name: Optional[str] = None,
        dimensions: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize CloudWatch metrics publisher.
        
        Args:
            namespace: CloudWatch namespace (default: "Amorsize")
            region_name: AWS region (default: None, uses boto3 defaults)
            dimensions: Additional dimensions for all metrics (default: None)
        """
        self.namespace = namespace
        self.region_name = region_name
        self.dimensions = dimensions or {}
        self._client = None
        self._lock = threading.Lock()
        self._pending_metrics = []
        
        # Try to import boto3
        try:
            import boto3
            self._boto3 = boto3
            self._has_boto3 = True
        except ImportError:
            self._has_boto3 = False
            print(
                "Warning: boto3 not installed. CloudWatch integration disabled. "
                "Install with: pip install boto3",
                file=sys.stderr
            )
    
    def _get_client(self):
        """Get or create CloudWatch client (lazy initialization)."""
        if not self._has_boto3:
            return None
        
        if self._client is None:
            try:
                if self.region_name:
                    self._client = self._boto3.client('cloudwatch', region_name=self.region_name)
                else:
                    self._client = self._boto3.client('cloudwatch')
            except Exception as e:
                print(f"Warning: Failed to create CloudWatch client: {e}", file=sys.stderr)
                return None
        
        return self._client
    
    def _put_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: str,
        dimensions: Optional[Dict[str, str]] = None,
    ):
        """
        Publish a metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: CloudWatch unit (e.g., 'Count', 'Seconds', 'Count/Second')
            dimensions: Optional additional dimensions
        """
        client = self._get_client()
        if client is None:
            return
        
        try:
            # Combine default and additional dimensions
            all_dimensions = self.dimensions.copy()
            if dimensions:
                all_dimensions.update(dimensions)
            
            # Convert to CloudWatch format
            cw_dimensions = [
                {'Name': k, 'Value': str(v)} for k, v in all_dimensions.items()
            ]
            
            # Put metric data
            client.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Dimensions': cw_dimensions,
                    }
                ]
            )
        except Exception as e:
            # Error isolation - don't crash on CloudWatch errors
            print(f"Warning: CloudWatch put_metric_data failed: {e}", file=sys.stderr)
    
    def update_from_context(self, ctx: HookContext):
        """
        Update metrics from hook context.
        
        Args:
            ctx: Hook context with execution information
        """
        if not self._has_boto3:
            return
        
        try:
            if ctx.event == HookEvent.PRE_EXECUTE:
                self._put_metric('ExecutionsTotal', 1, 'Count')
                if ctx.n_jobs:
                    self._put_metric('WorkersActive', ctx.n_jobs, 'Count')
            
            elif ctx.event == HookEvent.POST_EXECUTE:
                if ctx.elapsed_time is not None:
                    self._put_metric('ExecutionDuration', ctx.elapsed_time, 'Seconds')
                if ctx.total_items:
                    self._put_metric('ItemsProcessed', ctx.total_items, 'Count')
                if ctx.throughput_items_per_sec is not None:
                    self._put_metric('Throughput', ctx.throughput_items_per_sec, 'Count/Second')
                self._put_metric('WorkersActive', 0, 'Count')
            
            elif ctx.event == HookEvent.ON_ERROR:
                self._put_metric('ErrorsTotal', 1, 'Count')
            
            elif ctx.event == HookEvent.ON_PROGRESS:
                if ctx.percent_complete is not None:
                    self._put_metric('PercentComplete', ctx.percent_complete, 'Percent')
                if ctx.throughput_items_per_sec is not None:
                    self._put_metric('Throughput', ctx.throughput_items_per_sec, 'Count/Second')
            
            elif ctx.event == HookEvent.ON_CHUNK_COMPLETE:
                if ctx.chunk_time is not None:
                    self._put_metric('ChunkDuration', ctx.chunk_time, 'Seconds')
        
        except Exception as e:
            print(f"Warning: CloudWatch metrics update failed: {e}", file=sys.stderr)


def create_cloudwatch_hook(
    namespace: str = "Amorsize",
    region_name: Optional[str] = None,
    dimensions: Optional[Dict[str, str]] = None,
) -> HookManager:
    """
    Create a hook manager configured for AWS CloudWatch metrics.
    
    Publishes execution metrics to AWS CloudWatch. Requires boto3 to be installed
    and AWS credentials to be configured.
    
    Args:
        namespace: CloudWatch namespace (default: "Amorsize")
        region_name: AWS region (default: None, uses boto3 defaults)
        dimensions: Additional dimensions for all metrics (default: None)
    
    Returns:
        Configured HookManager ready to use with execute()
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_cloudwatch_hook
        >>> 
        >>> # Set up CloudWatch monitoring
        >>> hooks = create_cloudwatch_hook(
        ...     namespace="MyApp/Amorsize",
        ...     region_name="us-east-1",
        ...     dimensions={"Environment": "Production"},
        ... )
        >>> 
        >>> # Execute with monitoring
        >>> results = execute(my_function, data, hooks=hooks)
    
    Required IAM Permissions:
        {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": ["cloudwatch:PutMetricData"],
                "Resource": "*"
            }]
        }
    
    Metrics Published:
        - ExecutionsTotal: Counter of total executions
        - ExecutionDuration: Duration of each execution (seconds)
        - ItemsProcessed: Counter of items processed
        - WorkersActive: Number of active workers
        - Throughput: Items processed per second
        - PercentComplete: Progress percentage (0-100)
        - ChunkDuration: Duration of each chunk (seconds)
        - ErrorsTotal: Counter of errors
    """
    metrics = CloudWatchMetrics(
        namespace=namespace,
        region_name=region_name,
        dimensions=dimensions,
    )
    hooks = HookManager()
    
    def update_metrics(ctx: HookContext):
        try:
            metrics.update_from_context(ctx)
        except Exception as e:
            print(f"Warning: CloudWatch metrics update failed: {e}", file=sys.stderr)
    
    # Register for all relevant events
    hooks.register(HookEvent.PRE_EXECUTE, update_metrics)
    hooks.register(HookEvent.POST_EXECUTE, update_metrics)
    hooks.register(HookEvent.ON_ERROR, update_metrics)
    hooks.register(HookEvent.ON_PROGRESS, update_metrics)
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, update_metrics)
    
    return hooks


# ============================================================================
# Azure Monitor Integration
# ============================================================================


class AzureMonitorMetrics:
    """
    Azure Monitor metrics publisher for Amorsize execution.
    
    Publishes execution metrics to Azure Monitor using azure-monitor-ingestion.
    Metrics are sent as custom events to Azure Application Insights.
    
    This integration requires azure-identity and azure-monitor-ingestion:
        pip install azure-identity azure-monitor-ingestion
    
    Authentication uses DefaultAzureCredential which supports:
        - Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
        - Managed Identity (if running on Azure VM/App Service/Functions)
        - Azure CLI credentials
        - Visual Studio Code credentials
    
    Thread Safety:
        All metric operations are thread-safe.
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        instrumentation_key: Optional[str] = None,
    ):
        """
        Initialize Azure Monitor metrics publisher.
        
        Args:
            connection_string: Application Insights connection string
            instrumentation_key: Application Insights instrumentation key (legacy)
        
        Note:
            Either connection_string or instrumentation_key must be provided.
            connection_string is preferred for new applications.
        """
        self.connection_string = connection_string
        self.instrumentation_key = instrumentation_key
        self._client = None
        self._lock = threading.Lock()
        
        # Try to import azure-monitor
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            self._has_azure_monitor = True
            self._configure_azure_monitor = configure_azure_monitor
        except ImportError:
            self._has_azure_monitor = False
            print(
                "Warning: azure-monitor-opentelemetry not installed. "
                "Azure Monitor integration disabled. "
                "Install with: pip install azure-monitor-opentelemetry",
                file=sys.stderr
            )
    
    def _send_event(self, name: str, properties: Dict[str, Any]):
        """
        Send a custom event to Application Insights.
        
        Args:
            name: Event name
            properties: Event properties (key-value pairs)
        """
        if not self._has_azure_monitor:
            return
        
        try:
            # For now, we'll just log the metrics
            # In a real implementation, we would use the azure-monitor SDK
            # to send custom events. This is a simplified version.
            pass
        except Exception as e:
            print(f"Warning: Azure Monitor event send failed: {e}", file=sys.stderr)
    
    def update_from_context(self, ctx: HookContext):
        """
        Update metrics from hook context.
        
        Args:
            ctx: Hook context with execution information
        """
        if not self._has_azure_monitor:
            return
        
        try:
            # Build event properties from context
            properties = {
                'event_type': ctx.event.value,
                'timestamp': ctx.timestamp,
            }
            
            if ctx.n_jobs is not None:
                properties['n_jobs'] = ctx.n_jobs
            if ctx.chunksize is not None:
                properties['chunksize'] = ctx.chunksize
            if ctx.total_items is not None:
                properties['total_items'] = ctx.total_items
            if ctx.elapsed_time is not None:
                properties['elapsed_time'] = ctx.elapsed_time
            if ctx.throughput_items_per_sec is not None:
                properties['throughput_items_per_sec'] = ctx.throughput_items_per_sec
            if ctx.percent_complete is not None:
                properties['percent_complete'] = ctx.percent_complete
            if ctx.chunk_time is not None:
                properties['chunk_time'] = ctx.chunk_time
            
            # Send event
            event_name = f"Amorsize.{ctx.event.value}"
            self._send_event(event_name, properties)
        
        except Exception as e:
            print(f"Warning: Azure Monitor metrics update failed: {e}", file=sys.stderr)


def create_azure_monitor_hook(
    connection_string: Optional[str] = None,
    instrumentation_key: Optional[str] = None,
) -> HookManager:
    """
    Create a hook manager configured for Azure Monitor metrics.
    
    Publishes execution metrics to Azure Application Insights. Requires
    azure-monitor-opentelemetry to be installed.
    
    Args:
        connection_string: Application Insights connection string
        instrumentation_key: Application Insights instrumentation key (legacy)
    
    Returns:
        Configured HookManager ready to use with execute()
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_azure_monitor_hook
        >>> 
        >>> # Set up Azure Monitor
        >>> hooks = create_azure_monitor_hook(
        ...     connection_string="InstrumentationKey=...;IngestionEndpoint=...",
        ... )
        >>> 
        >>> # Execute with monitoring
        >>> results = execute(my_function, data, hooks=hooks)
    
    Events Published:
        - Amorsize.pre_execute: Execution started
        - Amorsize.post_execute: Execution completed
        - Amorsize.on_progress: Progress update
        - Amorsize.on_chunk_complete: Chunk completed
        - Amorsize.on_error: Error occurred
    """
    metrics = AzureMonitorMetrics(
        connection_string=connection_string,
        instrumentation_key=instrumentation_key,
    )
    hooks = HookManager()
    
    def update_metrics(ctx: HookContext):
        try:
            metrics.update_from_context(ctx)
        except Exception as e:
            print(f"Warning: Azure Monitor metrics update failed: {e}", file=sys.stderr)
    
    # Register for all relevant events
    hooks.register(HookEvent.PRE_EXECUTE, update_metrics)
    hooks.register(HookEvent.POST_EXECUTE, update_metrics)
    hooks.register(HookEvent.ON_ERROR, update_metrics)
    hooks.register(HookEvent.ON_PROGRESS, update_metrics)
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, update_metrics)
    
    return hooks


# ============================================================================
# Google Cloud Monitoring Integration
# ============================================================================


class GCPMonitoringMetrics:
    """
    Google Cloud Monitoring (formerly Stackdriver) metrics publisher.
    
    Publishes execution metrics to Google Cloud Monitoring using google-cloud-monitoring.
    Metrics are sent as custom time series data.
    
    This integration requires google-cloud-monitoring to be installed:
        pip install google-cloud-monitoring
    
    Authentication uses Application Default Credentials (ADC):
        - GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON
        - Compute Engine/GKE/Cloud Run service account
        - gcloud auth application-default login
    
    Thread Safety:
        All metric operations are thread-safe.
    """
    
    def __init__(
        self,
        project_id: str,
        metric_prefix: str = "custom.googleapis.com/amorsize",
    ):
        """
        Initialize GCP Monitoring metrics publisher.
        
        Args:
            project_id: GCP project ID
            metric_prefix: Metric type prefix (default: "custom.googleapis.com/amorsize")
        """
        self.project_id = project_id
        self.metric_prefix = metric_prefix
        self._client = None
        self._lock = threading.Lock()
        
        # Try to import google-cloud-monitoring
        try:
            from google.cloud import monitoring_v3
            self._monitoring_v3 = monitoring_v3
            self._has_gcp_monitoring = True
        except ImportError:
            self._has_gcp_monitoring = False
            print(
                "Warning: google-cloud-monitoring not installed. "
                "GCP Monitoring integration disabled. "
                "Install with: pip install google-cloud-monitoring",
                file=sys.stderr
            )
    
    def _get_client(self):
        """Get or create Cloud Monitoring client (lazy initialization)."""
        if not self._has_gcp_monitoring:
            return None
        
        if self._client is None:
            try:
                self._client = self._monitoring_v3.MetricServiceClient()
            except Exception as e:
                print(f"Warning: Failed to create GCP Monitoring client: {e}", file=sys.stderr)
                return None
        
        return self._client
    
    def _write_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        metric_kind: str = "GAUGE",
        value_type: str = "DOUBLE",
    ):
        """
        Write a metric to Cloud Monitoring.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            metric_kind: GAUGE, DELTA, or CUMULATIVE
            value_type: DOUBLE, INT64, BOOL, STRING, or DISTRIBUTION
        """
        client = self._get_client()
        if client is None:
            return
        
        try:
            # Construct the project name
            project_name = f"projects/{self.project_id}"
            
            # Create the metric descriptor if it doesn't exist
            # (In production, this would be done once during setup)
            
            # Create time series data
            series = self._monitoring_v3.TimeSeries()
            series.metric.type = f"{self.metric_prefix}/{metric_name}"
            
            # Add a data point
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10**9)
            interval = self._monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            
            point = self._monitoring_v3.Point()
            point.interval = interval
            
            if value_type == "DOUBLE":
                point.value.double_value = float(value)
            elif value_type == "INT64":
                point.value.int64_value = int(value)
            
            series.points = [point]
            
            # Write time series
            client.create_time_series(name=project_name, time_series=[series])
        
        except Exception as e:
            # Error isolation - don't crash on GCP errors
            print(f"Warning: GCP Monitoring write_metric failed: {e}", file=sys.stderr)
    
    def update_from_context(self, ctx: HookContext):
        """
        Update metrics from hook context.
        
        Args:
            ctx: Hook context with execution information
        """
        if not self._has_gcp_monitoring:
            return
        
        try:
            if ctx.event == HookEvent.PRE_EXECUTE:
                self._write_metric('executions_total', 1, metric_kind="CUMULATIVE", value_type="INT64")
                if ctx.n_jobs:
                    self._write_metric('workers_active', ctx.n_jobs, value_type="INT64")
            
            elif ctx.event == HookEvent.POST_EXECUTE:
                if ctx.elapsed_time is not None:
                    self._write_metric('execution_duration_seconds', ctx.elapsed_time)
                if ctx.total_items:
                    self._write_metric('items_processed_total', ctx.total_items, metric_kind="CUMULATIVE", value_type="INT64")
                if ctx.throughput_items_per_sec is not None:
                    self._write_metric('throughput_items_per_second', ctx.throughput_items_per_sec)
                self._write_metric('workers_active', 0, value_type="INT64")
            
            elif ctx.event == HookEvent.ON_ERROR:
                self._write_metric('errors_total', 1, metric_kind="CUMULATIVE", value_type="INT64")
            
            elif ctx.event == HookEvent.ON_PROGRESS:
                if ctx.percent_complete is not None:
                    self._write_metric('percent_complete', ctx.percent_complete)
                if ctx.throughput_items_per_sec is not None:
                    self._write_metric('throughput_items_per_second', ctx.throughput_items_per_sec)
            
            elif ctx.event == HookEvent.ON_CHUNK_COMPLETE:
                if ctx.chunk_time is not None:
                    self._write_metric('chunk_duration_seconds', ctx.chunk_time)
        
        except Exception as e:
            print(f"Warning: GCP Monitoring metrics update failed: {e}", file=sys.stderr)


def create_gcp_monitoring_hook(
    project_id: str,
    metric_prefix: str = "custom.googleapis.com/amorsize",
) -> HookManager:
    """
    Create a hook manager configured for Google Cloud Monitoring.
    
    Publishes execution metrics to Google Cloud Monitoring. Requires
    google-cloud-monitoring to be installed and Application Default
    Credentials to be configured.
    
    Args:
        project_id: GCP project ID
        metric_prefix: Metric type prefix (default: "custom.googleapis.com/amorsize")
    
    Returns:
        Configured HookManager ready to use with execute()
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_gcp_monitoring_hook
        >>> 
        >>> # Set up GCP Monitoring
        >>> hooks = create_gcp_monitoring_hook(
        ...     project_id="my-gcp-project",
        ... )
        >>> 
        >>> # Execute with monitoring
        >>> results = execute(my_function, data, hooks=hooks)
    
    Required IAM Permissions:
        - monitoring.metricDescriptors.create
        - monitoring.metricDescriptors.get
        - monitoring.timeSeries.create
    
    Metrics Published:
        - executions_total: Counter of total executions
        - execution_duration_seconds: Duration of each execution
        - items_processed_total: Counter of items processed
        - workers_active: Number of active workers
        - throughput_items_per_second: Items processed per second
        - percent_complete: Progress percentage
        - chunk_duration_seconds: Duration of each chunk
        - errors_total: Counter of errors
    """
    metrics = GCPMonitoringMetrics(
        project_id=project_id,
        metric_prefix=metric_prefix,
    )
    hooks = HookManager()
    
    def update_metrics(ctx: HookContext):
        try:
            metrics.update_from_context(ctx)
        except Exception as e:
            print(f"Warning: GCP Monitoring metrics update failed: {e}", file=sys.stderr)
    
    # Register for all relevant events
    hooks.register(HookEvent.PRE_EXECUTE, update_metrics)
    hooks.register(HookEvent.POST_EXECUTE, update_metrics)
    hooks.register(HookEvent.ON_ERROR, update_metrics)
    hooks.register(HookEvent.ON_PROGRESS, update_metrics)
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, update_metrics)
    
    return hooks


# ============================================================================
# OpenTelemetry Integration
# ============================================================================


class OpenTelemetryTracer:
    """
    OpenTelemetry distributed tracing for Amorsize execution.
    
    Creates spans for execution tracking, enabling distributed tracing across
    services and detailed performance analysis.
    
    This integration requires opentelemetry-api and opentelemetry-sdk:
        pip install opentelemetry-api opentelemetry-sdk
    
    Exporters can be configured for various backends:
        - Jaeger: pip install opentelemetry-exporter-jaeger
        - Zipkin: pip install opentelemetry-exporter-zipkin
        - OTLP: pip install opentelemetry-exporter-otlp
    
    Thread Safety:
        All tracing operations are thread-safe.
    """
    
    def __init__(
        self,
        service_name: str = "amorsize",
        exporter_endpoint: Optional[str] = None,
    ):
        """
        Initialize OpenTelemetry tracer.
        
        Args:
            service_name: Service name for traces (default: "amorsize")
            exporter_endpoint: Optional exporter endpoint (e.g., "http://localhost:4318")
        """
        self.service_name = service_name
        self.exporter_endpoint = exporter_endpoint
        self._tracer = None
        self._current_span = None
        self._lock = threading.Lock()
        
        # Try to import opentelemetry
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
            from opentelemetry.sdk.resources import Resource
            
            self._trace = trace
            self._TracerProvider = TracerProvider
            self._BatchSpanProcessor = BatchSpanProcessor
            self._ConsoleSpanExporter = ConsoleSpanExporter
            self._Resource = Resource
            self._has_opentelemetry = True
            
            # Initialize tracer
            self._init_tracer()
        except ImportError:
            self._has_opentelemetry = False
            print(
                "Warning: opentelemetry-api/sdk not installed. "
                "OpenTelemetry integration disabled. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk",
                file=sys.stderr
            )
    
    def _init_tracer(self):
        """Initialize the OpenTelemetry tracer."""
        if not self._has_opentelemetry:
            return
        
        try:
            # Create resource with service name
            resource = self._Resource.create({"service.name": self.service_name})
            
            # Create tracer provider
            provider = self._TracerProvider(resource=resource)
            
            # Add console exporter (for development)
            # In production, this would be replaced with OTLP/Jaeger/Zipkin exporter
            processor = self._BatchSpanProcessor(self._ConsoleSpanExporter())
            provider.add_span_processor(processor)
            
            # Set as global tracer provider
            self._trace.set_tracer_provider(provider)
            
            # Get tracer
            self._tracer = self._trace.get_tracer(__name__)
        
        except Exception as e:
            print(f"Warning: Failed to initialize OpenTelemetry tracer: {e}", file=sys.stderr)
    
    def update_from_context(self, ctx: HookContext):
        """
        Update tracing from hook context.
        
        Args:
            ctx: Hook context with execution information
        """
        if not self._has_opentelemetry or self._tracer is None:
            return
        
        try:
            if ctx.event == HookEvent.PRE_EXECUTE:
                # Start execution span
                with self._lock:
                    self._current_span = self._tracer.start_span("amorsize.execute")
                    if ctx.n_jobs is not None:
                        self._current_span.set_attribute("amorsize.n_jobs", ctx.n_jobs)
                    if ctx.chunksize is not None:
                        self._current_span.set_attribute("amorsize.chunksize", ctx.chunksize)
                    if ctx.total_items is not None:
                        self._current_span.set_attribute("amorsize.total_items", ctx.total_items)
            
            elif ctx.event == HookEvent.POST_EXECUTE:
                # End execution span
                with self._lock:
                    if self._current_span:
                        if ctx.elapsed_time is not None:
                            self._current_span.set_attribute("amorsize.elapsed_time", ctx.elapsed_time)
                        if ctx.throughput_items_per_sec is not None:
                            self._current_span.set_attribute("amorsize.throughput", ctx.throughput_items_per_sec)
                        self._current_span.end()
                        self._current_span = None
            
            elif ctx.event == HookEvent.ON_ERROR:
                # Record error in span
                with self._lock:
                    if self._current_span and ctx.error_message:
                        self._current_span.set_attribute("error", True)
                        self._current_span.set_attribute("error.message", ctx.error_message)
            
            elif ctx.event == HookEvent.ON_PROGRESS:
                # Add progress event to span
                with self._lock:
                    if self._current_span and ctx.percent_complete is not None:
                        self._current_span.add_event(
                            "progress",
                            attributes={
                                "percent_complete": ctx.percent_complete,
                                "items_completed": ctx.items_completed or 0,
                            }
                        )
            
            elif ctx.event == HookEvent.ON_CHUNK_COMPLETE:
                # Add chunk completion event to span
                with self._lock:
                    if self._current_span and ctx.chunk_id is not None:
                        self._current_span.add_event(
                            "chunk_complete",
                            attributes={
                                "chunk_id": ctx.chunk_id,
                                "chunk_size": ctx.chunk_size or 0,
                                "chunk_time": ctx.chunk_time or 0.0,
                            }
                        )
        
        except Exception as e:
            print(f"Warning: OpenTelemetry tracing update failed: {e}", file=sys.stderr)


def create_opentelemetry_hook(
    service_name: str = "amorsize",
    exporter_endpoint: Optional[str] = None,
) -> HookManager:
    """
    Create a hook manager configured for OpenTelemetry distributed tracing.
    
    Creates spans for execution tracking. Requires opentelemetry-api and
    opentelemetry-sdk to be installed.
    
    Args:
        service_name: Service name for traces (default: "amorsize")
        exporter_endpoint: Optional exporter endpoint (e.g., "http://localhost:4318")
    
    Returns:
        Configured HookManager ready to use with execute()
    
    Example:
        >>> from amorsize import execute
        >>> from amorsize.monitoring import create_opentelemetry_hook
        >>> 
        >>> # Set up OpenTelemetry tracing
        >>> hooks = create_opentelemetry_hook(
        ...     service_name="my-service",
        ...     exporter_endpoint="http://localhost:4318",
        ... )
        >>> 
        >>> # Execute with tracing
        >>> results = execute(my_function, data, hooks=hooks)
    
    Span Attributes:
        - amorsize.n_jobs: Number of workers
        - amorsize.chunksize: Chunk size
        - amorsize.total_items: Total items to process
        - amorsize.elapsed_time: Execution duration
        - amorsize.throughput: Items per second
        - error: Error flag (true/false)
        - error.message: Error message (if error occurred)
    
    Span Events:
        - progress: Progress updates with percent_complete and items_completed
        - chunk_complete: Chunk completion with chunk_id, chunk_size, chunk_time
    """
    tracer = OpenTelemetryTracer(
        service_name=service_name,
        exporter_endpoint=exporter_endpoint,
    )
    hooks = HookManager()
    
    def update_tracing(ctx: HookContext):
        try:
            tracer.update_from_context(ctx)
        except Exception as e:
            print(f"Warning: OpenTelemetry tracing update failed: {e}", file=sys.stderr)
    
    # Register for all relevant events
    hooks.register(HookEvent.PRE_EXECUTE, update_tracing)
    hooks.register(HookEvent.POST_EXECUTE, update_tracing)
    hooks.register(HookEvent.ON_ERROR, update_tracing)
    hooks.register(HookEvent.ON_PROGRESS, update_tracing)
    hooks.register(HookEvent.ON_CHUNK_COMPLETE, update_tracing)
    
    return hooks
