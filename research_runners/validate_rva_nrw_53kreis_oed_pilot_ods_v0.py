# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two fully synthetic 53-Kreis NRW conditional OED portfolios + original-source receipt.

Pinned official ods-tools 5.0.8 format validation; no provider building points,
R+V actual county portfolio, PV roof-peril contract, GUL/IL/RI or model lookup.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from export_rva_nrw_53kreis_oed_pilot_v0 import (
    PV_SENSITIVITY, SAMPLE_N, export_nrw_pilot
)


def _read(path:Path)->list[dict[str,str]]:
    with path.open(encoding="utf-8",newline="") as stream:
        return list(csv.DictReader(stream))


def validate_pair(root:Path)->dict:
    from ods_tools import __version__ as ver
    from ods_tools.oed import OedExposure
    if ver!="5.0.8":
        raise ValueError("ODS Tools required exact 5.0.8")
    if root.exists() or not root.parent.is_dir():
        raise ValueError("fresh output root required")
    root.mkdir(mode=0o700)
    try:
        reports={}
        counts={}
        for case in PV_SENSITIVITY:
            out=root/case
            receipt=export_nrw_pilot(out,case,"age_archetype",SAMPLE_N)
            # The OED constructor checks schema; note missing lat/long fields
            # deliberately BLOCK geographic hazard lookup even when syntax OK.
            OedExposure(location=str(out/"location.csv"),account=str(out/"account.csv"),check_oed=True)
            loc=_read(out/"location.csv")
            acc=_read(out/"account.csv")
            kreis=_read(out/"kreis_summary.csv")
            cohort=_read(out/"cohort_receipt.csv")
            if (len(loc),len(acc),len(kreis),len(cohort))!=(SAMPLE_N,SAMPLE_N,53,530):
                raise ValueError("NRW OED population mismatch")
            if len({r["LocNumber"] for r in loc})!=SAMPLE_N:
                raise ValueError("duplicate fictional location IDs")
            if {r["AccNumber"] for r in loc}!={r["AccNumber"] for r in acc}:
                raise ValueError("NRW fictional account IDs mismatch")
            if any(r["Latitude"] or r["Longitude"] for r in loc):
                raise ValueError("accidentally geocoded, not allowed in public scenario")
            if sum(int(r["FictionalExportedTIVEUR"]) for r in cohort)!=receipt["exported_fictional_building_TIV_eur"]:
                raise ValueError("cell sum of fictional value mismatch")
            if (sum(int(r["NRWConditional2025FictionalSampleContracts"]) for r in kreis)!=SAMPLE_N
                or sum(int(r["Full2025FictionalCountyContractsFromNationalPrior"]) for r in kreis)!=
                   receipt["NRW_fictional_full_prior_contract_count"]):
                raise ValueError("NRW conditional vs full nationwide prior mismatch")
            if (receipt["NRW_company_county_distribution_observed"] is not False
                or receipt["germany_peril_model_lookup_allowed"] is not False
                or receipt["status"]!="RESEARCH_NOT_GEOLOCATED_NOT_MODEL_READY"):
                raise ValueError("unsafe invented company/pv/model admission")
            for file,sha in receipt["output_sha256"].items():
                if hashlib.sha256((out/file).read_bytes()).hexdigest()!=sha:
                    raise ValueError("output receipt mismatch")
            counts[case]={r["KreisAGS2022"]:int(r["NRWConditional2025FictionalSampleContracts"]) for r in kreis}
            reports[case]={
                "fictional_tiv_eur":receipt["exported_fictional_building_TIV_eur"],
                "fictional_NRW_full_contract_population":receipt["NRW_fictional_full_prior_contract_count"],
                "fictional_nrw_conditional_sample":SAMPLE_N,
                "real_2022_nrw_county_count":53,
                "real_2022_nrw_residential_use_building_count":4042220,
                "real_2026_nrw_registered_building_pv_generating_units":876684,
                "real_rv_county_market_shares":False,
                "geocoded":False,
                "model_ready":False,
                "sample_is_unscaled":True,
                "dataset_directory":case,
                "source_sha256":receipt["input_sha256"],
            }
        base,other=[counts[c] for c in PV_SENSITIVITY]
        if set(base)!=set(other) or len(base)!=53:
            raise ValueError("NRW sensitivity county identity mismatch")
        moved=sum(abs(base[k]-other[k]) for k in base)
        if moved%2:
            raise ValueError("NRW pair conservation mismatch")
        movement=moved//2
        if movement==0:
            raise ValueError("PV ecological counterfactual failed to shift a regional sample")
        report={
            "schema":"RVA_NRW_CONDITIONAL_53KREIS_2_CASE_SOURCE_VALIDATED_OED_V0",
            "status":"NOT_GEOLOCATED_NO_REAL_INSURER_EXPOSURE_NO_CAT_RUN",
            "cases":reports,
            "fictional_sampled_contracts_reallocated_between_counties":movement,
            "fictional_sampled_contract_total_variation_percent":round(movement/SAMPLE_N*100,4),
            "normalization":"10,000 fictitious NRW-only conditional records per scenario; not R+V observed NRW count",
            "national_insurer_count_not_nrw_insurer_count":True,
            "year_vintages_disjoint":"census 2022 / issuer HGB 2025 / secondary PV 2026",
            "PV_generating_units_not_unique_roofs_or_company_insured_addresses":True,
            "real_site_geocodes":False,
            "actual_insurer_policy_or_roof_insurance":False,
            "germany_windstorm_native_GUL_IL_RI_OEP_AEP":False,
        }
        (root/"scenario_comparison.json").write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        return report
    except Exception:
        shutil.rmtree(root)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outdir",nargs="?",type=Path)
    args=parser.parse_args()
    if args.outdir is not None:
        result=validate_pair(args.outdir)
    else:
        with tempfile.TemporaryDirectory(prefix="nrw-oed-53-source-") as temp:
            result=validate_pair(Path(temp)/"nrw")
    print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
