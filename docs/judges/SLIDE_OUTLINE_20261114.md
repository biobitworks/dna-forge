# Judge methodology — 12-slide review outline

The companion deck is DNAForge_Biobase_Judge_Methodology_20261114.pptx.
This Markdown provides the content for text-based review.

| Slide | Subject | Bound source/claim |
|---|---|---|
| 1 | Find the Right Patients | Project challenge and objective |
| 2 | A report task, C1 organ, C2 retrieval | 9,010 train / 979 test reports; 190 labeled / 67 held-out slides |
| 3 | Input source and permission | Organizer local packs; hashes not rights |
| 4 | Pretrained backbones vs. fitted models | Frozen feature vectors, SVM, experimental MIL |
| 5 | Shared fold training, model output | Pinned code, 5-fold OOF, selected C1/C2 |
| 6 | Leave-one-module-out and domain shift | Negative evidence and supplier generalization |
| 7 | Development metrics | Correctly label F1=1.000 leakage risk |
| 8 | Two-device deterministic replay | Five exact SHA-256 matches |
| 9 | FCO/FCG graph | 23-member computed root, 153 typed edges; not signing |
| 10 | Submission artifacts | Three SHA-256s, local-clock pre-key snapshot |
| 11 | DNAForge desktop, DAISY, Tamarind | Separate incomplete integration/admission lanes |
| 12 | Judge-ready evidence and unresolved gates | No official score/upload receipt claimed |

The only defensible novel contribution is integrating and replaying
the data/model/custody workflow, not novel foundation pretraining
or clinically validated patient selection.
