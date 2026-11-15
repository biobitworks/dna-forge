# DNA Forge × Biobase — final teammate and signed dashboard handoff

**Evidence successor T015 | Parent public Git main:** 2f23887a3a0dcf94f2f679744f25210dc5b84286.

## Which teammate uploads and merges were admitted?

**Verified GitHub predecessor snapshot:** 21 merged PRs, 0 open PRs and 12 open issues. The dashboard presents the grouped PR inventory and source-linked direct teammate uploads. Git push is not a Biobase competition upload receipt.

- **Claude / original implementation:** initial repository commit 8a64a8411144, parsed report criteria, slide model feature heads and submission runs. PRs #1, #12–#22 include original track work, accepted model/ablation and source/provenance contributions. Git identity is recorded author metadata, not verified personhood.
- **Efrazar patient-selector demo:** direct Git commit 139c2c47f589. A separate Streamlit user interface and alternative patient selection approach; initial direct commit ALSO contained generated challenge output rows in public Git history. PR #24 removed them from the CURRENT Git tree; the historical exposure remains UNRESOLVED. Direct cleanup commit 00d3dbd2b3b4 retained.
- **Efrazar EndoForge V2:** direct commit 30b6e0799a61 with a distinct synthetic endometriosis/PCOS clinical/hormonal/molecular prototype. Local validation documentation reports tests passing, but independent MagicPro system Python test collection failed because Streamlit was missing. Not a clinically validated model and not part of original Biobase Task A/C1/C2 submissions.
- **PI/PM independent lane:** PR #23 cross-device exact replay, #25 model/training handoff, #27 immutable selected-file freeze, #29–#32 judge/research successor evidence, #33 interactive LOMO dashboard, #34 matched same-key baseline rerun and thesis audit.

**Effect on the challenge score:** The teammate additions and documentation merges broaden demos and research opportunities but do not change the selected original Task A/C1/C2 prediction bytes. All selected file SHA-256 digests remain unchanged. The score gains belong to the originally frozen report parser / lightweight SVM / class-aware retrieval combination, not to the later EndoForge upload, the patient-selector add-on, or the FCG custody graph.

**Same-key local post-release comparison:** Task A keyword F1 0.272870 → team F1 1.000000. C1 organ accuracy 70.15% → 89.55% (+19.40 percentage points); C2 P@1 77.61% → 88.06% (+10.45 pp), P@5 66.87% → 89.25% (+22.39 pp), P@10 57.16% → 88.06% (+30.90 pp). C1 exact paired McNemar p = 0.0009765625. This is locally observed using original Biobase baseline scripts against the same downloaded answer key, NOT organizer-certified or external clinical performance. Failed paraphrase controls, negative LOMO results and supplier-domain weaknesses remain.

## What to show to teammates and judges

1. [Updated interactive LOMO / model gains / teammates dashboard](LOMO_JUDGE_DASHBOARD_20261114.html). It is a standalone HTML file with no backend or private data.
2. [Full thesis and team-lane audit](TEAM_THESIS_TASK_COMMIT_AUDIT_20261114.md).
3. [Matched baseline aggregates](../evidence/20261114_postkey_matched_baselines_aggregate.json) and [teammate commit/PR snapshot](../evidence/20261114_team_upload_merge_aggregate.json).
4. Locally serve from the docs/judges directory using Python's built-in http.server bound to 127.0.0.1 on port 8767; visit http://127.0.0.1:8767/LOMO_JUDGE_DASHBOARD_20261114.html on MagicPro.

The report and slide datasets are separate and do not link individual patient records to image IDs. Neither original data nor private downloaded key or selected outputs are published.

## Scoped licensing

- **Apache-2.0:** original software, where the relevant copyright holder has authorized the grant; this includes the authored judge HTML/CSS/JS and Python evidence scripts. Legal text: [LICENSE](../../LICENSE).
- **CC BY-NC-ND 4.0:** designated original Biobitworks/Cellico.Bio research text, figures and method decks where owned/licensable. See [LICENSING.md](../../LICENSING.md).
- **RIGHTS_UNVERIFIED:** independent teammate-authored folders and any material without confirmed contributor grant. Upstream third-party models, papers, datasets and challenge packs keep their licenses; root Apache does NOT blanket-relicense them. See [NOTICE](../../NOTICE.md).

## Computed 15-leaf binary Merkle root

**Final root (SHA-256):**

    33bc74cfad628671e5760d6c2f1706af0e49f59d53ee6d1be4b6301ed7f37ca9

This root is computed and recomputed from exactly 15 declared public files, ordered by UTF-8 path, with content SHA-256 over original bytes; leaf hash uses a 0x00 prefix and domain-separated path/content digest, and parent hash uses 0x01 plus raw left/right hashes. Odd levels duplicate their last child. All leaf hashes/paths and the full construction appear in [Merkle manifest](../evidence/20261114_dashboard_merkle_v1.json), SHA-256:

    228ee0b914487cde5b6fb20181a4e6c10b676ffd851787431390401df3c11490

**This is a binary Merkle snapshot, NOT an MMR commitment and NOT the entire FCG canonical root.** Integrity inclusion does not establish attribution, source rights, truth, causality, model quality or timestamp validity. Manifest and handoff are separate from the 15 leaves to avoid self-referential hashing.

### Actual Ed25519 signature and public key

A new tool-operated Ed25519 SSH key pair was generated on MagicPro and used to sign the exact canonical attestation message. Signature verification with the matching published public key **PASSED**.

- [Public key](../evidence/keys/dnaforge_dashboard_tool_ed25519.pub).
- Public-key fingerprint: SHA256:k4OeAghtm6UxX7do469gFe2j9/fJ3uhB/vVgaLf3/CA.
- [Exact signed attestation text](../evidence/20261114_dashboard_attestation_message.txt).
- [SSH Ed25519 signature](../evidence/20261114_dashboard_attestation_message.txt.sig).
- Signature SHA-256: d8a80db5e9033fb7bb68ecf57ab6a4890b67d13895a34ad1e38f061581ef0692.
- Cryptographic identity label: dnaforge-review-tool; namespace: dnaforge-dashboard.
- **Private key NOT published:** stored under the private MagicPro user directory in projects/private/biobase-20261114/attestation-keys with owner-only file mode 0600. No passphrase was set for this local demonstration key; use a managed, preferably hardware-backed institutional key for production.
- **Trust ceiling:** this is an actually verified signature of bytes by a locally generated key. It is NOT OpenAI's organizational key, the user's personal signing key or legal identity signature, an independent human attestation, a real timestamp, or a claim that Merkle/FCG proves scientific causation.
- **MMR NOT_COMPUTED.** Older receipt signing remains NOT_SIGNED where not independently established.

### Public-only verification (no secret key needed)

    python3 scripts/build_judge_lomo_heatmap.py
    python3 scripts/dashboard_merkle.py --check
    python3 scripts/verify_dashboard_attestation.py
    python3 -m pytest -q tests/test_judge_heatmap.py tests/test_team_license_dashboard.py tests/test_postkey_team_audit.py
    python3 scripts/check_no_data.py

The verifier reconstructs the 15-leaf root and source bytes, hashes the manifest, verifies the signed message, verifies the public-key fingerprint and Ed25519 SSH signature, and fails if anything declared is changed.

## Handoff and status

| Gate | Final state |
|---|---|
| Teammate source upload/PR inventory | OBSERVED at pinned predecessor commit |
| Dashboard shows teammate uploads, LOMO and same-key gains | IMPLEMENTED; EXECUTED on MagicPro |
| Selected original Biobase files changed by teammate uploads | NEGATIVE: unchanged |
| Binary Merkle root, 15 ordered public leaves | COMPUTED, VERIFIED |
| Locally generated key signature of this root | SIGNED, SIGNATURE_VERIFIED locally |
| OpenAI or human institutional identity signature | NOT_SIGNED / NOT_VERIFIED |
| MMR append-only commitment | NOT_COMPUTED |
| Contest upload and official organizer scoring receipt | NOT_VERIFIED |
| Third-party contributor rights and historic generated-data Git exposure | UNRESOLVED |
| Clinical/external-corpus transfer | NOT_TESTED |

**NEXT_ACTION:** Review the updated presentation and license exceptions with teammates; obtain organizer portal upload receipt and explicit contributor rights clearance. For production attestation, rotate to a stable human/organization-controlled signing identity rather than treating a tool-generated key as authorship.

TURN_BREAKPOINT
ID: DNAFORGE-DASHBOARD-TEAM-LICENSE-T015
PARENT: DNAFORGE-TEAM-JUDGE-VERIFICATION-T014 / 2f23887a3a0dcf94f2f679744f25210dc5b84286
VERIFIED_NEW: 21 merged PR predecessor inventory; source linked direct teammate uploads; computed 15-leaf root; locally verified public-key signature; scoped license files.
EXECUTED: Git review, dashboard rebuild, Merkle computation, Ed25519 signing and verification.
OBSERVED: same-key local gain preserved; 15-leaf Merkle root and cryptographic verification PASS.
DECISIONS: Apache-2.0 authorized original code; CC BY-NC-ND 4.0 designated owned original content; third-party rights unresolved.
PROPOSED: organizational signing identity and donor-disjoint external validation.
NOT_TESTED: organizer upload receipt, clinical transfer.
FAILURES: previous EndoForge test collection missing Streamlit; 3 of 7 synthetic paraphrase robustness controls failed.
UNRESOLVED: challenge licensing terms, contributor rights, historical Git data exposure.
NEXT_ACTION: peer review and organizer acceptance proof, then future governed validation.
