# Talus Data Grounding Manifest

**Owner:** Member 2 (Data / Synthetic Generator) · **Trace to:** `docs/decisions/ADR-002-neyveli-reference-mine.md`, `docs/03_DATA_PLAN.md`

This manifest is the **operational record of the grounding phase** — what real sources anchor the synthetic generator, and their exact provenance. It is updated as each grounding step completes.

---

## Anchor Mine

```
Anchor mine  : Neyveli Mine-II
Company      : NLC India Limited
Region       : Neyveli, Cuddalore district, Tamil Nadu, India
Mining method: Open-cast lignite mining (BWE / conveyor / spreader)
Scale        : ~15 MTPA, ~7,193.975 ha, 365-day three-shift operation
Stripping    : ~5.2:1
```

## Coordinates

```
Documented extent : 11°27′N–11°32′N, 79°27′E–79°35′E
Approx           : lat 11.45–11.53 N, lon 79.45–79.58 E
Anchor point     : [to determine — mine center / documented Mine-II coordinate]
Status           : ⏳ pending
```

## IMD (rainfall)

```
Dataset  : IMD 0.25° × 0.25° Daily Gridded Rainfall
Period   : 1901–2024
Grid cell: [to determine from grid origin, not eyeballed]
Format   : NetCDF
Purpose  : rainfall distribution grounding (rainfall_24h_mm, rainfall_7d_mm)
Status   : ⏳ pending download
```

## DEM (terrain)

```
Provider : ISRO Bhuvan / CartoDEM (preferred); SRTM 30 m (fallback)
Coverage : [to determine — tile covering Neyveli]
Resolution: [to record]
Purpose  : elevation → slope angle / height grounding
Note     : regional terrain ≠ mine bench geometry; benches may be
           documented separately and marked synthetic in provenance.
Status   : ⏳ pending
```

## Geology (rock parameters)

```
Context  : Neyveli lignite field overburden (geological literature)
Sources  : [to collect]
Purpose  : cohesion / friction angle / unit weight grounding
Note     : mark literature-derived where evidence is insufficient
Status   : ⏳ pending
```

## Blasting (operational)

```
Sources  : [published mining literature]
Ranges   : [PPV, frequency — to record with source + interpretation]
Purpose  : blast_frequency_per_week, blast_vibration_ppv_mms
Note     : synthetic, literature-derived; no claim of NLC blast logs
Status   : ⏳ pending
```

## Crack (visual)

```
Dataset  : Ultralytics Crack-Seg
Images   : 4,029 (3,717 train / 200 val / 112 test)
Purpose  : crack-feature extraction grounding (density/length/orientation)
Domain gap: road/wall → mine rock (documented limitation)
Status   : ⏳ pending download
```

---

## Grounding references

See `research/sources.md` → "Neyveli reference-mine sources" for the full list (EAC/NGT minutes, USGS groundwater-control study, Ministry of Coal report, IMD, Crack-Seg).

## Data honesty

Neyveli defines the **operational context and spatial scenario**. The prototype validates on **public, historical and synthetic data**. Real deployment would require a mine-partner telemetry/incident-data agreement.
