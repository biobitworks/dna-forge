"""Synthetic-only integrity test of teammate handoff references."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_primary_readme_links_exist():
    for rel in (
        "README.md", "docs/SUBMISSION.md",
        "docs/MODEL_TRAINING_HANDOFF_20261114.md",
        "docs/PRESENTATION_REVIEW_20261114.md",
        "docs/PI_PM_CLAUDE_RECOVERY_CROSSNODE_20261114.md",
        "docs/evidence/20261114_enssvm_crossnode_verified.json",
        "scripts/verify_selected_submission.py",
        "notebooks/05_crossnode_enssvm_replay.ipynb",
        "envs/biobase-enssvm-crossnode-20261114.txt",
    ):
        assert (ROOT / rel).is_file(), rel

def test_readme_separates_performance_evidence():
    text = (ROOT/"README.md").read_text()
    for term in ("NOT_COMPUTED", "NOT_VERIFIED", "4 PM", "cross", "MagicPro", "MagicStudio", "SHA-256"):
        assert term in text, term

def test_replay_numerical_versions_pinned():
    p=(ROOT/"envs/biobase-enssvm-crossnode-20261114.txt").read_text()
    for line in ("numpy==2.0.2","scipy==1.13.1","scikit-learn==1.6.1"):
        assert line in p
