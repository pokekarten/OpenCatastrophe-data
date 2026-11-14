#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline WFS-vs-2016-site negative control from reviewed ORIGINAL publisher metadata.

No WFS GetFeature, original shapefile, polygons or dates are acquired here.
An advertised WGS84 bounding box is only a necessary, not sufficient,
condition for coverage. A source covering many historical floods cannot
validate the 2016 Loing event solely because its bbox might overlap.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

class SourceScopeBlocked(ValueError):
    """Unreviewed source or incompatible metadata."""

# Exactly sourced first-party facts. Publisher data.gouv licence=lov2, its
# linked Geo-IDE public WFS GetCapabilities was returned by a bounded
# public service metadata query. This is NOT a feature/asset receipt.
_REVIEWED_ID = "67377bc98609c51859c40b28"
_SOURCE_KIND = "MULTI_EVENT_HISTORICAL_FLOOD_ENVELOPE"
_SITE_ID = "CER_LO_16_S_174"
_SITE_WGS84 = (Decimal("2.72937190"), Decimal("48.00108820"))
# Original WFS GetCapabilities WGS84 lower/upper corner, NOT measured 2016.
_REVIEWED_WFS_BBOX = tuple(map(Decimal, (
    "2.76257501317139", "48.0382890910261",
    "3.13472665244762", "48.1469782244935"
)))
_NUM = re.compile(r"-?(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,14})?")


def _number(value):
    if not isinstance(value, str) or not _NUM.fullmatch(value):
        raise SourceScopeBlocked("coordinates must be bounded decimal WGS84 strings")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise SourceScopeBlocked("invalid WGS84 decimal") from exc


def audit_scope(candidate):
    if not isinstance(candidate, dict) or set(candidate) != {
        "dataset_id", "source_role", "site_id", "site_wgs84_lon_lat",
        "advertised_wfs_wgs84_bbox"
    }:
        raise SourceScopeBlocked("required published dataset/site/bbox fields only")
    if candidate["dataset_id"] != _REVIEWED_ID:
        raise SourceScopeBlocked("not the first-party reviewed Loiret dataset")
    if candidate["source_role"] != _SOURCE_KIND:
        raise SourceScopeBlocked("source is neither single flood nor certified observations")
    if candidate["site_id"] != _SITE_ID:
        raise SourceScopeBlocked("test site identity differs from the official 2016 marker")
    point = candidate["site_wgs84_lon_lat"]
    box = candidate["advertised_wfs_wgs84_bbox"]
    if not isinstance(point, list) or len(point) != 2:
        raise SourceScopeBlocked("WGS84 site must be [lon,lat]")
    if not isinstance(box, list) or len(box) != 4:
        raise SourceScopeBlocked("WFS envelope must be [west,south,east,north]")
    actual = tuple(_number(x) for x in point)
    bounds = tuple(_number(x) for x in box)
    if actual != _SITE_WGS84 or bounds != _REVIEWED_WFS_BBOX:
        raise SourceScopeBlocked("unreviewed original coordinate or WFS metadata version")
    west, south, east, north = bounds
    lon, lat = actual
    if not (Decimal(-180) <= west < east <= Decimal(180) and
            Decimal(-90) <= south < north <= Decimal(90)):
        raise SourceScopeBlocked("invalid WFS advertised coordinate envelope")
    site_inside_bbox = west <= lon <= east and south <= lat <= north
    # For reviewed official metadata this MUST be false; if it becomes true,
    # the original frozen-source contract must undergo separate scientific review.
    if site_inside_bbox:
        raise SourceScopeBlocked("unexpected source scope changed, manual re-review required")
    return {
        "profile": "ddt45-horsppri-clery-wfs-montargis-negative-control-v0",
        "catalogue_dataset_id": _REVIEWED_ID,
        "provider": "DDT Loiret / Geo-IDE",
        "catalogue_dataset_licence": "Licence Ouverte 2.0",
        "source_semantics": _SOURCE_KIND,
        "test_site_id": _SITE_ID,
        "test_site_wgs84_lon_lat": [str(x) for x in actual],
        "wfs_advertised_wgs84_bbox": [str(x) for x in bounds],
        "published_wfs_bbox_contains_montargis_2016_mark": False,
        "layer_is_independent_montargis_2016_extent": False,
        "layer_is_2016_event_specific": False,
        "provider_geometry_bytes_acquired_or_sha256_attested": False,
        "provider_feature_schema_or_topology_verified": False,
        "individual_flood_event_date_per_feature_verified": False,
        "building_2016_depth_or_loss_admitted": False,
        "scientific_verdict": "SPATIALLY_EXCLUDED_AND_TEMPORALLY_MIXED_FOR_MONTARGIS_2016",
    }


def _strict_keys(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise SourceScopeBlocked("duplicate JSON key")
        obj[k] = v
    return obj


def _reject_nonfinite(_):
    raise SourceScopeBlocked("nonfinite JSON number")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        path = args.metadata_json
        if not path.is_file() or path.stat().st_size > 4096:
            raise SourceScopeBlocked("bounded local metadata file required")
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_keys,
                         parse_constant=_reject_nonfinite)
        result = audit_scope(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, SourceScopeBlocked) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
