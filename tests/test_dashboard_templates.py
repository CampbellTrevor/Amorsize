"""
Tests for dashboard templates and alert configurations.

This test module verifies:
- Dashboard template generation
- Alert configuration generation
- Template structure validation
- Deployment helper functions
"""

import json
import pytest


class TestCloudWatchDashboards:
    """Tests for CloudWatch dashboard templates."""
    
    def test_get_cloudwatch_dashboard_basic(self):
        """Test basic CloudWatch dashboard generation."""
        from amorsize.dashboards import get_cloudwatch_dashboard
        
        dashboard_json = get_cloudwatch_dashboard()
        assert dashboard_json is not None
        
        # Parse JSON
        dashboard = json.loads(dashboard_json)
        assert 'widgets' in dashboard
        assert len(dashboard['widgets']) > 0
    
    def test_get_cloudwatch_dashboard_with_dimensions(self):
        """Test CloudWatch dashboard with custom dimensions."""
        from amorsize.dashboards import get_cloudwatch_dashboard
        
        dashboard_json = get_cloudwatch_dashboard(
            namespace="TestApp/Amorsize",
            region="us-west-2",
            dimensions={"Environment": "Test", "Version": "1.0"}
        )
        
        dashboard = json.loads(dashboard_json)
        
        # Verify dashboard structure
        assert 'widgets' in dashboard
        widgets = dashboard['widgets']
        assert len(widgets) == 10  # Expected number of widgets
        
        # Verify first widget has correct region
        first_widget = widgets[0]
        assert first_widget['properties']['region'] == 'us-west-2'
    
    def test_cloudwatch_dashboard_widget_types(self):
        """Test that CloudWatch dashboard has correct widget types."""
        from amorsize.dashboards import get_cloudwatch_dashboard
        
        dashboard_json = get_cloudwatch_dashboard()
        dashboard = json.loads(dashboard_json)
        
        # Check widget types
        widget_types = set()
        for widget in dashboard['widgets']:
            view_type = widget['properties'].get('view', 'unknown')
            widget_types.add(view_type)
        
        # Should have both single value (KPI) and time series widgets
        assert 'singleValue' in widget_types
        assert 'timeSeries' in widget_types
    
    def test_cloudwatch_dashboard_metrics(self):
        """Test that CloudWatch dashboard includes all expected metrics."""
        from amorsize.dashboards import get_cloudwatch_dashboard
        
        dashboard_json = get_cloudwatch_dashboard()
        dashboard = json.loads(dashboard_json)
        
        # Collect all metric names
        metrics = set()
        for widget in dashboard['widgets']:
            for metric in widget['properties']['metrics']:
                if len(metric) >= 2:
                    # Handle both string and dict entries
                    metric_name = metric[1] if isinstance(metric[1], str) else None
                    if metric_name:
                        metrics.add(metric_name)
        
        # Verify key metrics are present
        expected_metrics = {
            'ExecutionsTotal',
            'ItemsProcessed',
            'ExecutionDuration',
            'ErrorsTotal',
            'Throughput',
            'WorkersActive',
            'PercentComplete',
            'ChunkDuration'
        }
        
        assert expected_metrics.issubset(metrics)


class TestCloudWatchAlarms:
    """Tests for CloudWatch alarm configurations."""
    
    def test_get_cloudwatch_alarms_basic(self):
        """Test basic CloudWatch alarm generation."""
        from amorsize.dashboards import get_cloudwatch_alarms
        
        alarms = get_cloudwatch_alarms()
        assert alarms is not None
        assert isinstance(alarms, list)
        assert len(alarms) == 4  # Expected number of alarms
    
    def test_cloudwatch_alarms_structure(self):
        """Test CloudWatch alarm structure."""
        from amorsize.dashboards import get_cloudwatch_alarms
        
        alarms = get_cloudwatch_alarms()
        
        for alarm in alarms:
            # Verify required fields
            assert 'AlarmName' in alarm
            assert 'AlarmDescription' in alarm
            assert 'MetricName' in alarm
            assert 'Namespace' in alarm
            assert 'Period' in alarm
            assert 'EvaluationPeriods' in alarm
            assert 'Threshold' in alarm
            assert 'ComparisonOperator' in alarm
    
    def test_cloudwatch_alarms_with_sns(self):
        """Test CloudWatch alarms with SNS topic."""
        from amorsize.dashboards import get_cloudwatch_alarms
        
        sns_topic = "arn:aws:sns:us-east-1:123456789012:test-topic"
        alarms = get_cloudwatch_alarms(sns_topic_arn=sns_topic)
        
        # Verify all alarms have the SNS topic configured
        for alarm in alarms:
            assert 'AlarmActions' in alarm
            assert sns_topic in alarm['AlarmActions']
    
    def test_cloudwatch_alarm_types(self):
        """Test that all expected alarm types are generated."""
        from amorsize.dashboards import get_cloudwatch_alarms
        
        alarms = get_cloudwatch_alarms()
        
        # Check alarm names
        alarm_names = [alarm['AlarmName'] for alarm in alarms]
        
        # Verify expected alarm types (updated to reflect actual alarm names)
        assert any('HighErrorCount' in name for name in alarm_names)
        assert any('SlowExecution' in name for name in alarm_names)
        assert any('LowThroughput' in name for name in alarm_names)
        assert any('NoExecutions' in name for name in alarm_names)


class TestGrafanaDashboard:
    """Tests for Grafana dashboard templates."""
    
    def test_get_grafana_dashboard_basic(self):
        """Test basic Grafana dashboard generation."""
        from amorsize.dashboards import get_grafana_dashboard
        
        dashboard = get_grafana_dashboard()
        assert dashboard is not None
        assert isinstance(dashboard, dict)
    
    def test_grafana_dashboard_structure(self):
        """Test Grafana dashboard structure."""
        from amorsize.dashboards import get_grafana_dashboard
        
        dashboard = get_grafana_dashboard()
        
        # Verify required fields
        assert 'title' in dashboard
        assert dashboard['title'] == "Amorsize Metrics"
        assert 'panels' in dashboard
        assert len(dashboard['panels']) == 8  # Expected number of panels
        assert 'tags' in dashboard
        assert 'amorsize' in dashboard['tags']
    
    def test_grafana_dashboard_panel_types(self):
        """Test Grafana dashboard panel types."""
        from amorsize.dashboards import get_grafana_dashboard
        
        dashboard = get_grafana_dashboard()
        
        # Collect panel types
        panel_types = set()
        for panel in dashboard['panels']:
            panel_types.add(panel['type'])
        
        # Should have both stat (KPI) and timeseries panels
        assert 'stat' in panel_types
        assert 'timeseries' in panel_types
    
    def test_grafana_dashboard_with_custom_datasource(self):
        """Test Grafana dashboard with custom datasource."""
        from amorsize.dashboards import get_grafana_dashboard
        
        custom_uid = "CUSTOM123"
        dashboard = get_grafana_dashboard(datasource_uid=custom_uid)
        
        # Verify all panels use the custom datasource
        for panel in dashboard['panels']:
            if 'targets' in panel:
                for target in panel['targets']:
                    assert target['datasource']['uid'] == custom_uid


class TestAzureWorkbook:
    """Tests for Azure Monitor workbook templates."""
    
    def test_get_azure_workbook_basic(self):
        """Test basic Azure workbook generation."""
        from amorsize.dashboards import get_azure_monitor_workbook
        
        workbook = get_azure_monitor_workbook()
        assert workbook is not None
        assert isinstance(workbook, dict)
    
    def test_azure_workbook_structure(self):
        """Test Azure workbook structure."""
        from amorsize.dashboards import get_azure_monitor_workbook
        
        workbook = get_azure_monitor_workbook()
        
        # Verify required fields
        assert 'version' in workbook
        assert 'items' in workbook
        assert len(workbook['items']) > 0
    
    def test_azure_workbook_item_types(self):
        """Test Azure workbook has correct item types."""
        from amorsize.dashboards import get_azure_monitor_workbook
        
        workbook = get_azure_monitor_workbook()
        
        # Collect item types
        item_types = set()
        for item in workbook['items']:
            item_types.add(item['type'])
        
        # Should have text (type 1) and query (type 3) items
        assert 1 in item_types  # Text/Markdown
        assert 3 in item_types  # KQL Query


class TestGCPDashboard:
    """Tests for Google Cloud Monitoring dashboard templates."""
    
    def test_get_gcp_dashboard_basic(self):
        """Test basic GCP dashboard generation."""
        from amorsize.dashboards import get_gcp_dashboard
        
        dashboard = get_gcp_dashboard(project_id="test-project")
        assert dashboard is not None
        assert isinstance(dashboard, dict)
    
    def test_gcp_dashboard_structure(self):
        """Test GCP dashboard structure."""
        from amorsize.dashboards import get_gcp_dashboard
        
        dashboard = get_gcp_dashboard(project_id="test-project")
        
        # Verify required fields
        assert 'display_name' in dashboard
        assert 'grid_layout' in dashboard
        assert 'widgets' in dashboard['grid_layout']
        assert len(dashboard['grid_layout']['widgets']) == 6  # Expected widgets
    
    def test_gcp_dashboard_widget_types(self):
        """Test GCP dashboard has correct widget types."""
        from amorsize.dashboards import get_gcp_dashboard
        
        dashboard = get_gcp_dashboard(project_id="test-project")
        
        # Check widget types
        has_scorecard = False
        has_chart = False
        
        for widget in dashboard['grid_layout']['widgets']:
            if 'score_card' in widget:
                has_scorecard = True
            if 'xy_chart' in widget:
                has_chart = True
        
        # Should have both score cards and charts
        assert has_scorecard
        assert has_chart
    
    def test_gcp_dashboard_with_custom_prefix(self):
        """Test GCP dashboard with custom metric prefix."""
        from amorsize.dashboards import get_gcp_dashboard
        
        custom_prefix = "custom.googleapis.com/myapp"
        dashboard = get_gcp_dashboard(
            project_id="test-project",
            metric_prefix=custom_prefix
        )
        
        # Verify widgets use the custom prefix
        widgets = dashboard['grid_layout']['widgets']
        first_widget = widgets[0]
        
        # Extract metric filter (structure varies by widget type)
        if 'score_card' in first_widget:
            filter_str = first_widget['score_card']['time_series_query']['time_series_filter']['filter']
            assert custom_prefix in filter_str


class TestDeploymentHelpers:
    """Tests for dashboard deployment helper functions."""
    
    def test_deploy_cloudwatch_dashboard_requires_boto3(self):
        """Test that deploy_cloudwatch_dashboard requires boto3."""
        from amorsize.dashboards import deploy_cloudwatch_dashboard
        
        # This should raise ImportError if boto3 is not installed
        # We can't actually deploy without AWS credentials, so we just test the import check
        try:
            # Try to import boto3
            import boto3
            # If boto3 is available, we can't test the ImportError path
            pytest.skip("boto3 is installed, can't test ImportError path")
        except ImportError:
            # boto3 not installed - function should raise ImportError
            with pytest.raises(ImportError, match="boto3 is required"):
                deploy_cloudwatch_dashboard("{}", "test-dashboard")
    
    def test_deploy_cloudwatch_alarms_requires_boto3(self):
        """Test that deploy_cloudwatch_alarms requires boto3."""
        from amorsize.dashboards import deploy_cloudwatch_alarms
        
        try:
            import boto3
            pytest.skip("boto3 is installed, can't test ImportError path")
        except ImportError:
            with pytest.raises(ImportError, match="boto3 is required"):
                deploy_cloudwatch_alarms([])


class TestTemplateIntegration:
    """Integration tests for dashboard templates."""
    
    def test_all_templates_generate_valid_json(self):
        """Test that all templates generate valid JSON."""
        from amorsize.dashboards import (
            get_cloudwatch_dashboard,
            get_cloudwatch_alarms,
            get_grafana_dashboard,
            get_azure_monitor_workbook,
            get_gcp_dashboard
        )
        
        # CloudWatch dashboard
        cw_dashboard = get_cloudwatch_dashboard()
        json.loads(cw_dashboard)  # Should not raise
        
        # CloudWatch alarms
        alarms = get_cloudwatch_alarms()
        json.dumps(alarms, default=str)  # Should not raise
        
        # Grafana dashboard
        grafana_dash = get_grafana_dashboard()
        json.dumps(grafana_dash)  # Should not raise
        
        # Azure workbook
        azure_wb = get_azure_monitor_workbook()
        json.dumps(azure_wb)  # Should not raise
        
        # GCP dashboard
        gcp_dash = get_gcp_dashboard(project_id="test")
        json.dumps(gcp_dash)  # Should not raise
    
    def test_templates_are_not_empty(self):
        """Test that all templates contain meaningful content."""
        from amorsize.dashboards import (
            get_cloudwatch_dashboard,
            get_cloudwatch_alarms,
            get_grafana_dashboard,
            get_azure_monitor_workbook,
            get_gcp_dashboard
        )
        
        # All templates should have substantial content (> 100 chars)
        assert len(get_cloudwatch_dashboard()) > 100
        assert len(json.dumps(get_cloudwatch_alarms())) > 100
        assert len(json.dumps(get_grafana_dashboard())) > 100
        assert len(json.dumps(get_azure_monitor_workbook())) > 100
        assert len(json.dumps(get_gcp_dashboard(project_id="test"))) > 100


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
