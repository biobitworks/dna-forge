"""Tests on a small synthetic pack layout (no challenge data needed)."""
import csv
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from dnaforge import custody
from dnaforge.data import BiobaseData
from dnaforge.probes import loo_eval, pool_tiles, precision_at, rank_similar
from dnaforge.__main__ import main


def make_pack(root: Path, n=12, dim=8, seed=0):
    rng = np.random.default_rng(seed)
    groups = ["Breast", "Lung", "Colon and rectum"]
    centers = {g: rng.normal(size=dim) * 5 for g in groups}
    slides, vecs = [], []
    for i in range(n):
        g = groups[i % 3]
        held = i >= n - 3
        s = {"id": f"S{i:02d}", "supplierId": f"SUPP-0{1 + i % 2}", "stain": "H&E"}
        if held:
            s["heldout"] = True
        else:
            s.update(organ=g, organGroup=g)
        slides.append(s)
        vecs.append({"id": s["id"], "v": (centers[g] + rng.normal(size=dim)).tolist()})
    (root / "slides/pack_slides").mkdir(parents=True)
    (root / "slides/pack_slides/slides_manifest.json").write_text(json.dumps(
        {"slides": slides, "organGroupList": groups, "organGroups": {g: g for g in groups}}))
    for m in ("gigapath", "dinov2"):
        d = root / "tiles/tilepack/embeddings" / m
        d.mkdir(parents=True)
        (d / "slide-vectors.json").write_text(json.dumps(vecs))
    # int8 tiles for dinov2: 2 tiles per slide
    d = root / "tiles/tilepack/embeddings/dinov2"
    tv = np.clip(rng.normal(size=(2 * n, dim)) * 40, -127, 127).astype(np.int8)
    tv.tofile(d / "tile-vectors.i8")
    np.arange(4 * n, dtype="<u2").tofile(d / "tile-coords.u16")
    (d / "tile-meta.json").write_text(json.dumps({"dim": dim, "scale": 127, "tiles": 2 * n, "license": "x",
                                                  "slides": {s["id"]: {"offset": 2 * i, "count": 2} for i, s in enumerate(slides)}}))
    with open(root / "tiles/tilepack/tiles.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["slide_id", "level", "col", "row", "index", "file"])
        for i, s in enumerate(slides):
            for j in range(2):
                w.writerow([s["id"], 12, j, 0, 2 * i + j, f"tiles/{s['id']}/{j}_0.jpg"])
    return slides


def test_load_and_embeddings(tmp_path):
    make_pack(tmp_path)
    d = BiobaseData.load(tmp_path)
    assert len(d.slides) == 12 and len(d.heldout) == 3 and len(d.labelled) == 9
    e = d.embeddings("dinov2", tiles=True)
    assert e.tile_vectors.shape == (24, 8) and e.tiles("S03").shape == (2, 8)
    assert abs(e.tile_vectors).max() <= 1.0
    assert len(d.tiles_4um()) == 24
    assert pool_tiles(e.tiles("S03"), "topk", k=1).shape == (8,)


def test_loo_and_ranking():
    X = np.array([[1, 0], [0.9, 0.1], [0, 1], [0.1, 0.9]], float)
    y = ["a", "a", "b", "b"]
    r = loo_eval(X, y)
    assert r["c1_acc"] == 1.0 and r["p@1"] == 1.0
    ranked = rank_similar(X[:1], X, [0], [0, 1, 2, 3], top=2)
    assert ranked[0] == [1, 3] or ranked[0][0] == 1
    assert precision_at({0: [1]}, {0: "a", 1: "a"}, ks=(1,))["p@1"] == 1.0


def test_custody_ingest_verify_and_run_record(tmp_path):
    root = tmp_path / "biobase"; root.mkdir()
    make_pack(root)
    z = tmp_path / "pack.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("a.txt", "hello")
    out = tmp_path / "custody/ingest.json"
    rec = custody.ingest([z], root, out)
    assert rec["sources"]["pack.zip"]["sha256"] == custody.sha256_file(z)
    assert custody.verify(out, root) == []
    assert custody.verify(custody.local_path(out), root) == []
    assert "slides_manifest.json" not in out.read_text() and "slides_manifest.json" in custody.local_path(out).read_text()
    (root / "slides/pack_slides/extra.csv").write_text("x")
    assert "added: slides/pack_slides/extra.csv" in custody.verify(out, root)
    (root / "slides/pack_slides/extra.csv").unlink()
    (root / "slides/pack_slides/slides_manifest.json").write_text("{}")
    assert any(p.startswith("changed:") for p in custody.verify(out, root))
    # no data content in the manifest, only names/sizes/hashes
    assert "organGroup" not in out.read_text()


def test_cli_submit_writes_files_and_record(tmp_path):
    make_pack(tmp_path)
    runs = tmp_path / "runs"
    assert main(["--root", str(tmp_path), "--runs", str(runs), "submit", "--models", "gigapath"]) == 0
    run_dir = next(runs.iterdir())
    rec = json.loads((run_dir / "record.json").read_text())
    assert rec["status"] == "ok" and set(rec["outputs"]) == {"submission_slides_organ.csv", "submission_slides_similar.csv"}
    rows = list(csv.DictReader(open(run_dir / "submission_slides_organ.csv")))
    assert len(rows) == 3 and all(r["organ"] for r in rows)
    sim = list(csv.DictReader(open(run_dir / "submission_slides_similar.csv")))
    assert len(sim) == 30 and all(r["query_slide_id"] != r["result_slide_id"] for r in sim)
    assert main(["--root", str(tmp_path), "--runs", str(runs), "eval", "--models", "gigapath", "dinov2"]) == 0


def test_transforms(tmp_path):
    PIL = pytest.importorskip("PIL")
    from PIL import Image
    from dnaforge.transforms import Preprocess, is_blank
    white = Image.new("RGB", (200, 254), (250, 250, 250))
    pink = Image.new("RGB", (254, 254), (200, 120, 170))
    assert is_blank(white) and not is_blank(pink)
    pink.save(tmp_path / "t.jpg"); white.save(tmp_path / "w.jpg")
    pre = Preprocess(size=224, train=True)
    a = pre(tmp_path / "t.jpg")
    assert a.shape == (3, 224, 224) and a.dtype == np.float32
    assert pre(tmp_path / "w.jpg") is None


def test_run_ids_unique(tmp_path):
    with custody.RunRecord("x", runs_dir=tmp_path) as a, custody.RunRecord("x", runs_dir=tmp_path) as b:
        assert a.dir != b.dir


def test_folds(tmp_path):
    pytest.importorskip("sklearn")
    from dnaforge.__main__ import make_folds
    make_pack(tmp_path, n=33)
    f = make_folds(BiobaseData.load(tmp_path), n_splits=3)
    assert f["count"] == 30 and set(f["folds"].values()) == {0, 1, 2}
    assert "organ" not in json.dumps(f["folds"])


def test_tile_dataset_picklable():
    import pickle
    from dnaforge.transforms import TileDataset
    ds = TileDataset([], labels={"a": "Lung"})
    assert pickle.loads(pickle.dumps(ds)).classes == ["Lung"]
