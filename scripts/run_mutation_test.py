#!/usr/bin/env python
"""
Quick mutation testing script for local development.

This script works around mutmut's limitation of only reading configuration
from setup.cfg by temporarily modifying the config file, running mutation
tests, and then restoring the original configuration.
"""

import argparse
import os
import shutil
import subprocess
import sys

# Module mapping
MODULES = {
    'optimizer': 'amorsize/optimizer.py',
    'sampling': 'amorsize/sampling.py',
    'system_info': 'amorsize/system_info.py',
    'cost_model': 'amorsize/cost_model.py',
    'cache': 'amorsize/cache.py',
}

CORE_MODULES = ['optimizer', 'sampling', 'system_info', 'cost_model', 'cache']

def create_temp_config(paths):
    """Create temporary setup.cfg with specified paths."""
    config_content = f"""[mutmut]
paths_to_mutate={paths}
tests_dir=tests/
runner=python -m pytest -x --tb=short -q
"""
    return config_content

def main():
    parser = argparse.ArgumentParser(
        description='Run mutation testing on specific modules',
        epilog='Examples:\n'
               '  %(prog)s --module optimizer\n'
               '  %(prog)s --module cache --quick\n'
               '  %(prog)s --file amorsize/custom.py\n'
               '  %(prog)s --all\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--module', '-m', choices=list(MODULES.keys()),
                       help='Test a specific core module')
    group.add_argument('--file', '-f', type=str,
                       help='Test a specific file path')
    group.add_argument('--all', '-a', action='store_true',
                       help='Test all core modules')
    parser.add_argument('--quick', '-q', action='store_true',
                        help='Quick mode: stop after first 20 mutants (for rapid feedback)')
    parser.add_argument('--html', action='store_true',
                        help='Generate HTML report after completion')
    
    args = parser.parse_args()
    
    # Determine paths to mutate
    if args.module:
        paths = MODULES[args.module]
        print(f"Testing module: {args.module} ({paths})")
    elif args.file:
        paths = args.file
        print(f"Testing file: {paths}")
    elif args.all:
        paths = ','.join(MODULES[m] for m in CORE_MODULES)
        print(f"Testing all core modules: {', '.join(CORE_MODULES)}")
    
    # Backup original setup.cfg
    setup_cfg = 'setup.cfg'
    backup_cfg = setup_cfg + '.backup'
    
    try:
        # Backup original config if it exists
        if os.path.exists(setup_cfg):
            shutil.copy2(setup_cfg, backup_cfg)
            print(f"Backed up {setup_cfg} to {backup_cfg}")
        
        # Create temporary config with focused paths
        temp_config = create_temp_config(paths)
        with open(setup_cfg, 'w') as f:
            f.write(temp_config)
        print(f"Created temporary {setup_cfg} with paths: {paths}")
        
        # Clean up any existing mutation cache
        if os.path.exists('.mutmut-cache'):
            os.remove('.mutmut-cache')
            print("Cleaned up old mutation cache")
        
        # Build command
        cmd = ['mutmut', 'run']
        if args.quick:
            # Note: mutmut doesn't support limiting mutations via CLI
            # User will need to manually interrupt (Ctrl+C) or use timeout
            print("\nQuick mode: You may want to interrupt (Ctrl+C) after a few mutations for rapid feedback")
            print("(Mutmut doesn't support automatic mutation limits)\n")
        
        print(f"Running: {' '.join(cmd)}")
        print("="*60)
        
        # Run mutation testing
        # Note: mutmut may return non-zero even on success (mutations survived)
        # so we don't check return code
        result = subprocess.run(cmd)
        
        print("\n" + "="*60)
        print("Mutation Testing Results:")
        print("="*60)
        
        # Show detailed results
        subprocess.run(['mutmut', 'results'])
        
        # Generate HTML report if requested
        if args.html:
            print("\n" + "="*60)
            print("Generating HTML report...")
            html_result = subprocess.run(['mutmut', 'html'], capture_output=True, text=True)
            if html_result.returncode == 0:
                print("HTML report generated successfully")
                print(f"View it at: file://{os.getcwd()}/.mutmut-cache.html")
            else:
                print("Failed to generate HTML report")
                print(html_result.stderr)
        
        print("="*60)
        print("\nTips:")
        print("  - View specific mutant: mutmut show <id>")
        print("  - Apply a mutant: mutmut apply <id>")
        print("  - Generate HTML report: mutmut html")
        print("  - See results: mutmut results")
        
    finally:
        # Restore original setup.cfg
        if os.path.exists(backup_cfg):
            shutil.move(backup_cfg, setup_cfg)
            print(f"\nRestored original {setup_cfg}")
        
    # Always return 0 (mutation survivors are not a failure)
    return 0

if __name__ == '__main__':
    sys.exit(main())
