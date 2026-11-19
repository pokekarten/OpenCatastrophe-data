#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Validate a LOCAL Insurers Global name-index snapshot; emit metadata-only evidence.

No downloading, database access, publication of third-party rows, or model admission.
The provider's 'verified' flag is a directory claim, not legal verification.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_VERSION = "2026-09-08+97f331e66662"
SOURCE_URL = "https://insurers.global/api/v1/insurers/names.json"
SOURCE_TERMS = "https://insurers.global/terms/"
ATTRIBUTION = "KAFS North America, insurers.global (https://insurers.global)"
PROVIDER_STATES = frozenset({"verified", "partial", "unverified"})


def inspect_bytes(raw: bytes, expected_version: str = EXPECTED_VERSION) -> dict[str, Any]:
    if not raw:
        raise ValueError("empty source snapshot")
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("source must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("source root must be object")
    if payload.get("version") != expected_version:
        raise ValueError("source version changed; review new edition before importing")
    if payload.get("all") != SOURCE_URL:
        raise ValueError("source endpoint mismatch")
    licence = payload.get("licence")
    if not isinstance(licence, str) or "CC BY 4.0" not in licence or "KAFS North America" not in licence:
        raise ValueError("source licence/attribution not as reviewed")
    entries = payload.get("data")
    if not isinstance(entries, list) or not entries:
        raise ValueError("missing source data")
    if type(payload.get("count")) is not int or payload["count"] != len(entries):
        raise ValueError("declared row count inconsistent")
    slugs: set[str] = set()
    country_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    provider_counts: Counter[str] = Counter()
    for pos, record in enumerate(entries):
        if not isinstance(record, dict):
            raise ValueError(f"row {pos}: not an object")
        for key in ("slug", "name", "country", "classCode", "verification"):
            if not isinstance(record.get(key), str) or not record[key].strip():
                raise ValueError(f"row {pos}: missing or empty {key}")
        slug = record["slug"]
        if slug in slugs:
            raise ValueError(f"duplicate source slug {slug!r}")
        slugs.add(slug)
        status = record["verification"]
        if status not in PROVIDER_STATES:
            raise ValueError(f"row {pos}: unexpected provider verification state")
        country_counts[record["country"]] += 1
        class_counts[record["classCode"]] += 1
        provider_counts[status] += 1
    return {
        "schema": "oc-insurer-directory-source-receipt-v0",
        "source_url": SOURCE_URL,
        "source_terms_url": SOURCE_TERMS,
        "dataset_version": expected_version,
        "sha256_of_local_input_bytes": hashlib.sha256(raw).hexdigest(),
        "rows": len(entries),
        "unique_source_slugs": len(slugs),
        "country_slugs": len(country_counts),
        "classes": dict(sorted(class_counts.items())),
        "provider_verification_claims": dict(sorted(provider_counts.items())),
        "attribution": ATTRIBUTION,
        "research_only": True,
        "regulator_verified_by_this_audit": False,
        "insured_exposure_observed": False,
        "model_admitted": False,
        "warning": "This checks local file structure and source metadata, not original HTTP provenance, regulator identity, or rights to underlying third-party records.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="locally acquired provider JSON, never committed")
    parser.add_argument("--expected-version", default=EXPECTED_VERSION)
    args = parser.parse_args()
    result = inspect_bytes(args.input.read_bytes(), args.expected_version)
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
