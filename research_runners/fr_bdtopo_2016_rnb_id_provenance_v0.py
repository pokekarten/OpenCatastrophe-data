#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original v2.1 historical BD TOPO DBF ID/provenance preflight vs current RNB.

Only a tiny AOI and exactly two public RNB IDs, no raw historical record
IDs, geometries, addresses, or current RNB external IDs printed/persisted.
2016 v2.1 IDs cannot be presumed stable across version 3.0 and 2023.
A record's computer creation/edit date != physical building construction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import shapefile
from pyproj import Transformer
from shapely.geometry import box, shape as as_shape

from research_runners.fr_bdtopo_2016_d077_bounded_buildings_v0 import (
    EXPECTED_CRS, FAMILIES, MAX_CANDIDATES, PONTHIERRY_LONLAT_BBOX,
)
from research_runners.fr_bdtopo_2016_rnb_polygon_bridge_v0 import (
    BridgeError, RNB_IDS, RNB_PILOT_GUARD,
    bounded_rnb_bytes, current_rnb_shape,
)

ID_FIELDS = frozenset(("ID", "ID_SOURCE", "ID_BDTOPO", "ID_BAT"))
DATE_FIELDS = frozenset(("DATE_CREAT", "DATE_MAJ", "DATE_APP", "DATE_CONF"))
DATE_PATTERN = re.compile(r"^(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})(?:.*)?$")
MAX_DB_FIELDS = 200
MAX_FIELD_NAME_LEN = 40


def bounded_historical_attribute_receipts(folder: Path) -> tuple[list[dict], dict]:
    if folder.is_symlink() or not folder.is_dir():
        raise BridgeError("expected non-symlink local historical extraction")
    t = Transformer.from_crs(4326, 2154, always_xy=True)
    x0,y0,x1,y1 = PONTHIERRY_LONLAT_BBOX
    xx,yy = t.transform([x0,x1,x0,x1],[y0,y0,y1,y1])
    bounds = min(xx),min(yy),max(xx),max(yy)
    area = box(*bounds)
    records = []
    schema = {}
    total = 0
    for family in FAMILIES:
        parts = [folder / (family+ext) for ext in (".shp",".shx",".dbf",".prj")]
        if any(not p.is_file() or p.is_symlink() for p in parts):
            raise BridgeError("missing or unsafe original DBF geometry components")
        from pyproj import CRS
        if not CRS.from_wkt(parts[-1].read_text(encoding="utf-8-sig")).equals(
            EXPECTED_CRS,ignore_axis_order=True
        ):
            raise BridgeError("old original DBF CRS cannot be verified")
        with shapefile.Reader(str(parts[0]),encoding="utf-8") as reader:
            fields = [str(item[0]) for item in reader.fields[1:]]
            if (not fields or len(fields)>MAX_DB_FIELDS or
                any(len(f)>MAX_FIELD_NAME_LEN for f in fields)):
                raise BridgeError("unexpected historical DBF field schema")
            schema[family] = fields
            for selected_family_index, sr in enumerate(reader.iterShapeRecords(bbox=bounds)):
                total += 1
                if total > MAX_CANDIDATES:
                    raise BridgeError("unbounded original DBF feature scan")
                geom = as_shape(sr.shape.__geo_interface__)
                if geom.is_empty or not geom.is_valid:
                    raise BridgeError("invalid original 2016 polygon")
                if not geom.intersects(area):
                    continue
                raw = sr.record.as_dict()
                keys = {str(k).upper(): k for k in raw}
                id_hash = {}
                for key in sorted(ID_FIELDS & set(keys)):
                    value = raw.get(keys[key])
                    if value is None:
                        continue
                    val = str(value).strip()
                    if 0 < len(val) <= 300:
                        id_hash[key] = {
                            "sha256": hashlib.sha256(val.encode("utf-8")).hexdigest(),
                            "byte_length": len(val.encode("utf-8")),
                        }
                dates = {}
                for key in sorted(DATE_FIELDS & set(keys)):
                    value = raw.get(keys[key])
                    if value is None:
                        continue
                    val = str(value).strip()
                    if len(val) <= 36 and DATE_PATTERN.match(val):
                        dates[key] = val
                    elif val:
                        dates[key] = "[NOT_VALIDATED_AS_DATE]"
                # Identifiers are presented as hash receipts and source field
                # names only; never print raw IDs from third-party original.
                records.append({
                    "original_family": family,
                    "bounded_bbox_iteration_index_not_original_feature_id":
                        selected_family_index,
                    "historic_area_m2": round(float(geom.area),2),
                    "original_id_sha256_by_field": id_hash,
                    "original_temporal_field_values": dates,
                    "original_historic_id_verified_for_cross_version_identity": False,
                })
    if len(records) != 3:
        raise BridgeError("three historical AOI source rows expected")
    return records,schema


def rnb_external_id_receipts(payload: bytes, requested_id: str) -> tuple[list[dict],list[str]]:
    # Retain exact original strings locally for a hash-equality-only crosscheck.
    current_rnb_shape(requested_id,payload)
    try:
        record=json.loads(payload)
    except (UnicodeError,ValueError) as exc:
        raise BridgeError("malformed RNB source JSON") from exc
    ext_ids=record.get("ext_ids") or []
    if not isinstance(ext_ids,list) or len(ext_ids)>30:
        raise BridgeError("unexpected RNB external IDs shape")
    evidence=[]
    exact_bdtopo=[]
    for item in ext_ids:
        if not isinstance(item,dict):
            raise BridgeError("malformed RNB external ID item")
        provider=item.get("source")
        version=item.get("source_version")
        rawid=item.get("id")
        if provider not in ("bdtopo","bdnb") or not isinstance(version,str):
            continue
        if not isinstance(rawid,str) or not 0<len(rawid)<300:
            continue
        evidence.append({
            "source":provider,
            "source_version":version[:60],
            "id_sha256":hashlib.sha256(rawid.strip().encode("utf-8")).hexdigest(),
            "raw_id_printed":False,
        })
        if provider=="bdtopo":
            exact_bdtopo.append(rawid.strip())
    return evidence,exact_bdtopo


def research_id_crosscheck(folder: Path, fetch=bounded_rnb_bytes) -> dict:
    originals, schema=bounded_historical_attribute_receipts(folder)
    currents=[]
    current_ids=[]
    for rnb_id in RNB_IDS:
        raw=fetch(rnb_id)
        meta,ids=rnb_external_id_receipts(raw,rnb_id)
        currents.append({"rnb_id":rnb_id,"external_id_receipts":meta})
        current_ids.append(ids)
    for row in originals:
        hashed=row["original_id_sha256_by_field"]
        # Direct text hash equality is a *research-only* positive, not a
        # version-safe historical building identity.
        row["literal_2016_id_matches_2023_bdtopo_external_id_by_rnb"]={
            rid:sorted([
                name for name,h in hashed.items()
                if any(h["sha256"]==hashlib.sha256(x.encode("utf-8")).hexdigest()
                       for x in ids)
            ]) for rid,ids in zip(RNB_IDS,current_ids)
        }
    return {
        "receipt_kind":"FR_BDTOPO_V21_2016_D077_RNB_2023_ID_PROVENANCE_V0",
        "old_product_version":"2.1",
        "original_archive_vintage":"2016-03-24",
        "rnb_modern_bdtopo_mapping_versions_observed":
            sorted(set(item["source_version"] for c in currents
                    for item in c["external_id_receipts"] if item["source"]=="bdtopo")),
        "original_shapefile_schema_field_names_by_family":schema,
        "historical_bounded_aoi_candidate_count":len(originals),
        "original_bounded_attribute_receipts":originals,
        "current_public_rnb_external_id_receipts":currents,
        "original_v21_identifiers_version_stable_proven":False,
        "historic_current_same_physical_building_identity_proven":False,
        "edition_date_not_observed_construction_date":True,
        "dbf_date_creat_is_not_building_construction_date":True,
        "historical_2016_source_license_reviewed":False,
        "archive_mirror_hash_not_official_publisher_hash":True,
        "raw_historic_or_current_source_ids_logged":False,
        "source_geometries_or_records_persisted":False,
        "cat_model_admitted":False,
    }


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extracted-building-shapefiles",required=True,type=Path)
    args=p.parse_args()
    try:
        result=research_id_crosscheck(args.extracted_building_shapefiles)
    except Exception as exc:
        # No unsafe input or provider-specific URL/contents in error logs.
        print(json.dumps({"receipt_kind":"FR_BDTOPO_V21_2016_D077_RNB_2023_ID_PROVENANCE_V0",
                          "status":"BLOCKED","error_type":type(exc).__name__,
                          "cat_model_admitted":False},sort_keys=True))
        return 2
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
