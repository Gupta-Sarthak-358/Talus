> **ARCHIVED — Mine V1 (SIH25071 open-pit). Active track is SIH26001 NER landslide — see docs/sih26001/. Do not use for new work.**

---

# Talus Limitations

**Status:** Frozen for MVP · Distinction: a *limitation* is the consequence of a choice or of data reality. An *assumption* (see `docs/07_ASSUMPTIONS.md`) is "we decided to do X."

Keep this separate from assumptions. For example:

- **Assumption:** We use synthetic vibration values.
- **Limitation:** The model therefore cannot claim real-world vibration predictive validity.

---

## Limitations

1. **No Indian mine telemetry** — the system has never ingested real mine sensor/incident data.
2. **Synthetic labels** — risk labels come from a physics-informed generator, not observed outcomes; predictive validity is demonstrated architecturally, not empirically.
3. **Domain shift** — models trained on synthetic distributions may not transfer to a real mine without retraining on local data.
4. **Generic crack dataset** — CV detects cracks from roads/walls imagery; **generic crack data ≠ mine-specific severity**.
5. **Simplified mine geometry** — zones and roads are schematic; no full 3D pit model.
6. **No field validation** — no deployment, no real-site calibration.
7. **Prototype thresholds** — bands and escalation thresholds are not calibrated safety standards.
8. **No production safety certification** — not a certified safety-critical system; never to be treated as one.
9. **Single geography baseline** — rainfall grounding uses selected real grid cells; other regions would need their own distributions.
10. **Routing is map-schematic** — route results depend on the drawn road graph, not surveyed haul-road geometry.
11. **Explanation fidelity follows model fidelity** — SHAP explains *the model*, not the physical slope.

---

## What This Means in Practice

- Every risk score carries confidence and missing-evidence so the system never presents a bare number as certain.
- The demo narrative is: **"the prototype validates the architecture using historical, public and simulated data — real deployment requires a sensor-data partnership with a mining operator."**
- Judges asking "is this data real?" get the honest answer: no, and this document explains exactly why that is acceptable for the prototype's purpose.

---

*This transparency is a strength, not a weakness. Do not remove these limitations from the narrative.*