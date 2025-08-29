import quicksand as qs


def main():
	img = qs.Templates.build("./", name="py311-tools")
	print("built:", img)
	sbx = qs.Sandbox(template=img)
	print("sandbox:", sbx.id)
	sbx.shutdown()


if __name__ == "__main__":
	main()


