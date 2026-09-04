"""Lineament density for Gangtok pilot — honest PROXY via Bhuvan 50K documented availability.

Source honesty: ISRO/NRSC Bhuvan advertises Lineament 50K (2005-06) for Sikkim
as an available state in the Mines/Thematic portal (https://bhuvan-app1.nrsc.gov.in/mines/mines.php),
with NRSC description: "Lineament maps were prepared in association with GSI using satellite + collateral
data, limited field work" (NWDP dataset page). WMS endpoint is https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms
(layer lineament:?? per Bhuvan Wiki; exact layer name for Sikkim requires a QGIS GetCapabilities browse —
WMS timed out from this machine 2026-09-04, so no API auto-extract).

What we do for the pilot (honest, no fabrication from DEM edges):
  - The Gangtok DRAP (data/raw/docs/Gangtok_Disaster_Resilience_Action_Plan.pdf) contains
    Figure 24 Lineament Buffer Map + Figure 47 Lineaments Density Map (Gangtok) alongside
    Figure 25/48 Lithology — same NESAC source, same town extent. The density map shows
    central Gangtok as low-moderate density (visually <1.5 km/km2) within a Himalayan
    context where published Gangtok-adjacent work cites 0.3-1.4. We therefore set a
    conservative literature-anchored proxy: 0.8 km/km2 for all four pilot points,
    tagged PROXY-published-map + Bhuvan-availability, with the 50K scale limit stated.
  - This is stronger than STUB (documented source + documented layer availability + map context)
    but weaker than a per-slope Bhuvan vector clip (which needs QGIS manual "Clip and Ship"
    — documented as the upgrade path).

Outputs:
  data/processed/terrain/s234_lineament.json (evidence + per-slope value + limits + upgrade path)

Tag: PROXY-published-map (literature/Bhuvan-availability + figure context, not a vector clip).
Replace with Bhuvan vector clip when the QGIS extract lands; manifest carries the limit.

Run: python scripts/extract_lineament.py
"""
from __future__ import annotations
import hashlib, json, pathlib

OUT=pathlib.Path("data/processed/terrain/s234_lineament.json")
PDF=pathlib.Path("data/raw/docs/Gangtok_Disaster_Resilience_Action_Plan.pdf")
VALUE=0.8  # km/km2 — conservative literature proxy, see docstring

MAPPING={"S1": VALUE, "S2": VALUE, "S3": VALUE, "S4": VALUE}

def main():
    assert PDF.exists()
    import pymupdf
    doc=pymupdf.open(str(PDF))
    # verify figure exists
    has=False
    for i in range(len(doc)):
        if "Figure 24" in doc[i].get_text() and "Lineament" in doc[i].get_text():
            has=True; print(f"[OK] lineament figure index on p{i+1}")
            break
    assert has
    has2=False
    for i in range(len(doc)):
        if "Figure 47" in doc[i].get_text() and "Lineament" in doc[i].get_text():
            has2=True; print(f"[OK] lineament density figure on p{i+1}")
            break
    assert has2
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rec={
        "source_pdfs": [str(PDF).replace("\\","/")],
        "figures_cited": "Figure 24 Lineament Buffer Map + Figure 47 Lineaments Density Map, Gangtok (Source: NESAC, same report as lithology)",
        "bhuvan_layer": "Lineament 50K 2005-06 — Sikkim listed as available state (bhuvan-app1.nrsc.gov.in/mines/mines.php); NRSC: 'in association with GSI, satellite + collateral, limited field work' (nwdp.nwic.in/dataset/lineament)",
        "wms": "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms (layer Lineament per Bhuvan Wiki; exact Sikkim layer name needs QGIS GetCapabilities browse — WMS timed out from this machine 2026-09-04)",
        "pilot_points": "S1 27.3450/88.6000, S2 27.3380/88.6120, S3 27.3250/88.6065, S4 27.3150/88.5950 — all central Gangtok, same map extent as lithology",
        "row_values": MAPPING,
        "value_basis": "conservative proxy 0.8 km/km2 — literature-anchored (Gangtok-adjacent 0.3-1.4 in Himalayan 50K; density map shows central Gangtok low-moderate <1.5); uniform across 4 points because 50K figure not digitized per-slope",
        "tag": "PROXY-published-map (Bhuvan availability + figure context, not a vector clip)",
        "limit": "50K scale; not a per-slope Bhuvan clip; replace via Bhuvan Thematic 'Clip and Ship' or WMS GetFeature in QGIS → length/area → km/km2",
        "upgrade_path": "Bhuvan Thematic portal → Sikkim Lineament 50K → clip Gangtok AOI (88.58-88.63E, 27.30-27.36N) → export Shapefile → calculate lineament_density per slope",
    }
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"[OK] wrote {OUT}")
    for k,v in MAPPING.items():
        print(k, v)
    print("sha256:", hashlib.sha256(OUT.read_bytes()).hexdigest())
if __name__=="__main__":
    main()
