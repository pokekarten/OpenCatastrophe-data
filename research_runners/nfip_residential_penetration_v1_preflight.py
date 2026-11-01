#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict, offline FEMA NFIP residential-penetration v1 source-byte preflight.

Output is deliberately non-geographic aggregate *diagnostics*, not a county
risk table or insurance input. Does not fetch APIs, copy raw rows or admit data.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ENTITY = "NfipResidentialPenetrationRates"
VERSION = "v1"
MAX_BYTES = 15_000_000
MAX_RECORDS = 10_000
FIPS = re.compile(r"[0-9]{5}\\Z")


class NFIPPenetrationError(ValueError):
    pass


def _strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise NFIPPenetrationError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise NFIPPenetrationError("nonfinite JSON constant")


def _int(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise NFIPPenetrationError(f"{field}: expected nonnegative integer")
    return value


def _ratio(value, field):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise NFIPPenetrationError(f"{field}: invalid decimal")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise NFIPPenetrationError(f"{field}: invalid decimal") from exc
    if not result.is_finite() or result < 0:
        raise NFIPPenetrationError(f"{field}: invalid ratio")
    # FEMA warns that rates may exceed 100% because the denominator is modelled.
    # Never cap to 1 or infer that values > 1 are invalid.
    return result


def validate_original(raw, expected_sha256):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise NFIPPenetrationError("expected sha256 must be lowercase hex")
    if len(raw) > MAX_BYTES:
        raise NFIPPenetrationError("source response exceeds size budget")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise NFIPPenetrationError("source sha256 mismatch")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_pairs,
                         parse_float=Decimal, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NFIPPenetrationError("malformed provider JSON") from exc
    if not isinstance(obj, dict) or not isinstance(obj.get("metadata"), dict):
        raise NFIPPenetrationError("missing provider metadata envelope")
    metadata = obj["metadata"]
    if metadata.get("entityname") != ENTITY or metadata.get("version") != VERSION:
        raise NFIPPenetrationError("wrong FEMA dataset or API version")
    rows = obj.get(ENTITY)
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_RECORDS:
        raise NFIPPenetrationError("invalid or unbounded FEMA response rows")
    if metadata.get("top") is not None:
        top = metadata["top"]
        if isinstance(top, bool) or not isinstance(top, int) or top < len(rows):
            raise NFIPPenetrationError("invalid provider metadata top")
    ids = set()
    geographic_dates = set()
    periods = Counter()
    over_one = Counter()
    null_ratio = Counter()
    missing_structures = Counter()
    zero_structures = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise NFIPPenetrationError("invalid provider row")
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id.strip() or row_id in ids:
            raise NFIPPenetrationError("missing/duplicate ephemeral row id")
        ids.add(row_id)
        fips = row.get("fipsCode")
        if not isinstance(fips, str) or FIPS.fullmatch(fips) is None:
            raise NFIPPenetrationError("invalid 5-digit original county FIPS")
        date_text = row.get("asOfDate")
        if not isinstance(date_text, str) or re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", date_text) is None:
            raise NFIPPenetrationError("invalid asOfDate format")
        try:
            date.fromisoformat(date_text)
        except ValueError as exc:
            raise NFIPPenetrationError("invalid asOfDate") from exc
        key = (fips, date_text)
        if key in geographic_dates:
            raise NFIPPenetrationError("duplicate county and asOfDate")
        geographic_dates.add(key)
        for field in ("state", "county"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 150:
                raise NFIPPenetrationError("missing or malformed administrative label")
        for suffix, cnt, den, rate in (
            ("total", "resContractsInForce", "totalResStructures", "resPenetrationRate"),
            ("sfha", "resContractsInForceSfha", "totalResStructuresSfha",
             "resPenetrationRateSfha"),
        ):
            contracts = row.get(cnt)
            structures = row.get(den)
            # Nulls are missing, not zero. Track separately.
            if contracts is not None:
                _int(contracts, cnt)
            if structures is not None:
                _int(structures, den)
            v = _ratio(row.get(rate), rate)
            if v is None:
                null_ratio[suffix] += 1
            elif v > 1:
                over_one[suffix] += 1
            if structures is None:
                missing_structures[suffix] += 1
            elif structures == 0:
                zero_structures[suffix] += 1
        periods[date_text] += 1
    return {
        "profile": "openfema-nfip-residential-penetration-v1-research-preflight",
        "source_identity": ENTITY,
        "api_version": VERSION,
        "source_sha256": digest,
        "source_byte_count": len(raw),
        "source_record_count": len(rows),
        "record_counts_by_as_of_date": dict(sorted(periods.items())),
        "ratio_over_100pct_counts": dict(sorted(over_one.items())),
        "missing_ratio_counts": dict(sorted(null_ratio.items())),
        "missing_structure_denominator_counts": dict(sorted(missing_structures.items())),
        "zero_structure_denominator_counts": dict(sorted(zero_structures.items())),
        "record_identity_does_not_persist_between_provider_refreshes": True,
        "denominator_is_modelled_nsi_2022_structure_stock": True,
        "includes_private_flood_insurance": False,
        "source_completeness_proven": False,
        "original_geographic_rows_exported": False,
        "model_input_admitted": False,
        "external_source_data_persisted": False,
        "scientific_and_rights_admission_proven": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args(argv)
    try:
        path = args.source_json
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise NFIPPenetrationError("source missing, symlink or oversized")
        result = validate_original(path.read_bytes(), args.sha256)
    except (NFIPPenetrationError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
