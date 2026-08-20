# Neyveli Blasting: Grounding, PPV Model, Frequency & Regulation

Research artifact for TALUS BLAST track. Purpose: replace the placeholder `blast_vibration_ppv_mms = random.uniform(2, 20)` with a physically derived, site-specific blast disturbance model. Scope: NLC Mine II (primary; Mine I used for the NIRM regression anchor).

---

## 1. BLAST-01: Operational grounding (what actually happens at Neyveli)

### 1.1 Verified facts (multi-source)

| Fact | Value | Source | Confidence |
|---|---|---|---|
| Blasting purpose | **Loosen material for cost-effective BWE excavation**; "no fragmentation or displacement of rock is required" | NIRM 2005 (Adhikari); NLC EC; IJEA 2013 | **High** (verbatim) |
| Fraction of OB blasted | **~30%** of total overburden (Surface + Top benches in the old 4-bench layout; Northern half of mine is hard Cuddalore sandstone) | MiningTechnology blog / NLC era docs | High |
| Modern practice | NLC **drills and blasts each bench before stripping** | Coal Age 2015 ("Neyveli Updates Its Excavator Fleet") | High |
| Explosive consumption | **~7,300 mtpy**, mainly **site-mixed emulsion** | Coal Age 2015 (Mohan, NLC) | High |
| Blasthole diameter | **200 mm** | NLC Deputy Chief Engineer (Drilling & Blasting), LinkedIn | Medium (primary practitioner) |
| Bench height (blasted) | **15–22 m** | NLC Deputy Chief Engineer (Drilling & Blasting) | Medium |
| Blast-hole initiation | **Electronic detonators + NONEL** | NLC DCE; IJEA 2013 ("controlled blasting using the latest electronic detonators") | Medium-High |
| Explosive type | Site-mixed emulsion, bulk delivery system | Coal Age; NLC DCE | High |
| Strata cutting resistance | 15–20 MPa (vs 7–10 MPa for German design basis) | Coal Age 2015 (NLC authors) | High |
| OB rate (Mine II) | 5 stripping benches, ~**78 M m³/yr** total capacity | Coal Age 2015 | High |

### 1.2 Derived quantities (CLEARLY LABELED — not measured)

These are computed from the verified constraints above. **Do not treat as measured.** Tagged `derived`.

- Mine-II stripped OB ≈ **78 M m³/yr** (bench capacity, Coal Age).
- Blasted OB volume ≈ 30% × 78 M ≈ **23.4 M m³/yr**.
- **Effective powder factor ≈ 7,300 t/yr ÷ 23.4 M m³/yr ≈ 0.31 kg/m³** — a low specific charge, which is exactly the mechanism NIRM cites for Neyveli's high PPV (see §2.2).
- **Charge per hole ≈ 545 m³/hole × 0.31 kg/m³ ≈ 170 kg/hole** (200 mm hole, nominal B×S ≈ 5.5 × 5.5 m, H ≈ 18 m).
- **Charge per delay (MCD) ≈ 100–600 kg**, mode ~300 kg (1–3 holes per delay with electronic/NONEL delays). Cross-checked against regulatory scaled distances (§4.4): civil-compliant MCD at Mine II ≈ 100–450 kg for distances 150–300 m.
- **Blast frequency ≈ 14–28 blasts/week** (≈ 43,000 holes/yr ÷ (30–60 holes/blast) ÷ 52 wk). Wide uncertainty; not directly documented. Treat as a tunable latent with broad prior.

### 1.3 Blast location model

Blasting occurs on the **overburden benches advancing ahead of the BWEs** (Surface→Top→Middle→Bottom in the old 4-bench layout; 5 benches incl. 18 m lowest OB bench in the current layout; lignite bench is NOT blasted). Distances to exposed structures (LAUBAG/NLC Master Plan 1995):

| Structure | Distance from blast site | Source | Confidence |
|---|---|---|---|
| Village east of Mine I | 300 m | Master Plan §3.2.6.2 | High |
| Village south of Mine I | 400 m | Master Plan §3.2.6.2 | High |
| Mandarakuppam village (Mine II) | ≤300 m from blast; **150 m from boundary** | Master Plan §3.2.6.2 | High |
| Mine-II site office + Mandarakuppam–Valayamadevi road | ≤500 m | Master Plan §3.2.6.2 | High |

---

## 2. BLAST-02: Neyveli PPV model (LOCKED)

### 2.1 The model

Square-root scaled-distance attenuation (ISEE 1998 convention: surface blast → surface measurement):

```
PPV = K · (D / √W)^(–b)      [mm/s]
  D = distance blast → monitoring point (m)
  W = maximum charge per delay (kg)
  K, b = site constants
```

### 2.2 Locked Neyveli constants (NIRM, "Role of Blast Design Parameters on Ground Vibration", MT/134/02, Adhikari et al. 2005)

| Parameter | Value | Source status |
|---|---:|---|
| K | **858.90** | clear text, two independent extractions |
| b | **1.58** | clear text |
| r (correlation) | **0.86** | clear text |
| Blasts monitored | **22** | Table 2.1 |
| Observations | **68** | Table 2.1; 84 data sets used in regression (Mine I + II, mostly Mine II) |
| Frequency range | **5–27 Hz** | Table 2.1; "frequency <10 Hz is usually present" |
| Relative PPV | **Highest of all mines studied** (coal, iron ore, limestone, copper, diamond) | Fig. 2.8 discussion |

**Why Neyveli PPV is high (NIRM's own explanation):** low specific charge (see §1.2 derived PF ≈ 0.31 kg/m³) and/or higher water table + wet ground. The wet-ground link connects directly to the geology/groundwater track (aquifer sands, 8–10 m³ water per tonne pumped).

### 2.3 Legacy NIRM study (1994, for NLC Master Plan; NIRM/Kolar Gold Fields)

- Study window: 27.9.94–2.10.94, Mine I + Mine II.
- Safe level adopted for the study: **12.5 mm/s** (USBM "older homes" threshold).
- Mine I measured PPV often **above** 12.5 mm/s; Mine II below it.
- Frequency: **Mine I 5–39 Hz; Mine II 5–28 Hz**.
- Recommended scaled distances: Mine I **25 m/√kg**; Mine II **14.6 m/√kg**.
- Findings corroborate NIRM 2005: **higher charge per delay → higher PPV**; resonance risk because residential natural frequencies span **4–24 Hz** (overlaps Neyveli's 5–27 Hz).

### 2.4 Sanity-check of the locked model

Chosen to reproduce regulatory-realistic behaviour: at D=400 m, W=300 kg → SD=23.1, PPV≈6.0 mm/s (OK vs 10 mm/s @ 8–25 Hz); at D=300 m, W=400 kg → SD=15.0, PPV≈11.9 mm/s (exceeds 10; marginal). At <8 Hz frequencies the 5 mm/s limit is exceeded far more often. This reproduces NIRM's conclusion that Neyveli blasting is **heavily constrained** by the DGMS low-frequency limits.

---

## 3. BLAST-03: Frequency model

### 3.1 Evidence

| Source | Frequency evidence |
|---|---|
| NIRM 2005 Table 2.1 / Fig 2.9 | Overall **5–27 Hz**; <10 Hz "usually present" |
| LAUBAG 1995 (Master Plan) | Mine I **5–39 Hz**; Mine II **5–28 Hz** |
| Residential structures | Natural frequencies **4–24 Hz** → resonance overlap |

### 3.2 Recommended construction (defer to generator; BLAST-03 partially done)

Sampling a flat `uniform(5, 27)` is acceptable as a default but discards the "usually <10 Hz" information. Preferred: a **left-skewed distribution** over 5–27 Hz with:

- **P(f < 8 Hz) ≈ 0.4–0.55** (wets the low-frequency bucket where DGMS is strictest),
- mode ≈ 9–12 Hz,
- upper tail thin ≥ 20 Hz.

Parametric candidate (transformed-normal / lognormal) or a simple empirical 3-bin model:
- <8 Hz: 45% | 8–25 Hz: 50% | >25 Hz: 5%.

The DGMS boundary at 8 Hz and 25 Hz makes these bins the ones that matter; the 8–25 Hz window carries the 10 mm/s (domestic) / 20 mm/s (industrial) / 5 mm/s (sensitive) limits, <8 Hz carries the strictest 5/10/2 limits.

---

## 4. BLAST-04: DGMS (Tech)(S&T) Circular 7 of 1997 thresholds (stored SEPARATELY)

**Do not use these as the TALUS risk label.** They are statutory structure-complliance limits, not a slope-failure equation. They enter the generator only as the regulatory overlay.

Permissible PPV (mm/s) by dominant excitation frequency:

**Category A — Buildings/structures NOT belonging to the owner**

| Structure type | < 8 Hz | 8–25 Hz | > 25 Hz |
|---|---:|---:|---:|
| Domestic houses/structures (kuchha, brick & cement) | 5 | 10 | 15 |
| Industrial buildings (RCC & framed) | 10 | 20 | 25 |
| Objects of historical importance & sensitive structures | 2 | 5 | 10 |

**Category B — Buildings belonging to the owner (limited span of life)**

| Structure type | < 8 Hz | 8–25 Hz | > 25 Hz |
|---|---:|---:|---:|
| Domestic houses/structures | 10 | 15 | 25 |
| Industrial buildings (RCC & framed) | 15 | 25 | 50 |

Sources: DGMS Circular 7/1997 verbatim tables recovered from: NIRM 2005 report (Table 1.1); EC-ADS response PDF (environmentclearance.nic.in); DGMS vibration-limits ScriSd copy; J. Sustainable Mining (2023) characterization. All five agree. **High confidence.**

NIRM's policy recommendation (2005): the 5 mm/s low-frequency residential limit is unnecessarily restrictive for Neyveli-class lignite mines; their surveys found no visible damage even at >4× the limit and recommend raising the low-frequency limit to 10 mm/s. Not a regulation — context.

---

## 5. BLAST-05: Generator design (deferred until 01–04 locked — now ready)

### 5.1 Latent event model (internal; preserves Member 3 interface)

The ML-facing columns stay exactly as planned:

```
blast_frequency_per_week   (schema name preserved)
blast_vibration_ppv_mms     (schema name preserved)
```

Internally, generate from richer physics:

```
BLAST EVENT
 ├── blast_occurs            ← weekly Poisson-ish from §1.2 (prior rate ~14–28/wk, tunable)
 ├── charge_per_delay_kg     ← sampled from §1.2 range (100–600 kg, mode ~300)
 ├── distance_m              ← from synthetic spatial layout (blast point → zone centroid/edge)
 ├── dominant_frequency_hz   ← sampled from §3.2 distribution (5–27 Hz, P<8Hz≈0.45)
 ├── ppv_raw_mms             ← PPV = 858.90 · (D/√W)^(−1.58)
 ├── ppv_observed_mms         ← ppv_raw × lognormal scatter (Calibration target: reproduce Table 2.1 scatter, r≈0.86)
 └── blast_disturbance       ← composite of ppv + frequency + distance + receiver zone
```

### 5.2 Blast disturbance (do NOT collapse to "PPV high → bad")

Blast severity = f(PPV, dominant frequency, distance, receiver zone):

1. **PPV versus DGMS limit for the receiver class** → compliance margin (`ppv / limit(freq, structure_category)`). Neyveli-specific: at <8 Hz, strictest; 8–25 Hz the main operating band.
2. **Resonance risk** — overlap of dominant frequency with residential 4–24 Hz band (Neyveli blasts sit inside it); low-PPV, low-frequency events still stress structures.
3. **Distance** — spatial from synthetic geometry (physically meaningful, unlike a scalar sample).
4. **Zone** — slope zone, infrastructure zone, township zone (members-1/2/3 geography); structure category A vs B per DGMS.

The exported `blast_vibration_ppv_mms` is then the **observed PPV at the nearest exposed structure** (truncated/scattered version of ppv_raw for the relevant zone), not a blanket random draw.

### 5.3 Provenance & versioning

- Constants locked in `data/processed/blasting/neyveli_blast_constants.csv` (below).
- Generator consumption rule: NEVER re-fit K/b or the DGMS table; re-draw only the stochastic drivers (W, D, f, scatter).

---

## 6. Cross-checks & consistency

- NIRM 2005 K/b fit (2005, 22 blasts) vs LAUBAG 1994 recommendations (SD 14.6–25 m/√kg) are mutually consistent: plugging SD=14.6 → PPV = 858.9×14.6^(−1.58) ≈ 11.7 mm/s ≈ the 12.5 mm/s safe level adopted in 1994; SD=25 → ≈ 4.3 mm/s. **Both eras agree.** ✅
- Derived powder factor (~0.31 kg/m³) matches NIRM's cited "low specific charge" mechanism. ✅
- Charge-per-delay 100–600 kg reproduces measured-class PPV (6–12 mm/s at 300–400 m). ✅
- Frequency bands: Mine I 5–39, Mine II 5–28, NIRM 5–27 — consistent 5 Hz floor band. ✅
- Blast geometry (200 mm / 15–22 m benches) fits the geology track's bench heights (6–25 m) and the blasting-only-on-OB premise (lignite bench unblasted). ✅

---

## Sources

- NIRM (2005) — Adhikari, G.R., et al., "Role of Blast Design Parameters on Ground Vibration…" MT/134/02: https://www.ultraenviro.com/nirm-vib-report.pdf (mirror of the DEP-hosted PDF). Also https://files.dep.state.pa.us/mining/BureauOfMiningPrograms/BMPPortalFiles/Blasting_Research_Papers/2005%20Adhikari%20Role%20of%20Blast%20Design.pdf
- NLC / LAUBAG (1995) — "Master Plan for Neyveli Area, Vol. VI Environment", §3.2.6 Ground vibration: https://archive.org/stream/in.ernet.dli.2015.474587/2015.474587.Neyveli-Lignite_djvu.txt (_secondary: OCR dump)
- Coal Age (2015) — "Neyveli Updates Its Excavator Fleet": https://www.coalage.com/features/neyveli-updates-its-excavator-fleet/
- MiningTechnology blog (2017) — "Lignite Mining at Neyveli & Bucket Wheel Excavators": http://miningtechnology1.blogspot.com/2017/06/lignite-mining-at-neyveli-bucket-wheel.html (_secondary ref blog)
- IJEA (2013) — "Balancing environmental protection and industry sustainability": https://www.ijeat.org/wp-content/uploads/papers/v2i4/D1418042413.pdf
- DGMS (Tech)(S&T) Circular No. 7 of 1997 — tables via NIRM report Table 1.1; EC-ADS response PDF; J. Sustainable Mining 2023 (Bulushi et al.)
- EC site (2022) — Itoura ADS response: https://environmentclearance.nic.in/writereaddata/Online/EDS/0_0_07_Jun_2022_1809378631ItouraADSResponse.pdf
- NLC operator experience (200 mm / 15–22 m benches): https://linkedin.com/in/mukteshwar-prasad-8200b429 (secondary, practitioner)
- NLC mining overview: https://www.nlcindia.in/new_website/mining.htm