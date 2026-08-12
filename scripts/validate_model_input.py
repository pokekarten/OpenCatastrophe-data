# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Validate one typed OpenCatastrophe model-input binding."""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scripts import validate_manifest
except ModuleNotFoundError:  # direct script execution
    import validate_manifest  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
DATASET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
MANIFEST_RE = re.compile(r"^manifests/([A-Za-z0-9][A-Za-z0-9._-]*)\.json$")
STORAGE_RE = re.compile(r"^external://[A-Za-z0-9][A-Za-z0-9._/-]*$")
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)

TOP_KEYS = {
    "schema_version", "manifest", "dataset_id", "artifact", "storage_reference",
    "sha256", "modelling_layer", "scientific_role", "peril", "measure",
    "spatial", "temporal", "quality",
}
LAYERS = {
    "event_catalogue", "hazard", "exposure", "vulnerability", "observed_loss",
    "engine", "standard", "other",
}
ROLES = {"training", "calibration", "validation", "holdout", "benchmark", "context"}
ARTIFACTS = {"raw", "derived"}
AGGREGATIONS = {
    "instantaneous", "mean", "maximum", "minimum", "accumulation", "count",
    "probability", "categorical", "other",
}
SPATIAL_SUPPORTS = {
    "point", "line", "polygon", "grid_cell", "raster_cell",
    "administrative_area", "asset", "event", "other",
}
TEMPORAL_SUPPORTS = {
    "static", "instant_series", "interval_series", "event_series", "climatology",
}
MISSING_POLICIES = {"forbidden", "explicit", "source_defined"}
QUALITY_POLICIES = {"none", "preserved", "filtered", "source_defined"}


class ModelInputError(ValueError):
    pass


def _reject_constant(value: str) -> None:
    raise ModelInputError(f"non-finite JSON number is forbidden: {value}")


def _strict_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ModelInputError(f"non-finite JSON number is forbidden: {value}")
    return parsed


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ModelInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_strict_float,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ModelInputError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise ModelInputError("model input root must be an object")
    return payload


def _closed(obj: dict[str, Any], allowed: set[str], required: set[str], field: str) -> None:
    unknown = sorted(set(obj) - allowed)
    missing = sorted(required - set(obj))
    if unknown:
        raise ModelInputError(f"{field} contains unexpected fields: {', '.join(unknown)}")
    if missing:
        raise ModelInputError(f"{field} is missing fields: {', '.join(missing)}")


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelInputError(f"{field} must be an object")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ModelInputError(f"{field} must be a non-empty trimmed string")
    return value


def _identifier(value: Any, field: str) -> str:
    text = _string(value, field)
    if not IDENTIFIER_RE.fullmatch(text):
        raise ModelInputError(f"{field} must be a lowercase stable identifier")
    return text


def _nullable_identifier(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _identifier(value, field)


def _positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelInputError(f"{field} must be a positive finite number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ModelInputError(f"{field} must be a positive finite number")
    return number


def _positive_integer_or_none(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ModelInputError(f"{field} must be null or a positive integer")
    return value


def _timestamp_or_none(value: Any, field: str) -> datetime | None:
    if value is None:
        return None
    text = _string(value, field)
    if not RFC3339_RE.fullmatch(text):
        raise ModelInputError(f"{field} must be RFC-3339 with an explicit timezone")
    normalized = text[:-1] + "+00:00" if text[-1:] in {"Z", "z"} else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ModelInputError(f"{field} is not a valid date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ModelInputError(f"{field} must include a timezone")
    return parsed


def _validate_storage_reference(value: Any) -> str:
    text = _string(value, "storage_reference")
    if not STORAGE_RE.fullmatch(text):
        raise ModelInputError("storage_reference must be a canonical external:// reference")
    segments = text[len("external://"):].split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ModelInputError("storage_reference contains noncanonical path segments")
    return text


def _validate_semantics(payload: dict[str, Any]) -> None:
    peril = _mapping(payload["peril"], "peril")
    _closed(peril, {"id", "subperil"}, {"id", "subperil"}, "peril")
    _identifier(peril["id"], "peril.id")
    _nullable_identifier(peril["subperil"], "peril.subperil")

    measure = _mapping(payload["measure"], "measure")
    _closed(measure, {"quantity", "unit", "aggregation"}, {"quantity", "unit", "aggregation"}, "measure")
    _identifier(measure["quantity"], "measure.quantity")
    _string(measure["unit"], "measure.unit")
    if measure["aggregation"] not in AGGREGATIONS:
        raise ModelInputError("invalid measure.aggregation")

    spatial = _mapping(payload["spatial"], "spatial")
    _closed(spatial, {"crs", "support", "resolution"}, {"crs", "support", "resolution"}, "spatial")
    _string(spatial["crs"], "spatial.crs")
    if spatial["support"] not in SPATIAL_SUPPORTS:
        raise ModelInputError("invalid spatial.support")
    resolution = spatial["resolution"]
    if resolution is not None:
        resolution_obj = _mapping(resolution, "spatial.resolution")
        _closed(resolution_obj, {"value", "unit"}, {"value", "unit"}, "spatial.resolution")
        _positive_number(resolution_obj["value"], "spatial.resolution.value")
        _string(resolution_obj["unit"], "spatial.resolution.unit")

    temporal = _mapping(payload["temporal"], "temporal")
    _closed(
        temporal,
        {"support", "start", "end", "step_seconds", "aggregation_window_seconds"},
        {"support", "start", "end", "step_seconds", "aggregation_window_seconds"},
        "temporal",
    )
    if temporal["support"] not in TEMPORAL_SUPPORTS:
        raise ModelInputError("invalid temporal.support")
    start = _timestamp_or_none(temporal["start"], "temporal.start")
    end = _timestamp_or_none(temporal["end"], "temporal.end")
    step = _positive_integer_or_none(temporal["step_seconds"], "temporal.step_seconds")
    window = _positive_integer_or_none(
        temporal["aggregation_window_seconds"], "temporal.aggregation_window_seconds"
    )
    if temporal["support"] == "static":
        if any(value is not None for value in (start, end, step, window)):
            raise ModelInputError("static temporal support requires null bounds and cadence")
    else:
        if start is None or end is None:
            raise ModelInputError("non-static temporal support requires start and end")
        if end <= start:
            raise ModelInputError("temporal.end must be later than temporal.start")

    quality = _mapping(payload["quality"], "quality")
    _closed(
        quality,
        {"missing_value_policy", "quality_flag_policy"},
        {"missing_value_policy", "quality_flag_policy"},
        "quality",
    )
    if quality["missing_value_policy"] not in MISSING_POLICIES:
        raise ModelInputError("invalid quality.missing_value_policy")
    if quality["quality_flag_policy"] not in QUALITY_POLICIES:
        raise ModelInputError("invalid quality.quality_flag_policy")


def _require_manifest_admission(manifest: dict[str, Any], artifact_kind: str) -> None:
    review_status = manifest["review"]["status"]
    admitted_kinds = validate_manifest.REVIEW_KINDS[review_status]
    if artifact_kind not in admitted_kinds:
        raise ModelInputError(
            f"{artifact_kind} artifact is outside referenced manifest review/admission scope"
        )


def _validate_manifest_semantic_bindings(
    payload: dict[str, Any], manifest: dict[str, Any]
) -> None:
    if "variables_and_units" in manifest:
        quantity = payload["measure"]["quantity"]
        unit = payload["measure"]["unit"]
        variables = manifest["variables_and_units"]
        if not any(
            variable["name"] == quantity and variable["unit"] == unit
            for variable in variables
        ):
            raise ModelInputError(
                "measure.quantity/unit does not match referenced manifest variables_and_units"
            )

    manifest_spatial = manifest.get("spatial")
    if manifest_spatial is not None:
        manifest_crs = manifest_spatial.get("crs")
        if manifest_crs is not None and payload["spatial"]["crs"] != manifest_crs:
            raise ModelInputError("spatial.crs does not match referenced manifest")


def validate_model_input(payload: dict[str, Any], *, root: Path = ROOT) -> None:
    _closed(payload, TOP_KEYS, TOP_KEYS, "model input")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ModelInputError("unsupported schema_version")

    manifest_ref = _string(payload["manifest"], "manifest")
    match = MANIFEST_RE.fullmatch(manifest_ref)
    if not match:
        raise ModelInputError("manifest must be a canonical manifests/<dataset_id>.json path")

    dataset_id = _string(payload["dataset_id"], "dataset_id")
    if not DATASET_ID_RE.fullmatch(dataset_id):
        raise ModelInputError("dataset_id contains unsupported characters")
    if match.group(1) != dataset_id:
        raise ModelInputError("manifest path must match dataset_id")

    if payload["artifact"] not in ARTIFACTS:
        raise ModelInputError("artifact must be raw or derived")
    storage_reference = _validate_storage_reference(payload["storage_reference"])
    digest = payload["sha256"]
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise ModelInputError("sha256 must be a lowercase SHA-256")
    if payload["modelling_layer"] not in LAYERS:
        raise ModelInputError("invalid modelling_layer")
    if payload["scientific_role"] not in ROLES:
        raise ModelInputError("invalid scientific_role")

    manifest_path = root / manifest_ref
    if manifest_path.is_symlink():
        raise ModelInputError("referenced manifest must not be a symlink")
    try:
        manifest = validate_manifest.load_manifest(manifest_path)
        validate_manifest.validate_structure(manifest)
    except validate_manifest.ManifestError as exc:
        raise ModelInputError(f"referenced manifest is invalid: {exc}") from exc

    if manifest["dataset_id"] != dataset_id:
        raise ModelInputError("dataset_id does not match referenced manifest")
    version = manifest.get("version_or_release")
    if isinstance(version, str) and version.strip().lower() == "latest":
        raise ModelInputError("referenced manifest uses mutable version label latest")
    if manifest["modelling_layer"] != payload["modelling_layer"]:
        raise ModelInputError("modelling_layer does not match referenced manifest")

    _require_manifest_admission(manifest, payload["artifact"])

    manifest_artifact = manifest.get(f"{payload['artifact']}_artifact")
    if manifest_artifact is None:
        raise ModelInputError(f"{payload['artifact']} artifact is not identified by the manifest")
    if manifest_artifact["storage_reference"] != storage_reference:
        raise ModelInputError("storage_reference does not match selected manifest artifact")
    if manifest_artifact["sha256"] != digest:
        raise ModelInputError("sha256 does not match selected manifest artifact")

    _validate_semantics(payload)
    _validate_manifest_semantic_bindings(payload, manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_input", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        payload = load_strict_json(args.model_input)
        validate_model_input(payload, root=args.root)
    except ModelInputError as exc:
        print(f"BLOCKED: {exc}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
