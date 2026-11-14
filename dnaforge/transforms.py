"""Tile preprocessing for vision models.

Pure-numpy/PIL transforms so they run anywhere; `TileDataset` wraps them for
PyTorch when torch is installed.
"""
from __future__ import annotations

import random
from collections import defaultdict
from pathlib import Path
from typing import Callable, Optional, Sequence

import numpy as np

# ImageNet statistics, which DINOv2, H-optimus-0, GigaPath and BiomedCLIP expect
# (BiomedCLIP's own CLIP mean/std are close; pass mean/std explicitly to override).
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def load_rgb(path: str | Path):
    from PIL import Image
    return Image.open(path).convert("RGB")


def tissue_fraction(img, white: int = 220, black: int = 20) -> float:
    """Share of pixels that look like tissue (not glass, not black)."""
    a = np.asarray(img, dtype=np.uint8)
    gray = a.mean(axis=2)
    sat = a.max(axis=2).astype(int) - a.min(axis=2)
    tissue = (gray < white) & (gray > black) & (sat > 15)
    return float(tissue.mean())


def is_blank(img, min_tissue: float = 0.1) -> bool:
    return tissue_fraction(img) < min_tissue


def pad_to_square(img, size: int, fill=(255, 255, 255)):
    """Edge tiles can be smaller than 254 px; pad with glass-white instead of stretching."""
    from PIL import Image
    w, h = img.size
    if w == size and h == size:
        return img
    canvas = Image.new("RGB", (max(w, size), max(h, size)), fill)
    canvas.paste(img, (0, 0))
    return canvas.crop((0, 0, size, size)) if canvas.size != (size, size) else canvas


def resize(img, size: int = 224):
    from PIL import Image
    return img.resize((size, size), Image.BICUBIC)


def to_array(img, mean: Sequence[float] = IMAGENET_MEAN, std: Sequence[float] = IMAGENET_STD) -> np.ndarray:
    """HWC uint8 -> CHW float32, normalised."""
    a = np.asarray(img, dtype=np.float32) / 255.0
    a = (a - np.asarray(mean, np.float32)) / np.asarray(std, np.float32)
    return a.transpose(2, 0, 1).copy()


def augment(img, rng: random.Random):
    """Label-preserving histology augmentations: flips, 90° rotations, mild colour jitter."""
    from PIL import Image, ImageEnhance
    if rng.random() < 0.5:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if rng.random() < 0.5:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img = img.rotate(90 * rng.randrange(4))
    img = ImageEnhance.Color(img).enhance(rng.uniform(0.85, 1.15))
    img = ImageEnhance.Brightness(img).enhance(rng.uniform(0.9, 1.1))
    return img


class Preprocess:
    """Callable pipeline: path -> CHW float32 array (or None if blank)."""

    def __init__(self, size: int = 224, tile_size: int = 254, drop_blank: bool = True,
                 train: bool = False, seed: int = 0, mean=IMAGENET_MEAN, std=IMAGENET_STD):
        self.size, self.tile_size, self.drop_blank, self.train = size, tile_size, drop_blank, train
        self.rng = random.Random(seed)
        self.mean, self.std = mean, std

    def __call__(self, path) -> Optional[np.ndarray]:
        img = load_rgb(path)
        if self.drop_blank and is_blank(img):
            return None
        img = pad_to_square(img, self.tile_size)
        if self.train:
            img = augment(img, self.rng)
        return to_array(resize(img, self.size), self.mean, self.std)


def sample_tiles(tiles: list, per_slide: int, seed: int = 0) -> list:
    """Evenly cap the number of tiles per slide, deterministically."""
    by = defaultdict(list)
    for t in tiles:
        by[t.slide_id].append(t)
    rng = random.Random(seed)
    out = []
    for sid in sorted(by):
        ts = sorted(by[sid], key=lambda t: (t.row, t.col))
        out += ts if len(ts) <= per_slide else rng.sample(ts, per_slide)
    return out


try:
    from torch.utils.data import Dataset as _TorchDataset
except Exception:  # torch is optional
    _TorchDataset = object


class TileDataset(_TorchDataset):
    """PyTorch Dataset of (tensor, label index or -1, slide id, ok). Blank tiles become zeros with ok=False.

    Defined at module scope so DataLoader workers can pickle it under the spawn start method (macOS default).
    """

    def __init__(self, tiles: list, labels: Optional[dict] = None, preprocess: Optional[Callable] = None):
        self.tiles = list(tiles)
        self.labels = labels or {}
        self.classes = sorted(set(self.labels.values()))
        self._cidx = {c: i for i, c in enumerate(self.classes)}
        self.pre = preprocess or Preprocess()

    def __len__(self):
        return len(self.tiles)

    def __getitem__(self, i):
        import torch
        t = self.tiles[i]
        a = self.pre(t.path)
        ok = a is not None
        x = torch.from_numpy(a) if ok else torch.zeros(3, self.pre.size, self.pre.size)
        y = self._cidx.get(self.labels.get(t.slide_id), -1)
        return x, y, t.slide_id, ok
