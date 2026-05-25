# Claude Code Execution Plan
## holodeck-serial | Phase 5

---

## Objective

Stand up the holodeck-serial repository, implement the MVW reference instance,
build the benchmark runner, and produce the first empirical SCE-04 result — all
executable via Claude Code from the repo root.

---

## Session 1 — Repo Initialization

```bash
# From repo root
git init
git remote add origin https://github.com/khaaliswooden-max/holodeck-serial
mkdir -p paper spec src/core src/benchmarks/wsi src/benchmarks/tc \
          src/benchmarks/psf src/benchmarks/if_ src/benchmarks/eg \
          src/benchmarks/sce src/benchmarks/dr src/benchmarks/oi \
          src/mvw hardware results docs
touch results/.gitkeep
git add .
git commit -m "chore: scaffold holodeck-serial repo structure"
git push -u origin main
```

**Claude Code prompt:**
> "Initialize the holodeck-serial repo at the path above.
> Move all files from /home/claude/holodeck-serial/ into the correct directories
> per the README structure. Verify no files are missing. Commit with message
> 'feat: add Phase 1-3 artifacts — benchmark set, MVW definition, IEEE paper scaffold'."

---

## Session 2 — MVW Reference Implementation

**Target file:** `src/mvw/mvw_instance.py`

**Claude Code prompt:**
> "Implement MVW(100, 8, 4, 3, 4, 1) in Python as a pure serial simulation engine.
>
> Requirements:
> - Single-threaded only. No threading, multiprocessing, or asyncio.
> - Entity schema: {id, x, y, z, vx, vy, vz, mass, type} — 8 attributes.
> - Physics rules: Newton's 3 laws + elastic collision (4 rules).
> - Spatial index: implement both naive O(N²) and BVH O(N log N) collision detection.
>   Toggle via flag so we can profile both.
> - Tick function: deterministic. Given same initial state + same input sequence,
>   produces identical output every run.
> - Observer interface: a query(entity_id) method that returns full entity state.
> - Seed-based initialization: MVW(seed=42) produces identical world every run.
>
> Use Python standard library only. No numpy, no scipy, no external physics engines.
> The goal is a verifiably serial implementation, not a fast one."

---

## Session 3 — SCE Profiler (Closes SCE-04)

**Target file:** `src/mvw/mvw_profiler.py`

**Claude Code prompt:**
> "Write a profiler for mvw_instance.py that measures:
>
> SCE-01: CPU cycles per tick — use time.perf_counter() with 10,000-tick runs.
>   Report mean, std, min, max.
>
> SCE-02: RAM per 1,000 entities — use tracemalloc. Report bytes.
>
> SCE-03: Tick cost scaling law — run MVW at N = [10, 50, 100, 500, 1000, 5000].
>   Plot ticks/sec vs N. Fit O(N), O(N log N), O(N²) curves. Report which fits best.
>
> SCE-04: Serial sufficiency test — run MVW(100) for 60 seconds wall-clock time.
>   Count actual ticks completed. Pass if ticks/sec >= 60.
>
> Output results as JSON to results/sce_profile_{timestamp}.json and
> print a human-readable summary to stdout.
>
> The profiler must run on a single core. Pin to CPU 0 if possible (Linux: taskset)."

---

## Session 4 — Benchmark Runner

**Target file:** `src/benchmarks/run_benchmarks.py`

**Claude Code prompt:**
> "Build a benchmark runner that executes all 27 benchmarks defined in
> spec/benchmark_set_v0.1.md against the MVW reference implementation.
>
> Structure:
> - Each domain (WSI, TC, PSF, IF, EG, SCE, DR, OI) has its own test module
>   in src/benchmarks/{domain}/.
> - Each benchmark is a function that returns: {id, name, result, threshold,
>   passed, duration_ms, notes}.
> - The runner collects all results and writes to results/benchmark_report_{timestamp}.json.
> - Print a markdown table to stdout: benchmark ID | threshold | result | PASS/FAIL.
>
> Start with SCE domain (most critical) and DR domain (determinism verification).
> Stub remaining domains with TODO markers.
>
> Acceptance criteria: SCE-04 must produce a result. DR-01, DR-03 must produce results.
> All other benchmarks may be stubs for this session."

---

## Session 5 — Hardware Specification

**Target file:** `hardware/target_spec.md`

**Claude Code prompt:**
> "Write the hardware specification document for holodeck-serial Phase 4.
>
> Define the 'serial baseline' hardware:
> - Target CPU: single-core, >= 1 GHz, x86-64 reference platform
> - Memory: minimum RAM for MVW(100) + profiler overhead
> - Storage: benchmark result persistence requirements
> - OS: Linux (for CPU pinning via taskset)
>
> Also define:
> - The empirical validation plan: what must be run, on what hardware,
>   to advance SCE-04 from SPECULATIVE to VERIFIED
> - The cross-platform determinism test matrix (addresses Q3):
>   same code, same seed on x86-64 / ARM64 / RISC-V — hash comparison protocol
>
> Use the MVW compute cost estimates from the whitepaper as the basis
> for minimum hardware requirements."

---

## Session 6 — Paper Figures

**Claude Code prompt:**
> "Generate the figures for holodeck_serial_IEEE_Paper.tex:
>
> Figure 1: Benchmark domain dependency graph (WSI → TC → PSF → IF → EG → SCE → DR,
>   with OI as a side channel). Output as SVG and PDF.
>
> Figure 2: SCE scaling law plot — three curves on one chart:
>   O(N²) naive, O(N log N) BVH, 60 ticks/sec threshold line.
>   X-axis: entity count N (log scale, 10 to 100,000).
>   Y-axis: ticks/sec (log scale).
>   Mark the MVW N=100 operating point.
>   Output as PDF (for LaTeX inclusion).
>
> Figure 3: MVW 6-tuple diagram — visual representation of (N,M,P,K,T,Φ)
>   as a structured decomposition.
>
> Save all figures to paper/figures/.
> Update holodeck_serial_IEEE_Paper.tex to include all three figures."

---

## Execution Sequence Summary

```
Session 1:  Repo init + file migration           ~15 min
Session 2:  MVW reference implementation         ~45 min
Session 3:  SCE profiler → first SCE-04 result   ~30 min
Session 4:  Benchmark runner (SCE + DR)          ~45 min
Session 5:  Hardware specification               ~20 min
Session 6:  Paper figures                        ~30 min
                                           Total: ~3 hours
```

**End state of Phase 5:**
- GitHub repo fully scaffolded
- MVW(100,8,4,3,4,1) running and profiled
- SCE-04 has a real number (not analytical estimate)
- Benchmark runner producing JSON output
- IEEE paper has figures, compiles cleanly with pdflatex

---

## Phase 6 Preview (Post-Claude Code)

After Phase 5 completion:
- Submit empirical SCE-04 result to upgrade SPECULATIVE → VERIFIED
- Tackle Q1 (emergence threshold) via agent-based modeling experiment
- Draft full paper sections from this scaffold
- Target: IEEE VR 2027 or equivalent simulation/computing venue

---

*holodeck-serial Phase 5 Execution Plan | Zuup Innovation Lab*
