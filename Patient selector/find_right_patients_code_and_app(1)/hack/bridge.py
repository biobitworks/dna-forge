"""Bridge (proof of concept): run the Task A criteria engine on the 57 slide reports (free text), then use
C2 similarity to propose more candidate slides for each criterion. Research demo on synthetic/de-identified data."""
import json, re
from collections import Counter, defaultdict
from pathlib import Path
import criteria_engine as CE
from slides_common import manifest
OUT = Path(__file__).parent / "out"
G2O = {"Breast": "breast", "Colon and rectum": "colon", "Lung": "lung", "Prostate": "prostate", "Stomach": "stomach", "Kidney": "kidney", "Skin": "skin"}
O2G = {v: k for k, v in G2O.items()}

def receptor_ft(t, name, pat):
    m = re.search(pat + r"[^.;,]{0,25}?(weakly positive|low positive|positive|negative)", t, re.I)
    if not m: return None
    w = m.group(1).lower(); return "low positive" if w in ("weakly positive", "low positive") else w

def to_fields(s):
    """Free-text final diagnosis -> structured-vocabulary fields (only what the text states)."""
    t = s["report"].get("finalDiagnosis", "") + " " + (s.get("marker") or "")
    f, org = {}, G2O.get(s.get("organGroup"))
    f["Specimen"] = (org or "other").capitalize() + " (slide report)"
    f["Diagnosis"] = s["report"].get("finalDiagnosis", "")[:200]
    m = re.search(r"(\d+)\s+out of\s+(\d+)\s+lymph nodes", t)
    if m: f["Lymph nodes"] = f"{m.group(1)} of {m.group(2)} positive"
    if org == "breast":
        er, pr, h2 = receptor_ft(t, "ER", r"\bER\b"), receptor_ft(t, "PR", r"\bPR\b"), receptor_ft(t, "HER2", r"HER2(?:/Neu)?")
        if er or pr or h2: f["Biomarkers"] = "; ".join(f"{n} {v}" for n, v in (("ER", er), ("PR", pr), ("HER2", h2)) if v)
        g = re.search(r"\bG([123])\b", t)
        if g: f["Nottingham grade"] = g.group(1)
    if org == "prostate":
        g = re.search(r"Gleason score (\d\+\d=\d+), Grade Group (\d)", t)
        if g: f["Gleason score"] = f"{g.group(1)}, Grade Group {g.group(2)}"
        if re.search(r"with extraprostatic extension", t): f["Extraprostatic extension"] = "present (stated in report)"
        if re.search(r"with perineural invasion", t): f["Perineural invasion"] = "present"
    if org in ("lung", "stomach", "colon", "kidney", "prostate"): f["Histologic type"] = f["Diagnosis"]
    return f, org

# fields each criterion depends on (beyond organ); used to label "organ-level candidate, field not reported"
NEEDS = {"c01": ["Biomarkers", "Lymph nodes"], "c02": ["Biomarkers"], "c03": ["Biomarkers"], "c04": ["Lymphovascular invasion", "Tumor size"],
 "c05": ["Margins"], "c06": ["Tumor focality", "age"], "c07": ["Nottingham grade", "Lymphovascular invasion"], "c08": ["Lymph nodes"],
 "c09": ["Histologic type"], "c10": ["Tumor deposits"], "c11": ["Lymph nodes", "Lymphovascular invasion"], "c12": ["Pathologic stage"],
 "c13": ["Tumor size", "Perineural invasion"], "c14": ["Visceral pleural invasion"], "c15": ["Margins"], "c16": ["Lymph nodes"],
 "c17": ["Gleason score"], "c18": ["Seminal vesicle invasion"], "c19": ["Margins", "Extraprostatic extension"], "c20": ["Perineural invasion", "Lymphovascular invasion"],
 "c21": ["HER2"], "c22": ["Lymph nodes"], "c23": ["Pathologic stage"], "c24": ["ISUP grade"], "c25": ["Sarcomatoid or rhabdoid features"],
 "c26": ["Extent of invasion"], "c27": ["Margins"], "c28": ["Diagnosis grade"], "c29": ["age", "Lymph nodes"], "c30": ["sex", "report year"]}

# histology the criterion requires; if the free text states a different one, the slide is ruled out (not a candidate)
HIST = {"c09": r"mucinous", "c15": r"squamous", "c16": r"adenocarcinoma", "c22": r"poorly cohesive|signet|diffuse",
        "c24": r"clear cell", "c27": r"basal cell", "c28": r"invasive squamous cell carcinoma(?!.{0,5}not identified)"}

def criterion_organs():
    tab = json.load(open(OUT / "a_table.json")); ans = json.load(open(CE.__file__.replace("criteria_engine.py", "") + "../data/pack_reports/criteria_train_answers.json"))
    return {c: Counter(tab[i]["organ"] for i in ids).most_common(1)[0][0] for c, ids in ans.items()}

if __name__ == "__main__":
    S = manifest(); byid = {s["id"]: s for s in S}
    C1 = json.load(open(OUT / "c1_predictions.json")); NN = json.load(open(OUT / "c2_neighbours.json"))
    crit = {c["id"]: c["text"] for c in json.load(open(CE.Path(__file__).parent.parent / "data/pack_reports/criteria.json"))} if hasattr(CE, "Path") else None
    crit = {c["id"]: c["text"] for c in json.load(open(Path(__file__).parent.parent / "data/pack_reports/criteria.json"))}
    corg = criterion_organs()
    group_of = lambda i: byid[i].get("organGroup") or C1[i]["pred"]
    rows = {}
    for s in S:
        if not s.get("report") or "finalDiagnosis" not in s["report"]: continue
        f, org = to_fields(s)
        r = dict(organ=org, sex=s.get("sex"), age_band=None, report_year=None, histology=f.get("Histologic type") or f["Diagnosis"],
                 pT=None, pN=None, nodes_pos=None, nodes_examined=None, size_mm=None, lvi=None, pni=CE.present(f.get("Perineural invasion")),
                 ER=None, PR=None, HER2=None, MMR=None, fields=f)
        r["nodes_pos"], r["nodes_examined"] = CE.nodes_pos(f.get("Lymph nodes"))
        b = f.get("Biomarkers", "")
        for k in ("ER", "PR", "HER2"):
            m = re.search(k + r" (low positive|positive|negative)", b); r[k] = m.group(1) if m else None
        rows[s["id"]] = r
    print("slide reports with finalDiagnosis:", len(rows), "of", sum(1 for s in S if s.get("report")))
    out = {}
    for cid, fn in CE.FILTERS.items():
        seeds, cands = {}, []
        for sid, r in rows.items():
            if r["age_band"] is None and cid in ("c06", "c29"): e = None
            else:
                try: e = fn(r, r["fields"])
                except Exception: e = None
            if e: seeds[sid] = dict(status="match", evidence=e)
            elif r["organ"] == corg[cid] and (cid not in HIST or re.search(HIST[cid], r["fields"]["Diagnosis"], re.I) and not re.search(r"(?:residual )?" + HIST[cid] + r".{0,5}not identified", r["fields"]["Diagnosis"], re.I)):
                cands.append(sid); seeds[sid] = dict(status="organ-level candidate (fields not reported: " + ", ".join(NEEDS[cid]) + ")", evidence={"Diagnosis": r["fields"]["Diagnosis"]})
        # C2 expansion from every seed: neighbours in the same organ group (known label or C1 prediction)
        target = O2G[corg[cid]]; sugg = {}
        for sid, info in seeds.items():
            for n in NN[sid]:
                j = n["id"]
                if j in seeds or group_of(j) != target: continue
                w = (1.0 if info["status"] == "match" else 0.5) * n["cos"]
                if w > sugg.get(j, {}).get("score", -1):
                    sugg[j] = dict(score=w, via=sid, heldout=bool(byid[j].get("heldout")), group=group_of(j), group_source="label" if byid[j].get("organGroup") else f"C1 prediction ({C1[j]['conf']:.2f})")
        out[cid] = dict(text=crit[cid], organ=corg[cid], seeds=seeds, suggestions=dict(sorted(sugg.items(), key=lambda x: -x[1]["score"])[:15]))
        nm = sum(v["status"] == "match" for v in seeds.values())
        if seeds: print(f"{cid} {crit[cid][:55]:55s} matches={nm} organ-candidates={len(seeds)-nm} C2-suggested={len(out[cid]['suggestions'])}")
    json.dump(out, open(OUT / "bridge.json", "w"), indent=1)
    for cid in ("c01", "c02", "c17"):
        for sid, v in out[cid]["seeds"].items():
            if v["status"] == "match": print(cid, sid[:30], v["evidence"])
