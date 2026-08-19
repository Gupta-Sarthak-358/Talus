# Talus Project Brief

**Status:** Frozen (MVP scope) · **Context:** SIH 2026, College Internal Hackathon · **Today's date:** 2026-08-19

This is the **single most important document**. It freezes what Talus actually is. If a proposal conflicts with this brief, this document wins.

---

## Problem

Open-pit mines generate fragmented environmental, geological, operational and visual signals. These signals are difficult to combine into a unified, explainable risk picture.

The current state:

- **Fragmented information** — scattered across systems, rarely combined.
- **Manual risk assessment** — too much manual cross-referencing.
- **Reactive response** — safety actions happen after problems surface, not before.

## Problem Statement

**Risk-Aware Decision Support for Open-Pit Mine Safety**

## Solution

Talus converts scattered mine data into **explainable risk** and **actionable safety decisions**.

Talus produces a zone-level risk score (0–100) with a stated confidence, explains *why* the score is what it is (SHAP), tracks how fast risk is escalating, and converts the result into **role-specific actions**:

- Worker → safe route guidance
- Safety Officer → early risk intervention / escalation
- Mine Manager → operational decisions / evacuation coordination
- Rescue Team → risk-aware response / safe access

It also computes **risk-aware routes** (safety-weighted Dijkstra instead of plain shortest path) and supports **what-if simulation** so a safety officer can test how changed conditions shift risk, live.

## Core Differentiation

From:

> "What is the risk?"

To:

> "What should we do now?"

Context: a related official problem statement — **SIH25071, "AI-Based Rockfall Prediction and Alert System for Open-Pit Mines"** — already covers *detection → alert*. Talus is not a better predictor; Talus is a **complete decision-support layer** built around the same underlying risk question:

- Every risk score carries **confidence** and a **list of missing evidence** — no bare black-box numbers.
- Who gets told what, in what words, and what action follows is part of the product, not an afterthought.

## System Philosophy

```text
Detect → Understand → Escalate → Decide → Act
```

## Core Modules

1. **Data Layer** — environmental, geological, operational, visual, historical inputs.
2. **Feature Processing** — combines raw signals into model-ready features.
3. **Risk Engine** — zone-level risk score + confidence.
4. **Explainability** — SHAP feature contributions.
5. **Trend Detection** — rapidly increasing risk / escalation.
6. **Decision Engine** — role-specific recommendations.
7. **Risk-Aware Routing** — safety-weighted Dijkstra.
8. **Dashboard** — zone-based open-pit mine risk map (React + Leaflet).

## MVP

- Random Forest risk engine
- SHAP explainability
- Confidence + missing-evidence reporting
- Risk trend / escalation detection
- Role-based decisions (4 roles)
- Risk-aware Dijkstra routing
- React + Leaflet dashboard
- FastAPI backend
- Synthetic training data (physics-informed FoS labels)

## Explicitly Out of Scope

- Live IoT / real sensor integration
- Real mine deployment
- Autonomous evacuation
- Drone integration
- Production-grade safety certification
- Mine-specific CV validation
- 3D digital twin
- Real-time video CV
- Per-role mobile apps
- Claiming real Indian mine telemetry (it does not exist publicly)

## Data Honesty (do not remove)

No public Indian mine sensor/incident dataset was identified. Prototype validation therefore uses **public, historical and synthetic data**, informed by referenced research. *The prototype validates the architecture, not a production-calibrated risk model.*

---

*See [ADR-001: One-Week MVP Scope](decisions/ADR-001-mvp-scope.md) for the formal decision record.*