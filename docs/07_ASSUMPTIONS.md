# Talus Assumptions

**Status:** Frozen for MVP · Distinction: an *assumption* is "we decided to do X." A *limitation* (see `docs/08_LIMITATIONS.md`) is "because of X, the system cannot claim Y."

---

1. Mine-specific telemetry is **unavailable** for Indian open-pit mines.
2. Synthetic data is used for prototype training and validation.
3. Rainfall distributions are grounded in **IMD** gridded historical data for real mining-region grid cells.
4. Terrain (elevation, slope) can be derived from public DEM sources (**ISRO Bhuvan CartoDEM / SRTM**).
5. Blast frequency and vibration features are literature-derived parameter ranges, not measured logs.
6. Groundwater is represented by a **derived proxy** (rainfall + time-since-last-rain), not real piezometer readings.
7. Generic crack imagery (Crack-Seg) has a **domain gap** to mine rock faces; it trains the detection *mechanism* only.
8. The FoS equation is a simplified infinite-slope approximation — adequate for prototype realism, not site-specific geotechnical analysis.
9. Risk thresholds and risk bands are **prototype thresholds**, not calibrated safety standards.
10. The risk score is **not a certified safety determination**.
11. Final operational decisions remain with qualified personnel — Talus recommends, it does not command.
12. The demo may be anchored to a real documented weather/incident pattern for grounding, but the dataset itself remains synthetic.
13. Implied use of global landslide patterns (NASA COOLR/GLC) is for pattern validation only, not mine-specific evidence.

---

Any change to these assumptions requires updating this document and the affected downstream docs (requirements, data plan, model plan, limitations).