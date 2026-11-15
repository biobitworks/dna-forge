# Judge LOMO dashboard — source-backed local self-evaluation

Status: IMPLEMENTED and EXECUTED on MagicPro. Visit the locally
running server:

    http://127.0.0.1:8767/LOMO_JUDGE_DASHBOARD_20261114.html

To restart when no process listens on port 8767:

    cd ~/projects/inbox/pi-dnaforge-judge-heatmap-20261114
    python3 -m http.server 8767 --bind 127.0.0.1 --directory docs/judges

The HTML also opens as a standalone local file without a backend.

## Data → model → analysis → output

- Start: 9,010 labeled and 979 heldout synthetic reports, 30 criteria,
  263 slides (190 usable organ labels, 67 heldout queries); four
  organizer-provided pretrained image embedding families.
- Transform: typed diagnosis predicates and fixed-fold embedding
  features. Locally fit lightweight SVM classifiers, and compare
  LR, kNN and experimental MIL; no foundation model retraining.
- Development: selected ens-SVM C1 OOF 0.86316, C2 P@1 0.86842,
  P@5 0.82947, P@10 0.80000. Predecessor fitting receipts have
  dirty-code state; clean reruns reproduced five exact output
  SHA-256 hashes on MagicPro and MagicStudio.
- Clean extended-ensemble LOMO: 13 variants, three fold seeds, FULL
  C1 0.85439. Remove GigaPath: C1 -14.04 percentage points; replace
  SVM with LR: -2.46 pp C1; remove class-agreement C2 term: P@5
  -25.93 pp without changing C1; supplier centering addition:
  -4.04 pp C1. These are comparisons within this development arm.
  The selected ens-SVM arm has ten variants but a dirty-code
  predecessor; it is separately labeled.
- Downloaded answer-key self-evaluation: original frozen files
  rehashed against before-4-PM snapshot (6/6 PASS). Task A macro
  F1 1.000 (608 TP, zero FP/FN); C1 60/67 = 89.55%; C2
  P@1 88.06%, P@5 89.25%, P@10 88.06%. Calculated locally
  AFTER key release; not returned by the organizer's webpage.
  All key rows and report/slide identifiers remain PRIVATE.
- Organizers' approximate baselines: C1 ~70% and C2 P@1 ~80%,
  P@5 ~70%, P@10 ~60%; they were not rerun as a matched
  randomized controlled experiment. Task A F1 1.000 on synthetic
  data cannot establish clinical generalization because the rules
  were developed with labeled training data visible.

## Evidence limits

SHA identifies exact bytes, not biological truth. The 23-member
FCG and 153 declared edges establish declared custody relationships,
not model causality. NOT_SIGNED; MMR NOT_COMPUTED. Pre-key
observation used an untrusted local system clock.

Organizer website score and upload receipt are NOT_VERIFIED. This
dashboard does not submit a challenge entry. Keep the original
selected files immutable.

## Recompute and verify

    python3 scripts/build_judge_lomo_heatmap.py
    python3 -m pytest -q tests/test_judge_heatmap.py
    python3 scripts/check_no_data.py

The builder reads only aggregate tracked run records and a
post-key aggregate-only score projection. No patient/slide IDs,
complete answer key, raw embeddings or row-level predictions are
published in this viewer.

TURN_BREAKPOINT
ID: DNAFORGE-LOMO-JUDGES-T012
PARENT: DNAFORGE-CITATION-GAPS-T011 / prekey receipt
VERIFIED_NEW: downloaded-key score, clean extended LOMO visual.
EXECUTED: local selfscore, aggregate dashboard, HTTP 200, tests.
OBSERVED: original/snapshot 6/6 matches, three task scores, 5/5 replay.
DECISIONS: private key/rows retained; public aggregate only.
NOT_TESTED: organizer website certification and upload.
UNRESOLVED: external clinical validation, organizer confirmation.
NEXT_ACTION: human upload exact frozen files; retain receipt.
