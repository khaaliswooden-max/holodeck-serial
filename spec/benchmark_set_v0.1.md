# Benchmark Set v0.1 — holodeck-serial

## Zuup Innovation Lab | A. Khaalis Wooden, Sr.

This document is the canonical enumeration of the 27 benchmarks executed by
`src/benchmarks/run_benchmarks.py` against the MVW(100,8,4,3,4,1) reference
implementation. Each benchmark carries an epistemic confidence marker:

- **VERIFIED** — derivable from first principles or established literature.
- **PLAUSIBLE** — logically sound, requires empirical calibration.
- **SPECULATIVE** — theoretical, requires experimental validation.

The benchmark set is the contribution of the position paper
(`paper/holodeck_serial_IEEE_Paper.tex`). This spec is the machine-readable
companion: the IDs, thresholds, and confidence markers here are the source of
truth for the runner.

---

## Priority Order

```
SCE → DR → TC → WSI → PSF → IF → EG → OI
```

SCE (Serial Compute Efficiency) and DR (Determinism & Reproducibility) are the
load-bearing domains for the paper's central claim and are implemented as real
measurements. Remaining domains are implemented where tractable and stubbed
(returning `notes="TODO"`) otherwise.

---

## Domain 1 — World State Integrity (WSI)

| ID     | Metric                            | Threshold                | Conf.       |
|--------|-----------------------------------|--------------------------|-------------|
| WSI-01 | State retention across ticks      | 100% / 10K ticks         | PLAUSIBLE   |
| WSI-02 | Zero contradictory assertions     | 0 / 1M queries           | VERIFIED    |
| WSI-03 | State query latency               | ≤ 1 ms / 10K entities    | SPECULATIVE |
| WSI-04 | Round-trip serialization fidelity | Bit-identical / 1K runs  | VERIFIED    |

## Domain 2 — Temporal Coherence (TC)

| ID    | Metric                 | Threshold                       | Conf.       |
|-------|------------------------|---------------------------------|-------------|
| TC-01 | Tick determinism       | Hash-equal / 100 runs           | VERIFIED    |
| TC-02 | Causal ordering        | 0 violations / 10K events       | VERIFIED    |
| TC-03 | Simulation rate        | ≥ 60 ticks/sec (MVW)            | SPECULATIVE |
| TC-04 | Time dilation stability| Pass at 0.1×, 1×, 10×           | PLAUSIBLE   |

## Domain 3 — Physical Simulation Fidelity (PSF)

| ID     | Metric                       | Threshold              | Conf.     |
|--------|------------------------------|------------------------|-----------|
| PSF-01 | Projectile trajectory accuracy | ≤ 0.1% / 1K samples  | VERIFIED  |
| PSF-02 | Elastic collision momentum   | Error ≤ 1e-6           | VERIFIED  |
| PSF-03 | Constraint satisfaction      | 0 violations / 10K frames | PLAUSIBLE |
| PSF-04 | Interaction matrix coverage  | 100% of defined pairs  | PLAUSIBLE |

## Domain 4 — Interaction Fidelity (IF)

| ID    | Metric                    | Threshold               | Conf.     |
|-------|---------------------------|-------------------------|-----------|
| IF-01 | Input-to-state latency    | ≤ 16.6 ms (60 Hz)       | PLAUSIBLE |
| IF-02 | Input sequence determinism| Hash-equal / 50 runs    | VERIFIED  |
| IF-03 | Input event coverage      | 100% of defined events  | PLAUSIBLE |
| IF-04 | Interaction rule compliance| 0 violations / 10K events | PLAUSIBLE |

## Domain 5 — Environmental Generation (EG)

| ID    | Metric                   | Threshold               | Conf.       |
|-------|--------------------------|-------------------------|-------------|
| EG-01 | Spec-to-world completeness | 100% / 100 specs      | PLAUSIBLE   |
| EG-02 | Generation determinism   | Hash-equal (seed+spec)  | VERIFIED    |
| EG-03 | Generation speed         | ≤ 5 s (MVW)             | SPECULATIVE |
| EG-04 | Spec language coverage   | All benchmark envs.     | PLAUSIBLE   |

## Domain 6 — Serial Compute Efficiency (SCE)

| ID     | Metric                | Threshold                                 | Conf.       |
|--------|-----------------------|-------------------------------------------|-------------|
| SCE-01 | CPU cycles per tick (MVW) | Profiler measurement                  | SPECULATIVE |
| SCE-02 | RAM per 1K entities   | Profiler measurement                      | SPECULATIVE |
| SCE-03 | Tick cost scaling law | O(N log N) or better                      | PLAUSIBLE   |
| SCE-04 | Serial sufficiency    | All benchmarks pass, single-core, ≥ 1 GHz | SPECULATIVE |

## Domain 7 — Determinism & Reproducibility (DR)

| ID    | Metric                       | Threshold                | Conf.     |
|-------|------------------------------|--------------------------|-----------|
| DR-01 | Cross-platform reproducibility | Hash-equal (same impl.)| PLAUSIBLE |
| DR-02 | Floating point stability     | ≤ 1e-9 divergence/tick   | PLAUSIBLE |
| DR-03 | Seed-based replayability     | Full replay from seed+log| VERIFIED  |

## Domain 8 — Observer Interface Completeness (OI)

| ID    | Metric                    | Threshold              | Conf.       |
|-------|---------------------------|------------------------|-------------|
| OI-01 | State query API coverage  | 100% of world state    | PLAUSIBLE   |
| OI-02 | Query result determinism  | Hash-equal / same state| VERIFIED    |
| OI-03 | Scene graph export fidelity | Lossless / 10 formats| SPECULATIVE |

---

## Result Schema

Every benchmark function returns a dictionary:

```python
{
    "id": "SCE-04",            # benchmark identifier
    "name": "Serial sufficiency",
    "result": 161290.0,        # measured value (type varies by benchmark)
    "threshold": ">= 60 ticks/sec",
    "passed": True,            # bool, or None if stub/not-applicable
    "duration_ms": 60000.0,    # wall-clock time to execute the benchmark
    "notes": "",               # free text; "TODO" marks an unimplemented stub
    "confidence": "SPECULATIVE"
}
```

The runner aggregates these into `results/benchmark_report_{timestamp}.json`
and prints a markdown table to stdout.

---

*Benchmark Set v0.1 — companion to the IEEE position paper. Thresholds for
SPECULATIVE benchmarks are calibration targets, not pass/fail gates, until the
empirical validation plan in `hardware/target_spec.md` is executed.*
