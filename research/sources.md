# Talus Data Sources Index

Single place for source URLs. Code and docs say "see `research/sources.md`" instead of scattering links.

| Source | URL | Purpose |
|---|---|---|
| IMD gridded rainfall | https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html | Rainfall distribution for synthetic generation |
| ISRO Bhuvan CartoDEM | https://bhuvan-app3.nrsc.gov.in/data/ | DEM → slope angle/height (candidate; not used) |
| NASA/USGS SRTM | https://www.opendem.info/download_srtm.html | Global DEM fallback (candidate; not used) |
| **Copernicus GLO-30 DEM (USED)** | https://portal.opentopography.org/datasets · `Copernicus_DSM_GLO30_N11_E079` via AWS open data | DEM → elevation/slope (regional context; bench geometry from engineering inputs) |
| Ultralytics Crack-Seg | https://docs.ultralytics.com/datasets/segment/crack-seg | CV crack detection mechanism |
| NASA COOLR / GLC | https://landslides.nasa.gov | Global event validation |
| Susceptibility benchmark | https://www.sciencedirect.com/science/article/pii/S0012825224002551 | Sanity-check synthetic distributions |
| Landslide4Sense | https://github.com/iarai/Landslide4Sense-2022 | (Noted) satellite-based extension |
| DGMS | https://www.dgms.gov.in/ | Regulatory context |
| SIH 2026 themes | https://sih.gov.in/SIH_Themes | Hackathon context |
| SIH25071 (related PS) | https://prezi.com/p/quiaxpdaqkn9/ai-based-rockfall-prediction-and-alert-system-for-open-pit-mines/ | Related prior problem statement |
| Senegal/rockfall ML paper (details) | https://www.researchgate.net/publication/379730899 | Rockfall hazard ML approach context |

---

## Neyveli reference-mine sources

Anchor: **Neyveli Mine-II, NLC India Limited** (open-cast lignite, Tamil Nadu). See `docs/decisions/ADR-002-neyveli-reference-mine.md` and `data/grounding_manifest.md`.

| Source | URL | Purpose |
|---|---|---|
| Wikipedia — NLC India Limited | https://en.wikipedia.org/wiki/NLC_India_Limited | Company / open-cast context |
| Wikipedia — Hutti Gold Mines (rejected anchor) | https://en.wikipedia.org/wiki/Hutti_Gold_Mines_Limited | Why Neyveli, not Hutti |
| Green Tribunal — 8th EAC (Coal) minutes: Mine-II extent 11°27′N–11°32′N, 79°27′E–79°35′E | https://www.greentribunal.gov.in/sites/default/files/news_updates/12_1.pdf | Anchor coordinates |
| Green Tribunal — Neyveli mine-industrial complex, ~1369 mm avg precipitation, aquifer discussion | https://www.greentribunal.gov.in/sites/default/files/news_updates/OA%20107%20of%202023%20Rejointer%20filed%20by%20R11.pdf | Rainfall + groundwater proxy grounding |
| USGS — Ground-water control in the Neyveli lignite field | https://www.usgs.gov/publications/ground-water-control-neyveli-lignite-field-south-arcot-district-madras-state-india | Hydrogeology / groundwater proxy |
| Ministry of Coal — Neyveli open-cast lignite, ~1200 mm annual rainfall, water management | https://coal.nic.in/sites/default/files/2026-03/90326_pib.pdf | Rainfall + operational context |
| Environment Clearance — 8th EAC minutes, Mine-II (15 MTPA, complexity) | https://environmentclearance.nic.in/writereaddata/Form-1A/Minutes/22022021A489I75KFinalMoMof8thEACApproved.pdf | Operational complexity evidence |
| Environment Clearance — Mine-II project detail (~7,194 ha, BWE/conveyor, 5.2:1 stripping) | https://environmentclearance.nic.in/writereaddata/Form_345678/Form_4/511912421217Y64F8PFRR.pdf | Mine geometry / scale grounding |
| Environment Clearance — groundwater depressurisation as part of safe mining | https://environmentclearance.nic.in/writereaddata/Online/EDS/0_0_23_Jun_2015_1608117501Comb_ReplytoMoEF_Mine-I_23-6-2015.pdf | Groundwater → risk chain |

---

## Related research resources

- [Talus Master Project Document](../docs/source/Talus_Master_Project_Document.md) — full annotated reference notes (Part B).
- [Talus Data & Training Plan](../docs/source/Talus_Data_Training_Plan.md) — source-by-source research detail.
- [Talus Data Plan](../docs/03_DATA_PLAN.md) — provenance table.
- [Talus References](../research/references.md) — what each source is for.

---

*Copyright note: papers stay referenced (DOI/URL); only freely redistributable materials are committed in-repo.*