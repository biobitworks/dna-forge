import numpy as np
import pytest

from dnaforge.contrib import read_predictions, write_predictions


def test_contract_roundtrip_and_stack(tmp_path):
    pytest.importorskip("sklearn")
    from dnaforge.stack import stack
    rng = np.random.default_rng(0)
    groups = ["A", "B", "C"]
    ids = [f"s{i:02d}" for i in range(30)]
    labels = {s: groups[i % 3] for i, s in enumerate(ids)}
    folds = {s: i % 5 for i, s in enumerate(ids)}
    dirs = []
    for m in range(2):
        d = tmp_path / f"run{m}"; d.mkdir()
        oof = {s: np.eye(3)[groups.index(labels[s])] * 2 + rng.random(3) for s in ids}
        held = {f"h{i}": rng.random(3) for i in range(4)}
        write_predictions(d, groups, oof, held, folds)
        dirs.append(d)
    g, rows = read_predictions(dirs[0] / "oof_organ.csv")
    assert g == groups and abs(rows["s00"][1].sum() - 1) < 1e-5 and rows["s00"][0] == 0
    _, h = read_predictions(dirs[0] / "heldout_organ.csv")
    assert all(v[0] == -1 for v in h.values())
    r = stack(dirs, labels, folds)
    assert r["report"]["average"] > 0.9 and r["held"].shape == (4, 3)


def test_mil_trains():
    torch = pytest.importorskip("torch")
    from dnaforge.mil import predict, train_fold
    rng = np.random.default_rng(0)
    bags = [rng.normal(size=(5, 8)).astype(np.float32) + (i % 2) * 3 for i in range(20)]
    y = np.array([i % 2 for i in range(20)])
    m = train_fold(bags, y, 2, 8, epochs=5, lr=1e-2, seed=0, device="cpu")
    P = predict(m, bags, "cpu")
    assert P.shape == (20, 2) and (P.argmax(1) == y).mean() > 0.8

