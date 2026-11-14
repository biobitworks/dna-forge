"""HistAI metadata enrichment: filter gynecologic cases, dedupe, and emit custody/knowledge-graph objects.

Source: the HistAI WSI collection's case metadata (metadata.json, a JSON array linked from the dataset
README, CC BY-NC 4.0). Each record has diagnosis, conclusion, diff_diagnostic, grossing, micro_protocol,
icd10, age, gender, case_mapping (histai/<subset>/case_<n>), additional_info and specialization.

Categories (a case can carry several tags):
  endometriosis      icd10 N80.*  or text endometrio(sis|ma|tic cyst), adenomyosis
  pre-endometriosis  endometrial hyperplasia / atypia (N85.0, N85.1), adenomyosis, endometrial polyp (N84.0)
  pcos               icd10 E28.2  or text polycystic ovar*, Stein-Leventhal
  uterus             uterine / endometrial / cervical / myometrial codes (C53-C55, D06, D25, D26, N71-N72,
                     N84-N87) or uterus terms in diagnosis / conclusion / grossing
  diagnostic         uterine-tagged cases taken for diagnosis: biopsy, curettage, scraping, aspiration,
                     hysteroscopy (as opposed to resection specimens)

Dedupe runs in two passes:
  1. exact:   the same case_mapping appearing more than once (kept once)
  2. content: different case_mapping but identical normalised (diagnosis, conclusion, micro_protocol,
              age, gender, icd10); kept as one cluster with all case ids listed, as candidate
              re-submissions or the same patient sampled twice. The cluster is the knowledge-graph entity.

Outputs:
  <out>/histai-gyn.jsonl            full filtered records + tags + cluster id  (local / magicROCKETbox only)
  custody/histai-gyn.json           public: counts, per-category Merkle roots, cluster hashes, no free text
  custody/histai-gyn.prov.jsonld    public: PROV-O + ICD-10 links (case ids, codes, tags; no report text)

  python -m dnaforge.histai metadata.json --out /Volumes/magicROCKETbox/dna-forge/histai
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from . import fcg as F

ICD_URI = "http://id.who.int/icd/release/10/"

CODE_RULES = {
    "endometriosis": [r"^N80"],
    "pre-endometriosis": [r"^N85\.?[01]", r"^N84\.?0", r"^N80\.?0"],
    "pcos": [r"^E28\.?2"],
    "uterus": [r"^C5[345]", r"^D06", r"^D2[56]", r"^N7[12]", r"^N8[4-7]", r"^N80"],
}
TEXT_RULES = {
    "endometriosis": r"endometrio(sis|ma|tic|id cyst)|chocolate cyst|adenomyo",
    "pre-endometriosis": r"endometrial (hyperplasia|intraepithelial|polyp)|atypical hyperplasia|adenomyo",
    "pcos": r"polycystic ovar|stein.leventhal|\bpcos\b",
    "uterus": r"\buter(us|ine)\b|endometri|myometri|\bcervi(x|cal)\b|cervical canal|corpus uteri|leiomyom",
}
DIAGNOSTIC = r"biops|curettage|scraping|aspirat|hysteroscop|pipelle|endometrial sampling"
TEXT_FIELDS = ("diagnosis", "conclusion", "diff_diagnostic", "grossing", "additional_info")


def norm(s) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def codes(rec) -> list:
    raw = rec.get("icd10") or ""
    parts = raw if isinstance(raw, list) else re.split(r"[,;\s]+", str(raw))
    return [p.strip().upper() for p in parts if p.strip()]


def tags(rec) -> list:
    cs = codes(rec)
    text = " ".join(str(rec.get(f) or "") for f in TEXT_FIELDS).lower()
    out = set()
    for tag, pats in CODE_RULES.items():
        if any(re.match(p, c) for p in pats for c in cs):
            out.add(tag)
    for tag, pat in TEXT_RULES.items():
        if re.search(pat, text):
            out.add(tag)
    if out & {"endometriosis", "pre-endometriosis"}:
        out.add("uterus")
    if "uterus" in out and re.search(DIAGNOSTIC, text + " " + str(rec.get("micro_protocol") or "").lower()):
        out.add("diagnostic")
    return sorted(out)


def content_key(rec) -> str:
    key = [norm(rec.get(f)) for f in ("diagnosis", "conclusion", "micro_protocol")]
    key += [str(rec.get("age") or ""), norm(rec.get("gender")), ",".join(sorted(codes(rec)))]
    return hashlib.sha256(F.canonical(key)).hexdigest()


def load(path) -> list:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else list(data.values())


def select(records: list) -> dict:
    """Filter, dedupe and cluster. Returns {"clusters": [...], "stats": {...}}."""
    stats = Counter(total=len(records))
    seen_case = set()
    clusters = {}
    for rec in records:
        t = tags(rec)
        if not t:
            continue
        stats["matched"] += 1
        case = rec.get("case_mapping") or ""
        if case and case in seen_case:
            stats["dup_exact"] += 1
            continue
        seen_case.add(case)
        k = content_key(rec)
        c = clusters.get(k)
        if c is None:
            clusters[k] = {"content_sha256": k, "cases": [case], "tags": t, "icd10": codes(rec),
                           "age": rec.get("age"), "gender": rec.get("gender"),
                           "specialization": rec.get("specialization"), "record": rec}
        else:
            stats["dup_content"] += 1
            c["cases"].append(case)
            c["tags"] = sorted(set(c["tags"]) | set(t))
    out = sorted(clusters.values(), key=lambda c: c["content_sha256"])
    for c in out:
        c["cases"].sort()
    stats["clusters"] = len(out)
    by_tag = Counter(t for c in out for t in c["tags"])
    return {"clusters": out, "stats": dict(stats), "by_tag": dict(sorted(by_tag.items()))}


def case_fco(c) -> dict:
    ident = {"content_sha256": c["content_sha256"], "cases": c["cases"], "icd10": c["icd10"], "tags": c["tags"]}
    return F.fco("histai-case", ident)


def graph(sel: dict, source_sha256: str) -> dict:
    by_tag = defaultdict(list)
    for c in sel["clusters"]:
        for t in c["tags"]:
            by_tag[t].append(case_fco(c))
    cats = [F.fcg(f"histai-gyn/{t}", ms, kind="category") for t, ms in sorted(by_tag.items())]
    g = F.fcg("histai-gyn", cats, kind="dataset")
    g["identity_source"] = {"metadata_sha256": source_sha256, "licence": "CC-BY-NC-4.0"}
    return g


def public(g: dict, sel: dict) -> dict:
    return {"name": g["identity"]["name"], "root": g["identity"]["root"], "source": g["identity_source"],
            "stats": sel["stats"], "by_tag": sel["by_tag"],
            "categories": {m["identity"]["name"]: {"root": m["identity"]["root"], "count": m["identity"]["count"]}
                           for m in g["members"]},
            "clusters": [c["content_sha256"] for c in sel["clusters"]]}


def to_prov(g: dict, sel: dict) -> dict:
    uid = lambda h: f"urn:sha256:{h}"
    items, codes_seen = [], set()
    src = {"@id": uid(g["identity_source"]["metadata_sha256"]), "@type": "prov:Entity",
           "fcg:kind": "source", "dcterms:license": "https://creativecommons.org/licenses/by-nc/4.0/",
           "dcterms:title": "HistAI WSI collection case metadata"}
    items.append(src)
    items.append({"@id": uid(g["hash"]), "@type": ["prov:Entity", "prov:Collection"], "fcg:kind": "dataset",
                  "fcg:root": g["identity"]["root"], "prov:wasDerivedFrom": {"@id": src["@id"]},
                  "prov:hadMember": [{"@id": uid(m["hash"])} for m in g["members"]]})
    for cat in g["members"]:
        items.append({"@id": uid(cat["hash"]), "@type": ["prov:Entity", "prov:Collection"], "fcg:kind": "category",
                      "dcterms:identifier": cat["identity"]["name"], "fcg:count": cat["identity"]["count"],
                      "prov:hadMember": [{"@id": uid(m["hash"])} for m in cat["members"]]})
    for c in sel["clusters"]:
        m = case_fco(c)
        items.append({"@id": uid(m["hash"]), "@type": "prov:Entity", "fcg:kind": "histai-case",
                      "dcterms:identifier": c["cases"], "fcg:contentSha256": c["content_sha256"],
                      "fcg:tag": c["tags"], "prov:wasDerivedFrom": {"@id": src["@id"]},
                      "dcterms:subject": [{"@id": ICD_URI + code} for code in c["icd10"]]})
        codes_seen.update(c["icd10"])
    for code in sorted(codes_seen):
        items.append({"@id": ICD_URI + code, "@type": "skos:Concept", "skos:notation": code,
                      "skos:inScheme": {"@id": ICD_URI}})
    ctx = dict(F.PROV_CONTEXT)
    ctx.setdefault("skos", "http://www.w3.org/2004/02/skos/core#")
    ctx.setdefault("dcterms", "http://purl.org/dc/terms/")
    return {"@context": ctx, "@graph": items}


def main(argv=None):
    p = argparse.ArgumentParser(prog="dnaforge.histai", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("metadata")
    p.add_argument("--out", required=True, help="local folder for the full filtered records (not the repo)")
    p.add_argument("--custody", default="custody")
    a = p.parse_args(argv)
    from .custody import sha256_file
    src_sha = sha256_file(Path(a.metadata))
    sel = select(load(a.metadata))
    g = graph(sel, src_sha)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    with open(out / "histai-gyn.jsonl", "w", encoding="utf-8") as f:
        for c in sel["clusters"]:
            f.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    cd = Path(a.custody); cd.mkdir(parents=True, exist_ok=True)
    (cd / "histai-gyn.json").write_text(json.dumps(public(g, sel), indent=1, sort_keys=True))
    (cd / "histai-gyn.prov.jsonld").write_text(json.dumps(to_prov(g, sel), indent=1, sort_keys=True))
    print(json.dumps({"source_sha256": src_sha, "root": g["identity"]["root"], **sel["stats"],
                      "by_tag": sel["by_tag"]}, indent=1))


if __name__ == "__main__":
    main()
