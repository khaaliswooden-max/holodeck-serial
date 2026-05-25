"""Serial tick scheduler (I) -- the single-threaded simulation loop.

Each tick: (1) apply queued input events in their given order, (2) integrate
motion, (3) resolve collisions. Strictly sequential; one tick fully completes
before the next begins. No threading/async -- this is the architectural claim,
not an optimization.

Input events are tuples whose first element is one of the T=4 interaction
types: 'create', 'destroy', 'move', 'query'. Query events are answered and
their results returned from `tick`, satisfying causal ordering (TC-02): a query
observes the state at the moment it is processed within the tick.
"""

from world import World
import physics


class Scheduler:
    def __init__(self, world=None, dt=0.01, gravity=(0.0, 0.0, 0.0),
                 mode="naive"):
        # dt: fixed timestep. Fixed (not wall-clock-derived) for determinism.
        self.world = world if world is not None else World()
        self.dt = float(dt)
        self.gravity = (float(gravity[0]), float(gravity[1]), float(gravity[2]))
        self.mode = mode
        self.last_collisions = 0

    def _apply_event(self, ev):
        kind = ev[0]
        w = self.world
        if kind == "move":
            _, eid, dx, dy, dz = ev
            w.move(eid, dx, dy, dz)
            return None
        if kind == "create":
            _, x, y, z, vx, vy, vz, mass, etype = ev
            return w.create(x, y, z, vx, vy, vz, mass, etype)
        if kind == "destroy":
            _, eid = ev
            return w.destroy(eid)
        if kind == "query":
            _, eid = ev
            e = w.query(eid)
            return None if e is None else list(e)
        raise ValueError("unknown event type: %r" % (kind,))

    def tick(self, events=None):
        """Advance the simulation by exactly one tick.

        Returns the list of results for any query events (in event order)."""
        query_results = []
        if events:
            for ev in events:
                res = self._apply_event(ev)
                if ev[0] == "query":
                    query_results.append(res)
        physics.integrate(self.world.entities, self.dt, self.gravity,
                           self.world.bounds)
        self.last_collisions = physics.resolve_collisions(
            self.world.entities, mode=self.mode)
        self.world.tick_count += 1
        return query_results

    def run(self, n_ticks, schedule=None):
        """Run n_ticks. `schedule` optionally maps tick-index -> event list."""
        for t in range(n_ticks):
            events = schedule.get(t) if schedule else None
            self.tick(events)
        return self.world.tick_count
