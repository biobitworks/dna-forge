"""Command line: python -m dnaforge <command> --root ~/dna-forge/biobase

  ingest   hash the source zips and the extracted packs into custody/ingest-<date>.json
  verify   re-hash the extracted packs against a custody manifest
  eval     leave-one-out and supplier-holdout numbers for each embedding model
  submit   write C1 and C2 CSVs from one model (or a concatenation), with a run record
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

from . import custody
from .data import MODELS, BiobaseData
from .probes import knn_predict, l2n, loo_eval, rank_similar, supplier_holdout_eval


def _features(data: BiobaseData, models: list, ids: list | None = None):
    embs = [data.embeddings(m) for m in models]
    common = [s.id for s in data.slides if all(e.slide(s.id) is not None for e in embs)]
    if ids is not None:
        common = [i for i in ids if i in set(common)]
    X = np.hstack([l2n(e.matrix(common)) for e in embs])
    return common, X


def _emb_files(data, models):
    base = data.root / "tiles/tilepack/embeddings"
    return [data.root / "slides/pack_slides/slides_manifest.json"] + [base / m / "slide-vectors.json" for m in models]


def cmd_ingest(a):
    root = Path(a.root).expanduser()
    out = Path(a.out or f"custody/ingest-{dt.date.today().isoformat()}.json")
    rec = custody.ingest([Path(z).expanduser() for z in a.zips], root, out)
    print(f"ingest {rec['id']}: {len(rec['sources'])} archives, "
          f"{sum(t['count'] for t in rec['extracted'].values())} files hashed -> {out}")


def cmd_verify(a):
    probs = custody.verify(a.manifest, Path(a.root).expanduser())
    print("intact" if not probs else "\n".join(probs))
    return 1 if probs else 0


def cmd_eval(a):
    data = BiobaseData.load(Path(a.root).expanduser())
    lab = {s.id: s for s in data.labelled}
    sets = [[m] for m in a.models] + ([a.models] if len(a.models) > 1 else [])
    with custody.RunRecord("eval", config=vars(a) | {"func": None}, inputs=_emb_files(data, a.models), runs_dir=a.runs) as run:
        for ms in sets:
            ids, X = _features(data, ms, [i for i in lab])
            y = [lab[i].organ_group for i in ids]
            r = loo_eval(X, y, k=a.k)
            r["supplier_holdout"] = supplier_holdout_eval(X, y, [lab[i].supplier for i in ids], k=a.k)
            r["n"] = len(ids)
            run.metrics["+".join(ms)] = r
            print(f"{'+'.join(ms):40s} n={len(ids)} C1={r['c1_acc']:.3f} "
                  f"P@1/5/10={r['p@1']:.2f}/{r['p@5']:.2f}/{r['p@10']:.2f} "
                  f"supplier-holdout={ {k: round(v['acc'], 2) for k, v in r['supplier_holdout'].items()} }")
    print(f"record: {run.dir/'record.json'}")


def cmd_submit(a):
    data = BiobaseData.load(Path(a.root).expanduser())
    with custody.RunRecord("submit-" + "+".join(a.models), config=vars(a) | {"func": None},
                           inputs=_emb_files(data, a.models), runs_dir=a.runs) as run:
        ids, X = _features(data, a.models)
        pos = {i: n for n, i in enumerate(ids)}
        lab = [i for i in ids if data.by_id[i].labelled]
        held = [s.id for s in data.heldout]
        missing = [h for h in held if h not in pos]
        hq = [h for h in held if h in pos]
        Q, L = X[[pos[i] for i in hq]], X[[pos[i] for i in lab]]
        pred = knn_predict(Q, L, [data.by_id[i].organ_group for i in lab], k=a.k)
        ranked = rank_similar(Q, X, hq, ids, top=10)
        organ = run.dir / "submission_slides_organ.csv"
        sim = run.dir / "submission_slides_similar.csv"
        with open(organ, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["slide_id", "organ"]); w.writerows(zip(hq, pred))
        with open(sim, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["query_slide_id", "rank", "result_slide_id"])
            for q in hq:
                w.writerows((q, r + 1, t) for r, t in enumerate(ranked[q]))
        run.output(organ); run.output(sim)
        run.metrics = {"heldout": len(held), "answered": len(hq), "missing_vectors": missing}
    print(f"wrote {organ} and {sim} ({len(hq)}/{len(held)} held-out answered); record: {run.dir/'record.json'}")


def make_folds(data: BiobaseData, n_splits: int = 5, seed: int = 0) -> dict:
    """Shared CV folds over labelled slides: StratifiedKFold(n_splits, shuffle, seed) on ids sorted.
    The file holds ids and fold numbers only, no labels."""
    from sklearn.model_selection import StratifiedKFold
    lab = sorted(data.labelled, key=lambda s: s.id)
    ids, y = [s.id for s in lab], [s.organ_group for s in lab]
    folds = {}
    for f, (_, te) in enumerate(StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(ids, y)):
        for i in te:
            folds[ids[i]] = f
    return {"scheme": "sklearn.StratifiedKFold(shuffle=True) over labelled slides sorted by id, stratified by organGroup",
            "seed": seed, "n_splits": n_splits, "count": len(folds), "folds": dict(sorted(folds.items()))}


def cmd_folds(a):
    data = BiobaseData.load(Path(a.root).expanduser())
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(make_folds(data, a.n_splits, a.seed), indent=1))
    print(f"wrote {out}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="dnaforge", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default="~/dna-forge/biobase", help="folder holding the unzipped packs")
    p.add_argument("--runs", default="runs")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("ingest"); s.add_argument("zips", nargs="+"); s.add_argument("--out"); s.set_defaults(func=cmd_ingest)
    s = sub.add_parser("folds"); s.add_argument("--out", default="custody/folds.json")
    s.add_argument("--n-splits", type=int, default=5); s.add_argument("--seed", type=int, default=0); s.set_defaults(func=cmd_folds)
    s = sub.add_parser("verify"); s.add_argument("manifest"); s.set_defaults(func=cmd_verify)
    for name, fn in (("eval", cmd_eval), ("submit", cmd_submit)):
        s = sub.add_parser(name)
        s.add_argument("--models", nargs="+", default=list(MODELS) if name == "eval" else ["gigapath"])
        s.add_argument("--k", type=int, default=1)
        s.set_defaults(func=fn)
    a = p.parse_args(argv)
    return a.func(a) or 0


if __name__ == "__main__":
    sys.exit(main())
