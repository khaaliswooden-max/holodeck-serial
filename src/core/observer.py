"""Observer interface (Phi) -- the single external state-query endpoint.

This is the mechanism by which a system outside the simulation reads world
state, resolving the "closed system with no exit" integrity failure (gap
analysis Attack 5). Reads are pure: querying never mutates the world, and the
same state always yields the same answer (OI-02).
"""

import hashlib
import json

from world import (ID, X, Y, Z, VX, VY, VZ, MASS, TYPE, RADIUS)

_FIELD_NAMES = ("id", "x", "y", "z", "vx", "vy", "vz", "mass", "type", "radius")


class Observer:
    """Read-only view over a World. The Phi=1 endpoint."""

    def __init__(self, world):
        self.world = world

    def query(self, eid):
        """Return a full entity-state dict, or None if the id is absent.

        Returns a copy so callers cannot mutate world state through the
        observer (read purity)."""
        e = self.world.query(eid)
        if e is None:
            return None
        return dict(zip(_FIELD_NAMES, (
            e[ID], e[X], e[Y], e[Z], e[VX], e[VY], e[VZ],
            e[MASS], e[TYPE], e[RADIUS])))

    def all_ids(self):
        return [e[ID] for e in self.world.entities]

    def snapshot(self):
        """Full ordered world state as a list of entity dicts."""
        return [self.query(e[ID]) for e in self.world.entities]

    def query_hash(self, eid):
        """Deterministic digest of a single query result (OI-02)."""
        payload = json.dumps(self.query(eid), sort_keys=True,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # --- Scene-graph export (OI-03). Lossless == round-trippable to dicts. ---

    def export(self, fmt="json"):
        snap = self.snapshot()
        if fmt == "json":
            return json.dumps(snap, sort_keys=True, separators=(",", ":"))
        if fmt == "dict":
            return snap
        if fmt == "csv":
            lines = [",".join(_FIELD_NAMES)]
            for row in snap:
                lines.append(",".join(repr(row[f]) for f in _FIELD_NAMES))
            return "\n".join(lines)
        raise ValueError("unsupported export format: %r" % (fmt,))
