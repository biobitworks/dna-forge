# Model contribution contract

Teammates contribute small, orthogonal models. The core workstream stacks
them into the final model that produces our C1 and C2 submissions, and records
every step in the fractal custody graph (FCG): each file, fold set and run is a
custody object, each run's set of objects is a graph, and those graphs nest
into one root that covers the whole chain. This page is the interface between
contributors and the stack. If your model follows it, it can be stacked and
placed in the FCG without anyone reading your code.

Slide ids may be replaced by blinded tokens before data reaches you. Wherever
this page says `slide_id`, use whatever identifier the core pipeline handed
you (id or token), unchanged.

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

- The fold file is `custody/local/folds.json` (gitignored). Regenerate it with
  `python -m dnaforge folds` and check it against the committed
  `custody/folds.sha256`. It is written from the labelled slides that have an
  organ group. Format:
  `{"scheme": "...", "seed": 0, "n_splits": 5, "folds": {"<slide_id>": 0, ...}}`.
  It is a stratified 5-fold split (seed 0) over the labelled slides that have
  an organ group, sorted by id. It holds ids and fold numbers only, no labels.
- Do not make your own folds for anything you hand to the stack.
- Held-out slides are never in a fold and never get a label.

## Files each contribution writes

All under `runs/<run-id>/` (see CONTRIBUTING.md for run ids and
`record.json`).

| File | Rows | Columns |
|---|---|---|
| `record.json` | one record | RunRecord fields, with `config.contract: "v1"`, `config.model_family`, `metrics.oof_acc` (out-of-fold organ-group accuracy) and `metrics.node` (hostname it ran on) |
| `oof_organ.csv` | every slide in `custody/local/folds.json` | `slide_id,fold,` then one probability column per organ group, named exactly as in the manifest's `organGroupList` and in that order |
| `heldout_organ.csv` | the 67 held-out slides | `slide_id,fold,` with `fold` set to `-1`, then the same probability columns. Train on all folds for this file. |
| `heldout_similar.csv` (optional, for C2) | up to 50 per held-out slide | `query_slide_id,result_slide_id,score`, higher score means more similar, no self-matches |
| `oof_similar.csv` (optional, for C2) | up to 50 per labelled slide | same columns; results drawn only from slides outside the query's fold |

Rules:

- Probabilities in each row sum to 1 (within 1e-6). If your model gives scores,
  convert them with a softmax and say so in `notes`.
- A slide your model cannot score (for example, no vector) is left out, not
  filled with a uniform row. The stacker handles gaps.
- Hash every output file into `record.json` `outputs`.
- **Do not commit the prediction CSVs.** Held-out predictions imply labels
  for held-out slides. Only `record.json` is committed; its `outputs` hashes
  prove which files were used. Hand the CSVs to the core team on the
  machines (ask Byron where), never through git, issues or chat.
- Never commit the labels or the manifest.

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
