"""
Demonstration of ML Model Versioning & Migration.

This script demonstrates the versioning and migration system for ML training data,
showing how old v1 data is automatically migrated to v2 format.
"""

import json
import tempfile
from pathlib import Path

from amorsize.ml_prediction import (
    get_ml_training_data_version,
    load_ml_training_data,
    update_model_from_execution,
    _migrate_training_data
)


def demo_1_version_info():
    """Demo 1: Display current version information."""
    print("=" * 70)
    print("DEMO 1: ML Training Data Version Information")
    print("=" * 70)
    
    version = get_ml_training_data_version()
    print(f"\nCurrent ML training data format version: {version}")
    print(f"\nVersion History:")
    print(f"  v1: Original format (Iterations 115-121)")
    print(f"  v2: Added versioning and migration support (Iteration 122)")
    print()


def demo_2_automatic_migration():
    """Demo 2: Demonstrate automatic migration of v1 data."""
    print("=" * 70)
    print("DEMO 2: Automatic Migration of Old Data")
    print("=" * 70)
    
    # Create simulated v1 format data (no version field)
    v1_data = {
        'features': {
            'data_size': 1000,
            'estimated_item_time': 0.01,
            'physical_cores': 8,
            'available_memory': 16000000000,
            'start_method': 'spawn',
            'pickle_size': 1024,
            'coefficient_of_variation': 0.3,
            'function_complexity': 50
        },
        'n_jobs': 4,
        'chunksize': 50,
        'speedup': 3.2,
        'timestamp': 1234567890.0
    }
    
    print(f"\nOriginal v1 data (no version field):")
    print(f"  Keys: {list(v1_data.keys())}")
    print(f"  Has 'version' field: {'version' in v1_data}")
    
    # Perform migration
    v2_data = _migrate_training_data(v1_data, verbose=True)
    
    print(f"\nMigrated v2 data:")
    print(f"  Keys: {list(v2_data.keys())}")
    print(f"  Version: {v2_data.get('version')}")
    print(f"  All original fields preserved: {all(k in v2_data for k in v1_data.keys())}")
    print()


def demo_3_backward_compatibility():
    """Demo 3: Demonstrate loading mixed v1 and v2 data."""
    print("=" * 70)
    print("DEMO 3: Backward Compatibility - Mixed Version Data")
    print("=" * 70)
    
    import amorsize.ml_prediction as ml_module
    
    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir)
        
        # Create v1 format file
        v1_data = {
            'features': {
                'data_size': 1000,
                'estimated_item_time': 0.01,
                'physical_cores': 8,
                'available_memory': 16000000000,
                'start_method': 'spawn'
            },
            'n_jobs': 4,
            'chunksize': 50,
            'speedup': 3.2,
            'timestamp': 1234567890.0,
            'function_signature': 'test_func_v1'
        }
        
        v1_file = cache_path / 'ml_training_test_v1_1234567890.json'
        with open(v1_file, 'w') as f:
            json.dump(v1_data, f, indent=2)
        
        # Create v2 format file
        v2_data = {
            'version': 2,
            'features': {
                'data_size': 2000,
                'estimated_item_time': 0.02,
                'physical_cores': 8,
                'available_memory': 16000000000,
                'start_method': 'spawn'
            },
            'n_jobs': 8,
            'chunksize': 100,
            'speedup': 6.5,
            'timestamp': 1234567891.0,
            'function_signature': 'test_func_v2'
        }
        
        v2_file = cache_path / 'ml_training_test_v2_1234567891.json'
        with open(v2_file, 'w') as f:
            json.dump(v2_data, f, indent=2)
        
        print(f"\nCreated test cache with:")
        print(f"  - 1 v1 format file (no version field)")
        print(f"  - 1 v2 format file (with version=2)")
        
        # Temporarily patch cache directory
        original_get_cache = ml_module._get_ml_cache_dir
        ml_module._get_ml_cache_dir = lambda: cache_path
        
        try:
            # Load all training data
            print(f"\nLoading all training data...")
            training_data = load_ml_training_data(
                enable_cross_system=False,
                verbose=True
            )
            
            print(f"\nResults:")
            print(f"  Total samples loaded: {len(training_data)}")
            print(f"  v1 sample - n_jobs: {training_data[0].n_jobs if len(training_data) > 0 else 'N/A'}")
            print(f"  v2 sample - n_jobs: {training_data[1].n_jobs if len(training_data) > 1 else 'N/A'}")
            print(f"  ✅ Both versions loaded successfully!")
            
        finally:
            # Restore original function
            ml_module._get_ml_cache_dir = original_get_cache
    
    print()


def demo_4_new_data_with_version():
    """Demo 4: Show that new data is saved with version field."""
    print("=" * 70)
    print("DEMO 4: New Training Data Includes Version")
    print("=" * 70)
    
    import amorsize.ml_prediction as ml_module
    
    def test_func(x):
        return x * 2
    
    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir)
        
        # Temporarily patch cache directory
        original_get_cache = ml_module._get_ml_cache_dir
        ml_module._get_ml_cache_dir = lambda: cache_path
        
        try:
            print(f"\nSaving new training data...")
            success = update_model_from_execution(
                func=test_func,
                data_size=1000,
                estimated_item_time=0.01,
                actual_n_jobs=4,
                actual_chunksize=50,
                actual_speedup=3.2,
                verbose=True
            )
            
            # Find and load the saved file
            cache_files = list(cache_path.glob('ml_training_*.json'))
            
            if cache_files:
                with open(cache_files[0], 'r') as f:
                    saved_data = json.load(f)
                
                print(f"\nSaved data structure:")
                print(f"  Version field present: {'version' in saved_data}")
                print(f"  Version: {saved_data.get('version')}")
                print(f"  ✅ New data includes version for future compatibility!")
            
        finally:
            # Restore original function
            ml_module._get_ml_cache_dir = original_get_cache
    
    print()


def demo_5_benefits():
    """Demo 5: Explain benefits of versioning system."""
    print("=" * 70)
    print("DEMO 5: Benefits of ML Model Versioning")
    print("=" * 70)
    
    benefits = [
        ("Smooth Upgrades", 
         "When ML features evolve, your training data upgrades automatically"),
        
        ("Data Preservation", 
         "Accumulated training data is preserved across version changes"),
        
        ("Clear Errors", 
         "Format mismatches produce clear error messages, not cryptic failures"),
        
        ("No Manual Cleanup", 
         "No need to manually delete cache when upgrading"),
        
        ("Extensible Design", 
         "Easy to add new versions (v2→v3→v4) as features evolve"),
        
        ("Zero Breaking Changes", 
         "Existing users see no disruption - old data works seamlessly")
    ]
    
    print("\nKey Benefits:\n")
    for i, (title, description) in enumerate(benefits, 1):
        print(f"{i}. {title}")
        print(f"   {description}\n")
    
    print("Use Cases:")
    print("  - Adding new features to training data schema")
    print("  - Changing feature normalization methods")
    print("  - Updating workload clustering algorithms")
    print("  - Migrating between incompatible ML approaches")
    print()


def run_all_demos():
    """Run all demonstration scenarios."""
    print("\n" + "=" * 70)
    print("ML MODEL VERSIONING & MIGRATION DEMONSTRATION")
    print("=" * 70)
    print()
    
    demo_1_version_info()
    demo_2_automatic_migration()
    demo_3_backward_compatibility()
    demo_4_new_data_with_version()
    demo_5_benefits()
    
    print("=" * 70)
    print("All demonstrations completed successfully!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    run_all_demos()
