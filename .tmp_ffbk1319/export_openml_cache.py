#!/usr/bin/env python3
"""Materialise the public freMTPL2 OpenML cache for an offline FFBK integration test.

Temporary execution support only. This file contains no private FFBK source.
"""
from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

from sklearn.datasets import fetch_openml, get_data_home

OUT = Path('.tmp_ffbk1319/cache_export')
OUT.mkdir(parents=True, exist_ok=True)

meta = {}
for data_id in (41214, 41215):
    fetch_openml(data_id=data_id, as_frame=True)
    with urllib.request.urlopen(
        f'https://www.openml.org/api/v1/json/data/{data_id}', timeout=60
    ) as response:
        meta[str(data_id)] = json.loads(response.read().decode())['data_set_description']

(OUT / 'openml-meta.json').write_text(
    json.dumps(meta, indent=2, sort_keys=True) + '\n', encoding='utf-8'
)
cache = Path(get_data_home())
shutil.make_archive(str(OUT / 'scikit_learn_data'), 'gztar', cache.parent, cache.name)
print(f'OPENML_CACHE_EXPORT_OK cache={cache}')
