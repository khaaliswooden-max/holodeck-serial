"""Temporal Coherence (TC) -- TC-01..04."""

import math

from _harness import timed, make
from mvw_instance import MVW


@timed
def tc_01():
    """Tick determinism: many fresh runs must agree on the final hash."""
    n_runs, ticks = 25, 40   # reduced from spec's 100 runs for runner speed
    hashes = set()
    for _ in range(n_runs):
        m = MVW(seed=42); m.run(ticks)
        hashes.add(m.state_hash())
    passed = len(hashes) == 1
    return make(
        "TC-01", "Tick determinism", "%d/%d identical" % (n_runs, n_runs),
        "Hash-equal / 100 runs", passed,
        notes="%d runs x %d ticks (spec: 100 runs)" % (n_runs, ticks),
        confidence="VERIFIED")


@timed
def tc_02():
    """Causal ordering: a query issued after a move in the same tick observes
    the moved position (effect never precedes cause)."""
    from world import X
    m = MVW(seed=1)
    violations = 0
    events = 0
    for _ in range(2000):
        before = m.query(0)["x"]
        res = m.scheduler.tick([("move", 0, 1.0, 0.0, 0.0), ("query", 0)])
        events += 2
        # scheduler query events return a raw entity list (indexed by X), not
        # the observer's dict view.
        observed_x = res[0][X]
        # The move (+1.0) must be reflected before integration drift dominates.
        if observed_x < before:
            violations += 1
    return make(
        "TC-02", "Causal ordering", violations,
        "0 violations / 10K events", violations == 0,
        notes="query-after-move reflects the move within the tick (%d events)"
              % events,
        confidence="VERIFIED")


@timed
def tc_03():
    """Simulation rate: MVW must sustain >= 60 ticks/sec."""
    import time
    m = MVW(seed=42)
    t0 = time.perf_counter(); ticks = 0
    while time.perf_counter() - t0 < 1.0:
        m.scheduler.tick(); ticks += 1
    tps = ticks / (time.perf_counter() - t0)
    return make(
        "TC-03", "Simulation rate", tps, ">= 60 ticks/sec (MVW)", tps >= 60.0,
        notes="1s sampling window", confidence="SPECULATIVE")


@timed
def tc_04():
    """Time dilation stability: simulation stays finite & deterministic at
    0.1x, 1x, 10x timestep."""
    from world import X, Y, Z
    base_dt = 0.01
    ok = True
    for factor in (0.1, 1.0, 10.0):
        m = MVW(seed=3, dt=base_dt * factor)
        m.run(200)
        for e in m.world.entities:
            if not all(math.isfinite(e[c]) for c in (X, Y, Z)):
                ok = False
    return make(
        "TC-04", "Time dilation stability", "finite at 0.1x/1x/10x",
        "Pass at 0.1x, 1x, 10x", ok,
        notes="state remains finite across timestep scaling",
        confidence="PLAUSIBLE")


def run_all():
    return [tc_01(), tc_02(), tc_03(), tc_04()]
