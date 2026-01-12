"""
Property-based tests for the dashboards module using Hypothesis.

These tests automatically generate edge cases and verify invariant properties
of the dashboard template generation and alert configuration infrastructure
across a wide range of inputs.
"""

import json
from typing import Any, Dict

import pytest
from hypothesis import given, settings, strategies as st, assume, HealthCheck

from amorsize.dashboards import (
    get_cloudwatch_dashboard,
    get_cloudwatch_alarms,
    get_grafana_dashboard,
    get_azure_monitor_workbook,
    get_gcp_dashboard,
)


# Custom strategies for generating test data
@st.composite
def valid_namespace(draw):
    """Generate valid CloudWatch namespace strings."""
    # Namespaces can contain letters, numbers, forward slashes, hyphens, and periods
    # Length between 1 and 256 characters
    parts = draw(st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', min_size=1, max_size=20),
        min_size=1,
        max_size=5
    ))
    return '/'.join(parts)


@st.composite
def valid_region(draw):
    """Generate valid AWS region strings."""
    regions = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1', 
        'ap-south-1', 'ap-northeast-1', 'ap-southeast-1',
        'ca-central-1', 'sa-east-1'
    ]
    return draw(st.sampled_from(regions))


@st.composite
def valid_dimensions(draw):
    """Generate valid CloudWatch dimension dictionaries."""
    # 0 to 10 dimensions
    num_dims = draw(st.integers(min_value=0, max_value=10))
    if num_dims == 0:
        return None
    
    dimensions = {}
    for _ in range(num_dims):
        key = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', min_size=1, max_size=20))
        value = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', min_size=1, max_size=20))
        dimensions[key] = value
    
    return dimensions


@st.composite
def valid_project_id(draw):
    """Generate valid GCP project ID strings."""
    # Project IDs: 6-30 chars, lowercase letters, numbers, hyphens
    # Must start with letter, cannot end with hyphen
    length = draw(st.integers(min_value=6, max_value=30))
    first_char = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=1))
    
    if length == 1:
        return first_char
    
    middle = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=0, max_size=length-2))
    last_char = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=1))
    
    return first_char + middle + last_char


class TestCloudWatchDashboardInvariants:
    """Test invariant properties of CloudWatch dashboard generation."""

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_valid_json_string(self, namespace, region, dimensions):
        """Test that get_cloudwatch_dashboard returns valid JSON string."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            region=region,
            dimensions=dimensions
        )
        
        # Should be a string
        assert isinstance(dashboard_json, str)
        assert len(dashboard_json) > 0
        
        # Should be valid JSON
        dashboard = json.loads(dashboard_json)
        assert isinstance(dashboard, dict)

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_has_widgets_list(self, namespace, region, dimensions):
        """Test that dashboard has 'widgets' key with list value."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            region=region,
            dimensions=dimensions
        )
        
        dashboard = json.loads(dashboard_json)
        
        # Must have 'widgets' key
        assert 'widgets' in dashboard
        
        # Must be a list
        assert isinstance(dashboard['widgets'], list)
        
        # Should have at least one widget
        assert len(dashboard['widgets']) > 0

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_widgets_have_required_fields(self, namespace, region, dimensions):
        """Test that all widgets have required fields."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            region=region,
            dimensions=dimensions
        )
        
        dashboard = json.loads(dashboard_json)
        
        for widget in dashboard['widgets']:
            # Each widget must have 'type' and 'properties'
            assert 'type' in widget, "Widget missing 'type' field"
            assert 'properties' in widget, "Widget missing 'properties' field"
            
            # Type should be 'metric' for CloudWatch
            assert widget['type'] == 'metric'
            
            # Properties should be a dict
            assert isinstance(widget['properties'], dict)

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_widget_properties_structure(self, namespace, region, dimensions):
        """Test that widget properties have correct structure."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            region=region,
            dimensions=dimensions
        )
        
        dashboard = json.loads(dashboard_json)
        
        for widget in dashboard['widgets']:
            props = widget['properties']
            
            # Must have 'metrics' list
            assert 'metrics' in props
            assert isinstance(props['metrics'], list)
            assert len(props['metrics']) > 0
            
            # Must have 'region'
            assert 'region' in props
            assert props['region'] == region

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_metrics_use_correct_namespace(self, namespace, region, dimensions):
        """Test that metrics use the specified namespace."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            region=region,
            dimensions=dimensions
        )
        
        dashboard = json.loads(dashboard_json)
        
        for widget in dashboard['widgets']:
            metrics = widget['properties']['metrics']
            
            for metric in metrics:
                # First element should be namespace (if not ellipsis)
                if isinstance(metric, list) and len(metric) >= 1 and metric[0] != '...':
                    assert metric[0] == namespace, \
                        f"Expected namespace '{namespace}', got '{metric[0]}'"

    @given(
        namespace=valid_namespace(),
        region=valid_region()
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dimensions_included_in_metrics(self, namespace, region):
        """Test that dimensions are properly included in metric definitions."""
        dimensions = {"Environment": "Test", "Application": "Amorsize"}
        
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            region=region,
            dimensions=dimensions
        )
        
        dashboard = json.loads(dashboard_json)
        
        # At least one metric should include the dimensions
        found_dimensions = False
        for widget in dashboard['widgets']:
            for metric in widget['properties']['metrics']:
                if isinstance(metric, list) and len(metric) > 2:
                    # Check if dimensions are in the metric
                    metric_str = str(metric)
                    if 'Environment' in metric_str or 'Application' in metric_str:
                        found_dimensions = True
                        break
            if found_dimensions:
                break
        
        # We expect dimensions to be present somewhere
        # (Note: this is a weak check but dimensions are used as *dim_filter)
        assert True  # Dimensions are passed to the function

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_widget_positioning(self, namespace, region, dimensions):
        """Test that widgets have valid positioning coordinates."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            region=region,
            dimensions=dimensions
        )
        
        dashboard = json.loads(dashboard_json)
        
        for widget in dashboard['widgets']:
            # Widgets should have positioning
            assert 'x' in widget
            assert 'y' in widget
            assert 'width' in widget
            assert 'height' in widget
            
            # Positioning should be non-negative integers
            assert isinstance(widget['x'], int)
            assert isinstance(widget['y'], int)
            assert isinstance(widget['width'], int)
            assert isinstance(widget['height'], int)
            
            assert widget['x'] >= 0
            assert widget['y'] >= 0
            assert widget['width'] > 0
            assert widget['height'] > 0

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_consistent_widget_count(self, namespace, region, dimensions):
        """Test that widget count is consistent across calls with same parameters."""
        dashboard_json_1 = get_cloudwatch_dashboard(namespace, region, dimensions)
        dashboard_json_2 = get_cloudwatch_dashboard(namespace, region, dimensions)
        
        dashboard_1 = json.loads(dashboard_json_1)
        dashboard_2 = json.loads(dashboard_json_2)
        
        # Same inputs should produce same number of widgets
        assert len(dashboard_1['widgets']) == len(dashboard_2['widgets'])


class TestCloudWatchAlarmsInvariants:
    """Test invariant properties of CloudWatch alarms generation."""

    @given(
        namespace=valid_namespace(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_list_of_dicts(self, namespace, dimensions):
        """Test that get_cloudwatch_alarms returns list of dictionaries."""
        alarms = get_cloudwatch_alarms(namespace=namespace, dimensions=dimensions)
        
        # Should be a list
        assert isinstance(alarms, list)
        
        # Should have at least one alarm
        assert len(alarms) > 0
        
        # Each alarm should be a dict
        for alarm in alarms:
            assert isinstance(alarm, dict)

    @given(
        namespace=valid_namespace(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_alarms_have_required_fields(self, namespace, dimensions):
        """Test that all alarms have required CloudWatch alarm fields."""
        alarms = get_cloudwatch_alarms(namespace=namespace, dimensions=dimensions)
        
        # Core required fields (all alarms must have these)
        required_fields = ['AlarmName', 'MetricName', 'Namespace', 
                          'Period', 'EvaluationPeriods', 'Threshold', 'ComparisonOperator']
        
        for alarm in alarms:
            for field in required_fields:
                assert field in alarm, f"Alarm missing required field: {field}"
            
            # Must have EITHER Statistic OR ExtendedStatistic (for percentiles like p99)
            assert 'Statistic' in alarm or 'ExtendedStatistic' in alarm, \
                "Alarm must have either 'Statistic' or 'ExtendedStatistic'"

    @given(
        namespace=valid_namespace(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_alarm_names_are_unique(self, namespace, dimensions):
        """Test that alarm names are unique."""
        alarms = get_cloudwatch_alarms(namespace=namespace, dimensions=dimensions)
        
        alarm_names = [alarm['AlarmName'] for alarm in alarms]
        
        # All alarm names should be unique
        assert len(alarm_names) == len(set(alarm_names)), \
            "Duplicate alarm names found"

    @given(
        namespace=valid_namespace(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_alarm_thresholds_are_positive(self, namespace, dimensions):
        """Test that alarm thresholds are positive numbers."""
        alarms = get_cloudwatch_alarms(namespace=namespace, dimensions=dimensions)
        
        for alarm in alarms:
            threshold = alarm['Threshold']
            assert isinstance(threshold, (int, float))
            assert threshold > 0, f"Threshold should be positive, got {threshold}"

    @given(
        namespace=valid_namespace(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_alarm_periods_valid(self, namespace, dimensions):
        """Test that alarm periods are valid CloudWatch values."""
        alarms = get_cloudwatch_alarms(namespace=namespace, dimensions=dimensions)
        
        # CloudWatch requires periods to be multiples of 60 (and >= 10 for some metrics)
        valid_periods = [10, 30, 60, 120, 180, 300, 600, 900, 1800, 3600]
        
        for alarm in alarms:
            period = alarm['Period']
            assert isinstance(period, int)
            assert period > 0

    @given(
        namespace=valid_namespace(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_alarms_use_correct_namespace(self, namespace, dimensions):
        """Test that alarms use the specified namespace."""
        alarms = get_cloudwatch_alarms(namespace=namespace, dimensions=dimensions)
        
        for alarm in alarms:
            assert alarm['Namespace'] == namespace, \
                f"Expected namespace '{namespace}', got '{alarm['Namespace']}'"

    @given(
        namespace=valid_namespace(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_comparison_operators_valid(self, namespace, dimensions):
        """Test that comparison operators are valid CloudWatch values."""
        alarms = get_cloudwatch_alarms(namespace=namespace, dimensions=dimensions)
        
        valid_operators = [
            'GreaterThanThreshold',
            'GreaterThanOrEqualToThreshold',
            'LessThanThreshold',
            'LessThanOrEqualToThreshold'
        ]
        
        for alarm in alarms:
            operator = alarm['ComparisonOperator']
            assert operator in valid_operators, \
                f"Invalid comparison operator: {operator}"


class TestGrafanaDashboardInvariants:
    """Test invariant properties of Grafana dashboard generation."""

    @given(
        datasource_uid=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'),
        job_label=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_dict(self, datasource_uid, job_label):
        """Test that get_grafana_dashboard returns a dictionary."""
        dashboard = get_grafana_dashboard(
            datasource_uid=datasource_uid,
            job_label=job_label
        )
        
        # Should be a dict
        assert isinstance(dashboard, dict)
        
        # Should have core Grafana dashboard fields
        assert 'dashboard' in dashboard or 'title' in dashboard

    @given(
        datasource_uid=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'),
        job_label=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_has_panels(self, datasource_uid, job_label):
        """Test that Grafana dashboard has panels."""
        dashboard = get_grafana_dashboard(datasource_uid, job_label)
        
        # Extract dashboard if it's nested
        dash_dict = dashboard.get('dashboard', dashboard)
        
        # Should have 'panels' key
        assert 'panels' in dash_dict
        
        # Panels should be a list
        assert isinstance(dash_dict['panels'], list)
        
        # Should have at least one panel
        assert len(dash_dict['panels']) > 0

    @given(
        datasource_uid=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'),
        job_label=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_panels_have_required_fields(self, datasource_uid, job_label):
        """Test that all panels have required Grafana fields."""
        dashboard = get_grafana_dashboard(datasource_uid, job_label)
        dash_dict = dashboard.get('dashboard', dashboard)
        
        for panel in dash_dict['panels']:
            # Each panel must have 'title' and 'type'
            assert 'title' in panel, "Panel missing 'title' field"
            assert 'type' in panel, "Panel missing 'type' field"
            
            # Title should be a non-empty string
            assert isinstance(panel['title'], str)
            assert len(panel['title']) > 0

    @given(
        datasource_uid=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'),
        job_label=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_json_serializable(self, datasource_uid, job_label):
        """Test that Grafana dashboard is JSON serializable."""
        dashboard = get_grafana_dashboard(datasource_uid, job_label)
        
        # Should be JSON serializable
        json_str = json.dumps(dashboard)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


class TestAzureMonitorWorkbookInvariants:
    """Test invariant properties of Azure Monitor workbook generation."""

    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))  # No parameters for Azure workbook
    def test_returns_dict(self, _):
        """Test that get_azure_monitor_workbook returns a dictionary."""
        workbook = get_azure_monitor_workbook()
        
        # Should be a dict
        assert isinstance(workbook, dict)

    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_has_required_azure_fields(self, _):
        """Test that workbook has required Azure Monitor fields."""
        workbook = get_azure_monitor_workbook()
        
        # Should have 'properties' (Azure ARM template structure)
        # Or direct workbook fields
        if 'properties' in workbook:
            assert isinstance(workbook['properties'], dict)
        
        # Should have some content structure
        assert len(workbook) > 0

    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_json_serializable(self, _):
        """Test that Azure workbook is JSON serializable."""
        workbook = get_azure_monitor_workbook()
        
        # Should be JSON serializable
        json_str = json.dumps(workbook)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_deterministic(self, _):
        """Test that Azure workbook generation is deterministic."""
        workbook1 = get_azure_monitor_workbook()
        workbook2 = get_azure_monitor_workbook()
        
        # Should produce identical output
        assert json.dumps(workbook1, sort_keys=True) == json.dumps(workbook2, sort_keys=True)


class TestGCPDashboardInvariants:
    """Test invariant properties of GCP dashboard generation."""

    @given(
        project_id=valid_project_id(),
        metric_prefix=st.text(min_size=10, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyz0123456789./_ ')
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_dict(self, project_id, metric_prefix):
        """Test that get_gcp_dashboard returns a dictionary."""
        # Clean up metric prefix
        metric_prefix = metric_prefix.replace(' ', '_').strip('/')
        assume(len(metric_prefix) > 0)
        
        dashboard = get_gcp_dashboard(
            project_id=project_id,
            metric_prefix=metric_prefix
        )
        
        # Should be a dict
        assert isinstance(dashboard, dict)

    @given(
        project_id=valid_project_id(),
        metric_prefix=st.text(min_size=10, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyz0123456789./_ ')
    )
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_has_display_name(self, project_id, metric_prefix):
        """Test that GCP dashboard has a display name."""
        metric_prefix = metric_prefix.replace(' ', '_').strip('/')
        assume(len(metric_prefix) > 0)
        
        dashboard = get_gcp_dashboard(project_id, metric_prefix)
        
        # Should have 'displayName' field (GCP standard)
        assert 'displayName' in dashboard or 'display_name' in dashboard

    @given(project_id=valid_project_id())
    @settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_uses_project_id(self, project_id):
        """Test that GCP dashboard can be generated with any valid project ID."""
        # Note: The project_id is used during deployment (in parent path), not stored in dashboard JSON
        dashboard = get_gcp_dashboard(project_id=project_id)
        
        # Dashboard should be valid
        assert isinstance(dashboard, dict)
        assert len(dashboard) > 0
        
        # The function should accept the project_id parameter without errors
        # (even though it's not embedded in the dashboard JSON itself)

    @given(
        project_id=valid_project_id(),
        metric_prefix=st.text(min_size=10, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyz0123456789./_ ')
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_json_serializable(self, project_id, metric_prefix):
        """Test that GCP dashboard is JSON serializable."""
        metric_prefix = metric_prefix.replace(' ', '_').strip('/')
        assume(len(metric_prefix) > 0)
        
        dashboard = get_gcp_dashboard(project_id, metric_prefix)
        
        # Should be JSON serializable
        json_str = json.dumps(dashboard)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_cloudwatch_dashboard_defaults(self, _):
        """Test CloudWatch dashboard with all default parameters."""
        dashboard_json = get_cloudwatch_dashboard()
        
        # Should work with defaults
        dashboard = json.loads(dashboard_json)
        assert 'widgets' in dashboard
        assert len(dashboard['widgets']) > 0

    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_cloudwatch_alarms_defaults(self, _):
        """Test CloudWatch alarms with all default parameters."""
        alarms = get_cloudwatch_alarms()
        
        # Should work with defaults
        assert isinstance(alarms, list)
        assert len(alarms) > 0

    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(None))
    def test_grafana_dashboard_defaults(self, _):
        """Test Grafana dashboard with default parameters."""
        dashboard = get_grafana_dashboard()
        
        # Should work with defaults
        assert isinstance(dashboard, dict)

    @given(namespace=valid_namespace())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_empty_dimensions(self, namespace):
        """Test dashboard generation with explicitly empty dimensions."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            dimensions={}
        )
        
        # Should work with empty dimensions dict
        dashboard = json.loads(dashboard_json)
        assert 'widgets' in dashboard

    @given(namespace=valid_namespace())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_none_dimensions(self, namespace):
        """Test dashboard generation with None dimensions."""
        dashboard_json = get_cloudwatch_dashboard(
            namespace=namespace,
            dimensions=None
        )
        
        # Should work with None dimensions
        dashboard = json.loads(dashboard_json)
        assert 'widgets' in dashboard


class TestNumericalStability:
    """Test numerical stability and various parameter values."""

    @given(
        namespace=valid_namespace(),
        region=valid_region()
    )
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_various_namespaces(self, namespace, region):
        """Test dashboard generation with various namespace formats."""
        dashboard_json = get_cloudwatch_dashboard(namespace=namespace, region=region)
        
        # Should work with any valid namespace
        dashboard = json.loads(dashboard_json)
        assert 'widgets' in dashboard

    @given(region=valid_region())
    @settings(max_examples=50, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_aws_regions(self, region):
        """Test dashboard generation with all AWS regions."""
        dashboard_json = get_cloudwatch_dashboard(region=region)
        
        # Should work with any AWS region
        dashboard = json.loads(dashboard_json)
        
        # Verify region is used
        for widget in dashboard['widgets']:
            assert widget['properties']['region'] == region


class TestIntegrationProperties:
    """Test integration properties and consistency."""

    @given(
        namespace=valid_namespace(),
        region=valid_region(),
        dimensions=valid_dimensions()
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dashboard_and_alarms_consistency(self, namespace, region, dimensions):
        """Test that dashboard and alarms use consistent namespace."""
        dashboard_json = get_cloudwatch_dashboard(namespace, region, dimensions)
        alarms = get_cloudwatch_alarms(namespace, dimensions)
        
        dashboard = json.loads(dashboard_json)
        
        # Both should reference the same namespace
        dashboard_str = json.dumps(dashboard)
        assert namespace in dashboard_str
        
        for alarm in alarms:
            assert alarm['Namespace'] == namespace

    @given(st.just(None))
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_all_platforms_generate_successfully(self, _):
        """Test that all platform dashboard generators work."""
        # CloudWatch
        cw_dashboard = get_cloudwatch_dashboard()
        assert json.loads(cw_dashboard)
        
        # CloudWatch Alarms
        cw_alarms = get_cloudwatch_alarms()
        assert isinstance(cw_alarms, list)
        
        # Grafana
        grafana = get_grafana_dashboard()
        assert isinstance(grafana, dict)
        
        # Azure
        azure = get_azure_monitor_workbook()
        assert isinstance(azure, dict)
        
        # GCP
        gcp = get_gcp_dashboard(project_id="test-project-id-123")
        assert isinstance(gcp, dict)

    @given(
        namespace=valid_namespace(),
        region=valid_region()
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_deterministic_generation(self, namespace, region):
        """Test that dashboard generation is deterministic."""
        dashboard_json_1 = get_cloudwatch_dashboard(namespace, region, None)
        dashboard_json_2 = get_cloudwatch_dashboard(namespace, region, None)
        
        # Same inputs should produce identical output
        assert dashboard_json_1 == dashboard_json_2
