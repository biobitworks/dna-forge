#!/usr/bin/env python3
"""Deterministic 0x00-leaf / 0x01-parent binary Merkle tree over PUBLIC files.

Scope is an immutable document/source snapshot. No MMR or signed identity
is inferred from the Merkle root; signature verified separately.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/evidence/20261114_dashboard_merkle_v1.json'
PARENT = '2f23887a3a0dcf94f2f679744f25210dc5b84286'
# Explicit list = canonical membership. Sort lexicographically by UTF-8 path.
PATHS = tuple(sorted((
    '.github/workflows/dashboard-attestation.yml',
    'LICENSE',
    'LICENSING.md',
    'NOTICE.md',
    'README.md',
    'docs/evidence/20261114_postkey_matched_baselines_aggregate.json',
    'docs/evidence/20261114_team_upload_merge_aggregate.json',
    'docs/judges/LOMO_JUDGE_DASHBOARD_20261114.html',
    'docs/judges/TEAM_THESIS_TASK_COMMIT_AUDIT_20261114.md',
    'scripts/assets/lomo_judge_dashboard_template.html',
    'scripts/build_judge_lomo_heatmap.py',
    'scripts/dashboard_merkle.py',
    'scripts/verify_dashboard_attestation.py',
    'tests/test_judge_heatmap.py',
    'tests/test_team_license_dashboard.py',
)))

def sha(raw):
    return hashlib.sha256(raw).digest()

def canonical_leaf(path, digest_hex):
    # Full delimiter rule and path bytes are specified; no ambiguous joins.
    name = path.encode('utf-8')
    assert b'\x00' not in name and b'\n' not in name
    payload = b'DNAFORGE_DASHBOARD_LEAF_V1\x00' + name + b'\x00' + digest_hex.encode('ascii')
    return sha(b'\x00' + payload)

def tree_root(leaf_hashes):
    if not leaf_hashes:
        raise ValueError('empty Merkle tree')
    level = list(leaf_hashes)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])  # duplicate final node when odd
        level = [sha(b'\x01' + level[j] + level[j+1])
                 for j in range(0,len(level),2)]
    return level[0].hex()

def construct(root=ROOT):
    leaves = []
    for i,rel in enumerate(PATHS):
        p = root / rel
        if not p.is_file() or p.is_symlink():
            raise ValueError('missing / symlink leaf: '+rel)
        raw = p.read_bytes()
        digest = sha(raw).hex()
        leaves.append({
            'index':i,'path':rel,'bytes':len(raw),
            'content_sha256':digest,
            'leaf_sha256':canonical_leaf(rel,digest).hex(),
        })
    return {
        'schema':'dnaforge.dashboard.merkle.v1',
        'type':'BINARY_MERKLE_SNAPSHOT_NOT_MMR',
        'project':'biobitworks/dna-forge',
        'parent_git_sha1':PARENT,
        'construction':'ordered UTF-8 path ascending; content sha256 over raw file bytes; leaf sha256(0x00 || ASCII DNAFORGE_DASHBOARD_LEAF_V1 || 0x00 || UTF8 path || 0x00 || lowercase content SHA256 hex); parent sha256(0x01 || 32-byte raw left hash || 32-byte raw right hash); odd level duplicates its final child; no JSON canonicalization of file contents',
        'leaf_order':'utf8_lexicographic_path',
        'leaves':leaves,
        'leaf_count':len(leaves),
        'root_sha256':tree_root([bytes.fromhex(x['leaf_sha256']) for x in leaves]),
        'mmr':'NOT_COMPUTED',
        'signature':'SEPARATE_SSH_ED25519_SIGNATURE_VERIFIED_BY_VERIFY_SCRIPT',
        'scope_limit':'Only explicitly listed public files; not whole Git repo, original data, identity, ownership, scientific truth or upload evidence',
    }

def canonical_json(o):
    return (json.dumps(o,ensure_ascii=True,sort_keys=True,indent=2)+'\n').encode('utf8')

def check(root=ROOT, manifest=MANIFEST):
    observed=construct(root)
    stored=json.loads(manifest.read_bytes())
    if canonical_json(stored)!=canonical_json(observed):
        raise ValueError('Merkle manifest vs source file mismatch')
    if stored['root_sha256']!=tree_root([bytes.fromhex(x['leaf_sha256']) for x in stored['leaves']]):
        raise ValueError('Merkle recomputation mismatch')
    return observed

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--write',action='store_true')
    ap.add_argument('--check',action='store_true')
    a=ap.parse_args()
    if a.write:
        MANIFEST.write_bytes(canonical_json(construct()))
    result=check() if a.check else construct()
    print('DASHBOARD_BINARY_MERKLE_PASS','LEAVES',result['leaf_count'],'ROOT',result['root_sha256'],'MMR',result['mmr'])

if __name__=='__main__':
    main()
