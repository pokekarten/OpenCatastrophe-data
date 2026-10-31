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


def test_current_catalogue(root):
    ids = check(root)
    assert ids[0] == 'ec-jrc.ghsl.ghs-built-s.r2023a'
    assert ids[1] == 'ec-jrc.ghsl.ghs-built-v.r2023a'
    for path, unit in zip(('landscape/sources-ghsl-built-s-2026.json','landscape/sources-ghsl-built-v-2026.json'),('m2','m3')):
        entry=json.loads((Path(root)/path).read_text())['entries'][0]
        assert unit in entry['resolution_or_granularity']
        assert entry['authoritative_url'].startswith('https://')
        assert entry['note']
    return {'candidate_count': len(ids), 'model_input_admitted': False}


if __name__ == '__main__':
    print(test_current_catalogue(Path(__file__).resolve().parents[1]))
