# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Closed Trusted-Main profiler for the exact receipted ESRM20 Kosovo exposure XML.

The production entry point has no caller-selectable provider target. It transiently
reads one immutable GitLab object, verifies the already-established byte identity,
and only then reports bounded XML metadata/declarations. It never persists provider
bytes and it never promotes selection, value semantics, publication, or model use.
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath
from typing import Any

try:
    from scripts.acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
except ModuleNotFoundError:  # pragma: no cover
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _declared_length,
        _open_fixed,
        _remaining,
        _validate_exact_response,
        utc_now,
    )
    from efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target

_CANONICAL_SOURCE_ISSUE = 282
_CANONICAL_DATASET_ID = "efehr.esrm20.risk-inputs.v1.0"
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Kosovo.xml"
_CANONICAL_EXPECTED_BYTE_COUNT = 664
_CANONICAL_EXPECTED_SHA256 = "61be4c534e6bdd1577d15dd289b2c604fde41f00f8f636901634daf2f41bcceb"
_CANONICAL_MAX_PROFILE_BYTES = 4096
_CANONICAL_NRML_NAMESPACE = "http://openquake.org/xmlns/nrml/0.5"

SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
DATASET_ID = _CANONICAL_DATASET_ID
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
REPOSITORY_PATH = _CANONICAL_REPOSITORY_PATH
EXPECTED_BYTE_COUNT = _CANONICAL_EXPECTED_BYTE_COUNT
EXPECTED_SHA256 = _CANONICAL_EXPECTED_SHA256
MAX_PROFILE_BYTES = _CANONICAL_MAX_PROFILE_BYTES
NRML_NAMESPACE = _CANONICAL_NRML_NAMESPACE

_CANONICAL_OPEN_FIXED = _open_fixed
_CANONICAL_UTC_NOW = utc_now
_CANONICAL_MONOTONIC = time.monotonic


class RuntimeExposureXmlProfileError(RuntimeError):
    """Fail-closed profile error."""


class ByteIdentityMismatch(RuntimeExposureXmlProfileError):
    """Fetched bytes no longer match the trusted receipt."""


class XmlSemanticProfileError(RuntimeExposureXmlProfileError):
    """Exact bytes do not satisfy the bounded XML profile contract."""


def _require_canonical_identity() -> None:
    identities = (
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (DATASET_ID, _CANONICAL_DATASET_ID, "dataset"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (REPOSITORY_PATH, _CANONICAL_REPOSITORY_PATH, "path"),
        (EXPECTED_BYTE_COUNT, _CANONICAL_EXPECTED_BYTE_COUNT, "byte count"),
        (EXPECTED_SHA256, _CANONICAL_EXPECTED_SHA256, "SHA-256"),
        (MAX_PROFILE_BYTES, _CANONICAL_MAX_PROFILE_BYTES, "maximum byte count"),
        (NRML_NAMESPACE, _CANONICAL_NRML_NAMESPACE, "NRML namespace"),
    )
    for observed, expected, label in identities:
        if type(observed) is not type(expected) or observed != expected:
            raise RuntimeExposureXmlProfileError(f"runtime exposure {label} drifted")
    if _open_fixed is not _CANONICAL_OPEN_FIXED or utc_now is not _CANONICAL_UTC_NOW:
        raise RuntimeExposureXmlProfileError("runtime exposure production transport drifted")
    if time.monotonic is not _CANONICAL_MONOTONIC:
        raise RuntimeExposureXmlProfileError("runtime exposure production clock drifted")


def _tag(local: str) -> str:
    return f"{{{NRML_NAMESPACE}}}{local}"


def _only_text(element: ET.Element, *, label: str) -> str:
    if list(element):
        raise XmlSemanticProfileError(f"{label} unexpectedly contains child elements")
    text = (element.text or "").strip()
    if not text:
        raise XmlSemanticProfileError(f"{label} is empty")
    return text


def _safe_asset_reference(value: str) -> str:
    if not value or value != value.strip() or "\\" in value or "\x00" in value:
        raise XmlSemanticProfileError("unsafe asset reference")
    raw_parts = value.split("/")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or any(part in ("", ".", "..") for part in raw_parts)
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise XmlSemanticProfileError("unsafe asset reference")
    if path.suffix.lower() != ".csv":
        raise XmlSemanticProfileError("runtime exposure asset is not CSV")
    return value


def profile_xml_bytes(payload: bytes) -> dict[str, Any]:
    """Profile bounded source declarations; do not infer downstream semantics."""
    if type(payload) is not bytes or not payload:
        raise XmlSemanticProfileError("runtime exposure payload is empty or not bytes")
    if len(payload) > MAX_PROFILE_BYTES:
        raise XmlSemanticProfileError("runtime exposure payload exceeds profile bound")
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise XmlSemanticProfileError("DTD/entity declarations are forbidden")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise XmlSemanticProfileError("runtime exposure XML is malformed") from exc

    root_tag = root.tag
    if type(root_tag) is not str:
        raise XmlSemanticProfileError("runtime exposure NRML root local name drifted")
    if root_tag.startswith("{") and "}" in root_tag:
        root_namespace, root_local_name = root_tag[1:].split("}", 1)
    else:
        root_namespace, root_local_name = "", root_tag
    if root_local_name != "nrml":
        raise XmlSemanticProfileError("runtime exposure NRML root local name drifted")
    if root_namespace != NRML_NAMESPACE:
        if root_namespace == "http://openquake.org/xmlns/nrml/0.4":
            raise XmlSemanticProfileError("runtime exposure NRML root namespace is legacy 0.4")
        raise XmlSemanticProfileError("runtime exposure NRML root namespace is unrecognized")
    if root.attrib:
        raise XmlSemanticProfileError("runtime exposure NRML root attributes present")

    models = list(root)
    if len(models) != 1 or models[0].tag != _tag("exposureModel"):
        raise XmlSemanticProfileError("expected exactly one exposureModel")
    model = models[0]
    allowed_model_attrs = {"id", "category", "taxonomySource"}
    if not set(model.attrib) <= allowed_model_attrs or "id" not in model.attrib:
        raise XmlSemanticProfileError("exposureModel attributes drifted")

    allowed_children = {
        "description", "conversions", "occupancyPeriods", "tagNames", "assets", "exposureFields"
    }
    child_by_local: dict[str, ET.Element] = {}
    for child in model:
        if not child.tag.startswith("{" + NRML_NAMESPACE + "}"):
            raise XmlSemanticProfileError("foreign exposureModel child namespace")
        local = child.tag.split("}", 1)[1]
        if local not in allowed_children or local in child_by_local:
            raise XmlSemanticProfileError("unknown or duplicate exposureModel child")
        child_by_local[local] = child
    if "description" not in child_by_local or "assets" not in child_by_local:
        raise XmlSemanticProfileError("required exposure metadata is missing")

    description = _only_text(child_by_local["description"], label="description")
    assets_el = child_by_local["assets"]
    if list(assets_el) or assets_el.attrib:
        raise XmlSemanticProfileError("assets declaration drifted")
    assets = [_safe_asset_reference(item) for item in (assets_el.text or "").split()]
    if not assets or len(set(assets)) != len(assets):
        raise XmlSemanticProfileError("asset references are empty or duplicated")

    cost_types: list[dict[str, str]] = []
    area: dict[str, str] | None = None
    conversions = child_by_local.get("conversions")
    if conversions is not None:
        if conversions.attrib or (conversions.text or "").strip():
            raise XmlSemanticProfileError("conversions envelope drifted")
        seen_conv: set[str] = set()
        for conv_child in conversions:
            if not conv_child.tag.startswith("{" + NRML_NAMESPACE + "}"):
                raise XmlSemanticProfileError("foreign conversions namespace")
            local = conv_child.tag.split("}", 1)[1]
            if local in seen_conv or local not in {"costTypes", "area"}:
                raise XmlSemanticProfileError("unknown or duplicate conversions child")
            seen_conv.add(local)
            if local == "area":
                if list(conv_child) or (conv_child.text or "").strip() or set(conv_child.attrib) != {"type", "unit"}:
                    raise XmlSemanticProfileError("area declaration drifted")
                area = {"type": conv_child.attrib["type"], "unit": conv_child.attrib["unit"]}
            else:
                if conv_child.attrib or (conv_child.text or "").strip():
                    raise XmlSemanticProfileError("costTypes envelope drifted")
                for entry in conv_child:
                    if entry.tag != _tag("costType") or list(entry) or (entry.text or "").strip():
                        raise XmlSemanticProfileError("costType declaration drifted")
                    if set(entry.attrib) != {"name", "type", "unit"}:
                        raise XmlSemanticProfileError("costType attributes drifted")
                    cost_types.append({key: entry.attrib[key] for key in ("name", "type", "unit")})
        names = [item["name"] for item in cost_types]
        if len(names) != len(set(names)):
            raise XmlSemanticProfileError("duplicate costType name")

    def split_text(name: str) -> list[str]:
        element = child_by_local.get(name)
        if element is None:
            return []
        if list(element) or element.attrib:
            raise XmlSemanticProfileError(f"{name} declaration drifted")
        return (element.text or "").split()

    occupancy_periods = split_text("occupancyPeriods")
    tag_names = split_text("tagNames")

    exposure_fields: list[dict[str, str]] = []
    fields = child_by_local.get("exposureFields")
    if fields is not None:
        if fields.attrib or (fields.text or "").strip():
            raise XmlSemanticProfileError("exposureFields envelope drifted")
        for field in fields:
            if field.tag != _tag("field") or list(field) or (field.text or "").strip():
                raise XmlSemanticProfileError("exposure field declaration drifted")
            keys = set(field.attrib)
            if not {"oq", "input"} <= keys or not keys <= {"oq", "input", "type"}:
                raise XmlSemanticProfileError("exposure field attributes drifted")
            exposure_fields.append({key: field.attrib[key] for key in ("oq", "type", "input") if key in field.attrib})

    return {
        "nrml_namespace": NRML_NAMESPACE,
        "exposure_model": {
            "id": model.attrib["id"],
            "category": model.attrib.get("category"),
            "taxonomy_source": model.attrib.get("taxonomySource"),
            "description": description,
        },
        "asset_references": assets,
        "cost_types": cost_types,
        "area": area,
        "occupancy_periods": occupancy_periods,
        "tag_names": tag_names,
        "exposure_fields": exposure_fields,
        "structural_cost_type_declared": any(item["name"] == "structural" for item in cost_types),
        "structural_value_inputs": [
            item["input"] for item in exposure_fields
            if item.get("oq") == "value" and item.get("type") == "structural"
        ],
    }


def _fetch_exact_payload(*, opener: Any, now: Any, monotonic: Any) -> tuple[bytes, dict[str, Any]]:
    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
        url = raw_file_api_url(target)
    except EfehrReceiptError as exc:
        raise EfehrAcquisitionError("trusted runtime exposure target is invalid") from exc
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/xml,text/xml,text/plain;q=0.9", "User-Agent": "OpenCatastrophe-EFEHR-xml-profile-v1"},
        method="GET",
    )
    try:
        with opener(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, url)
            _declared_length(response, MAX_PROFILE_BYTES)
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(min(1024, MAX_PROFILE_BYTES + 1 - total))
                if not chunk:
                    break
                if type(chunk) is not bytes:
                    raise EfehrAcquisitionError("provider returned non-bytes payload")
                total += len(chunk)
                if total > MAX_PROFILE_BYTES:
                    raise EfehrAcquisitionError("runtime exposure XML exceeds profile bound")
                chunks.append(chunk)
            payload = b"".join(chunks)
            headers = getattr(response, "headers", {})
            receipt = {
                "retrieved_at": now(),
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "content_type": headers.get("Content-Type") if hasattr(headers, "get") else None,
                "etag": headers.get("ETag") if hasattr(headers, "get") else None,
            }
    except (EfehrAcquisitionError, OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        raise
    return payload, receipt


def _profile_runtime_exposure_xml(*, opener: Any, now: Any, monotonic: Any) -> dict[str, Any]:
    payload, receipt = _fetch_exact_payload(opener=opener, now=now, monotonic=monotonic)
    if receipt["byte_count"] != EXPECTED_BYTE_COUNT or receipt["sha256"] != EXPECTED_SHA256:
        raise ByteIdentityMismatch("runtime exposure bytes do not match trusted receipt")
    profile = profile_xml_bytes(payload)
    return {
        "runtime_exposure_identity": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "repository_path": REPOSITORY_PATH,
        },
        "receipt": receipt,
        "profile": profile,
        "xml_content_interpreted": True,
        "exact_kosovo_exposure_selected": False,
        "value_structural_wiring_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def profile_runtime_exposure_xml() -> dict[str, Any]:
    _require_canonical_identity()
    return _profile_runtime_exposure_xml(
        opener=_CANONICAL_OPEN_FIXED,
        now=_CANONICAL_UTC_NOW,
        monotonic=_CANONICAL_MONOTONIC,
    )