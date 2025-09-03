#!/usr/bin/env python3
"""
Simple test script for Quixand refactored code
Tests basic functionality without requiring specific Docker images
"""

from quixand import Sandbox
import sys

def test_sandbox_operations():
    """Test basic sandbox operations"""
    print("Testing Quixand Sandbox Operations...")
    print("=" * 50)
    
    try:
        # Create sandbox with default image
        with Sandbox(timeout=30) as sandbox:
            print(f"✓ Sandbox created: {sandbox.id[:8]}")
            
            # Test 1: Command execution
            result = sandbox.run("echo 'Hello from refactored Quixand!'")
            assert result.exit_code == 0
            print(f"✓ Command execution: {result.text.strip()}")
            
            # Test 2: File write
            test_content = "This is a test file from refactored code"
            sandbox.files.write("test.txt", test_content)
            print("✓ File write successful")
            
            # Test 3: File read
            content = sandbox.files.read("test.txt")
            assert content == test_content
            print("✓ File read successful")
            
            # Test 4: Directory operations
            sandbox.files.mkdir("test_dir")
            print("✓ Directory created")
            
            # Test 5: File listing
            files = sandbox.files.ls(".")
            print(f"✓ File listing: {len(files)} items found")
            
            # Test 6: Python code execution
            code = """
print("Python execution test")
import sys
print(f"Python version: {sys.version.split()[0]}")
"""
            result = sandbox.run(f"python -c '{code}'")
            print(f"✓ Python execution: {result.text.strip()}")
            
        print("\n" + "=" * 50)
        print("All tests passed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_sandbox_operations())