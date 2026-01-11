"""
Example: Using Pre-built Dashboard Templates for Cloud Monitoring

This example demonstrates how to deploy and use pre-built dashboard templates
and alert configurations for Amorsize cloud monitoring integrations.

The example covers:
1. AWS CloudWatch dashboards and alarms
2. Grafana dashboards for Prometheus
3. Azure Monitor workbooks
4. Google Cloud Monitoring dashboards
"""

import json
import time


def example_1_cloudwatch_dashboard():
    """
    Example 1: Deploy CloudWatch Dashboard
    
    Creates and deploys a comprehensive CloudWatch dashboard with:
    - Key performance indicators (KPIs)
    - Performance trends over time
    - Resource utilization metrics
    - Chunk-level performance
    """
    print("=" * 70)
    print("Example 1: Deploy CloudWatch Dashboard")
    print("=" * 70)
    
    from amorsize.dashboards import get_cloudwatch_dashboard, deploy_cloudwatch_dashboard
    
    # Step 1: Generate dashboard template
    dashboard_json = get_cloudwatch_dashboard(
        namespace="MyApp/Amorsize",
        region="us-east-1",
        dimensions={"Environment": "Production", "Service": "DataProcessing"}
    )
    
    print("\n✓ Generated CloudWatch dashboard template")
    print(f"  Dashboard has {len(json.loads(dashboard_json)['widgets'])} widgets")
    
    # Step 2: Preview the dashboard structure
    dashboard_dict = json.loads(dashboard_json)
    print("\n  Dashboard widgets:")
    for i, widget in enumerate(dashboard_dict['widgets'], 1):
        title = widget['properties'].get('title', 'Untitled')
        view_type = widget['properties'].get('view', 'Unknown')
        print(f"    {i}. {title} ({view_type})")
    
    # Step 3: Deploy the dashboard (requires AWS credentials)
    print("\n  To deploy this dashboard, run:")
    print("  >>> response = deploy_cloudwatch_dashboard(")
    print("  ...     dashboard_json,")
    print("  ...     dashboard_name='amorsize-prod-metrics',")
    print("  ...     region='us-east-1'")
    print("  ... )")
    
    # Alternative: Deploy using AWS CLI
    print("\n  Or use AWS CLI:")
    print("  aws cloudwatch put-dashboard \\")
    print("    --dashboard-name amorsize-prod-metrics \\")
    print("    --dashboard-body file://dashboard.json")
    
    # Save to file for manual deployment
    with open('/tmp/cloudwatch_dashboard.json', 'w') as f:
        f.write(dashboard_json)
    print("\n✓ Dashboard template saved to: /tmp/cloudwatch_dashboard.json")


def example_2_cloudwatch_alarms():
    """
    Example 2: Deploy CloudWatch Alarms
    
    Creates alarms for:
    - High error rates
    - Long execution duration
    - Low throughput
    - No executions (service outage detection)
    """
    print("\n" + "=" * 70)
    print("Example 2: Deploy CloudWatch Alarms")
    print("=" * 70)
    
    from amorsize.dashboards import get_cloudwatch_alarms, deploy_cloudwatch_alarms
    
    # Step 1: Generate alarm configurations
    alarms = get_cloudwatch_alarms(
        namespace="MyApp/Amorsize",
        region="us-east-1",
        dimensions={"Environment": "Production"},
        sns_topic_arn="arn:aws:sns:us-east-1:123456789012:amorsize-alerts"
    )
    
    print(f"\n✓ Generated {len(alarms)} CloudWatch alarms")
    
    # Step 2: Preview alarm configurations
    print("\n  Alarm configurations:")
    for alarm in alarms:
        name = alarm['AlarmName']
        metric = alarm['MetricName']
        threshold = alarm['Threshold']
        comparison = alarm['ComparisonOperator']
        print(f"    - {name}")
        print(f"      Metric: {metric}, Threshold: {threshold}, Operator: {comparison}")
    
    # Step 3: Deploy alarms (requires AWS credentials)
    print("\n  To deploy these alarms, run:")
    print("  >>> responses = deploy_cloudwatch_alarms(")
    print("  ...     alarms,")
    print("  ...     region='us-east-1'")
    print("  ... )")
    
    # Alternative: Deploy using boto3 directly
    print("\n  Or use boto3 directly:")
    print("  import boto3")
    print("  cw = boto3.client('cloudwatch', region_name='us-east-1')")
    print("  for alarm in alarms:")
    print("      cw.put_metric_alarm(**alarm)")
    
    # Save to file for reference
    with open('/tmp/cloudwatch_alarms.json', 'w') as f:
        json.dump(alarms, f, indent=2, default=str)
    print("\n✓ Alarm configurations saved to: /tmp/cloudwatch_alarms.json")


def example_3_grafana_dashboard():
    """
    Example 3: Create Grafana Dashboard for Prometheus
    
    Creates a Grafana dashboard with:
    - KPI stat panels
    - Time series graphs
    - Resource utilization
    - Performance metrics
    """
    print("\n" + "=" * 70)
    print("Example 3: Create Grafana Dashboard")
    print("=" * 70)
    
    from amorsize.dashboards import get_grafana_dashboard
    
    # Step 1: Generate dashboard
    dashboard = get_grafana_dashboard(
        datasource_uid="PROM123",  # Your Prometheus datasource UID
        job_label="amorsize"
    )
    
    print(f"\n✓ Generated Grafana dashboard with {len(dashboard['panels'])} panels")
    
    # Step 2: Preview panel structure
    print("\n  Dashboard panels:")
    for panel in dashboard['panels']:
        title = panel.get('title', 'Untitled')
        panel_type = panel.get('type', 'unknown')
        print(f"    - {title} ({panel_type})")
    
    # Step 3: Import to Grafana
    print("\n  To import this dashboard to Grafana:")
    print("  1. Save the dashboard JSON to a file")
    print("  2. Go to Grafana UI → Dashboards → Import")
    print("  3. Upload the JSON file")
    print("\n  Or use Grafana HTTP API:")
    print("  import requests")
    print("  response = requests.post(")
    print("      'http://grafana:3000/api/dashboards/db',")
    print("      json={'dashboard': dashboard, 'overwrite': True},")
    print("      headers={'Authorization': 'Bearer YOUR_API_KEY'}")
    print("  )")
    
    # Save to file
    with open('/tmp/grafana_dashboard.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    print("\n✓ Dashboard saved to: /tmp/grafana_dashboard.json")


def example_4_azure_workbook():
    """
    Example 4: Create Azure Monitor Workbook
    
    Creates an Azure Monitor workbook with:
    - Execution timeline
    - Duration percentiles
    - Throughput analysis
    - Error tracking
    """
    print("\n" + "=" * 70)
    print("Example 4: Create Azure Monitor Workbook")
    print("=" * 70)
    
    from amorsize.dashboards import get_azure_monitor_workbook
    
    # Step 1: Generate workbook template
    workbook = get_azure_monitor_workbook()
    
    print(f"\n✓ Generated Azure Monitor workbook with {len(workbook['items'])} items")
    
    # Step 2: Preview workbook structure
    print("\n  Workbook items:")
    for item in workbook['items']:
        item_type = item['type']
        if item_type == 1:  # Text
            print("    - Text/Markdown section")
        elif item_type == 3:  # Query
            title = item['content'].get('title', 'Query')
            print(f"    - {title} (KQL Query)")
    
    # Step 3: Deploy to Azure
    print("\n  To deploy this workbook to Azure:")
    print("  az monitor app-insights workbook create \\")
    print("    --resource-group myResourceGroup \\")
    print("    --name Amorsize-Metrics \\")
    print("    --location eastus \\")
    print("    --serialized-data '$(cat workbook.json)'")
    
    # Save to file
    with open('/tmp/azure_workbook.json', 'w') as f:
        json.dump(workbook, f, indent=2)
    print("\n✓ Workbook template saved to: /tmp/azure_workbook.json")


def example_5_gcp_dashboard():
    """
    Example 5: Create Google Cloud Monitoring Dashboard
    
    Creates a GCP dashboard with:
    - Score cards for KPIs
    - Time series charts
    - Resource metrics
    - Error tracking
    """
    print("\n" + "=" * 70)
    print("Example 5: Create GCP Dashboard")
    print("=" * 70)
    
    from amorsize.dashboards import get_gcp_dashboard
    
    # Step 1: Generate dashboard
    dashboard = get_gcp_dashboard(
        project_id="my-gcp-project",
        metric_prefix="custom.googleapis.com/amorsize"
    )
    
    widget_count = len(dashboard['grid_layout']['widgets'])
    print(f"\n✓ Generated GCP dashboard with {widget_count} widgets")
    
    # Step 2: Preview widget structure
    print("\n  Dashboard widgets:")
    for widget in dashboard['grid_layout']['widgets']:
        title = widget.get('title', 'Untitled')
        widget_type = 'score_card' if 'score_card' in widget else 'xy_chart'
        print(f"    - {title} ({widget_type})")
    
    # Step 3: Deploy to GCP
    print("\n  To deploy this dashboard to GCP using Python:")
    print("  from google.cloud import monitoring_dashboard_v1")
    print("  client = monitoring_dashboard_v1.DashboardsServiceClient()")
    print("  parent = f'projects/my-gcp-project'")
    print("  dashboard_obj = monitoring_dashboard_v1.Dashboard(**dashboard)")
    print("  client.create_dashboard(parent=parent, dashboard=dashboard_obj)")
    
    print("\n  Or use gcloud CLI:")
    print("  gcloud monitoring dashboards create \\")
    print("    --config-from-file=dashboard.json")
    
    # Save to file
    with open('/tmp/gcp_dashboard.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    print("\n✓ Dashboard saved to: /tmp/gcp_dashboard.json")


def example_6_production_setup():
    """
    Example 6: Complete Production Setup
    
    Shows how to deploy a complete monitoring stack with:
    - CloudWatch metrics + dashboard + alarms
    - Integration with Amorsize execution
    """
    print("\n" + "=" * 70)
    print("Example 6: Complete Production Setup")
    print("=" * 70)
    
    from amorsize import execute
    from amorsize.monitoring import create_cloudwatch_hook
    from amorsize.dashboards import (
        get_cloudwatch_dashboard,
        get_cloudwatch_alarms,
        deploy_cloudwatch_dashboard,
        deploy_cloudwatch_alarms
    )
    
    # Configuration
    NAMESPACE = "MyApp/Amorsize"
    REGION = "us-east-1"
    DIMENSIONS = {"Environment": "Production", "Service": "DataProcessor"}
    SNS_TOPIC = "arn:aws:sns:us-east-1:123456789012:alerts"
    
    print("\n1. Deploy CloudWatch dashboard...")
    dashboard_json = get_cloudwatch_dashboard(
        namespace=NAMESPACE,
        region=REGION,
        dimensions=DIMENSIONS
    )
    print("   Dashboard template generated ✓")
    print("   To deploy: deploy_cloudwatch_dashboard(dashboard_json, 'amorsize-prod')")
    
    print("\n2. Deploy CloudWatch alarms...")
    alarms = get_cloudwatch_alarms(
        namespace=NAMESPACE,
        region=REGION,
        dimensions=DIMENSIONS,
        sns_topic_arn=SNS_TOPIC
    )
    print(f"   {len(alarms)} alarm configurations generated ✓")
    print("   To deploy: deploy_cloudwatch_alarms(alarms)")
    
    print("\n3. Configure monitoring hooks...")
    hooks = create_cloudwatch_hook(
        namespace=NAMESPACE,
        region_name=REGION,
        dimensions=DIMENSIONS
    )
    print("   CloudWatch hooks configured ✓")
    
    print("\n4. Run workload with monitoring...")
    print("   Example:")
    print("   def process_item(x):")
    print("       return x * x")
    print("   ")
    print("   data = range(10000)")
    print("   results = execute(process_item, data, hooks=hooks)")
    print("   ")
    print("   Metrics will be automatically sent to CloudWatch!")
    
    print("\n5. Access your metrics:")
    print(f"   - Dashboard: AWS Console → CloudWatch → Dashboards → amorsize-prod")
    print(f"   - Alarms: AWS Console → CloudWatch → Alarms")
    print(f"   - Metrics: AWS Console → CloudWatch → Metrics → {NAMESPACE}")
    
    print("\n✓ Production monitoring setup complete!")
    print("\n  Your Amorsize workloads are now fully observable with:")
    print("  - Real-time performance dashboards")
    print("  - Automated alerting on anomalies")
    print("  - Historical trend analysis")
    print("  - Resource utilization tracking")


def example_7_multi_cloud_dashboards():
    """
    Example 7: Multi-Cloud Dashboard Deployment
    
    Shows how to deploy dashboards across multiple cloud providers
    for unified observability.
    """
    print("\n" + "=" * 70)
    print("Example 7: Multi-Cloud Dashboard Deployment")
    print("=" * 70)
    
    from amorsize.dashboards import (
        get_cloudwatch_dashboard,
        get_grafana_dashboard,
        get_azure_monitor_workbook,
        get_gcp_dashboard
    )
    
    print("\n1. AWS CloudWatch Dashboard...")
    aws_dashboard = get_cloudwatch_dashboard(
        namespace="MultiCloud/Amorsize",
        region="us-east-1"
    )
    with open('/tmp/aws_dashboard.json', 'w') as f:
        f.write(aws_dashboard)
    print("   ✓ Generated: /tmp/aws_dashboard.json")
    
    print("\n2. Grafana Dashboard (Prometheus)...")
    grafana_dashboard = get_grafana_dashboard(
        datasource_uid="PROM123",
        job_label="amorsize"
    )
    with open('/tmp/grafana_dashboard.json', 'w') as f:
        json.dump(grafana_dashboard, f, indent=2)
    print("   ✓ Generated: /tmp/grafana_dashboard.json")
    
    print("\n3. Azure Monitor Workbook...")
    azure_workbook = get_azure_monitor_workbook()
    with open('/tmp/azure_workbook.json', 'w') as f:
        json.dump(azure_workbook, f, indent=2)
    print("   ✓ Generated: /tmp/azure_workbook.json")
    
    print("\n4. Google Cloud Dashboard...")
    gcp_dashboard = get_gcp_dashboard(
        project_id="my-project-123",
        metric_prefix="custom.googleapis.com/amorsize"
    )
    with open('/tmp/gcp_dashboard.json', 'w') as f:
        json.dump(gcp_dashboard, f, indent=2)
    print("   ✓ Generated: /tmp/gcp_dashboard.json")
    
    print("\n✓ Multi-cloud dashboard templates generated!")
    print("\n  Deploy to each platform:")
    print("  - AWS: Use AWS CloudWatch Console or CLI")
    print("  - Grafana: Import via UI or HTTP API")
    print("  - Azure: Use Azure CLI or Portal")
    print("  - GCP: Use gcloud CLI or Python API")
    
    print("\n  Benefit: Consistent monitoring experience across all platforms")


if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  Amorsize Dashboard Templates - Comprehensive Examples".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    
    # Run all examples
    try:
        example_1_cloudwatch_dashboard()
        time.sleep(0.5)
        
        example_2_cloudwatch_alarms()
        time.sleep(0.5)
        
        example_3_grafana_dashboard()
        time.sleep(0.5)
        
        example_4_azure_workbook()
        time.sleep(0.5)
        
        example_5_gcp_dashboard()
        time.sleep(0.5)
        
        example_6_production_setup()
        time.sleep(0.5)
        
        example_7_multi_cloud_dashboards()
        
        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print("\nGenerated files in /tmp/:")
        print("  - cloudwatch_dashboard.json")
        print("  - cloudwatch_alarms.json")
        print("  - grafana_dashboard.json")
        print("  - azure_workbook.json")
        print("  - gcp_dashboard.json")
        print("  - aws_dashboard.json (multi-cloud)")
        print("\nThese templates are ready to deploy to your cloud environments!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
