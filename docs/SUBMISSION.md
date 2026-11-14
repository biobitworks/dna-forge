# Submission: requirements, what we built, and the evidence

Each challenge requirement maps to the code that meets it and to the committed
evidence (run records, output hashes, the fractal custody graph root), so a
reviewer can trace every submitted file back to the Biobase packs. Fill in the
FINAL column at the 3:30 PM PT freeze. Nothing in this file is an answer-key
score.

## Final files (frozen at 3:30 PM PT)

| Task | File (kept on magicPRO, never committed) | Run id | sha256 | Check passed |
|---|---|---|---|---|
| C1 organ | `submission_slides_organ.csv` | TBD (candidate `20261114T191440Z-submit-ens-svm-4dc083`) | TBD (candidate `8a69914d…7356`) | [ ] |
| C2 similar | `submission_slides_similar.csv` | TBD (candidate same run) | TBD (candidate `ed38172b…d423`) | [ ] |
| A criteria | `submission_criteria.json` | TBD (candidate `20261114T190839Z-reports-task-a-071c4c`) | TBD (candidate `1604ae15…8345`) | [ ] |
| Custody | `custody/fcg.json`, `custody/fcg.prov.jsonld` | session FCG | root TBD (current `abc4d069…c793c`) | [ ] |

The candidate C1/C2 run has `code.dirty: true`. Re-run it from a clean commit
before the freeze so its record names a commit that reproduces it.

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
| R3 | Task A: for each of 30 criteria, the matching test report ids; scored by mean F1 (reports pack) | `dnaforge.reports`: parser for the final diagnosis block plus a predicate per criterion | run record; train F1 1.000 is a fit check on the rule-building data, not an estimate (see #2) |
| R4 | Beat the baselines: about 70% C1 and P@1 about 0.8 for GigaPath 1-NN; keyword F1 0.27 for task A (packs) | shared 5-fold OOF evaluation (`custody/folds.sha256`) | ens-svm OOF C1 0.863, P@1/5/10 0.868 / 0.829 / 0.800 (local, not answer key) |
| R5 | No labelling or outside lookup of held-out items (DATA_POLICY.md) | models train only on labelled slides; `dnaforge.fcg` can blind ids to tokens for contributors (tokenize, shuffle, double-blind) | FCG key commitment `a1ac784e…f218`; run configs |
| R6 | Public repo holds no challenge data, labels or report text (DATA_POLICY.md) | `.gitignore`, `scripts/check_no_data.py`, data-guard CI | CI green on every PR; submission files stay on the machine |
| R7 | Chain of custody from downloaded zips to submitted files (Byron, DATA_POLICY.md) | ingest manifests, run records, fractal custody graph exported as W3C PROV-O JSON-LD | `custody/ingest-*.json`, `runs/*/record.json`, FCG root |
| R8 | Model and data licences respected (DATA_POLICY.md) | licence table in DATA_POLICY.md | open: hackathon rules and data agreement, Kaggle endometriosis and HistAI terms (#7) |
| R9 | Hackathon rules and data agreement (organisers) | TBD | open: link the rules in DATA_POLICY.md (#7) |
| R10 | Results reported honestly: local vs answer key, post-4 PM marked post-hoc (CONTRIBUTING.md) | write-up (#11) | answer-key scores added after 4:00 PM in a separate, post-hoc section |

## Open before the freeze

- R8 and R9: the rules, the data agreement and the enrichment licences (#7).
- R3: a held-out or cross-validated F1 for task A.
- Re-run the C1/C2 candidate from a clean commit, then fill in the final table.
