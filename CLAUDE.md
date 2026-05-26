# CLAUDE.md — holodeck-serial
## Claude Code Project Memory | Zuup Innovation Lab

---

## What This Project Is

A benchmark framework for holodeck-class simulation engines grounded in serial
compute. The central claim: a deterministic, stateful, interactive simulation
engine (Tier C holodeck) is achievable on a single-core serial CPU without GPU
or distributed compute as architectural primitives.

This is a research project. Phase 1-3 are complete (benchmark set, integrity
analysis, IEEE whitepaper). You are executing Phase 4-6.

---

## Constraints — Read Before Writing Any Code

1. **Serial only.** The reference implementation must be single-threaded.
   No threading, multiprocessing, asyncio, numpy, scipy, or external physics
   engines. Python standard library only for the simulation kernel.
   This is not a performance optimization — it is the architectural claim.

2. **Determinism is non-negotiable.** Given identical seed + input sequence,
   every run must produce bit-identical output. If any operation introduces
   non-determinism, flag it and fix it before proceeding.

3. **Epistemic markers required.** All threshold values in comments and
   docstrings must carry: VERIFIED, PLAUSIBLE, or SPECULATIVE.
   Example: `# SPECULATIVE — N=100 threshold not empirically calibrated`

4. **Zero external dependencies for core simulation.** `requirements.txt`
   lists profiling and test tools only. The simulation itself imports nothing
   outside stdlib.

---

## Minimum Viable World (MVW) — The Atomic Unit

```
MVW = (N=100, M=8, P=4, K=3, T=4, Φ=1)
```

| Param | Value | Meaning |
|-------|-------|---------|
| N | 100 | Entity count |
| M | 8 | Attributes per entity: {x, y, z, vx, vy, vz, mass, type} |
| P | 4 | Physics rules: Newton's 3 laws + elastic collision |
| K | 3 | Spatial dimensions (Euclidean 3-space) |
| T | 4 | Interaction types: {move, create, destroy, query} |
| Φ | 1 | Observer API endpoint |

**Key result — analytical claim vs. empirical measurement:**
- *Analytical* (1 op = 1 cycle @ 1 GHz): MVW achieves ~162,000 ticks/sec vs the
  60 ticks/sec threshold — a ~2,700× margin. This is the paper's headline claim
  and remains SPECULATIVE (idealized 1-op-per-cycle model).
- *Empirical* (CPython, single core, `results/sce_profile_*.json`): SCE-04
  sustains **~371 ticks/sec** over a 60s run — a **~6.2× margin** (PASS). The
  ~440× gap from the analytical figure is the CPython interpreter tax; a compiled
  serial implementation would approach the analytical bound. The rate is
  host-dependent — a prior cloud run measured ~311 ticks/sec / ~5.2×, so treat
  the empirical figure as ~310–370 ticks/sec (≥5× headroom) pending the
  reproduce-on-baseline-hardware plan in `hardware/target_spec.md`.

---

## Benchmark Domains (27 total)

| Domain | ID | Benchmarks |
|--------|----|------------|
| World State Integrity | WSI | WSI-01 through WSI-04 |
| Temporal Coherence | TC | TC-01 through TC-04 |
| Physical Simulation Fidelity | PSF | PSF-01 through PSF-04 |
| Interaction Fidelity | IF | IF-01 through IF-04 |
| Environmental Generation | EG | EG-01 through EG-04 |
| Serial Compute Efficiency | SCE | SCE-01 through SCE-04 |
| Determinism & Reproducibility | DR | DR-01 through DR-03 |
| Observer Interface | OI | OI-01 through OI-03 |

**Priority order for implementation:** SCE → DR → TC → WSI → PSF → IF → EG → OI

---

## Directory Structure

```
holodeck-serial/
├── CLAUDE.md                    ← You are here
├── README.md
├── requirements.txt
├── .gitignore
├── paper/
│   ├── holodeck_serial_IEEE_Paper.tex
│   ├── holodeck_serial_IEEE_Paper.pdf
│   └── references.bib
├── spec/
│   ├── MVW_Definition_v0.1.md
│   ├── benchmark_set_v0.1.md    ← Generate this from BENCHMARK SPEC below
│   └── holodeck_formal.md
├── src/
│   ├── core/
│   │   ├── world.py             ← World state manager
│   │   ├── physics.py           ← Newtonian physics engine
│   │   ├── scheduler.py         ← Serial tick scheduler
│   │   └── observer.py          ← Observer interface
│   ├── mvw/
│   │   ├── mvw_instance.py      ← MVW(100,8,4,3,4,1) reference implementation
│   │   └── mvw_profiler.py      ← SCE-01/02/03/04 profiling harness
│   └── benchmarks/
│       ├── run_benchmarks.py    ← Master benchmark runner
│       ├── wsi/, tc/, psf/
│       ├── if_/, eg/, sce/
│       ├── dr/, oi/
│       └── report.py            ← JSON + markdown output
├── hardware/
│   ├── target_spec.md
│   └── profiling_plan.md
├── results/                     ← Benchmark JSON output lands here
│   └── .gitkeep
└── docs/
    ├── open_questions.md        ← Q1-Q4 research agenda
    └── gap_analysis.md
```

---

## Session Execution Order

Run sessions in order. Each session has a clear acceptance criterion.
Do not proceed to the next session until the criterion is met.

### Session 1 — Repo structure
**Criterion:** All directories exist, all existing files in correct locations,
clean `git status`.

### Session 2 — MVW reference implementation
**File:** `src/mvw/mvw_instance.py`
**Criterion:** `python src/mvw/mvw_instance.py` runs without error, prints
entity count, tick count, and a hash of final state.

### Session 3 — SCE profiler
**File:** `src/mvw/mvw_profiler.py`
**Criterion:** `python src/mvw/mvw_profiler.py` completes and writes
`results/sce_profile_{timestamp}.json`. SCE-04 has a ticks/sec value.

### Session 4 — Benchmark runner (SCE + DR priority)
**File:** `src/benchmarks/run_benchmarks.py`
**Criterion:** Runner executes SCE-01 through SCE-04 and DR-01, DR-03.
Prints markdown table. Writes JSON to results/.

### Session 5 — Hardware spec
**File:** `hardware/target_spec.md`
**Criterion:** Document exists, defines serial baseline hardware, empirical
validation plan, and cross-platform determinism test matrix.

### Session 6 — Paper figures
**Files:** `paper/figures/fig1_dependency_graph.pdf`,
`paper/figures/fig2_scaling_law.pdf`, `paper/figures/fig3_mvw_diagram.pdf`
**Criterion:** Three figures exist as PDFs. LaTeX compiles cleanly with figures
included.

---

## Open Research Questions (Do Not Close Without Evidence)

| ID | Question | Status |
|----|----------|--------|
| Q1 | Minimum N for emergent behavior | Open |
| Q2 | BVH serial classification | Open |
| Q3 | Fixed-point vs IEEE 754 fidelity | Open |
| Q4 | Turing completeness of T=4 vocabulary | Open |

---

## Author / Attribution

- **Author:** A. Khaalis Wooden, Sr. | MBA; MSIT Candidate, SNHU
- **Org:** Zuup Innovation Lab / Visionblox LLC
- **Email:** aldrich.wooden@snhu.edu
- **GitHub:** github.com/khaaliswooden-max/holodeck-serial

---

## What Success Looks Like

After all six sessions:
1. GitHub repo fully populated per directory structure
2. `python src/mvw/mvw_profiler.py` produces SCE-04 result with real ticks/sec
3. `python src/benchmarks/run_benchmarks.py` produces a benchmark report
4. `cd paper && pdflatex holodeck_serial_IEEE_Paper.tex` compiles to 5-page PDF
5. All results committed to `results/` directory

That is the empirical foundation for upgrading SCE-04 from SPECULATIVE to PLAUSIBLE,
and the basis for the full paper submission.
