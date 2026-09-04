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
4. **No live sensor integration** in the prototype — adapter fixture only.
5. **Multilingual NER coverage needs community co-design** beyond the pilot
   language matrix.
6. **Offline sync needs field testing** — demonstrated as architecture, not
   proven in deployment.
7. **IMD grid coarseness** (~27 km) misses hyperlocal cloudbursts.
8. **OSM rural gaps** — road/exposure overlays are QA-dependent.
9. **Prototype bands ≠ safety standards.** Operational decisions remain with
   qualified authorities.

## Field reporting — demo honesty (new in this build)

*   Citizen/field reports are **unverified input** — `verified` status requires an officer `PATCH` review (demo role-toggle only; real auth + moderation are post-hackathon). Until verified, a report never promotes to a training `event` or a `previous_landslide` label — it lives in a candidate sidecar with `crowd-verified` + photo SHA256.
*   Photo/video **bytes are never committed** (metadata-only lane per contract §4 + `.gitignore:46`); only `{filename,mime,size_bytes,sha256,exif_lat,exif_lon}` is stored, with an explicit `consent: true` gate. EXIF vs claimed >200m is flagged; unsupported mime is flagged; per-boot rate cap 20 is a demo guard, not production moderation.
*   Offline outbox is `localStorage` + retry + sync badge (no service worker — `6` below). Full PWA + background sync + content moderation are post-hackathon.

## Carryover discipline from v1

- Confidence is calibrated P(elevated susceptibility), never "probability of
  failure."
- ML counterfactuals labeled counterfactual; causal claims via scenario
  engine only.
- Every score ships with missing evidence. A confident-looking number with
  hidden gaps is a bug, not a feature.
