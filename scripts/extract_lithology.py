"""Lithology for Gangtok pilot — digitized from published NESAC/Gangtok maps (SIH26001).

Sources (committed, LOCAL ONLY per .gitignore data/raw/*):
  data/raw/docs/Gangtok_Disaster_Resilience_Action_Plan.pdf (230 pp, 14692654 bytes, sha256 bad2aa98…)
    - p71 §3.4.9 + p118 §5.4.5: "The main Gangtok town stands over the intrusive lingtse granite gneiss.
      The rocks are highly weathered with soil cover <1 to ~10 m. The Lithology map of Gangtok was prepared
      by using the published report of SSDMA, Gangtok and GSI. Source: NESAC" — Figure 25 & 48: Lithology Map, Gangtok.
    - The same NMHS report + CGWB 2025 (data/raw/docs/CGWB_Gangtok_2025.pdf) corroborate local units:
      Lingtse Granite Gneiss, Chungthang Schist/Gneiss, Darjeeling Gneiss, Phyllite, Quaternary alluvium.
      CGWB text: "major portions of Gangtok town are Chungthang Subgroup (biotite gneiss, quartzite, impure marble,
      graphitic schist)" — consistent: Lingste intrudes Chungthang, both map to gneiss family at pilot scale.

Method (honest digitization, not a native GSI vector):
  - No downloadable Gangtok lithology Shapefile found; the authoritative local map is the NESAC figure in the NMHS report.
  - All four pilot slopes (27.3150-27.3450N, 88.5950-88.6120E) lie within the central Gangtok town agglomeration
    shown in Figure 9-25, which the report places on Lingste Granite Gneiss. Therefore all four are coded as that unit.
  - Codebook: GSI/Bhukosh uses lithology names directly; we store the NESAC name verbatim
    (lingtse_granite_gneiss) with source cited. Chungthang/Darjeeling/Phyllite are noted as nearby units
    but not at the pilot points.

Output (committed):
  data/processed/terrain/s234_lithology.json (evidence + per-slope mapping + cited pages)
Row values for feature_matrix update are inside it.

Label: PROXY-published-map (digitized, not Bhukosh vector) — stronger than STUB, weaker than USGS-grade REAL.
Replace with Bhukosh vector when reachable; manifest carries the limit.

Run: python scripts/extract_lithology.py
Requires: pymupdf + stdlib (both present on py311).
"""
from __future__ import annotations
import hashlib, json, pathlib

PDF = pathlib.Path("data/raw/docs/Gangtok_Disaster_Resilience_Action_Plan.pdf")
OUT = pathlib.Path("data/processed/terrain/s234_lithology.json")

MAPPING = {
    "S1": "lingtse_granite_gneiss",
    "S2": "lingtse_granite_gneiss",
    "S3": "lingtse_granite_gneiss",
    "S4": "lingtse_granite_gneiss",
}
# Pilot points all inside central Gangtok town per report Figure 9-25 extent.

def main():
    assert PDF.exists(), f"missing {PDF}"
    import pymupdf
    doc=pymupdf.open(str(PDF))
    # verify the key phrase still there (guards against PDF replacement)
    found=False
    for i in range(len(doc)):
        if "lingtse granite gneiss" in doc[i].get_text().lower():
            found=True; print(f"[OK] lithology phrase on p{i+1}")
            break
    assert found, "lithology phrase not found — PDF changed"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rec={
        "source_pdf": str(PDF).replace("\\","/"),
        "pages_cited": "p71 §3.4.9, p118 §5.4.5 + Figures 25/48 Lithology Map, Gangtok (Source: NESAC; SSDMA+GSI)",
        "phrase": "main Gangtok town stands over the intrusive lingtse granite gneiss (highly weathered, soil <1 to ~10 m)",
        "corroboration_pdf": "data/raw/docs/CGWB_Gangtok_2025.pdf — Chungthang Subgroup major town unit (biotite gneiss etc.)",
        "pilot_points": "S1 27.3450/88.6000, S2 27.3380/88.6120, S3 27.3250/88.6065, S4 27.3150/88.5950 — all central Gangtok (Fig 9-25)",
        "row_values": MAPPING,
        "tag": "PROXY-published-map (digitized NESAC figure, not Bhukosh vector)",
        "codebook": "GSI/Bhukosh lithology names verbatim; lingtse_granite_gneiss is intrusive gneiss family",
        "limit": "50K figure resolution; Chungthang/Darjeeling/Phyllite nearby but not at pilot points per map",
    }
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"[OK] wrote {OUT}")
    for k,v in MAPPING.items():
        print(k, v)
    print("sha256:", hashlib.sha256(OUT.read_bytes()).hexdigest())
if __name__=="__main__":
    main()
