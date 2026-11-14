"""Sweep slide-model variants with 5-fold stratified CV (3 fold seeds) on labelled slides only.
python3 scripts/sweep.py [--root ~/dna-forge/biobase] [--only name,name]"""
import argparse, json, sys, time, warnings
warnings.simplefilter("ignore")
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dnaforge.data import BiobaseData
from dnaforge import models as M

G, A4 = M.GIGA, M.ALL4
V = {
    "giga-1nn": [(G, None, "wknn", {"k": 1}, 1)],
    "giga-wknn3": [(G, None, "wknn", {"k": 3, "power": 4}, 1)],
    "giga-wknn5": [(G, None, "wknn", {"k": 5, "power": 4}, 1)],
    "giga-wknn7": [(G, None, "wknn", {"k": 7, "power": 4}, 1)],
    "giga-wknn5-p1": [(G, None, "wknn", {"k": 5, "power": 1}, 1)],
    "giga-lr-C.01": [(G, None, "lr", {"Creg": 0.01}, 1)],
    "giga-lr-C.1": [(G, None, "lr", {"Creg": 0.1}, 1)],
    "giga-lr-C1": [(G, None, "lr", {"Creg": 1.0}, 1)],
    "giga-svm-C.01": [(G, None, "svm", {"Creg": 0.01}, 1)],
    "giga-ldaknn": [(G, None, "ldaknn", {"k": 5}, 1)],
    "giga-sc-1nn": [(["gigapath~sc"], None, "wknn", {"k": 1}, 1)],
    "giga-sc-lr-C.1": [(["gigapath~sc"], None, "lr", {"Creg": 0.1}, 1)],
    "hopt-lr-C.1": [(["hoptimus"], None, "lr", {"Creg": 0.1}, 1)],
    "hopt-meanmax-lr": [(["hoptimus@meanmax"], None, "lr", {"Creg": 0.1}, 1)],
    "hopt-topk-1nn": [(["hoptimus@topk"], None, "wknn", {"k": 1}, 1)],
    "bclip-meanmax-lr": [(["biomedclip@meanmax"], None, "lr", {"Creg": 0.1}, 1)],
    "dino-meanmax-lr": [(["dinov2@meanmax"], None, "lr", {"Creg": 0.1}, 1)],
    "all4-1nn": [(A4, None, "wknn", {"k": 1}, 1)],
    "all4w-lr-C.1": [(A4, [2, 1, 1, 0.5], "lr", {"Creg": 0.1}, 1)],
    "all4w-lr-C.01": [(A4, [2, 1, 1, 0.5], "lr", {"Creg": 0.01}, 1)],
    "giga+hopt-lr": [(["gigapath", "hoptimus"], None, "lr", {"Creg": 0.1}, 1)],
    "giga+hoptmm-lr": [(["gigapath", "hoptimus@meanmax"], [2, 1], "lr", {"Creg": 0.1}, 1)],
    "all4w-sc-lr": [(["gigapath~sc", "hoptimus~sc", "biomedclip~sc", "dinov2~sc"], [2, 1, 1, 0.5], "lr", {"Creg": 0.1}, 1)],
    "ens-lr+wknn": [(G, None, "lr", {"Creg": 0.1}, 1), (G, None, "wknn", {"k": 5, "power": 4}, 1)],
    "ens-lr-models": [(G, None, "lr", {"Creg": 0.1}, 2), (["hoptimus@meanmax"], None, "lr", {"Creg": 0.1}, 1),
                      (["biomedclip@meanmax"], None, "lr", {"Creg": 0.1}, 1)],
    "ens-big": [(G, None, "lr", {"Creg": 0.1}, 2), (G, None, "wknn", {"k": 5, "power": 4}, 1),
                (A4, [2, 1, 1, 0.5], "lr", {"Creg": 0.1}, 1), (["hoptimus@meanmax"], None, "lr", {"Creg": 0.1}, 1)],
    # round 2
    "giga-svm-C.001": [(G, None, "svm", {"Creg": 0.001}, 1)],
    "giga-svm-C.1": [(G, None, "svm", {"Creg": 0.1}, 1)],
    "giga+hopt-svm": [(["gigapath", "hoptimus"], None, "svm", {"Creg": 0.01}, 1)],
    "giga+hopt-w2-svm": [(["gigapath", "hoptimus"], [2, 1], "svm", {"Creg": 0.01}, 1)],
    "all4w-svm": [(A4, [2, 1, 1, 0.5], "svm", {"Creg": 0.01}, 1)],
    "giga-sc-svm": [(["gigapath~sc"], None, "svm", {"Creg": 0.01}, 1)],
    "ens-svm+lr+lda": [(G, None, "svm", {"Creg": 0.01}, 1), (G, None, "lr", {"Creg": 0.1}, 1),
                       (G, None, "ldaknn", {"k": 5}, 1)],
    "ens-svm+gh-lr": [(G, None, "svm", {"Creg": 0.01}, 1), (["gigapath", "hoptimus"], None, "lr", {"Creg": 0.1}, 1)],
    "ens-svm+gh-svm": [(G, None, "svm", {"Creg": 0.01}, 1), (["gigapath", "hoptimus"], [2, 1], "svm", {"Creg": 0.01}, 1)],
}

ap = argparse.ArgumentParser()
ap.add_argument("--root", default="~/dna-forge/biobase")
ap.add_argument("--only", default="")
ap.add_argument("--seeds", default="0,1,2")
ap.add_argument("--out", default="runs/sweep.json")
a = ap.parse_args()
data = BiobaseData.load(Path(a.root).expanduser())
classes = data.organ_groups
C = len(classes)
lab = sorted(s.id for s in data.labelled)
y = np.array([classes.index(data.by_id[i].organ_group) for i in lab])
seeds = [int(s) for s in a.seeds.split(",")]
foldsets = [M.stratified_folds(lab, list(y), 5, s) for s in seeds]
feats, cache = {}, {}
M.ensure_features(data, [(G, None, None, None, None)], feats, cache)
names = [n for n in V if not a.only or n in a.only.split(",")]
res = {}
for n in names:
    t = time.time()
    M.ensure_features(data, V[n], feats, cache)
    rs = [M.cv_eval(V[n], feats, lab, y, C, f, alpha=[1.0, 0.0, 0.3, 3.0, 10.0]) for f in foldsets]
    m = {k: float(np.mean([r[k] for r in rs])) for k in ("c1_acc", "p@1", "p@5", "p@10")}
    m["c1_sd"] = float(np.std([r["c1_acc"] for r in rs]))
    for al in (0.0, 0.3, 3.0, 10.0):
        m[f"a{al}_p@1/5/10"] = [round(float(np.mean([r["by_alpha"][al][k] for r in rs])), 3) for k in ("p@1", "p@5", "p@10")]
    res[n] = m
    print(f"{n:20s} C1={m['c1_acc']:.3f}±{m['c1_sd']:.3f} P@1/5/10(cos+class)={m['p@1']:.3f}/{m['p@5']:.3f}/{m['p@10']:.3f}"
          f"  a0={m['a0.0_p@1/5/10']} a.3={m['a0.3_p@1/5/10']} a3={m['a3.0_p@1/5/10']} a10={m['a10.0_p@1/5/10']}  {time.time()-t:.0f}s", flush=True)
Path(a.out).parent.mkdir(exist_ok=True)
Path(a.out).write_text(json.dumps(res, indent=1))
