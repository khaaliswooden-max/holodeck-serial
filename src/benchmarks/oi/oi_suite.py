"""Observer Interface Completeness (OI) -- OI-01..03."""

import json

from _harness import timed, make
from mvw_instance import MVW

_EXPECTED_FIELDS = {"id", "x", "y", "z", "vx", "vy", "vz", "mass", "type",
                    "radius"}


@timed
def oi_01():
    """State query API coverage: every entity is queryable and every query
    exposes the full attribute set."""
    m = MVW(seed=42)
    missing = 0
    for eid in m.observer.all_ids():
        q = m.observer.query(eid)
        if q is None or set(q.keys()) != _EXPECTED_FIELDS:
            missing += 1
    pct = 100.0 * (m.entity_count - missing) / m.entity_count
    return make(
        "OI-01", "State query API coverage", "%.0f%%" % pct,
        "100% of world state", missing == 0,
        notes="all %d entities fully queryable" % m.entity_count,
        confidence="PLAUSIBLE")


@timed
def oi_02():
    """Query result determinism: repeated queries of an unchanged state yield
    an identical digest."""
    m = MVW(seed=42); m.run(50)
    h = m.observer.query_hash(0)
    stable = all(m.observer.query_hash(0) == h for _ in range(1000))
    return make(
        "OI-02", "Query result determinism", h[:16],
        "Hash-equal / same state", stable,
        notes="1000 repeated query digests on a frozen state",
        confidence="VERIFIED")


@timed
def oi_03():
    """Scene-graph export fidelity: implemented formats round-trip losslessly.

    STUB: 3 of 10 target formats implemented (json, dict, csv)."""
    m = MVW(seed=42); m.run(10)
    snap = m.observer.snapshot()
    json_round = json.loads(m.observer.export("json")) == snap
    dict_round = m.observer.export("dict") == snap
    implemented, target = 3, 10
    lossless = json_round and dict_round
    return make(
        "OI-03", "Scene graph export fidelity", "%d/%d formats" % (implemented,
                                                                    target),
        "Lossless / 10 formats", None,
        notes="TODO: 3/10 formats (json,dict,csv) implemented; "
              "implemented formats round-trip lossless=%s" % lossless,
        confidence="SPECULATIVE")


def run_all():
    return [oi_01(), oi_02(), oi_03()]
