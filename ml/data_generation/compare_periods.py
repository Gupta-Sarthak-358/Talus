import json

from pathlib import Path

BASE = Path("data/processed/imd/analysis")
mod = json.loads((BASE / "summary_2000_2024.json").read_text(encoding="utf-8"))
hist = json.loads((BASE / "summary_1901_2024.json").read_text(encoding="utf-8"))


def g(d, grp, key):
    return d["distribution"][grp][key]


print("=== DIMENSION 1: zero inflation ===")
for k in ["zero_rain_pct", "wet_day_pct"]:
    print(f'  {k}: 2000-24={mod["integrity"][k]}  1901-24={hist["integrity"][k]}')

print("\n=== DIMENSION 3: tail (mm) ===")
for key in ["p90", "p95", "p99", "p99_5", "p99_9", "maximum"]:
    for grp in ["all_days", "wet_days"]:
        print(f'  {grp} {key}: 2000-24={g(mod, grp, key)}  1901-24={g(hist, grp, key)}')
for win in ["1d", "3d", "7d"]:
    print(f'  rolling {win} P99: 2000-24={mod["rolling_windows_mm"][win]["p99"]}  1901-24={hist["rolling_windows_mm"][win]["p99"]}')
    print(f'  rolling {win} max: 2000-24={mod["rolling_windows_mm"][win]["maximum"]}  1901-24={hist["rolling_windows_mm"][win]["maximum"]}')

print("\n=== DIMENSION 4: interannual ===")
for k in ["annual_mean_mm", "annual_min_mm", "annual_max_mm", "annual_std_mm"]:
    print(f'  {k}: 2000-24={mod[k]}  1901-24={hist[k]}')
print("  annual_dist (2000-24):", mod["annual_distribution_mm"])
print("  annual_dist (1901-24):", hist["annual_distribution_mm"])
print("  year_counts (2000-24):", mod["annual_year_counts"])
print("  year_counts (1901-24):", hist["annual_year_counts"])
