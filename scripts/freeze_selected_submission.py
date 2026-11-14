#!/usr/bin/env python3
"""Preserve an exact, authorized pre-key candidate with local and safe receipts.

No key / reference answers are opened. Local OS clock observations are
not a trusted timestamp, signature, or cryptographically committed MMR.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

from verify_selected_submission import EXPECTED, verify

IDENTITY = "dnaforge.prekey-selected-snapshot.v1"
CUTOFF = datetime(2026, 11, 14, 16, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
SAFE_BASENAME = "20261114_prekey_selected_receipt.json"

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def dump_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False, ensure_ascii=False) + "\n").encode("utf-8")

def clock_gate(now: datetime):
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone-aware clock required")
    if now.astimezone(timezone.utc) >= CUTOFF.astimezone(timezone.utc):
        raise ValueError("pre-key cutoff passed; refuse to create freeze")
    if now.year != 2026 or now.month != 11 or now.day != 14:
        raise ValueError("wrong day for this exact event")
    return now.astimezone(timezone.utc).isoformat()

def freeze(source: Path, snapshot: Path, local_receipt: Path, public_receipt: Path,
           revision: str, now: datetime):
    observed_utc = clock_gate(now)
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("invalid Git SHA-1 identity")
    if any(x.exists() or x.is_symlink() for x in (snapshot, local_receipt, public_receipt)):
        raise FileExistsError("append-only: destination already exists")
    if not source.is_dir() or source.is_symlink():
        raise ValueError("selected source folder unavailable")
    source_files = verify(source, EXPECTED)
    snapshot.mkdir(parents=True, exist_ok=False, mode=0o700)
    observed = {}
    for name in sorted(EXPECTED):
        original = source / name
        target = snapshot / name
        shutil.copyfile(original, target)
        target.chmod(0o400)
        actual = sha256_bytes(target.read_bytes())
        if actual != EXPECTED[name]:
            raise ValueError("copy verification failed: " + name)
        observed[name] = {"sha256":actual,"bytes":target.stat().st_size}
    if observed != source_files:
        raise ValueError("snapshot and selected originals differ")
    # Realize the local public copy before the clock boundary, but do not
    # pretend local process or Git timestamps are trusted attestation.
    clock_gate(datetime.now(timezone.utc))
    record = {
        "schema": IDENTITY,
        "event_date": "2026-11-14",
        "observed_utc": observed_utc,
        "clock_source": "local_system_clock_untrusted",
        "deadline_local": "2026-11-14T16:00:00-08:00",
        "code_commit": revision,
        "source": "selected_candidate_on_authorized_magicPRObox",
        "source_verification": "SHA256_MATCHED_ORIGINAL_SELECTED_3_OF_3",
        "snapshot_verification": "SHA256_MATCHED_READONLY_COPY_3_OF_3",
        "submission": observed,
        "organizer_scoring": "NOT_COMPUTED",
        "organizer_submission": "NOT_VERIFIED",
        "official_answer_key": "NOT_ACCESSED",
        "signature": "NOT_SIGNED",
        "mmr_commitment": "NOT_COMPUTED",
        "status": "LOCAL_PREKEY_SNAPSHOT_OBSERVED",
    }
    local_data = {**record, "restricted_snapshot": str(snapshot),
                  "restricted_original": str(source),
                  "execution_host": "magicPRObox"}
    public_data = dump_bytes(record)
    local_bytes = dump_bytes(local_data)
    if b"/Users/" in public_data or b"SUPP-" in public_data:
        raise ValueError("private identity leaked into public receipt")
    for dest, data in ((local_receipt,local_bytes),(public_receipt,public_data)):
        dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with dest.open("xb") as f: f.write(data)
        dest.chmod(0o600)
    return {
        "public_sha256":sha256_bytes(public_data),
        "local_sha256":sha256_bytes(local_bytes),
        "observed_utc":observed_utc,
        "files":observed,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--snapshot",required=True,type=Path)
    p.add_argument("--local-receipt",required=True,type=Path)
    p.add_argument("--public-receipt",required=True,type=Path)
    p.add_argument("--source-commit",required=True)
    a=p.parse_args()
    now=datetime.now(timezone.utc)
    evidence=freeze(a.source,a.snapshot,a.local_receipt,a.public_receipt,a.source_commit,now)
    print("PREKEY_SNAPSHOT_PASS",evidence["observed_utc"])
    print("PUBLIC_RECEIPT_SHA256",evidence["public_sha256"])
    for name,x in evidence["files"].items():
        print("MATCH",name,x["sha256"],x["bytes"])
    print("LOCALLY_OBSERVED_ONLY_NOT_SIGNED_NO_OFFICIAL_KEY_NO_MMR")

if __name__=="__main__":
    main()
