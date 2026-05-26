# Minimum Viable World (MVW) — Definition v0.1
## Holodeck-Serial Project | Zuup Innovation Lab

---

## Purpose

The MVW is the smallest instantiation of a holodeck that satisfies the Tier C definition:
> A deterministic, stateful, interactive simulation engine that can instantiate arbitrary
> synthetic environments from sequential instruction execution.

MVW exists to close the circular dependency across benchmarks TC-03, SCE-01, SCE-02,
SCE-03, and SCE-04, which all reference "minimum viable world complexity" without
defining it.

---

## Formal Definition

An MVW is a 6-tuple:

    MVW = (N, M, P, K, T, Φ)

Where:

| Symbol | Name              | Minimum Value | Derivation Basis                          | Confidence  |
|--------|-------------------|---------------|-------------------------------------------|-------------|
| N      | Entity count      | 100           | Sufficient for non-trivial interaction    | SPECULATIVE |
| M      | Attributes/entity | 8             | {x,y,z, vx,vy,vz, mass, type}            | VERIFIED    |
| P      | Physics rules     | 4             | Newton's 3 laws + elastic collision       | VERIFIED    |
| K      | Spatial dims      | 3             | Euclidean 3-space minimum for "world"     | VERIFIED    |
| T      | Interaction types | 4             | {move, create, destroy, query}            | PLAUSIBLE   |
| Φ      | Observer interface| 1             | Single state-query API endpoint           | VERIFIED    |

---

## Grounding Derivation

### Why N = 100? (PLAUSIBLE — empirically supported; see Q1 finding below)
100 entities is sufficient to produce emergent collision behavior without trivializing
the physics solver. The Q1 emergence experiment (`src/experiments/q1_emergence.py`)
now provides empirical support: the emergent velocity distribution becomes Gaussian
(Maxwell–Boltzmann) to within ~2% at **N ≈ 100** (finite-size excess kurtosis follows
`−6/(3N+2)`). N = 100 is therefore a reasonable, mildly conservative statistical
minimum — not arbitrary. See the density caveat below.

A first-principles derivation would require:
- A complexity model for entity interaction density
- A minimum emergence threshold (when does a simulation become non-trivial?)
- Empirical profiling on target hardware

### Why M = 8? (VERIFIED)
The 8 attributes {x, y, z, vx, vy, vz, mass, type} represent the minimal state for
a Newtonian particle in 3D space. This is derivable from Newton's equations of motion:

    F = ma  →  requires {mass, acceleration}
    x(t) = x₀ + v₀t + ½at²  →  requires {position, velocity}
    type  →  required for collision rule dispatch

No attribute can be removed without losing simulation expressiveness.

### Why P = 4? (VERIFIED)
Newton's three laws of motion plus elastic collision response constitute a closed,
consistent physics ruleset for Newtonian mechanics:

    P1: Inertia (F=0 → constant velocity)
    P2: Force-acceleration (F=ma)
    P3: Action-reaction
    P4: Elastic collision (momentum + kinetic energy conservation)

This is the minimum ruleset that produces physically coherent, non-trivial behavior.

### Why K = 3? (VERIFIED)
A holodeck is definitionally a spatial environment. K < 3 reduces to a line or plane —
insufficient for arbitrary environment instantiation. K = 3 is the minimum.

### Why T = 4? (PLAUSIBLE)
{move, create, destroy, query} is the minimal interaction vocabulary for:
- Changing world state (move, create, destroy)
- Observing world state (query)

T < 4 removes either the ability to modify or observe the world — both are required
by the Tier C definition.

---

## Density: The Missing Parameter (Q1 Finding — proposed for v0.2)

The Q1 emergence experiment surfaced a gap the original 6-tuple does not close:
**the MVW fixes the entity count N but not the spatial density** (equivalently,
the box size L or packing fraction φ). N alone does not determine whether
entities actually interact.

Empirical evidence (`results/q1_emergence_*.json`):

- At a collision-rich density (mean free path ≈ box size), N = 100 reaches the
  emergent Maxwell–Boltzmann regime, and chaotic mixing appears for all N ≥ 2.
- **But at the implementation's nominal box L = 100, MVW(100) is ~100× too
  dilute to collide**: collisions per particle ≈ 0 at N = 100 (and only ~0.09
  at N = 1000) over hundreds of ticks. The interaction graph never percolates.
  Inter-particle collisions only become significant at L = 100 for N ≈ 10⁴.

So the *binding* under-specification for emergent dynamics is **density, not N**.

**Proposed v0.2 refinement.** Promote the MVW to a 7-tuple by adding a density
parameter, specified dimensionlessly so it is resolution-independent:

```
MVW = (N, M, P, K, T, Φ, ρ)
```

where ρ is a **packing fraction** target (recommended φ ≈ 0.05–0.10, i.e.
mean free path ≲ box size). Equivalently, fix the box side L for unit-radius
particles. For N = 100 with the reference radius scale, φ ≈ 0.06 corresponds to
**L ≈ 10** (not 100) — that is the configuration in which MVW(100) exhibits the
emergent thermal behavior its claim assumes.

| Symbol | Name | Recommended | Confidence |
|--------|------|-------------|------------|
| ρ (φ)  | Packing fraction | 0.05–0.10 | PLAUSIBLE — from Q1 sweep, not yet finely calibrated |

Until v0.2 formalizes ρ, treat the nominal box as a free parameter and set it so
the mean free path does not exceed the domain.

---

## MVW Compute Cost Estimate (grounds SCE-04)

Per-tick serial compute cost for MVW(100, 8, 4, 3, 4, 1):

    State update:    N × M operations     = 100 × 8   = 800 ops/tick
    Physics eval:    N × P operations     = 100 × 4   = 400 ops/tick
    Collision check: N² / 2 comparisons   = 100² / 2  = 5,000 ops/tick (naive)
                     N log N (with BVH)   = 100 × 7   = 700 ops/tick (optimized)
    Observer query:  O(1) per query       = 1 op/query

    Total (naive):   ~6,200 ops/tick
    Total (BVH):     ~1,900 ops/tick

At 1 GHz (10⁹ ops/sec), even the naive implementation yields:
    10⁹ / 6,200 ≈ 161,290 ticks/sec  >>  60 ticks/sec threshold (SCE-04)

**SCE-04 is provisionally grounded.** A 1 GHz serial CPU is sufficient for MVW
at N=100, with >2,000× headroom. The open question is how this scales with N.

Scaling law estimate (SPECULATIVE):
    Naive:  O(N²) collision detection degrades at N ≈ 12,800 entities
    BVH:    O(N log N) degrades at N ≈ 10⁸ entities

This provides the whitepaper's empirical claim boundary.

---

## Open Research Questions (documented for whitepaper)

| ID  | Question                                          | Blocks       |
|-----|---------------------------------------------------|--------------|
| Q1  | What is the minimum N for emergent behavior?      | WSI-01, TC-03|
| Q2  | Does BVH count as "serial" under Interpretation 1?| SCE-03       |
| Q3  | Can fixed-point arithmetic preserve P4 fidelity?  | DR-01, DR-02 |
| Q4  | What is the minimum T for Turing-complete worlds? | EG-01        |

---

*MVW v0.1 — Partial closure sufficient for whitepaper grounding. Full empirical
calibration deferred to Phase 4 (hardware scaffold + profiling).*
