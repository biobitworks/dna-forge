#!/usr/bin/env python3
"""Fail if challenge data would end up in git. See DATA_POLICY.md.

Usage:
    python3 scripts/check_no_data.py            # check files tracked by git
    python3 scripts/check_no_data.py PATH ...   # check only these paths
    python3 scripts/check_no_data.py --allow-ids  # skip the slide id check

Checks:
  1. Path matches a blocked pattern (mirrors .gitignore plus common
     slide, array and model formats).
  2. File is larger than 1 MB.
  3. Text file contains a slide-id-like string. Exempt: custody/*.json,
     runs/<run-id>/record.json, *.csv under runs/<run-id>/ (submissions
     such as organ.csv, similar.csv), and any file whose first line
     contains the marker "data-guard: allow".
"""
import fnmatch
import os
import re
import subprocess
import sys

BLOCKED_DIRS = ("data", "biobase")
BLOCKED_GLOBS = (
    "*.zip", "*.jpg", "*.jpeg", "*.png", "*.dzi", "*.i8", "*.u16",
    "slide-vectors.json", "tile-meta.json", "points.json", "*.jsonl",
    "*.svs", "*.tif", "*.tiff", "*.ndpi", "*.npy", "*.npz",
    "*.pt", "*.pth", "*.safetensors", "*.parquet",
)
MAX_BYTES = 1024 * 1024
SLIDE_ID = re.compile(r"SUPP-\d\d-biobase_[0-9a-f-]{36}")
ALLOW_MARKER = "data-guard: allow"


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True,
                         check=True).stdout
    return [p for p in out.decode("utf-8", "replace").split("\0") if p]


def blocked_reason(path):
    parts = path.replace(os.sep, "/").split("/")
    for d in BLOCKED_DIRS:
        if d in parts[:-1]:
            return "inside blocked directory '%s/'" % d
    name = parts[-1].lower()
    for g in BLOCKED_GLOBS:
        if fnmatch.fnmatch(name, g):
            return "matches blocked pattern '%s'" % g
    return None


def id_exempt(path):
    p = os.path.normpath(path).replace(os.sep, "/")
    if p.startswith("custody/") and p.endswith(".json"):
        return True  # ingest records: names and hashes only
    parts = p.split("/")
    if parts[0] == "runs" and len(parts) >= 3:
        # run records and small submission CSVs (size is checked first)
        return parts[-1] == "record.json" or parts[-1].endswith(".csv")
    return False


def check(path, allow_ids):
    problems = []
    reason = blocked_reason(path)
    if reason:
        problems.append(reason)
    if not os.path.isfile(path):
        return problems  # tracked but deleted in the working tree
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        problems.append("larger than 1 MB (%d bytes)" % size)
        return problems
    if allow_ids or id_exempt(path):
        return problems
    with open(path, "rb") as f:
        raw = f.read()
    if b"\0" in raw[:8192]:
        return problems  # binary; size and pattern checks cover it
    text = raw.decode("utf-8", "replace")
    if ALLOW_MARKER in text.split("\n", 1)[0]:
        return problems
    for lineno, line in enumerate(text.splitlines(), 1):
        if SLIDE_ID.search(line):
            problems.append("slide-id-like string on line %d" % lineno)
            break
    return problems


def main(argv):
    allow_ids = "--allow-ids" in argv
    paths = [a for a in argv if a != "--allow-ids"]
    if not paths:
        try:
            paths = tracked_files()
        except (OSError, subprocess.CalledProcessError) as e:
            print("data-guard: could not run 'git ls-files': %s" % e)
            return 2
    failures = 0
    for p in paths:
        for msg in check(p, allow_ids):
            print("BLOCKED %s: %s" % (p, msg))
            failures += 1
    if failures:
        print("\ndata-guard: %d problem(s) in %d file(s) checked. Challenge"
              " data must not be committed; see DATA_POLICY.md." %
              (failures, len(paths)))
        return 1
    print("data-guard: OK, %d file(s) checked." % len(paths))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
