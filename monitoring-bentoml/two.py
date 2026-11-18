import sys
import threading
import time

import httpx

URL = "http://127.0.0.1:3000/work"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 2

t0 = time.perf_counter()


def call(i):
    r = httpx.post(URL, json={"seconds": 2}, timeout=60)
    print(f"request {i}: done at {time.perf_counter() - t0:.2f} s -> {r.json()}")


threads = [threading.Thread(target=call, args=(i,)) for i in range(N)]
for t in threads:
    t.start()
for t in threads:
    t.join()