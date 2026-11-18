# import time
# import bentoml

# @bentoml.service
# class Monitor:
#     @bentoml.api
#     def work(self, seconds: float = 1.0) -> dict:
#         count = 0
#         t0 = time.perf_counter()
#         while time.perf_counter() - t0 < seconds:
#             count += 1
#         return {"loops": count}

import os
import time

import bentoml
import psutil


@bentoml.service
class Monitor:
    def __init__(self):
        self.proc = psutil.Process(os.getpid())
        self.proc.cpu_percent(None)
    
    @bentoml.api
    def work(self, seconds: float = 1.0) -> dict:
        print(f"server: work start {time.strftime('%H:%M:%S')}", flush=True)
        count = 0
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < seconds:
            count += 1
        print(f"server: work end   {time.strftime('%H:%M:%S')}", flush=True)
        return {"loops": count}

    @bentoml.api
    def square_one(self, x: float) -> float:
        print(f"server: square_one called with x={x}", flush=True)
        time.sleep(1)
        return x * x

    @bentoml.api(batchable=True, max_batch_size=8, max_latency_ms=5000)
    def square_batch(self, xs: list[float]) -> list[float]:
        print(f"server: square_batch called with {len(xs)} items: {xs}", flush=True)
        time.sleep(1)
        return [x * x for x in xs]

    def __metrics__(self, content: str) -> str:
        cpu = self.proc.cpu_percent(None)
        ram_mb = self.proc.memory_info().rss / 1024**2
        extra = (
            "# HELP monitor_process_cpu_percent CPU usage of this service process\n"
            "# TYPE monitor_process_cpu_percent gauge\n"
            f"monitor_process_cpu_percent {cpu}\n"
            "# HELP monitor_process_ram_mb RAM used by this service process (MB)\n"
            "# TYPE monitor_process_ram_mb gauge\n"
            f"monitor_process_ram_mb {ram_mb:.1f}\n"
        )
        return content + extra