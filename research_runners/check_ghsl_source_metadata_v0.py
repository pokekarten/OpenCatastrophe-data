"""Check that newly researched GHSL source candidates are not admitted."""
import json
from pathlib import Path

def check(root):
    ids=[]
    for path in ('landscape/sources-ghsl-built-s-2026.json','landscape/sources-ghsl-built-v-2026.json'):
        data=json.loads((Path(root)/path).read_text())
        assert len(data['entries']) == 1
        item=data['entries'][0]
        assert item['admission_status'] == 'not_admitted'
        assert item['rights_review_status'] == 'not_reviewed'
        assert item['scientific_review_status'] == 'not_reviewed'
        ids.append(item['candidate_id'])
    assert len(set(ids)) == 2
    return ids
