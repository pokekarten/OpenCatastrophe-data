# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Acquire original ARCO chunks for missing Ciara UTC labels; external storage only."""
import argparse
from datetime import datetime,timedelta
import hashlib
import json
from pathlib import Path
import urllib.request

BASE='https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3/'
VARIABLE='10m_wind_gust_since_previous_post_processing'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();out=a.output_dir.resolve()
    if any((parent/'.git').exists() for parent in [out,*out.parents]):
        raise ValueError('External original storage required')
    out.mkdir(parents=True,exist_ok=False)
    records=[]
    paths=['time/.zattrs',VARIABLE+'/.zarray']
    start=datetime(2020,2,7);epoch=datetime(1900,1,1)
    for h in range(24):
        index=int(((start+timedelta(hours=h))-epoch).total_seconds()/3600)
        paths.append(f'{VARIABLE}/{index}.0.0')
    for index,path in enumerate(paths):
        with urllib.request.urlopen(BASE+path,timeout=45) as response:
            raw=response.read(20_000_001)
        if len(raw)>20_000_000:raise ValueError('Source response exceeds bound')
        name=f'{index:02d}.bin';(out/name).write_bytes(raw)
        records.append({'url':BASE+path,'file':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        (out/'receipt.json').write_text(json.dumps({'schema':'CIARA_MISSING_DAY_RAW_V1',
            'complete':len(records)==26,'source_hour_labels':'2020-02-07 00..23 UTC',
            'decoded_and_validated':False,'scientific_admission':False,'records':records},indent=2))
    print(json.dumps({'downloaded_objects':len(records),'bytes':sum(r['bytes'] for r in records)}))

if __name__=='__main__':main()
