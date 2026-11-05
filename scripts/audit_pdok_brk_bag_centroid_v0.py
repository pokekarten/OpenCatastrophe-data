# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded, aggregate-only PDOK BRK parcel ↔ BAG building centroid challenge.

Offline research diagnostic. It never downloads data, returns object IDs,
confirms parcel/building identity, or approves data for insurance models.
Two current CRS84 GeoJSON collections MUST come from a *small shared bbox*.
A centroid inside a parcel is only a potential spatial relation, not legal
ownership, precise parcel boundary, insured location, or valid 1:1 join.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys

MAX_BYTES = 2_000_000
MAX_FEATURES = 1000
MAX_COORDS = 100_000
ALLOWED_SNAPSHOT_GAP_SECONDS = 86400
ACTIVE_STATUS = "Pand in gebruik"
FORBIDDEN_PROPERTY = re.compile(
    r"(eigenaar|owner|grundbuch|boekingsblad|buchungsblatt|postcode|"
    r"huisnummer|address|adres|title_number|persoon)", re.IGNORECASE
)


class ParcelBagError(ValueError):
    """Malformed, unsafe or incomplete PDOK source snapshot."""


def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ParcelBagError("duplicate JSON key")
        out[key] = value
    return out


def _no_constant(value):
    raise ParcelBagError("nonfinite JSON number")


def load(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ParcelBagError("file exceeds 2MB budget")
    return json.loads(p.read_text(encoding="utf-8"),
                      object_pairs_hook=_object, parse_constant=_no_constant)


def _stamp(value):
    if not isinstance(value, str):
        raise ParcelBagError("missing source timestamp")
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ParcelBagError("invalid timestamp") from exc
    if ts.tzinfo is None:
        raise ParcelBagError("source timestamp must have timezone")
    return ts.astimezone(timezone.utc)


def _bbox(value):
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise ParcelBagError("bbox needs west,south,east,north")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
        raise ParcelBagError("bbox coordinates must be finite")
    w, s, e, n = value
    if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
        raise ParcelBagError("bbox invalid or axis order reversed")
    if e - w > 0.01 or n - s > 0.01:
        raise ParcelBagError("research bbox exceeds 0.01 degrees")
    return w, s, e, n


def _rings(geometry):
    if not isinstance(geometry, dict) or set(geometry) != {"type", "coordinates"}:
        raise ParcelBagError("expected GeoJSON polygon geometry")
    kind = geometry["type"]
    source = geometry["coordinates"]
    if kind == "Polygon":
        polys = [source]
    elif kind == "MultiPolygon":
        polys = source
    else:
        raise ParcelBagError("only Polygon/MultiPolygon accepted")
    if not isinstance(polys, list) or not polys:
        raise ParcelBagError("empty polygons")
    count = 0
    for poly in polys:
        if not isinstance(poly, list) or not poly:
            raise ParcelBagError("missing polygon outer ring")
        for ring in poly:
            if not isinstance(ring, list) or len(ring) < 4:
                raise ParcelBagError("invalid ring")
            if ring[0] != ring[-1]:
                raise ParcelBagError("ring is not closed")
            for p in ring:
                count += 1
                if count > MAX_COORDS or not isinstance(p, list) or len(p) != 2:
                    raise ParcelBagError("invalid or oversized coordinate list")
                if not all(type(v) in (float, int) and math.isfinite(v) for v in p):
                    raise ParcelBagError("nonfinite coordinate")
                if not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90):
                    raise ParcelBagError("coordinate outside CRS84")
    return polys


def _area_centroid(ring):
    # Recenter before shoelace products to avoid catastrophic cancellation
    # with coordinates such as (5.1202, 52.0902) and metre-sized buildings.
    x0, y0 = ring[0]
    a = cx = cy = 0.0
    for p, q in zip(ring, ring[1:]):
        px, py = p[0] - x0, p[1] - y0
        qx, qy = q[0] - x0, q[1] - y0
        cross = px * qy - qx * py
        a += cross
        cx += (px + qx) * cross
        cy += (py + qy) * cross
    if abs(a) < 1e-18:
        raise ParcelBagError("degenerate outer polygon")
    return abs(a), (x0 + cx / (3 * a), y0 + cy / (3 * a))


def _ring_point(pt, ring):
    """Return -1 for boundary, 0 for outside, 1 for inside."""
    x, y = pt
    inside = False
    for p, q in zip(ring, ring[1:]):
        ax, ay = p
        bx, by = q
        cr = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
        if abs(cr) < 1e-13 and min(ax, bx) - 1e-12 <= x <= max(ax, bx) + 1e-12 and min(ay, by) - 1e-12 <= y <= max(ay, by) + 1e-12:
            return -1
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    return int(inside)


def _in_polys(pt, polys):
    unknown = False
    for rings in polys:
        outer = _ring_point(pt, rings[0])
        if outer == -1:
            unknown = True
            continue
        if outer == 0:
            continue
        holes = [_ring_point(pt, ring) for ring in rings[1:]]
        if -1 in holes:
            unknown = True
        elif not any(v == 1 for v in holes):
            return 1
    return -1 if unknown else 0


def _collection(doc, kind, bbox):
    if not isinstance(doc, dict) or doc.get("type") != "FeatureCollection":
        raise ParcelBagError("not a GeoJSON FeatureCollection")
    stamp = _stamp(doc.get("timeStamp"))
    if any(isinstance(link, dict) and link.get("rel") == "next" for link in doc.get("links", [])):
        raise ParcelBagError("pagination: query is incomplete; narrow bbox")
    feats = doc.get("features")
    if not isinstance(feats, list) or not 0 < len(feats) <= MAX_FEATURES:
        raise ParcelBagError("collection missing or outside feature-count limit")
    if doc.get("numberReturned") != len(feats):
        raise ParcelBagError("numberReturned mismatch or absent")
    output = []
    seen = set()
    for raw in feats:
        if not isinstance(raw, dict) or raw.get("type") != "Feature":
            raise ParcelBagError("invalid GeoJSON feature")
        props = raw.get("properties")
        if not isinstance(props, dict) or any(FORBIDDEN_PROPERTY.search(k) for k in props):
            raise ParcelBagError("forbidden or malformed property field")
        key = "identificatie_lokaal_id" if kind == "parcel" else "identificatie"
        identity = props.get(key)
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ParcelBagError("missing or duplicate safe source identity")
        seen.add(identity)
        polys = _rings(raw.get("geometry"))
        xs = [p[0] for rings in polys for ring in rings for p in ring]
        ys = [p[1] for rings in polys for ring in rings for p in ring]
        if max(xs) < bbox[0] or min(xs) > bbox[2] or max(ys) < bbox[1] or min(ys) > bbox[3]:
            raise ParcelBagError("feature geometry lies outside requested bbox")
        output.append((identity, props, polys))
    return stamp, output


def audit(parcels, buildings, *, bbox):
    bounds = _bbox(bbox)
    parcel_time, parcel_rows = _collection(parcels, "parcel", bounds)
    bag_time, bag_rows = _collection(buildings, "building", bounds)
    gap = abs((parcel_time - bag_time).total_seconds())
    if gap > ALLOWED_SNAPSHOT_GAP_SECONDS:
        raise ParcelBagError("source snapshots are more than a day apart")
    eligible = [(p, polygons) for p, attr, polygons in parcel_rows
                if attr.get("status_historie_waarde") == "Geldig"]
    statuses = Counter()
    active = one = none = multiple = outside = ambiguous = 0
    parcel_building_links = Counter()
    for building_id, props, polys in bag_rows:
        status = props.get("status")
        if not isinstance(status, str):
            raise ParcelBagError("building has no status")
        statuses[status] += 1
        if status != ACTIVE_STATUS:
            continue
        active += 1
        # Use the largest outer geometry only; a multi-part building's centroid
        # cannot be interpreted as physical coverage of all components.
        outer = max((ring_list[0] for ring_list in polys),
                    key=lambda ring: _area_centroid(ring)[0])
        center = _area_centroid(outer)[1]
        if _in_polys(center, polys) != 1:
            outside += 1
            continue
        hits = [id_ for id_, poly in eligible if _in_polys(center, poly) == 1]
        uncertain = any(_in_polys(center, poly) == -1 for _, poly in eligible)
        if uncertain:
            ambiguous += 1
            continue
        if not hits:
            none += 1
        elif len(hits) == 1:
            one += 1
            parcel_building_links[hits[0]] += 1
        else:
            multiple += 1
    return {
        "schema": "pdok-brk-bag-centroid-candidate-qa-v0",
        "research_only": True,
        "source_admitted": False,
        "model_input_approved": False,
        "exact_polygon_intersection_verified": False,
        "legal_property_or_insurer_identity_verified": False,
        "bbox_crs": "OGC:CRS84",
        "parcel_source": "PDOK BRK Kadastrale Kaart OGC v1 perceel",
        "building_source": "PDOK BAG OGC v2 pand",
        "parcel_feature_count": len(parcel_rows),
        "eligible_parcel_count": len(eligible),
        "bag_building_feature_count": len(bag_rows),
        "bag_status_counts": dict(sorted(statuses.items())),
        "active_building_count": active,
        "active_centroid_in_one_parcel_candidate": one,
        "active_centroid_in_multiple_parcel_candidates": multiple,
        "active_centroid_no_parcel_candidate": none,
        "active_centroid_outside_own_geometry": outside,
        "active_centroid_on_ambiguous_boundary": ambiguous,
        "eligible_parcels_with_multiple_active_building_centroids": sum(v > 1 for v in parcel_building_links.values()),
        "source_timestamp_gap_seconds": int(gap),
        "conservation_check_passed": active == one + multiple + none + outside + ambiguous,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parcels", type=Path, required=True)
    parser.add_argument("--buildings", type=Path, required=True)
    parser.add_argument("--bbox", required=True, help="CRS84 west,south,east,north; <=0.01 degree sides")
    args = parser.parse_args(argv)
    try:
        report = audit(load(args.parcels), load(args.buildings),
                       bbox=[float(x) for x in args.bbox.split(",")])
    except (ValueError, OSError) as exc:
        print("INVALID_INPUT: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
