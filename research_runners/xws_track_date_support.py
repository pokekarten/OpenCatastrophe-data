# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Check source date labels against track timestamps without asserting identity."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import argparse


def inspect(path):
    times=[]
    with path.open(newline='') as f:
        for row in csv.reader(f,skipinitialspace=True):
            if len(row)<2:raise ValueError('Missing track timestamp')
            times.append(datetime.strptime(row[1].strip(),'%Y-%m-%d %H:%M:%S'))
    if not times or len(set(times))!=len(times):raise ValueError('Empty or duplicate track times')
    if times!=sorted(times):raise ValueError('Nonmonotonic track times')
    return {'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'track_rows':len(times),'first_label':times[0].isoformat(),
            'last_label':times[-1].isoformat(),
            'calendar_dates':sorted({t.strftime('%Y%m%d') for t in times}),
            'timezone_verified':False,'physical_identity_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('track',type=Path);a=p.parse_args()
    print(json.dumps(inspect(a.track),indent=2))
