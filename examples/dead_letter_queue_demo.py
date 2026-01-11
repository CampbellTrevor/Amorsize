"""
Demonstration of Dead Letter Queue (DLQ) functionality for handling permanently failed items.

This module shows how to use the DLQ feature to:
1. Collect items that fail even after retries
2. Inspect and monitor failures
3. Replay failed items after fixing issues
4. Persist failure information for auditing

The DLQ complements retry and circuit breaker patterns by providing a way to
handle items that fail permanently, enabling graceful degradation and recovery.
"""

import time
from amorsize import DLQPolicy, DLQFormat, DeadLetterQueue, replay_failed_items


def demo_1_basic_usage():
    """
    Demo 1: Basic Dead Letter Queue Usage
    
    Shows how to create a DLQ, add failed items, and inspect them.
    """
    print("\n" + "=" * 70)
    print("Demo 1: Basic DLQ Usage")
    print("=" * 70)
    
    # Create a DLQ with default settings
    dlq = DeadLetterQueue()
    
    # Simulate processing items where some fail
    def risky_process(item):
        """Function that fails on certain items."""
        if item % 3 == 0:
            raise ValueError(f"Item {item} is divisible by 3")
        return item * 2
    
    items = range(10)
    results = []
    
    for item in items:
        try:
            result = risky_process(item)
            results.append(result)
        except Exception as e:
            # Add failed item to DLQ
            dlq.add(item, e)
            print(f"❌ Item {item} failed: {e}")
    
    print(f"\n✅ Successfully processed {len(results)} items")
    print(f"❌ {dlq.size()} items in DLQ")
    
    # Inspect the DLQ
    print("\nDLQ Summary:")
    summary = dlq.get_summary()
    print(f"  Total failed items: {summary['total_entries']}")
    print(f"  Error types: {summary['error_types']}")
    
    # Examine individual failures
    print("\nFailed Items:")
    for entry in dlq.get_entries():
        print(f"  - Item {entry.item}: {entry.error_type} - {entry.error_message}")


def demo_2_with_retry_integration():
    """
    Demo 2: DLQ Integration with Retry Logic
    
    Shows how DLQ works with retry patterns. Items go to DLQ only after
    all retry attempts are exhausted.
    """
    print("\n" + "=" * 70)
    print("Demo 2: DLQ with Retry Logic")
    print("=" * 70)
    
    # Configure DLQ
    policy = DLQPolicy(
        directory="/tmp/demo_dlq",
        format=DLQFormat.JSON,
        auto_persist=False  # Manual control for demo
    )
    dlq = DeadLetterQueue(policy)
    
    # Simulated failure counter
    failure_counts = {}
    
    def flaky_operation(item):
        """Operation that fails randomly but eventually succeeds."""
        # Items divisible by 7 always fail
        if item % 7 == 0:
            raise RuntimeError(f"Item {item} is permanently broken")
        
        # Other items fail first 2 times, then succeed
        failure_counts[item] = failure_counts.get(item, 0) + 1
        if failure_counts[item] <= 2:
            raise ConnectionError(f"Transient failure for item {item}")
        
        return item * 100
    
    def process_with_retry(item, max_retries=3):
        """Process with retry logic and DLQ on permanent failure."""
        for attempt in range(max_retries):
            try:
                return flaky_operation(item)
            except Exception as e:
                if attempt == max_retries - 1:
                    # Final retry failed - add to DLQ
                    dlq.add(
                        item=item,
                        error=e,
                        retry_count=max_retries,
                        metadata={
                            "function": "flaky_operation",
                            "final_attempt": attempt + 1
                        }
                    )
                    print(f"❌ Item {item} failed after {max_retries} retries")
                    raise
                else:
                    print(f"  ⚠️  Item {item} failed (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(0.01)
    
    # Process items
    items = [1, 7, 14, 21, 3, 5]
    results = []
    
    for item in items:
        try:
            result = process_with_retry(item)
            results.append(result)
            print(f"✅ Item {item} succeeded")
        except Exception:
            pass  # Already handled in DLQ
    
    print(f"\n📊 Processing complete:")
    print(f"  ✅ Successful: {len(results)}")
    print(f"  ❌ Failed: {dlq.size()}")
    
    # Analyze failures
    summary = dlq.get_summary()
    print(f"\n📋 Failure Analysis:")
    print(f"  Average retry count: {summary['avg_retry_count']:.1f}")
    print(f"  Error distribution:")
    for error_type, count in summary['error_types'].items():
        print(f"    - {error_type}: {count}")


def demo_3_replay_after_fix():
    """
    Demo 3: Replaying Failed Items After Fixing Issues
    
    Shows how to replay items from the DLQ after fixing the underlying problem.
    """
    print("\n" + "=" * 70)
    print("Demo 3: Replay Failed Items")
    print("=" * 70)
    
    dlq = DeadLetterQueue(DLQPolicy(auto_persist=False))
    
    # Simulate a buggy function
    is_buggy = True
    
    def process_data(item):
        """Function with a bug that can be fixed."""
        if is_buggy and item > 5:
            raise ValueError(f"Bug: Cannot handle item {item}")
        return item ** 2
    
    # Initial processing - some items fail
    print("Phase 1: Initial processing (with bug)")
    items = range(1, 11)
    results = []
    
    for item in items:
        try:
            result = process_data(item)
            results.append(result)
            print(f"  ✅ Item {item} -> {result}")
        except Exception as e:
            dlq.add(item, e)
            print(f"  ❌ Item {item} failed: {e}")
    
    print(f"\nInitial results: {len(results)} succeeded, {dlq.size()} failed")
    
    # Fix the bug
    print("\n🔧 Fixing the bug...")
    is_buggy = False
    
    # Replay failed items
    print("\nPhase 2: Replaying failed items")
    recovered_results, still_failed = replay_failed_items(dlq, process_data)
    
    print(f"\n📊 Replay results:")
    print(f"  ✅ Recovered: {len(recovered_results)}")
    print(f"  ❌ Still failing: {len(still_failed)}")
    print(f"  🎯 DLQ size after replay: {dlq.size()}")
    
    # Combine all results
    all_results = results + recovered_results
    print(f"\n🏁 Final: {len(all_results)} total successful items")


def demo_4_persistence_and_monitoring():
    """
    Demo 4: Persistence and Monitoring
    
    Shows how to persist DLQ to disk for auditing and monitoring across sessions.
    """
    print("\n" + "=" * 70)
    print("Demo 4: Persistence and Monitoring")
    print("=" * 70)
    
    # Create DLQ with auto-persist
    policy = DLQPolicy(
        directory="/tmp/persistent_dlq",
        format=DLQFormat.JSON,  # Human-readable for debugging
        auto_persist=True,      # Automatically save to disk
        include_traceback=True  # Include full stack traces
    )
    
    dlq = DeadLetterQueue(policy)
    
    # Simulate various types of failures
    print("Simulating various failures...")
    
    def complex_operation(item):
        """Operation with multiple failure modes."""
        if item.get("type") == "network":
            raise ConnectionError("Network timeout")
        elif item.get("type") == "validation":
            raise ValueError("Invalid data format")
        elif item.get("type") == "permission":
            raise PermissionError("Access denied")
        return item
    
    test_items = [
        {"id": 1, "type": "network", "data": "payload1"},
        {"id": 2, "type": "validation", "data": "payload2"},
        {"id": 3, "type": "permission", "data": "payload3"},
        {"id": 4, "type": "network", "data": "payload4"},
        {"id": 5, "type": "ok", "data": "payload5"},
    ]
    
    for item in test_items:
        try:
            complex_operation(item)
            print(f"  ✅ Item {item['id']}: success")
        except Exception as e:
            dlq.add(
                item=item,
                error=e,
                retry_count=1,
                metadata={
                    "source": "complex_operation",
                    "item_id": item["id"]
                }
            )
            print(f"  ❌ Item {item['id']}: {type(e).__name__}")
    
    # Show monitoring information
    print(f"\n📊 DLQ Monitoring Dashboard:")
    summary = dlq.get_summary()
    print(f"  Total failed items: {summary['total_entries']}")
    print(f"  Failure breakdown:")
    for error_type, count in sorted(summary['error_types'].items()):
        print(f"    {error_type}: {count}")
    
    # Show that data is persisted
    print(f"\n💾 DLQ persisted to: {policy.directory}/dlq.json")
    print(f"  (Can be loaded in a new session for analysis)")
    
    # Demonstrate loading from disk
    print("\n🔄 Simulating new session - loading from disk...")
    dlq2 = DeadLetterQueue(policy)
    dlq2.load()
    print(f"  Loaded {dlq2.size()} entries from persistent storage")


def demo_5_size_limiting():
    """
    Demo 5: Size Limiting and Management
    
    Shows how DLQ automatically manages size to prevent unbounded growth.
    """
    print("\n" + "=" * 70)
    print("Demo 5: Size Limiting")
    print("=" * 70)
    
    # Create DLQ with size limit
    policy = DLQPolicy(
        directory="/tmp/limited_dlq",
        max_entries=10,  # Keep only last 10 failures
        auto_persist=False
    )
    
    dlq = DeadLetterQueue(policy)
    
    # Add more items than the limit
    print(f"Adding 15 failed items (limit: {policy.max_entries})...")
    for i in range(15):
        dlq.add(
            item=f"item_{i}",
            error=Exception(f"error_{i}"),
            metadata={"index": i}
        )
    
    print(f"\nDLQ size: {dlq.size()} (oldest entries automatically removed)")
    
    # Verify that oldest entries were removed
    entries = dlq.get_entries()
    first_item = entries[0].metadata["index"]
    last_item = entries[-1].metadata["index"]
    
    print(f"First item index: {first_item} (oldest kept)")
    print(f"Last item index: {last_item} (newest)")
    print(f"\n✅ Automatic pruning keeps DLQ bounded")
    
    # Show clearing
    cleared = dlq.clear()
    print(f"\n🧹 Cleared {cleared} entries from DLQ")
    print(f"DLQ size after clear: {dlq.size()}")


def demo_6_real_world_pattern():
    """
    Demo 6: Real-World Pattern - API Processing with DLQ
    
    Complete example showing retry + circuit breaker + DLQ integration.
    """
    print("\n" + "=" * 70)
    print("Demo 6: Real-World API Processing Pattern")
    print("=" * 70)
    
    dlq = DeadLetterQueue(DLQPolicy(auto_persist=False))
    
    # Simulate API state
    api_down = False
    rate_limited_ids = {5, 15}
    
    def call_external_api(user_id):
        """Simulate calling an external API."""
        if api_down:
            raise ConnectionError("API is down")
        if user_id in rate_limited_ids:
            raise Exception("Rate limit exceeded")
        if user_id % 13 == 0:
            raise ValueError("Invalid user ID format")
        return {"user_id": user_id, "data": f"profile_{user_id}"}
    
    def process_user_batch(user_ids, max_retries=3):
        """Process a batch of users with retry and DLQ."""
        results = []
        
        for user_id in user_ids:
            success = False
            
            for attempt in range(max_retries):
                try:
                    result = call_external_api(user_id)
                    results.append(result)
                    success = True
                    break
                except ConnectionError as e:
                    # Network errors - worth retrying
                    if attempt < max_retries - 1:
                        time.sleep(0.01)
                    else:
                        dlq.add(user_id, e, retry_count=max_retries,
                               metadata={"category": "network_error"})
                except ValueError as e:
                    # Validation errors - won't be fixed by retrying
                    dlq.add(user_id, e, retry_count=0,
                           metadata={"category": "validation_error"})
                    break
                except Exception as e:
                    # Other errors
                    if attempt < max_retries - 1:
                        time.sleep(0.01)
                    else:
                        dlq.add(user_id, e, retry_count=max_retries,
                               metadata={"category": "unknown_error"})
            
            if success:
                print(f"  ✅ User {user_id}")
            else:
                print(f"  ❌ User {user_id}")
        
        return results
    
    # Process batch
    print("Processing user batch...")
    user_ids = [1, 5, 10, 13, 15, 20, 26]
    results = process_user_batch(user_ids)
    
    print(f"\n📊 Batch processing complete:")
    print(f"  ✅ Successful: {len(results)}")
    print(f"  ❌ Failed: {dlq.size()}")
    
    # Analyze failures by category
    print(f"\n📋 Failure Analysis:")
    entries = dlq.get_entries()
    categories = {}
    for entry in entries:
        cat = entry.metadata.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    for category, count in categories.items():
        print(f"  {category}: {count}")
    
    print("\n💡 Actions:")
    for entry in entries:
        category = entry.metadata.get("category")
        if category == "validation_error":
            print(f"  - Fix data format for user {entry.item}")
        elif category == "network_error":
            print(f"  - Retry user {entry.item} when network recovers")
        else:
            print(f"  - Investigate user {entry.item}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("AMORSIZE - Dead Letter Queue Demonstrations")
    print("=" * 70)
    
    demos = [
        ("Basic Usage", demo_1_basic_usage),
        ("Retry Integration", demo_2_with_retry_integration),
        ("Replay After Fix", demo_3_replay_after_fix),
        ("Persistence & Monitoring", demo_4_persistence_and_monitoring),
        ("Size Limiting", demo_5_size_limiting),
        ("Real-World Pattern", demo_6_real_world_pattern),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n⚠️  Demo '{name}' encountered an error: {e}")
    
    print("\n" + "=" * 70)
    print("All demonstrations complete!")
    print("=" * 70)
    
    print("\n📚 Key Takeaways:")
    print("  1. DLQ collects items that fail permanently after retries")
    print("  2. Provides monitoring and inspection capabilities")
    print("  3. Supports replay after fixing underlying issues")
    print("  4. Persists to disk for auditing and cross-session analysis")
    print("  5. Automatically manages size to prevent unbounded growth")
    print("  6. Integrates seamlessly with retry and circuit breaker patterns")
