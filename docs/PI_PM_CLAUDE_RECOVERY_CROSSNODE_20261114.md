# Claude workstream recovery and cross-node training

Date: November 14, 2026, before official held-out evaluation.
Repository: biobitworks/dna-forge.
Exact predecessor: main at dda6c509815e0437171b15b0a76c6c64ee8856ae.
All results below were obtained by independent tool executions on the named machines, not reconstructed from chat.

## Claude PRs recovered

| PR | Scope | Observed status |
|---|---|---|
| #1 | Workstream and data policy | MERGED |
| #12 | Contributor onboarding, templates and data guard | MERGED |
| #13 | Core data/custody/transforms and initial model runs | MERGED |
| #15 | Structured report predicates, task A | MERGED |
| #16 | Ensemble SVM slides, stacked from #13 | MERGED |
| #17 | FCO/FCG, MIL, stacking and enrichment, stacked from #13 | MERGED |
| #18 | Submission checker and requirements map | MERGED |
| #19 | C1 CSV extra-column checker fix | MERGED |
| #20 | Submission candidate, Task A cross-check and FCG | MERGED |
| #21 | Final submission table | MERGED |
| #22 | Request for missing orthogonal data | MERGED |

Original three candidate submission files remain in the restricted MagicPro directory
~/dna-forge/SUBMISSION-FINAL. Nothing in this PR overwrites or uploads them.
Source rights are governed by DATA_POLICY.md.

## Source to evidence to claim

Both machines executed the same dnaforge ensemble method ens-svm, using
identical code commit dda6c509815e0437171b15b0a76c6c64ee8856ae,
identical method configuration, and SHA-256-matched input assets.
Both new run records report status ok and code.dirty false.

| Evidence | SHA-256 on both machines |
|---|---|
| Slide manifest | 1d07d56b5b39e3b1e72d68f843f2896d5c1a2f0fdae7b70db6e52594053c8f22 |
| GigaPath slide vectors | a12350969f733118f9447b05aaf397cfa88ac5728b335fdaff01006137a85a05 |
| H-optimus slide vectors | b505ab01f0e68ed3001fda1a035dbd86c909ff422e3a9a084b9957f4ea352bd5 |
| 5-fold assignment | 2f3cd6de81c08b2f4d66739492519f570d564b8a4a9a86118823c7fa7e6608d0 |
| Ensemble configuration | 7c2faf3fb63cdf5edcbd2b38d89bbb00c15c1357e502100cb2296a4941f2cd2d |

Python 3.9.6, NumPy 2.0.2, scikit-learn 1.6.1 and SciPy 1.13.1
were used on both hosts. Out-of-fold C1 accuracy was
0.8631578947368421, with P@1/5/10 = 0.868421052631579,
0.8294736842105263, 0.8. The methods used 190 known-label
training slides and produced predictions for 67 unlabeled slides.

All five output files had independently rehashed, byte-identical SHA-256 values:
- OOF organ scores: c06259e83a316212d8ae390a959ca9b1e672b768d4eb3a9a5390c864758a1d4e
- Held-out organ scores: 92ecf5a678ce0b710726065e0bef1cc72e5e44efdacac26f9f0c2cc59111169c
- Held-out similar scores: acb62125b7f627a6d47d825fd80e65bb30f10399bb8ecc2b451bd855a6230930
- Final C1 CSV: 8a69914d27c707c8a61694c8d8123f2139141cd5b79ac358193dda5da4cf7356
- Final C2 CSV: ed38172b0075b0415fcce2866a3c68d55a1214e578d0ddc97c19c070fb90d423

These final C1/C2 hashes match the original MagicPro submission candidates.
The new machine-local verified records are under docs/evidence.
The combined comparison is docs/evidence/20261114_enssvm_crossnode_verified.json.
No raw slides, IDs, labels, embeddings, or prediction rows are committed.
All identities above are SHA-256 content identities, NOT signatures or accuracy evidence.

## Negative results, failures and limitations

- PREDECESSOR DISCREPANCY: the earlier candidate run record
  20261114T201402Z-submit-ens-svm-e8e6d7 has code.dirty true,
  despite its description as a clean re-run in PR #20. This successor
  records new clean runs rather than rewriting the previous record.
- SUPPORTED: byte-identical cross-machine output from the pinned
  training data, code, settings, and numerical environment.
- NOT_SUPPORTED: hidden-test accuracy, clinical correctness or
  an improvement caused by graph custody.
- OBSERVED previously: some supplier-held-out accuracy drops
  substantially; the alternative MIL/stacked training did not
  improve the selected development baseline in PR #17.
- Task A: training F1 1.000 on hand-written rules and reused
  predicates across 5 train folds is not independently held-out
  rule-development validation. Do not label it hidden-test F1.
- NOT_TESTED: official post-4-PM score, sponsor opt-in, final
  submission, new full-tile model training on MagicStudio.
- NOT_COMPUTED: MMR commitment and any new accuracy attributable
  specifically to provenance graph infrastructure.

## Preserved local ingest artifacts not admitted to Git

| Node | Object | Manifest SHA-256 | Source archive SHA-256 | State |
|---|---|---|---|---|
| MagicStudio | ingest-2026-11-14-synthea.json | fd61a1063cbf29873a5c144e67de262199f16ee93e4bc02e506022dcd17bcf35 | 66141b772671452f590f9b7bb999eb201f1f16beb94a84ab0885ed723b36b315 | OBSERVED_LOCAL, NOT_ADMITTED |
| MagicPro | ingest-2026-11-14-enrichment.json | 74ae76e17440a9a2aaa95ec8d1390d55bd58fab290e576baf3980f0d215d0ed0 | d71108f925ce37d691f684ed6f3c80c0dc409514d31fa73816f5ee75766e97cd | OBSERVED_LOCAL, NOT_ADMITTED |

These remain untracked in the original Claude worktrees and are
preserved. Do not publish raw data, assume licensing, or join
Synthea/enrichment data to the Biobase hidden labels.

## FCG verification boundary

The committed custody/fcg.json session root was independently recomputed
from all 23 declared member hashes and matched
0ce023dc527748224c98a1fa4af7e3f62612d500f1f0520e68f6fe94f3a303e5;
the projection declares 153 edges. This checks listed-member inclusion
against the declared algorithm, not source attribution, causal claims,
cryptographic signing or MMR commitment.

## Team delivery gates (Pacific)

2:30 PM optional orthogonal model cutoff.
3:00 PM human sponsor opt-in with Team ID.
3:30 PM team target for exact-byte prediction freeze; must occur before 4 PM.
4:00 PM first allowed access to official answer key, no post-hoc retuning.
5:00 PM final organizer submission requires human completion.

Canonical code is in dna-forge. The separate private CohortLens repo
is an independent comparison baseline, not another team submission.
Preserve existing candidate files and append successors with new
run records rather than modifying predecessor evidence.

### TURN_BREAKPOINT
ID: DNAFORGE-CLAUDE-RECOVERY-T005
PARENT: DNAFORGE-PI-REVIEW-T004
PROJECT: biobitworks/dna-forge
SOURCE_COMMIT: dda6c509815e0437171b15b0a76c6c64ee8856ae
EXECUTED: MagicPro and MagicStudio independent ens-svm replay.
OBSERVED: identical source/config/fold identity, 5/5 output digests.
SUPPORTED: exact-byte reproducibility, not an independent hidden-test score.
PROPOSED: later independent official scoring, separate source admission.
NOT_TESTED: submission, official accuracy, complete full-tile MagicStudio work.
FAILURES: predecessor dirty candidate, external direct SSH transport timeout.
UNRESOLVED: source licences, Synthea/enrichment admission, human opt-in.
NEXT_ACTION: review this PR, preserve frozen files, confirm opt-in,
evaluate only after 4 PM PT and submit before 5 PM PT.
