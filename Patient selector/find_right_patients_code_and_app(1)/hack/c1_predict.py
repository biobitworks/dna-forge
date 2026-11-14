"""Task C1 final: GigaPath, per-supplier mean-centred, logistic regression C=10. Fallback model for slides
GigaPath lacks: BiomedCLIP, same recipe. Writes submission + per-slide probabilities for the app."""
import csv, json, numpy as np, warnings
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from slides_common import *
warnings.filterwarnings("ignore")
OUT = Path(__file__).parent / "out"
S = manifest(); sup = {s["id"]: s["supplierId"] for s in S}

def features(model):
    V = vectors(model); ids = [s["id"] for s in S if s["id"] in V]
    X = l2(np.stack([V[i] for i in ids]))
    X = X - X.mean(0)
    for sp in set(sup.values()):
        idx = [k for k, i in enumerate(ids) if sup[i] == sp]; X[idx] -= X[idx].mean(0)
    return ids, l2(X)

def fit_predict(model):
    ids, X = features(model); pos = {i: k for k, i in enumerate(ids)}
    lab = [s for s in S if not s.get("heldout") and s.get("organGroup") and s["id"] in pos]
    tr = [pos[s["id"]] for s in lab]; y = np.array([s["organGroup"] for s in lab])
    clf = LogisticRegression(C=10, max_iter=5000, class_weight="balanced").fit(X[tr], y)
    P = clf.predict_proba(X)
    # out-of-fold probabilities for labelled slides (honest confidences in the app)
    oof = np.zeros((len(lab), len(clf.classes_)))
    for a, b in StratifiedKFold(5, shuffle=True, random_state=0).split(X[tr], y):
        m = LogisticRegression(C=10, max_iter=5000, class_weight="balanced").fit(X[tr][a], y[a])
        oof[np.ix_(b, [list(clf.classes_).index(c) for c in m.classes_])] = m.predict_proba(X[tr][b])
    P[tr] = oof
    return {i: dict(zip(clf.classes_, map(float, P[pos[i]]))) for i in ids}, float((np.array(clf.classes_)[oof.argmax(1)] == y).mean())

if __name__ == "__main__":
    prim, acc_p = fit_predict("gigapath"); fb, acc_f = fit_predict("biomedclip")
    print(f"OOF accuracy (single 5-fold) gigapath={acc_p:.3f} biomedclip={acc_f:.3f}")
    held = [s["id"] for s in S if s.get("heldout")]
    tmpl = [r["slide_id"] for r in csv.DictReader(open(D / "pack_slides/submission_template_slides_organ.csv"))]
    assert set(tmpl) == set(held), "template != held-out set"
    out = {}
    for i in [s["id"] for s in S]:
        src, p = ("gigapath", prim[i]) if i in prim else ("biomedclip", fb[i])
        top = max(p, key=p.get); out[i] = dict(pred=top, conf=p[top], model=src, probs=p)
    with open(OUT / "submission_slides_organ.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["slide_id", "organ"]); [w.writerow([i, out[i]["pred"]]) for i in tmpl]
    json.dump(out, open(OUT / "c1_predictions.json", "w"))
    from collections import Counter
    print("held-out without gigapath:", [i for i in held if i not in prim])
    print("held-out prediction mix:", Counter(out[i]["pred"] for i in held))
