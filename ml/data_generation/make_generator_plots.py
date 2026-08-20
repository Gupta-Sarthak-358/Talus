"""Phase 1B verification plots.

Visual ground-truth for the Phase 1B definition of done:
- rainfall: wet-day intensity curve and monthly means vs the 2000-2024 IMD grounding
- terrain/geology: per-zone static engineering geometry and material properties
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


def make_plots(df, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rain_plots(df, out_dir)
    zone_plots(df, out_dir)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from generator_v1 import build_internal_state, build_timeline

    timeline = build_timeline("2024-01-01", 365)
    df = build_internal_state(timeline, 42)
    out = BASE_DIR / "data" / "processed" / "generator_v1" / "plots"
    make_plots(df, out)
    print("plots written to", out)