import sys
import bentoml

sid = open("last_session.txt").read().strip()
action = sys.argv[1] #pause | resume | cancel | status
with bentoml.SyncHTTPClient("http://127.0.0.1:3000") as c:
    print(getattr(c,action)(session_id=sid))