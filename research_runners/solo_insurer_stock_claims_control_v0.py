# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only extension: reconcile contract stock, reported claims and written GWP.

Consumes only operator-local, manually transcribed exact issuer inputs and the
original PDF bytes. Never counts a subtotal and its children twice. Annual
gross *written* premium divided by *year-end* contract stock is NOT a tariff
rate; annual reported claims divided by stock is NOT actuarial claim frequency.
The population is contracts, not unique insured physical buildings.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re

from solo_insurer_gwp_control_v0 import GWPControlError, validate_solo_gwp

_CODE = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")
_MAX_ROWS = 200
_MAX_COUNT = 10**15 - 1
_INPUT_FIELDS = {
    "schema_version", "input_class", "issuer_key", "reporting_date",
    "contract_population", "claims_population", "risk_situs_evidence",
    "stock_pdf_page_zero_based", "lob_stock_rows", "rollup_checks",
}
_STOCK_FIELDS = {"lob_code", "year_end_contracts", "reported_claims"}
_ROLLUP_FIELDS = {
    "rollup_code", "child_lob_codes", "gross_written_thousand_eur",
    "year_end_contracts", "reported_claims",
}


def _count(value: object, label: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]{0,14})\Z", value):
        raise GWPControlError(f"{label}: expected nonnegative integer as decimal string")
    return int(value)


def _written(value: object, label: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]{0,14})(?:\.[0-9]{1,2})?\Z", value):
        raise GWPControlError(f"{label}: expected EUR-thousands gross written plain decimal")
    return Decimal(value)


def validate_solo_stock_claims(
    gwp_control: dict, stock_control: dict, original_pdf_bytes: bytes
) -> dict:
    """Make one dated PDF identity and three independent non-promoting checks.

    A population containing only selected lines is valid for targeted
    research, but no all-business aggregate is inferred from that subset.
    """
    gwp_receipt = validate_solo_gwp(gwp_control, original_pdf_bytes)
    if not isinstance(stock_control, dict) or set(stock_control) != _INPUT_FIELDS:
        raise GWPControlError("invalid solo contract/claim research control schema")
    if (stock_control["schema_version"] != "0.1.0"
            or stock_control["input_class"] != "research_only_manual_transcription"):
        raise GWPControlError("only manual research table observations are allowed")
    if (stock_control["issuer_key"] != gwp_receipt["issuer_key"]
            or stock_control["reporting_date"] != gwp_receipt["reporting_date"]):
        raise GWPControlError("legal entity or financial/reporting period mismatch")
    if stock_control["contract_population"] != "at_least_one_year_contracts_at_year_end":
        raise GWPControlError("contract population must be explicitly scoped")
    if stock_control["claims_population"] != "all_reported_claims_for_reporting_year":
        raise GWPControlError("claims are reported all-peril incidents, not CAT losses")
    if stock_control["risk_situs_evidence"] != "not_observed":
        raise GWPControlError("country/district and building locations are not observed")
    page = stock_control["stock_pdf_page_zero_based"]
    if not isinstance(page, int) or isinstance(page, bool) or not 0 <= page <= 2000:
        raise GWPControlError("invalid zero-based stock-table PDF page")
    if page == gwp_control["source"]["pdf_page_zero_based"]:
        raise GWPControlError("stock and annual premium source pages must be separately identified")

    direct = {
        line["lob_code"]: _written(line["gross_written"], line["lob_code"])
        for line in gwp_control["direct_lob_rows"]
    }
    raw_rows = stock_control["lob_stock_rows"]
    if not isinstance(raw_rows, list) or not 1 <= len(raw_rows) <= _MAX_ROWS:
        raise GWPControlError("stock rows must contain 1..200 source-matched lines")
    rows = {}
    for entry in raw_rows:
        if not isinstance(entry, dict) or set(entry) != _STOCK_FIELDS:
            raise GWPControlError("invalid source-matched stock row")
        key = entry["lob_code"]
        if not isinstance(key, str) or not _CODE.fullmatch(key) or key not in direct or key in rows:
            raise GWPControlError("unmatched or duplicated stock LoB")
        stock = _count(entry["year_end_contracts"], f"{key}/year_end_contracts")
        claims = _count(entry["reported_claims"], f"{key}/reported_claims")
        rows[key] = {"year_end_contracts": stock, "reported_claims": claims}

    raw_rollups = stock_control["rollup_checks"]
    if not isinstance(raw_rollups, list) or len(raw_rollups) > len(raw_rows):
        raise GWPControlError("invalid LoB subtotal challenge list")
    rollup_names = set()
    used_children = set()
    summaries = []
    for roll in raw_rollups:
        if not isinstance(roll, dict) or set(roll) != _ROLLUP_FIELDS:
            raise GWPControlError("invalid independent subtotal challenge")
        name = roll["rollup_code"]
        if not isinstance(name, str) or not _CODE.fullmatch(name) or name in rollup_names or name in direct:
            raise GWPControlError("invalid rollup identity or subtotal counted as direct atomic LoB")
        rollup_names.add(name)
        children = roll["child_lob_codes"]
        if not isinstance(children, list) or len(children) < 2 or len(children) > len(rows):
            raise GWPControlError("rollup needs at least two direct atomic LoBs")
        if (any(not isinstance(c, str) for c in children) or len(set(children)) != len(children)
                or any(c not in rows for c in children)):
            raise GWPControlError("rollup children duplicate, unknown or without stock observations")
        if any(c in used_children for c in children):
            raise GWPControlError("overlapping rollup groups could double-count a child")
        used_children.update(children)
        observed_gwp = _written(roll["gross_written_thousand_eur"], f"{name}/gwp")
        observed_stock = _count(roll["year_end_contracts"], f"{name}/stock")
        observed_claims = _count(roll["reported_claims"], f"{name}/claims")
        if sum((direct[c] for c in children), Decimal(0)) != observed_gwp:
            raise GWPControlError(f"{name}: gross written premium subtotal mismatch")
        if sum(rows[c]["year_end_contracts"] for c in children) != observed_stock:
            raise GWPControlError(f"{name}: year-end contract subtotal mismatch")
        if sum(rows[c]["reported_claims"] for c in children) != observed_claims:
            raise GWPControlError(f"{name}: annual reported-claim subtotal mismatch")
        summaries.append({
            "rollup_code": name, "child_lob_count": len(children),
            "three_independent_marginals_conserved": True,
        })

    # Ratios use distinct periods/denominators, and are deliberately NOT
    # labelled average insurance premium, rate, event frequency or CAT claim.
    ratios = []
    for key in sorted(rows):
        stock = rows[key]["year_end_contracts"]
        premium = direct[key] * Decimal(1000)
        ratios.append({
            "lob_code": key,
            "annual_written_eur_per_year_end_contract_reference": (
                str((premium / stock).quantize(Decimal("0.01"))) if stock else None
            ),
            "reported_claims_per_year_end_contract_reference": (
                str((Decimal(rows[key]["reported_claims"]) / stock).quantize(Decimal("0.000001")))
                if stock else None
            ),
            "real_tariff_or_actuarial_frequency": False,
        })
    return {
        "schema_version": "0.1.0",
        "input_class": "research_only_manual_transcription",
        "issuer_key": gwp_receipt["issuer_key"],
        "reporting_date": gwp_receipt["reporting_date"],
        "pdf_sha256": gwp_receipt["original_local_pdf_sha256"],
        "premium_pdf_page_zero_based": gwp_receipt["pdf_source_page_zero_based"],
        "stock_pdf_page_zero_based": page,
        "matched_stock_lob_count": len(rows),
        "validated_rollups": summaries,
        "derived_reference_ratios": ratios,
        "source_fingerprint_matches_local_pdf": True,
        "all_issuers_company_country_risk_situs_known": False,
        "geolocated_insured_assets_observed": False,
        "tiv_from_premiums_observed": False,
        "cat_specific_claims_observed": False,
        "rights_and_scientific_review_complete": False,
        "actual_source_transcription_independently_verified": False,
        "model_input_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-pdf", type=Path, required=True)
    parser.add_argument("--gwp-json", type=Path, required=True)
    parser.add_argument("--stock-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        for file_path, limit in (
            (args.gwp_json, 2_000_000), (args.stock_json, 2_000_000),
            (args.report_pdf, 100_000_000)
        ):
            if file_path.stat().st_size > limit:
                raise GWPControlError("local research input exceeds size cap")
        gwp = json.loads(args.gwp_json.read_text("utf-8"))
        stock = json.loads(args.stock_json.read_text("utf-8"))
        out = validate_solo_stock_claims(gwp, stock, args.report_pdf.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError, GWPControlError) as exc:
        parser.exit(status=2, message=f"BLOCKED: {exc}\n")
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
