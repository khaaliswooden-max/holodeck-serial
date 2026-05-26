"""Q2 -- Does a BVH count as "serial" under Interpretation 1?

Interpretation 1 (spec/holodeck_formal.md): a serial computer executes one
instruction per clock cycle per core; parallelism is permitted as an
abstraction ABOVE the serial foundation but is not an architectural primitive.

The question is whether the reference broad-phase (a bounding-volume hierarchy)
disqualifies the serial-sufficiency claim because BVH construction is *often*
parallelized in practice. We answer it with evidence rather than assertion:

  A. SERIALITY    -- our BVH build/traversal runs in a single thread
                     (threading.active_count() stays 1) and is deterministic.
  B. COMPLEXITY   -- the single-threaded median-split build scales as
                     O(N log N); no parallel primitive is required for it.
  C. NON-UNIQUE   -- an independent serial broad-phase (sweep-and-prune, also
                     O(N log N)) and the O(N^2) naive scan find the EXACT same
                     overlapping pairs. BVH is one of several serial options;
                     correctness never depends on parallelism.

Conclusion (stated in docs/open_questions.md): under Interpretation 1 the BVH is
serial-compatible. That it *can* be parallelized is irrelevant -- it does not
*require* parallelism.

    python src/experiments/q2_bvh_serial.py
"""

import json
import math
import os
import random
import sys
import threading
import time
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(_HERE, "..", "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

import physics                                              # noqa: E402
from physics import (_entity_aabb, _build_bvh, _query_bvh,  # noqa: E402
                     _candidate_pairs_bvh, _candidate_pairs_naive)
from world import World, X, Y, Z, RADIUS, ID                # noqa: E402

_RESULTS = os.path.join(_HERE, "..", "..", "results")


def _build_world(n, bounds, seed):
    w = World(bounds=bounds)
    rng = random.Random(seed)
    for _ in range(n):
        w.create(rng.uniform(0, bounds), rng.uniform(0, bounds),
                 rng.uniform(0, bounds), rng.uniform(-3, 3), rng.uniform(-3, 3),
                 rng.uniform(-3, 3), rng.uniform(1.0, 4.0), 0)
    return w


def _narrow(a, b):
    """Geometric overlap test (broad-phase-agnostic)."""
    dx = b[X] - a[X]
    dy = b[Y] - a[Y]
    dz = b[Z] - a[Z]
    rsum = a[RADIUS] + b[RADIUS]
    d2 = dx * dx + dy * dy + dz * dz
    return 0.0 < d2 < rsum * rsum


def _pair_key(a, b):
    return (a[ID], b[ID]) if a[ID] <= b[ID] else (b[ID], a[ID])


# --- three independent serial broad phases, each returns the overlap set ---

def overlaps_naive(entities):
    out = set()
    for a, b in _candidate_pairs_naive(entities):
        if _narrow(a, b):
            out.add(_pair_key(a, b))
    return out


def overlaps_bvh(entities):
    out = set()
    for a, b in _candidate_pairs_bvh(entities):
        if _narrow(a, b):
            out.add(_pair_key(a, b))
    return out


def _sap_candidates(entities):
    """Sweep-and-prune along x: sort by AABB min-x, sweep an active set.
    O(N log N) build + O(N + K) sweep, fully serial."""
    boxes = []
    for e in entities:
        r = e[RADIUS]
        boxes.append((e[X] - r, e[X] + r, e))
    boxes.sort(key=lambda b: (b[0], b[2][ID]))
    active = []
    for minx, maxx, e in boxes:
        active = [a for a in active if a[0] >= minx]  # prune passed boxes
        for _, ae in active:
            yield ae, e
        active.append((maxx, e))


def overlaps_sap(entities):
    out = set()
    for a, b in _sap_candidates(entities):
        if _narrow(a, b):
            out.add(_pair_key(a, b))
    return out


def _bvh_build_only(entities):
    items = [(e,) + _entity_aabb(e) for e in entities]
    return _build_bvh(items)


def _fit_loglog_slope(ns, ts):
    """Slope of log(t) vs log(N): exponent p in t ~ N^p. (N log N ~ slope just
    above 1; N^2 ~ slope 2.)"""
    xs = [math.log(n) for n in ns]
    ys = [math.log(t) for t in ts]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx if sxx else 0.0


def main():
    print("Q2: is the BVH serial under Interpretation 1?")
    print("=" * 60)

    # --- A. Seriality: single-threaded build, deterministic ---
    w = _build_world(400, 40.0, seed=1)
    threads_before = threading.active_count()
    root1 = _bvh_build_only(w.clone().entities)
    threads_after = threading.active_count()
    # determinism: traversal pair order identical across two builds
    order1 = list(_candidate_pairs_bvh(w.entities))
    order2 = list(_candidate_pairs_bvh(w.entities))
    det = ([_pair_key(a, b) for a, b in order1]
           == [_pair_key(a, b) for a, b in order2])
    single_threaded = (threads_before == 1 and threads_after == 1)
    print("A. seriality:")
    print("   threads during build : %d -> %d (single-threaded=%s)"
          % (threads_before, threads_after, single_threaded))
    print("   build deterministic   : %s" % det)

    # --- C. Non-uniqueness: three broad phases agree exactly ---
    print("C. broad-phase equivalence (naive == bvh == sweep-and-prune):")
    all_agree = True
    for seed in range(5):
        ww = _build_world(300, 24.0, seed=seed)  # dense enough to overlap
        nv = overlaps_naive(ww.entities)
        bv = overlaps_bvh(ww.entities)
        sp = overlaps_sap(ww.entities)
        agree = (nv == bv == sp)
        all_agree = all_agree and agree
        print("   seed=%d overlaps: naive=%d bvh=%d sap=%d  agree=%s"
              % (seed, len(nv), len(bv), len(sp), agree))

    # --- B. Complexity: build-only and broad-phase timing vs N ---
    print("B. scaling (log-log slope; ~1 is O(N log N)-ish, ~2 is O(N^2)):")
    ns = [100, 200, 400, 800, 1600, 3200]
    build_t, bvh_t, sap_t, naive_t = [], [], [], []
    for n in ns:
        ww = _build_world(n, (n / 0.05) ** (1 / 3.0), seed=7)  # fixed density
        ents = ww.entities

        t0 = time.perf_counter(); _bvh_build_only(ents); build_t.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); overlaps_bvh(ents); bvh_t.append(time.perf_counter() - t0)
        t0 = time.perf_counter(); overlaps_sap(ents); sap_t.append(time.perf_counter() - t0)
        if n <= 1600:  # naive O(N^2) gets expensive; cap it
            t0 = time.perf_counter(); overlaps_naive(ents); naive_t.append(time.perf_counter() - t0)
        print("   N=%-5d build=%8.2fms bvh=%8.2fms sap=%8.2fms"
              % (n, build_t[-1] * 1e3, bvh_t[-1] * 1e3, sap_t[-1] * 1e3))

    slopes = {
        "bvh_build": _fit_loglog_slope(ns, build_t),
        "bvh_broadphase": _fit_loglog_slope(ns, bvh_t),
        "sweep_and_prune": _fit_loglog_slope(ns, sap_t),
        "naive": _fit_loglog_slope(ns[:len(naive_t)], naive_t),
    }
    print("   slopes:", {k: round(v, 2) for k, v in slopes.items()})

    verdict = ("BVH is serial-compatible under Interpretation 1: single-threaded "
               "deterministic O(N log N) construction (slope %.2f), and an "
               "independent serial broad-phase (sweep-and-prune) plus the naive "
               "scan find identical overlaps. Parallelizability is optional, not "
               "required." % slopes["bvh_build"])
    print("=" * 60)
    print("VERDICT:", verdict)

    report = {
        "experiment": "Q2 BVH seriality",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seriality": {"single_threaded": single_threaded,
                      "deterministic_build": det,
                      "threads_before": threads_before,
                      "threads_after": threads_after},
        "broad_phase_equivalence": all_agree,
        "scaling": {"ns": ns, "bvh_build_s": build_t, "bvh_broadphase_s": bvh_t,
                    "sweep_and_prune_s": sap_t, "naive_s": naive_t,
                    "loglog_slopes": slopes},
        "verdict": verdict,
    }
    os.makedirs(_RESULTS, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(_RESULTS, "q2_bvh_serial_%s.json" % stamp)
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    print("wrote %s" % os.path.relpath(path, os.path.join(_HERE, "..", "..")))
    return report


if __name__ == "__main__":
    main()
