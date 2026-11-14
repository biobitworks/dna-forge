"""Command line: python -m dnaforge <command> --root ~/dna-forge/biobase

  ingest   hash the source zips and the extracted packs into custody/ingest-<date>.json
  verify   re-hash the extracted packs against a custody manifest
  eval     leave-one-out and supplier-holdout numbers for each embedding model
  submit   write C1 and C2 CSVs from one model (or a concatenation), with a run record;
           --method <name> uses a dnaforge.models method (see `models.METHODS`) and also writes
           oof_organ.csv / heldout_organ.csv / heldout_similar.csv for stacking
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


def _feature_inputs(data, raw_specs, extra=()):
    """Every file a set of feature specs reads: slide vectors for each model, plus tile vectors and
    tile metadata for pooled specs (model@pool), plus the manifest and any extra files."""
    base = data.root / "tiles/tilepack/embeddings"
    files = {data.root / "slides/pack_slides/slides_manifest.json"}
    for spec in raw_specs:
        model, _, pool = spec.replace("~sc", "").partition("@")
        files.add(base / model / "slide-vectors.json")
        if pool and pool != "slide":
            files |= {base / model / "tile-vectors.i8", base / model / "tile-meta.json"}
    files |= {Path(x) for x in extra}
    return sorted(files)


def cmd_ingest(a):
    root = Path(a.root).expanduser()
    out = Path(a.out or f"custody/ingest-{dt.date.today().isoformat()}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
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
    if a.method:
        return cmd_submit_method(a)
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
    """Folds go to custody/local/folds.json (gitignored, has slide ids); custody/folds.sha256 (committed)
    lets every node prove it uses the same folds. Regenerate anywhere with the same seed."""
    import hashlib
    data = BiobaseData.load(Path(a.root).expanduser())
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(make_folds(data, a.n_splits, a.seed), indent=1, sort_keys=True)
    out.write_text(text)
    digest = hashlib.sha256(text.encode()).hexdigest()
    Path(a.hash_out).write_text(f"{digest}  folds.json (n_splits={a.n_splits}, seed={a.seed})\n")
    print(f"wrote {out} (sha256 {digest}) and {a.hash_out}")


def _load_folds(path: Path, lab_ids: list, y: list) -> tuple:
    from . import models as M
    if path.exists():
        f = json.loads(path.read_text())["folds"]
        if all(i in f for i in lab_ids):
            return {i: int(f[i]) for i in lab_ids}, str(path)
    return M.stratified_folds(lab_ids, y, 5, 0), "StratifiedKFold(5, shuffle=True, random_state=0) over sorted labelled ids"


def cmd_submit_method(a):
    import socket
    from . import models as M
    data = BiobaseData.load(Path(a.root).expanduser())
    classes = data.organ_groups
    C = len(classes)
    method = M.METHODS[a.method]
    specs = sorted({s.split("@")[0].replace("~sc", "") for m in method for s in m[0]} | {"hoptimus"})
    all_ids = [s.id for s in data.slides]
    lab = sorted(s.id for s in data.labelled)
    y = np.array([classes.index(data.by_id[i].organ_group) for i in lab])
    rest = [i for i in all_ids if i not in set(lab)]          # held-out + unlabelled non-held-out
    held = [s.id for s in data.heldout]
    cfg = {"method": a.method, "members": method, "alpha": a.alpha, "c2_space": a.c2_space, "classes": classes}
    raw_specs = [sp for m in method for sp in m[0]] + [a.c2_space, "hoptimus"]
    inputs = _feature_inputs(data, raw_specs, extra=[a.folds] if Path(a.folds).exists() else [])
    with custody.RunRecord("submit-" + a.method, config=cfg, inputs=inputs, runs_dir=a.runs) as run:
        folds, fold_src = _load_folds(Path(a.folds), lab, list(y))
        feats = M.ensure_features(data, method, {})
        M.ensure_features(data, [([a.c2_space], None, None, None, None)], feats)
        cv = M.cv_eval(method, feats, lab, y, C, folds, alpha=a.alpha, c2_space=a.c2_space)
        P_rest = M.fit_predict(method, feats, lab, y, rest, C)
        prob = dict(zip(rest, P_rest))
        pred = {i: classes[int(prob[i].argmax())] for i in held}
        # C2: every other slide is a candidate; labelled ones carry their one-hot label
        cand_P = np.vstack([M._onehot(y, C), P_rest])
        cx_ids, CX = feats[M.feature_key([a.c2_space])]
        ranked = M.rank_c2(CX, cx_ids, held, lab + rest, cand_P, np.vstack([prob[i] for i in held]),
                           alpha=a.alpha, top=50, return_scores=True)
        d = run.dir
        hdr = ["slide_id", "fold"] + classes
        with open(d / "oof_organ.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(hdr)
            w.writerows([i, folds[i]] + [f"{v:.6f}" for v in row] for i, row in zip(lab, cv["P"]))
        with open(d / "heldout_organ.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(hdr)
            w.writerows([i, -1] + [f"{v:.6f}" for v in prob[i]] for i in held)
        with open(d / "heldout_similar.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["query_slide_id", "result_slide_id", "score"])
            for q in held:
                w.writerows((q, t, f"{sc:.6f}") for t, sc in ranked[q])
        with open(d / "submission_slides_organ.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["slide_id", "organ"]); w.writerows((i, pred[i]) for i in held)
        with open(d / "submission_slides_similar.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["query_slide_id", "rank", "result_slide_id"])
            for q in held:
                w.writerows((q, r + 1, t) for r, (t, _) in enumerate(ranked[q][:10]))
        for n in ("oof_organ.csv", "heldout_organ.csv", "heldout_similar.csv",
                  "submission_slides_organ.csv", "submission_slides_similar.csv"):
            run.output(d / n)
        run.metrics = {"oof_acc": cv["c1_acc"], "oof_p@1": cv["p@1"], "oof_p@5": cv["p@5"], "oof_p@10": cv["p@10"],
                       "node": socket.gethostname(), "folds": fold_src, "n_labelled": len(lab),
                       "heldout": len(held), "answered": len(held)}
    print(f"{a.method}: OOF C1={cv['c1_acc']:.3f} P@1/5/10={cv['p@1']:.3f}/{cv['p@5']:.3f}/{cv['p@10']:.3f}; "
          f"wrote {run.dir}; record: {run.dir/'record.json'}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="dnaforge", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default="~/dna-forge/biobase", help="folder holding the unzipped packs")
    p.add_argument("--runs", default="runs")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("ingest"); s.add_argument("zips", nargs="+"); s.add_argument("--out"); s.set_defaults(func=cmd_ingest)
    s = sub.add_parser("folds"); s.add_argument("--out", default="custody/local/folds.json"); s.add_argument("--hash-out", default="custody/folds.sha256")
    s.add_argument("--n-splits", type=int, default=5); s.add_argument("--seed", type=int, default=0); s.set_defaults(func=cmd_folds)
    s = sub.add_parser("verify"); s.add_argument("manifest"); s.set_defaults(func=cmd_verify)
    for name, fn in (("eval", cmd_eval), ("submit", cmd_submit)):
        s = sub.add_parser(name)
        s.add_argument("--models", nargs="+", default=list(MODELS) if name == "eval" else ["gigapath"])
        s.add_argument("--k", type=int, default=1)
        if name == "submit":
            s.add_argument("--method", help="a dnaforge.models.METHODS name (overrides --models/--k)")
            s.add_argument("--alpha", type=float, default=3.0, help="C2 weight on organ-group agreement")
            s.add_argument("--c2-space", dest="c2_space", default="gigapath", help="embedding for C2 cosine")
            s.add_argument("--folds", default="custody/local/folds.json")
        s.set_defaults(func=fn)
    a = p.parse_args(argv)
    return a.func(a) or 0


if __name__ == "__main__":
    sys.exit(main())
