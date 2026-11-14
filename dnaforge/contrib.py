"""Model contribution contract: shared folds and the prediction files every small model writes.

Each contribution run writes, under runs/<id>/:
  record.json         RunRecord (committed)
  oof_organ.csv       slide_id, fold, <one probability column per organ group>   (labelled slides, out-of-fold)
  heldout_organ.csv   same columns, fold = -1                                    (the 67 held-out slides)
  heldout_similar.csv optional: query_slide_id, result_slide_id, score (top 50)
The CSVs stay on the machine (they imply held-out labels) and are gitignored.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


def load_folds(path: str | Path = "custody/folds.json") -> dict:
    return json.loads(Path(path).read_text())["folds"]


def write_predictions(run_dir: str | Path, groups: list, oof: dict, heldout: dict, folds: dict) -> tuple:
    """oof/heldout: {slide_id: probability vector aligned to groups}."""
    run_dir = Path(run_dir)
    paths = []
    for name, rows, fold_of in (("oof_organ.csv", oof, lambda s: folds[s]), ("heldout_organ.csv", heldout, lambda s: -1)):
        p = run_dir / name
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["slide_id", "fold", *groups])
            for sid in sorted(rows):
                v = np.asarray(rows[sid], float)
                v = v / v.sum() if v.sum() > 0 else np.full(len(groups), 1 / len(groups))
                w.writerow([sid, fold_of(sid), *[f"{x:.6f}" for x in v]])
        paths.append(p)
    return tuple(paths)


def read_predictions(path: str | Path) -> tuple:
    """Returns (groups, {slide_id: (fold, vector)})."""
    with open(path, newline="") as f:
        r = csv.reader(f)
        head = next(r)
        groups = head[2:]
        rows = {row[0]: (int(row[1]), np.array([float(x) for x in row[2:]])) for row in r}
    return groups, rows
