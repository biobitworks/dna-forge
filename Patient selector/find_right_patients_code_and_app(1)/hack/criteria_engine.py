"""Structured table + 30 explicit, readable eligibility filters.
Each filter returns None (no match) or a dict {field: value} of the evidence that matched."""
import re

ORGANS = ["breast", "colon", "lung", "prostate", "stomach", "kidney", "skin"]

def organ_of(f):
    s = f.get("Specimen", "").lower()
    if "lung" in s: return "lung"
    for o in ORGANS:
        if s.startswith(o) or s.startswith("a. " + o): return o
    return None

def num(s, pat=r"(\d+(?:\.\d+)?)"):
    m = re.search(pat, s or "");  return float(m.group(1)) if m else None

def size_mm(s):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(mm|cm)", s or "")
    if not m: return None
    v = float(m.group(1));  return v * 10 if m.group(2) == "cm" else v

def nodes_pos(s):
    m = re.search(r"(\d+)\s+of\s+(\d+)\s+positive", s or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)

def present(s):   # "present", "present (PL1)", "present, left" -> True; "not identified" -> False
    s = (s or "").lower().strip()
    if not s: return None
    if s.startswith("not identified") or s.startswith("absent") or s.startswith("none"): return False
    return s.startswith("present")

def stage(f):
    s = f.get("Pathologic stage (AJCC 8th ed.)", "")
    t = re.search(r"\b(?:y|r)?p(T[0-9a-z]+|Tis|TX)", s); n = re.search(r"\b(?:y)?p(N[0-9X][a-z]*)", s)
    return (t.group(1) if t else None, n.group(1) if n else None)

def receptor(bio, name):   # ER/PR/HER2 status word from the Biomarkers field
    m = re.search(name + r"\s+(positive|negative|equivocal)", bio or "")
    return m.group(1) if m else None

def mmr(text):
    s = re.search(r"[^.]*(?:[Mm]ismatch repair|MMR)[^.]*\.", text)
    if not s: return None
    return "deficient (loss)" if "loss" in s.group(0) else "proficient (intact)"

def age_lo(b):
    return int(re.match(r"(\d+)", b).group(1)) if b else None
def age_hi(b):
    return 200 if b.endswith("+") else int(b.split("-")[1])

def row(p):
    """Flatten a parsed report into the structured table row."""
    f = p["fields"]; o = organ_of(f); pT, pN = stage(f); pos, tot = nodes_pos(f.get("Lymph nodes"))
    bio = f.get("Biomarkers", "")
    return dict(organ=o, sex=p.get("sex"), age_band=p.get("age_band"), report_year=p.get("report_year"),
        histology=f.get("Histologic type") or f.get("Diagnosis"), pT=pT, pN=pN, nodes_pos=pos, nodes_examined=tot,
        size_mm=size_mm(f.get("Tumor size")), lvi=present(f.get("Lymphovascular invasion")),
        pni=present(f.get("Perineural invasion")), ER=receptor(bio, "ER"), PR=receptor(bio, "PR"),
        HER2=receptor(bio, "HER2") or (re.match(r"(positive|negative|equivocal)", f.get("HER2", "")) or [None, None])[1] if (bio or f.get("HER2")) else None,
        MMR=mmr(p["text"]) if o == "colon" else None, fields=f)

# ---------- helpers that return evidence ----------
def ev(f, *keys):  return {k: f[k] for k in keys if k in f}
H = "header"

def c01(r, f):  # breast, HER2 negative, >=1 positive node
    if r["organ"] == "breast" and r["HER2"] == "negative" and (r["nodes_pos"] or 0) >= 1: return ev(f, "Biomarkers", "Lymph nodes")
def c02(r, f):
    if r["organ"] == "breast" and r["ER"] == "positive" and r["PR"] == "negative": return ev(f, "Biomarkers")
def c03(r, f):
    if r["organ"] == "breast" and r["ER"] == r["PR"] == r["HER2"] == "negative": return ev(f, "Biomarkers")
def c04(r, f):
    if r["organ"] == "breast" and r["lvi"] and (r["size_mm"] or 0) > 20: return ev(f, "Lymphovascular invasion", "Tumor size")
def c05(r, f):  # negative margins, closest invasive distance <= 3 mm  (ambiguity: "within 3 mm" read as <= 3)
    m = f.get("Margins", "")
    if r["organ"] == "breast" and m.startswith("negative"):
        d = num(m, r"is (\d+(?:\.\d+)?) mm from the closest")
        if d is not None and d <= WITHIN_MM: return ev(f, "Margins")
WITHIN_MM = 3
def c06(r, f):
    if r["organ"] == "breast" and f.get("Tumor focality", "").startswith("multifocal") and age_hi(r["age_band"]) < 60:
        return {**ev(f, "Tumor focality"), H: "age band " + r["age_band"]}
def c07(r, f):
    if r["organ"] == "breast" and num(f.get("Nottingham grade")) == 3 and r["lvi"] is False: return ev(f, "Nottingham grade", "Lymphovascular invasion")
def colon_node_pos(r, include_n1c):  # >=1 positive node; stage III also includes pN1c (tumor deposits, 0 nodes)
    return (r["nodes_pos"] or 0) >= 1 or (include_n1c and (r["pN"] or "").startswith("N1c"))
C08_INCLUDE_N1C = True    # verified on train: answer key counts 3 pN1c cases as stage III
C29_INCLUDE_N1C = False   # AMBIGUOUS: "node-positive" read literally; no train case decides it
def c08(r, f):
    if r["organ"] == "colon" and colon_node_pos(r, C08_INCLUDE_N1C): return ev(f, "Lymph nodes", "Pathologic stage (AJCC 8th ed.)")
def c09(r, f):
    if r["organ"] == "colon" and "mucinous" in (r["histology"] or "").lower(): return ev(f, "Histologic type")
def c10(r, f):
    if r["organ"] == "colon" and present(f.get("Tumor deposits")): return ev(f, "Tumor deposits")
def c11(r, f):
    if r["organ"] == "colon" and r["nodes_pos"] == 0 and r["lvi"]: return ev(f, "Lymph nodes", "Lymphovascular invasion")
def c12(r, f):
    if r["organ"] == "colon" and (r["pT"] or "").startswith("T4"): return ev(f, "Depth of invasion", "Pathologic stage (AJCC 8th ed.)")
def c13(r, f):
    if r["organ"] == "colon" and (r["size_mm"] or 0) >= 50 and r["pni"] is False: return ev(f, "Tumor size", "Perineural invasion")
def c14(r, f):
    if r["organ"] == "lung" and present(f.get("Visceral pleural invasion")): return ev(f, "Visceral pleural invasion")
def c15(r, f):
    if r["organ"] == "lung" and "squamous" in (r["histology"] or "").lower() and re.search(r"bronchial margin (?:involved|positive)", f.get("Margins", "")):
        return ev(f, "Histologic type", "Margins")
def c16(r, f):
    if r["organ"] == "lung" and "adenocarcinoma" in (r["histology"] or "").lower() and (r["nodes_pos"] or 0) >= 1: return ev(f, "Histologic type", "Lymph nodes")
def c17(r, f):
    g = num(f.get("Gleason score"), r"Grade Group (\d)")
    if r["organ"] == "prostate" and g and g >= 4: return ev(f, "Gleason score")
def c18(r, f):
    if r["organ"] == "prostate" and present(f.get("Seminal vesicle invasion")): return ev(f, "Seminal vesicle invasion")
def c19(r, f):
    if r["organ"] == "prostate" and f.get("Margins", "").startswith("positive") and f.get("Extraprostatic extension", "").startswith("not identified"):
        return ev(f, "Margins", "Extraprostatic extension")
def c20(r, f):
    if r["organ"] == "prostate" and r["pni"] and r["lvi"] is False: return ev(f, "Perineural invasion", "Lymphovascular invasion")
def c21(r, f):
    if r["organ"] == "stomach" and f.get("HER2", "").startswith("positive"): return ev(f, "HER2")
def c22(r, f):
    h = (r["histology"] or "").lower()
    if r["organ"] == "stomach" and h.startswith("poorly cohesive") and "mixed" not in h and (r["nodes_pos"] or 0) >= 1: return ev(f, "Histologic type", "Lymph nodes")
def c23(r, f):
    if r["organ"] == "stomach" and (r["pT"] or "").startswith("T4"): return ev(f, "Depth of invasion", "Pathologic stage (AJCC 8th ed.)")
def c24(r, f):
    if r["organ"] == "kidney" and "clear cell" in (r["histology"] or "").lower() and num(f.get("ISUP grade"), r"(\d)") in (3, 4): return ev(f, "Histologic type", "ISUP grade")
def c25(r, f):
    if r["organ"] == "kidney" and present(f.get("Sarcomatoid or rhabdoid features")): return ev(f, "Sarcomatoid or rhabdoid features")
def c26(r, f):  # renal vein (main or segmental branches) or IVC
    e = f.get("Extent of invasion", "").lower()
    if r["organ"] == "kidney" and ("renal vein" in e or "vena cava" in e): return ev(f, "Extent of invasion")
def c27(r, f):
    m = f.get("Margins", "").lower()
    if r["organ"] == "skin" and (f.get("Diagnosis") or "").lower().startswith("basal cell carcinoma") and (
        re.search(r"extends to the (?:peripheral and )?deep margin", m) or re.search(r"deep margins? (?:is |are )?involved", m) or "deep margins involved" in m or "and deep margins involved" in m):
        return ev(f, "Diagnosis", "Margins")
def c28(r, f):
    d = (f.get("Diagnosis") or "")
    if r["organ"] == "skin" and d.lower().startswith("invasive squamous cell carcinoma") and re.search(r"\(G[23]\)", d): return ev(f, "Diagnosis")
def c29(r, f):
    if r["organ"] == "colon" and age_lo(r["age_band"]) >= 70 and colon_node_pos(r, C29_INCLUDE_N1C): return {**ev(f, "Lymph nodes"), H: "age band " + r["age_band"]}
def c30(r, f):
    if r["organ"] == "lung" and r["sex"] == "F" and r["report_year"] in (2023, 2024): return {H: f"sex F, year {r['report_year']}", **ev(f, "Histologic type")}

FILTERS = {f"c{i:02d}": globals()[f"c{i:02d}"] for i in range(1, 31)}

def match_all(rows):
    """rows: list of (id, row). Returns {cid: {id: evidence}}."""
    out = {}
    for cid, fn in FILTERS.items():
        out[cid] = {}
        for rid, r in rows:
            e = fn(r, r["fields"])
            if e: out[cid][rid] = e
    return out
