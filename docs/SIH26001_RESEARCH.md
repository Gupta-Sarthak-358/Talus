# SIH26001 — Complete Research & Strategy Document

**TALUS: Physics-Informed Landslide Risk Intelligence and Decision Support System for NER**

> This document consolidates all research, analysis, and strategic planning for
> migrating TALUS from open-pit mine rockfall (SIH25071) to NER landslide
> monitoring (SIH26001). It covers the problem statement, domain research,
> existing systems audit, data availability, architecture mapping, validation
> strategy, competitive positioning, and roadmap.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [SIH26001 Problem Statement Analysis](#2-sih26001-problem-statement-analysis)
3. [NER Domain Context](#3-ner-domain-context)
4. [Existing Systems Landscape](#4-existing-systems-landscape)
5. [Gap Analysis](#5-gap-analysis)
6. [Data Sources & Availability](#6-data-sources--availability)
7. [Physics & ML Adaptation](#7-physics--ml-adaptation)
8. [Architecture Mapping: TALUS → NER](#8-architecture-mapping-talus--ner)
9. [Validation & Ground Truth Strategy](#9-validation--ground-truth-strategy)
10. [Research Survey](#10-research-survey)
11. [Competitive Positioning](#11-competitive-positioning)
12. [Roadmap & Next Steps](#12-roadmap--next-steps)

---

## 1. Executive Summary

**Problem:** The North Eastern Region (NER) of India faces frequent landslides
during monsoon seasons, causing loss of life, infrastructure damage, and
isolation of remote villages. Current monitoring is reactive and dependent on
manual reporting. No operational system in NER combines AI/ML prediction with
role-based decision support, road connectivity tracking, emergency
prioritisation, and offline functionality.

**Opportunity:** SIH26001 (AI-Based Early Warning and Landslide Risk Monitoring
System in NER) under the Ministry of Development of North Eastern Region
(MDoNER) calls for exactly this system. The TALUS architecture — originally
built for mine rockfall — maps almost perfectly onto SIH26001's requirements.
What changes is the data layer and physics; the architecture survives intact.

**Key finding:** Unlike the mine problem (where no public dataset existed), NER
has real, documented landslide data from multiple sources — GSI Bhusanket
(91,000+ mapped landslides), NASA COOLR, ISRO Landslide Atlas (80,000+),
published academic inventories (490-1,330+ events with rainfall records), and
40+ years of IMD rainfall data. This means we can train on real events, not
synthetic data — a stronger evidence base than TALUS v1.

**Competitive gap:** GSI's Regional Landslide Forecasting System (RLFS) uses
rainfall thresholds only — no AI/ML, no soil moisture, no satellite analysis,
no per-slope prediction, no role-based decisions, no road tracking, no offline.
GSI has explicitly listed "Integration of AI/ML as a decision-support layer" as
their next advancement initiative. We are solving a problem they've publicly
identified.

**Recommendation:** Migrate TALUS to SIH26001. The architecture survives. The
data gets better. The domain gets more urgent.

---

## 2. SIH26001 Problem Statement Analysis

### 2.1 Full text

**Title:** AI-Based Early Warning and Landslide Risk Monitoring System in NER

**Category:** Software | **Theme:** Disaster Management

**Organization:** Ministry of Development of North Eastern Region (MDoNER)

**Background:**
> The North Eastern Region (NER) frequently faces landslides, flash floods, road
> blockages, and slope failures due to heavy rainfall, fragile terrain, and
> unplanned hill cutting. These incidents often disrupt connectivity, damage
> infrastructure, delay emergency response, and isolate remote villages for days.
> Currently, monitoring of vulnerable zones is mostly reactive and dependent on
> manual reporting. There is limited use of real-time predictive systems for
> identifying high-risk zones and issuing early warnings to authorities and local
> communities. With increasing climate vulnerability in the region, there is a
> need for an AI-enabled real-time monitoring and prediction system that can help
> authorities take preventive action before disasters occur.

**Description:**
> This problem statement proposes the development of an AI-powered early warning
> and monitoring platform capable of predicting and tracking landslide-prone
> areas in real time across the North Eastern Region. The solution should:
>
> a. Collect and analyse data from: Rainfall patterns, Soil moisture sensors,
>    Satellite imagery, Terrain/slope data, Historical landslide records
>
> b. Use AI/ML models to identify high-risk zones and predict possible
>    landslide events.
>
> c. Provide real-time alerts to district administrations, disaster management
>    authorities, and local communities.
>
> d. Integrate GIS mapping for visualization of vulnerable roads, villages,
>    and infrastructure.
>
> e. Allow citizens/field officials to upload geo-tagged photos/videos of
>    cracks, slope movement or blocked roads.
>
> f. Generate dashboards showing: Risk severity levels, Road connectivity
>    status, Weather-linked risk forecasts, Emergency response prioritisation.
>
> g. Support multilingual notifications and low-network/offline functionality
>    for remote areas.

**Expected Solution:**
> A scalable AI-based software platform with:
> - Real-time GIS dashboard and risk heatmaps
> - AI/ML-based predictive analytics engine
> - Mobile/web application for field reporting and alerts
> - Integration with IMD weather APIs, satellite feeds, and sensor data
> - Automated SMS/app-based early warning system
> - Cloud-based architecture with offline sync support for remote regions

### 2.2 Decomposition into technical requirements

| # | Requirement | Technical need | TALUS v1 equivalent |
|---|---|---|---|
| R1 | Multi-source data ingestion | ETL pipeline for rainfall, soil moisture, satellite, DEM, geology | Generator pipeline |
| R2 | AI/ML risk prediction | ML model (RF/XGBoost/LightGBM) on conditioning factors | ML predictor |
| R3 | Real-time GIS dashboard | Leaflet/Mapbox + risk heatmap layer | Zone map |
| R4 | Risk severity levels | Score → band mapping (5 levels) | Risk bands |
| R5 | Road connectivity status | Road network graph + risk overlay | Routing graph |
| R6 | Weather-linked forecasts | IMD API integration + temporal prediction | Trend chart |
| R7 | Emergency prioritisation | Role-based decision logic | Decision engine |
| R8 | Field reporting (geo-tagged) | Mobile app with camera + GPS | Evidence card |
| R9 | SMS/app alerts | Notification pipeline | Alert system |
| R10 | Multilingual support | i18n framework + local languages | Not present |
| R11 | Offline/low-network | Local-first architecture + sync | Local-first design |
| R12 | Explainability | SHAP per prediction | SHAP module |
| R13 | Calibrated confidence | Isotonic calibration | Calibration |

### 2.3 What the PS does NOT require

- Real-time IoT sensor deployment (we use satellite/reanalysis data as proxy)
- InSAR ground deformation monitoring (requires hardware)
- Exact location/time prediction of individual landslides (we predict susceptibility)
- Hardware installation (PS is Software category)

---

## 3. NER Domain Context

### 3.1 Why NER is landslide-prone

The North Eastern Region comprises 8 states: Arunachal Pradesh, Assam, Manipur,
Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura. Key factors:

**Geological:**
- Part of the seismically active Eastern Himalayan belt (Zone V — highest hazard)
- Complex geology: schist, phyllite, sandstone, gneiss, alluvial deposits
- Active tectonic lineaments and fault zones
- Fragile rock formations weathered by tectonic activity

**Climatic:**
- Extreme monsoon rainfall: Cherrapunji receives ~12,000 mm/year
- Rainfall intensity: >144mm/day triggers landslides (Dahal & Hasegawa 2008)
- ~67-73% of annual rainfall concentrated in monsoon season (June-September)
- Climate change increasing rainfall variability and extremes

**Topographic:**
- Steep slopes (0-76° range in Meghalaya)
- Deep valleys and river gorges
- Rapid elevation changes over short distances (e.g. Dauki fault escarpment)

**Anthropogenic:**
- Unplanned road cutting (identified as #1 predictor in Meghalaya — NEHU 2026)
- Deforestation and land-use change
- Construction on unstable slopes
- Hydropower project development

### 3.2 Landslide statistics for NER

| State | Total landslides (GSI) | With dates | Landslide events |
|---|---|---|---|
| Arunachal Pradesh | 26,451 | 58 | — |
| Assam | 571 | 91 | 72 |
| Manipur | 3,013 | 42 | — |
| Meghalaya | 1,225 | 304 | 235 |
| Mizoram | 1,860 | 581 | 272 |
| Nagaland | 2,104 | 946 | 840 |
| Sikkim | 2,923 | 2,218 | 459 |
| Tripura | 89 | 12 | — |

**Key number:** 37,903+ documented landslides in NER states. However, many lack
precise dates. Sikkim and Nagaland have the best-dated inventories.

### 3.3 Rainfall thresholds for NER landslides

From Monga & Ganguli (2026, J. Hydrologic Engineering) — 490 rain-driven
landslides, 2006-2019, 8 NER stations:

- Regional moisture-driven landslide (MDL) threshold: E (mm) = −11.10 + 0.62×D (hr),
  for 24 < D < 1440 hr (Monga & Ganguli, J. Hydrologic Engineering, Jan 2026,
  peer-reviewed version of 2024 preprint)
- Monsoon season threshold: ~13 mm/day separates slide vs no-slide days
- 67% of events occurred during monsoon (June-September)
- Spatial variability: Guwahati/Shillong have higher thresholds (91.8mm/3-day)
  vs Aizawl/Imphal (lower thresholds)
- LULC controls on thresholds: forested areas have higher rainfall tolerance

### 3.4 Key conditioning factors (from published research)

From multiple NER landslide studies (Meghalaya 2021, Dibang Valley 2026,
Aizawl 2026):

| Factor | Importance | Source |
|---|---|---|
| Elevation | High (gravitational stress) | Dibang 2026 |
| Slope angle | High (steepness → instability) | All studies |
| Lithology | High (material strength) | Dibang 2026 |
| Rainfall | High (trigger) | All studies |
| Lineament density | High (tectonic faults) | Dibang 2026 |
| Distance to roads | Very High (#1 in Meghalaya) | NEHU 2026 |
| NDVI / vegetation | Moderate (root reinforcement) | Multiple |
| Soil moisture | Moderate (pore pressure) | Dibang 2026 |
| Distance to rivers | Moderate (toe erosion) | Multiple |
| LULC | Moderate (land use impact) | Multiple |
| Aspect | Low-Moderate (sun vs moisture) | Multiple |
| Curvature | Low-Moderate (water accumulation) | Multiple |
| TWI/SPI | Low-Moderate (hydrology) | Multiple |
| Geomorphology | Low (terrain type) | Multiple |

---

## 4. Existing Systems Landscape

### 4.1 Government operational systems

#### GSI Regional Landslide Forecasting System (RLFS)

- **Operator:** GSI National Landslide Forecasting Centre (NLFC), Kolkata
- **Method:** Empirical rainfall thresholds + Numerical Weather Prediction models
- **Output:** 24/48hr landslide forecast bulletins, 4 levels (Low/Moderate/High/
  Very High)
- **Coverage:** 21+ districts across 8 states (as of mid-2025, up from 16 at
  inception in Jul 2024; expanding toward nationwide 2030 target)
- **NER coverage:**
  - Assam: Dima Hasao, Cachar (experimental, MoU with ASDMA Aug 2024)
  - Nagaland: Peren, Dimapur, Kohima (experimental)
  - Sikkim: 6 districts (experimental)
  - Mizoram: planned
  - Meghalaya: planned
- **Accuracy:** CSI >70% in operational districts (Darjeeling, Kalimpong,
  Nilgiris, Rudraprayag)
- **Public tools:** Bhusanket portal (inventory + maps), Bhooskhalan app
  (crowd-sourced reporting + forecast visualization)
- **GSI's own assessment of gaps:**
  - Scarcity of AWS/ARGs/ground sensors
  - InSAR for near-real-time monitoring still limited
  - Data sharing among agencies remains challenging
  - Need for AI/ML integration as decision-support layer
  - Need for Gram Panchayat-level granularity

#### IIT Mandi — P-RIL / GEE Portal (Prof. Dericks Praise Shukla)

- **Coverage:** Entire Indian Himalayan Region (most extensive in India)
- **Method:** Topographic susceptibility (26,000 GSI landslides) + real-time
  rainfall (IMERG) → P-RIL (Probability of Rainfall-Induced Landslides)
- **Output:** Daily landslide forecasts via Google Earth Engine web portal,
  PDF bulletins, WhatsApp alerts
- **Training:** 26,000 landslides from GSI database, ensemble ML models
- **Status:** Operational, web-based

#### IIT Mandi — Ground-Shift Sensor Network (Prof. Varun Dutt)

- **Method:** Detects sub-millimeter slope movement via physical sensors
- **Output:** On-site hooters/blinkers triggered by detected movement
- **Status:** Deployed in Himachal Pradesh

#### IIT Mandi — Low-Cost AI Sensor Array (Prof. Kala Venkata Uday)

- **Method:** Low-cost sensor arrays across 60+ sites in Himachal Pradesh
- **Output:** Predicts landslides up to 3 hours in advance, >90% accuracy
- **Status:** Deployed, operational

#### Nagaland Eliona

- **Launched:** May 2026
- **Operator:** NSDMA Nagaland
- **Type:** AI-native Climate and Disaster Intelligence Supercomputing Platform
- **Capabilities:** Weather/climate modelling, disaster simulations, earth
  observation analytics, ML research, decision intelligence
- **Status:** Launched, capabilities being built out

#### NESAC Disaster Management Support

- **Operator:** North Eastern Space Applications Centre, Shillong
- **Capabilities:** Landslide hazard zonation, vulnerability assessment,
  risk assessment maps for Guwahati city
- **Status:** Operational, NER-focused

### 4.2 Research / prototype systems

#### NASA LHASA 2.0 (Open-Source, Operational)

- **Full name:** Landslide Hazard Assessment for Situational Awareness
- **Operator:** NASA Goddard Space Flight Center
- **Repository:** github.com/nasa/LHASA (open-source)
- **Method:** XGBoost ML model at 1km daily resolution, using IMERG rainfall,
  SMAP soil moisture, snow mass, slope, distance to faults, lithologic strength
- **Output:** Global landslide probability maps, exposure analysis (population
  + roads), 1-3 day forecast capability
- **Resolution:** 30 arc-second (~1km), 60°N-60°S
- **Status:** Operational, updated ~4x daily via landslides.nasa.gov/viewer
- **Key advantage:** Pre-computed global susceptibility map as free prior;
  twice as likely to catch historical landslides as LHASA v1 at same FP rate
- **Relevance to TALUS v2:**
  - **Benchmark:** Run LHASA over NER and show our NER-specific model beats it
  - **Fallback layer:** For sparse-data pixels, blend LHASA susceptibility
  - **Credibility:** "We outperform NASA's own operational model" > "GSI lacks AI"

#### ML-CASCADE / ILSM (IIT Delhi, Open-Source)

- **Authors:** Nirdesh Sharma, Manabendra Saharia, G.V. Ramana (IIT Delhi)
- **Method:** Ensemble ML (ANN + RF + SVM) with imbalance handling (OSS +
  SVMSMOTE), blending approach
- **Resolution:** 0.001° (~100m), pan-India
- **Accuracy:** 95.73%, sensitivity 97.08%, MCC 0.915
- **Inventory:** 154,329 GSI landslide points + 489 from global repository
- **Output:** India Landslide Susceptibility Map (ILSM), 5 classes
- **Status:** Published (Catena 2024), open-source, Zenodo dataset
- **Relevance to TALUS v2:**
  - Closest published precedent to our pipeline design
  - Handles "areas with no labeled landslides" problem
  - Methodology can be directly referenced for training data approach

#### Amrita A-LEWS / AmritaWNA (Amrita Vishwa Vidyapeetham)

- **Type:** Real-time IoT geophysical sensor + AI + GIS landslide early warning
- **Sensors:** 100-200+ geophysical sensors (rainfall, pore water pressure,
  seismic activity) across monitored slopes
- **Coverage:** Munnar, Kerala (since 2009); Chandmari, Gangtok, Sikkim
  (since 2015, 200+ sensors across 150-acre monitored area)
- **Capabilities:** 3-24hr advance warnings, landslide monitoring
- **Track record:** Operational since 2009, 5,000+ lives protected
- **Limitation:** Hardware-heavy, requires physical deployment, not scalable
  to all of NER
- **Note:** "Amritakripa" is Amrita's separate crowdsourced disaster-relief
  coordination app (Kerala floods 2018) — not the sensor system

#### NEHU AI Landslide Susceptibility Map (Meghalaya)

- **Published:** February 2026
- **Method:** 10 ML models ensemble, GSI + NESAC data
- **Accuracy:** >90%
- **Output:** Static susceptibility map (5 risk categories)
- **Finding:** ~7% of Meghalaya in very-high risk; East Khasi Hills most
  vulnerable; proximity to roads is #1 predictor

#### Dibang Valley LSM (Mihu et al. 2026)

- **Method:** XGBoost + LightGBM, 10 conditioning factors
- **Data:** 537 inventoried landslides (376 train / 161 test)
- **Accuracy:** AUC 0.96
- **Top predictors:** Elevation, lithology, rainfall, lineament density
- **Finding:** 25-35% of valley in high/very-high susceptibility

#### Brahmaputra-CoPilot (IIT Patna, 2025)

- **Type:** Multilingual edge-AI flood + landslide advisory
- **Languages:** Assamese-Hindi-English code-mix
- **Data:** Rainfall nowcasts, river gauge, SAR flood masks, DEM
- **Status:** Conceptual/simulation only, not deployed
- **Limitation:** Never implemented; simulation benchmarks only

### 4.3 Commercial / enterprise systems

| System | Type | Relevance |
|---|---|---|
| SCS Tech Smart LEWS | IoT + AI + GIS, enterprise | Not public, not NER-specific |
| Landslide Monitoring Dashboard | Web-based monitoring | landslidemonitoring.in, basic |
| NRSC NDEM | National disaster geoportal | Includes landslide early warning |

---

## 5. Gap Analysis

### 5.1 What exists vs what SIH26001 requires

| Requirement | Who does it | Who doesn't | Gap severity |
|---|---|---|---|
| Rainfall data integration | GSI RLFS, IIT Mandi | — | ✓ Solved |
| Soil moisture integration | A-LEWS (hardware only) | GSI RLFS, IIT Mandi | **Major** |
| Satellite imagery analysis | NRSC/NESAC (raw data) | GSI RLFS (no analysis) | **Major** |
| Terrain/slope-specific prediction | IIT Mandi (susceptibility) | GSI RLFS (regional only) | **Moderate** |
| Historical landslide records | GSI Bhusanket (91,000+) | — | ✓ Available |
| AI/ML risk prediction | Research (NEHU, Dibang), NASA LHASA (global) | GSI RLFS (thresholds only) | **Moderate** |
| Real-time GIS dashboard | NDEM (basic), A-LEWS | GSI RLFS (bulletins only) | **Major** |
| Field reporting (geo-tagged) | Bhooskhalan (basic) | No structured workflow | **Major** |
| Road connectivity status | Nobody | — | **Complete** |
| Emergency prioritisation | Nobody | — | **Complete** |
| Weather-linked risk forecasts | GSI RLFS (24/48hr) | Most others | ✓ Partial |
| Multilingual notifications | Brahmaputra-CoPilot (conceptual) | All operational systems | **Major** |
| Low-network/offline | A-LEWS (sensor-based) | All web-based systems | **Major** |
| Role-based dashboards | Nobody combines all | — | **Complete** |
| Calibrated confidence | Nobody in NER space | — | **Complete** |
| Per-prediction explainability | Research only | All operational systems | **Major** |

### 5.2 The critical gap: GSI explicitly wants AI/ML

From GSI's own advancement initiatives (NIDM presentation 2026):

> "Integration of AI/ML as a decision-support layer in the existing landslide
> early warning system"

And from GSI DG Asit Saha (Economic Times, July 2025):

> "There is ongoing research underway to develop a more robust landslide
> forecasting model and expert system leveraging artificial intelligence (AI)"

**We are solving a problem GSI has publicly identified as their next priority.**

### 5.3 What makes TALUS v2 different from everything else

Every existing system does 2-3 things. TALUS v2 does all of them:

| Capability | GSI RLFS | IIT Mandi P-RIL | NASA LHASA | A-LEWS | **TALUS v2** |
|---|---|---|---|---|---|
| Rainfall thresholds | ✓ | ✓ | ✓ | ✓ | ✓ |
| AI/ML prediction | ✗ | Partial | ✓ (XGBoost) | ✗ | **✓** |
| Soil moisture | ✗ | ✗ | ✓ (SMAP) | ✓ (hardware) | **✓** |
| Satellite imagery | ✗ | ✗ | ✓ (IMERG) | ✓ | **✓** |
| Terrain analysis | ✗ | ✓ | ✓ | ✓ | **✓** |
| Calibrated confidence | ✗ | ✗ | ✗ | ✗ | **✓** |
| SHAP explainability | ✗ | ✗ | ✗ | ✗ | **✓** |
| Per-slope prediction | ✗ | Partial | ✓ | ✓ | **✓** |
| Real-time GIS | ✗ | ✓ | ✓ | ✓ | **✓** |
| Role-based decisions | ✗ | ✗ | ✗ | ✗ | **✓** |
| Road connectivity | ✗ | ✗ | ✗ | ✗ | **✓** |
| Emergency prioritisation | ✗ | ✗ | ✗ | ✗ | **✓** |
| Risk-aware routing | ✗ | ✗ | ✗ | ✗ | **✓** |
| Field reporting | ✗ | ✗ | ✓ | ✗ | **✓** |
| Scenario simulation | ✗ | ✗ | ✗ | ✗ | **✓** |
| Evidence transparency | ✗ | ✗ | ✗ | ✗ | **✓** |
| Offline functionality | ✗ | ✗ | Partial | ✗ | **✓** |
| Multilingual | ✗ | ✗ | ✗ | ✗ | **✓** |

---

## 6. Data Sources & Availability

### 6.1 Rainfall

| Dataset | Resolution | Coverage | Access |
|---|---|---|---|
| IMD 0.25° gridded daily | 0.25° (~27.5 km), daily, 1901-present | National | imdpune.gov.in |
| IMD station data | Point, daily, 1980-2019 | 8 NER stations | IMD DSP portal |
| CHIRPS | 0.05° (~5 km), daily, 1981-present | Global | CHIRPS portal |
| NASA GPM IMERG | 0.1° (~10 km), half-hourly | Global | NASA GES DISC |
| NCMRWF forecasts | Various | National | NCMRWF |

**NER stations with daily rainfall (1980-2019):** Aizawl, Darjeeling, Gangtok,
Kalimpong, Kohima, Guwahati, Shillong, Imphal

### 6.2 Soil moisture

| Dataset | Resolution | Coverage | Access |
|---|---|---|---|
| ERA5 (ECMWF) | 0.25° (~27.5 km), hourly | Global, 1979-present | Copernicus CDS |
| SMAP (NASA) | 36km, daily | Global, 2015-present | NASA Earthdata |
| Sentinel-1 SAR | 10m, 6-12 day revisit | Global | ESA Copernicus |

ERA5 volumetric water content (0.15-0.45 range) is most used in NER research.
SMAP provides finer temporal resolution.

### 6.3 DEM / Terrain

| Dataset | Resolution | Access |
|---|---|---|
| SRTM DEM v3 | 30m | USGS Earth Explorer |
| Copernicus GLO-30 | 30m | Copernicus |
| Cartosat-1 DEM | 30m | ISRO Bhuvan |
| ALOS PALSAR DEM | 12.5m | NASA Earthdata |

Derived products: slope, aspect, curvature, TWI, SPI, flow accumulation,
drainage network, hillshade, elevation bands.

### 6.4 Satellite / Land Cover

| Dataset | Resolution | Access |
|---|---|---|
| Sentinel-2 | 10m | ESA Copernicus |
| Landsat-8 | 30m | USGS Earth Explorer |
| MODIS LULC | 500m | NASA Earthdata |
| ISRO Bhuvan LULC | 30m | Bhuvan |

NDVI computed from Sentinel-2/Landsat-8. LULC classification from Sentinel-2.

### 6.5 Geology / Lithology

| Dataset | Access |
|---|---|
| GSI Bhukosh geological maps | bhukosh.gsi.gov.in |
| Lineament density (derived) | Computed from DEM + geological maps |
| Seismic zone maps | GSI / NDMA |

### 6.6 Historical landslide inventories

| Source | NER coverage | Events | Access |
|---|---|---|---|
| GSI Bhusanket | 37,903+ in NER | Point locations + year | bhukosh.gsi.gov.in |
| NASA GLC (Global Landslide Catalog) | Global, 11,000+ since 2007 | Point + date | landslides.nasa.gov/viewer |
| NASA COOLR (crowdsourced) | Global, community-contributed | Point + date | landslides.nasa.gov/viewer |
| ISRO Landslide Atlas | 80,000+ nationwide | Seasonal + event-based | nrsc.gov.in |
| NESAC | NER-specific | Regional | NESAC Shillong |
| Mizoram inventory (Sarma 2026) | 19 events, 2016-2025 | Individual events | Zenodo (open) |
| Meghalaya (NEHU 2026) | 1,330+ | Point locations | Published research |
| Dibang Valley (Mihu 2026) | 537 | Point locations | Published research |
| NEH thresholds (Monga 2026) | 490 events, 2006-2019 | Point + year | Published research |
| ILSM (Sharma et al. 2024) | India-wide, 100m | 154,329 landslide points | Zenodo (open) |
| National LSM (Khan et al. 2025) | India-wide, 90m | 109,504 landslides | Nature Scientific Reports |

### 6.7 Infrastructure / Exposure

| Dataset | Access |
|---|---|
| Road network | OpenStreetMap / Bhuvan |
| Settlement locations | Census / OSM |
| River network (derived from DEM) | Computed |
| Critical facilities | OSM / State GIS portals |

### 6.8 Real-time APIs

| Source | API | Data |
|---|---|---|
| IMD | Weather forecast API | Rainfall forecasts |
| Sentinel Hub | EO Browser | Satellite imagery |
| Google Earth Engine | GEE API | Processed satellite data |
| OSM Overpass API | REST | Road/building data |

### 6.9 Verified data access (Aug 2026)

All primary data sources confirmed accessible:

| Dataset | Access method | Account needed | Verified |
|---|---|---|---|
| IMD 0.25° daily rainfall | imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html | No (direct download) | ✅ |
| IMD rainfall (Python) | `pip install imdlib` → `imd.get_data('rain', 1901, 2024)` | No | ✅ |
| IMD rainfall (CLI) | `pip install imddata` → `imddata --name rain --syear 2020 --eyear 2024` | No | ✅ |
| ERA5 soil moisture | cds.climate.copernicus.eu (CDS API) | Free CDS account | ✅ |
| SRTM DEM 30m | USGS EarthExplorer or NASA Earthdata | Free account | ✅ |
| NASA COOLR landslides | landslides.nasa.gov/viewer (CSV/SHP/GDB download) | No | ✅ |
| COOLR REST API | gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer | No | ✅ |
| GSI Bhusanket inventory | bhusanket.gsi.gov.in (NLSM maps + landslide polygons) | No | ✅ |
| GSI Bhukosh geology | bhukosh.gsi.gov.in/Bhukosh/Public | No | ✅ |
| Sentinel-2 NDVI | ESA Copernicus Open Access Hub | Free account | ✅ |
| OSM roads/rivers | Overpass API or Geofabrik extracts | No | ✅ |
| ISRO Landslide Atlas | nrsc.gov.in | No | ✅ |
| ILSM (Sharma et al. 2024) | Zenodo (100m, 154K points) | No | ✅ |
| National LSM (Khan et al. 2025) | Nature Scientific Reports (DOI: 10.1038/s41598-025-33446-0) | No | ✅ |
| NASA LHASA 2.0 | github.com/nasa/LHASA + landslides.nasa.gov/viewer | No | ✅ |
| ML-CASCADE / ILSM (IIT Delhi) | Zenodo + published (Catena 2024) | No | ✅ |

**IMD grid spec:** 135×129 grid, 66.5°E-100°E × 6.5°N-38.5°N, 0.25° resolution.
NER bounding box (88°E-98°E, 21°N-29°N) falls entirely within this grid.

---

## 7. Physics & ML Adaptation

### 7.1 What changes from mine to NER

| Aspect | Mine (TALUS v1) | NER Landslide (TALUS v2) |
|---|---|---|
| Failure mode | Rockfall from bench slope | Soil/rockslide on hillside |
| Primary trigger | Rainfall + blasting | Rainfall (antecedent + triggering) |
| Material | Rock (cohesion-dominated) | Soil/weathered rock (friction + cohesion) |
| Water mechanism | Wetting → pore pressure → crack growth | Infiltration → saturation → pore pressure |
| Geometry | Fixed bench (angle, height) | Variable terrain (DEM-derived) |
| Vegetation | Not a factor | NDVI significant predictor |
| Human factors | Blasting (PPV, crack growth) | Road cutting (#1 predictor in Meghalaya) |
| Seismicity | Not a factor | Zone V (highest hazard) |
| Drainage | Not a factor | Distance to rivers significant |
| Lineaments | Not a factor | Tectonic faults control groundwater |

### 7.2 New physics chain

**Mine chain (v1):**
```
Rainfall → groundwater wetting → pore pressure → cracks → cohesion loss → FoS → score
```

**NER chain (v2):**
```
Rainfall (antecedent + triggering)
    ↓
Soil moisture / wetting state (infiltration model)
    ↓
Pore pressure in soil mantle
    ↓
Shear strength reduction
    ↓
Slope stability (FoS per pixel)
    ↓
Landslide susceptibility score
```

### 7.3 New feature set

| # | Feature | Unit/Type | Source | Role |
|---|---|---|---|---|
| 1 | slope_angle | degrees | DEM-derived | Structural geometry |
| 2 | elevation | m | DEM | Structural geometry |
| 3 | aspect | degrees | DEM | Sun exposure / moisture |
| 4 | curvature | dimensionless | DEM | Water accumulation |
| 5 | twi | dimensionless | DEM | Topographic wetness |
| 6 | spi | dimensionless | DEM | Stream power |
| 7 | rainfall_24h_mm | mm | IMD/GPM | Triggering |
| 8 | rainfall_7d_mm | mm | IMD/GPM | Antecedent |
| 9 | rainfall_30d_mm | mm | IMD/GPM | Antecedent |
| 10 | soil_moisture | 0-1 | ERA5/SMAP | Pore pressure proxy |
| 11 | ndvi | -1 to 1 | Sentinel-2 | Vegetation / root strength |
| 12 | lulc | categorical | Sentinel-2 | Land use impact |
| 13 | lithology | categorical | GSI Bhukosh | Material strength |
| 14 | distance_to_road | m | OSM | Anthropogenic disturbance |
| 15 | distance_to_river | m | DEM-derived | Toe erosion |
| 16 | lineament_density | km/km² | GSI + DEM | Tectonic weakness |
| 17 | drain_density | km/km² | DEM | Surface drainage |

Plus:
- `zone_id` (spatial unit — pixel, slope, or administrative)
- `previous_landslide` (0/1 — pre-existing failure)

### 7.4 Target

**Primary:** landslide susceptibility (binary: event / no-event at this location
and time)

**Secondary:** risk level (5 bands: very low, low, moderate, high, very high)

**Not:** exact location/time of individual landslides (we predict susceptibility,
not specific events)

### 7.5 ML model selection

Based on published NER research:

| Model | Published AUC in NER | Notes |
|---|---|---|
| XGBoost | 0.95-0.96 | Best in Dibang Valley, Chamoli |
| LightGBM | 0.96 | Best in Dibang Valley |
| Random Forest | 0.83-0.90 | Good, interpretable |
| Ensemble (RF+XGBoost+LGBM) | 0.95+ | NEHU Meghalaya approach |
| Logistic Regression | 0.85-0.89 | Baseline |
| CNN (1D) | 0.88 | B-1D MCNN study |

**Recommendation:** Start with RF + XGBoost ensemble (matches TALUS v1
approach), add LightGBM as third family. Seven-family convergence test from
v1 can be adapted.

---

## 8. Architecture Mapping: TALUS → NER

### 8.1 Module mapping

| TALUS v1 Module | TALUS v2 (NER) | Change needed |
|---|---|---|
| Generator (physics sim) | **NGEN** (NER data pipeline) | Complete rewrite — real data, not synthetic |
| ML Predictor | **ML Predictor** | Retrain on NER features; same RF/XGBoost architecture |
| SHAP Explainability | **SHAP Explainability** | Same module, new feature names |
| Calibration | **Calibration** | Same isotonic approach, new target |
| Trend/Escalation | **Trend/Escalation** | Same logic, adapted to monsoon temporal patterns |
| Decision Engine | **Decision Engine** | New roles: villager, officer, manager, rescue |
| Routing | **Routing** | New graph: NER road network with risk weights |
| Scenario Engine | **Scenario Engine** | New physics: rainfall thresholds, soil moisture scenarios |
| Evidence Card | **Evidence Card** | New provenance: satellite, sensor, crowd-sourced |
| Alert System | **Alert System** | Add SMS gateway, multilingual, offline sync |
| Dashboard | **Dashboard** | New UI: GIS heatmap, road status, emergency priority |
| Backend API | **Backend API** | Same FastAPI, new endpoints |
| Mobile App | **Mobile App** | New: camera/GPS for field reporting, offline tiles |

### 8.2 What survives unchanged

- Architecture pattern (two-engine: ML + physics simulation)
- Calibration methodology (isotonic, Brier-measured)
- SHAP explainability framework
- Decision engine pattern (role-based escalation)
- Routing algorithm (risk-weighted Dijkstra)
- Evidence transparency (missing data flags)
- Test suite structure
- Offline-first design philosophy

### 8.3 What changes significantly

- **Data pipeline:** Synthetic generator → real NER geospatial data ingestion
- **Physics chain:** Mine FoS → rainfall-infiltration slope stability
- **Features:** 12 mine features → 17 NER features
- **Training data:** 73,000 synthetic rows → real historical landslide events
- **Scenario engine:** Mine storm replay → rainfall threshold scenarios
- **UI:** Mine zone map → NER GIS heatmap with roads/villages
- **Mobile:** Evidence card → field reporting with camera/GPS
- **Notifications:** Alert system → SMS + multilingual + offline

---

## 9. Validation & Ground Truth Strategy

### 9.1 The data advantage

Unlike TALUS v1 (synthetic-only), TALUS v2 has real ground truth:

- **490+ dated landslide events** with rainfall records (Monga 2026)
- **537 inventoried landslides** in Dibang Valley (Mihu 2026)
- **1,330+ landslides** in Meghalaya (NEHU/Agrawal 2021)
- **91,000+ mapped landslides** in GSI Bhusanket
- **40+ years of IMD rainfall** at 8 NER stations
- **Published benchmark results** (AUC 0.89-0.96) to validate against

### 9.2 Training data construction

```
Positive samples (landslide occurred):
    Historical landslide location + date
    + Antecedent rainfall (7d, 30d before event)
    + Soil moisture at time of event
    + Terrain features (slope, elevation, etc.)
    + Geology, LULC, proximity to roads/rivers

Negative samples (no landslide):
    Random locations >300m from any known landslide
    + Same temporal conditions
    + Same terrain/geology features
```

### 9.3 Validation approach

1. **Spatial cross-validation:** Leave-one-cluster-out (not random split —
   spatial autocorrelation)
2. **Temporal validation:** Train on 2007-2018, test on 2019-2024
3. **Published benchmark comparison:** Match or exceed AUC 0.96 (Dibang)
4. **LHASA benchmark:** Run NASA LHASA 2.0 over NER and show we outperform it
5. **Calibration validation:** Brier score, ECE on held-out events
6. **Scenario validation:** Cross-check against published rainfall thresholds
   (Monga 2026)

### 9.4 What we can validate against

| Published result | Our target |
|---|---|
| Dibang XGBoost AUC 0.96 | Match or exceed |
| Meghalaya ensemble >90% accuracy | Match or exceed |
| NEH rainfall threshold: E = −11.10 + 0.62×D | Scenario engine produces consistent results |
| GSI RLFS CSI >70% | Our system should exceed (we add more data sources) |
| NASA LHASA 2.0 over NER | Our NER-specific model should outperform global model |

---

## 10. Research Survey

### 10.1 NER-specific landslide studies

| Study | Year | Region | Method | Key finding |
|---|---|---|---|---|
| Agrawal & Dixit (Meghalaya) | 2021 | Meghalaya | FR, AHP, FAHP | 1,330 landslides; 15 conditioning factors; southern escarpment highest risk |
| NEHU (Meghalaya) | 2026 | Meghalaya | 10 ML models ensemble | >90% accuracy; proximity to roads #1 predictor |
| Mihu et al. (Dibang) | 2026 | Arunachal Pradesh | XGBoost + LightGBM | AUC 0.96; elevation, lithology, rainfall, lineament density dominate |
| Mittamidi et al. (Aizawl) | 2026 | Mizoram | AHP + FR + Yc | 10 layers; AUC 0.891 (AHP), 0.905 (FR), 0.889 (Yc) |
| Monga & Ganguli | 2026 | NEH (8 stations) | Quantile regression | 490 events; moisture-driven thresholds; E = −11.10 + 0.62×D; 67% monsoon |
| Sarma & Paul (Mizoram) | 2026 | Mizoram | Rate-and-state friction | 19 events, 2016-2025; rainfall → pore pressure → failure timing |
| Khan et al. (National) | 2025 | India (national) | AHP, FR, Yc | 109,504 landslides; Nagaland 55%, Mizoram 53% susceptible; AUC 0.874-0.905 |
| IIT Mandi P-RIL | 2026 | IHR (all) | Ensemble ML + P-RIL | 26,000 GSI landslides; daily forecasts; Google Earth Engine |
| NASA LHASA 2.0 | 2021+ | Global (60°N-60°S) | XGBoost + IMERG/SMAP | 1km daily; open-source; twice as accurate as v1 |
| ML-CASCADE / ILSM (IIT Delhi) | 2024 | India (national) | Ensemble ML (ANN+RF+SVM) | 100m; 95.73% accuracy; 154K landslide points |

### 10.2 Broader landslide ML studies

> **Note:** The following papers are cited in broader literature reviews but
> could not be independently verified with primary sources (DOI/repo) as of
> Aug 2026. Treat specific accuracy figures as unverified until primary source
> is confirmed. Do NOT cite these live to judges without pulling the original.

| Study | Year | Method | Key finding |
|---|---|---|---|
| B-1D MCNN | 2024 | Bayesian-optimized CNN | 87.5% accuracy; slope stability classification |
| Matilda | 2025 | SVR + RF + ELM | R² >0.98 for FoS; simulation + AI hybrid |
| Cloud-based EWS (Zhonglian) | 2025 | LSTM + D-S theory | 69 sensors; R² 0.91; reduce false alarms |
| SlopeWise (Keen AI) | 2025 | CV for crack detection | Drone footage → crack detection |
| PIML frameworks | 2024-2026 | Physics-informed NN | Embed physics in loss function; data-efficient |
| Granite pillar stability | 2026 | Stacking ensemble | 93% accuracy; SHAP for explainability |

### 10.3 Key physics papers

| Paper | DOI / Source | Verified | Relevance |
|---|---|---|---|
| Dahal & Hasegawa 2008 | 10.1016/j.geomorph.2008.01.014, Geomorphology | ✅ | I=73.90×D^(-0.79); >144mm/day → high risk in Himalayas |
| Guzzetti et al. 2007 | Landslides journal | ⚠️ not re-checked | Global rainfall thresholds for landslide triggering |
| Marino et al. 2020 | 10.1007/s10346-020-01400-y, Landslides | ✅ | In-situ soil moisture improves regional LEWS |
| Springman et al. 2013 | ETH Zurich / Springer | ✅ (co-author confirmed) | Wetness anomalies → failures in Switzerland |
| Klose 2015 | Not re-checked | ⚠️ | Critical VWC threshold ~0.40 — treat as approximate |
| Iverson 2000 | 10.1029/2000WR900090, Water Resources Research | ✅ | Rainfall infiltration theory; Richards equation; infinite slope model |

---

## 11. Competitive Positioning

### 11.1 The one-sentence position

> "Every existing system stops at detection or threshold alerting. TALUS v2
> starts where detection ends: understand the risk, explain why, simulate
> what-if, escalate to the right people, and route around danger."

### 11.2 Three things to say if asked "how is this different?"

1. **"GSI's RLFS uses rainfall thresholds. We add AI/ML that integrates soil
   moisture, terrain, satellite, and historical records — the layer GSI has
   explicitly said they need."**

2. **"No operational system in NER today provides role-based emergency
   prioritisation, road connectivity tracking, or risk-aware routing. We do."**

3. **"We don't just say 'risk is high.' We say 'here's which road to avoid,
   here's which village to evacuate first, here's where to send rescue teams,
   and here's what data we're missing.'"**

### 11.3 What NOT to claim

- We are NOT replacing GSI's RLFS — we complement it with AI/ML
- We are NOT doing real-time InSAR — that requires hardware
- We are NOT deploying IoT sensors — that's A-LEWS/AmritaWNA's domain
- We are NOT predicting exact landslide locations/times — we predict susceptibility
- We are NOT claiming field-validated production accuracy — this is a prototype

### 11.4 Honest limitations (to state proactively)

1. We use satellite/reanalysis soil moisture (not in-situ sensors) — resolution
   limitations
2. Historical landslide inventories have spatial/temporal incompleteness
3. The model is static (conditioning factors don't change) — only rainfall and
   soil moisture are dynamic
4. No real-time sensor integration in prototype
5. Multilingual NLP for NER languages needs community co-design
6. Offline sync architecture needs field testing

---

## 12. Roadmap & Next Steps

### 12.1 Phase 0: Data assembly (NOW — before hackathon)

| Task | Source | Priority |
|---|---|---|
| Download IMD 0.25° gridded daily rainfall for NER (1980-2024) | imdpune.gov.in | Critical |
| Download SRTM DEM 30m for NER states | USGS Earth Explorer | Critical |
| Compile GSI Bhusanket NER landslide inventory | bhukosh.gsi.gov.in | Critical |
| Download ERA5 soil moisture for NER (2000-2024) | Copernicus CDS | High |
| Download Sentinel-2 NDVI/LULC for NER | ESA Copernicus | High |
| Download GSI lithology maps for NER | bhukosh.gsi.gov.in | High |
| Download OSM road/river network for NER | OpenStreetMap | High |
| Download published inventories (Mizoram, Meghalaya, Dibang) | Zenodo / papers | High |
| Compute terrain features (slope, aspect, curvature, TWI, SPI) from DEM | GIS tools | Critical |

### 12.2 Phase 1: Core ML (hackathon sprint 1)

| Task | Deliverable |
|---|---|
| Build NER data pipeline (ETL from all sources) | Feature matrix per pixel/zone |
| Train RF + XGBoost on historical events | Trained models |
| Validate against published benchmarks | AUC, accuracy metrics |
| Implement SHAP explainability | Per-prediction explanations |
| Implement isotonic calibration | Calibrated probabilities |

### 12.3 Phase 2: Decision layer (hackathon sprint 2)

| Task | Deliverable |
|---|---|
| Build GIS dashboard with risk heatmap | Leaflet/Mapbox map |
| Implement role-based decision engine | 4 roles: villager, officer, manager, rescue |
| Add road connectivity overlay | Road graph + risk weights |
| Implement risk-aware routing | Safe detour recommendations |
| Build scenario engine (rainfall threshold simulation) | What-if tool |

### 12.4 Phase 3: Platform (hackathon sprint 3)

| Task | Deliverable |
|---|---|
| Build mobile field reporting app | Camera + GPS + offline |
| Implement SMS/app alert pipeline | Multilingual notifications |
| Add offline sync architecture | Local-first + cloud sync |
| Integrate IMD weather API | Real-time rainfall feeds |
| Polish dashboards and presentation | Demo-ready |

### 12.5 Timeline

```
Now (Aug 27)     : Data assembly begins
Sept 1-20        : SIH idea submission window
Oct-Nov          : Evaluation period
Dec 2026         : Grand Finale (if selected)
```

---

## Appendix A: Key Numbers to Remember

| Metric | Value | Source |
|---|---|---|
| NER documented landslides | 37,903+ | GSI Bhusanket |
| India-wide mapped landslides | 91,000+ (33,904 field-validated) | GSI |
| ISRO Landslide Atlas events | 80,000+ | NRSC/ISRO |
| Dibang Valley inventory | 537 events | Mihu et al. 2026 |
| Meghalaya inventory | 1,330+ events | Agrawal 2021 / NEHU 2026 |
| NEH rainfall-triggered events | 490 (2006-2019) | Monga & Ganguli 2026 |
| IMD NER stations | 8 (daily, 1980-2019) | IMD |
| Published AUC (NER ML) | 0.89-0.96 | Multiple studies |
| GSI RLFS districts | 21+ across 8 states (mid-2025, expanding) | GSI |
| GSI target: operational | Nationwide by 2030 | GSI roadmap |
| GSI CSI in operational districts | >70% | GSI |
| NER states | 8 | — |
| landslide-prone area of India | 0.42 million km² (12.6%) | GSI |
| AWS density in landslide areas | 1 per 350 km² | GSI |
| ILSM (Sharma et al. 2024) | 154,329 points, 100m, 95.73% accuracy | Zenodo / Catena |
| National LSM (Khan et al. 2025) | 109,504 landslides, 90m, AUC 0.874-0.905 | Scientific Reports |

## Appendix B: Data Download Checklist

```
[ ] IMD daily gridded rainfall (0.25°, 1980-2024) for NER bounding box
[ ] SRTM DEM v3 30m for NER 8 states
[ ] ERA5 soil moisture (volumetric water content, 1979-2024)
[ ] Sentinel-2 L1C for NDVI computation (2023-2024, cloud-free composites)
[ ] GSI Bhukosh lithology maps for NER
[ ] GSI Bhusanket landslide inventory (NER filter)
[ ] NASA COOLR global landslide catalog
[ ] ISRO Landslide Atlas products
[ ] OSM road network for NER (Overpass API)
[ ] OSM river network for NER
[ ] OSM settlement/building data for NER
[ ] Published inventories from papers (Zenodo: Mizoram, Dibang)
[ ] India Landslide Susceptibility Map (ILSM 100m, Zenodo)
[ ] Census village/population data for NER
```

## Appendix C: References

1. SIH26001 Problem Statement — Ministry of Development of North Eastern Region
2. GSI Regional Landslide Forecasting System — bhusanket.gsi.gov.in
3. GSI NLFC NIDM Presentation 2026 — nidm.gov.in
4. Lok Sabha Question No.664 (22.07.2026) — sansad.in
5. Mihu et al. (2026) — Dibang Valley LSM, Springer
6. NEHU (2026) — Meghalaya AI LSM, Times of India
7. Monga & Ganguli (2026) — NEH moisture-driven thresholds, J. Hydrologic Engineering
8. Sarma & Paul (2026) — Mizoram frictional timescales, Zenodo
9. Agrawal & Dixit (2021) — Meghalaya LSM, multiple models
10. Khan et al. (2025) — National-scale LSM, Scientific Reports (DOI: 10.1038/s41598-025-33446-0)
11. Mittamidi et al. (2026) — Aizawl LSM, AHP + FR + Yc, Disaster Advances
12. IIT Mandi P-RIL (2026) — Economic Times
13. Nagaland Eliona (2026) — India Today NE
14. ASDMA-GSI MoU (2024) — Business Standard
15. GSI DG interview (2025) — Economic Times
16. ISRO Landslide Atlas (2023) — nrsc.gov.in
17. ILSM (Sharma, Saharia & Ramana, Catena 2024) — Zenodo
18. Indian Infrastructure Vulnerability to Landslides (2025) — Zenodo
19. Brahmaputra-CoPilot (Nayak & Dudam, IJRASET 2025) — simulation-only, not deployed
20. Amrita A-LEWS / AmritaWNA — amrita.edu
21. SCS Tech Smart LEWS — scstechindia.com (confirmed real)
22. NASA LHASA 2.0 — github.com/nasa/LHASA (open-source, operational)
23. ML-CASCADE / ILSM (IIT Delhi) — open-source, Zenodo
24. Landslide Monitoring Dashboard — landslidemonitoring.in
