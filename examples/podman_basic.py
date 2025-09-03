#!/usr/bin/env python3
"""
Basic Podman Runtime Example
Shows how to use the Podman container runtime directly
"""

from quixand.container import PodmanRuntime, ContainerConfig, ExecConfig

def main():
    """Demonstrate Podman runtime usage"""
    print("=== Podman Runtime Example ===\n")
    
    # 1. Initialize Podman runtime
    try:
        runtime = PodmanRuntime()
        print("[OK] Podman runtime initialized")
    except Exception as e:
        print(f"[ERROR] Podman not available: {e}")
        return 1
    
    # 2. Create simple container configuration
    config = ContainerConfig(
        name="podman_example",
        image="alpine:latest",
        workdir="/workspace",
        env={"USER": "podman"},
        command=["sleep", "20"]
    )
    
    # 3. Create and start container
    print("\nCreating container...")
    container_id = runtime.create_container(config)
    print(f"[OK] Container created: {container_id[:12]}")
    
    runtime.start_container(container_id)
    print("[OK] Container started")
    
    # 4. Execute commands
    print("\nRunning commands...")
    
    # Check OS info
    exec_config = ExecConfig(
        command=["cat", "/etc/os-release"]
    )
    result = runtime.exec_in_container(container_id, exec_config)
    lines = result.stdout.decode().strip().split('\n')
    for line in lines[:2]:  # Show first 2 lines
        if line.startswith('NAME=') or line.startswith('VERSION='):
            print(f"  {line}")
    
    # List files
    exec_config = ExecConfig(
        command=["ls", "-la", "/workspace"]
    )
    result = runtime.exec_in_container(container_id, exec_config)
    print(f"\nWorkspace contents:")
    print(result.stdout.decode().strip()[:200])  # First 200 chars
    
    # 5. Test timeout handling
    print("\nTesting command with timeout...")
    exec_config = ExecConfig(
        command=["sh", "-c", "echo 'Start' && sleep 1 && echo 'Done'"]
    )
    result = runtime.exec_in_container(container_id, exec_config, timeout=3)
    print(f"Command output: {result.stdout.decode().strip()}")
    print(f"Execution time: {result.duration_seconds:.2f}s")
    
    # 6. Container exists check
    exists = runtime.container_exists(container_id)
    print(f"\nContainer exists: {exists}")
    
    # 7. Clean up
    print("\nCleaning up...")
    runtime.stop_container(container_id, timeout=5)
    runtime.remove_container(container_id, force=True)
    print("[OK] Container removed")
    
    # Verify container removed
    exists = runtime.container_exists(container_id)
    print(f"Container exists after removal: {exists}")
    
    print("\n=== Example completed successfully ===")
    return 0

if __name__ == "__main__":
    exit(main())