"""Synthetic tests for dnaforge.models (no challenge data)."""
import numpy as np

from dnaforge import models as M


def blobs(n_per=10, C=3, dim=16, seed=0, spread=1.0):
    rng = np.random.default_rng(seed)
    centers = rng.normal(size=(C, dim)) * 4
    X = np.vstack([centers[c] + spread * rng.normal(size=(n_per, dim)) for c in range(C)])
    y = np.repeat(np.arange(C), n_per)
    return X, y


def test_wknn_rows_are_probabilities_and_correct():
    X, y = blobs()
    P = M.wknn_proba(X, y, X, 3, k=5, exclude_self=True)
    assert P.shape == (30, 3)
    assert np.allclose(P.sum(1), 1)
    assert (P.argmax(1) == y).mean() > 0.9


def test_logreg_handles_missing_class_in_train():
    X, y = blobs(C=4)
    keep = y != 3
    P = M.logreg_proba(X[keep], y[keep], X, 5, Creg=1.0)
    assert P.shape == (40, 5) and np.allclose(P[:, [3, 4]], 0)
    assert (P[keep].argmax(1) == y[keep]).mean() > 0.9


def test_lda_knn_and_svm_run():
    X, y = blobs(n_per=12)
    for fn in (M.lda_knn_proba, M.svm_proba):
        P = fn(X[::2], y[::2], X[1::2], 3)
        assert (P.argmax(1) == y[1::2]).mean() > 0.8


def test_supplier_center_removes_offset():
    X, y = blobs(n_per=20, C=2)
    sup = ["A" if i % 2 else "B" for i in range(len(y))]
    Xs = X + np.where(np.array(sup)[:, None] == "A", 50.0, 0.0)  # big supplier shift
    Z = M.supplier_center(Xs, sup)
    assert abs(Z[np.array(sup) == "A"].mean(0) @ Z[np.array(sup) == "B"].mean(0)) < 1
    assert (M.wknn_proba(Z, y, Z, 2, k=1, exclude_self=True).argmax(1) == y).mean() > 0.9


def test_impute_missing_uses_reference_neighbours():
    X, y = blobs(n_per=10, C=2)
    present = np.ones(len(y), bool)
    present[0] = False
    Xm = X.copy(); Xm[0] = 0
    Z = M.impute_missing(Xm, present, X)
    assert np.linalg.norm(Z[0]) > 0
    assert M.wknn_proba(np.delete(Z, 0, 0), np.delete(y, 0), Z[:1], 2, k=1).argmax() == y[0]


def test_rank_c2_prefers_class_agreement():
    ids = ["q", "a", "b"]
    X = np.array([[1.0, 0], [0.9, 0.44], [0.95, 0.31]])  # b is closer by cosine
    cand_P = np.array([[1.0, 0], [0, 1.0]])           # a is class 0, b is class 1
    q_P = np.array([[1.0, 0]])
    assert M.rank_c2(X, ids, ["q"], ["a", "b"], cand_P, q_P, alpha=0)["q"][0] == "b"
    assert M.rank_c2(X, ids, ["q"], ["a", "b"], cand_P, q_P, alpha=1)["q"][0] == "a"


def test_folds_and_cv_eval():
    X, y = blobs(n_per=10)
    ids = [f"S{i:02d}" for i in range(len(y))]
    folds = M.stratified_folds(ids, list(y), 5, 0)
    assert set(folds.values()) == set(range(5)) and len(folds) == 30
    assert folds == M.stratified_folds(ids[::-1], list(y[::-1]), 5, 0)  # order-independent
    feats = {M.feature_key(["gigapath"]): (ids, X)}
    method = [(["gigapath"], None, "lr", {"Creg": 1.0}, 1.0)]
    r = M.cv_eval(method, feats, ids, y, 3, folds, alpha=1.0)
    assert r["c1_acc"] > 0.9 and r["p@5"] > 0.8 and r["P"].shape == (30, 3)


def test_tile_vote():
    rng = np.random.default_rng(1)
    c = rng.normal(size=(2, 8)) * 3
    tiles = {f"s{i}": M.l2n(c[i % 2] + rng.normal(size=(4, 8))) for i in range(8)}
    tr = [f"s{i}" for i in range(6)]
    P = M.tile_vote_proba(tiles, tr, np.array([i % 2 for i in range(6)]), ["s6", "s7"], 2)
    assert list(P.argmax(1)) == [0, 1]
