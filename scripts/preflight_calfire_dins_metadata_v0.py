# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, metadata-only safety preflight for CAL FIRE DINS POSTFIRE layer 0.

This command accepts a locally saved, separately authorized ArcGIS layer-metadata
JSON response. It NEVER connects to a provider, reads feature records, requests
personal fields or emits field values. The returned JSON is only a schema receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MAX_METADATA_BYTES = 524_288
LAYER_ID = 0
LAYER_NAME = "POSTFIRE"
MANDATORY_FIELDS = {
    "OBJECTID": "esriFieldTypeOID",
    "GLOBALID": "esriFieldTypeGlobalID",
    "DAMAGE": "esriFieldTypeString",
    "STRUCTURETYPE": "esriFieldTypeString",
    "INCIDENTNUM": "esriFieldTypeString",
    "INCIDENTSTARTDATE": "esriFieldTypeDate",
}
DAMAGE_DOMAIN = frozenset({
    "Destroyed (>50%)", "Major (25-50%)", "Minor (10-25%)",
    "Affected (>0-10%)", "Inaccessible", "No Damage",
})

OPTIONAL_SCIENCE_FIELDS = frozenset(
    {"ROOFCONSTRUCTION", "EXTERIORSIDING", "FIRENAME", "YEARBUILT"}
)
SENSITIVE_FIELDS = frozenset(
    {
        "INSPECTORFIRSTNAME", "INSPECTORLASTNAME", "STREETNUMBER",
        "STREETNAME", "STREETTYPE", "STREETSUFFIX", "SITEADDRESS",
        "APN", "LATITUDE", "LONGITUDE", "ZIPCODE", "COMMENTS",
    }
)


class DinsMetadataError(ValueError):
    """Invalid, drifting, unsafe or non-metadata ArcGIS response."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in pairs:
        if key in found:
            raise DinsMetadataError("duplicate JSON key")
        found[key] = value
    return found


def _reject_constant(value: str) -> None:
    raise DinsMetadataError("nonfinite JSON constant is forbidden")


def preflight_metadata(raw: bytes) -> dict[str, object]:
    """Return a privacy-safe receipt; reject feature payloads and schema drift."""
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_METADATA_BYTES):
        raise DinsMetadataError("metadata byte size out of range")
    try:
        source = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DinsMetadataError("metadata is not valid UTF-8 JSON") from exc
    if type(source) is not dict:
        raise DinsMetadataError("metadata top-level object required")
    if any(key in source for key in ("features", "results", "edits", "attachments")):
        raise DinsMetadataError("feature-level payload is not allowed")
    if (
        type(source.get("id")) is not int
        or source["id"] != LAYER_ID
        or source.get("name") != LAYER_NAME
        or source.get("type") != "Feature Layer"
        or source.get("geometryType") != "esriGeometryPoint"
        or source.get("objectIdField") != "OBJECTID"
        or source.get("globalIdField") != "GLOBALID"
        or source.get("typeIdField") != "DAMAGE"
    ):
        raise DinsMetadataError("wrong layer identity or geometry semantics")
    raw_fields = source.get("fields")
    if type(raw_fields) is not list or not raw_fields:
        raise DinsMetadataError("nonempty field descriptors required")
    types: dict[str, str] = {}
    for field in raw_fields:
        if type(field) is not dict:
            raise DinsMetadataError("field descriptor must be an object")
        name, field_type = field.get("name"), field.get("type")
        if (
            type(name) is not str or not name or len(name) > 128
            or type(field_type) is not str or not field_type
        ):
            raise DinsMetadataError("invalid field name/type")
        if name in types:
            raise DinsMetadataError("duplicate field name")
        types[name] = field_type
    for name, required_type in MANDATORY_FIELDS.items():
        if types.get(name) != required_type:
            raise DinsMetadataError("required field missing or type drift: " + name)
    layer_types = source.get("types")
    if type(layer_types) is not list or not layer_types:
        raise DinsMetadataError("DAMAGE type domain required")
    damage_values: set[str] = set()
    for item in layer_types:
        if type(item) is not dict or type(item.get("id")) is not str:
            raise DinsMetadataError("malformed DAMAGE domain member")
        domain_label = item["id"]
        if domain_label in damage_values:
            raise DinsMetadataError("duplicate DAMAGE domain member")
        damage_values.add(domain_label)
    if damage_values != DAMAGE_DOMAIN:
        raise DinsMetadataError("DAMAGE domain semantics differ from reviewed source")
    return {
        "contract": "CALFIRE-DINS-LAYER0-METADATA-PREFLIGHT-v0",
        "layer_id": LAYER_ID,
        "layer_name": LAYER_NAME,
        "metadata_bytes": len(raw),
        "metadata_sha256": hashlib.sha256(raw).hexdigest(),
        "declared_field_count": len(types),
        "damage_states": sorted(damage_values),
        "incident_time_field_type": types["INCIDENTSTARTDATE"],
        "damage_states_are_insurance_loss_ratios": False,
        "science_fields_present": sorted(OPTIONAL_SCIENCE_FIELDS.intersection(types)),
        "sensitive_field_names_present": sorted(SENSITIVE_FIELDS.intersection(types)),
        "feature_rows_read": 0,
        "model_data_admitted": False,
        "scientific_warning": (
            "DINS inspection frame is incomplete; prior to 2018, undamaged "
            "structures were not systematically recorded."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as handle:
            raw = handle.read(MAX_METADATA_BYTES + 1)
        receipt = preflight_metadata(raw)
    except (OSError, DinsMetadataError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
