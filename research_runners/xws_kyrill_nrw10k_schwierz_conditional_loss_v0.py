# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Kyrill/XWS 2007: Schwierz-2010 conditional one-event loss SENSITIVITY ONLY.

Uses published numerical PAA and MDD knots from the CLIMADA Schwierz-2010
storm impact function. Original arithmetic here is independent stdlib Python;
the GPL-licensed CLIMADA implementation is NOT bundled or imported.
This is NOT an observed R+V insured-loss model, a German-calibrated building
vulnerability, a stochastic GUL, an insured IL/RI or an annual OEP/AEP.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

XWS_ZIP_SHA = "631ef3b4f25ac5512bb8c71d936fc2d1ee6922af2f3ab01df17ca3f987a0f918"
XWS_CSV_SHA = "80ad88ddcb8860d7f2396a35a2e3ce57d3b73eb4b98353503e9a04bd3dac8cdf"
OED_ZIP_SHA = "5b0055ce71314f7d7baf4f67008cd4abba3df28a4bce0690bbe9521a3cc35757"
OED_MANIFEST_SHA = "b4713a9a09a55193d39b64550bc1408ba588303d8a4e658f05536b3dbe14b416"
HU22_SHA = "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da"
EXPECTED_N = 10000
EXPECTED_COUNTIES = 53
EXPECTED_TIV = 4826029500
XWS_FIELDS = {
    "recalibrated_lower95": "KyrillLower95GustMS",
    "recalibrated_mean": "KyrillRecalMeanGustMS",
    "recalibrated_upper95": "KyrillUpper95GustMS",
    "uncontaminated_raw": "KyrillRawUncontaminatedGustMS",
}
STRENGTHS = {"low_half_reference": Decimal("0.5"),
             "reference_unmodified": Decimal("1"),
             "high_double_reference": Decimal("2")}
# Numerical parameters attributed to Schwierz et al. (2010), as published in
# CLIMADA ImpfStormEurope.from_schwierz, under GPLv3. Only numeric points are
# restated here, with independently authored interpolation and financial checks.
SOURCE_URL = "https://climada-python.readthedocs.io/en/latest/_modules/climada/entity/impact_funcs/storm_europe.html"
KNOTS = tuple(map(Decimal, ("0","20","25","30","35","40","45","50","55","60","80","100")))
PAA = tuple(map(Decimal, ("0","0","0.001","0.00676","0.03921","0.10707",
                          "0.25357","0.48869","0.82907","1","1","1")))
MDD = tuple(map(Decimal, ("0","0","0.001","0.00177515","0.00367253","0.00749977",
                          "0.01263556","0.01849639","0.02370487","0.037253","0.037253","0.037253")))
CENT = Decimal("0.01")


class SensitivityBlocked(ValueError):
    pass


def impact_parts(gust_m_s: Decimal) -> tuple[Decimal, Decimal]:
    """Linear interpolation of PAA and MDD SEPARATELY, then multiply."""
    if not isinstance(gust_m_s, Decimal) or not gust_m_s.is_finite() or gust_m_s < 0 or gust_m_s > 150:
        raise SensitivityBlocked("non-finite or out-of-physics wind source")
    if gust_m_s <= KNOTS[1]:
        return Decimal(0), Decimal(0)
    for i in range(2, len(KNOTS)):
        if gust_m_s <= KNOTS[i]:
            t = (gust_m_s - KNOTS[i-1]) / (KNOTS[i] - KNOTS[i-1])
            return (PAA[i-1] + t*(PAA[i]-PAA[i-1]),
                    MDD[i-1] + t*(MDD[i]-MDD[i-1]))
    return PAA[-1], MDD[-1]


def site_loss_cents(gust_m_s: Decimal, fictional_tiv_eur: int, multiplier: Decimal) -> int:
    if type(fictional_tiv_eur) is not int or not 0 < fictional_tiv_eur <= 1000000000:
        raise SensitivityBlocked("fictional building value missing or out of bounds")
    if multiplier not in STRENGTHS.values():
        raise SensitivityBlocked("undocumented sensitivity multiplier")
    paa, mdd = impact_parts(gust_m_s)
    # Each fictional risk is rounded to cents BEFORE grouped aggregation.
    return int((Decimal(fictional_tiv_eur) * paa * mdd * multiplier * 100
               ).to_integral_value(rounding=ROUND_HALF_UP))


def _zip(path: Path, expected_sha: str, expected_files: set[str], max_bytes: int) -> zipfile.ZipFile:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
        raise SensitivityBlocked("bounded local original-derived research ZIP required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise SensitivityBlocked("original research artifact ZIP SHA-256 mismatch")
    z = zipfile.ZipFile(io.BytesIO(raw))
    if set(z.namelist()) != expected_files or z.testzip() is not None:
        z.close()
        raise SensitivityBlocked("archive member set or CRC mismatch")
    return z


def _rows(blob: bytes, *, cap=2000000) -> list[dict]:
    if len(blob) > cap:
        raise SensitivityBlocked("archive CSV exceeds bounded decoder budget")
    parser=csv.DictReader(io.StringIO(blob.decode("utf-8")))
    if not parser.fieldnames or len(parser.fieldnames)!=len(set(parser.fieldnames)):
        raise SensitivityBlocked("duplicate or missing source CSV headers")
    return list(parser)


def original_pair(xws: Path, oed: Path) -> tuple[list[dict], dict[str,tuple[int,str]], dict]:
    with _zip(xws, XWS_ZIP_SHA, {
        "xws-kyrill-2007-fictitious-nrw-10k-gust-only.csv",
        "xws-kyrill-2007-source-and-no-loss-receipt.json"}, 5000000) as z:
        raw=z.read("xws-kyrill-2007-fictitious-nrw-10k-gust-only.csv")
        if hashlib.sha256(raw).hexdigest() != XWS_CSV_SHA:
            raise SensitivityBlocked("original four-product site gust CSV SHA mismatch")
        winds=_rows(raw)
        receipt=json.loads(z.read("xws-kyrill-2007-source-and-no-loss-receipt.json"))
        if (receipt.get("status")!="HISTORICAL_SOURCE_GUST_SITE_CROSSWALK_NOT_GERMANY_CAT_LOSS"
            or receipt.get("historical_physical_storm_count")!=1
            or receipt.get("fictional_geocoded_source_physical_site_count")!=EXPECTED_N
            or receipt.get("fictional_Kreis_count")!=EXPECTED_COUNTIES
            or receipt.get("fictional_TIV_eur_conserved_not_real_RV")!=EXPECTED_TIV
            or receipt.get("fictional_OED_zip_SHA256")!=OED_ZIP_SHA
            or receipt.get("fictional_OED_manifest_SHA256")!=OED_MANIFEST_SHA
            or receipt.get("source_original_2022_HU_SHA256")!=HU22_SHA
            or receipt.get("site_hazard_csv_SHA256")!=XWS_CSV_SHA
            or receipt.get("actual_RV_insured_site_identity_or_tiv_observed") is not False
            or receipt.get("annual_Gross_Net_OEP_AEP_authorized") is not False
            or receipt.get("native_Oasis_GUL_IL_RI_ran_for_Kyrill") is not False):
            raise SensitivityBlocked("original XWS source/insurer/model boundary changed")
    with _zip(oed,OED_ZIP_SHA,{"account.csv","location.csv","physical_candidate_evidence.csv","manifest.json"},3000000) as z:
        man_raw=z.read("manifest.json")
        if hashlib.sha256(man_raw).hexdigest()!=OED_MANIFEST_SHA:
            raise SensitivityBlocked("original OED scenario manifest SHA mismatch")
        manifest=json.loads(man_raw)
        if (manifest.get("fictional_policy_count")!=EXPECTED_N
            or manifest.get("real_source_counties_represented")!=EXPECTED_COUNTIES
            or manifest.get("source_original_2022_HU_complete_archive_SHA256")!=HU22_SHA
            or manifest.get("model_input_approved") is not False
            or manifest.get("physical_building_footprints_are_actual_RV_insured_sites") is not False):
            raise SensitivityBlocked("original physical buildings are not a certified insured portfolio")
        for fname in ("account.csv","location.csv","physical_candidate_evidence.csv"):
            if hashlib.sha256(z.read(fname)).hexdigest()!=manifest["output_file_SHA256"][fname]:
                raise SensitivityBlocked("original OED inner-CSV SHA mismatch")
        locations=_rows(z.read("location.csv"))
        accounts=_rows(z.read("account.csv"))
        original_physical=_rows(z.read("physical_candidate_evidence.csv"))
    if any(len(rows)!=EXPECTED_N for rows in (winds,locations,accounts,original_physical)):
        raise SensitivityBlocked("original 10,000-row population mismatch")
    vals={}
    for r in locations:
        k=r.get("LocNumber")
        if k in vals or not k or r.get("AccNumber")!=k or r.get("CountryCode")!="DE" or r.get("LocPerilsCovered")!="WW2":
            raise SensitivityBlocked("original fictitious OED identity/peril changed")
        ags=r.get("LocGroup","")
        if not ags.startswith("KREIS-05") or len(ags)!=11:
            raise SensitivityBlocked("original fictional Kreis identity invalid")
        try:val=int(r["BuildingTIV"])
        except (KeyError,ValueError,TypeError) as exc:raise SensitivityBlocked("fictional OED TIV invalid") from exc
        if str(val)!=r["BuildingTIV"] or not 0<val<=1000000000:
            raise SensitivityBlocked("fictional OED TIV out of bounds")
        vals[k]=(val,ags[6:])
    if (set(vals)!={r.get("AccNumber") for r in accounts}
        or set(vals)!={r.get("LocNumber") for r in original_physical}
        or any(r.get("SourcePhysicalCandidateNotInsuredSite")!="true" for r in original_physical)
        or sum(x[0] for x in vals.values())!=EXPECTED_TIV):
        raise SensitivityBlocked("original site/TIV and public physical-source proof mismatch")
    return winds,vals,receipt


def simulate(winds: list[dict], vals: dict[str,tuple[int,str]]) -> dict:
    if len(winds)!=EXPECTED_N or len(vals)!=EXPECTED_N:
        raise SensitivityBlocked("full 10k historical-to-fictional population required")
    totals=defaultdict(int)
    county_totals=defaultdict(int)
    county_tiv=defaultdict(int)
    county_n=defaultdict(int)
    positive_sites=defaultdict(int)
    seen=set()
    for row in winds:
        key=row.get("FictionalLocNumber")
        if not key or key in seen or key not in vals:
            raise SensitivityBlocked("duplicate or missing historical wind source site")
        seen.add(key)
        tiv,ags=vals[key]
        if (row.get("KreisAGS2022")!=ags
            or row.get("IsActualRVInsuredSite")!="false"
            or row.get("WindVulnerabilityCalibrated")!="false"):
            raise SensitivityBlocked("site identity or original noncalibration marker changed")
        wind={}
        for name,col in XWS_FIELDS.items():
            try:gust=Decimal(row[col])
            except (KeyError,ValueError,TypeError) as exc:
                raise SensitivityBlocked("missing physical original XWS wind gust") from exc
            impact_parts(gust)
            wind[name]=gust
        if not wind["recalibrated_lower95"]<=wind["recalibrated_mean"]<=wind["recalibrated_upper95"]:
            raise SensitivityBlocked("source wind quantile field ordering inconsistent")
        county_tiv[ags]+=tiv
        county_n[ags]+=1
        for field,gust in wind.items():
            for scenario,factor in STRENGTHS.items():
                label=(field,scenario)
                cents=site_loss_cents(gust,tiv,factor)
                totals[label]+=cents
                county_totals[(ags,*label)]+=cents
                if cents>0:positive_sites[label]+=1
    if (seen!=set(vals) or len(county_n)!=EXPECTED_COUNTIES
        or sum(county_n.values())!=EXPECTED_N
        or sum(county_tiv.values())!=EXPECTED_TIV):
        raise SensitivityBlocked("fictional county, TIV and original XWS source mismatch")
    summary=[]
    by_county=[]
    for field in XWS_FIELDS:
        for scenario,factor in STRENGTHS.items():
            label=(field,scenario)
            loss_cents=totals[label]
            summary.append({
                "historical_wind_source_variant":field,
                "hypothetical_damage_sensitivity":scenario,
                "non_empirical_MDR_PAA_product_multiplier":str(factor),
                "conditional_expected_groundup_eur":f"{Decimal(loss_cents)/100:.2f}",
                "conditional_expected_groundup_fraction_of_fictional_TIV":str(
                    (Decimal(loss_cents)/Decimal(100*EXPECTED_TIV)).quantize(Decimal("0.000000000001"))),
                "fictional_sites_with_positive_rounded_expected_loss":positive_sites[label],
            })
            for ags in sorted(county_n):
                by_county.append({
                    "KreisAGS2022":ags,
                    "HistoricalWindField":field,
                    "SyntheticDamageSensitivity":scenario,
                    "FictionalPolicies":county_n[ags],
                    "FictionalTIVEUR":county_tiv[ags],
                    "ConditionalExpectedGroundupEUR":f"{Decimal(county_totals[(ags,*label)])/100:.2f}",
                })
            if sum(county_totals[(ags,*label)] for ags in county_n)!=loss_cents:
                raise SensitivityBlocked("expected conditional loss cents not conserved by county")
    return {
        "schema":"Kyrill_2007_10k_NRW_Schwierz2010_PAA_MDD_conditional_sensitivity_v0",
        "status":"ONE_HISTORICAL_EVENT_HYPOTHETICAL_GROUNDUP_NOT_INSURED_CAT_LOSS",
        "wind_source_original_event":"Kyrill 2007-01-18, XWS historic",
        "historical_physical_storm_count":1,
        "site_count":EXPECTED_N, "county_count":EXPECTED_COUNTIES,
        "fictional_tiv_eur":EXPECTED_TIV,
        "source_xws_site_wind_original_zip_sha256":XWS_ZIP_SHA,
        "source_original_fictional_oed_zip_sha256":OED_ZIP_SHA,
        "published_impact_function_reference":SOURCE_URL,
        "published_impact_function":"Schwierz et al. 2010 / CLIMADA from_schwierz numerical PAA and MDD points",
        "impact_function_calibrated_to_2025_RV_or_original_HU22":False,
        "interpolation":"linear PAA and linear MDD independently; expected damage fraction=PAA*MDD",
        "financial_rounding":"per fictitious risk round conditional expected EUR to cent, then sum exactly by county",
        "sensitivity_multipliers_are_invented":True,
        "original_95percent_gust_variants_are_not_loss_confidence_bounds":True,
        "one_historical_storm_four_wind_views_not_four_independent_events":True,
        "conditional_expected_groundup_is_not_stochastic_sampled_GUL":True,
        "insurance_terms_deductibles_limits_or_treaties_applied":False,
        "native_Oasis_or_NextGen_GUL_IL_RI_executed":False,
        "annual_event_frequency_justified":False,
        "gross_net_OEP_AEP_calibrated":False,
        "insurer_RV_actual_risks_or_tiv_observed":False,
        "results":summary,
        "county_rows":by_county,
    }


def write(output_json:Path,output_csv:Path,report:dict) -> None:
    if output_json==output_csv or any(p.is_symlink() or p.exists() or not p.parent.is_dir() for p in (output_json,output_csv)):
        raise SensitivityBlocked("fresh research output files required")
    by_county=report.pop("county_rows")
    csv_output=io.StringIO(newline="")
    headers=list(by_county[0])
    writer=csv.DictWriter(csv_output,fieldnames=headers,lineterminator="\n")
    writer.writeheader()
    writer.writerows(by_county)
    csv_raw=csv_output.getvalue().encode("utf-8")
    report["per_county_csv_sha256"]=hashlib.sha256(csv_raw).hexdigest()
    report["per_county_csv_rows"]=len(by_county)
    report["third_party_XWS_NetCDF_files_committed"]=False
    report["site_level_original_hazard_and_policy_positions_published"]=False
    raw=json.dumps(report,ensure_ascii=True,sort_keys=True,indent=2).encode()+b"\n"
    try:
        output_csv.write_bytes(csv_raw)
        output_json.write_bytes(raw)
    except Exception:
        output_csv.unlink(missing_ok=True)
        output_json.unlink(missing_ok=True)
        raise


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_XWS_Kyrill_10k_hazard_only_zip",type=Path)
    parser.add_argument("original_HU22_10k_fictional_OED_zip",type=Path)
    parser.add_argument("new_summary_json",type=Path)
    parser.add_argument("new_county_sensitivity_csv",type=Path)
    args=parser.parse_args()
    winds,values,_=original_pair(args.original_XWS_Kyrill_10k_hazard_only_zip,
                                args.original_HU22_10k_fictional_OED_zip)
    with localcontext() as ctx:
        ctx.prec=42
        report=simulate(winds,values)
    write(args.new_summary_json,args.new_county_sensitivity_csv,report)
    print(json.dumps({k:report[k] for k in ("status","site_count","county_count","fictional_tiv_eur",
          "results","per_county_csv_sha256","gross_net_OEP_AEP_calibrated")},sort_keys=True))
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except (SensitivityBlocked,OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
        print("XWS_KYRILL_2010_SCHWIERZ_CONDITIONAL_ONLY_BLOCKED: "+str(exc)[:160],file=sys.stderr)
        raise SystemExit(2)
