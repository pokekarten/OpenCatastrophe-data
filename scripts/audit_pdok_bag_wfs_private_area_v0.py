# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline bounded, privacy-first BAG WFS verblijfsobject usable-area receipt.

Original provider facts enter ONLY from an already authorized PRIVATE local
GeoJSON file. The URL must prove a narrowly bounded WFS 2.0 GetFeature
request with server-side PropertyName projection. The returned properties
MUST contain precisely five non-address fields. Feature IDs, exact
coordinates/geometry, and per-building/household information are never
emitted. A WFS pandidentificatie is ONE displayed reference: do not assume
that it captures all pand[] references of the newer BAG OGC API v2.

Research diagnostics only, never a replacement-cost or TIV calculation.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, urlsplit

ALLOWED_PATH = "/kadaster/bag/wfs/v2_0"
ALLOWED_FIELDS = frozenset({
    "identificatie", "oppervlakte", "pandidentificatie", "status", "gebruiksdoel"
})
MAX_BYTES = 1_000_000
MAX_RECORDS = 100
MAX_BBOX_EDGE_METRES = 1000.0
ACTIVE_STATUS = "Verblijfsobject in gebruik"
MIN_CELL_COUNT = 5
ID_RE = re.compile(r"[A-Za-z0-9_.:-]{1,80}\Z")
AREA_LIMIT = 100_000


class BagWfsPrivacyError(ValueError):
    """Untrusted WFS request, unsafe source data, or incomplete page."""


def _unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise BagWfsPrivacyError("duplicate JSON key")
        out[key] = value
    return out


def _bad_constant(_value):
    raise BagWfsPrivacyError("invalid nonfinite JSON value")


def load_private(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise BagWfsPrivacyError("private input exceeds 1MB bound")
    return json.loads(p.read_text(encoding="utf-8"),
                      object_pairs_hook=_unique_pairs,
                      parse_constant=_bad_constant)


def validate_wfs_request(url):
    if not isinstance(url, str):
        raise BagWfsPrivacyError("missing explicit original WFS request URL")
    u = urlsplit(url)
    if (u.scheme != "https" or u.netloc != "service.pdok.nl"
            or u.path != ALLOWED_PATH or u.fragment):
        raise BagWfsPrivacyError("untrusted provider host/path")
    pairs = parse_qsl(u.query, keep_blank_values=True, strict_parsing=True)
    params = {}
    for key, value in pairs:
        if key in params:
            raise BagWfsPrivacyError("duplicate WFS request parameter")
        params[key] = value
    expected = {
        "service", "version", "request", "typeNames", "count",
        "outputFormat", "propertyName", "bbox"
    }
    if set(params) != expected:
        raise BagWfsPrivacyError("missing/extra WFS query parameters")
    for key, val in {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "bag:verblijfsobject",
        "outputFormat": "application/json",
    }.items():
        if params[key] != val:
            raise BagWfsPrivacyError("wrong WFS query contract: " + key)
    requested_fields = params["propertyName"].split(",")
    if (len(requested_fields) != len(ALLOWED_FIELDS)
            or set(requested_fields) != ALLOWED_FIELDS):
        raise BagWfsPrivacyError("provider must select exactly five safe fields")
    if not params["count"].isdecimal():
        raise BagWfsPrivacyError("invalid count")
    count = int(params["count"])
    if not 1 <= count <= MAX_RECORDS:
        raise BagWfsPrivacyError("unbounded or invalid feature limit")
    try:
        coordinates = params["bbox"].split(",")
        if len(coordinates) != 5 or coordinates[4] != "EPSG:28992":
            raise ValueError("bbox must be EPSG:28992")
        nums = [float(s) for s in coordinates[:4]]
        if not all(math.isfinite(v) for v in nums):
            raise ValueError("non-finite RD New coordinates")
        xmin, ymin, xmax, ymax = nums
        if not (0 <= xmin < xmax <= 300_000
                and 250_000 <= ymin < ymax <= 700_000):
            raise ValueError("bbox outside plausible Netherlands RD New bounds")
        if xmax - xmin > MAX_BBOX_EDGE_METRES or ymax - ymin > MAX_BBOX_EDGE_METRES:
            raise ValueError("bbox too wide for bounded private pilot")
    except ValueError as exc:
        raise BagWfsPrivacyError("invalid, oversized or wrongly projected bbox") from exc
    return {"bbox": tuple(nums), "count": count}


def _check_id(value):
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


def audit(doc, *, source_url):
    request = validate_wfs_request(source_url)
    if not isinstance(doc, dict) or doc.get("type") != "FeatureCollection":
        raise BagWfsPrivacyError("not a WFS GeoJSON FeatureCollection")
    if doc.get("name") != "verblijfsobject":
        raise BagWfsPrivacyError("unexpected WFS feature typename")
    crs = doc.get("crs")
    if (not isinstance(crs, dict) or crs.get("type") != "name"
            or crs.get("properties", {}).get("name")
            != "urn:ogc:def:crs:EPSG::28992"):
        raise BagWfsPrivacyError("wrong source CRS; RD New explicitly required")
    features = doc.get("features")
    if not isinstance(features, list) or len(features) > request["count"]:
        raise BagWfsPrivacyError("unbounded feature count")
    # Do not silently aggregate an incomplete page; source count can exceed
    # the requested count and must be handled by separately bounded samples.
    if type(doc.get("numberMatched")) is not int or doc["numberMatched"] != len(features):
        raise BagWfsPrivacyError("incomplete or invalid numberMatched")
    if any(isinstance(link, dict) and link.get("rel") == "next"
           for link in doc.get("links", [])):
        raise BagWfsPrivacyError("unexpected WFS pagination continuation")
    if any(x not in {"type", "name", "crs", "numberMatched", "features", "bbox"}
           for x in doc):
        raise BagWfsPrivacyError("unexpected root metadata field")

    seen = set()
    active_area = 0
    active_units = 0
    excluded = 0
    refs_observed = 0
    missing_ref = 0
    usages = Counter()
    statuses = Counter()
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise BagWfsPrivacyError("malformed GeoJSON feature")
        if set(feature) - {"type", "properties", "geometry", "bbox"}:
            raise BagWfsPrivacyError("feature contains extra disallowed fields")
        props = feature.get("properties")
        if not isinstance(props, dict) or set(props) != ALLOWED_FIELDS:
            raise BagWfsPrivacyError("address-bearing, incomplete or unexpected property set")
        unit_id = props["identificatie"]
        if not _check_id(unit_id) or unit_id in seen:
            raise BagWfsPrivacyError("unsafe or duplicate source unit identifier")
        seen.add(unit_id)
        area = props["oppervlakte"]
        if type(area) is not int or not 1 <= area <= AREA_LIMIT:
            raise BagWfsPrivacyError("missing or invalid observed unit usable area")
        status = props["status"]
        use = props["gebruiksdoel"]
        if not isinstance(status, str) or not 1 <= len(status) <= 100:
            raise BagWfsPrivacyError("missing or invalid status")
        if not isinstance(use, str) or not 1 <= len(use) <= 200:
            raise BagWfsPrivacyError("missing or invalid occupancy/use")
        reference = props["pandidentificatie"]
        if reference is not None and not _check_id(reference):
            raise BagWfsPrivacyError("unsafe BAG WFS singular pand reference")
        # Geometries can appear even when only selected properties are
        # requested. Never log or retain them in a result; source bbox
        # is an ephemeral query scope, not a public per-feature location.
        geom = feature.get("geometry")
        if not isinstance(geom, dict) or geom.get("type") != "Point":
            raise BagWfsPrivacyError("expected original BAG WFS unit point")
        if not isinstance(geom.get("coordinates"), list):
            raise BagWfsPrivacyError("unexpected unit geometry shape")

        statuses[status] += 1
        if status == ACTIVE_STATUS:
            active_units += 1
            active_area += area
            usages[use] += 1
            if reference is None:
                missing_ref += 1
            else:
                refs_observed += 1
        else:
            excluded += 1

    if active_units != refs_observed + missing_ref:
        raise BagWfsPrivacyError("unit-reference conservation failed")
    # Publish NO per-use cells below the privacy threshold. The overall
    # result is itself suppressed if <5 in-use units appear in the bbox.
    publishable = active_units >= MIN_CELL_COUNT
    grouped = {name: count for name, count in sorted(usages.items())
               if count >= MIN_CELL_COUNT and publishable}
    return {
        "schema": "bag-wfs-projected-unit-area-private-qa-v0",
        "analysis_only": True,
        "source": "PDOK BAG WFS 2.0 verblijfsobject",
        "source_projection_fields_verified": True,
        "source_contains_address_fields_in_returned_properties": False,
        "provider_geometry_included_in_output": False,
        "individual_source_ids_included_in_output": False,
        "source_admitted": False,
        "insured_tiv_verified": False,
        "per_building_usable_area_assigned": False,
        "complete_multi_pand_links_verified": False,
        "wfs_pandidentificatie_semantics": "singular_legacy_reference_not_multi_pand_proof",
        "all_records": len(features) if publishable else None,
        "active_unit_count": active_units if publishable else None,
        "active_usable_area_total_m2": active_area if publishable else None,
        "inactive_unit_count": excluded if publishable else None,
        "active_units_with_singular_wfs_reference": refs_observed if publishable else None,
        "active_units_without_wfs_reference": missing_ref if publishable else None,
        "active_usage_groups_minimum_5": grouped,
        "count_suppressed_for_privacy": not publishable,
        "status_groups_not_published_for_privacy": True,
        "conservation_check_passed": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="Private bounded BAG-WFS GeoJSON, never commit")
    parser.add_argument("--source-url", required=True,
                        help="Exact trusted server-side projected WFS request URL")
    args = parser.parse_args(argv)
    try:
        result = audit(load_private(args.input), source_url=args.source_url)
    except (OSError, ValueError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
