# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline C3S EWS single-region Poisson-count research calibration challenger.

Requires exact pinned original C3S annual summary CSV bytes; delegates the
provider's scientific field/threshold/algorithm checks to the existing
research_runners.c3s_wind_annual_summary_v0 parser. Fits only a *toy stationary
count rate* and independently scores a nonoverlapping holdout. It does not
create an annual event catalogue, occurrence IDs, a CAT model, or insurer EP.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re

from research_runners.c3s_wind_annual_summary_v0 import (
    AnnualSummaryError, parse_annual_csv,
)

CONTRACT = 'C3S_EWS_SINGLE_REGION_HOLDOUT_POISSON_COUNT_V0'
HEX_SHA = re.compile(r'[a-f0-9]{64}\Z')


class CalibrationError(ValueError):
    pass


def _year(value, name):
    if type(value) is not int or not 1940 <= value <= 2026:
        raise CalibrationError(f'{name}: expected calendar year 1940..2026')
    return value


def _s(value, name):
    if type(value) is not str or not value or value.strip() != value or len(value) > 100:
        raise CalibrationError(f'{name}: invalid explicit selector')
    return value


def _series(rows, *, start, end, name):
    data={}
    for row in rows:
        year=row['year']
        if start <= year <= end:
            if year in data: raise CalibrationError(f'{name}: duplicate selected source year')
            data[year]=row['storm_number']
    expected=set(range(start,end+1))
    if set(data) != expected:
        raise CalibrationError(f'{name}: incomplete annual source sequence, including zero-storm years')
    return [data[y] for y in sorted(data)]


def fit_c3s_count_rate(*, original_csv_bytes: bytes, expected_csv_sha256: str,
                       region: str, algorithm: str, threshold_mps: str,
                       train_start: int, train_end: int,
                       holdout_start: int, holdout_end: int) -> dict:
    """Fit one source-observed annual count margin, never cross-algorithm merge.

    The year-to-year independence and Poisson variance are untested hypotheses,
    and this is not a frequency fit to *all* physical events. Source NUTS vintage
    is explicitly unresolved at this stage; automatic exposure joins prohibited.
    """
    if (type(original_csv_bytes) is not bytes or type(expected_csv_sha256) is not str or
            not HEX_SHA.fullmatch(expected_csv_sha256) or
            hashlib.sha256(original_csv_bytes).hexdigest() != expected_csv_sha256):
        raise CalibrationError('original C3S input bytes are not hash pinned')
    for k,v in [('train_start',train_start),('train_end',train_end),
                ('holdout_start',holdout_start),('holdout_end',holdout_end)]:
        _year(v,k)
    if not train_start < train_end < holdout_start <= holdout_end:
        raise CalibrationError('strict separate nonoverlapping train/holdout years required')
    if holdout_start != train_end+1:
        raise CalibrationError('contiguous train/holdout partitions mandatory in v0')
    if train_end-train_start+1 < 2 or holdout_end-holdout_start+1 < 2:
        raise CalibrationError('at least two years in each partition required')
    region=_s(region,'region')
    algorithm=_s(algorithm,'algorithm')
    threshold=_s(threshold_mps,'threshold_mps')
    try:
        source=parse_annual_csv(original_csv_bytes)
    except AnnualSummaryError as exc:
        raise CalibrationError('source parser rejected official CSV schema or physics') from exc
    if (source['evidence_class'] != 'C3S_ANNUAL_REGIONAL_HAZARD_ONLY_NO_EVENT_OR_INSURANCE_LOSS'
            or source['source_csv_sha256'] != expected_csv_sha256):
        raise CalibrationError('annual hazard evidence contract changed')
    selected=[r for r in source['rows'] if r['region']==region and
              r['algorithm']==algorithm and r['threshold_mps']==threshold]
    if not selected:
        raise CalibrationError('unobserved exact region/threshold/algorithm source selector')
    train=_series(selected,start=train_start,end=train_end,name='training')
    holdout=_series(selected,start=holdout_start,end=holdout_end,name='holdout')
    total=sum(train)
    lam=Fraction(total,len(train))
    rate=float(lam)
    mean=float(lam)
    variance=sum((x-mean)**2 for x in train)/(len(train)-1)
    dispersion=variance/rate if rate>0 else (0 if variance==0 else None)
    p_any=1-math.exp(-rate)
    # Log likelihood is a held-out *predictive* log score, not proof Poisson fit.
    if total==0 and any(x>0 for x in holdout):
        holdout_log_likelihood=None
        zero_train_positive_holdout=True
    elif total==0:
        holdout_log_likelihood=0.0
        zero_train_positive_holdout=False
    else:
        holdout_log_likelihood=sum(k*math.log(rate)-rate-math.lgamma(k+1) for k in holdout)
        zero_train_positive_holdout=False
    brier=sum(((int(x>0))-p_any)**2 for x in holdout)/len(holdout)
    selector={'region':region,'algorithm':algorithm,'threshold_mps':threshold,
              'train_years':[train_start,train_end], 'holdout_years':[holdout_start,holdout_end]}
    payload={'selector':selector, 'source_csv_sha256':expected_csv_sha256,
             'source_contract':'C3S_ANNUAL_REGIONAL_HAZARD_ONLY_NO_EVENT_OR_INSURANCE_LOSS'}
    dig=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'contract':CONTRACT, 'status':'UNADMITTED_RESEARCH_COUNT_RATE_ONLY',
            'method':'STATIONARY_POISSON_MLE_DIAGNOSTIC_NOT_CALIBRATED_CAT',
            'source_dataset':source['official_dataset'],
            'original_source_csv_sha256':expected_csv_sha256,
            'selector_and_split_sha256':dig,
            'selector':selector,
            'nuts_vintage':source['nuts_vintage'],
            'automatic_nuts_join_permitted':False,
            'train_annual_counts':train, 'holdout_annual_counts':holdout,
            'train_count_total':total,
            'train_year_count':len(train), 'holdout_year_count':len(holdout),
            'poisson_lambda_events_per_year':rate,
            'poisson_lambda_exact':{'numerator':lam.numerator,'denominator':lam.denominator},
            'train_sample_variance_counts':variance,
            'train_variance_to_mean_ratio':dispersion,
            'poisson_probability_at_least_one_event':p_any,
            'holdout_mean_count':sum(holdout)/len(holdout),
            'holdout_occurrence_brier_score':brier,
            'holdout_log_likelihood':holdout_log_likelihood,
            'zero_train_positive_holdout_failure':zero_train_positive_holdout,
            'explicit_limits':['Only one exact original regional annual count selector',
               'No NUTS version verified or automatic asset geography join',
               'No physical event IDs, catalogue weights, event footprints or insured loss',
               'No full intra-peril stochastic annual occurrence or dependence calibration',
               'Neither model validation nor Zurich group wind CAT pricing']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original_csv_file',type=Path)
    p.add_argument('--expected-source-sha256',required=True)
    p.add_argument('--region',required=True)
    p.add_argument('--algorithm',required=True)
    p.add_argument('--threshold-mps',required=True)
    p.add_argument('--train-start',type=int,required=True)
    p.add_argument('--train-end',type=int,required=True)
    p.add_argument('--holdout-start',type=int,required=True)
    p.add_argument('--holdout-end',type=int,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.is_symlink() or args.out.resolve()==args.original_csv_file.resolve() or args.out.exists():
        p.error('refuse overwrite, original-source aliases or linked output paths')
    result=fit_c3s_count_rate(original_csv_bytes=args.original_csv_file.read_bytes(),
        expected_csv_sha256=args.expected_source_sha256,
        region=args.region,algorithm=args.algorithm,threshold_mps=args.threshold_mps,
        train_start=args.train_start,train_end=args.train_end,
        holdout_start=args.holdout_start,holdout_end=args.holdout_end)
    # One exclusive creation; no original CSV modification or production writes.
    with args.out.open('x',encoding='utf-8') as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False)
        f.write('\n')
    print(json.dumps({'status':result['status'],'source_sha256':result['original_source_csv_sha256'],
                      'lambda_per_year':result['poisson_lambda_events_per_year'],
                      'holdout_brier':result['holdout_occurrence_brier_score']},sort_keys=True))


if __name__=='__main__':
    main()
