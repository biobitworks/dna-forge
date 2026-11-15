"""Regression gates: aggregate-only judge heatmap with explicit evidence states."""
from pathlib import Path
import json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def test_source_backed_dashboard_and_score_without_private_rows():
    p=ROOT/'docs/judges/LOMO_JUDGE_DASHBOARD_20261114.html'
    html=p.read_text()
    match=re.search(r'<script id="data" type="application/json">(.*?)</script>',html,re.S)
    assert match
    x=json.loads(match.group(1))
    assert x['schema']=='dnaforge.judges.lomo-explorer.v1'
    assert x['local_selfscore']['metrics']['criteria_mean_f1']==1
    assert x['local_selfscore']['metrics']['c1_correct']==60
    assert x['local_selfscore']['metrics']['c1_n']==67
    assert x['local_selfscore']['metrics']['c2_p5']>0.89
    assert x['official']['upload_receipt']=='NOT_VERIFIED'
    assert x['fcg']['members']==23 and x['fcg']['edges']==153
    assert x['replay']['matching_outputs']==5
    assert len(x['ablation_groups'][0]['rows'])==13
    assert len(x['ablation_groups'][1]['rows'])==10
    assert not x['ablation_groups'][0]['code_dirty']
    assert x['ablation_groups'][1]['code_dirty']
    assert x['fcg']['signing']=='NOT_SIGNED' and x['fcg']['mmr']=='NOT_COMPUTED'
    for bad in ('SUPP-', '/Users/', 'result_slide_id', 'patient_id', '"test_labels"'):
        assert bad not in html,bad
def test_builder_frozen_aggregate_replays_byte_identically():
    p=ROOT/'docs/judges/LOMO_JUDGE_DASHBOARD_20261114.html'
    before=p.read_bytes()
    proc=subprocess.run([sys.executable,str(ROOT/'scripts/build_judge_lomo_heatmap.py')],cwd=str(ROOT),capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr
    assert p.read_bytes()==before
def test_explicit_submission_label():
    j=json.loads((ROOT/'docs/evidence/20261114_local_selfscore_aggregates.json').read_text())
    assert 'NOT_ORGANIZER_CERTIFIED' in j['state']
    assert j['official_website_score']=='NOT_VERIFIED'
    assert j['organizer_uploaded']=='NOT_VERIFIED'
    assert j['signing']=='NOT_SIGNED' and j['mmr']=='NOT_COMPUTED'
