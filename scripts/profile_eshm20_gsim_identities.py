# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Profile the GSIM identity surface of the exact receipted ESHM20 GMM tree.

This module is intentionally narrower than OpenQuake execution. It verifies
one already-receipted provider object before inspection, then extracts only the
model token and argument-key names that OpenQuake 3.14 would pass to
``valid.gsim``. It does not resolve aliases, load the OpenQuake registry,
instantiate GSIM classes, retain argument values, or authorize model use.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from typing import Any

SCHEMA_VERSION = "oc-eshm20-gsim-identity-profile-v1"
SOURCE_ISSUE = 281
CONTROL_ISSUE = 427
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
EXPECTED_BRANCH_SET_COUNT = 6
EXPECTED_BRANCH_COUNT = 80

FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID = 5301858821
FIRST_ORDER_RECEIPT_RUN_ID = 31880089623
FIRST_ORDER_RECEIPT_EXECUTION_SHA = "ab66e3e4c58c9b8f18587f1a8a51cf67cf9851b1"

OPENQUAKE_REPOSITORY = "gem/oq-engine"
OPENQUAKE_TAG = "v3.14.0"
OPENQUAKE_COMMIT = "9f044c93d72846421a8faa90ebf0a6afacdf3c20"
OPENQUAKE_GSIM_LT_REFERENCE = (
    "openquake/hazardlib/gsim_lt.py::GsimLogicTree._build_trts_branches"
)
OPENQUAKE_VALID_REFERENCE = "openquake/hazardlib/valid.py::to_toml/gsim"

MAX_BRANCH_SETS = 64
MAX_BRANCHES = 512
MAX_MODEL_TEXT_CHARS = 32768
MAX_MODEL_LINES = 1024
MAX_ARGUMENT_KEYS = 256
MAX_IDENTITY_CHARS = 256

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:+/@-]+$")
_SAFE_MODEL_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_SAFE_ARGUMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Eshm20GsimIdentityProfileError(ValueError):
    """Raised when bounded GSIM identity profiling cannot close safely."""


def _local_name(tag: object) -> str:
    if type(tag) is not str:
        raise Eshm20GsimIdentityProfileError("GMM XML tag has invalid type")
    return tag.rsplit("}", 1)[-1]


def _safe_identity(value: object, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise Eshm20GsimIdentityProfileError(f"{field} is missing or not canonical")
    if len(value) > MAX_IDENTITY_CHARS or not _SAFE_ID_RE.fullmatch(value):
        raise Eshm20GsimIdentityProfileError(f"{field} contains unsupported characters")
    return value


def _safe_label(value: object, field: str) -> str:
    """Accept a bounded human-readable provider label, not an identifier."""

    if type(value) is not str or not value or value != value.strip():
        raise Eshm20GsimIdentityProfileError(f"{field} is missing or not canonical")
    if len(value) > MAX_IDENTITY_CHARS:
        raise Eshm20GsimIdentityProfileError(f"{field} exceeds bounds")
    if not value.isprintable() or any(ord(char) == 127 for char in value):
        raise Eshm20GsimIdentityProfileError(f"{field} contains controls")
    return value


def _verify_payload_identity(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise Eshm20GsimIdentityProfileError("GMM payload must be immutable bytes")
    if len(payload) != EXPECTED_BYTE_COUNT:
        raise Eshm20GsimIdentityProfileError(
            "GMM byte count does not match the trusted receipt"
        )
    observed = hashlib.sha256(payload).hexdigest()
    if observed != EXPECTED_SHA256:
        raise Eshm20GsimIdentityProfileError(
            "GMM SHA-256 does not match the trusted receipt"
        )
    return observed


def _parse_xml(xml_text: str) -> ET.Element:
    if type(xml_text) is not str:
        raise Eshm20GsimIdentityProfileError("GMM XML text must be a string")
    lowered = xml_text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise Eshm20GsimIdentityProfileError("DTD/entity declarations are not allowed")
    if "\x00" in xml_text:
        raise Eshm20GsimIdentityProfileError("NUL is not allowed in GMM XML")
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise Eshm20GsimIdentityProfileError("verified GMM XML is malformed") from exc


def _argument_key(value: object) -> str:
    if type(value) is not str or not _SAFE_ARGUMENT_RE.fullmatch(value):
        raise Eshm20GsimIdentityProfileError("GSIM argument key is unsupported")
    return value


def _model_name(value: object) -> str:
    if type(value) is not str or not _SAFE_MODEL_RE.fullmatch(value):
        raise Eshm20GsimIdentityProfileError("GSIM model token is unsupported")
    return value


def _structural_model_identity(model: ET.Element) -> tuple[str, tuple[str, ...]]:
    """Extract only the requested model token and argument-key names.

    OpenQuake 3.14 first applies ``valid.to_toml`` and then ``valid.gsim``.
    This helper intentionally stops before TOML value parsing, alias lookup,
    registry lookup, path resolution or class instantiation.
    """

    raw_text = model.text or ""
    if len(raw_text) > MAX_MODEL_TEXT_CHARS:
        raise Eshm20GsimIdentityProfileError("GSIM model text exceeds bounds")
    if any(ord(char) < 32 and char not in "\t\n\r" for char in raw_text):
        raise Eshm20GsimIdentityProfileError("GSIM model text contains controls")

    lines = raw_text.splitlines()
    if len(lines) > MAX_MODEL_LINES:
        raise Eshm20GsimIdentityProfileError("GSIM model line count exceeds bounds")
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        raise Eshm20GsimIdentityProfileError("GSIM uncertaintyModel is empty")

    argument_keys: set[str] = set()
    for key in model.attrib:
        key = _argument_key(key)
        if key in argument_keys:
            raise Eshm20GsimIdentityProfileError("GSIM argument key is duplicated")
        argument_keys.add(key)

    first = lines[0]
    if first.startswith("[["):
        raise Eshm20GsimIdentityProfileError("GSIM arrays-of-tables are outside the profile")

    if first.startswith("["):
        if not first.endswith("]") or first.count("[") != 1 or first.count("]") != 1:
            raise Eshm20GsimIdentityProfileError("GSIM table header is malformed")
        name = _model_name(first[1:-1].strip())
        body = lines[1:]
    else:
        if len(lines) != 1 or "=" in first or first.startswith("#"):
            raise Eshm20GsimIdentityProfileError(
                "bare GSIM form must contain exactly one model token"
            )
        name = _model_name(first)
        body = []

    for line in body:
        if line.startswith("#"):
            continue
        if line.startswith("["):
            raise Eshm20GsimIdentityProfileError(
                "nested or multiple GSIM tables are outside the profile"
            )
        if "=" not in line:
            raise Eshm20GsimIdentityProfileError("GSIM argument assignment is malformed")
        key_text, value_text = line.split("=", 1)
        if not value_text.strip():
            raise Eshm20GsimIdentityProfileError("GSIM argument value is empty")
        key = _argument_key(key_text.strip())
        if key in argument_keys:
            raise Eshm20GsimIdentityProfileError("GSIM argument key is duplicated")
        argument_keys.add(key)
        if len(argument_keys) > MAX_ARGUMENT_KEYS:
            raise Eshm20GsimIdentityProfileError("GSIM argument-key count exceeds bounds")

    return name, tuple(sorted(argument_keys))


def _profile_root(root: ET.Element) -> dict[str, Any]:
    branch_sets = [
        node for node in root.iter() if _local_name(node.tag) == "logicTreeBranchSet"
    ]
    if not branch_sets or len(branch_sets) > MAX_BRANCH_SETS:
        raise Eshm20GsimIdentityProfileError(
            "GMM branch-set count is invalid or exceeds bounds"
        )

    branch_set_ids: set[str] = set()
    branch_ids: set[str] = set()
    records: list[dict[str, Any]] = []

    for branch_set in branch_sets:
        if branch_set.attrib.get("uncertaintyType") != "gmpeModel":
            raise Eshm20GsimIdentityProfileError(
                "GMM logic tree contains a non-gmpeModel branch set"
            )
        branch_set_id = _safe_identity(
            branch_set.attrib.get("branchSetID"), "branchSetID"
        )
        if branch_set_id in branch_set_ids:
            raise Eshm20GsimIdentityProfileError("GMM branchSetID is duplicated")
        branch_set_ids.add(branch_set_id)

        trt_value = branch_set.attrib.get("applyToTectonicRegionType")
        tectonic_region_type = (
            _safe_label(trt_value, "applyToTectonicRegionType")
            if trt_value is not None
            else None
        )

        branches = [
            child for child in list(branch_set)
            if _local_name(child.tag) == "logicTreeBranch"
        ]
        if not branches:
            raise Eshm20GsimIdentityProfileError("GMM branch set has no branches")

        for branch in branches:
            branch_id = _safe_identity(branch.attrib.get("branchID"), "branchID")
            if branch_id in branch_ids:
                raise Eshm20GsimIdentityProfileError("GMM branchID is duplicated")
            branch_ids.add(branch_id)
            if len(branch_ids) > MAX_BRANCHES:
                raise Eshm20GsimIdentityProfileError("GMM branch count exceeds bounds")

            models = [
                child for child in list(branch)
                if _local_name(child.tag) == "uncertaintyModel"
            ]
            if len(models) != 1:
                raise Eshm20GsimIdentityProfileError(
                    "GMM branch must contain exactly one uncertaintyModel"
                )
            gsim_name, argument_keys = _structural_model_identity(models[0])
            records.append(
                {
                    "branch_set_id": branch_set_id,
                    "branch_id": branch_id,
                    "tectonic_region_type": tectonic_region_type,
                    "gsim_name": gsim_name,
                    "argument_keys": list(argument_keys),
                }
            )

    records.sort(
        key=lambda record: (
            record["branch_set_id"],
            record["branch_id"],
            record["gsim_name"],
            tuple(record["argument_keys"]),
        )
    )
    names = sorted({record["gsim_name"] for record in records})
    keys = sorted({key for record in records for key in record["argument_keys"]})
    return {
        "branch_set_count": len(branch_sets),
        "branch_count": len(records),
        "branches": records,
        "unique_gsim_names": names,
        "unique_argument_keys": keys,
    }


def _profile_xml_text(xml_text: str) -> dict[str, Any]:
    """Internal synthetic/offline entry point used by focused tests."""

    return _profile_root(_parse_xml(xml_text))


def profile_verified_gsim_identities(payload: bytes) -> dict[str, Any]:
    """Verify the frozen provider bytes, then return bounded GSIM identities."""

    observed_sha256 = _verify_payload_identity(payload)
    try:
        xml_text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Eshm20GsimIdentityProfileError(
            "verified GMM payload is not strict UTF-8"
        ) from exc

    profile = _profile_xml_text(xml_text)
    if profile["branch_set_count"] != EXPECTED_BRANCH_SET_COUNT:
        raise Eshm20GsimIdentityProfileError(
            "verified GMM branch-set count drifted from trusted evidence"
        )
    if profile["branch_count"] != EXPECTED_BRANCH_COUNT:
        raise Eshm20GsimIdentityProfileError(
            "verified GMM branch count drifted from trusted evidence"
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
        "first_order_receipt_result_comment_id": FIRST_ORDER_RECEIPT_RESULT_COMMENT_ID,
        "first_order_receipt_run_id": FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "openquake_reference": {
            "repository": OPENQUAKE_REPOSITORY,
            "tag": OPENQUAKE_TAG,
            "commit": OPENQUAKE_COMMIT,
            "gsim_logic_tree": OPENQUAKE_GSIM_LT_REFERENCE,
            "gsim_parser": OPENQUAKE_VALID_REFERENCE,
        },
        **profile,
        "alias_resolution_verified": False,
        "runtime_compatibility_verified": False,
        "gsim_instantiation_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
