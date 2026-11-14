"""Tests for dnaforge.reports on hand-written synthetic strings (no challenge data)."""
from dnaforge.reports import CRITERIA, Case, parse_diagnosis, prf

MULTI = """SURGICAL PATHOLOGY REPORT (SYNTHETIC; NOT A REAL PATIENT)
Patient: F, age band 50-59 | Report year: 2023

SPECIMEN: Breast, left, lumpectomy

FINAL DIAGNOSIS:
  Histologic type: Invasive lobular carcinoma
  Nottingham grade: 3 (score 8 of 9)
  Tumor size: 25 mm
  Margins: negative; invasive carcinoma is 2 mm from the closest margin (deep)
  Tumor focality: multifocal (2 foci; the largest is reported)
  Lymphovascular invasion: present
  Lymph nodes: 2 of 7 positive
  Biomarkers: ER positive, 90% of tumor cells, strong; PR negative, less than 1% of tumor cells; HER2 negative (score 1+)
  Pathologic stage (AJCC 8th ed.): pT2(m) pN1a

GROSS DESCRIPTION:
Made-up text.
"""

ONELINE = """Patient: M, age band 70-79 | Report year: 2021

SPECIMEN: Colon (sigmoid colon), sigmoid colectomy

FINAL DIAGNOSIS: Histologic type: Mucinous adenocarcinoma; Tumor size: 5.0 cm; Margins: proximal margin negative (4.0 cm); distal margin negative (6.1 cm); Lymphovascular invasion: not identified; Perineural invasion: not identified; Tumor deposits: present (1); Lymph nodes: 0 of 20 positive; Pathologic stage (AJCC 8th ed.): pT4a pN1c.

MICROSCOPIC DESCRIPTION:
Made-up text.
"""

SKIN = """Patient: F, age band 60-69 | Report year: 2022

SPECIMEN: Skin, nose, excision

FINAL DIAGNOSIS: Basal cell carcinoma, nodular type; Margins: peripheral and deep margins involved by carcinoma.

GROSS DESCRIPTION:
x
"""


def test_parse_multiline_keeps_semicolons_in_values():
    d = parse_diagnosis(MULTI)
    assert d["Specimen"] == "Breast, left, lumpectomy"
    assert d["Biomarkers"].startswith("ER positive") and d["Biomarkers"].endswith("(score 1+)")
    assert d["Margins"] == "negative; invasive carcinoma is 2 mm from the closest margin (deep)"


def test_parse_oneline_layout():
    d = parse_diagnosis(ONELINE)
    assert d["Margins"] == "proximal margin negative (4.0 cm); distal margin negative (6.1 cm)"
    assert d["Pathologic stage (AJCC 8th ed.)"] == "pT4a pN1c"
    assert d["Tumor deposits"] == "present (1)"


def test_case_fields_and_predicates():
    b = Case(MULTI, "B1")
    assert (b.organ, b.sex, b.age_band, b.year, b.pT, b.pN) == ("breast", "F", "50-59", 2023, "pT2(m)", "pN1a")
    assert b.size_mm() == 25 and b.nodes() == (2, 7)
    hits = {cid for cid, fn in CRITERIA.items() if fn(b)}
    assert {"c01", "c02", "c04", "c05", "c06"} <= hits
    assert "c03" not in hits and "c07" not in hits  # not triple-negative; LVI present

    c = Case(ONELINE, "C1")
    hits = {cid for cid, fn in CRITERIA.items() if fn(c)}
    assert {"c08", "c09", "c10", "c12", "c13"} <= hits  # pN1c counts as stage III; 5.0 cm is ">= 5 cm"
    assert "c11" not in hits and "c29" not in hits  # no LVI; no positive lymph nodes

    s = Case(SKIN, "S1")
    assert s.organ == "skin" and s.d["Diagnosis"] == "Basal cell carcinoma, nodular type"
    assert CRITERIA["c27"](s)


def test_prf():
    assert prf({1, 2}, {2, 3}) == (0.5, 0.5, 0.5)
    assert prf(set(), set()) == (1.0, 1.0, 1.0)
