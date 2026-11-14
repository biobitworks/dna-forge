"""Leave-one-module-out ablation: drop one component at a time from a full pipeline, re-score with
5-fold stratified CV on labelled slides (3 fold seeds; seed 0 = the shared custody folds), and record
every variant in one custody run record so we can see what each module contributes.

Modules ablated
  embeddings  gigapath, hoptimus, biomedclip, dinov2 (dropped from every block of the full model)
  members     each ensemble member of the full model
  classifier  SVM -> logistic regression
  c2          class-agreement term (alpha 3 -> 0) and embedding term (C2 by class agreement only)
  add-ons     supplier centring (~sc), tile pooling meanmax, are tried as additions ("+module")

  python3 scripts/ablate.py [--root ~/dna-forge/biobase] [--seeds 0,1,2] [--base full|ens-svm]
"""
import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.simplefilter("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dnaforge import custody, models as M  # noqa: E402
from dnaforge.data import BiobaseData  # noqa: E402

EMB = ["gigapath", "hoptimus", "biomedclip", "dinov2"]
SVM = {"Creg": 0.01}
BASES = {
    # current submission
    "ens-svm": [(["gigapath"], None, "svm", SVM, 1.0), (["gigapath", "hoptimus"], None, "svm", SVM, 1.0)],
    # everything in: the submission plus an all-four-embeddings member
    "full": [(["gigapath"], None, "svm", SVM, 1.0), (["gigapath", "hoptimus"], None, "svm", SVM, 1.0),
             (EMB, [2, 1, 1, 0.5], "svm", SVM, 1.0)],
}
ALPHA = 3.0


def base_model(spec: str) -> str:
    return spec.split("@")[0].split("~")[0]


def drop_embedding(members, emb):
    out = []
    for specs, w, clf, kw, ew in members:
        keep = [(s, (w[i] if w else None)) for i, s in enumerate(specs) if base_model(s) != emb]
        if not keep:
            continue
        ss = [s for s, _ in keep]
        ww = [x for _, x in keep] if w else None
        if (ss, ww) not in [(o[0], o[1]) for o in out]:
            out.append((ss, ww, clf, kw, ew))
    return out


def variants(base):
    v = {"FULL": (base, ALPHA, None)}
    for e in EMB:
        if any(base_model(s) == e for m in base for s in m[0]):
            v[f"-emb:{e}"] = (drop_embedding(base, e), ALPHA, "hoptimus" if e == "gigapath" else None)
    if len(base) > 1:
        for j, m in enumerate(base):
            v[f"-member:{'+'.join(m[0])}"] = (base[:j] + base[j + 1:], ALPHA, None)
    v["-clf:svm->lr"] = ([(s, w, "lr", {"Creg": 0.1}, ew) for s, w, _, _, ew in base], ALPHA, None)
    v["-c2:class-agreement"] = (base, 0.0, None)
    v["-c2:embedding"] = (base, 1000.0, None)
    v["+sc"] = ([([s + "~sc" for s in ss], w, c, k, ew) for ss, w, c, k, ew in base], ALPHA, None)
    v["+hoptimus@meanmax"] = (base + [(["hoptimus@meanmax"], None, "lr", {"Creg": 0.1}, 1.0)], ALPHA, None)
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="~/dna-forge/biobase")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--base", default="full", choices=list(BASES))
    ap.add_argument("--runs", default="runs")
    a = ap.parse_args()
    root = Path(a.root).expanduser()
    data = BiobaseData.load(root)
    classes = data.organ_groups
    C = len(classes)
    lab = sorted(s.id for s in data.labelled)
    y = np.array([classes.index(data.by_id[i].organ_group) for i in lab])
    seeds = [int(s) for s in a.seeds.split(",")]
    foldsets = [M.stratified_folds(lab, list(y), 5, s) for s in seeds]
    emb_dir = root / "tiles/tilepack/embeddings"
    inputs = [root / "slides/pack_slides/slides_manifest.json"] + \
             [p for e in EMB for p in (emb_dir / e / "slide-vectors.json", emb_dir / e / "tile-vectors.i8")
              if p.exists()]
    vs = variants(BASES[a.base])
    cfg = {"base": a.base, "seeds": seeds, "alpha": ALPHA,
           "variants": {k: {"members": m, "alpha": al, "c2_space": c2 or "gigapath"} for k, (m, al, c2) in vs.items()}}
    feats, cache = {}, {}
    M.ensure_features(data, [(["gigapath"], None, None, None, None)], feats, cache)
    with custody.RunRecord(f"ablate-{a.base}", config=cfg, inputs=inputs, runs_dir=a.runs) as run:
        res = {}
        for name, (members, alpha, c2) in vs.items():
            t = time.time()
            M.ensure_features(data, members, feats, cache)
            if c2:  # C2 embedding space must not use the dropped model either
                M.ensure_features(data, [([c2], None, None, None, None)], feats, cache)
            rs = [M.cv_eval(members, feats, lab, y, C, f, alpha=alpha, c2_space=c2) for f in foldsets]
            m = {k: float(np.mean([r[k] for r in rs])) for k in ("c1_acc", "p@1", "p@5", "p@10")}
            m["c1_sd"] = float(np.std([r["c1_acc"] for r in rs]))
            m["c1_seed0"] = float(rs[0]["c1_acc"])
            res[name] = m
            print(f"{name:34s} C1={m['c1_acc']:.3f}±{m['c1_sd']:.3f}  P@1/5/10={m['p@1']:.3f}/{m['p@5']:.3f}/{m['p@10']:.3f}"
                  f"  ({time.time() - t:.0f}s)", flush=True)
        full = res["FULL"]
        for name, m in res.items():
            m["delta"] = {k: round(m[k] - full[k], 4) for k in ("c1_acc", "p@1", "p@5", "p@10")}
        run.metrics = res
        print("\nimpact when removed / added (negative = module helps):")
        for name, m in sorted(res.items(), key=lambda kv: kv[1]["delta"]["c1_acc"]):
            if name != "FULL":
                d = m["delta"]
                print(f"  {name:34s} dC1={d['c1_acc']:+.3f} dP@1={d['p@1']:+.3f} dP@5={d['p@5']:+.3f} dP@10={d['p@10']:+.3f}")
    print(f"record: {run.dir / 'record.json'}")


if __name__ == "__main__":
    main()
