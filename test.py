import quixand as qs
config = qs.Config(timeout=600, image="python:3.11-slim")
ply = qs.Playground(n=2, config=config)
import time
start_time = time.time()
sandboxs = []
for _ in range(2):
    sandboxs.append( ply.create() )
for sbx in sandboxs:
    sbx.shutdown()
end_time = time.time()
total_time = end_time - start_time
seconds_per_box = total_time / 5
print(f"This took {total_time:.2f} seconds ({seconds_per_box:.2f} seconds per box)")