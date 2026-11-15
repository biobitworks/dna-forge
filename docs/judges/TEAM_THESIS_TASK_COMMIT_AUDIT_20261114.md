# DNA Forge × Biobase — thesis, team commit audit, scoring and judge requirements

**Successor review:** November 14, 2026 PT, after publication of the challenge answer key. This document supplements pre-key README/SUBMISSION and judge records rather than erasing them.

**Frozen inspected GitHub main predecessor:** dd89bec6f7a4252bf52419113ae5e0b26563ad7b, incorporating merged PR #33. At this snapshot: **20 merged PRs, zero open PRs, 12 open issues**. GitHub Actions data-guard and crossnode-evidence both PASS. The main branch is **not protected**, and direct team pushes can bypass PR review. Git author names distinguish at least Claude, efrazar and Byron P. Lee; GitHub PR author identity biobitworks is shared, and authorship of individual contributions cannot be attributed beyond the actual recorded Git metadata. This audit documents reachable public repository content and explicitly known separate repositories; it does **not** prove every unpushed local file exists or was merged.

## Central thesis and exact challenge question

**Can small interpretable local models and an auditable evidence chain improve synthetic pathology report eligibility search and organ-level slide discovery beyond simple supplied baselines, while preserving reproducible outputs and explicit failures?**

What is answered: **three independent tasks**, not a single cross-modal patient-matching pipeline. Biobase's synthetic pathology reports do not correspond to the WSI slide IDs. The challenge calls this *Find the Right Patients*, but our submission independently retrieves report matches, predicts slide organ group and retrieves slide neighbors. We did **not** validate linked patient/specimen cohorts, clinical trial enrolment, real-world prospective diagnoses or new wet-lab discoveries.

The organizer pack README is the primary task-level scoring source:
- Task A: for each of 30 plain-English criteria, output matching test report IDs; mean per-criterion F1. Count-only answers are permitted but do not earn F1.
- Task C1: one organ name or accepted organ group per each of 67 held-out slides; classification accuracy.
- Task C2: up to ten nonself nearest slides per held-out query; organ-group precision@1, @5 and @10.
- The three tasks are optional. Neither pack provides a verified combined three-task weighting or overall winner score. Do not invent one.
- Organizer reference baseline sources: official pack scripts baseline_keyword.py and baseline_slides.py. The public hackathon event page establishes attendance context; complete Biobase terms and data agreement remain **UNKNOWN**.

## The actual data → analytics → output workflow

| Step | Input / method | What executed and is supported |
|---|---|---|
| Source | Five Biobase ZIP packs, 9,010 labeled and 979 test synthetic reports, 30 criteria; 263 slides, 190 usable organ-labeled, six other non-held-out without organ labels, 67 held-out | Organizers' locally stored packs; source-hash custody. Not redistributable in public GitHub without rights |
| Features | Supplied pretrained Prov-GigaPath, H-optimus-0, BiomedCLIP and DINOv2 slide embeddings | **Reused frozen vectors. None of these foundation encoders was pretrained/fine-tuned by the team** |
| Task A | Deterministic parser of machine-generated final diagnoses and 30 handwritten eligibility predicates | 30 JSON criterion result lists; **no fitted Task A language model** |
| C1 organ | 190 labeled examples, shared 5-fold split, fitted SVM ensemble on selected supplied vectors | Locally trained small classifier, frozen 67-row candidate |
| C2 similarity | Vector similarity with predicted class-agreement adjustment | Frozen 670 rank rows, no held-out self matches |
| Controls | kNN, LR, stacking, MIL, five-fold OOF, supplier shift, LOMO across three seeds | Clean extended LOMO 13 variants; historical selected-ens-SVM LOMO 10 variants with code.dirty=true; negatives retained |
| Exact replay | Same code, numerical environment and input/fold identity on MagicPro and MagicStudio | Five output SHA-256 digests identical; repeatability only, not proof of biology |
| Graph | FCO provenance atoms; typed FCG and PROV-O; run/output digests | Public 23-member root and 153 declared edges; hashes are identity/custody, **not** causal proof, SIGNED or MMR |
| Candidate freeze | Three exact original files on MagicPro and restricted pre-key copy | Original and snapshot 6/6 SHA identities rechecked; original outputs **unchanged** |
| Key scoring | Downloaded 4 PM key, original frozen predictions, original baseline scripts separately rerun | Locally self-scored after release; no row-level key or predictions published; organizer website confirmation NOT_VERIFIED |
| Organizer delivery | Human upload/acceptance | **NOT_VERIFIED**; a passing local score is not a proof of submission |

## Matched post-key results against original challenge baseline scripts

These were independently recomputed on MagicPro using the **same downloaded answer key** for frozen team and reference baseline files, after the 4 PM release. It is an exact comparison on this fixed synthetic challenge, not a new external clinical test or a prospective model-selection exercise. Private source receipts were computed for original baseline code, supplied GigaPath vectors, manifest, outputs and the downloaded key. Only aggregated values and hashes are published in docs/evidence/20261114_postkey_matched_baselines_aggregate.json.

| Task / primary metric | Original pack baseline rerun | Selected unchanged team output | Difference |
|---|---:|---:|---:|
| A / mean F1 over 30 criteria | **0.272870** (keyword; 414 TP / 1459 FP / 194 FN) | **1.000000** (608 TP / 0 FP / 0 FN) | +0.727130 F1 |
| C1 / 67-slide organ accuracy | **47/67 = 70.15%** (GigaPath 1-NN) | **60/67 = 89.55%** | **+19.40 pp** |
| C2 / P@1 | **52/67 = 77.61%** | **59/67 = 88.06%** | **+10.45 pp** |
| C2 / P@5 | **224/335 = 66.87%** | **299/335 = 89.25%** | **+22.39 pp** |
| C2 / P@10 | **383/670 = 57.16%** | **590/670 = 88.06%** | **+30.90 pp** |

For C1, paired correctness: 46 both correct, 6 both wrong, 14 team-only correct, 1 baseline-only correct. **Exact two-sided McNemar p = 0.0009765625** on this held-out set. This statistical test does not remove supplier dependence, model-development reuse, data-generator correlations or research-selection effects. Report F1 1.000 matches the synthetic template/answer key; prior independent metamorphic paraphrase tests FAILED in 3/7 cases. No clinical performance claim is supported.

The team used a stronger feature ensemble and class-aware retrieval rather than 1-NN alone. The combined system improvements cannot be attributed exclusively to SVM, one embedding, or provenance. Controlled LOMO helps isolate a subset of module contributions, but the **graph has no demonstrated predictive effect**.

## LOMO results the judges should actually show

Clean full four-embedding arm, three shared development seeds:
- Removing GigaPath: **-14.04 percentage points C1 accuracy**.
- Replacing SVM with logistic regression: **-2.46 pp C1 accuracy**.
- Removing the C2 class-agreement term: **-25.93 pp P@5**, zero C1 change.
- Adding supplier centering: **-4.04 pp C1 accuracy**.
- Removing DINOv2: **+0.35 pp C1 accuracy** — negative contribution from that module in this tested configuration.

The selected two-member ablation predecessor had **code.dirty=true** and is kept as a separate selectable arm in the interactive heatmap. Do not fold dirty and clean runs into one experimental estimate. Models fit after switching to a clean pinned source reproduced the five output hashes on both Macs.

## Merge / contributor / lane reconciliation

| Recorded lane | Git-level observations | State and caveat |
|---|---|---|
| Claude startup and onboard | Initial commit 8a64a841… authored Claude; PR #12 onboarding; source/reports and slide tracks were reviewed in PRs #13, #15, #16, #17 | Main contains corresponding merged code, run/provenance materials |
| Teammate submission/scope | PRs **#1, #18–#22** merged. #19 repaired a demonstrated schema-check failure; #20 froze clean Task A and older ensemble outputs; #22 requested missing orthogonal data | No open PR. Older claude/project-thread-3aorn6 branch has one unique *commit identity* but its docs/DATA_REQUESTS.md blob is **byte-identical** to main. Do not remerge stale snapshot |
| PI/PM independent verification | PRs **#23–#25, #27, #29–#33** merged: two-Mac replay, current data-guard repair, model handoff, freeze, judge slides, Tamarind/ChEMBL bounded evidence, citations and LOMO dashboard | Selected original bytes and pre-key receipts preserved; selfscore added only as post-key successor |
| Efrazar patient selector | Direct commit 139c2c47… added source/demo and **generated predictions/labels to Git history**. #24 removed generated data from *current tree*; subsequent direct 00d3dbd2… adjusted files | **Historical public Git exposure UNRESOLVED (issue #26)**; later CI PASS proves current tracked tree only |
| Efrazar EndoForge V2 | Direct main commit 30b6e079… adds separate synthetic endometriosis/PCOS prototype; source README/VALIDATION and synthetic Python tests included | Not one of the official Biobase Task A/C1/C2 submissions. Its own file reports 13 tests PASS on author's environment; independent MagicPro system Python test collection **FAILED** because Streamlit is not installed; no diagnosis or clinical claim |
| Private CohortLens baseline | biobitworks/biobase-cohortlens-20261114 main 2a6f39c14…, PRs **#5–#11** merged | Separate independently frozen arm. **Not merged into the public team's selected model**, no substitution |
| DAISY / Tamarind / ChEMBL | v2 deck and bounded completed Tamarind descriptor + 25→24 ChEMBL record transformation, PR #30 | Not a drug-screening model trained on DAISY; no efficacy improvement claimed |
| DNAForge upstream desktop app | Separate humic-labs/dnaforge-app source reviewed for installation/tests | Full startup health smoke FAILED upstream; not integrated into the Biobase classifier |

**Branch audit:** 12 remote branches existed at review. Ten heads including main were ancestry-contained in main. The two exceptions are an old feat/core-data head with 28 Git commits not literally reachable (but the important current models/FCG/ablation code blobs are already in main, and merging its tree would remove newer files), and the Claude branch above with its duplicated document blob. **No blind merges or branch deletions** are warranted. The branch count is not an unmerged-deliverable count.

**PR inventory (20 merged):** #1, #12, #13, #15, #16, #17, #18, #19, #20, #21, #22, #23, #24, #25, #27, #29, #30, #31, #32, #33. At review **zero open PRs**. The current public Git graph and CI confirm these; ownership of actual people versus automation remains limited to Git author/committer metadata.

## Challenge compliance and research limits — judge readiness

| Gate | State | Evidence / gap |
|---|---|---|
| A/C1/C2 schemas and count/rank constraints | PASS | Original three frozen files, format guard, six source/snapshot SHA matches |
| Score A/C1/C2 on downloaded key | OBSERVED_LOCAL | All task metrics above, aggregate SHA sources; webpage result NOT_VERIFIED |
| Compare baselines reproducibly | OBSERVED_LOCAL | Organizer's actual baseline scripts rerun against same key; separate receipt; no source edits |
| Train locally vs pretrained models | SUPPORTED | Lightweight SVM and experimental MIL; foundation embeddings only reused |
| Claim LOMO contribution | SUPPORTED_WITHIN_DEVELOPMENT_ARMS | Source-backed clean vs dirty split, not clinical proof |
| Two-Mac exact-byte replay | PASS | Five output digest matches on pinned source/numerical stack |
| Source→FCO→FCG→claim integrity | DECLARED_AND_LOCALLY_RECOMPUTED | 23 members, 153 edges, no verified signing/MMR, no causal attribution |
| Public repo current data guard | PASS | Green on inspected exact main commit; historical generated data leak persists |
| Data agreement, allowed redistribution, teammate registration | UNKNOWN/NOT_VERIFIED | Organizer/team to produce actual agreement and opt-in/Team ID |
| Official upload acceptance / competition rank | NOT_VERIFIED | No organizer acceptance or combined official score receipt |
| Clinical/external hospital diagnostic utility | NOT_TESTED | Synthetic reports, mismatched report/slide IDs, supplier-shift susceptibility, no pathologist validation |
| Independent EndoForge V2 runtime verification | BLOCKED_BY_ENV | Missing Streamlit in review interpreter; package contains reported tests but no CI matrix for that separate folder |

**Presentation order:** Problem and precise three tasks → challenge input inventory → pretrained vectors vs locally fit models → model/data transformations → matched same-key gains → clean LOMO heatmap and negative ablations → two-Mac custody/replay → three frozen output digests → clinical/rights/organizer-submission limitations. Use the current [interactive HTML](LOMO_JUDGE_DASHBOARD_20261114.html) and [12-slide v2 deck](DNAForge_Biobase_Judge_Methodology_20261114_v2.pptx). The older deck is a predecessor and does not contain post-key same-baseline scores.

## Direct answer to the thesis

**SUPPORTED in this synthetic benchmark:** Explicit field-aware pathology matching and a small pretrained-feature-based SVM/retrieval system beat the original keyword and GigaPath 1-NN baselines on all measured task metrics, and the selected output bytes reproduced exactly across two Macs.

**NOT_SUPPORTED:** Real patient-to-slide multimodal matching; clinically validated eligibility; external-site generalization; causality from FCO/FCG; drug-screening discoveries; organizer-certified upload or final ranking.

**Next research action:** Independent histologist-reviewed human tissue/clinical cohort with donor-linked records, licensed reuse, blinded annotations, source-disjoint evaluation, patient-cluster uncertainty, and a locked test set; preserve the original synthetic benchmark separately.

TURN_BREAKPOINT
ID: DNAFORGE-TEAM-JUDGE-AUDIT-T013
PARENT: DNAFORGE-LOMO-JUDGES-T012 / dd89bec6f7a4252bf52419113ae5e0b26563ad7b
VERIFIED_NEW: 20 merged PRs; 12 open issues; old branch content comparison; same-key rerun baselines; original frozen digests; new matched aggregate.
EXECUTED: Git history/branch/PR/CI audit; original baseline script reexecution; independent key scoring; exact paired McNemar; docs successor.
OBSERVED: Task A 0.272870→1; C1 47/67→60/67; C2 52/224/383→59/299/590 hits at 1/5/10; C1 p 0.0009765625.
DECISIONS: Hold old branches; no historical rewrite; publish aggregate scores only; distinguish teammate-independent EndoForge.
PROPOSED: external clinical validation and branch protection.
NOT_TESTED: organizer upload/certification, downstream clinical validation.
FAILURES: independent EndoForge test collection on system Python missing Streamlit; predecessor synthetic paraphrase 3/7.
UNRESOLVED: rights, Team ID/receipt, prior public Git history, external source shift.
NEXT_ACTION: obtain organizer upload confirmation and data agreement; qualified clinical study; choose a distinct EndoForge runtime for separate verification.
