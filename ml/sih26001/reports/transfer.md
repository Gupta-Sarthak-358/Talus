# Leave-one-state-out transfer (train-SK/test-WB and reverse, RF500+LR, seed 42)

Hardest honest test: different inventory, terrain, monsoon exposure per side.
Reference: pooled GroupKFold-8 OOF RF 0.9308 / LR 0.8945.

| direction | train n | test n | RF AUC | RF Brier | LR AUC | LR Brier |
|---|---|---|---|---|---|---|
| train-SK_test-WB | 2019 | 917 | 0.7097 | 0.2986 | 0.7276 | 0.2096 |
| train-WB_test-SK | 917 | 2019 | 0.9108 | 0.1632 | 0.9112 | 0.1166 |
