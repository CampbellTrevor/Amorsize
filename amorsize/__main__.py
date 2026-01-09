"""
Command-line interface for Amorsize.

Enables running Amorsize from the command line:
    python -m amorsize optimize module.function --data-range 100
    python -m amorsize execute module.function --data-file input.txt
"""

import argparse
import importlib
import json
import sys
from typing import Any, Callable, List, Optional

from . import optimize, execute, validate_system, __version__
from .comparison import compare_strategies, compare_with_optimizer, ComparisonConfig
from .history import (
    save_result, load_result, list_results, delete_result,
    compare_entries, clear_history
)


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


def format_output_human(result, mode: str, show_profile: bool = False):
    """
    Format optimization result in human-readable form.
    
    Args:
        result: OptimizationResult or (results, OptimizationResult) tuple
        mode: "optimize" or "execute"
        show_profile: Whether to show detailed profile
    """
    # Handle execute mode with tuple result
    if mode == "execute" and isinstance(result, tuple):
        results, opt_result = result
        print(f"\n{'='*70}")
        print("EXECUTION COMPLETE")
        print(f"{'='*70}")
        print(f"Processed {len(results)} items")
        print(f"Sample results (first 5): {results[:5]}")
        result = opt_result
        print(f"\n{'='*70}")
        print("OPTIMIZATION DETAILS")
        print(f"{'='*70}")
    else:
        print(f"\n{'='*70}")
        print("OPTIMIZATION ANALYSIS")
        print(f"{'='*70}")
    
    # Show basic results
    print(f"\nRecommendation:")
    print(f"  n_jobs:            {result.n_jobs}")
    print(f"  chunksize:         {result.chunksize}")
    print(f"  estimated_speedup: {result.estimated_speedup:.2f}x")
    print(f"\nReason:")
    print(f"  {result.reason}")
    
    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
    
    # Show detailed profile if requested
    if show_profile and result.profile:
        print(f"\n{'='*70}")
        print("DETAILED DIAGNOSTIC PROFILE")
        print(f"{'='*70}")
        print(result.explain())


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


def cmd_optimize(args: argparse.Namespace):
    """Execute the 'optimize' command."""
    # Load function
    func = load_function(args.function)
    
    # Load data
    data = load_data(args)
    
    # Run optimization
    result = optimize(
        func,
        data,
        sample_size=args.sample_size,
        target_chunk_duration=args.target_chunk_duration,
        verbose=args.verbose,
        profile=args.profile,
        use_spawn_benchmark=not args.no_spawn_benchmark,
        use_chunking_benchmark=not args.no_chunking_benchmark,
        auto_adjust_for_nested_parallelism=not args.no_auto_adjust
    )
    
    # Format and display output
    if args.json:
        format_output_json(result, "optimize")
    else:
        format_output_human(result, "optimize", show_profile=args.profile)


def cmd_execute(args: argparse.Namespace):
    """Execute the 'execute' command."""
    # Load function
    func = load_function(args.function)
    
    # Load data
    data = load_data(args)
    
    # Run execution
    result = execute(
        func,
        data,
        sample_size=args.sample_size,
        target_chunk_duration=args.target_chunk_duration,
        verbose=args.verbose,
        profile=args.profile,
        use_spawn_benchmark=not args.no_spawn_benchmark,
        use_chunking_benchmark=not args.no_chunking_benchmark,
        auto_adjust_for_nested_parallelism=not args.no_auto_adjust,
        return_optimization_result=True  # Always get both for CLI
    )
    
    # Format and display output
    if args.json:
        format_output_json(result, "execute")
    else:
        format_output_human(result, "execute", show_profile=args.profile)


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
            from .visualization import visualize_comparison_result, check_matplotlib
            
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
                    print(f"\n✓ Visualizations saved:")
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
            function_name = args.function.split('.')[-1] if '.' in args.function else args.function.split(':')[-1] if ':' in args.function else args.function
            
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
        print(f"Error: One or both history entries not found.", file=sys.stderr)
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
            print(f"  ⚠ REGRESSION DETECTED: Entry 2 is slower than Entry 1")
        else:
            print(f"  ✓ Performance improved or stable")
        
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
        help='Show detailed diagnostic profile'
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
    
    # Execute subcommand
    execute_parser = subparsers.add_parser(
        'execute',
        parents=[parent_parser],
        help='Optimize and execute function on data'
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

