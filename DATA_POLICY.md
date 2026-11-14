# Data policy and chain of custody

This repository is public and will be submitted. The challenge data is not.

## Rules we follow

- **No challenge data in git.** Slides, tiles, thumbnails, embeddings,
  manifests and reports stay on our machines. `.gitignore` blocks the
  common file types; reviewers should reject any PR that adds data.
- **Hashes, not files.** At ingest we record the SHA-256 of every
  downloaded zip and every extracted file in `custody/ingest-<date>.json`.
  That file holds names, sizes and hashes only, no content or labels.
- **Every run is recorded.** Each training or evaluation run writes
  `runs/<run id>/record.json`: input hashes, git commit, command and
  config, host, start and end time, metrics, and hashes of any submission
  files written. Records are committed; caches are not.
- **Held-out slides stay unlabelled.** No manual labelling, no lookup of
  held-out slides in outside sources.
- **Model licences.** Embeddings are used under each model's own terms
  (see the tile pack's `embeddings/models.json`). Any new model we add is
  listed here with its licence.

## Open item

The packs themselves contain no licence or terms file. The hackathon's
rules and data agreement need to be checked and linked here before
submission.
