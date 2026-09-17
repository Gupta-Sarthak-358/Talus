# VI-2P Feasibility: physics-transfer survey (2026-09-18, no fitting, no borrowing)

Question: does an openly available pretrained physics-informed landslide model exist
whose weights/structure transfer to TALUS rainfall-triggered 7-day forecasting?

## Candidates

| Candidate | Physics | Input | Output | Weights | Code | License | Transferable? |
|---|---|---|---|---|---|---|---|
| Dahal & Lombardo PINN (EngGeo 2024) | Newmark permanent deformation (coseismic) | terrain proxies + ground motion | susceptibility + geotechnical latents | none published (notebooks train fresh) | yes, github.com/ashokdahal/PINN | CC0-1.0 | NO — seismic trigger, susceptibility task; architecture idea only |
| Cao/Gong TL-PINN (2026, cacaie + Geo-Extreme) | Iverson/Richards 1D infiltration | rain + soil params + pressure-head sensors | FS / failure timing / diffusivity | none published | not found (DeepXDE/TF per paper) | n/a | NO — no artifact; inverse mode needs piezometers TALUS lacks (MISSING) |
| Tong et al. CNN-LSTM-TL surrogate (2026) | FEM Monte Carlo + random fields | soil spatial fields | FoS | none (synthetic-data method) | not found | n/a | NO — needs FEM chain + soil fields we lack |

## Verdict

VI-2P-as-borrowing: NO-GO. No openly available pretrained weights match our
mechanism (rainfall infiltration), scale (regional), and task (forecasting).
What exists is either wrong-mechanism (coseismic), artifact-less (TL-PINN papers),
or needs instrumentation/data we demonstrably lack (piezometers, soil fields).

## Recommended residual (not started)

VI-2P-B: analytical Iverson response as physics feature — no weights needed.
Linearized pore-pressure response R(t*) from archived rainfall with ensemble over
diffusivity D0/depth H ranges (sensitivity, not calibration); infinite-slope FoS
trajectory as an additional evidence branch under the frozen M0/VI evaluation.
Requires its own justification; assumptions must be explicit ranges, not points.
