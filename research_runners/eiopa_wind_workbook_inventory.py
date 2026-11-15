# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read original workbook semantics without exporting source cells."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def inventory(path):
    import openpyxl
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheets=[]
    for sheet in workbook:
        # Provider workbooks may contain formatting up to Excel's row limit.
        # Ignore advertised dimensions and stream actual XML rows.
        sheet.reset_dimensions()
        rows=sheet.iter_rows(values_only=True)
        header=next(rows)
        names=[str(v).strip() if v is not None else None for v in header]
        counts=Counter(); nonempty=0; last=1
        for i,row in enumerate(rows,2):
            if not any(v is not None for v in row):
                continue
            nonempty+=1;last=i
            item=dict(zip(names,row))
            for key in ['Peril','As of date','Country','Category','LoB','Event']:
                if item.get(key) is not None:
                    counts[(key,str(item[key]))]+=1
        sheets.append({'sheet':sheet.title,'headers':names,'nonempty_data_rows':nonempty,
                       'last_nonempty_row':last,'category_counts':[
                           {'field':k,'label':v,'rows':n} for (k,v),n in sorted(counts.items())]})
    workbook.close()
    return {'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes':path.stat().st_size,'sheets':sheets}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    result={'schema':'EIOPA_WIND_WORKBOOK_INVENTORY_V1','calibration_ready':False,
            'exposure_loss_denominators_matched':False,'files':[inventory(s) for s in a.source]}
    with a.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(result))
