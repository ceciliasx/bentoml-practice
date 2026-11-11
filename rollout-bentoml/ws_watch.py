import sys
import time
from websockets.sync.client import connect

sid = open("last_session.txt").read().strip()
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
t0 = time.perf_counter()
with connect(f"ws://127.0.0.1:3000/live/ws/{sid}?from_index={start}") as ws:
    for msg in ws:
        print(f"client +{time.perf_counter() - t0:.2f}s  {msg}")
print("closed by server")