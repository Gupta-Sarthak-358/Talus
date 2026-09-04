"""Evidence figures for docs/EVIDENCE_TALUS_COUNTERFACTUALS.md.

Reads data/sih26001/processed/counterfactual_*.csv +
data/sih26001/evidence/counterfactual_summary.json (built by
scripts/counterfactual_past_events.py) + the training matrix, and renders
presentation-ready PNGs into docs/evidence_figs/.

Model-performance numbers are transcribed from ml/sih26001/reports/*.md
(cited in the doc — this script plots, it does not recompute OOF).

Run: py scripts/make_evidence_figs.py (needs matplotlib/pandas/numpy/sklearn/joblib)
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
PROC = REPO / "data/sih26001/processed"
FIG = REPO / "docs/evidence_figs"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})
BAND_SPANS = [(0, 50, "#e8f3df", "Very Low"), (50, 65, "#f7f3d9", "Low"),
              (65, 75, "#fdecc8", "Moderate"), (75, 85, "#fdd9b5", "High"),
              (85, 100, "#f8d0d0", "Critical")]
NAVY = "#1f3a5f"
RED = "#c0392b"


def shade_bands(ax, ymin=0, ymax=100):
    for lo, hi, col, _ in BAND_SPANS:
        ax.axhspan(lo, hi, color=col, alpha=0.55, linewidth=0)


def load_case(cid):
    df = pd.read_csv(PROC / f"counterfactual_{cid}.csv", parse_dates=["date"])
    return df


def daily_panel(cid, title, event_label, markers=(), rain_ylim=None, fname=None):
    """Rain bars (twin) + calibrated score line + band shading + event/markers."""
    df = load_case(cid)
    fig, ax1 = plt.subplots(figsize=(10, 4.6))
    shade_bands(ax1)
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Talus score (calibrated P × 100)")
    ax1.plot(df.date, df.score, color=NAVY, lw=2.2, label="Talus score")
    ax1.scatter(df.date, df.score, color=NAVY, s=12, zorder=4)
    ax2 = ax1.twinx()
    ax2.bar(df.date, df.rain_24h, color="#5b8fc4", alpha=0.75, width=0.9, label="IMD 24h rain (mm)")
    ax2.set_ylabel("IMD daily rainfall (mm)")
    if rain_ylim:
        ax2.set_ylim(0, rain_ylim)
    for i, (mdate, mlabel, mcolor) in enumerate(markers):
        ax1.axvline(pd.Timestamp(mdate), color=mcolor, ls="--", lw=1.4)
        ax1.text(pd.Timestamp(mdate), 96 - 8 * (i % 2), mlabel, color=mcolor, fontsize=8.5,
                 ha="right" if "event" in mlabel.lower() else "left", va="top",
                 bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5))
    ax1.set_title(title, loc="left", fontweight="bold")
    fig.autofmt_xdate(rotation=30)
    fig.savefig(FIG / (fname or f"fig_{cid}.png"))
    plt.close(fig)


def main():
    summ = json.load(open(REPO / "data/sih26001/evidence/counterfactual_summary.json"))
    by_id = {c["id"]: c for c in summ["cases"]}

    # ---- Fig 1: lead-time summary (days in High+ / Critical+ within 30d pre-event)
    order = ["mangan-jun2024", "dipudara-aug2024", "sichey-jun2021", "lumsay-jun2022", "nh10-oct2022"]
    labels, highs, crits, notes = [], [], [], []
    for cid in order:
        df = load_case(cid)
        c = by_id[cid]
        n = len(df)
        highs.append(int((df.score >= 75).sum()))
        crits.append(int((df.score >= 85).sum()))
        tag = c["title"].split(",")[0]
        labels.append(tag + (" *" if c.get("event_date_fuzzy") else ""))
        notes.append("MISS — disclosed" if cid == "nh10-oct2022" else "")
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.barh(y, highs, color="#e67e22", alpha=0.85, label="days High or worse (≥75)")
    ax.barh(y, crits, color=RED, alpha=0.9, label="days Critical (≥85)")
    for i, (h, cr, nt) in enumerate(zip(highs, crits, notes)):
        ax.text(max(h, 1) + 0.4, i, f"{h}d / {cr}d  {nt}", va="center", fontsize=9)
    ax.set_yticks(y, labels)
    ax.set_xlabel(f"days out of {n} pre-event days at/above band")
    ax.set_title("Counterfactual warning coverage: days Talus would have held High/Critical before each slide",
                 loc="left", fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.95, loc="lower left", fontsize=9)
    ax.text(0.99, -0.22, "* fuzzy month-known date (June 2022 / ~8 June 2021) — peak-spell analysis, flagged",
            transform=ax.transAxes, ha="right", fontsize=8, color="#666")
    fig.savefig(FIG / "fig1_leadtime.png")
    plt.close(fig)

    # ---- Fig 2: Mangan daily
    daily_panel(
        "mangan-jun2024", "Mangan corridor, May–June 2024 — Talus score vs IMD rain (Mangan cell)",
        "event", markers=[("2024-06-13", "slides night Jun 12–13 (9 dead)", RED),
                          ("2024-06-13", "IMD red alert (reactive)", "#7d3c98")],
        rain_ylim=130, fname="fig2_mangan_daily.png")

    # ---- Fig 3: Dipudara daily (+ precursor window)
    df = load_case("dipudara-aug2024")
    fig, ax1 = plt.subplots(figsize=(10, 4.6))
    shade_bands(ax1)
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Talus score (calibrated P × 100)")
    ax1.axvspan(pd.Timestamp("2024-08-13"), pd.Timestamp("2024-08-19"), color="#f5c542", alpha=0.25)
    ax1.text(pd.Timestamp("2024-08-16"), 92, "7 days of precursor slides\n(manual evacuation)", ha="center",
             fontsize=8.5, bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
    ax1.plot(df.date, df.score, color=NAVY, lw=2.2)
    ax1.scatter(df.date, df.score, color=NAVY, s=12, zorder=4)
    ax2 = ax1.twinx()
    ax2.bar(df.date, df.rain_24h, color="#5b8fc4", alpha=0.75, width=0.9)
    ax2.set_ylabel("IMD daily rainfall (mm)")
    ax1.axvline(pd.Timestamp("2024-08-20"), color=RED, ls="--", lw=1.4)
    ax1.text(pd.Timestamp("2024-08-20"), 80, "main slide Aug 20, 07:30 (0 casualties — evacuated)", color=RED,
             fontsize=8.5, ha="right", va="top", bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5))
    ax1.set_title("Dipudara (Teesta-V), Jul–Aug 2024 — precursors arrived inside a standing Critical warning",
                  loc="left", fontweight="bold")
    fig.autofmt_xdate(rotation=30)
    fig.savefig(FIG / "fig3_dipudara_daily.png")
    plt.close(fig)

    # ---- Fig 4: fuzzy + miss mini-panels (Sichey, Lumsay, NH-10)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, cid, title in [
            (axes[0], "sichey-jun2021", "Sichey, May–Jun 2021\n(1 dead, date-fuzzy)"),
            (axes[1], "lumsay-jun2022", "Lumsay/Adampul, May–Jun 2022\n(month-known)"),
            (axes[2], "nh10-oct2022", "NH-10 19/20 Mile, Sep–Oct 2022\n(MISS — disclosed)")]:
        df = load_case(cid)
        for lo, hi, col, _ in BAND_SPANS:
            ax.axhspan(lo, hi, color=col, alpha=0.55, linewidth=0)
        ax.plot(df.date, df.score, color=NAVY, lw=1.8)
        ax2 = ax.twinx()
        ax2.bar(df.date, df.rain_24h, color="#5b8fc4", alpha=0.7, width=1.0)
        ev = by_id[cid]["event_date"]
        ax.axvline(pd.Timestamp(ev), color=RED, ls="--", lw=1.3)
        ax.set_title(title, fontsize=9.5)
        ax.tick_params(axis="x", labelsize=7)
        for lbl in ax.get_xticklabels():
            lbl.set_rotation(30)
    axes[0].set_ylabel("Talus score")
    axes[0].set_ylim(0, 100)
    fig.suptitle("Fuzzy-date cases peak inside the right spell; the October rockfall case is a disclosed miss",
                 fontweight="bold", x=0.02, ha="left")
    fig.subplots_adjust(top=0.80)
    fig.savefig(FIG / "fig4_fuzzy_miss.png")
    plt.close(fig)

    # ---- Fig 5: model performance (transcribed from ml/sih26001/reports/*.md,
    # retrained 2936-row Sikkim+Darjeeling matrix)
    models = ["LR", "RF", "XGB", "LGBM"]
    aucs = [0.8947, 0.8983, 0.9029, 0.9015]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.0))
    bars = a1.bar(models, aucs, color=["#95a5a6", NAVY, "#2e7d6f", "#6c7a89"])
    a1.axhline(0.96, color=RED, ls="--", lw=1.2, label="Dibang XGB 0.96 (published bar)")
    a1.set_ylim(0.8, 1.0)
    a1.set_ylabel("spatial-OOF AUC")
    a1.set_title("Discrimination (GroupKFold-8 OOF)", loc="left", fontweight="bold", fontsize=10)
    for b, v in zip(bars, aucs):
        a1.text(b.get_x() + b.get_width() / 2, v + 0.004, f"{v}", ha="center", fontsize=9)
    a1.legend(frameon=False, fontsize=8)
    cal = ["RF raw", "RF isotonic", "naive"]
    bv = [0.1254, 0.118, 0.25]
    bars2 = a2.bar(cal, bv, color=["#95a5a6", NAVY, "#d5d8dc"])
    a2.set_ylabel("Brier score (lower = better)")
    a2.set_title("Calibration", loc="left", fontweight="bold", fontsize=10)
    for b, v in zip(bars2, bv):
        a2.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v}", ha="center", fontsize=9)
    fig.suptitle("Talus Phase-1 model evidence (frozen bundle, reported 2026-09-04)", fontweight="bold", x=0.02, ha="left")
    fig.savefig(FIG / "fig5_model_perf.png")
    plt.close(fig)

    # ---- Fig 6: permutation importance (transcribed from metrics.md, retrained)
    imp = [("elevation", 0.0705), ("distance_to_road", 0.0332), ("ndvi", 0.0161),
           ("slope_angle", 0.0034), ("soil_moisture", 0.003), ("aspect", 0.0003),
           ("rainfall_24h_mm", 0.0001), ("rainfall_30d_mm", 0.0001),
           ("distance_to_river", 0.0), ("curvature", 0.0)]
    feats, vals = zip(*imp)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.barh(list(feats)[::-1], list(vals)[::-1], color=NAVY, alpha=0.85)
    ax.set_xlabel("permutation AUC drop (in-sample screening, RF full-data fit)")
    ax.set_title("What the model leans on: terrain + road proximity dominate; rain rides underneath",
                 loc="left", fontweight="bold")
    fig.savefig(FIG / "fig6_importance.png")
    plt.close(fig)

    # ---- Fig 7: June 2024 hyetograph Gangtok vs Mangan + Dahal line
    import xarray as xr
    ds = xr.open_dataset(str(REPO / "data/raw/imd/ind2024_rfp25.nc"))
    dates, gk, mg = [], [], []
    for day in pd.date_range("2024-06-01", "2024-06-20"):
        for lat, lon, store in [(27.34, 88.61, gk), (27.51, 88.53, mg)]:
            v = float(ds.RAINFALL.sel(LATITUDE=lat, LONGITUDE=lon, method="nearest")
                      .sel(TIME=day.strftime("%Y-%m-%d")).values)
            store.append(0.0 if v != v else v)
        dates.append(day)
    ds.close()
    x = np.arange(len(dates))
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.bar(x - 0.2, gk, 0.4, label="Gangtok cell (27.25, 88.50)", color="#5b8fc4", alpha=0.9)
    ax.bar(x + 0.2, mg, 0.4, label="Mangan cell (27.75, 88.50)", color=NAVY, alpha=0.9)
    ax.axhline(144, color=RED, ls="--", lw=1.4, label="Dahal–Hasegawa 144 mm/day")
    ax.axvspan(11.5, 13.5, color=RED, alpha=0.12)
    ax.text(12.5, 150, "slide nights Jun 12–13", ha="center", fontsize=9, color=RED)
    ax.text(12.5, 120, "Mangan station reported >220 mm/24h;\ngridded cell peaks at 108.9 (smoothing caveat)",
            ha="center", fontsize=8, style="italic",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
    ax.set_xticks(x[::2], [d.strftime("%m-%d") for d in dates[::2]])
    ax.set_ylabel("IMD daily rainfall (mm)")
    ax.set_title("June 2024: the disaster window in the repo's own rainfall archive", loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9)
    fig.savefig(FIG / "fig7_rain_compare.png")
    plt.close(fig)

    # ---- Fig 8: full-matrix score histogram (dynamic-range proof)
    import joblib as jl
    bnd = jl.load(str(REPO / "ml/models/sih26001_rf_v1.joblib"))
    iso2 = jl.load(str(REPO / "ml/models/sih26001_iso_v1.joblib"))["isotonic"]
    mat = pd.read_csv(str(REPO / "data/sih26001/processed/feature_matrix.training.csv"))
    NUM = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river", "drain_density"]
    X = mat[[c for c in NUM if c != "spi_log"] + ["lulc"]].copy()
    X["spi_log"] = np.log1p(mat["spi"].clip(lower=0))
    praw = bnd["model"].predict_proba(bnd["encoder"].transform(X))[:, 1]
    scal = np.clip(iso2.predict(praw), 0, 1) * 100
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.hist([scal[mat.event.to_numpy() == 0], scal[mat.event.to_numpy() == 1]],
            bins=20, stacked=True, color=["#5b8fc4", RED], alpha=0.85,
            label=["background (1468)", "inventoried slides (1468)"])
    for thr, nm in [(50, "Low"), (65, ""), (75, "High"), (85, "Critical")]:
        if nm:
            ax.axvline(thr, color="#333", ls=":", lw=1)
            ax.text(thr + 0.6, ax.get_ylim()[1] * 0.94, nm, fontsize=8)
    ax.set_xlabel("Talus score (calibrated P × 100, climatological rain)")
    ax.set_ylabel("training rows")
    ax.set_title("The gauge is not stuck: scores spread across bands (cases below sit in the red tail)",
                 loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9)
    fig.savefig(FIG / "fig8_score_hist.png")
    plt.close(fig)

    # ---- Fig 9: inventory map (training positives + pilot + case sites)
    side = pd.read_csv(str(REPO / "data/sih26001/processed/training_sidecar.csv"))
    pos = side.merge(mat[["zone_id", "event"]], on="zone_id")
    SLOPES = {"S1": (27.3450, 88.6000), "S2": (27.3380, 88.6120),
              "S3": (27.3250, 88.6065), "S4": (27.3150, 88.5950),
              "D1": (27.047, 88.263), "D2": (27.040, 88.275),
              "D3": (27.027, 88.2695), "D4": (27.017, 88.258),
              "N1": (27.695, 88.735), "N2": (27.688, 88.747),
              "N3": (27.675, 88.7415), "N4": (27.665, 88.730)}
    CASEPTS = {"Mangan Jun-24": (27.51, 88.53), "Dipudara Aug-24": (27.2525, 88.4606),
               "Lumsay Jun-22": (27.3263, 88.5954), "Sichey Jun-21": (27.3379, 88.6094),
               "NH-10 Oct-22": (27.13, 88.51)}
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    ax.scatter(pos.loc[pos.event == 0, "lon"], pos.loc[pos.event == 0, "lat"], s=6, c="#5b8fc4",
               alpha=0.5, label="background (1468)")
    ax.scatter(pos.loc[pos.event == 1, "lon"], pos.loc[pos.event == 1, "lat"], s=10, c=RED,
               alpha=0.65, label="inventoried slides (1468)")
    for zid, (la, lo) in SLOPES.items():
        ax.scatter([lo], [la], s=110, marker="*", c="#f5b301", edgecolors="black", linewidths=0.8, zorder=5)
    for nm, (la, lo) in CASEPTS.items():
        ax.scatter([lo], [la], s=90, marker="X", c="black", zorder=5)
    # hand-staggered labels: the Gangtok cluster is dense (S2/Sichey ~40 m apart)
    _OFF = {"S1": (0.010, 0.010), "S2": (0.010, 0.004), "S3": (-0.062, -0.004), "S4": (-0.062, 0.004),
            "D1": (0.010, 0.004), "D2": (0.010, 0.004), "D3": (-0.062, -0.004), "D4": (-0.062, 0.004),
            "N1": (0.010, 0.004), "N2": (0.010, 0.004), "N3": (-0.062, -0.004), "N4": (-0.062, 0.004),
            "Mangan Jun-24": (0.010, 0.004), "Dipudara Aug-24": (0.010, 0.004),
            "Lumsay Jun-22": (-0.075, -0.016), "Sichey Jun-21": (0.010, -0.020),
            "NH-10 Oct-22": (0.010, 0.004)}
    for zid, (la, lo) in SLOPES.items():
        dx, dy = _OFF[zid]
        ax.text(lo + dx, la + dy, zid, fontsize=9, fontweight="bold")
    for nm, (la, lo) in CASEPTS.items():
        dx, dy = _OFF[nm]
        ax.text(lo + dx, la + dy, nm, fontsize=8)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title("Evidence geography: 1,468 GSI slides, 12 pilot slopes, 5 counterfactual sites",
                 loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    ax.set_aspect("equal", adjustable="datalim")
    fig.savefig(FIG / "fig9_inventory_map.png")
    plt.close(fig)

    print("wrote 9 figures ->", FIG)


def fig_dynamic_inputs():
    """Fig 10: what actually moved — daily CCI soil (2024 cases) + event NDVI vs matrix NDVI."""
    dyn = json.load(open(REPO / "data/sih26001/processed/counterfactual_dynamic.json"))["cases"]
    summ = json.load(open(REPO / "data/sih26001/evidence/counterfactual_summary.json"))
    mat_all = pd.read_csv(str(REPO / "data/sih26001/processed/feature_matrix.training.csv"))
    mat_ndvi_by_row = dict(zip(mat_all.zone_id, mat_all.ndvi))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    for cid, label, color in [("mangan-jun2024", "Mangan (May 14–Jun 13)", NAVY),
                              ("dipudara-aug2024", "Dipudara (Jul 21–Aug 20)", "#2e7d6f")]:
        s = dyn[cid]["soil"]
        dates = sorted(s)
        x = [(pd.Timestamp(d) - pd.Timestamp(dates[-1])).days for d in dates]  # days before event
        y = [s[d] if s[d] is not None else np.nan for d in dates]
        a1.plot(x, y, "o-", color=color, ms=3.5, lw=1.6, label=label)
    a1.set_xlabel("days before slide")
    a1.set_ylabel("CCI soil moisture (m³/m³, daily observed)")
    a1.set_title("Soil moved: observed daily wetting", loc="left",
                 fontweight="bold", fontsize=10)
    a1.legend(frameon=False, fontsize=9)
    cases = ["Mangan\nJun-24", "Dipudara\nAug-24", "Lumsay\nJun-22", "Sichey\nJun-21", "NH-10\nOct-22"]
    cids = ["mangan-jun2024", "dipudara-aug2024", "lumsay-jun2022", "sichey-jun2021", "nh10-oct2022"]
    by_id = {c["id"]: c for c in summ["cases"]}
    # Matrix-analogue NDVI looked up live (analogues move when the matrix grows).
    mat_ndvi = [round(float(mat_ndvi_by_row[by_id[c]["terrain_analogue_row"]]), 3) for c in cids]
    ev_ndvi = [0.753, 0.852, 0.271, 0.322, 0.891]
    scenes = ["S2 03-May-24", "S2 16-Aug-24", "S2 24-Apr-22", "S2 14-Apr-21", "S2 01-Oct-22"]
    x = np.arange(len(cases))
    a2.bar(x - 0.2, mat_ndvi, 0.4, label="matrix quasi-static", color="#95a5a6", alpha=0.9)
    a2.bar(x + 0.2, ev_ndvi, 0.4, label="event-contemporary scene", color=NAVY, alpha=0.9)
    for i, sc in enumerate(scenes):
        a2.text(i, max(mat_ndvi[i], ev_ndvi[i]) + 0.03, sc, ha="center", fontsize=7, color="#444")
    a2.set_xticks(x, cases, fontsize=8.5)
    a2.set_ylabel("NDVI (SCL-gated point read)")
    a2.set_ylim(0, 1.1)
    a2.set_title("Vegetation moved: pre-event scenes", loc="left",
                 fontweight="bold", fontsize=10)
    a2.legend(frameon=False, fontsize=9)
    fig.suptitle("Not only rainfall: soil moisture ran daily, NDVI came from pre-event scenes",
                 fontweight="bold", x=0.02, ha="left")
    fig.savefig(FIG / "fig10_dynamic_inputs.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
    fig_dynamic_inputs()
    print("wrote fig10 ->", FIG / "fig10_dynamic_inputs.png")
