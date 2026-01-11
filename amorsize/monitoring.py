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
                if ctx.elapsed_time > 0:
                    self._execution_duration_seconds.append(ctx.elapsed_time)
                if ctx.total_items:
                    self._items_processed_total += ctx.total_items
                if ctx.throughput_items_per_sec > 0:
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
                if ctx.elapsed_time > 0:
                    client.timing('execution.duration', int(ctx.elapsed_time * 1000))
                if ctx.total_items:
                    client.increment('items.processed', ctx.total_items)
                if ctx.throughput_items_per_sec > 0:
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
