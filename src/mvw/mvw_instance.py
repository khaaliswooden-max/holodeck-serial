"""MVW(100, 8, 4, 3, 4, 1) -- the reference Minimum Viable World instance.

Composes the serial kernel (core/world, physics, scheduler, observer) into the
atomic unit of holodeck complexity defined in spec/MVW_Definition_v0.1.md:

    MVW = (N=100, M=8, P=4, K=3, T=4, Phi=1)

Determinism contract: MVW(seed=S) constructs a bit-identical world every run,
and a fixed (seed, input-schedule) pair produces a bit-identical final state.
The seeded RNG is consumed in a fixed field order (x,y,z,vx,vy,vz,mass,type)
per entity so the construction is reproducible.

Standard library only. Run directly:
    python src/mvw/mvw_instance.py
"""

import os
import random
import sys

# Put the serial kernel (src/core) on the path. The kernel modules import one
# another by bare name and must stay free of package machinery.
_CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from world import World, VX, VY, VZ, MASS   # noqa: E402
from scheduler import Scheduler             # noqa: E402
from observer import Observer               # noqa: E402

# --- MVW defaults. All carry epistemic markers per CLAUDE.md. ---
DEFAULT_N = 100            # SPECULATIVE -- N=100 not empirically calibrated (Q1)
DEFAULT_BOUNDS = 100.0     # PLAUSIBLE  -- domain side chosen for ~sparse packing
DEFAULT_DT = 0.01         # PLAUSIBLE  -- fixed timestep; stability not swept
VELOCITY_RANGE = 5.0       # PLAUSIBLE  -- initial speed scale
MASS_MIN, MASS_MAX = 1.0, 10.0   # VERIFIED -- arbitrary positive masses for P4
TYPE_COUNT = 3             # PLAUSIBLE  -- {0,1,2}; type drives no special rule yet


class MVW:
    """A seeded, runnable Minimum Viable World."""

    def __init__(self, seed=42, n=DEFAULT_N, bounds=DEFAULT_BOUNDS,
                 dt=DEFAULT_DT, gravity=(0.0, 0.0, 0.0), mode="naive"):
        self.seed = seed
        self.n = n
        self.bounds = bounds
        self.world = World(bounds=bounds)
        self.scheduler = Scheduler(self.world, dt=dt, gravity=gravity,
                                   mode=mode)
        self.observer = Observer(self.world)
        self._populate()

    def _populate(self):
        """Generation function G: seed -> S_0. Fixed RNG consumption order."""
        rng = random.Random(self.seed)
        L = self.bounds
        margin = 1.0  # keep initial spawns off the walls
        for _ in range(self.n):
            x = rng.uniform(margin, L - margin)
            y = rng.uniform(margin, L - margin)
            z = rng.uniform(margin, L - margin)
            vx = rng.uniform(-VELOCITY_RANGE, VELOCITY_RANGE)
            vy = rng.uniform(-VELOCITY_RANGE, VELOCITY_RANGE)
            vz = rng.uniform(-VELOCITY_RANGE, VELOCITY_RANGE)
            mass = rng.uniform(MASS_MIN, MASS_MAX)
            etype = rng.randrange(TYPE_COUNT)
            self.world.create(x, y, z, vx, vy, vz, mass, etype)

    # --- API ---

    def run(self, n_ticks, schedule=None):
        return self.scheduler.run(n_ticks, schedule)

    def query(self, eid):
        """Phi: full state of one entity (read-only)."""
        return self.observer.query(eid)

    def state_hash(self):
        return self.world.state_hash()

    @property
    def tick_count(self):
        return self.world.tick_count

    @property
    def entity_count(self):
        return self.world.entity_count

    def total_kinetic_energy(self):
        """Sum of 1/2 m v^2 -- used by PSF energy-conservation checks."""
        ke = 0.0
        for e in self.world.entities:
            v2 = e[VX] * e[VX] + e[VY] * e[VY] + e[VZ] * e[VZ]
            ke += 0.5 * e[MASS] * v2
        return ke

    def total_momentum(self):
        """Vector sum of m*v -- used by PSF momentum-conservation checks."""
        px = py = pz = 0.0
        for e in self.world.entities:
            px += e[MASS] * e[VX]
            py += e[MASS] * e[VY]
            pz += e[MASS] * e[VZ]
        return (px, py, pz)


def main():
    mvw = MVW(seed=42)
    print("MVW(100, 8, 4, 3, 4, 1) reference instance")
    print("  seed            : %d" % mvw.seed)
    print("  entity_count    : %d" % mvw.entity_count)
    print("  initial hash    : %s" % mvw.state_hash())
    ticks = 1000
    mvw.run(ticks)
    print("  ticks run       : %d" % mvw.tick_count)
    print("  final entity_count : %d" % mvw.entity_count)
    print("  final hash      : %s" % mvw.state_hash())
    sample = mvw.query(0)
    print("  observer.query(0): x=%.6f y=%.6f z=%.6f mass=%.4f type=%d"
          % (sample["x"], sample["y"], sample["z"], sample["mass"],
             sample["type"]))


if __name__ == "__main__":
    main()
