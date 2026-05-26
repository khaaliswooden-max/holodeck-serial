"""World state manager (S) for the Tier C holodeck.

Holds the canonical, ordered, queryable world state. Pure Python standard
library only -- this module is part of the simulation kernel and must never
import numpy, scipy, threading, multiprocessing, or asyncio.

Entity layout is a flat list indexed by the module-level constants below rather
than a class with attributes. This is a deliberate performance choice for the
serial kernel: list indexing is measurably faster than attribute access in
CPython, and the SCE scaling benchmarks push N to 5000.  # PLAUSIBLE -- list
vs __slots__ gap not formally micro-benchmarked here, but list indexing is the
conventional faster path in CPython.

The M=8 simulation attributes are {x, y, z, vx, vy, vz, mass, type}. `id` is
identity (not one of the 8 attributes) and `radius` is a derived quantity
cached for collision detection.
"""

import hashlib
import struct

# --- Entity field indices (Entity is a flat list) ---
ID, X, Y, Z, VX, VY, VZ, MASS, TYPE, RADIUS = range(10)
ENTITY_WIDTH = 10

# Derived-radius scale: r = BASE_RADIUS * mass ** (1/3).
# VERIFIED -- volume-proportional radius for uniform-density spheres (r ~ m^(1/3)).
BASE_RADIUS = 0.5


def make_entity(eid, x, y, z, vx, vy, vz, mass, etype):
    """Construct an entity list with a derived collision radius."""
    radius = BASE_RADIUS * (mass ** (1.0 / 3.0))
    return [eid, x, y, z, vx, vy, vz, mass, etype, radius]


class World:
    """Ordered container of entities over a cubic spatial domain [0, L]^3.

    Iteration order is insertion order and is stable across runs given an
    identical construction sequence -- this is load-bearing for determinism.
    """

    def __init__(self, bounds=100.0):
        self.bounds = float(bounds)        # cube side length L (K=3 dims)
        self.entities = []                 # ordered list of entity lists
        self._by_id = {}                   # id -> entity list (O(1) query)
        self._next_id = 0
        self.tick_count = 0

    # --- T=4 interaction primitives: create, destroy, move, query ---

    def create(self, x, y, z, vx, vy, vz, mass, etype):
        """T:create -- add an entity, return its assigned id."""
        eid = self._next_id
        self._next_id += 1
        e = make_entity(eid, x, y, z, vx, vy, vz, mass, etype)
        self.entities.append(e)
        self._by_id[eid] = e
        return eid

    def destroy(self, eid):
        """T:destroy -- remove an entity by id. Returns True if removed."""
        e = self._by_id.pop(eid, None)
        if e is None:
            return False
        # Linear removal preserves order; acceptable for the MVW scale.
        self.entities.remove(e)
        return True

    def move(self, eid, dx, dy, dz):
        """T:move -- translate an entity's position by a delta."""
        e = self._by_id.get(eid)
        if e is None:
            return False
        e[X] += dx
        e[Y] += dy
        e[Z] += dz
        return True

    def query(self, eid):
        """T:query -- return the live entity list, or None. See observer.py
        for the read-only external-facing view."""
        return self._by_id.get(eid)

    @property
    def entity_count(self):
        return len(self.entities)

    # --- Serialization / hashing (WSI-04, OI-02, DR domain) ---

    def serialize(self):
        """Canonical, bit-exact byte encoding of full world state.

        Encodes each entity in insertion order as little-endian fixed-width
        fields. Uses raw IEEE-754 doubles (not repr) so the hash captures the
        exact bit pattern of every float -- required for WSI-04 / DR-03.
        """
        buf = bytearray()
        buf += struct.pack("<dI", self.bounds, self.tick_count)
        buf += struct.pack("<I", len(self.entities))
        for e in self.entities:
            # id, type as ints; the six kinematics + mass + radius as doubles.
            buf += struct.pack(
                "<iI7d",
                e[ID], e[TYPE],
                e[X], e[Y], e[Z], e[VX], e[VY], e[VZ], e[MASS],
            )
        return bytes(buf)

    def state_hash(self):
        """SHA-256 hex digest of the canonical serialization."""
        return hashlib.sha256(self.serialize()).hexdigest()

    def clone(self):
        """Deep-ish copy sufficient for replay/branching (entities are flat
        lists of immutables)."""
        w = World(self.bounds)
        w._next_id = self._next_id
        w.tick_count = self.tick_count
        for e in self.entities:
            ce = list(e)
            w.entities.append(ce)
            w._by_id[ce[ID]] = ce
        return w
