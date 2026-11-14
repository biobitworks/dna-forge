import numpy as np, warnings, json
from c1_organ import *
warnings.filterwarnings("ignore")
allids = [s["id"] for s in S]; sup_all = {s["id"]: s["supplierId"] for s in S}
def centred(models):
    Xa = matrix(allids, models)       # centre per supplier using all 263 slides (no labels used)
    for sp in set(sup_all.values()):
        idx = [i for i, a in enumerate(allids) if sup_all[a] == sp]
        Xa[idx] -= Xa[idx].mean(0)
    Xa = l2(Xa); pos = {a: i for i, a in enumerate(allids)}
    return Xa[[pos[i] for i in ids]]
s02 = g == "SUPP-02"
for combo in [["gigapath"], ["biomedclip", "gigapath"], ["hoptimus", "gigapath"], ["hoptimus", "biomedclip", "gigapath"]]:
    for cen in [False, True]:
        X = centred(combo) if cen else matrix(ids, combo)
        for k in ["knn1", "knn3", "lrC10", "lrC30", "lrC100"]:
            accs = []; acc02 = []
            for rep in range(5):
                a, p = cv(X, k, "strat", reps=1) if rep == 0 else (None, None)
                sp = StratifiedKFold(5, shuffle=True, random_state=rep); pred = np.empty(len(y), dtype=object)
                for tr, te in sp.split(X, y): pred[te] = make(k).fit(X[tr], y[tr]).predict(X[te])
                accs.append((pred == y).mean()); acc02.append((pred[s02] == y[s02]).mean())
            b, _ = cv(X, k, "loso", g)
            print(f"{'+'.join(combo):30s} centred={cen!s:5s} {k:6s} strat={np.mean(accs):.3f}±{np.std(accs):.3f} SUPP-02={np.mean(acc02):.3f} loso={b:.3f}")
