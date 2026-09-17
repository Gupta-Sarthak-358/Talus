"""Japan 3-tank Soil Water Index (RESEARCH:47) — JMA-validated SWI.

Simplified JMA tank params (Okada 1992, used by JMA for landslide warnings):
  Tank1: L1=15mm,  a1=0.10, b1=0.12 (surface)
  Tank2: L2=60mm,  a2=0.05, b2=0.05 (subsurface)
  Tank3: L3=60mm,  a3=0.01 (groundwater)
Inflow = daily rainfall (observed 7d + forecast). Outflow = a*storage, infiltration = b*storage.
SWI = S1+S2+S3 (mm). Normalized 0-1 via tanh(SWI/100) for comparability with soil_moisture 0-1.

This replaces single soil_moisture 0.271 proxy for warning logic; model scoring still uses
original soil_moisture per frozen 17 feats, SWI is warning-overlay only.
"""

def swi_from_series(daily_rain_mm: list[float]) -> float:
    L1, L2, L3 = 15.0, 60.0, 60.0
    a1, b1 = 0.10, 0.12
    a2, b2 = 0.05, 0.05
    a3 = 0.01
    s1 = s2 = s3 = 0.0
    for r in daily_rain_mm:
        # Tank1 inflow
        s1 += r
        q1 = a1 * max(0, s1 - L1)
        inf1 = b1 * s1
        s1 = max(0, s1 - q1 - inf1)
        # Tank2
        s2 += inf1
        q2 = a2 * max(0, s2 - L2)
        inf2 = b2 * s2
        s2 = max(0, s2 - q2 - inf2)
        # Tank3
        s3 += inf2
        q3 = a3 * s3
        s3 = max(0, s3 - q3)
    swi_mm = s1 + s2 + s3
    # normalize 0-1 (JMA warns at SWI ~ 120-160mm per terrain; 100mm tanh midpoint)
    import math
    return math.tanh(swi_mm / 100.0)

def swi_for_zone(rainfall_7d: float, rainfall_30d: float, forecast_daily: list[float] | None = None) -> float:
    # Reconstruct daily series: 7d observed evenly + 30d tail + forecast next 3d
    # Simple: 7d uniform, 30d tail = (30d-7d)/23 uniform for earlier days
    obs_7 = [rainfall_7d / 7.0] * 7
    tail = max(0, rainfall_30d - rainfall_7d)
    obs_tail = [tail / 23.0] * 23 if tail else []
    series = obs_tail + obs_7
    if forecast_daily:
        series = series + forecast_daily[:3]
    return swi_from_series(series)
