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



def test_fco_fcg_primitives_and_rejection():
    from dnaforge import fcg
    assert fcg.leaf(b"x") != fcg.leaf(b"\x01x")
    a, b = fcg.fco("file", {"sha256": "aa"}), fcg.fco("file", {"sha256": "bb"})
    g1, g2 = fcg.fcg("g", [a, b]), fcg.fcg("g", [b, a])
    assert g1["identity"]["root"] == g2["identity"]["root"]           # order independent
    parent = fcg.fcg("p", [g1, fcg.fco("run", {"name": "r"})])          # fractal: an FCG is a member
    assert parent["identity"]["count"] == 2
    bad = dict(a, identity={"sha256": "tampered"})
    with pytest.raises(ValueError):
        fcg.fcg("g", [bad])
    with pytest.raises(ValueError):
        fcg.fcg("g", [a, a])


def test_fcg_build_and_blind(tmp_path):
    import json, zipfile
    from dnaforge import custody, fcg
    from tests.test_core import make_pack
    root = tmp_path / "data"; root.mkdir()
    make_pack(root)
    z = tmp_path / "biobase-challenge-slides.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("x", "y")
    cdir = tmp_path / "custody"
    custody.ingest([z], root, cdir / "ingest-x.json")
    runs = tmp_path / "runs"
    with custody.RunRecord("r", inputs=[root / "slides/pack_slides/slides_manifest.json"], runs_dir=runs) as run:
        o = run.dir / "o.csv"; o.write_text("a"); run.output(o)
    key = b"k" * 32
    g = fcg.build(cdir, runs, key=key)
    assert {m["kind"] for m in g["members"]} == {"dataset", "run"}
    assert {e["type"] for e in g["edges"]} == {"USED_BY", "PRODUCED"}
    pub = json.dumps(fcg.public(g))
    assert "slides_manifest" not in pub and "S00" not in pub and fcg.commitment(key) in pub
    prov = fcg.to_prov(g)
    types = {json.dumps(x.get("@type")) for x in prov["@graph"]}
    assert '"prov:Activity"' in types and any("prov:used" in x for x in prov["@graph"])
    assert "slides_manifest" not in json.dumps(prov)
    (cdir / "local").mkdir(exist_ok=True); (cdir / "local/fco.key").write_bytes(key)
    r = fcg.blind(root, out_dir=cdir / "local/blind", key_path=cdir / "local/fco.key")
    mod = (cdir / "local/blind/modeller.csv").read_text()
    assert r["tokens"] == 12 and "S0" not in mod and "Breast" not in mod
    assert "Breast" in (cdir / "local/blind/custodian.csv").read_text()


def test_endo_eval_on_synthetic(tmp_path):
    pytest.importorskip("sklearn")
    from dnaforge.endo import evaluate, load
    rng = np.random.default_rng(0)
    p = tmp_path / "e.csv"
    rows = ["Age,Pain,Diagnosis"] + [f"{rng.integers(20,50)},{(d:=int(rng.random()<.4))*3+rng.random()},{d}" for _ in range(200)]
    p.write_text("\n".join(rows))
    cols, X, y = load(p)
    assert cols == ["Age", "Pain"] and X.shape == (200, 2)
    assert evaluate(X, y)["logreg"]["auc"] > 0.9
