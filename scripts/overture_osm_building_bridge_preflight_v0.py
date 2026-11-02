# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, version-exact OSM -> Overture building GERS bridge candidate preflight.

Consumes a bounded projection of already lawfully obtained bridge Parquet rows.
It never queries a provider, stores source data or authorizes CAT model inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from uuid import UUID

SCHEMA = "opencatastrophe-overture-osm-building-bridge-v0"
MAX_BYTES = 500_000
MAX_LOCAL = 100
MAX_BRIDGE = 500
RELEASE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\.\d+\Z")
OSM_ID_RE = re.compile(r"[nwr][1-9]\d{0,16}@[1-9]\d{0,9}\Z")


class BridgeError(ValueError):
    """Reject malformed or unsuitable candidate mapping evidence."""


def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise BridgeError(f"duplicate JSON property: {key}")
        out[key] = value
    return out


def _reject_nonfinite(value):
    raise BridgeError(f"invalid numeric constant: {value}")


def _read(path):
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise BridgeError("bridge input missing or oversized")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object,
                      parse_constant=_reject_nonfinite)


def _fields(value, fields, context):
    if type(value) is not dict or set(value) != set(fields):
        raise BridgeError(f"{context}: unexpected/missing fields")


def _string(value, context):
    if type(value) is not str or not 1 <= len(value) <= 128 or not value.strip():
        raise BridgeError(f"{context}: invalid text")
    return value


def _gers_id(value):
    value = _string(value, "gers id")
    try:
        if str(UUID(value)) != value:
            raise ValueError("noncanonical UUID")
    except ValueError as exc:
        raise BridgeError("noncanonical GERS candidate UUID") from exc
    return value


def _osm_record_id(value):
    value = _string(value, "OSM record_id")
    if not OSM_ID_RE.fullmatch(value):
        raise BridgeError("OSM record_id requires object type and exact @version")
    return value


def bridge_osm_buildings(payload, *, expected_release):
    """Return reciprocal one-to-one candidate links; no false global completeness."""
    _fields(payload, {"schema", "release", "bridge_provider", "bridge_dataset",
                      "local_records", "bridge_rows"}, "input")
    if payload["schema"] != SCHEMA or payload["bridge_provider"] != "osm":
        raise BridgeError("not the OSM building bridge contract")
    if payload["bridge_dataset"] != "OpenStreetMap":
        raise BridgeError("source dataset must be explicitly OpenStreetMap")
    if type(expected_release) is not str or not RELEASE_RE.fullmatch(expected_release):
        raise BridgeError("expected release must be exact")
    if payload["release"] != expected_release:
        raise BridgeError("release mismatch; do not join bridge revisions")
    locals_raw = payload["local_records"]
    bridges_raw = payload["bridge_rows"]
    if type(locals_raw) is not list or not 1 <= len(locals_raw) <= MAX_LOCAL:
        raise BridgeError("invalid local batch size")
    if type(bridges_raw) is not list or not 1 <= len(bridges_raw) <= MAX_BRIDGE:
        raise BridgeError("invalid bridge slice size")
    local_ids = set()
    local_records = {}
    for row in locals_raw:
        _fields(row, {"local_id", "record_id"}, "local")
        local_id = _string(row["local_id"], "local id")
        record_id = _osm_record_id(row["record_id"])
        if local_id in local_ids:
            raise BridgeError("duplicate local ID")
        local_ids.add(local_id)
        local_records[local_id] = record_id

    bridge_pairs = set()
    bridge_by_record = {}
    for row in bridges_raw:
        _fields(row, {"id", "record_id", "dataset", "provider", "theme", "type"}, "bridge row")
        if (row["provider"], row["theme"], row["type"], row["dataset"]) != (
                "osm", "buildings", "building", "OpenStreetMap"):
            raise BridgeError("foreign partition, theme, feature type or dataset")
        record_id = _osm_record_id(row["record_id"])
        gers = _gers_id(row["id"])
        pair = (record_id, gers)
        if pair in bridge_pairs:
            raise BridgeError("duplicate bridge mapping row")
        bridge_pairs.add(pair)
        bridge_by_record.setdefault(record_id, set()).add(gers)
    by_gers = {}
    for local_id, record_id in local_records.items():
        for gers in bridge_by_record.get(record_id, ()):
            by_gers.setdefault(gers, set()).add(local_id)

    candidates, ambiguous, missing = [], [], []
    for local_id, record_id in sorted(local_records.items()):
        gers_ids = bridge_by_record.get(record_id, set())
        if not gers_ids:
            missing.append(local_id)
        elif len(gers_ids) != 1 or any(len(by_gers[gers]) != 1 for gers in gers_ids):
            ambiguous.append(local_id)
        else:
            candidates.append({"local_id": local_id, "source_record_id": record_id,
                               "overture_feature_id": next(iter(gers_ids))})
    return {
        "schema": SCHEMA,
        "release": expected_release,
        "provider": "osm",
        "local_record_count": len(local_records),
        "bridge_slice_rows": len(bridges_raw),
        "version_exact_bridge_candidates": candidates,
        "ambiguous_local_ids": ambiguous,
        "unmatched_in_provided_slice": missing,
        "bridge_slice_proves_global_absence": False,
        "source_file_original_bytes_verified": False,
        "gers_registry_membership_verified": False,
        "physical_geometry_crosschecked": False,
        "independent_model_input_approved": False,
        "raw_data_import_authorized": False,
        "insured_value_inferred": False,
        "note": "Matches require actual provider release/bridge source receipts and independent current registry check; OSM @version is not silently stripped."
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-release", required=True)
    args = parser.parse_args(argv)
    try:
        result = bridge_osm_buildings(_read(args.input), expected_release=args.expected_release)
    except (BridgeError, OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
