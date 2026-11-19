# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Inventory original CLIMK event views without inferring occurrence rates."""
import argparse
import hashlib
import json
from pathlib import Path


def inventory(paths):
    from netCDF4 import Dataset
    views = []
    sources = []
    for path in paths:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest in sources:
            raise ValueError('duplicate source bytes')
        sources.append(digest)
        with Dataset('original', memory=raw) as ds:
            names = ds.variables['Storm_Names'][:]
            dates = ds.variables['Storm_Dates'][:]
            if len(names) != 50 or len(dates) != 50:
                raise ValueError('expected 50 source-selected events')
            for index, (name, date) in enumerate(zip(names, dates)):
                views.append(dict(source_sha256=digest, source_file=path.name,
                                  source_storm_index=index,
                                  provider_name=str(name).strip(),
                                  provider_date_label=str(date).strip()))
    groups = {}
    for v in views:
        key = (v['provider_name'].casefold(), v['provider_date_label'])
        groups.setdefault(key, []).append(v)
    return dict(schema='CLIMK_MULTISOURCE_EVENT_INVENTORY_V1',
                source_count=len(sources), source_view_count=len(views),
                complete_annual_catalogue=False, annual_rates_established=False,
                grouping='literal case-insensitive name and exact provider date; candidate identity only',
                events=[dict(provider_name_key=k[0],provider_date_label=k[1],
                             source_views=v) for k,v in sorted(groups.items())])


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():p.error('refuse overwrite')
    result=inventory(args.source)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(dict(source_count=result['source_count'],source_views=result['source_view_count'],candidate_groups=len(result['events']),complete_annual_catalogue=False)))
