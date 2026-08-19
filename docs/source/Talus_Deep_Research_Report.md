# Executive Summary  
We propose **Talus**, an *Explainable Rockfall Risk Estimation & Safe-Route Recommendation* platform for open-pit mines. Building on the SIH-2025 rockfall prediction theme, Talus fuses geological, environmental, and operational data to continuously assess rockfall risk per mine zone. Crucially, it adds **explainability and decision support**: clear SHAP-based breakdowns of why risk is high, trend alerts for rapidly rising hazard, and role-specific guidance (e.g. worker warnings, safety-officer insights, rescue priorities). An interactive map shows zone risks and “safe” evacuation paths. For the SIH 2026 internal hackathon, Talus will be demonstrated via a web/mobile prototype with simulated data: sliders for rainfall/blasting and images of cracks generate a changing risk map, SHAP explanations, and recommended detours and alerts.  

Talus is grounded in Indian context and standards. DGMS guidelines emphasize that heavy rainfall, steep benches, groundwater, and lack of monitoring cause most slope failures in opencast mines. ISRO’s disaster-management programs (e.g. NDEM) offer geospatial layers (elevation, land use, hazard zones) that Talus will leverage. Critically, Talus addresses known data gaps: there is *no public sensor network for mine stability*, so we will use historical incident data, weather and DEM datasets, and **synthetic data** (e.g. simulated slope failures and generated crack images) to train models. Explainability via SHAP ensures transparency and trust. 

**Key components**: (1) *Risk Estimator*: a regression/classifier (e.g. random forest, XGBoost, or neural nets) that outputs a zone-level risk score (0–100) or hazard probability from features like slope angle, rainfall intensity, crack severity, blasting vibration, historical rockfall counts, etc. (2) *SHAP Explainer*: attributes each zone’s risk to input features, producing clear “+X” contributions. (3) *Trend Detector*: flags zones where risk is rising sharply over time for early warning. (4) *GIS Visualization*: a Leaflet-powered map (React app) showing zones colored by risk, plus plotted “safe routes”. (5) *Routing Engine*: a PostGIS-based graph where each road segment’s cost increases with risk, so Dijkstra finds *risk-aware* paths. (6) *Alerts/Interface*: role-tailored messages – e.g. “Zone B risk 85: evacuate workers via Route 4” for field crews, and dashboard summaries for engineers and regulators.  

Talus emphasizes feasibility: it relies on public or easily-simulated data (IMD rainfall grids, geological DEMs, known mine layouts, DGMS slope reports), and standard open-source libraries (Scikit-learn/PyTorch for ML, SHAP for explainability, Leaflet/PostGIS for GIS). The prototype will focus on software; real sensors (vibration, inclinometers) are *not* required to demo the core concept. Over an 8-week sprint, the team will gather data, train ML models, build the UI/backend, and iteratively test on synthetic scenarios. Deliverables include a PPT, web prototype, demo video, and code repository. We will evaluate Talus via cross-validation (predictive accuracy) and scenario tests (consistency of alerts).  

Below we analyze stakeholders, data, models, architecture, timeline, and regulatory/ethical issues in detail. 

## Problem Statement (SIH 2026 Context)  
Rockfalls in open-pit mines cause frequent fatalities and damage. Mining regulators (DGMS) report that slope failures – often triggered by heavy rain, blasting, or geometry changes – are among the top accident causes. **Existing SIH 2025** addressed *prediction* of rockfalls. For SIH 2026, we **reframe** the problem as:  

> **“How can mining authorities transform fragmented site data into timely, explainable rockfall risk assessments and action recommendations?”**  

Rather than a black-box alert, Talus continuously fuses available data (weather, slope surveys, crack imagery, blasting logs, etc.) into a zone-level “rockfall risk” score. It then provides context (“why risk is high? what’s rising fastest?”) and decision support (evacuation routes, alerts). This shift from pure prediction to *risk management* fills a gap: mines may lack real-time monitoring, but still possess environmental data (from IMD, ISRO DEMs, internal logs, etc.). Talus leverages this to inform **when and how** to respond.  

## Stakeholders & User Roles  
- **Mine Workers/Field Crews**: Need clear, simple alerts (e.g. red-light zones, evacuation orders). Talus would push SMS/app notifications like *“Zone B (NW bench) risk ↑85 – avoid area”* or recommended safe routes (see GIS section).  
- **Site Safety Officers / Engineers**: Use the dashboard to monitor all zones. They need detailed *explanations* of risk (feature contributions), and trend charts. For example: “Zone B risk climbed 50→85 in 2 hours due to heavy rain and crack growth.” They can verify sensors or dispatch inspections.  
- **Mine Geotechnical Engineers**: Interested in underlying factors (soil, rock type, slope angle) and model calibration. They will use SHAP breakdowns to validate the model (“fault soil+rain=primary cause here”) and set design adjustments.  
- **Operations Managers / Executives**: Concerned with safety compliance and downtime. Talus provides aggregated key metrics (e.g. number of high-risk zones, evacuation counts) and ensures regulatory reporting (with audit logs of risk decisions).  
- **Regulators (DGMS)**: They require evidence of “due diligence.” Talus’s explainable logs (time-stamped risk reports, metrics) help demonstrate proactive safety management. By aligning alerts with DGMS guidelines (e.g. Red alert if Factor of Safety <1.3), Talus assists compliance.  
- **Nearby Community / Emergency Services**: Though secondary for this hackathon, Talus’s outputs (e.g. landslide/watershed maps from ISRO data) could feed district disaster planners. For now, focus is internal stakeholders.  

## Data Requirements and Sources  
Talus needs multi-type data inputs:  

- **Environmental/Weather:** Rainfall intensity and duration are critical triggers. We will use *Indian Meteorological Dept.* (IMD) data: e.g. high-resolution gridded rainfall (0.25°) available for 1901–2024. Live data can come from IMD RSS or district rain gauges (CWC river basin network). Temperature and humidity (IMD) can also be proxies.  
- **Geospatial/DEM:** Terrain elevation and slope are key. ISRO’s Bhuvan portal and NDEM provide free DEMs (SRTM/CartoDEM) and hazard layers. Geological Survey of India maps (strata type, rock strength) could be added if available (likely just as static GIS layers). Mine layout (bench/pit boundaries) will be digitized from public reports or paper maps.  
- **Operational Mining Data:** Design parameters (bench height/width, slope angle) from mining plans (DGMS circular 7/2011 requires geotech cell). Logs of past rockfall incidents (DGMS accident data if accessible) and blasting events (dates, charge weights) inform historical risk. In practice, we’ll simulate or use anonymized logs.  
- **Visual Crack Data:** Photographs of slope faces are used for CV. No public dataset exists for mine-specific cracks, but *transfer learning* is possible with road/concrete crack datasets (see below). We may collect a small set of annotated images (e.g. from open sources or create synthetic ones).  
- **Health Indicators:** If available, inclinometer or displacement meter readings (DGMS recommends monitoring instruments), as well as micro-seismic/vibration data post-blast. Such real sensor feeds likely won’t be accessible for prototype, but we will simulate plausible values for model inputs.  

### Official/Indian Data Agencies  
- **IMD (Ministry of Earth Sciences):** Provides historical and near-real-time rainfall. The official gridded rainfall dataset is “IMD 0.25°”. Current weather APIs (IMD doesn’t publicly provide an API, but local gauge data can be scraped or obtained).  
- **CWC (Central Water Commission):** River basin flood alerts can be combined with local rainfall to infer rising water tables.  
- **ISRO/NRSC (NDEM):** Satellite imagery (e.g. ISRO’s Bhuvan) and hazard maps (landslide susceptibility, flood inundation) are available. We can use these for baseline hazard zoning.  
- **DGMS (Mines Safety):** Although raw accident data isn’t public, DGMS publishes circulars and guidelines on slope monitoring (e.g. Circular 7/2011) which define critical thresholds. We will encode such rules as features (e.g. if bench height exceeds guidelines).  
- **Mining Databases:** If any government mine registry (Coal India, NMDC) is open, we can fetch nominal mine dimensions.  
- **Academic Datasets:** Indian researchers may have published slope stability or rockfall studies. For example, Senanayake et al. (2024) in *Int. J. Rock Mech.* attempted ML for rockfall hazard (though full text was blocked). Such papers may cite regional data, but most data is proprietary.  

### Data Gaps & Synthetic Generation  
No public dataset comprehensively covers all inputs. Major gaps: **real-time crack images** and **fine-scale geotech properties**. To address this:  
- **Synthetic Data:** Use physics-based simulation tools (e.g. RocFall, FLAC) to generate synthetic rockfall scenarios on hypothetical slope profiles. Perturb input features (rainfall events, blasting magnitude) and record “outcome” risk states.  
- **Augmented Imagery:** Generate synthetic crack images by programmatically superimposing crack patterns on slope photos using image libraries (Pillow, GANs) or 3D modeling. Alternatively, apply *transfer learning* from available crack datasets (see below) and fine-tune on a few hand-labeled mine images.  
- **Bootstrapping:** As one team suggested, synthetic DEM/weather can bootstrap initial model training. We’ll rely on that strategy, then adapt with any real data we can gather.  

**Example of Indian datasets:** IMD rainfall (gridded); Ultralytics “Crack Segmentation” (4,029 crack images); public slope survey reports. No dedicated “open-pit rockfall” dataset is known, so synthetic is key.  

## Machine Learning Models  
Talus will explore several ML approaches for risk scoring:  

- **Classical models (light, explainable):** Random Forests or Gradient Boosted Trees (XGBoost/LightGBM) can combine heterogeneous features (numerical and categorical) and handle missing data. They often yield good baseline accuracy on tabular hazard data, and SHAP works well on tree models. Logistic regression with engineered features (e.g. zone stability index) is interpretable. Disadvantages: may not capture complex nonlinear interactions as deep nets can.  
- **Neural networks:** Fully-connected MLPs or small feedforward nets can learn complex patterns but risk overfitting on limited data. Recurrent models (LSTM/GRU) might be used if we feed time series of sensor/weather into the net, predicting future risk. CNNs are mainly for image data (see next section).  
- **Hybrid models:** For temporal-spatial data, one could combine CNN (for spatial patterns like slope morphology) with LSTM (for sequence of events). However, given prototype constraints, we likely treat each zone as independent.  
- **Uncertainty & Calibration:** We will treat risk as a regression or probability. Tree and NN models often output uncalibrated probabilities. We will apply **probability calibration** techniques (e.g. Platt scaling or isotonic regression via scikit-learn) to ensure outputs are reliable confidences. We will evaluate calibration with reliability curves and Brier score.  
- **Evaluation Metrics:** For a *regression-style risk score*, use RMSE and MAE against any ground truth (e.g. simulated hazard levels). For binary “rockfall vs not” classification, use accuracy, precision/recall (to minimize false alarms), and AUROC. Since false negatives (missed hazard) are costly, we will emphasize recall (sensitivity) during tuning. Model selection will use k-fold validation on historical/simulated events.  

A comparative table of candidate models:

| Model          | Pros                            | Cons                             | Data Needs                          |
|----------------|---------------------------------|----------------------------------|-------------------------------------|
| Random Forest  | Robust, fast, handles missing data; SHAP explainer works directly.  | May require many trees for accuracy; limited extrapolation beyond training range. | Moderate-size tabular set (~1000+ events) |
| XGBoost/LightGBM | Often high accuracy, handles complex relations.              | Sensitive to hyperparams; needs more tuning; less interpretable per tree but SHAP still applies. | Similar to RF, benefits from more data. |
| Logistic/Linear | Very interpretable; probabilistic outputs.                     | Too simplistic for nonlinear interactions; may underfit. | Works even on small data; needs clear features. |
| Neural Net (MLP)| Can model complex patterns if enough data; integrated with uncertainty (e.g. dropout). | Black-box; needs more data/hp tuning; calibration needed. | Large labeled dataset or transfer learning.  |
| Ensemble (Stack)| Combines multiple models to improve accuracy.                 | Complex; risk of overfitting; slow. | Extensive data; careful validation needed. |

Ultimately, we will likely implement a RandomForest or XGBoost as a first version, due to ease of use and SHAP compatibility.  

## Explainability and Calibration  
To make Talus *trustworthy*, we will embed explainable AI techniques:  

- **SHAP (Shapley Additive Explanations):** For each zone’s risk prediction, compute SHAP values for input features. This produces a list of contributions (“+X mm rainfall contributed +0.30 to risk”). We will display these in the UI (as text or bar charts) so users see *why* the score is high. For example, if SHAP shows **Rainfall +30%, CrackDepth +25%, SlopeAngle +20%**, the safety officer knows heavy rain and widening cracks are driving risk. SHAP also offers a summary view of feature importance across zones.  
- **LIME/Counterfactuals (Optional):** As a fallback, we may allow small textual rules (if X>Z then risk up) or simple counterfactual queries (“if rainfall were 20% lower, risk would drop to Y”). However, SHAP is the focus for clear additive explanations.  
- **Calibration:** As noted, we will post-process model outputs so the predicted risk (e.g. a “60% chance of rockfall”) is statistically meaningful. This uses scikit-learn’s `CalibratedClassifierCV` or isotonic regression, ensuring that e.g. of all zones with predicted 0.8 risk, ~80% truly experienced an event. We will report calibration curves in validation.  

**Mock SHAP Example (ASCII):** Suppose Zone B has these feature values: heavy rainfall, large crack, steep slope, recent blasts. A SHAP breakdown might look like:

```
Zone B Risk Score = 0.87 (out of 1.0)

Feature Contributions (SHAP):  
+0.30  Crack severity (large, increasing)  
+0.25  Recent rainfall (heavy, 50 mm)  
+0.20  Slope angle (≥70°)  
+0.10  Past rockfall history (moderate)  
-0.05  Aftershock stabilization (time since blast)  

-> Base risk was 0.07, raised to 0.87 by these factors.
```

This format (or a bar-chart in the UI) makes the risk transparent to users. 

## Computer-Vision Crack Detection  
We will optionally include an image-processing pipeline: workers or drones capture slope-face photos, and a model detects and quantifies cracks. Key points:  

- **Approach:** Use a CNN-based segmentation model (e.g. U-Net or YOLOv8-seg) to identify cracks in images. We can train on an existing dataset of structural cracks. For example, the *Ultralytics Crack Segmentation* dataset provides 4,029 annotated images of road/wall cracks. While not mine-specific, it can serve for transfer learning. We can fine-tune on a small set of real or synthetic slope images where cracks are labeled.  
- **Annotations:** Cracks can be annotated as pixel masks (for segmentation) or bounding boxes (for detection). Segmentation yields crack area, which could correlate to hazard. We might measure *crack length/width* as features.  
- **Transfer Learning:** Start with a pre-trained model (from COCO or Crack-Seg) and retrain on even a few dozen mine crack images. Techniques like augmentations (rotation, lighting changes) will help generalize. If time-constrained, even simple edge filters (Canny + morphological ops) could flag major cracks as fallback.  
- **Datasets:** In addition to Crack-Seg, other public sets (e.g. SDNET2018 for concrete) are available. We may cite those generally. There is no Indian “rock crack” dataset, so we rely on publicly known ones for structural cracks.  
- **Feasibility:** CV is the highest-risk component. If insufficient data exists, we may skip production crack module and hard-code “high crack severity” via a UI switch in demo. But even a basic model would enhance explainability by providing that feature input.  

## GIS & Safe-Routing  
Talus integrates with a map interface (using **Leaflet.js** on React) and a PostGIS spatial database. Key components:  
- **Risk Map Layers:** Each mine “zone” (bench, ramp, area) will be a polygon with attributes (current risk score, trend). We color zones red/yellow/green by risk. As conditions change, these update dynamically.  
- **Geospatial Data:** The map will include pit boundaries, major infrastructure (offices, workshops), and shelters/assembly points. This data could be imported from KML/shapefiles (public or manually created).  
- **Routing Graph:** We represent the road network within the mine as a graph in PostGIS. Each segment has a base cost proportional to length. We then adjust the cost by the risk of adjacent zones. For example:  

  ``` 
  cost(edge) = length(edge) * (1 + α * max(risk_of_adjacent_zones))
  ``` 

  where α is a weight (e.g. α=2). Thus a road passing through a high-risk bench incurs extra cost, causing Dijkstra to prefer longer but safer detours.  

- **Safe-Route Algorithm:** Using the risk-weighted costs, we run Dijkstra (via pgRouting or a Python library) to compute shortest *safe* path between any two points (e.g. worker → shelter, or team base → incident). The UI will show both the normal shortest path and the safer alternative. If a road is extremely risky (risk > threshold), we may mark it blocked (no path).  
- **GIS Tools:** We will use PostgreSQL with PostGIS and possibly pgRouting (open-source) to handle spatial queries and graph routing. Leaflet (React-Leaflet) will display maps and allow clicking to simulate incidents or view routes.  

## System Architecture  
The architecture is a **Web-based decision platform** with optional mobile clients. All code will be open-source, using standard stacks:  

```mermaid
flowchart LR
  subgraph Mobile/Web Client
    A[React UI\n(Leaflet Map, Forms, Alerts)]
  end
  subgraph Backend Service
    B[FastAPI Server]
    C[PostgreSQL + PostGIS]
    D[AI Models (Python)]
  end
  subgraph Data Sources
    E[IMD Weather Data]
    F[Mine GIS (DEM, Layout)]
    G[Satellite/ISRO Layers]
    H[Synthetic Training Data]
  end
  subgraph Offline Mesh (Prototype)
    X[Local Data (simulated)]
  end

  E --> B
  F --> B
  G --> B
  H --> B

  B -- Query/Store --> C
  B -- Call ML models --> D
  D --> B

  A -- HTTP (REST/WS) --> B

  %% offline mode simulated by using H in place of E,F
  E --> X
  F --> X
  G --> X
  H --> X
```

- **Frontend:** A React application with Leaflet maps. It handles user login (demo mode), displays the risk map, plots “safe” routes, and shows pop-ups with SHAP breakdowns and alerts. It also includes form inputs for simulating conditions (e.g. sliders for rainfall, buttons to trigger an “New Crush-event” in a zone).  
- **Backend:** A Python FastAPI service. Endpoints include: getting/updating zone data, running risk prediction (calls ML models), and computing routes. It periodically fetches data (in real deployment) but in prototype it uses stored JSON or synthetic data.  
- **Database:** PostgreSQL+PostGIS stores mine geometry and time-series of feature values. It also logs incident records. The ML models query this DB for the latest inputs.  
- **ML & CV:** Implemented in Python (Scikit-learn, XGBoost, PyTorch). Risk model predicts score per zone. SHAP is computed (TreeExplainer or DeepExplainer depending on model). The crack-detection CNN (e.g. a tiny U-Net) can run on the backend or on-device.  
- **Offline Prototype Mode:** For the internal demo, we may simulate an offline scenario by treating some “client” as an isolated data source (this may involve dropping some feeds). The architecture itself remains mostly online-oriented, as offline mesh is out-of-scope for this problem.  

## Offline Prototype vs Real Deployment  
- **Prototype:** All data is local/simulated. We will pre-load historical/synthetic data into the DB. UI sliders let judges tweak conditions. Models run on the same machine or backend. Connectivity issues are not simulated.  
- **Real Deployment:** Would involve IoT sensors (piezometers, weather stations, cameras), mobile data links (or local mesh networks), and possibly edge computing near mines. The app would run on devices with intermittent connectivity, caching data. True deployment must handle disconnected mode, GDPR-like privacy for worker data, and robust, real-time pipelines. We will *mention* this gap in limitations.  

## Demo Plan & Minimal Dataset  
We will prepare a small synthetic dataset for a fictional open-pit mine:  

- **Mine Layout:** 4 zones (A, B, C, D) with known coordinates.  
- **Background Data:** A DEM profile and average rainfall/climate.  
- **Features:** For each zone, tabulate a few time-stamped records of (rainfall, slope, blasting, crack metric, etc.) and a “true” risk value (from a toy model or rules).  
- **Crack Images:** A few annotated images (even generic rock wall cracks from creative common sources). Or use snippets from Crack-Seg as stand-ins.  
- **Scenarios:** Pre-set scenarios (e.g. “heavy storm”, “post-blast”) to trigger risk changes.  

**Demo sequence** (for evaluators):  
1. Show **risk map** with all zones (green for low risk).  
2. **Click Zone B** – pop-up shows "Risk 65", and a SHAP breakdown (e.g. +rain +crack, base).  
3. Use slider: increase rainfall → see Zone B color go red, risk jump, SHAP re-computed (rain component larger).  
4. Show **trend chart** for Zone B risk (rising line).  
5. Introduce a **new crack image** (via file upload or simulated event): risk updates further.  
6. Show **safe route** calculation: draw path from a worker spawn to exit. First map shows shortest path, second shows risk-aware path (e.g. avoiding Zone B).  
7. Trigger **alerts**: push notifications or on-screen messages like “Evacuate Zone B (risk 85).” Demonstrate different messages for “Worker” vs “Supervisor” roles.  
8. All while speaking to how data flows: “Input data → Risk model → GIS/map → Actions.”  

This covers all core features. The PPT (Slide) will summarize these points, but we will actually *do* them in the prototype.  

## Implementation Timeline (8 Weeks)  
We break the next 8 weeks into milestones. Team of 6 can be roughly: 2 frontend, 2 backend, 1 ML/CV, 1 testing/integration. Below is a week-by-week plan with deliverables:

| Week | Milestones                                    | Deliverables                          |
|------|-----------------------------------------------|---------------------------------------|
| 1    | Refine problem statement; gather data sources (IMD rainfall, DEM, crack images, synth rules). Set up project (Git repo, frameworks). | Data inventory; initial DB with sample data. |
| 2    | Develop risk model pipeline: select features, build toy RandomForest/XGBoost, train on synthetic data. Basic SHAP integration. | Working risk-prediction script; initial SHAP outputs. |
| 3    | Implement GIS database: load mine zones and map layers into PostGIS. Prototype Leaflet map with static zones. | Map UI with dummy zones; DB schema. |
| 4    | Connect risk model to backend: FastAPI endpoint for /predictRisk. Frontend fetches risk per zone. | Dynamic risk map (colors update via API). |
| 5    | Build CV crack detector (use pre-trained YOLO or U-Net). Integrate to derive “crack severity” feature. | Crack detection demo on sample images; backend endpoint. |
| 6    | Routing engine: encode road graph, implement risk-weighted Dijkstra. Frontend to toggle risk-aware route. | Example of safe route displayed on map. |
| 7    | UI polish: SHAP explanation pop-ups, trend charts (e.g. using Chart.js), alert notifications. Prepare role-based message templates. | Feature-complete prototype (besides data). |
| 8    | Testing & data tuning: simulate scenarios end-to-end. Prepare PPT slides, record 2-min demo video. Finalize code repo. | Demo video, final prototype build, PPT ready. |

(Note: Weeks overlap tasks in parallel.) Each week ends with a “demoable” increment.  

## Implementation Details  

- **Tech Stack:** React + Leaflet (UI), FastAPI (backend), PostgreSQL/PostGIS (data), Pandas + scikit-learn/XGBoost (ML), SHAP library for explanations, PyTorch/TensorFlow or OpenCV (CV), pgRouting (C++) or custom for routing. Use git/GitHub for version control. All chosen tools are open-source.  
- **Development Practices:** Containerize services (Docker) for consistency; write unit tests for core modules (e.g. risk calculation). Document code and data schema for clarity.  
- **Compute:** A standard laptop with 8GB RAM suffices for prototyping. Pre-trained models will be small, or use CPU only. If needed, free-tier cloud instances (AWS/GCP) can run heavier tasks.  
- **Team Roles:** We should assign (tentatively) – *Team Lead* (overall coordination, PPT design), *Data Engineer* (data gathering/synthetic generation), *Backend Engineer* (API, DB), *Frontend Engineer* (UI/UX), *ML Engineer* (models, SHAP), *CV Specialist* (crack detection, data labeling). Cross-training is possible.  

## Evaluation Plan and Experiments  
To validate Talus during development:  

- **Model Accuracy:** Use cross-validation on our synthetic/historical dataset. For regression risk, compute MAE/RMSE. For classification (risk>threshold), compute precision/recall. Iterate features to improve.  
- **Explainability Checks:** Verify SHAP values make sense: e.g. if we artificially increase rainfall in test, SHAP should show its coefficient rising. Check that features with no effect have near-zero SHAP.  
- **Route Testing:** Design artificial road graph and risky zones; confirm risk-weighted routing avoids high-risk edges. Benchmark against plain Dijkstra to show difference.  
- **UI/UX:** Conduct a quick informal user test among teammates: does the alert wording make sense? Is the map clear? Feedback can refine the interface.  
- **Performance:** Ensure API response and routing are under 1 sec for demo. Simulate up to 100 zones to test scaling.  
- **Failure Modes:** Test corner cases, e.g. no data (missing input), or conflicting data (rain=0 but high risk) to see if system fails gracefully (e.g. shows “data unavailable” warnings).  

We will log these results (with screenshots/code) to include in handover materials for SIH judges.  

## Regulatory, Safety, and Ethical Considerations  
- **DGMS Compliance:** The system will align with Mines Act & DGMS Circulars. We avoid making automatic life-safety decisions; Talus gives *recommendations*. Final decisions remain with certified personnel. Alerts will advise (“should evacuate”), not command. All interventions comply with regulations (e.g. if safety factors drop below 1.3, it triggers an alarm as per DGMS rule).  
- **Data Privacy:** We won’t handle personal data (e.g. individual worker IDs) in this prototype. If extended, location check-ins of personnel would require opt-in. All data in Talus is essentially geospatial and sensor readings – generally not PII. Still, we’ll note this and use secure channels (HTTPS).  
- **Model Bias and Liability:** Our model estimates risk but is not infallible. We will include disclaimers (e.g. “Talus provides guidance only”). False negatives (missed hazard) are dangerous; we will calibrate conservatively and test for under-prediction. False positives (false alarms) cause distrust; we will tune to minimize those via ROC analysis.  
- **Safety:** If used for actual mines, Talus must be tested in field trials. For SIH, we state that our prototype is an aid – human engineers would review all alerts.  
- **Ethical Use:** We ensure Talus is used solely for safety. No commercial exploitation without oversight. As open-source hackathon work, we follow standard research ethics.  

## Limitations & Future Work  
- **Data Availability:** Our prototype uses synthetic/historical data. In practice, real-time data (weather stations, crack sensors) would be needed. This is a major gap. As noted, *Talus currently assumes data feeds that may not exist*. We will highlight this and suggest collaboration with mines/IG organisations for real data.  
- **Generality:** Models trained on one mine may not transfer well to others (different geology). We plan to allow re-training with local data, but acknowledge domain shift as a challenge.  
- **Scale:** The prototype covers one mine area. Future work could extend to multiple mines via the same platform (multi-tenant).  
- **Edge/Offline Operation:** We do not implement the offline mesh concept in this project. In remote mines without connectivity, an edge-deployed version of Talus (with local compute) would be required. That is noted as future extension.  
- **Additional Hazards:** While focused on rockfalls, the platform could in future incorporate related hazards (e.g. flooding in pit, gas leaks).  
- **User Training:** The system’s recommendations should be validated by experts. We assume users have basic training in rock mechanics.  

## Prioritized Action List (Next 8 Weeks)  
1. **Week 1:** Finalize scope & data plan. Set up code repo, environments. Collect base data (IMD grids, existing maps).  
2. **Week 2:** Implement risk-scoring pipeline (model+features) and SHAP analysis.  
3. **Week 3:** Build GIS database and simple map UI.  
4. **Week 4:** Connect backend API for risk queries. Integrate with UI coloring.  
5. **Week 5:** Develop or integrate crack-detection model and map its output.  
6. **Week 6:** Implement risk-weighted routing, show alternate paths.  
7. **Week 7:** Develop alert generation (role-specific), trend warnings, UI polishing.  
8. **Week 8:** Full system test, bug fixes, prepare final PPT/video/repo.  

Throughout, schedule short daily stand-ups to track progress.  

## Resource List (APIs, Datasets, Libraries, Compute)  

- **Datasets/APIs:**  
  - *IMD Pune Gridded Rainfall* (NetCDF) – high-res historical/real-time rain.  
  - *Crack Segmentation Dataset* (Roboflow/Ultralytics) – 4K annotated crack images (for CV).  
  - *OpenStreetMap* or manual shapefiles for mine roads.  
  - *DGPS/Vintage Data* from a known mine (if any open).  
  - *Google Maps API* (optional, for basemap).  
- **Libraries/Tools:**  
  - **ML:** Scikit-learn (includes calibration), XGBoost/LightGBM, PyTorch.  
  - **Explain:** SHAP (TreeExplainer/DeepExplainer), LIME.  
  - **CV:** OpenCV (preprocessing), Ultralytics YOLO (for segmentation) or TensorFlow/Keras U-Net.  
  - **GIS/Routing:** PostGIS, pgRouting or NetworkX (Python). Leaflet.js in React. shapely/fiona for geometry.  
  - **Web:** FastAPI (Python), React + Material-UI (or Tailwind) for frontend.  
  - **Other:** Pandas, NumPy, chart.js/Plotly for plotting.  
- **Compute:** A modern laptop (16GB RAM recommended). No specialized hardware needed beyond a possible GPU for CV (a mid-range GPU for 4K images would speed up training, but not mandatory). Cloud GPU (e.g. free Google Colab) can be used for CNN training if needed.  

## Tables  

**Datasets Inventory**

| Dataset Name | Source (Institution)           | Variables/Format            | Access         | Suitability (for Talus)                    |
|--------------|-------------------------------|-----------------------------|----------------|-------------------------------------------|
| IMD Gridded Rainfall | India Meteorological Dept (MoES) | Daily rainfall (mm) on 0.25° grid (NetCDF) | Public (IMD Pune) | High – world-class coverage of rain, essential input. |
| Ultralytics Crack-Seg | Ultralytics/Roboflow | 4,029 crack images (jpg + segmentation masks) | Open (GitHub)  | Medium – good for transfer learning on cracks. |
| Satellite DEM (SRTM) | NASA/ISRO (NDEM) | Elevation data (GeoTIFF)     | Public (ISRO/NDEM) | High – base terrain for slope angles. |
| Mine Layout (synthetic) | Own creation              | GIS polygons (PostGIS)     | N/A            | High – needed for zones and roads.       |
| Synthetic Scenarios | Generated by team         | Tabular features + “true risk” | Prototype build | Medium – fills training gap.             |
| OpenStreetMap roads | OpenStreetMap               | Road graph (OSM XML)        | Public (osm.org) | Medium – to build mining road network.   |
| DGMS Circulars | DGMS website           | Text guidelines            | Public         | Context – helps define risk logic.       |

**Candidate Models**

| Algorithm           | Type         | Pros                                           | Cons                                       | Data Needs                |
|---------------------|--------------|------------------------------------------------|--------------------------------------------|--------------------------|
| Random Forest      | Tree-based   | Handles mixed data, robust, fast training. SHAP-ready. | May overfit small data; less smooth outputs. | Hundreds of samples, feature engineering. |
| XGBoost/LightGBM  | Tree-based   | Often best tabular performance; handles missing. | More hyperparameters; risk of overfitting if small data. | Similar to RF, plus careful tuning. |
| Logistic/Linear   | Regression   | Simple, interpretable, fast.                   | Cannot capture nonlinear interactions.     | Works with small data if features are good. |
| Neural Net (MLP)  | Deep learning| Can learn complex patterns if enough data.     | Black-box, needs more data/compute; harder to explain. | Thousands of examples ideally. |
| Ensemble (Stack)  | Hybrid       | Can blend strengths of multiple models.        | Complex, computationally heavy.            | Large labeled dataset; careful design. |
| LSTM/GRU         | RNN (time)   | Incorporates temporal trends.                  | Requires sequential data; slower.         | Time-series data per zone; extended history. |

**Implementation Milestones**

| Week | Tasks                                    | Output/Milestone                        |
|------|------------------------------------------|-----------------------------------------|
| 1    | Scope finalization; data gathering; repo set-up. | Data inventory and starter templates. |
| 2    | Build risk model prototype (RF/GBM + SHAP). | Working model + SHAP outputs.         |
| 3    | GIS DB and React map (static).         | Map showing zones (no logic).          |
| 4    | Connect model to API; color zones by risk. | Live risk map (colors change).        |
| 5    | Develop crack-detection model (CV).    | Crack detector working on sample image. |
| 6    | Implement routing (risk-weighted); UI for route toggle. | Safe-route feature operational.       |
| 7    | Alerts/trends UI; refine explain outputs. | Alerts display; trend chart plot.     |
| 8    | Final integration; testing; PPT/video prep. | Demo-ready prototype + docs.          |

## System Architecture (Mermaid Diagram)  

```mermaid
graph TB
  subgraph Frontend
    UI[React + Leaflet Map\n(User Interface)]
    UI --> |API calls (REST/JSON)| Backend
  end
  subgraph Backend
    Backend[FastAPI Server]
    Models[Risk ML & CV Models]
    DB[PostgreSQL + PostGIS]
    Backend -- DB query --> DB
    Backend -- predict() --> Models
    Models -- results --> Backend
  end
  subgraph DataSources
    Weather[IMD Weather Data]
    DEM[Elevation/ISRO Data]
    Operations[Mine Survey Logs]
    Weather --> Backend
    DEM --> Backend
    Operations --> Backend
  end
```

- **Data Flow:** On the frontend, a user-trigger (e.g. “simulate rainfall”) hits the React UI, which calls the FastAPI backend. The backend queries the database for current features (plus any simulated inputs), runs the **Risk Model**, obtains a score and SHAP values, and updates the GIS DB. The backend then returns updated zone risks and route info to the UI.  

## PPT Summary Slide (One-Page Content)  

- **Problem:** Open-pit mine slopes suffer unpredictable rockfalls (rain, blasting, cracks). Data is siloed; decisions lack unified support. (SIH2025 had a rockfall prediction problem.)  
- **Solution (Talus):** A *Risk Management Platform* – it fuses weather, geology, and imagery into real-time **zone-level risk scores**. Key features:  
  - **Explainable AI:** SHAP-based breakdown (“rain + crack = high risk”).  
  - **Trend Alerts:** Identifies rapidly escalating zones (pre-warning).  
  - **Risk-Aware Routing:** Re-routes evacuation paths away from danger.  
  - **Role-Specific Alerts:** Notifies workers (“Zone B red – evacuate”), officers (“Risk ↑ due to rains”), managers (reports).  
- **Architecture:** React/Leaflet front-end, FastAPI + PostgreSQL/PostGIS back-end. ML models (RandomForest/XGBoost + CNN) with SHAP for explainability. Data: IMD rain, ISRO/DEM, synthetic scenarios.  
- **Impact:** Enhances worker safety by actionable alerts; empowers engineers with data-driven insight; complements DGMS guidelines with transparent risk scoring. Could cut rockfall incidents dramatically (industry claims up to ~70–90% reduction).  
- **Feasibility:** Prototype uses only software (no new sensors needed). By SIH internal hackathon deadline, we will deliver a working web demo (map, alerts, demo video), PPT, and code repo.  
- **Next Steps:** Prioritize data prep, model training, and UI integration (week-by-week plan). Identify labs (IMD, ISRO) for possible data access. Test and calibrate the system, focusing on true-safety outcomes.  

Each bullet above would appear on the slide (visually, the slide would have very brief text with supporting icons or mini-graphics, not all citations). 

## References  

- SIH 2025 Problem Statement: *“AI-Based Rockfall Prediction and Alert System for Open-Pit Mines”*.  
- DGMS Mining Safety Guidelines on slope monitoring.  
- ISRO Disaster Management Services (NDEM, satellite mapping).  
- IMD Gridded Rainfall Data (0.25°).  
- Ultralytics Crack Segmentation Dataset (4,029 images).  
- SHAP Explainability (Shapley values).  
- Sklearn Probability Calibration (reliability).  

