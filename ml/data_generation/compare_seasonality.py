import pandas as pd

from pathlib import Path

BASE = Path("data/processed/imd/analysis")
m25 = pd.read_csv(BASE / "monthly_stats_2000_2024.csv")
m124 = pd.read_csv(BASE / "monthly_stats_1901_2024.csv")

print("month | mean_daily 25y | 124y | wet_freq 25y | 124y | total 124y")
for _, a in m124.iterrows():
    m = int(a["timestamp"])
    b = m25[m25["timestamp"] == m].iloc[0]
    print(f"{m:2d} | {b['mean_daily']:9.2f} | {a['mean_daily']:6.2f} | "
          f"{b['wet_day_freq']*100:6.1f} | {a['wet_day_freq']*100:6.1f} | {a['total']:9.1f}")

octdec25 = m25[m25["timestamp"].isin([10, 11, 12])]["total"].sum()
octdec124 = m124[m124["timestamp"].isin([10, 11, 12])]["total"].sum()
print()
print("Oct-Dec share 2000-24:", round(octdec25 / m25["total"].sum() * 100, 1), "%")
print("Oct-Dec share 1901-24:", round(octdec124 / m124["total"].sum() * 100, 1), "%")
print("Nov share 1901-24:", round(m124[m124["timestamp"] == 11]["total"].iloc[0] / m124["total"].sum() * 100, 1), "%")
