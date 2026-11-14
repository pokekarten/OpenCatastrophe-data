# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Build complete KNMI hour-ending windows for original CLIMK event labels."""
import csv,zipfile,json,hashlib
from pathlib import Path
from datetime import datetime,timedelta
from netCDF4 import Dataset
import argparse
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive-dir',type=Path,required=True)
p.add_argument('--hazard',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():p.error('refuse overwrite')
b=a.archive_dir;h=a.hazard
source_hashes={}

with Dataset(h) as d:events=list(zip(map(str,d.variables['Storm_Names'][:]),map(str,d.variables['Storm_Dates'][:])))
result=[]
for station in [235,260,280,310,330]:
 obs={}
 for period in ['2001-2010','2011-2020']:
  p=b/f'uurgeg_{station}_{period}.zip'
  source_hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
  with zipfile.ZipFile(p) as z:lines=z.read(z.namelist()[0]).decode('utf-8-sig').splitlines()
  fields=[x.strip() for x in next(x for x in lines if x.startswith('# STN,'))[2:].split(',')]
  for line in lines:
   vals=[x.strip() for x in line.split(',')]
   if len(vals)!=len(fields) or not vals[0].isdigit():continue
   r=dict(zip(fields,vals));dt=datetime.strptime(r['YYYYMMDD'],'%Y%m%d')+timedelta(hours=int(r['HH']))
   if dt in obs:raise ValueError('duplicate timestamp')
   obs[dt]=float(r['FX'])/10 if r['FX'] else None
 rows=[]
 for index,(name,date) in enumerate(events):
  mid=datetime.strptime(date,'%Y%m%d');labels=[mid-timedelta(days=1)+timedelta(hours=i) for i in range(1,73)]
  vals=[obs.get(t) for t in labels];valid=[v for v in vals if v is not None]
  rows.append(dict(storm_index=index,provider_name=name,provider_date=date,valid_hours=len(valid),complete=len(valid)==72,peak_mps=max(valid) if len(valid)==72 else None))
 result.append(dict(station=station,complete_events=sum(r['complete'] for r in rows),events=rows))
with a.output.open('x') as stream:json.dump(dict(schema='KNMI_CLIMK_COMPLETE_WINDOWS_V1',annual_catalogue_complete=False,hazard_sha256=hashlib.sha256(h.read_bytes()).hexdigest(),archive_sha256=source_hashes,stations=result),stream,indent=2,allow_nan=False);print([(r['station'],r['complete_events']) for r in result]);print('common complete',sum(all(s['events'][i]['complete'] for s in result) for i in range(50)))
