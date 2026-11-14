"""Ensemble stacker: combine contributed small models into one prediction.

  python -m dnaforge.stack --root ~/dna-forge/biobase run_dir_1 run_dir_2 ...

Level-2 model: multinomial logistic regression on the concatenated out-of-fold probabilities,
scored by cross-validation over the same shared folds (a second-level OOF, so the reported number
is not optimistic). Also reports each input's OOF accuracy and the plain probability average.
C2 ranking: cosine similarity of the stacked probability vectors blended with GigaPath similarity.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from . import custody
from .contrib import load_folds, read_predictions
from .data import BiobaseData
from .probes import l2n, precision_at


def stack(run_dirs: list, labels: dict, folds: dict, C: float = 1.0):
    from sklearn.linear_model import LogisticRegression
    inputs = []
    groups = None
    for d in run_dirs:
        g, oof = read_predictions(Path(d) / "oof_organ.csv")
        _, held = read_predictions(Path(d) / "heldout_organ.csv")
        if groups is None:
            groups = g
        assert g == groups, f"{d}: organ group columns differ"
        inputs.append((Path(d).name, oof, held))
    ids = sorted(s for s in labels if all(s in o for _, o, _ in inputs))
    held_ids = sorted(set.intersection(*[set(h) for _, _, h in inputs]))
    y = np.array([labels[s] for s in ids])
    X = np.hstack([np.stack([o[s][1] for s in ids]) for _, o, _ in inputs])
    H = np.hstack([np.stack([h[s][1] for s in held_ids]) for _, _, h in inputs])
    f = np.array([folds[s] for s in ids])
    report = {}
    for name, o, _ in inputs:
        P = np.stack([o[s][1] for s in ids])
        report[name] = float(np.mean(np.array(groups)[P.argmax(1)] == y))
    avg = X.reshape(len(ids), len(inputs), len(groups)).mean(1)
    report["average"] = float(np.mean(np.array(groups)[avg.argmax(1)] == y))
    oof2 = np.zeros((len(ids), len(groups)))
    for k in sorted(set(f)):
        tr, te = f != k, f == k
        m = LogisticRegression(C=C, max_iter=5000).fit(X[tr], y[tr])
        oof2[np.ix_(te, [groups.index(c) for c in m.classes_])] = m.predict_proba(X[te])
    # Optimistic: the base models' OOF columns for rows outside fold k came from models that saw fold k's
    # labels, so this second-level CV leaks. An unbiased number needs base models retrained in an outer
    # split; until then the stack is only chosen when it beats every single input AND the average.
    report["stacked_lr"] = float(np.mean(np.array(groups)[oof2.argmax(1)] == y))
    report["stacked_lr_estimate"] = "optimistic (shared folds, no outer split)"
    final = LogisticRegression(C=C, max_iter=5000).fit(X, y)
    Ph = np.zeros((len(held_ids), len(groups)))
    Ph[:, [groups.index(c) for c in final.classes_]] = final.predict_proba(H)
    Hav = H.reshape(len(held_ids), len(inputs), len(groups)).mean(1)
    best_single = max(report[n] for n, _, _ in inputs)
    use_stack = report["stacked_lr"] > max(report["average"], best_single)
    return {"groups": groups, "ids": ids, "held_ids": held_ids, "oof": oof2 if use_stack else avg,
            "held": Ph if use_stack else Hav, "method": "stacked_lr" if use_stack else "average", "report": report}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("runs_in", nargs="+")
    p.add_argument("--root", default="~/dna-forge/biobase")
    p.add_argument("--folds", default="custody/local/folds.json")
    p.add_argument("--runs", default="runs")
    p.add_argument("--sim-model", default="gigapath")
    p.add_argument("--alpha", type=float, default=0.5, help="weight of probability similarity vs embedding similarity in C2")
    a = p.parse_args(argv)
    data = BiobaseData.load(Path(a.root).expanduser())
    labels = {s.id: s.organ_group for s in data.labelled}
    folds = load_folds(a.folds)
    inputs = [Path(r) / n for r in a.runs_in for n in ("oof_organ.csv", "heldout_organ.csv", "record.json") if (Path(r) / n).exists()]
    with custody.RunRecord("ensemble-stack", config=vars(a), inputs=inputs + [Path(a.folds)], runs_dir=a.runs) as run:
        r = stack(a.runs_in, labels, folds)
        G = np.array(r["groups"])
        run.metrics = {"oof_acc": r["report"], "method": r["method"], "n_inputs": len(a.runs_in)}
        # C1
        organ = run.dir / "submission_slides_organ.csv"
        with open(organ, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["slide_id", "organ"])
            w.writerows(zip(r["held_ids"], G[r["held"].argmax(1)]))
        # C2: blend probability-vector similarity with embedding similarity over the whole pool
        emb = data.embeddings(a.sim_model)
        prob = {**dict(zip(r["ids"], r["oof"])), **dict(zip(r["held_ids"], r["held"]))}
        pool = [s for s in prob if emb.slide(s) is not None]
        E = l2n(emb.matrix(pool)); P = l2n(np.stack([prob[s] for s in pool]))
        S = a.alpha * (P @ P.T) + (1 - a.alpha) * (E @ E.T)
        idx = {s: i for i, s in enumerate(pool)}
        sim = run.dir / "submission_slides_similar.csv"
        ranked = {}
        with open(sim, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["query_slide_id", "rank", "result_slide_id"])
            for q in r["held_ids"]:
                if q not in idx:
                    continue
                order = [pool[j] for j in np.argsort(-S[idx[q]]) if pool[j] != q][:10]
                ranked[q] = order
                w.writerows((q, k + 1, t) for k, t in enumerate(order))
        # labelled-only C2 estimate with the same blend (queries = labelled slides)
        lab_ranked = {q: [pool[j] for j in np.argsort(-S[idx[q]]) if pool[j] != q][:10] for q in r["ids"] if q in idx}
        run.metrics["c2_labelled_estimate"] = precision_at(lab_ranked, labels)
        run.output(organ); run.output(sim)
    print(f"{r['method']}: {r['report']}  C2 est {run.metrics['c2_labelled_estimate']}\n-> {run.dir}")


if __name__ == "__main__":
    main()
