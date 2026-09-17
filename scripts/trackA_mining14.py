"""Ingest mining pass 13: stale-provisional conversions (Phase IV-A).

  REJECT 1: SeesaGolai-20210601 — mechanism now resolves AGAINST natural slide
    (CE: valley-side private construction/traffic; MLA: excavation/seepage/tremors,
    'sinking'; road-FORMATION failure, not cut-slope failure). Reversible only on
    geotechnical evidence. Provisionals must convert, not accumulate.
  HOLD 2: Sichey (ASCE 2024 peer-reviewed Sichey debris-flow model added as slope
    context; event still single-source); MyongKyong (still single-source).
  NOTED: Kalijhora-2019 car anecdote (Firstpost 2022, dateless).
  Pool holds 22; audit re-run for confirmation.
Run: mnemo-venv python scripts/trackA_mining14.py
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    d = pd.read_csv(TRACKER)

    def setrow(mask, **kw):
        for k, v in kw.items():
            d.loc[mask, k] = v

    setrow(d["slide_no"] == "NEWS-SEESAGOLAI-20210601",
           source_2="CE KC Sharma (valley-side private construction/traffic-volume) + GT Dhungel "
                    "(excavation/seepage/tremors, 'sinking') + Minister (natural-disaster label)",
           source_convergence="single-outlet, mechanism contested",
           status="rejected",
           event_identity="REJECTED 2026-09-18: road-FORMATION cave-in/subsidence with suspected "
                          "valley-side undercutting; not a cut-slope or natural slide. Reversible only "
                          "on geotechnical evidence.",
           event_type="rejected (mechanism)",
           ceiling="NO-mechanism")
    setrow(d["slide_no"] == "NEWS-SICHEY-20210609",
           source_2="Dehls&Bhasin InSAR (3-7cm/yr) + Sajwan&Sengupta ASCE-2024 peer-reviewed Sichey "
                    "debris-flow model (failure surface, runout, collapsed building in-surface)",
           source_convergence="single (event); doubly peer-attested slope",
           event_identity="single-event; slope instability peer-attested x2 but event uncorroborated; "
                          "time conflict unresolved")
    d.to_csv(TRACKER, index=False)
    elig = d[d["eligible_for_championship"].astype(str) == "True"]
    log(f"rows={len(d)} championship={len(elig)} (gap {30 - len(elig)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
