"""TALUS Scenario Engine v1.5 (extension layer over frozen generator v1.4.0).

See spec.md for the contract. This module COMPOSES frozen generators with
modified input realizations; it never modifies physics and never writes
fos/instability_score/risk_label directly (enforced by validate_scenarios).
"""
import zlib
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd

sys_path = r"C:\Users\satvi\Desktop\Talus\ml\data_generation"
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from generator_schema import ZONES
from rainfall import generate_rainfall
from terrain import generate_terrain
from geology import generate_geology
from groundwater import generate_groundwater
from blast import generate_blast
from blast.sampler import (_constants, ZONE_RECEIVER_DISTANCE_M, MCD_RANGE_KG,
                           MCD_MODE_KG, FREQ_BINS, SCATTER_SIGMA, PPV_CEILING_MMS)
from cracks import generate_cracks
from instability import generate_instability

IMD_CSV = Path(r"C:\Users\satvi\Desktop\Talus\data\processed\imd\neyveli_rainfall_1901_2024.csv")

TEMPLATES = {
    "dec_1902": ("1902-12-01", "1902-12-31"),
    "apr_1931": ("1931-04-01", "1931-04-30"),
    "nov_2015": ("2015-11-01", "2015-11-30"),
    "dec_1996": ("1996-12-01", "1996-12-31"),
}


@dataclass
class Scenario:
    name: str
    kind: str = "none"
    zone_id: str = "ZONE_A"
    seed: int = 42
    start_day: int = 200
    duration_days: int = 5
    params: dict = field(default_factory=dict)
    scenario_seed: int = 0

    def with_(self, **kw):
        return replace(self, **kw)


def _scenario_rng(sc):
    return np.random.default_rng(np.random.SeedSequence([sc.seed, 9000, zlib.crc32(sc.name.encode())]))


def _template_profile(template_id):
    imd = pd.read_csv(IMD_CSV, parse_dates=["timestamp"])
    a, b = TEMPLATES[template_id]
    w = imd[(imd.timestamp >= a) & (imd.timestamp <= b)]
    return w["rainfall_mm"].to_numpy(dtype=float)


def apply_rain_scenario(rain, sc):
    if sc.kind in ("none", "blast_surge"):
        return rain
    out = rain.copy()
    mm = out["rainfall_mm"].to_numpy(dtype=float).copy()
    n = len(mm)
    t0 = sc.start_day
    dur = sc.duration_days
    p = sc.params
    if sc.kind == "rainfall_storm":
        peak = float(p.get("peak_mm", 100.0))
        tri = np.minimum(np.arange(1, dur + 1), np.arange(dur, 0, -1)) / ((dur + 1) / 2.0)
        overlay = peak * tri
    elif sc.kind == "prolonged_rain":
        overlay = np.full(dur, float(p.get("daily_mm", 20.0)))
    elif sc.kind == "historical_rain":
        prof = _template_profile(p.get("template_id", "dec_1902"))
        scale = float(p.get("scale", 1.0))
        overlay = prof[:dur] * scale
        if len(overlay) < dur:
            overlay = np.pad(overlay, (0, dur - len(overlay)))
    elif sc.kind == "combined":
        peak = float(p.get("peak_mm", 100.0))
        tri = np.minimum(np.arange(1, dur + 1), np.arange(dur, 0, -1)) / ((dur + 1) / 2.0)
        overlay = peak * tri
    else:
        raise ValueError(sc.kind)
    end = min(t0 + dur, n)
    mm[t0:end] += overlay[: end - t0]
    out["rainfall_mm"] = mm
    for win in (3, 7):
        out[f"rainfall_{win}d_mm"] = pd.Series(mm).rolling(win, min_periods=1).sum().to_numpy()
    out["wet_day"] = mm > 0
    return out


def apply_blast_scenario(blast, timeline, sc):
    if sc.kind not in ("blast_surge", "combined"):
        return blast
    out = blast.copy()
    ppv_mult = float(sc.params.get("ppv_mult", 1.5))
    p_extra = float(sc.params.get("extra_event_prob", 0.25))
    rng = _scenario_rng(sc)
    K, b = _constants()
    dist = ZONE_RECEIVER_DISTANCE_M[sc.zone_id]
    n = len(out)
    occurs = out["blast_occurs"].to_numpy(dtype=bool).copy()
    charge = out["charge_per_delay_kg"].to_numpy(dtype=float).copy()
    freq = out["dominant_frequency_hz"].to_numpy(dtype=float).copy()
    ppv = out["blast_vibration_ppv_mms"].to_numpy(dtype=float).copy()

    window = slice(sc.start_day, min(sc.start_day + sc.duration_days, n))
    idx = np.arange(n)[window]
    scale_mask = occurs[idx]
    ppv[idx[scale_mask]] = np.minimum(ppv[idx[scale_mask]] * ppv_mult, PPV_CEILING_MMS)

    for t in idx[~occurs[idx]]:
        if rng.random() < p_extra:
            w = float(rng.triangular(MCD_RANGE_KG[0], MCD_MODE_KG, MCD_RANGE_KG[1]))
            r = rng.random()
            f = 0.0
            for prob, lo, hi in FREQ_BINS:
                if r < prob:
                    f = float(rng.uniform(lo, hi))
                    break
            raw = K * (dist / np.sqrt(w)) ** (-b)
            val = min(raw * float(rng.lognormal(0.0, SCATTER_SIGMA)), PPV_CEILING_MMS)
            occurs[t] = True
            charge[t] = w
            freq[t] = f
            ppv[t] = val

    out["blast_occurs"] = occurs
    out["charge_per_delay_kg"] = charge
    out["dominant_frequency_hz"] = freq
    out["blast_vibration_ppv_mms"] = ppv
    return out


def run_scenario(sc, days=365, start="2024-01-01"):
    timeline = pd.date_range(start=start, periods=days, freq="D")
    rain0 = generate_rainfall(timeline, sc.seed)
    rain = apply_rain_scenario(rain0, sc)
    blast0 = generate_blast(timeline, sc.zone_id, sc.seed)
    blast = apply_blast_scenario(blast0, timeline, sc)

    terrain = generate_terrain(sc.zone_id, sc.seed)
    geology = generate_geology(sc.zone_id, sc.seed)
    gw = generate_groundwater(rain["rainfall_mm"].to_numpy(), sc.zone_id, sc.seed)
    cracks = generate_cracks(timeline, rain, gw, blast, terrain, geology,
                             ZONES[sc.zone_id], sc.seed, sc.zone_id)

    rows = []
    for idx, ts in enumerate(timeline):
        r = rain.iloc[idx]
        g = gw.iloc[idx]
        bl = blast.iloc[idx]
        cr = cracks.iloc[idx]
        rows.append({
            "timestamp": ts, "zone_id": sc.zone_id,
            "rainfall_mm": r["rainfall_mm"], "rainfall_3d_mm": r["rainfall_3d_mm"],
            "rainfall_7d_mm": r["rainfall_7d_mm"], "wet_day": bool(r["wet_day"]),
            "rainfall_regime": r["rainfall_regime"],
            "elevation_m": terrain["elevation_m"], "regional_slope_deg": terrain["regional_slope_deg"],
            "bench_height_m": ZONES[sc.zone_id]["bench_height_m"],
            "bench_face_angle_deg": ZONES[sc.zone_id]["bench_face_angle_deg"],
            "distance_to_crest_m": ZONES[sc.zone_id]["distance_to_crest_m"],
            "slope_angle_deg": terrain["slope_angle_deg"], "slope_height_m": terrain["slope_height_m"],
            "material_class": geology["material_class"], "cohesion_kpa": geology["cohesion_kpa"],
            "friction_angle_deg": geology["friction_angle_deg"],
            "unit_weight_kn_m3": geology["unit_weight_kn_m3"],
            "parameter_regime": geology["parameter_regime"],
            "groundwater_state": g["groundwater_state"], "pore_pressure_kpa": g["pore_pressure_kpa"],
            "groundwater_thrust_kpa": g["groundwater_thrust_kpa"], "groundwater_proxy": g["groundwater_proxy"],
            "blast_occurs": bool(bl["blast_occurs"]),
            "blast_frequency_per_week": bl["blast_frequency_per_week"],
            "charge_per_delay_kg": bl["charge_per_delay_kg"],
            "blast_distance_m": bl["blast_distance_m"],
            "dominant_frequency_hz": bl["dominant_frequency_hz"],
            "blast_vibration_ppv_mms": bl["blast_vibration_ppv_mms"],
            "crack_family": cr["crack_family"], "crack_width_mm": cr["crack_width_mm"],
            "crack_depth_m": cr["crack_depth_m"], "crack_length_m": cr["crack_length_m"],
            "crack_density": cr["crack_density"], "water_filled": bool(cr["water_filled"]),
            "crack_growth_rate_mm_day": cr["crack_growth_rate_mm_day"],
            "crack_severity": cr["crack_severity"], "prior_incident": False,
            "synthetic": True,
        })
    df = pd.DataFrame(rows)
    generate_instability(df)
    df["scenario"] = sc.name
    return df


def baseline(zone_id="ZONE_A", seed=42, days=365):
    return run_scenario(Scenario(name=f"baseline_{zone_id}", kind="none",
                                 zone_id=zone_id, seed=seed), days=days)
