# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile external resource references from the receipted ESHM20 GMM tree.

The exact GMM logic-tree bytes are already frozen by the trusted #361 receipt.
This worker re-materializes only that immutable provider object, verifies its
byte identity before decoding/inspection, and reproduces only the narrow
OpenQuake 3.14 ``gsim_lt.rel_paths`` external-resource discovery rule:
assignment keys ending ``_file`` or ``_table`` may name relative resources.

It never instantiates GSIM classes, loads referenced resources, returns provider
bytes, or interprets GMM coefficients, branch weights, IMTs or model fitness.
"""

from __future__ import annotations

import ast
import hashlib
import posixpath
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
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from scripts.efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
    from scripts import verify_eshm20_root_config_dependencies as root_bridge
except ModuleNotFoundError:  # pragma: no cover - direct script import path
    from acquire_efehr_gitlab_receipt import (
        EfehrAcquisitionError,
        TOTAL_DEADLINE_SECONDS,
        _open_fixed,
        _read_bounded,
        _remaining,
        _validate_exact_response,
    )
    from efehr_gitlab_receipt import (
        EfehrReceiptError,
        raw_file_api_url,
        validate_target,
    )
    import verify_eshm20_root_config_dependencies as root_bridge

SCHEMA_VERSION = "oc-eshm20-gsim-resource-profile-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 374
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
REPOSITORY_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "gmpe_complete_logic_tree_5br.xml"
)
EXPECTED_BYTE_COUNT = 33760
EXPECTED_SHA256 = "e2c53f11174b8cd4de1f65af4dafc5af2e7a6848563e8a4c0ada44a54f22ff62"
OPENQUAKE_REFERENCE = (
    "gem/oq-engine@v3.14.0:openquake/hazardlib/gsim_lt.py::rel_paths/collect_files"
)
ROOT_DEPENDENCY_RESULT_COMMENT_ID = 5301726249
ROOT_DEPENDENCY_SECTION = "calculation"
ROOT_DEPENDENCY_OPTION = "gsim_logic_tree_file"
FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID = 5301857400
FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID = 5301858821
FIRST_ORDER_RECEIPT_RUN_ID = 31880089623
FIRST_ORDER_RECEIPT_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"
FIRST_ORDER_RECEIPT_RETRIEVED_AT = "2026-08-15T10:40:16Z"
INVENTORY_RECEIPT_COMMENT_ID = root_bridge.INVENTORY_RECEIPT_COMMENT_ID

MAX_BRANCH_SETS = 64
MAX_BRANCHES = 512
MAX_MODEL_TEXT_CHARS = 32768
MAX_MODEL_LINES = 1024
MAX_RESOURCE_REFERENCES = 256


class Eshm20GsimResourceProfileError(RuntimeError):
    """Raised when exact GMM resource profiling cannot close safely."""


def _local_name(tag: object) -> str:
    if type(tag) is not str:
        raise Eshm20GsimResourceProfileError("GMM logic-tree XML tag has invalid type")
    return tag.rsplit("}", 1)[-1]


def _require_safe_xml_identity(value: object, field: str) -> str:
    """Require safe exact XML identifiers before grouping or serialization."""

    if type(value) is not str or not value or value != value.strip():
        raise Eshm20GsimResourceProfileError(
            f"GMM {field} is missing, empty or not already trimmed"
        )
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Eshm20GsimResourceProfileError(
            f"GMM {field} contains control characters"
        )
    return value


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise Eshm20GsimResourceProfileError("GMM logic-tree payload must be immutable bytes")
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise Eshm20GsimResourceProfileError(
            "GMM logic-tree byte count does not match the trusted receipt"
        )
    observed = hashlib.sha256(payload).hexdigest()
    if observed != EXPECTED_SHA256:
        raise Eshm20GsimResourceProfileError(
            "GMM logic-tree SHA-256 does not match the trusted receipt"
        )
    return observed


def _validate_inventory() -> frozenset[str]:
    inventory = root_bridge.FROZEN_INVENTORY_PATHS
    if type(inventory) is not frozenset or len(inventory) != 62:
        raise Eshm20GsimResourceProfileError(
            "frozen ESHM20 provider inventory identity is invalid"
        )
    if REPOSITORY_PATH not in inventory:
        raise Eshm20GsimResourceProfileError(
            "GMM logic tree is absent from the frozen ESHM20 inventory"
        )
    return inventory


def _canonical_relative_resource(value: object) -> tuple[str, str]:
    if type(value) is not str or not value:
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource value must be a non-empty literal string"
        )
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource path contains control characters"
        )
    if "\\" in value:
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource path must use POSIX separators"
        )
    if "://" in value or "?" in value or "#" in value:
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource path cannot be a URL/query/fragment"
        )
    if value.startswith("/") or (len(value) >= 2 and value[1] == ":"):
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource path must be repository-relative"
        )

    pure = PurePosixPath(value)
    relative = pure.as_posix()
    if relative != value or any(part in {"", ".", ".."} for part in pure.parts):
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource path is not canonical"
        )
    base = posixpath.dirname(REPOSITORY_PATH)
    resolved = posixpath.normpath(posixpath.join(base, relative))
    if resolved == ".." or resolved.startswith("../") or resolved.startswith("/"):
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource path escapes the repository"
        )
    return relative, resolved


def _normalize_resource_key(raw_key: str) -> tuple[str, bool]:
    """Return a safe argument key while preserving the OQ 3.14 comment quirk.

    ``gsim_lt.rel_paths`` checks ``name.rstrip().endswith`` directly and does
    not remove TOML comments first. Therefore a single ``# coeff_file = ...``
    line can still become a collected dependency in that reference runtime.
    We retain that dependency but mark the origin as comment-prefixed so it is
    never misrepresented as an active GSIM argument.
    """

    key = raw_key.strip()
    comment_prefixed = key.startswith("#")
    if comment_prefixed:
        key = key[1:].strip()
    if not key or any(not (char.isalnum() or char == "_") for char in key):
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource argument name is invalid"
        )
    if not key.endswith(("_file", "_table")):
        raise Eshm20GsimResourceProfileError(
            "GSIM external resource argument lost its required suffix"
        )
    return key, comment_prefixed


def _resource_assignments(
    model_text: object,
) -> tuple[tuple[str, str, bool], ...]:
    if type(model_text) is not str:
        raise Eshm20GsimResourceProfileError(
            "GSIM uncertaintyModel text must be a string"
        )
    if len(model_text) > MAX_MODEL_TEXT_CHARS:
        raise Eshm20GsimResourceProfileError("GSIM uncertaintyModel text exceeds bounds")
    lines = model_text.splitlines()
    if len(lines) > MAX_MODEL_LINES:
        raise Eshm20GsimResourceProfileError("GSIM uncertaintyModel line count exceeds bounds")

    found: list[tuple[str, str, bool]] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("=")
        if len(parts) != 2:
            left = parts[0].rstrip() if parts else ""
            if left.endswith(("_file", "_table")):
                raise Eshm20GsimResourceProfileError(
                    "GSIM external resource assignment is ambiguous"
                )
            continue
        name, raw_value = parts
        raw_key = name.rstrip()
        if not raw_key.endswith(("_file", "_table")):
            continue
        key, comment_prefixed = _normalize_resource_key(raw_key)
        try:
            value = ast.literal_eval(raw_value.strip())
        except (ValueError, SyntaxError) as exc:
            raise Eshm20GsimResourceProfileError(
                "GSIM external resource value is not a literal string"
            ) from exc
        relative, _ = _canonical_relative_resource(value)
        found.append((key, relative, comment_prefixed))
        if len(found) > MAX_RESOURCE_REFERENCES:
            raise Eshm20GsimResourceProfileError(
                "GSIM external resource reference count exceeds bounds"
            )
    return tuple(found)


def _parse_xml(xml_text: str) -> ET.Element:
    lowered = xml_text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise Eshm20GsimResourceProfileError(
            "DTD/entity declarations are not allowed in GMM logic-tree XML"
        )
    if "\x00" in xml_text:
        raise Eshm20GsimResourceProfileError("NUL is not allowed in GMM logic-tree XML")
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise Eshm20GsimResourceProfileError(
            "verified GMM logic-tree XML is malformed"
        ) from exc


def _extract_resources(
    root: ET.Element,
    *,
    inventory: frozenset[str],
) -> tuple[int, int, list[dict[str, Any]]]:
    branch_sets = [
        node for node in root.iter() if _local_name(node.tag) == "logicTreeBranchSet"
    ]
    if not branch_sets or len(branch_sets) > MAX_BRANCH_SETS:
        raise Eshm20GsimResourceProfileError(
            "GMM logic-tree branch-set count is invalid or exceeds bounds"
        )

    branch_set_ids: set[str] = set()
    branch_ids: set[str] = set()
    branch_count = 0
    grouped: dict[tuple[str, str, bool, bool], set[tuple[str, str]]] = {}

    for branch_set in branch_sets:
        if branch_set.attrib.get("uncertaintyType") != "gmpeModel":
            raise Eshm20GsimResourceProfileError(
                "GMM logic tree contains a non-gmpeModel branch set"
            )
        branch_set_id = _require_safe_xml_identity(
            branch_set.attrib.get("branchSetID"), "branchSetID"
        )
        if branch_set_id in branch_set_ids:
            raise Eshm20GsimResourceProfileError("GMM branchSetID is duplicated")
        branch_set_ids.add(branch_set_id)

        branches = [
            child
            for child in list(branch_set)
            if _local_name(child.tag) == "logicTreeBranch"
        ]
        if not branches:
            raise Eshm20GsimResourceProfileError("GMM branch set has no logicTreeBranch")
        branch_count += len(branches)
        if branch_count > MAX_BRANCHES:
            raise Eshm20GsimResourceProfileError("GMM branch count exceeds bounds")

        for branch in branches:
            branch_id = _require_safe_xml_identity(
                branch.attrib.get("branchID"), "branchID"
            )
            if branch_id in branch_ids:
                raise Eshm20GsimResourceProfileError("GMM branchID is duplicated")
            branch_ids.add(branch_id)

            models = [
                child
                for child in list(branch)
                if _local_name(child.tag) == "uncertaintyModel"
            ]
            if len(models) != 1:
                raise Eshm20GsimResourceProfileError(
                    "GMM branch must contain exactly one uncertaintyModel"
                )
            model_text = models[0].text or ""
            for argument_key, relative_path, comment_prefixed in _resource_assignments(
                model_text
            ):
                _, resolved = _canonical_relative_resource(relative_path)
                member = resolved in inventory
                key = (argument_key, resolved, member, comment_prefixed)
                grouped.setdefault(key, set()).add((branch_set_id, branch_id))

    resources: list[dict[str, Any]] = []
    for (argument_key, resolved, member, comment_prefixed), origins in sorted(
        grouped.items(),
        key=lambda item: (item[0][1], item[0][0], item[0][3], item[0][2]),
    ):
        base = posixpath.dirname(REPOSITORY_PATH)
        relative = posixpath.relpath(resolved, base)
        resources.append(
            {
                "argument_key": argument_key,
                "relative_path": relative,
                "resolved_path": resolved,
                "selected_prefix_inventory_member": member,
                "comment_prefixed": comment_prefixed,
                "origins": [
                    {"branch_set_id": branch_set_id, "branch_id": branch_id}
                    for branch_set_id, branch_id in sorted(origins)
                ],
            }
        )
    return len(branch_sets), branch_count, resources


def extract_verified_gsim_resource_profile(payload: bytes) -> dict[str, Any]:
    """Verify exact GMM bytes, then profile only `_file`/`_table` resources."""

    observed_sha256 = _verify_payload_identity(payload)
    inventory = _validate_inventory()
    try:
        xml_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Eshm20GsimResourceProfileError(
            "verified GMM logic-tree payload is not strict UTF-8"
        ) from exc
    root = _parse_xml(xml_text)
    branch_set_count, branch_count, resources = _extract_resources(
        root, inventory=inventory
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "source_issue": SOURCE_ISSUE,
        "control_issue": CONTROL_ISSUE,
        "dataset_id": DATASET_ID,
        "project_id": PROJECT_ID,
        "project_path": PROJECT_PATH,
        "commit_sha": COMMIT_SHA,
        "repository_path": REPOSITORY_PATH,
        "byte_count": len(payload),
        "sha256": observed_sha256,
        "openquake_reference": OPENQUAKE_REFERENCE,
        "inventory_receipt_comment_id": INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": ROOT_DEPENDENCY_SECTION,
        "root_dependency_option": ROOT_DEPENDENCY_OPTION,
        "first_order_receipt_request_comment_id": FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_result_comment_id": FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
        "first_order_receipt_run_id": FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "first_order_receipt_retrieved_at": FIRST_ORDER_RECEIPT_RETRIEVED_AT,
        "branch_set_count": branch_set_count,
        "branch_count": branch_count,
        "resource_reference_count": len(resources),
        "resources": resources,
        "dependency_inventory_authorized": False,
        "dependency_receipt_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def acquire_eshm20_gsim_resource_profile(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize and inspect only the fixed receipted ESHM20 GMM tree."""

    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Eshm20GsimResourceProfileError(
            "trusted ESHM20 GMM resource-profile target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-GSIM-resource-profile-v1",
        },
        method="GET",
    )
    deadline = monotonic() + TOTAL_DEADLINE_SECONDS
    open_response = opener or _open_fixed

    try:
        with open_response(request, timeout=_remaining(deadline, monotonic)) as response:
            _validate_exact_response(response, file_url)
            raw = _read_bounded(
                response,
                deadline=deadline,
                maximum=EXPECTED_BYTE_COUNT,
                monotonic=monotonic,
            )
    except EfehrAcquisitionError as exc:
        raise Eshm20GsimResourceProfileError(
            "ESHM20 GMM logic-tree retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20GsimResourceProfileError(
            f"ESHM20 GMM logic-tree retrieval failed: {type(exc).__name__}"
        ) from exc

    result = extract_verified_gsim_resource_profile(raw)
    if (
        result.get("dependency_inventory_authorized") is not False
        or result.get("dependency_receipt_authorized") is not False
        or result.get("external_bytes_persisted") is not False
        or result.get("publication_authorized") is not False
        or result.get("model_use_authorized") is not False
    ):
        raise Eshm20GsimResourceProfileError(
            "verified ESHM20 GMM profile widened its authority ceiling"
        )
    return result
