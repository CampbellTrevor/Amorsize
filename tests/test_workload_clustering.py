"""
Tests for workload clustering and classification (Iteration 121).

Tests the k-means clustering algorithm, cluster-aware k-NN predictions,
and workload type classification functionality.
"""

import pytest
import time
from amorsize.ml_prediction import (
    WorkloadFeatures,
    WorkloadCluster,
    TrainingData,
    SimpleLinearPredictor,
    _cluster_workloads,
    _kmeans_plus_plus_init,
    _classify_cluster_type,
    MIN_CLUSTERING_SAMPLES,
    MAX_CLUSTERS
)


class TestWorkloadCluster:
    """Test WorkloadCluster class."""
    
    def test_cluster_creation(self):
        """Test creating a WorkloadCluster."""
        centroid = [0.5, 0.6, 0.7, 0.3, 0.4, 0.2, 0.1, 0.5, 0.6, 0.3, 0.7, 0.0]
        cluster = WorkloadCluster(
            cluster_id=0,
            centroid=centroid,
            member_indices=[0, 1, 2, 3],
            typical_n_jobs=4,
            typical_chunksize=100,
            avg_speedup=3.5,
            workload_type="CPU-intensive"
        )
        
        assert cluster.cluster_id == 0
        assert cluster.centroid == centroid
        assert len(cluster.member_indices) == 4
        assert cluster.typical_n_jobs == 4
        assert cluster.typical_chunksize == 100
        assert cluster.avg_speedup == 3.5
        assert cluster.workload_type == "CPU-intensive"
    
    def test_distance_to_centroid(self):
        """Test calculating distance to cluster centroid."""
        centroid = [0.5] * 12
        cluster = WorkloadCluster(
            cluster_id=0,
            centroid=centroid,
            member_indices=[0],
            typical_n_jobs=4,
            typical_chunksize=100,
            avg_speedup=3.0,
            workload_type="Mixed workload"
        )
        
        # Distance from identical vector should be 0
        distance = cluster.distance_to_centroid([0.5] * 12)
        assert distance == 0.0
        
        # Distance from different vector should be positive
        distance = cluster.distance_to_centroid([0.6] * 12)
        assert distance > 0.0
    
    def test_cluster_repr(self):
        """Test cluster string representation."""
        cluster = WorkloadCluster(
            cluster_id=1,
            centroid=[0.5] * 12,
            member_indices=[0, 1, 2],
            typical_n_jobs=8,
            typical_chunksize=50,
            avg_speedup=4.2,
            workload_type="I/O-bound"
        )
        
        repr_str = repr(cluster)
        assert "WorkloadCluster" in repr_str
        assert "id=1" in repr_str
        assert "I/O-bound" in repr_str
        assert "size=3" in repr_str


class TestClusteringAlgorithm:
    """Test k-means clustering algorithm."""
    
    def _create_training_data(self, n_samples: int, feature_pattern: str = "mixed"):
        """
        Helper to create training data with different patterns.
        
        Args:
            n_samples: Number of samples to create
            feature_pattern: Pattern type - "cpu", "io", "memory", or "mixed"
        """
        training_data = []
        
        for i in range(n_samples):
            # Create features based on pattern
            if feature_pattern == "cpu":
                # CPU-intensive: high execution time, low pickle size
                features = WorkloadFeatures(
                    data_size=1000 + i * 100,
                    estimated_item_time=0.001 + i * 0.0001,  # High time
                    physical_cores=8,
                    available_memory=8 * 1024**3,
                    start_method="fork",
                    pickle_size=100,  # Low pickle
                    coefficient_of_variation=0.2,
                    function_complexity=500
                )
                n_jobs = 8
                chunksize = 10
                speedup = 6.0
            elif feature_pattern == "io":
                # I/O-bound: low execution time, high pickle size
                features = WorkloadFeatures(
                    data_size=10000 + i * 100,
                    estimated_item_time=0.00001,  # Low time
                    physical_cores=8,
                    available_memory=8 * 1024**3,
                    start_method="spawn",
                    pickle_size=10000 + i * 1000,  # High pickle
                    coefficient_of_variation=0.3,
                    function_complexity=200
                )
                n_jobs = 4
                chunksize = 100
                speedup = 2.0
            elif feature_pattern == "memory":
                # Memory-intensive: large data, quick execution
                features = WorkloadFeatures(
                    data_size=100000 + i * 1000,  # Large data
                    estimated_item_time=0.00005,  # Quick
                    physical_cores=8,
                    available_memory=32 * 1024**3,
                    start_method="fork",
                    pickle_size=500,
                    coefficient_of_variation=0.1,
                    function_complexity=300
                )
                n_jobs = 6
                chunksize=200
                speedup = 4.5
            else:  # mixed - alternate between patterns
                if i % 3 == 0:
                    feature_pattern_recursive = "cpu"
                elif i % 3 == 1:
                    feature_pattern_recursive = "io"
                else:
                    feature_pattern_recursive = "memory"
                return self._create_training_data(n_samples, feature_pattern_recursive)
            
            sample = TrainingData(
                features=features,
                n_jobs=n_jobs,
                chunksize=chunksize,
                speedup=speedup,
                timestamp=time.time() - i
            )
            training_data.append(sample)
        
        return training_data
    
    def test_clustering_requires_min_samples(self):
        """Test that clustering requires minimum samples."""
        training_data = self._create_training_data(5, "cpu")  # Less than MIN_CLUSTERING_SAMPLES
        
        clusters = _cluster_workloads(training_data, verbose=False)
        
        # Should return empty list when not enough samples
        assert len(clusters) == 0
    
    def test_clustering_creates_multiple_clusters(self):
        """Test that clustering creates multiple clusters for diverse data."""
        # Create mixed workload data (15 samples of 3 types)
        training_data = self._create_training_data(15, "mixed")
        
        clusters = _cluster_workloads(training_data, verbose=True)
        
        # Should create multiple clusters
        assert len(clusters) >= 2
        assert len(clusters) <= MAX_CLUSTERS
        
        # All clusters should have members
        for cluster in clusters:
            assert len(cluster.member_indices) > 0
        
        # Total members across clusters should equal training data size
        total_members = sum(len(c.member_indices) for c in clusters)
        assert total_members == len(training_data)
    
    def test_clustering_with_fixed_k(self):
        """Test clustering with fixed number of clusters."""
        training_data = self._create_training_data(20, "mixed")
        
        clusters = _cluster_workloads(training_data, num_clusters=3, verbose=False)
        
        # Should create exactly 3 clusters (or less if some are empty)
        assert len(clusters) <= 3
        assert len(clusters) >= 2
    
    def test_cluster_characteristics(self):
        """Test that cluster metadata is computed correctly."""
        training_data = self._create_training_data(15, "mixed")
        
        clusters = _cluster_workloads(training_data, verbose=False)
        
        for cluster in clusters:
            # Check cluster has valid metadata
            assert cluster.cluster_id >= 0
            assert len(cluster.centroid) == 12  # 12 features
            assert cluster.typical_n_jobs >= 1
            assert cluster.typical_chunksize >= 1
            assert cluster.avg_speedup > 0
            assert len(cluster.workload_type) > 0
            
            # Check centroid is valid (all values in [0, 1] range)
            for val in cluster.centroid:
                assert 0.0 <= val <= 1.0
    
    def test_clustering_convergence(self):
        """Test that k-means converges properly."""
        training_data = self._create_training_data(20, "mixed")
        
        # Run clustering twice - should produce similar results
        clusters1 = _cluster_workloads(training_data, num_clusters=3, verbose=False)
        clusters2 = _cluster_workloads(training_data, num_clusters=3, verbose=False)
        
        # Number of clusters should be consistent
        assert len(clusters1) == len(clusters2)


class TestKMeansPlusPlusInit:
    """Test k-means++ initialization algorithm."""
    
    def test_init_creates_correct_number_of_centroids(self):
        """Test that k-means++ creates requested number of centroids."""
        feature_vectors = [[0.1] * 12, [0.5] * 12, [0.9] * 12, [0.3] * 12, [0.7] * 12]
        
        centroids = _kmeans_plus_plus_init(feature_vectors, num_clusters=3)
        
        assert len(centroids) == 3
        assert all(len(c) == 12 for c in centroids)
    
    def test_init_selects_diverse_centroids(self):
        """Test that k-means++ selects well-separated initial centroids."""
        # Create clearly separated feature vectors
        feature_vectors = (
            [[0.1] * 12] * 5 +  # Group 1
            [[0.5] * 12] * 5 +  # Group 2
            [[0.9] * 12] * 5    # Group 3
        )
        
        centroids = _kmeans_plus_plus_init(feature_vectors, num_clusters=3)
        
        # Centroids should be diverse (not all from same group)
        centroid_values = [c[0] for c in centroids]
        assert len(set(centroid_values)) > 1  # At least 2 different values


class TestWorkloadTypeClassification:
    """Test workload type classification."""
    
    def test_classify_cpu_intensive(self):
        """Test classification of CPU-intensive workloads."""
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,  # High execution time
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="fork",
            pickle_size=100,  # Low pickle overhead
            coefficient_of_variation=0.2,
            function_complexity=500
        )
        
        sample = TrainingData(
            features=features,
            n_jobs=8,
            chunksize=10,
            speedup=6.0,
            timestamp=time.time()
        )
        
        workload_type = _classify_cluster_type(
            features.to_vector(),
            [sample]
        )
        
        assert "CPU" in workload_type or "computation" in workload_type
    
    def test_classify_io_bound(self):
        """Test classification of I/O-bound workloads."""
        features = WorkloadFeatures(
            data_size=10000,
            estimated_item_time=0.00001,  # Low execution time
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="spawn",
            pickle_size=50000,  # High pickle overhead
            coefficient_of_variation=0.3,
            function_complexity=200
        )
        
        sample = TrainingData(
            features=features,
            n_jobs=4,
            chunksize=100,
            speedup=2.0,
            timestamp=time.time()
        )
        
        workload_type = _classify_cluster_type(
            features.to_vector(),
            [sample]
        )
        
        assert "I/O" in workload_type or "bound" in workload_type
    
    def test_classify_heterogeneous(self):
        """Test classification of heterogeneous workloads."""
        features = WorkloadFeatures(
            data_size=5000,
            estimated_item_time=0.001,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="fork",
            pickle_size=500,
            coefficient_of_variation=0.8,  # High CV
            function_complexity=300
        )
        
        sample = TrainingData(
            features=features,
            n_jobs=6,
            chunksize=50,
            speedup=3.5,
            timestamp=time.time()
        )
        
        workload_type = _classify_cluster_type(
            features.to_vector(),
            [sample]
        )
        
        assert "Heterogeneous" in workload_type or "Mixed" in workload_type


class TestClusterAwarePrediction:
    """Test cluster-aware k-NN predictions."""
    
    def _create_predictor_with_clusters(self):
        """Helper to create predictor with clustered training data."""
        predictor = SimpleLinearPredictor(k=5, enable_clustering=True)
        
        # Add CPU-intensive samples (cluster 1)
        for i in range(10):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=8 * 1024**3,
                start_method="fork",
                pickle_size=100,
                coefficient_of_variation=0.2,
                function_complexity=500
            )
            sample = TrainingData(
                features=features,
                n_jobs=8,
                chunksize=10,
                speedup=6.0,
                timestamp=time.time() - i
            )
            predictor.add_training_sample(sample)
        
        # Add I/O-bound samples (cluster 2)
        for i in range(10):
            features = WorkloadFeatures(
                data_size=10000,
                estimated_item_time=0.00001,
                physical_cores=8,
                available_memory=8 * 1024**3,
                start_method="spawn",
                pickle_size=50000,
                coefficient_of_variation=0.3,
                function_complexity=200
            )
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=100,
                speedup=2.0,
                timestamp=time.time() - i - 10
            )
            predictor.add_training_sample(sample)
        
        return predictor
    
    def test_clustering_disabled_by_default(self):
        """Test that clustering can be disabled."""
        predictor = SimpleLinearPredictor(k=5, enable_clustering=False)
        
        assert predictor.enable_clustering is False
        assert predictor.clusters == []
    
    def test_predictor_creates_clusters(self):
        """Test that predictor automatically creates clusters."""
        predictor = self._create_predictor_with_clusters()
        
        # Trigger cluster update by making a prediction
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="fork",
            pickle_size=100,
            coefficient_of_variation=0.2,
            function_complexity=500
        )
        
        result = predictor.predict(features, confidence_threshold=0.5, verbose=True)
        
        # Clusters should be created
        assert len(predictor.clusters) >= 2
    
    def test_cluster_aware_prediction_cpu(self):
        """Test prediction for CPU-intensive workload uses CPU cluster."""
        predictor = self._create_predictor_with_clusters()
        
        # Query with CPU-intensive features
        features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="fork",
            pickle_size=100,
            coefficient_of_variation=0.2,
            function_complexity=500
        )
        
        result = predictor.predict(features, confidence_threshold=0.5)
        
        # Should predict parameters similar to CPU cluster (high n_jobs, low chunksize)
        assert result is not None
        assert result.n_jobs >= 6  # CPU workloads typically use more workers
        assert "cluster" in result.reason.lower()
    
    def test_cluster_aware_prediction_io(self):
        """Test prediction for I/O-bound workload uses I/O cluster."""
        predictor = self._create_predictor_with_clusters()
        
        # Query with I/O-bound features
        features = WorkloadFeatures(
            data_size=10000,
            estimated_item_time=0.00001,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="spawn",
            pickle_size=50000,
            coefficient_of_variation=0.3,
            function_complexity=200
        )
        
        result = predictor.predict(features, confidence_threshold=0.5)
        
        # Should predict parameters similar to I/O cluster (lower n_jobs, higher chunksize)
        assert result is not None
        assert result.chunksize >= 50  # I/O workloads typically use larger chunks
        assert "cluster" in result.reason.lower()
    
    def test_find_best_cluster(self):
        """Test finding best matching cluster for features."""
        predictor = self._create_predictor_with_clusters()
        
        # Force cluster update
        predictor._update_clusters(verbose=False)
        
        # Find cluster for CPU-intensive features
        cpu_features = WorkloadFeatures(
            data_size=1000,
            estimated_item_time=0.01,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="fork",
            pickle_size=100,
            coefficient_of_variation=0.2,
            function_complexity=500
        )
        
        best_cluster = predictor._find_best_cluster(cpu_features)
        
        assert best_cluster is not None
        assert best_cluster.cluster_id >= 0
    
    def test_clusters_recomputed_after_new_samples(self):
        """Test that clusters are recomputed when new samples are added."""
        predictor = SimpleLinearPredictor(k=5, enable_clustering=True)
        
        # Add initial samples
        for i in range(10):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=8 * 1024**3,
                start_method="fork",
                pickle_size=100,
                coefficient_of_variation=0.2,
                function_complexity=500
            )
            sample = TrainingData(
                features=features,
                n_jobs=8,
                chunksize=10,
                speedup=6.0,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        # Clusters should be marked dirty
        assert predictor._clusters_dirty is True
        
        # Force cluster update
        predictor._update_clusters(verbose=False)
        
        # Clusters should now be clean
        assert predictor._clusters_dirty is False
        
        # Add more samples
        features = WorkloadFeatures(
            data_size=10000,
            estimated_item_time=0.00001,
            physical_cores=8,
            available_memory=8 * 1024**3,
            start_method="spawn",
            pickle_size=50000,
            coefficient_of_variation=0.3,
            function_complexity=200
        )
        sample = TrainingData(
            features=features,
            n_jobs=4,
            chunksize=100,
            speedup=2.0,
            timestamp=time.time()
        )
        predictor.add_training_sample(sample)
        
        # Clusters should be marked dirty again
        assert predictor._clusters_dirty is True


class TestClusterStatistics:
    """Test cluster statistics and inspection."""
    
    def test_get_cluster_statistics_no_clusters(self):
        """Test getting statistics when no clusters exist."""
        predictor = SimpleLinearPredictor(k=5, enable_clustering=True)
        
        # Add only a few samples (not enough for clustering)
        for i in range(5):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=8 * 1024**3,
                start_method="fork",
                pickle_size=100,
                coefficient_of_variation=0.2,
                function_complexity=500
            )
            sample = TrainingData(
                features=features,
                n_jobs=8,
                chunksize=10,
                speedup=6.0,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        stats = predictor.get_cluster_statistics()
        
        assert stats['num_clusters'] == 0
        assert stats['total_samples'] == 5
        assert stats['clusters'] == []
        assert stats['clustering_enabled'] is True
    
    def test_get_cluster_statistics_with_clusters(self):
        """Test getting statistics when clusters exist."""
        predictor = SimpleLinearPredictor(k=5, enable_clustering=True)
        
        # Add CPU-intensive samples
        for i in range(10):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=8 * 1024**3,
                start_method="fork",
                pickle_size=100,
                coefficient_of_variation=0.2,
                function_complexity=500
            )
            sample = TrainingData(
                features=features,
                n_jobs=8,
                chunksize=10,
                speedup=6.0,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        # Add I/O-bound samples
        for i in range(10):
            features = WorkloadFeatures(
                data_size=10000,
                estimated_item_time=0.00001,
                physical_cores=8,
                available_memory=8 * 1024**3,
                start_method="spawn",
                pickle_size=50000,
                coefficient_of_variation=0.3,
                function_complexity=200
            )
            sample = TrainingData(
                features=features,
                n_jobs=4,
                chunksize=100,
                speedup=2.0,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        stats = predictor.get_cluster_statistics()
        
        assert stats['num_clusters'] >= 2
        assert stats['total_samples'] == 20
        assert len(stats['clusters']) >= 2
        assert stats['clustering_enabled'] is True
        
        # Check cluster info structure
        for cluster_info in stats['clusters']:
            assert 'id' in cluster_info
            assert 'type' in cluster_info
            assert 'size' in cluster_info
            assert 'typical_n_jobs' in cluster_info
            assert 'typical_chunksize' in cluster_info
            assert 'avg_speedup' in cluster_info
            assert cluster_info['size'] > 0
    
    def test_clustering_disabled_statistics(self):
        """Test statistics when clustering is disabled."""
        predictor = SimpleLinearPredictor(k=5, enable_clustering=False)
        
        # Add samples
        for i in range(15):
            features = WorkloadFeatures(
                data_size=1000,
                estimated_item_time=0.01,
                physical_cores=8,
                available_memory=8 * 1024**3,
                start_method="fork",
                pickle_size=100,
                coefficient_of_variation=0.2,
                function_complexity=500
            )
            sample = TrainingData(
                features=features,
                n_jobs=8,
                chunksize=10,
                speedup=6.0,
                timestamp=time.time()
            )
            predictor.add_training_sample(sample)
        
        stats = predictor.get_cluster_statistics()
        
        # Should not create clusters even with enough samples
        assert stats['num_clusters'] == 0
        assert stats['total_samples'] == 15
        assert stats['clustering_enabled'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
