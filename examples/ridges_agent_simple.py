#!/usr/bin/env python3
"""
Simple Ridges Agent interaction example.
Demonstrates how to use Quixand container to interact with Ridges Agent service.
"""

import quixand as qs
import time
import json
import os

chutes_api_key = os.getenv("CHUTES_API_KEY", "")
if not chutes_api_key:
    print("Warning: CHUTES_API_KEY not set. Some features may not work.")
    exit(0)

def main():
    print("=== Ridges Agent Simple Example ===\n")
    image = qs.Templates.build("env_templates/ridges", name="ridges-agent")
    print(f"Image built: {image}\n")
    
    sandbox = qs.Sandbox(
        template=image,
        timeout=300,
        env={
            "CHUTES_API_KEY": chutes_api_key,
        },
    )
    print(f"Container ID: {sandbox.id[:8]}\n")
    
    try:
        print("Waiting for server to be ready...")
        max_retries = 30  # 30 seconds timeout
        retry_interval = 1  # 1 second between checks
        server_ready = False
        
        for i in range(max_retries):
            try:
                # Check health endpoint
                health_check = sandbox.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000/health"],
                    timeout=5
                )
                if health_check.text.strip() == "200":
                    server_ready = True
                    print(f"Server is ready after {i+1} seconds!")
                    break
            except Exception:
                pass
            
            if i % 5 == 0 and i > 0:
                print(f"Still waiting... ({i} seconds)")
            time.sleep(retry_interval)
        
        if not server_ready:
            print("Warning: Server may not be ready after timeout, proceeding anyway...")
        
        problem = "Write quicksort"

        print(f"\nWriting problem: {problem}")
        sandbox.files.write("problem_statement.txt", problem)
        
        print("\nSending request to Agent...")
        
        # Build curl command to run inside container
        curl_cmd = [
            "curl", "-X", "POST", 
            "http://localhost:8000/agents/latest",
        ]
        
        # Execute curl command inside container
        sandbox.run(curl_cmd, timeout=60)
        
        print("\nChecking output.json file...")
        try:
            output_json = sandbox.files.read("output.json")
            if output_json:
                data = json.loads(output_json)
                print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Could not read output.json: {e}")
            
    finally:
        print("\nShutting down container...")
        sandbox.shutdown()
        print("Done")


if __name__ == "__main__":
    main()