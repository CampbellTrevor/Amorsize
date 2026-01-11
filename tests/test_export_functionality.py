"""
Tests for the --export CLI flag functionality.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from amorsize import optimize


class TestExportFunctionality:
    """Test the --export flag functionality."""

    def test_export_json_basic(self):
        """Test basic JSON export without profiling."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        try:
            # Run optimization with export
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '100',
                    '--export', export_path,
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Check file was created
            assert os.path.exists(export_path)

            # Load and verify JSON structure
            with open(export_path, 'r') as f:
                data = json.load(f)

            assert data['mode'] == 'optimize'
            assert 'n_jobs' in data
            assert 'chunksize' in data
            assert 'estimated_speedup' in data
            assert 'reason' in data

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_json_with_profile(self):
        """Test JSON export with diagnostic profiling."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        try:
            # Run optimization with export and profiling
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '1000',
                    '--profile',
                    '--export', export_path,
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Check file was created
            assert os.path.exists(export_path)

            # Load and verify JSON structure
            with open(export_path, 'r') as f:
                data = json.load(f)

            assert data['mode'] == 'optimize'
            assert 'profile' in data
            
            profile = data['profile']
            assert 'physical_cores' in profile
            assert 'logical_cores' in profile
            assert 'spawn_cost_ms' in profile
            assert 'available_memory_gb' in profile
            assert 'avg_execution_time_ms' in profile

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_yaml_auto_detection(self):
        """Test YAML export with automatic format detection from extension."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            export_path = f.name

        try:
            # Run optimization with export
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '100',
                    '--export', export_path,
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Check file was created
            assert os.path.exists(export_path)

            # Load file content
            with open(export_path, 'r') as f:
                content = f.read()

            # YAML format should have key: value pairs
            assert 'mode: optimize' in content or 'mode:' in content
            assert 'n_jobs:' in content
            assert 'chunksize:' in content

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_yaml_explicit_format(self):
        """Test YAML export with explicit --export-format flag."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            export_path = f.name

        try:
            # Run optimization with export and explicit YAML format
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.factorial',
                    '--data-range', '200',
                    '--export', export_path,
                    '--export-format', 'yaml',
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Check file was created
            assert os.path.exists(export_path)

            # Load file content
            with open(export_path, 'r') as f:
                content = f.read()

            # YAML format should have key: value pairs
            assert 'mode:' in content
            assert 'n_jobs:' in content

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_execute_command(self):
        """Test export functionality with execute command."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        try:
            # Run execute with export
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'execute', 'math.sqrt',
                    '--data-range', '100',
                    '--export', export_path,
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Check file was created
            assert os.path.exists(export_path)

            # Load and verify JSON structure
            with open(export_path, 'r') as f:
                data = json.load(f)

            # Execute mode should include optimization result
            assert 'n_jobs' in data
            assert 'chunksize' in data

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_with_verbose_flag(self):
        """Test that verbose flag shows export confirmation."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        try:
            # Run optimization with export and verbose
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '100',
                    '--export', export_path,
                    '--verbose'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Check that verbose output mentions the export
            assert 'export' in result.stdout.lower() or 'Diagnostics exported' in result.stdout

            # Check file was created
            assert os.path.exists(export_path)

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_overwrite_existing_file(self):
        """Test that export overwrites existing files."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
            # Write some content
            f.write('{"old": "data"}')

        try:
            # Run optimization with export
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '100',
                    '--export', export_path,
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Load and verify new content
            with open(export_path, 'r') as f:
                data = json.load(f)

            # Should have new data, not old data
            assert 'old' not in data
            assert 'n_jobs' in data

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_invalid_path_error(self):
        """Test that invalid export path produces error."""
        import subprocess
        import sys

        # Try to export to an invalid directory
        invalid_path = '/nonexistent_directory_12345/export.json'

        result = subprocess.run(
            [
                sys.executable, '-m', 'amorsize',
                'optimize', 'math.sqrt',
                '--data-range', '100',
                '--export', invalid_path,
                '--quiet'
            ],
            capture_output=True,
            text=True
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0
        # Error message should mention export
        assert 'export' in result.stderr.lower() or 'error' in result.stderr.lower()

    def test_export_json_fallback_without_yaml(self):
        """Test that YAML export falls back to JSON if PyYAML not available."""
        # This test assumes PyYAML is installed, so we just verify the export works
        # In real scenario without PyYAML, it should export as JSON
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            export_path = f.name

        try:
            # Run optimization with YAML export
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '100',
                    '--export', export_path,
                    '--export-format', 'yaml',
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Check file was created
            assert os.path.exists(export_path)

            # Load file content - should be valid YAML or JSON
            with open(export_path, 'r') as f:
                content = f.read()

            # Should have structured data
            assert 'n_jobs' in content

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)


class TestExportContentQuality:
    """Test the quality and completeness of exported data."""

    def test_export_contains_all_basic_fields(self):
        """Test that basic export contains all required fields."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '100',
                    '--export', export_path,
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            with open(export_path, 'r') as f:
                data = json.load(f)

            # Required fields
            required_fields = ['mode', 'n_jobs', 'chunksize', 'estimated_speedup', 'reason']
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)

    def test_export_profile_completeness(self):
        """Test that profile export contains comprehensive diagnostic data."""
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'amorsize',
                    'optimize', 'math.sqrt',
                    '--data-range', '1000',
                    '--profile',
                    '--export', export_path,
                    '--quiet'
                ],
                capture_output=True,
                text=True,
                check=True
            )

            with open(export_path, 'r') as f:
                data = json.load(f)

            assert 'profile' in data
            profile = data['profile']

            # Check for important profile fields
            important_fields = [
                'physical_cores',
                'logical_cores',
                'spawn_cost_ms',
                'available_memory_gb',
                'avg_execution_time_ms',
                'start_method',
                'workload_type'
            ]

            for field in important_fields:
                assert field in profile, f"Missing profile field: {field}"

        finally:
            if os.path.exists(export_path):
                os.unlink(export_path)
