# Talus — Master Project Document
## Risk-Aware Decision Support for Open-Pit Mine Safety

This document contains everything needed to fill the official SIH 2026 6-slide template (Title → Idea → Technical Approach → Feasibility → Impact → Research & References). Sections below are ordered to match those slides exactly, so each section can be trimmed and pasted directly. Deeper research, full citations, and internal notes follow after, for your own reference and for anticipating judge questions — not all of it needs to go on slides.

---

# PART A — Content mapped to the 6 required slides

## Slide 1 — Title Page

| Field | Value |
|---|---|
| Problem Statement ID | Self-identified (not from an official released list) — leave blank or write "Self-Identified" |
| Problem Statement Title | Talus — Risk-Aware Decision Support for Open-Pit Mine Safety |
| Theme | Disaster Management |
| PS Category | Software |
| Team ID | *(fill in)* |
| Team Name | *(fill in)* |

---

## Slide 2 — Idea Title

**Proposed Solution (one line):**
Talus continuously assesses rockfall risk across mine zones, explains *why* risk is rising, tracks how fast it's escalating, and recommends safer routes and role-specific actions before conditions become critical — moving beyond prediction into decision support.

**Detailed explanation of the proposed solution:**
Open-cast and underground mines currently assess rockfall risk manually, using data — rainfall, slope angle, crack presence, blasting activity, vibration, prior incidents — that is scattered across systems and rarely combined in real time. Talus fuses these signals into a live, zone-wise risk score (0–100) with a stated confidence level, explains the score's contributing factors using SHAP, tracks whether risk is rising and how fast, recommends role-specific alerts (worker / safety officer / manager / rescue team each get a different message from the same event), and computes risk-aware safe routes between points on the mine map instead of simple shortest-path routing. A what-if simulator lets a safety officer test how changing conditions (e.g. rainfall increasing) would shift risk, live.

**How it addresses the problem:**
It replaces scattered, manual, reactive risk assessment with a single continuously-updated system that a safety officer can act on immediately — not just "here's a number" but "here's why, here's how fast it's changing, here's what each person should do, and here's the safest way to move right now."

**Innovation and uniqueness of the solution:**
A near-identical government problem statement already exists — **SIH25071, "AI-Based Rockfall Prediction and Alert System for Open-Pit Mines" (Ministry of Mines)** — and we say so directly rather than pretending otherwise. SIH25071's scope is *Detection → Alert*. Talus's scope is *Detection → Understanding (explainability) → Escalation tracking → Decision (role-based alerts + safe routing) → What-if analysis*. We are not claiming a better prediction model — we are claiming a more complete decision-support product built around the same underlying risk problem. Every risk score also carries a stated confidence and lists missing evidence, rather than presenting a bare number as certain — a detail most "AI predicts X" pitches omit entirely.

---

## Slide 3 — Technical Approach

**Technologies to be used:**
- Frontend: React, Leaflet (interactive zone-wise risk map)
- Backend: Python, Flask/FastAPI
- ML: Scikit-learn (Random Forest for risk scoring), SHAP (explainability)
- Computer Vision: Crack-detection model producing structured features (length, density, orientation) — not a direct severity judgment from a single image
- Routing: Risk-weighted Dijkstra (cost = distance + risk penalty)
- Data: Historical/public sources supplemented with synthetic data reflecting patterns from published rockfall research (see Part B)

**Methodology / process:**
```
                        MINE DATA
                              │
      ┌───────────────────────┼───────────────────────┐
      ▼                       ▼                       ▼
 Environmental            Geological               Visual
 (rainfall, vibration)    (slope, rock type)      (crack imagery)
      │                       │                       │
      └───────────────────────┼───────────────────────┘
                              ▼
                        RISK ENGINE
                  (risk score + confidence)
                              │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Risk Score         SHAP             Trend
      (with confidence)  Explanation      (escalation
                                            detection)
              │                │                │
              └────────────────┼────────────────┘
                              ▼
                      DECISION ENGINE
                              │
      ┌───────────────────────┼───────────────────────┐
      ▼                       ▼                       ▼
  Role-based              Risk-aware              What-if
   Alerts                  Routing               Simulator
      │                       │                       │
      └───────────────────────┼───────────────────────┘
                              ▼
                       MINE DASHBOARD
```

**Build tiers (internal — for planning, not necessarily a slide):**
- **Tier 1 (must work):** Risk engine, zone-wise GIS map, SHAP explainability, role-based alerts, risk-aware routing.
- **Tier 2 (strong differentiators, if time allows):** Crack detection, trend/escalation detection, what-if simulator, Risk Evidence Timeline (a log of how a zone's risk accumulated over time — e.g. "09:00 risk 41 → rainfall increased → 10:00 risk 48 → crack detected → 11:00 risk 61").
- **Tier 3 (do not attempt):** Live IoT sensors, drone integration, 3D digital twin, autonomous evacuation, real-time video CV, per-role mobile apps.

---

## Slide 4 — Feasibility and Viability

**Feasibility analysis:**

| Component | Feasibility |
|---|---|
| Random Forest risk scoring | High — standard, well within scope |
| SHAP explainability | High — well-documented library |
| Leaflet risk map + dashboard | High |
| Risk-aware Dijkstra routing | High — standard graph algorithm |
| CV crack detection | Medium — real mine-specific data doesn't exist; approximate model achievable |
| Live demo reliability | High — fully software, no hardware/mobile dependency to fail on stage |
| Full production deployment | Not attempted — explicitly out of scope for the prototype |

**Potential challenges and risks:**
- No public dataset of real Indian mine rockfall sensor data (rainfall/vibration/crack logs) exists — the prototype will run on synthetic data reflecting patterns from published research, not real mine telemetry.
- Crack-detection accuracy will be limited by relying on general-purpose crack datasets rather than mine-specific ones.
- The risk score's 0–100 thresholds are prototype operational thresholds, not calibrated safety standards.
- Because this closely maps to an existing official PS (SIH25071), the core prediction concept alone isn't novel — the differentiation must come from the decision-support layer, and needs to be stated clearly, not discovered by a judge.

**Strategies for overcoming these challenges:**
- State the synthetic-data approach transparently rather than implying real deployment data: *"the prototype validates the architecture using historical, public, and simulated data — real deployment would require a sensor-data partnership with a mining operator."*
- Report every risk score with a confidence value and a list of missing evidence, rather than presenting a bare number.
- Frame the CV output as structured features (crack length/density/orientation) feeding the risk model, not a standalone severity judgment.
- Lead the pitch with the Detection → Understanding → Decision → Action → Safety framing and name SIH25071 explicitly as related prior work being built past — on our terms, not a judge's.

---

## Slide 5 — Impact and Benefits

**Potential impact on the target audience:**
- Mine safety officers get a single, continuously updated, explainable view of rockfall risk instead of manually cross-referencing scattered data sources.
- Workers receive clear, role-specific, actionable guidance (e.g. "avoid Route 3") instead of generic alarms.
- Rescue teams get a recommended safe approach route during an active incident.
- Mine managers get visibility into how many workers are in an at-risk zone, supporting faster evacuation decisions.

**Benefits (social, economic, environmental):**
- **Social:** Directly targets worker safety in an industry with a real, documented fatality risk from rockfalls.
- **Economic:** Reduces operational losses from reactive, delayed risk response; supports better-informed continue/halt-operations decisions per zone rather than blanket shutdowns.
- **Environmental / operational:** Encourages proactive slope monitoring and inspection prioritization based on live risk trend rather than fixed schedules.

---

## Slide 6 — Research and References

*(Full annotated list with context in Part B — condensed for the slide below.)*

- Ministry of Mines, SIH25071 — "AI-Based Rockfall Prediction and Alert System for Open-Pit Mines" (related prior problem statement) — https://prezi.com/p/quiaxpdaqkn9/ai-based-rockfall-prediction-and-alert-system-for-open-pit-mines/
- "AI-Based Rockfall Prediction and Alert System for Open–Pit Mines," IEEE Conference Publication (CNN-LSTM ensemble, multi-source data fusion) — https://ieeexplore.ieee.org/abstract/document/11452992/
- "Prediction of rockfall hazard in open pit mines using a regression based machine learning model" — https://www.researchgate.net/publication/379730899
- "Application of Artificial Intelligence in Predicting Coal Mine Disaster Risks: A Review" — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12608180/
- "Rock mass classification prediction model using heuristic algorithms and support vector machines" — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8766606/
- Two-stage landslide early-warning system with tiered risk levels (blue/yellow/red), Dagushan open-pit mine case study — https://link.springer.com/article/10.1007/s10064-021-02461-6
- Directorate General of Mines Safety (DGMS), Government of India — regulatory context — https://www.dgms.gov.in/
- SIH 2026 official themes — https://sih.gov.in/SIH_Themes

---

# PART B — Deeper reference material (for your own use, Q&A prep, and anticipating judge questions)

## B1. Why each citation matters, not just that it exists

- **SIH25071 (Ministry of Mines):** This is the reason we must not present prediction itself as novel. It's the anchor for our entire "we go further" argument — the whole pitch's credibility depends on us naming this ourselves rather than a judge finding it first.
- **IEEE CNN-LSTM paper:** Shows the state-of-the-art approach is heavier than ours (drone imagery, micro-seismic data, edge-AI deployment). Useful for an honest answer if asked "why not use their approach" — because our contribution isn't a better model, it's the decision layer around a model.
- **ResearchGate regression ML paper:** Shows that even simple ML models (not deep learning) are an accepted, published approach to rockfall energy prediction — supports using Random Forest without needing to justify a heavier architecture.
- **PMC AI coal-disaster review:** Broader context — shows AI-for-mine-safety is an active, recognized research area beyond just rockfalls, useful if asked about the wider landscape.
- **Rock mass classification SVM paper:** Supports the geological-feature side of the risk model (rock type, slope, structural classification) if asked what determines baseline risk beyond weather/blasting.
- **Landslide early-warning tiered system paper (blue/yellow/red):** Directly supports our risk-band design (Very Low/Low/Moderate/High/Critical) and the idea of a two-stage, multi-factor early-warning system — cite this specifically if asked "is a tiered risk-band approach a real methodology or did you invent it."
- **DGMS:** The actual regulatory body governing Indian mine safety (Mines Act 1952, Coal Mines Regulations 2017, etc.). Useful for the impact/benefits slide and for grounding role-based alerts in a real institutional structure — even a loose mapping to DGMS categories reads as more credible than an abstract "workers get alerts."

## B2. The novelty question — full answer, for Q&A

**If asked "isn't this just SIH25071 with extra features":**
"SIH25071 asks how to predict a rockfall and alert someone. We're answering a different, later question: once you know risk is elevated, how does a mine actually respond — who gets told what, how do you know if it's getting worse, how do people move safely, and what happens under different conditions. Prediction is the input to our system, not the product. The product is the decision layer."

**If asked "how is your risk score different from a black-box prediction":**
"Every score we produce carries a confidence value and lists what evidence is missing — for example, 'Risk 82, Confidence 76%, vibration data unavailable.' We treat missing data as something to surface, not hide."

**If asked "where does your risk score actually come from, mathematically":**
"Features feed a model estimating probability of elevated risk within a defined time window; that probability is converted to an operational risk band (Very Low through Critical). These are prototype thresholds, not calibrated safety standards — calibrating them for real use would require historical incident data we don't have access to."

**If asked "is your data real":**
"No — real mine sensor and incident data for Indian open-pit mines isn't publicly available. Our prototype uses synthetic and historical-proxy data reflecting patterns described in the published research we cite. The prototype validates the system architecture and decision-support workflow, not a production-calibrated risk model."

## B3. Demo script (for internal rehearsal, not a slide)

1. Risk map — zones colored by score and confidence.
2. Click a high-risk zone → SHAP breakdown + Risk Evidence Timeline showing how it got there.
3. What-if simulator — raise rainfall/blasting live, watch score/confidence/map/SHAP update together.
4. Route request between two points → system routes around the flagged zone; show the cost breakdown (distance vs. risk penalty).
5. Trigger rapid escalation on a zone → show role-based alerts firing side by side (worker vs. safety officer vs. manager, same event, different message).

Optional strengthening: anchor one demo scenario to a real, documented rockfall incident's known conditions (a DGMS accident report or news coverage of a specific mine incident) rather than an entirely abstract scenario — this turns "we made up some numbers" into "we tested against a real case."

## B4. Explicit scope exclusions (say these out loud in the pitch)

No live IoT sensor integration. No drone/satellite feeds. No claim to outperform the published CNN-LSTM research. No implication that synthetic data represents real mine telemetry. No autonomous evacuation logic. Stating these clearly signals scope discipline rather than reading as a gap.
