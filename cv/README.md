# cv

Computer vision for Talus: crack detection and feature extraction.

Extracts structured crack features (length, density, orientation) from imagery.
Generic crack datasets (e.g. Ultralytics Crack-Seg) train the detection mechanism;
output feeds the Random Forest risk engine, not a direct severity claim.

See `docs/03_DATA_PLAN.md` and `docs/08_LIMITATIONS.md`.