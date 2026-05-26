# Serial Baseline — 1 GHz Single-Core CPU

## holodeck-serial | Phase 4

The **serial baseline** is the reference machine for the central claim: a
single-core CPU at ≥ 1 GHz is sufficient to run MVW(100,8,4,3,4,1) at ≥ 60
ticks/sec. This note records why the baseline is defined as it is. The full
hardware requirements table is in `hardware/target_spec.md`.

---

## Definition

> **Serial baseline** = one Von Neumann core, ≥ 1 GHz, executing one instruction
> per clock cycle, with no SIMD or GPU offload at the simulation-kernel level.

This follows Interpretation 1 (`spec/holodeck_formal.md`). Parallelism is
permitted *above* the kernel but is not an architectural primitive of the claim.

---

## Why 1 GHz

The analytical per-tick cost of MVW(100) is bounded (paper §IV,
`spec/MVW_Definition_v0.1.md`):

```
naive : ~6,150 ops/tick  ->  10^9 / 6,150  ≈ 162,000 ticks/sec
BVH   : ~1,900 ops/tick  ->  10^9 / 1,900  ≈ 526,000 ticks/sec
```

At 1 GHz, even the naive model clears the 60 ticks/sec threshold by ~2,700×.
1 GHz is therefore the round-number floor at which the claim is comfortable; the
threshold would still be met well below it.

This "1 op = 1 cycle" model is an idealization. The CPython reference
implementation pays a large interpreter tax (each "op" is many bytecode
operations), yet the measured rate (`results/sce_profile_*.json`) is still
~311 ticks/sec for N=100 — ~5.2× over threshold. A compiled or lower-level
serial implementation would approach the analytical figure.

---

## Single-Core Enforcement

- The kernel (`src/core/`, `src/mvw/`) imports no `threading`, `multiprocessing`,
  or `asyncio`.
- The profiler pins the process to **CPU 0** via `os.sched_setaffinity(0, {0})`
  (Linux). On platforms without affinity control the measurement is still valid
  but single-core occupancy is not enforced by the OS.
- Determinism (TC-01, DR-01, DR-03) is independent of core count because the
  kernel never observes wall-clock time or scheduler nondeterminism.
