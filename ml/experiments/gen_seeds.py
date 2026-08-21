import sys
import time

import pandas as pd

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
from generator_v1 import build_timeline, build_internal_state, project_ml

SEEDS = list(range(42, 62))
OUT = r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\seeds_42_61.csv"

start = time.time()
frames = []
for seed in SEEDS:
    tl = build_timeline("2024-01-01", 365)
    df = build_internal_state(tl, seed)
    ml = project_ml(df)
    ml["zone_id"] = df["zone_id"].astype(str)
    for c in ["fos", "instability_score", "risk_label"]:
        ml[c] = df[c]
    ml["seed"] = seed
    frames.append(ml)
    print(f"seed {seed} done ({time.time()-start:.1f}s elapsed)")

all_df = pd.concat(frames, ignore_index=True)
all_df.to_csv(OUT, index=False)
print(f"\nwrote {OUT}  rows={len(all_df)}  time={time.time()-start:.1f}s")