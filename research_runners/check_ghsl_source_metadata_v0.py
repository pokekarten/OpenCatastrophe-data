# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Check that newly researched GHSL source candidates are not admitted."""
import json
from pathlib import Path

def check(root):
    ids=[]
    for path in ('landscape/sources-ghsl-built-s-2026.json','landscape/sources-ghsl-built-v-2026.json'):
        data=json.loads((Path(root)/path).read_text())
        if len(data.get('entries', [])) != 1: raise ValueError('One source per file required')
        item=data['entries'][0]
        if item.get('admission_status') != 'not_admitted': raise ValueError('Source must not be admitted')
        if item.get('rights_review_status') != 'not_reviewed': raise ValueError('Rights need independent review')
        if item.get('scientific_review_status') != 'not_reviewed': raise ValueError('Scientific review pending')
        ids.append(item['candidate_id'])
    if len(set(ids)) != 2: raise ValueError('Duplicate GHSL source identity')
    return ids


def test_current_catalogue(root):
    ids = check(root)
    if ids[0] != 'ec-jrc.ghsl.ghs-built-s.r2023a': raise ValueError('Wrong built area product')
    if ids[1] != 'ec-jrc.ghsl.ghs-built-v.r2023a': raise ValueError('Wrong built volume product')
    for path, unit in zip(('landscape/sources-ghsl-built-s-2026.json','landscape/sources-ghsl-built-v-2026.json'),('m2','m3')):
        entry=json.loads((Path(root)/path).read_text())['entries'][0]
        if unit not in entry.get('resolution_or_granularity',''): raise ValueError('Incorrect GHSL units')
        if not entry.get('authoritative_url','').startswith('https://'): raise ValueError('Official URL missing')
        if not entry.get('note'): raise ValueError('Scientific caveat missing')
    return {'candidate_count': len(ids), 'model_input_admitted': False}


if __name__ == '__main__':
    print(test_current_catalogue(Path(__file__).resolve().parents[1]))
