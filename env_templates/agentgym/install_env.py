#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

def install_environment():
    """Install AgentGym environment based on ENV_NAME."""
    env_name = os.environ.get('ENV_NAME', '')
    
    if not env_name:
        print("No ENV_NAME specified, skipping environment installation")
        return
    
    print(f"Installing AgentGym environment: {env_name}")
    
    # Special handling for alfworld environment
    if env_name == "alfworld":
        print("Special handling for alfworld environment...")
        
        # Set environment variables for C compilation to avoid errors with textworld
        env = os.environ.copy()
        env["CFLAGS"] = "-O3 -fPIC -Wno-incompatible-pointer-types"
        env["CPPFLAGS"] = "-Wno-incompatible-pointer-types"
        
        # Install textworld with special flags
        print("Installing textworld with special compilation flags...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "textworld"
        ], env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Successfully installed textworld")
        else:
            print(f"Warning: textworld installation had issues")
            if result.stderr:
                print(f"Error output: {result.stderr}")
    
    # Check for setup.sh and execute it if it exists
    env_path = Path(f"/app/AgentGym/agentenv-{env_name}")
    setup_script = env_path / "setup.sh"
    
    if setup_script.exists():
        print(f"Found setup.sh for {env_name}, executing...")
        try:
            # Make the script executable
            setup_script.chmod(0o755)
            
            # Prepare environment with special flags for alfworld
            env = os.environ.copy()
            if env_name == "alfworld":
                env["CFLAGS"] = "-O3 -fPIC -Wno-incompatible-pointer-types"
                env["CPPFLAGS"] = "-Wno-incompatible-pointer-types"
            
            # Execute the setup script
            result = subprocess.run(
                ["bash", str(setup_script)],
                cwd=str(env_path),
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"Successfully executed setup.sh for {env_name}")
                if result.stdout:
                    print(f"Setup output:\n{result.stdout}")
            else:
                print(f"Warning: setup.sh execution failed with code {result.returncode}")
                if result.stderr:
                    print(f"Setup error:\n{result.stderr}")
                if result.stdout:
                    print(f"Setup output:\n{result.stdout}")
                # Continue installation anyway
                
        except Exception as e:
            print(f"Warning: Failed to execute setup.sh: {e}")
            # Continue with pip installation
    else:
        # If no setup.sh, proceed with pip installation
        if env_path.exists():
            # Try to install with no-build-isolation first for better compatibility
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", str(env_path), "--no-build-isolation"
            ], capture_output=True, text=True)
            
            # If that fails, try normal installation
            if result.returncode != 0:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-e", str(env_path)
                ], check=False)
    
    print(f"Environment {env_name} installation completed")

if __name__ == "__main__":
    install_environment()