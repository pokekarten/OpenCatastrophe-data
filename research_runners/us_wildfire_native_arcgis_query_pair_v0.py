#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, bounded USFS ArcGIS response pair audit for 2024 MTBS/FPA FOD.

Requires caller-frozen SHA-256-pinned provider response snapshots. Returns only
aggregate statistics, never event IDs, geometry, source observations or losses.
An HTTP reply hash does NOT authenticate publisher identity or source rights.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

try:
    from .us_wildfire_original_arcgis_metadata_v0 import classify_mtbs_fire_type
except ImportError:
    from us_wildfire_original_arcgis_metadata_v0 import classify_mtbs_fire_type

MAX_BYTES = 250_000
MAX_ROWS = 250
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}\Z")
VINTAGE = re.compile(r"MTBS[-_][A-Za-z0-9][A-Za-z0-9._-]{7,79}\Z")
COLUMNS = {
    "fpa": {
        "fod_id": "esriFieldTypeInteger",
        "mtbs_id": "esriFieldTypeString",
        "fire_year": "esriFieldTypeSmallInteger",
    },
    "mtbs": {
        "fire_id": "esriFieldTypeString",
        "year": "esriFieldTypeSmallInteger",
        "fire_type": "esriFieldTypeString",
        "perim_id": "esriFieldTypeString",
        "map_id": "esriFieldTypeInteger",
    },
}


class QueryAuditBlocked(ValueError):
    """Source-query response or identity evidence is missing or ambiguous."""


def _object(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise QueryAuditBlocked("duplicate JSON key in source response")
        data[key] = value
    return data


def _not_finite(value):
    raise QueryAuditBlocked("nonfinite JSON value in source response")


def _key(value, label, *, optional=False):
    if optional and value is None:
        return None
    if type(value) is not str or not SOURCE_KEY.fullmatch(value):
        raise QueryAuditBlocked(label + ": malformed or unknown-format event key")
    return value


def _result_rows(blob: bytes, sha: str, kind: str):
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise QueryAuditBlocked(kind + ": empty or oversized source response snapshot")
    if type(sha) is not str or not DIGEST.fullmatch(sha):
        raise QueryAuditBlocked(kind + ": exact lowercase SHA-256 digest required")
    actual_sha = hashlib.sha256(blob).hexdigest()
    if actual_sha != sha:
        raise QueryAuditBlocked(kind + ": original response snapshot hash mismatch")
    try:
        data = json.loads(blob.decode("utf-8"), object_pairs_hook=_object, parse_constant=_not_finite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise QueryAuditBlocked(kind + ": invalid UTF-8/JSON source response") from exc
    if not isinstance(data, dict) or "error" in data:
        raise QueryAuditBlocked(kind + ": ArcGIS query error or non-object payload")
    names = COLUMNS[kind]
    fields = data.get("fields")
    if not isinstance(fields, list) or len(fields) != len(names):
        raise QueryAuditBlocked(kind + ": expected exact selected source fields")
    actual_fields = {}
    for field in fields:
        if not isinstance(field, dict) or type(field.get("name")) is not str or type(field.get("type")) is not str:
            raise QueryAuditBlocked(kind + ": malformed ArcGIS field metadata")
        key = field["name"].casefold()
        if key in actual_fields:
            raise QueryAuditBlocked(kind + ": duplicate field name")
        actual_fields[key] = field["type"]
    if actual_fields != names:
        raise QueryAuditBlocked(kind + ": unexpected field name or native type")
    rows = data.get("features")
    if not isinstance(rows, list) or not 0 < len(rows) <= MAX_ROWS:
        raise QueryAuditBlocked(kind + ": expected nonempty bounded features array")
    for feature in rows:
        if not isinstance(feature, dict) or set(feature) != {"attributes"}:
            raise QueryAuditBlocked(kind + ": source sample must contain attributes only; no geometries")
        attrs = feature["attributes"]
        if not isinstance(attrs, dict) or {key.casefold() for key in attrs} != set(names) or len(attrs) != len(names):
            raise QueryAuditBlocked(kind + ": unexpected feature attributes")
        if any(type(key) is not str for key in attrs):
            raise QueryAuditBlocked(kind + ": non-string feature attribute key")
        # ArcGIS may retain provider field capitalization in output.
        fields_folded = {key.casefold(): value for key, value in attrs.items()}
        if len(fields_folded) != len(names):
            raise QueryAuditBlocked(kind + ": duplicated attribute by field capitalization")
        feature["attributes"] = fields_folded
    limit_flag = data.get("exceededTransferLimit")
    if limit_flag is not None and type(limit_flag) is not bool:
        raise QueryAuditBlocked(kind + ": invalid transfer-limit signal")
    return [f["attributes"] for f in rows], actual_sha, limit_flag


def audit_original_queries(
    fpa_blob: bytes, fpa_sha256: str, mtbs_blob: bytes, mtbs_sha256: str,
    *, selection: str, fpa_release: str, mtbs_vintage: str,
) -> dict:
    """Review a small source query pair; no insurer CAT event confirmation."""
    if selection not in ("unfiltered_2024", "mtbs_id_present_2024"):
        raise QueryAuditBlocked("selection must declare an explicit 2024 sampling design")
    if fpa_release != "FPA_FOD_20260615":
        raise QueryAuditBlocked("FPA-FOD original seventh edition not pinned")
    if type(mtbs_vintage) is not str or not VINTAGE.fullmatch(mtbs_vintage) or any(
        word in mtbs_vintage.casefold() for word in ("latest", "current", "unknown")
    ):
        raise QueryAuditBlocked("MTBS exact vintage label required; no latest/current alias")

    fpa, fpa_sha, fpa_limited = _result_rows(fpa_blob, fpa_sha256, "fpa")
    mtbs, mtbs_sha, mtbs_limited = _result_rows(mtbs_blob, mtbs_sha256, "mtbs")
    ids_seen = set()
    fpa_count_by_mtbs_id = Counter()
    for row in fpa:
        fid = row["fod_id"]
        if type(fid) is not int or fid <= 0 or fid in ids_seen:
            raise QueryAuditBlocked("duplicate, missing or nonpositive FPA FOD_ID")
        ids_seen.add(fid)
        if type(row["fire_year"]) is not int or row["fire_year"] != 2024:
            raise QueryAuditBlocked("FPA source response not bounded to fire_year 2024")
        key = _key(row["mtbs_id"], "FPA MTBS_ID", optional=True)
        if key is not None:
            fpa_count_by_mtbs_id[key] += 1
        elif selection == "mtbs_id_present_2024":
            raise QueryAuditBlocked("MTBS-ID-filtered FPA projection unexpectedly has missing link")

    mtbs_by_fire = {}
    stats = Counter()
    mtbs_count_by_fire = Counter()
    for row in mtbs:
        key = _key(row["fire_id"], "MTBS FIRE_ID")
        mtbs_count_by_fire[key] += 1
        if type(row["year"]) is not int or row["year"] != 2024:
            raise QueryAuditBlocked("MTBS layer 82 response not bounded to fire year 2024")
        if row["perim_id"] is not None:
            _key(row["perim_id"], "MTBS optional satellite-scene PERIM_ID")
            stats["perim_id_populated"] += 1
        if row["map_id"] is not None:
            if type(row["map_id"]) is not int:
                raise QueryAuditBlocked("MTBS MAP_ID must be integer/null; not a guaranteed event ID")
            stats["map_id_populated"] += 1
        fire_class, recognized = classify_mtbs_fire_type(row["fire_type"])
        stats["unrecognized_fire_type_rows"] += not recognized
        mtbs_by_fire[key] = fire_class

    dispositions = Counter()
    for row in fpa:
        key = row["mtbs_id"]
        if key is None:
            label = "fpa_mtbs_id_missing"
        elif key not in mtbs_count_by_fire:
            label = "not_in_supplied_mtbs_query_slice"
        elif fpa_count_by_mtbs_id[key] != 1 or mtbs_count_by_fire[key] != 1:
            label = "ambiguous_multiplicity_needs_review"
        elif mtbs_by_fire[key] == "prescribed":
            label = "prescribed_fire_not_wildfire"
        elif mtbs_by_fire[key] == "unknown":
            label = "unknown_fire_type"
        else:
            label = "unique_id_wildfire_research_candidate"
        dispositions[label] += 1
    names = (
        "fpa_mtbs_id_missing",
        "not_in_supplied_mtbs_query_slice",
        "ambiguous_multiplicity_needs_review",
        "prescribed_fire_not_wildfire",
        "unknown_fire_type",
        "unique_id_wildfire_research_candidate",
    )
    counts = {name: dispositions[name] for name in names}
    if sum(counts.values()) != len(fpa):
        raise QueryAuditBlocked("source row conservation failed")
    review = bool(counts["ambiguous_multiplicity_needs_review"] or counts["unknown_fire_type"] or
                  stats["unrecognized_fire_type_rows"])
    return {
        "audit": "us-wildfire-native-2024-arcgis-query-pair-v0",
        "state": "REVIEW_NEEDED" if review else "BOUNDED_RESEARCH_SAMPLE_ONLY",
        "selection_mode_declared_by_caller_not_attested": selection,
        "fpa_release_claim": fpa_release,
        "mtbs_vintage_label_claim": mtbs_vintage,
        "fpa_response_sha256": fpa_sha,
        "mtbs_response_sha256": mtbs_sha,
        "fpa_feature_count": len(fpa),
        "fpa_with_mtbs_id": sum(fpa_count_by_mtbs_id.values()),
        "mtbs_feature_count": len(mtbs),
        "mtbs_distinct_fire_ids_in_slice": len(mtbs_count_by_fire),
        "mtbs_perim_id_populated": stats["perim_id_populated"],
        "mtbs_map_id_populated": stats["map_id_populated"],
        "mtbs_unknown_original_fire_class_rows": stats["unrecognized_fire_type_rows"],
        "fpa_disposition": counts,
        "fpa_rows_conserved": True,
        "fpa_provider_transfer_limit": fpa_limited,
        "mtbs_provider_transfer_limit": mtbs_limited,
        "source_response_origin_authenticated": False,
        "original_archive_asset_hash_verified": False,
        "source_selection_representative_or_national_coverage_established": False,
        "perim_id_or_map_id_promoted_to_polygon_key": False,
        "physical_event_equivalence_proven": False,
        "financial_or_insured_loss_inferred": False,
        "source_rights_or_model_admission_granted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fpa-response", type=Path, required=True)
    parser.add_argument("--fpa-sha256", required=True)
    parser.add_argument("--mtbs-response", type=Path, required=True)
    parser.add_argument("--mtbs-sha256", required=True)
    parser.add_argument("--fpa-release", required=True)
    parser.add_argument("--mtbs-vintage", required=True)
    parser.add_argument("--selection", choices=("unfiltered_2024", "mtbs_id_present_2024"), required=True)
    args = parser.parse_args(argv)
    try:
        for p in (args.fpa_response, args.mtbs_response):
            if not p.is_file() or p.stat().st_size > MAX_BYTES:
                raise QueryAuditBlocked("missing or oversized local original-response snapshot")
        result = audit_original_queries(
            args.fpa_response.read_bytes(), args.fpa_sha256,
            args.mtbs_response.read_bytes(), args.mtbs_sha256,
            selection=args.selection, fpa_release=args.fpa_release,
            mtbs_vintage=args.mtbs_vintage,
        )
    except (QueryAuditBlocked, OSError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if result["state"] == "REVIEW_NEEDED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
