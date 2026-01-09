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
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

