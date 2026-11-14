"""Static, self-contained HTML fallback of the demo (no server): out/static_demo.html."""
import base64, json
from pathlib import Path
H = Path(__file__).parent; A = H / "app"; D = A / "data"
rep = json.load(open(D / "reports.json")); ce = json.load(open(D / "criteria_evidence.json"))
slides = json.load(open(D / "slides.json")); bridge = json.load(open(D / "bridge.json")); sc = json.load(open(D / "scores.json"))
test = {i: dict(t=r["report_text"], o=r["organ"]) for i, r in rep.items() if r["split"] == "test"}
crit = ce["criteria"]; evt = ce["evidence"]["test"]; trcount = {c: len(v) for c, v in ce["evidence"]["train"].items()}
thumbs = {s["id"]: "data:image/jpeg;base64," + base64.b64encode(open(A / "thumbs" / f"{s['id']}.jpg", "rb").read()).decode() for s in slides}
sl = [dict(id=s["id"], sup=s["supplierId"], g=s.get("organGroup"), h=s["heldout"], p=s["c1"]["pred"], c=round(s["c1"]["conf"], 3),
           top=sorted(s["c1"]["probs"].items(), key=lambda x: -x[1])[:5], nn=[[n["id"], round(n["cos"], 3)] for n in s["neighbours"]], r=s.get("report")) for s in slides]
br = {c: dict(seeds={k: v["status"] for k, v in b["seeds"].items()}, sug=[[k, v["group_source"], round(v["score"], 2), v["heldout"]] for k, v in b["suggestions"].items()][:10]) for c, b in bridge.items()}
f1 = {c: [round(sc["A"]["train_scores"][c]["f1"], 3), round(sc["A_baseline"]["scores"][c]["f1"], 3)] for c in trcount}
blob = json.dumps(dict(test=test, crit=crit, ev=evt, trc=trcount, slides=sl, thumbs=thumbs, bridge=br, f1=f1)).replace("</", "<\\/")
html = (A.parent / "static_template.html").read_text().replace("/*DATA*/null", blob)
(H / "out/static_demo.html").write_text(html); print("wrote out/static_demo.html", len(html) // 1024, "KB")
