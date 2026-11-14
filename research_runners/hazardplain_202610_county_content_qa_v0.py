# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only, release-pinned county content QA for three Hazard Plain CSVs.

No source bytes, county rows, individual FIPS, modeled-loss amounts or policy
data are persisted or emitted. This is research QA, NOT admission, calibration,
an independent empirical holdout or an insurance model run. Missing and
implausible numeric values are *counted*, not silently imputed or rescaled.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import io
import json
import re
import sys

from research_runners.hazardplain_202610_manifest_preflight_v0 import EXPECTED_FILES
from research_runners.hazardplain_202610_original_csv_receipt_v0 import (
    OriginalCSVError, fetch_original, fetch_official_manifest,
    validate_pinned_manifest, verify_original_csv,
)

NRI = "national/nri_county_hazard.csv"
EAL = "national/eal_outliers.csv"
NFIP = "national/b2c_county.csv"
NUMERIC_FIELDS = {
    NRI: ("eal_total", "eal_b", "eal_a", "exp_total", "exp_b", "exp_a", "afreq"),
    EAL: ("eal_total", "exp_total", "neighbor_median_eal", "ratio_to_neighbors",
          "rate", "rate_ratio", "se_damage_usd"),
    NFIP: ("fma_rl", "fma_srl", "nfip_rl", "nfip_srl", "any_category",
           "mitigated", "insured", "single_family_any_category",
           "non_residential_any_category", "unassigned", "member_not_listed_here"),
}
COUNT_FIELDS = frozenset(NUMERIC_FIELDS[NFIP])
KEY_SHAPE = re.compile(r"[0-9]{5}\Z")


class CountyQualityError(ValueError):
    """The pinned original or bounded county quality contract is inconsistent."""


def _numeric_class(value: str, *, integer: bool) -> str:
    if value.strip() == "":
        return "blank"
    try:
        number = Decimal(value.strip())
    except InvalidOperation:
        return "nonnumeric"
    if not number.is_finite():
        return "nonfinite"
    if integer and number != number.to_integral_value():
        return "noninteger"
    if number < 0:
        return "negative"
    if number == 0:
        return "zero"
    return "positive"


def _boolean_class(value: str) -> str:
    token = value.strip().lower()
    if token in ("true", "1", "yes"): return "true"
    if token in ("false", "0", "no"): return "false"
    if token in ("", "null", "na", "n/a"): return "missing"
    return "other"


def inspect_county_table(path: str, raw: bytes, *,
                         expected_columns: list[str], expected_rows: int,
                         expected_bytes: int, expected_sha256: str) -> tuple[dict, dict]:
    """Return a public aggregate QA receipt and PRIVATE in-memory join keys.

    Never serialise the second return object: it contains individual county
    and (county, hazard) identifiers solely for bounded cross-table checks.
    """
    if path not in NUMERIC_FIELDS:
        raise CountyQualityError("unsupported county quality table")
    original = verify_original_csv(
        raw, expected_bytes=expected_bytes, expected_sha256=expected_sha256,
        expected_rows=expected_rows, expected_columns=expected_columns)
    header = set(original["header_columns_verified"])
    required = {"stcofips"}
    if path != NFIP:
        required.add("hazard")
    if not required.issubset(header):
        raise CountyQualityError("required spatial/peril keys missing")
    numeric_names = [name for name in NUMERIC_FIELDS[path] if name in header]
    numeric_counts = {name: Counter() for name in numeric_names}
    fips = set()
    pairs = set()
    hazard_categories = set()
    hazard_per_fips = defaultdict(set)
    problems = Counter()
    flags = Counter()
    applicability_eal_joint = Counter()
    ages = set()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    for record in reader:
        code = record["stcofips"].strip()
        if not KEY_SHAPE.fullmatch(code):
            problems["invalid_five_digit_county_key"] += 1
            # Deliberately do not emit or retain the malformed identifier.
            continue
        if path == NFIP:
            if code in fips:
                problems["duplicate_county_key"] += 1
        else:
            hazard = record["hazard"].strip()
            if not hazard:
                problems["blank_hazard"] += 1
            elif len(hazard) > 80:
                problems["unbounded_hazard_label"] += 1
            else:
                pair = (code, hazard)
                if pair in pairs:
                    problems["duplicate_county_peril_key"] += 1
                pairs.add(pair)
                hazard_categories.add(hazard)
                hazard_per_fips[code].add(hazard)
        fips.add(code)
        for name in numeric_names:
            kind = _numeric_class(record[name], integer=name in COUNT_FIELDS)
            numeric_counts[name][kind] += 1
        if path == NRI and "applicable" in header:
            applicable = _boolean_class(record["applicable"])
            flags["nri_applicable_" + applicable] += 1
            # Cross-tab blanks with applicability before interpreting a
            # missing modeled EAL as zero or as an actionable data defect.
            applicability_eal_joint[
                "applicable_" + applicable + "__eal_" +
                _numeric_class(record["eal_total"], integer=False)
            ] += 1
        if path == EAL and "outlier" in header:
            flags["eal_outlier_" + _boolean_class(record["outlier"])] += 1
        if path == NFIP and "as_of_date" in header:
            date = record["as_of_date"].strip()
            if not date:
                problems["missing_nfip_source_as_of"] += 1
            elif len(date) > 40:
                problems["bad_nfip_source_as_of_length"] += 1
            else:
                ages.add(date)
    report = {
        "table": EXPECTED_FILES[path]["table"],
        "source_sha256_verified": original["original_sha256_computed"],
        "rows_verified": original["record_count_verified"],
        "unique_five_digit_county_keys": len(fips),
        "invalid_or_duplicate_key_counters": dict(sorted(problems.items())),
        "numeric_field_counts": {name: dict(sorted(c.items()))
                                 for name, c in sorted(numeric_counts.items())},
        "categorical_flag_counts": dict(sorted(flags.items())),
        "nri_applicability_vs_eal_status": (
            dict(sorted(applicability_eal_joint.items())) if path == NRI else None
        ),
        "distinct_hazard_categories": len(hazard_categories) if path != NFIP else None,
        "county_hazard_pairs": len(pairs) if path != NFIP else None,
        "counties_with_exactly_18_distinct_hazards": (
            sum(len(v) == 18 for v in hazard_per_fips.values()) if path == NRI else None
        ),
        "distinct_source_as_of_labels": len(ages) if path == NFIP else None,
        "data_values_or_county_identifiers_emitted": False,
        "numerical_outliers_corrected": False,
        "source_content_model_admitted": False,
    }
    return report, {"fips": fips, "pairs": pairs}


def evaluate_original_quality(*, manifest_fetch=fetch_official_manifest,
                              data_fetch=fetch_original) -> dict:
    """Exact identity checks precede every aggregate content profile."""
    tables = validate_pinned_manifest(manifest_fetch())
    reports = []
    private = {}
    for path, expected in sorted(EXPECTED_FILES.items()):
        table = tables.get(expected["table"])
        if not table or type(table.get("columns")) is not list:
            raise CountyQualityError("original provider table metadata missing")
        report, keys = inspect_county_table(
            path, data_fetch(path), expected_columns=table["columns"],
            expected_rows=expected["rows"], expected_bytes=expected["bytes"],
            expected_sha256=expected["sha256"])
        reports.append(report)
        private[path] = keys
    a = private[NRI]; b = private[EAL]; c = private[NFIP]
    cross = {
        "nri_counties_not_in_nfip_county_base": len(a["fips"] - c["fips"]),
        "nfip_counties_not_in_nri_county_base": len(c["fips"] - a["fips"]),
        "outlier_pairs_missing_from_nri_county_hazard": len(b["pairs"] - a["pairs"]),
        "outlier_counties_missing_from_nri_county_base": len(b["fips"] - a["fips"]),
        "counties_present_in_all_three_tables": len(a["fips"] & b["fips"] & c["fips"]),
        "geography_vintage_or_fips_reclassification_independently_verified": False,
    }
    # Source IDs stay private; no log includes the actual FIPS or per-site risk.
    return {
        "status": "ORIGINAL_CSV_CONTENT_AGGREGATE_RESEARCH_QA_ONLY",
        "release": "2026-10",
        "tables": reports,
        "cross_table_counts": cross,
        "original_bytes_verified_before_content_scan": True,
        "nfip_repetitive_class_counts_are_not_disjoint": True,
        "nri_modeled_eal_is_not_an_independent_insurer_claim": True,
        "raw_rows_or_individual_county_keys_emitted": False,
        "numeric_fixes_or_imputation_performed": False,
        "scientific_independence_established": False,
        "rights_reviewed_and_model_admitted": False,
        "insured_loss_or_aep_oep_generated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-live", action="store_true", required=True)
    parser.parse_args()
    try:
        print(json.dumps(evaluate_original_quality(), indent=2, sort_keys=True))
    except (OSError, TimeoutError, OriginalCSVError, CountyQualityError) as exc:
        print("BLOCKED: " + str(exc)[:150], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
