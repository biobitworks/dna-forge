# Workstreams

Who is doing what, so teammates can pick up complementary work instead of
duplicating it. Edit this file in a PR when you claim or finish something.

## The challenge in one paragraph

Biobase "Find the Right Patients" has two independent tracks:

- **Slides (C1, C2).** 263 de-identified H&E slides from four suppliers; 196
  labelled, 67 held out. C1: name the organ group of each held-out slide
  (accuracy). C2: for each held-out slide, return the 10 most similar slides
  (precision at 1, 5, 10 by organ group). Embeddings from four models
  (DINOv2, H-optimus-0, BiomedCLIP, Prov-GigaPath) are provided.
- **Reports (A).** 9,010 labelled synthetic pathology reports and 979 test
  reports; for each of 30 plain-language criteria, list the matching test
  report ids (mean F1). Keyword baseline: mean F1 0.27.

The answer key is released at 4:00 PM on the event day and scored in the
browser.

## Claimed: core data layer and slide tasks (Byron, with Claude)

Running on **magicPRO** (M1 Pro, 16 GB). magicSTUDIO (M1 Max, 32 GB) joins
once training is chained across machines.

1. **Core data structures.** Typed loaders for the slide manifest, organ
   groups, tile index, 0.5 µm tile pack, and the four embedding sets
   (slide vectors and int8 tile vectors). One `Dataset` object other code
   builds on.
2. **Chain of custody.** Every input zip and extracted file is SHA-256 hashed
   into a custody manifest at ingest; every run writes a record of the input
   hashes, code commit, config, host and metrics. Data itself is never
   committed (see DATA_POLICY.md).
3. **Transforms and preprocessing for vision models.** Blank-tile filtering,
   resize and stain-agnostic normalisation, tile sampling per slide, and
   PyTorch-ready datasets for fine-tuning or feature extraction.
4. **Slide baselines and probes.** First local numbers, from leave-one-out on
   the labelled slides (not the answer key):

   | Embedding | 1-NN organ accuracy | P@1 / P@5 / P@10 |
   |---|---|---|
   | DINOv2 | 0.56 | 0.56 / 0.34 / 0.27 |
   | H-optimus-0 | 0.58 | 0.58 / 0.40 / 0.31 |
   | BiomedCLIP | 0.58 | 0.58 / 0.43 / 0.34 |
   | Prov-GigaPath | 0.79 | 0.79 / 0.56 / 0.45 |
   | All four concatenated | 0.78 | 0.78 / 0.54 / 0.40 |

   Next: tile-level attention or mean-of-top-k pooling instead of a plain
   mean, metric learning on top of GigaPath, and supplier-aware evaluation
   (185 of 263 slides come from one supplier).

## Open for teammates

- **Reports track (task A).** Untouched. A structured parser for the final
  diagnosis block plus a criteria-to-field matcher should beat the keyword
  baseline by a wide margin.
- **Report text on slides.** 57 labelled slides carry report text; could be
  used as a text signal for C1 via BiomedCLIP's text encoder.
- **New tile embeddings.** Running a stronger pathology model (for example
  UNI or CONCH, licence permitting) over the 0.5 µm tile pack.
- **Extra training data.** HistAI public slides, if the licence allows.
- **Submission QA.** A checker that validates our CSVs against the templates
  before 4:00 PM.

Add your name next to an item when you take it.
