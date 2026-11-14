"""Tile-level kNN voting (fold seed 0) and supplier-holdout accuracy for a few methods.
Labelled slides only."""
import sys, warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dnaforge.data import BiobaseData
from dnaforge import models as M
from dnaforge.probes import l2n

data = BiobaseData.load(Path("~/dna-forge/biobase").expanduser())
classes = data.organ_groups; C = len(classes)
lab = sorted(s.id for s in data.labelled)
y = np.array([classes.index(data.by_id[i].organ_group) for i in lab])
folds = M.stratified_folds(lab, list(y), 5, 0)

for model in sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] else ["hoptimus"]:
    e = data.embeddings(model, tiles=True)
    T = {i: l2n(e.tiles(i)) for i in lab}
    P = np.zeros((len(lab), C))
    for f in range(5):
        te = [i for i in lab if folds[i] == f]; tr = [i for i in lab if folds[i] != f]
        Pt = M.tile_vote_proba(T, tr, np.array([y[lab.index(i)] for i in tr]), te, C)
        for i, r in zip(te, Pt):
            P[lab.index(i)] = r
    print(f"tile-vote {model}: C1={np.mean(P.argmax(1) == y):.3f}", flush=True)

sup = [data.by_id[i].supplier for i in lab]
for name in sys.argv[2].split(",") if len(sys.argv) > 2 else []:
    meth = M.METHODS[name]
    feats = M.ensure_features(data, meth, {})
    out = {}
    for s in sorted(set(sup)):
        te = [i for i, v in zip(lab, sup) if v == s]; tr = [i for i, v in zip(lab, sup) if v != s]
        Pt = M.fit_predict(meth, feats, tr, np.array([y[lab.index(i)] for i in tr]), te, C)
        out[s] = (len(te), round(float(np.mean(Pt.argmax(1) == np.array([y[lab.index(i)] for i in te]))), 3))
    print(f"supplier-holdout {name}: {out}", flush=True)
