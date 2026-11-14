# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Reproducible empirical year-block resampling of an explicit scenario schedule.

Retains within-year event membership and zero-event years. IID sampling of
whole years is an assumption, not proof of stationarity or calibrated rates.
"""
import copy
import hashlib
import json


def resample_config(config,simulation_years,seed):
    if type(simulation_years) is not int or not 1<=simulation_years<=100000:
        raise ValueError('1..100000 simulation years required')
    if type(seed) is not int:raise ValueError('integer resampling seed required')
    years=config['year_ids']
    if not years or any(type(y) is not int for y in years) or len(set(years))!=len(years):
        raise ValueError('unique explicit source years including zero-event years required')
    years=sorted(years);blocks={year:[] for year in years};seen=set()
    for entry in config['occurrences']:
        year=entry['year_id'];identity=entry['occurrence_id']
        if type(year) is not int or year not in blocks:raise ValueError('occurrence year outside source measure')
        if not isinstance(identity,str) or not identity or (year,identity) in seen:
            raise ValueError('invalid or duplicate source occurrence')
        seen.add((year,identity));blocks[year].append(entry)
    result=copy.deepcopy(config);result['year_ids']=list(range(1,simulation_years+1));result['occurrences']=[]
    mapping=[]
    for target in result['year_ids']:
        key=json.dumps(['wind-year-block-v1',seed,target],separators=(',',':')).encode()
        # Rejection avoids modulo bias in the discrete year selection.
        size=len(years);ceiling=2**256-(2**256%size);attempt=0
        while True:
            value=int.from_bytes(hashlib.sha256(key+str(attempt).encode()).digest(),'big')
            if value<ceiling:break
            attempt+=1
        source_year=years[value%size]
        mapping.append(dict(simulation_year=target,source_year=source_year))
        for entry in sorted(blocks[source_year],key=lambda e:e['occurrence_id']):
            event=copy.deepcopy(entry);event['year_id']=target
            result['occurrences'].append(event)
    provenance=dict(method='iid_empirical_whole_year_blocks_v1',seed=seed,source_year_ids=years,
                    simulation_years=simulation_years,source_zero_event_years=sum(not b for b in blocks.values()),
                    assumptions=['source years equally weighted','IID resampling between years','within-year event membership retained'],
                    source_calendar_completeness_verified=False,annual_frequency_calibrated=False,
                    mapping=mapping)
    return result,provenance
