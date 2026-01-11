"""
Streaming optimization module for imap/imap_unordered workloads.

This module provides optimization for streaming scenarios where results
are processed incrementally without accumulating all results in memory.
"""

from typing import Any, Callable, Iterator, List, Optional, Union

from .optimizer import DiagnosticProfile, calculate_amdahl_speedup
from .sampling import estimate_total_items, perform_dry_run
from .system_info import (
    check_start_method_mismatch,
    get_available_memory,
    get_chunking_overhead,
    get_multiprocessing_start_method,
    get_physical_cores,
    get_spawn_cost,
)

# Streaming optimization constants
# Buffer size calculation: buffer = n_jobs * BUFFER_SIZE_MULTIPLIER
# This allows prefetching for good throughput without excessive memory use
BUFFER_SIZE_MULTIPLIER = 3

# Maximum chunksize growth for adaptive chunking
# Limits how large chunks can grow to prevent load imbalance
MAX_CHUNKSIZE_GROWTH_FACTOR = 4

# Memory budget for result buffering (fraction of available memory)
# Conservative 10% allocation prevents memory exhaustion
RESULT_BUFFER_MEMORY_FRACTION = 0.1


class StreamingOptimizationResult:
    """
    Result container for streaming optimization analysis.

    Contains optimal parameters for imap/imap_unordered usage along with
    detailed rationale and performance estimates.
    """

    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        use_ordered: bool,
        reason: str,
        estimated_speedup: float,
        warnings: Optional[List[str]] = None,
        data: Optional[Union[List[Any], Iterator[Any]]] = None,
        profile: Optional[DiagnosticProfile] = None,
        use_adaptive_chunking: bool = False,
        adaptive_chunking_params: Optional[dict] = None,
        buffer_size: Optional[int] = None,
        memory_backpressure_enabled: bool = False,
        # New in Iteration 115: for online learning integration
        estimated_item_time: Optional[float] = None,
        pickle_size: Optional[int] = None,
        coefficient_of_variation: Optional[float] = None
    ):
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.use_ordered = use_ordered  # True = imap(), False = imap_unordered()
        self.reason = reason
        self.estimated_speedup = estimated_speedup
        self.warnings = warnings or []
        self.data = data
        self.profile = profile
        self.use_adaptive_chunking = use_adaptive_chunking
        self.adaptive_chunking_params = adaptive_chunking_params or {}
        self.buffer_size = buffer_size
        self.memory_backpressure_enabled = memory_backpressure_enabled
        # New in Iteration 115: store for online learning
        self.estimated_item_time = estimated_item_time
        self.pickle_size = pickle_size
        self.coefficient_of_variation = coefficient_of_variation

    def __repr__(self):
        method = "imap" if self.use_ordered else "imap_unordered"
        return (f"StreamingOptimizationResult(n_jobs={self.n_jobs}, "
                f"chunksize={self.chunksize}, method={method}, "
                f"estimated_speedup={self.estimated_speedup:.2f}x)")

    def __str__(self):
        method = "imap" if self.use_ordered else "imap_unordered"
        return (f"Recommended: n_jobs={self.n_jobs}, chunksize={self.chunksize}, "
                f"use pool.{method}()\n"
                f"Reason: {self.reason}\n"
                f"Estimated speedup: {self.estimated_speedup:.2f}x")

    def explain(self) -> str:
        """
        Return detailed explanation of streaming optimization.

        Returns:
            Human-readable explanation with diagnostic details
        """
        if self.profile is not None:
            return self.profile.explain_decision()
        else:
            return str(self)


def _validate_streaming_parameters(
    func: Callable,
    data: Union[List, Iterator],
    sample_size: int,
    target_chunk_duration: float,
    prefer_ordered: Optional[bool],
    buffer_size: Optional[int],
    enable_adaptive_chunking: bool,
    adaptation_rate: float,
    pool_manager: Any,
    enable_memory_backpressure: bool,
    memory_threshold: float
) -> None:
    """
    Validate parameters for optimize_streaming().

    Raises:
        ValueError: If any parameter is invalid
    """
    if not callable(func):
        raise ValueError("Invalid func: must be a callable function")

    if data is None:
        raise ValueError("Invalid data: cannot be None")

    if not isinstance(sample_size, int):
        raise ValueError(f"Invalid sample_size: must be int, got {type(sample_size).__name__}")
    if sample_size < 1:
        raise ValueError(f"Invalid sample_size: must be >= 1, got {sample_size}")
    if sample_size > 10000:
        raise ValueError(f"Invalid sample_size: must be <= 10000, got {sample_size}")

    if not isinstance(target_chunk_duration, (int, float)):
        raise ValueError(f"Invalid target_chunk_duration: must be numeric, got {type(target_chunk_duration).__name__}")
    if target_chunk_duration <= 0:
        raise ValueError(f"Invalid target_chunk_duration: must be > 0, got {target_chunk_duration}")
    if target_chunk_duration > 3600:
        raise ValueError(f"Invalid target_chunk_duration: must be <= 3600, got {target_chunk_duration}")

    if prefer_ordered is not None and not isinstance(prefer_ordered, bool):
        raise ValueError(f"Invalid prefer_ordered: must be bool or None, got {type(prefer_ordered).__name__}")

    if buffer_size is not None:
        if not isinstance(buffer_size, int):
            raise ValueError(f"Invalid buffer_size: must be int or None, got {type(buffer_size).__name__}")
        if buffer_size < 1:
            raise ValueError(f"Invalid buffer_size: must be >= 1 or None, got {buffer_size}")

    if not isinstance(enable_adaptive_chunking, bool):
        raise ValueError(f"Invalid enable_adaptive_chunking: must be bool, got {type(enable_adaptive_chunking).__name__}")

    if not isinstance(adaptation_rate, (int, float)):
        raise ValueError(f"Invalid adaptation_rate: must be numeric, got {type(adaptation_rate).__name__}")
    if not (0.0 <= adaptation_rate <= 1.0):
        raise ValueError(f"Invalid adaptation_rate: must be 0.0-1.0, got {adaptation_rate}")

    if not isinstance(enable_memory_backpressure, bool):
        raise ValueError(f"Invalid enable_memory_backpressure: must be bool, got {type(enable_memory_backpressure).__name__}")

    if not isinstance(memory_threshold, (int, float)):
        raise ValueError(f"Invalid memory_threshold: must be numeric, got {type(memory_threshold).__name__}")
    if not (0.0 <= memory_threshold <= 1.0):
        raise ValueError(f"Invalid memory_threshold: must be 0.0-1.0, got {memory_threshold}")

    # pool_manager validation (if provided)
    if pool_manager is not None:
        # Check if it has the required methods
        if not hasattr(pool_manager, 'get_pool'):
            raise ValueError("Invalid pool_manager: must have 'get_pool' method")


def optimize_streaming(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    prefer_ordered: Optional[bool] = None,
    buffer_size: Optional[int] = None,
    verbose: bool = False,
    use_spawn_benchmark: bool = True,
    use_chunking_benchmark: bool = True,
    profile: bool = False,
    enable_adaptive_chunking: bool = False,
    adaptation_rate: float = 0.3,
    pool_manager: Optional[Any] = None,
    enable_memory_backpressure: bool = False,
    memory_threshold: float = 0.8,
    enable_ml_prediction: bool = False,
    ml_confidence_threshold: float = 0.7,
    estimated_item_time: Optional[float] = None
) -> StreamingOptimizationResult:
    """
    Optimize parameters for streaming workloads using imap/imap_unordered.

    This function analyzes your function and data to determine optimal parameters
    for streaming execution (processing results one-by-one or in chunks without
    accumulating all results in memory). This is ideal for:

    - Very large datasets that don't fit in memory
    - Infinite generators or streams
    - Processing results as they become available
    - Avoiding memory accumulation of large return objects

    Args:
        func: Function to optimize (must accept single argument and be picklable)
        data: Input data (list, generator, or iterator)
        sample_size: Number of items to sample for analysis (default: 5)
        target_chunk_duration: Target duration per chunk in seconds (default: 0.2)
        prefer_ordered: Whether to prefer ordered results (imap vs imap_unordered).
                       If None, automatically chooses based on overhead analysis.
                       If True, forces imap(). If False, forces imap_unordered().
        buffer_size: Size of result buffer for imap/imap_unordered (default: None = auto).
                    Controls memory usage and parallelism. Larger = more memory,
                    better parallelism. Smaller = less memory, more backpressure.
        verbose: Print detailed analysis to stdout (default: False)
        use_spawn_benchmark: Measure actual spawn cost vs estimate (default: True)
        use_chunking_benchmark: Measure actual chunking overhead vs estimate (default: True)
        profile: Enable diagnostic profiling for detailed analysis (default: False)
        enable_adaptive_chunking: Enable runtime adaptive chunk size adjustment for
                                 heterogeneous workloads (default: False)
        adaptation_rate: How aggressively to adapt chunk sizes (0.0-1.0, default: 0.3).
                        Only used when enable_adaptive_chunking=True.
        pool_manager: Optional PoolManager instance for pool reuse across multiple
                     optimize_streaming calls (default: None = create new pools).
                     Use get_global_pool_manager() for application-wide reuse.
        enable_memory_backpressure: Enable memory-aware backpressure handling
                                   (default: False). Pauses consumption when memory
                                   pressure is high.
        memory_threshold: Memory usage threshold (0.0-1.0) to trigger backpressure
                         (default: 0.8 = 80%). Only used when
                         enable_memory_backpressure=True.
        enable_ml_prediction: Use ML to predict parameters without dry-run sampling
                             (default: False). Requires historical training data.
                             10-100x faster than dry-run when confident prediction available.
        ml_confidence_threshold: Minimum confidence (0-1) required for ML prediction
                                (default: 0.7). Falls back to dry-run if confidence too low.
        estimated_item_time: Optional rough estimate of per-item execution time (seconds).
                            Only used for ML prediction when enable_ml_prediction=True.
                            If not provided, a default estimate will be used.

    Returns:
        StreamingOptimizationResult with optimal parameters for streaming:
        - n_jobs: Number of worker processes
        - chunksize: Items per chunk for imap/imap_unordered
        - use_ordered: True for imap(), False for imap_unordered()
        - reason: Explanation of recommendation
        - estimated_speedup: Expected performance improvement
        - warnings: List of potential issues or constraints
        - data: Reconstructed data (for generators)
        - profile: Diagnostic profile (if enabled)
        - use_adaptive_chunking: Whether adaptive chunking is enabled
        - adaptive_chunking_params: Parameters for adaptive chunking
        - buffer_size: Recommended buffer size
        - memory_backpressure_enabled: Whether memory backpressure is enabled

    Usage Example:
        >>> from amorsize import optimize_streaming
        >>> from multiprocessing import Pool
        >>>
        >>> def process_item(x):
        ...     # Expensive function with large return value
        ...     return expensive_computation(x)
        >>>
        >>> # Optimize for streaming
        >>> result = optimize_streaming(process_item, data_generator(), verbose=True)
        >>>
        >>> # Use with imap/imap_unordered
        >>> with Pool(result.n_jobs) as pool:
        ...     if result.use_ordered:
        ...         iterator = pool.imap(process_item, result.data, chunksize=result.chunksize)
        ...     else:
        ...         iterator = pool.imap_unordered(process_item, result.data, chunksize=result.chunksize)
        ...
        ...     # Process results as they become available (no memory accumulation)
        ...     for item in iterator:
        ...         handle_result(item)

    Streaming vs Batch vs Map:
        - Use optimize_streaming() for: Large datasets, infinite streams, memory constraints
        - Use optimize() with Pool.map() for: Moderate datasets, need all results at once
        - Use process_in_batches() for: Large datasets with memory limits, batch processing

    Key Differences from optimize():
        - Does NOT consider result memory accumulation (streaming processes one at a time)
        - Provides guidance on ordered vs unordered based on overhead
        - Optimized for continuous processing rather than bulk operations
        - Suitable for infinite or very large datasets

    Note:
        For generators, the dry run consumes sample items. Use result.data
        instead of the original generator to get the reconstructed iterator
        with all items intact.
    """
    # Validate all parameters
    _validate_streaming_parameters(
        func, data, sample_size, target_chunk_duration,
        prefer_ordered, buffer_size, enable_adaptive_chunking,
        adaptation_rate, pool_manager, enable_memory_backpressure,
        memory_threshold
    )

    # Try ML prediction first if enabled
    if enable_ml_prediction:
        try:
            from .ml_prediction import predict_streaming_parameters
            from .sampling import estimate_total_items as est_total

            # Estimate data size for ML prediction
            # Note: For generators, we can't know size without consuming
            # For lists and other sized iterables, we can get the length
            data_size = est_total(data, sample_consumed=False)  # Don't assume consumed yet

            # Use provided estimate or default
            item_time = estimated_item_time if estimated_item_time is not None else 0.01

            if data_size > 0:
                ml_result = predict_streaming_parameters(
                    func=func,
                    data_size=data_size,
                    estimated_item_time=item_time,
                    confidence_threshold=ml_confidence_threshold,
                    verbose=verbose,
                    prefer_ordered=prefer_ordered
                )

                if ml_result is not None:
                    # ML prediction succeeded with high confidence
                    if verbose:
                        print(f"\n{'='*60}")
                        print("ML-ENHANCED STREAMING OPTIMIZATION")
                        print(f"{'='*60}")
                        print(f"✓ ML Prediction: n_jobs={ml_result.n_jobs}, "
                              f"chunksize={ml_result.chunksize}, "
                              f"buffer_size={ml_result.buffer_size}")
                        print(f"  Confidence: {ml_result.confidence:.1%}")
                        method = "imap" if ml_result.use_ordered else "imap_unordered"
                        print(f"  Method: {method}")
                        print(f"  Training samples: {ml_result.training_samples}")
                        print("\n→ Using ML prediction (10-100x faster than dry-run)")
                        print(f"{'='*60}\n")

                    # Determine buffer size (prefer user override)
                    final_buffer_size = buffer_size if buffer_size is not None else ml_result.buffer_size

                    # Determine adaptive chunking parameters
                    # Use ML recommendations if available, otherwise user settings
                    adaptive_params = {}
                    use_adaptive = enable_adaptive_chunking

                    # ML can recommend adaptive chunking for heterogeneous workloads
                    if ml_result.adaptive_chunking_enabled:
                        use_adaptive = True
                        adaptive_params = {
                            'initial_chunksize': ml_result.chunksize,
                            'target_chunk_duration': target_chunk_duration,
                            'adaptation_rate': ml_result.adaptation_rate or adaptation_rate,
                            'min_chunksize': ml_result.min_chunksize or max(1, ml_result.chunksize // 4),
                            'max_chunksize': ml_result.max_chunksize or (ml_result.chunksize * 4)
                        }
                        if verbose:
                            print(f"  → ML recommends adaptive chunking (rate={adaptive_params['adaptation_rate']:.2f})")
                    elif enable_adaptive_chunking:
                        # User explicitly enabled, use their settings
                        adaptive_params = {
                            'initial_chunksize': ml_result.chunksize,
                            'target_chunk_duration': target_chunk_duration,
                            'adaptation_rate': adaptation_rate,
                            'min_chunksize': max(1, ml_result.chunksize // 4),
                            'max_chunksize': ml_result.chunksize * 4
                        }

                    # Return ML-based result
                    return StreamingOptimizationResult(
                        n_jobs=ml_result.n_jobs,
                        chunksize=ml_result.chunksize,
                        use_ordered=ml_result.use_ordered,
                        reason=ml_result.reason,
                        estimated_speedup=2.0,  # Conservative estimate without dry-run
                        warnings=[],
                        data=data,
                        profile=None,  # No profile available from ML prediction
                        use_adaptive_chunking=use_adaptive,
                        adaptive_chunking_params=adaptive_params,
                        buffer_size=final_buffer_size,
                        memory_backpressure_enabled=enable_memory_backpressure,
                        # New in Iteration 115: for online learning
                        estimated_item_time=item_time,
                        pickle_size=None,  # Not available from ML prediction
                        coefficient_of_variation=None  # Not available from ML prediction
                    )
                elif verbose:
                    print(f"\n{'='*60}")
                    print("ML PREDICTION CONFIDENCE TOO LOW")
                    print(f"{'='*60}")
                    print("→ Falling back to dry-run sampling for accurate analysis")
                    print(f"{'='*60}\n")
            elif verbose:
                print("\nℹ Cannot estimate data size - skipping ML prediction\n")

        except ImportError:
            if verbose:
                print("\n⚠ ML prediction module not available - using dry-run sampling\n")
        except Exception as e:
            if verbose:
                print(f"\n⚠ ML prediction error: {e} - falling back to dry-run\n")

    # Initialize diagnostic profile if requested
    diag = DiagnosticProfile() if profile else None

    # Get system information
    physical_cores = get_physical_cores()
    spawn_cost = get_spawn_cost(use_benchmark=use_spawn_benchmark)
    chunking_overhead = get_chunking_overhead(use_benchmark=use_chunking_benchmark)
    start_method = get_multiprocessing_start_method()
    available_memory = get_available_memory()

    if verbose:
        print(f"\n{'='*60}")
        print("AMORSIZE STREAMING OPTIMIZATION")
        print(f"{'='*60}")
        print(f"System: {physical_cores} physical cores, {start_method} start method")
        print(f"Spawn cost: {spawn_cost*1000:.2f}ms per worker")
        print(f"Chunking overhead: {chunking_overhead*1000:.3f}ms per chunk")
        print(f"Available memory: {available_memory / (1024**3):.2f}GB")
        print()

    # Populate diagnostic profile
    if diag:
        diag.physical_cores = physical_cores
        diag.logical_cores = physical_cores * 2  # Assume hyperthreading
        diag.spawn_cost = spawn_cost
        diag.chunking_overhead = chunking_overhead
        diag.available_memory = available_memory
        diag.multiprocessing_start_method = start_method
        diag.target_chunk_duration = target_chunk_duration

    # Perform dry run sampling
    if verbose:
        print(f"Sampling function with {sample_size} items...")

    sampling_result = perform_dry_run(func, data, sample_size=sample_size)

    # Reconstruct data for generators
    from .sampling import reconstruct_iterator
    if sampling_result.is_generator:
        reconstructed_data = reconstruct_iterator(
            sampling_result.sample,
            sampling_result.remaining_data
        )
    else:
        reconstructed_data = data

    # Check for sampling errors
    if sampling_result.error:
        if verbose:
            print(f"✗ Sampling failed: {sampling_result.error}")
            print("→ Falling back to serial execution (n_jobs=1)")

        return StreamingOptimizationResult(
            n_jobs=1,
            chunksize=1,
            use_ordered=True,
            reason=f"Sampling error: {sampling_result.error}",
            estimated_speedup=1.0,
            warnings=[f"Sampling failed: {sampling_result.error}"],
            data=reconstructed_data,
            profile=diag,
            use_adaptive_chunking=False,
            buffer_size=1,
            memory_backpressure_enabled=False,
            estimated_item_time=None,
            pickle_size=None,
            coefficient_of_variation=None
        )

    # Populate sampling results in diagnostic profile
    if diag:
        diag.avg_execution_time = sampling_result.avg_time
        diag.avg_pickle_time = sampling_result.avg_pickle_time
        diag.return_size_bytes = sampling_result.return_size
        diag.peak_memory_bytes = sampling_result.peak_memory
        diag.sample_count = sampling_result.sample_count
        diag.is_picklable = sampling_result.is_picklable
        diag.coefficient_of_variation = sampling_result.coefficient_of_variation
        diag.is_heterogeneous = sampling_result.coefficient_of_variation > 0.5

    if verbose:
        print(f"✓ Sampling complete: {sampling_result.sample_count} items")
        print(f"  Avg execution time: {sampling_result.avg_time*1000:.3f}ms per item")
        print(f"  Avg pickle time: {sampling_result.avg_pickle_time*1000:.3f}ms per item")
        print(f"  Return size: {sampling_result.return_size} bytes")
        if sampling_result.coefficient_of_variation > 0:
            print(f"  Workload variability: CV={sampling_result.coefficient_of_variation:.2f}")
        print()

    # Check if function is picklable
    if not sampling_result.is_picklable:
        if verbose:
            print("✗ Function is not picklable")
            print("→ Cannot use multiprocessing (serial execution only)")

        return StreamingOptimizationResult(
            n_jobs=1,
            chunksize=1,
            use_ordered=True,
            reason="Function is not picklable - multiprocessing requires picklable functions",
            estimated_speedup=1.0,
            warnings=["Function is not picklable. Consider using dill or cloudpickle."],
            data=reconstructed_data,
            profile=diag,
            use_adaptive_chunking=False,
            buffer_size=1,
            memory_backpressure_enabled=False,
            estimated_item_time=sampling_result.avg_time,
            pickle_size=None,
            coefficient_of_variation=sampling_result.coefficient_of_variation
        )

    # Check if data items are picklable
    if not sampling_result.data_items_picklable:
        if verbose:
            print("✗ Data items are not picklable")
            if sampling_result.unpicklable_data_index is not None:
                print(f"  First unpicklable item at index: {sampling_result.unpicklable_data_index}")
            if sampling_result.data_pickle_error:
                print(f"  Error: {sampling_result.data_pickle_error}")
            print("→ Cannot use multiprocessing (serial execution only)")

        return StreamingOptimizationResult(
            n_jobs=1,
            chunksize=1,
            use_ordered=True,
            reason=f"Data items are not picklable - Data item at index {sampling_result.unpicklable_data_index} is not picklable",
            estimated_speedup=1.0,
            warnings=[
                "Data items contain unpicklable objects. "
                "Ensure data items don't contain thread locks, file handles, or other unpicklable objects."
            ],
            data=reconstructed_data,
            profile=diag,
            use_adaptive_chunking=False,
            buffer_size=1,
            memory_backpressure_enabled=False,
            estimated_item_time=sampling_result.avg_time,
            pickle_size=sampling_result.return_size,
            coefficient_of_variation=sampling_result.coefficient_of_variation
        )

    # Fast-fail checks for streaming optimization
    warnings = []

    # Check for nested parallelism
    if sampling_result.nested_parallelism_detected:
        warning_msg = (
            f"Nested parallelism detected: function uses internal threading "
            f"(libraries: {', '.join(sampling_result.parallel_libraries) if sampling_result.parallel_libraries else 'unknown'}). "
            f"Thread increase: +{sampling_result.thread_activity.get('delta', 0)} threads. "
            f"Reduce n_jobs to avoid oversubscription."
        )
        warnings.append(warning_msg)
        if verbose:
            print(f"⚠ {warning_msg}")

    # Check start method mismatch
    is_mismatch, mismatch_warning = check_start_method_mismatch()
    if is_mismatch:
        warnings.append(mismatch_warning)
        if verbose:
            print(f"⚠ {mismatch_warning}")

    # Estimate total items (for known-size datasets)
    total_items = estimate_total_items(reconstructed_data, sampling_result.is_generator)

    if diag:
        diag.total_items = total_items if total_items > 0 else -1

    # Calculate optimal chunksize based on target duration
    # For streaming, we want chunks that take target_chunk_duration seconds
    if sampling_result.avg_time > 0:
        optimal_chunksize = max(1, int(target_chunk_duration / sampling_result.avg_time))
    else:
        # If avg_time is zero or negative (error), use conservative default
        optimal_chunksize = 1

    # Adaptive chunking for heterogeneous workloads
    if sampling_result.coefficient_of_variation > 0.5:
        # Reduce chunksize for better load balancing
        cv = sampling_result.coefficient_of_variation
        scale_factor = max(0.25, 1.0 - cv * 0.5)
        optimal_chunksize = max(1, int(optimal_chunksize * scale_factor))

        if verbose:
            print(f"ℹ Heterogeneous workload (CV={cv:.2f}) - using smaller chunks for load balancing")
            print(f"  Adjusted chunksize: {optimal_chunksize}")

    if diag:
        diag.optimal_chunksize = optimal_chunksize

    # Calculate optimal n_jobs
    # For streaming, we don't have result memory accumulation constraint
    # So n_jobs is primarily limited by CPU cores and spawn cost

    # Check if function is fast enough to benefit from parallelization
    min_duration_for_parallel = spawn_cost / physical_cores
    if sampling_result.avg_time < min_duration_for_parallel:
        if verbose:
            print(f"✗ Function too fast ({sampling_result.avg_time*1000:.3f}ms per item)")
            print(f"  Spawn overhead ({spawn_cost*1000:.2f}ms) dominates execution time")
            print("→ Serial execution recommended")
            print(f"\n{'='*60}")
            print("OPTIMIZATION RESULTS")
            print(f"{'='*60}")
            print("Recommended: Serial execution (n_jobs=1)")
            print("Reason: Function too fast - spawn overhead dominates")

        if diag:
            diag.estimated_speedup = 1.0
            diag.rejection_reasons.append(
                f"Function too fast ({sampling_result.avg_time*1000:.3f}ms) - "
                f"spawn overhead ({spawn_cost*1000:.2f}ms) would dominate"
            )

        return StreamingOptimizationResult(
            n_jobs=1,
            chunksize=optimal_chunksize,
            use_ordered=True,
            reason=f"Function too fast ({sampling_result.avg_time*1000:.3f}ms per item) - spawn overhead would dominate",
            estimated_speedup=1.0,
            warnings=warnings,
            data=reconstructed_data,
            profile=diag,
            use_adaptive_chunking=False,
            buffer_size=buffer_size if buffer_size is not None else 1,
            memory_backpressure_enabled=enable_memory_backpressure,
            estimated_item_time=sampling_result.avg_time,
            pickle_size=sampling_result.return_size,
            coefficient_of_variation=sampling_result.coefficient_of_variation
        )

    # Calculate max workers based on CPU
    max_workers_cpu = physical_cores

    # Adjust for nested parallelism if detected
    if sampling_result.nested_parallelism_detected:
        from .sampling import check_parallel_environment_vars, estimate_internal_threads
        env_vars = check_parallel_environment_vars()
        estimated_threads = estimate_internal_threads(
            sampling_result.parallel_libraries,
            sampling_result.thread_activity,
            env_vars
        )
        adjusted_max_workers = max(1, physical_cores // estimated_threads)

        if adjusted_max_workers < max_workers_cpu:
            if verbose:
                print(f"ℹ Adjusting n_jobs from {max_workers_cpu} to {adjusted_max_workers}")
                print(f"  to avoid oversubscription ({estimated_threads} threads per worker)")
            max_workers_cpu = adjusted_max_workers
            warnings.append(
                f"Reduced n_jobs to {adjusted_max_workers} to prevent thread oversubscription "
                f"(function uses ~{estimated_threads} threads internally)"
            )

    if diag:
        diag.max_workers_cpu = max_workers_cpu
        diag.max_workers_memory = max_workers_cpu  # No result accumulation for streaming

    # Calculate speedup using Amdahl's Law (without result memory overhead)
    # For streaming, we process items incrementally, so no result accumulation
    if total_items > 0 and sampling_result.avg_time > 0:
        serial_time = total_items * sampling_result.avg_time

        if diag:
            diag.estimated_serial_time = serial_time

        # Calculate speedup for different worker counts
        best_speedup = 1.0
        optimal_n_jobs = 1

        for n in range(1, max_workers_cpu + 1):
            # Calculate total compute time for this worker count
            total_compute_time = total_items * sampling_result.avg_time

            speedup = calculate_amdahl_speedup(
                total_compute_time=total_compute_time,
                pickle_overhead_per_item=sampling_result.avg_pickle_time,
                spawn_cost_per_worker=spawn_cost,
                chunking_overhead_per_chunk=chunking_overhead,
                n_jobs=n,
                chunksize=optimal_chunksize,
                total_items=total_items,
                data_pickle_overhead_per_item=sampling_result.avg_data_pickle_time
            )

            if speedup > best_speedup:
                best_speedup = speedup
                optimal_n_jobs = n

        # Require at least 1.2x speedup for parallelization
        if best_speedup < 1.2:
            if verbose:
                print(f"✗ Insufficient speedup: {best_speedup:.2f}x (threshold: 1.2x)")
                print("→ Serial execution recommended")
                print(f"\n{'='*60}")
                print("OPTIMIZATION RESULTS")
                print(f"{'='*60}")
                print("Recommended: Serial execution (n_jobs=1)")
                print("Reason: Insufficient speedup")
                if warnings:
                    print("\nWarnings:")
                    for w in warnings:
                        print(f"  ⚠ {w}")
                print(f"{'='*60}\n")

            if diag:
                diag.estimated_speedup = 1.0
                diag.rejection_reasons.append(
                    f"Insufficient speedup: {best_speedup:.2f}x < 1.2x threshold"
                )

            # Respect user preference even for serial execution
            use_ordered_for_rejection = prefer_ordered if prefer_ordered is not None else True

            return StreamingOptimizationResult(
                n_jobs=1,
                chunksize=optimal_chunksize,
                use_ordered=use_ordered_for_rejection,
                reason=f"Insufficient speedup: {best_speedup:.2f}x (threshold: 1.2x)",
                estimated_speedup=1.0,
                warnings=warnings,
                data=reconstructed_data,
                profile=diag,
                use_adaptive_chunking=False,
                buffer_size=buffer_size if buffer_size is not None else 1,
                memory_backpressure_enabled=enable_memory_backpressure,
                estimated_item_time=sampling_result.avg_time,
                pickle_size=sampling_result.return_size,
                coefficient_of_variation=sampling_result.coefficient_of_variation
            )
    else:
        # Unknown dataset size or duration - use heuristic
        optimal_n_jobs = max_workers_cpu
        # Assume 80% efficiency for heuristic (conservative estimate)
        HEURISTIC_EFFICIENCY = 0.8
        best_speedup = float(optimal_n_jobs) * HEURISTIC_EFFICIENCY

        if verbose:
            print("ℹ Dataset size unknown - using heuristic estimation")

    if diag:
        diag.estimated_speedup = best_speedup
        diag.theoretical_max_speedup = float(optimal_n_jobs)
        diag.speedup_efficiency = best_speedup / optimal_n_jobs if optimal_n_jobs > 0 else 1.0

    # Decide between ordered (imap) vs unordered (imap_unordered)
    if prefer_ordered is not None:
        # User explicitly specified preference
        use_ordered = prefer_ordered
        order_reason = "user preference"
    else:
        # Auto-decide based on overhead analysis
        # imap_unordered is faster because it doesn't maintain result order
        # Use imap_unordered if overhead is significant relative to execution time
        order_overhead_fraction = (spawn_cost + sampling_result.avg_pickle_time) / sampling_result.avg_time

        if order_overhead_fraction > 0.2:
            # Overhead > 20% of execution time - use unordered for better performance
            use_ordered = False
            order_reason = f"unordered is ~10-20% faster (overhead={order_overhead_fraction*100:.0f}% of execution time)"
        else:
            # Overhead < 20% - ordered is fine, provides better UX
            use_ordered = True
            order_reason = "overhead is minimal, ordered results preferred for usability"

    if verbose:
        print(f"\n{'='*60}")
        print("OPTIMIZATION RESULTS")
        print(f"{'='*60}")
        print("Recommended configuration:")
        print(f"  n_jobs: {optimal_n_jobs} workers")
        print(f"  chunksize: {optimal_chunksize} items")
        print(f"  method: pool.{'imap' if use_ordered else 'imap_unordered'}()")
        print(f"  reason: {order_reason}")
        print(f"  estimated speedup: {best_speedup:.2f}x")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  ⚠ {w}")
        print(f"{'='*60}\n")

    # Build recommendation message
    method_name = "imap" if use_ordered else "imap_unordered"
    reason = (
        f"Streaming parallelization beneficial: {optimal_n_jobs} workers with chunks of {optimal_chunksize}. "
        f"Use pool.{method_name}() ({order_reason})."
    )

    if diag:
        diag.recommendations.append(
            f"Use pool.{method_name}() with n_jobs={optimal_n_jobs}, chunksize={optimal_chunksize}"
        )
        diag.recommendations.append(f"Expected speedup: {best_speedup:.2f}x")
        if not use_ordered:
            diag.recommendations.append(
                "Using imap_unordered() for better performance (results may arrive out of order)"
            )

    # Calculate adaptive chunking parameters if enabled
    adaptive_chunking_params = {}
    if enable_adaptive_chunking and sampling_result.coefficient_of_variation > 0.3:
        # Only enable adaptive chunking for heterogeneous workloads
        adaptive_chunking_params = {
            'initial_chunksize': optimal_chunksize,
            'target_chunk_duration': target_chunk_duration,
            'adaptation_rate': adaptation_rate,
            'min_chunksize': 1,
            'max_chunksize': optimal_chunksize * MAX_CHUNKSIZE_GROWTH_FACTOR,
            'enable_adaptation': True
        }
        if verbose:
            print(f"ℹ Adaptive chunking enabled (CV={sampling_result.coefficient_of_variation:.2f})")
            print(f"  Initial chunksize: {optimal_chunksize}, adaptation rate: {adaptation_rate}")
    elif enable_adaptive_chunking:
        # Homogeneous workload - adaptive chunking not beneficial
        if verbose:
            print(f"ℹ Adaptive chunking disabled (workload is homogeneous, CV={sampling_result.coefficient_of_variation:.2f})")
        enable_adaptive_chunking = False

    # Calculate buffer size if not provided
    calculated_buffer_size = buffer_size
    if calculated_buffer_size is None:
        # Auto-calculate buffer size based on memory and parallelism
        # Buffer should be large enough for good parallelism but not waste memory
        calculated_buffer_size = optimal_n_jobs * BUFFER_SIZE_MULTIPLIER

        # Adjust for memory constraints if backpressure is enabled
        if enable_memory_backpressure:
            # Estimate memory per result item
            memory_per_result = sampling_result.return_size
            if memory_per_result > 0:
                # Calculate how many results fit in memory budget
                max_results_in_memory = int(available_memory * RESULT_BUFFER_MEMORY_FRACTION / memory_per_result)
                max_results_in_memory = int(available_memory * 0.1 / memory_per_result)
                # Limit buffer size to prevent memory issues
                calculated_buffer_size = min(calculated_buffer_size, max(optimal_n_jobs, max_results_in_memory))
                if verbose and calculated_buffer_size < optimal_n_jobs * 3:
                    print(f"ℹ Buffer size limited to {calculated_buffer_size} due to memory constraints")

    # Add memory backpressure information to recommendations
    if enable_memory_backpressure and diag:
        diag.recommendations.append(
            f"Memory backpressure enabled (threshold: {memory_threshold*100:.0f}%)"
        )
        diag.recommendations.append(
            f"Buffer size: {calculated_buffer_size} items"
        )

    return StreamingOptimizationResult(
        n_jobs=optimal_n_jobs,
        chunksize=optimal_chunksize,
        use_ordered=use_ordered,
        reason=reason,
        estimated_speedup=best_speedup,
        warnings=warnings,
        data=reconstructed_data,
        profile=diag,
        use_adaptive_chunking=enable_adaptive_chunking,
        adaptive_chunking_params=adaptive_chunking_params,
        buffer_size=calculated_buffer_size,
        memory_backpressure_enabled=enable_memory_backpressure,
        # New in Iteration 115: for online learning
        estimated_item_time=sampling_result.avg_time,
        pickle_size=sampling_result.return_size,
        coefficient_of_variation=sampling_result.coefficient_of_variation
    )
