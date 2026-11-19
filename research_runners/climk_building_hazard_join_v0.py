# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Join explicit building points to native CLIMK hazard polygons for a scenario."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_runners.climk_germany_hazard_geojson_v0 import export
from scripts.inspect_climk_winds_era5_v0 import fetch_provider_bytes


def join_points(features, points):
    """Use west/south inclusive, east/north exclusive ownership at cell edges."""
    cells=[]
    for feature in features:
        ring=feature['geometry']['coordinates'][0]
        cells.append((min(p[0] for p in ring),min(p[1] for p in ring),
                      max(p[0] for p in ring),max(p[1] for p in ring),feature['properties']))
    results=[]; seen=set()
    for point in points:
        identity=point['building_id'].strip()
        if not identity or identity in seen: raise ValueError('missing or duplicate building_id')
        seen.add(identity)
        x=float(point['longitude']); y=float(point['latitude'])
        if not math.isfinite(x) or not math.isfinite(y) or not -180<=x<=180 or not -90<=y<=90:
            raise ValueError('building coordinate invalid')
        matches=[p for west,south,east,north,p in cells if west<=x<east and south<=y<north]
        if len(matches)>1: raise ValueError('overlapping hazard cells')
        p=matches[0] if matches else None
        status='outside_exported_grid' if p is None else ('missing_weather' if p['weather_missing'] else 'matched')
        results.append({'building_id':identity,'status':status,
            'areaperil_id':p['areaperil_id'] if p else None,
            'gust_mps':p['gust_mps'] if p else None})
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--buildings',type=Path,required=True,help='CSV: building_id,longitude,latitude')
    p.add_argument('--source',type=Path)
    p.add_argument('--storm-index',type=int,default=0)
    p.add_argument('--bounds',type=float,nargs=4,default=(5,47,16,56),metavar=('WEST','SOUTH','EAST','NORTH'))
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists(): p.error('output already exists')
    with args.buildings.open(newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['building_id','longitude','latitude']:
            p.error('expected exactly building_id,longitude,latitude')
        points=list(reader)
    if not 1<=len(points)<=10000: p.error('expected 1..10000 building points')
    hazard=export(args.source.read_bytes() if args.source else fetch_provider_bytes(),args.storm_index,args.bounds)
    rows=join_points(hazard['features'],points)
    result={'hazard_metadata':hazard['metadata'],'building_count':len(rows),
            'boundary_rule':'west/south inclusive, east/north exclusive',
            'status_counts':{s:sum(r['status']==s for r in rows) for s in ('matched','missing_weather','outside_exported_grid')},
            'insured_loss_calculated':False,'buildings':rows}
    with args.output.open('x') as f: json.dump(result,f,allow_nan=False)
    print(json.dumps({'building_count':len(rows),'status_counts':result['status_counts']}))

if __name__=='__main__': main()
