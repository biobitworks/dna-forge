"""Precompute everything the Streamlit app and the static HTML need into app/data (+ resized thumbnails)."""
import json, shutil
from pathlib import Path
from PIL import Image
from slides_common import manifest, D
H = Path(__file__).parent; OUT = H / "out"; APP = H / "app"
tab = json.load(open(OUT / "a_table.json")); ev = json.load(open(OUT / "a_evidence.json"))
text = {json.loads(l)["id"]: json.loads(l)["report_text"] for l in open(D / "pack_reports/test.jsonl")}
crit = json.load(open(D / "pack_reports/criteria.json"))
# reports: structured rows for all; full prose only for test (keeps the bundle small)
rows = {i: {k: v for k, v in r.items()} for i, r in tab.items()}
for i in rows:
    if i in text: rows[i]["report_text"] = text[i]
json.dump(rows, open(APP / "data/reports.json", "w"), separators=(",", ":"))
json.dump({"criteria": crit, "evidence": ev}, open(APP / "data/criteria_evidence.json", "w"))
S = manifest(); C1 = json.load(open(OUT / "c1_predictions.json")); NN = json.load(open(OUT / "c2_neighbours.json"))
keep = ["id", "supplierId", "stain", "magnification", "organ", "organGroup", "diagnosis", "heldout", "sex", "ageBucket", "marker"]
slides = []
for s in S:
    d = {k: s.get(k) for k in keep}; d["heldout"] = bool(s.get("heldout"))
    rep = s.get("report") or {}; d["report"] = rep.get("finalDiagnosis") or rep.get("siteOperation")
    d["c1"] = C1[s["id"]]; d["neighbours"] = NN.get(s["id"], []); slides.append(d)
json.dump(slides, open(APP / "data/slides.json", "w"))
shutil.copy(OUT / "bridge.json", APP / "data/bridge.json")
scores = dict(A=json.load(open(OUT / "a_train_scores.json")), A_baseline=json.load(open(OUT / "baseline_train_scores.json")),
              C1_grid=json.load(open(OUT / "c1_cv_grid.json")), C2_grid=json.load(open(OUT / "c2_cv_grid.json")))
off = OUT / "official_scores.json"
scores["official"] = json.load(open(off)) if off.exists() else None
json.dump(scores, open(APP / "data/scores.json", "w"))
for p in (D / "thumbnails").glob("*.jpg"):
    im = Image.open(p).convert("RGB"); im.thumbnail((300, 300)); sq = Image.new("RGB", (300, 300), "white")
    sq.paste(im, ((300 - im.width) // 2, (300 - im.height) // 2)); sq.save(APP / "thumbs" / p.name, quality=82)
print("bundle:", sum(f.stat().st_size for f in (APP / "data").iterdir()) // 1024, "KB data,",
      sum(f.stat().st_size for f in (APP / "thumbs").iterdir()) // 1024, "KB thumbs")
