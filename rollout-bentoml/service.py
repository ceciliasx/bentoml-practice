import asyncio
import json
import time
from typing import AsyncGenerator

import bentoml

@bentoml.service
class Rollout:
    @bentoml.api
    async def stream(self, n_steps: int = 10, rate: float = 2.0) -> AsyncGenerator[str,None]:
        t0 = time.perf_counter()
        for i in range(n_steps):
            await asyncio.sleep(1/rate) #act like its one model step
            print(f"server: computed frame {i}")
            yield json.dumps({"frame": i, "t_server": round(time.perf_counter() - t0, 3)}) + "\n"