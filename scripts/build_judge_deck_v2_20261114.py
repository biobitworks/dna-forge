#!/usr/bin/env python3
"""Rebuild a shareable, source-backed DNA Forge judge methods deck.

This slide deck deliberately contains NO original challenge IDs,
reports, embeddings, pred rows, thumbnails or secrets.
Install python-pptx in an isolated environment before execution.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
import sys

NAVY=RGBColor(8,16,31); PANEL=RGBColor(20,35,54)
WHITE=RGBColor(238,243,248); MUTED=RGBColor(164,188,211)
GOLD=RGBColor(223,179,87); TEAL=RGBColor(81,201,207)
RED=RGBColor(241,138,143); GREEN=RGBColor(111,208,170)
P=Presentation();P.slide_width=Inches(13.333);P.slide_height=Inches(7.5)

def shape(s,x,y,w,h,color=PANEL,round=False):
 t=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
 t.fill.solid();t.fill.fore_color.rgb=color;t.line.fill.background()

def text(s,content,x,y,w,h,size=17,color=WHITE,bold=False):
 t=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));f=t.text_frame;f.clear();f.word_wrap=True
 for i,line in enumerate(content.split("\n")):
  p=f.paragraphs[0] if i==0 else f.add_paragraph()
  p.text=line;p.font.name="Aptos";p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color
  p.space_after=Pt(4)

def slide(title,kicker):
 s=P.slides.add_slide(P.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=NAVY
 shape(s,0,0,.13,7.5,GOLD);text(s,kicker.upper(),.65,.36,11,.32,11,GOLD,True)
 text(s,title,.65,.91,12,1.05,27,WHITE,True)
 shape(s,.65,6.95,12,.015,RGBColor(49,65,87))
 text(s,"DNA Forge × Biobase • Nov 14 2026 • development evidence, not clinical validation",.71,7.08,11,.26,10,MUTED)
 text(s,str(len(P.slides)).zfill(2),12.26,7.06,.5,.3,10,GOLD,True)
 return s

def card(s,heading,body,x,y,w,h,accent=TEAL):
 shape(s,x,y,w,h,PANEL,True);shape(s,x,y,.06,h,accent)
 text(s,heading,x+.23,y+.18,w-.38,.4,17,accent,True)
 text(s,body,x+.23,y+.77,w-.49,h-.81,14,WHITE)

def rows(title,items,kicker):
 s=slide(title,kicker)
 for i,(a,b) in enumerate(items):
  y=1.91+i*.91;shape(s,.89,y,11.55,.75,PANEL,True)
  text(s,a,1.12,y+.15,3.2,.42,14,GOLD,True)
  text(s,b,4.13,y+.15,7.9,.48,15,WHITE)
 return s

s=slide("Find the Right Patients","Synthetic pathology AI and traceable evidence")
text(s,"From supplied pathology embeddings to locally fitted models and exactly reproducible outputs.",.8,2.18,11.9,1.2,25,WHITE)
text(s,"TASK A / 30 CRITERIA     •     C1 / ORGAN     •     C2 / SIMILAR SLIDES",.86,4.17,11.6,.42,19,TEAL,True)
text(s,"biobitworks/dna-forge",.88,5.38,10,.42,20,GOLD,True)
text(s,"MagicPro × MagicStudio • Local observed snapshot 15:16:56 PT",.88,6.1,11,.42,14,MUTED)

s=slide("Three tasks: no artificial report–slide identity join","The official challenge")
card(s,"A / CRITERIA","9,010 labeled train reports\n979 unlabeled test reports\n30 authored filters\nFormat: criterion → matching IDs",.72,2.0,3.86,3.86)
card(s,"C1 / ORGAN","263-slide manifest\n190 usable labeled slides\n67 held-out queries\nOutput: organ CSV",4.75,2.0,3.86,3.86,GOLD)
card(s,"C2 / SIMILAR","67 queries × 10 neighbors\n670 ranked rows\nNo self match\nOutput: similarity CSV",8.79,2.0,3.86,3.86,GREEN)
text(s,"Organizers supplied separate report and slide datasets; no validated patient-to-slide crosswalk.",.92,6.23,11.7,.42,13,RED)

rows("Governed source → derived outputs",[
 ("SOURCE","Five original ZIP packs; source rights and permissions remain a gate"),
 ("IDENTITY","Content SHA-256 does not confer permission or accuracy"),
 ("ATOM / FCO","Report predicates, image vectors, fold and run identities"),
 ("TYPED FCG","Declared relationships with independently addressable context"),
 ("ARTIFACT","Private selected files; public-safe hashes and receipts")],"Data transformation and privacy")

s=slide("Pretrained ≠ trained here","Model provenance")
card(s,"SUPPLIED / FROZEN","Prov-GigaPath\nH-optimus-0\nBiomedCLIP\nDINOv2\nNo backbone fine-tuning locally",.8,1.97,5.72,4.0,GOLD)
card(s,"LOCALLY FITTED","Selected: linear SVM ensemble\nAlternatives: LR and kNN\nExperimental attention-MIL\nExperimental stacking\nReports: explicit rules, no weights",6.81,1.97,5.72,4.0,TEAL)
text(s,"No pretrained encoder weight files or trained binary checkpoints are distributed in GitHub.",.9,6.3,11.3,.39,13,MUTED)

rows("Controlled local fitting: same folds on both Macs",[
 ("INPUT","GigaPath + H-optimus supplied feature vectors"),
 ("FIT","190 organ-labeled slides; shared SHA-pinned 5-fold split"),
 ("MODEL","Small selected ens-SVM; other candidates compared"),
 ("OUTPUT","67 organ predictions and 670 ranked similarity rows"),
 ("REPLAY","Pinned Python / NumPy / SciPy / scikit-learn versions, 5/5 output SHA matches")
 ],"Training, evaluation and reproduction")

s=slide("LOMO and supplier shift", "Ablations and negative evidence")
card(s,"CONTROLLED REMOVALS","Embedding-family sweeps and leave-one-module-out comparisons. GigaPath remains influential. Alternative MIL / stacking did not exceed the chosen development winner.",.8,2.04,5.72,3.78,GOLD)
card(s,"EXTERNAL VALIDITY","Supplier-held-out accuracy dropped versus shared folds. Different tissue/source domains are not proven equivalent. Preserve failure/null/negative states.",6.79,2.04,5.72,3.78,RED)
text(s,"Removing one component is a diagnostic comparison—not proof that the graph caused a model gain.",.85,6.2,11.6,.54,14,WHITE)

s=slide("Development metrics, not hidden scores","Results with uncertainty")
card(s,"TASK A","Training-derived F1 = 1.000\nKeyword baseline ~0.27\nRULES WERE AUTHORED WITH THE LABELED TRAIN SET VISIBLE",.8,2.02,3.74,3.86,RED)
card(s,"C1 ORGAN","OOF accuracy = 0.8632\nOrganizer baseline ~0.70\nNOT OFFICIAL HELD-OUT ACCURACY",4.78,2.02,3.74,3.86,GOLD)
card(s,"C2 RETRIEVAL","OOF P@1 / 5 / 10\n0.868 / 0.829 / 0.800\nOrganizer reported P@1 ~0.80",8.76,2.02,3.74,3.86,TEAL)
text(s,"No matched-split baseline rerun or post-4 PM score was available at this observation.",.86,6.31,11.6,.33,13,MUTED)

s=slide("Independent MagicPro × MagicStudio replay","Five exact matching outputs")
card(s,"MAGICPRO","Pinned clean source commit\nPython 3.9.6\nNumPy 2.0.2; SciPy 1.13.1\nscikit-learn 1.6.1\nSHA-256 computed for 5 outputs",.81,2.05,5.72,3.7,TEAL)
card(s,"MAGICSTUDIO","Same source, inputs and folds\nSame numerical environment\nIndependent model execution\n5/5 byte-identical SHA-256\nNo claim of hidden-test gain",6.76,2.05,5.72,3.7,GREEN)
text(s,"Reproducibility is an OBSERVED engineering property, not a verified biomedical conclusion.",.86,6.28,11.6,.34,14,GOLD)

rows("FCG: cryptographic identity is not causality",[
 ("SOURCE FCO","Archive, field and manifest identity"),
 ("TRANSFORM FCO","Code, model, run, fold and environment identity"),
 ("DERIVED FCO","Prediction/output hashes with scored and negative evidence"),
 ("FCG EDGES","153 declared typed relationships; 23 declared Merkle members"),
 ("PROOF CEILING","Root membership recomputed; NOT_SIGNED; MMR NOT_COMPUTED")
 ],"Chain of custody")

s=slide("Pre-key selected output identities","Protected original candidates")
card(s,"TASK A","Criteria JSON\n12,552 bytes\n1604ae15…d88345",.8,2.06,3.74,3.27,TEAL)
card(s,"C1 ORGAN","Organ CSV\n2,458 bytes\n8a69914d…cf7356",4.79,2.06,3.74,3.27,GOLD)
card(s,"C2 SIMILAR","Similarity CSV\n37,524 bytes\ned38172b…90d423",8.77,2.06,3.74,3.27,GREEN)
text(s,"Local system clock 15:16:56 PT • source/snapshot SHA verified 3/3 • official key NOT accessed",.88,5.77,11.5,.42,15,GOLD,True)
text(s,"NOT_SIGNED; no independent trusted timestamp; official upload receipt NOT_VERIFIED.",.88,6.33,11.5,.36,13,RED)

s=slide("Separate tooling: status without promotion","Orthogonal research lanes")
card(s,"DNAFORGE DESKTOP","Official Electron/Rust/Python product is separate. Install, helper builds, TS and 53 focused Python tests PASS; 174 desktop test executions PASS. Integrated GUI/API startup FAIL (preflight timeout).",.76,2.02,5.82,3.96,RED)
card(s,"DAISY / TAMARIND","Three VCC DAISY containers exited at deadlines; drug-screening ingest NOT_VERIFIED. Tamarind descriptor job COMPLETE on ethanol (MW 46.07). ChEMBL 25 IC50 activities pulled, 24 locally normalized. Drug-screening model training/docking NOT_TESTED.",6.81,2.02,5.82,3.96,GOLD)
text(s,"Neither pipeline has been validated as a Biobase model input or a clinical screening output.",.87,6.36,11.5,.38,13,MUTED)

s=slide("Judge-ready evidence and unresolved gates","Conclusion and next receipts")
card(s,"VERIFIED","Three format-valid challenge outputs\nTwo-Mac exact slide-model replay\nAuthor-defined eligibility parser\nAblations and negative tests preserved\nFCO/FCG provenance and privacy guard",.82,2.05,5.72,3.89,GREEN)
card(s,"NOT YET VERIFIED","Official answer-key scores/upload\nData agreement and sponsor opt-in\nPrior Git history remediation\nDesktop full source-start\nLicensed drug-screening ingestion\nTamarind paid calculation",6.79,2.05,5.72,3.89,RED)
text(s,"Main claim: auditable, byte-reproducible synthetic pathology selection—not new foundation-model training.",.86,6.33,11.53,.4,13,GOLD,True)

out=Path("docs/judges/DNAForge_Biobase_Judge_Methodology_20261114_v2.pptx")
P.core_properties.title="DNA Forge — Judge Methodology (Nov 14, 2026)"
P.core_properties.author="Biobitworks research team"
P.save(out)
print("GENERATED",out,"SLIDES",len(P.slides),"BYTES",out.stat().st_size)
