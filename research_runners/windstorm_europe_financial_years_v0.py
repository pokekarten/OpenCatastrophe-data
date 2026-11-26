# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Financial occurrence/year aggregation for explicitly supplied sampled losses.

Input losses must be realised samples, not mean damage ratios. Years are an
explicit equally weighted simulation population, including zero-event years.
"""
import math
from bisect import bisect_right


def amount(value,label):
    if type(value) not in (float,int) or not math.isfinite(value) or value<0:
        raise ValueError(label+' must be finite and nonnegative')
    return float(value)


def aggregate(year_ids, occurrences, policies, treaty):
    if not year_ids or any(type(y) is not int for y in year_ids) or len(set(year_ids))!=len(year_ids):
        raise ValueError('explicit unique integer simulation years required')
    contracts={}
    for key,p in policies.items():
        contracts[key]=(amount(p['deductible_eur'],'deductible'),amount(p['limit_eur'],'limit'))
    attach=amount(treaty['attachment_eur'],'attachment')
    limit=amount(treaty['limit_eur'],'treaty limit')
    years={y:{'year_id':y,'gross_annual_eur':0.,'net_annual_eur':0.,'gross_max_event_eur':0.,'net_max_event_eur':0.} for y in year_ids}
    seen=set();events=[]
    for event in occurrences:
        year=event['year_id']; identity=event['occurrence_id']
        if type(year) is not int or year not in years or not isinstance(identity,str) or not identity:
            raise ValueError('unknown year or invalid occurrence ID')
        if (year,identity) in seen: raise ValueError('duplicate financial occurrence; combine country losses first')
        seen.add((year,identity)); gross=[]
        for policy,loss in event['sampled_policy_ground_up_eur'].items():
            if policy not in contracts: raise ValueError('unknown policy')
            loss=amount(loss,'sampled ground-up loss');ded,cap=contracts[policy]
            gross.append(min(max(loss-ded,0.),cap))
        g=math.fsum(gross);ceded=min(max(g-attach,0.),limit);net=g-ceded
        row=years[year];row['gross_annual_eur']+=g;row['net_annual_eur']+=net
        row['gross_max_event_eur']=max(row['gross_max_event_eur'],g)
        row['net_max_event_eur']=max(row['net_max_event_eur'],net)
        events.append(dict(year_id=year,occurrence_id=identity,gross_eur=g,ceded_eur=ceded,net_eur=net))
    output=list(years.values())
    if any(not math.isfinite(v) for r in output for k,v in r.items() if k!='year_id'):
        raise ValueError('nonfinite annual aggregate')
    metrics={}
    for scope in ('gross','net'):
        annual=[r[scope+'_annual_eur'] for r in output]
        peaks=[r[scope+'_max_event_eur'] for r in output]
        sorted_annual=sorted(annual);sorted_peaks=sorted(peaks)
        metrics[scope]={'sample_mean_annual_loss_eur':math.fsum(annual)/len(annual),
            'empirical_ep':[{'threshold_eur':t,'AEP_strict':(len(annual)-bisect_right(sorted_annual,t))/len(annual),
                             'OEP_strict':(len(peaks)-bisect_right(sorted_peaks,t))/len(peaks)}
                            for t in sorted(set([0.]+annual+peaks))]}
    return {'years':output,'occurrences':events,'metrics':metrics,
            'year_measure':'explicit equally weighted supplied simulation years, including zero-event years',
            'treaty_scope':'single occurrence excess-of-loss; unlimited annual reinstatements; no annual aggregate terms',
            'input_loss_scope':'realised per-policy samples, not expected damage',
            'frequency_or_vulnerability_calibrated_by_this_module':False}
