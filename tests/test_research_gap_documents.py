"""Reference graph uses declarations; no model or causal attestation."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'docs/references'
def test_claim_graph_edges_are_grounded_and_bounded():
 refs=json.loads((D/'CITATION_REGISTRY_20261114.json').read_text())
 graph=json.loads((D/'RESEARCH_CLAIM_GRAPH_20261114.json').read_text())
 ids={x['id'] for x in refs['items']}|{x['id'] for x in graph['claims']}
 assert len(graph['claims'])==10 and len(graph['edges'])>=15
 for x in graph['edges']:
  assert x['from'] in ids and x['to'] in ids
  assert x['type'] not in {'CAUSES','PROVES','SIGNED','MMR_COMMITTED'}
 assert graph['signing']=='NOT_SIGNED'
 assert graph['mmr']=='NOT_COMPUTED'
 assert graph['experimental_roots']=='NOT_COMPUTED'
def test_plan_separates_identity_and_human_labels():
 p=(D/'SEX_SPECIFIC_RESEARCH_GAPS_20261114.md').read_text()
 for s in ('cisgender','NOT_ADMITTED','histologist','ABSTAIN','Donor','donor','GAP01','GAP11','MMP11','VCAN','patient'):
  assert s in p,s
 assert 'NOT_COMPUTED' in p
