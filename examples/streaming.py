import quixand as qs

def main():
	with qs.Sandbox(template="python:3.11-slim").pty("/bin/bash") as term:
		term.send("python -c \"import time; [print(f'Count: {i}', flush=True) or time.sleep(1) for i in range(10)]\"\n")
		for chunk in term.stream():
			print(chunk.decode("utf-8"), end="")


if __name__ == "__main__":
	main()


