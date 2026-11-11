import time
import bentoml

with bentoml.SyncHTTPClient("http://localhost:3000") as client:
    t0 = time.perf_counter()
    for chunk in client.stream(n_steps = 30, rate=2.0):
        print(f"client + {time.perf_counter() - t0:.2f}s {chunk.strip()}")