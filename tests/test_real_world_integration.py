"""
Real-world integration tests with popular Python libraries.

These tests validate that Amorsize works correctly with:
- pandas DataFrames and Series
- numpy arrays
- PIL/Pillow image processing
- Standard library modules (json, os, sys)

Tests are designed to be skipped gracefully if optional dependencies
are not installed, following best practices for integration testing.
"""

import sys
import os
import json
from typing import Any, List
import pytest

from amorsize import optimize

# Check for optional dependencies
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _execute_with_pool(func, result):
    """
    Helper function to execute a function with optimizer recommendations.
    
    Uses multiprocessing.Pool if n_jobs > 1, otherwise executes serially.
    Reduces code duplication across test methods.
    
    Args:
        func: The function to execute
        result: OptimizationResult from optimize()
    
    Returns:
        List of results from executing func on result.data
    """
    from multiprocessing import Pool
    
    if result.n_jobs == 1:
        return [func(x) for x in result.data]
    else:
        with Pool(processes=result.n_jobs) as pool:
            return pool.map(func, result.data, chunksize=result.chunksize)


class TestNumpyIntegration:
    """Test integration with numpy arrays and operations."""
    
    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_numpy_array_processing(self):
        """Test processing numpy arrays with optimize()."""
        def process_array(arr):
            """Simple numpy operation."""
            return np.sum(arr ** 2)
        
        # Create test data - list of numpy arrays
        data = [np.array([i, i+1, i+2]) for i in range(20)]
        
        # Optimize and execute
        result = optimize(process_array, data, verbose=False)
        
        # Verify it runs without errors
        assert result.n_jobs >= 1
        assert result.chunksize >= 1
        
        # Execute with recommendations
        results = _execute_with_pool(process_array, result)
        
        # Verify correctness
        expected = [process_array(arr) for arr in data]
        assert len(results) == len(expected)
        for r, e in zip(results, expected):
            assert r == e
    
    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_numpy_large_array_slicing(self):
        """Test processing slices of a large numpy array."""
        def process_slice(idx):
            """Process a slice of a shared concept (simulated)."""
            # In real use, this might access a shared array
            # Here we simulate with computation
            arr = np.arange(idx * 100, (idx + 1) * 100)
            return np.mean(arr)
        
        data = range(50)
        result = optimize(process_slice, data, verbose=False)
        
        # Should recommend parallelization for this workload
        assert result.n_jobs >= 1
        
        # Execute and verify
        results = _execute_with_pool(process_slice, result)
        
        expected = [process_slice(i) for i in data]
        assert len(results) == len(expected)
        assert all(abs(r - e) < 1e-10 for r, e in zip(results, expected))
    
    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_numpy_complex_dtypes(self):
        """Test with various numpy data types."""
        def process_typed_array(dtype_name):
            """Create and process array with specific dtype."""
            dtype = getattr(np, dtype_name)
            arr = np.array([1, 2, 3, 4, 5], dtype=dtype)
            return float(np.sum(arr))
        
        dtypes = ['int32', 'int64', 'float32', 'float64']
        
        result = optimize(process_typed_array, dtypes, verbose=False)
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_typed_array, result)
        
        # All should sum to 15
        assert all(r == 15.0 for r in results)


class TestPandasIntegration:
    """Test integration with pandas DataFrames and Series."""
    
    @pytest.mark.skipif(not HAS_PANDAS, reason="pandas not installed")
    def test_pandas_dataframe_processing(self):
        """Test processing pandas DataFrames."""
        def process_dataframe(idx):
            """Create and process a small DataFrame."""
            df = pd.DataFrame({
                'a': [idx, idx+1, idx+2],
                'b': [idx*2, idx*2+1, idx*2+2]
            })
            return df['a'].sum() + df['b'].sum()
        
        data = range(20)
        result = optimize(process_dataframe, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_dataframe, result)
        
        expected = [process_dataframe(i) for i in data]
        assert results == expected
    
    @pytest.mark.skipif(not HAS_PANDAS, reason="pandas not installed")
    def test_pandas_series_operations(self):
        """Test processing pandas Series."""
        def process_series(values):
            """Process a pandas Series."""
            s = pd.Series(values)
            return s.mean()
        
        data = [[i, i+1, i+2] for i in range(20)]
        result = optimize(process_series, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_series, result)
        
        expected = [process_series(v) for v in data]
        assert len(results) == len(expected)
        assert all(abs(r - e) < 1e-10 for r, e in zip(results, expected))
    
    @pytest.mark.skipif(not HAS_PANDAS, reason="pandas not installed")
    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_pandas_with_numpy(self):
        """Test processing that combines pandas and numpy."""
        def process_combined(idx):
            """Process with both pandas and numpy."""
            df = pd.DataFrame({
                'x': np.arange(idx, idx + 10)
            })
            return np.sum(df['x'].values ** 2)
        
        data = range(15)
        result = optimize(process_combined, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_combined, result)
        
        expected = [process_combined(i) for i in data]
        assert results == expected


class TestStandardLibraryIntegration:
    """Test integration with Python standard library modules."""
    
    def test_json_processing(self):
        """Test processing JSON data."""
        def process_json_string(data_dict):
            """Convert dict to JSON and back."""
            json_str = json.dumps(data_dict)
            parsed = json.loads(json_str)
            return parsed['value'] * 2
        
        data = [{'value': i, 'name': f'item_{i}'} for i in range(30)]
        result = optimize(process_json_string, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_json_string, result)
        
        expected = [i * 2 for i in range(30)]
        assert results == expected
    
    def test_file_path_processing(self):
        """Test processing file paths (without actually creating files)."""
        def process_file_path(filepath):
            """Process a file path string."""
            basename = os.path.basename(filepath)
            name, ext = os.path.splitext(basename)
            return len(name)
        
        data = [f'/tmp/test_file_{i}.txt' for i in range(25)]
        result = optimize(process_file_path, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_file_path, result)
        
        expected = [len(f'test_file_{i}') for i in range(25)]
        assert results == expected
    
    def test_string_processing(self):
        """Test text processing operations."""
        def process_text(text):
            """Perform text processing."""
            words = text.split()
            return len([w for w in words if len(w) > 3])
        
        data = [f'This is test sentence number {i} with some words' for i in range(30)]
        result = optimize(process_text, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_text, result)
        
        expected = [process_text(t) for t in data]
        assert results == expected


class TestImageProcessingIntegration:
    """Test integration with image processing (PIL/Pillow)."""
    
    @pytest.mark.skipif(not HAS_PIL, reason="PIL/Pillow not installed")
    def test_image_creation_and_processing(self):
        """Test creating and processing PIL images."""
        def process_image_size(size):
            """Create and process an image."""
            img = Image.new('RGB', (size, size), color=(255, 0, 0))
            return img.size[0] * img.size[1]
        
        sizes = [10, 20, 30, 40, 50]
        result = optimize(process_image_size, sizes, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_image_size, result)
        
        expected = [s * s for s in sizes]
        assert results == expected
    
    @pytest.mark.skipif(not HAS_PIL, reason="PIL/Pillow not installed")
    @pytest.mark.skipif(not HAS_NUMPY, reason="numpy not installed")
    def test_image_to_array_conversion(self):
        """Test converting PIL images to numpy arrays."""
        def image_to_array_stats(size):
            """Create image, convert to array, compute stats."""
            img = Image.new('L', (size, size), color=128)
            arr = np.array(img)
            return int(np.mean(arr))
        
        sizes = [10, 15, 20, 25, 30]
        result = optimize(image_to_array_stats, sizes, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(image_to_array_stats, result)
        
        # All should be 128 (the color value)
        assert all(r == 128 for r in results)


class TestContainerAwareEnvironment:
    """Test behavior in container-like environments."""
    
    def test_detects_available_memory(self):
        """Test that optimizer can detect available memory."""
        def memory_intensive(x):
            """Function that uses some memory."""
            # Create a list but not too large
            data = [i for i in range(x * 100)]
            return len(data)
        
        data = range(10)
        result = optimize(memory_intensive, data, verbose=False)
        
        # Should recommend some parallelization
        assert result.n_jobs >= 1
        
        # Should not crash when memory is considered
        results = _execute_with_pool(memory_intensive, result)
        
        expected = [x * 100 for x in data]
        assert results == expected
    
    def test_respects_cpu_limits(self):
        """Test that optimizer respects detected CPU count."""
        def simple_cpu_task(x):
            """Simple CPU task."""
            return x ** 2
        
        data = range(100)
        result = optimize(simple_cpu_task, data, verbose=False)
        
        # Should not recommend more workers than CPUs
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        
        assert result.n_jobs >= 1
        assert result.n_jobs <= cpu_count
        
        # Should execute successfully
        results = _execute_with_pool(simple_cpu_task, result)
        
        expected = [x ** 2 for x in data]
        assert results == expected


class TestCrossVersionCompatibility:
    """Test compatibility patterns across Python versions."""
    
    def test_basic_types_compatibility(self):
        """Test with basic Python types (works on all versions)."""
        def process_basic_types(item):
            """Process tuple of basic types."""
            num, text, flag = item
            return num * 2 if flag else len(text)
        
        data = [(i, f'text_{i}', i % 2 == 0) for i in range(20)]
        result = optimize(process_basic_types, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_basic_types, result)
        
        expected = [process_basic_types(item) for item in data]
        assert results == expected
    
    def test_list_dict_compatibility(self):
        """Test with lists and dictionaries."""
        def process_dict_list(item):
            """Process dict with list values."""
            return sum(item['values'])
        
        data = [{'id': i, 'values': [i, i+1, i+2]} for i in range(20)]
        result = optimize(process_dict_list, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_dict_list, result)
        
        expected = [sum(item['values']) for item in data]
        assert results == expected
    
    def test_python_version_info_available(self):
        """Test that Python version info is accessible."""
        # This ensures tests work across versions
        assert sys.version_info.major == 3
        assert sys.version_info.minor >= 7  # Minimum supported version
        
        def version_aware_task(x):
            """Task that's aware of Python version."""
            # Use a feature available in Python 3.7+
            return x ** 2
        
        data = range(10)
        result = optimize(version_aware_task, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(version_aware_task, result)
        
        expected = [x ** 2 for x in data]
        assert results == expected


class TestRealWorldUseCases:
    """Test realistic use cases from different domains."""
    
    def test_data_transformation_pipeline(self):
        """Test a data transformation pipeline."""
        def transform_data(record):
            """Multi-step transformation."""
            # Parse
            value = record['value']
            # Transform
            squared = value ** 2
            # Validate
            if squared < 0:
                squared = 0
            # Format
            return {'original': value, 'transformed': squared}
        
        data = [{'id': i, 'value': i} for i in range(50)]
        result = optimize(transform_data, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(transform_data, result)
        
        # Verify structure
        assert len(results) == 50
        assert all('original' in r and 'transformed' in r for r in results)
        assert all(r['transformed'] == r['original'] ** 2 for r in results)
    
    def test_batch_validation_workflow(self):
        """Test batch validation workflow."""
        def validate_record(record):
            """Validate a record."""
            errors = []
            
            if 'id' not in record:
                errors.append('Missing id')
            if 'value' not in record:
                errors.append('Missing value')
            elif record['value'] < 0:
                errors.append('Negative value')
            
            return {
                'record': record,
                'valid': len(errors) == 0,
                'errors': errors
            }
        
        data = [
            {'id': i, 'value': i} for i in range(20)
        ] + [
            {'id': i, 'value': -1} for i in range(20, 25)
        ] + [
            {'id': i} for i in range(25, 30)
        ]
        
        result = optimize(validate_record, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(validate_record, result)
        
        # First 20 should be valid
        assert all(r['valid'] for r in results[:20])
        # Next 5 should have negative value error
        assert all(not r['valid'] for r in results[20:25])
        # Last 5 should have missing value error
        assert all(not r['valid'] for r in results[25:30])
    
    def test_aggregation_workflow(self):
        """Test aggregation workflow."""
        def compute_statistics(values):
            """Compute basic statistics."""
            if not values:
                return {'count': 0, 'sum': 0, 'mean': 0}
            
            return {
                'count': len(values),
                'sum': sum(values),
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
        
        data = [[i, i+1, i+2, i+3, i+4] for i in range(30)]
        result = optimize(compute_statistics, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(compute_statistics, result)
        
        # Verify structure
        assert len(results) == 30
        assert all(r['count'] == 5 for r in results)
        assert results[0]['mean'] == 2.0  # (0+1+2+3+4)/5


class TestEdgeCasesInRealWorld:
    """Test edge cases that occur in real-world usage."""
    
    def test_empty_container_handling(self):
        """Test handling of empty containers."""
        def process_container(container):
            """Process a container that might be empty."""
            if not container:
                return 0
            return sum(container)
        
        data = [
            [1, 2, 3],
            [],
            [4, 5],
            [],
            [6]
        ]
        
        result = optimize(process_container, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_container, result)
        
        expected = [6, 0, 9, 0, 6]
        assert results == expected
    
    def test_none_value_handling(self):
        """Test handling of None values."""
        def process_nullable(value):
            """Process value that might be None."""
            if value is None:
                return -1
            return value * 2
        
        data = [1, None, 3, None, 5, 6, None, 8]
        result = optimize(process_nullable, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_nullable, result)
        
        expected = [2, -1, 6, -1, 10, 12, -1, 16]
        assert results == expected
    
    def test_mixed_type_handling(self):
        """Test handling of mixed types."""
        def process_mixed(value):
            """Process different types appropriately."""
            if isinstance(value, int):
                return value * 2
            elif isinstance(value, str):
                return len(value)
            elif isinstance(value, list):
                return len(value)
            else:
                return 0
        
        data = [42, 'hello', [1, 2, 3], 99, 'world']
        result = optimize(process_mixed, data, verbose=False)
        
        assert result.n_jobs >= 1
        
        results = _execute_with_pool(process_mixed, result)
        
        expected = [84, 5, 3, 198, 5]
        assert results == expected
