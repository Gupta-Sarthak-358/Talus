"""Phase 1B+1C verification plots.

Visual ground-truth for the Phase 1B+1C definition of done:
- rainfall: wet-day intensity curve and monthly means vs the 2000-2024 IMD grounding
- terrain/geology: per-zone static engineering geometry and material properties
- groundwater: rainfall -> pore-pressure lag/persistence; aquifer thrust per zone
- blast: PPV-vs-charge scatter (locked NIRM constants) and frequency histogram
Only called after the generator has produced real physics fields (1B+).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from generator_schema import BASE_DIR, ZONES
from rainfall.sampler import RAINFALL_CSV

SUMMARY_2000 = BASE_DIR / "data" / "processed" / "imd" / "analysis" / "monthly_stats_2000_2024.csv"


def rain_plots(df, out_dir):
    hist = pd.read_csv(RAINFALL_CSV, parse_dates=["timestamp"])
    wet_hist = hist[hist["rainfall_mm"] > 0]["rainfall_mm"].sort_values(ascending=False).values
    wet_gen = df[df["rainfall_mm"] > 0]["rainfall_mm"].sort_values(ascending=False).values

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(np.arange(1, len(wet_hist) + 1), wet_hist, label="IMD 2000-2024 wet days")
    ax.plot(np.arange(1, len(wet_gen) + 1), wet_gen, label="generator v1.1.0 (seed 42)", alpha=0.8)
    ax.set_yscale("log")
    ax.set_xlabel("Rank (descending)")
    ax.set_ylabel("Daily rainfall (mm, log)")
    ax.set_title("Wet-day intensity: grounding vs generator Phase 1B")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "rainfall_wet_intensity_1B.png", dpi=150)
    plt.close(fig)

    monthly = pd.read_csv(SUMMARY_2000)
    h_mean = monthly.set_index("timestamp")["mean_daily"]
    g_month = df.assign(m=df["timestamp"].dt.month).groupby("m")["rainfall_mm"].mean()
    x = np.arange(1, 13)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - 0.2, h_mean.reindex(x).values, 0.4, label="IMD 2000-2024", color="#4c72b0")
    ax.bar(x + 0.2, g_month.reindex(x).values, 0.4, label="generator v1.1.0 (seed 42)", color="#c44e52")
    ax.set_xticks(x)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean daily rainfall (mm)")
    ax.set_title("Monthly mean daily rainfall: grounding vs generator Phase 1B")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "rainfall_monthly_1B.png", dpi=150)
    plt.close(fig)


def zone_plots(df, out_dir):
    zones = list(ZONES)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    angles = [df[df["zone_id"] == z]["slope_angle_deg"].iloc[0] for z in zones]
    heights = [df[df["zone_id"] == z]["slope_height_m"].iloc[0] for z in zones]
    ax = axes[0]
    x = np.arange(len(zones))
    ax.bar(x - 0.2, angles, 0.4, label="slope_angle_deg", color="#c44e52")
    ax.bar(x + 0.2, heights, 0.4, label="slope_height_m", color="#4c72b0")
    ax.set_xticks(x)
    ax.set_xticklabels(zones, rotation=15)
    ax.set_ylabel("deg / m")
    ax.set_title("Zone engineering geometry (static, 1B)")
    ax.legend()

    materials = [df[df["zone_id"] == z]["material_class"].iloc[0] for z in zones]
    cohesion = [df[df["zone_id"] == z]["cohesion_kpa"].iloc[0] for z in zones]
    friction = [df[df["zone_id"] == z]["friction_angle_deg"].iloc[0] for z in zones]
    ax = axes[1]
    ax.bar(x - 0.2, cohesion, 0.4, label="cohesion_kpa", color="#55a868")
    ax.bar(x + 0.2, friction, 0.4, label="friction_angle_deg", color="#dd8452")
    for i, m in enumerate(materials):
        ax.text(i, 0, m, rotation=90, ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(zones, rotation=15)
    ax.set_ylabel("kPa / deg")
    ax.set_title("Zone geology (static, 1B)")
    ax.legend()

    fig.tight_layout()
    fig.savefig(out_dir / "zone_structure_1B.png", dpi=150)
    plt.close(fig)


def groundwater_plots(df, out_dir):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    gw = df[df["zone_id"] == "ZONE_D"].set_index("timestamp")  # confined-aquifer zone burst risk
    rain = df.groupby("timestamp")["rainfall_mm"].first()

    ax = axes[0]
    ax.plot(rain.index, rain.values, label="daily rainfall (mm)", color="#4c72b0", alpha=0.5)
    ax.plot(gw.index, gw["pore_pressure_kpa"], label="pore pressure (kPa, ZONE_D)", color="#c44e52")
    ax.set_xlabel("Date")
    ax.set_ylabel("mm / kPa")
    ax.set_title("Groundwater: rainfall -> pore pressure (lag/persistence, 1C)")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=30, labelsize=8)

    ax = axes[1]
    zones = list(ZONES)
    thrust = [df[df["zone_id"] == z]["groundwater_thrust_kpa"].iloc[0] for z in zones]
    x = np.arange(len(zones))
    ax.bar(x, thrust, color="#55a868")
    ax.set_xticks(x)
    ax.set_xticklabels(zones, rotation=15)
    ax.set_ylabel("groundwater thrust (kPa)")
    ax.set_title("Aquifer thrust per zone (D = confined below lignite, 1C)")
    fig.tight_layout()
    fig.savefig(out_dir / "groundwater_1C.png", dpi=150)
    plt.close(fig)


def blast_plots(df, out_dir):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    bl = df[df["blast_occurs"] & (df["zone_id"] == "ZONE_A")]

    ax = axes[0]
    ax.scatter(bl["charge_per_delay_kg"], bl["blast_vibration_ppv_mms"], s=6, alpha=0.4, color="#4c72b0")
    ax.set_xlabel("charge per delay (kg)")
    ax.set_ylabel("observed PPV (mm/s)")
    ax.set_title("PPV vs charge (ZONE_A, D=300 m): PPV=858.9*(D/√W)^-1.58 + scatter, 1C")
    ax.tick_params(axis="x", rotation=0, labelsize=8)

    ax = axes[1]
    ax.hist(bl["dominant_frequency_hz"], bins=30, color="#c44e52", alpha=0.8)
    ax.axvline(8, color="k", ls="--", lw=0.8)
    ax.axvline(25, color="k", ls="--", lw=0.8)
    ax.set_xlabel("dominant frequency (Hz)")
    ax.set_ylabel("events")
    ax.set_title("Dominant frequency (5-27 Hz, P(<8Hz)=45%; DGMS bands marked)")
    fig.tight_layout()
    fig.savefig(out_dir / "blast_1C.png", dpi=150)
    plt.close(fig)


def crack_plots(df, out_dir):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    colors = {"ZONE_A": "#4c72b0", "ZONE_B": "#c44e52", "ZONE_C": "#55a868", "ZONE_D": "#8172b2"}

    ax = axes[0]
    for z in ZONES:
        zz = df[df["zone_id"] == z].set_index("timestamp")
        ax.plot(zz.index, zz["crack_depth_m"], label=z, color=colors[z])
    ax.set_ylabel("crack depth (m)")
    ax.set_title("Crack depth ratchets with damage (memory, never resets), 1D")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=30, labelsize=8)

    ax = axes[1]
    for z in ZONES:
        zz = df[df["zone_id"] == z].set_index("timestamp")
        ax.plot(zz.index, zz["crack_growth_rate_mm_day"], label=z, color=colors[z], alpha=0.8)
    ax.set_ylabel("growth rate (mm/day)")
    ax.set_title("Growth rate: temporary spikes that feed cumulative damage, 1D")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=30, labelsize=8)

    ax = axes[2]
    fams = ["tension_crest", "blast_induced", "seepage", "desiccation", "floor_heave"]
    widths = [int(df[(df["zone_id"] == z) & (df["crack_family"] == f)].shape[0]) for z, f in
              [(z, f) for z in ZONES for f in fams]]
    data = np.zeros((len(ZONES), len(fams)), dtype=int)
    for i, z in enumerate(ZONES):
        for j, f in enumerate(fams):
            data[i, j] = int(df[(df["zone_id"] == z) & (df["crack_family"] == f)].shape[0])
    im = ax.imshow(data, aspect="auto", cmap="Blues")
    ax.set_xticks(np.arange(len(fams)))
    ax.set_xticklabels(fams, rotation=25, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(ZONES)))
    ax.set_yticklabels(ZONES, fontsize=8)
    ax.set_title("Crack family by zone (dominant driver), 1D")
    for i in range(len(ZONES)):
        for j in range(len(fams)):
            if data[i, j]:
                ax.text(j, i, str(data[i, j]), ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(out_dir / "cracks_1D.png", dpi=150)
    plt.close(fig)


def make_plots(df, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rain_plots(df, out_dir)
    zone_plots(df, out_dir)
    groundwater_plots(df, out_dir)
    blast_plots(df, out_dir)
    crack_plots(df, out_dir)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from generator_v1 import build_internal_state, build_timeline

    timeline = build_timeline("2024-01-01", 365)
    df = build_internal_state(timeline, 42)
    out = BASE_DIR / "data" / "processed" / "generator_v1" / "plots"
    make_plots(df, out)
    print("plots written to", out)