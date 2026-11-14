"""Task C2: top-10 similar slides. score = cosine + lam * P(query organ group == candidate organ group).
Query group probs = C1 (out-of-fold for labelled slides); candidate = one-hot true label if labelled, else C1 probs."""
import csv, json, numpy as np
from slides_common import *
from c1_predict import features
OUT = Path(__file__).parent / "out"
S = manifest(); lab = {s["id"]: s["organGroup"] for s in S if not s.get("heldout") and s.get("organGroup")}
C1 = json.load(open(OUT / "c1_predictions.json")); GROUPS = sorted({g for p in C1.values() for g in p["probs"]})

def emb(kind):
    if kind == "centred": return features("gigapath")
    V = vectors("gigapath"); ids = [s["id"] for s in S if s["id"] in V]; return ids, l2(np.stack([V[i] for i in ids]))

def probvec(i, as_candidate):
    if as_candidate and i in lab: return np.array([g == lab[i] for g in GROUPS], float)
    return np.array([C1[i]["probs"].get(g, 0.0) for g in GROUPS])

def rank(ids, X, lam):
    Sim = X @ X.T; Pq = np.stack([probvec(i, False) for i in ids]); Pc = np.stack([probvec(i, True) for i in ids])
    Sc = Sim + lam * (Pq @ Pc.T); np.fill_diagonal(Sc, -np.inf); return Sc

def evaluate(ids, Sc):
    li = [k for k, i in enumerate(ids) if i in lab]; lid = np.array(li)
    res = {1: [], 5: [], 10: []}
    for q in li:
        order = lid[np.argsort(-Sc[q, lid])]; order = order[order != q]
        hits = np.array([lab[ids[o]] == lab[ids[q]] for o in order[:10]])
        for k in res: res[k].append(hits[:k].mean())
    return {k: float(np.mean(v)) for k, v in res.items()}

if __name__ == "__main__":
    grid = []
    for kind in ["raw", "centred"]:
        ids, X = emb(kind)
        for lam in [0, 0.1, 0.25, 0.5, 1.0]:
            r = evaluate(ids, rank(ids, X, lam)); grid.append(dict(emb=kind, lam=lam, **{f"p@{k}": v for k, v in r.items()}))
            print(f"{kind:8s} lam={lam:<4} P@1={r[1]:.3f} P@5={r[5]:.3f} P@10={r[10]:.3f}")
    json.dump(grid, open(OUT / "c2_cv_grid.json", "w"), indent=1)

def write_submission(lam=1.0, kind="centred"):
    ids, X = emb(kind); Sc = rank(ids, X, lam); Sim = X @ X.T; pos = {i: k for k, i in enumerate(ids)}
    held = [s["id"] for s in S if s.get("heldout")]
    rows, nn = [], {}
    for i in ids:
        q = pos[i]; order = [o for o in np.argsort(-Sc[q]) if o != q][:10]
        nn[i] = [dict(id=ids[o], cos=float(Sim[q, o]), score=float(Sc[q, o])) for o in order]
    for i in held:
        rows += [(i, r + 1, n["id"]) for r, n in enumerate(nn[i])]
    with open(OUT / "submission_slides_similar.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["query_slide_id", "rank", "result_slide_id"]); w.writerows(rows)
    json.dump(nn, open(OUT / "c2_neighbours.json", "w"))
    return rows

if __name__ == "__main__":
    rows = write_submission()
    print("C2 rows:", len(rows), "queries:", len({r[0] for r in rows}), "self-hits:", sum(r[0] == r[2] for r in rows))
