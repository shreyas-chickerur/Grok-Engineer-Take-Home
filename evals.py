from typing import List, Dict, Any, Callable
import time

def run_table(inputs: List[Dict[str, Any]], func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for i, x in enumerate(inputs, 1):
        t0 = time.time()
        out = func(x)
        dt = time.time() - t0
        rows.append({"idx": i, "input": x, "output": out, "latency_s": round(dt, 3)})
    return rows
