# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Explicit two-point damage assumption, with keyed reproducible random draws.

Damage is zero with probability 1-PAA, otherwise MDD times replacement value.
Caller-supplied dependence groups share one uniform draw per occurrence/sample.
"""
import bisect
import hashlib
import json
import math


def response(gust,curve):
    if not curve or len(curve)<2 or not math.isfinite(gust): raise ValueError('invalid curve or gust')
    for i,(x,p,m) in enumerate(curve):
        if not all(math.isfinite(v) for v in (x,p,m)) or x<0 or not 0<=p<=1 or not 0<=m<=1:
            raise ValueError('invalid PAA/MDD curve')
        if i and (x<=curve[i-1][0] or p<curve[i-1][1] or m<curve[i-1][2]):
            raise ValueError('nonmonotone curve')
    if not curve[0][0]<=gust<=curve[-1][0]: raise ValueError('no curve extrapolation')
    i=min(bisect.bisect_right([r[0] for r in curve],gust)-1,len(curve)-2)
    a,b=curve[i:i+2];w=(gust-a[0])/(b[0]-a[0])
    return a[1]+w*(b[1]-a[1]),a[2]+w*(b[2]-a[2])


def uniform(seed,sample_id,occurrence_id,group):
    if type(seed) is not int or type(sample_id) is not int or sample_id<0:
        raise ValueError('integer seed and nonnegative sample ID required')
    if any(not isinstance(v,str) or not v for v in (occurrence_id,group)):
        raise ValueError('explicit occurrence and dependence group required')
    key=json.dumps(['wind-damage-v0',seed,sample_id,occurrence_id,group],ensure_ascii=True,separators=(',',':')).encode()
    # Midpoint of a 52-bit bin: strictly inside (0,1), deterministic across order.
    return ((int.from_bytes(hashlib.sha256(key).digest()[:8],'big')>>12)+0.5)/2**52


def sample_policy_losses(sites,curve,*,seed,sample_id,occurrence_id):
    losses={}; identities=set()
    for site in sites:
        identity=site['building_id'];policy=site['policy_id']
        if not isinstance(identity,str) or not identity or identity in identities:
            raise ValueError('unique building IDs required')
        if not isinstance(policy,str) or not policy: raise ValueError('explicit policy ID required')
        identities.add(identity)
        value=site['building_value_eur']
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
            raise ValueError('positive finite building value required')
        p,m=response(site['gust_mps'],curve)
        u=uniform(seed,sample_id,occurrence_id,site['dependence_group'])
        losses.setdefault(policy,[]).append(value*m if u<p else 0.)
    if not sites: raise ValueError('nonempty building population required')
    return {policy:math.fsum(values) for policy,values in sorted(losses.items())}
