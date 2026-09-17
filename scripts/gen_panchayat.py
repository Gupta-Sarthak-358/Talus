"""Gen Panchayat NGEN 100x22 — loops extract logic over panchayat_tiles centroids, scores via sih26001_rf_v1 (frozen 12-slope sample untouched)."""
import json, csv, pathlib, random
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
TILES=REPO/"data/sih26001/evidence/panchayat_tiles.json"
OUT=REPO/"data/sih26001/processed/feature_matrix.panchayat.csv"
SAMPLE=REPO/"data/sih26001/fixtures/feature_matrix.sample.csv"
# load live model if present
try:
    from backend.app.sih26001_model import get_live
    live=get_live()
except Exception:
    live=None

tiles=json.loads(TILES.read_text(encoding="utf-8"))["tiles"]
sample_rows=list(csv.DictReader(SAMPLE.open(encoding="utf-8")))
# header from sample
header=list(csv.DictReader(SAMPLE.open(encoding="utf-8")).fieldnames)
print(f"header {len(header)} cols, tiles {len(tiles)}")
# For each tile, build NGEN row via nearest sample perturb + score
import math, csv as csvm
out_rows=[]
for t in tiles:
    # nearest sample by lat/lon (simple: pick closest S zone)
    # use sample 0 as template for now
    base=dict(sample_rows[0])
    # overwrite with tile values + synthesize missing cols
    base["zone_id"]=t["zone_id"]
    base["time_window"]="2024-06-15T00:00:00Z/2024-06-15T23:59:59Z"
    base["slope_angle"]=str(t["slope_angle"])
    base["elevation"]=str(t["elevation"])
    base["rainfall_24h_mm"]=str(t["rainfall_24h_mm"])
    base["rainfall_7d_mm"]=str(t["rainfall_7d_mm"])
    base["rainfall_30d_mm"]=str(t["rainfall_30d_mm"])
    base["soil_moisture"]=str(t["soil_moisture"])
    base["ndvi"]=str(t["ndvi"])
    base["lulc"]=t["lulc"]
    base["evidence_quality"]="panchayat-synthetic"
    # distance etc keep base
    # ensure all header cols present
    for k in header:
        if k not in base:
            base[k]=sample_rows[0][k]
    out_rows.append(base)

# Score via live model to add col risk_score for evidence (not in NGEN, but for tiles API)
if live:
    for r in out_rows:
        try:
            # need full dict with numeric conversion
            sc=live.score_row({k:(float(v) if k not in ("zone_id","time_window","lulc","evidence_quality") else v) for k,v in r.items()})
            r["live_risk_score"]=str(sc["score"]) if sc else ""
            r["live_band"]=sc["band"] if sc else ""
        except Exception:
            r["live_risk_score"]=""
            r["live_band"]=""

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w=csv.DictWriter(f, fieldnames=header+ (["live_risk_score","live_band"] if live else []))
    w.writeheader()
    w.writerows(out_rows)
print(f"wrote {OUT} {len(out_rows)} rows, header+ live cols, sample frozen untouched")

# update panchayat_tiles.json with scored tiles for GET /api/panchayat/tiles live band
if live:
    # reload tiles and patch scores
    pj=json.loads(TILES.read_text(encoding="utf-8"))
    for tile, row in zip(pj["tiles"], out_rows):
        tile["risk_score"]=int(row.get("live_risk_score") or tile["risk_score"])
        tile["band"] = row.get("live_band") or ("Critical" if tile["risk_score"]>=85 else "High" if tile["risk_score"]>=75 else "Moderate" if tile["risk_score"]>=65 else "Low")
    TILES.write_text(json.dumps(pj, indent=2), encoding="utf-8")
    print("patched panchayat_tiles.json with live scores")
