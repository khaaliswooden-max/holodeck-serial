# Contributing to holodeck-serial

Thank you for your interest in contributing. This project is a research artifact
with specific architectural constraints. Read this document fully before opening
a pull request — contributions that violate the serial compute constraint will
not be merged regardless of performance gains.

---

## Core Constraint — Non-Negotiable

**The simulation kernel must remain single-threaded and serial.**

No threading, multiprocessing, asyncio, numpy, scipy, SIMD intrinsics, or GPU
offload in `src/core/` or `src/mvw/`. This is the architectural claim of the
research. Violating it defeats the purpose of the project.

The restriction does not apply to:
- Benchmark runners (`src/benchmarks/`)
- Figure generation scripts (`paper/figures/`)
- Profiling tools (`src/mvw/mvw_profiler.py`)

---

## Epistemic Marking

All threshold values, claims, and assertions in code comments and documentation
must carry an explicit confidence marker:

| Marker | Meaning |
|--------|---------|
| `# VERIFIED` | Derivable from first principles or established literature |
| `# PLAUSIBLE` | Logically sound, requires empirical calibration |
| `# SPECULATIVE` | Theoretical, requires experimental validation |

Example:
```python
TICK_RATE_THRESHOLD = 60  # SPECULATIVE — not empirically calibrated; see Q1
```

PRs that introduce unqualified quantitative claims will be returned for revision.

---

## How to Contribute

### Reporting Issues

Open a GitHub Issue with:
- A clear title stating the benchmark ID or component affected
- Steps to reproduce
- Expected vs. actual behavior
- Your hardware spec (CPU, single-core clock speed, OS) — this matters for SCE benchmarks

### Submitting Pull Requests

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Scope your PR** to one of these categories:
   - `feat/` — new benchmark implementation
   - `fix/` — bug in existing implementation
   - `research/` — open question investigation (Q1–Q4)
   - `paper/` — whitepaper revisions
   - `docs/` — documentation only

3. **Run the benchmark suite** before submitting:
   ```bash
   python src/benchmarks/run_benchmarks.py
   ```
   All previously passing benchmarks must still pass. Include the JSON output
   in your PR description.

4. **For new benchmark implementations**, your PR must include:
   - The implementation in the appropriate `src/benchmarks/{domain}/` directory
   - A results entry showing pass/fail against the defined threshold
   - The confidence marker on the threshold (VERIFIED / PLAUSIBLE / SPECULATIVE)
   - Any citations supporting the threshold value

5. **For open question investigations** (Q1–Q4), structure your PR as:
   - Evidence (code, data, citations)
   - Proposed confidence upgrade (e.g., SPECULATIVE → PLAUSIBLE)
   - What further evidence would be needed for the next upgrade

### Commit Message Format

```
<type>(<scope>): <short description>

[optional body]

[optional: Closes #issue]
```

Types: `feat`, `fix`, `docs`, `test`, `research`, `paper`, `chore`

Examples:
```
feat(sce): implement SCE-04 serial sufficiency benchmark
research(Q1): add emergence threshold experiment at N=10,50,100,500
fix(dr): correct hash comparison in DR-01 cross-platform test
paper(sec4): add empirical SCE-04 result to Section IV
```

---

## Open Research Questions — Priority Contributions

These are the highest-value contributions to the project:

| ID | Question | What's Needed |
|----|----------|---------------|
| Q1 | Minimum N for emergent behavior | Agent-based modeling experiment; statistical analysis |
| Q2 | BVH serial classification | Formal argument or citation; architectural decision |
| Q3 | Fixed-point vs IEEE 754 fidelity | PSF-02 benchmark under fixed-point arithmetic |
| Q4 | Turing completeness of T=4 vocabulary | Formal proof or counterexample |

Resolving any of these advances a benchmark from SPECULATIVE to PLAUSIBLE or
VERIFIED, directly strengthening the paper's empirical foundation.

---

## Code Style

- Python 3.10+
- No external dependencies in simulation kernel (`src/core/`, `src/mvw/`)
- Type hints required on all public functions
- Docstrings required on all classes and public methods
- `pytest` for all tests

---

## Academic Attribution

If this benchmark framework contributes to your published research, please cite:

```bibtex
@misc{wooden2026holodeck,
  author      = {Wooden, Aldrich K.},
  title       = {Toward a Holodeck on Serial Compute: A Benchmark Framework
                 and Open Research Agenda},
  year        = {2026},
  institution = {Zuup Innovation Lab / Southern New Hampshire University},
  note        = {github.com/khaaliswooden-max/holodeck-serial}
}
```

---

## Questions

Open a GitHub Discussion or reach out at aldrich.wooden@snhu.edu.
