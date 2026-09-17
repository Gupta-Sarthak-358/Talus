# SIH26001 ablation study (same protocol as train: KMeans-8 groups, GroupKFold OOF, RF500+LR, seed 42)

Baseline `full`: RF AUC 0.934 / Brier 0.1166; LR AUC 0.8914 / Brier 0.1274. Deltas below are RF-AUC vs full.

| config | RF AUC (Δ) | RF Brier | LR AUC (Δ) | LR Brier | n_feat |
|---|---|---|---|---|---|
| full | 0.934 (+0.0000) | 0.1166 | 0.8914 (+0.0000) | 0.1274 | 22 |
| no_rain | 0.9189 (-0.0151) | 0.1218 | 0.8946 (+0.0032) | 0.1241 | 19 |
| no_dem6 | 0.9307 (-0.0033) | 0.1215 | 0.8519 (-0.0395) | 0.1482 | 16 |
| no_soil | 0.9319 (-0.0021) | 0.1144 | 0.8937 (+0.0023) | 0.1241 | 21 |
| no_ndvi | 0.9314 (-0.0026) | 0.1214 | 0.8826 (-0.0088) | 0.1304 | 21 |
| no_osm | 0.9244 (-0.0096) | 0.1284 | 0.8742 (-0.0172) | 0.14 | 20 |
| no_seismic | 0.9225 (-0.0115) | 0.1192 | 0.8897 (-0.0017) | 0.1245 | 19 |
| no_drain | 0.9338 (-0.0002) | 0.1172 | 0.8919 (+0.0005) | 0.1269 | 21 |
| no_lulc | 0.9316 (-0.0024) | 0.1186 | 0.8886 (-0.0028) | 0.1291 | 17 |
| static_only | 0.9038 (-0.0302) | 0.1276 | 0.8877 (-0.0037) | 0.1254 | 17 |
| trigger_only | 0.9127 (-0.0213) | 0.144 | 0.6214 (-0.2700) | 0.2262 | 10 |
| loo_elevation | 0.9291 (-0.0049) | 0.1214 | 0.8557 (-0.0357) | 0.1477 | 21 |
| loo_distance_to_road | 0.9228 (-0.0112) | 0.129 | 0.8752 (-0.0162) | 0.1395 | 21 |
| loo_ndvi | 0.9314 (-0.0026) | 0.1214 | 0.8826 (-0.0088) | 0.1304 | 21 |
| loo_rainfall_7d | 0.9313 (-0.0027) | 0.1174 | 0.8923 (+0.0009) | 0.1264 | 21 |
| loo_twi | 0.9333 (-0.0007) | 0.1181 | 0.8913 (-0.0001) | 0.1276 | 21 |
| LEAK_prev_slide | 0.968 (+0.0340) | 0.0813 | 0.9467 (+0.0553) | 0.0948 | 23 |
| NULL_lith_lineament | 0.9336 (-0.0004) | 0.1174 | 0.8914 (+0.0000) | 0.1274 | 22 |
| CAND_aspect_sincos | 0.9322 (-0.0018) | 0.118 | 0.8939 (+0.0025) | 0.1261 | 23 |
| CAND_+twi_x_rain7 | 0.9328 (-0.0012) | 0.1179 | 0.8914 (+0.0000) | 0.1274 | 23 |
| CAND_+slope_x_rain7 | 0.935 (+0.0010) | 0.115 | 0.8913 (-0.0001) | 0.1274 | 23 |

## Reading
- LEAK_prev_slide quantifies why previous_landslide stays excluded (label construction leaks).
- NULL_lith_lineament quantifies the omission cost of the two uniform PROXY constants.
- CAND_* test skipped/improved encodings; adopted only if they beat full honestly.
- static_only vs trigger_only splits the trigger-vs-terrain debate with numbers.
