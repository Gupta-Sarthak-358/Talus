# Demo Scenario Summary (docs/06_DEMO_SCENARIO.md)

The demo is a **rehearsed test case**, not a live dice roll. Everything runs on
the deterministic synthetic dataset (seed 42 — `data/synthetic/v1/metadata.json`).
Your API must reproduce these exact numbers.

## Scenario: "Zone B Escalation"

Four zones A, B, C, D. Zone B = NW bench (steep, rain-exposed) — the protagonist.

### Initial state (first load of the dashboard)

| Zone | Risk | Band | Confidence | Trend |
|---|---|---|---|---|
| A | 22 | Low | 0.81 | stable |
| B | 48 | Moderate | 0.78 | stable |
| C | 35 | Low | 0.79 | stable |
| D | 28 | Low | 0.80 | stable |

### Event 1 — Rainfall increases (35 → 55 mm 24h)

- B risk rises to **≈ 58–63**
- SHAP: rainfall is top positive contributor
- Other zones barely move

### Event 2 — Crack density increases

- B risk rises to **≈ 68–74**
- SHAP: crack density dominant alongside rainfall
- Confidence may drop if evidence is missing

### Event 3 — Trend crosses threshold

- B flagged **rapidly increasing** → escalation alert fires
- `/trend` returns `"rapid_increase": true`

### Decision — one event, four messages

| Role | Expected message |
|---|---|
| worker | Avoid Zone B — safe route guidance |
| safety_officer | Prioritize inspection of Zone B (monitor → escalate) |
| mine_manager | Identify people at risk; coordinate evacuation of Zone B |
| rescue_team | Standby with a safer approach route to Zone B |

### Routing

- **Shortest route** crosses Zone B (cheap, dangerous)
- **Risk-aware route** avoids Zone B → `"avoided_zones": ["B"]`

### What-if

Rainfall → 80 mm: B risk jumps to **≥ 80** (Critical), map turns red, SHAP rain
contribution grows.

### Final state

| Zone | Risk | Band | Confidence | Trend |
|---|---|---|---|---|
| A | 24 | Low | 0.80 | stable |
| **B** | **85+** | **Critical** | 0.82 | **rapidly increasing** |
| C | 37 | Low | 0.79 | stable |
| D | 30 | Low | 0.80 | stable |

## Your backend checklist for this demo

- [ ] First load reproduces initial state table exactly
- [ ] `/risk/predict` with 55 mm rain → ~58–63
- [ ] `/risk/predict` with crack increase → ~68–74
- [ ] `/trend` flags B once the threshold is crossed
- [ ] `/decision` returns the 4 role messages above
- [ ] `/routes/safe` avoids B; shortest crosses it
- [ ] `/simulation/what-if` with 80 mm → ≥ 80, Critical
- [ ] No network calls — everything local

> If you implement only ONE thing correctly, make it this scenario — it's what
> the judges will see.