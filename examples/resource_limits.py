#!/usr/bin/env python3
"""
Resource Limits Example
Demonstrates how to set and test resource limits for sandboxes
"""

from quixand import Sandbox
from quixand.container.base import ResourceLimits
import time

def main():
    """Demonstrate resource limiting capabilities"""
    print("=== Resource Limits Example ===\n")
    
    # Example 1: Memory limit
    print("1. Testing memory limits...")
    limits = ResourceLimits(memory="50m")  # 50MB limit
    
    with Sandbox(resource_limits=limits, timeout=30) as sandbox:
        print(f"Sandbox created with 50MB memory limit")
        
        # Try to allocate small amount (should succeed)
        result = sandbox.run("python3 -c 'data = bytearray(10 * 1024 * 1024); print(\"Allocated 10MB\")'")
        if result.exit_code == 0:
            print(f"[OK] {result.text.strip()}")
        
        # Try to allocate too much (should fail)
        result = sandbox.run("python3 -c 'data = bytearray(100 * 1024 * 1024); print(\"Allocated 100MB\")'")
        if result.exit_code != 0:
            print("[OK] Large allocation failed as expected")
    
    # Example 2: CPU limits
    print("\n2. Testing CPU limits...")
    limits = ResourceLimits(cpu_quota=50000, cpu_period=100000)  # 50% CPU
    
    with Sandbox(resource_limits=limits, timeout=30) as sandbox:
        print(f"Sandbox created with 50% CPU limit")
        
        # CPU intensive task
        code = """
import time
start = time.time()
# CPU intensive loop
for _ in range(10**7):
    _ = sum(range(100))
elapsed = time.time() - start
print(f"Task completed in {elapsed:.2f}s")
"""
        result = sandbox.run(f"python3 -c '{code}'")
        print(f"Result: {result.text.strip()}")
    
    # Example 3: PID limits
    print("\n3. Testing PID limits...")
    limits = ResourceLimits(pids_limit=10)
    
    with Sandbox(resource_limits=limits, timeout=30) as sandbox:
        print(f"Sandbox created with max 10 PIDs")
        
        # Try to create many processes
        code = """
import os
for i in range(5):
    if os.fork() == 0:
        # Child process
        import time
        time.sleep(1)
        exit(0)
print("Created 5 child processes")
"""
        result = sandbox.run(f"python3 -c '{code}'")
        if result.exit_code == 0:
            print(f"[OK] {result.text.strip()}")
    
    # Example 4: Combined limits
    print("\n4. Testing combined limits...")
    limits = ResourceLimits(
        memory="100m",
        cpu_quota=25000,
        cpu_period=100000,  # 25% CPU
        pids_limit=20
    )
    
    with Sandbox(resource_limits=limits, timeout=30) as sandbox:
        print("Sandbox created with multiple limits:")
        print("  - Memory: 100MB")
        print("  - CPU: 25%")
        print("  - PIDs: 20")
        
        # Run a simple test
        result = sandbox.run("echo 'Running with multiple limits'")
        print(f"[OK] {result.text.strip()}")
        
        # Check resource usage
        result = sandbox.run("ps aux | wc -l")
        print(f"Process count: {result.text.strip()}")
    
    print("\n=== Example completed successfully ===")
    return 0

if __name__ == "__main__":
    exit(main())