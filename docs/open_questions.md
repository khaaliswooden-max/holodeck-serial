# Open Research Questions — Q1–Q4

## holodeck-serial research agenda

These four questions are the forward agenda emerging from the benchmark
framework. They are **not** to be closed without evidence (see CLAUDE.md).

---

## Q1 — Minimum emergence threshold

**Question:** What is the minimum entity count N at which a Newtonian simulation
exhibits non-trivial emergent behavior?

**Why it matters:** Determines whether N = 100 is conservative, sufficient, or
excessive for the MVW claim. The N = 100 value was **SPECULATIVE** — analytically
motivated, not empirically calibrated.

**Blocks:** WSI-01, TC-03.

**Status:** **PARTIAL — evidence gathered.** Experiment:
`src/experiments/q1_emergence.py`; data: `results/q1_emergence_*.json`; figure:
`results/q1_emergence.png`. Three independent proxies were swept over N:

1. **Thermalization (the binding constraint).** Starting each particle at equal
   speed `v0` with random direction (so each velocity *component* is
   Uniform(−v0,v0), excess kurtosis −1.2), an isolated elastic gas relaxes toward
   the microcanonical equilibrium, whose single-component excess kurtosis is
   exactly **−6/(3N+2)** — Gaussian (the Maxwell–Boltzmann signature) only as
   N→∞. Measured equilibrium kurtosis tracks this law within noise
   (mean residual −0.018 ± 0.077 over the sweep). Gaussianity tolerances give:
   - within 10%: **N ≳ 20**
   - within 5%:  **N ≳ 40**
   - within 2%:  **N ≳ 100**

   So **N = 100 is the threshold at which the emergent velocity distribution is
   Gaussian (Maxwell–Boltzmann) to within ~2%** — empirical support that N = 100
   is a reasonable, mildly conservative statistical minimum, not arbitrary.

2. **Mixing / chaos.** A 1e-6 velocity perturbation diverges with finite-time
   Lyapunov exponent λ ≈ 3–5 (per unit time) for **all N ≥ 2** once collisions
   occur (hard-sphere / Sinai-billiard chaos). Mixing is therefore *not* the
   binding constraint — it emerges immediately.

3. **Interaction-onset (a density result, not an N result).** At the MVW's
   nominal box **L = 100**, the gas is collision-starved: collisions per particle
   ≈ 0 at N = 100 and only ~0.09 at N = 1000 over 750 ticks. The interaction
   graph never percolates. Inter-particle collisions only matter at L = 100 for
   N on the order of 10⁴.

**Conclusion & new sub-question.** N = 100 is justified as a *statistical*
minimum (2% Gaussianity). But the binding under-specification of the MVW is
**density (box size L), not N**: at the nominal L = 100 the system barely
collides, so the dynamical emergence that thermalization assumes requires a
denser configuration. *Recommended MVW refinement: specify a packing fraction /
mean-free-path target alongside N.* Q1 stays open only on this density question;
the N-threshold itself is now evidence-backed.

Related work in agent-based modeling is directionally relevant but not directly
applicable to Newtonian particle engines; the result above is self-contained.

---

## Q2 — BVH serial classification

**Question:** Does a bounding volume hierarchy count as a "serial" data structure
under Interpretation 1?

**Why it matters:** BVH traversal is inherently sequential, but its construction
can be parallelized. If BVH construction is classified as serial, the O(N log N)
scaling analysis holds; if not, an alternative serial-compatible spatial index is
required. The reference implementation builds the BVH with a single-threaded
median-split and is therefore serial *as implemented* — but the classification
question is conceptual, not implementational.

**Blocks:** SCE-03.

**Status:** Open.

---

## Q3 — Fixed-point vs. IEEE 754

**Question:** Can elastic collision response (PSF-02) be implemented in
fixed-point arithmetic without loss of physical fidelity at the 1e-6 threshold?

**Why it matters:** IEEE-754 floating-point behavior varies across compiler
optimizations and CPU architectures, which threatens cross-platform determinism
(DR-01). Fixed-point arithmetic would make DR-01 trivially satisfiable at the
cost of dynamic range.

**Blocks:** DR-01, DR-02.

**Status:** Open / deferred to implementation phase. The reference kernel uses
IEEE-754 doubles and achieves bit-identical results *within a platform*; the
cross-platform matrix in `hardware/target_spec.md` is the test that would resolve
this empirically.

---

## Q4 — Turing completeness of interaction vocabulary

**Question:** Is T = 4 {move, create, destroy, query} a Turing-complete
interaction vocabulary for world simulation?

**Why it matters:** If so, the MVW interaction set is minimal; if not, a larger T
may be required for the "arbitrary environment" generation claimed in EG-01.

**Blocks:** EG-01.

**Status:** Open.

---

| ID | Question | Status | Blocks |
|----|----------|--------|--------|
| Q1 | Minimum N for emergent behavior | Partial — N≈100 for 2% MB Gaussianity; density is the real constraint | WSI-01, TC-03 |
| Q2 | BVH serial classification | Open | SCE-03 |
| Q3 | Fixed-point vs. IEEE 754 fidelity | Open | DR-01, DR-02 |
| Q4 | Turing completeness of T=4 vocabulary | Open | EG-01 |
