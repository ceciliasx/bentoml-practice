# import bentoml

# with bentoml.SyncHTTPClient("http://localhost:3000") as c:
#     print(c.start(n_steps=30,rate=2.0))


import bentoml

with bentoml.SyncHTTPClient("http://127.0.0.1:3000") as c:
    r = c.start(n_steps=60, rate=1.0)
print(r)
with open("last_session.txt", "w") as f:
    f.write(r["session_id"])