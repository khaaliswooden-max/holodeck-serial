"""Render the Q1 emergence figure from the latest results/q1_emergence_*.json.

    python src/experiments/q1_figure.py

Writes results/q1_emergence.png (and .pdf). matplotlib only (not the kernel).
"""

import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
_RESULTS = os.path.join(_HERE, "..", "..", "results")


def _latest():
    files = sorted(glob.glob(os.path.join(_RESULTS, "q1_emergence_*.json")))
    if not files:
        raise SystemExit("no q1_emergence_*.json in results/ -- run q1_emergence.py first")
    with open(files[-1]) as fh:
        return json.load(fh)


def main():
    data = _latest()
    dens = sorted(data["fixed_density_sweep"], key=lambda r: r["n"])
    box = sorted(data["fixed_box_sweep"], key=lambda r: r["n"])

    ns = [r["n"] for r in dens]
    kurt = [r["eq_kurt_mean"] for r in dens]
    kerr = [r["eq_kurt_std"] for r in dens]
    theory = [r["eq_kurt_theory"] for r in dens]
    lam = [r["lyapunov"] for r in dens]

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))

    # Panel 1: thermalization -- kurtosis vs N vs theory
    ax = axes[0]
    ax.errorbar(ns, kurt, yerr=kerr, fmt="o", color="#1f3b73", capsize=3,
                label="measured (eq.)", zorder=3)
    ax.plot(ns, theory, "-", color="#b5482a", linewidth=1.8,
            label=r"theory $-6/(3N+2)$")
    ax.axhline(0.0, color="green", linestyle="--", linewidth=1.0,
               label="Gaussian (MB)")
    ax.axhspan(-0.02, 0.02, color="green", alpha=0.10)
    ax.axhline(-1.2, color="#999999", linestyle=":", linewidth=1.0,
               label="initial (uniform)")
    ax.set_xscale("log")
    ax.set_xlabel("N (fixed density)")
    ax.set_ylabel("velocity-component excess kurtosis")
    ax.set_title("(1) Thermalization -> Maxwell-Boltzmann")
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(True, which="both", alpha=0.2)

    # Panel 2: mixing -- Lyapunov vs N
    ax = axes[1]
    ax.plot(ns, lam, "s-", color="#7a3b1f")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("N (fixed density)")
    ax.set_ylabel(r"finite-time Lyapunov $\lambda$ (1/time)")
    ax.set_title("(2) Mixing / chaos (positive = chaotic)")
    ax.grid(True, which="both", alpha=0.2)

    # Panel 3: interaction-onset at nominal box L=100
    ax = axes[2]
    bns = [r["n"] for r in box]
    cpp = [r["collisions_per_particle"] for r in box]
    ax.plot(bns, cpp, "o-", color="#1f3b73", label="collisions/particle")
    ax.axhline(1.0, color="green", linestyle="--", linewidth=1.0,
               label="onset (1 coll./particle)")
    ax.axvline(100, color="#b5482a", linestyle=":", linewidth=1.2,
               label="nominal MVW N=100")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("N (fixed box L=100)")
    ax.set_ylabel("collisions per particle")
    ax.set_title("(3) Interaction-onset at nominal density")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(True, which="both", alpha=0.2)

    fig.suptitle("Q1: minimum N for emergent behavior in the elastic-collision MVW",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    png = os.path.join(_RESULTS, "q1_emergence.png")
    pdf = os.path.join(_RESULTS, "q1_emergence.pdf")
    fig.savefig(png, dpi=130)
    fig.savefig(pdf)
    plt.close(fig)
    print("wrote %s and .pdf" % os.path.relpath(png, os.path.join(_HERE, "..", "..")))


if __name__ == "__main__":
    main()
