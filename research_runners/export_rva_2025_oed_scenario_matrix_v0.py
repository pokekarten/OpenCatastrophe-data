# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Produce six source-gated synthetic R+V-like OED 5.0 study scenarios as CI artifact.

This runs on the original-receipted 400-Kreis + 10 age-cohort source,
NOT arbitrary county fixtures. Outputs must never be called R+V insured sites,
observed TIV, model-ready coordinates, calibrated German CAT or gross/net EP.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
import tomllib
import argparse
import sys

from rva_2025_oed_staging_v0 import (
    CENSUS, AGES, HGB, CASES, export, rows_from_validated_sources,
    NATIONAL, GWP_CENTS,
)


def create_matrix(root: Path) -> dict:
    if root.exists() or not root.parent.is_dir():
        raise ValueError("output root must not exist; parent must exist")
    paths={"zensus_2022_counties":CENSUS,"zensus_2022_age":AGES,"rva_solo_hgb":HGB}
    raw={k:p.read_bytes() for k,p in paths.items()}
    if any(len(s)>1_000_000 for s in raw.values()):
        raise ValueError("unexpected source size")
    inputs=[tomllib.loads(v.decode("utf-8")) for v in raw.values()]
    input_sha={k:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
    root.mkdir(mode=0o700)
    try:
        summary=[]
        for case in CASES:
            cells=rows_from_validated_sources(inputs,case)
            if len(cells)!=4000 or sum(row["count"] for row in cells)!=NATIONAL:
                raise ValueError("source/authentic population gates did not conserve 4000 cells")
            for pattern in ("flat","age_archetype"):
                label=case.lower()+"__"+pattern
                out=root/label
                result=export(cells,out,case,"central",10000,input_sha,pattern)
                if (result["status"]!="NOT_GEOLOCATED_NOT_MODEL_READY"
                    or result["germany_peril_model_lookup_allowed"] is not False
                    or result["physical_site_coordinates_observed"] is not False
                    or result["exported_fictional_locations_and_policies"]!=10000
                    or result["company_2025_national_year_end_building_contracts_observed"]!=NATIONAL
                    or result["company_2025_national_annual_building_gwp_eur_cents_observed"]!=GWP_CENTS):
                    raise ValueError("unsafe scenario promotion or broken national counts")
                if pattern=="flat" and result["exported_fictional_building_tiv_eur"]!=4_500_000_000:
                    raise ValueError("flat 10k TIV benchmark changed")
                with (out/"cohort_receipt.csv").open(newline="",encoding="utf-8") as stream:
                    cohort=list(csv.DictReader(stream))
                if (len(cohort)!=4000
                    or sum(int(z["Fictional2025FullContractCount"]) for z in cohort)!=NATIONAL
                    or sum(int(z["Fictional2025ExportedContractCount"]) for z in cohort)!=10000
                    or sum(int(z["FictionalExportedBuildingTIVEUR"]) for z in cohort)
                      !=result["exported_fictional_building_tiv_eur"]):
                    raise ValueError("synthetic age/county allocation or TIV drift")
                summary.append({
                    "case":case,"valuation_pattern":pattern,"value_basis":"explicitly_fictional",
                    "sampled_contracts":10000,
                    "national_solo_observed_contract_control":NATIONAL,
                    "national_annual_solo_hgb_building_gwp_eur_cents":GWP_CENTS,
                    "sampled_fictional_tiv_eur":result["exported_fictional_building_tiv_eur"],
                    "geocodes_verified":False,"model_run_approved":False,
                    "OED_directory":label,
                    "input_sha256":input_sha
                })
        fieldnames=list(summary[0])
        with (root/"scenario_comparison.csv").open("x",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=fieldnames,lineterminator="\n")
            writer.writeheader()
            for row in summary:
                row=dict(row,input_sha256=json.dumps(row["input_sha256"],sort_keys=True))
                writer.writerow(row)
        disclaimer={
            "schema":"RVA_LIKE_400_KREIS_OED_6_SCENARIO_MATRIX_V0",
            "project":"OpenCatastrophe-data",
            "issuer_reference":"R+V Allgemeine Versicherung AG, solo, 2025",
            "source_date":"2022-05-15",
            "source_publisher":"Statistisches Bundesamt (Destatis) / Statistische Ämter des Bundes und der Länder",
            "original_source_url":"https://www.destatis.de/static/DE/zensus/gitterdaten/Regionaltabelle_Gebaeude_Wohnungen.xlsx",
            "source_license":"Datenlizenz Deutschland – Namensnennung – Version 2.0",
            "source_license_url":"https://www.govdata.de/dl-de/by-2-0",
            "observed_national_contracts_at_year_end":NATIONAL,
            "observed_national_building_gwp_eur_cents":GWP_CENTS,
            "original_source_sha256":input_sha,
            "scenario_count":len(summary),
            "model_input_approved":False,"geocoded":False,
            "actual_insurer_buildings_verified":False,
            "actual_insurer_tiv_observed":False,
            "natural_peril_covers_observed":False,
            "German_Oasis_GUL_IL_RI_run_verified":False,
            "note":"Original census physical opportunities and national insurer accounting are real separate source populations. Every county age insurer allocation, individual policy, value, OED peril selection and relationship is fictional. Locations have intentionally missing coordinate fields. This is NOT loss-model-ready.",
            "artifact_manifest_sha256":{},
        }
        for row in summary:
            for filename in ("location.csv","account.csv","cohort_receipt.csv","manifest.json"):
                path=root/row["OED_directory"]/filename
                disclaimer["artifact_manifest_sha256"][str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
        disclaimer["artifact_manifest_sha256"]["scenario_comparison.csv"]=hashlib.sha256((root/"scenario_comparison.csv").read_bytes()).hexdigest()
        (root/"SOURCE_LICENSE_AND_BOUNDARIES.json").write_text(json.dumps(disclaimer,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
        return disclaimer
    except Exception:
        shutil.rmtree(root)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root",type=Path)
    args=parser.parse_args()
    print(json.dumps(create_matrix(args.output_root),sort_keys=True,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    sys.exit(main())
