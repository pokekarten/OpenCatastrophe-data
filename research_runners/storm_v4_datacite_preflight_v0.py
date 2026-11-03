#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, original-byte-bound DataCite DOI metadata preflight for STORM v4.

The input is a locally captured public DOI metadata response (not STORM tracks).
This tool never makes network requests and never licenses, downloads or admits
provider files. Run with a separately observed raw-response SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

DOI = "10.4121/12706085.v4"
SOURCE_ID = "storm.ibtracs.present-climate.v4"
ACCESS_ID = "storm.ibtracs.present-climate.v4.datacite"
PROFILE = "storm-v4-datacite-metadata-preflight-v0"
MAX_BYTES = 262_144
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class Blocked(ValueError):
    """Provider metadata cannot be reconciled to the frozen dataset release."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise Blocked("duplicate JSON key")
        output[key] = value
    return output


def _reject_constant(value: str) -> None:
    raise Blocked("non-finite JSON constant " + value)


def _strict_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise Blocked("non-finite JSON number")
    return number


def inspect_metadata(raw: bytes, independent_sha256: str) -> dict[str, object]:
    if type(independent_sha256) is not str or not SHA256.fullmatch(independent_sha256):
        raise Blocked("independent SHA-256 must be lowercase 64-character hex")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise Blocked("DOI metadata response empty or exceeds 256-KiB cap")
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != independent_sha256:
        raise Blocked("original response SHA-256 mismatch")
    try:
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_strict_object,
            parse_constant=_reject_constant, parse_float=_strict_float,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Blocked("not strict UTF-8 JSON") from exc
    if type(payload) is not dict or type(payload.get("data")) is not dict:
        raise Blocked("not a DataCite single-DOI response")
    item = payload["data"]
    if item.get("type") != "dois" or item.get("id") != DOI:
        raise Blocked("wrong DataCite record type or exact v4 DOI")
    attributes = item.get("attributes")
    if type(attributes) is not dict or attributes.get("doi") != DOI:
        raise Blocked("DataCite attributes DOI mismatch")
    resource = attributes.get("types")
    if type(resource) is not dict or resource.get("resourceTypeGeneral") != "Dataset":
        raise Blocked("DOI is not explicitly a dataset")
    title_rows = attributes.get("titles")
    if type(title_rows) is not list or not title_rows:
        raise Blocked("dataset title missing")
    titles = [row.get("title") for row in title_rows if type(row) is dict]
    if not any(type(title) is str and "storm" in title.casefold()
               and "tropical cyclone" in title.casefold() for title in titles):
        raise Blocked("dataset title does not identify STORM tropical cyclones")
    publisher = attributes.get("publisher")
    if type(publisher) is not str or not publisher.strip():
        raise Blocked("publisher missing")
    version = attributes.get("version")
    if version is not None and (type(version) is not str
                                or version.strip().casefold() not in {"4", "4.0", "v4", "version 4"}):
        raise Blocked("explicit metadata version contradicts v4 DOI")
    rights_rows = attributes.get("rightsList", [])
    if type(rights_rows) is not list:
        raise Blocked("invalid DataCite rightsList")
    # Every populated assertion in a rights row must independently identify
    # the *same* CC0 grant. One good identifier must not mask an incompatible
    # rights URI or an arbitrary text field containing a CC0 URL substring.
    accepted = {
        "rights": {
            "cc0", "cc0-1.0", "cc0 1.0",
            "creative commons zero v1.0 universal",
            "creative commons cc0 1.0 universal",
            "creative commons zero 1.0 universal",
        },
        "rightsIdentifier": {"cc0", "cc0-1.0"},
        "rightsUri": {
            "https://creativecommons.org/publicdomain/zero/1.0",
            "https://creativecommons.org/publicdomain/zero/1.0/",
            "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
            "https://creativecommons.org/publicdomain/zero/1.0/legalcode/",
        },
    }
    cc0_confirmed = False
    for row in rights_rows:
        if type(row) is not dict:
            raise Blocked("invalid rightsList entry")
        present = False
        for field, allowed in accepted.items():
            value = row.get(field)
            if value is None or value == "":
                continue
            if type(value) is not str or value.strip().casefold() not in allowed:
                raise Blocked("DataCite rights claim requires independent review")
            present = True
        if present:
            cc0_confirmed = True
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "access_id": ACCESS_ID,
        "doi": DOI,
        "response_bytes": len(raw),
        "response_sha256": actual_sha,
        "data_cite_dataset_identity_verified": True,
        "datacite_cc0_claim_observed": cc0_confirmed,
        "provider_asset_inventory_verified": False,
        "original_track_files_acquired": False,
        "original_track_byte_identity_verified": False,
        "synthetic_year_and_event_semantics_verified": False,
        "model_hazard_footprint_verified": False,
        "source_admission_extended": False,
        "service_automation_authorized": False,
        "model_input_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider_metadata_json", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        with args.provider_metadata_json.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        result = inspect_metadata(raw, args.expected_sha256)
    except (OSError, Blocked) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
