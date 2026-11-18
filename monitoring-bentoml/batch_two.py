import sys
import threading
import time

import httpx

MODE = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 3
BASE = "http://127.0.0.1:3000"

t0 = time.perf_counter()


def call(i):
    if MODE == "one":
        r = httpx.post(f"{BASE}/square_one", json={"x": i}, timeout=60)
    else:
        r = httpx.post(f"{BASE}/square_batch", json={"xs": [i]}, timeout=60)
    print(f"request {i}: done at {time.perf_counter() - t0:.2f} s -> {r.json()}")


threads = [threading.Thread(target=call, args=(i,)) for i in range(N)]
for t in threads:
    t.start()
for t in threads:
    t.join()