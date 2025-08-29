import quicksand as qs


def main():
	with qs.Sandbox(template="python:3.11-slim").pty("/bin/bash") as term:
		term.send("echo hi\n")
		for chunk in term.stream():
			print(chunk.decode("utf-8"), end="")


if __name__ == "__main__":
	main()


