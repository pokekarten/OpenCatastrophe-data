# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile dependencies from only the receipted ESHM20 source-model logic tree.

Issue #361 already established the exact immutable byte identity of the one
source-model logic-tree file selected by the verified ESHM20 root config. This
worker re-materializes only that fixed provider object, verifies its exact byte
count and SHA-256 before decoding, delegates interpretation to the existing
reviewed offline source-model logic-tree parser, and returns bounded derived
metadata. Provider bytes are never returned or persisted and callers cannot
select provider/project/ref/path/parser/inventory or dependency expansion.
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
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
    from scripts import openquake_source_model_logic_tree_dependencies as parser
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
    import openquake_source_model_logic_tree_dependencies as parser
    import verify_eshm20_root_config_dependencies as root_bridge

SCHEMA_VERSION = "oc-eshm20-source-model-dependency-profile-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 367
DATASET_ID = "efehr.eshm20"
PROJECT_ID = 197
PROJECT_PATH = "efehr/eshm20"
COMMIT_SHA = "fbd334de68f85d72669f73fc5a314a113db67317"
REPOSITORY_PATH = (
    "oq_computational/oq_configuration_eshm20_v12e_region_main/"
    "source_model_logic_tree_eshm20_model_v12e.xml"
)
EXPECTED_BYTE_COUNT = 17579
EXPECTED_SHA256 = "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867"
PARSER_ID = (
    "scripts.openquake_source_model_logic_tree_dependencies."
    "extract_source_model_logic_tree_dependencies"
)
ROOT_DEPENDENCY_RESULT_COMMENT_ID = 5301726249
ROOT_DEPENDENCY_SECTION = "calculation"
ROOT_DEPENDENCY_OPTION = "source_model_logic_tree_file"
FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID = 5301857400
FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID = 5301858821
FIRST_ORDER_RECEIPT_RUN_ID = 31880089623
FIRST_ORDER_RECEIPT_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"
FIRST_ORDER_RECEIPT_RETRIEVED_AT = "2026-08-15T10:40:16Z"
INVENTORY_RECEIPT_COMMENT_ID = root_bridge.INVENTORY_RECEIPT_COMMENT_ID


class Eshm20SourceModelDependencyError(RuntimeError):
    """Raised when the fixed source-tree dependency profile cannot close safely."""


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise Eshm20SourceModelDependencyError(
            "source-model logic-tree payload must be immutable bytes"
        )
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise Eshm20SourceModelDependencyError(
            "source-model logic-tree byte count does not match the trusted receipt"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if observed_sha256 != EXPECTED_SHA256:
        raise Eshm20SourceModelDependencyError(
            "source-model logic-tree SHA-256 does not match the trusted receipt"
        )
    return observed_sha256


def _validate_frozen_inventory() -> frozenset[str]:
    inventory = root_bridge.FROZEN_INVENTORY_PATHS
    if type(inventory) is not frozenset or len(inventory) != 62:
        raise Eshm20SourceModelDependencyError(
            "frozen ESHM20 provider inventory identity is invalid"
        )
    if REPOSITORY_PATH not in inventory:
        raise Eshm20SourceModelDependencyError(
            "source-model logic tree is absent from the frozen ESHM20 inventory"
        )
    if any(path.endswith(".hdf5") for path in inventory):
        raise Eshm20SourceModelDependencyError(
            "frozen ESHM20 inventory unexpectedly contains an HDF5 companion"
        )
    return inventory


def _require_safe_origin_identity(value: object, field: str) -> str:
    """Require bounded textual identity before ordering or durable serialization."""

    if type(value) is not str or not value or value != value.strip():
        raise Eshm20SourceModelDependencyError(
            f"source-model dependency {field} is empty or not already trimmed"
        )
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Eshm20SourceModelDependencyError(
            f"source-model dependency {field} contains control characters"
        )
    return value


def _validate_dependency_shape(dependency: object) -> parser.SourceModelDependency:
    """Reject parser-return type/identity confusion before ordering operations."""

    if type(dependency) is not parser.SourceModelDependency:
        raise Eshm20SourceModelDependencyError(
            "source-model dependency parser returned an invalid item"
        )
    if type(dependency.resolved_path) is not str:
        raise Eshm20SourceModelDependencyError(
            "source-model dependency path has an invalid type"
        )
    if type(dependency.is_hdf5_companion) is not bool:
        raise Eshm20SourceModelDependencyError(
            "source-model dependency companion flag has an invalid type"
        )
    if type(dependency.origins) is not tuple or not dependency.origins:
        raise Eshm20SourceModelDependencyError(
            "source-model dependency must retain at least one declaring branch"
        )
    for origin in dependency.origins:
        if type(origin) is not parser.LogicTreeDependencyOrigin:
            raise Eshm20SourceModelDependencyError(
                "source-model dependency origin has an invalid type"
            )
        _require_safe_origin_identity(origin.uncertainty_type, "uncertainty type")
        _require_safe_origin_identity(origin.branch_id, "branch id")
    return dependency


def _dependency_order_key(
    dependency: parser.SourceModelDependency,
) -> tuple[str, bool, tuple[tuple[str, str], ...]]:
    return (
        dependency.resolved_path,
        dependency.is_hdf5_companion,
        tuple((origin.uncertainty_type, origin.branch_id) for origin in dependency.origins),
    )


def _serialize_dependencies(
    dependencies: object,
    *,
    inventory: frozenset[str],
) -> list[dict[str, Any]]:
    if type(dependencies) is not tuple:
        raise Eshm20SourceModelDependencyError(
            "source-model dependency parser returned an invalid collection"
        )

    typed_dependencies = tuple(_validate_dependency_shape(item) for item in dependencies)
    expected_order = tuple(sorted(typed_dependencies, key=_dependency_order_key))
    if typed_dependencies != expected_order:
        raise Eshm20SourceModelDependencyError(
            "source-model dependencies are not in canonical order"
        )

    seen_paths: set[str] = set()
    output: list[dict[str, Any]] = []
    for dependency in typed_dependencies:
        path = dependency.resolved_path
        if path not in inventory:
            raise Eshm20SourceModelDependencyError(
                "source-model dependency is absent from the frozen ESHM20 inventory"
            )
        if path in seen_paths:
            raise Eshm20SourceModelDependencyError(
                "source-model dependency parser returned a duplicate path"
            )
        seen_paths.add(path)

        if dependency.is_hdf5_companion or path.endswith(".hdf5"):
            raise Eshm20SourceModelDependencyError(
                "source-model dependency invented an HDF5 companion absent from inventory"
            )
        expected_origins = tuple(
            sorted(
                dependency.origins,
                key=lambda origin: (origin.uncertainty_type, origin.branch_id),
            )
        )
        if dependency.origins != expected_origins:
            raise Eshm20SourceModelDependencyError(
                "source-model dependency origins are not in canonical order"
            )

        origins: list[dict[str, str]] = []
        for origin in dependency.origins:
            if origin.uncertainty_type not in {"sourceModel", "extendModel"}:
                raise Eshm20SourceModelDependencyError(
                    "source-model dependency origin widened parser semantics"
                )
            origins.append(
                {
                    "uncertainty_type": origin.uncertainty_type,
                    "branch_id": origin.branch_id,
                }
            )

        output.append(
            {
                "resolved_path": path,
                "origins": origins,
                "is_hdf5_companion": False,
            }
        )
    return output


def extract_verified_source_model_dependencies(payload: bytes) -> dict[str, Any]:
    """Verify exact source-tree bytes, then derive bounded dependency metadata."""

    observed_sha256 = _verify_payload_identity(payload)
    inventory = _validate_frozen_inventory()
    try:
        xml_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Eshm20SourceModelDependencyError(
            "verified source-model logic-tree payload is not strict UTF-8"
        ) from exc

    try:
        dependencies = parser.extract_source_model_logic_tree_dependencies(
            xml_text,
            logic_tree_path=REPOSITORY_PATH,
            repository_inventory=inventory,
        )
    except parser.OpenQuakeLogicTreeError as exc:
        raise Eshm20SourceModelDependencyError(
            "verified source-model logic-tree dependency parsing failed closed"
        ) from exc

    serialized = _serialize_dependencies(dependencies, inventory=inventory)
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
        "parser": PARSER_ID,
        "inventory_receipt_comment_id": INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": ROOT_DEPENDENCY_SECTION,
        "root_dependency_option": ROOT_DEPENDENCY_OPTION,
        "first_order_receipt_request_comment_id": FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_result_comment_id": FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
        "first_order_receipt_run_id": FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "first_order_receipt_retrieved_at": FIRST_ORDER_RECEIPT_RETRIEVED_AT,
        "dependencies": serialized,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def acquire_eshm20_source_model_dependencies(
    *, opener: Any | None = None, monotonic: Any = time.monotonic
) -> dict[str, Any]:
    """Re-materialize and profile only the fixed receipted ESHM20 source tree."""

    try:
        target = validate_target(
            source_issue=SOURCE_ISSUE,
            dataset_id=DATASET_ID,
            project_id=PROJECT_ID,
            commit_sha=COMMIT_SHA,
            repository_path=REPOSITORY_PATH,
        )
    except EfehrReceiptError as exc:
        raise Eshm20SourceModelDependencyError(
            "trusted ESHM20 source-model dependency target is invalid"
        ) from exc

    file_url = raw_file_api_url(target)
    request = urllib.request.Request(
        file_url,
        headers={
            "Accept": "application/xml,text/xml,text/plain;q=0.9,application/octet-stream;q=0.8",
            "User-Agent": "OpenCatastrophe-ESHM20-source-model-dependency-profile-v1",
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
    except Eshm20SourceModelDependencyError:
        raise
    except EfehrAcquisitionError as exc:
        raise Eshm20SourceModelDependencyError(
            "ESHM20 source-model logic-tree retrieval failed closed"
        ) from exc
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise Eshm20SourceModelDependencyError(
            f"ESHM20 source-model logic-tree retrieval failed: {type(exc).__name__}"
        ) from exc

    result = extract_verified_source_model_dependencies(raw)
    if (
        result.get("dependency_inventory_authorized") is not False
        or result.get("external_bytes_persisted") is not False
        or result.get("publication_authorized") is not False
    ):
        raise Eshm20SourceModelDependencyError(
            "verified ESHM20 source-model result widened its authority ceiling"
        )
    return result
