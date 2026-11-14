"""Symptom-based endometriosis prediction (enrichment node, not a Biobase task).

Following the approach of self-report symptom ML (PMC10073113): tabular features, several standard
classifiers, stratified 5-fold CV, AUC / accuracy / sensitivity / specificity.

  python -m dnaforge.endo --csv ~/dna-forge/enrichment/kaggle-endometriosis/structured_endometriosis_data.csv
"""
from __future__ import annotations

import argparse
import csv
import socket
from pathlib import Path

import numpy as np

from . import custody


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    cols = [c for c in rows[0] if c != "Diagnosis"]
    X = np.array([[float(r[c]) for c in cols] for r in rows])
    y = np.array([int(float(r["Diagnosis"])) for r in rows])
    return cols, X, y


def evaluate(X, y, seed=0):
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    models = {
        "logreg": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=seed, n_jobs=-1),
        "grad_boost": GradientBoostingClassifier(random_state=seed),
    }
    cv = StratifiedKFold(5, shuffle=True, random_state=seed)
    out = {}
    for name, m in models.items():
        p = cross_val_predict(m, X, y, cv=cv, method="predict_proba")[:, 1]
        pred = (p >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
        out[name] = {"auc": float(roc_auc_score(y, p)), "acc": float(accuracy_score(y, pred)),
                     "sensitivity": float(tp / (tp + fn)), "specificity": float(tn / (tn + fp))}
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", required=True)
    p.add_argument("--runs", default="runs")
    a = p.parse_args(argv)
    path = Path(a.csv).expanduser()
    with custody.RunRecord("endo-symptoms", config={"csv": path.name}, inputs=[path], runs_dir=a.runs) as run:
        cols, X, y = load(path)
        run.metrics = {"node": socket.gethostname(), "n": int(len(y)), "prevalence": float(y.mean()),
                       "features": cols, "cv5": evaluate(X, y)}
    for k, v in run.metrics["cv5"].items():
        print(f"{k:14s} AUC={v['auc']:.3f} acc={v['acc']:.3f} sens={v['sensitivity']:.3f} spec={v['specificity']:.3f}")
    print(f"n={run.metrics['n']} prevalence={run.metrics['prevalence']:.3f} -> {run.dir}")


if __name__ == "__main__":
    main()
