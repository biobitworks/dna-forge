# Submission: requirements, what we built, and the evidence

## Post-key scoring and audit successor (reviewed 2026-11-14 PT)

The following original submission table and R1–R10 mapping were
authored **before** the organizer answer key was accessed. They remain
the evidence for the original selected bytes, and are not overwritten.

After key release, the original three files were reverified against
restricted frozen copies (six SHA checks), scored locally using the
downloaded answer key, and compared with freshly executed original
keyword/GigaPath challenge baselines on that **same** key.
See [full audit](judges/TEAM_THESIS_TASK_COMMIT_AUDIT_20261114.md) and
[public-safe aggregate receipt](evidence/20261114_postkey_matched_baselines_aggregate.json).

**Local results:** Task A mean F1 **1.000** (baseline 0.27287);
C1 **60/67 = 89.55%** (baseline 47/67 = 70.15%);
C2 P@1/5/10 **88.06% / 89.25% / 88.06%**
(baseline **77.61% / 66.87% / 57.16%**).
No new model was fitted using the released key; these were
self-evaluation and baseline-reexecution calculations.

**These scores are not yet certified by the organizers' scoring
website. The final upload acceptance remains NOT_VERIFIED.**
No answer-key rows or frozen output files were committed.

---


Each challenge requirement maps to the code that meets it and to the committed
evidence (run records, output hashes, the fractal custody graph root), so a
reviewer can trace every submitted file back to the Biobase packs. The original pre-key table
below lists the selected files; it is not itself an answer-key score.
The newer post-key **local** score is documented separately above.

## Final files (chosen 12:18 PM PT, freeze at 3:30 PM PT)

| Task | File (kept on magicPRO, never committed) | Run id | sha256 | Check passed |
|---|---|---|---|---|
| C1 organ | `submission_slides_organ.csv` | `20261114T201402Z-submit-ens-svm-e8e6d7` | `8a69914d27c707c8a61694c8d8123f2139141cd5b79ac358193dda5da4cf7356` | [x] |
| C2 similar | `submission_slides_similar.csv` | `20261114T201402Z-submit-ens-svm-e8e6d7` | `ed38172b0075b0415fcce2866a3c68d55a1214e578d0ddc97c19c070fb90d423` | [x] |
| A criteria | `submission_criteria.json` | `20261114T201401Z-reports-task-a-a8f4f3` | `1604ae1557ffad8e39c671a193fec113653984f2e8bf090791f5a15b62d88345` | [x] |
| Custody | `custody/fcg.json`, `custody/fcg.prov.jsonld` | session FCG (23 members, 153 edges) | root `0ce023dc527748224c98a1fa4af7e3f62612d500f1f0520e68f6fe94f3a303e5` | [x] |

Candidate output bytes match the earlier team runs, but note that the
slide record 20261114T201402Z-submit-ens-svm-e8e6d7 has code.dirty:
true. This predecessor must not be called a clean rerun. PR #23
independently re-executed the slide ens-SVM from clean pinned commit
dda6c509815e0437171b15b0a76c6c64ee8856ae on MagicPro and
MagicStudio, and confirmed bit-identical C1/C2 outputs. The Task A
run and the selected Task A hash are separately recorded. Official
hidden-test scores and organizer submission remain NOT_VERIFIED.

Check each file with:

```
python3 scripts/check_submission.py --manifest data/biobase/pack_slides/slides_manifest.json \
  --organ runs/<id>/submission_slides_organ.csv --similar runs/<id>/submission_slides_similar.csv \
  --record runs/<id>/record.json
python3 scripts/check_submission.py --criteria runs/<id>/submission_criteria.json \
  --criteria-template data/biobase/pack_reports/submission_template_criteria.json \
  --reports-test data/biobase/pack_reports/test.jsonl --record runs/<id>/record.json
```

## Requirements map

| # | Requirement (source) | What we built | Evidence |
|---|---|---|---|
| R1 | C1: one organ per held-out slide, columns `slide_id,organ`, answer matches organ or organ group in any case (pack README) | `dnaforge submit --method ens-svm`: SVM ensemble on GigaPath and GigaPath+H-optimus slide vectors | run record outputs; `check_submission.py` C1 checks |
| R2 | C2: up to 10 similar slides per held-out slide from the whole set, columns `query_slide_id,rank,result_slide_id`; scored P@1/5/10 by organ group (pack README) | same run, ranking in the GigaPath space | run record outputs; `check_submission.py` C2 checks (ranks, self-match, ids) |
| R3 | Task A: for each of 30 criteria, the matching test report ids; scored by mean F1 (reports pack) | `dnaforge.reports`: parser for the final diagnosis block plus a predicate per criterion | run record. Train F1 1.000. 5-fold CV F1 1.000 ± 0 (`20261114T201305Z-reports-cv-0cc031`), 979/979 test reports parse, 0/30 criteria with test counts outside 3 sigma. The predicates were hand-written while looking at all the training data, so the CV checks stability, not generalisation. Read the answer key score as the real estimate. |
| R4 | Beat the baselines: about 70% C1 and P@1 about 0.8 for GigaPath 1-NN; keyword F1 0.27 for task A (packs) | shared 5-fold OOF evaluation (`custody/folds.sha256`) | ens-svm OOF C1 0.863, P@1/5/10 0.868 / 0.829 / 0.800 (local, not answer key) |
| R5 | No labelling or outside lookup of held-out items (DATA_POLICY.md) | models train only on labelled slides; `dnaforge.fcg` can blind ids to tokens for contributors (tokenize, shuffle, double-blind) | FCG key commitment `a1ac784e…f218`; run configs |
| R6 | Public repo holds no challenge data, labels or report text (DATA_POLICY.md) | `.gitignore`, `scripts/check_no_data.py`, data-guard CI | current main data-guard green following PR #24; earlier direct demo commit contained generated challenge outputs and failed CI; Git history remediation remains UNRESOLVED |
| R7 | Chain of custody from downloaded zips to submitted files (Byron, DATA_POLICY.md) | ingest manifests, run records, fractal custody graph exported as W3C PROV-O JSON-LD | `custody/ingest-*.json`, `runs/*/record.json`, FCG root |
| R8 | Model and data licences respected (DATA_POLICY.md) | licence table in DATA_POLICY.md | open: hackathon rules and data agreement, Kaggle endometriosis and HistAI terms (#7) |
| R9 | Hackathon rules and data agreement (organisers) | TBD | open: link the rules in DATA_POLICY.md (#7) |
| R10 | Results reported honestly: local vs answer key, post-4 PM marked post-hoc (CONTRIBUTING.md) | write-up (#11) | answer-key scores added after 4:00 PM in a separate, post-hoc section |

## Open before the freeze

- R8 and R9: the rules, the data agreement and the enrichment licences (#7).
