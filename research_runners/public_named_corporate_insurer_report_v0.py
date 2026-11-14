# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded source-to-report projection of publicly named Berlin insurance accounts.

This is an insurer-agnostic report *evidence index*, not property exposure, an
insurance coverage schedule, an insured location map or a CAT model input.
Source rows are existing, manually reviewed official-government observations;
the export does not download source bytes, verify external PDFs or invent data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/observations/rva_berlin_senate_housing_insurer_relations_2025_v0.toml"
RVA = "R+V Allgemeine Versicherung AG"
EXPECTED_SCHEMA = "BERLIN_SENATE_2025_PUBLIC_HOUSING_BUILDING_INSURER_RELATIONSHIPS_V0"
EXPECTED_URL = "https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-22033.pdf"
ALLOWED_RELATIONS = {
    "named_member_of_coinsurance_consortium",
    "named_building_insurance_contract_counterparty",
    "other_insurers_named_no_rva_named",
}
UNOBSERVED = (
    "risk_addresses_known",
    "insured_building_count_known",
    "covered_property_tiv_known",
    "carrier_2026_still_current_confirmed",
    "individual_building_is_separate_insurance_contract",
)


def fail(reason: str) -> None:
    raise ValueError(reason)


def project(source: dict, *, source_sha256: str) -> dict:
    if (source.get("schema_version") != EXPECTED_SCHEMA
            or source.get("source_official_url") != EXPECTED_URL
            or source.get("source_document_number") != "Drucksache 19/22033"
            or source.get("source_statement_date") != "2025-04-01"
            or source.get("source_page_pdf_zero_based_for_relationships") != 2
            or source.get("policy_structure")
            != "building_insurance_overarching_blanket_company_contract_not_one_policy_per_building"):
        fail("Berlin Senate insurer evidence provenance/scope changed")

    if (source.get("public_named_berlin_housing_entities") != 6
            or source.get("confirmed_rva_named_housing_company_count") != 3
            or source.get("no_rva_named_other_insurer_company_count") != 3
            or source.get("company_2026_renewal_or_current_carrier_observed") is not False
            or source.get("degewo_rva_coinsurance_fraction_observed") is not False
            or source.get("model_real_rva_exposure_site_admitted") is not False):
        fail("unknown coverage, company or carrier scope was promoted to observation")

    companies = source.get("housing_companies")
    if not isinstance(companies, list) or len(companies) != 6:
        fail("expected six named public housing corporation observations")

    seen_companies: set[str] = set()
    edges = []
    named_rva = 0
    comparators = 0
    for company in companies:
        if not isinstance(company, dict):
            fail("malformed named company observation")
        corporate = company.get("legal_name")
        if not isinstance(corporate, str) or not corporate.strip() or corporate in seen_companies:
            fail("blank or duplicate corporate account")
        seen_companies.add(corporate)
        labels = company.get("named_insurers")
        if (not isinstance(labels, list) or not labels
                or any(not isinstance(label, str) or not label.strip() for label in labels)
                or len(set(labels)) != len(labels)):
            fail("missing or duplicate insurer labels")
        relation = company.get("insurance_relation_type")
        if relation not in ALLOWED_RELATIONS:
            fail("unknown relationship type")
        is_rva = RVA in labels
        if company.get("rva_allgemeine_explicitly_named") is not is_rva:
            fail("R+V statement contradicts the original named-insurer labels")
        if company.get("other_insurer_comparator") is not (not is_rva):
            fail("other-insurer comparator incorrectly classified")
        if company.get("source_question_number") != 2 or company.get("carrier_observation_date") != "2025-04-01":
            fail("carrier observation no longer from Senate Q2 dated April 2025")
        if any(company.get(field) is not False for field in UNOBSERVED):
            fail("unobserved insured building, TIV, site, contract or 2026 carrier claim")
        if relation == "named_member_of_coinsurance_consortium":
            if len(labels) < 2 or not is_rva or company.get("legal_name") != "degewo AG":
                fail("consortium attribution or carrier sharing changed")
        elif relation == "named_building_insurance_contract_counterparty":
            if len(labels) != 1 or not is_rva:
                fail("direct R+V named account misclassified")
        elif is_rva:
            fail("comparator incorrectly includes R+V")
        named_rva += int(is_rva)
        comparators += int(not is_rva)
        for label in labels:
            edges.append({
                "reported_carrier_label": label,
                "carrier_identity_leicode_verified": False,
                "reported_corporate_account": corporate,
                "relationship_date": "2025-04-01",
                "relationship_evidence_class": (
                    "named_member_of_consortium" if relation == "named_member_of_coinsurance_consortium"
                    else "named_building_insurance_provider"
                ),
                "member_of_insurer_consortium_explicitly_reported": (
                    relation == "named_member_of_coinsurance_consortium"
                ),
                "individual_insured_buildings_observed": False,
                "insured_asset_tiv_observed": False,
                "carrier_share_or_cession_observed": False,
                "carrier_current_as_of_2026_confirmed": False,
            })
    if (named_rva != 3 or comparators != 3 or len(edges) != 8
            or len({x["reported_carrier_label"] for x in edges}) != 5):
        fail("published named carrier-account relationships no longer reconcile")

    edges.sort(key=lambda e: (e["reported_carrier_label"], e["reported_corporate_account"]))
    labels = sorted({e["reported_carrier_label"] for e in edges})
    return {
        "schema_version": "PUBLIC_NAMED_CORPORATE_INSURANCE_ACCOUNT_REPORT_V0",
        "source": {
            "publisher_original_document": EXPECTED_URL,
            "document_reference": "Drucksache 19/22033, question 2",
            "reported_date": "2025-04-01",
            "typed_research_observation_sha256": source_sha256,
            "original_pdf_bytes_verified_by_this_export": False,
        },
        "research_only_not_admitted": True,
        "named_corporate_accounts_count": 6,
        "named_carrier_account_associations_count": len(edges),
        "carrier_label_count": len(labels),
        "reported_carrier_labels": labels,
        "carrier_account_edges": edges,
        "unresolved": [
            "This is named company insurance, not a schedule of individually insured buildings or policies.",
            "Contract period and 2026 renewal are unknown; do not present the insurer as currently covering the company.",
            "Actual property coverage, location, sums insured, insurer TIV and treaty shares are not observed.",
            "A competitor named for a company does not prove the absence of all R+V coverage or exclusive coverage.",
            "Original carrier labels are not crosswalked to LEI identifiers; no group/solo aggregation.",
            "Consortium co-insurance percentages, limits and deductible information are unknown.",
        ],
    }


def read_and_project(path: Path = SOURCE) -> dict:
    raw = path.read_bytes()
    if len(raw) > 256_000:
        fail("unbounded source observation")
    data = tomllib.loads(raw.decode("utf-8"))
    return project(data, source_sha256=hashlib.sha256(raw).hexdigest())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=SOURCE)
    args = p.parse_args(argv)
    try:
        print(json.dumps(read_and_project(args.source), sort_keys=True,
                         ensure_ascii=False, indent=2))
    except (OSError, ValueError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
