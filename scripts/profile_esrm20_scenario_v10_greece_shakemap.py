# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed offline profiler for the receipted ESRM20 Greece ShakeMap pair.

No network I/O is performed. Production entry points accept only the exact grid.xml
and uncertainty.xml byte identities receipted on trusted main for #285. Returned
facts are deliberately structural and do not establish event selection, validation,
holdout, publication, or model-use authority.
"""

from __future__ import annotations

import hashlib
import math
import re
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Final

_CANONICAL_GRID_BYTE_COUNT: Final = 5_290_966
_CANONICAL_GRID_SHA256: Final = "3c2fe7a2a7182fac999442ce3d88ddfd99004b7f999462ef2327f2eebc1ccd9f"
_CANONICAL_UNCERTAINTY_BYTE_COUNT: Final = 5_340_320
_CANONICAL_UNCERTAINTY_SHA256: Final = "eb08df5ff78f265fb45bf31dbd3dddf4f01bf10632382d4156a2bdf016e46417"
_CANONICAL_EVENT_ID: Final = "Greece_07-9-1999"
_CANONICAL_MAX_FIELDS: Final = 32
_CANONICAL_MAX_ROWS: Final = 500_000
_CANONICAL_MAX_COLUMNS: Final = 32
_CANONICAL_MAX_XML_BYTES: Final = 6_000_000
_HISTORICAL_OQ_3_12_1_UNIT_SENTINEL: Final = "ignored_by_openquake_3_12_1"

GRID_BYTE_COUNT: Final = _CANONICAL_GRID_BYTE_COUNT
GRID_SHA256: Final = _CANONICAL_GRID_SHA256
UNCERTAINTY_BYTE_COUNT: Final = _CANONICAL_UNCERTAINTY_BYTE_COUNT
UNCERTAINTY_SHA256: Final = _CANONICAL_UNCERTAINTY_SHA256
EVENT_ID: Final = _CANONICAL_EVENT_ID
MAX_FIELDS: Final = _CANONICAL_MAX_FIELDS
MAX_ROWS: Final = _CANONICAL_MAX_ROWS
MAX_COLUMNS: Final = _CANONICAL_MAX_COLUMNS
MAX_XML_BYTES: Final = _CANONICAL_MAX_XML_BYTES

_LOCAL_NAME_RE: Final = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_SAFE_META_RE: Final = re.compile(r"^[A-Za-z0-9_.:+/-]{0,96}$")
_XML_DECL_RE: Final = re.compile(r"^\s*<\?xml\s+([^?]*)\?>", re.IGNORECASE)
_ENCODING_RE: Final = re.compile(r"\bencoding\s*=\s*(['\"])([^'\"]+)\1", re.IGNORECASE)
_FORBIDDEN_DECL_RE: Final = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_ALLOWED_ENCODINGS: Final = frozenset({"utf-8", "utf8", "us-ascii", "ascii"})

_GRID_FIELD_UNITS: Final = {
    "LON": frozenset({"dd"}),
    "LAT": frozenset({"dd"}),
    "PGA": frozenset({"pctg"}),
    "PGV": frozenset({"cms"}),
    "MMI": frozenset({"mmi", "intensity"}),
    "PSA03": frozenset({"pctg"}),
    "PSA10": frozenset({"pctg"}),
    "PSA30": frozenset({"pctg"}),
    "STDPGA": frozenset({"ln(pctg)", "pctg"}),
    "URAT": frozenset({""}),
    "SVEL": frozenset({"ms"}),
}
_UNCERTAINTY_FIELD_UNITS: Final = {
    "LON": frozenset({"dd"}),
    "LAT": frozenset({"dd"}),
    "STDPGA": frozenset({"ln(pctg)"}),
    "STDPGV": frozenset({"ln(cms)"}),
    "STDMMI": frozenset({"mmi", "intensity"}),
    "STDPSA03": frozenset({"ln(pctg)"}),
    "STDPSA10": frozenset({"ln(pctg)"}),
    "STDPSA30": frozenset({"ln(pctg)"}),
}
_HISTORICAL_OQ_3_12_1_GRID_UNIT_FIELDS: Final = frozenset(_GRID_FIELD_UNITS)
_HISTORICAL_OQ_3_12_1_UNCERTAINTY_UNIT_FIELDS: Final = frozenset(_UNCERTAINTY_FIELD_UNITS)
_OQ_VALUE_IMTS: Final = {
    "MMI": "MMI",
    "PGA": "PGA",
    "PSA03": "SA(0.3)",
    "PSA10": "SA(1.0)",
    "PSA30": "SA(3.0)",
}
_OQ_UNCERTAINTY_IMTS: Final = {
    "STDMMI": "MMI",
    "STDPGA": "PGA",
    "STDPSA03": "SA(0.3)",
    "STDPSA10": "SA(1.0)",
    "STDPSA30": "SA(3.0)",
}


class ShakeMapProfileError(ValueError):
    """The fixed ShakeMap pair failed an identity or structural boundary."""


@dataclass(frozen=True)
class _GridProfile:
    namespace: str
    metadata: dict[str, str]
    fields: tuple[tuple[int, str, str], ...]
    specification: dict[str, int | float]
    row_count: int
    coordinate_sha256: str
    present_imts: tuple[str, ...]
    ignored_fields: tuple[str, ...]


def _require_canonical_authority() -> None:
    identities = (
        (GRID_BYTE_COUNT, _CANONICAL_GRID_BYTE_COUNT, "grid_byte_count"),
        (GRID_SHA256, _CANONICAL_GRID_SHA256, "grid_sha256"),
        (UNCERTAINTY_BYTE_COUNT, _CANONICAL_UNCERTAINTY_BYTE_COUNT, "uncertainty_byte_count"),
        (UNCERTAINTY_SHA256, _CANONICAL_UNCERTAINTY_SHA256, "uncertainty_sha256"),
        (EVENT_ID, _CANONICAL_EVENT_ID, "event_id"),
        (MAX_FIELDS, _CANONICAL_MAX_FIELDS, "max_fields"),
        (MAX_ROWS, _CANONICAL_MAX_ROWS, "max_rows"),
        (MAX_COLUMNS, _CANONICAL_MAX_COLUMNS, "max_columns"),
        (MAX_XML_BYTES, _CANONICAL_MAX_XML_BYTES, "max_xml_bytes"),
    )
    for observed, expected, label in identities:
        if type(observed) is not type(expected) or observed != expected:
            raise ShakeMapProfileError(f"production_authority_drift:{label}")


def _split_tag(tag: str) -> tuple[str, str]:
    if not isinstance(tag, str):
        raise ShakeMapProfileError("non_text_xml_tag")
    if tag.startswith("{"):
        end = tag.find("}")
        if end <= 1:
            raise ShakeMapProfileError("malformed_expanded_xml_name")
        namespace, local = tag[1:end], tag[end + 1 :]
    else:
        namespace, local = "", tag
    if not _LOCAL_NAME_RE.fullmatch(local):
        raise ShakeMapProfileError("unsafe_xml_local_name")
    return namespace, local


def _decode_xml(data: bytes, *, maximum: int) -> str:
    if type(data) is not bytes:
        raise TypeError("ShakeMap payloads must be bytes")
    if len(data) > maximum:
        raise ShakeMapProfileError("xml_byte_limit_exceeded")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise ShakeMapProfileError("non_ascii_utf8_xml_encoding")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ShakeMapProfileError("invalid_ascii_utf8_xml") from exc
    declaration = _XML_DECL_RE.match(text)
    if declaration:
        encoding = _ENCODING_RE.search(declaration.group(1))
        if encoding:
            normalized = encoding.group(2).strip().lower().replace("_", "-")
            if normalized not in _ALLOWED_ENCODINGS:
                raise ShakeMapProfileError("xml_encoding_declaration_mismatch")
    if _FORBIDDEN_DECL_RE.search(text):
        raise ShakeMapProfileError("dtd_or_entity_forbidden")
    return text


def _parse_positive_int(value: str | None, label: str) -> int:
    if value is None or not value.isdigit():
        raise ShakeMapProfileError(f"invalid_{label}")
    parsed = int(value)
    if parsed <= 0:
        raise ShakeMapProfileError(f"invalid_{label}")
    return parsed


def _parse_finite(value: str | None, label: str) -> float:
    if value is None:
        raise ShakeMapProfileError(f"missing_{label}")
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ShakeMapProfileError(f"invalid_{label}") from exc
    if not math.isfinite(parsed):
        raise ShakeMapProfileError(f"non_finite_{label}")
    return parsed


def _safe_meta(value: str | None, label: str) -> str:
    if value is None:
        return ""
    if not _SAFE_META_RE.fullmatch(value):
        raise ShakeMapProfileError(f"unsafe_{label}")
    return value


def _one_child(root: ET.Element, local: str, namespace: str) -> ET.Element:
    matches = []
    for child in root:
        child_namespace, child_local = _split_tag(child.tag)
        if child_namespace != namespace:
            raise ShakeMapProfileError("foreign_xml_namespace")
        if child_local == local:
            matches.append(child)
    if len(matches) != 1:
        raise ShakeMapProfileError(f"{local}_cardinality")
    return matches[0]


def _parse_fields(
    root: ET.Element,
    *,
    namespace: str,
    allowed_units: dict[str, frozenset[str]],
    max_fields: int,
    unit_metadata_ignored_fields: frozenset[str] = frozenset(),
) -> tuple[tuple[int, str, str], ...]:
    fields: list[tuple[int, str, str]] = []
    seen_names: set[str] = set()
    seen_indices: set[int] = set()
    for child in root:
        child_namespace, child_local = _split_tag(child.tag)
        if child_namespace != namespace:
            raise ShakeMapProfileError("foreign_xml_namespace")
        if child_local != "grid_field":
            continue
        if len(fields) >= max_fields:
            raise ShakeMapProfileError("grid_field_limit_exceeded")
        index = _parse_positive_int(child.attrib.get("index"), "grid_field_index")
        name = child.attrib.get("name", "")
        units = child.attrib.get("units", "")
        if name not in allowed_units:
            raise ShakeMapProfileError("unsupported_grid_field_name")
        if units not in allowed_units[name]:
            if name not in unit_metadata_ignored_fields:
                raise ShakeMapProfileError("unsupported_grid_field_units")
            units = _HISTORICAL_OQ_3_12_1_UNIT_SENTINEL
        if index in seen_indices:
            raise ShakeMapProfileError("duplicate_grid_field_index")
        if name in seen_names:
            raise ShakeMapProfileError("duplicate_grid_field_name")
        seen_indices.add(index)
        seen_names.add(name)
        fields.append((index, name, units))
    fields.sort(key=lambda item: item[0])
    if len(fields) < 2:
        raise ShakeMapProfileError("insufficient_grid_fields")
    expected = list(range(1, len(fields) + 1))
    if [item[0] for item in fields] != expected:
        raise ShakeMapProfileError("gapped_grid_field_indexes")
    names = [item[1] for item in fields]
    if names[:2] != ["LON", "LAT"]:
        raise ShakeMapProfileError("coordinate_fields_not_first")
    return tuple(fields)


def _parse_specification(root: ET.Element, *, namespace: str, max_rows: int) -> dict[str, int | float]:
    spec = _one_child(root, "grid_specification", namespace)
    nlon = _parse_positive_int(spec.attrib.get("nlon"), "nlon")
    nlat = _parse_positive_int(spec.attrib.get("nlat"), "nlat")
    if nlon * nlat > max_rows:
        raise ShakeMapProfileError("grid_cardinality_limit_exceeded")
    result: dict[str, int | float] = {"nlon": nlon, "nlat": nlat}
    for key in (
        "lon_min",
        "lat_min",
        "lon_max",
        "lat_max",
        "nominal_lon_spacing",
        "nominal_lat_spacing",
    ):
        result[key] = _parse_finite(spec.attrib.get(key), key)
    if result["lon_min"] > result["lon_max"] or result["lat_min"] > result["lat_max"]:
        raise ShakeMapProfileError("invalid_grid_bounds")
    if result["nominal_lon_spacing"] <= 0 or result["nominal_lat_spacing"] <= 0:
        raise ShakeMapProfileError("invalid_grid_spacing")
    return result


def _coordinate_digest_and_rows(
    root: ET.Element,
    *,
    namespace: str,
    field_count: int,
    expected_rows: int,
    max_columns: int,
) -> tuple[str, int]:
    if field_count > max_columns:
        raise ShakeMapProfileError("grid_column_limit_exceeded")
    grid_data = _one_child(root, "grid_data", namespace)
    if list(grid_data):
        raise ShakeMapProfileError("grid_data_must_be_text_only")
    text = grid_data.text or ""
    digest = hashlib.sha256()
    row_count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        row_count += 1
        if row_count > expected_rows:
            raise ShakeMapProfileError("grid_row_count_exceeded")
        tokens = stripped.split()
        if len(tokens) != field_count:
            raise ShakeMapProfileError("grid_row_width_mismatch")
        values = []
        for token in tokens:
            try:
                value = float(token)
            except ValueError as exc:
                raise ShakeMapProfileError("invalid_grid_numeric_token") from exc
            if not math.isfinite(value):
                raise ShakeMapProfileError("non_finite_grid_numeric_token")
            values.append(0.0 if value == 0.0 else value)
        digest.update(struct.pack(">dd", values[0], values[1]))
    if row_count != expected_rows:
        raise ShakeMapProfileError("grid_row_count_mismatch")
    return digest.hexdigest(), row_count


def _metadata(root: ET.Element) -> dict[str, str]:
    return {
        key: _safe_meta(root.attrib.get(source), key)
        for key, source in (
            ("event_id", "event_id"),
            ("shakemap_id", "shakemap_id"),
            ("shakemap_version", "shakemap_version"),
            ("code_version", "code_version"),
            ("shakemap_originator", "shakemap_originator"),
            ("map_status", "map_status"),
            ("shakemap_event_type", "shakemap_event_type"),
        )
    }


def _profile_xml(
    data: bytes,
    *,
    expected_byte_count: int,
    expected_sha256: str,
    allowed_units: dict[str, frozenset[str]],
    value_imts: dict[str, str],
    max_fields: int,
    max_rows: int,
    max_columns: int,
    max_xml_bytes: int,
    unit_metadata_ignored_fields: frozenset[str] = frozenset(),
) -> _GridProfile:
    if len(data) != expected_byte_count:
        raise ShakeMapProfileError("byte_count_mismatch")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ShakeMapProfileError("sha256_mismatch")
    text = _decode_xml(data, maximum=max_xml_bytes)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ShakeMapProfileError("invalid_xml") from exc
    namespace, local = _split_tag(root.tag)
    if local != "shakemap_grid":
        raise ShakeMapProfileError("unexpected_shakemap_root")
    fields = _parse_fields(
        root,
        namespace=namespace,
        allowed_units=allowed_units,
        max_fields=max_fields,
        unit_metadata_ignored_fields=unit_metadata_ignored_fields,
    )
    specification = _parse_specification(root, namespace=namespace, max_rows=max_rows)
    expected_rows = int(specification["nlon"]) * int(specification["nlat"])
    coordinate_sha256, row_count = _coordinate_digest_and_rows(
        root,
        namespace=namespace,
        field_count=len(fields),
        expected_rows=expected_rows,
        max_columns=max_columns,
    )
    names = tuple(field[1] for field in fields)
    present_imts = tuple(sorted(value_imts[name] for name in names if name in value_imts))
    ignored_fields = tuple(sorted(name for name in names if name not in {"LON", "LAT"} and name not in value_imts))
    return _GridProfile(
        namespace=namespace,
        metadata=_metadata(root),
        fields=fields,
        specification=specification,
        row_count=row_count,
        coordinate_sha256=coordinate_sha256,
        present_imts=present_imts,
        ignored_fields=ignored_fields,
    )


def _profile_verified_greece_shakemap_pair(
    grid_data: bytes,
    uncertainty_data: bytes,
    *,
    grid_expected_byte_count: int,
    grid_expected_sha256: str,
    uncertainty_expected_byte_count: int,
    uncertainty_expected_sha256: str,
    expected_event_id: str,
    max_fields: int = _CANONICAL_MAX_FIELDS,
    max_rows: int = _CANONICAL_MAX_ROWS,
    max_columns: int = _CANONICAL_MAX_COLUMNS,
    max_xml_bytes: int = _CANONICAL_MAX_XML_BYTES,
    historical_oq_3_12_1_compatibility: bool = False,
) -> dict[str, object]:
    """Private injection seam for already-bound bytes and deterministic tests."""
    if historical_oq_3_12_1_compatibility:
        exact_identity = (
            grid_expected_byte_count == _CANONICAL_GRID_BYTE_COUNT
            and grid_expected_sha256 == _CANONICAL_GRID_SHA256
            and uncertainty_expected_byte_count == _CANONICAL_UNCERTAINTY_BYTE_COUNT
            and uncertainty_expected_sha256 == _CANONICAL_UNCERTAINTY_SHA256
            and expected_event_id == _CANONICAL_EVENT_ID
        )
        if not exact_identity:
            raise ShakeMapProfileError("historical_compatibility_requires_canonical_identity")

    grid = _profile_xml(
        grid_data,
        expected_byte_count=grid_expected_byte_count,
        expected_sha256=grid_expected_sha256,
        allowed_units=_GRID_FIELD_UNITS,
        value_imts=_OQ_VALUE_IMTS,
        max_fields=max_fields,
        max_rows=max_rows,
        max_columns=max_columns,
        max_xml_bytes=max_xml_bytes,
        unit_metadata_ignored_fields=(
            _HISTORICAL_OQ_3_12_1_GRID_UNIT_FIELDS
            if historical_oq_3_12_1_compatibility
            else frozenset()
        ),
    )
    uncertainty = _profile_xml(
        uncertainty_data,
        expected_byte_count=uncertainty_expected_byte_count,
        expected_sha256=uncertainty_expected_sha256,
        allowed_units=_UNCERTAINTY_FIELD_UNITS,
        value_imts=_OQ_UNCERTAINTY_IMTS,
        max_fields=max_fields,
        max_rows=max_rows,
        max_columns=max_columns,
        max_xml_bytes=max_xml_bytes,
        unit_metadata_ignored_fields=(
            _HISTORICAL_OQ_3_12_1_UNCERTAINTY_UNIT_FIELDS
            if historical_oq_3_12_1_compatibility
            else frozenset()
        ),
    )
    if grid.namespace != uncertainty.namespace:
        raise ShakeMapProfileError("shakemap_namespace_mismatch")
    if (
        grid.metadata["event_id"]
        and uncertainty.metadata["event_id"]
        and grid.metadata["event_id"] != uncertainty.metadata["event_id"]
    ):
        raise ShakeMapProfileError("shakemap_event_id_pair_mismatch")
    if grid.specification != uncertainty.specification:
        raise ShakeMapProfileError("grid_specification_mismatch")
    if grid.row_count != uncertainty.row_count:
        raise ShakeMapProfileError("grid_row_count_pair_mismatch")
    if grid.coordinate_sha256 != uncertainty.coordinate_sha256:
        raise ShakeMapProfileError("coordinate_grid_mismatch")

    paired_imts = tuple(sorted(set(grid.present_imts) & set(uncertainty.present_imts)))
    return {
        "schema_version": "oc-esrm20-scenario-v10-greece-shakemap-profile-v1",
        "receipt_event_id": expected_event_id,
        "root_local_name": "shakemap_grid",
        "root_namespace": grid.namespace,
        "metadata": grid.metadata,
        "grid": {
            "byte_count": grid_expected_byte_count,
            "sha256": grid_expected_sha256,
            "fields": [
                {"index": index, "name": name, "units": units}
                for index, name, units in grid.fields
            ],
            "specification": grid.specification,
            "observed_row_count": grid.row_count,
            "coordinate_sha256": grid.coordinate_sha256,
            "openquake_3_12_1_present_imts": list(grid.present_imts),
            "ignored_fields": list(grid.ignored_fields),
        },
        "uncertainty": {
            "byte_count": uncertainty_expected_byte_count,
            "sha256": uncertainty_expected_sha256,
            "fields": [
                {"index": index, "name": name, "units": units}
                for index, name, units in uncertainty.fields
            ],
            "specification": uncertainty.specification,
            "observed_row_count": uncertainty.row_count,
            "coordinate_sha256": uncertainty.coordinate_sha256,
            "openquake_3_12_1_present_imts": list(uncertainty.present_imts),
            "ignored_fields": list(uncertainty.ignored_fields),
        },
        "openquake_3_12_1_paired_imts": list(paired_imts),
        "coordinate_grids_equal": True,
        "provider_file_content_profiled": True,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_fixed_greece_shakemap_pair(grid_data: bytes, uncertainty_data: bytes) -> dict[str, object]:
    """Return bounded facts for the exact receipted Greece grid/uncertainty pair."""
    _require_canonical_authority()
    return _profile_verified_greece_shakemap_pair(
        grid_data,
        uncertainty_data,
        grid_expected_byte_count=_CANONICAL_GRID_BYTE_COUNT,
        grid_expected_sha256=_CANONICAL_GRID_SHA256,
        uncertainty_expected_byte_count=_CANONICAL_UNCERTAINTY_BYTE_COUNT,
        uncertainty_expected_sha256=_CANONICAL_UNCERTAINTY_SHA256,
        expected_event_id=_CANONICAL_EVENT_ID,
        max_fields=_CANONICAL_MAX_FIELDS,
        max_rows=_CANONICAL_MAX_ROWS,
        max_columns=_CANONICAL_MAX_COLUMNS,
        max_xml_bytes=_CANONICAL_MAX_XML_BYTES,
        historical_oq_3_12_1_compatibility=True,
    )
