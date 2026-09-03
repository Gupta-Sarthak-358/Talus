# TALUS v2 Limitations — SIH26001

**Status:** Draft (state proactively — this list is a judging asset, not a
weakness) · **Source:** `docs/SIH26001_RESEARCH.md` §11.3–§11.4

## What we do NOT claim

- We are **not** replacing GSI RLFS — we complement it with AI/ML.
- We are **not** doing real-time InSAR (requires hardware).
- We are **not** deploying IoT sensors (A-LEWS/AmritaWNA's domain).
- We do **not** predict exact landslide locations/times — we predict
  susceptibility.
- We do **not** predict flash floods — rainfall is a landslide-trigger proxy,
  not a hydrological flood model. Road blockages are covered as derived
  road-status, not flood mapping.
- We do **not** claim field-validated production accuracy — this is a prototype.

## Honest limitations (say before asked)

1. **Satellite/reanalysis soil moisture, not in-situ sensors** — resolution
   limits at slope scale (cf. Marino et al. 2020).
2. **Inventory incompleteness** — many events lack precise dates; small slides
   go unreported (community reporting is itself a mitigation we build).
3. **Static model** — conditioning factors don't change; only rainfall + soil
   moisture are dynamic in the prototype.
4. **No real-time sensor integration** in the prototype.
5. **Multilingual NER coverage needs community co-design** beyond the pilot
   language matrix.
6. **Offline sync needs field testing** — demonstrated as architecture, not
   proven in deployment.
7. **IMD grid coarseness** (~27 km) misses hyperlocal cloudbursts.
8. **OSM rural gaps** — road/exposure overlays are QA-dependent.
9. **Prototype bands ≠ safety standards.** Operational decisions remain with
   qualified authorities.

## Carryover discipline from v1

- Confidence is calibrated P(elevated susceptibility), never "probability of
  failure."
- ML counterfactuals labeled counterfactual; causal claims via scenario
  engine only.
- Every score ships with missing evidence. A confident-looking number with
  hidden gaps is a bug, not a feature.
