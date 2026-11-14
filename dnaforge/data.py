"""Core data structures for the Biobase slide set.

`BiobaseData.load(root)` reads the unzipped packs laid out as

    root/slides/pack_slides/slides_manifest.json
    root/tiles/tilepack/{tiles.csv, embeddings/<model>/...}
    root/tiles-20x/tiles20x/{tiles20x.csv, blank_tiles.csv, <slide>/<col>_<row>.jpg}
    root/thumbnails/thumbnails/<slide>.jpg
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

MODELS = ("dinov2", "hoptimus", "biomedclip", "gigapath")


@dataclass(frozen=True)
class Slide:
    id: str
    supplier: str
    heldout: bool
    organ: Optional[str] = None
    organ_group: Optional[str] = None
    stain: Optional[str] = None
    magnification: Optional[float] = None
    mpp: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    scanner: Optional[str] = None
    has_report: bool = False
    raw: dict = field(default_factory=dict, compare=False, repr=False)

    @property
    def labelled(self) -> bool:
        return not self.heldout and self.organ_group is not None

    @classmethod
    def from_manifest(cls, d: dict) -> "Slide":
        return cls(id=d["id"], supplier=d.get("supplierId", ""), heldout=bool(d.get("heldout")),
                   organ=d.get("organ"), organ_group=d.get("organGroup"), stain=d.get("stain"),
                   magnification=d.get("magnification"), mpp=d.get("mpp"), width=d.get("width"),
                   height=d.get("height"), scanner=d.get("scanner"),
                   has_report=bool(d.get("hasReport") or d.get("report")), raw=d)


@dataclass(frozen=True)
class Tile:
    slide_id: str
    path: Path
    level: int
    col: int
    row: int
    index: Optional[int] = None      # row in the tile embedding files (tile pack only)
    um_per_px: Optional[float] = None
    blank: Optional[str] = None      # "black" / "glass" for known-blank 0.5 µm tiles


@dataclass
class Embeddings:
    """Slide vectors (n_slides x dim) and, where provided, int8 tile vectors."""
    model: str
    dim: int
    slide_ids: list
    slide_vectors: np.ndarray
    tile_vectors: Optional[np.ndarray] = None  # float32, n_tiles x dim
    tile_coords: Optional[np.ndarray] = None   # uint16, n_tiles x 2 (col, row)
    tile_slices: dict = field(default_factory=dict)  # slide id -> (offset, count)
    license: Optional[str] = None

    def slide(self, sid: str) -> Optional[np.ndarray]:
        i = self._index().get(sid)
        return None if i is None else self.slide_vectors[i]

    def tiles(self, sid: str) -> Optional[np.ndarray]:
        if self.tile_vectors is None or sid not in self.tile_slices:
            return None
        o, c = self.tile_slices[sid]
        return self.tile_vectors[o:o + c]

    def matrix(self, ids: list) -> np.ndarray:
        idx = self._index()
        return np.stack([self.slide_vectors[idx[i]] for i in ids])

    def _index(self) -> dict:
        if not hasattr(self, "_idx"):
            self._idx = {s: i for i, s in enumerate(self.slide_ids)}
        return self._idx

    @classmethod
    def load(cls, model_dir: str | Path, tiles: bool = False) -> "Embeddings":
        model_dir = Path(model_dir)
        rows = json.loads((model_dir / "slide-vectors.json").read_text())
        ids = [r["id"] for r in rows]
        sv = np.asarray([r["v"] for r in rows], dtype=np.float32)
        emb = cls(model=model_dir.name, dim=sv.shape[1], slide_ids=ids, slide_vectors=sv)
        meta_p = model_dir / "tile-meta.json"
        if meta_p.exists():
            meta = json.loads(meta_p.read_text())
            emb.license = meta.get("license")
            emb.tile_slices = {k: (v["offset"], v["count"]) for k, v in meta["slides"].items()}
            if tiles:
                n, d, scale = meta["tiles"], meta["dim"], meta.get("scale", 127)
                raw = np.fromfile(model_dir / "tile-vectors.i8", dtype=np.int8)
                emb.tile_vectors = (raw.reshape(n, d).astype(np.float32) / scale)
                emb.tile_coords = np.fromfile(model_dir / "tile-coords.u16", dtype="<u2").reshape(n, 2)
        return emb


@dataclass
class BiobaseData:
    root: Path
    slides: list
    organ_groups: list
    organ_to_group: dict

    # ---- loading -------------------------------------------------------
    @classmethod
    def load(cls, root: str | Path) -> "BiobaseData":
        root = Path(root)
        m = json.loads((root / "slides/pack_slides/slides_manifest.json").read_text())
        return cls(root=root, slides=[Slide.from_manifest(s) for s in m["slides"]],
                   organ_groups=list(m.get("organGroupList", [])), organ_to_group=dict(m.get("organGroups", {})))

    @property
    def by_id(self) -> dict:
        return {s.id: s for s in self.slides}

    @property
    def labelled(self) -> list:
        return [s for s in self.slides if s.labelled]

    @property
    def heldout(self) -> list:
        return [s for s in self.slides if s.heldout]

    def embeddings(self, model: str, tiles: bool = False) -> Embeddings:
        return Embeddings.load(self.root / "tiles/tilepack/embeddings" / model, tiles=tiles)

    def tiles_4um(self) -> list:
        base = self.root / "tiles/tilepack"
        return [Tile(r["slide_id"], base / r["file"], int(r["level"]), int(r["col"]), int(r["row"]), index=int(r["index"]))
                for r in _csv(base / "tiles.csv")]

    def tiles_05um(self, drop_blank: bool = True) -> list:
        base = self.root / "tiles-20x/tiles20x"
        blank = {r["file"]: r["kind"] for r in _csv(base / "blank_tiles.csv")} if (base / "blank_tiles.csv").exists() else {}
        out = []
        for r in _csv(base / "tiles20x.csv"):
            b = blank.get(r["file"])
            if drop_blank and b:
                continue
            out.append(Tile(r["slide_id"], base / r["file"], int(r["level"]), int(r["col"]), int(r["row"]),
                            um_per_px=float(r["um_per_px"]) if r.get("um_per_px") else None, blank=b))
        return out

    def thumbnail(self, sid: str) -> Path:
        return self.root / "thumbnails/thumbnails" / f"{sid}.jpg"


def _csv(p: Path) -> list:
    with open(p, newline="") as f:
        return list(csv.DictReader(f))
