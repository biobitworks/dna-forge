#!/usr/bin/env python3
"""Generate privacy-restricted-source, public-safe hash-only cross-node evidence.

Local raw challenge data and output rows are never copied into a receipt.
SHA-256 verifies byte identity only; equal predictions do not imply correct labels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

SCHEMA = "dnaforge.crossnode-enssvm.v1"
REQUIRED_INPUTS = {"slide_manifest", "gigapath_vectors", "hoptimus_vectors", "folds"}
REQUIRED_OUTPUTS = {
    "oof_organ.csv", "heldout_organ.csv", "heldout_similar.csv",
    "submission_slides_organ.csv", "submission_slides_similar.csv"
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def stable_json(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")

def require_sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("malformed SHA-256")
    return value

def role_of(path: str) -> str:
    p = Path(path)
    if p.name == "slides_manifest.json":
        return "slide_manifest"
    if p.name == "slide-vectors.json" and p.parent.name in {"gigapath", "hoptimus"}:
        return p.parent.name + "_vectors"
    if p.name == "folds.json":
        return "folds"
    raise ValueError("unexpected input role; refuse implicit attribution")

def summarise(record: Path, node: str) -> dict:
    if node not in {"magicPRObox", "magicSTUDIObox"}:
        raise ValueError("unrecognized node; refuse publishing arbitrary host data")
    r = json.loads(record.read_text())
    code = r.get("code", {})
    if r.get("status") != "ok" or code.get("dirty") is not False:
        raise ValueError("run is not successful or code is dirty")
    sha = require_sha(code.get("commit"))
    if r.get("config", {}).get("method") != "ens-svm":
        raise ValueError("unexpected training method")
    inputs = {}
    for path, metadata in r.get("inputs", {}).items():
        role = role_of(path)
        if role in inputs:
            raise ValueError("duplicated input role")
        src = Path(path)
        if not src.is_file():
            raise FileNotFoundError("input for role missing: " + role)
        live = digest(src.read_bytes())
        if live != require_sha(metadata.get("sha256")):
            raise ValueError("input rehash mismatch: " + role)
        inputs[role] = live
    if set(inputs) != REQUIRED_INPUTS:
        raise ValueError("missing or surplus input role: " + str(sorted(set(inputs)^REQUIRED_INPUTS)))
    out_meta = r.get("outputs", {})
    if set(out_meta) != REQUIRED_OUTPUTS:
        raise ValueError("missing/surplus output")
    outputs = {}
    sizes = {}
    for fname in sorted(REQUIRED_OUTPUTS):
        path = record.parent / fname
        if not path.is_file():
            raise FileNotFoundError("expected local output absent: " + fname)
        observed = digest(path.read_bytes())
        if observed != require_sha(out_meta[fname].get("sha256")):
            raise ValueError("output rehash mismatch: " + fname)
        outputs[fname] = observed
        sizes[fname] = path.stat().st_size
    metrics = r["metrics"]
    if metrics.get("answered") != 67 or metrics.get("n_labelled") != 190:
        raise ValueError("unexpected cohort counts")
    metric_names = ("oof_acc", "oof_p@1", "oof_p@5", "oof_p@10")
    scores = {x: float(metrics[x]) for x in metric_names}
    versions = {}
    for dist in ("numpy", "scikit-learn", "scipy"):
        try:
            versions[dist] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            versions[dist] = "UNKNOWN"
    # Deliberately exclude raw source paths, per-slide IDs, labels, run note text,
    # source usernames, private keys and all predictions.
    return {
        "schema": SCHEMA, "node": node, "run": record.parent.name,
        "source_commit": sha, "source_code_dirty": False,
        "method": "ens-svm", "config_sha256": digest(stable_json(r["config"])),
        "input_sha256": dict(sorted(inputs.items())),
        "output_sha256": outputs,
        "output_bytes": sizes,
        "development_metrics": scores,
        "labels": {"known_train_slides": 190, "unlabeled_heldout_slides": 67},
        "runtime": {"python": platform.python_version(), **versions},
        "verified": "LOCAL_REHASH_PASS",
        "claim_ceiling": "Cross-machine reproducibility only; hidden-test accuracy NOT_COMPUTED",
        "signing": "NOT_SIGNED", "mmr": "NOT_COMPUTED"
    }

def compare(a: dict, b: dict) -> dict:
    if a["node"] == b["node"]:
        raise ValueError("same machine cannot establish cross-machine reproduction")
    for x in (a,b):
        if x.get("schema") != SCHEMA or x.get("verified") != "LOCAL_REHASH_PASS":
            raise ValueError("unsupported or unverified local receipt")
        if x.get("source_code_dirty") is not False:
            raise ValueError("dirty code")
        if set(x.get("output_sha256", {})) != REQUIRED_OUTPUTS or set(x.get("input_sha256", {})) != REQUIRED_INPUTS:
            raise ValueError("required evidence absent")
        for h in list(x["input_sha256"].values()) + list(x["output_sha256"].values()):
            require_sha(h)
    checks = {k: a[k] == b[k] for k in ("source_commit","method","config_sha256",
                                       "input_sha256","output_sha256","output_bytes","development_metrics")}
    if not all(checks.values()):
        raise ValueError("CROSS_MACHINE_MISMATCH: " + str([k for k,v in checks.items() if not v]))
    return {
        "schema":"dnaforge.crossnode-comparison.v1",
        "nodes": sorted([a["node"],b["node"]]),
        "training_commit": a["source_commit"],
        "matching_checks": checks,
        "n_matching_outputs": len(REQUIRED_OUTPUTS),
        "output_sha256": dict(sorted(a["output_sha256"].items())),
        "development_metrics": a["development_metrics"],
        "input_sha256": a["input_sha256"],
        "environments": {x["node"]: x["runtime"] for x in (a,b)},
        "state": "OBSERVED_REPRODUCED_EXACT_BYTES",
        "official_hidden_test_metrics": "NOT_COMPUTED",
        "causal_claim": "NOT_SUPPORTED",
        "signing": "NOT_SIGNED",
        "mmr": "NOT_COMPUTED",
    }

def safe_write(dest: Path, obj: dict):
    payload = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    for forbidden in ("/Users/", "SUPP-", "report_text", "patient_id", "local_subject_lookup"):
        if forbidden in payload:
            raise ValueError("unsafe content in public receipt")
    if dest.exists():
        raise FileExistsError("append-only: refuse to overwrite existing receipt")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(payload)
    print("RECEIPT_WRITTEN",dest.name,"SHA256",digest(payload.encode()),"BYTES",len(payload.encode()))

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("summarize"); s.add_argument("--record",type=Path,required=True)
    s.add_argument("--node",required=True);s.add_argument("--out",type=Path,required=True)
    s=sub.add_parser("compare");s.add_argument("--magicpro",type=Path,required=True)
    s.add_argument("--magicstudio",type=Path,required=True);s.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if a.cmd=="summarize":
        safe_write(a.out,summarise(a.record,a.node))
    else:
        safe_write(a.out,compare(json.loads(a.magicpro.read_text()),json.loads(a.magicstudio.read_text())))

if __name__=="__main__":
    main()
