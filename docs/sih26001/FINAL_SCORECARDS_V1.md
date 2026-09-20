# Final scorecards v1 (frozen)

Generated 2026-09-20T09:11:25Z from frozen artifacts (see `runs/final_scorecards_v1.json` for machine-readable + input hashes). No fitting, no threshold tuning.

## 1. Predictive validity
- Spatial GroupKFold(8): RF 0.9345 / XGB 0.9421 / LGBM 0.9406; isotonic Brier 0.0967.
- Temporal holdout RF 0.8573; hard-negative stress 0.7804.
- Temporal campaign held-out: M0 0.531/0.317 → VI-0 0.468/0.595 → VI-1 0.388/0.615 → VI-2 0.481/0.368 (sat-only 0.500). **Campaign closed 2026-09-18: no validated timing signal.**

## 2. Warning performance (replay evidence)
- Trust ledger 5/6 flagged High+ before event day, median lead 26d (Mangan High Jun-10, Critical Jun-11, red alert Jun-13).
- In-domain analogues flagged optimistic, not hidden.

## 3. Warning burden
- Off-season 0/60 windows any-hot vs monsoon 28/60 (mean 5.8 hot-days).

## 4. Trust / domain
- Championship 23/18 episodes, 0 audit errors; 13-dev/10-heldout with cross-episode split correction.
- 0/10 out-of-regime framing locked; OOD guard shipped; validated vs inference regimes labeled.
- NO_FILL enforced; synthetics never in evidence.

## Championship split (frozen)
- Dev (13): NEWS-17MILE-20220615, NEWS-29MILE-20200923, NEWS-29MILE-20210906, NEWS-APDARA-20200627, NEWS-DARJ-20150701, NEWS-LINGCHOM-20200524, NEWS-MANGAN-20240613, NEWS-MANGANCHUNG-20200627, NEWS-NH10-20150709, NEWS-NH10-20211020, NEWS-NH10-20221009, NEWS-RONGEY-20220628, NEWS-TSONG-20190916
- Held-out (10): NEWS-20MILE-20220901, NEWS-29MILE-20210711, NEWS-BIRIKDARA-20220802, NEWS-DIPUDARA-20240820, NEWS-DIPUDARA-20240821, NEWS-MANTAM-20160813, NEWS-PATHING-20221124, NEWS-PUBUNG-20190708, NEWS-SOKPAY-20230326, NEWS-YUMTHANG-20220831
