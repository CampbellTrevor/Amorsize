"""
Command-line interface for Amorsize.

Enables running Amorsize from the command line:
    python -m amorsize optimize module.function --data-range 100
    python -m amorsize execute module.function --data-file input.txt
"""

import argparse
import importlib
import json
import os
import sys
from typing import Any, Callable, List

from . import __version__, execute, optimize, validate_system
from .comparison import ComparisonConfig, compare_strategies
from .history import (
    clear_history,
    compare_entries,
    delete_result,
    list_results,
    load_result,
    save_result,
)
from .tuning import quick_tune, tune_parameters


# ANSI color codes for terminal output
class Colors:
    """ANSI escape codes for colored terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'


# Global color settings
_USE_COLOR = None


def should_use_color() -> bool:
    """
    Determine if colored output should be used.
    
    Returns:
        True if colors should be used, False otherwise
    """
    global _USE_COLOR

    if _USE_COLOR is not None:
        return _USE_COLOR

    # Check if output is a TTY
    if not sys.stdout.isatty():
        return False

    # Check NO_COLOR environment variable (https://no-color.org/)
    if os.environ.get('NO_COLOR'):
        return False

    # Check TERM environment variable
    term = os.environ.get('TERM', '')
    if term == 'dumb':
        return False

    return True


def set_color_mode(enabled: bool):
    """Set whether colored output should be used."""
    global _USE_COLOR
    _USE_COLOR = enabled


def colorize(text: str, color: str) -> str:
    """
    Apply color to text if colors are enabled.
    
    Args:
        text: Text to colorize
        color: Color code from Colors class
        
    Returns:
        Colored text if colors enabled, otherwise plain text
    """
    if should_use_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def load_function(function_path: str) -> Callable:
    """
    Load a function from a module path.
    
    Args:
        function_path: Path in format "module.submodule.function" or "module:function"
        
    Returns:
        The loaded function
        
    Raises:
        ValueError: If function cannot be loaded
        
    Examples:
        >>> func = load_function("math.sqrt")
        >>> func = load_function("mymodule:myfunction")
    """
    # Support both . and : as separators
    if ':' in function_path:
        module_path, func_name = function_path.rsplit(':', 1)
    elif '.' in function_path:
        module_path, func_name = function_path.rsplit('.', 1)
    else:
        raise ValueError(
            f"Invalid function path: {function_path}. "
            "Use format 'module.function' or 'module:function'"
        )

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ValueError(f"Cannot import module '{module_path}': {e}")

    if not hasattr(module, func_name):
        raise ValueError(f"Module '{module_path}' has no function '{func_name}'")

    func = getattr(module, func_name)
    if not callable(func):
        raise ValueError(f"'{function_path}' is not a callable function")

    return func


def extract_function_name(function_path: str) -> str:
    """
    Extract the function name from a module path.
    
    Args:
        function_path: Path in format "module.function" or "module:function"
    
    Returns:
        Function name only (last component)
    
    Examples:
        >>> extract_function_name("math.factorial")
        'factorial'
        >>> extract_function_name("mymodule:myfunc")
        'myfunc'
    """
    if '.' in function_path:
        return function_path.split('.')[-1]
    elif ':' in function_path:
        return function_path.split(':')[-1]
    else:
        return function_path


def load_data(args: argparse.Namespace) -> List[Any]:
    """
    Load data based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        List of data items
        
    Priority order:
        1. --data-range: Generate range(N)
        2. --data-file: Read from file (one item per line)
        3. --data-stdin: Read from stdin (one item per line)
    """
    if args.data_range is not None:
        return list(range(args.data_range))

    if args.data_file:
        try:
            with open(args.data_file, 'r') as f:
                # Read lines, strip whitespace, filter empty lines
                data = [line.strip() for line in f if line.strip()]
                return data
        except Exception as e:
            raise ValueError(f"Cannot read data file '{args.data_file}': {e}")

    if args.data_stdin:
        try:
            # Read from stdin
            data = [line.strip() for line in sys.stdin if line.strip()]
            return data
        except Exception as e:
            raise ValueError(f"Cannot read from stdin: {e}")

    # No data source specified
    raise ValueError(
        "No data source specified. Use --data-range N, --data-file FILE, or --data-stdin"
    )


def format_output_human(result, mode: str, args: argparse.Namespace):
    """
    Format optimization result in human-readable form.
    
    Args:
        result: OptimizationResult or (results, OptimizationResult) tuple
        mode: "optimize" or "execute"
        args: Command-line arguments (for flags like --quiet, --explain, etc.)
    """
    # Extract flags
    quiet = getattr(args, 'quiet', False)
    show_explain = getattr(args, 'explain', False)
    show_tips = getattr(args, 'tips', False)
    show_overhead = getattr(args, 'show_overhead', False)
    show_profile = getattr(args, 'profile', False)

    # Handle execute mode with tuple result
    if mode == "execute" and isinstance(result, tuple):
        results, opt_result = result
        if not quiet:
            print(f"\n{colorize('='*70, Colors.CYAN)}")
            print(colorize("EXECUTION COMPLETE", Colors.BOLD + Colors.GREEN))
            print(f"{colorize('='*70, Colors.CYAN)}")
            print(f"Processed {colorize(str(len(results)), Colors.BOLD)} items")
            print(f"Sample results (first 5): {results[:5]}")
        result = opt_result
        if not quiet:
            print(f"\n{colorize('='*70, Colors.CYAN)}")
            print(colorize("OPTIMIZATION DETAILS", Colors.BOLD + Colors.CYAN))
            print(f"{colorize('='*70, Colors.CYAN)}")
    else:
        if not quiet:
            print(f"\n{colorize('='*70, Colors.CYAN)}")
            print(colorize("OPTIMIZATION ANALYSIS", Colors.BOLD + Colors.CYAN))
            print(f"{colorize('='*70, Colors.CYAN)}")

    # Quiet mode: just show the essentials
    if quiet:
        print(f"n_jobs={result.n_jobs} chunksize={result.chunksize} speedup={result.estimated_speedup:.2f}x")
        return

    # Show basic results with colors
    print(f"\n{colorize('Recommendation:', Colors.BOLD + Colors.GREEN)}")
    print(f"  {colorize('n_jobs:', Colors.BOLD)}            {colorize(str(result.n_jobs), Colors.BOLD + Colors.CYAN)}")
    print(f"  {colorize('chunksize:', Colors.BOLD)}         {colorize(str(result.chunksize), Colors.BOLD + Colors.CYAN)}")
    speedup_color = Colors.GREEN if result.estimated_speedup > 1.5 else Colors.YELLOW if result.estimated_speedup > 1.0 else Colors.RED
    print(f"  {colorize('estimated_speedup:', Colors.BOLD)} {colorize(f'{result.estimated_speedup:.2f}x', Colors.BOLD + speedup_color)}")

    print(f"\n{colorize('Reason:', Colors.BOLD)}")
    print(f"  {result.reason}")

    # Show warnings
    if result.warnings:
        print(f"\n{colorize('Warnings:', Colors.BOLD + Colors.YELLOW)}")
        for warning in result.warnings:
            print(f"  {colorize('⚠', Colors.YELLOW)} {warning}")

    # Show optimization tips if requested
    if show_tips:
        tips = _generate_optimization_tips(result)
        if tips:
            print(f"\n{colorize('='*70, Colors.CYAN)}")
            print(colorize("OPTIMIZATION TIPS", Colors.BOLD + Colors.MAGENTA))
            print(f"{colorize('='*70, Colors.CYAN)}")
            for i, tip in enumerate(tips, 1):
                print(f"\n{colorize(f'{i}.', Colors.BOLD + Colors.MAGENTA)} {tip}")

    # Show overhead breakdown if requested
    if show_overhead and result.profile:
        print(f"\n{colorize('='*70, Colors.CYAN)}")
        print(colorize("OVERHEAD BREAKDOWN", Colors.BOLD + Colors.YELLOW))
        print(f"{colorize('='*70, Colors.CYAN)}")
        _show_overhead_breakdown(result.profile)

    # Show user-friendly explanation if requested
    if show_explain and result.profile:
        print(f"\n{colorize('='*70, Colors.CYAN)}")
        print(colorize("DETAILED EXPLANATION", Colors.BOLD + Colors.BLUE))
        print(f"{colorize('='*70, Colors.CYAN)}")
        _show_user_friendly_explanation(result)

    # Show detailed profile if requested (technical details)
    if show_profile and result.profile:
        print(f"\n{colorize('='*70, Colors.CYAN)}")
        print(colorize("DETAILED DIAGNOSTIC PROFILE", Colors.BOLD + Colors.GRAY))
        print(f"{colorize('='*70, Colors.CYAN)}")
        print(result.explain())


def _generate_optimization_tips(result) -> List[str]:
    """
    Generate actionable optimization tips based on the result.
    
    Args:
        result: OptimizationResult
        
    Returns:
        List of tip strings
    """
    tips = []

    # Tip: Low speedup
    if result.estimated_speedup < 1.2:
        tips.append(
            f"{colorize('Low speedup detected', Colors.BOLD)} (< 1.2x): "
            f"Your function may be too fast or have high overhead. "
            f"Consider batching multiple items together or using serial execution."
        )

    # Tip: High n_jobs
    if result.profile and result.n_jobs >= result.profile.physical_cores:
        tips.append(
            f"{colorize('Using all cores', Colors.BOLD)}: "
            f"n_jobs={result.n_jobs} matches or exceeds physical cores ({result.profile.physical_cores}). "
            f"This is optimal for CPU-bound tasks but may cause oversubscription if your function uses internal threading."
        )

    # Tip: Small chunksize
    if result.profile and result.chunksize < 10:
        tips.append(
            f"{colorize('Small chunksize', Colors.BOLD)} ({result.chunksize}): "
            f"Each chunk processes few items. This is optimal for heterogeneous workloads "
            f"but may have higher overhead. Consider increasing target_chunk_duration if overhead is high."
        )

    # Tip: Large chunksize
    if result.profile and result.chunksize > 100:
        tips.append(
            f"{colorize('Large chunksize', Colors.BOLD)} ({result.chunksize}): "
            f"Each chunk processes many items. This reduces overhead but may cause load imbalance. "
            f"Consider decreasing target_chunk_duration for better load distribution."
        )

    # Tip: Memory constraints
    if result.profile and result.profile.max_workers_memory < result.profile.max_workers_cpu:
        tips.append(
            f"{colorize('Memory-constrained', Colors.BOLD)}: "
            f"Available memory limits n_jobs to {result.profile.max_workers_memory} "
            f"(physical cores: {result.profile.physical_cores}). "
            f"Consider reducing memory usage in your function or processing smaller batches."
        )

    # Tip: I/O bound workload
    if result.profile and result.profile.workload_type in ("io_bound", "mixed"):
        tips.append(
            f"{colorize('I/O-bound workload detected', Colors.BOLD)}: "
            f"Consider using {colorize('ThreadPoolExecutor', Colors.CYAN)} or {colorize('asyncio', Colors.CYAN)} "
            f"instead of multiprocessing for better performance with I/O operations."
        )

    # Tip: Heterogeneous workload
    if result.profile and result.profile.is_heterogeneous:
        tips.append(
            f"{colorize('Heterogeneous workload', Colors.BOLD)} (CV={result.profile.coefficient_of_variation:.2f}): "
            f"Item processing times vary significantly. Amorsize automatically reduces chunksize "
            f"to improve load balancing. Consider sorting items by expected processing time if possible."
        )

    return tips


def _show_overhead_breakdown(profile) -> None:
    """
    Show detailed overhead breakdown.
    
    Args:
        profile: DiagnosticProfile with overhead measurements
    """
    total_overhead = profile.overhead_spawn + profile.overhead_ipc + profile.overhead_chunking

    # Pre-compute percentages to avoid redundant calculations
    spawn_pct = (profile.overhead_spawn / total_overhead * 100) if total_overhead > 0 else 0.0
    ipc_pct = (profile.overhead_ipc / total_overhead * 100) if total_overhead > 0 else 0.0
    chunking_pct = (profile.overhead_chunking / total_overhead * 100) if total_overhead > 0 else 0.0

    print(f"\n{colorize('Overhead Components:', Colors.BOLD)}")
    print(f"  Spawn overhead:    {profile.overhead_spawn:.4f}s  ({colorize(f'{spawn_pct:.1f}%', Colors.CYAN)})")
    print(f"  IPC overhead:      {profile.overhead_ipc:.4f}s  ({colorize(f'{ipc_pct:.1f}%', Colors.CYAN)})")
    print(f"  Chunking overhead: {profile.overhead_chunking:.4f}s  ({colorize(f'{chunking_pct:.1f}%', Colors.CYAN)})")
    print(f"  {colorize('Total overhead:', Colors.BOLD)}    {colorize(f'{total_overhead:.4f}s', Colors.BOLD + Colors.YELLOW)}")

    print(f"\n{colorize('Performance Breakdown:', Colors.BOLD)}")
    print(f"  Parallel compute:  {profile.parallel_compute_time:.4f}s")
    print(f"  Total overhead:    {total_overhead:.4f}s")
    total_time = profile.parallel_compute_time + total_overhead
    print(f"  {colorize('Total time:', Colors.BOLD)}        {colorize(f'{total_time:.4f}s', Colors.BOLD + Colors.GREEN)}")

    if total_time > 0:
        efficiency = profile.parallel_compute_time / total_time * 100
        print(f"\n{colorize('Efficiency:', Colors.BOLD)} {colorize(f'{efficiency:.1f}%', Colors.BOLD + Colors.GREEN)} "
              f"(compute time / total time)")

    # Show per-item breakdown
    if profile.total_items > 0:
        print(f"\n{colorize('Per-Item Costs:', Colors.BOLD)}")
        print(f"  Avg execution time:  {profile.avg_execution_time*1000:.2f}ms")
        print(f"  Avg pickle time:     {profile.avg_pickle_time*1000:.2f}ms")
        print(f"  Avg data pickle:     {profile.avg_data_pickle_time*1000:.2f}ms")

        spawn_per_worker = profile.spawn_cost if profile.max_workers_cpu > 0 else 0
        print(f"  Spawn cost/worker:   {spawn_per_worker*1000:.2f}ms")


def _show_user_friendly_explanation(result) -> None:
    """
    Show user-friendly explanation of the optimization decision.
    
    Args:
        result: OptimizationResult
    """
    profile = result.profile
    if not profile:
        # This should not happen when --explain is used due to automatic profiling,
        # but provide a helpful message just in case
        print("Note: Profiling data not available. This feature requires profiling to be enabled.")
        return

    # Explain the decision
    print(f"\n{colorize('Why these parameters?', Colors.BOLD)}\n")

    # Explain n_jobs
    print(f"{colorize('n_jobs =', Colors.BOLD)} {colorize(str(result.n_jobs), Colors.BOLD + Colors.CYAN)}")
    if result.n_jobs == 1:
        print("  → Single worker (serial execution) because parallelization overhead exceeds benefits")
    elif result.n_jobs == profile.physical_cores:
        print(f"  → Using all {profile.physical_cores} physical cores for maximum CPU utilization")
    elif result.n_jobs < profile.physical_cores:
        if profile.max_workers_memory < profile.max_workers_cpu:
            print(f"  → Limited by available memory (can only safely run {result.n_jobs} workers)")
        else:
            print(f"  → Using {result.n_jobs} workers to balance parallelism and overhead")
    else:
        print(f"  → Using {result.n_jobs} workers (includes hyperthreading)")

    # Explain chunksize
    print(f"\n{colorize('chunksize =', Colors.BOLD)} {colorize(str(result.chunksize), Colors.BOLD + Colors.CYAN)}")
    target_duration = profile.target_chunk_duration
    actual_duration = profile.avg_execution_time * result.chunksize
    print(f"  → Target duration: {target_duration}s per chunk")
    print(f"  → Actual duration: ~{actual_duration:.3f}s per chunk")
    print(f"  → Each worker processes {result.chunksize} items per chunk")

    if profile.is_heterogeneous:
        print(f"  → Reduced from default due to heterogeneous workload (CV={profile.coefficient_of_variation:.2f})")

    # Explain speedup
    print(f"\n{colorize('estimated_speedup =', Colors.BOLD)} {colorize(f'{result.estimated_speedup:.2f}x', Colors.BOLD + Colors.GREEN)}")
    serial_time = profile.estimated_serial_time
    parallel_time = profile.parallel_compute_time + profile.overhead_spawn + profile.overhead_ipc + profile.overhead_chunking
    print(f"  → Serial time: {serial_time:.3f}s")
    print(f"  → Parallel time: {parallel_time:.3f}s (includes overhead)")
    print(f"  → Speedup: {serial_time:.3f}s / {parallel_time:.3f}s = {result.estimated_speedup:.2f}x")

    # Explain efficiency
    theoretical_max = min(result.n_jobs, profile.physical_cores)
    efficiency = (result.estimated_speedup / theoretical_max) * 100 if theoretical_max > 0 else 0
    print(f"  → Efficiency: {efficiency:.1f}% (actual speedup / theoretical max speedup of {theoretical_max}x)")

    # Key factors
    print(f"\n{colorize('Key factors considered:', Colors.BOLD)}")
    print(f"  • Physical cores: {profile.physical_cores}")
    print(f"  • Logical cores: {profile.logical_cores}")
    print(f"  • Available memory: {profile.available_memory / (1024**3):.1f} GB")
    print(f"  • Start method: {profile.multiprocessing_start_method}")
    print(f"  • Spawn cost: {profile.spawn_cost*1000:.1f}ms per worker")
    print(f"  • Workload type: {profile.workload_type}")

    if profile.rejection_reasons:
        print(f"\n{colorize('Constraints that limited optimization:', Colors.BOLD + Colors.YELLOW)}")
        for reason in profile.rejection_reasons:
            print(f"  {colorize('•', Colors.YELLOW)} {reason}")


def format_output_json(result, mode: str):
    """
    Format optimization result as JSON.
    
    Args:
        result: OptimizationResult or (results, OptimizationResult) tuple
        mode: "optimize" or "execute"
    """
    # Handle execute mode with tuple result
    if mode == "execute" and isinstance(result, tuple):
        results, opt_result = result
        output = {
            "mode": "execute",
            "results_count": len(results),
            "sample_results": results[:10],  # First 10 for JSON
            "optimization": {
                "n_jobs": opt_result.n_jobs,
                "chunksize": opt_result.chunksize,
                "estimated_speedup": opt_result.estimated_speedup,
                "reason": opt_result.reason,
                "warnings": opt_result.warnings
            }
        }
    else:
        output = {
            "mode": "optimize",
            "n_jobs": result.n_jobs,
            "chunksize": result.chunksize,
            "estimated_speedup": result.estimated_speedup,
            "reason": result.reason,
            "warnings": result.warnings
        }

    print(json.dumps(output, indent=2))


def _set_color_mode_from_args(args: argparse.Namespace):
    """
    Set color mode based on command-line arguments.
    
    Args:
        args: Command-line arguments
    """
    if hasattr(args, 'no_color') and args.no_color:
        set_color_mode(False)
    elif hasattr(args, 'color') and args.color:
        set_color_mode(True)


def cmd_optimize(args: argparse.Namespace):
    """Execute the 'optimize' command."""
    # Set color mode first
    _set_color_mode_from_args(args)

    # Load function
    func = load_function(args.function)

    # Load data
    data = load_data(args)

    # Determine if profiling is needed
    # Profile is needed for: --profile, --explain, --tips, --show-overhead
    need_profile = (
        args.profile or
        getattr(args, 'explain', False) or
        getattr(args, 'tips', False) or
        getattr(args, 'show_overhead', False)
    )

    # Run optimization
    result = optimize(
        func,
        data,
        sample_size=args.sample_size,
        target_chunk_duration=args.target_chunk_duration,
        verbose=args.verbose,
        profile=need_profile,  # Enable profiling if any feature needs it
        use_spawn_benchmark=not args.no_spawn_benchmark,
        use_chunking_benchmark=not args.no_chunking_benchmark,
        auto_adjust_for_nested_parallelism=not args.no_auto_adjust
    )

    # Format and display output
    if args.json:
        format_output_json(result, "optimize")
    else:
        format_output_human(result, "optimize", args)

    # Save configuration if requested
    if hasattr(args, 'save_config') and args.save_config:
        try:
            # Extract function name
            function_name = extract_function_name(args.function)

            result.save_config(
                args.save_config,
                function_name=function_name,
                overwrite=False
            )
            print(f"\n✓ Configuration saved to {args.save_config}")
        except FileExistsError:
            print(f"\n✗ Error: Configuration file already exists: {args.save_config}", file=sys.stderr)
            print("  Use a different filename or delete the existing file.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Error saving configuration: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def cmd_execute(args: argparse.Namespace):
    """Execute the 'execute' command."""
    # Set color mode first
    _set_color_mode_from_args(args)

    # Load function
    func = load_function(args.function)

    # Load data
    data = load_data(args)

    # Determine if profiling is needed
    need_profile = (
        args.profile or
        getattr(args, 'explain', False) or
        getattr(args, 'tips', False) or
        getattr(args, 'show_overhead', False)
    )

    # Check if we should load config instead of optimizing
    if hasattr(args, 'load_config') and args.load_config:
        try:
            import time
            from concurrent.futures import ThreadPoolExecutor
            from multiprocessing import Pool

            from .config import load_config

            config = load_config(args.load_config)

            if args.verbose:
                print(f"\n{'='*70}")
                print("LOADED CONFIGURATION")
                print(f"{'='*70}")
                print(config)
                print(f"\n{'='*70}")
                print("EXECUTING WITH LOADED CONFIG")
                print(f"{'='*70}\n")

            # Execute with loaded configuration
            start_time = time.perf_counter()

            if config.executor_type == "thread":
                with ThreadPoolExecutor(max_workers=config.n_jobs) as executor:
                    results = list(executor.map(func, data))
            else:
                with Pool(processes=config.n_jobs) as pool:
                    results = pool.map(func, data, chunksize=config.chunksize)

            end_time = time.perf_counter()
            execution_time = end_time - start_time

            # Format output
            if args.json:
                output = {
                    "mode": "execute",
                    "config_source": args.load_config,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type,
                    "execution_time": execution_time,
                    "results_count": len(results),
                    "sample_results": results[:10]
                }
                print(json.dumps(output, indent=2))
            else:
                print(f"\n{'='*70}")
                print("EXECUTION COMPLETE")
                print(f"{'='*70}")
                print(f"Configuration: {args.load_config}")
                print(f"Processed {len(results)} items in {execution_time:.4f}s")
                print(f"Sample results (first 5): {results[:5]}")
                print("\nUsed configuration:")
                print(f"  n_jobs:        {config.n_jobs}")
                print(f"  chunksize:     {config.chunksize}")
                print(f"  executor_type: {config.executor_type}")

            return

        except FileNotFoundError:
            print(f"\n✗ Error: Configuration file not found: {args.load_config}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Error loading configuration: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    # Normal execution path (optimize then execute)
    result = execute(
        func,
        data,
        sample_size=args.sample_size,
        target_chunk_duration=args.target_chunk_duration,
        verbose=args.verbose,
        profile=need_profile,  # Enable profiling if any feature needs it
        use_spawn_benchmark=not args.no_spawn_benchmark,
        use_chunking_benchmark=not args.no_chunking_benchmark,
        auto_adjust_for_nested_parallelism=not args.no_auto_adjust,
        return_optimization_result=True  # Always get both for CLI
    )

    # Format and display output
    if args.json:
        format_output_json(result, "execute")
    else:
        format_output_human(result, "execute", args)


def cmd_validate(args: argparse.Namespace):
    """Execute the 'validate' command."""
    # Run system validation
    result = validate_system(verbose=args.verbose)

    # Format and display output
    if args.json:
        # JSON output for programmatic use
        output = {
            "checks_passed": result.checks_passed,
            "checks_failed": result.checks_failed,
            "overall_health": result.overall_health,
            "warnings": result.warnings,
            "errors": result.errors,
            "details": result.details
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        # Human-readable output
        print(result)

    # Exit with appropriate code
    if result.overall_health in ["poor", "critical"]:
        sys.exit(1)


def cmd_tune(args: argparse.Namespace):
    """Execute the 'tune' command."""
    # Load function
    func = load_function(args.function)

    # Load data
    data = load_data(args)

    # Run tuning
    if args.quick:
        result = quick_tune(
            func,
            data,
            verbose=args.verbose,
            prefer_threads_for_io=args.threads
        )
    else:
        result = tune_parameters(
            func,
            data,
            n_jobs_range=args.n_jobs_range,
            chunksize_range=args.chunksize_range,
            use_optimizer_hint=not args.no_optimizer_hint,
            verbose=args.verbose,
            timeout_per_config=args.timeout_per_config,
            prefer_threads_for_io=args.threads
        )

    # Format and display output
    if args.json:
        # JSON output
        output = {
            "best_n_jobs": result.best_n_jobs,
            "best_chunksize": result.best_chunksize,
            "best_time": result.best_time,
            "best_speedup": result.best_speedup,
            "serial_time": result.serial_time,
            "configurations_tested": result.configurations_tested,
            "search_strategy": result.search_strategy,
            "executor_type": result.executor_type,
            "top_configurations": result.get_top_configurations(n=5)
        }

        if result.optimization_hint:
            output["optimizer_hint"] = {
                "n_jobs": result.optimization_hint.n_jobs,
                "chunksize": result.optimization_hint.chunksize,
                "estimated_speedup": result.optimization_hint.estimated_speedup
            }

        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(result)

    # Save result to history if requested
    if hasattr(args, 'save_result') and args.save_result:
        try:
            # For tuning, we'll convert it to a ComparisonResult-like format
            # by creating a minimal comparison result
            # Note: This is a simplified save - ideally we'd have a TuningEntry type
            from .comparison import ComparisonConfig, ComparisonResult

            # Create a config for the best result
            best_config = ComparisonConfig(
                name=f"Tuned: {result.best_n_jobs}x{result.best_chunksize}",
                n_jobs=result.best_n_jobs,
                chunksize=result.best_chunksize,
                executor_type=result.executor_type
            )

            # Create a minimal comparison result for history
            comparison_result = ComparisonResult(
                best_config=best_config,
                best_time=result.best_time,
                serial_time=result.serial_time,
                best_speedup=result.best_speedup,
                configs=[best_config],
                execution_times=[result.best_time],
                speedups=[result.best_speedup],
                timing_details={}
            )

            # Extract function name
            function_name = extract_function_name(args.function)

            # Get data size
            data_size = len(data) if hasattr(data, '__len__') else 0

            entry_id = save_result(comparison_result, args.save_result, function_name=function_name, data_size=data_size)
            print(f"\n✓ Tuning result saved to history as '{args.save_result}' (ID: {entry_id})")
        except Exception as e:
            print(f"\nWarning: Failed to save result to history: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()

    # Save configuration if requested
    if hasattr(args, 'save_config') and args.save_config:
        try:
            # Extract function name
            function_name = extract_function_name(args.function)

            result.save_config(
                args.save_config,
                function_name=function_name,
                overwrite=False
            )
            print(f"\n✓ Configuration saved to {args.save_config}")
        except FileExistsError:
            print(f"\n✗ Error: Configuration file already exists: {args.save_config}", file=sys.stderr)
            print("  Use a different filename or delete the existing file.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Error saving configuration: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def parse_strategy_config(config_str: str) -> ComparisonConfig:
    """
    Parse a strategy config from command line string.
    
    Format: "name:n_jobs,chunksize,executor" or "n_jobs,chunksize"
    
    Args:
        config_str: Strategy specification string
        
    Returns:
        ComparisonConfig object
        
    Examples:
        "2,50" -> ComparisonConfig("2 processes", n_jobs=2, chunksize=50)
        "Custom:4,25,thread" -> ComparisonConfig("Custom", n_jobs=4, chunksize=25, executor_type="thread")
        "8,10,process" -> ComparisonConfig("8 processes", n_jobs=8, chunksize=10, executor_type="process")
    """
    # Check if config has a name prefix
    if ':' in config_str:
        name, rest = config_str.split(':', 1)
        name = name.strip()
    else:
        name = None
        rest = config_str

    # Parse the parameters
    parts = [p.strip() for p in rest.split(',')]

    if len(parts) < 2:
        raise ValueError(
            f"Invalid config format '{config_str}'. "
            "Expected format: 'n_jobs,chunksize[,executor]' or 'name:n_jobs,chunksize[,executor]'"
        )

    try:
        n_jobs = int(parts[0])
        chunksize = int(parts[1])
    except ValueError:
        raise ValueError(
            f"Invalid n_jobs or chunksize in '{config_str}'. "
            "Both must be integers."
        )

    # Parse executor type if provided
    executor_type = "process"  # default
    if len(parts) >= 3:
        executor_type = parts[2].lower()
        if executor_type not in ["process", "thread", "serial"]:
            raise ValueError(
                f"Invalid executor type '{executor_type}' in '{config_str}'. "
                "Must be 'process', 'thread', or 'serial'."
            )

    # Generate default name if not provided
    if name is None:
        if n_jobs == 1 or executor_type == "serial":
            name = "Serial"
        else:
            executor_label = "processes" if executor_type == "process" else f"{executor_type}s"
            name = f"{n_jobs} {executor_label}"

    return ComparisonConfig(name, n_jobs, chunksize, executor_type)


def cmd_compare(args: argparse.Namespace):
    """Execute the 'compare' command."""
    # Load function
    func = load_function(args.function)

    # Load data
    data = load_data(args)

    # Parse strategy configs
    configs = []

    # Always include serial baseline unless explicitly disabled
    if not args.no_baseline:
        configs.append(ComparisonConfig("Serial", n_jobs=1))

    # Add optimizer recommendation if requested
    if args.include_optimizer:
        if args.verbose:
            print("Computing optimizer recommendation...")

        opt_result = optimize(
            func,
            data,
            sample_size=args.sample_size,
            target_chunk_duration=args.target_chunk_duration,
            verbose=args.verbose,
            use_spawn_benchmark=not args.no_spawn_benchmark,
            use_chunking_benchmark=not args.no_chunking_benchmark,
            auto_adjust_for_nested_parallelism=not args.no_auto_adjust
        )

        configs.append(
            ComparisonConfig(
                "Optimizer",
                n_jobs=opt_result.n_jobs,
                chunksize=opt_result.chunksize,
                executor_type=opt_result.executor_type
            )
        )

        if args.verbose:
            print(f"Optimizer recommends: n_jobs={opt_result.n_jobs}, "
                  f"chunksize={opt_result.chunksize}, executor={opt_result.executor_type}\n")

    # Parse user-provided configs
    if args.configs:
        for config_str in args.configs:
            try:
                config = parse_strategy_config(config_str)
                configs.append(config)
            except ValueError as e:
                print(f"Error parsing config '{config_str}': {e}", file=sys.stderr)
                sys.exit(1)

    # Validate we have at least 2 configs to compare
    if len(configs) < 2:
        print("Error: Need at least 2 configurations to compare.", file=sys.stderr)
        print("Use --configs to specify strategies or --include-optimizer", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Comparing {len(configs)} strategies...\n")

    # Run comparison
    result = compare_strategies(
        func,
        data,
        configs,
        max_items=args.max_items,
        timeout=args.timeout,
        verbose=args.verbose
    )

    # Format and display output
    if args.json:
        # JSON output
        output = {
            "strategies": [
                {
                    "name": config.name,
                    "n_jobs": config.n_jobs,
                    "chunksize": config.chunksize,
                    "executor_type": config.executor_type,
                    "time": time,
                    "speedup": speedup
                }
                for config, time, speedup in zip(result.configs, result.execution_times, result.speedups)
            ],
            "best_strategy": {
                "name": result.best_config.name,
                "n_jobs": result.best_config.n_jobs,
                "chunksize": result.best_config.chunksize,
                "executor_type": result.best_config.executor_type,
                "time": result.best_time,
                "speedup": result.speedups[result.best_config_index]
            },
            "recommendations": result.recommendations
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(result)

    # Generate visualizations if requested
    if args.visualize:
        try:
            from .visualization import check_matplotlib, visualize_comparison_result

            if not check_matplotlib():
                print("\nWarning: matplotlib is not installed. Skipping visualization.", file=sys.stderr)
                print("Install matplotlib with: pip install matplotlib", file=sys.stderr)
            else:
                if args.verbose:
                    print(f"\nGenerating visualizations in {args.visualize}...")

                plot_paths = visualize_comparison_result(
                    result,
                    output_dir=args.visualize,
                    plots=['all']
                )

                if plot_paths:
                    print("\n✓ Visualizations saved:")
                    for plot_type, path in plot_paths.items():
                        if path:
                            print(f"  - {plot_type}: {path}")
                else:
                    print("\nWarning: Failed to generate visualizations.", file=sys.stderr)
        except Exception as e:
            print(f"\nError generating visualizations: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()

    # Save result to history if requested
    if hasattr(args, 'save_result') and args.save_result:
        try:
            # Extract function name from the function path
            function_name = extract_function_name(args.function)

            # Get data size (use loaded data length)
            data_size = len(data) if hasattr(data, '__len__') else 0

            entry_id = save_result(result, args.save_result, function_name=function_name, data_size=data_size)
            print(f"\n✓ Result saved to history as '{args.save_result}' (ID: {entry_id})")
        except Exception as e:
            print(f"\nWarning: Failed to save result to history: {e}", file=sys.stderr)


def cmd_history_list(args: argparse.Namespace):
    """Execute the 'history list' command."""
    entries = list_results(name_filter=args.filter, limit=args.limit)

    if not entries:
        print("No history entries found.")
        return

    if args.json:
        # JSON output
        output = [
            {
                "id": entry.id,
                "name": entry.name,
                "timestamp": entry.timestamp,
                "function": entry.function_name,
                "data_size": entry.data_size,
                "best_strategy": entry.result.best_config.name,
                "system": entry.system_info
            }
            for entry in entries
        ]
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(f"Found {len(entries)} history entries:\n")
        print(f"{'ID':<14} {'Name':<25} {'Date':<20} {'Function':<30}")
        print("-" * 90)
        for entry in entries:
            # Format timestamp
            timestamp = entry.timestamp.replace('T', ' ').replace('Z', '')
            if '.' in timestamp:
                timestamp = timestamp.split('.')[0]  # Remove microseconds

            # Truncate long names
            name = entry.name[:24] if len(entry.name) > 24 else entry.name
            func_name = entry.function_name[:29] if len(entry.function_name) > 29 else entry.function_name

            print(f"{entry.id:<14} {name:<25} {timestamp:<20} {func_name:<30}")


def cmd_history_show(args: argparse.Namespace):
    """Execute the 'history show' command."""
    entry = load_result(args.id)

    if entry is None:
        print(f"Error: History entry '{args.id}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # JSON output
        print(json.dumps(entry.to_dict(), indent=2))
    else:
        # Human-readable output
        print("=" * 70)
        print(f"History Entry: {entry.name}")
        print("=" * 70)
        print(f"ID:        {entry.id}")
        print(f"Timestamp: {entry.timestamp}")
        print(f"Function:  {entry.function_name}")
        print(f"Data size: {entry.data_size}")
        print()

        print("System Information:")
        print(f"  Platform:       {entry.system_info.get('platform', 'N/A')}")
        print(f"  Physical cores: {entry.system_info.get('physical_cores', 'N/A')}")
        print(f"  Memory:         {entry.system_info.get('available_memory_gb', 'N/A'):.2f} GB")
        print(f"  Start method:   {entry.system_info.get('multiprocessing_start_method', 'N/A')}")
        print()

        print("Results:")
        print(f"  Best strategy:  {entry.result.best_config.name}")
        print(f"  Best time:      {entry.result.best_time:.4f}s")
        print(f"  Best speedup:   {entry.result.speedups[entry.result.best_config_index]:.2f}x")
        print()

        print(f"{'Strategy':<25} {'Workers':<10} {'Chunk':<10} {'Time (s)':<12} {'Speedup':<10}")
        print("-" * 70)
        for i, config in enumerate(entry.result.configs):
            print(f"{config.name:<25} {config.n_jobs:<10} {config.chunksize:<10} "
                  f"{entry.result.execution_times[i]:<12.4f} {entry.result.speedups[i]:<10.2f}x")


def cmd_history_compare(args: argparse.Namespace):
    """Execute the 'history compare' command."""
    comparison = compare_entries(args.id1, args.id2)

    if comparison is None:
        print("Error: One or both history entries not found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # JSON output
        print(json.dumps(comparison, indent=2))
    else:
        # Human-readable output
        e1 = comparison["entry1"]
        e2 = comparison["entry2"]
        comp = comparison["comparison"]

        print("=" * 70)
        print("History Comparison")
        print("=" * 70)

        print(f"\nEntry 1: {e1['name']} (ID: {e1['id']})")
        print(f"  Timestamp:     {e1['timestamp']}")
        print(f"  Best strategy: {e1['best_strategy']}")
        print(f"  Speedup:       {e1['speedup']:.2f}x")
        print(f"  Time:          {e1['execution_time']:.4f}s")

        print(f"\nEntry 2: {e2['name']} (ID: {e2['id']})")
        print(f"  Timestamp:     {e2['timestamp']}")
        print(f"  Best strategy: {e2['best_strategy']}")
        print(f"  Speedup:       {e2['speedup']:.2f}x")
        print(f"  Time:          {e2['execution_time']:.4f}s")

        print("\nComparison:")
        print(f"  Time delta:    {comp['time_delta_seconds']:+.4f}s ({comp['time_delta_percent']:+.1f}%)")
        print(f"  Speedup delta: {comp['speedup_delta']:+.2f}x")
        print(f"  Same system:   {'Yes' if comp['same_system'] else 'No'}")

        if comp['is_regression']:
            print("  ⚠ REGRESSION DETECTED: Entry 2 is slower than Entry 1")
        else:
            print("  ✓ Performance improved or stable")

        if not comp['same_system']:
            print("\n  Note: Results are from different systems. Direct comparison may not be meaningful.")


def cmd_history_delete(args: argparse.Namespace):
    """Execute the 'history delete' command."""
    if delete_result(args.id):
        print(f"✓ Deleted history entry '{args.id}'")
    else:
        print(f"Error: History entry '{args.id}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_history_clear(args: argparse.Namespace):
    """Execute the 'history clear' command."""
    if not args.yes:
        # Ask for confirmation
        response = input("Are you sure you want to delete ALL history entries? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return

    count = clear_history()
    print(f"✓ Deleted {count} history entries")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="amorsize",
        description="Dynamic Parallelism Optimizer & Overhead Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate system health and measurements
  python -m amorsize validate
  
  # Analyze optimal parameters for a function
  python -m amorsize optimize math.sqrt --data-range 1000
  
  # Execute with optimization
  python -m amorsize execute mymodule.process_item --data-file input.txt
  
  # Compare multiple strategies
  python -m amorsize compare math.factorial --data-range 100 --configs "2,50" "4,25" "8,10"
  
  # Compare with optimizer recommendation
  python -m amorsize compare mymodule.func --data-range 500 --include-optimizer --configs "4,20"
  
  # Get detailed profiling
  python -m amorsize optimize math.factorial --data-range 100 --profile
  
  # Show user-friendly explanation with tips
  python -m amorsize optimize math.sqrt --data-range 1000 --explain --tips
  
  # Show overhead breakdown
  python -m amorsize optimize mymodule.func --data-range 100 --show-overhead
  
  # Quiet mode (just the recommendation)
  python -m amorsize optimize math.sqrt --data-range 1000 --quiet
  
  # Output as JSON for scripting
  python -m amorsize optimize math.sqrt --data-range 1000 --json
  
  # Read data from stdin
  cat data.txt | python -m amorsize execute mymodule:process --data-stdin
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # ===== VALIDATE SUBCOMMAND =====
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate system health and measurement accuracy'
    )
    validate_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    validate_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output with progress information'
    )

    # Shared arguments for both commands
    parent_parser = argparse.ArgumentParser(add_help=False)

    parent_parser.add_argument(
        'function',
        help='Function to analyze/execute (format: module.function or module:function)'
    )

    # Data source (mutually exclusive)
    data_group = parent_parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument(
        '--data-range',
        type=int,
        metavar='N',
        help='Use range(N) as data source'
    )
    data_group.add_argument(
        '--data-file',
        metavar='FILE',
        help='Read data from file (one item per line)'
    )
    data_group.add_argument(
        '--data-stdin',
        action='store_true',
        help='Read data from stdin (one item per line)'
    )

    # Optimization parameters
    parent_parser.add_argument(
        '--sample-size',
        type=int,
        default=5,
        metavar='N',
        help='Number of items to sample (default: 5)'
    )
    parent_parser.add_argument(
        '--target-chunk-duration',
        type=float,
        default=0.2,
        metavar='SECONDS',
        help='Target duration per chunk in seconds (default: 0.2)'
    )

    # Output options
    parent_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parent_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parent_parser.add_argument(
        '--profile',
        '-p',
        action='store_true',
        help='Show detailed diagnostic profile (technical details)'
    )
    parent_parser.add_argument(
        '--explain',
        action='store_true',
        help='Show user-friendly explanation of optimization decisions'
    )
    parent_parser.add_argument(
        '--tips',
        action='store_true',
        help='Show actionable optimization tips and recommendations'
    )
    parent_parser.add_argument(
        '--show-overhead',
        action='store_true',
        help='Show detailed overhead breakdown (spawn, IPC, chunking)'
    )
    parent_parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Minimal output (just the recommendation)'
    )
    parent_parser.add_argument(
        '--color',
        action='store_true',
        help='Force colored output even if not a TTY'
    )
    parent_parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    # Benchmarking options
    parent_parser.add_argument(
        '--no-spawn-benchmark',
        action='store_true',
        help='Disable spawn cost benchmarking (use estimate)'
    )
    parent_parser.add_argument(
        '--no-chunking-benchmark',
        action='store_true',
        help='Disable chunking overhead benchmarking (use estimate)'
    )
    parent_parser.add_argument(
        '--no-auto-adjust',
        action='store_true',
        help='Disable automatic n_jobs adjustment for nested parallelism'
    )

    # Optimize subcommand
    optimize_parser = subparsers.add_parser(
        'optimize',
        parents=[parent_parser],
        help='Analyze function and recommend optimal parameters'
    )
    optimize_parser.add_argument(
        '--save-config',
        metavar='FILE',
        help='Save optimization result as reusable configuration file (JSON/YAML)'
    )

    # Execute subcommand
    execute_parser = subparsers.add_parser(
        'execute',
        parents=[parent_parser],
        help='Optimize and execute function on data'
    )
    execute_parser.add_argument(
        '--load-config',
        metavar='FILE',
        help='Load configuration from file and use those parameters (skips optimization)'
    )

    # ===== COMPARE SUBCOMMAND =====
    compare_parser = subparsers.add_parser(
        'compare',
        help='Compare multiple parallelization strategies'
    )

    compare_parser.add_argument(
        'function',
        help='Function to analyze (format: module.function or module:function)'
    )

    # Data source (mutually exclusive)
    compare_data_group = compare_parser.add_mutually_exclusive_group(required=True)
    compare_data_group.add_argument(
        '--data-range',
        type=int,
        metavar='N',
        help='Use range(N) as data source'
    )
    compare_data_group.add_argument(
        '--data-file',
        metavar='FILE',
        help='Read data from file (one item per line)'
    )
    compare_data_group.add_argument(
        '--data-stdin',
        action='store_true',
        help='Read data from stdin (one item per line)'
    )

    # Strategy configurations
    compare_parser.add_argument(
        '--configs',
        nargs='+',
        metavar='CONFIG',
        help='Strategy configs to compare (format: "n_jobs,chunksize" or "name:n_jobs,chunksize,executor")'
    )
    compare_parser.add_argument(
        '--include-optimizer',
        action='store_true',
        help='Include optimizer recommendation in comparison'
    )
    compare_parser.add_argument(
        '--no-baseline',
        action='store_true',
        help='Skip serial baseline (first config is used as baseline)'
    )

    # Comparison parameters
    compare_parser.add_argument(
        '--max-items',
        type=int,
        metavar='N',
        help='Limit benchmark to first N items (for large datasets)'
    )
    compare_parser.add_argument(
        '--timeout',
        type=float,
        default=120.0,
        metavar='SECONDS',
        help='Maximum time per benchmark in seconds (default: 120)'
    )

    # Optimization parameters (for --include-optimizer)
    compare_parser.add_argument(
        '--sample-size',
        type=int,
        default=5,
        metavar='N',
        help='Number of items to sample for optimizer (default: 5)'
    )
    compare_parser.add_argument(
        '--target-chunk-duration',
        type=float,
        default=0.2,
        metavar='SECONDS',
        help='Target duration per chunk for optimizer (default: 0.2)'
    )

    # Benchmarking options (for --include-optimizer)
    compare_parser.add_argument(
        '--no-spawn-benchmark',
        action='store_true',
        help='Disable spawn cost benchmarking (use estimate)'
    )
    compare_parser.add_argument(
        '--no-chunking-benchmark',
        action='store_true',
        help='Disable chunking overhead benchmarking (use estimate)'
    )
    compare_parser.add_argument(
        '--no-auto-adjust',
        action='store_true',
        help='Disable automatic n_jobs adjustment for nested parallelism'
    )

    # Output options
    compare_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    compare_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    compare_parser.add_argument(
        '--visualize',
        metavar='DIR',
        help='Generate visualization plots and save to directory (requires matplotlib)'
    )
    compare_parser.add_argument(
        '--save-result',
        metavar='NAME',
        help='Save comparison result to history with given name'
    )

    # ===== TUNE SUBCOMMAND =====
    tune_parser = subparsers.add_parser(
        'tune',
        help='Auto-tune parameters through empirical benchmarking',
        description='Automatically find optimal n_jobs and chunksize by benchmarking multiple configurations'
    )

    tune_parser.add_argument(
        'function',
        help='Function to tune (format: module.function or module:function)'
    )

    # Data source (mutually exclusive)
    tune_data_group = tune_parser.add_mutually_exclusive_group(required=True)
    tune_data_group.add_argument(
        '--data-range',
        type=int,
        metavar='N',
        help='Use range(N) as data source'
    )
    tune_data_group.add_argument(
        '--data-file',
        metavar='FILE',
        help='Read data from file (one item per line)'
    )
    tune_data_group.add_argument(
        '--data-stdin',
        action='store_true',
        help='Read data from stdin (one item per line)'
    )

    # Tuning strategy
    tune_parser.add_argument(
        '--quick',
        action='store_true',
        help='Use quick tuning with minimal search space (faster but less thorough)'
    )

    # Search space customization
    tune_parser.add_argument(
        '--n-jobs-range',
        nargs='+',
        type=int,
        metavar='N',
        help='List of n_jobs values to test (e.g., --n-jobs-range 1 2 4 8)'
    )
    tune_parser.add_argument(
        '--chunksize-range',
        nargs='+',
        type=int,
        metavar='N',
        help='List of chunksize values to test (e.g., --chunksize-range 10 50 100)'
    )

    # Options
    tune_parser.add_argument(
        '--no-optimizer-hint',
        action='store_true',
        help='Disable inclusion of optimizer hint in search space'
    )
    tune_parser.add_argument(
        '--threads',
        action='store_true',
        help='Use ThreadPoolExecutor instead of multiprocessing.Pool'
    )
    tune_parser.add_argument(
        '--timeout-per-config',
        type=float,
        metavar='SECONDS',
        help='Maximum time per configuration in seconds'
    )

    # Output options
    tune_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    tune_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output with progress information'
    )
    tune_parser.add_argument(
        '--save-result',
        metavar='NAME',
        help='Save tuning result to history with given name'
    )
    tune_parser.add_argument(
        '--save-config',
        metavar='FILE',
        help='Save best tuning result as reusable configuration file (JSON/YAML)'
    )

    # ===== HISTORY SUBCOMMAND =====
    history_parser = subparsers.add_parser(
        'history',
        help='Manage historical comparison results'
    )

    history_subparsers = history_parser.add_subparsers(dest='history_command', help='History command to execute')

    # history list
    history_list_parser = history_subparsers.add_parser(
        'list',
        help='List all saved results'
    )
    history_list_parser.add_argument(
        '--filter',
        metavar='NAME',
        help='Filter results by name (case-insensitive substring match)'
    )
    history_list_parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit number of results shown'
    )
    history_list_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    # history show
    history_show_parser = history_subparsers.add_parser(
        'show',
        help='Show details of a specific result'
    )
    history_show_parser.add_argument(
        'id',
        help='ID of the history entry to show'
    )
    history_show_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    # history compare
    history_compare_parser = history_subparsers.add_parser(
        'compare',
        help='Compare two historical results'
    )
    history_compare_parser.add_argument(
        'id1',
        help='ID of first history entry'
    )
    history_compare_parser.add_argument(
        'id2',
        help='ID of second history entry'
    )
    history_compare_parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    # history delete
    history_delete_parser = history_subparsers.add_parser(
        'delete',
        help='Delete a specific result'
    )
    history_delete_parser.add_argument(
        'id',
        help='ID of the history entry to delete'
    )

    # history clear
    history_clear_parser = history_subparsers.add_parser(
        'clear',
        help='Delete all history entries'
    )
    history_clear_parser.add_argument(
        '--yes',
        '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )

    return parser


def main():
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Check if command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Execute command
        if args.command == 'validate':
            cmd_validate(args)
        elif args.command == 'optimize':
            cmd_optimize(args)
        elif args.command == 'execute':
            cmd_execute(args)
        elif args.command == 'compare':
            cmd_compare(args)
        elif args.command == 'tune':
            cmd_tune(args)
        elif args.command == 'history':
            # Check history subcommand
            if not hasattr(args, 'history_command') or not args.history_command:
                print("Error: History subcommand required. Use 'list', 'show', 'compare', 'delete', or 'clear'.", file=sys.stderr)
                sys.exit(1)

            if args.history_command == 'list':
                cmd_history_list(args)
            elif args.history_command == 'show':
                cmd_history_show(args)
            elif args.history_command == 'compare':
                cmd_history_compare(args)
            elif args.history_command == 'delete':
                cmd_history_delete(args)
            elif args.history_command == 'clear':
                cmd_history_clear(args)
            else:
                print(f"Error: Unknown history subcommand: {args.history_command}", file=sys.stderr)
                sys.exit(1)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

