import json, numpy as np
from pathlib import Path
D = Path(__file__).parent.parent / "data"
MODELS = ["dinov2", "hoptimus", "biomedclip", "gigapath"]

def manifest():
    return json.load(open(D / "pack_slides/slides_manifest.json"))["slides"]

def vectors(model):
    return {r["id"]: np.asarray(r["v"], dtype=np.float32) for r in json.load(open(D / f"embeddings/{model}/slide-vectors.json"))}

def l2(X):
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)

def matrix(ids, models):
    """Concatenate per-model L2-normalised (and mean-centred) vectors; missing slide -> zeros for that block."""
    blocks = []
    for m in models:
        V = vectors(m); dim = len(next(iter(V.values())))
        mu = np.mean(np.stack(list(V.values())), 0)
        B = np.stack([V[i] - mu if i in V else np.zeros(dim, np.float32) for i in ids])
        blocks.append(l2(B) / np.sqrt(len(models)))
    return np.hstack(blocks)
