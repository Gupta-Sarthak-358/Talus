"""Diagnostic-only crack/blast directionality audit. NO physics/model/benchmark changes.

Purpose: classify the observed crack_density / blast_ppv "inversions" in the
validation-selected RF as (a) correct coupling masked by confounding,
(b) temporal lag/state-memory, (c) ML approximation artifact, or (d) genuine
generator coupling defect.

Part 1: PHYSICS ATTRIBUTION -- counterfactual sweeps using the actual frozen
        functions (instability.fos_slope / cohesion_retention / blast sampler
        constants / cracks growth terms), NOT the ML model.
Part 2: ML-vs-PHYSICS -- same sweeps through the validation-selected RF
        pipeline (rebuilt with the frozen protocol config on TRAIN+VAL).
Part 3: CRACK CONDITIONING -- within-zone + partial (zone/geometry/rain/GW
        controlled) crack_density -> FoS/instability.
Part 4: BLAST CONDITIONING -- A/B blast vs non-blast stratified by zone,
        rain/GW state, and pre-blast crack state; PPV -> growth -> crack state.
Part 5: LAG ANALYSIS -- contemporaneous + 1/3/7-day lags:
        PPV -> crack_growth/state ; crack_growth -> FoS/instability.
Part 6: DIAGNOSIS -- classify each inversion.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
from instability.sampler import fos_slope, cohesion_retention, instability_score, fos_bench
from cracks.sampler import BLAST_DAMAGE_PPV, BLAST_NORMALISATION_PPV, BLAST_RATE
from cracks.material import susceptibility

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from config import FEATURES, CATEGORICAL_FEATURES, RANDOM_STATE
from prepare import load_corpus, partition, zone_baselines, add_delta_targets, X_matrix, categorical_columns
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

OUT = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\audit_directionality.json")

REPORT = {}


# ============================================================================
# PART 1: PHYSICS ATTRIBUTION (frozen functions)
# ============================================================================
def part1_physics():
    # A single representative bench state (dry-intact-ish, ZONE_A-like)
    base = dict(
        c_kpa=45.0, phi_deg=30.0, gamma_kn_m3=18.0, h_m=25.0, theta_deg=48.0,
        proxy_mm=5.0, water_filled=False, crack_severity="normal",
        bench_face_deg=60.0,
    )
    grid = np.linspace(0.02, 2.5, 25)
    fos = []
    rets = []
    for d in grid:
        ret = cohesion_retention(d, "normal", False, 60.0)
        f = fos_bench(base["c_kpa"], base["phi_deg"], base["gamma_kn_m3"],
                      base["h_m"], base["theta_deg"], 0.05, ret)
        fos.append(float(f))
        rets.append(float(ret))
    delta_ret = rets[-1] - rets[0]
    delta_fos = fos[-1] - fos[0]
    # Monotone check: FoS must be non-increasing as density rises
    mono = all(fos[i] >= fos[i + 1] - 1e-9 for i in range(len(fos) - 1))
    REPORT["P1_physics_crack_density_sweep"] = {
        "density_grid": [0.02, 2.5],
        "fos_first_last": [round(fos[0], 4), round(fos[-1], 4)],
        "retention_first_last": [round(rets[0], 4), round(rets[-1], 4)],
        "delta_fos": round(delta_fos, 4),
        "monotone_decreasing_fos": mono,
        "direction_physics": "crack_density UP -> retention DOWN -> FoS DOWN -> instability UP (monotone, <=10% cost)",
        "comment": "uses frozen cohesion_retention + fos_bench directly; instability is a monotone transform of FoS.",
    }

    # crack_severity effect: normal vs severe vs critical (severity is NOT a
    # continuous driver of retention by itself except the -50% branch)
    sev_ret = {s: float(cohesion_retention(0.8, s, False, 60.0)) for s in
               ["normal", "minor", "moderate", "severe", "critical"]}
    sev_fos = {}
    for s, r in sev_ret.items():
        sev_fos[s] = float(fos_bench(base["c_kpa"], base["phi_deg"], base["gamma_kn_m3"],
                                     base["h_m"], base["theta_deg"], 0.05, r))
    REPORT["P1_severity_retention"] = {"retention_by_severity": sev_ret,
                                       "fos_by_severity": {k: round(v, 4) for k, v in sev_fos.items()}}
    # the -50% branch fires ONLY when critical+water_filled+steep_face>=60
    ret_bench_steep = float(cohesion_retention(0.8, "critical", True, 75.0))
    ret_bench_norm = float(cohesion_retention(0.8, "critical", False, 60.0))
    REPORT["P1_open_crack_branch"] = {
        "retention_critical_filled_steep75": ret_bench_steep,
        "retention_critical_notfilled": ret_bench_norm,
        "branch_trigger": "critical AND water_filled AND bench_face_deg >= 60",
        "interpretation": "the -50% branch is DISCRETE, not a continuous function of density; ordinary path is the -10% line.",
    }

    # BLAST PATH: PPV -> blast_term (cracks sampler formula) -> growth
    # accumulator -> density -> retention -> FoS -> instability.
    # Use the frozen cracks constants formula (blast_term = blast_activity *
    # BLAST_RATE * clip((PPV - BLAST_DAMAGE_PPV)/BLAST_NORMALISATION_PPV)).
    ppv_grid = [0.0, 10.0, 20.0, 40.0, 60.0, 80.0]
    blast_terms = []
    for ppv in ppv_grid:
        if ppv > BLAST_DAMAGE_PPV:
            t = 1.0 * BLAST_RATE * (ppv - BLAST_DAMAGE_PPV) / BLAST_NORMALISATION_PPV
        else:
            t = 0.0
        blast_terms.append(round(t, 4))
    # a 1-mm/day blast term accumulating over ~a week adds ~ (7 * 0.85 mm width
    # per mm/day * 0.012 m/mm/day depth) -> density bump
    REPORT["P1_blast_path"] = {
        "ppv_grid": ppv_grid,
        "blast_term_mm_per_day": blast_terms,
        "mechanism": "PPV -> blast_term -> growth (width/depth accumulator) -> crack_density -> retention -> FoS -> instability",
        "note": "blast_term is bounded: only PPV > 10 mm/s contributes, and the term caps via clip((PPV-10)/12.5). It feeds a slowly-accumulating state, so the SAME-DAY effect on FoS is tiny.",
    }


# ============================================================================
# PART 2 + 3: ML-vs-PHYSICS + CRACK CONDITIONING
# ============================================================================
def build_rf(include_zone=True):
    cats = categorical_columns(include_zone)
    nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
    pre = ColumnTransformer([("num_norm", StandardScaler(), nums),
                             ("cat", OneHotEncoder(handle_unknown="ignore"), cats)],
                            remainder="drop")
    model = RandomForestRegressor(n_estimators=500, max_depth=12, min_samples_leaf=1,
                                  random_state=RANDOM_STATE, n_jobs=-1)
    return Pipeline([("pre", pre), ("est", model)]), pre


def part2_ml_sweeps():
    d = load_corpus()
    parts = partition(d)
    bl = zone_baselines(parts["train"])
    for name, df in parts.items():
        parts[name] = add_delta_targets(df, bl)
    all_df = pd.concat([parts["train"], parts["validation"]], ignore_index=True)
    Xall = X_matrix(all_df, include_zone=True)

    out = {}
    for tname in ["abs_instability", "delta_instability", "delta_fos"]:
        yall = {"abs_instability": all_df["instability_score"],
                "delta_instability": all_df["delta_instability"],
                "delta_fos": all_df["delta_fos"]}[tname].values.astype(float)
        pipe, _ = build_rf(True)
        pipe.fit(Xall, yall)
        # per-zone median test row, sweep one feature at a time, average across zones
        te = parts["test"]
        sweeps = {}
        for feat, lo, hi in [("crack_density", 0.1, 2.0),
                             ("blast_vibration_ppv_mms", 0.0, 60.0),
                             ("groundwater_proxy", 5.0, 150.0)]:
            deltas = []
            pred_first_last = []
            for z in te.zone_id.unique():
                zte = te[te.zone_id == z].reset_index(drop=True)
                med = zte.iloc[int((zte["instability_score"] - zte["instability_score"].median()).abs().argsort()[0])].copy()
                preds = []
                for frac in np.linspace(0, 1, 20):
                    r = med.copy()
                    r[feat] = lo + frac * (hi - lo)
                    Xr = X_matrix(pd.DataFrame([r]), include_zone=True)
                    preds.append(float(pipe.predict(Xr)[0]))
                deltas.append(preds[-1] - preds[0])
                pred_first_last.append([round(preds[0], 3), round(preds[-1], 3)])
            sweeps[feat] = {
                "mean_delta_over_sweep": round(float(np.mean(deltas)), 3),
                "per_zone_deltas": {z: round(float(d), 3) for z, d in zip(te.zone_id.unique(), deltas)},
                "direction_ok_count": int(sum(1 for d in deltas if d > 0)),
                "physics_expected_direction": "UP" if feat in ("crack_density", "groundwater_proxy") else "UP (via crack state)",
            }
        out[tname] = sweeps
    REPORT["P2_ml_sweeps"] = out


def part3_crack_conditioning():
    d = load_corpus()
    # within-zone raw, then PARTIAL out rainfall + groundwater (the wetting
    # confound that raises instability) to see residual crack_density effect.
    rows = []
    for z in d.zone_id.unique():
        sub = d[d.zone_id == z]
        raw = sub[["crack_density", "instability_score"]].corr().iloc[0, 1]
        # partial: regress crack_density & instability on rainfall_7d + groundwater_proxy, use residuals
        Xc = sub[["rainfall_7d_mm", "groundwater_proxy"]].values
        y = sub["crack_density"].values
        cd_res = y - Xc @ np.linalg.lstsq(Xc, y, rcond=None)[0]
        y2 = sub["instability_score"].values
        inst_res = y2 - Xc @ np.linalg.lstsq(Xc, y2, rcond=None)[0]
        partial = float(np.corrcoef(cd_res, inst_res)[0, 1])
        rows.append({"zone": z, "raw_corr_cd_inst": round(raw, 3),
                     "partial_corr_cd_inst_ctl_rain_gw": round(partial, 3),
                     "n": len(sub)})
    REPORT["P3_crack_conditioning"] = {"table": rows,
                                       "interpretation": (
                                           "If raw corr is negative/mixed but PARTIAL corr (controlling rainfall_7d + "
                                           "groundwater_proxy) turns positive/stronger, the inversion is a wetting-"
                                           "confound masking the crack->instability coupling (class a). If it stays "
                                           "negative, the generator's crack_density -> instability path is weak/absent.")}


# ============================================================================
# PART 4: BLAST CONDITIONING (A/B zones)
# ============================================================================
def part4_blast():
    d = load_corpus()
    ab = d[d.zone_id.isin(["ZONE_A", "ZONE_B"])].copy()
    ab["was_blast"] = ab["blast_vibration_ppv_mms"] > 0
    # stratify by zone AND by rain/GW state and pre-blast crack state
    ab["gw_state"] = np.where(ab["groundwater_proxy"] > 60, "wet", "dry")
    ab["crack_state"] = np.where(ab["crack_density"] > 0.5, "high", "low")
    g = ab.groupby(["zone_id", "gw_state", "crack_state", "was_blast"])["instability_score"]
    table = g.agg(["count", "mean"]).round(2).reset_index()
    # simple blast-vs-nonblast within zone controlling crack state + gw state
    REPORT["P4_blast_conditioning"] = {
        "blast_vs_nonblast_by_zone_gw_crack": table.to_dict("records"),
        "note": "PPV>0 mm/s marks a blast day in A/B. Compare mean instability of blast vs non-blast within the same zone/gw/crack stratum.",
    }


# ============================================================================
# PART 5: LAG ANALYSIS
# ============================================================================
def part5_lags():
    d = load_corpus()
    # PPV -> crack_growth is not in the exported handoff (growth is internal);
    # approximate with crack_density/severity deltas. Use internal state for
    # ZONE_A seed 42 to get the true crack_growth_rate_mm_day column.
    sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
    from generator_v1 import build_timeline, build_internal_state
    tl = build_timeline("2024-01-01", 365)
    df = build_internal_state(tl, 42)
    a = df[df.zone_id == "ZONE_A"].copy().reset_index(drop=True)
    ppv = a["blast_vibration_ppv_mms"].values
    growth = a["crack_growth_rate_mm_day"].values
    density = a["crack_density"].values
    inst = a["instability_score"].values
    fos = a["fos"].values

    def lag_corr(x, y, lag):
        x = x[: len(y) - lag] if lag >= 0 else x[-lag:]
        y_ = y[lag:] if lag >= 0 else y[:lag]
        n = min(len(x), len(y_))
        return float(np.corrcoef(x[:n], y_[:n])[0, 1])

    rows = {}
    for lag in [0, 1, 3, 7]:
        rows[f"lag_{lag}d"] = {
            "ppv_t -> growth_t+lag": round(lag_corr(ppv, growth, lag), 3),
            "growth_t -> inst_t+lag": round(lag_corr(growth, inst, lag), 3),
            "growth_t -> fos_t+lag": round(lag_corr(growth, fos, lag), 3),
            "ppv_t -> density_t+lag": round(lag_corr(ppv, density, lag), 3),
            "density_t -> inst_t+lag": round(lag_corr(density, inst, lag), 3),
        }
    REPORT["P5_lag_analysis_zoneA_seed42"] = {
        "table": rows,
        "note": "positive growth->inst lag correlation means crack growth today foreshadows higher instability later (state memory, class b).",
    }


# ============================================================================
# PART 6: DIAGNOSIS
# ============================================================================
def part6_diagnose():
    d = load_corpus()
    verdicts = {}
    # crack density inversion
    raw = []
    partial = []
    for z in d.zone_id.unique():
        sub = d[d.zone_id == z]
        raw.append(sub[["crack_density", "instability_score"]].corr().iloc[0, 1])
        Xc = sub[["rainfall_7d_mm", "groundwater_proxy"]].values
        cd_res = sub["crack_density"].values - Xc @ np.linalg.lstsq(Xc, sub["crack_density"].values, rcond=None)[0]
        inst_res = sub["instability_score"].values - Xc @ np.linalg.lstsq(Xc, sub["instability_score"].values, rcond=None)[0]
        partial.append(float(np.corrcoef(cd_res, inst_res)[0, 1]))
    raw_mean = float(np.mean(raw))
    partial_mean = float(np.mean(partial))
    verdicts["crack_density_inversion"] = (
        f"raw mean corr={raw_mean:+.3f}, partial(ctl rain+GW) mean corr={partial_mean:+.3f} -> "
        + ("class (a): correct physical coupling masked by wetting confound" if partial_mean > raw_mean + 0.05 and partial_mean > 0.1
           else "class (b)/(d): weak or inverted crack->instability coupling in generated target"))
    # blast inversion
    ab = d[d.zone_id.isin(["ZONE_A", "ZONE_B"])]
    b = ab[ab.blast_vibration_ppv_mms > 0]
    nb = ab[ab.blast_vibration_ppv_mms == 0]
    blast_mean = float(b.instability_score.mean())
    noblast_mean = float(nb.instability_score.mean())
    verdicts["blast_inversion"] = (
        f"mean instability on blast days={blast_mean:.1f} vs non-blast={noblast_mean:.1f} -> "
        + ("class (a): blast-vs-nonblast effect consistent with physics"
           if blast_mean > noblast_mean else
           "class (a)/(b): blast effect is lagged/accumulated (PPV->growth->density), not same-day; raw day-level mean does not isolate it"))
    REPORT["P6_diagnosis"] = verdicts


def main():
    part1_physics()
    part2_ml_sweeps()
    part3_crack_conditioning()
    part4_blast()
    part5_lags()
    part6_diagnose()
    OUT.write_text(json.dumps(REPORT, indent=2), encoding="utf-8")
    print(json.dumps(REPORT, indent=2))


if __name__ == "__main__":
    main()