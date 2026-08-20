"""Material resistance / susceptibility coefficients for the CRACKS track (CRACK-04).

weakness (0..1): higher = more prone to cracking / less resistance. Clay and
fine-grained wet materials crack most; harder sandstone and lignite the least.
clay_like (0..1): degree of fine-grained shrink-swell behaviour feeding the
desiccation mechanism (only >0.5 can desiccate, CRACK-01.2).

DIRECTION CONTRACT: every growth mechanism that is scaled by material must be
MONOTONE NON-DECREASING in `weakness` (weakness up -> susceptibility up ->
crack growth up; cracks research line 88 "material weakness (clay > sandstone)",
line 169 "cracks concentrate in the weakest materials"). Use `susceptibility()`
and never multiply a term by (1 - weakness).
"""
from generator_schema import MATERIAL_CLASSES


def susceptibility(weakness):
    """Maps weakness [0,1] -> susceptibility [0.5, 1.0], monotone.

    Strongest material still retains a baseline response (0.5); the weakest
    material doubles that baseline (1.0). Monotone direction enforced by the
    1D audit gate (audit_cracks_1D.py, audit item 2).
    """
    return 0.5 + 0.5 * weakness


MATERIAL_WEAKNESS = {
    "lateritic_soil": 0.75,
    "clayey_sandstone": 0.55,
    "sandstone": 0.35,
    "clay": 1.0,
    "variegated_sandy_clay": 0.9,
    "carbonaceous_clay": 0.95,
    "aquifer_sand": 0.7,
    "lignite": 0.3,
    "overburden_mixed": 0.8,
}

CLAY_LIKE = {
    "lateritic_soil": 0.4,
    "clayey_sandstone": 0.45,
    "sandstone": 0.1,
    "clay": 1.0,
    "variegated_sandy_clay": 0.85,
    "carbonaceous_clay": 0.95,
    "aquifer_sand": 0.15,
    "lignite": 0.2,
    "overburden_mixed": 0.7,
}

assert set(MATERIAL_WEAKNESS) == set(MATERIAL_CLASSES), "weakness map covers all schema materials"
assert set(CLAY_LIKE) == set(MATERIAL_CLASSES), "clay map covers all schema materials"