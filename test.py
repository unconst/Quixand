import quixand as qx
LEAN_IMAGE = "leanprovercommunity/lean4:latest"
lean_config = qx.Config(timeout=600, image=LEAN_IMAGE, workdir="/workspace")
lean_executors = qx.Playground(n=2, config=lean_config)
sands = lean_executors.create()
print(sands.status())
a