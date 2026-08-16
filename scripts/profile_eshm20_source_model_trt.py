# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile bounded ESHM20 source-model TRT/source-type structure.

The parser is deliberately narrower than OpenQuake source conversion.  It
checks payload bytes against a caller-supplied child receipt identity that is
itself fenced to the trusted #414 receipt-set locator, then extracts only
source element types and effective tectonic-region labels.  It does not claim
that the supplied child receipt was itself retrieved from the canonical GitHub
ledger; that stronger binding belongs to a later trusted-main wrapper.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import re
import xml.etree.ElementTree as ET
from typing import Any, Iterable

try:
    from scripts.acquire_eshm20_source_model_child_receipts import (
        CHILDREN,
        EXPECTED_CHILD_COUNT,
        EXPECTED_PATHS_SHA256,
        MAX_ARTIFACT_BYTES,
        _paths_fingerprint,
        _require_canonical_child_set,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_eshm20_source_model_child_receipts import (
        CHILDREN,
        EXPECTED_CHILD_COUNT,
        EXPECTED_PATHS_SHA256,
        MAX_ARTIFACT_BYTES,
        _paths_fingerprint,
        _require_canonical_child_set,
    )

SCHEMA_VERSION = "oc-eshm20-source-model-trt-profile-v1"
AGGREGATE_SCHEMA_VERSION = "oc-eshm20-source-model-trt-aggregate-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 435
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"

RECEIPT_SET_RESULT_COMMENT_ID = 5306897047
RECEIPT_SET_RUN_ID = 31940875325
RECEIPT_SET_EXECUTION_SHA = "473f03765fd63d2da7e48d0c22b1618d4e1254d8"
RECEIPT_SET_CHILD_COUNT = 51
RECEIPT_SET_PATHS_SHA256 = (
    "2fcc885dc9fbbd8e9ee45b185dc9f2339af3654e9976ae5f07d4d097551944b7"
)
CHILD_PARENT_RESULT_COMMENT_ID = 5304432768

OPENQUAKE_REPOSITORY = "gem/oq-engine"
OPENQUAKE_TAG = "v3.14.0"
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
OPENQUAKE_SOURCE_CONVERTER_REFERENCE = (
    "openquake/hazardlib/sourceconverter.py::SourceConverter"
)

MAX_TRT_CHARS = 256
MAX_SOURCES_PER_FILE = 250_000
MAX_UNIQUE_TRTS_PER_FILE = 64
MAX_UNIQUE_SOURCE_TYPES_PER_FILE = 32

_SUPPORTED_SOURCE_TYPES = frozenset(
    {
        "areaSource",
        "pointSource",
        "multiPointSource",
        "simpleFaultSource",
        "kiteFaultSource",
        "complexFaultSource",
        "characteristicFaultSource",
        "nonParametricSeismicSource",
        "multiFaultSource",
    }
)
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class Eshm20SourceModelTrtProfileError(ValueError):
    """Raised when bounded source-model structure cannot close safely."""


@dataclass(frozen=True)
class ExpectedChildReceipt:
    """Expected byte identity plus fixed #414 receipt-set locator.

    Matching these fields does *not* independently prove that this receipt was
    fetched from GitHub comment 5306897047; it only supplies the exact expected
    byte identity for a later trusted wrapper to bind to that durable ledger
    result.
    """

    repository_path: str
    byte_count: int
    sha256: str
    project_id: int = PROJECT_ID
    project_path: str = PROJECT_PATH
    commit_sha: str = COMMIT_SHA
    receipt_set_result_comment_id: int = RECEIPT_SET_RESULT_COMMENT_ID
    receipt_set_run_id: int = RECEIPT_SET_RUN_ID
    receipt_set_execution_sha: str = RECEIPT_SET_EXECUTION_SHA
    child_parent_result_comment_id: int = CHILD_PARENT_RESULT_COMMENT_ID


def _local_name(tag: object) -> str:
    if type(tag) is not str:
        raise Eshm20SourceModelTrtProfileError("source-model XML tag has invalid type")
    return tag.rsplit("}", 1)[-1]


def _canonical_paths() -> tuple[str, ...]:
    try:
        specs = _require_canonical_child_set()
    except Exception as exc:  # defensive conversion of upstream worker error type
        raise Eshm20SourceModelTrtProfileError(
            "frozen ESHM20 source-model child authority is invalid"
        ) from exc
    paths = tuple(spec.repository_path for spec in specs)
    if len(paths) != RECEIPT_SET_CHILD_COUNT:
        raise Eshm20SourceModelTrtProfileError("canonical child count drifted")
    if RECEIPT_SET_CHILD_COUNT != EXPECTED_CHILD_COUNT:
        raise Eshm20SourceModelTrtProfileError("receipt-set child count authority drifted")
    if RECEIPT_SET_PATHS_SHA256 != EXPECTED_PATHS_SHA256:
        raise Eshm20SourceModelTrtProfileError("receipt-set path fingerprint authority drifted")
    if _paths_fingerprint(specs) != RECEIPT_SET_PATHS_SHA256:
        raise Eshm20SourceModelTrtProfileError("canonical child path fingerprint is invalid")
    return paths


def _validate_receipt(receipt: ExpectedChildReceipt) -> ExpectedChildReceipt:
    if type(receipt) is not ExpectedChildReceipt:
        raise Eshm20SourceModelTrtProfileError("expected child receipt has invalid type")
    if receipt.repository_path not in set(_canonical_paths()):
        raise Eshm20SourceModelTrtProfileError("receipt path is not one of the fixed 51 children")
    fixed = (
        (receipt.project_id, PROJECT_ID, "project id"),
        (receipt.project_path, PROJECT_PATH, "project path"),
        (receipt.commit_sha, COMMIT_SHA, "provider commit"),
        (
            receipt.receipt_set_result_comment_id,
            RECEIPT_SET_RESULT_COMMENT_ID,
            "receipt-set result comment",
        ),
        (receipt.receipt_set_run_id, RECEIPT_SET_RUN_ID, "receipt-set run"),
        (
            receipt.receipt_set_execution_sha,
            RECEIPT_SET_EXECUTION_SHA,
            "receipt-set execution",
        ),
        (
            receipt.child_parent_result_comment_id,
            CHILD_PARENT_RESULT_COMMENT_ID,
            "child parent result",
        ),
    )
    for observed, expected, label in fixed:
        if type(observed) is not type(expected) or observed != expected:
            raise Eshm20SourceModelTrtProfileError(f"{label} does not match frozen authority")
    if type(receipt.byte_count) is not int or not (0 < receipt.byte_count <= MAX_ARTIFACT_BYTES):
        raise Eshm20SourceModelTrtProfileError("receipt byte count is invalid")
    if type(receipt.sha256) is not str or not _SHA256_RE.fullmatch(receipt.sha256):
        raise Eshm20SourceModelTrtProfileError("receipt SHA-256 is invalid")
    return receipt


def _verify_payload_identity(payload: bytes, receipt: ExpectedChildReceipt) -> str:
    if type(payload) is not bytes:
        raise Eshm20SourceModelTrtProfileError("source-model payload must be immutable bytes")
    if len(payload) != receipt.byte_count:
        raise Eshm20SourceModelTrtProfileError("source-model byte count does not match receipt")
    observed = hashlib.sha256(payload).hexdigest()
    if observed != receipt.sha256:
        raise Eshm20SourceModelTrtProfileError("source-model SHA-256 does not match receipt")
    return observed


def _safe_trt(value: object, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise Eshm20SourceModelTrtProfileError(f"{field} is missing or not canonical")
    if len(value) > MAX_TRT_CHARS:
        raise Eshm20SourceModelTrtProfileError(f"{field} exceeds bounds")
    if not value.isprintable() or any(ord(char) == 127 for char in value):
        raise Eshm20SourceModelTrtProfileError(f"{field} contains controls")
    return value


def _parse_xml(payload: bytes) -> ET.Element:
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Eshm20SourceModelTrtProfileError("verified source-model bytes are not UTF-8") from exc
    lowered = text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise Eshm20SourceModelTrtProfileError("DTD/entity declarations are not allowed")
    if "\x00" in text:
        raise Eshm20SourceModelTrtProfileError("NUL is not allowed in source-model XML")
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        raise Eshm20SourceModelTrtProfileError("verified source-model XML is malformed") from exc


def _record_source(
    node: ET.Element,
    *,
    group_trt: str | None,
    type_counts: Counter[str],
    trt_counts: Counter[str],
    provenance_counts: Counter[str],
) -> None:
    source_type = _local_name(node.tag)
    if source_type not in _SUPPORTED_SOURCE_TYPES:
        raise Eshm20SourceModelTrtProfileError(
            f"unsupported source-model child element: {source_type}"
        )
    direct = node.attrib.get("tectonicRegion")
    if group_trt is None:
        effective = _safe_trt(direct, "source tectonicRegion")
        provenance = "direct_source"
    else:
        effective = group_trt
        if direct is None:
            provenance = "group_inherited"
        else:
            direct_trt = _safe_trt(direct, "source tectonicRegion")
            if direct_trt != group_trt:
                raise Eshm20SourceModelTrtProfileError(
                    "source tectonicRegion conflicts with sourceGroup tectonicRegion"
                )
            provenance = "group_effective_direct_confirmed"

    type_counts[source_type] += 1
    trt_counts[effective] += 1
    provenance_counts[provenance] += 1
    if sum(type_counts.values()) > MAX_SOURCES_PER_FILE:
        raise Eshm20SourceModelTrtProfileError("source count exceeds bounds")
    if len(type_counts) > MAX_UNIQUE_SOURCE_TYPES_PER_FILE:
        raise Eshm20SourceModelTrtProfileError("source-type count exceeds bounds")
    if len(trt_counts) > MAX_UNIQUE_TRTS_PER_FILE:
        raise Eshm20SourceModelTrtProfileError("tectonic-region count exceeds bounds")


def _profile_root(root: ET.Element) -> dict[str, Any]:
    if _local_name(root.tag) != "nrml":
        raise Eshm20SourceModelTrtProfileError("source-model root must be nrml")
    children = list(root)
    if len(children) != 1 or _local_name(children[0].tag) != "sourceModel":
        raise Eshm20SourceModelTrtProfileError("nrml must contain exactly one sourceModel")
    source_model = children[0]

    type_counts: Counter[str] = Counter()
    trt_counts: Counter[str] = Counter()
    provenance_counts: Counter[str] = Counter()
    group_count = 0

    for child in source_model:
        tag = _local_name(child.tag)
        if tag == "sourceGroup":
            group_count += 1
            group_trt = _safe_trt(child.attrib.get("tectonicRegion"), "sourceGroup tectonicRegion")
            for source_node in child:
                if _local_name(source_node.tag) == "sourceGroup":
                    raise Eshm20SourceModelTrtProfileError("nested sourceGroup is unsupported")
                _record_source(
                    source_node,
                    group_trt=group_trt,
                    type_counts=type_counts,
                    trt_counts=trt_counts,
                    provenance_counts=provenance_counts,
                )
        else:
            _record_source(
                child,
                group_trt=None,
                type_counts=type_counts,
                trt_counts=trt_counts,
                provenance_counts=provenance_counts,
            )

    source_count = sum(type_counts.values())
    if source_count < 1:
        raise Eshm20SourceModelTrtProfileError("sourceModel contains no sources")
    return {
        "source_count": source_count,
        "source_group_count": group_count,
        "source_type_counts": dict(sorted(type_counts.items())),
        "tectonic_region_type_counts": dict(sorted(trt_counts.items())),
        "trt_provenance_counts": dict(sorted(provenance_counts.items())),
        "unique_source_types": sorted(type_counts),
        "unique_tectonic_region_types": sorted(trt_counts),
    }


def profile_receipted_source_model(
    payload: bytes,
    expected_receipt: ExpectedChildReceipt,
) -> dict[str, Any]:
    """Verify payload↔receipt bytes, then profile bounded source structure."""

    receipt = _validate_receipt(expected_receipt)
    observed_sha256 = _verify_payload_identity(payload, receipt)
    structural = _profile_root(_parse_xml(payload))
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "receipt_identity": {
            "repository_path": receipt.repository_path,
            "byte_count": receipt.byte_count,
            "sha256": observed_sha256,
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "receipt_set_result_comment_id": RECEIPT_SET_RESULT_COMMENT_ID,
            "receipt_set_run_id": RECEIPT_SET_RUN_ID,
            "receipt_set_execution_sha": RECEIPT_SET_EXECUTION_SHA,
        },
        **structural,
        "openquake_reference": {
            "repository": OPENQUAKE_REPOSITORY,
            "tag": OPENQUAKE_TAG,
            "commit": OPENQUAKE_COMMIT,
            "source_converter_reference": OPENQUAKE_SOURCE_CONVERTER_REFERENCE,
        },
        "receipt_payload_identity_verified": True,
        "canonical_414_ledger_binding_verified": False,
        "source_structure_profile_verified": True,
        "source_physics_validity_verified": False,
        "source_gsim_trt_compatibility_verified": False,
        "branch_weight_validity_verified": False,
        "numerical_hazard_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def aggregate_source_model_profiles(profiles: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate exactly the fixed 51 path-bound profiles without widening claims."""

    items = list(profiles)
    if len(items) != RECEIPT_SET_CHILD_COUNT:
        raise Eshm20SourceModelTrtProfileError("aggregate requires exactly 51 child profiles")
    canonical_paths = _canonical_paths()
    observed_paths: list[str] = []
    type_counts: Counter[str] = Counter()
    trt_counts: Counter[str] = Counter()
    provenance_counts: Counter[str] = Counter()
    total_sources = 0
    for item in items:
        if type(item) is not dict or item.get("schema_version") != SCHEMA_VERSION:
            raise Eshm20SourceModelTrtProfileError("aggregate child profile schema is invalid")
        if item.get("receipt_payload_identity_verified") is not True:
            raise Eshm20SourceModelTrtProfileError("aggregate child payload identity is unverified")
        if item.get("source_structure_profile_verified") is not True:
            raise Eshm20SourceModelTrtProfileError("aggregate child source profile is unverified")
        if item.get("canonical_414_ledger_binding_verified") is not False:
            raise Eshm20SourceModelTrtProfileError("unexpected #414 ledger authority widening")
        receipt = item.get("receipt_identity")
        if type(receipt) is not dict:
            raise Eshm20SourceModelTrtProfileError("aggregate child receipt identity is invalid")
        path = receipt.get("repository_path")
        if type(path) is not str:
            raise Eshm20SourceModelTrtProfileError("aggregate child path is invalid")
        observed_paths.append(path)
        child_types = item.get("source_type_counts")
        child_trts = item.get("tectonic_region_type_counts")
        child_provenance = item.get("trt_provenance_counts")
        if not all(type(value) is dict for value in (child_types, child_trts, child_provenance)):
            raise Eshm20SourceModelTrtProfileError("aggregate child counts are invalid")
        for label, count in child_types.items():
            if label not in _SUPPORTED_SOURCE_TYPES or type(count) is not int or count < 0:
                raise Eshm20SourceModelTrtProfileError("aggregate source-type count is invalid")
            type_counts[label] += count
        for label, count in child_trts.items():
            _safe_trt(label, "aggregate tectonic region")
            if type(count) is not int or count < 0:
                raise Eshm20SourceModelTrtProfileError("aggregate TRT count is invalid")
            trt_counts[label] += count
        for label, count in child_provenance.items():
            if label not in {"direct_source", "group_inherited", "group_effective_direct_confirmed"}:
                raise Eshm20SourceModelTrtProfileError("aggregate TRT provenance is invalid")
            if type(count) is not int or count < 0:
                raise Eshm20SourceModelTrtProfileError("aggregate TRT provenance count is invalid")
            provenance_counts[label] += count
        child_total = item.get("source_count")
        if type(child_total) is not int or child_total < 1:
            raise Eshm20SourceModelTrtProfileError("aggregate child source count is invalid")
        if sum(child_types.values()) != child_total or sum(child_trts.values()) != child_total:
            raise Eshm20SourceModelTrtProfileError("aggregate child counts are inconsistent")
        if sum(child_provenance.values()) != child_total:
            raise Eshm20SourceModelTrtProfileError("aggregate child TRT provenance is inconsistent")
        total_sources += child_total

    if len(set(observed_paths)) != RECEIPT_SET_CHILD_COUNT:
        raise Eshm20SourceModelTrtProfileError("aggregate child paths are not unique")
    if tuple(sorted(observed_paths)) != canonical_paths:
        raise Eshm20SourceModelTrtProfileError("aggregate does not cover the fixed 51 child paths")
    return {
        "schema_version": AGGREGATE_SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "child_count": RECEIPT_SET_CHILD_COUNT,
        "child_paths_sha256": RECEIPT_SET_PATHS_SHA256,
        "source_count": total_sources,
        "source_type_counts": dict(sorted(type_counts.items())),
        "tectonic_region_type_counts": dict(sorted(trt_counts.items())),
        "trt_provenance_counts": dict(sorted(provenance_counts.items())),
        "unique_source_types": sorted(type_counts),
        "unique_tectonic_region_types": sorted(trt_counts),
        "receipt_set_locator": {
            "result_comment_id": RECEIPT_SET_RESULT_COMMENT_ID,
            "run_id": RECEIPT_SET_RUN_ID,
            "execution_sha": RECEIPT_SET_EXECUTION_SHA,
            "provider_commit": COMMIT_SHA,
        },
        "receipt_payload_identities_verified": True,
        "canonical_414_ledger_binding_verified": False,
        "source_structure_profile_verified": True,
        "source_physics_validity_verified": False,
        "source_gsim_trt_compatibility_verified": False,
        "branch_weight_validity_verified": False,
        "numerical_hazard_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
