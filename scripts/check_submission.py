#!/usr/bin/env python3
"""Check submission files before the freeze (issue #5). Standard library only.

  python3 scripts/check_submission.py --manifest data/biobase/pack_slides/slides_manifest.json \
      --organ runs/<id>/submission_slides_organ.csv --similar runs/<id>/submission_slides_similar.csv \
      [--criteria runs/<id>/submission_criteria.json --criteria-template <pack_reports>/submission_template_criteria.json \
       --reports-test <pack_reports>/test.jsonl] [--record runs/<id>/record.json]

C1 (slide_id,organ): exactly the held-out ids, once each; organ is a known organ name or organ group (any case).
C2 (query_slide_id,rank,result_slide_id): every held-out id is a query; ranks are 1..k with k <= 10, no gaps or
   repeats; no self-match; no repeated result per query; every result id is in the manifest.
Task A (JSON {criterion_id: [report ids]}): same keys as the template; ids are strings that exist in test.jsonl;
   no duplicates.
--record: each checked file's sha256 must equal the hash in that run record's outputs (by file name).

Prints one line per check and the sha256 of every file. Exit 0 when everything passes, 1 otherwise.
Prints no slide ids, labels or report text, only counts and hashes.
"""
import argparse, csv, hashlib, json, os, sys
from collections import defaultdict

problems = []


def bad(msg):
    problems.append(msg)
    print("  FAIL", msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_csv(path, header):
    with open(path, newline="") as f:
        r = csv.reader(f)
        got = next(r, None)
        if got != header:
            bad(f"{os.path.basename(path)}: header is {got}, expected {header}")
        return [row for row in r if row]


def check_organ(path, held, names):
    print(f"C1 {path}")
    rows = read_csv(path, ["slide_id", "organ"])
    ids = [r[0] for r in rows]
    if len(ids) != len(set(ids)):
        bad(f"C1: {len(ids) - len(set(ids))} duplicate slide ids")
    missing, extra = held - set(ids), set(ids) - held
    if missing:
        bad(f"C1: {len(missing)} held-out slides have no row")
    if extra:
        bad(f"C1: {len(extra)} rows are not held-out slides")
    unknown = sum(1 for r in rows if len(r) < 2 or r[1].strip().lower() not in names)
    if unknown:
        bad(f"C1: {unknown} organ values are not a known organ name or group")
    print(f"  {len(rows)} rows, {len(held & set(ids))} of {len(held)} held-out answered")


def check_similar(path, held, all_ids):
    print(f"C2 {path}")
    rows = read_csv(path, ["query_slide_id", "rank", "result_slide_id"])
    by_q = defaultdict(list)
    for r in rows:
        if len(r) != 3:
            bad(f"C2: a row has {len(r)} columns")
            continue
        try:
            by_q[r[0]].append((int(r[1]), r[2]))
        except ValueError:
            bad("C2: a rank is not an integer")
    if set(by_q) - held:
        bad(f"C2: {len(set(by_q) - held)} queries are not held-out slides")
    if held - set(by_q):
        bad(f"C2: {len(held - set(by_q))} held-out slides have no results")
    counts = defaultdict(int)
    for q, res in by_q.items():
        ranks = sorted(k for k, _ in res)
        if ranks != list(range(1, len(ranks) + 1)) or len(ranks) > 10:
            counts["ranks not 1..k (k<=10)"] += 1
        results = [t for _, t in res]
        if q in results:
            counts["self-match"] += 1
        if len(results) != len(set(results)):
            counts["repeated result"] += 1
        if any(t not in all_ids for t in results):
            counts["result id not in manifest"] += 1
    for what, n in counts.items():
        bad(f"C2: {n} queries with {what}")
    print(f"  {len(rows)} rows over {len(by_q)} queries")


def check_criteria(path, template_path, test_path):
    print(f"Task A {path}")
    sub, tmpl = json.load(open(path)), json.load(open(template_path))
    if not isinstance(sub, dict):
        bad("Task A: top level is not an object")
        return
    keys = set(tmpl) if isinstance(tmpl, dict) else set(tmpl)
    if set(sub) != keys:
        bad(f"Task A: {len(keys - set(sub))} template criteria missing, {len(set(sub) - keys)} unknown keys")
    valid = None
    if test_path:
        with open(test_path) as f:
            valid = {json.loads(line)["id"] for line in f if line.strip()}
    for cid, ids in sub.items():
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            bad(f"Task A: criterion {cid} is not a list of string ids")
            continue
        if len(ids) != len(set(ids)):
            bad(f"Task A: criterion {cid} has duplicate ids")
        if valid is not None and set(ids) - valid:
            bad(f"Task A: criterion {cid} has {len(set(ids) - valid)} ids not in test.jsonl")
    empty = sum(1 for v in sub.values() if isinstance(v, list) and not v)
    print(f"  {len(sub)} criteria, {sum(len(v) for v in sub.values() if isinstance(v, list))} ids, {empty} empty")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", help="slides_manifest.json (needed for C1/C2)")
    ap.add_argument("--organ")
    ap.add_argument("--similar")
    ap.add_argument("--criteria")
    ap.add_argument("--criteria-template")
    ap.add_argument("--reports-test", help="test.jsonl, to check that report ids exist")
    ap.add_argument("--record", help="run record whose outputs hashes must match")
    a = ap.parse_args(argv)
    problems.clear()

    files = []
    if a.organ or a.similar:
        if not a.manifest:
            ap.error("--manifest is required for C1/C2")
        m = json.load(open(a.manifest))
        slides = m["slides"]
        held = {s["id"] for s in slides if s.get("heldout")}
        all_ids = {s["id"] for s in slides}
        names = {g.lower() for g in m.get("organGroupList", [])} | {k.lower() for k in m.get("organGroups", {})}
        names |= {s["organ"].lower() for s in slides if s.get("organ")}
        if a.organ:
            check_organ(a.organ, held, names)
            files.append(a.organ)
        if a.similar:
            check_similar(a.similar, held, all_ids)
            files.append(a.similar)
    if a.criteria:
        if not a.criteria_template:
            ap.error("--criteria-template is required with --criteria")
        check_criteria(a.criteria, a.criteria_template, a.reports_test)
        files.append(a.criteria)
    if not files:
        ap.error("nothing to check")

    outs = {}
    if a.record:
        outs = json.load(open(a.record)).get("outputs", {})
    print("hashes")
    for p in files:
        h = sha256(p)
        print(f"  {h}  {p}")
        if a.record:
            want = (outs.get(os.path.basename(p)) or {}).get("sha256")
            if want is None:
                bad(f"{os.path.basename(p)} is not in the run record's outputs")
            elif want != h:
                bad(f"{os.path.basename(p)} hash differs from the run record")
    print("PASS" if not problems else f"FAIL ({len(problems)} problems)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
