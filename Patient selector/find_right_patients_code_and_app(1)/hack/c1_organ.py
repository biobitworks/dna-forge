"""Task C1: organ-group classification on slide embeddings. Compares kNN / logistic regression,
single and concatenated models, with (a) repeated stratified 5-fold CV and (b) leave-one-supplier-out CV."""
import csv, json, itertools, numpy as np, warnings
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import StratifiedKFold, LeaveOneGroupOut
from slides_common import *
warnings.filterwarnings("ignore")
OUT = Path(__file__).parent / "out"

S = manifest(); lab = [s for s in S if not s.get("heldout") and s.get("organGroup")]
held = [s for s in S if s.get("heldout")]
ids = [s["id"] for s in lab]; y = np.array([s["organGroup"] for s in lab]); g = np.array([s["supplierId"] for s in lab])

def make(kind):
    if kind.startswith("knn"):
        k = int(kind[3:]); return KNeighborsClassifier(n_neighbors=k, metric="cosine", weights="distance")
    C = float(kind.split("C")[1]); return LogisticRegression(C=C, max_iter=3000, class_weight="balanced")

def cv(X, kind, splitter, groups=None, reps=1):
    accs = []; pred_all = None
    for rep in range(reps):
        sp = StratifiedKFold(5, shuffle=True, random_state=rep) if splitter == "strat" else LeaveOneGroupOut()
        pred = np.empty(len(y), dtype=object)
        for tr, te in sp.split(X, y, groups):
            pred[te] = make(kind).fit(X[tr], y[tr]).predict(X[te])
        accs.append((pred == y).mean()); pred_all = pred
    return float(np.mean(accs)), pred_all

if __name__ == "__main__":
    kinds = ["knn1", "knn5", "knn10", "lrC0.3", "lrC1", "lrC3", "lrC10"]
    combos = [[m] for m in MODELS] + [list(c) for c in itertools.combinations(MODELS, 2)] + [["hoptimus", "biomedclip", "gigapath"], MODELS]
    res = []
    for combo in combos:
        X = matrix(ids, combo)
        for k in kinds:
            a, _ = cv(X, k, "strat", reps=5); b, _ = cv(X, k, "loso", g)
            res.append(dict(models="+".join(combo), clf=k, strat_cv=a, loso_cv=b))
            print(f"{'+'.join(combo):36s} {k:7s} strat5x5={a:.3f}  leave-supplier-out={b:.3f}")
    json.dump(res, open(OUT / "c1_cv_grid.json", "w"), indent=1)
