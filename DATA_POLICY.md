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

## Sources and their terms

| Source | What we use it for | Terms found (checked 2026-11-14) | In this repo |
|---|---|---|---|
| Biobase challenge packs (slides, tiles, tiles-20x, thumbnails, reports) | Training and evaluation for C1, C2, A | No licence or terms file in any pack | Hashes and run records only |
| [Synthea](https://synthetichealth.github.io/synthea/) (MITRE) | Synthetic patient records | Page: "Approved for Public Release; Distribution Unlimited"; the code repository is Apache-2.0 | Generator config only, if used |
| [Kaggle endometriosis dataset](https://www.kaggle.com/datasets/michaelanietie/endometriosis-dataset) | Symptom-based prediction | Licence not readable without a Kaggle login; check the dataset's License tab | Not committed until checked |
| [Ptarmigan-1](https://www.talus.bio/blog/try-ptarmigan-1-structure-free-drug/) (Talus Bio) | Structure-free compound screening via ptarmigan.app | Governed by talus.bio/terms; limit 10,000 compounds per screen, 10 screens per day | Results only, if terms allow |
| [bioRxiv 2026.07.28.741295](https://www.biorxiv.org/content/10.64898/2026.07.28.741295v1) | Ptarmigan-1 method reference | No licence stated in the text; cite, don't copy | Citation only |
| [MassIVE](https://massive.ucsd.edu) | Public proteomics datasets | Terms are set per dataset; record each dataset's MSV id and licence before use | Dataset ids only |
| [PMC10073113](https://pmc.ncbi.nlm.nih.gov/articles/PMC10073113/) | Symptom-based endometriosis ML method reference | Not readable automatically; check the article's licence line | Citation only |

## Open items

- **Hackathon rules and data agreement.** None of the packs or knowledge-base
  links contain the DNA Forge or Biobase rules. Link them here before
  submission.
- **Kaggle and PMC licences.** These pages were not readable automatically.
  Someone with a browser should confirm both.
