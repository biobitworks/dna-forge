"""Fractal custody objects (FCO) and fractal custody graphs (FCG), minimal mechanics for this challenge.

Exported as W3C PROV-O in JSON-LD (custody/fcg.prov.jsonld) so any knowledge-graph tool can load it.
Hashing is standard: canonical JSON plus an RFC 6962-style Merkle tree.
  canonical JSON  json.dumps(sort_keys, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
  leaf            sha256(0x00 || data)
  node            sha256(0x01 || left_hex + right_hex)
  FCG root        Merkle root over the SORTED hashes of its member FCOs; an FCG is itself an FCO,
                  so it can be a member of a parent FCG (file -> pack -> dataset -> session).
Admission is reject-not-annotate: a member with a problem is refused, never added with a warning.
Wall-clock times are not hashed.

Blinding: slide ids become tokens  fco-<16 hex> = HMAC-SHA256(key, id). The key lives in custody/local/
(gitignored); only its commitment sha256(key) is public. Modellers get tokens in a seeded random order
(tokenize, randomize); the label custodian file maps token -> label separately (double blind). Real ids
come back only when writing submission CSVs.

  python -m dnaforge.fcg build   # custody/fcg.json + fcg.prov.jsonld (public) and custody/local/fcg-full.*
  python -m dnaforge.fcg blind   # custody/local/blind/{modeller.csv, custodian.csv, unblind.csv}
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import random
import secrets
from pathlib import Path


def canonical(v) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def leaf(data: bytes) -> str:
    return hashlib.sha256(b"\x00" + data).hexdigest()


def node(left: str, right: str) -> str:
    return hashlib.sha256(b"\x01" + (left + right).encode("ascii")).hexdigest()


def merkle(hashes: list) -> str:
    level = sorted(hashes)
    if not level:
        return leaf(b"")
    while len(level) > 1:
        nxt = [node(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
        if len(level) % 2:
            nxt.append(level[-1])
        level = nxt
    return level[0]


def fco(kind: str, identity: dict, **props) -> dict:
    if not kind or not isinstance(identity, dict) or not identity:
        raise ValueError("FCO needs a kind and a non-empty identity")
    return {"kind": kind, "identity": identity, "hash": leaf(canonical({"kind": kind, **identity})), **props}


def fcg(name: str, members: list, kind: str = "fcg") -> dict:
    """Admit members (reject-not-annotate) and return the graph as an FCO of its own."""
    seen = set()
    for m in members:
        if "hash" not in m or m["hash"] != leaf(canonical({"kind": m["kind"], **m["identity"]})):
            raise ValueError(f"rejected member of {name}: hash does not match identity ({m.get('kind')})")
        if m["hash"] in seen:
            raise ValueError(f"rejected member of {name}: duplicate {m['hash'][:12]}")
        seen.add(m["hash"])
    root = merkle([m["hash"] for m in members])
    g = fco(kind, {"name": name, "root": root, "count": len(members)})
    g["members"] = members
    return g


# ---- tokens ---------------------------------------------------------------
def load_key(path="custody/local/fco.key") -> bytes:
    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(secrets.token_bytes(32))
        p.chmod(0o600)
    return p.read_bytes()


def token(key: bytes, value: str) -> str:
    return "fco-" + hmac.new(key, value.encode(), hashlib.sha256).hexdigest()[:16]


def commitment(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()


# ---- build from custody records -------------------------------------------
def build(custody_dir="custody", runs_dir="runs", key: bytes | None = None) -> dict:
    custody_dir = Path(custody_dir)
    key = key or load_key(custody_dir / "local/fco.key")
    datasets = []
    for m in sorted((custody_dir / "local").glob("ingest-*.json")):
        rec = json.loads(m.read_text())
        archives = [fco("archive", {"name": k, "sha256": v["sha256"], "bytes": v["bytes"]})
                    for k, v in sorted(rec.get("sources", {}).items())]
        packs = []
        for pack, tree in sorted(rec.get("extracted", {}).items()):
            files = [fco("file", {"path": token(key, f"{pack}/{rel}"), "sha256": meta["sha256"], "bytes": meta["bytes"]})
                     for rel, meta in sorted(tree["files"].items())]
            packs.append(fcg(pack, files, kind="pack"))
        datasets.append(fcg(m.stem, archives + packs, kind="dataset"))
    runs, edges = [], []
    file_index = {f["identity"]["sha256"]: f["hash"] for d in datasets for p in d["members"] if p["kind"] == "pack" for f in p["members"]}
    for r in sorted(Path(runs_dir).glob("*/record.json")):
        rec = json.loads(r.read_text())
        ident = {"name": rec.get("id", r.parent.name), "commit": (rec.get("code") or {}).get("commit"),
                 "config_sha256": leaf(canonical(rec.get("config", {}))),
                 "inputs": sorted(v["sha256"] for v in rec.get("inputs", {}).values()),
                 "outputs": sorted(v["sha256"] for v in rec.get("outputs", {}).values()),
                 "metrics_sha256": leaf(canonical(rec.get("metrics", {})))}
        run = fco("run", ident, node=(rec.get("host") or {}).get("hostname"))
        runs.append(run)
        for s in ident["inputs"]:
            edges.append({"type": "USED_BY", "src": file_index.get(s, s), "dst": run["hash"]})
        for s in ident["outputs"]:
            edges.append({"type": "PRODUCED", "src": run["hash"], "dst": s})
    session = fcg("dna-forge-session", datasets + runs, kind="session")
    session["edges"] = edges
    session["key_commitment"] = commitment(key)
    return session


def public(g: dict) -> dict:
    """Roots and counts only: what the public repo can hold."""
    def strip(m):
        out = {"kind": m["kind"], "hash": m["hash"]}
        if "members" in m:
            out.update(name=m["identity"]["name"], root=m["identity"]["root"], count=m["identity"]["count"])
            if m["kind"] != "pack":
                out["members"] = [strip(x) for x in m["members"]]
        elif m["kind"] in ("run", "archive"):
            out["identity"] = m["identity"]
        return out
    return {**strip(g), "key_commitment": g["key_commitment"], "edges": len(g.get("edges", []))}


# ---- W3C PROV-O / JSON-LD export -----------------------------------------
PROV_CONTEXT = {"prov": "http://www.w3.org/ns/prov#", "dcterms": "http://purl.org/dc/terms/",
                "fcg": "https://github.com/biobitworks/dna-forge/ns/fcg#", "xsd": "http://www.w3.org/2001/XMLSchema#"}


def to_prov(g: dict, include_files: bool = False) -> dict:
    """PROV-O JSON-LD: graphs and files are prov:Entity (graphs also prov:Collection with prov:hadMember),
    runs are prov:Activity linked by prov:used / prov:wasGeneratedBy. Ids are urn:sha256:<hash>."""
    items = []
    uid = lambda h: f"urn:sha256:{h}"

    def add(m):
        e = {"@id": uid(m["hash"]), "fcg:kind": m["kind"]}
        if m["kind"] == "run":
            e["@type"] = "prov:Activity"
            e["dcterms:identifier"] = m["identity"]["name"]
            e["prov:used"] = [{"@id": uid(x)} for x in m["identity"]["inputs"]]
            if m.get("node"):
                e["prov:wasAssociatedWith"] = {"@id": f"fcg:node/{m['node']}"}
            for o in m["identity"]["outputs"]:
                items.append({"@id": uid(o), "@type": "prov:Entity", "fcg:kind": "output",
                              "prov:wasGeneratedBy": {"@id": uid(m["hash"])}})
        else:
            e["@type"] = ["prov:Entity", "prov:Collection"] if "members" in m else "prov:Entity"
            ident = m["identity"]
            for k in ("name", "root", "count", "sha256", "bytes"):
                if k in ident:
                    e[f"fcg:{k}"] = ident[k]
            if "members" in m and (include_files or m["kind"] != "pack"):
                e["prov:hadMember"] = [{"@id": uid(x["hash"])} for x in m["members"]]
                for x in m["members"]:
                    add(x)
        items.append(e)
    add(g)
    return {"@context": PROV_CONTEXT, "@graph": items, "fcg:keyCommitment": g.get("key_commitment")}


# ---- blinding -------------------------------------------------------------
def blind(root: str | Path, out_dir="custody/local/blind", seed: int = 0, key_path="custody/local/fco.key") -> dict:
    from .data import BiobaseData
    data = BiobaseData.load(Path(root).expanduser())
    key = load_key(key_path)
    rows = [(token(key, s.id), s) for s in data.slides]
    random.Random(seed).shuffle(rows)                      # randomize
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    with open(out / "modeller.csv", "w", newline="") as f:  # what modellers see
        w = csv.writer(f); w.writerow(["token", "task"])
        w.writerows((t, "predict" if s.heldout else "train") for t, s in rows)
    with open(out / "custodian.csv", "w", newline="") as f:  # what the label custodian holds
        w = csv.writer(f); w.writerow(["token", "organ_group"])
        w.writerows((t, s.organ_group or "") for t, s in rows if s.labelled)
    with open(out / "unblind.csv", "w", newline="") as f:   # only used to write the submission files
        w = csv.writer(f); w.writerow(["token", "slide_id"]); w.writerows((t, s.id) for t, s in rows)
    return {"tokens": len(rows), "seed": seed, "key_commitment": commitment(key),
            "token_set_root": merkle([leaf(t.encode()) for t, _ in rows])}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["build", "blind"])
    p.add_argument("--root", default="~/dna-forge/biobase")
    p.add_argument("--custody", default="custody")
    p.add_argument("--runs", default="runs")
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args(argv)
    if a.cmd == "build":
        g = build(a.custody, a.runs)
        Path(a.custody, "local").mkdir(parents=True, exist_ok=True)
        Path(a.custody, "local/fcg-full.json").write_text(json.dumps(g, indent=1))
        Path(a.custody, "fcg.json").write_text(json.dumps(public(g), indent=1))
        Path(a.custody, "fcg.prov.jsonld").write_text(json.dumps(to_prov(g), indent=1))
        Path(a.custody, "local/fcg-full.prov.jsonld").write_text(json.dumps(to_prov(g, include_files=True), indent=1))
        print(f"FCG session root {g['identity']['root'][:16]}: {g['identity']['count']} members, "
              f"{len(g['edges'])} edges -> {a.custody}/fcg.json")
    else:
        r = blind(a.root, seed=a.seed, key_path=Path(a.custody) / "local/fco.key")
        Path(a.custody, "blind.json").write_text(json.dumps(r, indent=1))
        print(f"blinded {r['tokens']} slides, token set root {r['token_set_root'][:16]} -> custody/local/blind/")


if __name__ == "__main__":
    main()
