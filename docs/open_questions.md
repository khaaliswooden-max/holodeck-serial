# Open Research Questions — Q1–Q4

## holodeck-serial research agenda

These four questions are the forward agenda emerging from the benchmark
framework. They are **not** to be closed without evidence (see CLAUDE.md).

---

## Q1 — Minimum emergence threshold

**Question:** What is the minimum entity count N at which a Newtonian simulation
exhibits non-trivial emergent behavior?

**Why it matters:** Determines whether N = 100 is conservative, sufficient, or
excessive for the MVW claim. The N = 100 value is currently **SPECULATIVE** — it
is analytically motivated, not empirically calibrated.

**Blocks:** WSI-01, TC-03.

**Status:** Open. Related work in agent-based modeling is directionally relevant
but not directly applicable to Newtonian particle engines.

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
| Q1 | Minimum N for emergent behavior | Open | WSI-01, TC-03 |
| Q2 | BVH serial classification | Open | SCE-03 |
| Q3 | Fixed-point vs. IEEE 754 fidelity | Open | DR-01, DR-02 |
| Q4 | Turing completeness of T=4 vocabulary | Open | EG-01 |
