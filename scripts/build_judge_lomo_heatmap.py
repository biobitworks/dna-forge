#!/usr/bin/env python3
"""Rebuild judge LOMO heatmap from pinned, tracked aggregate run receipts only.

No raw Biobase reports, slide IDs, patient-level predictions, or private
embeddings are read or embedded. Output is a standalone offline HTML page.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("c1_acc", "p@1", "p@5", "p@10")
OUTPUT = ROOT / "docs/judges/LOMO_JUDGE_DASHBOARD_20261114.html"
TEMPLATE = ROOT / "scripts/assets/lomo_judge_dashboard_template.html"
SHA_RECORDS = {}


def source(rel):
    p = ROOT / rel
    if not p.is_file():
        raise FileNotFoundError(rel)
    b = p.read_bytes()
    obj = json.loads(b)
    if not isinstance(obj, dict):
        raise ValueError("expected object in source " + rel)
    SHA_RECORDS[rel] = hashlib.sha256(b).hexdigest()
    return obj


def run(rel):
    obj = source(rel)
    if obj.get("status") != "ok":
        raise ValueError("source run not successful: " + rel)
    if not isinstance(obj.get("metrics"), dict):
        raise ValueError("metrics missing: " + rel)
    return obj


def metrics(obj):
    result = {}
    for k in METRICS:
        value = float(obj[k])
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("invalid metric " + k)
        result[k] = value
    return result


def ablations(record, path, clean_expected):
    dirty = record["code"].get("dirty")
    if bool(dirty) != (not clean_expected):
        raise ValueError("ablation cleanliness changed; review receipt " + path)
    if record["config"]["seeds"] != [0, 1, 2]:
        raise ValueError("expected three shared development fold seeds")
    raw = record["metrics"]
    base = metrics(raw["FULL"])
    rows = []
    for name, value in raw.items():
        actual = metrics(value)
        delta = {k: round(actual[k] - base[k], 7) for k in METRICS}
        # The original run wrote rounded deltas; reject a material mismatch.
        claimed = value.get("delta", {})
        if claimed and any(abs(delta[k] - float(claimed[k])) > 0.00015 for k in METRICS):
            raise ValueError("recorded delta mismatch: " + name)
        category = (
            "Reference" if name == "FULL" else
            "Remove embedding" if name.startswith("-emb:") else
            "Remove ensemble member" if name.startswith("-member:") else
            "Alter classifier" if name.startswith("-clf:") else
            "Remove retrieval term" if name.startswith("-c2:") else
            "Add experimental module" if name.startswith("+") else
            "Other"
        )
        rows.append({
            "name": name, "category": category, "metrics": actual,
            "delta": delta, "sd_c1": float(value.get("c1_sd", 0)),
            "seed0_c1": float(value.get("c1_seed0", actual["c1_acc"])),
            "source": path,
        })
    return {
        "name": "All-four extended ensemble" if record["config"]["base"] == "full" else "Chosen two-member SVM ensemble",
        "id": record["config"]["base"],
        "code_dirty": bool(dirty),
        "status": "OBSERVED_CLEAN_DEVELOPMENT" if not dirty else "OBSERVED_DIRTY_CODE_DEVELOPMENT",
        "seeds": record["config"]["seeds"],
        "baseline": base,
        "rows": rows,
        "source": path,
        "source_sha256": SHA_RECORDS[path],
        "n_variants": len(rows),
    }


def picked_model(name, rel):
    obj = run(rel)
    m = obj["metrics"]
    return {
        "name": name,
        "accuracy": float(m["oof_acc"]),
        "p1": float(m["oof_p@1"]),
        "p5": float(m["oof_p@5"]),
        "p10": float(m["oof_p@10"]),
        "code_dirty": bool(obj["code"]["dirty"]),
        "source": rel,
        "source_sha256": SHA_RECORDS[rel],
    }


def build_payload():
    full_path = "runs/20261114T193955Z-ablate-full-623513/record.json"
    selected_path = "runs/20261114T194101Z-ablate-ens-svm-670425/record.json"
    models = [
        ("Selected ens-SVM", "runs/20261114T191440Z-submit-ens-svm-4dc083/record.json"),
        ("GigaPath SVM", "runs/20261114T191448Z-submit-giga-svm-94bd9a/record.json"),
        ("GigaPath + H-optimus SVM", "runs/20261114T191445Z-submit-gh-svm-83fd42/record.json"),
        ("GigaPath logistic regression", "runs/20261114T191450Z-submit-giga-lr-943a76/record.json"),
    ]
    a_full = ablations(run(full_path), full_path, clean_expected=True)
    a_selected = ablations(run(selected_path), selected_path, clean_expected=False)
    model_rows = [picked_model(name, rel) for name, rel in models]
    # These 4 records are predecessor development runs with dirty-code metadata.
    if not all(m["code_dirty"] for m in model_rows):
        raise ValueError("development model provenance changed")
    report = run("runs/20261114T190839Z-reports-task-a-071c4c/record.json")
    report_cv = run("runs/20261114T201305Z-reports-cv-0cc031/record.json")
    crossnode = source("docs/evidence/20261114_enssvm_crossnode_verified.json")
    prekey = source("docs/evidence/20261114_prekey_selected_receipt.json")
    answer_score = source("docs/evidence/20261114_local_selfscore_aggregates.json")
    matched = source("docs/evidence/20261114_postkey_matched_baselines_aggregate.json")
    team_uploads = source("docs/evidence/20261114_team_upload_merge_aggregate.json")
    fcg = source("custody/fcg.json")
    if matched["answer_key_sha256"] != answer_score["key_sha256"]:
        raise ValueError("source-key digest mismatch in matched baseline comparison")
    if matched["slides"]["team_c1_correct"] != answer_score["metrics"]["c1_correct"]:
        raise ValueError("team C1 aggregate drifted from original self-score")
    if matched["reports"]["team_macro_f1"] != answer_score["metrics"]["criteria_mean_f1"]:
        raise ValueError("team A aggregate drifted from original self-score")
    if (team_uploads["merged_pr_count"] != 21 or team_uploads["open_pr_count"] != 0 or
        sorted(team_uploads["merged_pr_numbers"]) != sorted({num for arm in team_uploads["pr_arms"].values() for num in arm})):
        raise ValueError("teammate PR snapshot count or inventory mismatch")
    if team_uploads["snapshot_main_commit"] != "2f23887a3a0dcf94f2f679744f25210dc5b84286":
        raise ValueError("unexpected predecessor team commit")
    if any(team_uploads["selected_submission_sha256"][name] !=
           answer_score["frozen_submissions_sha256"][name]
           for name in answer_score["frozen_submissions_sha256"]):
        raise ValueError("new team upload changed frozen submission identity")

    for rel in [
        "runs/20261114T191550Z-mil-hoptimus-b7b8b6/record.json",
        "runs/20261114T191906Z-mil-biomedclip-947e1d/record.json",
        "runs/20261114T192217Z-mil-dinov2-e9d554/record.json",
    ]:
        run(rel)
    mil = []
    for name, rel in (
        ("H-optimus MIL", "runs/20261114T191550Z-mil-hoptimus-b7b8b6/record.json"),
        ("BiomedCLIP MIL", "runs/20261114T191906Z-mil-biomedclip-947e1d/record.json"),
        ("DINOv2 MIL", "runs/20261114T192217Z-mil-dinov2-e9d554/record.json"),
    ):
        m = source(rel)
        mil.append({"name": name, "accuracy": float(m["metrics"]["oof_acc"]),
                    "source": rel, "code_dirty": bool(m["code"]["dirty"])})
    if answer_score["metrics"]["c1_n"] != 67 or answer_score["metrics"]["criteria_tp"] != 608:
        raise ValueError("local aggregate score dimensions changed")
    if fcg["count"] != 23 or fcg["edges"] != 153:
        raise ValueError("FCG snapshot counts changed")
    if crossnode["n_matching_outputs"] != 5 or crossnode["signing"] != "NOT_SIGNED":
        raise ValueError("crossnode receipt changed")
    if prekey["organizer_scoring"] != "NOT_COMPUTED" or prekey["signature"] != "NOT_SIGNED":
        raise ValueError("prekey receipt changed")
    if sum(report["metrics"]["test_counts"].values()) != 608:
        raise ValueError("criteria count changed")
    if report_cv["metrics"]["kfold"]["mean_f1"] != 1.0:
        raise ValueError("report CV source changed")
    if crossnode["development_metrics"]["oof_acc"] != model_rows[0]["accuracy"]:
        raise ValueError("selected model and crossnode disagree")
    frozen = {name: {"sha256": entry["sha256"], "bytes": entry["bytes"]}
              for name, entry in sorted(prekey["submission"].items())}
    if len(frozen) != 3:
        raise ValueError("selected file count changed")

    payload = {
        "schema": "dnaforge.judges.lomo-explorer.v1",
        "title": "DNA Forge | Model evidence & LOMO",
        "project": "biobitworks/dna-forge",
        "local_mode": "AGGREGATE_ONLY_NO_PATIENT_OR_SLIDE_IDS",
        "time_scope": "2026-11-14 development records; as-of pre-key custody",
        "source_counts": {"report_train": 9010, "report_test": 979, "criteria": 30,
                          "slides_total": 263, "slides_labeled": 190,
                          "slides_heldout": 67, "pretrained_embeddings": 4,
                          "criterion_return_rows": 608, "neighbor_rows": 670},
        "ablation_groups": [a_full, a_selected],
        "models": model_rows,
        "mil": mil,
        "report": {
            "train_f1": float(report["metrics"]["train_mean_f1"]),
            "reported_keyword_baseline_f1": float(report["metrics"]["baseline_keyword_mean_f1_reported"]),
            "row_subset_cv_f1": float(report_cv["metrics"]["kfold"]["mean_f1"]),
            "row_subset_cv_nfold": int(report_cv["metrics"]["kfold"]["folds"]),
            "source": "runs/20261114T190839Z-reports-task-a-071c4c/record.json",
            "cv_source": "runs/20261114T201305Z-reports-cv-0cc031/record.json",
            "status": "DEVELOPMENT_RULES_AUTHORED_WITH_FULL_LABELLED_TRAIN_SET",
        },
        "replay": {
            "matching_outputs": int(crossnode["n_matching_outputs"]),
            "nodes": crossnode["nodes"],
            "status": crossnode["state"],
            "trained_commit": crossnode["training_commit"],
            "dev_scores": crossnode["development_metrics"],
            "signing": crossnode["signing"],
            "mmr": crossnode["mmr"],
            "source": "docs/evidence/20261114_enssvm_crossnode_verified.json",
        },
        "fcg": {"root": fcg["root"], "members": fcg["count"],
                "edges": fcg["edges"], "status": "DECLARED_GRAPH_ROOT_PRIOR_RECOMPUTATION_REPORTED",
                "signing": "NOT_SIGNED", "mmr": "NOT_COMPUTED",
                "source": "custody/fcg.json"},
        "freeze": {
            "selected_files": frozen,
            "local_clock": prekey["observed_utc"],
            "clock_source": prekey["clock_source"],
            "scoring": prekey["organizer_scoring"],
            "submission": prekey["organizer_submission"],
            "source": "docs/evidence/20261114_prekey_selected_receipt.json",
        },
        "official": {"hidden_scores": "SELF_SCORED_LOCALLY_NOT_ORGANIZER_CERTIFIED",
                     "access": "ANSWER_KEY_DOWNLOADED_AND_HASH_VERIFIED_AFTER_4PM",
                     "upload_receipt": "NOT_VERIFIED",
                     "issue": "https://github.com/biobitworks/dna-forge/issues/11"},
        "stages": [
            {"name": "01 / Intake", "state": "OBSERVED", "info": "9,010 labeled + 979 test reports; 263 slide manifest"},
            {"name": "02 / Identity", "state": "EXECUTED", "info": "Content hashes, run input receipts and source pointers"},
            {"name": "03 / Parse", "state": "EXECUTED", "info": "30 explicitly coded report criteria; 608 test result memberships"},
            {"name": "04 / Feature reuse", "state": "EXECUTED", "info": "Four supplied pretrained feature families; no backbone training"},
            {"name": "05 / Fit", "state": "EXECUTED", "info": "SVM/C1 classifier and C2 retrieval; 190 labeled slides, 5 folds"},
            {"name": "06 / LOMO", "state": "OBSERVED", "info": "13 clean extended-ensemble variants across three fold seeds; negative results retained"},
            {"name": "07 / Cross-machine", "state": "PASS", "info": "Two Macs; 5/5 exact output SHA-256 matches"},
            {"name": "08 / Freeze", "state": "PASS_LOCAL", "info": "Three candidate files copied and hash-checked before 4 PM local clock"},
            {"name": "09 / Local key score", "state": "EXECUTED", "info": "Frozen files scored locally against downloaded answer key; organizer website receipt not verified"},
            {"name": "10 / Organizer upload", "state": "NOT_VERIFIED", "info": "No verified upload receipt or Team ID evidence"},
        ],
        "local_selfscore": answer_score,
        "matched_baselines": matched,
        "team_uploads": team_uploads,
        "rights": {
            "software": "Apache-2.0 where rightsholder has authority",
            "research_content": "CC BY-NC-ND 4.0 for owned original content",
            "contributor_relicense": "RIGHTS_UNVERIFIED",
            "third_party": "UPSTREAM_LICENSES_RETained_NOT_RELICENSED",
            "source": "LICENSING.md",
        },
        "source_sha256": dict(sorted(SHA_RECORDS.items())),
        "interpretation": {
            "delta": "delta = variant metric - within-arm FULL metric. Negative removal delta means the removed component helped under this controlled development comparison.",
            "baselines": "Original organizer baseline scripts re-executed on the same downloaded key after release. This is a local same-key system contrast, not an organizer-certified score or a prospective external evaluation.",
            "caveats": "Extended four-embedding LOMO run is code-clean. Selected two-member LOMO predecessor is code-dirty. Neither is an independent official hidden-test score.",
            "identity": "SHA-256 identifies bytes; declared FCG edges do not prove scientific truth, signing, or causality.",
        }
    }
    return payload


def build():
    payload = build_payload()
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    if any(bad in raw for bad in ("SUPP-", "/Users/", "patient_id", "report_id", "result_slide_id")):
        raise ValueError("private/source identifier leakage detected")
    template = TEMPLATE.read_text(encoding="utf8")
    if template.count("__DASHBOARD_DATA_JSON__") != 1:
        raise ValueError("template missing data anchor or has duplicate")
    # Source is controlled aggregate numerics and record filenames.
    html = template.replace("__DASHBOARD_DATA_JSON__", raw.replace("</", "<\\/"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf8")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print("JUDGE_DASHBOARD_BUILD_PASS", "data_sources", len(SHA_RECORDS),
          "bytes", OUTPUT.stat().st_size, "sha256", digest,
          "full_rows", payload["ablation_groups"][0]["n_variants"],
          "selected_rows", payload["ablation_groups"][1]["n_variants"])
    print("DASHBOARD_OUTPUT", OUTPUT)
    return payload


if __name__ == "__main__":
    build()
