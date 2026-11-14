# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Integrated conditional Windstorm Europe research model.

Run configuration explicitly supplies exposure, response classes, sampled
occurrences and financial terms. Selected CLIMK scenarios supply no rates.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_runners.climk_germany_hazard_geojson_v0 import export,validate_bounds
from research_runners.climk_building_hazard_join_v0 import join_points
from research_runners.germany_wind_scenario_loss_v0 import read_curve
from research_runners.windstorm_europe_damage_samples_v0 import response,sample_policy_losses
from research_runners.windstorm_europe_financial_years_v0 import aggregate


def construction_curve(path,column):
    """Read a declared percent response as a deterministic damage assumption."""
    with path.open(newline='') as f:
        reader=csv.DictReader(f)
        names=[n.strip() for n in reader.fieldnames or []]
        if not names or names[0]!='wind speed' or column not in names or len(set(names))!=len(names):
            raise ValueError('construction curve column absent or ambiguous')
        rows=[]
        for raw in reader:
            row={k.strip():v for k,v in raw.items()}
            rows.append((float(row['wind speed']),1.0,float(row[column])/100))
    # PAA=1 explicitly encodes deterministic response, not inferred occurrence.
    response(rows[0][0],rows)
    return rows


def execute(config,base,hazard_loader=None):
    if config.get('profile')!='windstorm-europe-research-v1': raise ValueError('unsupported model profile')
    if config.get('annual_schedule_basis')!='explicit_user_scenario_not_calibrated':
        raise ValueError('this version supports explicit scenario years only')
    if type(config.get('seed')) is not int: raise ValueError('integer seed required')
    bounds=validate_bounds(config['bounds'])
    sites=config['buildings']
    if not isinstance(sites,list) or not 1<=len(sites)<=10000: raise ValueError('bounded nonempty portfolio required')
    groups={}; countries=set()
    for s in sites:
        if not isinstance(s.get('country'),str) or len(s['country'])!=2 or not s['country'].isupper():
            raise ValueError('explicit ISO alpha-2 country required')
        countries.add(s['country'])
        if s['policy_id'] not in config['policies']: raise ValueError('building references unknown policy')
        value=s['building_value_eur']
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0: raise ValueError('positive EUR replacement value required')
        if not isinstance(s.get('dependence_group'),str) or not s['dependence_group']:raise ValueError('explicit dependence group required')
        groups.setdefault(s['response_id'],[]).append(s)
    curves={}; source_hashes={}
    for name,spec in config['responses'].items():
        path=(base/spec['path']).resolve();raw=path.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=spec['sha256']:raise ValueError('external response source hash mismatch')
        source_hashes[name]=digest
        if spec['kind']=='paa_mdd_two_point':curves[name]=read_curve(path)
        elif spec['kind']=='construction_percent_deterministic':curves[name]=construction_curve(path,spec['column'])
        else:raise ValueError('unsupported response law')
    if set(groups)-set(curves):raise ValueError('building response class missing')
    if hazard_loader is None:
        original=(base/config['hazard_source']).read_bytes()
        hazard_loader=lambda index:export(original,index,bounds)
    cache={}; paired_by_event={}; provenance=[]; occurrences=[]
    identity_to_storm={}
    for entry in config['occurrences']:
        index=entry['storm_index']; identity=entry['occurrence_id']
        if type(index) is not int or not 0<=index<50:raise ValueError('CLIMK source storm index must be 0..49')
        if identity in identity_to_storm and identity_to_storm[identity]!=index:
            raise ValueError('same occurrence identity references different physical storms')
        identity_to_storm[identity]=index
        if index not in cache:
            cache[index]=hazard_loader(index)
            pairs=join_points(cache[index]['features'],sites)
            if any(p['status']!='matched' for p in pairs): raise ValueError('portfolio hazard coverage incomplete')
            paired_by_event[index]={r['building_id']:r for r in pairs}
            provenance.append(cache[index]['metadata'])
        sampled={}
        # Year participates in sample identity so repeated storms in different
        # supplied years do not accidentally reuse the same damage realisation.
        sampling_identity=json.dumps([entry['year_id'],identity],separators=(',',':'))
        for response_id,population in groups.items():
            augmented=[dict(s,gust_mps=paired_by_event[index][s['building_id']]['gust_mps']) for s in population]
            part=sample_policy_losses(augmented,curves[response_id],seed=config['seed'],
                sample_id=entry['sample_id'],occurrence_id=sampling_identity)
            for policy,value in part.items():sampled.setdefault(policy,[]).append(value)
        occurrences.append(dict(year_id=entry['year_id'],occurrence_id=identity,
                               sampled_policy_ground_up_eur={k:math.fsum(v) for k,v in sampled.items()}))
    result=aggregate(config['year_ids'],occurrences,config['policies'],config['treaty'])
    result.update(profile=config['profile'],seed=config['seed'],countries=sorted(countries),
                  building_count=len(sites),response_source_sha256=source_hashes,
                  hazard_provenance=provenance,annual_schedule_basis=config['annual_schedule_basis'],
                  severity_laws={k:v['kind'] for k,v in config['responses'].items()},
                  calibrated_european_model=False)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():p.error('output already exists')
    raw=args.config.read_bytes();config=json.loads(raw)
    result=execute(config,args.config.resolve().parent)
    result['configuration_sha256']=hashlib.sha256(raw).hexdigest()
    with args.output.open('x') as f:json.dump(result,f,allow_nan=False,indent=2)
    print(json.dumps(dict(profile=result['profile'],buildings=result['building_count'],countries=result['countries'],
                         years=len(result['years']),occurrences=len(result['occurrences']),calibrated=False)))

if __name__=='__main__':main()
