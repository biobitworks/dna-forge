# Model contribution contract

Teammates contribute small, orthogonal models. The core workstream combines
them into the final combined model (the FCG) that produces our C1 and C2
submissions. This page is the interface between the two. If your model
follows it, it can be stacked without anyone reading your code.

The Biobase packs are the source of truth. Every input you read must be a
file whose hash is in the custody ingest manifest (`custody/ingest-<date>.json`).
If you make a derived file (new embeddings, features), hash it into your run
record's `inputs` or `outputs`.

## What "orthogonal" means here

The core team trains on the four provided slide embeddings. A contribution is
most useful when its errors differ from theirs. Good examples:

- a different signal (report text, thumbnails, tile-level features, a new
  pathology model over the 0.5 um tiles),
- a different model family (kNN, logistic regression, small MLP, gradient
  boosting, prototype or metric-learning models),
- a different view of the data (supplier-normalised vectors, tile attention
  instead of mean pooling).

Small is fine. A model that only beats the baseline on two organ groups can
still help the stack.

## Folds

Everyone uses the same folds, so out-of-fold predictions line up.

- The fold file is `custody/folds.json`, written once by the core workstream
  from the labelled slides that have an organ group. Format:
  `{"kind": "folds", "seed": 0, "n_folds": 5, "strategy": "...", "folds": {"<slide_id>": 0, ...}}`.
- Do not make your own folds for anything you hand to the stack.
- Held-out slides are never in a fold and never get a label.

## Files each contribution writes

All under `runs/<run-id>/` (see CONTRIBUTING.md for run ids and
`record.json`).

| File | Rows | Columns |
|---|---|---|
| `record.json` | one record | RunRecord fields, with `config.contract: "v1"` and `config.model_family` |
| `oof_organ.csv` | every slide in `custody/folds.json` | `slide_id,fold,` then one probability column per organ group, in `organ_groups.json` order |
| `heldout_organ.csv` | the 67 held-out slides | `slide_id,` then the same probability columns. Train on all folds for this file. |
| `heldout_similar.csv` (optional, for C2) | up to 50 per held-out slide | `query_slide_id,result_slide_id,score`, higher score means more similar, no self-matches |
| `oof_similar.csv` (optional, for C2) | up to 50 per labelled slide | same columns; results drawn only from slides outside the query's fold |

Rules:

- Probabilities in each row sum to 1 (within 1e-6). If your model gives scores,
  convert them with a softmax and say so in `notes`.
- A slide your model cannot score (for example, no vector) is left out, not
  filled with a uniform row. The stacker handles gaps.
- Hash every output file into `record.json` `outputs`.
- These CSVs contain slide ids and are allowed under `runs/` by the data
  guard. They contain no labels. Do not commit the labels or the manifest.

## How the stack uses them

The core workstream trains a meta-model on the `oof_*` files and applies it to
the `heldout_*` files. A contribution is included if it passes the format
check and adds out-of-fold accuracy or P@k when stacked. The run record of the
final model lists every contribution's run id and output hashes, so the chain
of custody runs from the Biobase zips to the submitted CSVs.

## Deadlines today (PT)

- 2:30 PM: last contributions accepted into the stack.
- 3:30 PM: submission CSVs frozen (see issue #5).
- 4:00 PM: answer key released. Anything after this is post-hoc.
