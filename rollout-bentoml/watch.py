# import sys
# import time
# import bentoml

# sid = sys.argv[1]
# start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
# t0 = time.perf_counter() #this time before the client
# with bentoml.SyncHTTPClient("http://localhost:3000") as c:
#     for chunk in c.frames(session_id=sid,from_index=start):
#         print(f"client + {time.perf_counter() - t0:.2f}s {chunk.strip()}")

import sys
import time
import bentoml

sid = open("last_session.txt").read().strip()
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
t0 = time.perf_counter()
with bentoml.SyncHTTPClient("http://127.0.0.1:3000") as c:
    for chunk in c.frames(session_id=sid, from_index=start):
        print(f"client +{time.perf_counter() - t0:.2f}s  {chunk.strip()}")