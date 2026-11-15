"""Public-safe teammate upload + licensing + signed binary Merkle regression gates."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from dashboard_merkle import PATHS, canonical_leaf, tree_root, check, construct
from verify_dashboard_attestation import verify

def test_team_snapshot_git_identity_and_relevance():
    src=json.loads((ROOT/'docs/evidence/20261114_team_upload_merge_aggregate.json').read_text())
    assert src['snapshot_main_commit']=='2f23887a3a0dcf94f2f679744f25210dc5b84286'
    assert src['merged_pr_count']==len(src['merged_pr_numbers'])==21
    assert src['open_pr_count']==0
    assert set((1,12,13,15,16,17,18,19,20,21,22,23,24,25,27,29,30,31,32,33,34))==set(src['merged_pr_numbers'])
    events={e['id']:e for e in src['team_events']}
    assert events['selector']['git_author']=='efrazar'
    assert events['endoforge']['git_sha']=='30b6e0799a61'
    assert 'DOES NOT raise official Biobase test scores' in events['endoforge']['impact']
    assert 'NOT_VERIFIED'==src['official_submission_state']
    assert 'UNRESOLVED'==src['historical_exposure_state']

def test_exact_same_key_score_and_immutable_frozen_outputs():
    team=json.loads((ROOT/'docs/evidence/20261114_team_upload_merge_aggregate.json').read_text())
    scored=json.loads((ROOT/'docs/evidence/20261114_postkey_matched_baselines_aggregate.json').read_text())
    original=json.loads((ROOT/'docs/evidence/20261114_local_selfscore_aggregates.json').read_text())
    assert team['selected_submission_sha256']==original['frozen_submissions_sha256']
    assert scored['answer_key_sha256']==original['key_sha256']
    assert scored['slides']['team_c1_correct']==60
    assert scored['slides']['baseline_c1_correct']==47
    assert scored['reports']['team_macro_f1']==1
    assert abs(scored['reports']['baseline_macro_f1']-0.2728699458256888)<1e-14
    assert scored['slides']['paired_c1_exact_mcnemar_two_sided_p']==0.0009765625

def test_dashboard_has_team_matched_scores_rights_and_no_row_data():
    html=(ROOT/'docs/judges/LOMO_JUDGE_DASHBOARD_20261114.html').read_text()
    assert '<section id="matched">' in html
    assert '<section id="team">' in html
    assert 'Apache-2.0' in html
    assert 'CC BY-NC-ND 4.0' in html
    assert 'TEAM_DASHBOARD_HANDOFF_20261114.md' in html
    assert 'NOT ORGANIZER CERTIFIED' in html
    assert 'LOCAL' in html
    for marker in ('SUPP-','SYN-','/Users/','patient_id','result_slide_id','"test_labels"','PRIVATE KEY'):
        assert marker not in html
    assert html.count('id="data"')==1
    data=json.loads(html.split('<script id="data" type="application/json">',1)[1].split('</script>',1)[0])
    assert data['team_uploads']['merged_pr_count']==21
    assert len(data['team_uploads']['team_events'])==7
    assert data['matched_baselines']['slides']['team_c1_correct']==60

def test_software_and_content_scopes_with_exceptions():
    lic=(ROOT/'LICENSE').read_text()
    assert 'Apache License' in lic[:200] and 'Version 2.0' in lic[:250]
    assert len(lic)>10000
    policy=(ROOT/'LICENSING.md').read_text()
    assert 'CC BY-NC-ND 4.0' in policy
    assert 'Apache-2.0' in policy
    assert 'RIGHTS_UNVERIFIED' in policy
    assert 'EndoForge-' in policy and 'Patient selector/' in policy
    assert 'NOT_VERIFIED' in policy
    assert (ROOT/'NOTICE.md').is_file()

def test_merkle_canonical_bytes_and_signed_root_verification():
    tree=check()
    assert len(PATHS)==tree['leaf_count']==15
    assert tree['root_sha256']==tree_root([bytes.fromhex(x['leaf_sha256']) for x in tree['leaves']])
    assert tree['mmr']=='NOT_COMPUTED'
    assert canonical_leaf('a.md','0'*64)!=canonical_leaf('b.md','0'*64)
    assert canonical_leaf('a.md','0'*64)!=canonical_leaf('a.md','1'*64)
    verified,msg=verify()
    assert verified['root_sha256']==tree['root_sha256']
    assert msg['signer_role']=='LOCAL_TOOL_GENERATED_KEY_NOT_ORGANIZATIONAL_IDENTITY'

def test_html_and_merkle_replay_deterministically():
    output=ROOT/'docs/judges/LOMO_JUDGE_DASHBOARD_20261114.html'
    before=output.read_bytes()
    r=subprocess.run([sys.executable,str(ROOT/'scripts/build_judge_lomo_heatmap.py')],capture_output=True,text=True,cwd=ROOT)
    assert r.returncode==0,r.stderr
    assert before==output.read_bytes()
    assert check()['root_sha256']
