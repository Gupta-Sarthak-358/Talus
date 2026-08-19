# ADR-001: One-Week MVP Scope

**Status:** Accepted · **Date:** 2026-08-19 · **Trace to:** `docs/00_PROJECT_BRIEF.md`

## Context

The Talus team has approximately one week and six developers. The goal is to demonstrate the complete decision-support workflow — not to build a production system or to replicate prior prediction-only systems.

## Decision

Build a **vertical-slice prototype** rather than a production system.

## Core (in scope)

- Random Forest risk engine
- SHAP explainability
- Confidence + missing-evidence reporting
- Risk trend / escalation detection
- Role-based decisions (worker / safety officer / manager / rescue team)
- Risk-aware Dijkstra routing
- React + Leaflet dashboard
- FastAPI backend
- Synthetic data (physics-informed FoS labels)

## Deferred (explicitly out of MVP)

- Live IoT / real mine telemetry
- Drone feeds
- Production CV
- Autonomous decisions / evacuation
- Mobile application
- 3D digital twin
- Real-time video CV
- Production-grade safety certification

## Reason

The team has approximately **one week** and **six developers**. The goal is to demonstrate the **complete decision-support workflow** end-to-end. Anything not required to show "Detect → Understand → Escalate → Decide → Act" is deferred.

## Consequence

Feature proposals that expand scope must be added here (as "In scope") rather than debated in chat. Proposals that conflict with the Deferred list are rejected by default.

---

## Change Log

- 2026-08-19 — ADR-001 created (MVP frozen).