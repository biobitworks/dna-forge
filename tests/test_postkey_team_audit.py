"""Post-key aggregate equality; no raw answer key in public repository."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[1]
def read(p):
 return json.loads((ROOT/p).read_text())
def test_aggregate_matches_prior_local_score_projection():
 a=read('docs/evidence/20261114_postkey_matched_baselines_aggregate.json')
 b=read('docs/evidence/20261114_local_selfscore_aggregates.json')
 assert a['schema']=='dnaforge.judges.postkey-matched-baselines-aggregate.v1'
 assert a['answer_key_sha256']==b['key_sha256']
 assert math.isclose(a['reports']['team_macro_f1'],b['metrics']['criteria_mean_f1'])
 assert math.isclose(a['slides']['team_c1_accuracy'],b['metrics']['c1_accuracy'])
 assert math.isclose(a['slides']['team_c2_precision']['5'],b['metrics']['c2_p5'])
 assert a['slides']['team_c1_correct']==60 and a['slides']['baseline_c1_correct']==47
 assert a['reports']['n_criteria']==30
 assert a['reports']['baseline_nonempty_criteria']==23
def test_paired_contingency_and_deltas():
 a=read('docs/evidence/20261114_postkey_matched_baselines_aggregate.json')
 p=a['slides']['paired_c1_confusion']
 assert sum(p.values())==67
 assert p['team_only_correct']==14 and p['baseline_only_correct']==1
 assert math.isclose(a['slides']['paired_c1_exact_mcnemar_two_sided_p'],2*(1+15)/2**15)
 assert math.isclose(a['slides']['delta_pp']['c1_accuracy_pp'],100*13/67)
 assert math.isclose(a['reports']['delta_f1'],1-a['reports']['baseline_macro_f1'])
def test_documentation_scope_and_no_private_rows():
 a=(ROOT/'docs/evidence/20261114_postkey_matched_baselines_aggregate.json').read_text()
 for forbidden in ('/Users/','SYN-','SUPP-','report_text','test_labels'):
  assert forbidden not in a
 for rel in ('README.md','docs/SUBMISSION.md','docs/judges/README_20261114.md'):
  text=(ROOT/rel).read_text()
  assert 'NOT_VERIFIED' in text
  assert 'post-key' in text.lower()
  assert 'TEAM_THESIS_TASK_COMMIT_AUDIT_20261114.md' in text
 audit=(ROOT/'docs/judges/TEAM_THESIS_TASK_COMMIT_AUDIT_20261114.md').read_text()
 assert 'NOT_VERIFIED' in audit and 'post-key' in audit.lower()
 assert '20 merged PRs' in (ROOT/'README.md').read_text()
 assert 'not for a linked' in (ROOT/'README.md').read_text().lower()
