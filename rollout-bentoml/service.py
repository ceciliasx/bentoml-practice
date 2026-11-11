import asyncio
import json
import time
import uuid
from typing import AsyncGenerator

import bentoml

ENDED = ("done", "cancelled")

class Session:
    def __init__(self,n_steps:int,rate:float):
        self.id = uuid.uuid4().hex[:8]
        self.n_steps = n_steps
        self.rate = rate
        self.frames = [] #frame store; for now in memory
        self.status = "running" #running | done
        self.changed = asyncio.Condition() #wakes up viewers when a frame is added
        self.go = asyncio.Event() #set = may compute, cleared = paused
        self.go.set()
        self.t0 = time.perf_counter()
        self.task = None

@bentoml.service
class Rollout:
    def __init__(self):
        self.sessions = {} #session_id -> Session

    async def _run(self, s: Session):
        for i in range(s.n_steps):
            await s.go.wait()                 # waits here while paused
            if s.status == "cancelled":
                break
            await asyncio.to_thread(time.sleep, 1 / s.rate)
            print(f"server: session {s.id} computed frame {i}", flush=True)
            async with s.changed:
                s.frames.append({"frame": i, "t_server": round(time.perf_counter() - s.t0, 3)})
                s.changed.notify_all()
        async with s.changed:
            if s.status != "cancelled":
                s.status = "done"
            s.changed.notify_all()           # wake viewers so they can finish
        print(f"server: session {s.id} ended ({s.status})", flush=True)

    @bentoml.api
    async def start(self,n_steps:int=30,rate:float=2.0) -> dict:
        s = Session(n_steps,rate)
        self.sessions[s.id] = s
        s.task = asyncio.create_task(self._run(s))
        return {"session_id": s.id}

    @bentoml.api
    async def status(self,session_id:str) -> dict:
        s = self.sessions[session_id]
        return {"status": s.status,"frames_ready": len(s.frames)}

    @bentoml.api
    async def pause(self, session_id: str) -> dict:
        s = self.sessions[session_id]
        if s.status == "running":
            s.status = "paused"
            s.go.clear()
        return {"status": s.status, "frames_ready": len(s.frames)}

    @bentoml.api
    async def resume(self, session_id: str) -> dict:
        s = self.sessions[session_id]
        if s.status == "paused":
            s.status = "running"
            s.go.set()
        return {"status": s.status, "frames_ready": len(s.frames)}

    @bentoml.api
    async def cancel(self, session_id: str) -> dict:
        s = self.sessions[session_id]
        if s.status in ("running", "paused"):
            s.status = "cancelled"
            s.go.set()                        # wake a paused loop so it sees "cancelled"
        return {"status": s.status, "frames_ready": len(s.frames)}

    @bentoml.api
    async def frames(self,session_id:str,from_index: int = 0) -> AsyncGenerator[str,None]:
        s = self.sessions[session_id]
        i = from_index
        while True:
            async with s.changed:
                await s.changed.wait_for(lambda: len(s.frames) > i or s.status in ENDED)
            while i<len(s.frames):
                yield json.dumps(s.frames[i]) + "\n"
                i += 1
            if s.status in ENDED:
                return