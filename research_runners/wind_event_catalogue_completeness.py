# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Audit explicit monthly deliveries; never infer zero storms from missing files."""
import argparse
import json
from datetime import datetime
from pathlib import Path


def audit(data):
    start=datetime.strptime(data['first_month'],'%Y-%m')
    end=datetime.strptime(data['last_month'],'%Y-%m')
    if end<start:raise ValueError('Reversed coverage')
    expected=[];current=start
    while current<=end:
        expected.append(current.strftime('%Y-%m'))
        current=datetime(current.year+(current.month==12),current.month%12+1,1)
    tracker=data['tracking_algorithm']
    if not isinstance(tracker,str) or not tracker.strip():raise ValueError('One tracker required')
    months={};ids=set();missing_footprints=[];zero=[]
    for delivery in data['months']:
        month=delivery['month']
        if month not in expected or month in months:raise ValueError('Duplicate or unexpected delivery month')
        if delivery['tracking_algorithm']!=tracker:raise ValueError('Mixed tracking algorithms')
        if delivery['delivery_complete'] is not True:raise ValueError('Incomplete source delivery')
        digest=delivery['source_sha256']
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Source SHA256 required')
        events=delivery['events']
        if not isinstance(events,list):raise ValueError('Event list required')
        if not events:zero.append(month)
        for event in events:
            identity=event['event_id']
            if not isinstance(identity,str) or not identity.strip() or identity in ids:
                raise ValueError('Missing or duplicate physical event identity')
            ids.add(identity)
            if event['footprint_verified'] is not True:missing_footprints.append(identity)
        months[month]=delivery
    missing=sorted(set(expected)-months.keys())
    return {'schema':'WIND_EVENT_CATALOGUE_COMPLETENESS_V1','missing_months':missing,
            'explicit_zero_event_months':zero,'distinct_events':len(ids),
            'events_without_verified_footprint':missing_footprints,
            'delivery_claims_complete':not missing,
            'catalogue_claims_complete':not missing and not missing_footprints,
            'source_bytes_independently_verified':False,
            'frequency_weights_verified':False,'annual_risk_authorized':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);a=p.parse_args()
    print(json.dumps(audit(json.loads(a.manifest.read_text())),indent=2))
