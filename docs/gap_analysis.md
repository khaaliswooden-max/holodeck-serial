# Gap Analysis — Adversarial Integrity Attack

## holodeck-serial | Phase 2 artifact

We applied adversarial review to the benchmark framework itself, identifying five
classes of integrity failure. This document records the attack, the resolution
status, and the residual gap. It is the prose source for
`paper/holodeck_serial_IEEE_Paper.tex` Section V.

**Net assessment: 3 of 5 fully resolved, 1 partially resolved, 1 deferred.**

---

## Attack 1 — Circular Dependency — RESOLVED

Six benchmarks (TC-03, SCE-01 through SCE-04) referenced "minimum viable world
complexity" without ever defining it. The benchmarks were mutually circular.

**Resolution:** The MVW 6-tuple (`spec/MVW_Definition_v0.1.md`) defines the
complexity unit explicitly: MVW = (N=100, M=8, P=4, K=3, T=4, Φ=1).

**Residual gap:** The N = 100 threshold is analytically motivated but not
empirically calibrated → Open Question Q1.

---

## Attack 2 — Undecidable Benchmark — RESOLVED

PSF-04 originally required "no undefined behavior" across all interactions — a
formally undecidable property for open environments (halting-problem reduction).

**Resolution:** Replaced with a *closed interaction matrix coverage* requirement.
The matrix is defined at system initialization; coverage is finite and
measurable.

---

## Attack 3 — Threshold Arbitrariness — PARTIALLY RESOLVED

Thresholds marked SPECULATIVE (WSI-03, TC-03, SCE-01, SCE-02, EG-03) lack
empirical calibration.

**Resolution:** SCE-04 receives analytical grounding via the MVW compute-cost
model. The remaining SPECULATIVE thresholds are documented as open calibration
tasks, to be advanced by the profiler (`src/mvw/mvw_profiler.py`) and the
empirical validation plan in `hardware/target_spec.md`.

**Residual gap:** Until the profiler results are reproduced on the serial
baseline hardware, these remain SPECULATIVE.

---

## Attack 4 — Floating Point Non-Determinism — DEFERRED

DR-01 cross-platform determinism is non-trivial. IEEE-754 behavior varies across
compiler optimizations and CPU architectures.

**Resolution:** Deferred to implementation phase as Open Question Q3. The
architectural decision between fixed-point arithmetic and scoped IEEE-754
compliance is explicit, not hidden. The reference kernel achieves bit-identical
results within a platform; cross-platform parity is an empirical open item.

---

## Attack 5 — Missing Observer Domain — RESOLVED

The original seven domains constituted a formally closed system with no external
verification mechanism — a simulation with no exit.

**Resolution:** Domain 8 (Observer Interface, OI-01..03) was added. The observer
interface (`src/core/observer.py`) is the mechanism by which an external system
queries world state, making the system verifiable from outside.

---

| # | Attack | Status |
|---|--------|--------|
| 1 | Circular dependency | Resolved (residual: Q1) |
| 2 | Undecidable benchmark (PSF-04) | Resolved |
| 3 | Threshold arbitrariness | Partially resolved |
| 4 | Floating-point non-determinism | Deferred (Q3) |
| 5 | Missing observer domain | Resolved |
