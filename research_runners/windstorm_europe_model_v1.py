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
import tomllib
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


def execute(config,base,hazard_loader=None,validate_only=False):
    if 'year_block_resampling' in config:
        from research_runners.windstorm_europe_year_blocks_v1 import resample_config
        import copy
        source=copy.deepcopy(config);settings=source.pop('year_block_resampling')
        sampled,receipt=resample_config(source,settings['simulation_years'],settings['seed'])
        result=execute(sampled,base,hazard_loader,validate_only)
        result['year_block_resampling']=receipt
        return result
    if config.get('profile')!='windstorm-europe-research-v1': raise ValueError('unsupported model profile')
    if config.get('annual_schedule_basis')!='explicit_user_scenario_not_calibrated':
        raise ValueError('this version supports explicit scenario years only')
    if type(config.get('seed')) is not int: raise ValueError('integer seed required')
    bounds=validate_bounds(config['bounds'])
    sites=config['buildings']
    if not isinstance(sites,list) or not 1<=len(sites)<=10000: raise ValueError('bounded nonempty portfolio required')
    # Validate year measure and financial terms even if no events are supplied.
    aggregate(config['year_ids'],[],config['policies'],config['treaty'])
    seen_occurrences=set()
    if not isinstance(config['occurrences'],list):raise ValueError('occurrence list required')
    for entry in config['occurrences']:
        year=entry['year_id'];identity=entry['occurrence_id']
        if type(entry['storm_index']) is not int or not 0<=entry['storm_index']<50:raise ValueError('CLIMK index must be 0..49')
        if type(year) is not int or year not in config['year_ids']:raise ValueError('unknown occurrence year')
        if not isinstance(identity,str) or not identity or (year,identity) in seen_occurrences:
            raise ValueError('missing or duplicate occurrence identity')
        seen_occurrences.add((year,identity))
        if type(entry['sample_id']) is not int or entry['sample_id']<0:raise ValueError('nonnegative integer sample ID required')
    groups={}; countries=set();building_ids=set()
    for s in sites:
        identity=s.get('building_id')
        if not isinstance(identity,str) or not identity.strip() or identity!=identity.strip() or identity in building_ids:
            raise ValueError('unique nonempty canonical building IDs required')
        building_ids.add(identity)
        x=float(s['longitude']);y=float(s['latitude'])
        if not math.isfinite(x) or not math.isfinite(y) or not -180<=x<=180 or not -90<=y<=90:
            raise ValueError('invalid building coordinates')
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
    if validate_only:
        from scripts.inspect_climk_winds_era5_v0 import verify_source_bytes
        receipt=verify_source_bytes((base/config['hazard_source']).read_bytes(),require_sha256=True)
        return dict(profile=config['profile'],status='inputs_verified_no_hazard_or_loss_run',
                    building_count=len(sites),countries=sorted(countries),source=receipt,
                    response_source_sha256=source_hashes,calibrated_european_model=False)
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
    p.add_argument('--validate-only',action='store_true')
    p.add_argument('--data-dir',type=Path,help='base directory for relative input data paths')
    args=p.parse_args()
    if args.output.exists():p.error('output already exists')
    raw=args.config.read_bytes()
    config=tomllib.loads(raw.decode()) if args.config.suffix=='.toml' else json.loads(raw)
    result=execute(config,args.data_dir.resolve() if args.data_dir else args.config.resolve().parent,validate_only=args.validate_only)
    result['configuration_sha256']=hashlib.sha256(raw).hexdigest()
    with args.output.open('x') as f:json.dump(result,f,allow_nan=False,indent=2)
    print(json.dumps(dict(profile=result['profile'],buildings=result['building_count'],countries=result['countries'],
                         years=len(result.get('years',[])),occurrences=len(result.get('occurrences',[])),calibrated=False)))

if __name__=='__main__':main()
