"""
Tests for data item picklability detection.

This module tests the safety check that verifies data items can be pickled
before recommending parallelization. This prevents runtime failures in
multiprocessing.Pool.map() when data contains unpicklable objects.
"""

import threading
import pytest
from amorsize import optimize
from amorsize.sampling import check_data_picklability, perform_dry_run


def flexible_function(x):
    """A function that can handle any type of input."""
    if isinstance(x, dict):
        return x.get("id", 0)
    elif isinstance(x, int):
        return x * 2
    else:
        return str(x)


class TestCheckDataPicklability:
    """Tests for the check_data_picklability function."""
    
    def test_picklable_primitives(self):
        """Test that primitive data types are picklable."""
        data = [1, 2, 3, 4, 5]
        picklable, idx, err = check_data_picklability(data)
        
        assert picklable is True
        assert idx is None
        assert err is None
    
    def test_picklable_strings(self):
        """Test that strings are picklable."""
        data = ["hello", "world", "test"]
        picklable, idx, err = check_data_picklability(data)
        
        assert picklable is True
        assert idx is None
        assert err is None
    
    def test_picklable_mixed_types(self):
        """Test that mixed primitive types are picklable."""
        data = [1, "hello", 3.14, True, None, (1, 2), [1, 2], {"key": "value"}]
        picklable, idx, err = check_data_picklability(data)
        
        assert picklable is True
        assert idx is None
        assert err is None
    
    def test_unpicklable_thread_lock(self):
        """Test that thread locks are detected as unpicklable."""
        lock = threading.Lock()
        data = [1, 2, lock, 4, 5]
        picklable, idx, err = check_data_picklability(data)
        
        assert picklable is False
        assert idx == 2  # Lock is at index 2
        assert err is not None
    
    def test_unpicklable_thread_lock_first_item(self):
        """Test detection when unpicklable item is first."""
        lock = threading.Lock()
        data = [lock, 1, 2, 3]
        picklable, idx, err = check_data_picklability(data)
        
        assert picklable is False
        assert idx == 0
        assert err is not None
    
    def test_unpicklable_thread_lock_last_item(self):
        """Test detection when unpicklable item is last."""
        lock = threading.Lock()
        data = [1, 2, 3, lock]
        picklable, idx, err = check_data_picklability(data)
        
        assert picklable is False
        assert idx == 3
        assert err is not None
    
    def test_empty_list(self):
        """Test that empty list is considered picklable."""
        data = []
        picklable, idx, err = check_data_picklability(data)
        
        assert picklable is True
        assert idx is None
        assert err is None


class TestPerformDryRunWithDataPicklability:
    """Tests for data picklability detection in perform_dry_run."""
    
    def test_dry_run_with_picklable_data(self):
        """Test that dry run succeeds with picklable data."""
        data = [1, 2, 3, 4, 5]
        result = perform_dry_run(flexible_function, data, sample_size=3)
        
        assert result.data_items_picklable is True
        assert result.unpicklable_data_index is None
        assert result.data_pickle_error is None
        assert result.error is None
    
    def test_dry_run_with_unpicklable_data(self):
        """Test that dry run detects unpicklable data."""
        lock = threading.Lock()
        data = [1, lock, 3, 4, 5]
        result = perform_dry_run(flexible_function, data, sample_size=3)
        
        assert result.data_items_picklable is False
        assert result.unpicklable_data_index == 1  # Lock is at index 1 in sample
        assert result.data_pickle_error is not None
    
    def test_dry_run_strings_are_picklable(self):
        """Test that string data is detected as picklable."""
        data = ["hello", "world", "test"]
        result = perform_dry_run(flexible_function, data, sample_size=2)
        
        assert result.data_items_picklable is True
        assert result.unpicklable_data_index is None


class TestOptimizeWithUnpicklableData:
    """Tests for optimize() function with unpicklable data items."""
    
    def test_optimize_rejects_unpicklable_data(self):
        """Test that optimize returns n_jobs=1 for unpicklable data."""
        lock = threading.Lock()
        data = [1, 2, lock, 4, 5, 6, 7, 8, 9, 10]
        
        result = optimize(flexible_function, data, sample_size=5)
        
        assert result.n_jobs == 1
        assert result.chunksize == 1
        assert result.estimated_speedup == 1.0
        assert "not picklable" in result.reason.lower()
        assert len(result.warnings) > 0
    
    def test_optimize_accepts_picklable_data(self):
        """Test that optimize works normally with picklable data."""
        data = list(range(100))
        
        result = optimize(flexible_function, data, sample_size=5)
        
        # Should not reject due to picklability
        # (may still reject for other reasons like speed)
        assert "not picklable" not in result.reason.lower()
    
    def test_unpicklable_data_verbose_mode(self):
        """Test that verbose mode shows data picklability issue."""
        lock = threading.Lock()
        data = [1, 2, lock, 4, 5]
        
        # Just ensure this doesn't crash in verbose mode
        result = optimize(flexible_function, data, sample_size=3, verbose=True)
        
        assert result.n_jobs == 1
        assert "not picklable" in result.reason.lower()
    
    def test_unpicklable_data_with_profiling(self):
        """Test that profiling mode captures data picklability issue."""
        lock = threading.Lock()
        data = [1, 2, lock, 4, 5, 6, 7, 8, 9, 10]
        
        result = optimize(flexible_function, data, sample_size=5, profile=True)
        
        assert result.profile is not None
        assert len(result.profile.rejection_reasons) > 0
        
        # Check that rejection reason mentions data picklability
        rejection_text = " ".join(result.profile.rejection_reasons)
        assert "data" in rejection_text.lower()
        assert "picklable" in rejection_text.lower()
        
        # Check recommendations
        assert len(result.profile.recommendations) > 0
        recommendations_text = " ".join(result.profile.recommendations)
        assert "dill" in recommendations_text.lower() or "cloudpickle" in recommendations_text.lower()
    
    def test_unpicklable_data_explain_output(self):
        """Test that explain() shows data picklability issue clearly."""
        lock = threading.Lock()
        data = [1, 2, lock, 4, 5, 6, 7, 8, 9, 10]
        
        result = optimize(flexible_function, data, sample_size=5, profile=True)
        explanation = result.explain()
        
        assert "data" in explanation.lower()
        assert "picklable" in explanation.lower()
        assert "dill" in explanation.lower() or "cloudpickle" in explanation.lower()


class TestRealWorldScenarios:
    """Tests for real-world scenarios with unpicklable data."""
    
    def test_file_handle_in_data(self):
        """Test detection of file handles in data (common mistake)."""
        # Create a temporary file handle
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f
            data = [1, 2, temp_file, 4, 5]
            
            result = optimize(flexible_function, data, sample_size=3)
            
            assert result.n_jobs == 1
            assert "not picklable" in result.reason.lower()
    
    def test_lambda_in_data_structure(self):
        """Test detection of lambdas in data structures."""
        lambda_func = lambda x: x * 2
        data = [
            {"id": 1, "func": lambda_func},
            {"id": 2, "func": lambda_func},
            {"id": 3, "func": lambda_func}
        ]
        
        result = optimize(flexible_function, data, sample_size=2)
        
        assert result.n_jobs == 1
        assert "not picklable" in result.reason.lower()
    
    def test_regular_dict_data_is_picklable(self):
        """Test that regular dictionaries are picklable."""
        data = [
            {"id": 1, "value": 100},
            {"id": 2, "value": 200},
            {"id": 3, "value": 300}
        ]
        
        result = optimize(flexible_function, data, sample_size=2)
        
        # Should not reject due to picklability
        assert "not picklable" not in result.reason.lower()


class TestEdgeCases:
    """Tests for edge cases in data picklability detection."""
    
    def test_empty_data_list(self):
        """Test that empty data doesn't cause false positives."""
        data = []
        
        # perform_dry_run should handle empty data gracefully
        result = perform_dry_run(flexible_function, data, sample_size=5)
        
        # Empty data causes error, but not due to picklability
        assert result.error is not None
        assert "Empty" in str(result.error)
    
    def test_single_item_unpicklable(self):
        """Test detection with single unpicklable item."""
        lock = threading.Lock()
        data = [lock]
        
        result = optimize(flexible_function, data, sample_size=1)
        
        assert result.n_jobs == 1
        assert "not picklable" in result.reason.lower()
    
    def test_nested_unpicklable_object(self):
        """Test detection of unpicklable objects nested in structures."""
        lock = threading.Lock()
        data = [
            {"id": 1, "lock": lock},
            {"id": 2, "lock": lock}
        ]
        
        result = optimize(flexible_function, data, sample_size=2)
        
        assert result.n_jobs == 1
        assert "not picklable" in result.reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
