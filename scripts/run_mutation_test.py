#!/usr/bin/env python
"""Quick mutation testing script for local development."""

import argparse
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

def main():
    parser = argparse.ArgumentParser(description='Run mutation testing')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--module', '-m', choices=list(MODULES.keys()))
    group.add_argument('--file', '-f', type=str)
    group.add_argument('--all', '-a', action='store_true')
    parser.add_argument('--quick', '-q', action='store_true')
    parser.add_argument('--max-mutations', type=int)
    
    args = parser.parse_args()
    
    if args.module:
        paths = MODULES[args.module]
    elif args.file:
        paths = args.file
    elif args.all:
        paths = ','.join(MODULES[m] for m in CORE_MODULES)
    
    max_mutations = args.max_mutations or (50 if args.quick else None)
    
    cmd = ['mutmut', 'run', '--paths-to-mutate', paths, '--tests-dir', 'tests/']
    if max_mutations:
        cmd.extend(['--max-mutations', str(max_mutations)])
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    # Show results even if some mutations survived
    print("\n" + "="*60)
    subprocess.run(['mutmut', 'results'])
    print("="*60)
    
    # Return 0 even if mutations survived (not a failure)
    return 0

if __name__ == '__main__':
    sys.exit(main())
