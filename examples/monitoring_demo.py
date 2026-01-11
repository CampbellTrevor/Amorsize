"""
Monitoring Integrations Demo - Complete Guide to Built-in Monitoring

This demo showcases all three monitoring integrations available in Amorsize:
1. Prometheus - Industry standard, pull-based metrics
2. StatsD - Simple push-based metrics for Datadog, Graphite, etc.
3. HTTP Webhooks - Generic integration for custom systems

Each integration is production-ready, thread-safe, and requires zero
additional dependencies beyond the main Amorsize package.
"""

import time
from amorsize import execute
from amorsize.monitoring import (
    create_prometheus_hook,
    create_statsd_hook,
    create_webhook_hook,
    create_multi_monitoring_hook,
)
from amorsize.hooks import HookEvent


# ============================================================================
# Demo 1: Prometheus Integration
# ============================================================================

def demo_prometheus():
    """
    Demo: Prometheus metrics integration.
    
    Prometheus is ideal for:
    - Time-series metrics and dashboards
    - Alerting based on metric thresholds
    - Long-term metric retention
    - Complex metric queries (PromQL)
    
    The integration provides:
    - HTTP metrics endpoint on configurable port
    - Standard Prometheus text format
    - Automatic metric collection during execution
    - No prometheus_client dependency required
    """
    print("\n" + "="*70)
    print("Demo 1: Prometheus Integration")
    print("="*70)
    
    # Create Prometheus hook (starts HTTP server on port 8000)
    hooks = create_prometheus_hook(port=8000, namespace="amorsize_demo")
    
    print("\nPrometheus metrics endpoint started on http://localhost:8000/metrics")
    print("You can now configure Prometheus to scrape this endpoint.")
    print("\nAdd to your prometheus.yml:")
    print("  scrape_configs:")
    print("    - job_name: 'amorsize'")
    print("      static_configs:")
    print("        - targets: ['localhost:8000']")
    
    # Example workload
    def compute_fibonacci(n):
        """Compute nth Fibonacci number (CPU-intensive)."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b
    
    # Execute with Prometheus monitoring
    print("\nExecuting workload with Prometheus monitoring...")
    data = range(1, 101)  # Fibonacci numbers 1-100
    results = execute(compute_fibonacci, data, hooks=hooks)
    
    print(f"✓ Processed {len(list(results))} items")
    print("\nMetrics available at: http://localhost:8000/metrics")
    print("Try: curl http://localhost:8000/metrics")
    print("\nExposed metrics:")
    print("  - amorsize_demo_executions_total")
    print("  - amorsize_demo_execution_duration_seconds")
    print("  - amorsize_demo_items_processed_total")
    print("  - amorsize_demo_workers_active")
    print("  - amorsize_demo_throughput_items_per_second")
    print("  - amorsize_demo_errors_total")


# ============================================================================
# Demo 2: StatsD Integration
# ============================================================================

def demo_statsd():
    """
    Demo: StatsD metrics integration.
    
    StatsD is ideal for:
    - Datadog monitoring
    - Graphite metrics collection
    - Simple UDP-based metrics
    - Low-latency metric submission
    
    The integration provides:
    - UDP metrics submission (fire-and-forget)
    - Standard StatsD wire format
    - Support for counters, gauges, timings, histograms
    - No statsd library dependency required
    """
    print("\n" + "="*70)
    print("Demo 2: StatsD Integration")
    print("="*70)
    
    # Create StatsD hook (sends to localhost:8125 by default)
    # For Datadog: hooks = create_statsd_hook(host='localhost', port=8125, prefix='amorsize')
    # For Graphite: hooks = create_statsd_hook(host='graphite.example.com', port=8125, prefix='amorsize')
    hooks = create_statsd_hook(
        host='localhost',
        port=8125,
        prefix='amorsize_demo'
    )
    
    print("\nStatsD metrics will be sent to localhost:8125")
    print("Make sure your StatsD server (Datadog agent, Graphite, etc.) is running.")
    
    # Example workload
    def process_text(text):
        """Simulate text processing."""
        return text.upper()
    
    # Execute with StatsD monitoring
    print("\nExecuting workload with StatsD monitoring...")
    data = ["hello", "world", "from", "amorsize"] * 25  # 100 items
    results = execute(process_text, data, hooks=hooks)
    
    print(f"✓ Processed {len(list(results))} items")
    print("\nMetrics sent to StatsD:")
    print("  - amorsize_demo.executions:1|c")
    print("  - amorsize_demo.execution.duration:<time>|ms")
    print("  - amorsize_demo.items.processed:<count>|c")
    print("  - amorsize_demo.workers.active:<count>|g")
    print("  - amorsize_demo.throughput:<rate>|g")
    
    # For Datadog, these metrics will appear as:
    # - amorsize_demo.executions
    # - amorsize_demo.execution.duration
    # - amorsize_demo.items.processed
    # - amorsize_demo.workers.active
    # - amorsize_demo.throughput


# ============================================================================
# Demo 3: HTTP Webhook Integration
# ============================================================================

def demo_webhook():
    """
    Demo: HTTP webhook integration.
    
    Webhooks are ideal for:
    - Slack/Teams notifications
    - Custom alerting systems
    - Integration with Zapier, IFTTT, etc.
    - Logging to external systems
    
    The integration provides:
    - JSON payload with execution context
    - Configurable HTTP method and headers
    - Bearer token authentication support
    - Event filtering (send only specific events)
    """
    print("\n" + "="*70)
    print("Demo 3: HTTP Webhook Integration")
    print("="*70)
    
    # Example: Slack webhook notification
    # Replace with your actual webhook URL
    slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    print(f"\nWebhook URL: {slack_webhook_url}")
    print("(Replace with your actual webhook URL to test)")
    
    # Create webhook hook that only sends completion and error events
    hooks = create_webhook_hook(
        url=slack_webhook_url,
        events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],
    )
    
    # Example with authentication
    # hooks = create_webhook_hook(
    #     url="https://api.example.com/monitoring/events",
    #     auth_token="your_secret_token",
    #     events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],
    # )
    
    # Example workload
    def square(x):
        return x * x
    
    print("\nExecuting workload with webhook monitoring...")
    data = range(1, 51)  # 50 items
    results = execute(square, data, hooks=hooks)
    
    print(f"✓ Processed {len(list(results))} items")
    print("\nWebhook payload sent (POST_EXECUTE event):")
    print("""
    {
        "event": "post_execute",
        "timestamp": 1234567890.123,
        "n_jobs": 4,
        "chunksize": 100,
        "total_items": 50,
        "elapsed_time": 0.15,
        "throughput_items_per_sec": 333.3,
        "percent_complete": 100.0,
        ...
    }
    """)
    
    print("\nCommon webhook integrations:")
    print("  - Slack: https://api.slack.com/messaging/webhooks")
    print("  - Microsoft Teams: https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/")
    print("  - Discord: https://discord.com/developers/docs/resources/webhook")
    print("  - Custom: Any HTTP endpoint accepting JSON POST requests")


# ============================================================================
# Demo 4: Multi-System Monitoring
# ============================================================================

def demo_multi_system():
    """
    Demo: Enable multiple monitoring systems simultaneously.
    
    This is useful when you want:
    - Prometheus dashboards + Slack alerts
    - Datadog metrics + custom webhooks
    - Multiple monitoring systems for different purposes
    
    The integration provides:
    - Single hook manager for all systems
    - Coordinated metric collection
    - Independent error isolation per system
    """
    print("\n" + "="*70)
    print("Demo 4: Multi-System Monitoring")
    print("="*70)
    
    # Enable Prometheus, StatsD, and Webhook simultaneously
    hooks = create_multi_monitoring_hook(
        prometheus_port=8001,                  # Prometheus on port 8001
        statsd_host='localhost',               # StatsD to localhost
        statsd_port=8125,                      # StatsD port
        webhook_url='https://example.com/hook',  # Webhook URL
        webhook_events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],  # Only send completion/errors
    )
    
    print("\nEnabled monitoring systems:")
    print("  ✓ Prometheus: http://localhost:8001/metrics")
    print("  ✓ StatsD: localhost:8125")
    print("  ✓ Webhook: https://example.com/hook")
    
    # Example workload
    def factorial(n):
        """Compute factorial."""
        if n <= 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
    
    print("\nExecuting workload with multi-system monitoring...")
    data = range(1, 21)  # Factorials of 1-20
    results = execute(factorial, data, hooks=hooks)
    
    print(f"✓ Processed {len(list(results))} items")
    print("\nAll systems received metrics:")
    print("  - Prometheus: Updated counters and gauges")
    print("  - StatsD: Sent UDP metrics")
    print("  - Webhook: Sent POST_EXECUTE notification")
    print("\nUse case: Prometheus for dashboards, webhook for Slack alerts")


# ============================================================================
# Demo 5: Real-World Monitoring Pattern
# ============================================================================

def demo_production_monitoring():
    """
    Demo: Production-grade monitoring setup.
    
    This demonstrates a realistic production setup combining:
    - Prometheus for metrics and alerting
    - Webhook for Slack notifications on completion/errors
    - Proper configuration and error handling
    """
    print("\n" + "="*70)
    print("Demo 5: Production Monitoring Pattern")
    print("="*70)
    
    # Production-grade configuration
    hooks = create_multi_monitoring_hook(
        prometheus_port=9090,  # Standard Prometheus port
        webhook_url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
        webhook_events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],
    )
    
    print("\nProduction monitoring setup:")
    print("  ✓ Prometheus metrics: http://localhost:9090/metrics")
    print("  ✓ Slack notifications: On completion and errors")
    print("  ✓ Error isolation: Monitoring failures won't crash execution")
    print("  ✓ Thread-safe: Safe for concurrent executions")
    
    # Production workload example
    def process_batch(item):
        """Simulate batch processing."""
        time.sleep(0.01)  # Simulate work
        return f"processed_{item}"
    
    print("\nRunning production workload...")
    data = range(1, 201)  # 200 items
    
    start_time = time.time()
    results = execute(process_batch, data, hooks=hooks)
    elapsed = time.time() - start_time
    
    result_list = list(results)
    print(f"\n✓ Processed {len(result_list)} items in {elapsed:.2f}s")
    print(f"  Throughput: {len(result_list) / elapsed:.1f} items/sec")
    
    print("\nPrometheus Alerting Rules (example):")
    print("""
    groups:
    - name: amorsize_alerts
      rules:
      - alert: AmorsizeExecutionSlow
        expr: amorsize_execution_duration_seconds > 60
        for: 5m
        annotations:
          summary: "Amorsize execution taking too long"
      
      - alert: AmorsizeErrorsHigh
        expr: rate(amorsize_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate in Amorsize executions"
    """)
    
    print("\nGrafana Dashboard (example queries):")
    print("  - Execution duration: rate(amorsize_execution_duration_seconds_sum[5m])")
    print("  - Throughput: rate(amorsize_items_processed_total[1m])")
    print("  - Error rate: rate(amorsize_errors_total[5m])")
    print("  - Active workers: amorsize_workers_active")


# ============================================================================
# Demo 6: Custom Monitoring Integration
# ============================================================================

def demo_custom_integration():
    """
    Demo: Building custom monitoring on top of webhook integration.
    
    Shows how to integrate with any HTTP API that accepts JSON:
    - Custom logging services
    - Internal monitoring systems
    - Cloud monitoring (CloudWatch, Azure Monitor, etc.)
    - Custom dashboards
    """
    print("\n" + "="*70)
    print("Demo 6: Custom Monitoring Integration")
    print("="*70)
    
    # Example: Custom monitoring API
    print("\nIntegrating with custom monitoring API...")
    
    # Your custom monitoring endpoint
    custom_api_url = "https://api.example.com/v1/monitoring/events"
    
    hooks = create_webhook_hook(
        url=custom_api_url,
        method='POST',
        headers={
            'X-API-Version': '1.0',
            'X-Client-Id': 'amorsize-app',
        },
        auth_token='your_api_token_here',
        events=[HookEvent.PRE_EXECUTE, HookEvent.POST_EXECUTE],
    )
    
    print(f"\nCustom API endpoint: {custom_api_url}")
    print("Headers: X-API-Version, X-Client-Id, Authorization")
    print("Events: PRE_EXECUTE, POST_EXECUTE")
    
    # Example workload
    def process_item(x):
        return x ** 2
    
    print("\nExecuting workload...")
    data = range(1, 26)  # 25 items
    results = execute(process_item, data, hooks=hooks)
    
    print(f"✓ Processed {len(list(results))} items")
    print("\nPayload sent to custom API:")
    print("""
    POST https://api.example.com/v1/monitoring/events
    Headers:
      Content-Type: application/json
      X-API-Version: 1.0
      X-Client-Id: amorsize-app
      Authorization: Bearer your_api_token_here
    
    Body:
    {
        "event": "post_execute",
        "timestamp": 1234567890.123,
        "n_jobs": 4,
        "chunksize": 50,
        "total_items": 25,
        "elapsed_time": 0.05,
        "throughput_items_per_sec": 500.0,
        "metadata": {}
    }
    """)
    
    print("\nCustom integration use cases:")
    print("  - CloudWatch Logs: Send events to AWS CloudWatch")
    print("  - Azure Monitor: POST to Azure Monitor Data Collector API")
    print("  - Google Cloud Logging: Send to Cloud Logging API")
    print("  - Elasticsearch: Index events for Kibana dashboards")
    print("  - Custom dashboards: Feed your own monitoring UI")


# ============================================================================
# Run All Demos
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print(" Amorsize Monitoring Integrations - Complete Demo Suite")
    print("="*70)
    
    print("\nThis demo showcases:")
    print("  1. Prometheus Integration - Pull-based metrics")
    print("  2. StatsD Integration - Push-based metrics")
    print("  3. HTTP Webhook Integration - Event notifications")
    print("  4. Multi-System Monitoring - Combined integrations")
    print("  5. Production Monitoring Pattern - Real-world setup")
    print("  6. Custom Integration - Building your own")
    
    print("\n" + "="*70)
    print("\nStarting demos...")
    
    # Run each demo
    try:
        demo_prometheus()
        time.sleep(1)
        
        demo_statsd()
        time.sleep(1)
        
        demo_webhook()
        time.sleep(1)
        
        demo_multi_system()
        time.sleep(1)
        
        demo_production_monitoring()
        time.sleep(1)
        
        demo_custom_integration()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print(" Demo Complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Choose the monitoring system(s) that fit your needs")
    print("  2. Configure your monitoring infrastructure")
    print("  3. Add monitoring hooks to your production code")
    print("  4. Set up dashboards and alerts")
    print("\nDocumentation:")
    print("  - Prometheus: https://prometheus.io/docs/")
    print("  - Datadog: https://docs.datadoghq.com/")
    print("  - StatsD: https://github.com/statsd/statsd")
    print("  - Webhooks: See your platform's webhook documentation")
    print("\nFor questions: https://github.com/CampbellTrevor/Amorsize/issues")
    print("="*70 + "\n")
