from pathlib import Path

import argparse
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CSV = BASE_DIR / "data" / "processed" / "imd" / "neyveli_rainfall_2000_2024.csv"
DEFAULT_START = 2000
DEFAULT_END = 2024

HEAVY_RAIN_MM = 64.5
ROLLING_WINDOWS = {"1d": 1, "3d": 3, "7d": 7}
DIST_QUANTILES = [0.50, 0.75, 0.90, 0.95, 0.99, 0.995, 0.999]
ROLL_QUANTILES = [0.50, 0.90, 0.95, 0.99]
TOP_N_EXTREMES = 20


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze Neyveli IMD daily rainfall")
    parser.add_argument("--input", default=str(DEFAULT_CSV))
    parser.add_argument("--start", type=int, default=DEFAULT_START)
    parser.add_argument("--end", type=int, default=DEFAULT_END)
    return parser.parse_args()


def quantile_stats(series, quantiles):
    out = {}
    for q in quantiles:
        out[f"p{q * 100:g}".replace(".", "_") if q != int(q) else f"p{int(q * 100)}"] = round(
            float(series.quantile(q)), 4
        )
    out["maximum"] = round(float(series.max()), 4)
    out["mean"] = round(float(series.mean()), 4)
    out["std"] = round(float(series.std(ddof=0)), 4)
    return out


def main():
    args = parse_args()

    output_root = BASE_DIR / "data" / "processed" / "imd" / "analysis"
    plots_dir = output_root / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    label = f"{args.start}_{args.end}"
    summary_path = output_root / f"summary_{label}.json"
    monthly_path = output_root / f"monthly_stats_{label}.csv"
    annual_path = output_root / f"annual_stats_{label}.csv"
    extremes_path = output_root / f"extremes_{label}.csv"

    df = pd.read_csv(args.input, parse_dates=["timestamp"])
    df = df[(df["timestamp"].dt.year >= args.start) & (df["timestamp"].dt.year <= args.end)]
    df = df.sort_values("timestamp").reset_index(drop=True)

    df["rainfall_1d"] = df["rainfall_mm"]
    for name, window in ROLLING_WINDOWS.items():
        if window == 1:
            continue
        df[f"rainfall_{name}"] = df["rainfall_mm"].rolling(window).sum()

    rainfall = df["rainfall_mm"]
    wet = rainfall[rainfall > 0]

    integrity = {
        "observations": int(len(df)),
        "start": str(df["timestamp"].min().date()),
        "end": str(df["timestamp"].max().date()),
        "missing_values": int(rainfall.isna().sum()),
        "duplicate_dates": int(df["timestamp"].duplicated().sum()),
        "negative_values": int((rainfall < 0).sum()),
        "zero_rain_days": int((rainfall == 0).sum()),
        "zero_rain_pct": round(float((rainfall == 0).mean()) * 100, 4),
        "wet_days": int((rainfall > 0).sum()),
        "wet_day_pct": round(float((rainfall > 0).mean()) * 100, 4),
    }

    distribution = {
        "all_days": quantile_stats(rainfall, DIST_QUANTILES),
        "wet_days": quantile_stats(wet, DIST_QUANTILES),
    }

    rolling = {}
    for name in ROLLING_WINDOWS:
        rolling[name] = quantile_stats(df[f"rainfall_{name}"].dropna(), ROLL_QUANTILES)

    annual = (
        df.assign(year=df["timestamp"].dt.year)
        .groupby("year")["rainfall_mm"]
        .agg(
            annual_total="sum",
            mean_daily="mean",
            wet_days=lambda s: (s > 0).sum(),
            heavy_rain_days=lambda s: (s >= HEAVY_RAIN_MM).sum(),
            max_daily="max",
            obs="count",
        )
        .round(4)
        .reset_index()
    )
    annual.to_csv(annual_path, index=False)

    annual_totals = annual["annual_total"]
    annual_quantiles = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
    annual_distribution = {}
    for q in annual_quantiles:
        annual_distribution[f"p{int(q * 100):02d}"] = round(float(annual_totals.quantile(q)), 4)
    annual_distribution["mean"] = round(float(annual_totals.mean()), 4)
    annual_distribution["std"] = round(float(annual_totals.std(ddof=0)), 4)
    annual_distribution["min"] = round(float(annual_totals.min()), 4)
    annual_distribution["max"] = round(float(annual_totals.max()), 4)

    year_thresholds = [500, 750, 1000, 1500, 2000, 2500]
    year_counts = {}
    for th in year_thresholds:
        year_counts[f"below_{th}"] = int((annual_totals < th).sum())
        year_counts[f"above_{th}"] = int((annual_totals > th).sum())
    year_counts["total_years"] = int(len(annual_totals))

    monthly = (
        df.assign(month=df["timestamp"].dt.month)["rainfall_mm"]
        .groupby(df["timestamp"].dt.month)
        .agg(
            total="sum",
            mean_daily="mean",
            p90=lambda s: s.quantile(0.90),
            p95=lambda s: s.quantile(0.95),
            median="median",
            wet_days=lambda s: (s > 0).sum(),
            obs="count",
        )
        .reset_index()
    )
    monthly["wet_day_freq"] = (monthly["wet_days"] / monthly["obs"]).round(4)
    monthly = monthly.round(4)
    monthly.to_csv(monthly_path, index=False)

    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month

    extremes = df.nlargest(TOP_N_EXTREMES, "rainfall_1d").copy()
    extremes = extremes.reset_index(drop=True)
    extremes.insert(0, "rank", range(1, len(extremes) + 1))
    extremes = extremes[
        ["rank", "timestamp", "rainfall_1d", "rainfall_3d", "rainfall_7d", "year", "month"]
    ].round(4)
    extremes.to_csv(extremes_path, index=False)

    summary = {
        "analysis_label": label,
        "source_file": args.input,
        "target": "Neyveli IMD grid point 11.50N 79.50E",
        "unit": "mm/day",
        "integrity": integrity,
        "distribution": distribution,
        "rolling_windows_mm": rolling,
        "annual_mean_mm": round(float(df["rainfall_mm"].mean()), 4),
        "annual_total_mm": round(float(df["rainfall_mm"].sum()), 4),
        "annual_min_mm": round(float(annual["annual_total"].min()), 4),
        "annual_max_mm": round(float(annual["annual_total"].max()), 4),
        "annual_std_mm": round(float(annual["annual_total"].std(ddof=0)), 4),
        "annual_distribution_mm": annual_distribution,
        "annual_year_counts": year_counts,
        "heavy_rain_threshold_mm": HEAVY_RAIN_MM,
        "top_extremes_summary": {
            "top1": {
                "date": str(extremes.iloc[0]["timestamp"].date()),
                "rain_1d_mm": float(extremes.iloc[0]["rainfall_1d"]),
                "rain_3d_mm": float(extremes.iloc[0]["rainfall_3d"]),
                "rain_7d_mm": float(extremes.iloc[0]["rainfall_7d"]),
            },
            "top1_pct_of_years_total": round(
                float(extremes.iloc[0]["rainfall_1d"])
                / float(df[df["year"] == extremes.iloc[0]["year"]]["rainfall_mm"].sum())
                * 100,
                4,
            ),
        },
        "files": {
            "monthly": str(monthly_path.relative_to(BASE_DIR)),
            "annual": str(annual_path.relative_to(BASE_DIR)),
            "extremes": str(extremes_path.relative_to(BASE_DIR)),
        },
    }

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    make_plots(df, monthly, annual, plots_dir, label)

    print(json.dumps(
        {
            "summary": {
                "observations": integrity["observations"],
                "start": integrity["start"],
                "end": integrity["end"],
                "missing": integrity["missing_values"],
                "duplicates": integrity["duplicate_dates"],
                "zero_pct": integrity["zero_rain_pct"],
                "wet_pct": integrity["wet_day_pct"],
                "mean_daily_all_days_mm": distribution["all_days"]["mean"],
                "mean_daily_wet_days_mm": distribution["wet_days"]["mean"],
                "annual_min_mm": summary["annual_min_mm"],
                "annual_max_mm": summary["annual_max_mm"],
                "annual_mean_mm": summary["annual_mean_mm"],
            }
        },
        indent=2,
    ))
    print()
    print("=== TOP %d EXTREME DAYS ===" % TOP_N_EXTREMES)
    print(
        extremes.to_string(
            index=False,
            formatters={"rainfall_1d": "{:.2f}".format, "rainfall_3d": "{:.2f}".format, "rainfall_7d": "{:.2f}".format},
        )
    )
    print()
    print(f"Summary: {summary_path}")
    print(f"Plots:   {plots_dir}")


def make_plots(df, monthly, annual, plots_dir, label):
    rainfall = df["rainfall_mm"]
    wet = rainfall[rainfall > 0]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(rainfall, bins=80, range=(0, rainfall.quantile(0.999)), color="#4c72b0", alpha=0.85)
    ax.set_xlabel("Daily rainfall (mm)")
    ax.set_ylabel("Days")
    ax.set_title(f"Daily rainfall distribution ({label})")
    fig.tight_layout()
    fig.savefig(plots_dir / f"histogram_daily_{label}.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(wet) + 1), np.sort(wet.values)[::-1], color="#c44e52")
    ax.set_yscale("log")
    ax.set_xlabel("Rank (wet days, descending)")
    ax.set_ylabel("Daily rainfall (mm, log)")
    ax.set_title(f"Wet-day intensity curve (log) ({label})")
    fig.tight_layout()
    fig.savefig(plots_dir / f"wet_day_intensity_{label}.png", dpi=150)
    plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(monthly.index + 1, monthly["mean_daily"], color="#4c72b0", alpha=0.85)
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Mean daily rainfall (mm)")
    ax1.set_title(f"Monthly seasonality ({label})")
    ax1.set_xticks(range(1, 13))
    ax2 = ax1.twinx()
    ax2.plot(monthly.index + 1, monthly["wet_day_freq"], color="#c44e52", marker="o", ls="--")
    ax2.set_ylabel("Wet-day frequency")
    fig.tight_layout()
    fig.savefig(plots_dir / f"monthly_seasonality_{label}.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(annual["year"], annual["annual_total"], color="#4c72b0", alpha=0.85)
    ax.axhline(annual["annual_total"].mean(), color="#c44e52", ls="--", label="mean")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual total (mm)")
    ax.set_title(f"Annual totals ({label})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(plots_dir / f"annual_totals_{label}.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()