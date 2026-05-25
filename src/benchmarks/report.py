"""Report rendering for the benchmark runner: markdown table + JSON file."""

import json
import os
from datetime import datetime, timezone

try:
    from tabulate import tabulate
except ImportError:  # tabulate is a listed dependency; fall back if absent
    tabulate = None


def _fmt_result(r):
    v = r["result"]
    if isinstance(v, float):
        return ("%.6g" % v)
    return str(v)


def _status(passed):
    if passed is True:
        return "PASS"
    if passed is False:
        return "FAIL"
    return "STUB"


def to_markdown(results):
    headers = ["ID", "Benchmark", "Threshold", "Result", "Status", "Conf."]
    rows = [
        [r["id"], r["name"], r["threshold"], _fmt_result(r),
         _status(r["passed"]), r.get("confidence", "")]
        for r in results
    ]
    if tabulate:
        return tabulate(rows, headers=headers, tablefmt="github")
    # Minimal hand-rolled markdown if tabulate is unavailable.
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return "\n".join([line, sep, body])


def summarize(results):
    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    stub = sum(1 for r in results if r["passed"] is None)
    return {"total": len(results), "passed": passed, "failed": failed,
            "stub": stub}


def write_json(results, results_dir, meta=None):
    os.makedirs(results_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "report": "holodeck-serial benchmark report",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "summary": summarize(results),
        "results": results,
    }
    if meta:
        report.update(meta)
    path = os.path.join(results_dir, "benchmark_report_%s.json" % stamp)
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    return path
