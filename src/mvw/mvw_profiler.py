"""SCE profiling harness -- produces the empirical SCE-01..04 results.

Closes SCE-04: replaces the analytical 162,000 ticks/sec estimate with a real,
measured number on this machine. Writes results/sce_profile_{timestamp}.json
and prints a human-readable summary.

Usage:
    python src/mvw/mvw_profiler.py                # full run (SCE-04 = 60s)
    python src/mvw/mvw_profiler.py --quick        # fast smoke run
    python src/mvw/mvw_profiler.py --sce04-seconds 30 --sce01-ticks 5000

The profiler is single-core: it pins to CPU 0 (os.sched_setaffinity) where the
platform allows, matching the serial-baseline measurement protocol.

Standard library only for measurement. (numpy is deliberately avoided here even
though it is permitted for figures, to keep the profiler aligned with the
serial-kernel philosophy.)
"""

import argparse
import json
import math
import os
import platform
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(_HERE, "..", "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from mvw_instance import MVW  # noqa: E402

_RESULTS_DIR = os.path.join(_HERE, "..", "..", "results")


def pin_to_cpu0():
    """Pin this process to CPU 0 if the platform supports affinity."""
    try:
        os.sched_setaffinity(0, {0})
        return True
    except (AttributeError, OSError):
        return False  # not available (e.g. macOS); measurement still valid


def _cpu_freq_hz():
    try:
        import psutil
        f = psutil.cpu_freq()
        if f and f.current:
            return f.current * 1e6  # MHz -> Hz
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# SCE-01 -- per-tick cost
# ---------------------------------------------------------------------------

def sce01(n_ticks, mode="naive"):
    mvw = MVW(seed=42, mode=mode)
    sched = mvw.scheduler
    per_tick = []
    for _ in range(n_ticks):
        t0 = time.perf_counter()
        sched.tick()
        per_tick.append(time.perf_counter() - t0)

    mean_s = statistics.fmean(per_tick)
    std_s = statistics.pstdev(per_tick)
    freq = _cpu_freq_hz()
    # Wall-time-derived cycle estimate, NOT a hardware performance counter.
    est_cycles = mean_s * freq if freq else None
    return {
        "id": "SCE-01",
        "name": "CPU cost per tick (MVW N=100)",
        "mode": mode,
        "n_ticks": n_ticks,
        "mean_ns": mean_s * 1e9,
        "std_ns": std_s * 1e9,
        "min_ns": min(per_tick) * 1e9,
        "max_ns": max(per_tick) * 1e9,
        "ticks_per_sec": (1.0 / mean_s) if mean_s > 0 else None,
        "cpu_freq_hz": freq,
        "est_cycles_per_tick": est_cycles,
        "confidence": "SPECULATIVE",
        "notes": ("est_cycles_per_tick is wall-time x measured CPU freq, not a "
                  "hardware perf counter"),
    }


# ---------------------------------------------------------------------------
# SCE-02 -- memory footprint
# ---------------------------------------------------------------------------

def sce02(n_entities=1000):
    tracemalloc.start()
    base = tracemalloc.take_snapshot()
    mvw = MVW(seed=42, n=n_entities)        # construct, do not run
    after = tracemalloc.take_snapshot()
    stats = after.compare_to(base, "filename")
    total = sum(s.size_diff for s in stats)
    tracemalloc.stop()
    per_entity = total / n_entities
    return {
        "id": "SCE-02",
        "name": "RAM per 1K entities",
        "n_entities": n_entities,
        "total_bytes": total,
        "bytes_per_entity": per_entity,
        "bytes_per_1k_entities": per_entity * 1000,
        "confidence": "SPECULATIVE",
        "notes": "tracemalloc allocation delta for world construction",
        # keep a reference so the allocation is not collected before snapshot
        "_live": bool(mvw.entity_count),
    }


# ---------------------------------------------------------------------------
# SCE-03 -- scaling law
# ---------------------------------------------------------------------------

def _measure_tps(n, mode, min_ticks=3, time_budget=0.5):
    """ticks/sec for a world of n entities: run >= min_ticks, stop after
    time_budget seconds. Returns (ticks_per_sec, seconds_per_tick)."""
    mvw = MVW(seed=42, n=n, mode=mode)
    sched = mvw.scheduler
    ticks = 0
    t0 = time.perf_counter()
    while True:
        sched.tick()
        ticks += 1
        elapsed = time.perf_counter() - t0
        if ticks >= min_ticks and elapsed >= time_budget:
            break
    elapsed = time.perf_counter() - t0
    return ticks / elapsed, elapsed / ticks


def _fit_through_origin(xs, ys):
    """Least-squares fit y = a*x through the origin; returns (a, r2)."""
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    a = sxy / sxx if sxx else 0.0
    ybar = statistics.fmean(ys)
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    ss_res = sum((y - a * x) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot else 1.0
    return a, r2


def sce03(naive_ns, bvh_ns):
    """Fit O(N), O(N log N), O(N^2) to measured seconds-per-tick for each mode."""
    models = {
        "O(N)": lambda n: float(n),
        "O(N log N)": lambda n: n * math.log2(n) if n > 1 else 1.0,
        "O(N^2)": lambda n: float(n * n),
    }

    def analyse(samples):
        ns = [s["n"] for s in samples]
        spt = [s["sec_per_tick"] for s in samples]
        fits = {}
        for name, f in models.items():
            xs = [f(n) for n in ns]
            _, r2 = _fit_through_origin(xs, spt)
            fits[name] = r2
        best = max(fits, key=fits.get)
        return {"samples": samples, "r2_by_model": fits, "best_fit": best}

    return {
        "id": "SCE-03",
        "name": "Tick cost scaling law",
        "naive": analyse(naive_ns),
        "bvh": analyse(bvh_ns),
        "threshold": "O(N log N) or better (BVH)",
        "confidence": "PLAUSIBLE",
        "notes": ("seconds/tick fit through origin; best_fit is the model with "
                  "highest R^2"),
    }


# ---------------------------------------------------------------------------
# SCE-04 -- serial sufficiency
# ---------------------------------------------------------------------------

def sce04(seconds, mode="naive"):
    mvw = MVW(seed=42, mode=mode)
    sched = mvw.scheduler
    ticks = 0
    t0 = time.perf_counter()
    deadline = t0 + seconds
    while time.perf_counter() < deadline:
        sched.tick()
        ticks += 1
    elapsed = time.perf_counter() - t0
    tps = ticks / elapsed
    return {
        "id": "SCE-04",
        "name": "Serial sufficiency",
        "mode": mode,
        "wall_seconds": elapsed,
        "ticks_completed": ticks,
        "ticks_per_sec": tps,
        "threshold_ticks_per_sec": 60.0,
        "passed": tps >= 60.0,
        "headroom_x": tps / 60.0,
        "confidence": "SPECULATIVE",
        "notes": ("empirical pure-Python single-core measurement; the paper's "
                  "162k analytical estimate assumes 1 op = 1 cycle at 1 GHz"),
    }


def main():
    ap = argparse.ArgumentParser(description="holodeck-serial SCE profiler")
    ap.add_argument("--sce01-ticks", type=int, default=10000)
    ap.add_argument("--sce04-seconds", type=float, default=60.0)
    ap.add_argument("--quick", action="store_true",
                    help="fast smoke run (small tick counts, 5s SCE-04)")
    args = ap.parse_args()

    sce01_ticks = args.sce01_ticks
    sce04_seconds = args.sce04_seconds
    scaling_naive_ns = [10, 50, 100, 500, 1000]
    scaling_bvh_ns = [10, 50, 100, 500, 1000, 5000]
    if args.quick:
        sce01_ticks = 1000
        sce04_seconds = 5.0
        scaling_naive_ns = [10, 50, 100, 500]
        scaling_bvh_ns = [10, 50, 100, 500, 1000]

    pinned = pin_to_cpu0()
    print("=" * 64)
    print("holodeck-serial SCE profiler")
    print("  platform : %s" % platform.platform())
    print("  python   : %s" % platform.python_version())
    print("  cpu0_pin : %s" % ("yes" if pinned else "unavailable"))
    print("=" * 64)

    print("[SCE-01] per-tick cost over %d ticks ..." % sce01_ticks)
    r01 = sce01(sce01_ticks)
    print("         mean=%.0f ns  std=%.0f ns  -> %.1f ticks/sec"
          % (r01["mean_ns"], r01["std_ns"], r01["ticks_per_sec"]))

    print("[SCE-02] RAM footprint ...")
    r02 = sce02()
    print("         %.0f bytes/entity  -> %.1f KB per 1K entities"
          % (r02["bytes_per_entity"], r02["bytes_per_1k_entities"] / 1024.0))

    print("[SCE-03] scaling law ...")
    naive_samples = []
    for n in scaling_naive_ns:
        tps, spt = _measure_tps(n, "naive")
        naive_samples.append({"n": n, "ticks_per_sec": tps, "sec_per_tick": spt})
        print("         naive N=%-5d %.1f ticks/sec" % (n, tps))
    bvh_samples = []
    for n in scaling_bvh_ns:
        tps, spt = _measure_tps(n, "bvh")
        bvh_samples.append({"n": n, "ticks_per_sec": tps, "sec_per_tick": spt})
        print("         bvh   N=%-5d %.1f ticks/sec" % (n, tps))
    r03 = sce03(naive_samples, bvh_samples)
    print("         best fit  naive=%s  bvh=%s"
          % (r03["naive"]["best_fit"], r03["bvh"]["best_fit"]))

    print("[SCE-04] serial sufficiency over %.0fs wall-clock ..." % sce04_seconds)
    r04 = sce04(sce04_seconds)
    print("         %d ticks in %.2fs -> %.1f ticks/sec  (%s, %.1fx headroom)"
          % (r04["ticks_completed"], r04["wall_seconds"], r04["ticks_per_sec"],
             "PASS" if r04["passed"] else "FAIL", r04["headroom_x"]))

    r02.pop("_live", None)
    report = {
        "profiler": "holodeck-serial SCE",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu0_pinned": pinned,
        "cpu_freq_hz": _cpu_freq_hz(),
        "mvw": "MVW(100,8,4,3,4,1)",
        "results": {"SCE-01": r01, "SCE-02": r02, "SCE-03": r03, "SCE-04": r04},
    }

    os.makedirs(_RESULTS_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = os.path.join(_RESULTS_DIR, "sce_profile_%s.json" % stamp)
    with open(out_path, "w") as fh:
        json.dump(report, fh, indent=2)
    print("=" * 64)
    print("wrote %s" % os.path.relpath(out_path, os.path.join(_HERE, "..", "..")))
    return out_path


if __name__ == "__main__":
    main()
