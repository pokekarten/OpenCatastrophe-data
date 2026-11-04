# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Official BGT bebouwing -> BAG pand identifier evidence (offline, aggregate-only).

The BRK Kadastrale Kaart bebouwing collection is derived from BGT and
contains identificatie_bag_pnd. This provides a direct cadastral-map-building
to BAG building identifier route. It is NOT a property title, parcel,
dwelling, ownership, policy, insurance limit or independent height source.

The bounded GeoJSON inputs must be acquired and rights-reviewed separately.
No download, model admission, raw IDs, or full address/owner output is produced.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from scripts.audit_pdok_brk_bag_centroid_v0 import (
    ALLOWED_SNAPSHOT_GAP_SECONDS, ParcelBagError, _bbox, _collection, load,
)


def audit(bgt, bag, *, bbox):
    bounds = _bbox(bbox)
    bgt_time, building_geometries = _collection(bgt, "parcel", bounds)
    bag_time, bag_buildings = _collection(bag, "building", bounds)
    gap = abs((bgt_time - bag_time).total_seconds())
    if gap > ALLOWED_SNAPSHOT_GAP_SECONDS:
        raise ParcelBagError("BGT and BAG snapshots are more than a day apart")

    bag_status_by_id = {}
    for bag_id, props, _geometry in bag_buildings:
        status = props.get("status")
        if not isinstance(status, str) or not status:
            raise ParcelBagError("BAG building missing status")
        bag_status_by_id[bag_id] = status

    linked_bag_ids = Counter()
    bgt_statuses = Counter()
    matched_statuses = Counter()
    matched = unmatched = missing_bag_ref = 0
    for _feature_id, props, _geometry in building_geometries:
        bgt_status = props.get("bgt_status")
        if not isinstance(bgt_status, str) or not bgt_status:
            raise ParcelBagError("BGT building has no lifecycle status")
        bgt_statuses[bgt_status] += 1
        bag_id = props.get("identificatie_bag_pnd")
        if bag_id is None:
            missing_bag_ref += 1
            continue
        if not isinstance(bag_id, str) or not bag_id or bag_id.strip() != bag_id:
            raise ParcelBagError("invalid BGT to BAG identifier")
        if bag_id not in bag_status_by_id:
            unmatched += 1
            continue
        matched += 1
        linked_bag_ids[bag_id] += 1
        matched_statuses[bag_status_by_id[bag_id]] += 1

    return {
        "schema": "pdok-bgt-bag-official-identity-challenge-v0",
        "research_only": True,
        "source_admitted": False,
        "model_input_approved": False,
        "legal_parcel_or_insurance_identity_verified": False,
        "independent_geometry_source_verified": False,
        "bgt_building_feature_count": len(building_geometries),
        "bag_building_feature_count": len(bag_buildings),
        "bgt_direct_id_matched_rows": matched,
        "bgt_without_bag_reference": missing_bag_ref,
        "bgt_with_bag_id_absent_in_sample": unmatched,
        "matched_distinct_bag_ids": len(linked_bag_ids),
        "bag_ids_with_multiple_bgt_geometries": sum(n > 1 for n in linked_bag_ids.values()),
        "bag_without_bgt_geometry_in_sample": len(bag_status_by_id) - len(linked_bag_ids),
        "bgt_status_counts": dict(sorted(bgt_statuses.items())),
        "matched_bag_status_counts": dict(sorted(matched_statuses.items())),
        "source_timestamp_gap_seconds": int(gap),
        "conservation_check_passed": len(building_geometries) == matched + unmatched + missing_bag_ref,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bgt", type=Path, required=True)
    parser.add_argument("--bag", type=Path, required=True)
    parser.add_argument("--bbox", required=True, help="CRS84 west,south,east,north, <= 0.01 degree sides")
    args = parser.parse_args(argv)
    try:
        report = audit(load(args.bgt), load(args.bag),
                       bbox=[float(v) for v in args.bbox.split(",")])
    except (ValueError, OSError) as exc:
        print("INVALID_INPUT: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
