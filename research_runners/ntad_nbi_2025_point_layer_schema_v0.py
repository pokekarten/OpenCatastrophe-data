# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original NTAD 2025 FHWA bridge point-layer metadata only; no raw geometries.

Published layer EPSG:4326 is not proof of independent 2025 bridge identities,
geodetic precision, insured locations or legacy NBI item conversion.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
from research_runners.fhwa_nbi_socrata_metadata_gate_v0 import Blocked, _unique_object

SOURCE = "https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_National_Bridge_Inventory/FeatureServer/0?f=pjson"
ITEM_ID = "bd1b6ee967134ea68fac351cef461b5e"
REQUIRED = {"STATE_CODE_001": "esriFieldTypeString",
            "STRUCTURE_NUMBER_008": "esriFieldTypeString",
            "LAT_016": "esriFieldTypeString", "LONG_017": "esriFieldTypeString",
            "YEAR_BUILT_027": "esriFieldTypeInteger"}


def audit_layer(original: bytes) -> dict:
    if type(original) is not bytes or not 500 <= len(original) <= 1_000_000:
        raise Blocked("complete bounded NTAD original layer metadata required")
    try:
        data = json.loads(original.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=lambda x: (_ for _ in ()).throw(Blocked(x)))
    except Blocked:
        raise
    except (UnicodeError, ValueError) as exc:
        raise Blocked("invalid original NTAD JSON") from exc
    if type(data) is not dict or data.get("error"):
        raise Blocked("original NTAD source error or wrong document")
    if (data.get("id") != 0 or data.get("type") != "Feature Layer" or
        data.get("name") != "National Bridge Inventory" or
        data.get("serviceItemId") != ITEM_ID or
        data.get("geometryType") != "esriGeometryPoint" or
        data.get("spatialReference", {}).get("wkid") != 4326):
        raise Blocked("wrong original NTAD source identity, point type or layer CRS")
    desc = data.get("description")
    if type(desc) is not str or "June 20, 2025" not in desc:
        raise Blocked("NTAD 2025 source vintage not declared")
    fields = data.get("fields")
    if type(fields) is not list or not 50 <= len(fields) <= 200:
        raise Blocked("missing NTAD original field schema")
    by_name = {}
    for field in fields:
        if type(field) is not dict or type(field.get("name")) is not str:
            raise Blocked("invalid NTAD field metadata")
        name = field["name"]
        if name in by_name:
            raise Blocked("duplicate NTAD field")
        by_name[name] = field
    for key, typ in REQUIRED.items():
        if by_name.get(key, {}).get("type") != typ:
            raise Blocked(f"original NTAD required field type changed: {key}")
    if (by_name["LAT_016"].get("length") != 8 or
        by_name["LONG_017"].get("length") != 9):
        raise Blocked("legacy coded NBI coordinate field widths changed")
    extent = data.get("extent")
    if type(extent) is not dict or extent.get("spatialReference", {}).get("wkid") != 4326:
        raise Blocked("published NTAD extent CRS mismatch")
    return {
        "source": SOURCE, "source_vintage_declared": "2025-06-20",
        "original_metadata_sha256": sha256(original).hexdigest(),
        "original_metadata_bytes": len(original), "field_count": len(by_name),
        "layer_geometry_type": "esriGeometryPoint", "declared_layer_epsg": 4326,
        "NBI_legacy_lat_lon_code_widths": [8, 9],
        "individual_NTAD_geometries_audited": False,
        "Socrata_NTAD_bridge_record_join_proven": False,
        "point_location_accuracy_or_datum_transformation_proven": False,
        "source_vintage_freshness_guaranteed": False,
        "rights_for_downstream_redistribution_reviewed": False,
        "insurer_exposure_or_TIV_proven": False,
        "model_input_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-layer-metadata", type=Path, required=True)
    args = parser.parse_args()
    source = args.original_layer_metadata
    if source.is_symlink() or not source.is_file() or not 500 <= source.stat().st_size <= 1_000_000:
        parser.error("bounded regular NTAD metadata JSON required")
    print(json.dumps(audit_layer(source.read_bytes()), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
