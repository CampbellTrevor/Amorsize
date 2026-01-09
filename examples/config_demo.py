"""
Configuration Export/Import Demo

This script demonstrates how to save and load optimal parallelization
configurations for reuse and sharing.
"""

import tempfile
from pathlib import Path


def expensive_cpu_func(x):
    """CPU-intensive function for testing."""
    return sum(i**2 for i in range(x))


def demo_1_basic_save_load():
    """Demo 1: Basic configuration save and load."""
    print("\n" + "="*70)
    print("DEMO 1: Basic Configuration Save and Load")
    print("="*70)
    
    from amorsize import optimize, load_config
    
    # Optimize and save configuration
    print("\n1. Optimizing function...")
    result = optimize(expensive_cpu_func, range(100, 200))
    print(f"   Optimal: n_jobs={result.n_jobs}, chunksize={result.chunksize}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'demo_config.json'
        
        print(f"\n2. Saving configuration to {config_path.name}...")
        result.save_config(
            config_path,
            function_name='expensive_cpu_func',
            notes='Demo configuration for CPU-intensive work'
        )
        
        print(f"\n3. Loading configuration...")
        config = load_config(config_path)
        print(config)
        
        print(f"\n4. Configuration can now be used:")
        print(f"   with Pool({config.n_jobs}) as pool:")
        print(f"       results = pool.map(func, data, chunksize={config.chunksize})")


def demo_2_tuning_save():
    """Demo 2: Save configuration from auto-tuning."""
    print("\n" + "="*70)
    print("DEMO 2: Save Configuration from Auto-Tuning")
    print("="*70)
    
    from amorsize import quick_tune
    
    print("\n1. Running quick tuning...")
    result = quick_tune(expensive_cpu_func, range(50, 150))
    
    print(f"\n2. Best configuration found:")
    print(f"   n_jobs:     {result.best_n_jobs}")
    print(f"   chunksize:  {result.best_chunksize}")
    print(f"   speedup:    {result.best_speedup:.2f}x")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'tuned_config.json'
        
        print(f"\n3. Saving tuned configuration...")
        result.save_config(
            config_path,
            function_name='expensive_cpu_func',
            notes='Empirically tuned configuration - tested multiple configs'
        )
        print(f"   Saved to {config_path.name}")


def demo_3_cli_workflow():
    """Demo 3: CLI workflow for config management."""
    print("\n" + "="*70)
    print("DEMO 3: CLI Workflow (commands to try)")
    print("="*70)
    
    print("""
1. Save configuration from optimization:
   
   python -m amorsize optimize mymodule.func --data-range 1000 \\
       --save-config production_config.json

2. Save configuration from tuning:
   
   python -m amorsize tune mymodule.func --data-range 1000 \\
       --quick \\
       --save-config tuned_config.json

3. Execute with saved configuration (fast - skips optimization):
   
   python -m amorsize execute mymodule.func --data-range 5000 \\
       --load-config production_config.json

Benefits:
- Much faster execution (no optimization overhead)
- Consistent parameters across runs
- Easy to share configurations with team
    """)


def demo_4_manual_config():
    """Demo 4: Create and use manual configuration."""
    print("\n" + "="*70)
    print("DEMO 4: Manual Configuration Creation")
    print("="*70)
    
    from amorsize import ConfigData, save_config, load_config
    
    print("\n1. Creating manual configuration...")
    config = ConfigData(
        n_jobs=4,
        chunksize=100,
        executor_type='process',
        estimated_speedup=3.5,
        function_name='batch_processor',
        data_size=10000,
        notes='Hand-tuned configuration for production deployment'
    )
    
    print(config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'manual_config.json'
        
        print(f"\n2. Saving manual configuration...")
        save_config(config, config_path)
        
        print(f"\n3. Configuration saved and can be loaded later:")
        print(f"   config = load_config('{config_path.name}')")


def demo_5_execute_with_config():
    """Demo 5: Actually execute function with loaded configuration."""
    print("\n" + "="*70)
    print("DEMO 5: Execute Function with Loaded Configuration")
    print("="*70)
    
    from amorsize import optimize, load_config
    from multiprocessing import Pool
    
    # First, optimize and save
    print("\n1. Optimizing and saving configuration...")
    result = optimize(expensive_cpu_func, range(100, 200))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'exec_config.json'
        result.save_config(config_path, function_name='expensive_cpu_func')
        
        # Now load and execute
        print(f"\n2. Loading configuration from {config_path.name}...")
        config = load_config(config_path)
        
        print(f"\n3. Executing function with loaded config...")
        print(f"   Using n_jobs={config.n_jobs}, chunksize={config.chunksize}")
        
        data = range(100, 120)  # Small dataset for demo
        
        with Pool(config.n_jobs) as pool:
            results = pool.map(expensive_cpu_func, data, chunksize=config.chunksize)
        
        print(f"\n4. Execution complete!")
        print(f"   Processed {len(results)} items")
        print(f"   Sample results: {results[:5]}")


def demo_6_config_comparison():
    """Demo 6: Compare multiple configurations."""
    print("\n" + "="*70)
    print("DEMO 6: Compare Multiple Configurations")
    print("="*70)
    
    from amorsize import ConfigData, save_config, load_config, list_configs
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create several configurations
        print("\n1. Creating multiple configurations...")
        
        configs_to_create = [
            (2, 50, 'Small system - 2 cores'),
            (4, 100, 'Medium system - 4 cores'),
            (8, 200, 'Large system - 8 cores'),
        ]
        
        for i, (n_jobs, chunksize, notes) in enumerate(configs_to_create, 1):
            config = ConfigData(
                n_jobs=n_jobs,
                chunksize=chunksize,
                notes=notes
            )
            save_config(config, tmpdir / f'config_{i}.json')
        
        # List all configurations
        print(f"\n2. Listing all configurations in directory...")
        configs = list_configs(tmpdir)
        
        print(f"\n   Found {len(configs)} configurations:")
        for config_path in configs:
            config = load_config(config_path)
            print(f"\n   {config_path.name}:")
            print(f"     n_jobs:    {config.n_jobs}")
            print(f"     chunksize: {config.chunksize}")
            print(f"     notes:     {config.notes}")


def demo_7_config_metadata():
    """Demo 7: Examine configuration metadata."""
    print("\n" + "="*70)
    print("DEMO 7: Configuration Metadata")
    print("="*70)
    
    from amorsize import optimize, load_config
    
    print("\n1. Creating configuration with full metadata...")
    result = optimize(expensive_cpu_func, range(100, 200), profile=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'metadata_config.json'
        result.save_config(
            config_path,
            function_name='expensive_cpu_func',
            notes='Configuration with full system metadata'
        )
        
        print(f"\n2. Loading and examining metadata...")
        config = load_config(config_path)
        
        print(f"\n   Configuration Details:")
        print(f"   - Function:       {config.function_name}")
        print(f"   - Source:         {config.source}")
        print(f"   - Created:        {config.timestamp}")
        print(f"   - Version:        {config.to_dict().get('amorsize_version')}")
        
        if config.system_info:
            print(f"\n   System Information:")
            print(f"   - Platform:       {config.system_info.get('platform')}")
            print(f"   - Python:         {config.system_info.get('python_version')}")
            print(f"   - Physical cores: {config.system_info.get('physical_cores')}")
            print(f"   - Start method:   {config.system_info.get('start_method')}")
        
        print(f"\n   Notes: {config.notes}")


def demo_8_yaml_format():
    """Demo 8: Using YAML format for configurations."""
    print("\n" + "="*70)
    print("DEMO 8: YAML Format (requires PyYAML)")
    print("="*70)
    
    try:
        import yaml
    except ImportError:
        print("\nPyYAML not installed. Install with: pip install pyyaml")
        print("Skipping YAML demo.")
        return
    
    from amorsize import ConfigData, save_config, load_config
    
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_path = Path(tmpdir) / 'config.yaml'
        
        print("\n1. Creating configuration...")
        config = ConfigData(
            n_jobs=4,
            chunksize=100,
            notes='YAML format configuration'
        )
        
        print(f"\n2. Saving as YAML...")
        save_config(config, yaml_path, format='yaml')
        
        print(f"\n3. YAML content:")
        print(yaml_path.read_text())
        
        print(f"\n4. Loading from YAML...")
        loaded = load_config(yaml_path)
        print(f"   n_jobs={loaded.n_jobs}, chunksize={loaded.chunksize}")


def demo_9_default_config_dir():
    """Demo 9: Using default configuration directory."""
    print("\n" + "="*70)
    print("DEMO 9: Default Configuration Directory")
    print("="*70)
    
    from amorsize import get_default_config_dir, ConfigData, save_config, list_configs
    
    config_dir = get_default_config_dir()
    print(f"\n1. Default configuration directory:")
    print(f"   {config_dir}")
    
    print(f"\n2. This directory is automatically created and can be used to")
    print(f"   store configurations persistently across runs.")
    
    print(f"\n3. Example usage:")
    print(f"   config = ConfigData(n_jobs=4, chunksize=100)")
    print(f"   save_config(config, config_dir / 'my_app.json')")
    print(f"   ...")
    print(f"   # Later, in another script:")
    print(f"   config = load_config(config_dir / 'my_app.json')")


def demo_10_error_handling():
    """Demo 10: Error handling and validation."""
    print("\n" + "="*70)
    print("DEMO 10: Error Handling")
    print("="*70)
    
    from amorsize import load_config, save_config, ConfigData
    
    print("\n1. Handling missing files:")
    try:
        config = load_config('/nonexistent/config.json')
    except FileNotFoundError as e:
        print(f"   ✓ Caught FileNotFoundError: {type(e).__name__}")
    
    print("\n2. Preventing accidental overwrites:")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.json'
        config = ConfigData(n_jobs=4, chunksize=100)
        
        # First save succeeds
        save_config(config, config_path)
        print(f"   ✓ First save successful")
        
        # Second save without overwrite fails
        try:
            save_config(config, config_path, overwrite=False)
        except FileExistsError:
            print(f"   ✓ Caught FileExistsError (overwrite protection)")
        
        # Second save with overwrite succeeds
        save_config(config, config_path, overwrite=True)
        print(f"   ✓ Save with overwrite=True successful")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("AMORSIZE CONFIGURATION EXPORT/IMPORT DEMOS")
    print("="*70)
    print("\nThese demos show how to save and reuse optimal configurations")
    print("for parallelization parameters.")
    
    demos = [
        demo_1_basic_save_load,
        demo_2_tuning_save,
        demo_3_cli_workflow,
        demo_4_manual_config,
        demo_5_execute_with_config,
        demo_6_config_comparison,
        demo_7_config_metadata,
        demo_8_yaml_format,
        demo_9_default_config_dir,
        demo_10_error_handling,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n✗ Demo failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("All demos complete!")
    print("="*70)
    print("\nKey takeaways:")
    print("- Save configurations with result.save_config()")
    print("- Load configurations with load_config()")
    print("- Use --save-config and --load-config in CLI")
    print("- Configurations include full metadata and system info")
    print("- Share configurations across team members and environments")


if __name__ == '__main__':
    main()
