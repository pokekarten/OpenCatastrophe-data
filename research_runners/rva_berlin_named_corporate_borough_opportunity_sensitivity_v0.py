# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Observed Berlin Senate 2025 corporate *DWELLING* footprint, not insurer sites.

April 2025 Berlin Senate report confirms R+V Allgemeine insurer for WBM and
GESOBAU, member of degewo/Allianz consortium. November report confirms June
2025 per-borough corporate dwelling stocks. Both are public facts; neither
proves that the June stock is fully covered, insured amounts, insurer ceded
share, insured policy count or specific building sites.
"""
from __future__ import annotations
import argparse, hashlib, json, tomllib
from pathlib import Path
from fractions import Fraction

HERE=Path(__file__).resolve().parents[1]
STOCK=HERE/"research/observations/rva_berlin_senate_housing_borough_stock_2025_v0.toml"
INSURER=HERE/"research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml"
ORIGINAL_PDFS=HERE/"research/observations/rva_berlin_senate_2025_original_pdf_receipts_v0.toml"
EXPECTED_ORIGINAL_PDFS=(
    ("BERLIN_SENATE_19_22033_20250401","2025-04-01",
     "https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf",
     "0671a38d440b0628088399c0ee0fa521e24d31738d19c2d8b93d65424c87143f",22528,6,7),
    ("BERLIN_SENATE_19_24229_20251111","2025-11-11",
     "https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24229.pdf",
     "1269725e4ff8427f32db22a66a0745bc12a75dc1281ca62de7d21ddcaead307e",21842,5,8),
)
COMPANIES=("degewo","gesobau","gewobag","howoge","stadt_und_land","wbm","berlinovo")
EXPECTED=(82637,49054,75091,82152,53304,34040,18666)
OTHER=(2541,307,329,276,1066,0,0)
BOROUGHS=("Charlottenburg-Wilmersdorf","Friedrichshain-Kreuzberg","Lichtenberg",
          "Marzahn-Hellersdorf","Mitte","Neukoelln","Pankow","Reinickendorf",
          "Spandau","Steglitz-Zehlendorf","Tempelhof-Schoeneberg",
          "Treptow-Koepenick")
COMPANY_TO_BOROUGH={"degewo":"degewo AG",
                     "gesobau":"GESOBAU AG",
                     "wbm":"WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"}
SCENARIOS=(("degewo_0pct_hypothetical_share",0),
           ("degewo_50pct_hypothetical_share",1),
           ("degewo_100pct_hypothetical_share",2))


def invalid(message:str):
    raise ValueError(message)


def validate_pinned_original_pdf_receipt(receipt:dict|None=None)->dict:
    """Source *attestation* gate, never an insured site or all-cell proof.

    Exact original bytes independently reread in source workflow #1342.
    This function ties the scenario to that provenance receipt; it does not
    itself fetch source PDF bytes or re-verify all 12×7 numeric facts.
    """
    if receipt is None:
        receipt=tomllib.loads(ORIGINAL_PDFS.read_text(encoding="utf-8"))
    if (receipt.get("schema_version")!="RVA_BERLIN_SENATE_2025_ORIGINAL_PDF_BYTES_V0"
        or receipt.get("original_files_acquired_and_hashed_in_ephemeral_github_action") is not True
        or receipt.get("verified_original_source_is_public_official_berlin_senate") is not True
        or receipt.get("raw_pdf_files_committed_or_redistributed") is not False
        or receipt.get("actual_RV_insured_berlin_building_sites_verified") is not False
        or receipt.get("actual_RV_degewo_coinsurance_participation_verified") is not False
        or receipt.get("real_RV_site_TIV_and_policy_limits_verified") is not False
        or receipt.get("model_CAT_admission") is not False):
        invalid("Original Senate PDF provenance or non-insurer source scope changed")
    records=receipt.get("documents",[])
    if len(records)!=2:invalid("Original Senate PDF receipts missing")
    for source,expected in zip(records,EXPECTED_ORIGINAL_PDFS):
        ID,dt,url,sha,size,pages,markers=expected
        if (source.get("id")!=ID
            or source.get("official_answer_date")!=dt
            or source.get("url")!=url
            or source.get("original_sha256")!=sha
            or source.get("original_bytes")!=size
            or source.get("original_pages")!=pages
            or source.get("positive_semantic_marker_count")!=markers
            or source.get("company_specific_insured_asset_count_observed") is not False):
            invalid("Original Senate PDF source hash/bytes/scope drift")
    return {
        "official_2025_senate_two_original_pdf_hashes_matched":True,
        "original_pdf_bytes_checked_from_previous_independent_workflow":True,
        "current_run_fetched_original_pdf_bytes":False,
        "specific_insured_rva_buildings_observed":False,
        "cat_exposure_model_admitted":False,
    }


def validate(s:dict, i:dict)->dict:
    pdf_provenance=validate_pinned_original_pdf_receipt()
    if (s.get("schema_version")!="BERLIN_SENATE_2025_LWU_12_BOROUGH_CORPORATE_DWELLING_MATRIX_V0"
        or s.get("source_official_url")!="https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-24229.pdf"
        or s.get("source_document_number")!="Drucksache 19/24229"
        or s.get("source_answer_date")!="2025-11-11"
        or s.get("source_table_question")!=2
        or s.get("source_stock_date_six_lwu")!="2025-06-30"
        or s.get("source_stock_date_berlinovo")!="2025-09-30"
        or s.get("source_pdf_page_zero_based")!=2
        or s.get("company_column_order")!=list(COMPANIES)):
        invalid("official Berlin 2025 borough stock source mapping changed")
    if (i.get("schema_version")!="BERLIN_SENATE_2025_PUBLIC_HOUSING_BUILDING_INSURER_RELATIONSHIPS_V0"
        or i.get("source_official_url")!="https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf"
        or i.get("source_statement_date")!="2025-04-01"):
        invalid("April 2025 named insurer evidence missing")
    rel={r["legal_name"]:r for r in i.get("housing_companies",[])}
    if len(rel)!=6:
        invalid("missing official client insurer positive and competitor records")
    for company,name in COMPANY_TO_BOROUGH.items():
        r=rel.get(name,{})
        if (r.get("rva_allgemeine_explicitly_named") is not True
            or "R+V Allgemeine Versicherung AG" not in r.get("named_insurers",[])):
            invalid("observed R+V named corporate-account relation missing")
    if (rel["degewo AG"]["insurance_relation_type"]!="named_member_of_coinsurance_consortium"
        or "Allianz AG" not in rel["degewo AG"]["named_insurers"]):
        invalid("degewo Allianz co-insurance consortium ignored")
    for company in ("Gewobag Wohnungsbau-Aktiengesellschaft Berlin",
                    "HOWOGE Wohnungsbaugesellschaft mbH",
                    "STADT UND LAND Wohnbauten-Gesellschaft mbH"):
        if rel.get(company,{}).get("rva_allgemeine_explicitly_named") is not False:
            invalid("competitor account falsely included in R+V")
    for f in ("original_pdf_byte_sha256_verified_this_turn",
              "any_property_insured_by_rva_from_matrix",
              "june_2025_corporate_stock_same_as_april_2025_policy_schedule",
              "insurance_contract_count_observed_from_this_matrix",
              "insured_buildings_count_observed",
              "insured_site_address_or_geocode_observed",
              "covered_tiv_or_rv_coinsurance_percent_observed"):
        if s.get(f) is not False:
            invalid("corporate dwelling stock incorrectly admitted as insured risk")
    if (s.get("company_by_borough_stock_really_observed") is not True
        or s.get("are_corporate_stock_dwellings") is not True
        or s.get("other_stock_not_borough_specific") is not True
        or s.get("borough_rows")!=12
        or s.get("original_reported_total_six_lwu_dwellings")!=376278
        or s.get("original_reported_total_berlinovo_dwellings")!=18666):
        invalid("public borough/company stock scope changed")
    total=s.get("national_published_row_totals",{})
    unassigned=s.get("unassigned_other_stock",{})
    for j,k in enumerate(COMPANIES):
        if total.get(k)!=EXPECTED[j] or unassigned.get(k)!=OTHER[j]:
            invalid("published Senate original housing stock total changed")
    rows=s.get("boroughs",[])
    if len(rows)!=12 or {x.get("borough_name") for x in rows}!=set(BOROUGHS):
        invalid("missing/duplicate original 12 Berlin borough names")
    sums={k:0 for k in COMPANIES}
    for row in rows:
        for k in COMPANIES:
            v=row.get(k)
            if type(v) is not int or v<0:
                invalid("invalid original numeric borough dwelling count")
            sums[k]+=v
    for j,k in enumerate(COMPANIES):
        if sums[k]+unassigned[k]!=EXPECTED[j]:
            invalid("per-corporation original Senate borough totals not reconciled")
    return {"boroughs":rows,"official_source_pdf_provenance":pdf_provenance,
            "published_company_totals":total,
            "published_other_not_borough_assignable":unassigned,
            "published_berlin_12_borough_totals":sums,
            "three_named_RV_linked_corporate_total_dwellings_including_other":
                total["degewo"]+total["gesobau"]+total["wbm"],
            "three_named_RV_linked_corporate_12_borough_dwellings":
                sums["degewo"]+sums["gesobau"]+sums["wbm"]}


def run(s:dict,i:dict)->dict:
    audit=validate(s,i)
    cases={}
    for case,degewo_twice_share in SCENARIOS:
        # Fractional corporate involvement only; these are hypothetical
        # dwelling-equivalent weights, NEVER inferred insured building sites.
        entries=[]
        for r in audit["boroughs"]:
            baseline=r["gesobau"]+r["wbm"]
            numerator_twice=baseline*2+degewo_twice_share*r["degewo"]
            entries.append({
                "berlin_borough":r["borough_name"],
                "actual_public_2025_gesobau_dwellings":r["gesobau"],
                "actual_public_2025_wbm_dwellings":r["wbm"],
                "actual_public_2025_degewo_dwellings":r["degewo"],
                "hypothetical_RV_linked_account_dwelling_equivalent_twice":numerator_twice,
                "real_RV_insured_building_count_observed":False,
            })
        total_twice=sum(x["hypothetical_RV_linked_account_dwelling_equivalent_twice"] for x in entries)
        cases[case]={
            "invented_degewo_coinsurance_or_covered_stock_multiplier":
                ("0","0.5","1")[degewo_twice_share],
            "hypothetical_total_account_dwelling_equivalents":str(Fraction(total_twice,2)),
            "boroughs":entries,
            "count_of_real_RV_insured_buildings_estimated":False,
            "insurer_portfolio_actual_TIV_observed":False,
            "case_is_declared_hypothesis_not_observation":True,
        }
    return {
        "schema_version":"BERLIN_RVA_2025_NAMED_CORPORATE_BOROUGH_OPPORTUNITY_SENSITIVITY_V0",
        "source":"Berlin Senate 19/22033 confirmed April 2025 corporate building insurers; 19/24229 June 2025 borough dwelling stocks",
        "actual_independent_corporate_stock_audit":{k:v for k,v in audit.items() if k!="boroughs"},
        "scenarios":cases,
        "insurer_exposure_admission":{
            "real_RV_buildings_or_coordinates":False,
            "real_RV_degewo_coinsurance_fraction":False,
            "real_RV_cover_or_tiv_per_borough":False,
            "insurance_contracts_equal_housing_units":False,
            "can_add_housing_dwellings_to_1060546_company_policy_total":False,
            "native_german_OEP_AEP_calibrated":False,
        }
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stock",type=Path,default=STOCK)
    p.add_argument("--insurer",type=Path,default=INSURER)
    args=p.parse_args()
    try:
        blobs=[x.read_bytes() for x in (args.stock,args.insurer)]
        if any(len(b)>500000 for b in blobs):invalid("input too large")
        s,i=[tomllib.loads(b.decode("utf-8")) for b in blobs]
        x=run(s,i)
        x["input_sha256"]={k:hashlib.sha256(v).hexdigest() for k,v in zip(("original_dwellings","official_insurer_relationship"),blobs)}
        print(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2))
    except (ValueError,OSError,UnicodeError) as e:
        p.exit(status=2,message="BLOCKED: "+str(e)+"\n")

if __name__=="__main__":
    main()
