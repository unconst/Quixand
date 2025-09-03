#!/usr/bin/env python3
"""
File Operations Example
Shows file operations using the Sandbox high-level API
"""

from quixand import Sandbox

def main():
    """Demonstrate file operations in sandbox"""
    print("=== File Operations Example ===\n")
    
    # Create sandbox
    with Sandbox(timeout=60) as sandbox:
        print(f"Sandbox created: {sandbox.id[:8]}")
        
        # 1. Write text file
        print("\n1. Writing files...")
        sandbox.files.write("hello.txt", "Hello, World!")
        print("[OK] Created hello.txt")
        
        sandbox.files.write("data.json", '{"key": "value"}')
        print("[OK] Created data.json")
        
        # 2. Read file
        print("\n2. Reading files...")
        content = sandbox.files.read("hello.txt")
        print(f"hello.txt content: {content}")
        
        # 3. List files
        print("\n3. Listing files...")
        files = sandbox.files.ls(".")
        for f in files:
            if not f.path.startswith('.'):  # Skip hidden files
                print(f"  {'[DIR]' if f.is_dir else '[FILE]'} {f.path}")
        
        # 4. Create directory structure
        print("\n4. Creating directories...")
        sandbox.files.mkdir("project/src", parents=True)
        sandbox.files.mkdir("project/tests", parents=True)
        print("[OK] Created project structure")
        
        # 5. Move files
        print("\n5. Moving files...")
        sandbox.files.mv("hello.txt", "project/hello.txt")
        sandbox.files.mv("data.json", "project/data.json")
        print("[OK] Moved files to project/")
        
        # 6. Verify with shell command
        print("\n6. Verifying with ls...")
        result = sandbox.run("ls -la project/")
        print(result.text)
        
        # 7. Copy between host and container
        print("\n7. Host file transfer...")
        
        # Create a local file
        with open("/tmp/host_file.txt", "w") as f:
            f.write("Data from host system")
        
        # Upload to sandbox
        sandbox.files.put("/tmp/host_file.txt", "uploaded.txt")
        print("[OK] Uploaded file from host")
        
        # Read uploaded file
        uploaded = sandbox.files.read("uploaded.txt")
        print(f"Uploaded content: {uploaded}")
        
        # Download from sandbox
        sandbox.files.get("project/data.json", "/tmp/downloaded.json")
        print("[OK] Downloaded file to host")
        
        # 8. Delete files
        print("\n8. Cleanup...")
        sandbox.files.rm("uploaded.txt")
        sandbox.files.rm("project", recursive=True)
        print("[OK] Files deleted")
        
    print("\n=== Example completed successfully ===")
    return 0

if __name__ == "__main__":
    exit(main())