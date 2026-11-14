"""Chain of custody: hash inputs at ingest and record every run.

Nothing here stores data content. Records hold paths, sizes and SHA-256 hashes,
plus the code commit, command, host and metrics, so any result can be traced to
the exact bytes it came from.
"""
from __future__ import annotations

import datetime as _dt
import getpass
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Iterable

CHUNK = 1 << 20


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def host_info() -> dict:
    return {
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
    }


def git_state(repo: str | Path | None = None) -> dict:
    repo = str(repo or Path(__file__).resolve().parent.parent)

    def run(*args):
        try:
            return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    return {"commit": run("rev-parse", "HEAD") or None,
            "branch": run("rev-parse", "--abbrev-ref", "HEAD") or None,
            "dirty": bool(run("status", "--porcelain"))}


def hash_tree(root: str | Path, files: Iterable[Path] | None = None) -> dict:
    """Hash every file under root. Returns {relative path: {bytes, sha256}} and a tree digest."""
    root = Path(root)
    paths = sorted(files) if files is not None else sorted(p for p in root.rglob("*") if p.is_file())
    entries = {}
    for p in paths:
        rel = p.relative_to(root).as_posix()
        entries[rel] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    digest = hashlib.sha256("".join(f"{k}\t{v['sha256']}\n" for k, v in entries.items()).encode()).hexdigest()
    return {"files": entries, "count": len(entries), "tree_sha256": digest}


def ingest(sources: list[str | Path], extracted_root: str | Path, out: str | Path) -> dict:
    """Hash source archives and the extracted tree, and write a custody manifest."""
    extracted_root = Path(extracted_root)
    record = {
        "kind": "ingest",
        "id": str(uuid.uuid4()),
        "time": now(),
        "host": host_info(),
        "code": git_state(),
        "sources": {Path(s).name: {"bytes": Path(s).stat().st_size, "sha256": sha256_file(s),
                                   "mtime": _dt.datetime.fromtimestamp(Path(s).stat().st_mtime, _dt.timezone.utc).isoformat(timespec="seconds")}
                    for s in sources},
        "extracted": {},
    }
    for sub in sorted(p for p in extracted_root.iterdir() if p.is_dir()):
        t = hash_tree(sub)
        record["extracted"][sub.name] = t
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(record, indent=1, sort_keys=True))
    return record


def verify(manifest: str | Path, extracted_root: str | Path) -> list[str]:
    """Re-hash the extracted tree and return a list of mismatches (empty means intact)."""
    rec = json.loads(Path(manifest).read_text())
    problems = []
    for sub, tree in rec["extracted"].items():
        base = Path(extracted_root) / sub
        for rel, meta in tree["files"].items():
            p = base / rel
            if not p.exists():
                problems.append(f"missing: {sub}/{rel}")
            elif sha256_file(p) != meta["sha256"]:
                problems.append(f"changed: {sub}/{rel}")
    return problems


class RunRecord:
    """Context manager that writes runs/<id>/record.json for one run.

        with RunRecord("knn-gigapath", config={...}, inputs=[paths]) as run:
            ...
            run.metrics["c1_loo_acc"] = 0.79
            run.output(path_to_submission_csv)
    """

    def __init__(self, name: str, config: dict | None = None, inputs: Iterable[str | Path] = (),
                 runs_dir: str | Path = "runs"):
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.id = f"{stamp}-{name}"
        self.dir = Path(runs_dir) / self.id
        self.config = config or {}
        self.inputs = [Path(p) for p in inputs]
        self.metrics: dict = {}
        self.outputs: dict = {}
        self.notes: list[str] = []

    def output(self, path: str | Path) -> Path:
        path = Path(path)
        self.outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        return path

    def __enter__(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        self.start = now()
        return self

    def __exit__(self, exc_type, exc, tb):
        rec = {
            "kind": "run", "id": self.id, "start": self.start, "end": now(),
            "status": "error" if exc_type else "ok", "error": repr(exc) if exc else None,
            "command": sys.argv, "host": host_info(), "code": git_state(), "config": self.config,
            "inputs": {str(p): {"bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in self.inputs if p.exists()},
            "metrics": self.metrics, "outputs": self.outputs, "notes": self.notes,
        }
        (self.dir / "record.json").write_text(json.dumps(rec, indent=1, sort_keys=True, default=str))
        return False
