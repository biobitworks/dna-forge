# Presentation review: Find the Right Patients

**Headline:** reproducible, traceable synthetic patient and tissue sample
selection — not de novo foundation-model training or clinical validation.

## What to show

1. Challenge problem: 30 eligibility criteria against synthetic pathology
   reports, 67 held-out slides for organ classification and image retrieval.
2. Standard method: structured report parser and predicates; pretrained
   pathology embeddings + fitted small SVM classifiers.
3. Distinctive engineering: separate clean model executions on MagicPro and
   MagicStudio, with identical five outputs; source/input/fold/output
   SHA-256, FCO/FCG typed relationships and replayable receipts.
4. Evidence limits: weaker MIL/stacking, supplier bias, reported Task A
   training perfection without independent nested rule-development CV.
5. Selected artifacts stay local on MagicPro, schema checked and hash
   verified; independent official score and submission receipt pending.

## Model and graph view

    Official licensed source packs (private, immutable)
        |-- report text -> parse fields -> criterion predicate -> A
        |-- slide manifest -> pretrained feature vectors
                                      |
                         train 190 labeled slides
                                      |
                         OOF 5-fold ens-SVM model
                                      |
                              C1 organ + C2 similar
        |-- input SHA-256 / transforms / runs / outputs
                                      |
                           typed FCO / FCG projection
                                      |
                        claim -> selected output hashes
                                      |
                       held-out evaluation AFTER 4 PM
                                      |
                         organizer submission receipt

**FCG is provenance infrastructure.** The declared root
0ce023dc527748224c98a1fa4af7e3f62612d500f1f0520e68f6fe94f3a303e5
recomputed over 23 listed members with 153 declared edges. This
supports integrity checking of included identities, NOT causality
or scientific truth; no signature/MMR commitment is verified.

## Scores with correct evidence status

| Task | Observed development outcome | Reported organizer baseline | Limit |
|---|---|---|---|
| C1 organ | OOF accuracy 0.863 | ~0.70 | Cross-validation, NOT official hidden |
| C2 similar | OOF P@1/5/10 0.868/0.829/0.800 | ~0.80 P@1 | Different evaluation protocols not directly matched |
| A reports | Train F1 and row-stability 1.000 | keyword ~0.27 | Predicates designed using full labeled train data |
| Patient selector demo | separately reported 0.82 C1 | ~0.70 | Separate pipeline; do NOT conflate with ens-SVM |
| Endo symptom enrichment | AUC about 0.655 | not a Biobase task | License/status separate |

## Standard vs new

- **Standard:** pretrained embeddings, SVM/LR/kNN, MIL, rule parsing.
- **New integration:** exact reproducibility across independent Macs,
  provenance graph lineage, explicit negative-result logging,
  privacy-separated source/prediction custody, strict admission status.
- **NOT_SUPPORTED:** accuracy improvement caused by FCG alone or use of
  patient-facing diagnostic results. No base model was trained from scratch.

## 90-second presentation script

"Finding the right patient starts with evidence. We received synthetic
pathology reports and tissue-slide feature vectors. We made thirty
eligibility rules inspectable, then trained a lightweight organ
classifier using the supplied pretrained image features. It also finds
similar slides.

Rather than claim a new pathology foundation model, we checked that
the same SVM run reproduced the exact same outputs on two Macs.
Each source file, fold assignment, executable version, model run and
selected output is represented by an independently addressable
custody record and links in our evidence graph.

Our development organ-classification estimate is about 86 percent;
similar-slide precision at one is about 87 percent. Those are not yet
official hidden-test scores. We kept negative findings, especially
supplier bias and weaker attention-MIL attempts. That is the value of
the graph: reviewers can trace both successes and failures, without
confusing a hash with biological proof."

## Important presentation and submission gates

- Demonstrate only an authorized locally generated app; do not publish
  raw challenge IDs, reports, slides or prediction rows.
- The prior demo commit placed generated outputs on public Git history;
  PR #24 corrected the current tree, but history remediation is
  UNRESOLVED. Do not say the repository was always data-safe.
- Team's selected outputs are in MagicPro SUBMISSION-FINAL; use
  scripts/verify_selected_submission.py for read-only SHA verification.
- Confirm human sponsor opt-in by 3PM PT; freeze exact bytes by the
  team's 3:30PM target and before 4PM; evaluate against the official
  hidden key only after 4PM; submit by 5PM.
- Organizer rules/data agreement and Kaggle licence not independently
  established. HistAI CC BY-NC. Any new ovarian PCOS/endometriosis
  literature stays PROPOSED/NOT_ADMITTED until permission and labeled
  data validation. A paper citation is not a labeled training sample.
