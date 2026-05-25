"""Newtonian physics engine (Delta) -- the state transition function.

Implements the P=4 ruleset:
    P1 Inertia            (F=0 -> constant velocity)
    P2 Force-acceleration (F=ma, applied as gravity here)
    P3 Action-reaction    (collision impulses are equal and opposite)
    P4 Elastic collision  (momentum + kinetic energy conserved, e=1)

Two broad-phase collision strategies are provided and selected via `mode`:
    "naive" -- O(N^2) all-pairs
    "bvh"   -- O(N log N) median-split bounding-volume hierarchy

Both feed an identical narrow phase, so they produce bit-identical results;
only the cost differs. This is what lets SCE-03 profile the scaling law while
DR-01/DR-03 still hold regardless of mode.

Standard library only. No numpy, no threading.
"""

import math

from world import X, Y, Z, VX, VY, VZ, MASS, RADIUS, ID

# Elastic restitution coefficient.
# VERIFIED -- e=1 is the definition of a perfectly elastic collision.
RESTITUTION = 1.0


def integrate(entities, dt, gravity, bounds):
    """P1+P2: semi-implicit (symplectic) Euler integration with elastic walls.

    Walls at the [0, bounds]^3 faces reflect the normal velocity component,
    which conserves kinetic energy (no energy injected/removed at boundaries).
    """
    gx, gy, gz = gravity
    L = bounds
    for e in entities:
        # P2: a = F/m; here the only body force is uniform gravity, so a=g.
        e[VX] += gx * dt
        e[VY] += gy * dt
        e[VZ] += gz * dt
        # P1: position advances by velocity.
        e[X] += e[VX] * dt
        e[Y] += e[VY] * dt
        e[Z] += e[VZ] * dt
        # Elastic wall reflection (energy-conserving).
        r = e[RADIUS]
        for axis_pos, axis_vel in ((X, VX), (Y, VY), (Z, VZ)):
            p = e[axis_pos]
            lo, hi = r, L - r
            if p < lo:
                e[axis_pos] = 2.0 * lo - p
                e[axis_vel] = -e[axis_vel]
            elif p > hi:
                e[axis_pos] = 2.0 * hi - p
                e[axis_vel] = -e[axis_vel]


def _candidate_pairs_naive(entities):
    """O(N^2) broad phase: every unordered pair."""
    n = len(entities)
    for i in range(n):
        for j in range(i + 1, n):
            yield entities[i], entities[j]


# --- BVH (median-split AABB tree) broad phase ---

class _Node:
    __slots__ = ("lo", "hi", "left", "right", "entity")

    def __init__(self, lo, hi, left=None, right=None, entity=None):
        self.lo = lo          # (minx, miny, minz) of the AABB
        self.hi = hi          # (maxx, maxy, maxz) of the AABB
        self.left = left
        self.right = right
        self.entity = entity  # set on leaves


def _entity_aabb(e):
    r = e[RADIUS]
    return ((e[X] - r, e[Y] - r, e[Z] - r),
            (e[X] + r, e[Y] + r, e[Z] + r))


def _build_bvh(items):
    """Recursively build an AABB tree by splitting on the longest axis at the
    median centroid. `items` is a list of (entity, lo, hi). O(N log N)."""
    if len(items) == 1:
        e, lo, hi = items[0]
        return _Node(lo, hi, entity=e)

    # Enclosing box.
    lo = [min(it[1][k] for it in items) for k in range(3)]
    hi = [max(it[2][k] for it in items) for k in range(3)]
    # Longest axis.
    axis = max(range(3), key=lambda k: hi[k] - lo[k])
    # Deterministic order: sort by centroid on axis, tie-break by entity id.
    items.sort(key=lambda it: ((it[1][axis] + it[2][axis]) * 0.5, it[0][ID]))
    mid = len(items) // 2
    left = _build_bvh(items[:mid])
    right = _build_bvh(items[mid:])
    return _Node(tuple(lo), tuple(hi), left=left, right=right)


def _aabb_overlap(lo1, hi1, lo2, hi2):
    return (lo1[0] <= hi2[0] and hi1[0] >= lo2[0] and
            lo1[1] <= hi2[1] and hi1[1] >= lo2[1] and
            lo1[2] <= hi2[2] and hi1[2] >= lo2[2])


def _query_bvh(node, lo, hi, eid, out):
    """Collect entities whose AABB overlaps [lo,hi] and whose id > eid (to
    emit each unordered pair exactly once)."""
    if node is None:
        return
    if not _aabb_overlap(lo, hi, node.lo, node.hi):
        return
    if node.entity is not None:
        if node.entity[ID] > eid:
            out.append(node.entity)
        return
    _query_bvh(node.left, lo, hi, eid, out)
    _query_bvh(node.right, lo, hi, eid, out)


def _candidate_pairs_bvh(entities):
    """O(N log N) broad phase via BVH self-query.

    The tree is constructed single-threaded (median split). See Open Question
    Q2 on whether BVH counts as 'serial' under Interpretation 1; as implemented
    here it is."""
    if len(entities) < 2:
        return
    items = [(e,) + _entity_aabb(e) for e in entities]
    root = _build_bvh(items)
    for e in entities:
        lo, hi = _entity_aabb(e)
        out = []
        _query_bvh(root, lo, hi, e[ID], out)
        for other in out:
            yield e, other


def _resolve_collision(a, b):
    """P3+P4: resolve a sphere-sphere collision with an equal/opposite impulse.

    Narrow phase: exact center distance vs. summed radii. Returns True if the
    pair was actually in contact and closing."""
    dx = b[X] - a[X]
    dy = b[Y] - a[Y]
    dz = b[Z] - a[Z]
    dist_sq = dx * dx + dy * dy + dz * dz
    rsum = a[RADIUS] + b[RADIUS]
    if dist_sq >= rsum * rsum or dist_sq == 0.0:
        return False

    dist = math.sqrt(dist_sq)
    # Unit normal from a -> b.
    nx, ny, nz = dx / dist, dy / dist, dz / dist
    # Relative velocity of a with respect to b.
    rvx = a[VX] - b[VX]
    rvy = a[VY] - b[VY]
    rvz = a[VZ] - b[VZ]
    vn = rvx * nx + rvy * ny + rvz * nz
    if vn <= 0.0:
        return False  # separating or parallel; no impulse (avoids sticking)

    inv_ma = 1.0 / a[MASS]
    inv_mb = 1.0 / b[MASS]
    # Impulse scalar for restitution e: J = (1+e) * vn / (1/ma + 1/mb).
    j = (1.0 + RESTITUTION) * vn / (inv_ma + inv_mb)
    a[VX] -= j * inv_ma * nx
    a[VY] -= j * inv_ma * ny
    a[VZ] -= j * inv_ma * nz
    b[VX] += j * inv_mb * nx
    b[VY] += j * inv_mb * ny
    b[VZ] += j * inv_mb * nz

    # Positional de-overlap split by inverse mass. Velocity untouched, so this
    # does not affect momentum or kinetic energy conservation.
    penetration = rsum - dist
    corr = penetration / (inv_ma + inv_mb)
    a[X] -= corr * inv_ma * nx
    a[Y] -= corr * inv_ma * ny
    a[Z] -= corr * inv_ma * nz
    b[X] += corr * inv_mb * nx
    b[Y] += corr * inv_mb * ny
    b[Z] += corr * inv_mb * nz
    return True


def resolve_collisions(entities, mode="naive"):
    """P4: detect and resolve all elastic collisions for one tick.

    Returns the number of collisions resolved. Pairs are gathered, then sorted
    by (id_a, id_b) and resolved in that fixed order for determinism."""
    if mode == "bvh":
        pairs = _candidate_pairs_bvh(entities)
    elif mode == "naive":
        pairs = _candidate_pairs_naive(entities)
    else:
        raise ValueError("mode must be 'naive' or 'bvh', got %r" % (mode,))

    # Normalize each pair to (lower-id, higher-id) and sort for determinism.
    ordered = []
    for a, b in pairs:
        if a[ID] <= b[ID]:
            ordered.append((a[ID], b[ID], a, b))
        else:
            ordered.append((b[ID], a[ID], b, a))
    ordered.sort(key=lambda t: (t[0], t[1]))

    resolved = 0
    for _, _, a, b in ordered:
        if _resolve_collision(a, b):
            resolved += 1
    return resolved
