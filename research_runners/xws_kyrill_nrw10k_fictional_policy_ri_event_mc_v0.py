# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""ONE historical XWS Kyrill event: fictional stochastic GUL -> IL -> QS -> XL -> net.

This is a deliberately simple, uncalibrated Bernoulli-PAA / fixed MDD severity
toy to demonstrate why applying deductibles to expected losses is invalid.
Each XWS windfield is an alternative view of the SAME single Kyrill event.
No independent annual occurrence law, no insurer underwriting, no credible EP.
Input: only the two immutable, SHA-pinned *research* ZIP artifacts. No original
third-party NetCDFs or original physical source identifiers are redistributed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

from xws_kyrill_nrw10k_schwierz_conditional_loss_v0 import (
    EXPECTED_COUNTIES, EXPECTED_N, EXPECTED_TIV, HU22_SHA, OED_ZIP_SHA,
    XWS_CSV_SHA, XWS_ZIP_SHA, SensitivityBlocked, impact_parts,
    original_pair, site_loss_cents,
)

SCHEMA = "XWS_KYRILL_2007_ONE_EVENT_FICTIONAL_GUL_IL_QS_XL_MC_V0"
HISTORICAL_WIND_FIELD = "KyrillRecalMeanGustMS"
SEED = 20261105
TRIALS = 2048
SHARED_UNIFORM_WEIGHTS = {
    "site_independent_hypothetical": 0.0,
    "mixture_25pct_shared_uniform_hypothetical": 0.25,
}
# Purely invented illustration, in whole EUR; not insurer or treaty facts.
POLICY_DEDUCTIBLE_EUR = 250
POLICY_LIMIT_EUR = 50000
QS_CEDED_PERCENT = 20
OCC_XL_ATTACHMENT_EUR = 15000
OCC_XL_LIMIT_EUR = 250000
REFERENCE_CONDITIONAL_GUL_CENTS = 5368691
MAX_SITES = 10000


class EventModelBlocked(ValueError):
    pass


def _as_cents(eur: int) -> int:
    if type(eur) is not int or eur < 0:
        raise EventModelBlocked("monetary terms must be nonnegative integer EUR")
    return eur * 100


def financial_tower(gul_cents: list[int]) -> dict[str,int]:
    """Explicit ordering: each occurrence site GUL -> policy -> QS -> cat XL.

    XL attaches to insurer QS-retained occurrence IL; not to risk-level expected
    loss and not to annual losses. Signed-amount and recovery conservation gate.
    """
    if not isinstance(gul_cents, list) or not gul_cents or len(gul_cents)>MAX_SITES:
        raise EventModelBlocked("bounded one-event gross risk list required")
    deductible=_as_cents(POLICY_DEDUCTIBLE_EUR)
    policy_limit=_as_cents(POLICY_LIMIT_EUR)
    attachment=_as_cents(OCC_XL_ATTACHMENT_EUR)
    xl_limit=_as_cents(OCC_XL_LIMIT_EUR)
    gross=insured=qs=0
    for damage in gul_cents:
        if type(damage) is not int or not 0<=damage<=10**14:
            raise EventModelBlocked("each sampled site damage must be integer cents")
        gross+=damage
        il=min(max(damage-deductible,0),policy_limit)
        ceded=(il*QS_CEDED_PERCENT+50)//100 # exact half-up to nearest cent
        insured+=il
        qs+=ceded
    retained_pre_xl=insured-qs
    xl=min(max(retained_pre_xl-attachment,0),xl_limit)
    net=retained_pre_xl-xl
    if (not 0<=net<=retained_pre_xl<=insured<=gross
        or qs+xl+net!=insured):
        raise EventModelBlocked("one-event financial treaty conservation failed")
    return dict(
        groundup_cents=gross,insured_before_reinsurance_cents=insured,
        quota_share_ceded_cents=qs,
        quota_share_retained_before_xl_cents=retained_pre_xl,
        occurrence_xl_recovery_cents=xl,
        insurer_net_after_qs_xl_cents=net,
    )


def _risk_catalogue(winds:list[dict],values:dict[str,tuple[int,str]]) -> tuple[list[tuple[str,float,int]],dict]:
    if len(winds)!=EXPECTED_N or len(values)!=EXPECTED_N:
        raise EventModelBlocked("complete original 10k site hazard and OED book required")
    seen=set()
    risks=[]
    original_reference_cents=0
    analytic_gul=Decimal(0)
    analytic_il=Decimal(0)
    analytic_qs=Decimal(0)
    for row in winds:
        key=row.get("FictionalLocNumber")
        if not key or key in seen or key not in values:
            raise EventModelBlocked("one-to-one original site IDs required")
        seen.add(key)
        tiv,county=values[key]
        if (row.get("KreisAGS2022")!=county
            or row.get("IsActualRVInsuredSite")!="false"
            or row.get("WindVulnerabilityCalibrated")!="false"):
            raise EventModelBlocked("source risk nonadmission or Kreis changed")
        try:
            gust=Decimal(row[HISTORICAL_WIND_FIELD])
        except (KeyError,ValueError,TypeError) as exc:
            raise EventModelBlocked("original historic mean source wind missing") from exc
        try:
            p,mdd=impact_parts(gust)
        except SensitivityBlocked as exc:
            raise EventModelBlocked(str(exc)) from exc
        if not (Decimal(0)<=p<=Decimal(1) and Decimal(0)<=mdd<=Decimal(1)):
            raise EventModelBlocked("incompatible PAA/MDD source curve")
        # When affected (Bernoulli PAA), damage has exactly a single
        # deterministic hypothetical fraction MDD; no severity variance.
        severity=int((Decimal(tiv)*mdd*100).to_integral_value(rounding=ROUND_HALF_UP))
        if not 0<=severity<=tiv*100:
            raise EventModelBlocked("fictional Bernoulli severity exceeds asset value")
        original_reference_cents+=site_loss_cents(gust,tiv,Decimal("1"))
        d=_as_cents(POLICY_DEDUCTIBLE_EUR)
        lim=_as_cents(POLICY_LIMIT_EUR)
        il=min(max(severity-d,0),lim)
        ceded=(il*QS_CEDED_PERCENT+50)//100
        analytic_gul+=p*severity
        analytic_il+=p*il
        analytic_qs+=p*ceded
        risks.append((key,float(p),severity))
    if len(seen)!=EXPECTED_N or original_reference_cents!=REFERENCE_CONDITIONAL_GUL_CENTS:
        raise EventModelBlocked("source-locked expected one-event reference is not reproduced")
    risks.sort(key=lambda x:x[0])
    return risks,{
        "original_Schwierz_one_event_reference_conditional_GUL_EUR":
            f"{Decimal(original_reference_cents)/100:.2f}",
        "analytical_marginal_Bernoulli_GUL_eur":f"{analytic_gul/100:.2f}",
        "analytical_marginal_Bernoulli_insured_IL_eur":f"{analytic_il/100:.2f}",
        "analytical_marginal_Bernoulli_QS_ceded_eur":f"{analytic_qs/100:.2f}",
        "analytical_marginal_retained_pre_XL_eur":f"{(analytic_il-analytic_qs)/100:.2f}",
        "analytical_non_annual_pre_XL_marginals_same_across_dependence":True,
    }


def nearest_rank(values:list[int],fraction:float) -> int:
    if not values or not 0<=fraction<=1:
        raise EventModelBlocked("empty or impossible conditional one-event quantile")
    items=sorted(values)
    return items[max(0,math.ceil(len(items)*fraction)-1)]


def one_scenario(risks:list[tuple[str,float,int]],*,share_weight:float,seed:int,trials:int) -> dict:
    if (type(seed) is not int or not 0<=seed<=2**32-1
        or type(trials) is not int or not 2<=trials<=16384
        or share_weight not in (0.0,0.25)
        or not risks or len(risks)>MAX_SITES):
        raise EventModelBlocked("strict synthetic common shock / trial / seed contract")
    rng=random.Random(seed)
    metrics=(
        "groundup_cents","insured_before_reinsurance_cents",
        "quota_share_ceded_cents","occurrence_xl_recovery_cents",
        "insurer_net_after_qs_xl_cents"
    )
    history={k:[] for k in metrics}
    affected=[]
    # COMMON RANDOM NUMBERS: exactly the same RNG sequence and identical
    # marginal PAA for both dependence alternatives. Only *assignment* of
    # independent vs event-shared U changes; 25% mixing weight is NOT a
    # claim that pairwise loss correlation or systemic occurrence is 25%.
    for _ in range(trials):
        shared_u=rng.random()
        gross_risks=[]
        n_affected=0
        for _,p,sev in risks:
            choose_shared=rng.random()
            independent_u=rng.random()
            active=(shared_u if choose_shared < share_weight else independent_u)<p
            if active and sev>0:
                gross_risks.append(sev)
                n_affected+=1
        # Avoid materializing 10k zeros: policy terms on zero loss return 0.
        # For all-zero events, a singleton [0] is economically equivalent.
        event=financial_tower(gross_risks or [0])
        for key in metrics:history[key].append(event[key])
        affected.append(n_affected)
    results={}
    for key in metrics:
        vals=history[key]
        mean=sum(vals)/trials
        stderr=statistics.stdev(vals)/math.sqrt(trials)
        results[key.replace("_cents","_eur")]={
            "sample_mean":f"{mean/100:.2f}",
            "sample_standard_error_of_mean_eur":f"{stderr/100:.2f}",
            "q50_one_event_eur":f"{nearest_rank(vals,0.5)/100:.2f}",
            "q95_one_event_eur":f"{nearest_rank(vals,0.95)/100:.2f}",
            "q99_one_event_eur":f"{nearest_rank(vals,0.99)/100:.2f}",
            "sample_max_eur":f"{max(vals)/100:.2f}",
        }
    mean_affected=sum(affected)/trials
    if (any(vals<0 for series in history.values() for vals in series)
        or any(history["quota_share_ceded_cents"][i]
               +history["occurrence_xl_recovery_cents"][i]
               +history["insurer_net_after_qs_xl_cents"][i]
               !=history["insured_before_reinsurance_cents"][i]
               for i in range(trials))):
        raise EventModelBlocked("aggregate path failed exact financial conservation")
    return {
        "share_common_uniform_mixing_weight_not_pairwise_correlation":share_weight,
        "n_conditionally_simulated_replicates_of_one_Kyrill_event":trials,
        "fictional_sites_affected_sample_mean":f"{mean_affected:.3f}",
        "replicates_with_no_triggered_site":sum(v==0 for v in affected),
        "statistical_outputs_are_one_event_conditional_not_annual_return_period":True,
        "summary":results,
    }


def execute(winds:list[dict],values:dict[str,tuple[int,str]],*,trials:int=TRIALS,seed:int=SEED)->dict:
    with localcontext() as ctx:
        ctx.prec=42
        risks,analytic=_risk_catalogue(winds,values)
    scenarios={}
    for scenario,weight in SHARED_UNIFORM_WEIGHTS.items():
        scenarios[scenario]=one_scenario(risks,share_weight=weight,seed=seed,trials=trials)
    return {
        "schema":SCHEMA,
        "status":"RESEARCH_ONLY_FICTIONAL_POLICY_QS_XL_SINGLE_HISTORICAL_EVENT_NOT_OEP_AEP",
        "source_kyrill_real_historical_event_date":"2007-01-18",
        "historical_event_count":1,
        "XWS_original_site_wind_zip_SHA256":XWS_ZIP_SHA,
        "XWS_original_site_wind_CSV_SHA256":XWS_CSV_SHA,
        "original_NRW_HU_full_source_SHA256":HU22_SHA,
        "fictional_NRW_OED_10k_zip_SHA256":OED_ZIP_SHA,
        "fictional_sample_site_count":len(risks),
        "fictional_sample_total_tiv_eur":EXPECTED_TIV,
        "windfield":"Kyrill recalibrated mean, original source rotated-pole 3-second gust",
        "wind_vulnerability":"Schwierz 2010 numerical PAA/MDD reference; not German insurer calibrated",
        "invented_secondary_uncertainty":"Bernoulli(PAA) damage presence; severity fixed at MDD*TIV if affected",
        "conditional_marginal_expected_reference":analytic,
        "hypothetical_financial_terms":{
            "policy_per_site_deductible_eur":POLICY_DEDUCTIBLE_EUR,
            "policy_per_site_max_payment_eur":POLICY_LIMIT_EUR,
            "quota_share_reinsurance_ceded_percent_of_post_policy_IL":QS_CEDED_PERCENT,
            "occurrence_cat_XL_attachment_eur_on_post_QS_retained":OCC_XL_ATTACHMENT_EUR,
            "occurrence_cat_XL_limit_eur":OCC_XL_LIMIT_EUR,
            "scope":"one historic event, no hours aggregation, annual reinstatements or cross-event aggregate",
        },
        "fixed_rng_seed_specific_to_this_toy_not_FFBK_RIM":seed,
        "n_trials_per_dependence_scenario":trials,
        "shared_uniform_hypothesis_not_empirical_event_wind_or_damage_correlation":True,
        "no_site_or_insurer_address_or_original_provider_NetCDF_republished":True,
        "actual_RV_policy_terms_or_reinsurance_observed":False,
        "credible_Germany_2025_building_fragility_calibrated":False,
        "native_Oasis_or_NextGen_Kyrill_financial_loss_run":False,
        "annual_event_rate_or_occurrence_distribution_verified":False,
        "gross_net_OEP_AEP_computed":False,
        "scenario_results":scenarios,
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_XWS_geocoded_10k_wind_zip",type=Path)
    parser.add_argument("source_original_NRW_HU_10k_fictional_OED_zip",type=Path)
    parser.add_argument("new_summary_json",type=Path)
    parser.add_argument("--seed",type=int,default=SEED)
    parser.add_argument("--trials",type=int,default=TRIALS)
    args=parser.parse_args()
    out=args.new_summary_json
    if out.exists() or out.is_symlink() or not out.parent.is_dir():
        raise EventModelBlocked("fresh output JSON path required")
    winds,values,_=original_pair(args.source_XWS_geocoded_10k_wind_zip,
                                 args.source_original_NRW_HU_10k_fictional_OED_zip)
    report=execute(winds,values,trials=args.trials,seed=args.seed)
    output=(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    out.write_bytes(output)
    print(json.dumps({
       "status":report["status"],
       "source_site_count":report["fictional_sample_site_count"],
       "historical_event_count":report["historical_event_count"],
       "rng_seed":args.seed,"trials":args.trials,
       "original_one_event_reference_GUL_eur":report["conditional_marginal_expected_reference"]["original_Schwierz_one_event_reference_conditional_GUL_EUR"],
       "fictional_financial_cases":report["scenario_results"],
       "output_json_sha256":hashlib.sha256(output).hexdigest(),
       "annual_Gross_Net_OEP_AEP_calibrated":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except (EventModelBlocked,SensitivityBlocked,OSError,KeyError,ValueError) as exc:
        print("XWS_KYRILL_FICTIONAL_EVENT_MC_BLOCKED: "+str(exc)[:180],file=sys.stderr)
        raise SystemExit(2)
