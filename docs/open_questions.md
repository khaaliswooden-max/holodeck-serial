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

**Status:** **RESOLVED (serial-compatible).** Experiment:
`src/experiments/q2_bvh_serial.py`; data: `results/q2_bvh_serial_*.json`.
Evidence:

- **Seriality.** The reference BVH build and traversal run in a single thread
  (`threading.active_count()` stays 1 throughout) and are deterministic across
  repeated builds. The construction is a recursive median split with a stable
  sort — sequential, no parallel primitive.
- **Complexity.** Build-only time scales with log-log slope **1.12** over
  N ∈ [100, 3200] (O(N log N)-class); the full BVH broad phase **1.16**; the
  naive scan **2.06** (O(N²)). The serial O(N log N) build is achievable with no
  parallelism.
- **Non-uniqueness.** An independent serial broad-phase — sweep-and-prune,
  O(N log N) sort + sweep — and the naive O(N²) scan find the **exact same**
  overlapping pairs as the BVH across 5 random configurations. Serial spatial
  indexing is not unique to BVH; correctness never depends on parallelism.
  (Sweep-and-prune's log-log slope was ~1.65 here — it degrades when many
  x-intervals overlap at high packing — so BVH is the more robust *serial*
  choice, not the only one.)

**Verdict.** Under Interpretation 1 (parallelism permitted above the serial
foundation but not required as a primitive), the BVH **counts as serial**. That
BVH *can* be parallelized is irrelevant — our build does not. The SCE-03 scaling
analysis that relies on serial O(N log N) collision detection therefore holds.

---

## Q3 — Fixed-point vs. IEEE 754

**Question:** Can elastic collision response (PSF-02) be implemented in
fixed-point arithmetic without loss of physical fidelity at the 1e-6 threshold?

**Why it matters:** IEEE-754 floating-point behavior varies across compiler
optimizations and CPU architectures, which threatens cross-platform determinism
(DR-01). Fixed-point arithmetic would make DR-01 trivially satisfiable at the
cost of dynamic range.

**Blocks:** DR-01, DR-02.

**Status:** **RESOLVED (two viable paths, fixed-point quantified).** Experiment:
`src/experiments/q3_fixed_point.py`; data: `results/q3_fixed_point_*.json`.

*Finding 1 — the IEEE-754 risk is one operation, not the whole kernel.* A static
audit of the hot path shows it uses only `+ - * /` and `math.sqrt` — all
**correctly-rounded** per IEEE-754 and therefore bit-portable across IEEE-754
platforms. The single portability hazard is `mass ** (1.0/3.0)` (libm `pow`, not
correctly rounded, ~1 ulp variance possible), computed once per entity for the
collision radius (`world.make_entity`). So the float kernel is *nearly*
cross-platform deterministic. **Lightweight fix (recommended, not yet applied):**
replace that `pow` with a portable cube-root or quantize the radius (e.g.
`round(..., 9)`) to absorb sub-ulp `pow` variance — this makes the float kernel
fully portable at no precision/range cost.

*Finding 2 — fixed-point preserves P4 fidelity, quantified.* A pure-integer
elastic-collision solver (values scaled by S, `math.isqrt`) is bit-identical on
every platform by construction (integer ops are exact), trivially resolving
DR-01. Conservation error scales ~1/S:

| scale S | max momentum err | max KE err | meets 1e-6 (momentum) |
|---------|------------------|------------|-----------------------|
| 2^18 | 3.1e-5 | 8.5e-3 | no |
| 2^22 | 2.1e-6 | 3.5e-4 | no |
| 2^26 | 1.3e-7 | 3.7e-5 | **yes** |
| 2^30 | 8.4e-9 | 2.6e-6 | yes |

(float reference for comparison: ~3e-14 / 2e-13.) So **fixed-point meets the
PSF-02 momentum threshold (≤1e-6) at S ≥ 2^26**; energy (quadratic in v)
converges slower and needs ~2^31. Range/precision tradeoff: precision ~1/S vs
max magnitude ~2^63/S for a fixed-width int64 port (2^26 leaves ~2^37 ≈ 1.4e11
headroom, ample for MVW values O(1e2)); in CPython, ints are arbitrary-precision
so there is no overflow at all.

**Verdict.** Cross-platform determinism is achievable two ways: (a) the cheap
float fix (portable cbrt / radius quantization), since only one op is at risk;
or (b) full fixed-point at S ≥ 2^26 for momentum fidelity. Q3's literal question
— "can fixed-point preserve P4 fidelity at 1e-6?" — is answered **yes**, with the
scale requirement quantified. Empirical confirmation still wants the
cross-architecture run matrix in `hardware/target_spec.md`.

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
| Q2 | BVH serial classification | Resolved — serial-compatible (single-threaded O(N log N); SaP/naive agree) | SCE-03 |
| Q3 | Fixed-point vs. IEEE 754 fidelity | Resolved — fixed-point meets 1e-6 momentum at S≥2^26; float kernel portable except one `pow` | DR-01, DR-02 |
| Q4 | Turing completeness of T=4 vocabulary | Open | EG-01 |
