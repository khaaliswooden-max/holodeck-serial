"""Q3 -- Can fixed-point arithmetic preserve P4 fidelity at the 1e-6 threshold?

Open question (docs/open_questions.md, Q3): IEEE-754 behavior varies across
architectures, threatening cross-platform determinism (DR-01/DR-02). The
proposed fix is fixed-point arithmetic. Can it preserve elastic-collision
(PSF-02) momentum/energy conservation at error <= 1e-6?

Two parts:

  PART 1 -- KERNEL IEEE-754 AUDIT.
  The reference kernel's hot path uses only correctly-rounded IEEE-754
  operations (+, -, *, /, and math.sqrt), all of which are bit-portable across
  IEEE-754 platforms. The ONE hazard is `mass ** (1/3)` (libm `pow`, not
  correctly rounded -> may differ by ~1 ulp across platforms), computed once per
  entity for the collision radius. So the kernel is *nearly* cross-platform
  deterministic; a portable cube-root (or fixed-point) closes the gap.

  PART 2 -- FIXED-POINT ELASTIC COLLISION.
  A pure-integer elastic-collision solver (values scaled by S, integer sqrt via
  math.isqrt). Integer arithmetic is exact and platform-independent, so it is
  bit-identical on every machine BY CONSTRUCTION (resolves DR-01 trivially). We
  sweep the scale S to find where momentum/energy conservation meets 1e-6, and
  quantify the range/precision tradeoff.

    python src/experiments/q3_fixed_point.py
"""

import json
import math
import os
import random
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_RESULTS = os.path.join(_HERE, "..", "..", "results")


# ---------------------------------------------------------------------------
# float reference elastic collision (same algorithm as core/physics.py)
# ---------------------------------------------------------------------------

def collide_float(va, vb, n, ma, mb):
    """Elastic (e=1) impulse along unit normal n. va, vb, n are 3-tuples."""
    rvx, rvy, rvz = va[0] - vb[0], va[1] - vb[1], va[2] - vb[2]
    vn = rvx * n[0] + rvy * n[1] + rvz * n[2]
    if vn <= 0.0:
        return va, vb
    j = 2.0 * vn / (1.0 / ma + 1.0 / mb)
    va2 = (va[0] - j / ma * n[0], va[1] - j / ma * n[1], va[2] - j / ma * n[2])
    vb2 = (vb[0] + j / mb * n[0], vb[1] + j / mb * n[1], vb[2] + j / mb * n[2])
    return va2, vb2


# ---------------------------------------------------------------------------
# fixed-point elastic collision (pure integer; values scaled by S)
# ---------------------------------------------------------------------------

def collide_fixed(va, vb, d, ma, mb, S):
    """va, vb are integer 3-tuples scaled by S. d is the integer separation
    vector (scaled by S) defining the collision normal. ma, mb integer masses.
    Returns post-collision integer velocities (scaled by S). Pure integer ops."""
    dist = math.isqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])  # scaled by S
    if dist == 0:
        return va, vb
    # unit normal, scaled by S:  n_i = d_i * S / dist
    nx = (d[0] * S) // dist
    ny = (d[1] * S) // dist
    nz = (d[2] * S) // dist
    rvx, rvy, rvz = va[0] - vb[0], va[1] - vb[1], va[2] - vb[2]   # scaled S
    # vn = rv . n / S  (rv:S * n:S = S^2; /S -> S)
    vn = (rvx * nx + rvy * ny + rvz * nz) // S                    # scaled S
    if vn <= 0:
        return va, vb
    # j = 2*vn*ma*mb/(ma+mb), scaled by S, exact integer
    j = (2 * vn * ma * mb) // (ma + mb)                           # scaled S
    # dv_i = (j * n_i) / (m * S):  (S * S)/S = S
    va2 = (va[0] - (j * nx) // (ma * S),
           va[1] - (j * ny) // (ma * S),
           va[2] - (j * nz) // (ma * S))
    vb2 = (vb[0] + (j * nx) // (mb * S),
           vb[1] + (j * ny) // (mb * S),
           vb[2] + (j * nz) // (mb * S))
    return va2, vb2


def _momentum(va, vb, ma, mb):
    return tuple(ma * va[k] + mb * vb[k] for k in range(3))


def _ke(va, vb, ma, mb):
    return (0.5 * ma * sum(c * c for c in va)
            + 0.5 * mb * sum(c * c for c in vb))


def _rand_collision(rng):
    """A random closing 2-body collision in float (velocities O(1-10),
    integer masses, a unit normal)."""
    va = tuple(rng.uniform(-8, 8) for _ in range(3))
    vb = tuple(rng.uniform(-8, 8) for _ in range(3))
    g = [rng.gauss(0, 1) for _ in range(3)]
    nrm = math.sqrt(sum(c * c for c in g)) or 1.0
    n = tuple(c / nrm for c in g)
    ma = rng.randint(1, 10)
    mb = rng.randint(1, 10)
    return va, vb, n, ma, mb


def sweep_scales(scales, trials=300):
    rng = random.Random(2024)
    cases = [_rand_collision(rng) for _ in range(trials)]

    # float reference conservation error
    fp_mom, fp_ke = 0.0, 0.0
    for va, vb, n, ma, mb in cases:
        p0 = _momentum(va, vb, ma, mb)
        k0 = _ke(va, vb, ma, mb)
        va2, vb2 = collide_float(va, vb, n, ma, mb)
        p1 = _momentum(va2, vb2, ma, mb)
        k1 = _ke(va2, vb2, ma, mb)
        fp_mom = max(fp_mom, max(abs(p1[k] - p0[k]) for k in range(3)))
        fp_ke = max(fp_ke, abs(k1 - k0))

    rows = []
    for S in scales:
        mom_err, ke_err = 0.0, 0.0
        for va, vb, n, ma, mb in cases:
            # scale velocities to integers; use the normal direction as the
            # integer separation vector (scaled by S).
            iva = tuple(round(c * S) for c in va)
            ivb = tuple(round(c * S) for c in vb)
            d = tuple(round(c * S) for c in n)   # direction; magnitude ~ S
            p0 = _momentum(iva, ivb, ma, mb)
            k0 = _ke(iva, ivb, ma, mb)
            iva2, ivb2 = collide_fixed(iva, ivb, d, ma, mb, S)
            p1 = _momentum(iva2, ivb2, ma, mb)
            k1 = _ke(iva2, ivb2, ma, mb)
            # convert errors back to physical units
            mom_err = max(mom_err, max(abs(p1[k] - p0[k]) for k in range(3)) / S)
            ke_err = max(ke_err, abs(k1 - k0) / (S * S))
        rows.append({"scale_bits": round(math.log2(S)), "scale": S,
                     "max_momentum_err": mom_err, "max_ke_err": ke_err,
                     "meets_1e6_momentum": mom_err <= 1e-6})
        print("  S=2^%-2d  max|dp|=%.3e  max|dKE|=%.3e  meets 1e-6: %s"
              % (rows[-1]["scale_bits"], mom_err, ke_err,
                 rows[-1]["meets_1e6_momentum"]))
    return fp_mom, fp_ke, rows


def main():
    print("Q3: fixed-point fidelity for elastic collisions (P4 / PSF-02)")
    print("=" * 62)

    # PART 1 -- IEEE-754 audit (static facts about the kernel)
    audit = {
        "hot_path_ops": ["+", "-", "*", "/", "math.sqrt"],
        "correctly_rounded_portable": True,
        "portability_hazard": "mass ** (1.0/3.0)  (libm pow, not correctly "
                              "rounded; ~1 ulp variance possible across libms)",
        "hazard_location": "world.make_entity (radius), computed once per entity",
        "note": ("basic ops and sqrt are correctly-rounded per IEEE-754 and "
                 "bit-portable; only the cube-root pow is a cross-platform risk"),
    }
    print("PART 1 -- IEEE-754 audit:")
    print("   hot-path ops      : %s (all correctly-rounded, portable)"
          % ", ".join(audit["hot_path_ops"]))
    print("   portability hazard: %s" % audit["portability_hazard"])
    print("   -> a portable cbrt or fixed-point closes the only gap")

    # PART 2 -- fixed-point fidelity sweep
    print("PART 2 -- fixed-point conservation vs scale S:")
    scales = [2 ** k for k in (10, 14, 18, 22, 26, 30)]
    fp_mom, fp_ke, rows = sweep_scales(scales)
    min_bits = next((r["scale_bits"] for r in rows
                     if r["meets_1e6_momentum"]), None)
    print("   float reference   : max|dp|=%.3e  max|dKE|=%.3e" % (fp_mom, fp_ke))
    print("=" * 62)
    if min_bits is not None:
        verdict = ("Fixed-point preserves elastic-collision momentum to <= 1e-6 "
                   "for scale S >= 2^%d, with bit-identical (platform-independent) "
                   "integer arithmetic. Tradeoff: precision ~1/S vs max magnitude "
                   "~2^63/S (S=2^%d leaves ample range for MVW values O(1e2))."
                   % (min_bits, min_bits))
    else:
        verdict = "No tested scale met 1e-6; larger S (wider ints) required."
    print("VERDICT:", verdict)

    report = {
        "experiment": "Q3 fixed-point fidelity",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "ieee754_audit": audit,
        "float_reference": {"max_momentum_err": fp_mom, "max_ke_err": fp_ke},
        "fixed_point_sweep": rows,
        "min_scale_bits_for_1e6": min_bits,
        "verdict": verdict,
    }
    os.makedirs(_RESULTS, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(_RESULTS, "q3_fixed_point_%s.json" % stamp)
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    print("wrote %s" % os.path.relpath(path, os.path.join(_HERE, "..", "..")))
    return report


if __name__ == "__main__":
    main()
