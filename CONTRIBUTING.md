# Contributing to dna-forge

This repo is our entry for the Biobase "Find the Right Patients" slide challenge at the DNA Forge AI x Biology Hackathon (2026-11-14). The answer key is released at 4:00 PM PT today. Read this page, pick an item, and start.

Two other files define the team rules. Read them once:

- [WORKSTREAM.md](WORKSTREAM.md): who is doing what, and what is open for you to take.
- [DATA_POLICY.md](DATA_POLICY.md): data handling and chain of custody.
- [docs/MODEL_CONTRACT.md](docs/MODEL_CONTRACT.md): the files your model must write so it can be stacked into the final combined model (FCG). Read this before you train anything.

Both are in PR #1 until it merges. Read them on that branch if `main` does not have them yet.

## 1. Five-minute quickstart

1. Clone the repo and make a virtual environment. The baseline uses the standard library only, so nothing needs installing to run it.

   ```
   git clone https://github.com/biobitworks/dna-forge.git
   cd dna-forge
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Download the challenge packs yourself from the Biobase challenge page. Each teammate downloads their own copy under the hackathon data agreement. Never pass data through the repo, an issue or a PR. The exact agreement link is TBD, see issue #7 (rules review).

3. Unzip the packs into this layout. `data/` is gitignored.

   ```
   data/biobase/
     pack_slides/   slides_manifest.json, organ_groups.json, submission templates, baseline_slides.py
     tilepack/      reduced-resolution tiles and embeddings/<model>/slide-vectors.json
     thumbs/        one thumbnail per slide
     fullres/       sample of tiles at about 0.5 microns per pixel
   ```

4. Run the baseline. `baseline_slides.py` ships in the slide pack. If it is not at the repo root yet, use `data/biobase/pack_slides/baseline_slides.py` instead.

   ```
   python3 baseline_slides.py \
     --manifest data/biobase/pack_slides/slides_manifest.json \
     --vectors data/biobase/tilepack/embeddings/gigapath/slide-vectors.json \
     --out-dir runs/<run-id>/
   ```

   It writes `baseline_organ.csv` (C1) and `baseline_similar.csv` (C2) into the run directory. The other embedding folders in the tile pack hold DINOv2, H-optimus-0 and BiomedCLIP vectors. The pack README lists answer-key baseline scores per model; Prov-GigaPath is the strongest (about 70% on C1).

5. Write a `record.json` for the run (section 3), then open [WORKSTREAM.md](WORKSTREAM.md) and claim something.

## 2. Data rules (must know)

The full rules are in [DATA_POLICY.md](DATA_POLICY.md). The short version:

- No challenge data in git. That covers slides, tiles, thumbnails, embeddings, manifests and reports. `.gitignore` blocks the common types, but check `git status` before every commit. Reviewers reject any PR that adds data.
- Held-out slides stay unlabelled. No manual labelling, and no looking up held-out slides in outside sources.
- Models are used under their own licences (see the tile pack's `embeddings/models.json`). Before adding a new model, check its licence and list it in DATA_POLICY.md.
- Keep slide ids and labels out of issue and PR text beyond what the discussion needs. Never paste lists of slide ids with organs or diagnoses.
- The hackathon rules and data agreement have not been checked yet. TBD, see issue #7 (rules review).

## 3. Provenance logging

Every number we report must trace back to a run record.

**Run id.** Use `YYYYMMDD-HHMM-<host>-<short-desc>`, in local time, for example `20261114-1105-magicPRO-gigapath-knn`.

**Run record.** Each run writes `runs/<run-id>/record.json`. The core pipeline's `dnaforge/custody.py` provides `RunRecord`, which writes this format for you; it is coming in a PR from branch `feat/core-data`. Once it lands, use `dnaforge.custody.RunRecord` rather than hand-rolling records. Until then, write the same keys by hand:

```json
{
  "kind": "run",
  "id": "20261114-1105-magicPRO-gigapath-knn",
  "start": "2026-11-14T11:05:12-08:00",
  "end": "2026-11-14T11:05:40-08:00",
  "status": "ok",
  "error": null,
  "command": ["python3", "baseline_slides.py",
              "--manifest", "data/biobase/pack_slides/slides_manifest.json",
              "--vectors", "data/biobase/tilepack/embeddings/gigapath/slide-vectors.json",
              "--out-dir", "runs/20261114-1105-magicPRO-gigapath-knn/"],
  "host": {"hostname": "magicPRO", "user": "<user>", "platform": "macOS-14-arm64", "python": "3.12.4"},
  "code": {"commit": "3f2c1ab", "branch": "alex/gigapath-knn", "dirty": false},
  "config": {"embedding": "gigapath", "method": "1-NN cosine", "k": 10},
  "inputs": {
    "data/biobase/pack_slides/slides_manifest.json": {"bytes": 123456, "sha256": "<sha256>"},
    "data/biobase/tilepack/embeddings/gigapath/slide-vectors.json": {"bytes": 2345678, "sha256": "<sha256>"}
  },
  "metrics": {
    "split": "loo-labelled",
    "c1_accuracy": 0.79,
    "c2_p_at_1": 0.79, "c2_p_at_5": 0.56, "c2_p_at_10": 0.45
  },
  "outputs": {
    "baseline_organ.csv": {"bytes": 4567, "sha256": "<sha256>"},
    "baseline_similar.csv": {"bytes": 45678, "sha256": "<sha256>"}
  },
  "notes": "Leave-one-out on labelled slides. Pre-deadline."
}
```

If a run fails, set `status` to the failure and put the message in `error`. If `code.dirty` is true, say what the uncommitted changes were in `notes`. Commit the record. Caches under `runs/*/cache/` are ignored. Submission CSVs in a run directory are committed only by explicit `git add`.

**Hashing files.** A fallback for hand-written records until `RunRecord` lands, standard library only:

```python
import hashlib, json, os, sys

def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()

if __name__ == "__main__":
    print(json.dumps({p: {"bytes": os.path.getsize(p), "sha256": sha256(p)}
                      for p in sys.argv[1:]}, indent=2))
```

**Ingest custody.** Ingest manifests live in `custody/ingest-<date>.json`, with `kind` set to `"ingest"`, `sources` mapping each zip name to `{bytes, sha256, mtime}`, and `extracted` mapping each pack to `{files, count, tree_sha256}`. They hold names, sizes and hashes only, no content or labels. The core workstream owns these files. If your downloaded copy hashes differently, open an issue rather than editing it.

**Say which split.** Every reported number names its split in `metrics.split`:

- `loo-labelled`: leave-one-out on the 196 labelled slides. This is the only validation we have before 4:00 PM.
- `answer-key`: scored against the answer key, available only after 4:00 PM.

Leave-one-out and answer-key numbers are not comparable; do not put them in one table without labelling each.

**Post-hoc work.** Anything run after the 4:00 PM release is post-hoc. Put `"post_hoc": true` in its `config` and say so in `notes` and in any PR or write-up that uses it. Never tune on the answer key and then present the result as a pre-deadline one. Our pre-deadline results are the CSVs frozen before 4:00 PM, with records whose `start` is before the release.

## 4. Workflow

**Claim work.** Assign yourself the GitHub issue and add your name next to the item in [WORKSTREAM.md](WORKSTREAM.md) in a small PR. If there is no issue, open one first.

**Branches.** Name them `<name>/<topic>`, for example `alex/submission-checker`.

**PRs.** Keep them small and focused, one change per PR. Every PR passes this checklist:

- [ ] No challenge data added (check `git status` and the diff for images, vectors, manifests, report text, `.jsonl`, zips).
- [ ] Every number in the PR description or code comments has a `runs/<run-id>/record.json` in the PR or already on `main`.
- [ ] Each number names its split (`loo-labelled` or `answer-key`), and post-hoc work is marked post-hoc.
- [ ] No slide id and label lists in the PR text.
- [ ] Any new model or dataset has its licence listed in DATA_POLICY.md.
- [ ] WORKSTREAM.md updated if you claimed or finished something.

**Machines.** Byron owns both shared machines. Ask Byron for access.

| Machine | Hardware | Role |
|---|---|---|
| magicPRO | M1 Pro, 16 GB | Runs the core models first |
| magicSTUDIO | M1 Max, 32 GB | Joins later for chained training |

Use the machine name as `<host>` in run ids. On your own laptop, use a short host name you keep the same all day.

## 5. Timeline for today (PT)

These checkpoints are suggestions. Only the 4:00 PM release is fixed.

| Time | Checkpoint |
|---|---|
| Now | Packs downloaded, baseline reproduced, item claimed in WORKSTREAM.md. |
| 1:00 PM | First leave-one-out numbers for your item, with records, in a PR. |
| 2:30 PM | Pick the method for each task from leave-one-out results. No new methods after this. |
| 3:30 PM | Submission CSVs frozen and validated by the submission checker. Run records and CSV hashes committed. |
| 4:00 PM | Answer key released. The challenge page scores our files in the browser. |
| After 4:00 PM | Record the answer-key scores of the frozen files as the result. Any further work is post-hoc and labelled as such. |

The submission checker is an open item in WORKSTREAM.md. Until it lands, check the files by hand against section 6.

## 6. Submission formats

**C1, organ labels.** Columns `slide_id,organ`, one row per held-out slide (67 in the pack).

```
slide_id,organ
SUPP-XX-biobase_<uuid>,Lung
```

The organ must match an organ or organ group name, in any letter case. The safe choice is one of the 15 group names from `organ_groups.json`: Bladder, Bone, Bone marrow, Breast, Colon and rectum, Esophagus, Kidney, Liver, Lung, Other or mixed, Prostate, Skin, Stomach, Thyroid, Uterus.

**C2, similar slides.** Columns `query_slide_id,rank,result_slide_id`.

```
query_slide_id,rank,result_slide_id
SUPP-XX-biobase_<uuid>,1,SUPP-YY-biobase_<uuid>
SUPP-XX-biobase_<uuid>,2,SUPP-ZZ-biobase_<uuid>
```

- Ranks run from 1 to 10, with up to 10 rows per query.
- `result_slide_id` is never the query itself. Results may be labelled or held-out slides.
- Score is precision at 1, 5 and 10 by organ group.

Start from the templates in the slide pack (`submission_template_slides_organ.csv`, `submission_template_slides_similar.csv`). The baseline skips held-out slides with no vector for the chosen model, so check that every held-out slide has a row.

## 7. Where to ask

- Open a GitHub issue on [biobitworks/dna-forge](https://github.com/biobitworks/dna-forge/issues) for questions, bugs and claims.
- Byron (GitHub `biobitworks`) is the maintainer. Ask Byron for machine access and for decisions on scope.
