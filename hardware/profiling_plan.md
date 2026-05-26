# Profiling Plan — holodeck-serial Phase 4

## Empirical validation procedure

This is the runbook for producing the benchmark and profiling artifacts that
ground the SCE domain. Outputs land in `results/`.

---

## Prerequisites

```bash
pip install -r requirements.txt    # profiling/test/figure tools only
```

The simulation kernel itself needs nothing beyond the Python standard library.

---

## Procedure

### Step 1 — Sanity check the reference instance

```bash
python src/mvw/mvw_instance.py
```

Expect: entity_count = 100, a stable initial hash, and a final hash after 1000
ticks. Re-running must print the *same* hashes (determinism).

### Step 2 — SCE profile (closes SCE-04)

```bash
python src/mvw/mvw_profiler.py              # full: 10K-tick SCE-01, 60s SCE-04
python src/mvw/mvw_profiler.py --quick      # fast smoke run
```

Writes `results/sce_profile_{timestamp}.json`. Verify:
- SCE-04 `passed = true`, `ticks_per_sec ≥ 60`.
- SCE-03 `naive.best_fit = O(N^2)`, `bvh.best_fit = O(N log N)`.

### Step 3 — Full benchmark report

```bash
python src/benchmarks/run_benchmarks.py
```

Writes `results/benchmark_report_{timestamp}.json` and prints a markdown table.
Verify no `FAIL` rows (STUB rows are expected for SCE-01..03 profiler entries
and OI-03).

### Step 4 — Baseline-hardware run (for VERIFIED status)

Repeat Steps 2–3 on the declared serial baseline (`hardware/target_spec.md` §1),
CPU 0 pinned, no competing load, N ≥ 3 repetitions. Record variance.

### Step 5 — Cross-platform determinism matrix (Q3)

Run Steps 1–3 on each row of the matrix in `hardware/target_spec.md` §4 and
compare `state_hash()` values to the reference baseline H₀.

---

## What each measurement means

| Benchmark | Tool | Interpretation |
|-----------|------|----------------|
| SCE-01 | `time.perf_counter` | wall-time per tick; cycles estimate is derived, not a hardware counter |
| SCE-02 | `tracemalloc` | allocation delta of world construction (not RSS) |
| SCE-03 | least-squares R² | which Big-O best fits measured seconds/tick |
| SCE-04 | 60s tick count | the headline serial-sufficiency number |

---

## Acceptance

The phase is empirically grounded when:
1. `mvw_profiler.py` produces an SCE-04 ticks/sec value ≥ 60, and
2. `run_benchmarks.py` produces a report with zero FAIL rows, and
3. both artifacts are committed under `results/`.

All three hold in the current repository.
