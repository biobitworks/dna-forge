"""Slide-level models on top of frozen embeddings, and the C1/C2 metrics."""
from __future__ import annotations

from collections import Counter
from typing import Optional

import numpy as np


def l2n(X: np.ndarray) -> np.ndarray:
    return X / np.clip(np.linalg.norm(X, axis=1, keepdims=True), 1e-12, None)


def pool_tiles(T: np.ndarray, how: str = "mean", k: int = 8) -> np.ndarray:
    """Pool a slide's tile vectors into one vector."""
    T = l2n(T)
    if how == "mean":
        v = T.mean(0)
    elif how == "max":
        v = T.max(0)
    elif how == "meanmax":
        v = np.concatenate([T.mean(0), T.max(0)])
    elif how == "topk":  # mean of the k tiles closest to the slide centroid (drops outlier tiles)
        c = l2n(T.mean(0, keepdims=True))[0]
        v = T[np.argsort(-(T @ c))[:k]].mean(0)
    else:
        raise ValueError(how)
    return v / (np.linalg.norm(v) or 1.0)


def knn_predict(Q: np.ndarray, X: np.ndarray, y: list, k: int = 1, exclude_self: bool = False) -> list:
    S = l2n(Q) @ l2n(X).T
    if exclude_self:
        np.fill_diagonal(S, -np.inf)
    out = []
    for row in S:
        idx = np.argsort(-row)[:k]
        votes = Counter()
        for j in idx:
            votes[y[j]] += float(row[j])
        out.append(max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0])
    return out


def rank_similar(Q: np.ndarray, X: np.ndarray, q_ids: list, x_ids: list, top: int = 10) -> dict:
    S = l2n(Q) @ l2n(X).T
    res = {}
    for qi, row in zip(q_ids, S):
        order = [x_ids[j] for j in np.argsort(-row) if x_ids[j] != qi]
        res[qi] = order[:top]
    return res


def precision_at(ranked: dict, group: dict, ks=(1, 5, 10)) -> dict:
    out = {}
    for k in ks:
        vals = []
        for q, lst in ranked.items():
            if q not in group:
                continue
            hits = [group.get(r) == group[q] for r in lst[:k]]
            vals.append(sum(hits) / k)
        out[f"p@{k}"] = float(np.mean(vals)) if vals else float("nan")
    return out


def loo_eval(X: np.ndarray, y: list, k: int = 1) -> dict:
    """Leave-one-out on labelled slides: C1 accuracy by k-NN, and C2 precision within the labelled pool."""
    pred = knn_predict(X, X, y, k=k, exclude_self=True)
    acc = float(np.mean([p == t for p, t in zip(pred, y)]))
    ids = list(range(len(y)))
    ranked = rank_similar(X, X, ids, ids)
    return {"c1_acc": acc, **precision_at(ranked, dict(enumerate(y)))}


def supplier_holdout_eval(X: np.ndarray, y: list, supplier: list, k: int = 1) -> dict:
    """Train on all suppliers but one, test on that one. Shows how much accuracy is supplier shortcut."""
    out = {}
    for s in sorted(set(supplier)):
        te = [i for i, v in enumerate(supplier) if v == s]
        tr = [i for i, v in enumerate(supplier) if v != s]
        if not te or not tr:
            continue
        pred = knn_predict(X[te], X[tr], [y[i] for i in tr], k=k)
        out[s] = {"n": len(te), "acc": float(np.mean([p == y[i] for p, i in zip(pred, te)]))}
    return out
