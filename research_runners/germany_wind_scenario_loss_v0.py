# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conditional wind loss from source-pinned hazard, explicit values and PAA/MDD."""
import argparse
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_runners.climk_germany_hazard_geojson_v0 import export
from research_runners.climk_building_hazard_join_v0 import join_points


def read_curve(path):
    with path.open(newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['intensity_m_s','paa','mdd']: raise ValueError('expected intensity_m_s,paa,mdd')
        rows=[tuple(float(r[k]) for k in reader.fieldnames) for r in reader]
    if len(rows)<2 or any(not all(math.isfinite(v) for v in r) for r in rows):
        raise ValueError('finite curve points required')
    if any(x<0 or not 0<=p<=1 or not 0<=m<=1 for x,p,m in rows): raise ValueError('curve bounds')
    if any(b[0]<=a[0] or b[1]<a[1] or b[2]<a[2] for a,b in zip(rows,rows[1:])):
        raise ValueError('increasing intensity and monotone PAA/MDD required')
    return rows


def damage_ratio(gust,curve):
    if not math.isfinite(gust) or not curve[0][0]<=gust<=curve[-1][0]:
        raise ValueError('gust outside curve; no extrapolation')
    i=min(max(bisect.bisect_right([r[0] for r in curve],gust)-1,0),len(curve)-2)
    a,b=curve[i:i+2]; w=(gust-a[0])/(b[0]-a[0])
    return (a[1]+w*(b[1]-a[1]))*(a[2]+w*(b[2]-a[2]))


def calculate(hazard,portfolio,curve):
    if not portfolio: raise ValueError('empty portfolio')
    for row in portfolio:
        value=float(row['building_value_eur'])
        if not math.isfinite(value) or value<=0: raise ValueError('positive explicit building value required')
    paired=join_points(hazard['features'],portfolio)
    if any(r['status']!='matched' for r in paired):
        raise ValueError('incomplete hazard coverage; loss aggregation blocked')
    cells={}; total_value=0; losses=[]
    for site,pair in zip(portfolio,paired):
        value=float(site['building_value_eur']); total_value+=value
        loss=value*damage_ratio(pair['gust_mps'],curve); losses.append(loss)
        cell=cells.setdefault(pair['areaperil_id'],{'building_count':0,'building_value_eur':0,'expected_ground_up_loss_eur':0})
        cell['building_count']+=1; cell['building_value_eur']+=value; cell['expected_ground_up_loss_eur']+=loss
    total=math.fsum(losses)
    if not math.isfinite(total) or not 0<=total<=total_value: raise ValueError('loss conservation failed')
    return {'hazard_metadata':hazard['metadata'],'building_count':len(portfolio),
            'building_value_eur':total_value,'expected_ground_up_loss_eur':total,
            'curve_semantics':'interpolate PAA and MDD separately, then multiply',
            'financial_scope':'conditional expected physical ground-up building damage; no policy terms',
            'germany_calibrated':False,'annual_frequency_established':False,
            'cell_aggregates':[dict(areaperil_id=k,**v) for k,v in sorted(cells.items())]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--portfolio',type=Path,required=True)
    p.add_argument('--curve',type=Path,required=True)
    p.add_argument('--curve-label',required=True)
    p.add_argument('--storm-index',type=int,default=0)
    p.add_argument('--all-storms',action='store_true',help='evaluate all 50 selected source scenarios; no annual weights')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists(): p.error('output already exists')
    with args.portfolio.open(newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['building_id','longitude','latitude','building_value_eur']:
            p.error('expected building_id,longitude,latitude,building_value_eur')
        portfolio=list(reader)
    if len(portfolio)>10000: p.error('maximum 10000 buildings')
    source=args.source.read_bytes(); curve=read_curve(args.curve)
    if args.all_storms:
        scenarios=[]
        for index in range(50):
            hazard=export(source,index)
            try:
                outcome=calculate(hazard,portfolio,curve)
                scenarios.append(dict(storm_index=index,status='completed',**outcome))
            except ValueError as exc:
                scenarios.append(dict(storm_index=index,status='blocked',reason=str(exc)))
        result={'scenarios':scenarios,'scenario_count':50,
                'completed':sum(r['status']=='completed' for r in scenarios),
                'annual_frequency_established':False,'germany_calibrated':False}
    else:
        result=calculate(export(source,args.storm_index),portfolio,curve)
    result.update(curve_label=args.curve_label,
                  curve_sha256=hashlib.sha256(args.curve.read_bytes()).hexdigest(),
                  portfolio_sha256=hashlib.sha256(args.portfolio.read_bytes()).hexdigest())
    with args.output.open('x') as f: json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k not in ('cell_aggregates','hazard_metadata','scenarios')}))

if __name__=='__main__': main()
