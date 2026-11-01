#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Research-only 2016 BD TOPO <> current RNB footprint geometry comparison.

Only the bounded original 2016 D077 SHP files from the separately
SHA-pinned mirror archive and 2 exact public RNB building-ID lookups
may be used. Original SHP and RNB raw responses remain temporary.
Never infer stable building identity, 2016 insured risk, flood depth or loss.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from pyproj import CRS, Transformer
from shapely.geometry import box, shape
from shapely.ops import transform
import shapefile

from research_runners.fr_bdtopo_2016_d077_bounded_buildings_v0 import (
    BoundedBuildingError, EXPECTED_CRS, FAMILIES,
    MAX_CANDIDATES, PONTHIERRY_LONLAT_BBOX,
)

RNB_IDS = ("5TR6PNH2YQPT", "TCHNNF59Y27V")
RNB_ROOT = "https://rnb-api.beta.gouv.fr/api/alpha/buildings/"
MAX_API_RESPONSE_BYTES = 128_000
RNB_PILOT_GUARD = (2.54, 48.53, 2.56, 48.55)
HISTORIC_AOI_EXPECTED_COUNT = 3


class BridgeError(ValueError):
    pass


def bounded_rnb_bytes(rnb_id: str) -> bytes:
    if rnb_id not in RNB_IDS:
        raise BridgeError("refuse unapproved RNB source identity")
    req = Request(
        RNB_ROOT + rnb_id + "/?format=json",
        headers={"Accept": "application/json",
                 "User-Agent": "OpenCatastrophe-2016-Research/0.1"},
        method="GET",
    )
    with urlopen(req, timeout=20) as response:
        if response.status != 200 or response.geturl().split("?")[0] != (
            RNB_ROOT + rnb_id + "/"
        ):
            raise BridgeError("unexpected upstream response or redirect")
        if response.headers.get("Content-Type", "").split(";")[0].strip() not in (
            "application/json", "application/geo+json"
        ):
            raise BridgeError("unexpected RNB media type")
        result = response.read(MAX_API_RESPONSE_BYTES + 1)
    if not result or len(result) > MAX_API_RESPONSE_BYTES:
        raise BridgeError("empty or oversized RNB API payload")
    return result


def current_rnb_shape(rnb_id: str, payload: bytes) -> tuple[object, dict]:
    if rnb_id not in RNB_IDS or not isinstance(payload, bytes):
        raise BridgeError("unknown source identifier")
    if len(payload) > MAX_API_RESPONSE_BYTES:
        raise BridgeError("RNB source bytes over cap")
    try:
        record = json.loads(payload)
    except (ValueError, UnicodeError) as exc:
        raise BridgeError("malformed current RNB JSON") from exc
    if (not isinstance(record, dict) or record.get("rnb_id") != rnb_id
        or record.get("is_active") is not True
        or record.get("status") != "constructed"):
        raise BridgeError("current RNB identity/status not as expected")
    rawshape = record.get("shape")
    if not isinstance(rawshape, dict) or rawshape.get("type") not in (
        "Polygon", "MultiPolygon"
    ):
        raise BridgeError("current RNB API did not return a polygon")
    try:
        polygon = shape(rawshape)
    except Exception as exc:
        raise BridgeError("current RNB polygon cannot be decoded") from exc
    if polygon.is_empty or not polygon.is_valid:
        raise BridgeError("current RNB shape invalid")
    xmin, ymin, xmax, ymax = polygon.bounds
    gx0, gy0, gx1, gy1 = RNB_PILOT_GUARD
    if not (gx0 <= xmin <= xmax <= gx1 and gy0 <= ymin <= ymax <= gy1):
        raise BridgeError("RNB shape outside exact small study region")
    reproject = Transformer.from_crs(4326, 2154, always_xy=True).transform
    projected = transform(reproject, polygon)
    if projected.is_empty or not projected.is_valid or projected.area <= 0:
        raise BridgeError("RNB reprojected shape invalid")
    evidence = {
        "current_rnb_id": rnb_id,
        "current_rnb_source_url": RNB_ROOT + rnb_id + "/?format=json",
        "source_json_sha256_observed_now": hashlib.sha256(payload).hexdigest(),
        "source_json_bytes": len(payload),
        "current_status": "constructed",
        "source_shape_type": rawshape["type"],
        "projected_epsg": 2154,
        "current_polygon_area_m2": round(projected.area, 2),
        "current_shape_geojson_persisted": False,
        "current_geometry_vintage_is_2016": False,
    }
    return projected, evidence


def historical_bounded_shapes(folder: Path) -> list[tuple[str, int, object]]:
    if not folder.is_dir() or folder.is_symlink():
        raise BridgeError("historical source folder invalid")
    t = Transformer.from_crs(4326, 2154, always_xy=True)
    lon0, lat0, lon1, lat1 = PONTHIERRY_LONLAT_BBOX
    x, y = t.transform([lon0, lon1, lon0, lon1],
                       [lat0, lat0, lat1, lat1])
    bounds = min(x), min(y), max(x), max(y)
    pilot_box = box(*bounds)
    records = []
    for family in FAMILIES:
        components = [folder / (family + ext)
                      for ext in (".shp", ".shx", ".dbf", ".prj")]
        if any(not p.is_file() or p.is_symlink() for p in components):
            raise BridgeError("source SHP/SHX/DBF/PRJ family missing or unsafe")
        if not CRS.from_wkt(components[-1].read_text(encoding="utf-8-sig")).equals(
            EXPECTED_CRS, ignore_axis_order=True
        ):
            raise BridgeError("2016 historical family CRS not verified EPSG:2154")
        with shapefile.Reader(str(components[0])) as reader:
            if reader.shapeType not in (
                shapefile.POLYGON, shapefile.POLYGONZ, shapefile.POLYGONM
            ):
                raise BridgeError("historical source not polygonal")
            for local_ordinal, source in enumerate(reader.iterShapes(bbox=bounds)):
                if len(records) >= MAX_CANDIDATES:
                    raise BridgeError("source candidate count above bounded limit")
                try:
                    polygon = shape(source.__geo_interface__)
                except Exception as exc:
                    raise BridgeError("cannot decode original 2016 polygon") from exc
                if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
                    raise BridgeError("historical source polygon invalid")
                if polygon.intersects(pilot_box):
                    records.append((family, local_ordinal, polygon))
    if len(records) != HISTORIC_AOI_EXPECTED_COUNT:
        raise BridgeError("archive/pilot geometry count drift: not three")
    return records


def compare(folder: Path, fetch=bounded_rnb_bytes) -> dict:
    historical = historical_bounded_shapes(folder)
    current = []
    current_receipts = []
    for rnb_id in RNB_IDS:
        geom, receipt = current_rnb_shape(rnb_id, fetch(rnb_id))
        current.append((rnb_id, geom))
        current_receipts.append(receipt)
    matches = []
    for family, local_ordinal, historic in historical:
        row = {
            "2016_source_family": family,
            "2016_selected_family_ordinal_not_provider_id": local_ordinal,
            "2016_mapped_footprint_area_m2": round(float(historic.area), 2),
            "source_2016_polygon_exported": False,
            "current_polygon_comparisons": [],
        }
        for rnb_id, now in current:
            intersection = float(historic.intersection(now).area)
            union = float(historic.union(now).area)
            row["current_polygon_comparisons"].append({
                "rnb_id": rnb_id,
                "intersection_area_m2": round(intersection, 2),
                "iou": round(intersection / union, 6) if union > 0 else None,
                "2016_polygon_covered_ratio": round(
                    intersection / historic.area, 6),
                "current_polygon_covered_ratio": round(
                    intersection / now.area, 6),
                "polygon_distance_m": round(float(historic.distance(now)), 2),
                "polygon_intersects": bool(historic.intersects(now)),
                "same_physical_building_identity_proven": False,
            })
        matches.append(row)
    return {
        "receipt_kind": "FR_BDTOPO_D077_2016_RNB_2026_POLYGON_BRIDGE_V0",
        "2016_mirror_archived_source_version": "BD TOPO 2.1 D077 2016-03-24",
        "historical_source_crs_epsg": 2154,
        "public_rnb_source_crs_epsg": 4326,
        "common_comparison_crs_epsg": 2154,
        "2016_historic_bbox_source_candidates": len(historical),
        "current_rnb_source_records": len(current),
        "current_rnb_api_metadata_receipts": current_receipts,
        "historic_current_pairwise_polygon_matrix": matches,
        "historic_to_modern_identity_automatically_assigned": False,
        "source_independence_proven": False,
        "historic_original_ign_provider_checksum_authenticated": False,
        "historic_2016_archived_data_reuse_rights_cleared": False,
        "specific_2016_flood_extent_referenced_in_join": False,
        "geographic_footprint_intersection_is_insured_damage": False,
        "insurer_tiv_claims_or_contract_data_present": False,
        "model_input_admitted": False,
        "original_shapefiles_and_rnb_responses_saved": False,
    }
