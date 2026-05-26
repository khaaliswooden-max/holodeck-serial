# Tier C Holodeck — Formal Definition

## Zuup Innovation Lab | holodeck-serial

This document fixes the formal model the benchmark framework is written against.
It is the definitional substrate for `paper/holodeck_serial_IEEE_Paper.tex`
Section II.

---

## Fidelity Tiers

| Tier | Description | In scope? |
|------|-------------|-----------|
| A | Full sensory immersion (visual, audio, haptic, proprioceptive). Display-complete. | No |
| B | Visual + audio + spatial interaction. VR-complete. | No |
| C | Computational simulation engine. The world exists as data; rendering is separable. | **Yes** |

This project addresses **Tier C** exclusively. The simulation engine is the
system under test; display and rendering are out of scope.

---

## Serial Computer (Interpretation 1)

A *serial computer* is a single physical machine under the Von Neumann
architecture executing one instruction per clock cycle per core. Parallelism is
permitted as an abstraction *above* the serial foundation but is not an
architectural primitive. This admits modern single-core processors operating
without SIMD or GPU offload at the simulation-kernel level.

The reference implementation (`src/`) honors this literally: single-threaded,
Python standard library only, no `threading`, `multiprocessing`, `asyncio`,
`numpy`, `scipy`, or external physics engines in the kernel.

---

## Tier C System

A Tier C holodeck system **H** is a 5-tuple:

```
H = (S, Δ, I, G, Φ)
```

| Symbol | Name | Reference module |
|--------|------|------------------|
| S | World state space | `src/core/world.py` |
| Δ | State transition function (physics engine), Δ: S × t → S | `src/core/physics.py` |
| I | Input event set | `src/core/scheduler.py` |
| G | Environment generation function (spec → S₀) | `src/mvw/mvw_instance.py` |
| Φ | Observer interface | `src/core/observer.py` |

The system is **serial-sufficient** iff all five components can be evaluated on a
single-core CPU at ≥ 1 GHz while satisfying all benchmark thresholds in
`spec/benchmark_set_v0.1.md`.

---

## State Transition Contract

Δ must be a pure function of `(state, input_events, dt)`. Given identical
inputs it must produce a bit-identical successor state. This is the determinism
contract that benchmarks TC-01, IF-02, DR-01, DR-03, OI-02 verify.

Sources of non-determinism are prohibited in the kernel:
- wall-clock time, `time.time()` reads inside Δ
- unseeded RNG (initialization RNG is seeded and consumed in fixed order)
- iteration over unordered containers (sets/dicts) without a stable sort key
- floating-point reductions whose order depends on hash or memory layout

See `docs/open_questions.md` Q3 for the cross-architecture IEEE-754 caveat.
