"""Slide-level organ models (C1) and similarity ranking (C2) on frozen embeddings.

Every method maps (features of all slides, train ids + labels) -> class probabilities
for any query ids, with columns in a fixed class order (the manifest's organGroupList).
C2 ranking mixes embedding similarity with agreement of (predicted) organ groups.

    feats = build_features(data, ["gigapath", "hoptimus@meanmax"])
    P = fit_predict("ens-lr", feats, train_ids, train_y, query_ids, classes)
    ranked = rank_c2(feats, P_all, ids, query_ids, alpha=1.0)
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Optional

import numpy as np

from .probes import l2n, pool_tiles

# ---------------------------------------------------------------- features


def supplier_center(X: np.ndarray, suppliers: list) -> np.ndarray:
    """Subtract each supplier's mean vector (over all its slides, no labels used), then re-normalise."""
    X = X.copy()
    sup = np.asarray(suppliers)
    for s in set(suppliers):
        m = sup == s
        X[m] -= X[m].mean(0, keepdims=True)
    return l2n(X)


def impute_missing(X: np.ndarray, present: np.ndarray, ref: np.ndarray, k: int = 5) -> np.ndarray:
    """Fill rows of X that are missing (present == False) with the mean of the k nearest present
    rows, where nearness is measured in a reference embedding available for every row."""
    X = X.copy()
    if present.all():
        return X
    R = l2n(ref)
    have = np.where(present)[0]
    for i in np.where(~present)[0]:
        nn = have[np.argsort(-(R[have] @ R[i]))[:k]]
        X[i] = X[nn].mean(0)
    return l2n(X)


def block(data, spec: str, ids: list, emb_cache: Optional[dict] = None) -> np.ndarray:
    """One feature block for `ids`. spec = model[@pool][~sc], e.g. 'gigapath', 'hoptimus@meanmax~sc'.
    pool is 'slide' (provided slide vector, default) or a pool_tiles mode (mean/max/meanmax/topk).
    '~sc' subtracts supplier means."""
    emb_cache = {} if emb_cache is None else emb_cache
    sc = spec.endswith("~sc")
    base = spec[:-3] if sc else spec
    model, _, pool = base.partition("@")
    pool = pool or "slide"
    key = (model, pool != "slide")
    if key not in emb_cache:
        emb_cache[key] = data.embeddings(model, tiles=pool != "slide")
    e = emb_cache[key]
    if pool == "slide":
        vecs = [e.slide(i) for i in ids]
    else:
        vecs = [None if e.tiles(i) is None else pool_tiles(e.tiles(i), pool) for i in ids]
    present = np.array([v is not None for v in vecs])
    dim = next(v for v in vecs if v is not None).shape[0]
    X = l2n(np.stack([v if v is not None else np.zeros(dim, np.float32) for v in vecs]).astype(np.float64))
    if not present.all():  # gigapath lacks 2 slides: impute from H-optimus neighbours
        rk = ("hoptimus", False)
        if rk not in emb_cache:
            emb_cache[rk] = data.embeddings("hoptimus")
        X = impute_missing(X, present, np.stack([emb_cache[rk].slide(i) for i in ids]))
    if sc:
        by = data.by_id
        X = supplier_center(X, [by[i].supplier for i in ids])
    return X


def build_features(data, specs: list, ids: Optional[list] = None, weights: Optional[list] = None,
                   emb_cache: Optional[dict] = None) -> tuple:
    """Concatenate L2-normalised blocks, block j scaled by sqrt(weight_j). Returns (ids, X)."""
    ids = ids or [s.id for s in data.slides]
    weights = weights or [1.0] * len(specs)
    Xs = [block(data, s, ids, emb_cache) * np.sqrt(w) for s, w in zip(specs, weights)]
    return ids, np.hstack(Xs)


# ---------------------------------------------------------------- classifiers
# Each returns an (n_query, n_classes) probability matrix in `classes` order.


def _onehot(y_idx: np.ndarray, C: int) -> np.ndarray:
    Y = np.zeros((len(y_idx), C))
    Y[np.arange(len(y_idx)), y_idx] = 1
    return Y


def wknn_proba(Xtr, ytr, Xq, C, k=5, power=4.0, exclude_self=False):
    """Similarity-weighted k-NN vote shares (weights = max(cos,0)^power)."""
    S = l2n(Xq) @ l2n(Xtr).T
    if exclude_self:
        np.fill_diagonal(S, -np.inf)
    P = np.zeros((len(Xq), C))
    idx = np.argsort(-S, axis=1)[:, :k]
    for r in range(len(Xq)):
        w = np.clip(S[r, idx[r]], 1e-6, None) ** power
        np.add.at(P[r], ytr[idx[r]], w)
    return P / P.sum(1, keepdims=True)


def logreg_proba(Xtr, ytr, Xq, C, Creg=1.0, standardize=True):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    if standardize:
        sc = StandardScaler().fit(Xtr)
        Xtr, Xq = sc.transform(Xtr), sc.transform(Xq)
    # The L2-regularised solution lies in the row span of Xtr, so projecting onto it is exact and fast.
    mu = Xtr.mean(0)
    _, _, Vt = np.linalg.svd(Xtr - mu, full_matrices=False)
    Xtr, Xq = (Xtr - mu) @ Vt.T, (Xq - mu) @ Vt.T
    m = LogisticRegression(C=Creg, max_iter=3000)
    m.fit(Xtr, ytr)
    P = np.zeros((len(Xq), C))
    P[:, m.classes_] = m.predict_proba(Xq)
    return P


def svm_proba(Xtr, ytr, Xq, C, Creg=1.0):
    """Linear SVM; softmax of decision scores as pseudo-probabilities."""
    from sklearn.svm import LinearSVC
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(Xtr)
    Xtr, Xq = sc.transform(Xtr), sc.transform(Xq)
    mu = Xtr.mean(0)  # project onto the training row span (same solution up to the intercept penalty, much faster)
    _, _, Vt = np.linalg.svd(Xtr - mu, full_matrices=False)
    Xtr, Xq = (Xtr - mu) @ Vt.T, (Xq - mu) @ Vt.T
    m = LinearSVC(C=Creg, max_iter=20000).fit(Xtr, ytr)
    D = m.decision_function(Xq)
    if D.ndim == 1:
        D = np.stack([-D, D], 1)
    E = np.exp(3 * (D - D.max(1, keepdims=True)))
    P = np.zeros((len(Xq), C))
    P[:, m.classes_] = E / E.sum(1, keepdims=True)
    return P


def lda_fit(Xtr, ytr, n_pca=64):
    """PCA (fit on train) then shrinkage LDA. Returns a transform function."""
    from sklearn.decomposition import PCA
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    p = PCA(n_components=min(n_pca, len(Xtr) - 1, Xtr.shape[1]), random_state=0).fit(Xtr)
    lda = LDA(solver="eigen", shrinkage="auto").fit(p.transform(Xtr), ytr)
    return lambda X: lda.transform(p.transform(X))


def lda_knn_proba(Xtr, ytr, Xq, C, k=5, power=4.0, n_pca=64):
    f = lda_fit(Xtr, ytr, n_pca)
    return wknn_proba(f(Xtr), ytr, f(Xq), C, k=k, power=power)


def tile_vote_proba(tiles_by_id: dict, tr_ids, ytr, q_ids, C, temp=0.05):
    """Tile-level kNN voting: each query tile votes for the label of its nearest training tile,
    weighted by exp(sim/temp); slide probabilities are the normalised vote mass."""
    Ttr = np.vstack([tiles_by_id[i] for i in tr_ids])
    lab = np.concatenate([np.full(len(tiles_by_id[i]), y) for i, y in zip(tr_ids, ytr)])
    own = np.concatenate([np.full(len(tiles_by_id[i]), n) for n, i in enumerate(tr_ids)])
    P = np.zeros((len(q_ids), C))
    for r, q in enumerate(q_ids):
        S = tiles_by_id[q] @ Ttr.T
        S[:, own == (tr_ids.index(q) if q in tr_ids else -1)] = -np.inf
        j = S.argmax(1)
        np.add.at(P[r], lab[j], np.exp((S[np.arange(len(j)), j] - 1) / temp))
    return P / P.sum(1, keepdims=True)


# ---------------------------------------------------------------- method registry
# A method = list of (feature specs, weights, classifier fn, kwargs, ensemble weight).

GIGA = ["gigapath"]
ALL4 = ["gigapath", "hoptimus", "biomedclip", "dinov2"]
CLF = {"wknn": wknn_proba, "lr": logreg_proba, "svm": svm_proba, "ldaknn": lda_knn_proba}

# 5-fold CV x 3 fold seeds on the 190 labelled slides (see scripts/sweep.py): giga-1nn 0.775,
# giga-lr 0.828, giga-svm 0.847, gh-svm 0.851, ens-svm 0.854. Note: StandardScaler inside lr/svm
# makes block weights irrelevant there.
METHODS: "OrderedDict[str, list]" = OrderedDict([
    ("giga-1nn", [(GIGA, None, "wknn", {"k": 1}, 1.0)]),
    ("giga-wknn5", [(GIGA, None, "wknn", {"k": 5, "power": 4}, 1.0)]),
    ("giga-lr", [(GIGA, None, "lr", {"Creg": 0.1}, 1.0)]),
    ("giga-sc-lr", [(["gigapath~sc"], None, "lr", {"Creg": 0.1}, 1.0)]),
    ("giga-ldaknn", [(GIGA, None, "ldaknn", {"k": 5}, 1.0)]),
    ("giga-svm", [(GIGA, None, "svm", {"Creg": 0.01}, 1.0)]),
    ("gh-svm", [(["gigapath", "hoptimus"], None, "svm", {"Creg": 0.01}, 1.0)]),
    ("ens-svm", [(GIGA, None, "svm", {"Creg": 0.01}, 1.0), (["gigapath", "hoptimus"], None, "svm", {"Creg": 0.01}, 1.0)]),
    ("all4-lr", [(ALL4, None, "lr", {"Creg": 0.1}, 1.0)]),
    ("hopt-meanmax-lr", [(["hoptimus@meanmax"], None, "lr", {"Creg": 0.1}, 1.0)]),
])
DEFAULT_METHOD = "ens-svm"  # fold-0 OOF C1 0.863, P@1/5/10 0.868/0.829/0.800 (alpha 3)


def fit_predict(method, feats: dict, tr_ids: list, ytr: np.ndarray, q_ids: list, C: int) -> np.ndarray:
    """feats maps a feature key (tuple of specs, tuple of weights) -> (ids, X). Missing keys are an error;
    use `method_feature_keys` + `build_features` to fill them."""
    members = METHODS[method] if isinstance(method, str) else method
    total, P = 0.0, np.zeros((len(q_ids), C))
    for specs, w, clf, kw, ew in members:
        ids, X = feats[feature_key(specs, w)]
        pos = {i: n for n, i in enumerate(ids)}
        Xtr, Xq = X[[pos[i] for i in tr_ids]], X[[pos[i] for i in q_ids]]
        P += ew * CLF[clf](Xtr, ytr, Xq, C, **kw)
        total += ew
    return P / total


def feature_key(specs, w=None):
    return (tuple(specs), tuple(w) if w else None)


def method_feature_keys(method) -> list:
    members = METHODS[method] if isinstance(method, str) else method
    return [(feature_key(s, w), s, w) for s, w, *_ in members]


def ensure_features(data, method, feats: dict, emb_cache: Optional[dict] = None) -> dict:
    ids = [s.id for s in data.slides]
    for key, specs, w in method_feature_keys(method):
        if key not in feats:
            feats[key] = build_features(data, list(specs), ids, list(w) if w else None, emb_cache)
    return feats


# ---------------------------------------------------------------- C2 ranking


def rank_c2(X: np.ndarray, ids: list, q_ids: list, cand_ids: list, cand_P: np.ndarray, q_P: np.ndarray,
            alpha: float = 1.0, top: int = 10, return_scores: bool = False):
    """score(q, c) = cos(x_q, x_c) + alpha * <p_q, p_c>.  cand_P rows are one-hot for labelled
    candidates and predicted probabilities for unlabelled ones; q_P are the query's predictions."""
    pos = {i: n for n, i in enumerate(ids)}
    Xn = l2n(X)
    Q, Cm = Xn[[pos[i] for i in q_ids]], Xn[[pos[i] for i in cand_ids]]
    S = Q @ Cm.T + alpha * (q_P @ cand_P.T)
    out = {}
    for r, q in enumerate(q_ids):
        order = [j for j in np.argsort(-S[r]) if cand_ids[j] != q][:top]
        out[q] = [(cand_ids[j], float(S[r, j])) for j in order] if return_scores else [cand_ids[j] for j in order]
    return out


# ---------------------------------------------------------------- evaluation


def stratified_folds(ids: list, y: list, n_splits=5, seed=0) -> dict:
    """{slide_id: fold} from StratifiedKFold over ids sorted (matches custody/folds.json for seed 0)."""
    import warnings
    from sklearn.model_selection import StratifiedKFold
    order = sorted(range(len(ids)), key=lambda i: ids[i])
    sid = [ids[i] for i in order]
    yy = [y[i] for i in order]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sk = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        out = {}
        for f, (_, te) in enumerate(sk.split(np.zeros(len(sid)), yy)):
            for j in te:
                out[sid[j]] = f
    return out


def cv_eval(method, feats: dict, lab_ids: list, y_idx: np.ndarray, C: int, folds: dict,
            alpha=1.0, c2_space=None) -> dict:
    """Out-of-fold C1 accuracy and C2 P@1/5/10 within the labelled pool.
    C2 for a test-fold query ranks all other labelled slides; candidates in the training folds
    carry their true one-hot labels, candidates in the test fold carry their OOF predictions,
    as in the real submission (labelled known, held-out predicted)."""
    from .probes import precision_at
    P = np.zeros((len(lab_ids), C))
    yd = dict(zip(lab_ids, y_idx))
    alphas = list(alpha) if isinstance(alpha, (list, tuple)) else [alpha]
    ranked = {a: {} for a in alphas}
    c2_space = c2_space or "gigapath"
    sx_ids, SX = feats[feature_key([c2_space] if isinstance(c2_space, str) else c2_space)]
    for f in sorted(set(folds[i] for i in lab_ids)):
        te = [i for i in lab_ids if folds[i] == f]
        tr = [i for i in lab_ids if folds[i] != f]
        Pte = fit_predict(method, feats, tr, np.array([yd[i] for i in tr]), te, C)
        for i, row in zip(te, Pte):
            P[lab_ids.index(i)] = row
        cand = tr + te
        cP = np.vstack([_onehot(np.array([yd[i] for i in tr]), C), Pte])
        for a in alphas:
            ranked[a].update(rank_c2(SX, sx_ids, te, cand, cP, Pte, alpha=a))
    acc = float(np.mean(P.argmax(1) == y_idx))
    out = {"c1_acc": acc, "P": P, **precision_at(ranked[alphas[0]], yd)}
    if len(alphas) > 1:
        out["by_alpha"] = {a: precision_at(ranked[a], yd) for a in alphas}
    return out
