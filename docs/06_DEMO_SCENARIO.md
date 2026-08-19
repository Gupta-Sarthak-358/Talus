# Talus Demo Scenario

**Status:** Frozen for MVP · Purpose: define a **known expected output** so the demo is a rehearsed test case, not a live dice roll.

The demo runs on the deterministic synthetic dataset (fixed seed — see `data/synthetic/v1/metadata.json`). Every number below is the expected output the team should be able to reproduce.

---

## Scenario: "Zone B Escalation"

### Mine Layout

Four zones on an open-pit bench map: **A, B, C, D** with roads connecting them. Zone B is a NW bench (steep, rain-exposed) — the scenario's protagonist.

### Initial State

| Zone | Risk | Band | Confidence | Trend |
|---|---|---|---|---|
| A | 22 | Low | 0.81 | stable |
| B | 48 | Moderate | 0.78 | stable |
| C | 35 | Low | 0.79 | stable |
| D | 28 | Low | 0.80 | stable |

---

### Event 1 — Rainfall increases

Rainfall in the 24h window rises (e.g. from 35 mm to 55 mm).

**Expected:**
- Zone B risk increases (target ≈ 48 → 58–63).
- SHAP shows rainfall as the top positive contributor.
- Other zones rise slightly or stay stable.

### Event 2 — Crack density increases

A new crack measurement is ingested; Zone B crack density increases.

**Expected:**
- Zone B risk increases further (target ≈ 58 → 68–74).
- SHAP shows crack density as a dominant contributor alongside rainfall.
- Confidence drops if the new reading is low-confidence or a feature goes missing.

### Event 3 — Trend crosses to rapidly increasing

Zone B trend flag becomes **rapidly increasing**.

**Expected:**
- **Escalation alert** fires for Zone B.
- Trend endpoint reports `"rapid_increase": true`.

---

### Decision — role-specific outputs (same event, different message)

| Role | Expected message |
|---|---|
| Worker | Avoid Zone B — safe route guidance. |
| Safety Officer | Prioritize inspection of Zone B (monitor → escalate). |
| Mine Manager | Identify people at risk; coordinate evacuation of Zone B. |
| Rescue Team | Standby with a safer approach route to Zone B. |

### Routing

- **Shortest route** between two points crosses Zone B.
- **Risk-aware route** avoids Zone B (longer but safer), with `avoided_zones: ["B"]`.

### What-if

Increase rainfall to extreme (e.g. 80 mm) via the WhatIf panel.

**Expected:**
- Zone B risk jumps further (target ≥ 80).
- Map color changes to red.
- SHAP rain contribution grows.

---

### Final State

| Zone | Risk | Band | Confidence | Trend |
|---|---|---|---|---|
| A | 24 | Low | 0.80 | stable |
| **B** | **85+** | **Critical** | 0.82 | **rapidly increasing** |
| C | 37 | Low | 0.79 | stable |
| D | 30 | Low | 0.80 | stable |

---

## Demo Rehearsal Checklist

- [ ] Seeds/versions pinned in `data/synthetic/v1/metadata.json`.
- [ ] Zone B initial state reproduced on first load.
- [ ] Event 1 → risk increases; SHAP rainfall positive.
- [ ] Event 2 → risk increases; SHAP crack positive.
- [ ] Event 3 → escalation alert fires.
- [ ] Four role messages render side by side.
- [ ] Risk-aware route avoids Zone B; shortest route crosses it.
- [ ] What-if pushes Zone B to Critical.
- [ ] No network calls; everything local.

---

*Optional strengthening: anchor the rainfall/geometry conditions to a real documented slope-failure weather event so the scenario is grounded, not abstract.*