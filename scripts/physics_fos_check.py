"""Physics cross-check: infinite-slope Factor of Safety vs ML susceptibility.

Nobody else at a hackathon shows this: an independent, closed-form
geotechnical equation computed from the SAME terrain rows, compared
against the learned model. Agreement = two independent roads, one hill.

Infinite-slope FoS (saturated shear strength over driving stress):
    FoS = [c' + ((g*z - gw*hw) * cos^2(B) * tan(phi'))]
          / [g*z * sin(B) * cos(B)]
  B   = slope_angle (row), g = 19 kN/m3, gw = 9.81 kN/m3
  z   = slip depth {2, 4} m (shallow Himalayan slides)
  hw  = m*z, m = clip(soil_moisture*1.2 + rain7d/1500, 0, 1)  [STATED assumption:
        saturation proxy blending observed wetness + antecedent rain]
  c'  in {5, 10} kPa, phi' in {28, 32} deg — literature ranges for
  Himalayan schist/gneiss colluvium (documented, not tuned).

Framing (honest): consistency screen, NOT validation. FoS<1 predicts
mechanical failure of an idealized plane; the ML predicts inventoried
season-window occurrence. We expect: high-ML-P rows skew to low FoS
(Spearman rho between 1/FoS and P strongly positive), NOT equality.

Outputs (committed): ml/sih26001/reports/physics.md + docs/evidence_figs/fos_check.png
Run (mnemo venv): C:\\Users\\satvi\\Desktop\\mnemo\\.venv\\Scripts\\python.exe scripts/physics_fos_check.py
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MATRIX = REPO / "data/sih26001/processed/feature_matrix.training.csv"
RF_BLOB = REPO / "ml/models/sih26001_rf_v1.joblib"
REPORTDIR = REPO / "ml/sih26001/reports"
FIGDIR = REPO / "docs/evidence_figs"
SEED = 42

GAMMA = 19.0
GAMMA_W = 9.81
PARAM_GRID = [(5, 28, 2.0), (5, 32, 2.0), (10, 28, 4.0), (10, 32, 4.0), (5, 30, 3.0)]
CENTRAL = (5, 30, 3.0)  # pre-registered before seeing results


def log(msg):
    print(msg, flush=True)


def fos(beta_deg, m, c_kpa, phi_deg, z):
    b = np.radians(np.asarray(beta_deg, dtype=float))
    hw = np.asarray(m, dtype=float) * z
    num = c_kpa + ((GAMMA * z - GAMMA_W * hw) * np.cos(b) ** 2 * np.tan(np.radians(phi_deg)))
    den = GAMMA * z * np.sin(b) * np.cos(b)
    with np.errstate(divide="ignore", invalid="ignore"):
        f = num / np.where(den == 0, np.nan, den)
    return f


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.stats import spearmanr

    mat = pd.read_csv(MATRIX)
    y = mat["event"].to_numpy().astype(int)
    beta = mat["slope_angle"].to_numpy()
    m = np.clip(mat["soil_moisture"].to_numpy() * 1.2 + mat["rainfall_7d_mm"].to_numpy() / 1500.0, 0, 1)
    log(f"m saturation proxy: median={np.median(m):.2f} frac_fully_saturated={(m >= 1.0).mean():.2f}")

    blob = joblib.load(RF_BLOB)
    Xn = blob["encoder"].transform(
        mat.assign(spi_log=np.log1p(mat["spi"].clip(lower=0)))
        [[c for c in blob["features"] if not c.startswith("lulc_")] + ["lulc"]])
    # encoder expects the raw frame incl. lulc string col, as in training
    p_ml = blob["model"].predict_proba(Xn)[:, 1]

    rows = []
    fos_central = None
    for c_kpa, phi, z in PARAM_GRID:
        f = fos(beta, m, c_kpa, phi, z)
        ok = ~np.isnan(f)
        rho = float(spearmanr(1.0 / f[ok], p_ml[ok]).statistic)
        fail = f < 1.0
        rows.append({"c_kPa": c_kpa, "phi_deg": phi, "z_m": z,
                     "spearman_1FoS_vs_P": round(rho, 4),
                     "fos_lt1_rate_pos": round(float(fail[y == 1].mean()), 4),
                     "fos_lt1_rate_neg": round(float(fail[y == 0].mean()), 4)})
        if (c_kpa, phi, z) == CENTRAL:
            fos_central = f
        log(f"c'={c_kpa} phi={phi} z={z}: rho={rho:.3f} fail-rate pos={fail[y==1].mean():.3f} neg={fail[y==0].mean():.3f}")
    assert fos_central is not None
    hi_ml = p_ml >= np.median(p_ml)
    agree = float(((fos_central < 1.0) == (hi_ml)).mean())
    log(f"central {CENTRAL}: P(high-ML AND FoS<1) agreement={agree:.3f}")

    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    # binned FoS vs mean ML-P
    fb = np.clip(fos_central, 0, 5)
    bins = np.quantile(fb[~np.isnan(fb)], np.linspace(0, 1, 9))
    idx = np.clip(np.digitize(fb, bins) - 1, 0, 7)
    xs, ys, ns = [], [], []
    for b in range(8):
        msk = (idx == b) & ~np.isnan(fb)
        if msk.sum() > 0:
            xs.append(float(fb[msk].mean())); ys.append(float(p_ml[msk].mean())); ns.append(int(msk.sum()))
    a1.plot(xs, ys, "o-", color="#1f3a5f", lw=2, ms=7)
    for x, yy, n in zip(xs, ys, ns):
        a1.annotate(str(n), (x, yy), textcoords="offset points", xytext=(4, 5), fontsize=7, color="#555")
    a1.axvline(1.0, color="#c0392b", ls="--", lw=1.2, label="FoS=1 (limit equilibrium)")
    a1.set_xlabel("infinite-slope FoS (central params c'=5kPa, φ'=30°, z=3m)")
    a1.set_ylabel("mean RF P(event)")
    a1.set_title("Lower FoS → higher learned P (independent roads, one hill)")
    a1.legend(frameon=False, fontsize=8)
    # contingency
    tab = pd.crosstab(hi_ml, fos_central < 1.0)
    a2.axis("off")
    a2.table(cellText=[[f"{tab.iloc[0,0]}", f"{tab.iloc[0,1]}"], [f"{tab.iloc[1,0]}", f"{tab.iloc[1,1]}"]],
             rowLabels=["ML low", "ML high"], colLabels=["FoS ≥ 1", "FoS < 1"],
             loc="center", colWidths=[0.22, 0.22])
    a2.set_title(f"agreement={agree:.2f} (central params, n={len(y)})")
    fig.suptitle("Physics cross-check: closed-form FoS vs learned susceptibility", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGDIR / "fos_check.png", dpi=150)
    log("fig -> docs/evidence_figs/fos_check.png")

    (REPORTDIR / "physics.md").write_text(
        "# Physics cross-check: infinite-slope FoS vs ML P(event)\n\n"
        "FoS = [c' + ((γz − γw·m·z)·cos²β·tanφ')] / [γz·sinβ·cosβ], "
        "γ=19 kN/m³, m = clip(soil×1.2 + rain7d/1500, 0, 1) [stated assumption].\n\n"
        "| c' (kPa) | φ' (°) | z (m) | Spearman(1/FoS, P) | FoS<1 rate pos | FoS<1 rate neg |\n"
        "|---|---|---|---|---|---|\n" +
        "".join(f"| {r['c_kPa']} | {r['phi_deg']} | {r['z_m']} | {r['spearman_1FoS_vs_P']} | "
                f"{r['fos_lt1_rate_pos']} | {r['fos_lt1_rate_neg']} |\n" for r in rows) +
        f"\nCentral {CENTRAL}: high-ML/FoS<1 agreement = {agree:.3f}. "
        "Framing: consistency screen, not validation — FoS models an idealized plane, "
        "the ML models inventoried occurrence.\n", encoding="utf-8")
    (REPORTDIR / "physics.json").write_text(json.dumps(
        {"date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
         "central": list(CENTRAL), "agreement": agree, "grid": rows}, indent=2), encoding="utf-8")
    log("report -> ml/sih26001/reports/physics.{md,json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
