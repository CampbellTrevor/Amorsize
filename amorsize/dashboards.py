"""
Dashboard templates and alert configurations for cloud monitoring integrations.

This module provides pre-built dashboard templates and alert rules for various
cloud monitoring platforms, making it easy to deploy production-ready observability
for Amorsize workloads.

Supported Platforms:
    - AWS CloudWatch Dashboards + CloudWatch Alarms
    - Azure Monitor Workbooks
    - Google Cloud Monitoring Dashboards
    - Grafana (for Prometheus metrics)

Usage:
    >>> from amorsize.dashboards import get_cloudwatch_dashboard, deploy_cloudwatch_dashboard
    >>> dashboard_json = get_cloudwatch_dashboard(namespace="MyApp/Amorsize")
    >>> deploy_cloudwatch_dashboard(dashboard_json, dashboard_name="amorsize-metrics")
"""

import json
from typing import Any, Dict, List, Optional


def get_cloudwatch_dashboard(
    namespace: str = "Amorsize",
    region: str = "us-east-1",
    dimensions: Optional[Dict[str, str]] = None
) -> str:
    """
    Get CloudWatch dashboard JSON for Amorsize metrics.
    
    This dashboard provides comprehensive visibility into:
    - Execution performance (duration, throughput)
    - Resource utilization (workers, items processed)
    - Error rates
    - Progress tracking
    
    Args:
        namespace: CloudWatch namespace (default: "Amorsize")
        region: AWS region (default: "us-east-1")
        dimensions: Optional dimension filters as key-value pairs
        
    Returns:
        Dashboard JSON as string, ready for CloudWatch API
        
    Example:
        >>> dashboard_json = get_cloudwatch_dashboard(
        ...     namespace="MyApp/Amorsize",
        ...     region="us-west-2",
        ...     dimensions={"Environment": "Production"}
        ... )
        >>> # Deploy with boto3:
        >>> import boto3
        >>> cw = boto3.client('cloudwatch', region_name='us-west-2')
        >>> cw.put_dashboard(
        ...     DashboardName='amorsize-metrics',
        ...     DashboardBody=dashboard_json
        ... )
    """
    # Build dimension filter for all widgets
    dim_filter = []
    if dimensions:
        for key, value in dimensions.items():
            dim_filter.append(key)
            dim_filter.append(value)
    
    dashboard = {
        "widgets": [
            # Row 1: Key Performance Indicators
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "ExecutionsTotal", *dim_filter, {"stat": "Sum", "label": "Total Executions"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "Total Executions",
                    "yAxis": {"left": {"label": "Count"}},
                    "view": "singleValue"
                }
            },
            {
                "type": "metric",
                "x": 6,
                "y": 0,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "ItemsProcessed", *dim_filter, {"stat": "Sum", "label": "Items Processed"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "Items Processed",
                    "yAxis": {"left": {"label": "Count"}},
                    "view": "singleValue"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "ExecutionDuration", *dim_filter, {"stat": "Average", "label": "Avg Duration"}]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": region,
                    "title": "Avg Execution Duration",
                    "yAxis": {"left": {"label": "Seconds"}},
                    "view": "singleValue"
                }
            },
            {
                "type": "metric",
                "x": 18,
                "y": 0,
                "width": 6,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "ErrorsTotal", *dim_filter, {"stat": "Sum", "label": "Total Errors"}]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": region,
                    "title": "Errors",
                    "yAxis": {"left": {"label": "Count"}},
                    "view": "singleValue"
                }
            },
            
            # Row 2: Performance Over Time
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "ExecutionDuration", *dim_filter, {"stat": "Average", "label": "Avg"}],
                        ["...", {"stat": "p50", "label": "p50"}],
                        ["...", {"stat": "p90", "label": "p90"}],
                        ["...", {"stat": "p99", "label": "p99"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": region,
                    "title": "Execution Duration (Percentiles)",
                    "yAxis": {"left": {"label": "Seconds"}},
                    "view": "timeSeries"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "Throughput", *dim_filter, {"stat": "Average", "label": "Items/sec"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": region,
                    "title": "Throughput",
                    "yAxis": {"left": {"label": "Items/Second"}},
                    "view": "timeSeries"
                }
            },
            
            # Row 3: Resource Utilization
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "WorkersActive", *dim_filter, {"stat": "Average", "label": "Active Workers"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": region,
                    "title": "Active Workers",
                    "yAxis": {"left": {"label": "Count"}},
                    "view": "timeSeries"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 12,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "PercentComplete", *dim_filter, {"stat": "Average", "label": "Progress"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": region,
                    "title": "Progress %",
                    "yAxis": {"left": {"label": "Percent", "min": 0, "max": 100}},
                    "view": "timeSeries"
                }
            },
            
            # Row 4: Chunk Performance
            {
                "type": "metric",
                "x": 0,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "ChunkDuration", *dim_filter, {"stat": "Average", "label": "Avg"}],
                        ["...", {"stat": "p50", "label": "p50"}],
                        ["...", {"stat": "p90", "label": "p90"}]
                    ],
                    "period": 60,
                    "stat": "Average",
                    "region": region,
                    "title": "Chunk Duration",
                    "yAxis": {"left": {"label": "Seconds"}},
                    "view": "timeSeries"
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 18,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [namespace, "ErrorsTotal", *dim_filter, {"stat": "Sum", "label": "Errors"}]
                    ],
                    "period": 60,
                    "stat": "Sum",
                    "region": region,
                    "title": "Error Rate",
                    "yAxis": {"left": {"label": "Count"}},
                    "view": "timeSeries"
                }
            }
        ]
    }
    
    return json.dumps(dashboard)


def get_cloudwatch_alarms(
    namespace: str = "Amorsize",
    region: str = "us-east-1",
    dimensions: Optional[Dict[str, str]] = None,
    sns_topic_arn: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get CloudWatch alarm configurations for Amorsize metrics.
    
    Creates alarms for:
    - High error rates (>5% of executions)
    - Long execution duration (>300s p99)
    - Low throughput (<10 items/sec)
    
    Args:
        namespace: CloudWatch namespace (default: "Amorsize")
        region: AWS region (default: "us-east-1")
        dimensions: Optional dimension filters
        sns_topic_arn: SNS topic ARN for alarm notifications
        
    Returns:
        List of alarm configurations
        
    Example:
        >>> alarms = get_cloudwatch_alarms(
        ...     namespace="MyApp/Amorsize",
        ...     sns_topic_arn="arn:aws:sns:us-east-1:123456789:alerts"
        ... )
        >>> import boto3
        >>> cw = boto3.client('cloudwatch')
        >>> for alarm in alarms:
        ...     cw.put_metric_alarm(**alarm)
    """
    # Build dimension list for alarms
    dim_list = []
    if dimensions:
        for key, value in dimensions.items():
            dim_list.append({"Name": key, "Value": value})
    
    alarms = []
    
    # Alarm 1: High error rate
    alarm_actions = [sns_topic_arn] if sns_topic_arn else []
    
    alarms.append({
        "AlarmName": f"Amorsize-HighErrorRate-{region}",
        "AlarmDescription": "Amorsize error rate exceeds 5% of total executions",
        "ActionsEnabled": True,
        "AlarmActions": alarm_actions,
        "MetricName": "ErrorsTotal",
        "Namespace": namespace,
        "Statistic": "Sum",
        "Dimensions": dim_list,
        "Period": 300,  # 5 minutes
        "EvaluationPeriods": 2,
        "Threshold": 0.05,  # 5% error rate
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "notBreaching"
    })
    
    # Alarm 2: Long execution duration (p99)
    alarms.append({
        "AlarmName": f"Amorsize-SlowExecution-{region}",
        "AlarmDescription": "Amorsize execution p99 duration exceeds 300 seconds",
        "ActionsEnabled": True,
        "AlarmActions": alarm_actions,
        "MetricName": "ExecutionDuration",
        "Namespace": namespace,
        "ExtendedStatistic": "p99",
        "Dimensions": dim_list,
        "Period": 300,
        "EvaluationPeriods": 2,
        "Threshold": 300.0,  # 5 minutes
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "notBreaching"
    })
    
    # Alarm 3: Low throughput
    alarms.append({
        "AlarmName": f"Amorsize-LowThroughput-{region}",
        "AlarmDescription": "Amorsize throughput drops below 10 items/second",
        "ActionsEnabled": True,
        "AlarmActions": alarm_actions,
        "MetricName": "Throughput",
        "Namespace": namespace,
        "Statistic": "Average",
        "Dimensions": dim_list,
        "Period": 300,
        "EvaluationPeriods": 3,
        "Threshold": 10.0,  # items/sec
        "ComparisonOperator": "LessThanThreshold",
        "TreatMissingData": "notBreaching"
    })
    
    # Alarm 4: No executions (potential service outage)
    alarms.append({
        "AlarmName": f"Amorsize-NoExecutions-{region}",
        "AlarmDescription": "No Amorsize executions detected in 15 minutes",
        "ActionsEnabled": True,
        "AlarmActions": alarm_actions,
        "MetricName": "ExecutionsTotal",
        "Namespace": namespace,
        "Statistic": "Sum",
        "Dimensions": dim_list,
        "Period": 900,  # 15 minutes
        "EvaluationPeriods": 1,
        "Threshold": 1.0,
        "ComparisonOperator": "LessThanThreshold",
        "TreatMissingData": "breaching"  # Treat missing data as alarm
    })
    
    return alarms


def get_grafana_dashboard(
    datasource_uid: str = "prometheus",
    job_label: str = "amorsize"
) -> Dict[str, Any]:
    """
    Get Grafana dashboard JSON for Prometheus metrics.
    
    Creates a comprehensive dashboard with:
    - KPI panels (executions, items, duration, errors)
    - Time series graphs (performance trends)
    - Resource utilization (workers, progress)
    - Chunk-level metrics
    
    Args:
        datasource_uid: Prometheus datasource UID in Grafana
        job_label: Prometheus job label for filtering
        
    Returns:
        Dashboard JSON dict
        
    Example:
        >>> dashboard = get_grafana_dashboard(datasource_uid="ABCD1234")
        >>> # Import to Grafana:
        >>> import requests
        >>> response = requests.post(
        ...     'http://grafana:3000/api/dashboards/db',
        ...     json={'dashboard': dashboard, 'overwrite': True},
        ...     headers={'Authorization': 'Bearer YOUR_API_KEY'}
        ... )
    """
    dashboard = {
        "title": "Amorsize Metrics",
        "tags": ["amorsize", "parallelization", "performance"],
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "30s",
        "panels": [
            # Row 1: KPIs
            {
                "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
                "id": 1,
                "title": "Total Executions",
                "type": "stat",
                "targets": [{
                    "datasource": {"uid": datasource_uid},
                    "expr": f'sum(increase(amorsize_executions_total{{job="{job_label}"}}[5m]))',
                    "refId": "A"
                }],
                "options": {
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "orientation": "auto",
                    "textMode": "value_and_name"
                }
            },
            {
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
                "id": 2,
                "title": "Items Processed",
                "type": "stat",
                "targets": [{
                    "datasource": {"uid": datasource_uid},
                    "expr": f'sum(increase(amorsize_items_processed_total{{job="{job_label}"}}[5m]))',
                    "refId": "A"
                }],
                "options": {
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "orientation": "auto",
                    "textMode": "value_and_name"
                }
            },
            {
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
                "id": 3,
                "title": "Avg Duration (s)",
                "type": "stat",
                "targets": [{
                    "datasource": {"uid": datasource_uid},
                    "expr": f'avg(rate(amorsize_execution_duration_seconds_sum{{job="{job_label}"}}[5m]) / rate(amorsize_execution_duration_seconds_count{{job="{job_label}"}}[5m]))',
                    "refId": "A"
                }],
                "options": {
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "orientation": "auto",
                    "textMode": "value_and_name"
                },
                "fieldConfig": {"defaults": {"unit": "s"}}
            },
            {
                "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
                "id": 4,
                "title": "Errors",
                "type": "stat",
                "targets": [{
                    "datasource": {"uid": datasource_uid},
                    "expr": f'sum(increase(amorsize_errors_total{{job="{job_label}"}}[5m]))',
                    "refId": "A"
                }],
                "options": {
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "orientation": "auto",
                    "textMode": "value_and_name"
                },
                "fieldConfig": {"defaults": {"color": {"mode": "thresholds"}, "thresholds": {"steps": [{"value": 0, "color": "green"}, {"value": 1, "color": "red"}]}}}
            },
            
            # Row 2: Performance Trends
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
                "id": 5,
                "title": "Execution Duration (Percentiles)",
                "type": "timeseries",
                "targets": [
                    {
                        "datasource": {"uid": datasource_uid},
                        "expr": f'histogram_quantile(0.50, rate(amorsize_execution_duration_seconds_bucket{{job="{job_label}"}}[5m]))',
                        "refId": "A",
                        "legendFormat": "p50"
                    },
                    {
                        "datasource": {"uid": datasource_uid},
                        "expr": f'histogram_quantile(0.90, rate(amorsize_execution_duration_seconds_bucket{{job="{job_label}"}}[5m]))',
                        "refId": "B",
                        "legendFormat": "p90"
                    },
                    {
                        "datasource": {"uid": datasource_uid},
                        "expr": f'histogram_quantile(0.99, rate(amorsize_execution_duration_seconds_bucket{{job="{job_label}"}}[5m]))',
                        "refId": "C",
                        "legendFormat": "p99"
                    }
                ],
                "fieldConfig": {"defaults": {"unit": "s"}}
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
                "id": 6,
                "title": "Throughput (items/sec)",
                "type": "timeseries",
                "targets": [{
                    "datasource": {"uid": datasource_uid},
                    "expr": f'avg(amorsize_throughput{{job="{job_label}"}})',
                    "refId": "A",
                    "legendFormat": "Throughput"
                }],
                "fieldConfig": {"defaults": {"unit": "ops"}}
            },
            
            # Row 3: Resource Utilization
            {
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
                "id": 7,
                "title": "Active Workers",
                "type": "timeseries",
                "targets": [{
                    "datasource": {"uid": datasource_uid},
                    "expr": f'avg(amorsize_workers_active{{job="{job_label}"}})',
                    "refId": "A",
                    "legendFormat": "Workers"
                }],
                "fieldConfig": {"defaults": {"unit": "short"}}
            },
            {
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
                "id": 8,
                "title": "Progress %",
                "type": "timeseries",
                "targets": [{
                    "datasource": {"uid": datasource_uid},
                    "expr": f'avg(amorsize_percent_complete{{job="{job_label}"}})',
                    "refId": "A",
                    "legendFormat": "Progress"
                }],
                "fieldConfig": {"defaults": {"unit": "percent", "min": 0, "max": 100}}
            }
        ]
    }
    
    return dashboard


def get_azure_monitor_workbook() -> Dict[str, Any]:
    """
    Get Azure Monitor workbook template for Application Insights.
    
    Returns:
        Workbook template JSON dict
        
    Example:
        >>> workbook = get_azure_monitor_workbook()
        >>> # Deploy with Azure CLI:
        >>> import subprocess
        >>> subprocess.run([
        ...     'az', 'monitor', 'app-insights', 'workbook', 'create',
        ...     '--resource-group', 'myResourceGroup',
        ...     '--name', 'Amorsize-Metrics',
        ...     '--serialized-data', json.dumps(workbook)
        ... ])
    """
    workbook = {
        "version": "Notebook/1.0",
        "items": [
            {
                "type": 1,
                "content": {
                    "json": "## Amorsize Metrics Dashboard\n\nComprehensive monitoring for Amorsize parallelization workloads."
                }
            },
            {
                "type": 3,
                "content": {
                    "version": "KqlItem/1.0",
                    "query": "customEvents\n| where name == 'amorsize_execution'\n| summarize count() by bin(timestamp, 5m)\n| render timechart",
                    "size": 0,
                    "title": "Executions Over Time",
                    "queryType": 0,
                    "resourceType": "microsoft.insights/components"
                }
            },
            {
                "type": 3,
                "content": {
                    "version": "KqlItem/1.0",
                    "query": "customEvents\n| where name == 'amorsize_execution'\n| extend duration = todouble(customMeasurements['duration'])\n| summarize avg(duration), percentile(duration, 50), percentile(duration, 90), percentile(duration, 99) by bin(timestamp, 5m)\n| render timechart",
                    "size": 0,
                    "title": "Execution Duration (Percentiles)",
                    "queryType": 0,
                    "resourceType": "microsoft.insights/components"
                }
            },
            {
                "type": 3,
                "content": {
                    "version": "KqlItem/1.0",
                    "query": "customEvents\n| where name == 'amorsize_execution'\n| extend items = todouble(customMeasurements['items_processed'])\n| extend duration = todouble(customMeasurements['duration'])\n| extend throughput = items / duration\n| summarize avg(throughput) by bin(timestamp, 5m)\n| render timechart",
                    "size": 0,
                    "title": "Throughput (items/sec)",
                    "queryType": 0,
                    "resourceType": "microsoft.insights/components"
                }
            },
            {
                "type": 3,
                "content": {
                    "version": "KqlItem/1.0",
                    "query": "customEvents\n| where name == 'amorsize_error'\n| summarize count() by bin(timestamp, 5m)\n| render barchart",
                    "size": 0,
                    "title": "Error Rate",
                    "queryType": 0,
                    "resourceType": "microsoft.insights/components"
                }
            }
        ]
    }
    
    return workbook


def get_gcp_dashboard(project_id: str, metric_prefix: str = "custom.googleapis.com/amorsize") -> Dict[str, Any]:
    """
    Get Google Cloud Monitoring dashboard configuration.
    
    Args:
        project_id: GCP project ID
        metric_prefix: Metric type prefix (default: "custom.googleapis.com/amorsize")
        
    Returns:
        Dashboard configuration dict
        
    Example:
        >>> dashboard = get_gcp_dashboard(project_id="my-project-123")
        >>> # Deploy with GCP API:
        >>> from google.cloud import monitoring_dashboard_v1
        >>> client = monitoring_dashboard_v1.DashboardsServiceClient()
        >>> parent = f"projects/{project_id}"
        >>> dashboard_obj = monitoring_dashboard_v1.Dashboard(
        ...     display_name="Amorsize Metrics",
        ...     **dashboard
        ... )
        >>> client.create_dashboard(parent=parent, dashboard=dashboard_obj)
    """
    dashboard = {
        "display_name": "Amorsize Metrics",
        "grid_layout": {
            "widgets": [
                # KPI: Total Executions
                {
                    "title": "Total Executions",
                    "score_card": {
                        "time_series_query": {
                            "time_series_filter": {
                                "filter": f'metric.type="{metric_prefix}/executions_total" resource.type="global"',
                                "aggregation": {
                                    "alignment_period": "300s",
                                    "per_series_aligner": "ALIGN_RATE"
                                }
                            }
                        }
                    }
                },
                # KPI: Items Processed
                {
                    "title": "Items Processed",
                    "score_card": {
                        "time_series_query": {
                            "time_series_filter": {
                                "filter": f'metric.type="{metric_prefix}/items_processed" resource.type="global"',
                                "aggregation": {
                                    "alignment_period": "300s",
                                    "per_series_aligner": "ALIGN_RATE"
                                }
                            }
                        }
                    }
                },
                # Chart: Execution Duration
                {
                    "title": "Execution Duration",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'metric.type="{metric_prefix}/execution_duration" resource.type="global"',
                                    "aggregation": {
                                        "alignment_period": "60s",
                                        "per_series_aligner": "ALIGN_DELTA",
                                        "cross_series_reducer": "REDUCE_MEAN"
                                    }
                                }
                            }
                        }],
                        "y_axis": {"label": "Duration (s)", "scale": "LINEAR"}
                    }
                },
                # Chart: Throughput
                {
                    "title": "Throughput",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'metric.type="{metric_prefix}/throughput" resource.type="global"',
                                    "aggregation": {
                                        "alignment_period": "60s",
                                        "per_series_aligner": "ALIGN_MEAN"
                                    }
                                }
                            }
                        }],
                        "y_axis": {"label": "Items/sec", "scale": "LINEAR"}
                    }
                },
                # Chart: Active Workers
                {
                    "title": "Active Workers",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'metric.type="{metric_prefix}/workers_active" resource.type="global"',
                                    "aggregation": {
                                        "alignment_period": "60s",
                                        "per_series_aligner": "ALIGN_MEAN"
                                    }
                                }
                            }
                        }],
                        "y_axis": {"label": "Count", "scale": "LINEAR"}
                    }
                },
                # Chart: Error Rate
                {
                    "title": "Errors",
                    "xy_chart": {
                        "data_sets": [{
                            "time_series_query": {
                                "time_series_filter": {
                                    "filter": f'metric.type="{metric_prefix}/errors_total" resource.type="global"',
                                    "aggregation": {
                                        "alignment_period": "60s",
                                        "per_series_aligner": "ALIGN_RATE"
                                    }
                                }
                            }
                        }],
                        "y_axis": {"label": "Errors/sec", "scale": "LINEAR"}
                    }
                }
            ]
        }
    }
    
    return dashboard


# Deployment helper functions

def deploy_cloudwatch_dashboard(
    dashboard_body: str,
    dashboard_name: str,
    region: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Deploy CloudWatch dashboard using boto3.
    
    Args:
        dashboard_body: Dashboard JSON string
        dashboard_name: Name for the dashboard
        region: AWS region
        
    Returns:
        Response from CloudWatch API
        
    Raises:
        ImportError: If boto3 is not installed
        
    Example:
        >>> dashboard_json = get_cloudwatch_dashboard()
        >>> response = deploy_cloudwatch_dashboard(
        ...     dashboard_json,
        ...     "amorsize-prod-metrics",
        ...     region="us-west-2"
        ... )
    """
    try:
        import boto3
    except ImportError:
        raise ImportError(
            "boto3 is required for CloudWatch dashboard deployment. "
            "Install with: pip install boto3"
        )
    
    client = boto3.client('cloudwatch', region_name=region)
    response = client.put_dashboard(
        DashboardName=dashboard_name,
        DashboardBody=dashboard_body
    )
    
    return response


def deploy_cloudwatch_alarms(
    alarms: List[Dict[str, Any]],
    region: str = "us-east-1"
) -> List[Dict[str, Any]]:
    """
    Deploy CloudWatch alarms using boto3.
    
    Args:
        alarms: List of alarm configurations from get_cloudwatch_alarms()
        region: AWS region
        
    Returns:
        List of responses from CloudWatch API
        
    Raises:
        ImportError: If boto3 is not installed
        
    Example:
        >>> alarms = get_cloudwatch_alarms(
        ...     sns_topic_arn="arn:aws:sns:us-east-1:123456789:alerts"
        ... )
        >>> responses = deploy_cloudwatch_alarms(alarms, region="us-east-1")
    """
    try:
        import boto3
    except ImportError:
        raise ImportError(
            "boto3 is required for CloudWatch alarm deployment. "
            "Install with: pip install boto3"
        )
    
    client = boto3.client('cloudwatch', region_name=region)
    responses = []
    
    for alarm in alarms:
        response = client.put_metric_alarm(**alarm)
        responses.append(response)
    
    return responses
