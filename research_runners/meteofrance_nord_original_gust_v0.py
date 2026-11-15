# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One fixed northern France 2020-2024 *original* CSV.GZ preflight.

This is an observed-source acquisition research canary. It emits only
file identity/hashes and non-sensitive aggregate QA; no original rows,
location coordinates, station IDs or insured assets are published.
"""
from __future__ import annotations

import argparse
import json
import sys

from research_runners.meteofrance_hourly_gust_v0 import (
    Blocked, _read_url, audit_gzip, verify_dictionary,
    DOCUMENT_URL, MAX_DOCUMENT_BYTES,
)
from research_runners.meteofrance_north_hourly_catalogue_v0 import (
    audit_catalogue, CATALOGUE_URL, MAX_CATALOGUE_BYTES,
)

DEPARTMENT = "59"
SOURCE_ID = "414ca541-fa77-4060-b93c-44fb3a85d693"
SOURCE_URL = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/synchro_ftp/BASE/HOR/H_59_previous-2020-2024.csv.gz"
SOURCE_BYTES = 15_928_750
MAX_SOURCE_BYTES = 32 * 1024 * 1024


def verify_resource(resource: dict) -> None:
    if type(resource) is not dict:
        raise Blocked("Nord source resource missing")
    if (resource.get("department") != DEPARTMENT
            or resource.get("resource_id") != SOURCE_ID
            or resource.get("original_url") != SOURCE_URL
            or resource.get("declared_compressed_bytes") != SOURCE_BYTES
            or resource.get("period") != "2020-2024"):
        raise Blocked("Nord original resource identity differs from verified official catalogue")
    if resource.get("source_admitted") is not False:
        raise Blocked("Nord resource admission must remain false")
    if resource.get("original_bytes_fetched") is not False:
        raise Blocked("metadata source claims pre-existing original bytes")


def audit_original(catalogue: bytes, field_dictionary: bytes, original: bytes) -> dict:
    overview = audit_catalogue(catalogue)
    match = [row for row in overview["sources"] if row["department"] == DEPARTMENT]
    if len(match) != 1:
        raise Blocked("Nord source is absent or not unique")
    verify_resource(match[0])
    dict_sha = verify_dictionary(field_dictionary)
    if len(original) != SOURCE_BYTES:
        raise Blocked("Nord original compressed bytes changed since provider metadata preflight")
    result = audit_gzip(original)
    if result["original_gzip_bytes"] != SOURCE_BYTES:
        raise Blocked("Nord source size assertion failed")
    if result["quality_checked_three_second_gusts"] == 0:
        raise Blocked("Nord source has no validated three-second gust observations")
    result.update({
        "profile": "meteofrance-nord-2020-2024-one-original-v0",
        "catalogue_sha256": overview["catalogue_sha256"],
        "official_resource_id": SOURCE_ID,
        "official_original_url": SOURCE_URL,
        "official_field_dictionary_sha256": dict_sha,
        "source_digest_newly_observed": True,
        "digest_not_yet_pinned_as_prior_receipt": True,
        "source_admitted": False,
        "annual_ep_authorized": False,
        "insured_loss_calibration_authorized": False,
    })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True,
                        help="one fixed publicly licensed original station source")
    args = parser.parse_args(argv)
    try:
        catalogue = _read_url(CATALOGUE_URL, MAX_CATALOGUE_BYTES)
        dictionary = _read_url(DOCUMENT_URL, MAX_DOCUMENT_BYTES)
        original = _read_url(SOURCE_URL, MAX_SOURCE_BYTES)
        print(json.dumps(audit_original(catalogue, dictionary, original), indent=2, sort_keys=True))
        return 0
    except (Blocked, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
