from pathlib import Path

import argparse
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = BASE_DIR / "data" / "processed" / "imd" / "neyveli_rainfall_2000_2024.csv"
DEFAULT_SEED = 42
DEFAULT_YEARS = 25

ROLL_WINDOWS = {"3d": 3, "7d": 7}
DIST_QUANTILES = [0.50, 0.90, 0.95, 0.99, 0.995, 0.999]
LABEL = "prototype_v0"


def parse_args():
    parser = argparse.ArgumentParser(description="Talus prototype_v0 rainfall sampler")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--years", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--samples", type=int, default=5)
    return parser.parse_args()


def quantile_stats(series, quantiles):
    out = {}
    for q in quantiles:
        name = f"p{q * 100:g}".replace(".", "_")
        out[name] = round(float(series.quantile(q)), 4)
    out["max"] = round(float(series.max()), 4)
    out["mean"] = round(float(series.mean()), 4)
    out["zero_pct"] = round(float((series == 0).mean()) * 100, 4)
    return out


def build_month_models(df):
    df = df.copy()
    df["state"] = (df["rainfall_mm"] > 0)
    month = df["timestamp"].dt.month
    prev_state = df["state"].shift(1)
    global_wet = df.loc[df["state"], "rainfall_mm"].values

    models = {}
    for m in range(1, 13):
        sel = df[month == m]
        wet_vals = sel.loc[sel["state"], "rainfall_mm"].values
        p_wet = float(sel["state"].mean()) if len(sel) else 0.0

        idx = df.index[(month == m) & prev_state.notna()]
        if len(idx):
            prev = prev_state.loc[idx].astype(bool)
            cur = df.loc[idx, "state"].astype(bool)
            n_wet_prev = int(prev.sum())
            n_dry_prev = int((~prev).sum())
            p_gw = int((prev & cur).sum()) / n_wet_prev if n_wet_prev else float("nan")
            p_gd = int((~prev & cur).sum()) / n_dry_prev if n_dry_prev else float("nan")
        else:
            p_gw = float("nan")
            p_gd = float("nan")

        models[m] = {
            "p_wet": p_wet,
            "p_wet_given_wet": p_gw,
            "p_wet_given_dry": p_gd,
            "wet_values": wet_vals,
            "n_wet": int(len(wet_vals)),
        }

    return models, global_wet


def simulate(years, start_year, models, global_wet, rng):
    import datetime as dt

    end = dt.date(start_year + years, 1, 1) - dt.timedelta(days=1)
    dates = pd.date_range(f"{start_year}-01-01", end, freq="D")
    n = len(dates)
    states = np.zeros(n, dtype=bool)
    rain = np.zeros(n, dtype=float)

    for t in range(n):
        m = dates[t].month
        model = models[m]
        if t == 0:
            p = model["p_wet"]
        else:
            p = model["p_wet_given_wet"] if states[t - 1] else model["p_wet_given_dry"]
            if not np.isfinite(p):
                p = model["p_wet"]

        states[t] = rng.random() < p
        if states[t]:
            pool = model["wet_values"] if len(model["wet_values"]) else global_wet
            rain[t] = 0.0 if len(pool) == 0 else float(rng.choice(pool))
        else:
            rain[t] = 0.0

    return pd.DataFrame({"timestamp": dates, "rainfall_mm": rain})


def summarize(df):
    rain = df["rainfall_mm"]
    wet = rain[rain > 0]
    out = {
        "n": int(len(df)),
        "zero_pct": round(float((rain == 0).mean()) * 100, 2),
        "stats_all": quantile_stats(rain, DIST_QUANTILES),
        "stats_wet": quantile_stats(wet, DIST_QUANTILES),
        "rolling": {},
    }
    for name, win in ROLL_WINDOWS.items():
        out["rolling"][name] = quantile_stats(rain.rolling(win).sum().dropna(), DIST_QUANTILES)
    monthly = (
        df.assign(year=df["timestamp"].dt.year, month=df["timestamp"].dt.month)
        .groupby("month")["rainfall_mm"]
        .agg(wet_freq=lambda s: round(float((s > 0).mean()) * 100, 2), mean=round_mean)
        .reset_index()
    )
    out["monthly"] = {
        str(int(r["month"])): {"wet_freq_pct": r["wet_freq"], "mean_mm": r["mean"]}
        for _, r in monthly.iterrows()
    }
    annual = df.assign(year=df["timestamp"].dt.year).groupby("year")["rainfall_mm"].sum()
    out["annual"] = {
        "mean": round(float(annual.mean()), 2),
        "min": round(float(annual.min()), 2),
        "max": round(float(annual.max()), 2),
    }
    return out


def round_mean(s):
    return round(float(s.mean()), 2)


def compare_plots(hist, syn, seed, years, out_dir):
    fig, ax = plt.subplots(figsize=(8, 5))
    hw = hist[hist["rainfall_mm"] > 0]["rainfall_mm"].sort_values(ascending=False).values
    sw = syn[syn["rainfall_mm"] > 0]["rainfall_mm"].sort_values(ascending=False).values
    ax.plot(np.arange(1, len(hw) + 1), hw, label="historical wet days")
    ax.plot(np.arange(1, len(sw) + 1), sw, label=f"synthetic wet days (seed={seed})", alpha=0.7)
    ax.set_yscale("log")
    ax.set_xlabel("Rank (descending)")
    ax.set_ylabel("Daily rainfall (mm, log)")
    ax.set_title(f"Wet-day intensity: historical vs {LABEL}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / f"wet_intensity_compare_seed{seed}.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    months = range(1, 13)
    h_mean = [hist.assign(m=hist["timestamp"].dt.month).groupby("m")["rainfall_mm"].mean().get(m, 0) for m in months]
    s_mean = [syn.assign(m=syn["timestamp"].dt.month).groupby("m")["rainfall_mm"].mean().get(m, 0) for m in months]
    x = np.arange(1, 13)
    ax.bar(x - 0.2, h_mean, 0.4, label="historical", color="#4c72b0")
    ax.bar(x + 0.2, s_mean, 0.4, label=f"synthetic seed={seed}", color="#c44e52")
    ax.set_xticks(x)
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean daily rainfall (mm)")
    ax.set_title(f"Monthly mean daily rainfall: historical vs {LABEL}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / f"monthly_compare_seed{seed}.png", dpi=150)
    plt.close(fig)


def main():
    args = parse_args()

    out_root = BASE_DIR / "data" / "processed" / "imd" / LABEL
    out_root.mkdir(parents=True, exist_ok=True)

    hist = pd.read_csv(args.input, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    models, global_wet = build_month_models(hist)
    hist_summary = summarize(hist)

    results = {"historical": hist_summary, "synthetic": []}
    rng = np.random.default_rng(args.seed)

    for s in range(args.samples):
        seed = args.seed + s
        r = np.random.default_rng(seed)
        syn = simulate(args.years, 2000, models, global_wet, r)
        syn_sum = summarize(syn)
        results["synthetic"].append({"seed": seed, **syn_sum})
        compare_plots(hist, syn, seed, args.years, out_root)

    out_root.joinpath(f"summary_{LABEL}.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )

    print("=== %s summary ===" % LABEL)
    print("Historical:")
    print("  zero_pct=%s  all_P99=%s  all_max=%s  wet_P99=%s  wet_max=%s" % (
        hist_summary["zero_pct"],
        hist_summary["stats_all"]["p99"],
        hist_summary["stats_all"]["max"],
        hist_summary["stats_wet"]["p99"],
        hist_summary["stats_wet"]["max"],
    ))
    print("  7d: P99=%s max=%s" % (
        hist_summary["rolling"]["7d"]["p99"],
        hist_summary["rolling"]["7d"]["max"],
    ))
    print("  annual: mean=%s min=%s max=%s" % (
        hist_summary["annual"]["mean"],
        hist_summary["annual"]["min"],
        hist_summary["annual"]["max"],
    ))
    print()
    print("Synthetic (per seed; mean across seeds shown):")
    syn = results["synthetic"]
    def avg_all(key):
        return round(sum(r["stats_all"][key] for r in syn) / len(syn), 2)
    def avg_wet(key):
        return round(sum(r["stats_wet"][key] for r in syn) / len(syn), 2)
    def avg_roll(window, key):
        return round(sum(r["rolling"][window][key] for r in syn) / len(syn), 2)
    def avg_annual(key):
        return round(sum(r["annual"][key] for r in syn) / len(syn), 2)
    print("  zero_pct=%.2f  all_P99=%s  all_max=%s  wet_P99=%s  wet_max=%s" % (
        sum(r["zero_pct"] for r in syn) / len(syn),
        avg_all("p99"), avg_all("max"), avg_wet("p99"), avg_wet("max"),
    ))
    print("  7d: P99=%s max=%s" % (avg_roll("7d", "p99"), avg_roll("7d", "max")))
    print("  annual: mean=%s min=%s max=%s" % (
        avg_annual("mean"), avg_annual("min"), avg_annual("max"),
    ))
    print()
    print("Saved to:", out_root)


if __name__ == "__main__":
    main()