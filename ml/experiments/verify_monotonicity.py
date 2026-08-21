import pandas as pd
import numpy as np

d = pd.read_csv(r"C:\Users\satvi\Desktop\Talus\data\processed\generator_v1\ml_handoff\synthetic_ml_dataset_seeds_42_91.csv")

# within-zone partial monotonicity on the RAW corpus (does data itself move
# the expected way when a dynamic variable rises, holding zone fixed?)
print("=== within-zone correlation with instability_score (all 50 seeds) ===")
for z in d.zone_id.unique():
    sub = d[d.zone_id == z]
    row = {}
    for c in ["rainfall_24h_mm", "rainfall_7d_mm", "groundwater_proxy",
              "crack_density", "blast_vibration_ppv_mms"]:
        row[c] = round(sub[c].corr(sub.instability_score), 3)
    print(f"{z}: {row}")

print("\n=== blast PPV>0 days: does instability rise with PPV? ===")
b = d[d.blast_vibration_ppv_mms > 0]
print("rows with PPV>0:", len(b))
print(b.groupby(b.blast_vibration_ppv_mms.round(1)).instability_score.mean().head(8).round(1))

print("\n=== crack_density binned vs mean instability (within ZONE_C, dry) ===")
c = d[(d.zone_id == "ZONE_C") & (d.rainfall_7d_mm < 5)]
c = c.assign(bin=pd.cut(c.crack_density, 6))
print(c.groupby("bin").instability_score.mean().round(2).to_string())

print("\n=== days_since_inspection vs instability (is it noise?) ===")
print(d.groupby(pd.cut(d.days_since_inspection, 5)).instability_score.mean().round(2).to_string())