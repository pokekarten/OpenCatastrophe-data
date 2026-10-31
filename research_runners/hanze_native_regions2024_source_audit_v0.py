#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Review the HANZE v3.0.2-beta native 2024 regional code glossary.

An exact provider glossary can identify a named *administrative region*;
it does not identify a hazard footprint, event duplicate, exposed insurer
asset, incurred insured loss or commercial geodata entitlement.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import re

if __package__:
    from .historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS, inspect_hanze_v302
else:
    from historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS, inspect_hanze_v302

PUBLISHER_RECORD = "https://zenodo.org/records/23670886"
FILE_URL = ("https://zenodo.org/api/records/23670886/files/"
            "S2_regions_codes_and_names_v2024.csv/content")
PUBLISHER_MD5 = "a5a36736c71f175f8aad5d9480bed827"
PUBLISHER_BYTES = 32001
MAX_BYTES = 150_000
GLOSSARY_HEADER = ("Code", "Name")
REGION = re.compile(r"[A-Z]{2}[A-Z0-9]{3}\Z")
SOURCE_VERSION = "HANZE v3.0.2 beta / S2 regions v2024"


class HANZERegionGlossaryError(ValueError):
    """Original bytes, structure or attempted regional join are uncertain."""


def read_hanze_original_regions(glossary: bytes, expected_sha256: str | None = None):
    """Verify the exact provider file and return *in-memory* code set and receipt."""
    if type(glossary) is not bytes or len(glossary) != PUBLISHER_BYTES or len(glossary) > MAX_BYTES:
        raise HANZERegionGlossaryError("publisher HANZE S2 original byte length mismatch")
    md5 = hashlib.md5(glossary, usedforsecurity=False).hexdigest()
    if md5 != PUBLISHER_MD5:
        raise HANZERegionGlossaryError("publisher HANZE S2 MD5 mismatch")
    sha = hashlib.sha256(glossary).hexdigest()
    if expected_sha256 is not None and (type(expected_sha256) is not str or
                                        expected_sha256 != sha):
        raise HANZERegionGlossaryError("independently pinned HANZE S2 SHA256 mismatch")
    try:
        reader = csv.DictReader(io.StringIO(glossary.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames != list(GLOSSARY_HEADER):
            raise HANZERegionGlossaryError("HANZE S2 CSV header mismatch")
        codes = set()
        countries = set()
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise HANZERegionGlossaryError("HANZE S2 row column mismatch")
            code, name = row["Code"], row["Name"]
            if (type(code) is not str or not REGION.fullmatch(code)
                    or type(name) is not str or not name.strip()):
                raise HANZERegionGlossaryError("invalid HANZE S2 code or empty name")
            if code in codes:
                raise HANZERegionGlossaryError("duplicate HANZE S2 region code")
            codes.add(code)
            countries.add(code[:2])
            if len(codes) > 10000:
                raise HANZERegionGlossaryError("HANZE S2 region upper bound exceeded")
    except (UnicodeError, csv.Error) as exc:
        raise HANZERegionGlossaryError("invalid HANZE original region glossary CSV") from exc
    if not 1000 <= len(codes) <= 3000:
        raise HANZERegionGlossaryError("unusual HANZE S2 region glossary cardinality")
    return codes, {
        "source": SOURCE_VERSION,
        "original_publisher_url": FILE_URL,
        "publisher_byte_length": len(glossary),
        "publisher_md5_confirmed": True,
        "observed_sha256": sha,
        "sha256_independently_pinned": expected_sha256 is not None,
        "distinct_region_codes": len(codes),
        "distinct_region_country_prefixes": len(countries),
        "regions_or_names_exported": False,
        "source_release_license_is_not_geometry_sublicense": True,
        "model_input_admitted": False,
    }


def _parts(raw: str):
    """Parse only bounded, explicit delimiter-list grammar, never guess tokens."""
    if type(raw) is not str or not raw or len(raw) > 5000:
        return None
    if REGION.fullmatch(raw):
        return [raw]
    delimiters = [char for char in (";", ",", "|") if char in raw]
    if len(delimiters) != 1:
        return None
    parts = [part.strip() for part in raw.split(delimiters[0])]
    if not 1 < len(parts) <= 100 or len(set(parts)) != len(parts):
        return None
    if any(not REGION.fullmatch(part) for part in parts):
        return None
    return parts


def audit_hanze_s2_candidate_codes(hanze_blob: bytes, expected_hanze_sha256: str,
                                  overlap: dict, s2_bytes: bytes,
                                  *, expected_s2_sha256: str | None = None) -> dict:
    if (type(overlap) is not dict
            or overlap.get("evidence_class") != "HISTORICAL_FLOOD_EVENT_CANDIDATE_LINKS_ONLY"
            or overlap.get("common_event_identity_proven") is not False
            or overlap.get("model_input_admitted") is not False
            or overlap.get("input_sha256", {}).get("hanze_csv") != expected_hanze_sha256):
        raise HANZERegionGlossaryError("invalid upstream original event stage")
    profile = inspect_hanze_v302(hanze_blob, expected_hanze_sha256)
    if profile.get("source_admitted") is not False:
        raise HANZERegionGlossaryError("invalid HANZE original source admission")
    allowed, src = read_hanze_original_regions(s2_bytes, expected_sha256=expected_s2_sha256)
    try:
        reader = csv.DictReader(io.StringIO(hanze_blob.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames != list(HANZE_COLUMNS):
            raise HANZERegionGlossaryError("HANZE source event header drift")
        by_id = {}
        for row in reader:
            if row["id"] in by_id:
                raise HANZERegionGlossaryError("repeated original event ID")
            by_id[row["id"]] = row
    except (UnicodeError, csv.Error) as exc:
        raise HANZERegionGlossaryError("malformed source event CSV") from exc
    seen = set()
    stats = Counter()
    for pair in overlap.get("candidate_pairs", []):
        if (type(pair) is not dict or pair.get("same_event_confirmed") is not False
                or pair.get("losses_joined") is not False
                or pair.get("relationship") != "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY"):
            raise HANZERegionGlossaryError("candidate identity or loss stage unsupported")
        did, hid = pair.get("dfo_event_id"), pair.get("hanze_event_id")
        if (type(did) is not str or type(hid) is not str
                or (did, hid) in seen or hid not in by_id):
            raise HANZERegionGlossaryError("source pair missing/duplicated")
        seen.add((did, hid))
        row = by_id[hid]
        if row["country_code"] != pair.get("country_iso2_from_supplied_crosswalk"):
            raise HANZERegionGlossaryError("HANZE original country differs from candidate")
        stats["pairs"] += 1
        code = row["admin_unit_code"].strip()
        if not code:
            stats["missing_raw_region_code"] += 1
            continue
        parsed = _parts(code)
        if parsed is None:
            stats["noncanonical_or_unsupported_region_list"] += 1
            continue
        stats["region_tokens_from_accepted_lists"] += len(parsed)
        if any(part[:2] != row["country_code"] for part in parsed):
            stats["country_inconsistent_region_list"] += 1
        elif any(part not in allowed for part in parsed):
            stats["missing_glossary_tokens"] += 1
        elif len(parsed) == 1:
            stats["exact_one_region_glossary_matched"] += 1
        else:
            stats["exact_multi_region_glossary_matched"] += 1
    if stats["pairs"] != overlap.get("candidate_pair_count"):
        raise HANZERegionGlossaryError("candidate count drift")
    return {
        "evidence_stage": "HANZE_V302_NATIVE_2024_REGION_GLOSSARY_LOOKUP_ONLY",
        "original_glossary": src,
        "candidate_pair_count": stats["pairs"],
        "status_counts": {
            key: stats[key] for key in (
                "exact_one_region_glossary_matched",
                "exact_multi_region_glossary_matched",
                "missing_raw_region_code",
                "noncanonical_or_unsupported_region_list",
                "country_inconsistent_region_list",
                "missing_glossary_tokens",
            )
        },
        "region_tokens_from_accepted_lists": stats["region_tokens_from_accepted_lists"],
        "reference_admin_region_is_not_actual_inundation": True,
        "gis_geometry_loaded": False,
        "source_event_identity_proven": False,
        "original_raw_event_or_glossary_rows_exported": False,
        "insurer_tiv_or_loss_created": False,
        "source_rights_and_geodata_sublicenses_reviewed": False,
        "model_input_admitted": False,
    }
