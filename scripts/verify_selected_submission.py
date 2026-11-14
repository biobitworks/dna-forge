#!/usr/bin/env python3
"""Read-only exact SHA-256 check of selected local submission candidates.

Bytes are checked without changing files. This is not a signature, a
submission receipt, or an official accuracy measurement.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

EXPECTED = {
    "submission_criteria.json": "1604ae1557ffad8e39c671a193fec113653984f2e8bf090791f5a15b62d88345",
    "submission_slides_organ.csv": "8a69914d27c707c8a61694c8d8123f2139141cd5b79ac358193dda5da4cf7356",
    "submission_slides_similar.csv": "ed38172b0075b0415fcce2866a3c68d55a1214e578d0ddc97c19c070fb90d423",
}

def verify(directory: Path, expected: dict) -> dict:
    if not directory.is_dir():
        raise FileNotFoundError("authorized directory missing")
    if not expected:
        raise ValueError("empty digest list")
    out = {}
    for name, expected_sha in sorted(expected.items()):
        if Path(name).name != name or len(expected_sha) != 64:
            raise ValueError("invalid expectation")
        p=directory/name
        if not p.is_file() or p.is_symlink():
            raise FileNotFoundError("required file absent or symlinked: "+name)
        h=hashlib.sha256()
        with p.open("rb") as f:
            while True:
                part=f.read(1024*1024)
                if not part:break
                h.update(part)
        if h.hexdigest()!=expected_sha:
            raise ValueError("MISMATCH: "+name)
        out[name]={"sha256":h.hexdigest(),"bytes":p.stat().st_size}
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",required=True,type=Path)
    a=p.parse_args()
    for name,data in verify(a.directory,EXPECTED).items():
        print("MATCH",name,data["sha256"],data["bytes"])
    print("SELECTED_OUTPUT_IDENTITY_PASS; OFFICIAL_SCORE_NOT_COMPUTED; NOT_SIGNED")

if __name__=="__main__":
    main()
