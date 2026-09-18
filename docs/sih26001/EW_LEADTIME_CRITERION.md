# Early-Warning Lead-Time Criterion (FROZEN 2026-09-18, before evaluation)

Question: for a known event, when did TALUS first enter a SUSTAINED elevated state?

## Warning mapping (unchanged from M0)

Very Low/Low → NORMAL, Moderate → WATCH, High → ALERT, Critical → CRITICAL.

## Escalation rule (persistence required)

First snapshot S (of T-30/T-14/T-7/T-3/T-1/T) with warning ≥ LEVEL **and** every
snapshot after S through T also ≥ LEVEL. A lone spike that drops back does not count.

## Lead time

`lead = event_date − date(S)`, snapshot resolution. Persistent WATCH lead and
persistent ALERT lead reported separately. Miss = no qualifying S (lead None).

## Background false escalation (approximation, declared)

Tier-B monsoon (60) + off-season (60) windows: fraction with ≥3 ALERT/CRITICAL-hot
days. Contiguity unmeasured in stored artifacts → conservative upper bound, labeled so.

## Scope

Descriptive analysis of frozen M0 outputs on all 23 events (dev+held-out reported
separately; nothing trains, nothing tunes). Evidence drivers recorded per event
(rain/soil/FoS at escalation) for Q7, descriptively only.
