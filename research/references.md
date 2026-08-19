# Talus Research References

Research index. Full source URLs live in `research/sources.md` — cite from there, don't scatter URLs across the docs.

---

## 1. Dharshini et al. 2025

G. Dharshini, D. Deepika, C. P., "AI-Based Rockfall Prediction and Alert System for Open-Pit Mines," in *2025 1st Int. Conf. Advancement in Futuristic Technologies (ICAFT)*, 2025.
DOI: 10.1109/ICAFT66710.2025.11452992

**Relevance:** Related rockfall prediction architecture (CNN-LSTM, multi-source fusion).
**What Talus takes:** Context for what "the state of the art" looks like and why Talus adds a decision layer rather than a heavier model.

## 2. Senanayake et al. 2024

I. P. Senanayake, P. Hartmann, A. Giacomini, J. Huang, K. Thoeni, "Prediction of rockfall hazard in open pit mines using a regression-based machine learning model," *Int. J. Rock Mech. Mining Sci.*, vol. 177, p. 105727, 2024.
DOI: 10.1016/j.ijrmms.2024.105727

**Relevance:** Supports **ML-based hazard modeling** — evidence that a regression/tabular ML approach to rockfall-related hazard is published and accepted.
**Not used as:** Evidence that Random Forest is universally best, nor as mine-specific training data.

## 3. Liu et al. 2021

F. Liu, Z. Yang, W. Deng, T. Yang, J. Zhou, Q. Yu, Y. Mao, "Rock landslide early warning system combining slope stability analysis, two-stage monitoring, and case-based reasoning: A case study," *Bull. Eng. Geol. Environ.*, vol. 80, no. 11, pp. 8433–8451, 2021.
DOI: 10.1007/s10064-021-02461-6

**Relevance:** Supports the **monitoring → warning → decision** workflow and the tiered risk-band methodology (blue/yellow/red) that Talus's Very Low→Critical bands build on.

## 4. DGMS (Directorate General of Mines Safety)

"The Coal Mines Regulations, 2017," Government of India.

**Relevance:** Regulatory context; institutional grounding for role-based alerts and slope-monitoring practice.

## 5. IMD (India Meteorological Department)

"Gridded Rainfall Data" (0.25° × 0.25°, daily, 1901–2024).

**Relevance:** Environmental input — grounds the synthetic rainfall distribution for real mining-region grid cells.

## 6. ISRO / Bhuvan / NDEM

ISRO, "Bhuvan / National Database for Emergency Management (NDEM)."

**Relevance:** Geospatial / terrain data — CartoDEM for slope angle/height derivation.

## 7. SIH 2026 (College Internal Hackathon)

Smart India Hackathon, "SIH 2026 Themes."

**Relevance:** Internal hackathon context for Team Sangyan.

## 8. SIH25071 (related prior problem statement)

Ministry of Mines, "AI-Based Rockfall Prediction and Alert System for Open-Pit Mines" — Smart India Hackathon problem statement SIH25071.

**Relevance:** Motivation for Talus's differentiation. SIH25071 covers detection → alert; Talus covers detection → understanding → escalation → decision → action. **Not** the current problem ID unless independently confirmed.

---

## Supporting sources (not cited on the deck)

- NASA COOLR / Global Landslide Catalog (landslides.nasa.gov) — event validation.
- ScienceDirect slope-unit susceptibility benchmark (7,360 units) — synthetic-data sanity check.
- Ultralytics Crack-Seg dataset — CV detection mechanism.
- Landslide4Sense — satellite-based extension, noted only.

---

*Data disclaimer (keep everywhere):* No public Indian mine sensor/incident dataset was identified. Prototype validation uses public, historical and synthetic data informed by the referenced research.