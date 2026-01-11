"""
Main optimizer module that coordinates the analysis and returns optimal parameters.
"""

from typing import Any, Callable, Iterator, List, Union, Tuple, Optional, Dict
import time
import warnings

from .system_info import (
    get_physical_cores,
    get_logical_cores,
    get_spawn_cost,
    get_chunking_overhead,
    calculate_max_workers,
    calculate_load_aware_workers,
    get_current_cpu_load,
    get_memory_pressure,
    check_start_method_mismatch,
    get_multiprocessing_start_method,
    get_available_memory,
    get_swap_usage
)
from .sampling import perform_dry_run, estimate_total_items, reconstruct_iterator, estimate_internal_threads, check_parallel_environment_vars
from .structured_logging import get_logger


class DiagnosticProfile:
    """
    Comprehensive diagnostic information about optimization decisions.
    
    This class captures all the factors that influenced the optimizer's
    decision, providing transparency into the decision-making process.
    """
    
    def __init__(self):
        # Sampling results
        self.avg_execution_time: float = 0.0
        self.avg_pickle_time: float = 0.0
        self.avg_data_pickle_time: float = 0.0
        self.return_size_bytes: int = 0
        self.data_size_bytes: int = 0
        self.peak_memory_bytes: int = 0
        self.sample_count: int = 0
        self.is_picklable: bool = False
        self.coefficient_of_variation: float = 0.0
        self.is_heterogeneous: bool = False
        self.workload_type: str = "cpu_bound"
        self.cpu_time_ratio: float = 1.0
        
        # System information
        self.physical_cores: int = 1
        self.logical_cores: int = 1
        self.spawn_cost: float = 0.0
        self.chunking_overhead: float = 0.0
        self.available_memory: int = 0
        self.multiprocessing_start_method: str = ""
        
        # Workload characteristics
        self.total_items: int = 0
        self.estimated_serial_time: float = 0.0
        self.estimated_result_memory: int = 0
        
        # Decision factors
        self.max_workers_cpu: int = 1
        self.max_workers_memory: int = 1
        self.optimal_chunksize: int = 1
        self.target_chunk_duration: float = 0.2
        
        # Overhead breakdown for recommended configuration
        self.overhead_spawn: float = 0.0
        self.overhead_ipc: float = 0.0
        self.overhead_chunking: float = 0.0
        self.parallel_compute_time: float = 0.0
        
        # Speedup analysis
        self.theoretical_max_speedup: float = 1.0
        self.estimated_speedup: float = 1.0
        self.speedup_efficiency: float = 1.0  # actual / theoretical
        
        # Decision path
        self.rejection_reasons: List[str] = []
        self.constraints: List[str] = []
        self.recommendations: List[str] = []
    
    def format_time(self, seconds: float) -> str:
        """Format time in human-readable form."""
        if seconds < 0.001:
            return f"{seconds * 1_000_000:.1f}μs"
        elif seconds < 1.0:
            return f"{seconds * 1000:.2f}ms"
        else:
            return f"{seconds:.3f}s"
    
    def format_bytes(self, bytes_val: int) -> str:
        """Format bytes in human-readable form."""
        if bytes_val < 1024:
            return f"{bytes_val}B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.2f}KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / (1024**2):.2f}MB"
        else:
            return f"{bytes_val / (1024**3):.2f}GB"
    
    def get_overhead_breakdown(self) -> Dict[str, float]:
        """Get breakdown of overhead components as percentages."""
        total_overhead = self.overhead_spawn + self.overhead_ipc + self.overhead_chunking
        if total_overhead == 0:
            return {"spawn": 0.0, "ipc": 0.0, "chunking": 0.0}
        
        return {
            "spawn": (self.overhead_spawn / total_overhead) * 100,
            "ipc": (self.overhead_ipc / total_overhead) * 100,
            "chunking": (self.overhead_chunking / total_overhead) * 100
        }
    
    def explain_decision(self) -> str:
        """
        Generate a detailed human-readable explanation of the optimization decision.
        
        Returns:
            Multi-line string with comprehensive diagnostic information
        """
        lines = []
        lines.append("=" * 70)
        lines.append("AMORSIZE DIAGNOSTIC PROFILE")
        lines.append("=" * 70)
        
        # Section 1: Workload Analysis
        lines.append("\n[1] WORKLOAD ANALYSIS")
        lines.append("-" * 70)
        lines.append(f"  Function execution time:  {self.format_time(self.avg_execution_time)} per item")
        lines.append(f"  Input pickle overhead:    {self.format_time(self.avg_data_pickle_time)} per item")
        lines.append(f"  Output pickle overhead:   {self.format_time(self.avg_pickle_time)} per item")
        lines.append(f"  Input data size:          {self.format_bytes(self.data_size_bytes)}")
        lines.append(f"  Return object size:       {self.format_bytes(self.return_size_bytes)}")
        lines.append(f"  Peak memory per call:     {self.format_bytes(self.peak_memory_bytes)}")
        if self.coefficient_of_variation > 0:
            lines.append(f"  Workload variability:     CV={self.coefficient_of_variation:.2f} ({'heterogeneous' if self.is_heterogeneous else 'homogeneous'})")
        lines.append(f"  Workload type:            {self.workload_type.replace('_', '-')} (CPU utilization: {self.cpu_time_ratio*100:.1f}%)")
        lines.append(f"  Total items to process:   {self.total_items if self.total_items > 0 else 'Unknown'}")
        if self.estimated_serial_time > 0:
            lines.append(f"  Estimated serial time:    {self.format_time(self.estimated_serial_time)}")
        if self.estimated_result_memory > 0:
            lines.append(f"  Total result memory:      {self.format_bytes(self.estimated_result_memory)}")
        
        # Section 2: System Resources
        lines.append("\n[2] SYSTEM RESOURCES")
        lines.append("-" * 70)
        lines.append(f"  Physical CPU cores:       {self.physical_cores}")
        lines.append(f"  Logical CPU cores:        {self.logical_cores}")
        lines.append(f"  Available memory:         {self.format_bytes(self.available_memory)}")
        lines.append(f"  Start method:             {self.multiprocessing_start_method}")
        lines.append(f"  Process spawn cost:       {self.format_time(self.spawn_cost)} per worker")
        lines.append(f"  Chunking overhead:        {self.format_time(self.chunking_overhead)} per chunk")
        
        # Section 3: Optimization Decision
        lines.append("\n[3] OPTIMIZATION DECISION")
        lines.append("-" * 70)
        lines.append(f"  Max workers (CPU limit):  {self.max_workers_cpu}")
        lines.append(f"  Max workers (RAM limit):  {self.max_workers_memory}")
        lines.append(f"  Optimal chunksize:        {self.optimal_chunksize}")
        lines.append(f"  Target chunk duration:    {self.format_time(self.target_chunk_duration)}")
        
        # Section 4: Performance Prediction
        if self.estimated_speedup > 1.0 or self.parallel_compute_time > 0:
            lines.append("\n[4] PERFORMANCE PREDICTION")
            lines.append("-" * 70)
            lines.append(f"  Theoretical max speedup:  {self.theoretical_max_speedup:.2f}x")
            lines.append(f"  Estimated actual speedup: {self.estimated_speedup:.2f}x")
            lines.append(f"  Parallel efficiency:      {self.speedup_efficiency * 100:.1f}%")
            
            if self.parallel_compute_time > 0:
                lines.append(f"\n  Time breakdown (parallel execution):")
                lines.append(f"    Computation:            {self.format_time(self.parallel_compute_time)}")
                lines.append(f"    Process spawn:          {self.format_time(self.overhead_spawn)}")
                lines.append(f"    IPC/Pickle:             {self.format_time(self.overhead_ipc)}")
                lines.append(f"    Task distribution:      {self.format_time(self.overhead_chunking)}")
                
                breakdown = self.get_overhead_breakdown()
                lines.append(f"\n  Overhead distribution:")
                lines.append(f"    Spawn:                  {breakdown['spawn']:.1f}%")
                lines.append(f"    IPC:                    {breakdown['ipc']:.1f}%")
                lines.append(f"    Chunking:               {breakdown['chunking']:.1f}%")
        
        # Section 5: Constraints and Rejections
        if self.rejection_reasons:
            lines.append("\n[5] REJECTION REASONS")
            lines.append("-" * 70)
            for reason in self.rejection_reasons:
                lines.append(f"  ✗ {reason}")
        
        if self.constraints:
            lines.append("\n[6] ACTIVE CONSTRAINTS")
            lines.append("-" * 70)
            for constraint in self.constraints:
                lines.append(f"  ⚠ {constraint}")
        
        # Section 6: Recommendations
        if self.recommendations:
            lines.append("\n[7] RECOMMENDATIONS")
            lines.append("-" * 70)
            for rec in self.recommendations:
                lines.append(f"  💡 {rec}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


class OptimizationResult:
    """Container for optimization results."""
    
    def __init__(
        self,
        n_jobs: int,
        chunksize: int,
        reason: str,
        estimated_speedup: float = 1.0,
        warnings: List[str] = None,
        data: Union[List, Iterator, None] = None,
        profile: Optional[DiagnosticProfile] = None,
        executor_type: str = "process",
        function_profiler_stats: Optional['pstats.Stats'] = None,
        cache_hit: bool = False
    ):
        self.n_jobs = n_jobs
        self.chunksize = chunksize
        self.reason = reason
        self.estimated_speedup = estimated_speedup
        self.warnings = warnings or []
        self.data = data
        self.profile = profile
        self.executor_type = executor_type  # "process" or "thread"
        self.function_profiler_stats = function_profiler_stats  # cProfile stats
        self.cache_hit = cache_hit  # True if result came from cache
    
    def __repr__(self):
        return (
            f"OptimizationResult(n_jobs={self.n_jobs}, "
            f"chunksize={self.chunksize}, "
            f"executor_type='{self.executor_type}', "
            f"estimated_speedup={self.estimated_speedup:.2f}x)"
        )
    
    def __str__(self):
        result = f"Recommended: n_jobs={self.n_jobs}, chunksize={self.chunksize}, executor={self.executor_type}\n"
        result += f"Reason: {self.reason}\n"
        result += f"Estimated speedup: {self.estimated_speedup:.2f}x"
        if self.cache_hit:
            result += " (cached)"
        if self.warnings:
            result += "\nWarnings:\n" + "\n".join(f"  - {w}" for w in self.warnings)
        return result
    
    def explain(self) -> str:
        """
        Get detailed diagnostic explanation of the optimization decision.
        
        Returns:
            Human-readable diagnostic report, or message if profiling wasn't enabled
        """
        if self.profile is None:
            return "Diagnostic profiling not enabled. Use optimize(..., profile=True) for detailed analysis."
        return self.profile.explain_decision()
    
    def show_function_profile(self, sort_by: str = 'cumulative', limit: int = 20) -> None:
        """
        Display cProfile function profiling results showing where time is spent
        inside the user's function.
        
        This shows the internal performance characteristics of your function,
        helping you identify bottlenecks and optimization opportunities.
        
        Args:
            sort_by: Sort key for stats. Common options:
                    'cumulative' - Total time in function + subcalls (default)
                    'time' - Time spent in function itself
                    'calls' - Number of function calls
                    'name' - Function name
            limit: Maximum number of lines to display (default: 20)
        
        Example:
            >>> result = optimize(my_func, data, enable_function_profiling=True)
            >>> result.show_function_profile(sort_by='cumulative', limit=30)
        
        Note:
            Requires enable_function_profiling=True in optimize() call.
        """
        if self.function_profiler_stats is None:
            print("Function profiling not enabled. Use optimize(..., enable_function_profiling=True)")
            return
        
        print("=" * 80)
        print("FUNCTION PERFORMANCE PROFILE")
        print("=" * 80)
        print("\nShowing where time is spent inside your function:")
        print(f"(Sorted by: {sort_by}, showing top {limit} entries)\n")
        
        # Sort and print stats
        self.function_profiler_stats.sort_stats(sort_by)
        self.function_profiler_stats.print_stats(limit)
    
    def save_function_profile(self, filepath: str, sort_by: str = 'cumulative', limit: int = 50) -> None:
        """
        Save cProfile function profiling results to a file.
        
        Args:
            filepath: Path to save profile report
            sort_by: Sort key for stats (see show_function_profile for options)
            limit: Maximum number of lines to include (default: 50)
        
        Example:
            >>> result = optimize(my_func, data, enable_function_profiling=True)
            >>> result.save_function_profile('function_profile.txt')
        """
        if self.function_profiler_stats is None:
            raise ValueError("Function profiling not enabled. Use optimize(..., enable_function_profiling=True)")
        
        # Import io for string capture
        import io
        
        # Capture stats to string buffer
        string_buffer = io.StringIO()
        self.function_profiler_stats.stream = string_buffer
        self.function_profiler_stats.sort_stats(sort_by)
        self.function_profiler_stats.print_stats(limit)
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("FUNCTION PERFORMANCE PROFILE\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Sorted by: {sort_by}, showing top {limit} entries\n\n")
            f.write(string_buffer.getvalue())
        
        print(f"Function profile saved to: {filepath}")
    
    def save_config(
        self,
        filepath: str,
        function_name: Optional[str] = None,
        notes: Optional[str] = None,
        overwrite: bool = False
    ) -> None:
        """
        Save this optimization result as a reusable configuration file.
        
        Args:
            filepath: Path to save configuration file
            function_name: Optional name of the function
            notes: Optional notes about this configuration
            overwrite: If True, overwrite existing file
        
        Examples:
            >>> result = optimize(my_func, data)
            >>> result.save_config('my_config.json', function_name='my_func')
        """
        from .config import save_config, ConfigData
        
        # Extract metadata from profile if available
        data_size = None
        avg_execution_time = None
        if self.profile:
            data_size = self.profile.total_items if self.profile.total_items > 0 else None
            avg_execution_time = self.profile.avg_execution_time
        
        config = ConfigData(
            n_jobs=self.n_jobs,
            chunksize=self.chunksize,
            executor_type=self.executor_type,
            estimated_speedup=self.estimated_speedup,
            function_name=function_name,
            data_size=data_size,
            avg_execution_time=avg_execution_time,
            notes=notes,
            source="optimize"
        )
        
        save_config(config, filepath, overwrite=overwrite)


def _validate_optimize_parameters(
    func: Any,
    data: Any,
    sample_size: int,
    target_chunk_duration: float,
    verbose: bool,
    use_spawn_benchmark: bool,
    use_chunking_benchmark: bool,
    profile: bool,
    auto_adjust_for_nested_parallelism: bool,
    progress_callback: Any,
    prefer_threads_for_io: bool,
    enable_function_profiling: bool,
    use_cache: bool,
    enable_memory_tracking: bool,
    use_ml_prediction: bool,
    ml_confidence_threshold: float,
    adjust_for_system_load: bool
) -> Optional[str]:
    """
    Validate input parameters for the optimize() function.
    
    Args:
        func: Function to validate
        data: Data to validate
        sample_size: Sample size to validate
        target_chunk_duration: Target chunk duration to validate
        verbose: Verbose flag to validate
        use_spawn_benchmark: Spawn benchmark flag to validate
        use_chunking_benchmark: Chunking benchmark flag to validate
        profile: Profile flag to validate
        auto_adjust_for_nested_parallelism: Auto-adjust flag to validate
        progress_callback: Progress callback to validate
        prefer_threads_for_io: Prefer threads for I/O flag to validate
        enable_function_profiling: Enable function profiling flag to validate
        use_cache: Use cache flag to validate
        enable_memory_tracking: Enable memory tracking flag to validate
        use_ml_prediction: Use ML prediction flag to validate
        ml_confidence_threshold: ML confidence threshold to validate
    
    Returns:
        None if all parameters are valid, error message string otherwise
    """
    # Validate func is callable
    if func is None:
        return "func parameter cannot be None"
    if not callable(func):
        return f"func parameter must be callable, got {type(func).__name__}"
    
    # Validate data is not None and is iterable
    if data is None:
        return "data parameter cannot be None"
    if not hasattr(data, '__iter__'):
        return f"data parameter must be iterable, got {type(data).__name__}"
    
    # Validate sample_size
    if not isinstance(sample_size, int):
        return f"sample_size must be an integer, got {type(sample_size).__name__}"
    if sample_size <= 0:
        return f"sample_size must be positive, got {sample_size}"
    if sample_size > 10000:
        return f"sample_size is unreasonably large ({sample_size}), maximum is 10000"
    
    # Validate target_chunk_duration
    if not isinstance(target_chunk_duration, (int, float)):
        return f"target_chunk_duration must be a number, got {type(target_chunk_duration).__name__}"
    if target_chunk_duration <= 0:
        return f"target_chunk_duration must be positive, got {target_chunk_duration}"
    if target_chunk_duration > 3600:
        return f"target_chunk_duration is unreasonably large ({target_chunk_duration}s), maximum is 3600s"
    
    # Validate boolean parameters
    if not isinstance(verbose, bool):
        return f"verbose must be a boolean, got {type(verbose).__name__}"
    if not isinstance(use_spawn_benchmark, bool):
        return f"use_spawn_benchmark must be a boolean, got {type(use_spawn_benchmark).__name__}"
    if not isinstance(use_chunking_benchmark, bool):
        return f"use_chunking_benchmark must be a boolean, got {type(use_chunking_benchmark).__name__}"
    if not isinstance(profile, bool):
        return f"profile must be a boolean, got {type(profile).__name__}"
    if not isinstance(auto_adjust_for_nested_parallelism, bool):
        return f"auto_adjust_for_nested_parallelism must be a boolean, got {type(auto_adjust_for_nested_parallelism).__name__}"
    if not isinstance(prefer_threads_for_io, bool):
        return f"prefer_threads_for_io must be a boolean, got {type(prefer_threads_for_io).__name__}"
    if not isinstance(enable_function_profiling, bool):
        return f"enable_function_profiling must be a boolean, got {type(enable_function_profiling).__name__}"
    if not isinstance(use_cache, bool):
        return f"use_cache must be a boolean, got {type(use_cache).__name__}"
    if not isinstance(enable_memory_tracking, bool):
        return f"enable_memory_tracking must be a boolean, got {type(enable_memory_tracking).__name__}"
    if not isinstance(use_ml_prediction, bool):
        return f"use_ml_prediction must be a boolean, got {type(use_ml_prediction).__name__}"
    
    # Validate ml_confidence_threshold
    if not isinstance(ml_confidence_threshold, (int, float)):
        return f"ml_confidence_threshold must be a number, got {type(ml_confidence_threshold).__name__}"
    if not (0.0 <= ml_confidence_threshold <= 1.0):
        return f"ml_confidence_threshold must be between 0.0 and 1.0, got {ml_confidence_threshold}"
    
    # Validate adjust_for_system_load
    if not isinstance(adjust_for_system_load, bool):
        return f"adjust_for_system_load must be a boolean, got {type(adjust_for_system_load).__name__}"
    
    # Validate progress_callback
    if progress_callback is not None and not callable(progress_callback):
        return f"progress_callback must be callable or None, got {type(progress_callback).__name__}"
    
    return None


def calculate_amdahl_speedup(
    total_compute_time: float,
    pickle_overhead_per_item: float,
    spawn_cost_per_worker: float,
    chunking_overhead_per_chunk: float,
    n_jobs: int,
    chunksize: int,
    total_items: int,
    data_pickle_overhead_per_item: float = 0.0
) -> float:
    """
    Calculate realistic speedup using Amdahl's Law with overhead accounting.
    
    This implements a refined version of Amdahl's Law that accounts for:
    1. Process spawn overhead (one-time cost per worker)
    2. Input data pickle overhead (per-item serialization cost for data → workers)
    3. Output result pickle overhead (per-item serialization cost for results → main)
    4. Chunking overhead (per-chunk communication cost)
    
    The formula breaks execution into:
    - Serial portion: spawn costs + data distribution overhead
    - Parallel portion: actual computation time divided across workers
    - IPC overhead: pickle time for both input data and output results (happens per item)
    
    Args:
        total_compute_time: Total serial computation time (seconds)
        pickle_overhead_per_item: Time to pickle one result (seconds)
        spawn_cost_per_worker: Time to spawn one worker process (seconds)
        chunking_overhead_per_chunk: Time per chunk for task distribution (seconds)
        n_jobs: Number of parallel workers
        chunksize: Items per chunk
        total_items: Total number of items to process
        data_pickle_overhead_per_item: Time to pickle one input data item (seconds)
    
    Returns:
        Estimated speedup factor (>1.0 means parallelization helps)
        
    Mathematical Model:
        Serial Time = T_compute
        
        Parallel Time = T_spawn + T_parallel_compute + T_data_ipc + T_result_ipc + T_chunking
        where:
            T_spawn = spawn_cost * n_jobs (one-time startup)
            T_parallel_compute = T_compute / n_jobs (ideal parallelization)
            T_data_ipc = data_pickle_overhead * total_items (input serialization)
            T_result_ipc = pickle_overhead * total_items (output serialization)
            T_chunking = chunking_overhead * num_chunks (task distribution)
        
        Both IPC overheads are unavoidable and happen regardless of parallelization,
        representing the "serial fraction" in Amdahl's Law because data must be
        distributed to workers and results collected sequentially.
    """
    if n_jobs <= 0 or total_compute_time <= 0:
        return 1.0
    
    # Serial execution time (baseline)
    serial_time = total_compute_time
    
    # Parallel execution breakdown:
    # 1. Spawn overhead (one-time cost to start all workers)
    spawn_overhead = spawn_cost_per_worker * n_jobs
    
    # 2. Parallel computation (ideal speedup)
    parallel_compute_time = total_compute_time / n_jobs
    
    # 3. Input data IPC overhead (pickle data items to send to workers)
    # This is per-item and largely serial (data distributed sequentially)
    data_ipc_overhead = data_pickle_overhead_per_item * total_items
    
    # 4. Output result IPC overhead (pickle/unpickle for inter-process communication)
    # This is per-item and largely serial (results collected sequentially)
    result_ipc_overhead = pickle_overhead_per_item * total_items
    
    # 5. Chunking overhead (additional cost per chunk for task distribution)
    # Each chunk requires queue operations, context switches, etc.
    # This is now dynamically measured per-system
    num_chunks = max(1, (total_items + chunksize - 1) // chunksize)
    chunking_overhead = chunking_overhead_per_chunk * num_chunks
    
    # Total parallel execution time
    parallel_time = spawn_overhead + parallel_compute_time + data_ipc_overhead + result_ipc_overhead + chunking_overhead
    
    # Calculate speedup
    if parallel_time > 0:
        speedup = serial_time / parallel_time
        # Speedup cannot exceed n_jobs (theoretical maximum)
        return min(speedup, float(n_jobs))
    
    return 1.0


def optimize(
    func: Callable[[Any], Any],
    data: Union[List, Iterator],
    sample_size: int = 5,
    target_chunk_duration: float = 0.2,
    verbose: bool = False,
    use_spawn_benchmark: bool = True,
    use_chunking_benchmark: bool = True,
    profile: bool = False,
    auto_adjust_for_nested_parallelism: bool = True,
    progress_callback: Optional[Callable[[str, float], None]] = None,
    prefer_threads_for_io: bool = True,
    enable_function_profiling: bool = False,
    use_cache: bool = True,
    enable_memory_tracking: bool = True,
    use_ml_prediction: bool = False,
    ml_confidence_threshold: float = 0.7,
    adjust_for_system_load: bool = False
) -> OptimizationResult:
    """
    Analyze a function and data to determine optimal parallelization parameters.
    
    This function performs a heuristic analysis to prevent "Negative Scaling"
    where parallelism is slower than serial execution, following these steps:
    
    1. Dry Run Sampling: Execute func on sample_size items to measure timing
    2. Overhead Estimation: Calculate process spawn costs (OS-dependent)
    3. Optimization: Determine optimal chunksize and n_jobs based on:
       - Target chunk duration (default: 0.2s to amortize IPC overhead)
       - Physical cores (not hyperthreaded logical cores)
       - Memory constraints (prevents OOM)
    
    Fail-Safe Protocol:
        If ANY step fails (pickling error, sampling error, etc.), the function
        returns n_jobs=1 (serial execution) rather than crashing your program.
        Safety over speed is the priority.
    
    Generator Handling:
        When data is a generator, the sampling process consumes items from it.
        To preserve the full dataset, the consumed items are automatically
        reconstructed using itertools.chain. The reconstructed data is available
        in the result.data attribute. For list inputs, result.data will contain
        the original list unchanged.
        
        IMPORTANT: When using generators, always use result.data instead of
        the original generator to ensure no data is lost:
        
        >>> gen = (x for x in range(1000))
        >>> result = optimize(func, gen)
        >>> # Use result.data, NOT gen!
        >>> with Pool(result.n_jobs) as pool:
        ...     results = pool.map(func, result.data, chunksize=result.chunksize)
    
    Args:
        func: The function to parallelize. Must accept a single argument and
              be picklable (no lambdas, no local functions with closures).
              Must be callable (not None).
        data: Iterable of input data (list, range, generator, etc.).
              Must be iterable (not None). Empty iterables are valid.
        sample_size: Number of items to sample for timing (default: 5).
                    Must be a positive integer (1 to 10000).
                    Larger values = more accurate but slower analysis.
        target_chunk_duration: Target duration per chunk in seconds (default: 0.2).
                              Must be a positive number (> 0, ≤ 3600).
                              Higher values = fewer chunks, less overhead.
        verbose: If True, print detailed analysis information.
                Must be a boolean.
        use_spawn_benchmark: If True, measure actual spawn cost instead of
                            using OS-based estimate. Default is True for accuracy.
                            Measurements are fast (~15ms) and cached globally.
                            Set to False for fastest startup if estimates are acceptable.
                            Must be a boolean.
        use_chunking_benchmark: If True, measure actual chunking overhead instead of
                               using default estimate. Default is True for accuracy.
                               Measurements are fast (~10ms) and cached globally.
                               Set to False for fastest startup if estimates are acceptable.
                               Must be a boolean.
        profile: If True, capture detailed diagnostic information in result.profile
                for in-depth analysis. Use result.explain() to view the diagnostic
                report. (default: False). Must be a boolean.
        auto_adjust_for_nested_parallelism: If True, automatically reduce n_jobs
                when nested parallelism is detected to avoid thread oversubscription.
                Calculates optimal n_jobs = physical_cores / estimated_internal_threads.
                (default: True). Set to False to disable auto-adjustment and only
                receive warnings. Must be a boolean.
        progress_callback: Optional callback function for progress updates during
                optimization. Called at key milestones with signature:
                `callback(phase: str, progress: float)` where phase is a descriptive
                string and progress is a value from 0.0 to 1.0. Default is None (no callbacks).
                Example: `lambda phase, pct: print(f"{phase}: {pct*100:.0f}%")`
        prefer_threads_for_io: If True, automatically use ThreadPoolExecutor instead of
                multiprocessing.Pool for I/O-bound workloads (< 30% CPU utilization).
                Threading is typically faster for I/O-bound tasks due to lower overhead
                and better handling of I/O operations that release the GIL. 
                (default: True). Set to False to always use multiprocessing.
                Must be a boolean.
        enable_function_profiling: If True, use Python's cProfile to profile the function
                execution during dry run sampling. This helps identify performance bottlenecks
                inside your function. Access results via result.show_function_profile() or
                result.save_function_profile(). (default: False). Must be a boolean.
                Note: Adds minimal overhead (~5-10% during sampling only).
        use_cache: If True, use cached optimization results when available. Caching speeds
                up repeated optimizations of the same function/workload by avoiding redundant
                dry-run sampling and benchmarking. Cache entries are automatically validated
                for system compatibility and expire after 7 days. (default: True).
                Set to False to force fresh optimization. Must be a boolean.
        enable_memory_tracking: If True, use tracemalloc to track peak memory usage during
                dry run sampling. Memory tracking adds ~2-3% overhead during sampling.
                When disabled, worker calculation falls back to using physical cores without
                memory constraints. (default: True). Must be a boolean.
                Set to False for fastest optimization when memory constraints are not needed.
        use_ml_prediction: If True, attempt to use ML-based prediction to estimate optimal
                parameters without dry-run sampling. Falls back to dry-run if confidence is
                too low or insufficient training data. This can provide 10-100x faster
                optimization for known workload patterns. (default: False). Must be a boolean.
                Note: ML prediction learns from cached optimization results. It becomes more
                accurate as you optimize more workloads.
        ml_confidence_threshold: Minimum confidence score (0.0-1.0) required to use ML
                prediction instead of dry-run sampling. Higher values (e.g., 0.9) ensure
                only high-confidence predictions are used but may fall back more often.
                Lower values (e.g., 0.5) use predictions more aggressively but with less
                certainty. (default: 0.7). Must be a float between 0.0 and 1.0.
        adjust_for_system_load: If True, dynamically adjust n_jobs based on current
                system CPU and memory load in addition to hardware constraints. This is
                useful in multi-tenant environments or when other processes are competing
                for resources. When enabled, worker count is reduced if CPU load exceeds
                70% or memory pressure exceeds 75%. (default: False for backward
                compatibility). Must be a boolean. Requires psutil for load detection.
    
    Raises:
        ValueError: If any parameter fails validation (e.g., None func, negative
                   sample_size, non-iterable data, invalid type for boolean params)
    
    Returns:
        OptimizationResult with:
            - n_jobs: Recommended number of workers
            - chunksize: Recommended chunk size
            - data: Reconstructed data (important for generators!)
            - executor_type: "process" (multiprocessing) or "thread" (threading)
            - reason: Explanation of recommendation
            - estimated_speedup: Expected performance improvement
            - warnings: List of constraints or issues
            - profile: DiagnosticProfile object (if profile=True)
            - function_profiler_stats: cProfile stats (if enable_function_profiling=True)
    
    Example:
        >>> def expensive_function(x):
        ...     result = 0
        ...     for i in range(1000):
        ...         result += x ** 2
        ...     return result
        >>> data = range(10000)
        >>> result = optimize(expensive_function, data, verbose=True)
        >>> print(f"Use n_jobs={result.n_jobs}, chunksize={result.chunksize}")
        >>> # Now use with multiprocessing.Pool:
        >>> from multiprocessing import Pool
        >>> with Pool(result.n_jobs) as pool:
        ...     # Use result.data to ensure generators are properly reconstructed
        ...     results = pool.map(expensive_function, result.data, chunksize=result.chunksize)
        
        >>> # For detailed diagnostic analysis:
        >>> result = optimize(expensive_function, data, profile=True)
        >>> print(result.explain())  # Shows comprehensive breakdown
    """
    # Step 0: Validate input parameters
    validation_error = _validate_optimize_parameters(
        func, data, sample_size, target_chunk_duration,
        verbose, use_spawn_benchmark, use_chunking_benchmark, profile,
        auto_adjust_for_nested_parallelism, progress_callback, prefer_threads_for_io,
        enable_function_profiling, use_cache, enable_memory_tracking,
        use_ml_prediction, ml_confidence_threshold, adjust_for_system_load
    )
    
    if validation_error:
        raise ValueError(f"Invalid parameter: {validation_error}")
    
    result_warnings = []
    
    # Initialize diagnostic profile if requested
    diag = DiagnosticProfile() if profile else None
    
    # Helper function to invoke progress callback safely
    def _report_progress(phase: str, progress: float):
        """Safely invoke progress callback if provided."""
        if progress_callback is not None:
            try:
                progress_callback(phase, progress)
            except Exception:
                # Silently ignore callback errors to avoid disrupting optimization
                pass
    
    # Helper function to save to cache and return result
    def _make_result_and_cache(
        n_jobs: int,
        chunksize: int,
        reason: str,
        estimated_speedup: float,
        warnings: List[str],
        data: Any,
        profile: Optional[DiagnosticProfile],
        executor: str,
        profiler_stats: Any,
        pickle_size: Optional[int] = None,
        coefficient_of_variation: Optional[float] = None,
        function_complexity: Optional[int] = None
    ) -> OptimizationResult:
        """Create OptimizationResult and save to cache if enabled."""
        # Save to cache if enabled and we have a cache key
        if use_cache and cache_key is not None and cache_entry is None:
            from .cache import save_cache_entry
            try:
                save_cache_entry(
                    cache_key=cache_key,
                    n_jobs=n_jobs,
                    chunksize=chunksize,
                    executor_type=executor,
                    estimated_speedup=estimated_speedup,
                    reason=reason,
                    warnings=warnings,
                    pickle_size=pickle_size,
                    coefficient_of_variation=coefficient_of_variation,
                    function_complexity=function_complexity
                )
            except Exception:
                # Silently fail if cache save fails
                pass
        
        return OptimizationResult(
            n_jobs=n_jobs,
            chunksize=chunksize,
            reason=reason,
            estimated_speedup=estimated_speedup,
            warnings=warnings,
            data=data,
            profile=profile,
            executor_type=executor,
            function_profiler_stats=profiler_stats
        )
    
    # Report start
    _report_progress("Starting optimization", 0.0)
    
    # Log optimization start
    logger = get_logger()
    func_name = getattr(func, '__name__', None)
    try:
        data_size_for_log = len(data) if hasattr(data, '__len__') else None
    except (TypeError, AttributeError):
        data_size_for_log = None
    logger.log_optimization_start(func_name=func_name, data_size=data_size_for_log)
    
    # Step 0.3: Try ML prediction if enabled (fastest path - before cache check)
    # ML prediction can provide 10-100x faster optimization than dry-run sampling
    ml_prediction = None
    if use_ml_prediction and not profile:
        # We need data size to make a prediction
        try:
            data_size_for_ml = len(data) if hasattr(data, '__len__') else None
        except (TypeError, AttributeError):
            data_size_for_ml = None
        
        if data_size_for_ml is not None and data_size_for_ml > 0:
            try:
                # Import ML module lazily (only when needed)
                from .ml_prediction import predict_parameters
                
                # Attempt prediction (with rough execution time estimate)
                # Use default 10ms per item as a conservative estimate
                ml_prediction = predict_parameters(
                    func=func,
                    data_size=data_size_for_ml,
                    estimated_item_time=0.01,  # Conservative 10ms estimate
                    confidence_threshold=ml_confidence_threshold,
                    verbose=verbose
                )
                
                if ml_prediction is not None:
                    if verbose:
                        print(f"✓ ML Prediction: n_jobs={ml_prediction.n_jobs}, "
                              f"chunksize={ml_prediction.chunksize}, "
                              f"confidence={ml_prediction.confidence:.1%}")
                        print(f"  Training samples: {ml_prediction.training_samples}, "
                              f"Feature match: {ml_prediction.feature_match_score:.1%}")
                    
                    # Log ML prediction success
                    logger.log_optimization_complete(
                        n_jobs=ml_prediction.n_jobs,
                        chunksize=ml_prediction.chunksize,
                        speedup=1.0,  # We don't have speedup estimate from ML yet
                        executor_type="process",  # Default
                        cache_hit=False
                    )
                    
                    # Return ML prediction result immediately (skip dry-run sampling)
                    return OptimizationResult(
                        n_jobs=ml_prediction.n_jobs,
                        chunksize=ml_prediction.chunksize,
                        reason=f"ML prediction: {ml_prediction.reason}",
                        estimated_speedup=1.0,  # Conservative estimate
                        warnings=[f"Using ML prediction (confidence: {ml_prediction.confidence:.1%})"],
                        data=data,  # Original data unchanged
                        profile=None,  # No profile for ML predictions
                        executor_type="process",  # Default to multiprocessing
                        function_profiler_stats=None,
                        cache_hit=False
                    )
                elif verbose:
                    print("✗ ML Prediction: Confidence too low, falling back to traditional optimization")
                    
            except ImportError:
                # ML module not available (shouldn't happen since it's internal)
                if verbose:
                    print("✗ ML Prediction: Module not available")
            except Exception as e:
                # ML prediction failed for some reason - fall back gracefully
                if verbose:
                    print(f"✗ ML Prediction: Error - {str(e)}")
    
    # Step 0.5: Check cache if enabled (but only if profile not requested)
    # We skip caching when profiling is requested because the cache doesn't
    # store full diagnostic profiles
    cache_entry = None
    cache_key = None
    if use_cache and not profile:
        # We need a preliminary data size estimate for cache key
        # Try to get it quickly without consuming the iterator
        try:
            data_size_estimate = len(data)  # Works for lists, ranges, etc.
        except TypeError:
            # For iterators/generators, we can't get size without consuming
            # Skip cache for now - will cache after first run
            data_size_estimate = None
        
        if data_size_estimate is not None:
            # Import cache module lazily (only when needed)
            from .cache import compute_cache_key, load_cache_entry, save_cache_entry
            
            # Use a very rough time estimate for cache key (will refine after dry run)
            # This is just for cache lookup - actual optimization will be more precise
            cache_key = compute_cache_key(func, data_size_estimate, 0.001)  # Assume 1ms per item
            cache_entry, cache_miss_reason = load_cache_entry(cache_key)
            
            if cache_entry is not None:
                if verbose:
                    print(f"✓ Cache hit! Using cached optimization result (saved {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cache_entry.timestamp))})")
                
                # Log cache hit
                logger.log_optimization_complete(
                    n_jobs=cache_entry.n_jobs,
                    chunksize=cache_entry.chunksize,
                    speedup=cache_entry.estimated_speedup,
                    executor_type=cache_entry.executor_type,
                    cache_hit=True
                )
                
                # Return cached result immediately
                # Note: We still need to handle generator reconstruction
                if hasattr(data, '__iter__') and not hasattr(data, '__len__'):
                    # It's a generator, we need to pass it through
                    reconstructed_data = data
                else:
                    reconstructed_data = data
                
                return OptimizationResult(
                    n_jobs=cache_entry.n_jobs,
                    chunksize=cache_entry.chunksize,
                    reason=f"{cache_entry.reason} (cached)",
                    estimated_speedup=cache_entry.estimated_speedup,
                    warnings=cache_entry.warnings,
                    data=reconstructed_data,
                    profile=None,  # Cache doesn't store full profile
                    executor_type=cache_entry.executor_type,
                    cache_hit=True
                )
    
    # Step 1: Perform dry run sampling
    if verbose:
        # Indicate if we attempted cache lookup but missed
        if use_cache and not profile and cache_key is not None and cache_entry is None:
            print(f"✗ Cache miss - {cache_miss_reason}")
        print("Performing dry run sampling...")
    
    _report_progress("Sampling function", 0.1)
    
    sampling_result = perform_dry_run(func, data, sample_size, enable_function_profiling, enable_memory_tracking)
    
    _report_progress("Sampling complete", 0.3)
    
    # Reconstruct data for generators to preserve consumed items
    # For lists, use original data. For generators, chain sample with remaining.
    if sampling_result.is_generator and sampling_result.remaining_data is not None:
        reconstructed_data = reconstruct_iterator(sampling_result.sample, sampling_result.remaining_data)
    else:
        reconstructed_data = sampling_result.remaining_data if sampling_result.remaining_data is not None else data
    
    # Populate diagnostic profile with sampling results
    if diag:
        diag.avg_execution_time = sampling_result.avg_time
        diag.avg_pickle_time = sampling_result.avg_pickle_time
        diag.avg_data_pickle_time = sampling_result.avg_data_pickle_time
        diag.return_size_bytes = sampling_result.return_size
        diag.data_size_bytes = sampling_result.data_size
        diag.peak_memory_bytes = sampling_result.peak_memory
        diag.sample_count = sampling_result.sample_count
        diag.is_picklable = sampling_result.is_picklable
        diag.coefficient_of_variation = sampling_result.coefficient_of_variation
        # Workload is considered heterogeneous if CV > 0.5
        # CV < 0.3: homogeneous (consistent execution times)
        # CV 0.3-0.7: moderately heterogeneous
        # CV > 0.7: highly heterogeneous (significant variance)
        diag.is_heterogeneous = sampling_result.coefficient_of_variation > 0.5
        diag.workload_type = sampling_result.workload_type
        diag.cpu_time_ratio = sampling_result.cpu_time_ratio
    
    # Compute ML features for cache (for ML training)
    # These features help improve ML prediction accuracy over time
    ml_pickle_size = sampling_result.return_size if sampling_result.return_size > 0 else None
    # CV of 0.0 is valid (perfectly homogeneous workload) - include if available
    ml_coefficient_of_variation = sampling_result.coefficient_of_variation if sampling_result.coefficient_of_variation >= 0 else None
    ml_function_complexity = None
    
    # Compute function complexity (bytecode size)
    try:
        if hasattr(func, '__code__'):
            ml_function_complexity = len(func.__code__.co_code)
    except (AttributeError, TypeError):
        # Built-in or special functions may not have __code__
        pass
    
    # Get physical cores early for nested parallelism adjustment calculations
    physical_cores = get_physical_cores()
    
    # Check for nested parallelism and add warnings
    estimated_internal_threads = 1  # Default: no internal parallelism
    
    if sampling_result.nested_parallelism_detected:
        nested_warning = "Nested parallelism detected: Function uses internal threading/parallelism"
        
        # Provide specific details - use .get() to safely access dict keys
        thread_delta = sampling_result.thread_activity.get('delta', 0)
        if thread_delta > 0:
            nested_warning += f" (thread count increased by {thread_delta})"
        
        if sampling_result.parallel_libraries:
            libs = ", ".join(sampling_result.parallel_libraries)
            nested_warning += f". Detected libraries: {libs}"
        
        result_warnings.append(nested_warning)
        
        # Estimate internal threads used by the function
        env_vars = check_parallel_environment_vars()
        estimated_internal_threads = estimate_internal_threads(
            sampling_result.parallel_libraries,
            sampling_result.thread_activity,
            env_vars
        )
        
        # Auto-adjust n_jobs if enabled
        if auto_adjust_for_nested_parallelism and estimated_internal_threads > 1:
            # Calculate what the adjusted value will be
            adjusted_max_workers = max(1, physical_cores // estimated_internal_threads)
            
            adjustment_msg = (
                f"Auto-adjusting n_jobs to account for {estimated_internal_threads} "
                f"estimated internal threads per worker"
            )
            result_warnings.append(adjustment_msg)
            
            if diag:
                diag.constraints.append(adjustment_msg)
                diag.recommendations.append(
                    f"n_jobs will be reduced to physical_cores/{estimated_internal_threads} "
                    f"= {adjusted_max_workers} to prevent thread oversubscription"
                )
            
            if verbose:
                print(f"INFO: {adjustment_msg}")
        else:
            # Not auto-adjusting, provide manual recommendations
            result_warnings.append(
                "Consider setting thread limits (e.g., OMP_NUM_THREADS=1, MKL_NUM_THREADS=1) "
                "to avoid thread oversubscription"
            )
            
            if diag:
                diag.recommendations.append(
                    "Set environment variables to limit internal threading: "
                    "OMP_NUM_THREADS=1, MKL_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1"
                )
                diag.recommendations.append(
                    "Or reduce n_jobs to account for internal parallelism "
                    "(e.g., use n_jobs=cores/internal_threads)"
                )
        
        if diag:
            diag.constraints.append(nested_warning)
        
        if verbose:
            print(f"WARNING: {nested_warning}")
            if sampling_result.parallel_libraries:
                print(f"  Detected libraries: {', '.join(sampling_result.parallel_libraries)}")
            # Use .get() with defaults for safe access
            thread_before = sampling_result.thread_activity.get('before', 0)
            thread_during = sampling_result.thread_activity.get('during', 0)
            thread_delta = sampling_result.thread_activity.get('delta', 0)
            print(f"  Thread activity: before={thread_before}, "
                  f"during={thread_during}, "
                  f"delta={thread_delta}")
            print(f"  Estimated internal threads: {estimated_internal_threads}")

    # Check workload type and provide recommendations for I/O-bound or mixed workloads
    if sampling_result.workload_type in ("io_bound", "mixed"):
        workload_warning = (
            f"Workload appears to be {sampling_result.workload_type.replace('_', '-')}: "
            f"CPU utilization is {sampling_result.cpu_time_ratio*100:.1f}%"
        )
        result_warnings.append(workload_warning)
        
        if sampling_result.workload_type == "io_bound":
            # Strongly recommend threading for I/O-bound tasks
            recommendation = (
                "For I/O-bound workloads, consider using threading "
                "(concurrent.futures.ThreadPoolExecutor) or asyncio instead of multiprocessing. "
                "Multiprocessing has higher overhead and doesn't benefit I/O operations that release the GIL."
            )
        else:  # mixed
            # For mixed workloads, provide both options
            recommendation = (
                "For mixed CPU/I/O workloads, consider: "
                "(1) threading if I/O dominates, or "
                "(2) multiprocessing if CPU computation is significant. "
                "Current recommendation uses multiprocessing but may be suboptimal."
            )
        
        result_warnings.append(recommendation)
        
        if diag:
            diag.constraints.append(workload_warning)
            diag.recommendations.append(recommendation)
        
        if verbose:
            print(f"WARNING: {workload_warning}")
            print(f"  {recommendation}")

    # Determine executor type based on workload and user preference
    executor_type = "process"  # Default to multiprocessing
    if prefer_threads_for_io and sampling_result.workload_type == "io_bound":
        # Use threading for I/O-bound workloads (lower overhead, better for I/O)
        executor_type = "thread"
        if verbose:
            print("Using ThreadPoolExecutor for I/O-bound workload")
        if diag:
            diag.recommendations.append("Using ThreadPoolExecutor instead of multiprocessing for I/O-bound workload")
    
    # Check for errors during sampling
    if sampling_result.error:
        if diag:
            diag.rejection_reasons.append(f"Sampling failed: {str(sampling_result.error)}")
        logger.log_rejection("sampling_failed", {"error": str(sampling_result.error)})
        _report_progress("Optimization complete", 1.0)
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason=f"Error during sampling: {str(sampling_result.error)}",
            estimated_speedup=1.0,
            warnings=[f"Sampling failed: {str(sampling_result.error)}"],
            data=reconstructed_data,
            profile=diag,
            executor_type=executor_type,  # Preserve I/O-bound threading decision
            function_profiler_stats=sampling_result.function_profiler_stats
        )
    
    # Check picklability
    if not sampling_result.is_picklable:
        if diag:
            diag.rejection_reasons.append("Function is not picklable - multiprocessing requires picklable functions")
            diag.recommendations.append("Use dill or cloudpickle to serialize complex functions")
        logger.log_rejection("function_not_picklable", {"executor_type": executor_type})
        _report_progress("Optimization complete", 1.0)
        return OptimizationResult(
            n_jobs=1,
            chunksize=1,
            reason="Function is not picklable - cannot use multiprocessing",
            estimated_speedup=1.0,
            warnings=["Function cannot be pickled. Use serial execution."],
            data=reconstructed_data,
            profile=diag,
            executor_type=executor_type,  # Preserve I/O-bound threading decision
            function_profiler_stats=sampling_result.function_profiler_stats
        )
    
    # Check if data items are picklable
    if not sampling_result.data_items_picklable:
        error_msg = f"Data item at index {sampling_result.unpicklable_data_index} is not picklable"
        if sampling_result.data_pickle_error:
            error_msg += f": {type(sampling_result.data_pickle_error).__name__}"
        
        if diag:
            diag.rejection_reasons.append(f"Data items are not picklable - multiprocessing requires picklable data")
            diag.recommendations.append("Ensure data items don't contain thread locks, file handles, or other unpicklable objects")
            diag.recommendations.append("Consider using dill or cloudpickle for more flexible serialization")
        
        _report_progress("Optimization complete", 1.0)
        return _make_result_and_cache(
            n_jobs=1,
            chunksize=1,
            reason=f"Data items are not picklable - {error_msg}",
            estimated_speedup=1.0,
            warnings=[error_msg + ". Use serial execution."],
            data=reconstructed_data,
            profile=diag,
            executor=executor_type,  # Preserve I/O-bound threading decision
            profiler_stats=sampling_result.function_profiler_stats,
            pickle_size=ml_pickle_size,
            coefficient_of_variation=ml_coefficient_of_variation,
            function_complexity=ml_function_complexity
        )
    
    avg_time = sampling_result.avg_time
    return_size = sampling_result.return_size
    peak_memory = sampling_result.peak_memory
    avg_pickle_time = sampling_result.avg_pickle_time
    
    # Log sampling completion
    logger.log_sampling_complete(
        sample_count=sampling_result.sample_count,
        avg_time=avg_time,
        is_picklable=sampling_result.is_picklable,
        workload_type=sampling_result.workload_type
    )
    
    if verbose:
        print(f"Average execution time: {avg_time:.4f}s")
        print(f"Average input data size: {sampling_result.data_size} bytes")
        print(f"Average input pickle time: {sampling_result.avg_data_pickle_time:.6f}s")
        print(f"Average return size: {return_size} bytes")
        print(f"Average output pickle time: {avg_pickle_time:.6f}s")
        print(f"Peak memory: {peak_memory} bytes")
        if sampling_result.coefficient_of_variation > 0:
            cv_label = "heterogeneous" if sampling_result.coefficient_of_variation > 0.5 else "homogeneous"
            print(f"Workload variability: CV={sampling_result.coefficient_of_variation:.2f} ({cv_label})")
    
    # Step 2: Estimate total workload and check for memory safety
    # This must happen BEFORE fast-fail checks because memory explosion
    # is a safety issue regardless of function speed
    total_items = estimate_total_items(data, False)
    available_memory = get_available_memory()
    memory_threshold = available_memory * 0.5
    
    if total_items > 0:
        estimated_total_time = avg_time * total_items
        
        # Estimate total memory for accumulated results
        # pool.map() keeps all results in memory until completion
        estimated_result_memory = return_size * total_items
        
        if diag:
            diag.total_items = total_items
            diag.estimated_serial_time = estimated_total_time
            diag.estimated_result_memory = estimated_result_memory
        
        if verbose:
            print(f"Estimated total items: {total_items}")
            print(f"Estimated serial execution time: {estimated_total_time:.2f}s")
            print(f"Estimated result memory accumulation: {estimated_result_memory / (1024**2):.2f} MB")
        
        # Check if result accumulation might cause OOM
        if estimated_result_memory > memory_threshold:
            memory_gb = estimated_result_memory / (1024**3)
            available_gb = available_memory / (1024**3)
            warning_message = (
                f"Large return objects detected: Results will consume ~{memory_gb:.2f}GB "
                f"(available: {available_gb:.2f}GB). Consider using imap_unordered() or "
                f"processing in batches to avoid memory exhaustion."
            )
            result_warnings.append(warning_message)
            
            if diag:
                diag.constraints.append(f"Result memory ({memory_gb:.2f}GB) exceeds safety threshold ({available_gb * 0.5:.2f}GB)")
                diag.recommendations.append("Consider using pool.imap_unordered() for memory-efficient streaming")
                diag.recommendations.append("Or process data in batches to control memory consumption")
            
            if verbose:
                print(f"WARNING: Result memory ({memory_gb:.2f}GB) exceeds safety threshold "
                      f"({available_gb * 0.5:.2f}GB). Risk of OOM!")
    else:
        # Can't determine size for generators
        estimated_total_time = None
        result_warnings.append("Cannot determine data size - using heuristics")
        if diag:
            diag.constraints.append("Generator size unknown - using conservative estimates")
    
    # Step 3: Get system information (physical_cores already retrieved earlier for nested parallelism)
    # Note: We need spawn_cost for intelligent fast-fail decisions, so get system info before checking
    _report_progress("Analyzing system", 0.5)
    
    logical_cores = get_logical_cores()
    spawn_cost = get_spawn_cost(use_benchmark=use_spawn_benchmark)
    chunking_overhead = get_chunking_overhead(use_benchmark=use_chunking_benchmark)
    
    # Log system info
    logger.log_system_info(
        physical_cores=physical_cores,
        logical_cores=logical_cores,
        available_memory_bytes=available_memory,
        start_method=get_multiprocessing_start_method()
    )
    
    # Populate diagnostic profile with system info
    if diag:
        diag.physical_cores = physical_cores
        diag.logical_cores = logical_cores
        diag.spawn_cost = spawn_cost
        diag.chunking_overhead = chunking_overhead
        diag.available_memory = available_memory
        diag.multiprocessing_start_method = get_multiprocessing_start_method()
        diag.target_chunk_duration = target_chunk_duration
    
    # Check for non-default start method
    is_mismatch, mismatch_warning = check_start_method_mismatch()
    if is_mismatch:
        result_warnings.append(mismatch_warning)
        if diag:
            diag.constraints.append(mismatch_warning)
    
    if verbose:
        print(f"Physical cores: {physical_cores}")
        print(f"Multiprocessing start method: {get_multiprocessing_start_method()}")
        print(f"Estimated spawn cost: {spawn_cost}s")
        print(f"Estimated chunking overhead: {chunking_overhead * 1000:.3f}ms per chunk")
        if is_mismatch:
            print(f"Warning: {mismatch_warning}")
    
    # Step 5: Early rejection for very small workloads
    # Only reject if even with 2 workers we can't get 1.2x speedup
    # This is more intelligent than a fixed threshold and uses actual overhead measurements
    if estimated_total_time is not None and total_items > 0 and avg_time > 0:
        # Calculate if 2 workers (minimum parallelization) would provide benefit
        # Use target_chunk_duration (function parameter) to estimate chunksize
        test_chunksize = max(1, int(target_chunk_duration / avg_time))
        test_speedup = calculate_amdahl_speedup(
            total_compute_time=total_items * avg_time,
            pickle_overhead_per_item=sampling_result.avg_pickle_time,
            spawn_cost_per_worker=spawn_cost,  # Per-worker spawn cost measured above
            chunking_overhead_per_chunk=chunking_overhead,
            n_jobs=2,
            chunksize=test_chunksize,
            total_items=total_items,
            data_pickle_overhead_per_item=sampling_result.avg_data_pickle_time
        )
        
        if test_speedup < 1.2:
            # Even with 2 workers, can't achieve minimum speedup threshold
            if diag:
                diag.rejection_reasons.append(
                    f"Even with 2 workers, estimated speedup is only {test_speedup:.2f}x (threshold: 1.2x)"
                )
                diag.rejection_reasons.append(
                    f"Workload too small ({estimated_total_time:.3f}s) relative to overhead "
                    f"(spawn: {spawn_cost*2:.3f}s, pickle: {sampling_result.avg_pickle_time*total_items:.3f}s)"
                )
                diag.estimated_speedup = 1.0
            
            if verbose:
                print(f"Workload too small for parallelization:")
                print(f"  Total work: {estimated_total_time:.3f}s")
                print(f"  Best speedup (2 workers): {test_speedup:.2f}x")
                print(f"  Threshold: 1.2x")
            
            _report_progress("Optimization complete", 1.0)
            # For serial execution (n_jobs=1), cap chunksize at total_items to avoid nonsensical values
            serial_chunksize = min(test_chunksize, total_items) if total_items > 0 else test_chunksize
            return _make_result_and_cache(
                n_jobs=1,
                chunksize=serial_chunksize,
                reason=f"Workload too small: best speedup with 2 workers is {test_speedup:.2f}x (threshold: 1.2x)",
                estimated_speedup=1.0,
                warnings=result_warnings,
                data=reconstructed_data,
                profile=diag,
                executor=executor_type,  # Preserve I/O-bound threading decision
                profiler_stats=sampling_result.function_profiler_stats,
                pickle_size=ml_pickle_size,
                coefficient_of_variation=ml_coefficient_of_variation,
                function_complexity=ml_function_complexity
            )
    
    # Step 6: Calculate optimal chunksize
    _report_progress("Calculating optimal parameters", 0.7)
    
    # Target: each chunk should take at least target_chunk_duration seconds
    # For heterogeneous workloads (high variance in execution times),
    # use smaller chunks to enable better load balancing
    if avg_time > 0:
        optimal_chunksize = max(1, int(target_chunk_duration / avg_time))
    else:
        optimal_chunksize = 1
    
    # Adaptive chunking: adjust for workload heterogeneity
    # High CV (coefficient of variation) means execution times vary significantly
    # Smaller chunks enable work-stealing and better load balance
    cv = sampling_result.coefficient_of_variation
    if cv > 0.5:
        # Heterogeneous workload: reduce chunksize for better load balancing
        # The higher the CV, the smaller the chunks should be
        # Scale factor ranges from 0.5 (CV=0.5) to 0.25 (CV=1.5+)
        scale_factor = max(0.25, 1.0 - (cv * 0.5))
        optimal_chunksize = max(1, int(optimal_chunksize * scale_factor))
        
        if verbose:
            print(f"Heterogeneous workload detected (CV={cv:.2f})")
            print(f"Reducing chunksize by {(1-scale_factor)*100:.0f}% for better load balancing")
        
        if diag:
            diag.constraints.append(f"Heterogeneous workload (CV={cv:.2f}) - using smaller chunks for load balancing")
            diag.recommendations.append(f"Workload variability detected - reduced chunksize to {optimal_chunksize} for better distribution")
    
    # Cap chunksize at a reasonable value
    if total_items > 0:
        # Don't make chunks larger than 10% of total items
        max_reasonable_chunksize = max(1, total_items // 10)
        optimal_chunksize = min(optimal_chunksize, max_reasonable_chunksize)
    
    if diag:
        diag.optimal_chunksize = optimal_chunksize
    
    if verbose:
        print(f"Optimal chunksize: {optimal_chunksize}")
    
    # Step 7: Determine number of workers
    # Consider memory constraints and optionally system load
    estimated_job_ram = peak_memory if peak_memory > 0 else 0
    
    if adjust_for_system_load:
        # Use load-aware calculation that considers current CPU and memory usage
        max_workers = calculate_load_aware_workers(physical_cores, estimated_job_ram)
        
        # Report current system load if verbose
        if verbose:
            current_cpu = get_current_cpu_load()
            current_memory = get_memory_pressure()
            print(f"Current system load: CPU {current_cpu:.1f}%, Memory {current_memory:.1f}%")
            if current_cpu >= 70.0 or current_memory >= 75.0:
                print(f"  Load-aware adjustment applied (high system load detected)")
    else:
        # Use standard calculation (hardware constraints only)
        max_workers = calculate_max_workers(physical_cores, estimated_job_ram)
    
    # Check for swap usage and warn if system is under memory pressure
    swap_percent, swap_used, swap_total = get_swap_usage()
    if swap_percent > 10.0:
        # System is using swap - workers have been reduced by calculate_max_workers
        swap_warning = (
            f"System is using swap memory ({swap_percent:.1f}% of {swap_total / (1024**3):.2f}GB). "
            f"Worker count has been reduced to prevent disk thrashing. "
            f"Consider freeing memory or reducing job memory footprint."
        )
        result_warnings.append(swap_warning)
        if diag:
            diag.constraints.append(swap_warning)
        if verbose:
            print(f"WARNING: System is using swap memory ({swap_percent:.1f}%)")
            print(f"  Worker count has been reduced to prevent disk thrashing")
    
    # Apply nested parallelism adjustment if enabled
    if auto_adjust_for_nested_parallelism and estimated_internal_threads > 1:
        # Reduce max_workers to account for internal threading
        # Formula: n_jobs = physical_cores / internal_threads
        adjusted_max_workers = max(1, physical_cores // estimated_internal_threads)
        
        # Warn if internal threads exceed physical cores (unusual but possible)
        if estimated_internal_threads > physical_cores:
            warning_msg = (
                f"Internal thread count ({estimated_internal_threads}) exceeds physical cores ({physical_cores}). "
                f"This may indicate overly aggressive internal parallelism settings."
            )
            result_warnings.append(warning_msg)
            if diag:
                diag.constraints.append(warning_msg)
        
        if adjusted_max_workers < max_workers:
            adjustment_info = (
                f"Reducing max_workers from {max_workers} to {adjusted_max_workers} "
                f"to account for {estimated_internal_threads} internal threads per worker"
            )
            result_warnings.append(adjustment_info)
            
            if diag:
                diag.constraints.append(adjustment_info)
            
            if verbose:
                print(f"INFO: {adjustment_info}")
            
            max_workers = adjusted_max_workers
    
    if diag:
        diag.max_workers_cpu = physical_cores
        diag.max_workers_memory = max_workers
    
    if max_workers < physical_cores:
        constraint_msg = (
            f"Memory constraints limit workers to {max_workers} "
            f"(physical cores: {physical_cores})"
        )
        result_warnings.append(constraint_msg)
        if diag:
            diag.constraints.append(constraint_msg)
            diag.recommendations.append("Consider reducing memory footprint per job or adding more RAM")
    
    # For CPU-bound tasks, use physical cores (not logical/hyperthreaded)
    optimal_n_jobs = max_workers
    
    if verbose:
        print(f"Optimal n_jobs: {optimal_n_jobs}")
    
    # Step 8: Estimate speedup using proper Amdahl's Law
    _report_progress("Estimating speedup", 0.9)
    
    if estimated_total_time and optimal_n_jobs > 1 and total_items > 0:
        # Use refined Amdahl's Law calculation with overhead accounting
        estimated_speedup = calculate_amdahl_speedup(
            total_compute_time=estimated_total_time,
            pickle_overhead_per_item=avg_pickle_time,
            spawn_cost_per_worker=spawn_cost,
            chunking_overhead_per_chunk=chunking_overhead,
            n_jobs=optimal_n_jobs,
            chunksize=optimal_chunksize,
            total_items=total_items,
            data_pickle_overhead_per_item=sampling_result.avg_data_pickle_time
        )
        
        # Populate diagnostic profile with speedup analysis
        if diag:
            diag.theoretical_max_speedup = float(optimal_n_jobs)
            diag.estimated_speedup = estimated_speedup
            diag.speedup_efficiency = estimated_speedup / optimal_n_jobs if optimal_n_jobs > 0 else 0.0
            
            # Calculate overhead breakdown
            num_chunks = max(1, (total_items + optimal_chunksize - 1) // optimal_chunksize)
            diag.overhead_spawn = spawn_cost * optimal_n_jobs
            diag.overhead_ipc = avg_pickle_time * total_items
            diag.overhead_chunking = chunking_overhead * num_chunks
            diag.parallel_compute_time = estimated_total_time / optimal_n_jobs
        
        if verbose:
            print(f"Estimated speedup: {estimated_speedup:.2f}x")
        
        # If speedup is less than 1.2x, parallelization may not be worth it
        if estimated_speedup < 1.2:
            if diag:
                # Reset speedup to 1.0 for serial execution (by definition)
                diag.estimated_speedup = 1.0
                diag.rejection_reasons.append(f"Estimated speedup ({estimated_speedup:.2f}x) below 1.2x threshold")
                diag.rejection_reasons.append("Parallelization overhead exceeds performance gains")
                diag.recommendations.append("Function needs to be slower or data size larger to benefit from parallelization")
            _report_progress("Optimization complete", 1.0)
            return OptimizationResult(
                n_jobs=1,
                chunksize=1,
                reason=f"Parallelization provides minimal benefit (estimated speedup: {estimated_speedup:.2f}x)",
                estimated_speedup=1.0,
                warnings=result_warnings + ["Overhead costs make parallelization inefficient for this workload"],
                data=reconstructed_data,
                profile=diag,
                executor_type=executor_type,  # Preserve I/O-bound threading decision
                function_profiler_stats=sampling_result.function_profiler_stats
            )
    else:
        # Fallback for cases where we don't have enough info
        estimated_speedup = float(optimal_n_jobs) * 0.7  # Conservative estimate
        if diag:
            diag.theoretical_max_speedup = float(optimal_n_jobs)
            diag.estimated_speedup = estimated_speedup
            diag.speedup_efficiency = 0.7
    
    # Step 9: Final sanity check
    if optimal_n_jobs == 1:
        if diag:
            # Reset speedup to 1.0 for serial execution (by definition)
            diag.estimated_speedup = 1.0
            diag.rejection_reasons.append("Only 1 worker recommended due to constraints")
        _report_progress("Optimization complete", 1.0)
        # For serial execution (n_jobs=1), cap chunksize at total_items to avoid nonsensical values
        serial_chunksize = min(optimal_chunksize, total_items) if total_items > 0 else optimal_chunksize
        return _make_result_and_cache(
            n_jobs=1,
            chunksize=serial_chunksize,
            reason="Serial execution recommended based on constraints",
            estimated_speedup=1.0,
            warnings=result_warnings,
            data=reconstructed_data,
            profile=diag,
            executor=executor_type,  # Preserve I/O-bound threading decision
            profiler_stats=sampling_result.function_profiler_stats,
            pickle_size=ml_pickle_size,
            coefficient_of_variation=ml_coefficient_of_variation,
            function_complexity=ml_function_complexity
        )
    
    # Success case: parallelization is beneficial
    if diag and estimated_speedup > 1.2:
        diag.recommendations.append(f"Use {optimal_n_jobs} workers with chunksize {optimal_chunksize} for ~{estimated_speedup:.2f}x speedup")
        if diag.speedup_efficiency < 0.5:
            diag.recommendations.append("Efficiency is low - consider if parallelization overhead is acceptable")
    
    # Log successful optimization
    logger.log_optimization_complete(
        n_jobs=optimal_n_jobs,
        chunksize=optimal_chunksize,
        speedup=estimated_speedup,
        executor_type=executor_type,
        cache_hit=False
    )
    
    _report_progress("Optimization complete", 1.0)
    
    return _make_result_and_cache(
        n_jobs=optimal_n_jobs,
        chunksize=optimal_chunksize,
        reason=f"Parallelization beneficial: {optimal_n_jobs} workers with chunks of {optimal_chunksize}",
        estimated_speedup=estimated_speedup,
        warnings=result_warnings,
        data=reconstructed_data,
        profile=diag,
        executor=executor_type,  # Use the determined executor type
        profiler_stats=sampling_result.function_profiler_stats,
        pickle_size=ml_pickle_size,
        coefficient_of_variation=ml_coefficient_of_variation,
        function_complexity=ml_function_complexity
    )
