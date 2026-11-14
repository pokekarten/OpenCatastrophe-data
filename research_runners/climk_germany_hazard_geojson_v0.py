# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Export source-pinned CLIMK gust cells in a Germany bounding box for QGIS."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.inspect_climk_winds_era5_v0 import (fetch_provider_bytes, verify_source_bytes,
    inspect_netcdf_header, PINNED_SHA256)


def cell_polygon(latitudes, longitudes, row, col):
    """Native centre midpoints define cell edges; output longitude then latitude."""
    if not 0 < row < len(latitudes)-1 or not 0 < col < len(longitudes)-1:
        raise ValueError('interior native cell required')
    north=(latitudes[row-1]+latitudes[row])/2
    south=(latitudes[row]+latitudes[row+1])/2
    west=(longitudes[col-1]+longitudes[col])/2
    east=(longitudes[col]+longitudes[col+1])/2
    if not all(math.isfinite(v) for v in (north,south,west,east)) or not (north>south and east>west):
        raise ValueError('invalid native cell geometry')
    return [[[west,south],[east,south],[east,north],[west,north],[west,south]]]


def export(original: bytes, storm_index: int) -> dict:
    import numpy as np
    from netCDF4 import Dataset
    if type(storm_index) is not int or not 0<=storm_index<50:
        raise ValueError('source storm index must be 0..49')
    verify_source_bytes(original,require_sha256=True)
    inspect_netcdf_header(original)
    features=[]; missing=0
    with Dataset('climk-map',mode='r',memory=original) as ds:
        lat=[float(v) for v in ds.variables['latitude'][:]]
        lon=[float(v) for v in ds.variables['longitude'][:]]
        name=str(ds.variables['Storm_Names'][storm_index]).strip()
        date=str(ds.variables['Storm_Dates'][storm_index]).strip()
        field=ds.variables['absolute_maxwindgusts'][storm_index,:,:]
        for row,y in enumerate(lat):
            if not 47<=y<=56: continue
            for col,x in enumerate(lon):
                if not 5<=x<=16: continue
                value=field[row,col]
                if np.ma.is_masked(value):
                    gust=None; missing+=1
                else:
                    gust=float(value)
                    if not math.isfinite(gust) or not 0<=gust<=150:
                        raise ValueError('invalid original gust; refusing map')
                features.append({'type':'Feature','id':row*269+col+1,
                    'geometry':{'type':'Polygon','coordinates':cell_polygon(lat,lon,row,col)},
                    'properties':{'areaperil_id':row*269+col+1,'native_row':row,
                        'native_col':col,'gust_mps':gust,'weather_missing':gust is None}})
    if not features: raise ValueError('empty source map')
    return {'type':'FeatureCollection','features':features,'metadata':{
        'profile':'CLIMK_GERMANY_BBOX_NATIVE_GUST_MAP_V0','storm_index':storm_index,
        'storm_name':name,'provider_date_label':date,'source_sha256':PINNED_SHA256,
        'source':'CLIMK-WINDS v2 ERA5; Flynn et al. (2025); Zenodo 15305753; CC BY 4.0',
        'selection':'native cell centres within 5..16 E, 47..56 N; bounding box includes neighbouring countries',
        'geometry':'native grid centre midpoints; longitude latitude WGS84',
        'gust_measure':'source absolute_maxwindgusts; 72h footprint maximum 3-second gust; m/s',
        'cell_count':len(features),'missing_cells':missing,
        'missing_value_policy':'null, never zero','calibrated_loss_model':False,
        'annual_frequency_established':False}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,help='local original NetCDF; omitted: fetch publisher')
    p.add_argument('--storm-index',type=int,default=0)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists(): p.error('output already exists')
    result=export(args.source.read_bytes() if args.source else fetch_provider_bytes(),args.storm_index)
    with args.output.open('x') as f: json.dump(result,f,allow_nan=False)
    print(json.dumps(result['metadata'],sort_keys=True))

if __name__=='__main__': main()
