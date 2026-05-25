# Hardware Specification — holodeck-serial Phase 4

## Zuup Innovation Lab | A. Khaalis Wooden, Sr.

This document defines the **serial baseline** hardware against which the serial
sufficiency claim (SCE-04) is evaluated, the plan for advancing SCE-04 from
SPECULATIVE to VERIFIED, and the cross-platform determinism test matrix that
addresses Open Question Q3.

---

## 1. Serial Baseline Hardware

The architectural claim is **single-core sufficiency**. The baseline is the
*minimum* machine on which MVW(100,8,4,3,4,1) must meet all thresholds.

| Component | Requirement | Rationale |
|-----------|-------------|-----------|
| CPU | Single core, ≥ 1 GHz, x86-64 | Von Neumann, one instr/cycle/core (Interpretation 1). SIMD/GPU offload prohibited at kernel level. |
| Cores used | Exactly 1 (pinned to CPU 0) | The kernel is single-threaded; profiler pins via `os.sched_setaffinity`. |
| RAM | ≥ 64 MB for MVW(100) + profiler | See §2; measured footprint is ~38 KB for the world itself. |
| Storage | ≥ 10 MB for result JSON persistence | `results/*.json` benchmark + profile reports. |
| OS | Linux (kernel ≥ 3.x) | Required for CPU pinning (`taskset` / `sched_setaffinity`). Other OSes run the kernel but cannot enforce single-core pinning. |
| Python | CPython 3.8+ | Stdlib-only kernel; no numpy/scipy/threading. |

The 1 GHz figure is the *analytical* reference (paper §IV). The empirical
baseline below is the CPython interpreter, which executes far fewer simulation
ticks per second than the 1-op-per-cycle analytical model — and still clears the
threshold by a wide margin.

---

## 2. Measured Footprint (this repository, current run)

From `results/sce_profile_*.json` and `results/benchmark_report_*.json`:

| Metric | Measured | Source |
|--------|----------|--------|
| SCE-02 RAM per entity | ~393 bytes | tracemalloc construction delta |
| SCE-02 RAM per 1K entities | ~384 KB | SCE-02 |
| MVW(100) world footprint | ~38 KB | 100 × 393 bytes |
| SCE-01 mean cost/tick | ~3.25 ms (N=100, naive) | perf_counter, 10K ticks |
| SCE-04 sustained rate | **~311 ticks/sec** (60s wall-clock) | SCE-04 |
| SCE-04 headroom vs 60 | **~5.2×** | SCE-04 |
| SCE-03 naive scaling | O(N²) (best R² fit) | SCE-03 |
| SCE-03 BVH scaling | O(N log N) (best R² fit) | SCE-03 |

**Minimum RAM derivation:** MVW(100) world ≈ 38 KB; CPython interpreter base
+ profiler (tracemalloc, snapshots) ≈ tens of MB. The 64 MB requirement is set
by the interpreter/profiler overhead, not the simulation state, which is
negligible. # PLAUSIBLE — interpreter overhead dominates; not separately profiled.

---

## 3. Empirical Validation Plan: SPECULATIVE → VERIFIED

SCE-04 is currently SPECULATIVE. To advance it to **VERIFIED**:

1. **Run on declared baseline hardware.** Execute `mvw_profiler.py` (full, 60s
   SCE-04) on a physical single-core ≥ 1 GHz x86-64 machine, CPU 0 pinned, no
   other load. Record `results/sce_profile_*.json`.
2. **Reproduce N ≥ 3 times.** Confirm ticks/sec variance is within ±10% across
   runs; confirm SCE-04 `passed=true` every time.
3. **Confirm the scaling law.** SCE-03 must report `best_fit = O(N²)` for naive
   and `O(N log N)` for BVH, matching the paper's §IV analysis.
4. **Cross-check determinism.** TC-01, DR-01, DR-03 must pass (hash-equal) on the
   baseline machine and produce the *same hashes* as the reference platform
   (subject to §4 caveats).

When steps 1–4 hold on the declared baseline, SCE-04 advances to VERIFIED for
that hardware class. The CPython result already demonstrates the claim holds
even with a ~1000× interpreter tax over the analytical model.

---

## 4. Cross-Platform Determinism Test Matrix (addresses Q3)

DR-01 requires hash-equality across implementations. IEEE-754 evaluation can
differ across architectures and compiler/runtime optimizations, so this is the
open empirical question (Q3 / gap-analysis Attack 4).

**Protocol:** run an identical seed + input schedule on each platform, then
compare `World.state_hash()` (SHA-256 of the bit-exact serialization).

| Platform | Arch | Runtime | Expected | Status |
|----------|------|---------|----------|--------|
| Reference | x86-64 | CPython 3.11 | baseline hash H₀ | captured |
| Server | x86-64 | CPython 3.8–3.12 | == H₀ | TODO |
| Apple Silicon | ARM64 | CPython 3.11 | == H₀ (to verify) | TODO |
| Raspberry Pi | ARM64 | CPython 3.11 | == H₀ (to verify) | TODO |
| RISC-V SBC | RISC-V | CPython 3.11 | == H₀ (to verify) | TODO |

**Decision rule (Q3 resolution):**
- If all platforms reproduce H₀ → IEEE-754 doubles are sufficient; DR-01 VERIFIED
  for CPython across these arches.
- If hashes diverge → migrate the kernel arithmetic to **fixed-point**
  (integer-scaled) for the collision/integration hot path, re-run the matrix,
  and re-evaluate PSF-02 fidelity at the 1e-6 threshold.

The kernel already isolates all floating-point arithmetic in
`src/core/physics.py`, so a fixed-point migration is contained to one module.

---

## 5. Profiling Harness Configuration

| Setting | Value | Where |
|---------|-------|-------|
| CPU affinity | CPU 0 | `mvw_profiler.pin_to_cpu0()` |
| SCE-01 sample | 10,000 ticks | `--sce01-ticks` |
| SCE-04 window | 60 s wall-clock | `--sce04-seconds` |
| SCE-03 N sweep | naive {10,50,100,500,1000}; bvh {…,5000} | `mvw_profiler.main` |
| Timer | `time.perf_counter` | monotonic, highest resolution |
| Memory | `tracemalloc` | allocation delta, not RSS |

See `hardware/profiling_plan.md` for the run procedure and
`hardware/serial_baseline.md` for the baseline definition rationale.
