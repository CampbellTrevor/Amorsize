"""
Tests for ML prediction with hardware-aware features (Iteration 114).

These tests verify that the advanced cost model integration with ML works correctly,
providing better predictions on systems with different hardware configurations.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from amorsize.ml_prediction import (
    WorkloadFeatures,
    PredictionResult,
    predict_parameters,
    update_model_from_execution,
    _HAS_COST_MODEL
)

# Try to import cost model components
try:
    from amorsize.cost_model import (
        SystemTopology,
        CacheInfo,
        NUMAInfo,
        MemoryBandwidthInfo,
        detect_system_topology
    )
    HAS_COST_MODEL = True
except ImportError:
    HAS_COST_MODEL = False
    SystemTopology = None
    CacheInfo = None
    NUMAInfo = None
    MemoryBandwidthInfo = None


class TestHardwareFeatureExtraction:
    """Test hardware feature extraction from system topology."""
    
    @pytest.mark.skipif(not HAS_COST_MODEL, reason="Cost model not available")
    def test_features_with_system_topology(self):
        """Test WorkloadFeatures with explicit system topology."""
        # Create a mock system topology
        cache_info = CacheInfo(
            l1_size=64 * 1024,      # 64KB L1
            l2_size=512 * 1024,     # 512KB L2
            l3_size=16 * 1024 * 1024,  # 16MB L3
            cache_line_size=64
        )
        
        numa_info = NUMAInfo(
            numa_nodes=2,
            cores_per_node=8,
            has_numa=True
        )
        
        memory_bandwidth = MemoryBandwidthInfo(
            bandwidth_gb_per_sec=50.0,
            is_estimated=True
        )
        
        topology = SystemTopology(
            cache_info=cache_info,
            numa_info=numa_info,
            memory_bandwidth=memory_bandwidth,
            physical_cores=16
        )
        
        # Create features with topology
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=16,
            available_memory=16 * 1024**3,
            start_method='fork',
            system_topology=topology
        )
        
        # Verify hardware features are extracted
        assert features.l3_cache_size == 16 * 1024 * 1024
        assert features.numa_nodes == 2
        assert features.memory_bandwidth_gb_s == 50.0
        assert features.has_numa == 1
        
        # Verify normalized features are in valid range
        assert 0.0 <= features.norm_l3_cache <= 1.0
        assert 0.0 <= features.norm_numa_nodes <= 1.0
        assert 0.0 <= features.norm_memory_bandwidth <= 1.0
        assert features.norm_has_numa in [0.0, 1.0]
    
    def test_features_without_system_topology(self):
        """Test WorkloadFeatures without system topology (defaults)."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method='fork',
            system_topology=None
        )
        
        # Verify default hardware features are used
        assert features.l3_cache_size == 8 * 1024 * 1024  # 8MB default
        assert features.numa_nodes == 1
        assert features.memory_bandwidth_gb_s == 25.0  # DDR4-3200 default
        assert features.has_numa == 0
        
        # Verify normalized features are valid
        assert 0.0 <= features.norm_l3_cache <= 1.0
        assert 0.0 <= features.norm_numa_nodes <= 1.0
        assert 0.0 <= features.norm_memory_bandwidth <= 1.0
        assert features.norm_has_numa == 0.0


class TestHardwareFeatureNormalization:
    """Test normalization of hardware features."""
    
    @pytest.mark.skipif(not HAS_COST_MODEL, reason="Cost model not available")
    def test_l3_cache_normalization(self):
        """Test L3 cache size normalization."""
        # Small cache (1MB - at lower bound)
        small_cache = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 1*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(25.0, True),
            physical_cores=8
        )
        
        # Large cache (256MB - at upper bound)
        large_cache = SystemTopology(
            cache_info=CacheInfo(64*1024, 1024*1024, 256*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(25.0, True),
            physical_cores=8
        )
        
        features_small = WorkloadFeatures(
            data_size=1000, estimated_item_time=0.01,
            physical_cores=8, available_memory=8*1024**3,
            start_method='fork', system_topology=small_cache
        )
        
        features_large = WorkloadFeatures(
            data_size=1000, estimated_item_time=0.01,
            physical_cores=8, available_memory=8*1024**3,
            start_method='fork', system_topology=large_cache
        )
        
        # Small cache should have lower normalized value
        assert features_small.norm_l3_cache < features_large.norm_l3_cache
        assert 0.0 <= features_small.norm_l3_cache <= 1.0
        assert 0.0 <= features_large.norm_l3_cache <= 1.0
    
    @pytest.mark.skipif(not HAS_COST_MODEL, reason="Cost model not available")
    def test_numa_normalization(self):
        """Test NUMA node count normalization."""
        # Single NUMA node
        single_numa = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(25.0, True),
            physical_cores=8
        )
        
        # Multiple NUMA nodes
        multi_numa = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 8*1024*1024, 64),
            numa_info=NUMAInfo(4, 16, True),
            memory_bandwidth=MemoryBandwidthInfo(100.0, True),
            physical_cores=64
        )
        
        features_single = WorkloadFeatures(
            data_size=1000, estimated_item_time=0.01,
            physical_cores=8, available_memory=8*1024**3,
            start_method='fork', system_topology=single_numa
        )
        
        features_multi = WorkloadFeatures(
            data_size=1000, estimated_item_time=0.01,
            physical_cores=64, available_memory=64*1024**3,
            start_method='fork', system_topology=multi_numa
        )
        
        # More NUMA nodes should have higher normalized value
        assert features_single.norm_numa_nodes < features_multi.norm_numa_nodes
        assert features_single.norm_has_numa == 0.0
        assert features_multi.norm_has_numa == 1.0


class TestHardwareFeatureVectorSize:
    """Test that feature vector has correct size with hardware features."""
    
    def test_vector_size_is_12(self):
        """Test that feature vector has 12 elements (enhanced in Iteration 114)."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        vector = features.to_vector()
        assert len(vector) == 12  # 8 original + 4 hardware features
        assert all(isinstance(v, float) for v in vector)
        assert all(0.0 <= v <= 1.0 for v in vector)
    
    def test_vector_includes_hardware_features(self):
        """Test that vector includes hardware features in correct order."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method='fork'
        )
        
        vector = features.to_vector()
        # Vector should be: [data_size, time, cores, memory, start_method,
        #                    pickle_size, cv, complexity,
        #                    l3_cache, numa_nodes, memory_bandwidth, has_numa]
        assert len(vector) == 12
        
        # Last 4 elements are hardware features
        l3_cache_norm = vector[8]
        numa_nodes_norm = vector[9]
        memory_bandwidth_norm = vector[10]
        has_numa_norm = vector[11]
        
        # All should be valid normalized values
        assert 0.0 <= l3_cache_norm <= 1.0
        assert 0.0 <= numa_nodes_norm <= 1.0
        assert 0.0 <= memory_bandwidth_norm <= 1.0
        assert has_numa_norm in [0.0, 1.0]


class TestHardwareFeatureDistance:
    """Test distance calculation with hardware features."""
    
    @pytest.mark.skipif(not HAS_COST_MODEL, reason="Cost model not available")
    def test_distance_with_different_hardware(self):
        """Test that hardware differences affect distance calculation."""
        # System with small cache
        small_cache_system = SystemTopology(
            cache_info=CacheInfo(32*1024, 256*1024, 4*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(25.0, True),
            physical_cores=8
        )
        
        # System with large cache
        large_cache_system = SystemTopology(
            cache_info=CacheInfo(64*1024, 1024*1024, 64*1024*1024, 64),
            numa_info=NUMAInfo(1, 8, False),
            memory_bandwidth=MemoryBandwidthInfo(25.0, True),
            physical_cores=8
        )
        
        # Create features with same workload but different hardware
        features1 = WorkloadFeatures(
            data_size=1000, estimated_item_time=0.01,
            physical_cores=8, available_memory=8*1024**3,
            start_method='fork', system_topology=small_cache_system
        )
        
        features2 = WorkloadFeatures(
            data_size=1000, estimated_item_time=0.01,
            physical_cores=8, available_memory=8*1024**3,
            start_method='fork', system_topology=large_cache_system
        )
        
        # Distance should be non-zero due to hardware differences
        distance = features1.distance(features2)
        assert distance > 0.0
        # But should be small since workload is same
        assert distance < 1.0  # Much less than max distance of sqrt(12)


class TestPredictionWithHardwareFeatures:
    """Test ML prediction with hardware-aware features."""
    
    def test_predict_parameters_without_topology(self):
        """Test predict_parameters works without cost model."""
        def dummy_func(x):
            return x * 2
        
        # Should work with default hardware values
        result = predict_parameters(
            func=dummy_func,
            data_size=1000,
            estimated_item_time=0.01,
            verbose=False
        )
        
        # May return None (no training data) but shouldn't crash
        assert result is None or isinstance(result, PredictionResult)
    
    @pytest.mark.skipif(not HAS_COST_MODEL, reason="Cost model not available")
    def test_predict_parameters_with_topology(self):
        """Test predict_parameters detects and uses system topology."""
        def dummy_func(x):
            return x * 2
        
        # Should detect topology internally
        result = predict_parameters(
            func=dummy_func,
            data_size=1000,
            estimated_item_time=0.01,
            verbose=True
        )
        
        # May return None (no training data) but shouldn't crash
        assert result is None or isinstance(result, PredictionResult)


class TestBackwardCompatibility:
    """Test backward compatibility with cached training data."""
    
    def test_load_old_training_data(self):
        """Test that old training data (8 features) can be loaded."""
        # Old cached data won't have hardware features
        # WorkloadFeatures should handle this gracefully with defaults
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method='fork',
            system_topology=None  # Old data won't have this
        )
        
        # Should work with default hardware values
        vector = features.to_vector()
        assert len(vector) == 12
        
        # Last 4 elements should be defaults
        assert features.l3_cache_size == 8 * 1024 * 1024  # 8MB default
        assert features.numa_nodes == 1
        assert features.memory_bandwidth_gb_s == 25.0
        assert features.has_numa == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
