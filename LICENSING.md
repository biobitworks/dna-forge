# DNA Forge / Biobase — scoped software and research licensing

**Rights policy introduced by the 2026-11-14 dashboard successor.** This
is a **prospective scope declaration for rights that the grantor
actually controls**, not evidence of ownership, consent, permission to
redistribute organizer assets, or retroactive relicensing of contributions.

## 1. Apache License, Version 2.0 — original software

The root [LICENSE](LICENSE) contains the unmodified official
[Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) legal text.
To the extent the relevant copyright holder has authorized publication,
the repository's original Biobitworks-controlled **software**—including
dnaforge/, applicable scripts/, tests/, code examples,
notebooks-as-executable-code, and the interactive judge dashboard's
HTML/CSS/JavaScript—is made available under **Apache-2.0**.

Apache-2.0 grants a copyright license and a conditional patent license
subject to its terms. It does **not** certify scientific correctness,
clinical safety, source data permissions or ownership.

## 2. CC BY-NC-ND 4.0 — designated original research content

To the extent Biobitworks / Cellico.Bio owns and can license the
underlying material, **original research text, explanations, figures,
methodology slide decks, research plans, and designated FCO/FCG
prose/visual content** are provided under
[Creative Commons Attribution–NonCommercial–NoDerivatives 4.0
International](https://creativecommons.org/licenses/by-nc-nd/4.0/).

Exact default notice:

> Unless otherwise explicitly licensed, original Biobitworks /
> Cellico.Bio material is licensed under CC BY-NC-ND 4.0; third-party
> components remain under their respective licenses.

The license's NoDerivatives restriction may limit sharing adaptations.
It is **not** applied automatically to software explicitly designated
Apache-2.0.

## 3. Explicit exceptions and unresolved ownership

- **Teammate-authored directories:** Patient selector/ and
  EndoForge-20261115T001037Z-1-001/ were directly pushed by the
  contributor recorded as efrazar / Efrazar. The maintainer's
  authority to relicense those entire folders has **NOT_BEEN_VERIFIED**.
  Do not treat the root Apache-2.0 license as a grant for any
  independently owned contributor files absent a documented grant.
  Their original authors' rights remain in force; explicit per-file
  grants take precedence.
- **Third-party software, models, datasets and reference assets**
  retain their own licenses and redistribution limits, including
  upstream GigaPath, H-optimus, BiomedCLIP, DINOv2, HistAI,
  Kaggle, Synthea and literature sources. No claim is made that all
  these assets can be redistributed. Full challenge data agreement
  and source permission remain **UNKNOWN / NOT_VERIFIED**.
- **Frozen competition predictions, downloaded answer keys, raw
  reports, slides, embeddings and identity maps** are private local
  assets, are not placed in this repository, and are not granted to
  third parties under either license by this document.
- **Repository-generated SHA-256 and Merkle hashes are evidence of
  byte identity only.** The rights to a digest, original source,
  public aggregate, and derived figure are separately governed.
- **Separate proprietary/private work** (including unrelated DAISY,
  invention records, credentials, internal data and other project
  repos) is NOT licensed by this repository's LICENSE.
- Trademarks and branding are not licensed merely by Apache-2.0.

**Ambiguity gate:** If ownership or permissions are unknown, the
affected contribution is RIGHTS_UNVERIFIED, not silently promoted
to Apache-2.0 or CC BY-NC-ND. A future rights-clearing revision must
be an append-only successor with contributor evidence. Historical
publication of generated challenge outputs in Git remains unresolved
and is not cured by changing repository license files.

## 4. Provenance and signatures

The separate signed dashboard evidence, where present, uses a
**locally generated tool-attestation Ed25519 key**. Such a key proves
only that someone controlling the signing private key signed the
specified bytes. It is **not** a person's legal signature, OpenAI's
organizational signature, a verified contributor identity, or evidence
of ownership or scientific truth.

See docs/judges/TEAM_DASHBOARD_HANDOFF_20261114.md for the exact
verified signed-message path, public key fingerprint, computed Merkle
construction, and trust limits. No private signing key belongs in Git.
A binary Merkle tree root is not an MMR commitment.
