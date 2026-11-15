#!/usr/bin/env python3
"""Verify public deterministic Merkle snapshot and SSH Ed25519 signature.

Uses the committed public key only; no private-key access. A successful
signature is proof of message integrity under THAT key, not a human or
OpenAI identity attestation, official upload, or scientific correctness.
"""
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from dashboard_merkle import ROOT,MANIFEST,check

EVIDENCE = ROOT / 'docs/evidence'
MESSAGE = EVIDENCE / '20261114_dashboard_attestation_message.txt'
SIGNATURE = EVIDENCE / '20261114_dashboard_attestation_message.txt.sig'
PUBKEY = EVIDENCE / 'keys/dnaforge_dashboard_tool_ed25519.pub'
IDENTITY = 'dnaforge-review-tool'
NAMESPACE = 'dnaforge-dashboard'

def verify():
    record=check()
    if shutil.which('ssh-keygen') is None:
        raise RuntimeError('ssh-keygen missing; signature NOT_VERIFIED')
    msg=MESSAGE.read_bytes()
    line_map={}
    for line in msg.decode('utf8').splitlines():
        if '=' in line:
            k,v=line.split('=',1)
            line_map[k]=v
    assert msg.endswith(b'\n') and msg.startswith(b'DNAFORGE_DASHBOARD_ATTESTATION_V1\n')
    assert line_map['project']=='biobitworks/dna-forge'
    assert line_map['parent_git_sha1']==record['parent_git_sha1']
    assert line_map['leaf_count']==str(record['leaf_count'])
    assert line_map['root_sha256']==record['root_sha256']
    assert line_map['manifest_sha256']==hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert line_map['signature_identity']==IDENTITY
    assert line_map['signature_namespace']==NAMESPACE
    assert line_map['signer_role']=='LOCAL_TOOL_GENERATED_KEY_NOT_ORGANIZATIONAL_IDENTITY'
    p=PUBKEY.read_text().strip()
    assert p.startswith('ssh-ed25519 ') and len(p.split())>=2
    keyinfo=subprocess.run(['ssh-keygen','-l','-E','sha256','-f',str(PUBKEY)],capture_output=True,text=True,check=True)
    assert line_map['public_key_fingerprint'] in keyinfo.stdout
    assert SIGNATURE.read_bytes().startswith(b'-----BEGIN SSH SIGNATURE-----')
    with tempfile.TemporaryDirectory(prefix='dnaforge-attest-') as temp:
        signers=Path(temp)/'signers'
        signers.write_text(IDENTITY+' '+p+'\n')
        verify=subprocess.run([
            'ssh-keygen','-Y','verify','-f',str(signers),
            '-I',IDENTITY,'-n',NAMESPACE,'-s',str(SIGNATURE)],
            input=msg,capture_output=True)
        if verify.returncode:
            raise ValueError('SSH signature verification FAILED: '+verify.stderr.decode('utf8','replace'))
    return record,line_map

if __name__=='__main__':
    r,m=verify()
    print('DASHBOARD_SIGNATURE_VERIFICATION_PASS',
          'ROOT',r['root_sha256'],
          'SIGNER_KEY',m['public_key_fingerprint'],
          'ASSERTION','BYTES_ONLY_NOT_PERSON_OR_ORGANIZATION',
          'MMR',r['mmr'])
