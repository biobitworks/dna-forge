"""Synthetic-only structure checks; no clinical datasets or PHI."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/references'
def records():
 return json.loads((D/'CITATION_REGISTRY_20261114.json').read_text())
def test_manifest_identity_and_ids():
 obj=records()
 assert hashlib.sha256((D/'CITATION_REGISTRY_20261114.tsv').read_bytes()).hexdigest()==obj['source_tsv_sha256']
 assert len(obj['items'])==22
 assert {x['id'] for x in obj['items']} == {'SRC%02d'%i for i in range(1,23)}
 assert len({x['url'] for x in obj['items']})==22
def test_rights_and_species_fail_closed():
 items={x['id']:x for x in records()['items']}
 assert items['SRC03']['data_license']=='UNKNOWN'
 assert items['SRC07']['status']=='UNAVAILABLE'
 assert items['SRC13']['status']=='MOUSE_HISTOLOGY_NOT_HUMAN_PCOS'
 assert items['SRC16']['status']=='NEGATIVE_Y_FISH_RESULT'
 assert all(x['admission']!='ADMITTED' for x in items.values())
def test_status_distinctions():
 text=(D/'REFERENCES_20261114.md').read_text()
 for token in ('cisgender','NOT_ADMITTED','466,371','mouse','MassIVE','microchimerism'):
  assert token in text
