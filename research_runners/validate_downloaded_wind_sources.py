# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Validate downloaded source bytes and structural contents, without admission."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_runners.knmi_historical_wind_acquisition import inspect


def validate(directory):
    results=[]
    for receipt in ['receipt.json','xws-receipt.json']:
        for entry in json.loads((directory/receipt).read_text()):
            if entry['status']!='downloaded':raise ValueError('Failed source download')
            path=directory/entry['file'];raw=path.read_bytes()
            if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:
                raise ValueError('Original integrity failure: '+path.name)
            result={'file':path.name,'integrity_verified':True}
            if path.name.startswith('uurgeg_'):
                _,station,period=path.stem.split('_')
                result.update(kind='KNMI',summary=inspect(raw,int(station),period))
            elif path.suffix=='.nc':
                import numpy as np
                from netCDF4 import Dataset
                variables=[]
                with Dataset(path) as source:
                    for name,var in source.variables.items():
                        info={'name':name,'shape':list(var.shape),'units':getattr(var,'units',None)}
                        if np.dtype(var.dtype).kind in 'fiu':
                            values=np.ma.asarray(var[:]);valid=values.compressed()
                            info.update(unmasked_count=int(valid.size),masked_count=int(np.ma.count_masked(values)),
                                        nonfinite_count=int((~np.isfinite(valid)).sum()))
                            finite=valid[np.isfinite(valid)]
                            if finite.size:info.update(minimum=float(finite.min()),maximum=float(finite.max()))
                        variables.append(info)
                result.update(kind='NetCDF',variables=variables)
            elif path.name.endswith('.csv.gz'):
                with gzip.open(path,'rt',encoding='utf-8-sig',newline='') as stream:
                    rows=csv.reader(stream,delimiter=';');header=next(rows);count=0
                    for row in rows:
                        if len(row)!=len(header):raise ValueError('Malformed CSV row')
                        count+=1
                result.update(kind='MeteoFrance',rows=count,columns=header)
            else:result['kind']='integrity_only'
            results.append(result)
    return {'schema':'WIND_SOURCE_STRUCTURE_VALIDATION_V1','scientific_admission':False,'results':results}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=validate(a.directory)
    with a.output.open('x') as stream:json.dump(r,stream,indent=2,allow_nan=False)
    print(json.dumps({'files_checked':len(r['results'])}))
