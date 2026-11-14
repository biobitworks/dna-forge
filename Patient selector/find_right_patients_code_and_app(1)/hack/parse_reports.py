"""Parse synthetic pathology reports into structured fields (header + FINAL DIAGNOSIS block)."""
import json, re, sys
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "pack_reports"

def known_keys(train_path=DATA / "train.jsonl"):
    keys = set()
    for l in open(train_path):
        keys.update(json.loads(l)["labels"]["diagnosis"].keys())
    return sorted(keys, key=len, reverse=True)

KEYS = None
HDR = re.compile(r"Patient:\s*([MF]),\s*age band\s*([0-9+\-]+)\s*\|\s*Report year:\s*(\d{4})")

def parse(text):
    global KEYS
    if KEYS is None:
        KEYS = known_keys()
    out = {}
    m = HDR.search(text)
    if m:
        out["sex"], out["age_band"], out["report_year"] = m.group(1), m.group(2), int(m.group(3))
    sm = re.search(r"^SPECIMEN:\s*(.+)$", text, re.M)
    fields = {}
    if sm: fields["Specimen"] = sm.group(1).strip()
    i = text.find("FINAL DIAGNOSIS:")
    j = text.find("GROSS DESCRIPTION:", i)
    block = text[i + len("FINAL DIAGNOSIS:"): j if j > 0 else None].strip()
    keyalt = "|".join(re.escape(k) for k in KEYS)
    # split at newlines, or at "; " that is followed by a known key + ":"
    parts = re.split(r"\n\s*|;\s+(?=(?:%s):)" % keyalt, block)
    keyre = re.compile(r"^(%s):\s*(.*)$" % keyalt, re.S)
    for p in parts:
        p = p.strip()
        if not p: continue
        km = keyre.match(p)
        if km:
            fields[km.group(1)] = km.group(2).strip()
        else:
            fields.setdefault("Diagnosis", p)
    if fields:  # one-line layout ends with a full stop on the last value
        last = list(fields)[-1]
        if "\n" not in block and fields[last].endswith("."):
            fields[last] = fields[last][:-1]
    out["fields"] = fields
    out["text"] = text
    return out

def load(path):
    return [json.loads(l) for l in open(path)]

if __name__ == "__main__":
    rs = load(DATA / "train.jsonl")
    bad = 0; badkeys = {}
    for r in rs:
        f = parse(r["report_text"])["fields"]; g = r["labels"]["diagnosis"]
        if f != g:
            bad += 1
            for k in set(f) | set(g):
                if f.get(k) != g.get(k): badkeys[k] = badkeys.get(k, 0) + 1
            if bad <= 3: print({k: (f.get(k), g.get(k)) for k in set(f) | set(g) if f.get(k) != g.get(k)})
    print(f"exact field match: {len(rs)-bad}/{len(rs)}", badkeys)
