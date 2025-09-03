#!/usr/bin/env python3
"""
Basic Docker Runtime Example
Shows how to use the Docker container runtime directly
Note: This example uses python:3.11-slim-bookworm image
"""

from quixand.container import DockerRuntime, ContainerConfig, ExecConfig, ResourceLimits
import tempfile
import os

def main():
    """Demonstrate Docker runtime usage"""
    print("=== Docker Runtime Example ===\n")
    
    # 1. Initialize Docker runtime
    try:
        runtime = DockerRuntime()
        print("[OK] Docker runtime initialized")
    except Exception as e:
        print(f"[ERROR] Docker not available: {e}")
        return 1
    
    # 2. Configure container
    config = ContainerConfig(
        name="docker_example",
        image="python:3.11-slim",  # Use the available image
        workdir="/app",
        env={"APP_ENV": "development"},
        resources=ResourceLimits(
            cpu_limit=0.5,      # Half CPU core
            memory_limit="128m" # 128MB RAM
        ),
        entrypoint=["/bin/sh"],
        command=["-c", "sleep 30"]
    )
    
    container_id = None
    
    try:
        # 3. Create and start container
        print("\nCreating container...")
        container_id = runtime.create_container(config)
        print(f"[OK] Container created: {container_id[:12]}")
        
        runtime.start_container(container_id)
        print("[OK] Container started")
        
        # 4. Execute commands in container
        print("\nExecuting commands...")
        
        # Simple command
        exec_config = ExecConfig(
            command=["echo", "Hello from Docker!"]
        )
        result = runtime.exec_in_container(container_id, exec_config)
        print(f"Echo output: {result.stdout.decode().strip()}")
        
        # Python command
        exec_config = ExecConfig(
            command=["python", "-c", "import sys; print(f'Python {sys.version.split()[0]}')"]
        )
        result = runtime.exec_in_container(container_id, exec_config)
        print(f"Python version: {result.stdout.decode().strip()}")
        
        # 5. File operations
        print("\nFile operations...")
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test data from host\n")
            temp_file = f.name
        
        # Copy to container
        runtime.copy_to_container(container_id, temp_file, "/app/test.txt")
        print("[OK] File copied to container")
        
        # Read from container
        exec_config = ExecConfig(
            command=["cat", "/app/test.txt"]
        )
        result = runtime.exec_in_container(container_id, exec_config)
        print(f"File content: {result.stdout.decode().strip()}")
        
        # Clean up temp file
        os.unlink(temp_file)
        
        # 6. Container info
        print("\nContainer info...")
        info = runtime.get_container_info(container_id)
        print(f"State: {info.state.value}")
        print(f"Created: {info.created_at}")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nNote: This example requires python:3.11-slim image")
        print("You can pull it with: docker pull python:3.11-slim")
        return 1
        
    finally:
        # 7. Cleanup - always clean up container
        if container_id:
            print("\nCleaning up...")
            try:
                runtime.stop_container(container_id, timeout=5)
                print("[OK] Container stopped")
            except:
                pass
            try:
                runtime.remove_container(container_id, force=True)
                print("[OK] Container removed")
            except:
                pass
    
    print("\n=== Example completed successfully ===")
    return 0

if __name__ == "__main__":
    exit(main())