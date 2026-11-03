# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed local preflight for an issuer's solo gross-written-premium table.

The input is a *private, analyst-transcribed* source table plus exact local PDF
bytes. Neither the input nor original source bytes belongs in public Git.
Matching the PDF SHA proves only a *local byte fingerprint*, not that someone
has correctly transcribed the PDF or cleared its licence. No insured TIV,
physical risk location, treaty or CAT model input can result from this audit.

Example (private file paths only):
 python research_runners/solo_insurer_gwp_control_v0.py \
   --report-pdf /private/issuer-annual-report.pdf \
   --rows-json /private/issuer-normalized-gwp.json
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit


class GWPControlError(ValueError):
    """A declared reporting scope or an arithmetic/source gate failed."""


_NUMBER = re.compile(r"(?:0|[1-9][0-9]{0,14})(?:\.[0-9]{1,2})?\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_CODE = re.compile(r"[A-Z][A-Z0-9_]{1,63}\Z")
_DENIED_QUERY = {"token", "api_key", "apikey", "access_token", "sig",
                 "signature", "key", "secret", "authorization", "credential"}
_SOURCE_FIELDS = {"issuer_report_url", "original_pdf_sha256", "pdf_page_zero_based",
                  "reporting_basis", "legal_entity_scope", "currency", "amount_unit"}
_INPUT_FIELDS = {"schema_version", "input_class", "reporting_date", "issuer_key",
                 "premium_measure", "country_location_evidence", "source",
                 "direct_lob_rows", "reported_direct_total",
                 "reported_assumed_total", "reported_combined_total"}


def _money(value: object, name: str) -> Decimal:
    if not isinstance(value, str) or not _NUMBER.fullmatch(value):
        raise GWPControlError(f"{name}: use a nonnegative plain decimal string, at most 2 decimal places")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise GWPControlError(f"{name}: invalid monetary value") from exc
    if not result.is_finite():
        raise GWPControlError(f"{name}: non-finite monetary value")
    return result


def _safe_source_url(url: object) -> None:
    if not isinstance(url, str) or any(c.isspace() for c in url):
        raise GWPControlError("source URL is missing/unsafe")
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        parsed.port
    except ValueError as exc:
        raise GWPControlError("malformed source URL") from exc
    if (parsed.scheme != "https" or not host or parsed.username is not None
            or parsed.password is not None or host == "localhost"
            or host.endswith((".local", ".internal", ".localhost"))):
        raise GWPControlError("source URL requires a public HTTPS host")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None and not ip.is_global:
        raise GWPControlError("source URL cannot be a private IP")
    if any(k.casefold() in _DENIED_QUERY for k, _v in parse_qsl(parsed.query)):
        raise GWPControlError("source URL contains a credential parameter")


def validate_solo_gwp(raw: dict, pdf_bytes: bytes) -> dict:
    """Reconcile only the declared solo HGB/GAAP *written* premium universe.

    All joint geographic/LoB cells remain unknown even after successful
    reconciliation. Separate assumed reinsurance is NOT direct insurance.
    """
    if not isinstance(raw, dict) or set(raw) != _INPUT_FIELDS:
        raise GWPControlError("invalid v0 input schema")
    if raw["schema_version"] != "0.1.0" or raw["input_class"] != "research_only_manual_transcription":
        raise GWPControlError("only manually transcribed research input is accepted")
    if raw["premium_measure"] != "gross_written_premium":
        raise GWPControlError("earned, net, claims or TIV cannot enter written premium audit")
    if raw["country_location_evidence"] != "not_proven_by_this_report":
        raise GWPControlError("premium line table cannot establish risk situs")
    if not isinstance(raw["issuer_key"], str) or not _CODE.fullmatch(raw["issuer_key"]):
        raise GWPControlError("issuer key must be an unambiguous internal code")
    period = raw["reporting_date"]
    if not isinstance(period, str):
        raise GWPControlError("reporting_date must be YYYY-MM-DD")
    try:
        if date.fromisoformat(period).isoformat() != period or not period.endswith("-12-31"):
            raise ValueError("not canonical year end")
    except ValueError as exc:
        raise GWPControlError("reporting_date must be a valid December 31 year-end") from exc
    source = raw["source"]
    if not isinstance(source, dict) or set(source) != _SOURCE_FIELDS:
        raise GWPControlError("invalid original-PDF source identity")
    _safe_source_url(source["issuer_report_url"])
    if source["reporting_basis"] != "local_statutory_gaap":
        raise GWPControlError("do not mix Solvency II/IFRS/GAAP bases")
    if source["legal_entity_scope"] != "solo":
        raise GWPControlError("group and solo figures cannot be reconciled together")
    if source["currency"] != "EUR" or source["amount_unit"] != "thousand_eur":
        raise GWPControlError("this bounded v0 supports only reported EUR thousands")
    page = source["pdf_page_zero_based"]
    if not isinstance(page, int) or isinstance(page, bool) or page < 0 or page > 2000:
        raise GWPControlError("source page must be an explicit zero-based PDF page")
    sha = source["original_pdf_sha256"]
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise GWPControlError("missing valid original-PDF SHA-256")
    if (not isinstance(pdf_bytes, bytes) or len(pdf_bytes) < 12 or
            len(pdf_bytes) > 100_000_000 or not pdf_bytes.startswith(b"%PDF-") or
            b"%%EOF" not in pdf_bytes[-2048:]):
        raise GWPControlError("a bounded locally held PDF is required")
    observed_sha = hashlib.sha256(pdf_bytes).hexdigest()
    if observed_sha != sha:
        raise GWPControlError("original-PDF digest does not match declared source")

    rows = raw["direct_lob_rows"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 200:
        raise GWPControlError("expected 1..200 atomic direct LoB rows")
    codes: set[str] = set()
    direct_sum = Decimal(0)
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"lob_code", "gross_written"}:
            raise GWPControlError("each direct LoB requires code and gross_written only")
        code = row["lob_code"]
        if not isinstance(code, str) or not _CODE.fullmatch(code) or code in codes:
            raise GWPControlError("duplicate or invalid direct LoB code")
        codes.add(code)
        direct_sum += _money(row["gross_written"], f"{code}/gross_written")

    direct = _money(raw["reported_direct_total"], "reported_direct_total")
    assumed = _money(raw["reported_assumed_total"], "reported_assumed_total")
    combined = _money(raw["reported_combined_total"], "reported_combined_total")
    if direct != direct_sum:
        raise GWPControlError("direct LoB values do not sum to reported direct total")
    if direct + assumed != combined:
        raise GWPControlError("reported direct plus separately assumed does not equal combined")
    if combined <= 0:
        raise GWPControlError("empty premium universe cannot be used")

    return {
        "schema_version": "0.1.0",
        "issuer_key": raw["issuer_key"],
        "reporting_date": period,
        "original_local_pdf_sha256": observed_sha,
        "pdf_source_page_zero_based": page,
        "lob_row_count": len(codes),
        "line_and_direct_assumed_totals_conserved": True,
        "source_fingerprint_matches_local_pdf": True,
        "extraction_verified_against_pdf_visuals": False,
        "original_issuer_authenticity_independently_verified": False,
        "rights_and_scientific_review_complete": False,
        "reported_country_by_lob_observed": False,
        "geolocated_insured_assets_observed": False,
        "insurance_tiv_observed": False,
        "underwriting_risk_bearer_net_position_observed": False,
        "model_input_approved": False,
        "reason": "local_arithmetic_only_no_independent_source_rights_geography_or_insured_tiv"
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-pdf", type=Path, required=True)
    parser.add_argument("--rows-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.rows_json.stat().st_size > 2_000_000 or args.report_pdf.stat().st_size > 100_000_000:
            raise GWPControlError("input too large")
        raw = json.loads(args.rows_json.read_text(encoding="utf-8"))
        result = validate_solo_gwp(raw, args.report_pdf.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError, GWPControlError) as exc:
        parser.exit(status=2, message=f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
