"""Determinism & Reproducibility (DR) -- DR-01, DR-02, DR-03. All real."""

import math

from _harness import timed, make
from mvw_instance import MVW


@timed
def dr_01():
    """Cross-platform reproducibility (within-platform proxy)."""
    a = MVW(seed=42); a.run(300)
    b = MVW(seed=42); b.run(300)
    equal = a.state_hash() == b.state_hash()
    return make(
        "DR-01", "Cross-platform reproducibility", a.state_hash()[:16],
        "Hash-equal (same impl.)", equal,
        notes=("same-platform identity verified; true cross-arch (x86/ARM/RISC-V) "
               "matrix is in hardware/target_spec.md (Q3)"),
        confidence="PLAUSIBLE")


@timed
def dr_02():
    """Floating-point stability: max per-tick positional divergence between two
    identical runs. Bit-identical execution => exactly 0.0."""
    a = MVW(seed=7); b = MVW(seed=7)
    from world import X, Y, Z
    max_div = 0.0
    for _ in range(300):
        a.scheduler.tick(); b.scheduler.tick()
        for ea, eb in zip(a.world.entities, b.world.entities):
            d = math.sqrt((ea[X] - eb[X]) ** 2 + (ea[Y] - eb[Y]) ** 2
                          + (ea[Z] - eb[Z]) ** 2)
            if d > max_div:
                max_div = d
    return make(
        "DR-02", "Floating point stability", max_div,
        "<= 1e-9 divergence/tick", max_div <= 1e-9,
        notes="divergence between two same-seed runs over 300 ticks",
        confidence="PLAUSIBLE")


@timed
def dr_03():
    """Seed-based replayability: identical (seed + input schedule) reproduces
    the final state hash exactly."""
    schedule = {
        10: [("create", 5.0, 5.0, 5.0, 1.0, 0.0, 0.0, 3.0, 1)],
        20: [("move", 0, 1.0, -1.0, 0.5)],
        40: [("destroy", 1)],
    }
    h1 = MVW(seed=123); h1.run(100, schedule=schedule)
    h2 = MVW(seed=123); h2.run(100, schedule=schedule)
    equal = h1.state_hash() == h2.state_hash()
    return make(
        "DR-03", "Seed-based replayability", h1.state_hash()[:16],
        "Full replay from seed+log", equal,
        notes="replayed create/move/destroy schedule reproduces final hash",
        confidence="VERIFIED")


def run_all():
    return [dr_01(), dr_02(), dr_03()]
