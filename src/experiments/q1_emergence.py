"""Q1 -- Minimum entity count N for emergent behavior.

Open research question (docs/open_questions.md, Q1): at what N does the
Newtonian MVW exhibit non-trivial emergent behavior? We operationalize
"emergent behavior" with three independent, measurable proxies and report the N
threshold each yields:

  1. THERMALIZATION (statistical-mechanics emergence)
     An isolated elastic gas relaxes from a non-equilibrium start (all particles
     equal speed v0, random directions -> each velocity COMPONENT is
     Uniform(-v0,v0), excess kurtosis -1.2) toward the microcanonical
     equilibrium. For a point uniform on the sphere S^(3N-1), one component has
     excess kurtosis exactly -6/(3N+2): it is Gaussian (the Maxwell-Boltzmann
     signature, kurtosis 0) only as N -> infinity. So "emergent MB behavior" is
     a tolerance on Gaussianity, with a known finite-size law to validate
     against. We measure equilibrium component kurtosis vs N.

  2. MIXING (dynamical-systems emergence)
     Two runs differing by a tiny velocity perturbation (eps) diverge. We
     measure the velocity-space separation growth (finite-time Lyapunov
     amplification). Positive/exponential growth => chaotic mixing.

  3. INTERACTION-ONSET (the trivial floor)
     The collision-interaction graph (who collided with whom). Emergence of
     collective structure requires the graph to percolate (a giant component).
     We report collisions/particle and the largest-component fraction.

Two sweeps: a fixed-DENSITY sweep (isolates the finite-size statistical effect)
and a fixed-BOX sweep at the MVW's nominal L=100 (isolates the collision-rate /
density effect and places the nominal MVW(N=100) operating point).

Standard library only for simulation and analysis (math.erf gives the normal
CDF). matplotlib is used for the figure only.

    python src/experiments/q1_emergence.py
    python src/experiments/q1_emergence.py --quick
"""

import argparse
import json
import math
import os
import random
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(_HERE, "..", "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

import physics                                  # noqa: E402
from world import World, X, Y, Z, VX, VY, VZ    # noqa: E402

_RESULTS = os.path.join(_HERE, "..", "..", "results")

# Fixed simulation constants for the emergence sweeps.
V0 = 5.0          # initial speed magnitude (all particles)
DT = 0.01         # timestep
MASS = 1.0        # equal mass -> single-temperature Maxwell-Boltzmann
# Number density (particles per unit volume) for the fixed-density sweep.
# Chosen so the mean free path << box (collision-rich): packing fraction ~6%.
DENSITY = 0.11
EPS = 1e-6        # perturbation for the Lyapunov/mixing proxy


# ---------------------------------------------------------------------------
# stdlib statistics
# ---------------------------------------------------------------------------

def _normal_cdf(x, mu, sigma):
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))


def excess_kurtosis(xs):
    n = len(xs)
    m = sum(xs) / n
    m2 = sum((v - m) ** 2 for v in xs) / n
    if m2 == 0.0:
        return 0.0
    m4 = sum((v - m) ** 4 for v in xs) / n
    return m4 / (m2 * m2) - 3.0


def ks_distance(xs, mu, sigma):
    """One-sample Kolmogorov-Smirnov distance to Normal(mu, sigma)."""
    s = sorted(xs)
    n = len(s)
    d = 0.0
    for i, v in enumerate(s):
        cdf = _normal_cdf(v, mu, sigma)
        d = max(d, abs((i + 1) / n - cdf), abs(cdf - i / n))
    return d


def mean_std(xs):
    n = len(xs)
    if n == 0:
        return 0.0, 0.0
    m = sum(xs) / n
    var = sum((v - m) ** 2 for v in xs) / n
    return m, math.sqrt(var)


def linfit_slope(xs, ys):
    """Least-squares slope of y vs x."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx if sxx else 0.0


# ---------------------------------------------------------------------------
# world construction / evolution
# ---------------------------------------------------------------------------

def _build(n, bounds, seed):
    """N equal-mass particles, random positions, all speed V0, random
    directions (a velocity-space shell: non-equilibrium)."""
    w = World(bounds=bounds)
    rng = random.Random(seed)
    margin = 1.0
    for _ in range(n):
        x = rng.uniform(margin, bounds - margin)
        y = rng.uniform(margin, bounds - margin)
        z = rng.uniform(margin, bounds - margin)
        # uniform random direction via normalized Gaussian
        gx, gy, gz = rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)
        norm = math.sqrt(gx * gx + gy * gy + gz * gz) or 1.0
        s = V0 / norm
        w.create(x, y, z, gx * s, gy * s, gz * s, MASS, 0)
    return w


def _density_bounds(n):
    return (n / DENSITY) ** (1.0 / 3.0)


def _components(w):
    out = []
    for e in w.entities:
        out.append(e[VX]); out.append(e[VY]); out.append(e[VZ])
    return out


# ---------------------------------------------------------------------------
# Proxy 1 + 3: thermalization and interaction-onset (one run)
# ---------------------------------------------------------------------------

def thermalize_run(n, bounds, ticks, seed, mode, sample_from=0.6):
    """Evolve and collect: time-averaged equilibrium component kurtosis/KS over
    the last (1-sample_from) fraction of ticks, total collisions/particle, and
    the collision-interaction giant-component fraction."""
    w = _build(n, bounds, seed)
    sigma_eq = V0 / math.sqrt(3.0)   # microcanonical component std (variance V0^2/3)
    init_kurt = excess_kurtosis(_components(w))

    # union-find for the interaction graph
    parent = {e[0]: e[0] for e in w.entities}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    total_collisions = 0
    sample_start = int(ticks * sample_from)
    kurt_samples = []
    ks_samples = []
    for t in range(ticks):
        rec = []
        physics.integrate(w.entities, DT, (0.0, 0.0, 0.0), bounds)
        total_collisions += physics.resolve_collisions(w.entities, mode, record=rec)
        for ida, idb in rec:
            union(ida, idb)
        if t >= sample_start and (t % 10 == 0):
            comps = _components(w)
            kurt_samples.append(excess_kurtosis(comps))
            ks_samples.append(ks_distance(comps, 0.0, sigma_eq))

    roots = {}
    for eid in parent:
        r = find(eid)
        roots[r] = roots.get(r, 0) + 1
    giant = max(roots.values()) / n if roots else 0.0

    eq_kurt = sum(kurt_samples) / len(kurt_samples) if kurt_samples else init_kurt
    eq_ks = sum(ks_samples) / len(ks_samples) if ks_samples else 1.0
    return {
        "init_kurt": init_kurt,
        "eq_kurt": eq_kurt,
        "eq_ks": eq_ks,
        "collisions_per_particle": total_collisions / n,
        "giant_fraction": giant,
    }


# ---------------------------------------------------------------------------
# Proxy 2: mixing / finite-time Lyapunov
# ---------------------------------------------------------------------------

def mixing_run(n, bounds, ticks, seed, mode):
    """Velocity-space divergence between a run and an eps-perturbed twin.
    Returns log10 amplification and an estimated Lyapunov exponent (per unit
    time)."""
    w = _build(n, bounds, seed)
    w2 = w.clone()
    w2.entities[0][VX] += EPS  # tiny perturbation to one particle

    def vdist():
        s = 0.0
        for a, b in zip(w.entities, w2.entities):
            s += ((a[VX] - b[VX]) ** 2 + (a[VY] - b[VY]) ** 2
                  + (a[VZ] - b[VZ]) ** 2)
        return math.sqrt(s)

    d0 = vdist() or EPS
    times, logs = [], []
    for t in range(ticks):
        physics.integrate(w.entities, DT, (0.0, 0.0, 0.0), bounds)
        physics.resolve_collisions(w.entities, mode)
        physics.integrate(w2.entities, DT, (0.0, 0.0, 0.0), bounds)
        physics.resolve_collisions(w2.entities, mode)
        d = vdist()
        if d > 0:
            times.append(t * DT)
            logs.append(math.log(d / d0))
    if not logs:
        return {"log10_amp": 0.0, "lyapunov": 0.0}
    # Fit slope over the growth region (before saturation at the system scale).
    sat = math.log((2.0 * V0 * math.sqrt(n)) / d0)  # rough saturation level
    grow_t = [t for t, l in zip(times, logs) if l < 0.8 * sat]
    grow_l = [l for l in logs if l < 0.8 * sat]
    lam = linfit_slope(grow_t, grow_l) if len(grow_t) > 3 else linfit_slope(times, logs)
    return {"log10_amp": logs[-1] / math.log(10), "lyapunov": lam}


# ---------------------------------------------------------------------------
# sweeps
# ---------------------------------------------------------------------------

def sweep_fixed_density(ns, ticks, seeds, mode):
    rows = []
    for n in ns:
        bounds = _density_bounds(n)
        kurts, kss, cpp, giants = [], [], [], []
        for s in range(seeds):
            r = thermalize_run(n, bounds, ticks, seed=1000 + s, mode=mode)
            kurts.append(r["eq_kurt"]); kss.append(r["eq_ks"])
            cpp.append(r["collisions_per_particle"]); giants.append(r["giant_fraction"])
        mix = mixing_run(n, bounds, max(ticks // 3, 150), seed=1000, mode=mode)
        km, ks_ = mean_std(kurts)
        theory = -6.0 / (3.0 * n + 2.0)   # microcanonical component kurtosis
        rows.append({
            "n": n, "bounds": bounds,
            "eq_kurt_mean": km, "eq_kurt_std": ks_,
            "eq_kurt_theory": theory,
            "eq_ks_mean": mean_std(kss)[0],
            "collisions_per_particle": mean_std(cpp)[0],
            "giant_fraction": mean_std(giants)[0],
            "lyapunov": mix["lyapunov"], "log10_amp": mix["log10_amp"],
            "init_kurt": -1.2,
        })
        print("  N=%-4d L=%5.1f  cpp=%5.1f  giant=%.2f  kurt=% .3f (theory % .3f)"
              "  lambda=% .2f"
              % (n, bounds, rows[-1]["collisions_per_particle"],
                 rows[-1]["giant_fraction"], km, theory, mix["lyapunov"]))
    return rows


def sweep_fixed_box(ns, ticks, mode, bounds=100.0):
    rows = []
    for n in ns:
        r = thermalize_run(n, bounds, ticks, seed=2000, mode=mode)
        rows.append({
            "n": n, "bounds": bounds,
            "collisions_per_particle": r["collisions_per_particle"],
            "giant_fraction": r["giant_fraction"],
            "eq_kurt": r["eq_kurt"],
        })
        print("  N=%-5d L=%.0f  cpp=%6.2f  giant=%.2f"
              % (n, bounds, r["collisions_per_particle"], r["giant_fraction"]))
    return rows


def _threshold(rows, key, tol, below=True):
    """Smallest N at which |value| crosses tol (below=True: |value| <= tol)."""
    for r in sorted(rows, key=lambda r: r["n"]):
        v = abs(r[key])
        if (below and v <= tol) or (not below and v >= tol):
            return r["n"]
    return None


def main():
    ap = argparse.ArgumentParser(description="Q1 emergence sweeps")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--ticks", type=int, default=1200)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args()

    ns_density = [2, 4, 8, 16, 32, 64, 100, 128, 256]
    ns_box = [10, 50, 100, 500, 1000]
    ticks, seeds = args.ticks, args.seeds
    if args.quick:
        ns_density = [4, 16, 64, 100, 256]
        ns_box = [10, 100, 500]
        ticks, seeds = 400, 2

    print("Q1 emergence experiment")
    print("=" * 60)
    print("[fixed-density sweep] density=%.3f v0=%.1f ticks=%d seeds=%d"
          % (DENSITY, V0, ticks, seeds))
    density_rows = sweep_fixed_density(ns_density, ticks, seeds, mode="bvh")
    print("[fixed-box sweep] L=100 ticks=%d" % (ticks // 2))
    box_rows = sweep_fixed_box(ns_box, ticks // 2, mode="bvh")

    # Theory-based thresholds: |kurt| = 6/(3N+2) <= tol  =>  N >= (6/tol - 2)/3.
    def theory_n(tol):
        return int(math.ceil((6.0 / tol - 2.0) / 3.0))

    # Validate the measured kurtosis against the microcanonical law.
    resid = mean_std([r["eq_kurt_mean"] - r["eq_kurt_theory"]
                      for r in density_rows])

    thresholds = {
        "thermal_kurt_0.10_theory": theory_n(0.10),
        "thermal_kurt_0.05_theory": theory_n(0.05),
        "thermal_kurt_0.02_theory": theory_n(0.02),
        "thermal_kurt_0.05_measured": _threshold(density_rows, "eq_kurt_mean", 0.05),
        "mixing_lyapunov_positive": _threshold(density_rows, "lyapunov", 0.5,
                                               below=False),
        "interaction_giant_0.9_fixed_box": _threshold(box_rows,
                                                       "giant_fraction", 0.9,
                                                       below=False),
    }
    analysis = {
        "kurtosis_law": "-6/(3N+2)  (microcanonical component excess kurtosis)",
        "measured_minus_theory_mean": resid[0],
        "measured_minus_theory_std": resid[1],
        "nominal_mvw_collisions_per_particle_L100":
            next((r["collisions_per_particle"] for r in box_rows
                  if r["n"] == 100), None),
        "interpretation": (
            "Thermal/Gaussian emergence follows -6/(3N+2): Gaussianity within "
            "5%% needs N>=%d, within 2%% needs N>=%d. Mixing (chaos) and "
            "interaction percolate at low N once collisions occur. At the "
            "nominal box L=100 the gas is collision-starved (cpp~0 at N=100), so "
            "DENSITY -- not N -- is the binding under-specification."
            % (theory_n(0.05), theory_n(0.02))),
    }
    print("=" * 60)
    print("thresholds (minimum N):")
    for k, v in thresholds.items():
        print("  %-34s %s" % (k, v))
    print("kurtosis law fit: measured - theory = %+.3f +/- %.3f"
          % (resid[0], resid[1]))

    report = {
        "experiment": "Q1 emergence",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "constants": {"V0": V0, "DT": DT, "MASS": MASS, "DENSITY": DENSITY,
                      "EPS": EPS, "ticks": ticks, "seeds": seeds},
        "fixed_density_sweep": density_rows,
        "fixed_box_sweep": box_rows,
        "thresholds": thresholds,
        "analysis": analysis,
    }
    os.makedirs(_RESULTS, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(_RESULTS, "q1_emergence_%s.json" % stamp)
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    print("wrote %s" % os.path.relpath(path, os.path.join(_HERE, "..", "..")))
    return report


if __name__ == "__main__":
    main()
