#!/bin/bash
# bootstrap_repo.sh
# Run this from your local holodeck-serial repo root after cloning.
# It copies all Phase 1-3 artifacts into the correct structure and commits.
#
# Usage:
#   git clone https://github.com/khaaliswooden-max/holodeck-serial
#   cd holodeck-serial
#   bash bootstrap_repo.sh

set -e

echo "==> Creating directory structure..."
mkdir -p paper/figures spec src/core src/mvw \
         src/benchmarks/{wsi,tc,psf,if_,eg,sce,dr,oi} \
         hardware results docs

echo "==> Adding .gitkeep to empty dirs..."
touch results/.gitkeep paper/figures/.gitkeep \
      src/core/.gitkeep src/mvw/.gitkeep hardware/.gitkeep

echo "==> Copying files from Claude output..."
# ---- Run this block only if pulling from Claude outputs ----
# Replace SOURCE_DIR with the path where you downloaded the Claude artifacts
# SOURCE_DIR=~/Downloads/holodeck-serial-artifacts
#
# cp $SOURCE_DIR/CLAUDE.md .
# cp $SOURCE_DIR/README.md .
# cp $SOURCE_DIR/requirements.txt .
# cp $SOURCE_DIR/.gitignore .
# cp $SOURCE_DIR/holodeck_serial_IEEE_Paper.tex paper/
# cp $SOURCE_DIR/holodeck_serial_IEEE_Paper.pdf paper/
# cp $SOURCE_DIR/references.bib paper/
# cp $SOURCE_DIR/MVW_Definition_v0.1.md spec/
# cp $SOURCE_DIR/Claude_Code_Execution_Plan.md docs/
# ---- End block ----

echo "==> Staging all files..."
git add .

echo "==> Committing Phase 1-3 artifacts..."
git commit -m "feat: Phase 1-3 complete — benchmark set, MVW definition, IEEE paper scaffold

- 8 benchmark domains, 27 benchmarks (spec/MVW_Definition_v0.1.md)
- Integrity/verticality attack: 3/5 resolved, 2 documented as open questions
- IEEE 5-page paper scaffold: LaTeX + BibTeX, 20 citations (paper/)
- CLAUDE.md: Claude Code project memory with session execution plan
- Directory structure ready for Phase 4-6 implementation

Open research questions: Q1 (emergence threshold), Q2 (BVH serial
classification), Q3 (fixed-point arithmetic), Q4 (T=4 Turing completeness)

Co-authored-by: Claude (Anthropic)"

echo "==> Pushing to origin/main..."
git push origin main

echo ""
echo "Done. Repo is live."
echo "Next: open Claude Code in the repo root. CLAUDE.md is your entry point."
echo "Start with Session 2: src/mvw/mvw_instance.py"
