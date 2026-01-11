"""
Checkpoint/Resume Examples for Amorsize

This example demonstrates how to use checkpoint/resume functionality to save
progress during long-running workloads and resume from failures.
"""

import os
import random
import shutil
import sys
import time

# Add parent directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amorsize import CheckpointManager, CheckpointPolicy, CheckpointState, get_pending_items, merge_results


# ============================================================================
# Demo 1: Basic Checkpoint/Resume Pattern
# ============================================================================

def demo_1_basic_checkpoint():
    """
    Demonstrate basic checkpoint/resume pattern.
    
    This shows how to:
    1. Create a checkpoint manager
    2. Process items while saving checkpoints
    3. Load checkpoint on failure
    4. Resume from where we left off
    """
    print("=" * 80)
    print("Demo 1: Basic Checkpoint/Resume Pattern")
    print("=" * 80)
    
    # Setup
    checkpoint_dir = "/tmp/amorsize_checkpoints_demo1"
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)
    
    policy = CheckpointPolicy(
        checkpoint_dir=checkpoint_dir,
        checkpoint_interval=5,  # Checkpoint every 5 items
        checkpoint_name="basic_demo",
        save_format="json",  # JSON for human readability
        auto_cleanup=False  # Keep checkpoint for demo
    )
    
    manager = CheckpointManager(policy)
    
    # Simulate a long-running task
    def expensive_computation(x):
        """Simulate expensive computation."""
        time.sleep(0.01)  # Simulate work
        return x ** 2
    
    data = list(range(20))
    checkpoint_name = "basic_demo"
    
    # First run: Process 10 items then "fail"
    print("\n1. First run (will process 10 items then fail)...")
    completed_indices = []
    results = []
    
    try:
        for i, item in enumerate(data):
            result = expensive_computation(item)
            completed_indices.append(i)
            results.append(result)
            
            # Checkpoint every 5 items
            if (i + 1) % 5 == 0:
                state = CheckpointState(
                    completed_indices=completed_indices.copy(),
                    results=results.copy(),
                    total_items=len(data),
                    checkpoint_time=time.time(),
                    n_jobs=1,
                    chunksize=5,
                    metadata={"phase": "initial"}
                )
                manager.save_checkpoint(checkpoint_name, state)
                print(f"   ✓ Checkpointed after {i + 1} items")
            
            # Simulate failure after 10 items
            if i >= 9:
                raise Exception("Simulated failure!")
    
    except Exception as e:
        print(f"   ✗ Execution failed: {e}")
        print(f"   → {len(completed_indices)} items were processed before failure")
    
    # Second run: Resume from checkpoint
    print("\n2. Second run (resuming from checkpoint)...")
    
    # Load checkpoint
    checkpoint_state = manager.load_checkpoint(checkpoint_name)
    
    if checkpoint_state:
        print(f"   ✓ Loaded checkpoint with {len(checkpoint_state.completed_indices)} completed items")
        
        # Get pending items
        pending_indices, pending_items = get_pending_items(data, checkpoint_state)
        print(f"   → Processing {len(pending_items)} remaining items...")
        
        # Process only pending items
        new_results = []
        for item in pending_items:
            result = expensive_computation(item)
            new_results.append(result)
        
        # Merge results
        final_results = merge_results(new_results, pending_indices, checkpoint_state, len(data))
        
        print(f"   ✓ Completed! Processed {len(final_results)} items total")
        print(f"   → Results: {final_results[:5]}... (showing first 5)")
    
    # Cleanup
    manager.delete_checkpoint(checkpoint_name)
    print("\n✓ Checkpoint cleaned up")


# ============================================================================
# Demo 2: Checkpoint Versioning
# ============================================================================

def demo_2_checkpoint_versioning():
    """
    Demonstrate checkpoint versioning and history.
    
    This shows how:
    1. Multiple checkpoint versions are maintained
    2. Old versions are automatically rotated
    3. You can recover from corrupted checkpoints
    """
    print("\n" + "=" * 80)
    print("Demo 2: Checkpoint Versioning")
    print("=" * 80)
    
    checkpoint_dir = "/tmp/amorsize_checkpoints_demo2"
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)
    
    policy = CheckpointPolicy(
        checkpoint_dir=checkpoint_dir,
        keep_history=3,  # Keep 3 versions
        save_format="pickle"
    )
    
    manager = CheckpointManager(policy)
    checkpoint_name = "versioned_demo"
    
    print("\n1. Creating multiple checkpoint versions...")
    
    # Create several checkpoints
    for version in range(5):
        state = CheckpointState(
            completed_indices=list(range(version + 1)),
            results=[i ** 2 for i in range(version + 1)],
            total_items=10,
            checkpoint_time=time.time(),
            n_jobs=2,
            chunksize=5,
            metadata={"version": version}
        )
        manager.save_checkpoint(checkpoint_name, state)
        print(f"   ✓ Saved checkpoint version {version}")
        time.sleep(0.01)
    
    print("\n2. Checking available versions...")
    
    # Check which versions exist
    current_path = manager._get_checkpoint_path(checkpoint_name, 0)
    v1_path = manager._get_checkpoint_path(checkpoint_name, 1)
    v2_path = manager._get_checkpoint_path(checkpoint_name, 2)
    v3_path = manager._get_checkpoint_path(checkpoint_name, 3)
    v4_path = manager._get_checkpoint_path(checkpoint_name, 4)
    
    print(f"   Current checkpoint: {current_path.exists()} (version 4)")
    print(f"   Version 1: {v1_path.exists()} (version 3)")
    print(f"   Version 2: {v2_path.exists()} (version 2)")
    print(f"   Version 3: {v3_path.exists()} (version 1 - should be deleted)")
    print(f"   Version 4: {v4_path.exists()} (version 0 - should be deleted)")
    
    # Load current
    current = manager.load_checkpoint(checkpoint_name)
    print(f"\n3. Current checkpoint contains {len(current.completed_indices)} items")
    print(f"   Metadata: {current.metadata}")
    
    # Cleanup
    manager.delete_checkpoint(checkpoint_name)
    print("\n✓ All versions cleaned up")


# ============================================================================
# Demo 3: JSON vs Pickle Format
# ============================================================================

def demo_3_format_comparison():
    """
    Demonstrate differences between JSON and Pickle formats.
    
    This shows:
    1. JSON is human-readable but limited
    2. Pickle supports all Python objects
    3. Performance differences
    """
    print("\n" + "=" * 80)
    print("Demo 3: JSON vs Pickle Format Comparison")
    print("=" * 80)
    
    checkpoint_dir = "/tmp/amorsize_checkpoints_demo3"
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)
    
    # Create sample state with various data types
    state = CheckpointState(
        completed_indices=list(range(100)),
        results=[i ** 2 for i in range(100)],
        total_items=1000,
        checkpoint_time=time.time(),
        n_jobs=4,
        chunksize=25,
        metadata={
            "description": "Large checkpoint with complex data",
            "nested": {"key": "value", "list": [1, 2, 3]}
        }
    )
    
    # Test JSON format
    print("\n1. Testing JSON format...")
    json_policy = CheckpointPolicy(checkpoint_dir=checkpoint_dir, save_format="json")
    json_manager = CheckpointManager(json_policy)
    
    start = time.time()
    json_path = json_manager.save_checkpoint("format_json", state)
    json_save_time = time.time() - start
    
    start = time.time()
    json_manager.load_checkpoint("format_json")
    json_load_time = time.time() - start
    
    json_size = json_path.stat().st_size
    
    print(f"   ✓ JSON saved in {json_save_time * 1000:.2f}ms")
    print(f"   ✓ JSON loaded in {json_load_time * 1000:.2f}ms")
    print(f"   ✓ JSON size: {json_size:,} bytes")
    print(f"   ✓ JSON is human-readable (check {json_path})")
    
    # Test Pickle format
    print("\n2. Testing Pickle format...")
    pickle_policy = CheckpointPolicy(checkpoint_dir=checkpoint_dir, save_format="pickle")
    pickle_manager = CheckpointManager(pickle_policy)
    
    start = time.time()
    pickle_path = pickle_manager.save_checkpoint("format_pickle", state)
    pickle_save_time = time.time() - start
    
    start = time.time()
    pickle_manager.load_checkpoint("format_pickle")
    pickle_load_time = time.time() - start
    
    pickle_size = pickle_path.stat().st_size
    
    print(f"   ✓ Pickle saved in {pickle_save_time * 1000:.2f}ms")
    print(f"   ✓ Pickle loaded in {pickle_load_time * 1000:.2f}ms")
    print(f"   ✓ Pickle size: {pickle_size:,} bytes")
    print(f"   ✓ Pickle is binary (more compact)")
    
    print("\n3. Comparison:")
    print(f"   Save time: Pickle is {json_save_time / pickle_save_time:.1f}x faster")
    print(f"   Load time: Pickle is {json_load_time / pickle_load_time:.1f}x faster")
    print(f"   File size: Pickle is {json_size / pickle_size:.1f}x smaller")
    
    # Cleanup
    json_manager.delete_checkpoint("format_json")
    pickle_manager.delete_checkpoint("format_pickle")


# ============================================================================
# Demo 4: Failure Scenarios
# ============================================================================

def demo_4_failure_scenarios():
    """
    Demonstrate handling various failure scenarios.
    
    This shows:
    1. Recovery from random failures
    2. Handling partial results
    3. Automatic checkpoint cleanup
    """
    print("\n" + "=" * 80)
    print("Demo 4: Failure Scenarios and Recovery")
    print("=" * 80)
    
    checkpoint_dir = "/tmp/amorsize_checkpoints_demo4"
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)
    
    policy = CheckpointPolicy(
        checkpoint_dir=checkpoint_dir,
        checkpoint_interval=3,  # Frequent checkpoints
        auto_cleanup=True
    )
    
    manager = CheckpointManager(policy)
    checkpoint_name = "failure_demo"
    
    def unreliable_computation(x):
        """Computation that randomly fails."""
        # Simulate random failures
        if random.random() < 0.15:  # 15% failure rate
            raise Exception(f"Random failure at x={x}")
        return x ** 3
    
    data = list(range(20))
    max_retries = 3
    retry_count = 0
    
    print(f"\n1. Processing {len(data)} items with unreliable function...")
    print("   (Function has 15% random failure rate)")
    
    while retry_count < max_retries:
        retry_count += 1
        print(f"\n   Attempt {retry_count}/{max_retries}:")
        
        # Load checkpoint if it exists
        checkpoint_state = manager.load_checkpoint(checkpoint_name)
        
        if checkpoint_state:
            print(f"   → Resuming from checkpoint ({len(checkpoint_state.completed_indices)} items done)")
            pending_indices, pending_items = get_pending_items(data, checkpoint_state)
            completed_indices = checkpoint_state.completed_indices.copy()
            results = checkpoint_state.results.copy()
        else:
            print(f"   → Starting fresh")
            pending_indices, pending_items = list(range(len(data))), data
            completed_indices = []
            results = []
        
        try:
            # Process items
            for idx, item in zip(pending_indices, pending_items):
                result = unreliable_computation(item)
                completed_indices.append(idx)
                results.append(result)
                
                # Checkpoint periodically
                if len(completed_indices) % 3 == 0:
                    state = CheckpointState(
                        completed_indices=completed_indices.copy(),
                        results=results.copy(),
                        total_items=len(data),
                        checkpoint_time=time.time(),
                        n_jobs=1,
                        chunksize=3,
                        metadata={"attempt": retry_count}
                    )
                    manager.save_checkpoint(checkpoint_name, state)
                    print(f"      Checkpoint: {len(completed_indices)}/{len(data)} items")
            
            # Success!
            print(f"\n   ✓ Success! All {len(results)} items processed")
            
            # Merge if we had a checkpoint
            if checkpoint_state:
                final_results = merge_results(
                    results[len(checkpoint_state.results):],
                    pending_indices,
                    checkpoint_state,
                    len(data)
                )
            else:
                final_results = results
            
            print(f"   → Final results: {final_results[:3]}... (showing first 3)")
            
            # Cleanup checkpoint (auto_cleanup would do this, but explicit for demo)
            if manager.load_checkpoint(checkpoint_name):
                manager.delete_checkpoint(checkpoint_name)
                print("\n   ✓ Checkpoint cleaned up after successful completion")
            
            break
        
        except Exception as e:
            print(f"      ✗ Failed: {e}")
            print(f"      → Progress saved: {len(completed_indices)}/{len(data)} items")
            
            if retry_count >= max_retries:
                print(f"\n   ✗ Max retries reached. Checkpoint preserved for manual recovery.")
            else:
                print(f"      → Will retry...")


# ============================================================================
# Demo 5: Benefits Summary
# ============================================================================

def demo_5_benefits():
    """Demonstrate the key benefits of checkpoint/resume."""
    print("\n" + "=" * 80)
    print("Demo 5: Benefits of Checkpoint/Resume")
    print("=" * 80)
    
    print("""
The checkpoint/resume feature provides several key benefits:

1. **Fault Tolerance**: Recover from failures without losing progress
   - Hardware failures (OOM, system crash)
   - Software errors (bugs in user code)
   - External service failures (network, API limits)

2. **Cost Savings**: Avoid re-computation of expensive work
   - Long-running scientific computations
   - Machine learning training/inference
   - Large-scale data processing

3. **Flexibility**: Resume at your convenience
   - Stop/start workloads as needed
   - Adjust resources between runs
   - Debug and fix issues incrementally

4. **Production Reliability**: Complements other reliability features
   - Works with retry logic (Iteration 157)
   - Works with circuit breaker (Iteration 158)
   - Provides last line of defense

5. **Zero Dependencies**: Pure Python, no external dependencies
   - Supports both JSON (readable) and Pickle (efficient) formats
   - Thread-safe for concurrent operations
   - Automatic versioning and cleanup

Usage Patterns:
   - Long-running batch jobs (hours/days)
   - Expensive computations (costly API calls, ML inference)
   - Unreliable environments (cloud spot instances)
   - Development/debugging (iterative workflow)
    """)
    
    print("=" * 80)


# ============================================================================
# Run All Demos
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("AMORSIZE CHECKPOINT/RESUME EXAMPLES")
    print("=" * 80)
    
    demo_1_basic_checkpoint()
    demo_2_checkpoint_versioning()
    demo_3_format_comparison()
    demo_4_failure_scenarios()
    demo_5_benefits()
    
    print("\n" + "=" * 80)
    print("ALL DEMOS COMPLETED")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("1. Checkpoint/resume saves progress during long workloads")
    print("2. Resume from last checkpoint on failure")
    print("3. Supports both JSON (readable) and Pickle (efficient)")
    print("4. Thread-safe with automatic versioning")
    print("5. Zero external dependencies\n")
