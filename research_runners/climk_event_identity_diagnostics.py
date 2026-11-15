# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Expose name/date disagreements without merging physical events."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research_runners.climk_multisource_event_inventory import inventory


def diagnose(views):
    names=defaultdict(set);dates=defaultdict(set)
    for v in views:
        name=v['provider_name'].casefold();date=v['provider_date_label']
        names[name].add(date);dates[date].add(name)
    return {'same_name_multiple_dates':[
                {'name':k,'date_labels':sorted(v)} for k,v in sorted(names.items()) if len(v)>1],
            'same_date_multiple_names':[
                {'date_label':k,'names':sorted(v)} for k,v in sorted(dates.items()) if len(v)>1],
            'automatic_physical_event_merges':0,'annual_rates_established':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    inv=inventory(a.source);views=[v for e in inv['events'] for v in e['source_views']]
    result={'schema':'CLIMK_IDENTITY_DIAGNOSTICS_V1','source_view_count':len(views),
            'literal_candidate_groups':len(inv['events']),**diagnose(views)}
    with a.output.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
