# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed original FHWA NBI Socrata *metadata-only* source audit.

This tool never requests bridge data, cannot infer insurance assets, and does
not validate SNBI-vs-legacy crosswalk, coordinate units or source rights.
Input: locally acquired complete JSON metadata from the official
https://data.transportation.gov/api/views/pced-83j4.json endpoint only.
The digest is a receipt of supplied bytes, NOT a publisher signature.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

DATASET_ID = "pced-83j4"
DATASET_PAGE = "https://data.transportation.gov/Roadways-and-Bridges/National-Bridge-Inventory/pced-83j4"
METADATA_ENDPOINT = "https://data.transportation.gov/api/views/pced-83j4.json"
CONTRACT = "OC_FHWA_NBI_SOCRATA_2026_METADATA_ONLY_V0"
MAX_ORIGINAL_BYTES = 4_000_000
PUBLISHED_COLUMNS_AT_REVIEW = 124
REQUIRED = {
    "year": "number",
    "state_code_001": "number",
    "structure_number_008": "text",
    "lat_016": "number",
    "long_017": "number",
    "year_built_027": "number",
}


class Blocked(ValueError):
    """Original provider source, vintage or data-contract boundary not met."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise Blocked("duplicate JSON object key in original metadata")
        out[key] = value
    return out


def audit_metadata(original: bytes, *, expected_sha256: str | None = None) -> dict:
    """Audit source schema, never source rows or insurance geography."""
    if type(original) is not bytes or not 32 <= len(original) <= MAX_ORIGINAL_BYTES:
        raise Blocked("complete bounded original Socrata JSON metadata bytes required")
    digest = sha256(original).hexdigest()
    if expected_sha256 is not None:
        if (type(expected_sha256) is not str or
                not re.fullmatch(r"[a-f0-9]{64}", expected_sha256) or
                expected_sha256 != digest):
            raise Blocked("original metadata SHA-256 mismatch")
    try:
        doc = json.loads(
            original.decode("utf-8"), object_pairs_hook=_unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(Blocked("nonfinite JSON")),
        )
    except Blocked:
        raise
    except (ValueError, UnicodeError) as exc:
        raise Blocked("metadata is not valid strict UTF-8 JSON") from exc
    if type(doc) is not dict or doc.get("id") != DATASET_ID:
        raise Blocked("wrong FHWA NBI Socrata dataset identity")
    name = doc.get("name")
    if type(name) is not str or "National Bridge Inventory" not in name:
        raise Blocked("unexpected FHWA NBI original dataset title")
    if doc.get("viewType", "tabular") != "tabular":
        raise Blocked("unexpected non-tabular Socrata dataset")
    columns = doc.get("columns")
    if type(columns) is not list or not 124 <= len(columns) <= 150:
        raise Blocked("missing or changed original NBI column inventory")
    field_types = {}
    for column in columns:
        if type(column) is not dict:
            raise Blocked("invalid original column descriptor")
        field = column.get("fieldName")
        dtype = column.get("dataTypeName")
        if (type(field) is not str or not 1 <= len(field) <= 80 or
                type(dtype) is not str or not 1 <= len(dtype) <= 40):
            raise Blocked("original column field/type missing")
        if field in field_types:
            raise Blocked("duplicate NBI API field name")
        field_types[field] = dtype
    # Socrata may include colon-prefixed row-management fields.
    user_fields = {k: v for k, v in field_types.items() if not k.startswith(":")}
    if len(user_fields) != PUBLISHED_COLUMNS_AT_REVIEW:
        raise Blocked("published 124-column NBI source schema changed")
    for key, dtype in REQUIRED.items():
        if key not in user_fields or (dtype is not None and user_fields[key] != dtype):
            raise Blocked(f"required original NBI field missing/type changed: {key}")
    return {
        "contract": CONTRACT,
        "status": "FHWA_NBI_METADATA_SCHEMA_ONLY_NOT_MODEL_ADMITTED",
        "dataset_id": DATASET_ID,
        "source_page": DATASET_PAGE,
        "metadata_endpoint_declared_not_proven_by_bytes": METADATA_ENDPOINT,
        "original_metadata_sha256": digest,
        "original_metadata_byte_count": len(original),
        "published_column_count": len(user_fields),
        "socrata_internal_column_count": len(field_types) - len(user_fields),
        "required_field_types": {key: user_fields[key] for key in sorted(REQUIRED)},
        "source_metadata_is_cryptographically_publisher_signed": False,
        "all_source_rows_obtained": False,
        "year_of_record_verified_against_real_bridge_rows": False,
        "legacy_nbi_to_2026_snbi_data_crosswalk_verified": False,
        "lat_lon_encoding_and_crs_verified": False,
        "bridge_identity_and_geometry_deduplicated": False,
        "source_data_rights_independently_reviewed": False,
        "insured_site_or_tiv_identified": False,
        "hazard_vulnerability_or_fragility_validated": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-metadata", type=Path, required=True)
    parser.add_argument("--expected-sha256", help="optional external operator-chosen pin")
    parser.add_argument("--out", type=Path, help="new sanitized receipt only; never overwrite")
    opts = parser.parse_args(argv)
    source = opts.original_metadata
    if source.is_symlink() or not source.is_file() or not 32 <= source.stat().st_size <= MAX_ORIGINAL_BYTES:
        parser.error("bounded regular original metadata file required")
    if opts.out is not None and (opts.out.exists() or opts.out.is_symlink() or
                                 opts.out.resolve() == source.resolve()):
        parser.error("refuse existing or source-alias receipt output")
    receipt = audit_metadata(source.read_bytes(), expected_sha256=opts.expected_sha256)
    data = json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if opts.out is None:
        print(data, end="")
    else:
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        with opts.out.open("x", encoding="utf-8") as handle:
            handle.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
