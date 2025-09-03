#!/usr/bin/env python3
"""
Streaming Output Example
Shows how to handle streaming output from long-running commands
"""

from quixand import Sandbox
import time

def main():
    """Demonstrate streaming output capabilities"""
    print("=== Streaming Output Example ===\n")
    
    # Create sandbox
    with Sandbox(timeout=60) as sandbox:
        print(f"Sandbox created: {sandbox.id[:8]}")
        
        # Example 1: Stream line by line output
        print("\n1. Streaming line-by-line output...")
        code = """
import time
for i in range(5):
    print(f"Line {i+1}")
    time.sleep(1)
"""
        
        # Run with streaming
        for line in sandbox.run_stream(f"python3 -c '{code}'"):
            print(f"[STREAM] {line.strip()}")
        
        # Example 2: Progress indicator
        print("\n2. Progress indicator...")
        code = """
import time
total = 20
for i in range(total):
    progress = (i + 1) / total * 100
    print(f"Progress: {progress:.0f}%")
    time.sleep(0.2)
print("Completed!")
"""
        
        # Track progress
        for line in sandbox.run_stream(f"python3 -c '{code}'"):
            if "Progress:" in line:
                print(f"\r{line.strip()}", end="", flush=True)
            elif "Completed" in line:
                print(f"\n[OK] {line.strip()}")
        
        # Example 3: Real-time log monitoring
        print("\n3. Real-time log monitoring...")
        
        # Start a background process
        sandbox.run_background("""
python3 -c "
import time
for i in range(10):
    print(f'[LOG] Event {i+1} occurred')
    time.sleep(0.5)
"
""")
        
        # Stream logs
        print("Monitoring logs...")
        time.sleep(6)  # Let it run for a bit
        
        # Example 4: Handle mixed stdout/stderr
        print("\n4. Mixed stdout/stderr streaming...")
        code = """
import sys
import time
for i in range(3):
    print(f"[STDOUT] Message {i+1}")
    print(f"[STDERR] Warning {i+1}", file=sys.stderr)
    time.sleep(0.5)
"""
        
        # Stream both outputs
        for line in sandbox.run_stream(f"python3 -c '{code}'", combine_output=True):
            if "[STDERR]" in line:
                print(f"⚠️  {line.strip()}")
            else:
                print(f"✓ {line.strip()}")
        
        # Example 5: Interactive-like behavior
        print("\n5. Interactive command simulation...")
        
        # Create a script that expects input
        sandbox.files.write("interactive.py", """
name = input("Enter your name: ")
print(f"Hello, {name}!")
age = input("Enter your age: ")
print(f"You are {age} years old.")
""")
        
        # Run with predefined inputs
        result = sandbox.run("echo -e 'Alice\\n25' | python3 interactive.py")
        print(result.text)
    
    print("\n=== Example completed successfully ===")
    return 0

if __name__ == "__main__":
    exit(main())
