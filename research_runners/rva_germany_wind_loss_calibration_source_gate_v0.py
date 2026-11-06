# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed German wind loss calibration source eligibility (metadata only).

Do not download, mine, redistribute, fit, reweight or join any external
GDV/EIOPA/HANZE/EEA/C3S observations. This is a *metadata* and licensing
admission gate; code does not contain or execute data-acquisition logic.
All six research candidates are currently reference-only or physical
geography-only. No individual R+V claims, vulnerability fit or annual EP.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import tomllib
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "research/observations/rva_germany_wind_loss_calibration_source_register_v0.toml"
SCHEMA = "RVA_GERMANY_WIND_LOSS_CALIBRATION_SOURCE_REGISTER_V0"
EXPECTED = {
    "gdv_naturgefahrenreport_2026": (
        "www.gdv.de", "ACTUAL_AGGREGATED_INSURED_CLAIMS_AND_CLAIM_COUNTS",
        "NO_AUTOMATED_TEXT_AND_DATA_MINING_WITHOUT_GDV_EXPLICIT_CONSENT",
        "REFERENCE_ONLY",
    ),
    "eiopa_catastrophe_data_hub_2023": (
        "www.eiopa.europa.eu", "ACTUAL_PARTIAL_MARKET_INSURED_BUILDING_LOSS_AND_EXPOSURE_AGGREGATES",
        "DATASET_SPECIFIC_REUSE_AND_WORKBOOK_PROVENANCE_NOT_VERIFIED",
        "REFERENCE_ONLY",
    ),
    "hanze_european_windstorm_impacts_v1_2025": (
        "zenodo.org", "MIXED_REPORTED_ECONOMIC_HUMAN_FORESTRY_INFRASTRUCTURE_IMPACTS",
        "ZENODO_RECORD_DISPLAYS_EMPTY_LICENSE_FIELD_REVIEW_REQUIRED",
        "REFERENCE_ONLY",
    ),
    "c3s_european_windstorm_tier3_reanalysis": (
        "cds.climate.copernicus.eu", "MODELED_BUILDING_DAMAGE_NOT_OBSERVED_INSURED_CLAIMS",
        "ODBL_OSM_DERIVATIVE_AND_COPERNICUS_PRODUCT_RIGHTS_REQUIRE_REVIEW",
        "REFERENCE_ONLY",
    ),
    "eea_1980_2023_economic_insured_catdat": (
        "sdi.eea.europa.eu", "AGGREGATED_MIXED_ECONOMIC_AND_INSURED_CLIMATE_LOSSES",
        "UNDERLYING_CATDAT_INSTITUTIONAL_AGREEMENT_REUSE_NOT_CONFIRMED",
        "REFERENCE_ONLY",
    ),
    "nrw_hu22_2022_building_footprints": (
        "www.opengeodata.nrw.de", "ACTUAL_PUBLIC_GEOMETRY_ONLY_NO_OBSERVED_INSURANCE_LOSS",
        "PRODUCT_YEAR_SPECIFIC_NRW_HU2022_REUSE_METADATA_STILL_TO_CONFIRM",
        "SOURCE_REPLAY_ONLY_NOT_AS_LOSS_CALIBRATION",
    ),
}
FIELDS = {
    "id", "publisher", "label", "landing_url", "rights_url", "period",
    "observed_measure", "hazard_specificity", "granularity", "denominator",
    "licence_review", "lineage", "access", "source_file_sha256",
    "approval_evidence", "limitations",
}
ROOT_FIELDS = {
    "schema", "as_of", "purpose", "all_sources_reference_only_or_source_replay",
    "independent_German_wind_damage_calibration_completed",
    "actual_RV_policy_geography_or_claims_observed",
    "loss_frequency_per_year_model_admitted",
    "gross_net_annual_OEP_AEP_admitted", "required_before_any_loss_fit",
    "records",
}
REQUIRED_GATES = {
    "source_specific_licensed_reuse_or_manual_permission",
    "event_wind_only_intensity_and_matching_time_height_duration",
    "event_loss_observed_vs_economic_or_simulated_classification",
    "exposure_denominator_and_carrier_sample_coverage",
    "geographic_and_date_granularity_match_and_out_of_sample_holdout",
    "insurance_contract_policy_limits_deductibles_and_covered_perils",
    "independent_scientific_review_and_explicit_owner_model_admission",
}


class SourceRightsBlocked(ValueError):
    """Source research reference may not be promoted to accepted calibration data."""


def validate_registry(doc: dict) -> dict:
    if not isinstance(doc, dict) or set(doc) != ROOT_FIELDS:
        raise SourceRightsBlocked("source register top-level schema incomplete/unknown")
    if (
        doc["schema"] != SCHEMA or doc["as_of"] != "2026-11-06"
        or doc["all_sources_reference_only_or_source_replay"] is not True
        or doc["independent_German_wind_damage_calibration_completed"] is not False
        or doc["actual_RV_policy_geography_or_claims_observed"] is not False
        or doc["loss_frequency_per_year_model_admitted"] is not False
        or doc["gross_net_annual_OEP_AEP_admitted"] is not False
    ):
        raise SourceRightsBlocked("unsupported factual/scientific model-promotion claim")
    gates = doc["required_before_any_loss_fit"]
    if not isinstance(gates, list) or len(gates) != len(REQUIRED_GATES) or set(gates) != REQUIRED_GATES:
        raise SourceRightsBlocked("required licence, denominator or modelling gates removed")
    records = doc["records"]
    if not isinstance(records, list) or len(records) != len(EXPECTED):
        raise SourceRightsBlocked("expected six independently attributed source families")
    seen = set()
    kinds = Counter()
    for src in records:
        if not isinstance(src, dict) or set(src) != FIELDS:
            raise SourceRightsBlocked("unrecognized source rights metadata fields")
        sid = src["id"]
        if sid not in EXPECTED or sid in seen:
            raise SourceRightsBlocked("unrecognized or duplicated source identifier")
        seen.add(sid)
        hostname, measure, rights, access = EXPECTED[sid]
        if (
            src["observed_measure"] != measure
            or src["licence_review"] != rights
            or src["access"] != access
            or src["approval_evidence"] not in ("NONE", "SOURCE_ONLY_CI_42246960507")
            or len(src["limitations"]) < 30
            or len(src["denominator"]) < 18
            or not src["granularity"]
            or not src["lineage"]
            or not src["period"]
        ):
            raise SourceRightsBlocked("source lost one of its explicit no-calibration legal/method boundaries")
        for urlfield in ("landing_url", "rights_url"):
            url = src[urlfield]
            parsed = urlparse(url)
            if (
                parsed.scheme != "https" or not parsed.netloc
                or parsed.username or parsed.password or parsed.fragment
                or parsed.hostname is None
                or not re.fullmatch(r"[a-z0-9.\-]+", parsed.hostname)
                or len(url) > 600
            ):
                raise SourceRightsBlocked("source URL not a canonical HTTPS reference")
        if urlparse(src["landing_url"]).hostname != hostname:
            raise SourceRightsBlocked("source host is not the verified original publisher")
        if sid == "nrw_hu22_2022_building_footprints":
            if (
                src["source_file_sha256"] !=
                "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da"
                or src["approval_evidence"] != "SOURCE_ONLY_CI_42246960507"
            ):
                raise SourceRightsBlocked("authentic original HU22 source/rights receipt drift")
        elif src["source_file_sha256"] != "NOT_ACQUIRED" or src["approval_evidence"] != "NONE":
            raise SourceRightsBlocked("unfetched or unlicensed external observations claimed imported")
        kinds[src["observed_measure"]] += 1
    if seen != set(EXPECTED):
        raise SourceRightsBlocked("source population incomplete")
    return {
        "status": "ALL_SIX_CALIBRATION_SOURCES_REFERENCE_ONLY_NO_MODEL_FIT",
        "source_count": len(seen),
        "observed_partial_insurer_sample_sources": sum(
            n for kind, n in kinds.items() if kind.startswith("ACTUAL_PARTIAL_MARKET")
        ),
        "recorded_GDV_TDM_permission": False,
        "German_site_specific_GUL_vulnerability_fit_approved": False,
        "annual_OEP_AEP_return_frequency_estimated": False,
        "external_workbook_original_bytes_ingested": False,
        "licence_or_data_reuse_approval_inferred": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-register", type=Path, default=DEFAULT)
    p = parser.parse_args()
    try:
        if p.source_register.is_symlink() or p.source_register.stat().st_size > 80_000:
            raise SourceRightsBlocked("source register path is untrusted")
        doc = tomllib.loads(p.source_register.read_text(encoding="utf-8"))
        report = validate_registry(doc)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, tomllib.TOMLDecodeError, SourceRightsBlocked, TypeError, KeyError, AttributeError) as exc:
        parser.exit(2, "WIND_CALIBRATION_SOURCE_RIGHTS_BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
