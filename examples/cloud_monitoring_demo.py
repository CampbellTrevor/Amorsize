"""
Cloud-Native Monitoring Integration Demo

This script demonstrates how to use Amorsize with cloud-native monitoring
integrations including AWS CloudWatch, Azure Monitor, Google Cloud Monitoring,
and OpenTelemetry distributed tracing.

Each demo shows realistic usage patterns for production environments.
"""

import time
from typing import Any, List

# ============================================================================
# Demo 1: AWS CloudWatch Monitoring
# ============================================================================


def demo_cloudwatch_monitoring():
    """
    Demo: AWS CloudWatch Integration
    
    Shows how to publish Amorsize execution metrics to AWS CloudWatch.
    Metrics can be visualized in CloudWatch dashboards and used for alarms.
    """
    print("=" * 80)
    print("Demo 1: AWS CloudWatch Monitoring")
    print("=" * 80)
    print()
    
    from amorsize import execute
    from amorsize.monitoring import create_cloudwatch_hook
    
    # Sample workload
    def process_item(x: int) -> int:
        """Simulate some processing work."""
        time.sleep(0.01)  # Simulate work
        return x * 2
    
    data = list(range(100))
    
    print("Setting up CloudWatch monitoring...")
    print("  Namespace: MyApp/Amorsize")
    print("  Region: us-east-1")
    print("  Dimensions: Environment=Development")
    print()
    
    # Create CloudWatch hook with custom configuration
    hooks = create_cloudwatch_hook(
        namespace="MyApp/Amorsize",
        region_name="us-east-1",
        dimensions={"Environment": "Development"},
    )
    
    print("Executing workload with CloudWatch monitoring...")
    print()
    
    # Execute with CloudWatch monitoring
    # Note: This requires boto3 and AWS credentials configured
    try:
        results = execute(
            process_item,
            data,
            hooks=hooks,
        )
        
        print(f"✓ Processed {len(results)} items successfully")
        print()
        print("Metrics published to CloudWatch:")
        print("  - ExecutionsTotal: Counter metric")
        print("  - ExecutionDuration: Duration in seconds")
        print("  - ItemsProcessed: Total items processed")
        print("  - WorkersActive: Active worker count")
        print("  - Throughput: Items per second")
        print("  - PercentComplete: Progress percentage")
        print("  - ChunkDuration: Per-chunk timing")
        print()
        print("View metrics in AWS Console:")
        print("  CloudWatch > Metrics > Custom Namespaces > MyApp/Amorsize")
        print()
    
    except ImportError:
        print("⚠ boto3 not installed - CloudWatch metrics disabled")
        print("  Install with: pip install boto3")
        print()
        print("If boto3 is installed, configure AWS credentials:")
        print("  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("  - Configure ~/.aws/credentials")
        print("  - Use IAM role (if on EC2/ECS/Lambda)")
        print()
    
    print()


# ============================================================================
# Demo 2: Azure Monitor Integration
# ============================================================================


def demo_azure_monitor():
    """
    Demo: Azure Monitor Integration
    
    Shows how to send Amorsize execution telemetry to Azure Application Insights.
    Events can be queried with KQL and visualized in Azure dashboards.
    """
    print("=" * 80)
    print("Demo 2: Azure Monitor (Application Insights)")
    print("=" * 80)
    print()
    
    from amorsize import execute
    from amorsize.monitoring import create_azure_monitor_hook
    
    # Sample workload
    def analyze_data(x: int) -> dict:
        """Simulate data analysis."""
        time.sleep(0.01)
        return {"value": x, "result": x ** 2}
    
    data = list(range(100))
    
    print("Setting up Azure Monitor...")
    print("  Connection String: InstrumentationKey=...;IngestionEndpoint=...")
    print()
    
    # Create Azure Monitor hook
    # Note: Use your actual Application Insights connection string
    connection_string = "InstrumentationKey=your-key;IngestionEndpoint=https://region.applicationinsights.azure.com/"
    
    hooks = create_azure_monitor_hook(
        connection_string=connection_string,
    )
    
    print("Executing workload with Azure Monitor...")
    print()
    
    try:
        results = execute(
            analyze_data,
            data,
            hooks=hooks,


        )
        
        print(f"✓ Processed {len(results)} items successfully")
        print()
        print("Custom events sent to Application Insights:")
        print("  - Amorsize.pre_execute: Execution started")
        print("  - Amorsize.post_execute: Execution completed")
        print("  - Amorsize.on_progress: Progress updates")
        print("  - Amorsize.on_chunk_complete: Chunk timing")
        print("  - Amorsize.on_error: Error tracking")
        print()
        print("Query events in Azure Portal:")
        print("  Application Insights > Logs > customEvents")
        print("  | where name startswith 'Amorsize'")
        print()
    
    except ImportError:
        print("⚠ azure-monitor-opentelemetry not installed")
        print("  Install with: pip install azure-monitor-opentelemetry")
        print()
        print("Get connection string from Azure Portal:")
        print("  Application Insights > Overview > Connection String")
        print()
    
    print()


# ============================================================================
# Demo 3: Google Cloud Monitoring
# ============================================================================


def demo_gcp_monitoring():
    """
    Demo: Google Cloud Monitoring
    
    Shows how to publish Amorsize metrics to Google Cloud Monitoring
    (formerly Stackdriver). Metrics appear as custom time series.
    """
    print("=" * 80)
    print("Demo 3: Google Cloud Monitoring (Stackdriver)")
    print("=" * 80)
    print()
    
    from amorsize import execute
    from amorsize.monitoring import create_gcp_monitoring_hook
    
    # Sample workload
    def transform_data(x: int) -> str:
        """Simulate data transformation."""
        time.sleep(0.01)
        return f"item_{x}"
    
    data = list(range(100))
    
    print("Setting up GCP Monitoring...")
    print("  Project ID: my-gcp-project")
    print("  Metric Prefix: custom.googleapis.com/amorsize")
    print()
    
    # Create GCP Monitoring hook
    hooks = create_gcp_monitoring_hook(
        project_id="my-gcp-project",
        metric_prefix="custom.googleapis.com/amorsize",
    )
    
    print("Executing workload with GCP Monitoring...")
    print()
    
    try:
        results = execute(
            transform_data,
            data,
            hooks=hooks,


        )
        
        print(f"✓ Processed {len(results)} items successfully")
        print()
        print("Custom metrics written to Cloud Monitoring:")
        print("  - executions_total: Execution count (cumulative)")
        print("  - execution_duration_seconds: Duration (gauge)")
        print("  - items_processed_total: Items count (cumulative)")
        print("  - workers_active: Worker count (gauge)")
        print("  - throughput_items_per_second: Throughput (gauge)")
        print("  - percent_complete: Progress (gauge)")
        print("  - chunk_duration_seconds: Chunk timing (gauge)")
        print()
        print("View metrics in GCP Console:")
        print("  Monitoring > Metrics Explorer")
        print("  Resource Type: Global")
        print("  Metric: custom.googleapis.com/amorsize/*")
        print()
    
    except ImportError:
        print("⚠ google-cloud-monitoring not installed")
        print("  Install with: pip install google-cloud-monitoring")
        print()
        print("Configure Application Default Credentials:")
        print("  - Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
        print("  - Or use: gcloud auth application-default login")
        print()
    
    print()


# ============================================================================
# Demo 4: OpenTelemetry Distributed Tracing
# ============================================================================


def demo_opentelemetry_tracing():
    """
    Demo: OpenTelemetry Distributed Tracing
    
    Shows how to create distributed tracing spans for Amorsize execution.
    Spans can be exported to Jaeger, Zipkin, or any OTLP-compatible backend.
    """
    print("=" * 80)
    print("Demo 4: OpenTelemetry Distributed Tracing")
    print("=" * 80)
    print()
    
    from amorsize import execute
    from amorsize.monitoring import create_opentelemetry_hook
    
    # Sample workload
    def api_call(x: int) -> dict:
        """Simulate API call."""
        time.sleep(0.01)
        return {"id": x, "status": "success"}
    
    data = list(range(100))
    
    print("Setting up OpenTelemetry...")
    print("  Service Name: data-processing-service")
    print("  Exporter: OTLP (http://localhost:4318)")
    print()
    
    # Create OpenTelemetry hook
    hooks = create_opentelemetry_hook(
        service_name="data-processing-service",
        exporter_endpoint="http://localhost:4318",
    )
    
    print("Executing workload with OpenTelemetry tracing...")
    print()
    
    try:
        results = execute(
            api_call,
            data,
            hooks=hooks,


        )
        
        print(f"✓ Processed {len(results)} items successfully")
        print()
        print("Tracing spans created:")
        print("  - amorsize.execute: Root execution span")
        print()
        print("Span attributes:")
        print("  - amorsize.n_jobs: Number of workers")
        print("  - amorsize.chunksize: Chunk size")
        print("  - amorsize.total_items: Total items")
        print("  - amorsize.elapsed_time: Execution duration")
        print("  - amorsize.throughput: Items per second")
        print()
        print("Span events:")
        print("  - progress: Progress updates")
        print("  - chunk_complete: Chunk completion")
        print()
        print("View traces in your backend:")
        print("  - Jaeger: http://localhost:16686")
        print("  - Zipkin: http://localhost:9411")
        print("  - Or any OTLP-compatible backend")
        print()
    
    except ImportError:
        print("⚠ opentelemetry-api/sdk not installed")
        print("  Install with: pip install opentelemetry-api opentelemetry-sdk")
        print()
        print("For exporters:")
        print("  - OTLP: pip install opentelemetry-exporter-otlp")
        print("  - Jaeger: pip install opentelemetry-exporter-jaeger")
        print("  - Zipkin: pip install opentelemetry-exporter-zipkin")
        print()
    
    print()


# ============================================================================
# Demo 5: Multi-Cloud Monitoring
# ============================================================================


def demo_multi_cloud_monitoring():
    """
    Demo: Multi-Cloud Monitoring
    
    Shows how to send metrics to multiple cloud providers simultaneously.
    Useful for hybrid cloud environments or during cloud migration.
    """
    print("=" * 80)
    print("Demo 5: Multi-Cloud Monitoring (AWS + Azure + GCP)")
    print("=" * 80)
    print()
    
    from amorsize import execute
    from amorsize.hooks import HookManager
    from amorsize.monitoring import (
        create_azure_monitor_hook,
        create_cloudwatch_hook,
        create_gcp_monitoring_hook,
    )
    
    # Sample workload
    def process_record(x: int) -> dict:
        """Process a record."""
        time.sleep(0.01)
        return {"id": x, "processed": True}
    
    data = list(range(100))
    
    print("Setting up multi-cloud monitoring...")
    print("  ✓ AWS CloudWatch")
    print("  ✓ Azure Application Insights")
    print("  ✓ Google Cloud Monitoring")
    print()
    
    # Create hooks for each cloud provider
    cloudwatch_hooks = create_cloudwatch_hook(
        namespace="MultiCloud/Amorsize",
        region_name="us-east-1",
    )
    
    azure_hooks = create_azure_monitor_hook(
        connection_string="InstrumentationKey=...;IngestionEndpoint=...",
    )
    
    gcp_hooks = create_gcp_monitoring_hook(
        project_id="my-gcp-project",
    )
    
    # Combine all hooks into one manager
    combined_hooks = HookManager()
    
    # Copy hooks from each provider
    for event, callbacks in cloudwatch_hooks._hooks.items():
        for callback in callbacks:
            combined_hooks.register(event, callback)
    
    for event, callbacks in azure_hooks._hooks.items():
        for callback in callbacks:
            combined_hooks.register(event, callback)
    
    for event, callbacks in gcp_hooks._hooks.items():
        for callback in callbacks:
            combined_hooks.register(event, callback)
    
    print("Executing workload with multi-cloud monitoring...")
    print()
    
    results = execute(
        process_record,
        data,
        hooks=combined_hooks,


    )
    
    print(f"✓ Processed {len(results)} items successfully")
    print()
    print("Metrics published to:")
    print("  ✓ AWS CloudWatch: MyApp/Amorsize namespace")
    print("  ✓ Azure Monitor: Amorsize.* custom events")
    print("  ✓ GCP Monitoring: custom.googleapis.com/amorsize/* time series")
    print()
    print("Benefits of multi-cloud monitoring:")
    print("  - Consistent metrics across all clouds")
    print("  - Facilitates cloud migration")
    print("  - Enables cross-cloud analytics")
    print("  - Redundancy in monitoring")
    print()
    
    print()


# ============================================================================
# Demo 6: Production Monitoring Setup
# ============================================================================


def demo_production_monitoring_setup():
    """
    Demo: Complete Production Monitoring Setup
    
    Shows a realistic production configuration with all monitoring systems
    integrated, including error alerting and performance tracking.
    """
    print("=" * 80)
    print("Demo 6: Production Monitoring Setup (Best Practices)")
    print("=" * 80)
    print()
    
    from amorsize import execute
    from amorsize.hooks import HookEvent, HookManager
    from amorsize.monitoring import (
        create_cloudwatch_hook,
        create_opentelemetry_hook,
        create_prometheus_hook,
        create_webhook_hook,
    )
    
    # Sample workload
    def production_task(x: int) -> dict:
        """Production workload."""
        time.sleep(0.01)
        if x % 100 == 0:  # Simulate occasional error
            raise ValueError(f"Failed to process item {x}")
        return {"id": x, "result": x * 2}
    
    data = list(range(500))
    
    print("Production Monitoring Configuration:")
    print()
    print("1. Prometheus Metrics (port 8000)")
    print("   - Real-time dashboards")
    print("   - Alerting rules")
    print()
    print("2. AWS CloudWatch")
    print("   - Long-term metric storage")
    print("   - CloudWatch alarms")
    print()
    print("3. OpenTelemetry Tracing")
    print("   - Distributed tracing")
    print("   - Performance analysis")
    print()
    print("4. Webhook Alerts (Slack)")
    print("   - Error notifications")
    print("   - Completion notifications")
    print()
    
    # Set up monitoring stack
    prom_hooks = create_prometheus_hook(port=8000)
    
    cw_hooks = create_cloudwatch_hook(
        namespace="Production/Amorsize",
        region_name="us-east-1",
        dimensions={"Service": "DataProcessing"},
    )
    
    otel_hooks = create_opentelemetry_hook(
        service_name="data-processing-prod",
        exporter_endpoint="http://otel-collector:4318",
    )
    
    webhook_hooks = create_webhook_hook(
        url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        events=[HookEvent.POST_EXECUTE, HookEvent.ON_ERROR],
    )
    
    # Combine all hooks
    production_hooks = HookManager()
    
    for hooks_set in [prom_hooks, cw_hooks, otel_hooks, webhook_hooks]:
        for event, callbacks in hooks_set._hooks.items():
            for callback in callbacks:
                production_hooks.register(event, callback)
    
    print("Executing production workload...")
    print()
    
    try:
        results = execute(
            production_task,
            data,
            hooks=production_hooks,


        )
        
        print(f"✓ Processed {len(results)} items")
        print()
    
    except Exception as e:
        print(f"⚠ Execution failed: {e}")
        print()
    
    print("Monitoring Outputs:")
    print()
    print("1. Prometheus:")
    print("   http://localhost:8000/metrics")
    print()
    print("2. CloudWatch:")
    print("   CloudWatch > Metrics > Production/Amorsize")
    print()
    print("3. Distributed Tracing:")
    print("   Jaeger/Zipkin UI > Service: data-processing-prod")
    print()
    print("4. Slack Notifications:")
    print("   #alerts channel > Amorsize execution updates")
    print()
    print("Recommended Alerts:")
    print("  - Error rate > 1%")
    print("  - Execution duration > P95")
    print("  - Throughput < threshold")
    print("  - Worker failures")
    print()
    
    print()


# ============================================================================
# Demo 7: Custom Metrics and Dimensions
# ============================================================================


def demo_custom_metrics_and_dimensions():
    """
    Demo: Custom Metrics and Dimensions
    
    Shows how to add custom dimensions to cloud metrics for better filtering
    and aggregation in dashboards.
    """
    print("=" * 80)
    print("Demo 7: Custom Metrics and Dimensions")
    print("=" * 80)
    print()
    
    from amorsize import execute
    from amorsize.monitoring import create_cloudwatch_hook
    
    # Sample workload
    def customer_data_processing(x: int) -> dict:
        """Process customer data."""
        time.sleep(0.01)
        return {"customer_id": x, "processed": True}
    
    data = list(range(200))
    
    print("Using custom dimensions for better metric organization:")
    print()
    
    # Different configurations for different environments
    environments = [
        {
            "name": "Production",
            "dimensions": {
                "Environment": "Production",
                "Service": "CustomerDataProcessor",
                "Region": "us-east-1",
                "Version": "v2.1.0",
            }
        },
        {
            "name": "Staging",
            "dimensions": {
                "Environment": "Staging",
                "Service": "CustomerDataProcessor",
                "Region": "us-west-2",
                "Version": "v2.2.0-rc1",
            }
        },
    ]
    
    for env in environments:
        print(f"Environment: {env['name']}")
        print(f"  Dimensions: {env['dimensions']}")
        
        hooks = create_cloudwatch_hook(
            namespace="MyCompany/DataProcessing",
            region_name="us-east-1",
            dimensions=env['dimensions'],
        )
        
        # Execute with environment-specific monitoring
        results = execute(
            customer_data_processing,
            data[:10],  # Small sample for demo
            hooks=hooks,


        )
        
        print(f"  ✓ Processed {len(results)} items")
        print()
    
    print("Metric Filtering Examples:")
    print()
    print("CloudWatch Insights Query:")
    print("  SELECT AVG(ExecutionDuration)")
    print("  FROM 'MyCompany/DataProcessing'")
    print("  WHERE Environment = 'Production'")
    print("    AND Service = 'CustomerDataProcessor'")
    print("  GROUP BY Region")
    print()
    print("Benefits:")
    print("  - Compare performance across environments")
    print("  - Track metrics by service version")
    print("  - Regional performance analysis")
    print("  - Cost allocation by dimension")
    print()
    
    print()


# ============================================================================
# Main Demo Runner
# ============================================================================


def main():
    """Run all cloud monitoring demos."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Amorsize Cloud Monitoring Demos" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    demos = [
        ("AWS CloudWatch", demo_cloudwatch_monitoring),
        ("Azure Monitor", demo_azure_monitor),
        ("GCP Monitoring", demo_gcp_monitoring),
        ("OpenTelemetry", demo_opentelemetry_tracing),
        ("Multi-Cloud", demo_multi_cloud_monitoring),
        ("Production Setup", demo_production_monitoring_setup),
        ("Custom Dimensions", demo_custom_metrics_and_dimensions),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        print(f"Running Demo {i}/{len(demos)}: {name}")
        print()
        
        try:
            demo_func()
        except Exception as e:
            print(f"⚠ Demo failed: {e}")
            print()
        
        if i < len(demos):
            print("Press Enter to continue to next demo...")
            input()
            print()
    
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "All Demos Complete!" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Next Steps:")
    print("  1. Install cloud SDKs: boto3, azure-monitor-opentelemetry, google-cloud-monitoring")
    print("  2. Configure credentials for your cloud provider(s)")
    print("  3. Integrate monitoring into your production code")
    print("  4. Set up dashboards and alerts")
    print("  5. Monitor performance and optimize as needed")
    print()


if __name__ == "__main__":
    main()
