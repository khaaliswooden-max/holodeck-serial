"""Environmental Generation (EG) -- EG-01..04."""

import time

from _harness import timed, make
from mvw_instance import MVW


@timed
def eg_01():
    """Spec-to-world completeness: each spec (seed, N) yields a world with
    exactly N entities."""
    n_specs = 100
    incomplete = 0
    for s in range(n_specs):
        target = 50 + (s % 51)  # vary requested entity count per spec
        m = MVW(seed=s, n=target)
        if m.entity_count != target:
            incomplete += 1
    pct = 100.0 * (n_specs - incomplete) / n_specs
    return make(
        "EG-01", "Spec-to-world completeness", "%.0f%%" % pct,
        "100% / 100 specs", incomplete == 0,
        notes="%d specs instantiated to requested entity count" % n_specs,
        confidence="PLAUSIBLE")


@timed
def eg_02():
    """Generation determinism: identical (seed, spec) -> identical initial
    state hash."""
    a = MVW(seed=42, n=100)
    b = MVW(seed=42, n=100)
    equal = a.state_hash() == b.state_hash()
    return make(
        "EG-02", "Generation determinism", a.state_hash()[:16],
        "Hash-equal (seed+spec)", equal,
        notes="initial-state hash equality for identical generation inputs",
        confidence="VERIFIED")


@timed
def eg_03():
    """Generation speed: MVW(100) construction time."""
    iters = 50
    t0 = time.perf_counter()
    for _ in range(iters):
        MVW(seed=42)
    gen_s = (time.perf_counter() - t0) / iters
    return make(
        "EG-03", "Generation speed", gen_s, "<= 5 s (MVW)", gen_s <= 5.0,
        notes="mean MVW(100) construction time over %d builds" % iters,
        confidence="SPECULATIVE")


@timed
def eg_04():
    """Spec language coverage: generation succeeds across the benchmark range
    of entity counts."""
    sizes = (1, 10, 100, 1000)
    ok = all(MVW(seed=42, n=s).entity_count == s for s in sizes)
    return make(
        "EG-04", "Spec language coverage", "%d sizes" % len(sizes),
        "All benchmark envs.", ok,
        notes="generation verified for N in %s; richer spec DSL is TODO"
              % (sizes,),
        confidence="PLAUSIBLE")


def run_all():
    return [eg_01(), eg_02(), eg_03(), eg_04()]
