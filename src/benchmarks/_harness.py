"""Shared helpers for the benchmark suites.

Every benchmark function returns the result schema defined in
spec/benchmark_set_v0.1.md. `timed` injects duration_ms; `make` builds the dict.
"""

import functools
import time


def timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        d = fn(*args, **kwargs)
        d.setdefault("duration_ms", (time.perf_counter() - t0) * 1000.0)
        return d
    return wrapper


def make(bid, name, result, threshold, passed, notes="", confidence=""):
    return {
        "id": bid,
        "name": name,
        "result": result,
        "threshold": threshold,
        "passed": passed,
        "notes": notes,
        "confidence": confidence,
    }
