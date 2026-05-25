# Changelog

All notable changes to holodeck-serial are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### In Progress
- Session 2: MVW reference implementation (`src/mvw/mvw_instance.py`)
- Session 3: SCE profiler — empirical SCE-04 result
- Session 4: Benchmark runner (SCE + DR priority)
- Session 5: Hardware specification document
- Session 6: Paper figures (dependency graph, scaling law, MVW diagram)

---

## [0.3.0] — 2026-05-25

### Added
- `CLAUDE.md` — Claude Code project memory; session execution plan with
  acceptance criteria for all six sessions
- `requirements.txt` — profiling and test dependencies; explicit comment
  that simulation kernel uses stdlib only
- `.gitignore` — LaTeX artifacts, Python cache, result JSON files
- `bootstrap_repo.sh` — one-command repo population script
- Full directory scaffold: `src/`, `spec/`, `paper/`, `hardware/`,
  `results/`, `docs/` with `.gitkeep` files

### Changed
- `README.md` updated to reflect final directory structure and phase status

---

## [0.2.0] — 2026-05-25

### Added
- `paper/holodeck_serial_IEEE_Paper.tex` — complete IEEE 5-page paper scaffold;
  8 benchmark domains, 27 benchmarks in formatted tables, Tier C formal
  definition, MVW compute cost derivation, scaling boundary equations,
  adversarial integrity analysis, 4 open research questions
- `paper/references.bib` — 20 citations: Von Neumann, Turing, Ericson,
  Goldberg, Lamport, Axelrod, Epstein, and others
- `paper/holodeck_serial_IEEE_Paper.pdf` — compiled 4-page IEEE PDF
  (5th page pending figures from Session 6)
- `spec/MVW_Definition_v0.1.md` — Minimum Viable World formal definition;
  6-tuple parameterization with derivation rationale and confidence markers;
  analytical grounding for SCE-04 (~162,000 ticks/sec at 1 GHz)

### Research
- Analytical result: MVW(100,8,4,3,4,1) achieves ~162,000 ticks/sec on
  1 GHz serial CPU — 2,700× margin over 60 ticks/sec threshold [SPECULATIVE]
- Scaling boundary identified: naive O(N²) degrades at N≈5,774;
  BVH O(N log N) extends to N≈10⁸

---

## [0.1.0] — 2026-05-25

### Added
- `README.md` — project overview, directory structure, phase status table,
  MVW summary, open questions, setup instructions, BibTeX citation block
- Benchmark set v0.1 — 8 domains, 27 benchmarks with epistemic confidence
  markers (VERIFIED / PLAUSIBLE / SPECULATIVE)
- Integrity/verticality attack — 5 attacks identified, 3 fully resolved:
  - Attack 1 (circular dependency): resolved by MVW definition
  - Attack 2 (undecidable benchmark PSF-04): resolved by closed interaction matrix
  - Attack 3 (threshold arbitrariness): partially resolved; SCE-04 analytically grounded
  - Attack 4 (floating point non-determinism): deferred — Open Question Q3
  - Attack 5 (missing observer domain): resolved by adding Domain 8 (OI)
- Four open research questions documented: Q1–Q4
- Tier C holodeck formal definition as 5-tuple: (S, Δ, I, G, Φ)
- Three definitional gates established and resolved:
  - Gate 1: Fidelity tier → Tier C (computational simulation engine)
  - Gate 2: Serial computer → Interpretation 1 (single physical machine)
  - Gate 3: Whitepaper claim → Claim C (architecture + empirical benchmarks)

---

[Unreleased]: https://github.com/khaaliswooden-max/holodeck-serial/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/khaaliswooden-max/holodeck-serial/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/khaaliswooden-max/holodeck-serial/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/khaaliswooden-max/holodeck-serial/releases/tag/v0.1.0
