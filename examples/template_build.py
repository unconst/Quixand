import quixand as qs


def main():
	img = qs.Templates.build("./", name="py311-tools")
	print("built:", img)
	
	sbx = qs.Sandbox(
		template=img,
		volumes=[
			{"source": "/var/run/docker.sock", "target": "/var/run/docker.sock", "type": "bind"}
		]
	)
	print("sandbox:", sbx.id)
	print("✓ Docker socket mounted for nested execution support")
	
	with open("examples/minimal.py", "r") as f:
		minimal_code = f.read()
	
	sbx.files.write("minimal.py", minimal_code)
	print("✓ Copied minimal.py to sandbox")
	
	print("\n=== Executing minimal.py inside sandbox (nested execution) ===")
	
	result = sbx.run(["python", "minimal.py"])
	
	print("\nOutput from nested execution:")
	print(result.text)
	
	if result.stderr:
		print("\nErrors (if any):")
		print(result.stderr)
	
	print("\n=== Nested execution completed ===")
	
	sbx.shutdown()
	print("✓ Sandbox shut down")


if __name__ == "__main__":
	main()
