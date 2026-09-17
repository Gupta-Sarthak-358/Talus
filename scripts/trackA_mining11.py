"""Ingest mining pass 10: GSI/district-report layer + evidence ceiling (Phase IV-A).

  NEW PROVISIONAL 1: SoBhir-20160803 (NESAC peer-reviewed: GPS + 490mm + date; needs 2nd source).
  PROVENANCE: Rongey-20220628 += SSDMA Tier-1 ("Rongyeck woman + two minor sons" match).
  CEILING: new `ceiling` column on every non-eligible NEWS row —
    NO-mechanism / NO-duplicate / NO-box(frozen) / YES-corroboration /
    MAYBE-coordinate / YES-IF-ARCHIVE / NO-post-championship-rule.
  LEADS logged (dateless, not rows): SSDMA menu (Sokpay-18-families, Namchi-40-villages,
  Bey-UpperDzongu?, Tsong, Martam, W.Sikkim 2-dead-3-injured); Wadia status-report table;
  GSI-2019-monsoon Darjeeling field inventory (no per-event dates).
Run: mnemo-venv python scripts/trackA_mining11.py
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


CEILING = {
    # mechanism rejects: immutable
    "NEWS-LINGZYA-20220615": "NO-mechanism", "NEWS-BHALUKHOLA-20210617": "NO-mechanism",
    "NEWS-MELTHUM-20240528": "NO-mechanism", "NEWS-SAMARDUNG-20260720": "NO-mechanism",
    "NEWS-CHUNGTHANG-20231004": "NO-mechanism",
    # duplicates/aggregates: not samples
    "NEWS-MAJWA-20240610": "NO-duplicate", "NEWS-SIKKIM-20220617": "NO-aggregate",
    # frozen-box transfers: championship NO, transfer usable
    "NEWS-GARO-20220609": "NO-box(frozen)", "NEWS-GUWAHATI-20220614": "NO-box(frozen)",
    "NEWS-LAITLAREM-20220617": "NO-box(frozen)", "NEWS-TIGDO-20200710": "NO-box(frozen)",
    "NEWS-MODIRIJO-20200710": "NO-box(frozen)", "NEWS-TUPUL-20220630": "NO-box(frozen)",
    "NEWS-SUBALSINGH-20180518": "NO-box(frozen)", "NEWS-KAMBUK-20180518": "NO-box(frozen)",
    "NEWS-NONGSTOIN-20230617": "NO-box(frozen)", "NEWS-HLIMEN-20240528": "NO-box(frozen)",
    # provisional-transfer: corroboration may promote within transfer
    "NEWS-SOOD-20220619": "YES-corroboration", "NEWS-HOLLONGI-20200923": "YES-corroboration",
    "NEWS-ITANAGAR-20190717": "YES-corroboration", "NEWS-NH29-20190704": "YES-corroboration",
    "NEWS-PALKU-20180520": "YES-corroboration", "NEWS-BELBARI-20180520": "YES-corroboration",
    "NEWS-LUMSHONG-20220616": "YES-corroboration", "NEWS-PYNTHOR-20231008": "YES-corroboration",
    "NEWS-RNGAIN-20230414": "YES-corroboration", "NEWS-HUNTHAR-20240528": "YES-corroboration",
    # in-domain provisionals
    "NEWS-29MILE-20200923": "n/a-eligible-now", "NEWS-SEESAGOLAI-20210601": "MAYBE-mechanism+outlet",
    "NEWS-SICHEY-20210609": "YES-corroboration", "NEWS-17MILE-20220615": "n/a-eligible-now",
    "NEWS-BIRIKDARA-20220802": "n/a-eligible-now", "NEWS-MYONGKYONG-20200524": "YES-corroboration",
    "NEWS-MANGANCHUNG-20200627": "n/a-eligible-now", "NEWS-APDARA-20200627": "n/a-eligible-now",
    "NEWS-SADAPHAMTAM-20260725": "YES-IF-ARCHIVE(ind2026)",
    "NEWS-SOURENI-20251005": "NO-post-championship-rule", "NEWS-DILARAM-20251005": "NO-post-championship-rule",
    "NEWS-PUBUNG-20190708": "n/a-eligible-now",
}


def main() -> int:
    d = pd.read_csv(TRACKER)
    if "ceiling" not in d.columns:
        d["ceiling"] = ""

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    setrow(d["slide_no"] == "NEWS-RONGEY-20220628",
           source_2=d.loc[d["slide_no"] == "NEWS-RONGEY-20220628", "source_2"].iloc[0]
           + " + SSDMA Tier-1 news menu ('Rongyeck woman + two minor sons' exact match)")

    new_rows = [
        {"slide_no": "NEWS-SOBHIR-20160803", "district": "Mangan", "lat": 27.5397, "lon": 88.5007,
         "year": 2016, "month_hint": "August 2016", "exact_date": "2016-08-03",
         "time": "490mm cloudburst day",
         "source": "NESAC peer-reviewed inventory (Prasad 2019: GPS 27d32'22.92 88d30'2.47, Kanaka dam, 10 houses, 300m road)",
         "source_url": "nesac.gov.in inventory PDF",
         "source_2": "",
         "source_convergence": "single-strong (peer-reviewed)", "date_precision": "exact",
         "location_precision": "So Bhir, Dzongu near Mantam (GPS, HIGH confidence)",
         "fatalities": "0 reported (infra/agri)", "road_association": "300m road washed, Kanaka bridge submerged",
         "status": "provisional-exact", "precision_status": "EXACT_VERIFIED", "priority": "mined",
         "source_tier": "Tier1-academic",
         "event_identity": "debris slide, oldest candidate (2016); needs press/admin second source",
         "related_episode_id": "EP-AUG2016-DZONGU", "exactness_status": "EXACT_PROVISIONAL",
         "geography_status": "IN_DOMAIN", "DEM_status": "COVERED", "rainfall_status": "AVAILABLE",
         "satellite_status": "L8-check-at-replay", "event_type": "infrastructure-damage?",
         "ceiling": "YES-corroboration"},
    ]
    d = pd.concat([d, pd.DataFrame(new_rows)], ignore_index=True)
    for slide, val in CEILING.items():
        d.loc[d["slide_no"] == slide, "ceiling"] = val
    # eligible rows: ceiling n/a
    d.loc[d["eligible_for_championship"].astype(str) == "True", "ceiling"] = "n/a-eligible"

    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    la, lo = 27.5397, 88.5007
    geo = bool(LON0 <= lo <= LON1 and LAT0 <= la <= LAT1)
    rain = (REPO / "data/raw/imd/ind2016_rfp25.nc").exists()
    sep = float(2 * 6371000.0 * np.arcsin(np.sqrt(
        np.sin(np.radians(pla - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(pla))
        * np.sin(np.radians(plo - lo) / 2) ** 2)).min())
    idx = d[d["slide_no"] == "NEWS-SOBHIR-20160803"].index[0]
    d.loc[idx, "contam_geo"] = str(geo)
    d.loc[idx, "contam_dem"] = "True"
    d.loc[idx, "contam_rain"] = str(rain)
    d.loc[idx, "contam_prox_m"] = round(sep, 1)
    d.loc[idx, "eligible_for_championship"] = "False"
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    log(f"SoBhir: geo={geo} rain={rain} prox={round(sep,1)}m (provisional: needs 2nd source)")
    log(f"rows={len(d)} championship={len(elig)}")
    log("ceiling: " + str(d[d["slide_no"].str.startswith("NEWS-", na=False)]["ceiling"].value_counts().to_dict()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
