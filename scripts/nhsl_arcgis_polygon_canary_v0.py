# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded, offline NHSL official ArcGIS polygon-layer + 3-row schema canary.

Accepts two locally acquired *official service JSON* responses; fetches nothing.
Neither a successful check nor published licence implies OED/insured admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

if __package__:
    from .nhsl_oed_staging_preflight_v0 import (
        NHSLStagingError, REQUIRED_FIELDS, examine_row,
    )
else:
    from nhsl_oed_staging_preflight_v0 import (
        NHSLStagingError, REQUIRED_FIELDS, examine_row,
    )

LAYER_URL = (
    "https://maps-cartes.services.geo.ca/server_serveur/rest/services/"
    "NRCan/physical_exposure_en/MapServer/1"
)
# This query is for an exact three-feature read-only canary, not a census total.
SAMPLE_URL = (
    LAYER_URL
    + "/query?where=1%3D1%20AND%20pruid%3D%2724%27"
    + "&outFields=Sauid%2CE_SauidLat%2CE_SauidLon%2CEt_BldgNum%2C"
      "Et_BldgArea%2CEt_StrValue%2CEt_NStrValue%2CEt_BldgValue%2C"
      "Et_ContValue%2CEt_AssetValue%2COBJECTID"
    + "&returnGeometry=false&resultRecordCount=3&orderByFields=OBJECTID&f=pjson"
)
FIELDS = {
    "Sauid": "esriFieldTypeString",
    "E_SauidLat": "esriFieldTypeDouble",
    "E_SauidLon": "esriFieldTypeDouble",
    "Et_BldgNum": "esriFieldTypeDouble",
    "Et_BldgArea": "esriFieldTypeDouble",
    "Et_StrValue": "esriFieldTypeDouble",
    "Et_NStrValue": "esriFieldTypeDouble",
    "Et_BldgValue": "esriFieldTypeDouble",
    "Et_ContValue": "esriFieldTypeDouble",
    "Et_AssetValue": "esriFieldTypeDouble",
    "OBJECTID": "esriFieldTypeOID",
}
MAX_METADATA_BYTES = 300_000
MAX_SAMPLE_BYTES = 50_000


class NHSLServiceError(ValueError):
    """Source-shaped ArcGIS response fails a bounded scientific/technical gate."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise NHSLServiceError(f"duplicate JSON property: {key}")
        output[key] = value
    return output


def _reject_constant(value: str) -> None:
    raise NHSLServiceError(f"invalid JSON non-finite constant: {value}")


def _load(path: Path, maximum: int) -> tuple[dict[str, Any], str]:
    if not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise NHSLServiceError("missing, empty or oversized provider JSON")
    raw = path.read_bytes()
    if not 0 < len(raw) <= maximum:
        raise NHSLServiceError("missing, empty or oversized provider JSON")
    try:
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NHSLServiceError("invalid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise NHSLServiceError("top-level provider JSON must be an object")
    return payload, hashlib.sha256(raw).hexdigest()


def _check_layer(layer: dict[str, Any]) -> None:
    if (
        type(layer.get("id")) is not int or layer["id"] != 1
        or layer.get("name") != "Landuse"
        or layer.get("type") != "Feature Layer"
        or layer.get("geometryType") != "esriGeometryPolygon"
        or layer.get("capabilities") != "Map,Data,Query"
    ):
        raise NHSLServiceError("wrong NHSL polygon layer ID/role/geometry")
    ref = layer.get("sourceSpatialReference")
    if not isinstance(ref, dict) or ref.get("latestWkid") != 3857:
        raise NHSLServiceError("NHSL source geometry CRS is not pinned EPSG:3857")
    source_fields = layer.get("fields")
    if not isinstance(source_fields, list) or len(source_fields) != 64:
        raise NHSLServiceError("NHSL MapServer polygon field count drifted from 64")
    actual: dict[str, str] = {}
    for field in source_fields:
        if not isinstance(field, dict) or not isinstance(field.get("name"), str):
            raise NHSLServiceError("invalid ArcGIS layer field")
        name = field["name"]
        if name in actual:
            raise NHSLServiceError("duplicate ArcGIS field name")
        actual[name] = field.get("type")
    for field, expected_type in FIELDS.items():
        if actual.get(field) != expected_type:
            raise NHSLServiceError(f"wrong or missing NHSL field/type: {field}")


def audit_pair(layer: dict[str, Any], query: dict[str, Any],
               layer_sha256: str, sample_sha256: str) -> dict[str, Any]:
    for digest in (layer_sha256, sample_sha256):
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise NHSLServiceError("provider metadata/sample SHA-256 invalid")
    _check_layer(layer)
    if "error" in query:
        raise NHSLServiceError("ArcGIS service returned an error")
    outfields = query.get("fields")
    if not isinstance(outfields, list) or len(outfields) != len(FIELDS):
        raise NHSLServiceError("query returned wrong field count")
    typed_fields = {}
    for item in outfields:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise NHSLServiceError("query field declaration malformed")
        if item["name"] in typed_fields:
            raise NHSLServiceError("duplicate query field")
        typed_fields[item["name"]] = item.get("type")
    if typed_fields != FIELDS:
        raise NHSLServiceError("query field/type projection differs from requested original fields")

    features = query.get("features")
    if not isinstance(features, list) or len(features) != 3:
        raise NHSLServiceError("expected precisely three bounded feature records")
    if type(query.get("exceededTransferLimit")) is not bool:
        raise NHSLServiceError("ArcGIS transfer limit missing or invalid")
    seen_oid: set[int] = set()
    seen_sauid: set[str] = set()
    oid_order: list[int] = []
    totals = {
        "estimated_buildings": Decimal(0),
        "modeled_building_replacement_cad_2019": Decimal(0),
        "modeled_contents_replacement_cad_2019": Decimal(0),
        "modeled_total_replacement_cad_2019": Decimal(0),
        "aggregate_finished_area_sqft": Decimal(0),
    }
    fractional_count = 0
    for feature in features:
        if not isinstance(feature, dict) or set(feature) != {"attributes"}:
            raise NHSLServiceError("unexpected raw geometry or malformed feature")
        attrs = feature["attributes"]
        if not isinstance(attrs, dict) or set(attrs) != set(FIELDS):
            raise NHSLServiceError("missing or extraneous fields in NHSL feature")
        oid = attrs["OBJECTID"]
        if type(oid) is not int or oid < 1 or oid in seen_oid:
            raise NHSLServiceError("duplicate/invalid OBJECTID")
        seen_oid.add(oid)
        oid_order.append(oid)
        try:
            checked = examine_row({field: attrs[field] for field in REQUIRED_FIELDS})
        except NHSLStagingError as exc:
            raise NHSLServiceError(f"NHSL scientific aggregate row rejected: {exc}") from exc
        sauid = checked["settled_area_source_id"]
        if sauid in seen_sauid:
            raise NHSLServiceError("duplicate settled-area ID")
        seen_sauid.add(sauid)
        amounts = checked["replacement_cost_components_cad_2019"]
        totals["estimated_buildings"] += Decimal(checked["aggregated_buildings_estimated"])
        totals["aggregate_finished_area_sqft"] += Decimal(checked["aggregated_finished_area_sqft"])
        totals["modeled_building_replacement_cad_2019"] += Decimal(amounts["buildings_total"])
        totals["modeled_contents_replacement_cad_2019"] += Decimal(amounts["contents"])
        totals["modeled_total_replacement_cad_2019"] += Decimal(amounts["assets_total"])
        fractional_count += int(checked["aggregated_building_count_nonintegral"])
    if oid_order != sorted(oid_order):
        raise NHSLServiceError("sample not ordered by OBJECTID")

    if (
        abs(
            totals["modeled_building_replacement_cad_2019"]
            + totals["modeled_contents_replacement_cad_2019"]
            - totals["modeled_total_replacement_cad_2019"]
        ) > Decimal("0.06")
    ):
        raise NHSLServiceError("three-row sampled building/contents total disagrees")

    return {
        "source_candidate_id": "can.nrcan.nhsl.physical-exposure.2016-2020",
        "proof_type": "live_NRCAN_ArcGIS_polygon_layer_bounded_three_row_canary",
        "official_metadata_url": LAYER_URL + "?f=pjson",
        "official_sample_query_url": SAMPLE_URL,
        "input_layer_json_sha256": layer_sha256,
        "input_sample_json_sha256": sample_sha256,
        "live_polygon_layer_id": 1,
        "live_polygon_field_count": 64,
        "source_dictionary_yaml_field_count": 66,
        "matched_required_nhsl_fields": len(REQUIRED_FIELDS),
        "observed_feature_count": 3,
        "query_exceeded_transfer_limit": query["exceededTransferLimit"],
        "sampled_nonintegral_building_count_records": fractional_count,
        "sample_only_totals": {key: str(value) for key, value in totals.items()},
        "monetary_unit": "CAD",
        "monetary_base_year": 2019,
        "geometry_spatial_reference": "EPSG:3857",
        "centroid_coordinate_role": "settled_area_centroid_not_one_roof",
        "provider_data_license_catalog_label": "Open Government Licence - Canada",
        "original_source_rows_stored_in_repository": False,
        "original_GPKG_v1_bytes_or_excel_dictionary_compared": False,
        "offline_json_origin_authenticated": False,
        "source_rights_independently_reviewed": False,
        "scientific_fitness_reviewed": False,
        "insurance_coverage_verified": False,
        "can_export_oed_loc_or_account": False,
        "model_input_approved": False,
        "admission_status": "not_admitted",
    }


def inspect_files(metadata_path: Path, sample_path: Path) -> dict[str, Any]:
    layer, layer_sha256 = _load(metadata_path, MAX_METADATA_BYTES)
    query, sample_sha256 = _load(sample_path, MAX_SAMPLE_BYTES)
    return audit_pair(layer, query, layer_sha256, sample_sha256)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer-json", type=Path, required=True)
    parser.add_argument("--sample-json", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = inspect_files(args.layer_json, args.sample_json)
    except (NHSLServiceError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
