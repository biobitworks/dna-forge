"""Task A (criteria search) for the Biobase synthetic pathology reports.

The final diagnosis block of every report is written by code, so we parse it into
structured fields and answer each plain-language criterion with a hand-written
predicate over those fields (plus organ, stage, age band, sex and year).

    python3 -m dnaforge.reports --pack <pack_reports dir> --out <submission.json>

The run is wrapped in a custody RunRecord: runs/<id>/record.json holds input hashes,
train metrics per criterion and the hash of the submission file. No report text is
ever written to the record.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Every field name the final diagnosis block can carry (README of the pack).
FIELD_NAMES = [
    "Specimen", "Diagnosis", "Margins", "Tumor size", "Aggressive growth pattern", "Ulceration",
    "Perineural invasion", "Depth", "Pathologic stage", "Depth of invasion", "Lymphovascular invasion",
    "High-risk features", "Pathologic stage (AJCC 8th ed.)", "Invasive carcinoma", "Breslow thickness",
    "Mitotic rate", "Regression", "Tumor-infiltrating lymphocytes", "Microscopic satellites", "Neurotropism",
    "Extension along follicular epithelium", "Dermal invasion", "Residual melanoma in this excision",
    "Biopsy correlation", "Clark level", "Tumor site", "Histologic type", "Nottingham grade", "Tumor focality",
    "Ductal carcinoma in situ", "Lymph nodes", "Biomarkers", "Neoadjuvant therapy", "Visceral pleural invasion",
    "Gleason score", "Tumor extent", "Cribriform glands", "Intraductal carcinoma", "Extraprostatic extension",
    "Seminal vesicle invasion", "Histologic grade", "HER2", "Macroscopic tumor perforation", "Tumor deposits",
    "ISUP grade", "Sarcomatoid or rhabdoid features", "Extent of invasion",
]
# Longest first so "Pathologic stage (AJCC 8th ed.)" wins over "Pathologic stage".
_KEYS = sorted(FIELD_NAMES, key=len, reverse=True)
_KEY_RE = re.compile(r"^(" + "|".join(re.escape(k) for k in _KEYS) + r"|Part [A-Z], [^:]+): (.*)$", re.S)

_HEADER_RE = re.compile(r"Patient:\s*([MF])\s*,\s*age band\s*([0-9+\-]+)\s*\|\s*Report year:\s*(\d{4})")
_SPEC_RE = re.compile(r"^SPECIMEN:\s*(.+)$", re.M)
_SECTION_RE = re.compile(r"^[A-Z][A-Z ]+:", re.M)


def _split_key(piece: str):
    m = _KEY_RE.match(piece)
    return (m.group(1), m.group(2)) if m else (None, piece)


def _assemble(pieces: List[str], joiner: str) -> Dict[str, str]:
    """Turn a sequence of 'Key: value' pieces into a dict. A piece without a known key
    either is the unkeyed skin diagnosis (first piece) or continues the previous value
    (values such as Margins and Biomarkers contain '; ' themselves)."""
    out: Dict[str, str] = {}
    last: Optional[str] = None
    for p in pieces:
        p = p.strip()
        if not p:
            continue
        k, v = _split_key(p)
        if k is None:
            if last is None:
                k = "Diagnosis"
            else:
                out[last] = out[last] + joiner + p
                continue
        out[k] = v.strip()
        last = k
    return out


def final_diagnosis_block(text: str) -> str:
    i = text.find("FINAL DIAGNOSIS:")
    if i < 0:
        return ""
    body = text[i + len("FINAL DIAGNOSIS:"):]
    m = _SECTION_RE.search(body)
    return body[:m.start()] if m else body


def parse_diagnosis(text: str) -> Dict[str, str]:
    """Parse the final diagnosis block in either layout into {field: text}."""
    block = final_diagnosis_block(text)
    first, _, rest = block.partition("\n")
    first = first.strip()
    if first:  # one-line layout: everything after the heading on one line, '; '-separated
        line = first[:-1] if first.endswith(".") else first
        fields = _assemble(line.split("; "), "; ")
    else:      # one field per line
        lines = [l for l in rest.split("\n") if l.strip()]
        fields = _assemble(lines, " ")
    m = _SPEC_RE.search(text)
    if m:
        fields = {"Specimen": m.group(1).strip(), **fields}
    return fields


def parse_header(text: str) -> Dict[str, object]:
    m = _HEADER_RE.search(text)
    if not m:
        return {"sex": None, "age_band": None, "report_year": None}
    return {"sex": m.group(1), "age_band": m.group(2), "report_year": int(m.group(3))}


def organ_of(spec: str) -> Optional[str]:
    s = spec.lower()
    if re.match(r"^(a\.\s*)?skin\b", s):
        return "skin"
    for o in ("breast", "colon", "prostate", "stomach", "kidney"):
        if s.startswith(o):
            return o
    if "lung" in s:
        return "lung"
    if s.startswith("skin") or " skin" in s:
        return "skin"
    return None


class Case:
    """Structured view of one report."""

    def __init__(self, text: str, rid: str = ""):
        self.id = rid
        self.d = parse_diagnosis(text)
        h = parse_header(text)
        self.sex, self.age_band, self.year = h["sex"], h["age_band"], h["report_year"]
        self.organ = organ_of(self.d.get("Specimen", ""))
        stage = self.d.get("Pathologic stage (AJCC 8th ed.)", "")
        mt = re.search(r"\b(pT[0-9a-zX]+(?:\(m\))?)", stage)
        mn = re.search(r"\b(pN[0-9A-Za-z]+(?:\([a-z+]+\))*)", stage)
        self.pT = mt.group(1) if mt else None
        self.pN = mn.group(1) if mn else None
        if self.pT == "pTis" and not self.pN:
            self.pN = "pNX"  # in-situ skin stages are written as "pTis" alone; the labels call them pNX

    def f(self, key: str) -> str:
        return self.d.get(key, "").lower()

    # ---- derived values -------------------------------------------------------------
    @property
    def age_min(self) -> Optional[int]:
        if not self.age_band:
            return None
        m = re.match(r"(\d+)", self.age_band)
        return int(m.group(1)) if m else None

    @property
    def age_max(self) -> Optional[int]:
        if not self.age_band:
            return None
        if self.age_band.endswith("+"):
            return 200
        m = re.match(r"\d+-(\d+)", self.age_band)
        return int(m.group(1)) if m else None

    def nodes(self):
        """(positive, examined) from the Lymph nodes field, or (None, None)."""
        m = re.match(r"(\d+) of (\d+)", self.f("Lymph nodes"))
        return (int(m.group(1)), int(m.group(2))) if m else (None, None)

    @property
    def nodes_pos(self) -> Optional[int]:
        return self.nodes()[0]

    def size_mm(self) -> Optional[float]:
        m = re.match(r"([0-9.]+)\s*(mm|cm)", self.f("Tumor size"))
        if not m:
            return None
        v = float(m.group(1))
        return v * 10 if m.group(2) == "cm" else v

    def present(self, key: str) -> bool:
        return self.f(key).startswith("present")

    def absent(self, key: str) -> bool:
        return self.f(key).startswith("not identified")

    def marker(self, name: str) -> Optional[str]:
        """'positive' / 'negative' / 'equivocal' for ER, PR or HER2 (breast Biomarkers or stomach HER2)."""
        if name == "HER2" and "HER2" in self.d:
            v = self.f("HER2")
        else:
            v = self.f("Biomarkers")
            m = re.search(r"\b" + name.lower() + r" (positive|negative|equivocal|low)", v)
            return m.group(1) if m else None
        m = re.match(r"(positive|negative|equivocal|low)", v)
        return m.group(1) if m else None

    def grade_group(self) -> Optional[int]:
        m = re.search(r"grade group (\d)", self.f("Gleason score"))
        return int(m.group(1)) if m else None


def _pos_nodes(c: Case) -> bool:
    n = c.nodes_pos
    return n is not None and n >= 1


# ---- the 30 criteria, one predicate each ------------------------------------------------
CRITERIA: Dict[str, Callable[[Case], bool]] = {
    "c01": lambda c: c.organ == "breast" and c.marker("HER2") == "negative" and _pos_nodes(c),
    "c02": lambda c: c.organ == "breast" and c.marker("ER") == "positive" and c.marker("PR") == "negative",
    "c03": lambda c: c.organ == "breast" and c.marker("ER") == "negative" and c.marker("PR") == "negative"
    and c.marker("HER2") == "negative",
    "c04": lambda c: c.organ == "breast" and c.present("Lymphovascular invasion") and (c.size_mm() or 0) > 20,
    "c05": lambda c: c.organ == "breast" and _breast_close_margin(c, 3.0),
    "c06": lambda c: c.organ == "breast" and c.f("Tumor focality").startswith("multifocal")
    and c.age_max is not None and c.age_max < 60,
    "c07": lambda c: c.organ == "breast" and c.f("Nottingham grade").startswith("3")
    and c.absent("Lymphovascular invasion"),
    # Stage III = any regional nodal disease, including pN1c (tumor deposits, 0 positive nodes).
    "c08": lambda c: c.organ == "colon" and ((c.pN or "pN0") not in ("pN0", "pNX") or _pos_nodes(c)),
    "c09": lambda c: c.organ == "colon" and c.f("Histologic type").startswith("mucinous adenocarcinoma"),
    "c10": lambda c: c.organ == "colon" and c.present("Tumor deposits"),
    "c11": lambda c: c.organ == "colon" and c.nodes_pos == 0 and c.present("Lymphovascular invasion"),
    "c12": lambda c: c.organ == "colon" and (c.pT or "").startswith("pT4"),
    "c13": lambda c: c.organ == "colon" and (c.size_mm() or 0) >= 50 and c.absent("Perineural invasion"),
    "c14": lambda c: c.organ == "lung" and c.present("Visceral pleural invasion"),
    "c15": lambda c: c.organ == "lung" and c.f("Histologic type").startswith("squamous cell carcinoma")
    and "bronchial margin involved" in c.f("Margins"),
    "c16": lambda c: c.organ == "lung" and "adenocarcinoma" in c.f("Histologic type") and _pos_nodes(c),
    "c17": lambda c: c.organ == "prostate" and (c.grade_group() or 0) >= 4,
    "c18": lambda c: c.organ == "prostate" and c.present("Seminal vesicle invasion"),
    "c19": lambda c: c.organ == "prostate" and c.f("Margins").startswith("positive")
    and c.absent("Extraprostatic extension"),
    "c20": lambda c: c.organ == "prostate" and c.present("Perineural invasion") and c.absent("Lymphovascular invasion"),
    "c21": lambda c: c.organ == "stomach" and c.marker("HER2") == "positive",
    "c22": lambda c: c.organ == "stomach" and c.f("Histologic type").startswith("poorly cohesive carcinoma")
    and _pos_nodes(c),
    "c23": lambda c: c.organ == "stomach" and (c.pT or "").startswith("pT4"),
    "c24": lambda c: c.organ == "kidney" and "clear cell" in c.f("Histologic type")
    and c.f("ISUP grade")[:1] in ("3", "4"),
    "c25": lambda c: c.organ == "kidney" and c.present("Sarcomatoid or rhabdoid features"),
    "c26": lambda c: c.organ == "kidney" and bool(re.search(r"renal vein|vena cava", c.f("Extent of invasion"))),
    "c27": lambda c: c.organ == "skin" and c.f("Diagnosis").startswith("basal cell carcinoma")
    and _deep_margin_involved(c.f("Margins")),
    "c28": lambda c: c.organ == "skin" and c.f("Diagnosis").startswith("invasive squamous cell carcinoma")
    and bool(re.search(r"\((g2|g3)\)", c.f("Diagnosis"))),
    "c29": lambda c: c.organ == "colon" and c.age_min is not None and c.age_min >= 70 and _pos_nodes(c),
    "c30": lambda c: c.organ == "lung" and c.sex == "F" and c.year in (2023, 2024),
}


def _breast_close_margin(c: Case, mm: float) -> bool:
    m = c.f("Margins")
    if not m.startswith("negative"):
        return False
    d = re.search(r"invasive carcinoma is ([0-9.]+) mm from the closest margin", m)
    return bool(d) and float(d.group(1)) <= mm


def _deep_margin_involved(m: str) -> bool:
    """True when a clause of the margin text puts tumor at the deep margin."""
    for clause in m.split(";"):
        if "deep" in clause and re.search(r"involved|extends to|positive", clause) and "negative" not in clause:
            return True
    return False


# ---- evaluation -------------------------------------------------------------------------
def prf(pred: set, gold: set):
    tp = len(pred & gold)
    p = tp / len(pred) if pred else (1.0 if not gold else 0.0)
    r = tp / len(gold) if gold else (1.0 if not pred else 0.0)
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def load_jsonl(path):
    with open(path) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def select(cases: List[Case]) -> Dict[str, List[str]]:
    return {cid: [c.id for c in cases if fn(c)] for cid, fn in CRITERIA.items()}


def check_parser(rows) -> dict:
    """Compare parsed fields with labels.diagnosis and the derived organ/pT/pN/demographics with labels."""
    n_field = n_field_ok = n_case_ok = 0
    meta_bad = {"organ": 0, "pT": 0, "pN": 0, "sex": 0, "age_band": 0, "report_year": 0}
    bad_examples = []
    for r in rows:
        c = Case(r["report_text"], r["id"])
        gold = r["labels"]["diagnosis"]
        ok = True
        for k, v in gold.items():
            n_field += 1
            if c.d.get(k) == v:
                n_field_ok += 1
            else:
                ok = False
        if set(c.d) != set(gold):
            ok = False
        if not ok and len(bad_examples) < 5:
            bad_examples.append(r["id"])
        n_case_ok += ok
        L = r["labels"]
        for k, got in (("organ", c.organ), ("pT", c.pT), ("pN", c.pN), ("sex", c.sex),
                       ("age_band", c.age_band), ("report_year", c.year)):
            if got != L[k]:
                meta_bad[k] += 1
    return {"fields": n_field, "fields_exact": n_field_ok, "cases": len(rows), "cases_exact": n_case_ok,
            "label_mismatches": meta_bad, "bad_example_ids": bad_examples}


def evaluate(cases: List[Case], answers: Dict[str, List[str]]):
    pred = select(cases)
    table = {}
    for cid in CRITERIA:
        p, r, f = prf(set(pred[cid]), set(answers.get(cid, [])))
        table[cid] = {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
                      "n_pred": len(pred[cid]), "n_gold": len(answers.get(cid, []))}
    mean_f1 = sum(t["f1"] for t in table.values()) / len(table)
    return table, mean_f1, pred


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Biobase Task A: criteria search over synthetic reports")
    ap.add_argument("--pack", required=True, help="pack_reports directory")
    ap.add_argument("--out", help="submission JSON path (default runs/<id>/submission_criteria.json)")
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--show-errors", metavar="CID", help="print FP/FN ids for one criterion (debug)")
    a = ap.parse_args(argv)
    from dnaforge.custody import RunRecord

    pack = Path(a.pack)
    train_p, test_p = pack / "train.jsonl", pack / "test.jsonl"
    ans_p, tmpl_p = pack / "criteria_train_answers.json", pack / "submission_template_criteria.json"
    inputs = [train_p, test_p, ans_p, pack / "criteria.json", tmpl_p]
    with RunRecord("reports-task-a", config={"method": "parsed final-diagnosis fields + hand-written predicates"},
                   inputs=inputs, runs_dir=a.runs_dir) as run:
        train = load_jsonl(train_p)
        run.metrics["parser"] = check_parser(train)
        tcases = [Case(r["report_text"], r["id"]) for r in train]
        answers = json.loads(ans_p.read_text())
        table, mean_f1, pred = evaluate(tcases, answers)
        run.metrics["train_per_criterion"] = table
        run.metrics["train_mean_f1"] = round(mean_f1, 4)
        run.metrics["baseline_keyword_mean_f1_reported"] = 0.27
        for cid, t in table.items():
            print(f"{cid}  P={t['precision']:.3f} R={t['recall']:.3f} F1={t['f1']:.3f}  pred={t['n_pred']} gold={t['n_gold']}")
        print(f"train mean F1 = {mean_f1:.4f}")
        print("parser:", json.dumps(run.metrics["parser"]))
        if a.show_errors:
            cid = a.show_errors
            g, pr = set(answers[cid]), set(pred[cid])
            print("FP:", sorted(pr - g)[:15])
            print("FN:", sorted(g - pr)[:15])

        test = load_jsonl(test_p)
        cases = [Case(r["report_text"], r["id"]) for r in test]
        valid = {r["id"] for r in test}
        sub_pred = select(cases)
        template = json.loads(tmpl_p.read_text())
        sub = {cid: sorted(i for i in sub_pred.get(cid, []) if i in valid) for cid in template}
        out = Path(a.out) if a.out else run.dir / "submission_criteria.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(sub, indent=1))
        run.output(out)
        run.metrics["test_counts"] = {cid: len(v) for cid, v in sub.items()}
        run.metrics["test_unparsed_organ"] = sum(1 for c in cases if c.organ is None)
        run.notes.append("submission file is kept on the machine only; it is never committed")
        print("wrote", out, "run", run.id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
