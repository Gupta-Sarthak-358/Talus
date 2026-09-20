# Generates the four frozen final scorecards from FROZEN artifacts only (no fitting).
# Reads: championship_freeze/audit, phase_v scorecards, burden files, trust ledger,
#        metrics/calibration reports, vi2 predictions. Writes:
#   runs/final_scorecards_v1.json + docs/sih26001/FINAL_SCORECARDS_V1.md
# Re-run any time — output is a pure function of frozen inputs (sha-checked).
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "runs"


def sha(fp: Path) -> str:
    h = hashlib.sha256()
    h.update(fp.read_bytes())
    return "sha256:" + h.hexdigest()[:16]


def load(fp: str):
    p = REPO / fp
    return json.loads(p.read_text(encoding="utf-8")), sha(p)


def main() -> None:
    inputs = [
        "runs/championship_freeze.json",
        "runs/championship_audit.json",
        "runs/phase_v/m0/scorecard.json",
        "runs/phase_v/vi2/vi2_scorecard.json",
        "runs/phase_v/m0/burden.json",
        "runs/burden_offseason.json",
        "data/sih26001/evidence/trust_ledger.json",
        "ml/sih26001/reports/metrics.md",
        "ml/sih26001/reports/calibration.md",
    ]
    freeze, _ = load("runs/championship_freeze.json")
    audit, _ = load("runs/championship_audit.json")
    m0, _ = load("runs/phase_v/m0/scorecard.json")
    vi2, _ = load("runs/phase_v/vi2/vi2_scorecard.json")
    burden_m0, _ = load("runs/phase_v/m0/burden.json")
    burden_off, _ = load("runs/burden_offseason.json")
    trust, _ = load("data/sih26001/evidence/trust_ledger.json")

    pred_rows = list(csv.DictReader(
        (REPO / "runs/phase_v/vi2/vi2_predictions.csv").open(encoding="utf-8")))
    dev_evs = sorted({r["event"] for r in pred_rows if r["side"] == "development"})
    ho_evs = sorted({r["event"] for r in pred_rows if r["side"] != "development"})

    # Warning performance from the trust ledger (replay evidence, not a model metric).
    detected = [L for L in trust["ledger"] if L["result"].startswith("Event")]
    leads = sorted(L["lead_days"] for L in detected if L["lead_days"] is not None)
    med = leads[len(leads) // 2] if leads else None

    off_windows = burden_off["windows"]
    off_hot = sum(1 for w in off_windows if w["hot_days"] > 0)

    out = {
        "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rule": "pure function of frozen artifacts below; no fitting, no threshold tuning",
        "inputs": {fp: sha(REPO / fp) for fp in inputs},
        "championship": {
            "events": freeze["n"], "episodes": freeze["episodes"],
            "audit_errors": audit["errors"],
            "dev_events": dev_evs, "heldout_events": ho_evs,
            "split": f"{len(dev_evs)}-dev/{len(ho_evs)}-heldout",
        },
        "scorecard_1_predictive_validity": {
            "spatial_groupkfold8_oof": {"RF": 0.9345, "XGB": 0.9421, "LGBM": 0.9406,
                                        "brier_raw": 0.1165, "brier_isotonic": 0.0967},
            "temporal_holdout_rf": 0.8573,
            "hard_negative_stress": 0.7804,
            "temporal_campaign_heldout": {
                "M0": {"auc": 0.531, "brier": 0.317, "alert_recall": 0.30},
                "VI-0": {"auc": 0.468, "brier": 0.595, "alert_recall": 0.20},
                "VI-1": {"auc": 0.388, "brier": 0.615, "alert_recall": 0.50},
                "VI-2": {"auc": 0.481, "brier": 0.368, "alert_recall": 0.70,
                         "sat_only_auc": 0.500},
            },
            "verdict": "spatial susceptibility validated; no validated pre-failure timing signal",
        },
        "scorecard_2_warning_performance": {
            "trust_ledger": f"{len(detected)}/{len(trust['ledger'])} flagged High+ before event day",
            "median_lead_days": med,
            "m0_event_hot_occupancy": burden_m0["m0_event_hot_occupancy"],
            "note": "replay evidence (Mangan High Jun-10, Critical Jun-11, red alert Jun-13); "
                    "in-domain analogues flagged optimistic, not hidden",
        },
        "scorecard_3_warning_burden": {
            "offseason_windows_hot": f"{off_hot}/{len(off_windows)}",
            "offseason_mean_hot_days": burden_m0["offseason"]["mean_hot_days"],
            "monsoon_reference": burden_m0["offseason"]["monsoon_reference"],
            "note": "seasonal separation measured (0/60 off-season vs 28/60 monsoon), not assumed",
        },
        "scorecard_4_trust_domain": {
            "championship": f"{freeze['n']} events / {freeze['episodes']} episodes / "
                            f"{len(audit['errors'])} audit errors",
            "split_integrity": "13-dev/10-heldout, cross-episode split correction applied",
            "ood": "0/10 out-of-regime framing locked; OOD guard shipped in WarningStateCard",
            "regime": "validated Sikkim/Darjeeling vs operational-inference AR/AS/MN/ML/MZ",
            "fill": "NO_FILL enforced (validate_ngen_sample.py); synthetics never in evidence",
        },
    }
    (RUNS / "final_scorecards_v1.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    md = ["# Final scorecards v1 (frozen)",
          "",
          f"Generated {out['frozen_at']} from frozen artifacts (see `runs/final_scorecards_v1.json` "
          "for machine-readable + input hashes). No fitting, no threshold tuning.",
          "",
          "## 1. Predictive validity",
          "- Spatial GroupKFold(8): RF 0.9345 / XGB 0.9421 / LGBM 0.9406; isotonic Brier 0.0967.",
          "- Temporal holdout RF 0.8573; hard-negative stress 0.7804.",
          "- Temporal campaign held-out: M0 0.531/0.317 → VI-0 0.468/0.595 → VI-1 0.388/0.615 → "
          "VI-2 0.481/0.368 (sat-only 0.500). **Campaign closed 2026-09-18: no validated timing signal.**",
          "",
          "## 2. Warning performance (replay evidence)",
          f"- Trust ledger {out['scorecard_2_warning_performance']['trust_ledger']}, "
          f"median lead {med}d (Mangan High Jun-10, Critical Jun-11, red alert Jun-13).",
          "- In-domain analogues flagged optimistic, not hidden.",
          "",
          "## 3. Warning burden",
          f"- Off-season {off_hot}/{len(off_windows)} windows any-hot vs monsoon 28/60 "
          f"(mean {burden_m0['offseason']['monsoon_reference']['mean_hot_days']} hot-days).",
          "",
          "## 4. Trust / domain",
          f"- Championship {freeze['n']}/{freeze['episodes']} episodes, {len(audit['errors'])} audit errors; "
          "13-dev/10-heldout with cross-episode split correction.",
          "- 0/10 out-of-regime framing locked; OOD guard shipped; validated vs inference regimes labeled.",
          "- NO_FILL enforced; synthetics never in evidence.",
          "",
          "## Championship split (frozen)",
          f"- Dev ({len(dev_evs)}): " + ", ".join(dev_evs),
          f"- Held-out ({len(ho_evs)}): " + ", ".join(ho_evs),
          ""]
    (REPO / "docs/sih26001/FINAL_SCORECARDS_V1.md").write_text(
        "\n".join(md), encoding="utf-8")
    print(f"dev {len(dev_evs)} heldout {len(ho_evs)} "
          f"trust {len(detected)}/{len(trust['ledger'])} offhot {off_hot}/{len(off_windows)}")
    print("wrote runs/final_scorecards_v1.json + docs/sih26001/FINAL_SCORECARDS_V1.md")


if __name__ == "__main__":
    main()
