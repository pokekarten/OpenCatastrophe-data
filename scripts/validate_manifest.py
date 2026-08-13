# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Strict, dependency-free validation for OpenCatastrophe dataset manifests."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

SCHEMA_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
DATASET_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
EXTERNAL_RE = re.compile(r"^external://[A-Za-z0-9][A-Za-z0-9._/-]*$")
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")
SENSITIVE_QUERY = {
    "access_key", "access_token", "api_key", "apikey", "auth", "authorization", "credential",
    "key", "secret", "sig", "signature", "token", "x-amz-credential",
    "x-amz-signature", "x-goog-credential", "x-goog-signature",
}
LOCAL_HOST_SUFFIXES = (".local", ".localhost", ".internal")

TOP_KEYS = {
    "schema_version", "dataset_id", "provider", "product_name", "version_or_release",
    "canonical_source", "retrieved_at", "retrieval_query_or_filters", "access_class",
    "modelling_layer", "intended_use", "raw_artifact", "derived_artifact", "licensing",
    "redistribution", "privacy", "spatial", "temporal", "variables_and_units",
    "transformation", "review",
}
REQUIRED_TOP = {
    "schema_version", "dataset_id", "provider", "product_name", "canonical_source",
    "retrieved_at", "access_class", "modelling_layer", "intended_use", "licensing",
    "redistribution", "privacy", "review",
}
ARTIFACT_KEYS = {"byte_size", "sha256", "storage_reference"}
LICENSING_KEYS = {
    "status", "spdx_expression", "licence_name", "terms_reference", "terms_reviewed_at",
    "terms_version_or_date", "terms_content_sha256", "commercial_use_status",
    "attribution_requirements", "share_alike_or_derivative_requirements", "notes",
}
REDISTRIBUTION_KEYS = {"status", "scope", "conditions"}
PRIVACY_KEYS = {"personal_data_status", "confidential_or_proprietary_status", "notes"}
REVIEW_KEYS = {"status", "reviewed_at", "reviewer", "notes"}
TRANSFORMATION_KEYS = {"code_reference", "config_identity"}
SPATIAL_KEYS = {"crs", "extent"}
TEMPORAL_KEYS = {"extent"}
VARIABLE_KEYS = {"name", "unit", "description"}

ACCESS = {"open", "registration_required", "authenticated", "restricted", "unknown"}
LAYERS = {"event_catalogue", "hazard", "exposure", "vulnerability", "observed_loss", "engine", "standard", "other"}
LICENCE_STATUS = {"verified", "unverified", "conflicting", "unknown"}
COMMERCIAL = {"allowed", "restricted", "prohibited", "unknown"}
REDIST_STATUS = {"allowed", "restricted", "prohibited", "unknown"}
REDIST_SCOPE = {"raw", "derived_only", "metadata_only", "none"}
PERSONAL = {"none", "contains", "unknown"}
REVIEW_STATUS = {"pending", "approved_metadata_only", "approved_derived", "approved_raw", "rejected"}
PUBLIC_KINDS = {"metadata", "derived", "raw"}
SCOPE_KINDS = {
    "none": set(), "metadata_only": {"metadata"},
    "derived_only": {"metadata", "derived"}, "raw": {"metadata", "derived", "raw"},
}
REVIEW_KINDS = {
    "pending": set(), "rejected": set(), "approved_metadata_only": {"metadata"},
    "approved_derived": {"metadata", "derived"}, "approved_raw": {"metadata", "derived", "raw"},
}


class ManifestError(ValueError):
    pass


def _reject_constant(value: str) -> None:
    raise ManifestError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise ManifestError("manifest root must be an object")
    return payload


def _closed(obj: dict[str, Any], allowed: set[str], required: set[str], field: str) -> None:
    unknown = sorted(set(obj) - allowed)
    missing = sorted(required - set(obj))
    if unknown:
        raise ManifestError(f"{field} contains unexpected fields: {', '.join(unknown)}")
    if missing:
        raise ManifestError(f"{field} is missing fields: {', '.join(missing)}")


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be an object")
    return value


def _string(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ManifestError(f"{field} must be a non-empty trimmed string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ManifestError(f"{field} must be valid UTF-8") from exc
    return value


def _timestamp(value: Any, field: str) -> str:
    text = _string(value, field)
    assert text is not None
    if not RFC3339_RE.fullmatch(text):
        raise ManifestError(f"{field} must be RFC-3339 with an explicit timezone")
    normalized = text[:-1] + "+00:00" if text[-1:] in {"Z", "z"} else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ManifestError(f"{field} is not a valid date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ManifestError(f"{field} must include a timezone")
    return text


def _public_url(value: Any, field: str) -> str:
    text = _string(value, field)
    assert text is not None
    if any(ch.isspace() for ch in text):
        raise ManifestError(f"{field} must not contain whitespace")
    try:
        parsed = urlparse(text)
        host = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise ManifestError(f"{field} is malformed") from exc
    if not text.startswith("https://") or parsed.scheme != "https" or not parsed.netloc:
        raise ManifestError(f"{field} must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise ManifestError(f"{field} must not contain URL credentials")
    if not host:
        raise ManifestError(f"{field} must contain a hostname")
    lowered = host.lower().rstrip(".")
    if lowered == "localhost" or lowered.endswith(LOCAL_HOST_SUFFIXES):
        raise ManifestError(f"{field} must not reference a local/private hostname")
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise ManifestError(f"{field} must not reference a non-global IP address")
    if any(name.lower() in SENSITIVE_QUERY for name, _ in parse_qsl(parsed.query, keep_blank_values=True)):
        raise ManifestError(f"{field} must not contain credential/signature query parameters")
    return text


def _external_reference(value: Any, field: str) -> str:
    text = _string(value, field)
    assert text is not None
    if not EXTERNAL_RE.fullmatch(text):
        raise ManifestError(f"{field} must be a canonical external:// reference")
    segments = text[len("external://"):].split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ManifestError(f"{field} must not contain empty, dot, or parent path segments")
    return text


def _artifact(value: Any, field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    obj = _mapping(value, field)
    _closed(obj, ARTIFACT_KEYS, ARTIFACT_KEYS, field)
    size = obj["byte_size"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ManifestError(f"{field}.byte_size must be a non-negative integer")
    digest = obj["sha256"]
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise ManifestError(f"{field}.sha256 must be a lowercase SHA-256")
    _external_reference(obj["storage_reference"], f"{field}.storage_reference")
    return obj


def _optional_scope(manifest: dict[str, Any]) -> None:
    spatial = manifest.get("spatial")
    if spatial is not None:
        obj = _mapping(spatial, "spatial")
        _closed(obj, SPATIAL_KEYS, set(), "spatial")
        for key in obj:
            if obj[key] is not None:
                _string(obj[key], f"spatial.{key}")
    temporal = manifest.get("temporal")
    if temporal is not None:
        obj = _mapping(temporal, "temporal")
        _closed(obj, TEMPORAL_KEYS, set(), "temporal")
        if obj.get("extent") is not None:
            _string(obj["extent"], "temporal.extent")
    variables = manifest.get("variables_and_units", [])
    if not isinstance(variables, list):
        raise ManifestError("variables_and_units must be an array")
    for index, value in enumerate(variables):
        obj = _mapping(value, f"variables_and_units[{index}]")
        _closed(obj, VARIABLE_KEYS, {"name", "unit"}, f"variables_and_units[{index}]")
        _string(obj["name"], f"variables_and_units[{index}].name")
        if obj["unit"] is not None:
            _string(obj["unit"], f"variables_and_units[{index}].unit")
        if obj.get("description") is not None:
            _string(obj["description"], f"variables_and_units[{index}].description")


def validate_structure(manifest: dict[str, Any]) -> None:
    _closed(manifest, TOP_KEYS, REQUIRED_TOP, "manifest")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestError("unsupported schema_version")
    dataset_id = _string(manifest["dataset_id"], "dataset_id")
    assert dataset_id is not None
    if not DATASET_ID_RE.fullmatch(dataset_id):
        raise ManifestError("dataset_id contains unsupported characters")
    for key in ("provider", "product_name", "intended_use"):
        _string(manifest[key], key)
    if manifest.get("version_or_release") is not None:
        _string(manifest["version_or_release"], "version_or_release")
    _public_url(manifest["canonical_source"], "canonical_source")
    _timestamp(manifest["retrieved_at"], "retrieved_at")
    if manifest.get("retrieval_query_or_filters") is not None:
        _string(manifest["retrieval_query_or_filters"], "retrieval_query_or_filters")
    if manifest["access_class"] not in ACCESS:
        raise ManifestError("invalid access_class")
    if manifest["modelling_layer"] not in LAYERS:
        raise ManifestError("invalid modelling_layer")

    licensing = _mapping(manifest["licensing"], "licensing")
    _closed(licensing, LICENSING_KEYS, {"status", "terms_reference", "terms_reviewed_at", "commercial_use_status"}, "licensing")
    if licensing["status"] not in LICENCE_STATUS:
        raise ManifestError("invalid licensing.status")
    _public_url(licensing["terms_reference"], "licensing.terms_reference")
    _timestamp(licensing["terms_reviewed_at"], "licensing.terms_reviewed_at")
    if licensing["commercial_use_status"] not in COMMERCIAL:
        raise ManifestError("invalid licensing.commercial_use_status")
    for key in ("spdx_expression", "licence_name", "terms_version_or_date", "attribution_requirements", "share_alike_or_derivative_requirements", "notes"):
        if licensing.get(key) is not None:
            _string(licensing[key], f"licensing.{key}")
    terms_hash = licensing.get("terms_content_sha256")
    if terms_hash is not None and (not isinstance(terms_hash, str) or not SHA256_RE.fullmatch(terms_hash)):
        raise ManifestError("licensing.terms_content_sha256 must be null or a lowercase SHA-256")
    if licensing["status"] == "verified" and not (licensing.get("spdx_expression") or licensing.get("licence_name")):
        raise ManifestError("verified licensing requires a licence identity")

    redistribution = _mapping(manifest["redistribution"], "redistribution")
    _closed(redistribution, REDISTRIBUTION_KEYS, {"status", "scope"}, "redistribution")
    if redistribution["status"] not in REDIST_STATUS or redistribution["scope"] not in REDIST_SCOPE:
        raise ManifestError("invalid redistribution state")
    if redistribution.get("conditions") is not None:
        _string(redistribution["conditions"], "redistribution.conditions")
    if redistribution["status"] in {"unknown", "prohibited"} and redistribution["scope"] != "none":
        raise ManifestError("unknown/prohibited redistribution must use scope=none")
    if redistribution["status"] == "allowed" and redistribution["scope"] == "none":
        raise ManifestError("allowed redistribution cannot use scope=none")

    privacy = _mapping(manifest["privacy"], "privacy")
    _closed(privacy, PRIVACY_KEYS, {"personal_data_status", "confidential_or_proprietary_status"}, "privacy")
    if privacy["personal_data_status"] not in PERSONAL or privacy["confidential_or_proprietary_status"] not in PERSONAL:
        raise ManifestError("invalid privacy state")
    if privacy.get("notes") is not None:
        _string(privacy["notes"], "privacy.notes")

    review = _mapping(manifest["review"], "review")
    _closed(review, REVIEW_KEYS, {"status", "reviewed_at", "reviewer"}, "review")
    if review["status"] not in REVIEW_STATUS:
        raise ManifestError("invalid review.status")
    if review["status"] == "pending":
        if review["reviewed_at"] is not None or review["reviewer"] is not None:
            raise ManifestError("pending review must not claim reviewer/reviewed_at")
    else:
        _timestamp(review["reviewed_at"], "review.reviewed_at")
        _string(review["reviewer"], "review.reviewer")
    if review.get("notes") is not None:
        _string(review["notes"], "review.notes")

    raw = _artifact(manifest.get("raw_artifact"), "raw_artifact")
    derived = _artifact(manifest.get("derived_artifact"), "derived_artifact")
    transformation = manifest.get("transformation")
    if transformation is not None:
        obj = _mapping(transformation, "transformation")
        _closed(obj, TRANSFORMATION_KEYS, TRANSFORMATION_KEYS, "transformation")
        _string(obj["code_reference"], "transformation.code_reference")
        _string(obj["config_identity"], "transformation.config_identity")
    if derived is not None and transformation is None:
        raise ManifestError("derived_artifact requires transformation lineage")
    _optional_scope(manifest)


def assert_public_asset_allowed(manifest: dict[str, Any], asset_kind: str) -> None:
    validate_structure(manifest)
    if asset_kind not in PUBLIC_KINDS:
        raise ManifestError(f"unsupported asset kind: {asset_kind}")
    licensing = manifest["licensing"]
    redistribution = manifest["redistribution"]
    privacy = manifest["privacy"]
    review = manifest["review"]
    if manifest["access_class"] == "unknown":
        raise ManifestError("source access class is unknown")
    if asset_kind == "raw" and manifest["access_class"] == "restricted":
        raise ManifestError("restricted source access blocks raw source-byte publication")
    if licensing["status"] != "verified" or licensing["commercial_use_status"] != "allowed":
        raise ManifestError("licensing is not verified for commercial use")
    if redistribution["status"] != "allowed":
        raise ManifestError("redistribution is not explicitly allowed")
    if privacy["personal_data_status"] != "none" or privacy["confidential_or_proprietary_status"] != "none":
        raise ManifestError("privacy/confidentiality is not explicitly clear")
    if asset_kind not in SCOPE_KINDS[redistribution["scope"]]:
        raise ManifestError("asset kind exceeds source redistribution scope")
    if asset_kind not in REVIEW_KINDS[review["status"]]:
        raise ManifestError("asset kind exceeds repository review scope")
    if asset_kind == "raw" and manifest.get("raw_artifact") is None:
        raise ManifestError("raw publication requires raw_artifact identity")
    if asset_kind == "derived" and (manifest.get("derived_artifact") is None or manifest.get("transformation") is None):
        raise ManifestError("derived publication requires artifact identity and transformation lineage")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--public-asset", choices=("metadata", "derived", "raw"))
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        validate_structure(manifest)
        if args.public_asset:
            assert_public_asset_allowed(manifest, args.public_asset)
    except ManifestError as exc:
        print(f"BLOCKED: {exc}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
