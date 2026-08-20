# Talus Assumptions

**Status:** Frozen for MVP · Distinction: an *assumption* is "we decided to do X." A *limitation* (see `docs/08_LIMITATIONS.md`) is "because of X, the system cannot claim Y."

---

1. Mine-specific telemetry is **unavailable** for Indian open-pit mines.
2. Synthetic data is used for prototype training and validation.
3. Rainfall distributions are grounded in **IMD** gridded historical data for real mining-region grid cells.
4. Terrain (elevation, slope) is derived from a public DEM (**Copernicus GLO-30**, ESA) for regional context; **mine bench geometry is a separate fixed engineering-input layer** (Neyveli: OB 25 m×4+18 m, mineral 6 m @ 75°, overall 45°), tagged by provenance.
5. Blast vibration uses the **Neyveli-fitted attenuation model** (NIRM 2005: `PPV = 858.90·(D/√W)^(−1.58)`); blast frequency is **production-derived** with a wide prior (14–28/wk), not measured explosive logs.
6. Groundwater is represented by a **derived proxy** (rainfall + time-since-last-rain), not real piezometer readings.
7. Generic crack imagery (Crack-Seg) has a **domain gap** to mine rock faces; it trains the detection *mechanism* only.
8. The FoS equation is a simplified infinite-slope approximation — adequate for prototype realism, not site-specific geotechnical analysis.
9. Risk thresholds and risk bands are **prototype thresholds**, not calibrated safety standards.
10. The risk score is **not a certified safety determination**.
11. Final operational decisions remain with qualified personnel — Talus recommends, it does not command.
12. The demo may be anchored to a real documented weather/incident pattern for grounding, but the dataset itself remains synthetic.
13. Implied use of global landslide patterns (NASA COOLR/GLC) is for pattern validation only, not mine-specific evidence.
14. Crack state is synthesized from geometry + environment (mechanisms grounded in literature and lignite-mine analogs, e.g. Greece). Crack depth is **bench-bounded** (≤ ⅓–½ slope height) and severity is a ranked decision surface, **≠ width alone**.

---

Any change to these assumptions requires updating this document and the affected downstream docs (requirements, data plan, model plan, limitations).