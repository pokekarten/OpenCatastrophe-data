# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Derive a deterministic Kosovo-residential ESRM20 exposure wrapper.

The caller supplies the already-receipted provider wrapper bytes. This module is
offline-only: it verifies their exact identity and bounded semantic profile,
changes only the external asset reference, and returns derived bytes plus a
fail-closed evidence record. It does not read the selected CSV or persist bytes.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from copy import deepcopy
from typing import Any

from scripts import profile_esrm20_runtime_exposure_xml as exposure_profile

_CANONICAL_SCHEMA_VERSION = "oc-esrm20-kosovo-residential-wrapper-recipe-v1"
_CANONICAL_SOURCE_ISSUE = 282
_CANONICAL_CONTROL_ISSUE = 611
_CANONICAL_DOWNSTREAM_ISSUE = 609
_CANONICAL_PROJECT_ID = 269
_CANONICAL_PROJECT_PATH = "efehr/esrm20"
_CANONICAL_COMMIT_SHA = "05f83bbc9df81d02ee8ddb1801d9d781355ce783"
_CANONICAL_SOURCE_REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Kosovo.xml"
_CANONICAL_SOURCE_BYTE_COUNT = 664
_CANONICAL_SOURCE_SHA256 = (
    "61be4c534e6bdd1577d15dd289b2c604fde41f00f8f636901634daf2f41bcceb"
)
_CANONICAL_SELECTED_REPOSITORY_PATH = "Exposure/OQ_Exposure_Input_Kosovo_Res.csv"
_CANONICAL_SELECTED_BYTE_COUNT = 160627
_CANONICAL_SELECTED_SHA256 = (
    "12a20d393c8d677d304263aed96eb05f81098104fd7e3fb0d119aafc336aa00f"
)
_CANONICAL_SELECTED_ASSET = "OQ_Exposure_Input_Kosovo_Res.csv"
_CANONICAL_OUTPUT_LOGICAL_PATH = (
    "Exposure/OQ_Exposure_Input_Kosovo_Residential_Reconstructed.xml"
)
_CANONICAL_EXPERIMENT_LABEL = "reconstructed_experiment"
_CANONICAL_SCOPE = "kosovo_residential_only"
_CANONICAL_SOURCE_ASSETS = (
    "OQ_Exposure_Input_Kosovo_Com.csv",
    "OQ_Exposure_Input_Kosovo_Ind.csv",
    _CANONICAL_SELECTED_ASSET,
)

SCHEMA_VERSION = _CANONICAL_SCHEMA_VERSION
SOURCE_ISSUE = _CANONICAL_SOURCE_ISSUE
CONTROL_ISSUE = _CANONICAL_CONTROL_ISSUE
DOWNSTREAM_ISSUE = _CANONICAL_DOWNSTREAM_ISSUE
PROJECT_ID = _CANONICAL_PROJECT_ID
PROJECT_PATH = _CANONICAL_PROJECT_PATH
COMMIT_SHA = _CANONICAL_COMMIT_SHA
SOURCE_REPOSITORY_PATH = _CANONICAL_SOURCE_REPOSITORY_PATH
SOURCE_BYTE_COUNT = _CANONICAL_SOURCE_BYTE_COUNT
SOURCE_SHA256 = _CANONICAL_SOURCE_SHA256
SELECTED_REPOSITORY_PATH = _CANONICAL_SELECTED_REPOSITORY_PATH
SELECTED_BYTE_COUNT = _CANONICAL_SELECTED_BYTE_COUNT
SELECTED_SHA256 = _CANONICAL_SELECTED_SHA256
SELECTED_ASSET = _CANONICAL_SELECTED_ASSET
OUTPUT_LOGICAL_PATH = _CANONICAL_OUTPUT_LOGICAL_PATH
EXPERIMENT_LABEL = _CANONICAL_EXPERIMENT_LABEL
SCOPE = _CANONICAL_SCOPE
SOURCE_ASSETS = _CANONICAL_SOURCE_ASSETS

_CANONICAL_PROFILE_XML_BYTES = exposure_profile.profile_xml_bytes

class KosovoResidentialWrapperError(ValueError):
    """The source identity, source profile, or derived wrapper is invalid."""


def _expected_source_profile() -> dict[str, Any]:
    return {
        "nrml_namespace": "http://openquake.org/xmlns/nrml/0.4",
        "exposure_model": {
            "id": "exposure",
            "category": "buildings",
            "taxonomy_source": "GEM taxonomy",
            "description": "exposure model",
        },
        "asset_references": list(_CANONICAL_SOURCE_ASSETS),
        "cost_types": [
            {"name": "structural", "type": "aggregated", "unit": "EUR"}
        ],
        "area": None,
        "occupancy_periods": ["day", "night", "transit"],
        "tag_names": ["occupancy", "name_2", "id_2", "id_1", "name_1"],
        "exposure_fields": [],
        "structural_cost_type_declared": True,
        "structural_value_inputs": [],
    }


_CANONICAL_EXPECTED_SOURCE_PROFILE = _expected_source_profile


def _require_canonical_authority() -> None:
    identities = (
        (SCHEMA_VERSION, _CANONICAL_SCHEMA_VERSION, "schema version"),
        (SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (CONTROL_ISSUE, _CANONICAL_CONTROL_ISSUE, "control issue"),
        (DOWNSTREAM_ISSUE, _CANONICAL_DOWNSTREAM_ISSUE, "downstream issue"),
        (PROJECT_ID, _CANONICAL_PROJECT_ID, "project"),
        (PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (
            SOURCE_REPOSITORY_PATH,
            _CANONICAL_SOURCE_REPOSITORY_PATH,
            "source path",
        ),
        (SOURCE_BYTE_COUNT, _CANONICAL_SOURCE_BYTE_COUNT, "source byte count"),
        (SOURCE_SHA256, _CANONICAL_SOURCE_SHA256, "source SHA-256"),
        (
            SELECTED_REPOSITORY_PATH,
            _CANONICAL_SELECTED_REPOSITORY_PATH,
            "selected path",
        ),
        (
            SELECTED_BYTE_COUNT,
            _CANONICAL_SELECTED_BYTE_COUNT,
            "selected byte count",
        ),
        (SELECTED_SHA256, _CANONICAL_SELECTED_SHA256, "selected SHA-256"),
        (SELECTED_ASSET, _CANONICAL_SELECTED_ASSET, "selected asset"),
        (OUTPUT_LOGICAL_PATH, _CANONICAL_OUTPUT_LOGICAL_PATH, "output path"),
        (EXPERIMENT_LABEL, _CANONICAL_EXPERIMENT_LABEL, "experiment label"),
        (SCOPE, _CANONICAL_SCOPE, "scope"),
        (SOURCE_ASSETS, _CANONICAL_SOURCE_ASSETS, "source asset set"),
    )
    for observed, expected, label in identities:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialWrapperError(f"{label} authority drifted")
    if exposure_profile.profile_xml_bytes is not _CANONICAL_PROFILE_XML_BYTES:
        raise KosovoResidentialWrapperError("runtime exposure profiler authority drifted")
    if _expected_source_profile is not _CANONICAL_EXPECTED_SOURCE_PROFILE:
        raise KosovoResidentialWrapperError("source profile authority drifted")
    profiler_authority = (
        (exposure_profile.SOURCE_ISSUE, _CANONICAL_SOURCE_ISSUE, "source issue"),
        (exposure_profile.PROJECT_ID, _CANONICAL_PROJECT_ID, "project"),
        (exposure_profile.PROJECT_PATH, _CANONICAL_PROJECT_PATH, "project path"),
        (exposure_profile.COMMIT_SHA, _CANONICAL_COMMIT_SHA, "commit"),
        (
            exposure_profile.REPOSITORY_PATH,
            _CANONICAL_SOURCE_REPOSITORY_PATH,
            "source path",
        ),
        (
            exposure_profile.EXPECTED_BYTE_COUNT,
            _CANONICAL_SOURCE_BYTE_COUNT,
            "source byte count",
        ),
        (exposure_profile.EXPECTED_SHA256, _CANONICAL_SOURCE_SHA256, "source SHA-256"),
        (
            exposure_profile.NRML_NAMESPACE_LEGACY_04,
            "http://openquake.org/xmlns/nrml/0.4",
            "NRML namespace",
        ),
    )
    for observed, expected, label in profiler_authority:
        if type(observed) is not type(expected) or observed != expected:
            raise KosovoResidentialWrapperError(f"profiler {label} authority drifted")


def _verify_source_identity(source_wrapper: bytes) -> str:
    if type(source_wrapper) is not bytes:
        raise KosovoResidentialWrapperError("source wrapper must be bytes")
    if len(source_wrapper) != SOURCE_BYTE_COUNT:
        raise KosovoResidentialWrapperError("source wrapper byte identity mismatch")
    digest = hashlib.sha256(source_wrapper).hexdigest()
    if digest != SOURCE_SHA256:
        raise KosovoResidentialWrapperError("source wrapper byte identity mismatch")
    return digest


def _profile(payload: bytes, *, label: str) -> dict[str, Any]:
    try:
        return exposure_profile.profile_xml_bytes(payload)
    except exposure_profile.RuntimeExposureXmlProfileError as exc:
        raise KosovoResidentialWrapperError(f"{label} profile is invalid") from exc


def _derive_from_verified_source(source_wrapper: bytes) -> tuple[bytes, dict[str, Any]]:
    expected_source_profile = _expected_source_profile()
    source_profile = _profile(source_wrapper, label="source wrapper")
    if source_profile != expected_source_profile:
        raise KosovoResidentialWrapperError("source wrapper semantic profile drifted")

    root = ET.fromstring(source_wrapper)
    namespace = expected_source_profile["nrml_namespace"]
    assets = root.findall(f".//{{{namespace}}}assets")
    if len(assets) != 1:
        raise KosovoResidentialWrapperError("source wrapper assets element drifted")
    assets[0].text = SELECTED_ASSET

    serialized = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    canonical = ET.canonicalize(
        serialized,
        with_comments=False,
        strip_text=True,
        rewrite_prefixes=True,
    )
    # ElementTree emits an unusable empty-URI prefix declaration for
    # unqualified attributes when prefixes are rewritten (including on
    # Python 3.14). The bounded source profile permits no foreign namespace,
    # so these declarations are serializer artifacts and safe to omit.
    canonical = re.sub(r' xmlns:n[0-9]+=""', "", canonical)
    output = canonical.encode("utf-8")

    expected_output_profile = deepcopy(expected_source_profile)
    expected_output_profile["asset_references"] = [SELECTED_ASSET]
    if _profile(output, label="derived wrapper") != expected_output_profile:
        raise KosovoResidentialWrapperError("derived wrapper semantic profile drifted")

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "issues": {
            "source": SOURCE_ISSUE,
            "control": CONTROL_ISSUE,
            "downstream": DOWNSTREAM_ISSUE,
        },
        "source_wrapper": {
            "project_id": PROJECT_ID,
            "project_path": PROJECT_PATH,
            "commit_sha": COMMIT_SHA,
            "repository_path": SOURCE_REPOSITORY_PATH,
            "byte_count": SOURCE_BYTE_COUNT,
            "sha256": SOURCE_SHA256,
        },
        "selected_asset": {
            "repository_path": SELECTED_REPOSITORY_PATH,
            "byte_count": SELECTED_BYTE_COUNT,
            "sha256": SELECTED_SHA256,
        },
        "output": {
            "logical_path": OUTPUT_LOGICAL_PATH,
            "media_type": "application/xml",
            "byte_count": len(output),
            "sha256": hashlib.sha256(output).hexdigest(),
        },
        "transformation": {
            "operation": "replace_assets_reference",
            "source_asset_references": list(SOURCE_ASSETS),
            "derived_asset_references": [SELECTED_ASSET],
            "xml_serialization": (
                "xml.etree.ElementTree.c14n2-rewrite-prefixes-valid-xml"
            ),
        },
        "experiment_label": EXPERIMENT_LABEL,
        "scope": SCOPE,
        "source_wrapper_bytes_returned": False,
        "selected_asset_bytes_read": False,
        "derived_wrapper_bytes_returned": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "historical_reproduction": False,
        "value_structural_wiring_verified": False,
        "horizontal_component_conversion_applied": False,
    }
    return output, evidence


def build_kosovo_residential_exposure_wrapper(
    source_wrapper: bytes,
) -> tuple[bytes, dict[str, Any]]:
    """Return the deterministic residential-only wrapper and bounded evidence."""
    _require_canonical_authority()
    _verify_source_identity(source_wrapper)
    return _derive_from_verified_source(source_wrapper)
