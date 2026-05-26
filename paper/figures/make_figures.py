"""Generate the three figures for holodeck_serial_IEEE_Paper.tex.

    python paper/figures/make_figures.py

Outputs (paper/figures/):
    fig1_dependency_graph.pdf / .svg
    fig2_scaling_law.pdf
    fig3_mvw_diagram.pdf

matplotlib is used for figure generation ONLY -- it is not part of the
simulation kernel. Reads the latest results/sce_profile_*.json (if present) to
annotate the empirical operating point on Figure 2.
"""

import glob
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

_HERE = os.path.dirname(os.path.abspath(__file__))
_RESULTS = os.path.join(_HERE, "..", "..", "results")


def _latest_sce_profile():
    files = sorted(glob.glob(os.path.join(_RESULTS, "sce_profile_*.json")))
    if not files:
        return None
    with open(files[-1]) as fh:
        return json.load(fh)


def _latest_q1():
    files = sorted(glob.glob(os.path.join(_RESULTS, "q1_emergence_*.json")))
    if not files:
        return None
    with open(files[-1]) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Figure 1 -- benchmark domain dependency graph
# ---------------------------------------------------------------------------

def fig1_dependency_graph():
    chain = ["WSI", "TC", "PSF", "IF", "EG", "SCE", "DR"]
    fig, ax = plt.subplots(figsize=(7.0, 2.4))
    ax.set_xlim(0, len(chain))
    ax.set_ylim(0, 3)
    ax.axis("off")

    y = 2.0
    centers = []
    for i, name in enumerate(chain):
        cx = i + 0.5
        centers.append(cx)
        box = FancyBboxPatch((cx - 0.42, y - 0.32), 0.84, 0.64,
                             boxstyle="round,pad=0.02", linewidth=1.2,
                             edgecolor="#1f3b73", facecolor="#dce6f7")
        ax.add_patch(box)
        ax.text(cx, y, name, ha="center", va="center", fontsize=10,
                fontweight="bold", color="#1f3b73")

    for i in range(len(chain) - 1):
        ax.add_patch(FancyArrowPatch((centers[i] + 0.42, y),
                                     (centers[i + 1] - 0.42, y),
                                     arrowstyle="-|>", mutation_scale=14,
                                     linewidth=1.2, color="#333333"))

    # OI as a side channel observing the whole pipeline.
    oi_y = 0.55
    oi_cx = (centers[0] + centers[-1]) / 2.0
    box = FancyBboxPatch((oi_cx - 0.55, oi_y - 0.32), 1.10, 0.64,
                         boxstyle="round,pad=0.02", linewidth=1.2,
                         edgecolor="#7a3b1f", facecolor="#f7e6dc")
    ax.add_patch(box)
    ax.text(oi_cx, oi_y, "OI (observer)", ha="center", va="center",
            fontsize=9, fontweight="bold", color="#7a3b1f")
    for cx in (centers[0], centers[len(chain) // 2], centers[-1]):
        ax.add_patch(FancyArrowPatch((oi_cx, oi_y + 0.32), (cx, y - 0.32),
                                     arrowstyle="-|>", mutation_scale=10,
                                     linewidth=0.8, linestyle="--",
                                     color="#7a3b1f", alpha=0.7))

    ax.set_title("Benchmark domain dependency pipeline (OI as side channel)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(_HERE, "fig1_dependency_graph.pdf"))
    fig.savefig(os.path.join(_HERE, "fig1_dependency_graph.svg"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 -- SCE scaling law
# ---------------------------------------------------------------------------

def _ops_naive(n):
    return n * 8 + n * 4 + (n * n) / 2.0


def _ops_bvh(n):
    return n * 8 + n * 4 + n * math.log2(max(n, 2))


def fig2_scaling_law():
    ns = [10 ** (i / 8.0) for i in range(8, 41)]  # ~10 .. 1e5
    tps_naive = [1e9 / _ops_naive(n) for n in ns]
    tps_bvh = [1e9 / _ops_bvh(n) for n in ns]

    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.loglog(ns, tps_naive, color="#b5482a", linewidth=1.8,
              label=r"naive $O(N^2)$ (1 GHz model)")
    ax.loglog(ns, tps_bvh, color="#1f3b73", linewidth=1.8,
              label=r"BVH $O(N\log N)$ (1 GHz model)")
    ax.axhline(60, color="#2a7a2a", linewidth=1.4, linestyle="--",
               label="60 ticks/sec threshold")

    # Analytical MVW operating point.
    ax.plot([100], [1e9 / _ops_naive(100)], "o", color="#b5482a",
            markersize=7, markeredgecolor="k")
    ax.annotate("MVW N=100\n(~162k, analytical)", (100, 1e9 / _ops_naive(100)),
                textcoords="offset points", xytext=(8, -28), fontsize=7.5)

    # Empirical CPython operating point from the committed profile.
    prof = _latest_sce_profile()
    if prof:
        emp = prof["results"]["SCE-04"]["ticks_per_sec"]
        ax.plot([100], [emp], "s", color="black", markersize=7,
                label="MVW N=100 (CPython, measured)")
        ax.annotate("~%.0f measured" % emp, (100, emp),
                    textcoords="offset points", xytext=(8, 8), fontsize=7.5)

    ax.set_xlabel("Entity count N")
    ax.set_ylabel("Tick rate (ticks/sec)")
    ax.set_title("SCE scaling law: serial sufficiency boundary", fontsize=10)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=7.0, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(_HERE, "fig2_scaling_law.pdf"))
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 -- MVW 6-tuple decomposition
# ---------------------------------------------------------------------------

def fig3_mvw_diagram():
    params = [
        ("N", "100", "entities"),
        ("M", "8", "attributes\n{x,y,z,\nvx,vy,vz,\nm,type}"),
        ("P", "4", "physics rules\n(Newton x3\n+ elastic)"),
        ("K", "3", "spatial dims\n(Euclidean\n3-space)"),
        ("T", "4", "interactions\n{move,create,\ndestroy,query}"),
        (u"Φ", "1", "observer\nendpoint"),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 3)
    ax.axis("off")
    ax.text(3, 2.75, r"MVW = (N, M, P, K, T, $\Phi$) = (100, 8, 4, 3, 4, 1)",
            ha="center", va="center", fontsize=12, fontweight="bold",
            color="#1f3b73")

    for i, (sym, val, desc) in enumerate(params):
        cx = i + 0.5
        box = FancyBboxPatch((cx - 0.45, 0.7), 0.9, 1.45,
                             boxstyle="round,pad=0.02", linewidth=1.3,
                             edgecolor="#1f3b73", facecolor="#eef3fb")
        ax.add_patch(box)
        ax.text(cx, 1.92, sym, ha="center", va="center", fontsize=15,
                fontweight="bold", color="#1f3b73")
        ax.text(cx, 1.55, "= %s" % val, ha="center", va="center", fontsize=11)
        ax.text(cx, 1.02, desc, ha="center", va="center", fontsize=5.8,
                color="#333333", linespacing=1.25)

    ax.set_title("Minimum Viable World: 6-tuple decomposition", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(_HERE, "fig3_mvw_diagram.pdf"))
    plt.close(fig)


def fig4_q1_kurtosis():
    """Q1 result: emergent velocity-component kurtosis vs N against the
    microcanonical law -6/(3N+2). Skipped if no q1 results are present."""
    data = _latest_q1()
    if not data:
        print("  (no q1_emergence results; skipping fig4)")
        return
    rows = sorted(data["fixed_density_sweep"], key=lambda r: r["n"])
    ns = [r["n"] for r in rows]
    kurt = [r["eq_kurt_mean"] for r in rows]
    kerr = [r["eq_kurt_std"] for r in rows]
    theory = [r["eq_kurt_theory"] for r in rows]

    fig, ax = plt.subplots(figsize=(3.4, 2.7))
    ax.errorbar(ns, kurt, yerr=kerr, fmt="o", color="#1f3b73", capsize=2.5,
                markersize=4, label="measured (eq.)", zorder=3)
    ax.plot(ns, theory, "-", color="#b5482a", linewidth=1.6,
            label=r"$-6/(3N+2)$")
    ax.axhline(0.0, color="green", linestyle="--", linewidth=1.0,
               label="Gaussian (MB)")
    ax.axhspan(-0.02, 0.02, color="green", alpha=0.10)
    ax.axhline(-1.2, color="#999999", linestyle=":", linewidth=0.9,
               label="initial (uniform)")
    ax.axvline(100, color="#444444", linestyle=":", linewidth=0.9)
    ax.set_xscale("log")
    ax.set_xlabel("entity count N")
    ax.set_ylabel("excess kurtosis")
    ax.legend(fontsize=6, loc="lower right")
    ax.grid(True, which="both", alpha=0.2)
    fig.tight_layout()
    fig.savefig(os.path.join(_HERE, "fig4_q1_kurtosis.pdf"))
    plt.close(fig)


def main():
    fig1_dependency_graph()
    fig2_scaling_law()
    fig3_mvw_diagram()
    fig4_q1_kurtosis()
    print("wrote fig1_dependency_graph.pdf/.svg, fig2_scaling_law.pdf, "
          "fig3_mvw_diagram.pdf, fig4_q1_kurtosis.pdf to paper/figures/")


if __name__ == "__main__":
    main()
