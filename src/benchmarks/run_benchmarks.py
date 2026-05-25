"""Master benchmark runner for holodeck-serial.

Executes the 27 benchmarks defined in spec/benchmark_set_v0.1.md against the
MVW(100,8,4,3,4,1) reference implementation, in the CLAUDE.md priority order
(SCE -> DR -> TC -> WSI -> PSF -> IF -> EG -> OI), prints a markdown table, and
writes results/benchmark_report_{timestamp}.json.

    python src/benchmarks/run_benchmarks.py
"""

import os
import platform
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..")
# Kernel + MVW + harness + each domain dir on the path (bare-name imports).
for _p in [_HERE,
           os.path.join(_SRC, "core"),
           os.path.join(_SRC, "mvw"),
           os.path.join(_HERE, "sce"), os.path.join(_HERE, "dr"),
           os.path.join(_HERE, "tc"), os.path.join(_HERE, "wsi"),
           os.path.join(_HERE, "psf"), os.path.join(_HERE, "if_"),
           os.path.join(_HERE, "eg"), os.path.join(_HERE, "oi")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import report  # noqa: E402
import sce_suite, dr_suite, tc_suite, wsi_suite  # noqa: E402
import psf_suite, if_suite, eg_suite, oi_suite    # noqa: E402

# Priority order per CLAUDE.md.
_SUITES = [
    ("SCE", sce_suite), ("DR", dr_suite), ("TC", tc_suite), ("WSI", wsi_suite),
    ("PSF", psf_suite), ("IF", if_suite), ("EG", eg_suite), ("OI", oi_suite),
]
_RESULTS_DIR = os.path.join(_SRC, "..", "results")


def main():
    print("holodeck-serial benchmark runner -- MVW(100,8,4,3,4,1)")
    print("platform: %s | python %s\n"
          % (platform.platform(), platform.python_version()))

    results = []
    for name, suite in _SUITES:
        print("running %s ..." % name)
        results.extend(suite.run_all())

    print("\n" + report.to_markdown(results) + "\n")
    summary = report.summarize(results)
    print("summary: %d total | %d pass | %d fail | %d stub"
          % (summary["total"], summary["passed"], summary["failed"],
             summary["stub"]))

    meta = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "mvw": "MVW(100,8,4,3,4,1)",
    }
    path = report.write_json(results, _RESULTS_DIR, meta=meta)
    print("wrote %s" % os.path.relpath(path, os.path.join(_SRC, "..")))


if __name__ == "__main__":
    main()
