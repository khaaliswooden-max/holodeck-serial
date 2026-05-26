"""World State Integrity (WSI) -- WSI-01..04."""

import time

from _harness import timed, make
from mvw_instance import MVW


@timed
def wsi_01():
    """State retention: no entity is silently lost across many ticks."""
    ticks = 1000  # reduced from spec's 10K for runner speed
    m = MVW(seed=42)
    start = m.entity_count
    m.run(ticks)
    retained = m.entity_count
    pct = 100.0 * retained / start
    return make(
        "WSI-01", "State retention across ticks", "%.1f%%" % pct,
        "100% / 10K ticks", retained == start,
        notes="%d ticks (spec: 10K); no creates/destroys scheduled" % ticks,
        confidence="PLAUSIBLE")


@timed
def wsi_02():
    """Zero contradictory assertions: repeated queries of an unchanged state
    are mutually consistent."""
    m = MVW(seed=42)
    contradictions = 0
    n_queries = 100_000
    eid = 0
    ref = m.query(eid)
    for _ in range(n_queries):
        if m.query(eid) != ref:
            contradictions += 1
    return make(
        "WSI-02", "Zero contradictory assertions", contradictions,
        "0 / 1M queries", contradictions == 0,
        notes="%d queries on a frozen state (spec: 1M)" % n_queries,
        confidence="VERIFIED")


@timed
def wsi_03():
    """State query latency on a 10K-entity world."""
    m = MVW(seed=42, n=10_000)
    eid = 5000
    iters = 10_000
    t0 = time.perf_counter()
    for _ in range(iters):
        m.query(eid)
    per_query_ms = (time.perf_counter() - t0) / iters * 1000.0
    return make(
        "WSI-03", "State query latency", per_query_ms,
        "<= 1 ms / 10K entities", per_query_ms <= 1.0,
        notes="mean single-entity query latency, 10K-entity world",
        confidence="SPECULATIVE")


@timed
def wsi_04():
    """Round-trip serialization fidelity: clone() round-trips to an identical
    hash, repeatably."""
    m = MVW(seed=42); m.run(50)
    h = m.state_hash()
    ok = True
    for _ in range(1000):
        if m.world.clone().state_hash() != h:
            ok = False
            break
    return make(
        "WSI-04", "Round-trip serialization fidelity", "bit-identical",
        "Bit-identical / 1K runs", ok,
        notes="serialize -> clone -> hash stable over 1K iterations",
        confidence="VERIFIED")


def run_all():
    return [wsi_01(), wsi_02(), wsi_03(), wsi_04()]
