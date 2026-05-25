"""Serial Compute Efficiency (SCE) -- SCE-01..04. Real measurements.

Reuses the profiler functions with lighter parameters so the runner stays fast.
The authoritative, full-length numbers are produced by src/mvw/mvw_profiler.py
and written to results/sce_profile_{timestamp}.json.
"""

from _harness import timed, make
from mvw_profiler import sce01 as _p01, sce02 as _p02, sce04 as _p04, _measure_tps


@timed
def sce_01():
    r = _p01(n_ticks=500)
    return make(
        "SCE-01", "CPU cost per tick (MVW)", r["mean_ns"],
        "profiler measurement", None,
        notes="mean ns/tick over 500 ticks (full run uses 10000)",
        confidence="SPECULATIVE")


@timed
def sce_02():
    r = _p02(n_entities=1000)
    return make(
        "SCE-02", "RAM per 1K entities", r["bytes_per_1k_entities"],
        "profiler measurement", None,
        notes="tracemalloc bytes for 1000-entity world construction",
        confidence="SPECULATIVE")


@timed
def sce_03():
    # Light scaling probe: O(N^2) for naive, O(N log N) for bvh expected.
    naive = {n: _measure_tps(n, "naive", min_ticks=2, time_budget=0.2)[0]
             for n in (10, 100, 500)}
    bvh = {n: _measure_tps(n, "bvh", min_ticks=2, time_budget=0.2)[0]
           for n in (10, 100, 1000)}
    # naive should slow ~4x from N=100->N=500 (4x pairs); report the ratio.
    ratio = naive[100] / naive[500] if naive[500] else float("inf")
    return make(
        "SCE-03", "Tick cost scaling law",
        "naive 100->500 slowdown %.1fx" % ratio,
        "O(N log N) or better (bvh)", None,
        notes="full O() fit in sce_profile JSON; bvh N=1000=%.0f tps"
              % bvh[1000],
        confidence="PLAUSIBLE")


@timed
def sce_04():
    r = _p04(seconds=3.0)
    return make(
        "SCE-04", "Serial sufficiency", r["ticks_per_sec"],
        ">= 60 ticks/sec", r["passed"],
        notes="3s window in runner; authoritative 60s run in sce_profile JSON "
              "(%.0fx headroom)" % r["headroom_x"],
        confidence="SPECULATIVE")


def run_all():
    return [sce_01(), sce_02(), sce_03(), sce_04()]
