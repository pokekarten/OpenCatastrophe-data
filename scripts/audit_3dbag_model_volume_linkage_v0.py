# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Private original BAG WFS -> 3DBAG Building volume identity challenge.

Offline only. The WFS output is from the verified five-field BAG projection.
3DBAG requests are expected to be the individual /collections/pand/items/
NL.IMBAG.Pand.{BAG_ID} endpoints. We verify exact CityJSONFeature Building
identity and model-geometry volume validity, reporting only >=5-building
aggregate LoD values. The CityJSON 2.0 *format* is NOT a pinned 3DBAG release.

No output may include per-building volumes, BAG IDs, coordinates, residents,
addresses, insurers, policies, replacement costs or actual insured TIV.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sys

if __package__:
    from .audit_pdok_bag_wfs_private_area_v0 import (
        BagWfsPrivacyError, ROOT, audit as audit_wfs, load_private,
    )
else:
    from audit_pdok_bag_wfs_private_area_v0 import (
        BagWfsPrivacyError, ROOT, audit as audit_wfs, load_private,
    )

BAG_ID = re.compile(r"\d{16}\Z")
CITYJSON_REFERENCE_SYSTEM = "https://www.opengis.net/def/crs/EPSG/0/7415"
MODEL_PREFIX = "NL.IMBAG.Pand."
LODS = ("lod12", "lod13", "lod22")
MIN_PUBLIC_GROUP = 5
MAX_SOURCE_MODELS = 15
MAX_MODEL_FILE_BYTES = 1_000_000
MAX_VOLUME_M3 = 100_000_000


class ModelledVolumeError(ValueError):
    """Unable to validate an original-source, private 3DBAG object response."""


def _parse_private_model(path):
    p = Path(path).resolve()
    if p == ROOT or ROOT in p.parents:
        raise ModelledVolumeError("original 3DBAG bytes must remain outside Git checkout")
    if p.stat().st_size > MAX_MODEL_FILE_BYTES:
        raise ModelledVolumeError("3DBAG per-building response over size budget")
    return load_private(p)


def _original_building(doc):
    """Return a verified BAG ref and nullable LoD metrics, never a raw ID report."""
    if not isinstance(doc, dict):
        raise ModelledVolumeError("3DBAG item response must be an object")
    meta = doc.get("metadata")
    if (not isinstance(meta, dict) or meta.get("type") != "CityJSON"
            or meta.get("version") != "2.0"
            or not isinstance(meta.get("metadata"), dict)
            or meta["metadata"].get("referenceSystem") != CITYJSON_REFERENCE_SYSTEM):
        raise ModelledVolumeError("unverified CityJSON 2.0 metadata or EPSG:7415 CRS")
    f = doc.get("feature")
    if not isinstance(f, dict) or f.get("type") != "CityJSONFeature":
        raise ModelledVolumeError("expected one CityJSONFeature, not a page")
    fid = f.get("id")
    if not isinstance(fid, str) or not fid.startswith(MODEL_PREFIX):
        raise ModelledVolumeError("unexpected 3DBAG building ID namespace")
    bag_id = fid[len(MODEL_PREFIX):]
    if not BAG_ID.fullmatch(bag_id):
        raise ModelledVolumeError("invalid 16-digit official BAG pand identifier")
    objs = f.get("CityObjects")
    if not isinstance(objs, dict) or fid not in objs:
        raise ModelledVolumeError("missing matching parent 3DBAG Building")
    parent = objs[fid]
    if not isinstance(parent, dict) or parent.get("type") != "Building":
        raise ModelledVolumeError("matching BAG identity is not a Building object")
    attrs = parent.get("attributes")
    if not isinstance(attrs, dict):
        raise ModelledVolumeError("missing model attributes")
    quality = attrs.get("b3_kwaliteitsindicator")
    if type(quality) is not bool:
        raise ModelledVolumeError("missing model quality marker")

    volumes = {}
    invalid_lods = set()
    for lod in LODS:
        vol = attrs.get("b3_volume_" + lod)
        val3dity = attrs.get("b3_val3dity_" + lod)
        # Nonempty val3dity code list is a real geometry QA issue and must
        # NOT be silently replaced with a geometrically plausible volume.
        if not isinstance(val3dity, str):
            raise ModelledVolumeError("missing 3D validity-code field")
        if val3dity != "[]":
            invalid_lods.add(lod)
            volumes[lod] = None
        elif (type(vol) not in (float, int) or not math.isfinite(vol)
              or not 0 < vol <= MAX_VOLUME_M3):
            volumes[lod] = None
        else:
            volumes[lod] = float(vol)

    return bag_id, quality, invalid_lods, volumes


def audit(wfs, model_docs, *, wfs_source_url):
    if not isinstance(model_docs, list) or not 1 <= len(model_docs) <= MAX_SOURCE_MODELS:
        raise ModelledVolumeError("invalid bounded 3DBAG model-response count")
    # Reuse the audited WFS identity, projection, bounding, privacy and
    # numberMatched==features completeness contract.
    safe_wfs = audit_wfs(wfs, source_url=wfs_source_url)
    if not safe_wfs["conservation_check_passed"]:
        raise ModelledVolumeError("WFS completeness guard failed")
    observed = wfs["features"]
    expected = {
        str(f["properties"]["pandidentificatie"])
        for f in observed
        if (f["properties"]["status"] == "Verblijfsobject in gebruik"
            and f["properties"]["pandidentificatie"] is not None)
    }
    if any(not BAG_ID.fullmatch(v) for v in expected):
        raise ModelledVolumeError("WFS reference not a 16-digit BAG pand ID")
    if len(expected) > MAX_SOURCE_MODELS:
        raise ModelledVolumeError("source references exceed individual-model budget")
    if not expected:
        raise ModelledVolumeError("no explicit active BAG building refs")

    seen = set()
    modelled = 0
    invalid_by_lod = Counter()
    quality_fails = 0
    values_by_lod = {lod: [] for lod in LODS}
    for doc in model_docs:
        bag_id, quality, invalid_lods, vols = _original_building(doc)
        if bag_id not in expected or bag_id in seen:
            raise ModelledVolumeError("unexpected or duplicate 3DBAG BAG ID")
        seen.add(bag_id)
        modelled += 1
        if not quality:
            quality_fails += 1
        for lod in LODS:
            if lod in invalid_lods:
                invalid_by_lod[lod] += 1
            if quality and vols[lod] is not None:
                values_by_lod[lod].append(vols[lod])

    if modelled > len(expected):
        raise ModelledVolumeError("invalid 3DBAG response cardinality")
    summary = {}
    for lod in LODS:
        count = len(values_by_lod[lod])
        summary[lod] = {
            "valid_model_count": count,
            "invalid_3d_geometry_code_count": invalid_by_lod[lod],
            "sum_modelled_volume_m3": (
                round(math.fsum(values_by_lod[lod]), 2)
                if count >= MIN_PUBLIC_GROUP else None
            ),
            "volume_suppressed_below_five": count < MIN_PUBLIC_GROUP,
        }
    return {
        "schema": "bag-to-3dbag-private-volume-linkage-v0",
        "analysis_only": True,
        "wfs_source_checked": True,
        "wfs_address_fields_excluded": True,
        "building_source": "3DBAG API individual CityJSONFeature by official BAG pand ID",
        "wfs_sample_active_units": safe_wfs["active_unit_count"],
        "distinct_expected_bag_pand_refs": len(expected),
        "distinct_3dbag_building_id_matches": len(seen),
        "expected_buildings_without_supplied_3dbag_model": len(expected) - len(seen),
        "models_with_quality_marker_false": quality_fails,
        "volumes_by_lod": summary,
        "model_3d_reference_system": "EPSG:7415",
        "cityjson_format_version": "2.0",
        "exact_3dbag_release_verified": False,
        "complete_multi_pand_relation_verified": False,
        "source_rights_reviewed": False,
        "source_admitted": False,
        "replacement_cost_estimated": False,
        "real_insured_tiv_or_policy_verified": False,
        "no_raw_ids_or_geometries_in_output": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wfs", type=Path, required=True,
                        help="private complete five-field BAG WFS GeoJSON response")
    parser.add_argument("--wfs-source-url", required=True)
    parser.add_argument("--models", type=Path, nargs="+", required=True,
                        help="private individual 3DBAG item JSON files")
    args = parser.parse_args(argv)
    try:
        if len(args.models) > MAX_SOURCE_MODELS:
            raise ModelledVolumeError("too many models")
        doc = load_private(args.wfs)
        data = [_parse_private_model(p) for p in args.models]
        out = audit(doc, data, wfs_source_url=args.wfs_source_url)
    except (ValueError, OSError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
