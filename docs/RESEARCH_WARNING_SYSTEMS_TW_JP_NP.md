# Operational landslide warning systems: Taiwan, Japan, Nepal — lessons for TALUS

Source: team research synthesis (Sept 2026). Positioning conclusion:

> **TALUS should not try to invent a completely new warning system. It should combine
> the strongest ideas these systems already use, then add the specific intelligence
> layer we are developing.**

Studied systems: **Taiwan** (closest overall analogue — terrain, rainfall, landslides,
road exposure, disaster-management needs), **Japan** (mature operational benchmark),
**Nepal** (closest regional Himalayan analogue + community/last-mile reality check).

References: Taiwan ARDSWC debris-flow network (https://246.ardswc.gov.tw/EN),
JMA soil-water index + Dosha Kiki-Kuru risk map, MLIT disaster portal + road
 intelligence, Nepal DHM + ICIMOD/SERVIR community EWS work. Full link set in chat
archive; key claims re-verified against primary pages before judging.

## 1. What to steal from Taiwan

- **Static hazard + dynamic trigger, explicitly separated.** Long-term potential
  (slopes, sediment, terrain, historical areas) vs short-term trigger (rainfall,
  intensity, accumulation, monitoring). Validates the TALUS static+dynamic architecture.
- **Location-specific warning thresholds.** Effective accumulated rainfall + intensity
  per warning zone/gauge, routinely updated after events, quakes, environmental change.
  Lesson: never one NER-wide rainfall threshold. (Implementation note: FROZEN_BANDS stay
  for scoring per scaffold contract; zone-specific *warning logic* is built on top.)
- **Earthquake-conditioned thresholds.** Post-quake threshold reductions, raised again
  after recovery evidence. Operational precedent for our seismic-memory conditioning
  feature (framed as conditioning, never as "the quake caused this slide").
- **Two monitoring families.** Non-contact pre-event warning (rainfall: earlier, less
  certain) + contact event-triggered monitoring (wire sensors, geophones: later, more
  certain). Supports TALUS multi-lane evidence (rainfall / satellite / field), not one oracle.
- **BigGIS integration** (satellite + aerial + UAV + government layers + event data +
  historical change in one GIS). Our wound-map direction (recent anthropogenic
  disturbance as a time-varying evidence layer) aligns with serious operational
  architecture — as an explicit model feature, not just distance-to-road.
- **Historical imagery as operational knowledge** (97,500+ images by event/time/location).
  Precedent for the TALUS temporal replay / event-history evidence layer.
- **Consequence-aware warning** (protected households, affected locations, road/railway
  risk, evacuation info). Supports hazard ≠ risk: hazard + runout + exposure =
  operational priority.
- **Action-oriented messages.** Yellow = prepare for evacuation; Red = evacuate per
  local government; warning pages carry what/why/actions/rainfall/shelters/phones +
  cell broadcast. Validates: prediction is not the output, action is.

## 2. What to steal from Japan

- **Soil-water memory (tank model).** Current + previous rainfall → stored soil water →
  warning decisions. Direct validation of the TALUS soil lane and antecedent-wetness
  features.
- **Risk map + near-future trajectory.** 1 km grid, 10-min updates, observed + forecast
  rainfall → five risk levels. TALUS should show current risk + where it is heading
  (forecast clearly labeled, never mixed with observed).
- **Observed vs forecast, explicitly separated.** Architecture: past (observed) | now
  (observed+forecast) | future (forecast) → risk trajectory. Reinforces the replay
  causality rule: history screens never use future information.
- **Road operational intelligence as first-class.** Pre-emptive restriction sections
  (segments restricted before disasters on historical evidence), emergency routes,
  closures, passable routes, live cameras. Directly relevant to SIH26001 road
  connectivity: hazard → road exposure → road importance → connectivity consequence.
- **Excavated-slope monitoring precedent** (GPS on expressway cut slopes with ops-room
  display + emergency messaging). Human-modified slopes + roads + monitoring is an
  established concept; TALUS proposes the remote-sensing implementation for unmonitored
  terrain. Wording: "simplified angle-of-reach screening approximation," never a
  debris-flow simulator claim.
- **Satellite role discipline.** Before event → susceptibility/change evidence; during →
  monitoring where available; after → rapid damage assessment (MLIT demo targets ~2.5h
  post-imaging). No magical real-time landslide sensor claims.

## 3. What to steal from Nepal

- **Low-cost monitoring** (no ₹10-lakh-per-hillside designs).
- **Community participation** — field observations as evidence (our Reports lane).
- **Low-network operation** — offline-first is a requirement, not a feature.
- **Local-government workflow** — build for officers, not scientists.
- **Human-readable warnings** — a village officer doesn't read SHAP values.
- Cell broadcast stays honestly FUTURE (no telecom integration exists to claim).

## 4. Locked TALUS architecture (backed by operational precedent, not imagination)

STATIC STATE (DEM/slope, geology, land cover, historical slides, roads, exposure) +
LIVE STATE (rainfall, soil moisture, forecast, satellite change, field reports, seismic)
→ HAZARD INTELLIGENCE (susceptibility + trigger + change) → CALIBRATED HAZARD →
RUNOUT/EXPOSURE → OPERATIONAL RISK → warning / routing / prioritisation → ACTION
(dashboard + mobile/field) → FIELD FEEDBACK → model/map update.

## 5. Warning State Machine (next build after map fix + cleanup)

NORMAL → WATCH → ALERT → CRITICAL → EVACUATE/RESTRICT/RESPOND, each transition with a
stated reason (rainfall accumulation, soil wetness, fresh disturbance, exposure
intersection, forecast exceedance, connectivity threat).

## 6. Positioning (judge-safe wording)

- Core: "TALUS is a physics-informed, evidence-driven landslide risk intelligence
  system that combines terrain susceptibility, evolving conditions, anthropogenic
  disturbance, infrastructure exposure and field evidence to convert hazard forecasts
  into operational decisions."
- Memorable: "Don't just ask where the mountain may fail. Ask what changed, who is
  exposed, and what should happen next."
- Wound hook: "We don't just map the mountain. We map where people are changing it."
- Never claim: "nobody models roads" (Taiwan/Japan disprove it) or "nobody does
  earthquake memory" (Taiwan disproves it). Use: "recent anthropogenic disturbance as
  a time-varying evidence layer" and "seismic history as a persistent conditioning factor."
- Product as four questions: When (replay: how early did TALUS know?) · Why (wound +
  drivers: what changed?) · Who (runout + exposure: who gets hit?) · Trust (lead-time
  + trust ledger: does the warning deserve action?)

## 7. Capability comparison (honest status at time of writing)

| Capability | Taiwan | Japan | Nepal | TALUS |
|---|---|---|---|---|
| Terrain susceptibility | Yes | Yes | Yes | Yes |
| Historical landslides | Yes | Yes | Yes | Yes |
| Rainfall triggering | Yes | Yes | Yes | Yes |
| Antecedent rainfall | Yes | Strong | Yes | Yes |
| Soil-water state | Yes | Strong | Limited | Yes (v09.2 upgrade) |
| Local thresholds | Strong | Strong | Regional | Warning-logic layer (bands frozen) |
| Earthquake conditioning | Explicit | Yes | Relevant | Planned (verified USGS feed) |
| Satellite monitoring | Strong | Strong | Growing | Yes |
| Historical imagery/replay | Strong | Strong | Limited | Yes (replay bundle) |
| Road risk | Strong | Strong | Important | Yes |
| Road closure status | Yes | Strong | Important | Planned |
| Exposure / runout | Yes | Yes | Yes | Planned |
| Field monitoring | Strong | Strong | Cost-sensitive | Yes (Reports lane) |
| Community warning | Strong | Strong | Strong | Planned (multilingual+offline exist) |
| Cell broadcast | Yes | Yes | Limited | Future (honest) |
| Offline/low-network | Relevant | Relevant | Critical | Yes |
| AI/ML | Increasing | Increasing | Growing | Core |
| Explainability | Not central | Not central | Limited | Core |

Benchmark before SIH freeze: feature-by-feature vs Taiwan ARDSWC, Japan JMA/MLIT,
Nepal DHM/ICIMOD.
