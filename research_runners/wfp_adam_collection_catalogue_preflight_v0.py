#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, source-sha-bound ADAM OGC catalogue preflight.

Input is independently captured *catalogue metadata* from the WFP ADAM
GET /api/collections endpoint. Does not make a network request or fetch event
features, and does not grant source rights or scientific model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE_ID = "wfp.adam.ogc-global-disaster-impact"
PROFILE = "wfp-adam-ogc-collections-metadata-preflight-v0"
PROVIDER_URL = "https://api.adam.geospatial.wfp.org/api/collections"
MAX_BYTES = 262_144
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
EXPECTED_IDS = frozenset({
    "adam.adam_eq_events",
    "adam.adam_fl_events",
    "adam.adam_fl_alerts",
    "adam.adam_fl_alerts_mom_forecast",
    "adam.adam_fl_glofas_gauges_forecast",
    "adam.adam_ts_events",
    "adam.adam_ts_tracks",
    "adam.adam_ts_buffers",
    "adam.adam_ts_nodes",
    "adam.adam_ts_disturbance_events",
    "adam.adam_ts_disturbance_tracks",
    "adam.adam_ts_disturbance_buffers",
    "adam.adam_ts_disturbance_nodes",
})


class ADAMCatalogueError(ValueError):
    """WFP ADAM provider metadata differs from the pinned expectations."""


def _object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ADAMCatalogueError("duplicate provider JSON key")
        obj[key] = value
    return obj


def _nonfinite(_value):
    raise ADAMCatalogueError("non-finite provider JSON number")


def inspect_adam_catalogue_bytes(blob: bytes, expected_sha256: str) -> dict:
    if type(expected_sha256) is not str or not DIGEST.fullmatch(expected_sha256):
        raise ADAMCatalogueError("expected SHA256 must be independent lowercase hex")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise ADAMCatalogueError("catalogue response missing or exceeds metadata byte cap")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha256:
        raise ADAMCatalogueError("source catalogue SHA256 mismatch")
    try:
        payload = json.loads(blob.decode("utf-8"), object_pairs_hook=_object,
                             parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ADAMCatalogueError("catalogue must be strict UTF-8 JSON") from exc
    if type(payload) is not dict or type(payload.get("collections")) is not list:
        raise ADAMCatalogueError("expected OGC collection listing")
    collections = payload["collections"]
    if len(collections) != 13:
        raise ADAMCatalogueError("collection count differs from documented 13")
    ids = []
    for row in collections:
        if type(row) is not dict or type(row.get("id")) is not str:
            raise ADAMCatalogueError("collection ID missing")
        if type(row.get("title")) is not str or not row["title"].strip():
            raise ADAMCatalogueError("collection title missing")
        if type(row.get("links")) is not list or not row["links"]:
            raise ADAMCatalogueError("collection links absent")
        ids.append(row["id"])
    if set(ids) != EXPECTED_IDS or len(set(ids)) != len(ids):
        raise ADAMCatalogueError("undocumented, missing or duplicated ADAM collection ID")
    links = payload.get("links")
    if type(links) is not list:
        raise ADAMCatalogueError("catalogue pagination links missing")
    if any(type(link) is not dict or type(link.get("rel")) is not str for link in links):
        raise ADAMCatalogueError("invalid catalogue pagination links")
    if any(link.get("rel") == "next" for link in links):
        raise ADAMCatalogueError("partial paginated catalogue not accepted")
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "source_catalogue_url": PROVIDER_URL,
        "source_response_sha256": digest,
        "source_metadata_bytes": len(blob),
        "documented_collection_count": len(ids),
        "earthquake_collection_count": 1,
        "flood_collection_count": 4,
        "tropical_cyclone_collection_count": 8,
        "metadata_only": True,
        "events_or_footprints_downloaded": False,
        "independent_observed_damage_verified": False,
        "upstream_correlation_reviewed": False,
        "commercial_reuse_approved": False,
        "source_admitted_for_model_use": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider_catalogue_json", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.provider_catalogue_json.resolve() == args.out.resolve():
        parser.error("refusing to overwrite the original provider catalogue")
    try:
        profile = inspect_adam_catalogue_bytes(
            args.provider_catalogue_json.read_bytes(), args.expected_sha256,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ADAMCatalogueError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
