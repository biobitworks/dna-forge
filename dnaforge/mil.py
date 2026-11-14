"""Attention-MIL over a model's int8 tile vectors, trained per shared fold (PyTorch, MPS if available).

  python -m dnaforge.mil --root ~/dna-forge/biobase --model hoptimus

Writes a contribution run (oof_organ.csv, heldout_organ.csv, record.json) per the contract in contrib.py.
"""
from __future__ import annotations

import argparse
import socket
from pathlib import Path

import numpy as np

from . import custody
from .contrib import load_folds, write_predictions
from .data import BiobaseData


def build(dim, n_cls, hidden=128, drop=0.25):
    import torch.nn as nn
    import torch

    class ABMIL(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Sequential(nn.Linear(dim, hidden), nn.GELU(), nn.Dropout(drop))
            self.att_a = nn.Linear(hidden, 64); self.att_b = nn.Linear(hidden, 64); self.att_w = nn.Linear(64, 1)
            self.head = nn.Linear(hidden, n_cls)

        def forward(self, x):  # x: tiles x dim
            h = self.enc(x)
            a = self.att_w(torch.tanh(self.att_a(h)) * torch.sigmoid(self.att_b(h))).squeeze(-1)
            w = torch.softmax(a, 0)
            return self.head((w[:, None] * h).sum(0))
    return ABMIL()


def train_fold(bags, y, n_cls, dim, epochs, lr, seed, device, max_tiles=64):
    import torch
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    m = build(dim, n_cls).to(device)
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-2)
    counts = np.bincount(y, minlength=n_cls).astype(float)
    wts = torch.tensor(np.where(counts > 0, counts.sum() / (n_cls * np.maximum(counts, 1)), 0), dtype=torch.float32, device=device)
    lossf = torch.nn.CrossEntropyLoss(reduction="none")  # one slide per step: apply the class weight by hand
    for _ in range(epochs):
        m.train()
        for i in rng.permutation(len(bags)):
            b = bags[i]
            if len(b) > max_tiles:
                b = b[rng.choice(len(b), max_tiles, replace=False)]
            out = m(torch.from_numpy(b).to(device))
            loss = (wts[y[i]] * lossf(out[None], torch.tensor([y[i]], device=device))).sum()
            opt.zero_grad(); loss.backward(); opt.step()
    return m


def predict(m, bags, device):
    import torch
    m.eval()
    with torch.no_grad():
        return np.stack([torch.softmax(m(torch.from_numpy(b).to(device)), -1).cpu().numpy() for b in bags])


def main(argv=None):
    import torch
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default="~/dna-forge/biobase")
    p.add_argument("--model", default="hoptimus", choices=["dinov2", "hoptimus", "biomedclip"])
    p.add_argument("--folds", default="custody/local/folds.json")
    p.add_argument("--runs", default="runs")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--seeds", type=int, default=3, help="ensemble of seeds per fold")
    a = p.parse_args(argv)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    data = BiobaseData.load(Path(a.root).expanduser())
    emb = data.embeddings(a.model, tiles=True)
    groups = data.organ_groups
    folds = load_folds(a.folds)
    lab = [s for s in sorted(folds) if emb.tiles(s) is not None]
    held = [s.id for s in data.heldout if emb.tiles(s.id) is not None]
    gi = {g: i for i, g in enumerate(groups)}
    lab_by = data.by_id
    y = np.array([gi[lab_by[s].organ_group] for s in lab])
    bags = {s: np.ascontiguousarray(emb.tiles(s), dtype=np.float32) for s in lab + held}
    f = np.array([folds[s] for s in lab])
    mdir = data.root / "tiles/tilepack/embeddings" / a.model
    with custody.RunRecord(f"mil-{a.model}", config=vars(a) | {"device": device},
                           inputs=[Path(a.folds), data.root / "slides/pack_slides/slides_manifest.json",
                                   mdir / "tile-vectors.i8", mdir / "tile-meta.json"], runs_dir=a.runs) as run:
        oof = {}
        for k in sorted(set(f)):
            tr, te = np.where(f != k)[0], np.where(f == k)[0]
            P = np.mean([predict(train_fold([bags[lab[i]] for i in tr], y[tr], len(groups), emb.dim, a.epochs, a.lr,
                                            a.seed + s, device), [bags[lab[i]] for i in te], device) for s in range(a.seeds)], 0)
            oof.update({lab[i]: P[j] for j, i in enumerate(te)})
        Ph = np.mean([predict(train_fold([bags[s] for s in lab], y, len(groups), emb.dim, a.epochs, a.lr, a.seed + s, device),
                              [bags[s] for s in held], device) for s in range(a.seeds)], 0)
        acc = float(np.mean([np.argmax(oof[s]) == gi[lab_by[s].organ_group] for s in lab]))
        for pth in write_predictions(run.dir, groups, oof, dict(zip(held, Ph)), folds):
            run.output(pth)
        run.metrics = {"oof_acc": acc, "node": socket.gethostname(), "n_labelled": len(lab), "n_heldout": len(held)}
    print(f"mil-{a.model} oof_acc={acc:.3f} device={device} -> {run.dir}")


if __name__ == "__main__":
    main()
