# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Reproduce the Ciara original-source review without publishing source amounts."""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_runners.eiopa_wind_workbook_inventory import inventory
from research_runners.eiopa_lob_reconciliation import reconcile
from research_runners.eiopa_country_coverage import compare


def read(path):
    import openpyxl
    w=openpyxl.load_workbook(path,read_only=True,data_only=True)
    s=w.active;s.reset_dimensions();it=s.values
    header=[str(v).strip() if v is not None else None for v in next(it)]
    rows=[dict(zip(header,row)) for row in it if any(v is not None for v in row)]
    w.close()
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exposure',type=Path,required=True)
    p.add_argument('--losses',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    exposure=read(a.exposure);losses=read(a.losses)
    storms=[r for r in losses if r.get('Category')=='Storm']
    if not storms or any(r.get('Event')!='Windstorm Ciara Feb. 2020' for r in storms):
        raise ValueError('Expected exclusively Ciara storm rows; review changed source before use')
    result={'schema':'EIOPA_CIARA_ORIGINAL_REVIEW_V1',
            'sources':[inventory(a.exposure),inventory(a.losses)],
            'lob_reconciliation':reconcile(storms),
            'country_overlap':compare(exposure,storms),
            'calibration_ready':False,'loss_ratio_computable':False}
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps({'storm_rows':len(storms),'groups':len(result['lob_reconciliation']),
                      'calibration_ready':False}))

if __name__=='__main__':main()
